"""Private short-lived camera test previews. No saved settings are changed."""
import json
import os
import re
import secrets
import time
from pathlib import Path
from common import DATA

ROOT = DATA / 'draft-previews'
PENDING = ROOT / 'pending.json'
TOKEN = re.compile(r'^[a-f0-9]{32}$')
MAX_AGE = 55  # requests not serviced within this interval are abandoned


def _write(path, data):
    ROOT.mkdir(parents=True, exist_ok=True)
    temporary = ROOT / ('.' + secrets.token_hex(8) + '.tmp')
    try:
        with temporary.open('x') as stream:
            os.chmod(temporary, 0o600)
            json.dump(data, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def result_path(token):
    if not TOKEN.fullmatch(token):
        raise ValueError('Invalid preview ID')
    return ROOT / f'result-{token}.json'


def image_path(token):
    if not TOKEN.fullmatch(token):
        raise ValueError('Invalid preview ID')
    return ROOT / f'frame-{token}.jpg'


def write_result(token, state, message=''):
    _write(result_path(token), {'state':state, 'message':message[:200]})


def enqueue(profile, rotate180, fps):
    ROOT.mkdir(parents=True, exist_ok=True)
    if PENDING.exists():
        try:
            old=json.loads(PENDING.read_text())
            if time.time()-float(old['created']) < MAX_AGE:
                raise ValueError('Another preview is waiting for the camera. Please wait for it to finish.')
        except (OSError, KeyError, TypeError, json.JSONDecodeError):
            pass
        PENDING.unlink(missing_ok=True)
    token=secrets.token_hex(16)
    _write(PENDING, {'id':token,'created':time.time(),'profile':profile,
                     'rotate180':bool(rotate180), 'fps':int(fps)})
    return token


def pending_request():
    if not PENDING.exists():
        return None
    try:
        data=json.loads(PENDING.read_text())
        token=data['id']
        if not TOKEN.fullmatch(token):
            raise ValueError('Invalid preview request')
        if time.time() - float(data['created']) >= MAX_AGE:
            write_result(token, 'error', 'Preview expired while waiting for the camera. Try again when recording has finished.')
            PENDING.unlink(missing_ok=True)
            return None
        return data
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        PENDING.unlink(missing_ok=True)
        return None


def expire_old_files():
    # No long-term storage or growing pile of private draft images.
    if not ROOT.exists():
        return
    cutoff=time.time()-3600
    for path in ROOT.glob('*'):
        if path == PENDING or not path.is_file():
            continue
        if path.stat().st_mtime < cutoff:
            path.unlink(missing_ok=True)
