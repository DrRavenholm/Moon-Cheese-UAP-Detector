"""Scheduled recording / time-lapse jobs. Camera ownership remains exclusively in detector.py.

State machine is persisted in SQLite so browser reloads, reconnects, and Pi reboots
cannot accidentally create duplicate sessions. Jobs are private until explicitly published.
"""
import csv
import io
import json
import math
import os
import shutil
import sqlite3
import subprocess
import time
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from time_display import schedule_utc, valid_zone

from common import DATA, connection, now_iso, read_config, write_status

ROOT = DATA / 'observation-jobs'
READY = DATA / 'jobs-engine-ready'
KINDS = ('scheduled_video', 'timelapse')
MODES = ('basic', 'advanced')
TERMINAL = ('complete', 'failed', 'cancelled', 'missed', 'interrupted')
ACTIVE = ('capturing', 'rendering', 'archiving', 'finalising')


class Cancelled(Exception):
    pass

class Interrupted(Exception):
    pass


def engine_ready():
    try:
        pid=int(READY.read_text().strip())
        os.kill(pid,0)
        return pid>0
    except (OSError,ValueError):
        return False


def mark_ready():
    READY.parent.mkdir(parents=True,exist_ok=True)
    READY.write_text(str(os.getpid()))


def migrate():
    ROOT.mkdir(parents=True, exist_ok=True)
    with connection() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS observation_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL CHECK(kind IN ('scheduled_video','timelapse')),
            mode TEXT NOT NULL CHECK(mode IN ('basic','advanced')),
            title TEXT NOT NULL, note TEXT NOT NULL DEFAULT '',
            start_utc TEXT NOT NULL, tzname TEXT NOT NULL,
            duration_seconds INTEGER NOT NULL,
            profile_slot TEXT NOT NULL DEFAULT 'auto',
            interval_seconds INTEGER NOT NULL DEFAULT 15,
            output_fps INTEGER NOT NULL DEFAULT 25,
            exposure_us INTEGER NOT NULL DEFAULT 1000000,
            gain REAL NOT NULL DEFAULT 4,
            manual_exposure INTEGER NOT NULL DEFAULT 0,
            focus_mode TEXT NOT NULL DEFAULT 'manual',
            lens_position REAL NOT NULL DEFAULT 0,
            awb_enabled INTEGER NOT NULL DEFAULT 1,
            red_gain REAL NOT NULL DEFAULT 1,
            blue_gain REAL NOT NULL DEFAULT 1,
            brightness REAL NOT NULL DEFAULT 0,
            contrast REAL NOT NULL DEFAULT 1,
            saturation REAL NOT NULL DEFAULT 1,
            status TEXT NOT NULL DEFAULT 'queued',
            completed_frames INTEGER NOT NULL DEFAULT 0,
            planned_frames INTEGER NOT NULL DEFAULT 0,
            started_utc TEXT, finished_utc TEXT, phase TEXT NOT NULL DEFAULT '',
            error TEXT NOT NULL DEFAULT '',
            pinned INTEGER NOT NULL DEFAULT 0, public INTEGER NOT NULL DEFAULT 0,
            public_note INTEGER NOT NULL DEFAULT 0, created_by INTEGER NOT NULL,
            cancel_requested INTEGER NOT NULL DEFAULT 0,
            created_utc TEXT NOT NULL, updated_utc TEXT NOT NULL
        )''')
        db.execute('CREATE INDEX IF NOT EXISTS idx_jobs_start ON observation_jobs(status,start_utc)')


def _parse_local(start, timezone_name):
    return schedule_utc(start,timezone_name)


def create(form, user_id, now=None):
    """Validate and queue job atomically, rejecting overlaps and low-space plans."""
    migrate()
    if not engine_ready():
        raise ValueError('Scheduling will be available after the camera recorder finishes its safe upgrade restart.')
    now = now or datetime.now(timezone.utc)
    kind = form.get('kind', '')
    mode = form.get('mode', 'basic')
    if kind not in KINDS or mode not in MODES:
        raise ValueError('Invalid recording type.')
    if kind == 'scheduled_video':
        mode = 'basic'
    profile_slot=str(form.get('profile_slot','auto'))
    if profile_slot not in ('auto','day','night','custom1','custom2'):raise ValueError('Unsupported camera profile.')
    title = str(form.get('title', '')).strip()[:120]
    if not title:
        raise ValueError('Please enter a name.')
    # The saved detector timezone is authoritative; never trust a browser-supplied override.
    tzname = str(read_config().get('schedule_timezone') or 'Europe/London')
    valid_zone(tzname)
    start = _parse_local(form.get('start', ''), tzname)
    if not (now - timedelta(seconds=30) <= start <= now + timedelta(days=366)):
        raise ValueError('Choose a future start time within one year.')
    try:
        duration = int(form.get('duration_minutes', 60)) * 60
        interval = int(form.get('interval_seconds', 15))
        fps = int(form.get('output_fps', 25))
        exposure_us = int(round(float(form.get('exposure_ms', 1000)) * 1000))
        gain = float(form.get('gain', 4))
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError('Enter valid numeric recording settings.') from exc
    if not 60 <= duration <= 8 * 3600:
        raise ValueError('Duration must be between 1 minute and 8 hours.')
    if not 5 <= interval <= 3600 or fps not in (15, 24, 25, 30):
        raise ValueError('Choose a supported interval and output frame rate.')
    manual = (form.get('exposure_mode') == 'manual' or form.get('manual_exposure') == '1') and mode == 'advanced' and kind == 'timelapse'
    if manual and not 100 <= exposure_us <= 112000000:
        raise ValueError('Exposure / shutter must be between 0.1 and 112000 milliseconds.')
    if not math.isfinite(gain) or not 1 <= gain <= 16:
        raise ValueError('Analogue gain must be between 1 and 16×.')
    focus_mode = str(form.get('focus_mode','infinity')) if mode == 'advanced' else 'auto'
    if focus_mode not in ('auto','infinity','manual'):raise ValueError('Choose a valid focus mode.')
    try:
        lens=float(form.get('lens_position',0))
        red_gain=float(form.get('red_gain',1))
        blue_gain=float(form.get('blue_gain',1))
        brightness=float(form.get('brightness',0))
        contrast=float(form.get('contrast',1))
        saturation=float(form.get('saturation',1))
    except (ValueError,TypeError):raise ValueError('Invalid advanced camera setting.')
    awb_enabled = form.get('awb_enabled','1') == '1'
    if not all(math.isfinite(v) for v in (lens,red_gain,blue_gain,brightness,contrast,saturation)) or not (0 <= lens <= 32 and 0 <= red_gain <= 8 and 0 <= blue_gain <= 8 and
            -1 <= brightness <= 1 and 0 <= contrast <= 4 and 0 <= saturation <= 4):
        raise ValueError('Advanced camera setting outside the supported range.')
    if manual and exposure_us / 1000000 + 1.5 >= interval:
        raise ValueError('Exposure must leave at least 1.5 seconds for camera processing between frames.')
    frames = (duration - 1) // interval + 1 if kind == 'timelapse' else 0
    if kind == 'timelapse' and frames < 2:
        raise ValueError('Choose an interval that captures at least two frames during the session.')
    if frames > 3000:
        raise ValueError('Too many frames for one session (maximum 3000).')
    from storage_estimator import estimate_space
    space = estimate_space(frames=frames,duration=duration,kind=kind)
    if not space['fits']:
        raise ValueError('Not enough free storage: estimated job needs '
                         f"{space['bytes']/1024**3:.1f} GiB plus a 2 GiB safety reserve; "
                         f"only {space['available']/1024**3:.1f} GiB is available. "
                         'Reduce the duration, increase the interval or free space in Storage Management.')
    end = start + timedelta(seconds=duration)
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        previous = db.execute('''SELECT id, start_utc, duration_seconds FROM observation_jobs
            WHERE status IN ('queued','capturing','rendering','archiving','finalising')''').fetchall()
        for job in previous:
            job_start = datetime.fromisoformat(job['start_utc'])
            job_end = job_start + timedelta(seconds=job['duration_seconds'])
            # Reserve a modest wrap-up gap for mode switching and output processing.
            if start < job_end + timedelta(minutes=15) and end + timedelta(minutes=15) > job_start:
                raise ValueError(f'The camera is already booked for job #{job["id"]}. Allow 15 minutes between jobs.')
        stamp = now.isoformat(timespec='seconds')
        db.execute('''INSERT INTO observation_jobs
            (kind,mode,title,start_utc,tzname,duration_seconds,interval_seconds,output_fps,
             exposure_us,gain,manual_exposure,profile_slot,focus_mode,lens_position,awb_enabled,
             red_gain,blue_gain,brightness,contrast,saturation,planned_frames,
             created_by,created_utc,updated_utc)
             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (kind,mode,title,start.isoformat(timespec='seconds'),tzname,duration,
             interval,fps,exposure_us,gain,int(manual),profile_slot,focus_mode,lens,int(awb_enabled),
             red_gain,blue_gain,brightness,contrast,saturation,frames,user_id,stamp,stamp))
        job_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
    return job_id


