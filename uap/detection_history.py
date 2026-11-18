"""Bounded, administrator-only detection history for unattended night monitoring.

One row per UTC minute in a separate SQLite file. Stored summaries contain no
camera frames, user names, images or credentials. The recorder remains usable
if this optional logging DB cannot be written.
"""
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from common import DATA

PATH = DATA / 'detection-history.sqlite3'
KEEP_DAYS = 7
_last_minute = None
_last_counts = {}


def _connect():
    db=sqlite3.connect(str(PATH),timeout=2.0)
    db.execute('PRAGMA busy_timeout=2000')
    db.execute('''CREATE TABLE IF NOT EXISTS samples (
         minute_utc TEXT PRIMARY KEY, sample TEXT NOT NULL)''')
    return db


def maybe_record(snapshot):
    """Store a 60-second summary without writing each video frame to disk."""
    global _last_minute, _last_counts
    now=datetime.now(timezone.utc)
    minute=now.strftime('%Y-%m-%dT%H:%M:00Z')
    if minute==_last_minute:return False
    counts=snapshot.get('counts') or {}
    delta={key:max(0,int(value)-int(_last_counts.get(key,0)))
           if int(value)>=int(_last_counts.get(key,0)) else max(0,int(value))
           for key,value in counts.items() if isinstance(value,int) and not isinstance(value,bool)}
    row=dict(snapshot)
    row['minute_utc']=minute
    row['delta']=delta
    # Do not retain source filenames, camera pictures or exception tracebacks.
    DATA.mkdir(parents=True,exist_ok=True)
    with _connect() as db:
        db.execute('INSERT OR REPLACE INTO samples(minute_utc,sample) VALUES (?,?)',
                   (minute,json.dumps(row,separators=(',',':'))))
        cutoff=(now-timedelta(days=KEEP_DAYS)).strftime('%Y-%m-%dT%H:%M:00Z')
        db.execute('DELETE FROM samples WHERE minute_utc < ?', (cutoff,))
    _last_minute=minute
    _last_counts=dict(counts)
    return True


def read_day(day, limit=1440):
    """Return UTC-day samples only, newest first, with strict date validation."""
    if not isinstance(day,str) or len(day)!=10 or datetime.strptime(day,'%Y-%m-%d').strftime('%Y-%m-%d')!=day:
        raise ValueError('Select a valid UTC date in YYYY-MM-DD format.')
    if not PATH.is_file():return []
    end=(datetime.strptime(day,'%Y-%m-%d')+timedelta(days=1)).strftime('%Y-%m-%d')
    with _connect() as db:
        entries=db.execute('SELECT sample FROM samples WHERE minute_utc >= ? AND minute_utc < ? ORDER BY minute_utc DESC LIMIT ?',
                           (day+'T00:00:00Z',end+'T00:00:00Z',min(1440,max(1,int(limit))))).fetchall()
    return [json.loads(text) for (text,) in reversed(entries)]
