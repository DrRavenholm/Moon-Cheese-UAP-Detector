"""One-camera-owner IPC for deliberate full resolution still captures.

Dashboard merely queues a request. The detector owns the camera, closes its
video MP4 and releases the sensor before this module opens a still pipeline.
"""
import json
import math
import os
import secrets
import time
import shutil
from datetime import datetime, timezone
from pathlib import Path
from common import DATA

ROOT = DATA / 'photography'
QUEUE = ROOT / 'request.json'
TOKEN_LENGTH = 32
MAX_PENDING_AGE = 240
MAX_EXPOSURE_MS = 112_000


def _atomic_json(path, item):
    ROOT.mkdir(mode=0o750, parents=True, exist_ok=True)
    tmp = ROOT / ('.' + secrets.token_hex(12))
    try:
        with tmp.open('x') as f:
            os.chmod(tmp, 0o600)
            json.dump(item, f)
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def validate(raw):
    """Whitelist and bound all camera controls; never accept file paths."""
    raw = dict(raw)
    def number(name, default, lower, upper):
        try: v = float(raw.get(name, default))
        except (ValueError, TypeError): raise ValueError(f'Invalid {name}')
        if not math.isfinite(v) or not lower <= v <= upper:
            raise ValueError(f'{name} must be between {lower} and {upper}')
        return v
    mode = str(raw.get('mode', 'auto'))
    if mode not in ('auto', 'manual'): raise ValueError('Choose Auto or Manual exposure')
    fmt = str(raw.get('format', 'jpg')).lower()
    if fmt not in ('jpg','png'): raise ValueError('Choose JPEG or PNG')
    focus = str(raw.get('focus','infinity'))
    if focus not in ('infinity','auto'): raise ValueError('Choose Infinity or Auto focus')
    awb = str(raw.get('awb','auto'))
    if awb not in ('auto','manual'): raise ValueError('Choose Auto or Manual white balance')
    return dict(mode=mode, format=fmt, focus=focus, awb=awb,
                exposure_ms=number('exposure_ms',1000,0.1,MAX_EXPOSURE_MS),
                gain=number('gain',4,1,16),
                brightness=number('brightness',0,-1,1),
                contrast=number('contrast',1,0.25,4),
                saturation=number('saturation',1,0,3),
                red_gain=number('red_gain',1.5,0.1,8),
                blue_gain=number('blue_gain',1.5,0.1,8))


def output_path(token, fmt):
    if len(token)!=TOKEN_LENGTH or any(c not in '0123456789abcdef' for c in token):
        raise ValueError('Invalid capture reference')
    if fmt not in ('jpg','png'): raise ValueError('Invalid format')
    return ROOT / f'photo-{token}.{fmt}'


def result_path(token):
    output_path(token,'jpg')
    return ROOT / f'result-{token}.json'


def queue_capture(values):
    config = validate(values)
    ROOT.mkdir(mode=0o750, parents=True, exist_ok=True)
    if QUEUE.exists():
        try:
            old=json.loads(QUEUE.read_text())
            if time.time()-float(old.get('created',0)) < MAX_PENDING_AGE:
                raise ValueError('Another photograph is already queued')
        except (json.JSONDecodeError, OSError, TypeError):
            pass
    token=secrets.token_hex(16)
    job={'id':token,'created':time.time(),'params':config}
    # Single-request producer: exclusive create, no overwrite of a concurrent request.
    if QUEUE.exists():
        try:
            old=json.loads(QUEUE.read_text())
            if time.time()-float(old.get('created',0)) >= MAX_PENDING_AGE:
                QUEUE.unlink(missing_ok=True)
        except (OSError, ValueError, TypeError):
            QUEUE.unlink(missing_ok=True)
    try:
        with QUEUE.open('x') as f:
            os.chmod(QUEUE,0o600)
            json.dump(job,f)
    except FileExistsError:
        raise ValueError('Another photograph request is pending')
    _atomic_json(result_path(token),{'state':'queued','message':'Waiting for camera'})
    return token


