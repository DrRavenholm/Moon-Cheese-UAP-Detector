#!/usr/bin/python3
"""Camera-independent plate-solver queue worker."""
import fcntl
import sys
from plate_solving import ROOT, process_requests

def main():
    ROOT.mkdir(parents=True,exist_ok=True,mode=0o750)
    with (ROOT/'.solve-lock').open('a+') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return 0
        process_requests()
    return 0

if __name__=='__main__':sys.exit(main())
