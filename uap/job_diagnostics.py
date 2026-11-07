"""Read-only detection of stalled scheduled jobs; never assumes camera ownership."""
from datetime import datetime,timezone
from common import connection

ACTIVE_STATUSES=('capturing','rendering','archiving','finalising')


def _date(value):
    if not value:return None
    try:
        result=datetime.fromisoformat(str(value).replace('Z','+00:00'))
        return result.replace(tzinfo=timezone.utc) if result.tzinfo is None else result
    except (ValueError,TypeError):return None


def recent_jobs(now=None):
    now=now or datetime.now(timezone.utc)
    with connection() as db:
        rows=[dict(r) for r in db.execute('''SELECT id,kind,title,status,phase,error,updated_utc
            FROM observation_jobs ORDER BY id DESC LIMIT 12''')]
    for job in rows:
        last=_date(job.get('updated_utc'))
        elapsed=max(0,(now-last).total_seconds()) if last else None
        # Capture should regularly advance; rendering can legitimately take longer.
        limit=90*60 if job['status']=='rendering' else 30*60 if job['status'] in ('archiving','finalising') else 20*60
        job['age_minutes']=round(elapsed/60) if elapsed is not None else None
        job['suspect']=job['status'] in ACTIVE_STATUSES and (elapsed is None or elapsed>limit)
    return rows


def check_stalled(now=None):
    """Create or clear an admin-only alert; never cancel or restart a job."""
    now=now or datetime.now(timezone.utc)
    from notifications import create_notice
    rows=recent_jobs(now)
    with connection() as db:
        admins=[r['id'] for r in db.execute("SELECT id FROM users WHERE role='admin' AND enabled=1")]
        watched={r['fault_key']:r['active'] for r in db.execute("SELECT fault_key,active FROM fault_state WHERE fault_key LIKE 'job-watch:%'")}
        live={f"job-watch:{j['id']}":j for j in rows if j['suspect']}
        # Warn only once per suspected stall; recovery after a status update.
        for key,job in live.items():
            if watched.get(key):continue
            db.execute('''INSERT INTO fault_state(fault_key,active,changed_utc) VALUES (?,?,?)
                 ON CONFLICT(fault_key) DO UPDATE SET active=excluded.active,changed_utc=excluded.changed_utc''',
                 (key,1,now.isoformat()))
            for uid in admins:
                create_notice(db,uid,'fault',f'stalled:{job["id"]}:active',
                  f'Scheduled job #{job["id"]} has not reported progress',
                  'This is a monitoring warning, not an automatic cancellation. Check the job detail, detector heartbeat, disk space and rendering status. No camera restart was performed.',now)
        for key,active in watched.items():
            if not active or key in live:continue
            db.execute('UPDATE fault_state SET active=0,changed_utc=? WHERE fault_key=?',(now.isoformat(),key))
            for uid in admins:
                create_notice(db,uid,'recovery',f'{key}:cleared:{now.date()}',
                  f'Scheduled job monitoring cleared (#{key.split(":")[-1]})',
                  'The job is no longer suspected to be stalled; check its final status in Scheduled Video or Time-lapse Studio.',now)
    return len(live)
