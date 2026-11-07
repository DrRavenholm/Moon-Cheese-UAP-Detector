#!/usr/bin/python3
"""Simple command-line checks for the test build."""
import argparse
import json
import sys
from pathlib import Path
from common import DATA, STATUS, add_event, ensure_db

parser = argparse.ArgumentParser()
parser.add_argument('command', choices=['demo', 'status', 'help'])
args = parser.parse_args()
ensure_db()
if args.command == 'demo':
    idx = add_event('Demo / test notification (not camera footage)', demo=True)
    print(f'Created labelled DEMO event #{idx}; refresh the dashboard.')
elif args.command == 'status':
    print(STATUS.read_text() if STATUS.exists() else 'No detector heartbeat yet')
else:
    parser.print_help()