def item(job_id):
    with connection() as db:
        r = db.execute('SELECT * FROM observation_jobs WHERE id=?', (int(job_id),)).fetchone()
    return dict(r) if r else None


def due(now=None):
    """Claim only timely jobs; late starts become missed and notify admins."""
    now=now or datetime.now(timezone.utc)
    missed=[]; claimed=None
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        rows=list(db.execute("SELECT id,start_utc FROM observation_jobs WHERE status='queued' ORDER BY start_utc"))
        for row in rows:
            start=datetime.fromisoformat(row['start_utc'])
            if (now-start).total_seconds()>120:
                db.execute("UPDATE observation_jobs SET status='missed',error='Start time passed while camera was unavailable',finished_utc=?,updated_utc=? WHERE id=?",
                           (now.isoformat(),now.isoformat(),row['id']))
                missed.append(row['id'])
            elif start<=now and claimed is None:
                if db.execute("UPDATE observation_jobs SET status='capturing',phase='Starting camera',started_utc=?,updated_utc=? WHERE id=? AND status='queued'",
                              (now.isoformat(),now.isoformat(),row['id'])).rowcount:
                    claimed=dict(db.execute('SELECT * FROM observation_jobs WHERE id=?',(row['id'],)).fetchone())
    for jid in missed: notify(jid,False)
    return claimed


