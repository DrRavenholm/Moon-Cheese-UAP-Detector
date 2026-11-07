#!/usr/bin/python3
"""Raspberry Pi motion recorder with a 5-second pre-roll and quiet-time tail.

Uses the Picamera2 CircularOutput2 encoder output, which holds video in a
rolling buffer even when no file is being saved. The buffer is delayed: close
the MP4 after POST+PRE quiet seconds to keep POST seconds of actual footage.
This is a basic difference detector, not an identification/classification model.
"""
import logging
import shutil
import signal
import time
from pathlib import Path
from datetime import datetime, timezone

from common import DATA, RECORDINGS, THUMBS, SETTINGS, RESOLUTIONS, add_event, connection, ensure_db, read_config, write_status
from observation_jobs import (migrate as jobs_migrate, due as job_due, orphaned as jobs_orphaned, perform as perform_job, mark_ready as jobs_mark_ready)
from storm import StormGuard
from storm_events import activated as storm_activated, recovered as storm_recovered, close_orphaned_on_startup
from motion_logic import ClipPlanner
from sky_tracking import SkyLightTracker
from motion_logic import detection_decision
from trigger_logic import source_for_trigger
from hardware import capture_capabilities
from scheduling import detection_window
from camera_profiles import selected_profile, effective_slot, camera_controls
from draft_preview import pending_request, PENDING, write_result, image_path, expire_old_files
from photography import pending as pending_photo, state as photo_state, capture_still

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
LOG = logging.getLogger('detector')
STOP = False


def terminate(signum, frame):
    global STOP
    STOP = True


signal.signal(signal.SIGTERM, terminate)
signal.signal(signal.SIGINT, terminate)