def pending():
    if not QUEUE.exists(): return None
    try:
        job=json.loads(QUEUE.read_text())
        if time.time()-float(job['created'])>MAX_PENDING_AGE:
            QUEUE.unlink(missing_ok=True)
            _atomic_json(result_path(job['id']),{'state':'error','message':'Camera did not accept the request in time'})
            return None
        return job
    except (ValueError, KeyError, OSError):
        QUEUE.unlink(missing_ok=True)
        return None


def state(token, status, message='', **extra):
    _atomic_json(result_path(token), {'state':status,'message':str(message)[:220],**extra})


def capture_still(job, rotate180=False):
    """Called ONLY after the detector has closed and released its camera."""
    from picamera2 import Picamera2
    from libcamera import Transform, controls as lc_controls
    token=job['id']
    p=validate(job['params'])
    outfile=output_path(token,p['format'])
    cam=None
    try:
        # Avoid worsening a nearly-full card with a large still capture.
        minimum=1024**3 if p['format']=='png' else 512*1024**2
        if shutil.disk_usage(ROOT).free < minimum:
            raise RuntimeError('Not enough free disk space for a full-resolution photograph')
        state(token,'preparing','Preparing photography camera')
        cam=Picamera2()
        native=cam.sensor_resolution
        if not native or native[0]<100 or native[1]<100:
            raise RuntimeError('Camera sensor resolution unavailable')
        allowed=cam.camera_controls
        knobs={'Brightness':p['brightness'],'Contrast':p['contrast'],'Saturation':p['saturation']}
        if p['mode']=='manual':
            us=int(p['exposure_ms']*1000)
            knobs.update(AeEnable=False,ExposureTime=us,AnalogueGain=p['gain'],
                         FrameDurationLimits=(us, max(us, 200000)))
        else:
            knobs.update(AeEnable=True)
        if p['awb']=='manual':
            knobs.update(AwbEnable=False,ColourGains=(p['red_gain'],p['blue_gain']))
        else: knobs.update(AwbEnable=True)
        if 'AfMode' in allowed:
            knobs['AfMode']=(lc_controls.AfModeEnum.Manual if p['focus']=='infinity'
                              else lc_controls.AfModeEnum.Continuous)
        if p['focus']=='infinity' and 'LensPosition' in allowed:
            knobs['LensPosition']=0.0
        missing=[k for k in ('AeEnable','ExposureTime','AnalogueGain') if p['mode']=='manual' and k not in allowed]
        if missing: raise RuntimeError('Manual photo controls unavailable: '+', '.join(missing))
        knobs={k:v for k,v in knobs.items() if k in allowed}
        cam.configure(cam.create_still_configuration(
            main={'size': tuple(native)},
            transform=Transform(hflip=bool(rotate180),vflip=bool(rotate180)),
            controls=knobs))
        cam.start()
        # Status begins after camera start/configuration, not while queued or switching.
        # Picamera2 captures asynchronously to the status reader; this duration is
        # an estimate, not proof that sensor exposure started at this exact instant.
        if p['mode']=='manual':
            state(token,'exposing','Manual exposure in progress',
                  exposure_seconds=p['exposure_ms']/1000.0,
                  exposure_started_epoch=time.time())
        else:
            state(token,'capturing','Automatic photograph in progress')
        # Starting the still stream with manual controls allows capture_file
        # to wait for a full exposure. No second camera owner is created.
        cam.capture_file(str(outfile))
        state(token,'saving','Saving photograph')
        if not outfile.is_file() or outfile.stat().st_size==0:
            raise RuntimeError('Camera did not save the photograph')
        state(token,'done','Photograph saved',format=p['format'],width=int(native[0]),height=int(native[1]),
              bytes=outfile.stat().st_size,created_utc=datetime.now(timezone.utc).isoformat())
    except Exception as exc:
        outfile.unlink(missing_ok=True)
        state(token,'error',str(exc))
    finally:
        if cam is not None:
            try: cam.stop()
            except Exception: pass
            try: cam.close()
            except Exception: pass
        QUEUE.unlink(missing_ok=True)