def orphaned():
    """On recorder startup, preserve unfinished files and report interrupted jobs."""
    migrate()
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        jobs=[r['id'] for r in db.execute("SELECT id FROM observation_jobs WHERE status IN ('capturing','rendering','archiving','finalising')")]
        if jobs:
            db.execute("""UPDATE observation_jobs SET status='interrupted',
                phase='Interrupted; partial media preserved',
                error='Interrupted by detector shutdown or restart; available source files retained',
                finished_utc=?,updated_utc=?
                WHERE status IN ('capturing','rendering','archiving','finalising')""",(now_iso(),now_iso()))
    for job_id in jobs:
        notify(job_id,False)
    return len(jobs)


def update(job_id, status=None, phase=None, frames=None, error=None):
    fields = ['updated_utc=?']; values = [now_iso()]
    if status is not None: fields.append('status=?'); values.append(status)
    if phase is not None: fields.append('phase=?'); values.append(phase)
    if frames is not None: fields.append('completed_frames=?'); values.append(int(frames))
    if error is not None: fields.append('error=?'); values.append(str(error)[:500])
    if status in TERMINAL: fields.append('finished_utc=?'); values.append(now_iso())
    with connection() as db:
        db.execute('UPDATE observation_jobs SET '+','.join(fields)+' WHERE id=?', (*values,int(job_id)))


def cancelled(job_id):
    with connection() as db:
        row = db.execute('SELECT cancel_requested FROM observation_jobs WHERE id=?',(job_id,)).fetchone()
    return not row or bool(row[0])


