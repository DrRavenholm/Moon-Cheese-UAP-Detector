#!/usr/bin/python3
"""Dedicated short-lived astronomical downloader; never runs in camera/detector."""
import fcntl
import sys
from pathlib import Path
from sky_map_data import ROOT, auto

def main():
    ROOT.mkdir(mode=0o750,parents=True,exist_ok=True)
    with (ROOT/'.download-lock').open('a+') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return 0
        auto()
    return 0

if __name__=='__main__':sys.exit(main())