def run_camera(settings):
    import cv2
    from picamera2 import Picamera2
    from picamera2.encoders import H264Encoder
    from picamera2.outputs import CircularOutput2, PyavOutput
    from libcamera import Transform, controls as lc_controls

    w, h = 320, 240
    fps = int(settings.get('fps', 15))
    caps = capture_capabilities()
    if not 5 <= fps <= caps['max_fps']:
        raise ValueError(f'Requested {fps} fps exceeds the checked {caps["max_fps"]} fps limit on this hardware')
    resolution = settings.get('resolution', '1280x720')
    if resolution not in RESOLUTIONS:
        raise ValueError('Unsupported camera resolution')
    video_width, video_height = RESOLUTIONS[resolution]
    pre = float(settings.get('pre_motion_seconds', 5))
    post = float(settings.get('post_motion_seconds', 5))
    cap = float(settings.get('max_clip_seconds', 300))
    if not (1 <= pre <= 15 and 1 <= post <= 60 and cap >= pre + post + 2):
        raise ValueError('Invalid pre/post recording duration or clip rollover interval')
    planner = ClipPlanner(pre_seconds=pre, post_seconds=post,
                          max_seconds=cap)
    storm = StormGuard()
    storm.set_config(settings)
    storm_notification_id = None
    storm_cooling_before = False
    profile = settings.get('detection_profile', 'general')
    if profile not in ('general', 'sky_lights', 'combined'):
        raise ValueError('Unrecognised detection profile')
    sky_tracker = (SkyLightTracker(
        brightness=int(settings.get('sky_brightness', 180)),
        min_area=int(settings.get('sky_min_area', 2)),
        max_area=int(settings.get('sky_max_area', 100)),
        confirm_frames=int(settings.get('sky_confirm_frames', 3)),
        min_movement=int(settings.get('sky_min_movement', 2)))
        if profile in ('sky_lights', 'combined') else None)
    selected_slot, selected_cfg = selected_profile(settings)
    camera = Picamera2()
    allowed_controls = camera.camera_controls
    controls = camera_controls(selected_cfg, fps, allowed_controls, lc_controls)
    camera.configure(camera.create_video_configuration(
        main={'size': (video_width, video_height), 'format': 'YUV420'},
        lores={'size': (w, h), 'format': 'YUV420'},
        transform=Transform(hflip=bool(settings.get('rotate_180', False)),
                            vflip=bool(settings.get('rotate_180', False))),
        controls=controls))
    # Scale bitrate to the capture size; a higher resolution uses more storage.
    bitrate = {'640x480': 1_500_000, '1280x720': 2_500_000,
               '1920x1080': 4_500_000}[resolution]
    encoder = H264Encoder(bitrate=bitrate, repeat=True, iperiod=fps)
    circular = CircularOutput2(buffer_duration_ms=int(pre * 1000))
    previous = None
    last_preview = 0
    last_heartbeat = 0
    recording = False
    filename = None
    thumbnail = None
    highest = 0
    part = 0
    session_name = None
    streaming = False
    camera_closed = False
    trigger_source = ''
    settings_version = SETTINGS.stat().st_mtime_ns if SETTINGS.exists() else 0
    last_settings_check = 0
    last_profile_check = 0
    last_schedule_check = 0
    record_allowed = True
    schedule_reason = 'Continuous monitoring'
    last_draft_check = 0
    last_space_check = 0
    low_disk = False
    suppress_detection_until = 0
    # Keep a copy of ordinary controls, so an unsaved test never becomes active.
    ordinary_controls = {k: v for k, v in controls.items() if k != 'FrameRate'}

    def test_unsaved_preview(req):
        nonlocal suppress_detection_until, previous, last_preview, sky_tracker
        token=req['id']
        requested=req.get('profile')
        try:
            if int(req['fps']) != fps:
                raise ValueError('Recording frame rate changed. Save it before testing a profile.')
            overrides = camera_controls(requested, fps, allowed_controls, lc_controls)
            temporary = {k:v for k,v in overrides.items() if k != 'FrameRate'}
            # Camera ownership never leaves this process; no second Picamera2
            # instance is opened. No clip is active when this function runs.
            camera.set_controls(temporary)
            write_status('testing', 'Testing unsaved camera settings; recordings temporarily paused')
            # Keep the encoder running, collecting frames until exposure/AWB settle.
            # 1.5s accommodates several AE/AWB iterations at supported rates.
            finish_at=time.monotonic()+1.5
            while time.monotonic()<finish_at:
                camera.capture_array('lores')
            colour = cv2.cvtColor(camera.capture_array('main'), cv2.COLOR_YUV2BGR_I420)
            if bool(req.get('rotate180')) != bool(settings.get('rotate_180')):
                colour = cv2.rotate(colour, cv2.ROTATE_180)
            target=image_path(token)
            small=cv2.resize(colour, (960, max(1,int(960*video_height/video_width))))
            tempfile=target.with_suffix('.pending')
            try:
                if not cv2.imwrite(str(tempfile)+'.jpg', small, [cv2.IMWRITE_JPEG_QUALITY, 85]):
                    raise RuntimeError('Unable to write preview image')
                Path(str(tempfile)+'.jpg').replace(target)
            finally:
                Path(str(tempfile)+'.jpg').unlink(missing_ok=True)
            write_result(token, 'done', 'Temporary camera profile tested')
        except Exception as exc:
            LOG.exception('Draft preview failed')
            write_result(token, 'error', str(exc))
        finally:
            # On camera errors, let the outer service restart the hardware rather
            # than leaving temporary manual exposure/gain active indefinitely.
            camera.set_controls(ordinary_controls)
            PENDING.unlink(missing_ok=True)
            last_preview=time.monotonic()
            # Allow the pre-roll buffer to refill entirely with ordinary footage.
            suppress_detection_until=last_preview+pre+1
            previous=None
            if sky_tracker is not None:
                sky_tracker.clear()  # start tracking from a clean observation


    def begin_clip(now, *, part_of_same_motion=False, source=''):
        nonlocal filename, thumbnail, recording, highest, part, session_name, trigger_source
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
        if not part_of_same_motion:
            session_name = stamp
            part = 0
        part += 1
        basename = f'event_{session_name}_part{part:02d}'
        filename = RECORDINGS / f'{basename}.mp4'
        thumbnail = THUMBS / f'{basename}.jpg'
        # Use the current low-resolution Y plane as the event's thumbnail.
        cv2.imwrite(str(thumbnail), latest_frame)
        circular.open_output(PyavOutput(str(filename)))
        recording = True
        storm.start(now)
        highest = 0
        trigger_source = source
        LOG.info('Recording started: %s (pre-roll %.1fs, part %d)', filename, pre, part)

    def finish_clip(interrupted=False, storm_stop=False, scheduled=False):
        nonlocal filename, thumbnail, recording, highest, trigger_source
        if not recording:
            return
        circular.close_output()
        recording = False
        storm.finish(time.monotonic())
        # Closing the output writes the MP4 index. Only save valid files.
        if filename.is_file() and filename.stat().st_size > 0:
            label = {'general':'Motion detected', 'sky_lights':'Moving light detected', 'combined':'Motion / light detected'}[profile]
            title = label if part == 1 else f'{label} (part {part})'
            event_id = add_event(title, video=filename.name,
                                 thumbnail=thumbnail.name if thumbnail.is_file() else None,
                                 score=highest, trigger_source=trigger_source,
                                 image_top_bearing=int(settings.get('image_top_bearing', 0)),
                                 camera_elevation=int(settings.get('camera_elevation', 90)),
                                 camera_rotated=int(bool(settings.get('rotate_180', False))),
                                 camera_profile=selected_slot)
            if interrupted or storm_stop or scheduled:
                with connection() as db:
                    note = ('Recording ended for a scheduled observation session.' if scheduled else
                            'Recording ended for manual full-resolution photography.' if interrupted else
                            'Recording ended because event-storm protection temporarily paused detections.')
                    db.execute('UPDATE events SET note=? WHERE id=?', (note,event_id))
            LOG.info('Saved event #%s: %s', event_id, filename)
        else:
            LOG.warning('No valid MP4 was produced for %s', filename)
        filename = None
        thumbnail = None
        highest = 0
        trigger_source = ''

    try:
        # The encoder stays running all the time; this is what gives us pre-roll.
        camera.start_recording(encoder, circular)
        streaming = True
        write_status('running', 'Camera connected; looking for motion')
        LOG.info('Camera/encoder started at %s fps, %s resolution, %s profile, pre-roll %.1fs', fps, resolution, profile, pre)
        while not STOP:
            # The recorder owns the only camera. Scheduled observations claim it
            # atomically, finalise any active MP4, and restore detection on return.
            planned_job = job_due()
            if planned_job:
                LOG.info('Starting observation job #%s: %s', planned_job['id'], planned_job['title'])
                write_status('job-starting', f'Starting {planned_job["title"]}; motion detection suspended')
                if recording:
                    finish_clip(scheduled=True)
                camera.stop_recording()
                streaming = False
                camera.close()
                camera_closed = True
                from observation_jobs import notify as job_notify
                job_notify(planned_job['id'],False,started=True)
                perform_job(planned_job, settings, stopping=lambda:STOP)
                return  # main() reopens camera with original saved configuration
            # A deliberate still request takes priority over a long motion event.
            # Close the current MP4 cleanly, then release the only camera owner.
            job = pending_photo()
            if job:
                LOG.info('Photography request %s: finishing any current clip', job['id'])
                photo_state(job['id'], 'preparing', 'Saving current recording and switching camera')
                write_status('photography', 'Capturing a manual photograph; detection briefly suspended')
                if recording:
                    finish_clip(interrupted=True)
                camera.stop_recording()
                streaming = False
                camera.close()
                camera_closed = True
                capture_still(job, rotate180=settings.get('rotate_180', False))
                # Returning lets main() restore ALL ordinary controls from the
                # unchanged saved settings, including the pre-roll buffer.
                return
            now = time.monotonic()
            # A hard free-space floor prevents a full card from breaking SQLite
            # and the web UI. Nothing is deleted automatically by this guard.
            if now - last_space_check >= 15:
                last_space_check = now
                low_disk = shutil.disk_usage(DATA).free < 1024 ** 3
                if low_disk and recording:
                    finish_clip()
                    planner.active = False
                    planner.hits = 0
                    planner.last_motion = None
                    planner.segment_started = None
                    previous = None
                if low_disk:
                    write_status('storage','Low disk: recordings suspended until at least 1 GB is free')
                    last_heartbeat = now
            if now - last_draft_check >= 0.5:
                last_draft_check = now
                req=pending_request()
                if req and not recording and not planner.active:
                    test_unsaved_preview(req)
                    expire_old_files()
            latest_frame = camera.capture_array('lores')[:h, :w]
            now = time.monotonic()
            if now - last_preview >= 4:
                # Colour capture from the encoded stream, rather than the greyscale
                # lores analysis plane. The recorder and motion logic are unchanged.
                try:
                    colour = cv2.cvtColor(camera.capture_array('main'), cv2.COLOR_YUV2BGR_I420)
                    thumb = cv2.resize(colour, (640, max(1, int(640 * video_height / video_width))))
                    preview_tmp = DATA / 'latest-pending.jpg'
                    if cv2.imwrite(str(preview_tmp), thumb, [cv2.IMWRITE_JPEG_QUALITY, 75]):
                        preview_tmp.replace(DATA / 'latest.jpg')
                    # Admin HD cache is demand-driven: no additional camera capture,
                    # and no full-HD JPEG is written when the Live Camera is idle.
                    # A separate admin-only endpoint refreshes the request timestamp.
                    hd_request = DATA / 'hd-preview-request'
                    try:
                        active = time.time() - hd_request.stat().st_mtime < 35
                    except OSError:
                        active = False
                    if active:
                        hd_tmp = DATA / 'latest-hd-pending.jpg'
                        if cv2.imwrite(str(hd_tmp), colour, [cv2.IMWRITE_JPEG_QUALITY, 91]):
                            hd_tmp.replace(DATA / 'latest-hd.jpg')
                except Exception as exc:
                    LOG.warning('Camera preview capture failed: %s', exc)
                last_preview = now
            # Sunrise or sunset can switch between two camera profiles without
            # a settings save. Finish an active event before restarting.
            if settings.get('camera_profile_mode') == 'solar' and now - last_profile_check >= 30:
                last_profile_check = now
                if effective_slot(settings) != selected_slot and not planner.active and not recording:
                    LOG.info('Sunrise/sunset camera profile changed; restarting camera')
                    write_status('restarting', 'Applying daylight camera profile')
                    return
            if now - last_schedule_check >= 3:
                last_schedule_check = now
                try:
                    record_allowed, schedule_reason = detection_window(settings)
                except (ValueError, TypeError) as exc:
                    record_allowed, schedule_reason = False, 'Invalid schedule: ' + str(exc)[:90]
            # Record both state transitions. Messages go only to administrator accounts.
            if storm_cooling_before and not storm.cooling(now):
                try: storm_recovered(storm_notification_id)
                except Exception: LOG.exception('Could not log storm recovery')
                storm_notification_id = None
                storm_cooling_before = False
            if now - last_heartbeat >= 5:
                if low_disk:
                    state, message = 'storage', 'Low disk: recordings suspended until at least 1 GB is free'
                elif storm.cooling(now) and record_allowed:
                    state, message = 'storm', f'Event-storm protection: new recordings resume in {int(storm.remaining(now)//60)+1} minute(s)'
                elif recording:
                    state, message = 'running', ('Recording current event' if record_allowed else
                                                 'Finishing current recording, then pausing')
                elif record_allowed:
                    state, message = 'running', 'Monitoring for motion'
                else:
                    state, message = ('paused' if settings.get('detection_paused') else 'scheduled'), schedule_reason
                write_status(state, message)
                last_heartbeat = now
            gray = cv2.GaussianBlur(latest_frame, (5, 5), 0)
            if now < suppress_detection_until:
                previous = None
            # The guard is evaluated while a file is actively open; one long
            # sunrise event therefore trips even if it rolls over into segments.
            if storm.check(now):
                if recording:
                    finish_clip(storm_stop=True)
                planner.active = False
                planner.hits = 0
                planner.last_motion = None
                planner.segment_started = None
                previous = None
                if sky_tracker is not None:
                    sky_tracker.clear()
                try: storm_notification_id = storm_activated(storm.cooldown_seconds)
                except Exception: LOG.exception('Could not log storm activation')
                storm_cooling_before = True
                write_status('storm', 'Event-storm protection: too much continuous motion; temporarily cooling down')
                last_heartbeat = now
            if previous is not None:
                general_detected, general_score = False, 0
                sky_detected, sky_score = False, 0
                if profile in ('general', 'combined'):
                    mask = cv2.threshold(cv2.absdiff(previous, gray),
                                         int(settings.get('pixel_threshold', 32)),
                                         255, cv2.THRESH_BINARY)[1]
                    general_score = int(cv2.countNonZero(mask))
                    general_detected = general_score >= int(settings.get('min_changed_pixels', 65))
                if sky_tracker is not None:
                    sky_detected, sky_score = sky_tracker.feed(latest_frame)
                moving = (record_allowed and not low_disk and not storm.cooling(now) and
                          detection_decision(profile, general_detected, sky_detected))
                score = max(general_score, sky_score)
                source = source_for_trigger(profile, general_detected, sky_detected)
                if moving and recording:
                    highest = max(highest, score)
                action = planner.feed(now, moving)
                if action == 'start':
                    begin_clip(now, source=source)
                    highest = score
                elif action == 'stop':
                    finish_clip()
                elif action == 'rollover':
                    # Long uninterrupted events continue immediately as the
                    # next clip; we never wait for a fresh motion trigger.
                    finish_clip()
                    begin_clip(now, part_of_same_motion=True, source=source)
                    highest = score
            previous = gray
            # Read new settings without requiring commands or sudo from the web app.
            # Delay camera restart until the current motion session finishes.
            if now - last_settings_check >= 3:
                last_settings_check = now
                newest = SETTINGS.stat().st_mtime_ns if SETTINGS.exists() else 0
                if newest != settings_version:
                    new_cfg = read_config()
                    camera_keys = ('fps', 'resolution', 'detection_profile', 'sky_brightness',
                                   'sky_min_area', 'sky_max_area', 'sky_confirm_frames',
                                   'sky_min_movement', 'pixel_threshold', 'min_changed_pixels',
                                   'pre_motion_seconds', 'post_motion_seconds', 'max_clip_seconds',
                                   'camera_profile_mode', 'camera_profiles', 'rotate_180')
                    if any(new_cfg.get(k) != settings.get(k) for k in camera_keys):
                        if not planner.active and not recording:
                            LOG.info('Applying recording configuration; restarting camera')
                            write_status('restarting', 'Applying camera and recording settings')
                            return
                        # Finish the current event before changing capture settings.
                    else:
                        settings = new_cfg
                        storm.set_config(settings)
                        settings_version = newest
                        last_schedule_check = 0  # Apply pause/schedule changes promptly.
    finally:
        if streaming:
            if recording:
                # When the camera/output are stopped together, CircularOutput2
                # flushes the last pre-roll window as well. Do not close first.
                try:
                    camera.stop_recording()
                    streaming = False
                finally:
                    recording = False
                    if filename and filename.is_file() and filename.stat().st_size > 0:
                        label = {'general':'Motion detected', 'sky_lights':'Moving light detected', 'combined':'Motion / light detected'}[profile]
                        title = label if part == 1 else f'{label} (part {part})'
                        add_event(title, video=filename.name,
                                  thumbnail=thumbnail.name if thumbnail and thumbnail.is_file() else None,
                                  score=highest, trigger_source=trigger_source,
                                 image_top_bearing=int(settings.get('image_top_bearing', 0)),
                                 camera_elevation=int(settings.get('camera_elevation', 90)),
                                 camera_rotated=int(bool(settings.get('rotate_180', False))),
                                 camera_profile=selected_slot)
            else:
                camera.stop_recording()
        if not camera_closed:
            camera.close()


def main():
    ensure_db()
    jobs_migrate()
    jobs_orphaned()
    jobs_mark_ready()
    try:close_orphaned_on_startup()
    except Exception:LOG.exception('Unable to reconcile storm history on startup')
    while not STOP:
        try:
            settings = read_config()
            write_status('starting', 'Checking for camera')
            run_camera(settings)
        except (KeyboardInterrupt, SystemExit):
            break
        except Exception as exc:
            LOG.exception('Camera/recorder error; retrying in 30 seconds')
            write_status('waiting', f'Camera/recorder unavailable; retrying: {str(exc)[:140]}')
            for _ in range(30):
                if STOP:
                    break
                time.sleep(1)
    write_status('stopped', 'Detector has stopped')


if __name__ == '__main__':
    main()