def cancel(job_id):
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        job = db.execute('SELECT status FROM observation_jobs WHERE id=?',(job_id,)).fetchone()
        if not job: raise ValueError('Recording job not found.')
        if job['status'] == 'queued':
            db.execute("UPDATE observation_jobs SET status='cancelled',finished_utc=?,updated_utc=? WHERE id=?",(now_iso(),now_iso(),job_id))
        elif job['status'] in ACTIVE:
            db.execute('UPDATE observation_jobs SET cancel_requested=1 WHERE id=?',(job_id,))
        else:
            raise ValueError('Only pending or active jobs can be cancelled.')


def set_meta(job_id, title, note, pinned, public, public_note):
    title = (title or '').strip()[:120]
    note = (note or '')[:8000]
    if not title: raise ValueError('Please provide a title.')
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        row=db.execute('SELECT status FROM observation_jobs WHERE id=?',(job_id,)).fetchone()
        if not row: raise ValueError('Job not found.')
        if public and row['status']!='complete':
            raise ValueError('Only completed recordings can be shared publicly.')
        db.execute('UPDATE observation_jobs SET title=?,note=?,pinned=?,public=?,public_note=?,updated_utc=? WHERE id=?',
                   (title,note,int(bool(pinned)),int(bool(public)),int(bool(public and public_note)),now_iso(),job_id))


def job_dir(job_id):
    return ROOT / str(int(job_id))


def files(job_id):
    """Only fixed names inside a numeric job directory; no user paths."""
    directory=job_dir(job_id)
    if not directory.is_dir() or directory.is_symlink(): return []
    return sorted(p for p in (directory/'video').glob('segment-*.mp4') if p.is_file() and not p.is_symlink()) if (directory/'video').is_dir() else []


def download(job_id, name):
    allowed = ('timelapse.mp4','source-frames.zip','thumbnail.jpg')
    if name in allowed:
        path=job_dir(job_id)/name
    elif name.startswith('segment-') and name.endswith('.mp4') and len(name)==18 and name[8:14].isdigit():
        path=job_dir(job_id)/'video'/name
    else:
        return None
    if path.is_file() and not path.is_symlink(): return path
    return None


def delete(job_id, source_only=False):
    """Confirm protections in writer transaction before removing anything."""
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        row=db.execute('SELECT * FROM observation_jobs WHERE id=?',(job_id,)).fetchone()
        if not row or row['status'] not in TERMINAL or row['pinned'] or row['public']:
            return False
        if source_only:
            if row['kind']!='timelapse': return False
            # Delete only the archive, not the final MP4.
            archive=download(job_id,'source-frames.zip')
            if archive: archive.unlink()
            return True
        if db.execute('DELETE FROM observation_jobs WHERE id=? AND pinned=0 AND public=0',(job_id,)).rowcount:
            directory=job_dir(job_id)
            if directory.is_dir() and not directory.is_symlink(): shutil.rmtree(directory)
            return True
    return False


def active():
    with connection() as db:
        row = db.execute("SELECT * FROM observation_jobs WHERE status IN ('capturing','rendering','archiving','finalising') ORDER BY id DESC LIMIT 1").fetchone()
    return dict(row) if row else None


def busy_soon(now=None, grace_seconds=180):
    now=now or datetime.now(timezone.utc)
    with connection() as db:
        active_row=db.execute("SELECT 1 FROM observation_jobs WHERE status IN ('capturing','rendering','archiving','finalising') LIMIT 1").fetchone()
        next_row=db.execute("SELECT start_utc FROM observation_jobs WHERE status='queued' ORDER BY start_utc LIMIT 1").fetchone()
    return bool(active_row or (next_row and datetime.fromisoformat(next_row['start_utc']) <= now+timedelta(seconds=grace_seconds)))


