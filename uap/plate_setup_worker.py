#!/usr/bin/python3
"""Root-owned, strictly allowlisted optional Debian plate-solver installer.

No user-supplied package, source URL, shell command or subprocess args.
The star database is separately downloaded by the unprivileged Sky Data Manager.
"""
import json
import os
import pwd
import shutil
import subprocess
import sys
from pathlib import Path
from plate_solving import ROOT, SETUP_REQUEST, SETUP_STATUS, _write, _read


def status(message, state):
    _write(SETUP_STATUS,{'state':state,'message':message[:250]})
    # Allow the unprivileged dashboard service to read root-created status.
    account=pwd.getpwnam('uapdetector')
    os.chown(SETUP_STATUS,account.pw_uid,account.pw_gid)


def main():
    if os.geteuid()!=0:return 2
    if not SETUP_REQUEST.is_file() or SETUP_REQUEST.is_symlink():return 0
    try:
        job=_read(SETUP_REQUEST)
        SETUP_REQUEST.unlink(missing_ok=True)
        if job.get('action')!='install-astap':return 2
        if shutil.which('astap_cli'):
            status('ASTAP is already installed','installed');return 0
        status('Installing the Debian ASTAP command-line package; monitoring continues','installing')
        subprocess.run(['/usr/bin/apt-get','update'],check=True,timeout=300,
                       stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,stdin=subprocess.DEVNULL)
        subprocess.run(['/usr/bin/apt-get','install','-y','astap-cli'],check=True,timeout=360,
                       stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,stdin=subprocess.DEVNULL)
        if not shutil.which('astap_cli'):raise RuntimeError('Debian installed the package but ASTAP executable was not found')
        status('ASTAP installed; download W08 index on the Calibration page','installed')
        return 0
    except (subprocess.SubprocessError, OSError, RuntimeError) as exc:
        status('Could not install ASTAP from the configured Debian repositories. See: sudo journalctl -u uap-plate-setup -n 40','error')
        return 1

if __name__=='__main__':sys.exit(main())
