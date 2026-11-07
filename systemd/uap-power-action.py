#!/usr/bin/python3
"""Dedicated privileged helper, activated only by a root-owned systemd unit.

The dashboard itself retains NoNewPrivileges=true. This helper recognises only
reboot/shutdown and refuses to power off if it cannot stop the recorder safely.
"""
import json, subprocess, sys
from pathlib import Path

ROOT=Path('/var/lib/uap-detector/power-requests')

def process():
    jobs=sorted(ROOT.glob('*.json'))
    if not jobs:return 0
    request=jobs[0]
    if request.is_symlink() or request.stat().st_size>4096:
        request.unlink(missing_ok=True);return 1
    try:
        data=json.loads(request.read_text())
    finally:
        request.unlink(missing_ok=True)
    action=data.get('action')
    if action not in ('reboot','shutdown'):return 2
    print(f'UAP power request: {action} from administrator {str(data.get("admin","unknown"))[:40]}',flush=True)
    # SIGTERM is handled by the camera recorder: the encoder finalises its MP4
    # and writes an event before exiting. Do not power off if stopping fails.
    try:
        subprocess.run(['/usr/bin/systemctl','stop','uap-detector.service'],timeout=95,check=True)
    except (subprocess.CalledProcessError,subprocess.TimeoutExpired) as exc:
        print('Recorder could not be stopped safely: refusing power action',exc,file=sys.stderr)
        return 3
    command='reboot' if action=='reboot' else 'poweroff'
    subprocess.run(['/usr/bin/systemctl',command],timeout=15,check=True)
    return 0

if __name__=='__main__':
    try:sys.exit(process())
    except Exception as exc:
        print('Power action failed:',exc,file=sys.stderr)
        sys.exit(4)