def notify(job_id, success, started=False):
    """Local admin notices; never email or push."""
    try:
        from notifications import create_notice, migrate as migrate_notices
        migrate_notices()
        j=item(job_id)
        at=datetime.now(timezone.utc)
        status = 'started' if started else (j['status'] if j else ('complete' if success else 'failed'))
        with connection() as db:
            users=db.execute("SELECT id FROM users WHERE enabled=1 AND role='admin'").fetchall()
            for user in users:
                create_notice(db,user['id'],'digest' if started else ('recovery' if success else 'fault'),
                              f'observation-job:{job_id}:{status}',
                              f'{"Started" if started else "Completed" if success else "Attention"}: {j["title"] if j else "Observation"}',
                              f'Job #{job_id} · {status}. Open Scheduled Video or Time-lapse Studio to review.',at)
    except Exception:
        import logging
        logging.exception('Could not create local observation job notification')


def verify_video(path):
    if not path.is_file() or path.stat().st_size < 1024:
        raise RuntimeError('Output video is empty or missing.')
    if shutil.which('ffprobe'):
        result=subprocess.run(['ffprobe','-v','error','-select_streams','v:0',
                                '-show_entries','stream=width,height','-of','csv=p=0',str(path)],
                               capture_output=True,text=True,timeout=30)
        if result.returncode or not result.stdout.strip():
            raise RuntimeError('Video did not pass media verification.')


