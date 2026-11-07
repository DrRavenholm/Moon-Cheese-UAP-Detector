"""Unified, read-only storage inventory and safely scoped storage-tab filtering."""
import os
import shutil
import subprocess
import time
from pathlib import Path

from common import DATA, RECORDINGS, connection
from storage import file_size
from management import photos
import observation_jobs as oj

TABS = ('overview', 'recordings', 'photos', 'scheduled_video', 'timelapse')
TERMINAL = oj.TERMINAL
JOB_STATUSES = ('all','queued','capturing','rendering','archiving','finalising','complete','failed','cancelled','interrupted','missed')
RECORD_STATUSES = ('all','new','viewed','dismissed','flagged','identified','unresolved')
_cached = {'at':0, 'value':None}


def job_bytes(job):
    directory=oj.job_dir(job['id'])
    sizes={'total':0,'zip':0,'mp4':0}
    if directory.is_dir() and not directory.is_symlink():
        for path in directory.rglob('*'):
            if path.is_file() and not path.is_symlink():
                try: size=path.stat().st_size
                except OSError: continue
                sizes['total']+=size
                if path.suffix.lower()=='.mp4':sizes['mp4']+=size
                if path.name=='source-frames.zip':sizes['zip']+=size
    return sizes


def media_rows(tab,query='',status='all',visibility='all',sort='newest',older='0',protection='all'):
    """All filters are applied before pagination, including size sorting."""
    if tab=='photos':
        rows=[]
        for p in photos():
            if query.casefold() not in (p['title']+' '+p['note']).casefold():continue
            if visibility!='all' and bool(p['public'])!=(visibility=='public'):continue
            row=dict(p)
            row.update(label=p['title'] or 'Photograph '+p['token'][:8], time=p['modified'],
                       protected=bool(p['pinned'] or p['public']), bytes=p['bytes'],ident=p['token'])
            rows.append(row)
    elif tab=='recordings':
        with connection() as db:
            events=[dict(x) for x in db.execute('SELECT id,kind,status,time_utc,video,pinned,public FROM events WHERE video IS NOT NULL ORDER BY id DESC')]
        from datetime import datetime, timedelta, timezone
        limit=(datetime.now(timezone.utc)-timedelta(days=int(older))).isoformat(timespec='seconds') if older!='0' else None
        rows=[]
        for e in events:
            if status!='all' and e['status']!=status:continue
            if visibility!='all' and bool(e['public'])!=(visibility=='public'):continue
            if limit and e['time_utc']>=limit:continue
            if query.casefold() not in (e['kind']+' '+str(e['id'])).casefold():continue
            e.update(label=f"{e['kind']} #{e['id']}",time=e['time_utc'],
                     bytes=file_size(RECORDINGS,e['video'],'.mp4'),ident=e['id'],
                     protected=bool(e['pinned'] or e['public'] or e['status'] in ('flagged','identified','unresolved')))
            rows.append(e)
    elif tab in ('scheduled_video','timelapse'):
        with connection() as db:
            jobs=[dict(x) for x in db.execute('SELECT * FROM observation_jobs WHERE kind=? ORDER BY id DESC',(tab,))]
        rows=[]
        for j in jobs:
            if status!='all' and j['status']!=status:continue
            if visibility!='all' and bool(j['public'])!=(visibility=='public'):continue
            if query.casefold() not in (j['title']+' '+j['note']+' '+str(j['id'])).casefold():continue
            sizes=job_bytes(j)
            j.update(label=j['title'],time=j['start_utc'],ident=j['id'],bytes=sizes['total'],
                     zip_bytes=sizes['zip'],mp4_bytes=sizes['mp4'],
                     protected=bool(j['pinned'] or j['public'] or j['status'] not in TERMINAL))
            rows.append(j)
    else:rows=[]
    if protection!='all':rows=[x for x in rows if bool(x['protected'])==(protection=='protected')]
    rows.sort(key=lambda x:(x['bytes'],str(x['ident'])) if sort=='largest' else
              (x['time'],str(x['ident'])), reverse=sort!='oldest')
    return rows


def _du(path):
    """Measurements may be unavailable on restricted installations; never delete files."""
    path=Path(path)
    if not path.exists():return 0
    if path.is_file():
        try:return path.stat().st_size
        except OSError:return 0
    try:
        p=subprocess.run(['du','-sxB1',str(path)],text=True,capture_output=True,timeout=8,check=True)
        return int(p.stdout.split()[0])
    except (OSError,ValueError,subprocess.SubprocessError,IndexError):return None


def disk_report(refresh=False):
    """Partition totals reconcile with df; nested categories are never summed twice."""
    if not refresh and _cached['value'] and time.monotonic()-_cached['at']<180:return _cached['value']
    disk=shutil.disk_usage(DATA)
    roots={
        'Motion recordings': RECORDINGS,
        'Scheduled media and time-lapses': DATA/'observation-jobs',
        'Photographs': DATA/'photography',
        'Thumbnails and previews': DATA/'thumbnails',
        'Docker/containerd': Path('/var/lib/containerd'),
        'Operating system software': Path('/usr'),
        'Package cache': Path('/var/cache'),
        'Swap file': Path('/var/swap'),
        'Application backups': Path('/var/backups/uap-detector'),
    }
    sizes={label:_du(path) for label,path in roots.items()}
    # NPM Docker installations can alternatively keep their images under /var/lib/docker.
    docker=_du('/var/lib/docker')
    if docker is not None and sizes['Docker/containerd'] is not None:
        sizes['Docker/containerd']+=docker
    known=sum(v for v in sizes.values() if v is not None)
    sizes['Other system and reserved space']=max(0,disk.used-known)
    report={'total':disk.total,'used':disk.used,'free':disk.free,'categories':sizes,
            'job_counts':{},'job_sizes':{'scheduled_video':0,'timelapse':0},'zip_bytes':0,'video_bytes':0}
    with connection() as db:
        jobs=[dict(x) for x in db.execute('SELECT id,kind FROM observation_jobs')]
    for job in jobs:
        sizes_job=job_bytes(job)
        report['job_counts'][job['kind']]=report['job_counts'].get(job['kind'],0)+1
        report['job_sizes'][job['kind']]+=sizes_job['total']
        report['zip_bytes']+=sizes_job['zip']
        report['video_bytes']+=sizes_job['mp4']
    # Eligible files are only *potentially* reclaimable by explicit confirmed deletion.
    # We intentionally exclude pinned, public, active and protected-status items.
    report['reclaimable_bytes']=sum(
        item['bytes'] for media in ('recordings','photos','scheduled_video','timelapse')
        for item in media_rows(media) if not item['protected'])
    _cached.update(at=time.monotonic(), value=report)
    return report