def complete_timelapse(job, frame_dir, stopping=lambda:False):
    """Create verified MP4 + source ZIP before deleting loose frames."""
    jid=job['id']
    root=job_dir(jid)
    images=sorted(frame_dir.glob('frame_*.jpg'))
    if len(images)<2: raise RuntimeError('Need at least two captured frames to render a time-lapse.')
    if not shutil.which('ffmpeg'): raise RuntimeError('ffmpeg is not installed.')
    update(jid,'rendering','Rendering MP4 video')
    write_status('job-rendering',f'Time-lapse #{jid}: rendering {len(images)} frames')
    target=root/'timelapse.partial.mp4'
    # libx264 is supported by the Raspberry Pi OS ffmpeg package. Serial encode
    # with low threads to avoid exhausting the 2 GB Pi 4 during long sessions.
    command=['ffmpeg','-hide_banner','-loglevel','error','-y','-threads','2',
             '-framerate',str(job['output_fps']),'-i',str(frame_dir/'frame_%06d.jpg'),
             '-vf','scale=w=1920:h=1080:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=1920:1080:(ow-iw)/2:(oh-ih)/2',
             '-c:v','libx264','-preset','veryfast','-crf','24','-pix_fmt','yuv420p',
             '-movflags','+faststart',str(target)]
    process=subprocess.Popen(command,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    try:
        began=time.monotonic()
        while process.poll() is None:
            if stopping():raise Interrupted('Detector shutting down during rendering; source frames preserved.')
            if cancelled(jid):raise Cancelled('Rendering cancelled; source frames preserved.')
            if time.monotonic()-began>7200:
                raise RuntimeError('Rendering timed out; source frames preserved.')
            write_status('job-rendering',f'Time-lapse #{jid}: rendering video')
            time.sleep(5)
        if process.returncode:
            failure=process.stderr.read(2048).decode('utf-8','replace')
            raise RuntimeError('Time-lapse rendering failed: '+failure[:450])
    finally:
        if process.poll() is None:
            process.terminate()
            try:process.wait(timeout=10)
            except subprocess.TimeoutExpired:process.kill();process.wait()
        process.stderr.close()
    verify_video(target)
    target.replace(root/'timelapse.mp4')
    update(jid,'archiving','Creating private photograph archive')
    write_status('job-archiving',f'Time-lapse #{jid}: archiving original photographs')
    zip_tmp=root/'source-frames.partial.zip'
    with zipfile.ZipFile(zip_tmp,'w',compression=zipfile.ZIP_STORED,allowZip64=True) as output:
        for i,photo in enumerate(images):
            if stopping():raise Interrupted('Shutdown during archiving; original frames preserved.')
            if cancelled(jid):raise Cancelled('Stopped during archiving; original frames preserved')
            output.write(photo,photo.name)
            if i%25==0:
                write_status('job-archiving',f'Time-lapse #{jid}: archiving {i+1}/{len(images)} frames')
        metadata={'job_id':jid,'title':job['title'],'time_utc':now_iso(),
                  'capture_interval_seconds':job['interval_seconds'],
                  'output_fps':job['output_fps'],'exposure_us':job['exposure_us'],
                  'gain':job['gain'],'source_frames':len(images)}
        output.writestr('capture-settings.json', json.dumps(metadata,indent=2))
        manifest=frame_dir/'capture-times.csv'
        if manifest.exists():output.write(manifest,'capture-times.csv')
    with zipfile.ZipFile(zip_tmp) as archive:
        if archive.testzip() is not None or len(archive.namelist()) != len(images)+(2 if (frame_dir/'capture-times.csv').is_file() else 1):
            raise RuntimeError('Source photograph archive failed verification.')
    zip_tmp.replace(root/'source-frames.zip')
    # Both permanent outputs verified. The source images stay OUT of the photo gallery.
    shutil.rmtree(frame_dir)


def _make_thumb_from_frame(frame, path):
    import cv2
    h,w=frame.shape[:2]
    ratio=min(420/w,240/h,1)
    small=cv2.resize(frame,(max(1,int(w*ratio)),max(1,int(h*ratio))))
    cv2.imwrite(str(path),small,[cv2.IMWRITE_JPEG_QUALITY,80])


def _disk_ok():
    if shutil.disk_usage(DATA).free < 1024**3:
        raise RuntimeError('Less than 1 GB free; capture stopped to protect the Pi.')


def perform(job, settings, stopping=lambda:False):
    """Called synchronously ONLY by the detector after it releases its camera."""
    jid=job['id']
    root=job_dir(jid)
    root.mkdir(parents=True,exist_ok=True)
    camera=None
    try:
        from picamera2 import Picamera2
        from libcamera import Transform, controls as lc_controls
        import cv2
        _disk_ok()
        camera=Picamera2()
        rotate=bool(settings.get('rotate_180',False))
        transform=Transform(hflip=rotate,vflip=rotate)
        if job['kind']=='scheduled_video':
            from common import RESOLUTIONS
            video_size=RESOLUTIONS.get(settings.get('resolution'),(1280,720))
            from camera_profiles import selected_profile, camera_controls, get_profiles
            slot=job['profile_slot']
            if slot=='auto': _,profile=selected_profile(settings)
            else: profile=get_profiles(settings)[slot]
            cam_controls=camera_controls(profile,int(settings.get('fps',15)),camera.camera_controls,lc_controls)
            config=camera.create_video_configuration(main={'size':video_size,'format':'YUV420'},
                       lores={'size':(320,240),'format':'YUV420'}, transform=transform,controls=cam_controls)
        else:
            dims=camera.sensor_resolution
            config=camera.create_still_configuration(main={'size':tuple(dims)},transform=transform)
        camera.configure(config)
        if job['kind']=='timelapse':
            controls={'AeEnable': not bool(job['manual_exposure']), 'AwbEnable':True}
            # Preserve enough time for readout and interval scheduling.
            interval_max=int(max(0.1,job['interval_seconds']-1.5)*1000000)
            if 'FrameDurationLimits' in camera.camera_controls:
                controls['FrameDurationLimits']=(100,interval_max)
            available=camera.camera_controls
            def supported(key,value):
                if key in available: controls[key]=value
            supported('AwbEnable',bool(job['awb_enabled']) if job['mode']=='advanced' else True)
            if job['mode']=='advanced' and not job['awb_enabled']:supported('ColourGains',(float(job['red_gain']),float(job['blue_gain'])))
            if job['mode']=='advanced':
                for key,column in [('Brightness','brightness'),('Contrast','contrast'),('Saturation','saturation')]:
                    supported(key,float(job[column]))
            if job['mode']=='advanced' and job['manual_exposure']:
                supported('ExposureTime',int(job['exposure_us']))
                supported('AnalogueGain',float(job['gain']))
                supported('FrameDurationLimits',(int(job['exposure_us'])+10000,min(interval_max,int(job['exposure_us'])+100000)))
            # Manual infinity focus for sky photographs; other cases use camera's
            # default autofocus. Camera reports supported controls dynamically.
            if 'AfMode' in camera.camera_controls:
                if job['mode']=='basic' or job['focus_mode']=='auto':
                    controls['AfMode']=lc_controls.AfModeEnum.Continuous
                else:
                    controls['AfMode']=lc_controls.AfModeEnum.Manual
                    if 'LensPosition' in available:
                        controls['LensPosition']=(0.0 if job['focus_mode']=='infinity' else float(job['lens_position']))
            camera.set_controls(controls)
        if job['kind']=='scheduled_video':
            from picamera2.encoders import H264Encoder
            from picamera2.outputs import PyavOutput
            vdir=root/'video';vdir.mkdir(exist_ok=True)
            end=time.monotonic()+job['duration_seconds']
            segment=0
            while time.monotonic()<end:
                if stopping():raise Interrupted('Detector shutting down; partial files preserved.')
                if cancelled(jid): raise Cancelled('Stopped by administrator')
                _disk_ok()
                segment+=1
                output=vdir/f'segment-{segment:06d}.mp4'
                encoder=H264Encoder(bitrate=4500000,repeat=True,iperiod=int(settings.get('fps',15)))
                camera.start_recording(encoder,PyavOutput(str(output)))
                try:
                    segment_end=min(end,time.monotonic()+300)
                    while time.monotonic()<segment_end:
                        if stopping():raise Interrupted('Detector shutting down; partial files preserved.')
                        if cancelled(jid): raise Cancelled('Stopped by administrator')
                        _disk_ok()
                        update(jid,phase=f'Recording segment {segment}')
                        write_status('job-video',f'Scheduled video #{jid}: recording segment {segment}')
                        camera.capture_array('lores')
                        time.sleep(0.25)
                finally:
                    camera.stop_recording()
                verify_video(output)
                if segment==1:
                    capture=cv2.VideoCapture(str(output))
                    ok,image=capture.read();capture.release()
                    if ok: _make_thumb_from_frame(image,root/'thumbnail.jpg')
            update(jid,'complete','Finished recording')
        else:
            frame_dir=root/'frames';frame_dir.mkdir(exist_ok=True)
            end=time.monotonic()+job['duration_seconds']
            capture_number=0
            camera.start()
            next_at=time.monotonic()
            while time.monotonic()<end:
                if stopping():raise Interrupted('Detector shutting down; partial files preserved.')
                if cancelled(jid): raise Cancelled('Stopped by administrator')
                _disk_ok()
                delay=next_at-time.monotonic()
                if delay>0: time.sleep(min(delay,0.5));continue
                capture_number+=1
                path=frame_dir/f'frame_{capture_number:06d}.jpg'
                camera.capture_file(str(path))
                with (frame_dir/'capture-times.csv').open('a',encoding='utf-8') as manifest:
                    manifest.write(f'{path.name},{now_iso()}\n')
                if capture_number==1:
                    thumb=cv2.imread(str(path))
                    if thumb is not None: _make_thumb_from_frame(thumb,root/'thumbnail.jpg')
                update(jid,frames=capture_number,phase=f'Capturing frame {capture_number}/{job["planned_frames"]}')
                write_status('job-timelapse',f'Time-lapse #{jid}: frame {capture_number}/{job["planned_frames"]}')
                next_at+=job['interval_seconds']
            camera.stop();camera.close();camera=None
            complete_timelapse(job,frame_dir,stopping=stopping)
            update(jid,'complete','Finished video and source archive')
        notify(jid,True)
    except Interrupted as exc:
        update(jid,'interrupted','Interrupted by service shutdown',error=str(exc))
        notify(jid,False)
    except Cancelled as exc:
        update(jid,'cancelled','Stopped by administrator',error=str(exc))
        notify(jid,False)
    except Exception as exc:
        import logging
        logging.exception('Scheduled observation job #%s failed',jid)
        update(jid,'failed','Capture or processing failed',error=str(exc))
        notify(jid,False)
    finally:
        if camera:
            try: camera.stop()
            except Exception: pass
            try: camera.close()
            except Exception: pass
        # main() now restores the normal detector camera configuration.
        write_status('restarting','Restoring normal motion detection after scheduled observation')
