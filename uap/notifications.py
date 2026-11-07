"""Local, in-dashboard reports and admin-only health alerts. No external delivery."""
import sqlite3
import sys
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfoNotFoundError
from common import connection, ensure_db, read_config
from observations import recordings_between, summarize, timezone_for
from health import system_health

WEEKDAYS=('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday')


def migrate():
    ensure_db()
    with connection() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS notice_preferences (
            user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            frequency TEXT NOT NULL DEFAULT 'off' CHECK(frequency IN ('off','daily','weekly')),
            local_time TEXT NOT NULL DEFAULT '08:00',
            timezone TEXT NOT NULL DEFAULT 'Europe/London',
            weekday INTEGER NOT NULL DEFAULT 0 CHECK(weekday BETWEEN 0 AND 6))''')
        db.execute('''CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_utc TEXT NOT NULL,
            category TEXT NOT NULL CHECK(category IN ('digest','fault','recovery')),
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            unique_key TEXT NOT NULL,
            read_at TEXT,
            UNIQUE(user_id, unique_key))''')
        db.execute('''CREATE TABLE IF NOT EXISTS fault_state (
            fault_key TEXT PRIMARY KEY,
            active INTEGER NOT NULL,
            changed_utc TEXT NOT NULL)''')
        db.execute('''CREATE TABLE IF NOT EXISTS notice_generation_ledger (
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            unique_key TEXT NOT NULL,
            generated_utc TEXT NOT NULL,
            PRIMARY KEY(user_id,unique_key))''')
        # Recover existing digest keys when upgrading, before users delete them.
        db.execute('''INSERT OR IGNORE INTO notice_generation_ledger(user_id,unique_key,generated_utc)
                      SELECT user_id,unique_key,created_utc FROM notices
                      WHERE category='digest' ''')
        db.execute('CREATE INDEX IF NOT EXISTS idx_notices_user_time ON notices(user_id,created_utc DESC)')


def preferences(user_id, default_timezone='Europe/London'):
    with connection() as db:
        row=db.execute('SELECT * FROM notice_preferences WHERE user_id=?',(user_id,)).fetchone()
    return dict(row) if row else {'user_id':user_id,'frequency':'off','local_time':'08:00','timezone':default_timezone,'weekday':0}


def update_preferences(user_id, frequency, local_time, tzname, weekday):
    if frequency not in ('off','daily','weekly'): raise ValueError('Choose Off, Daily or Weekly.')
    try:
        h,m=map(int,local_time.split(':'))
        if not (0<=h<=23 and 0<=m<=59 and len(local_time)==5): raise ValueError()
    except (ValueError,AttributeError): raise ValueError('Choose a valid time.')
    try:
        import zoneinfo
        zoneinfo.ZoneInfo(tzname)
    except (ValueError, TypeError, ZoneInfoNotFoundError): raise ValueError('Choose a valid IANA timezone.')
    weekday=int(weekday)
    if not 0<=weekday<=6: raise ValueError('Choose a valid weekday.')
    with connection() as db:
        db.execute('''INSERT INTO notice_preferences(user_id,frequency,local_time,timezone,weekday) VALUES (?,?,?,?,?)
            ON CONFLICT(user_id) DO UPDATE SET frequency=excluded.frequency,local_time=excluded.local_time,
            timezone=excluded.timezone,weekday=excluded.weekday''',(user_id,frequency,local_time,tzname,weekday))


def create_notice(db, user_id, category, key, title, body, now):
    if category == 'digest':
        # Persist generation independently from the visible notification and its
        # delivery attempts: deleting a notice must not cause new email/push.
        cursor = db.execute('''INSERT OR IGNORE INTO notice_generation_ledger
                               (user_id,unique_key,generated_utc) VALUES (?,?,?)''',
                            (user_id,key,now.isoformat(timespec='seconds')))
        if cursor.rowcount == 0:
            return
    db.execute('''INSERT OR IGNORE INTO notices(user_id,created_utc,category,title,body,unique_key)
                  VALUES (?,?,?,?,?,?)''', (user_id,now.isoformat(timespec='seconds'),category,title,body,key))


def dispatch_summaries(now=None):
    """Once per due day; windows are rolling 24/168 elapsed hours ending at scheduled delivery."""
    now=now or datetime.now(timezone.utc)
    with connection() as db:
        users=db.execute('''SELECT u.id,u.role,p.frequency,p.local_time,p.timezone,p.weekday
            FROM users u JOIN notice_preferences p ON p.user_id=u.id WHERE u.enabled=1 AND p.frequency!='off' ''').fetchall()
    for user in users:
        tz=timezone_for(user['timezone']); local=now.astimezone(tz)
        if local.strftime('%H:%M') < user['local_time']: continue
        if user['frequency']=='weekly' and local.weekday()!=user['weekday']: continue
        days=7 if user['frequency']=='weekly' else 1
        hour,minute=map(int,user['local_time'].split(':'))
        # Set the exact nominal delivery time on this *local* date, then
        # subtract an elapsed 24 or 168 hours in UTC. This remains an actual
        # 24-hour window when a daylight-saving transition occurs.
        due_local=local.replace(hour=hour,minute=minute,second=0,microsecond=0)
        due_utc=due_local.astimezone(timezone.utc)
        start=due_utc-timedelta(hours=24*days)
        end=due_utc
        rows=recordings_between(start,end)
        info=summarize(rows)
        label='Weekly' if days==7 else 'Daily'
        key=f'digest:{user["frequency"]}:{local.date().isoformat()}'
        local_start=start.astimezone(tz)
        local_end=end.astimezone(tz)
        window=f'{local_start.strftime("%d %b %Y, %H:%M %Z")} → {local_end.strftime("%d %b %Y, %H:%M %Z")}'
        lines=[f'Reporting window: {window}', f'Saved recordings: {info["total"]}',
               'Review: ' + (', '.join(f'{k.title()} {v}' for k,v in sorted(info['statuses'].items())) or 'none'),
               'Triggers: ' + (', '.join(f'{k} {v}' for k,v in sorted(info['triggers'].items())) or 'none')]
        with connection() as db:
            create_notice(db,user['id'],'digest',key,f'{label} observation summary','\n'.join(lines),now)


def dispatch_faults(now=None, health=None):
    now=now or datetime.now(timezone.utc)
    h=health or system_health()
    detector=h['detector']
    # Some states are legitimate (paused/scheduled). A stale heartbeat is never legitimate.
    stale=(detector['state'] in ('offline','failed','error','waiting') or
           detector['age_seconds'] is None or detector['age_seconds']>180)
    # A scheduled video/time-lapse intentionally owns the camera and stops the
    # ordinary preview. Do not create spurious snapshot faults/recoveries while
    # it is capturing or finalising. Other faults (disk, heartbeat) remain live.
    try:
        from observation_jobs import active as active_observation
        intentional_job=bool(active_observation()) or detector['state'] in ('job-video','job-timelapse','job-rendering','job-archiving','job-starting')
    except (sqlite3.Error, OSError, ImportError):
        intentional_job=detector['state'] in ('job-video','job-timelapse','job-rendering','job-archiving','job-starting')
    # A short recovery grace prevents false snapshot faults while the detector
    # reopens the video pipeline and starts producing its normal cached preview.
    try:
        if not intentional_job:
            with connection() as db:
                last=db.execute("SELECT finished_utc FROM observation_jobs WHERE finished_utc IS NOT NULL ORDER BY finished_utc DESC LIMIT 1").fetchone()
            if last and last['finished_utc']:
                finished=datetime.fromisoformat(last['finished_utc'].replace('Z','+00:00'))
                if finished.tzinfo is None:finished=finished.replace(tzinfo=timezone.utc)
                intentional_job=timedelta(0)<=now-finished<timedelta(minutes=5)
    except (sqlite3.Error, OSError, ValueError, TypeError):
        pass
    problems={
       'detector': (stale, 'Detector heartbeat missing or unhealthy'),
       'disk': (bool(h['disk_warning']), 'Low available recording storage'),
       'snapshot': (h['snapshot_age_seconds'] is None or h['snapshot_age_seconds']>180,
                    'Camera snapshot unavailable or stale')}
    with connection() as db:
        admins=[r['id'] for r in db.execute("SELECT id FROM users WHERE enabled=1 AND role='admin'")]
        for key,(active,desc) in problems.items():
            if key=='snapshot' and intentional_job: continue
            old=db.execute('SELECT active FROM fault_state WHERE fault_key=?',(key,)).fetchone()
            if old and bool(old['active'])==active: continue
            # Do not create recovery messages for problems not previously observed.
            db.execute('INSERT INTO fault_state(fault_key,active,changed_utc) VALUES (?,?,?) ON CONFLICT(fault_key) DO UPDATE SET active=excluded.active,changed_utc=excluded.changed_utc',
                       (key,int(active),now.isoformat(timespec='seconds')))
            if active or (old and old['active']):
                category='fault' if active else 'recovery'
                title=(desc if active else f'Recovered: {desc}')
                key_id=f'{category}:{key}:{now.isoformat(timespec="seconds")}'
                for uid in admins:
                    create_notice(db,uid,category,key_id,title,
                                  ({'detector':'The camera service heartbeat is missing or unhealthy. Open System Health and verify the detector service and camera connection.',
                                    'disk':'Recording storage is running low. Review Storage Management and remove eligible media or increase disk capacity.',
                                    'snapshot':'The ordinary camera preview has not updated recently. Check System Health; deliberate scheduled camera sessions are excluded.'}.get(key,'Open System Health to investigate.')
                                   if active else
                                   {'detector':'The camera service is reporting a healthy heartbeat again.',
                                    'disk':'Available recording storage has returned above the warning threshold.',
                                    'snapshot':'Fresh camera snapshots have resumed.'}.get(key,'The condition is no longer detected.')), now)


def dispatch_update_notices(now=None):
    """One check per administrator-local day at their configured summary time.

    Reuses existing admin notice delivery, with a persistent per-version ledger
    to prevent repeated email/push notifications even if a notice is deleted.
    """
    now=now or datetime.now(timezone.utc)
    from software_updates import get_release, VERSION, version_newer
    with connection() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS software_update_daily_checks (
            user_id INTEGER NOT NULL,local_day TEXT NOT NULL,
            PRIMARY KEY(user_id,local_day))''')
        db.execute('''CREATE TABLE IF NOT EXISTS software_update_announced (
            user_id INTEGER NOT NULL,version TEXT NOT NULL,
            PRIMARY KEY(user_id,version))''')
        admins=db.execute('''SELECT u.id,p.local_time,p.timezone FROM users u
            LEFT JOIN notice_preferences p ON p.user_id=u.id
            WHERE u.enabled=1 AND u.role='admin' ''').fetchall()
    due=[]
    for person in admins:
        tz=timezone_for(person['timezone'] or 'Europe/London')
        local=now.astimezone(tz)
        if local.strftime('%H:%M')<(person['local_time'] or '08:00'):continue
        local_day=local.date().isoformat()
        with connection() as db:
            result=db.execute('''INSERT OR IGNORE INTO software_update_daily_checks(user_id,local_day)
                                 VALUES (?,?)''',(person['id'],local_day))
            if result.rowcount:due.append(person['id'])
    if not due:return
    try:release=get_release()
    except (ValueError,OSError):return
    version=release['version']
    if not version_newer(version,VERSION) or not (release['archive'] and release['checksum']):return
    for uid in due:
        with connection() as db:
            result=db.execute('''INSERT OR IGNORE INTO software_update_announced(user_id,version)
                                 VALUES (?,?)''',(uid,version))
            if result.rowcount:
                create_notice(db,uid,'fault','software-update:'+version,
                    'Moon Cheese v'+version+' available',
                    'A newer official stable Moon Cheese release is available. Open System Health → Software updates to review and install it. No automatic installation has started.',now)


def run():
    migrate()
    now=datetime.now(timezone.utc)
    dispatch_summaries(now)
    dispatch_faults(now)
    dispatch_update_notices(now)
    # Observe possible stuck scheduled jobs without changing camera ownership.
    try:
        from job_diagnostics import check_stalled
        check_stalled(now)
    except sqlite3.OperationalError:
        pass  # Older installations without observation_jobs table.
    cleanup_old_notices(read_config(), now)
    # Opt-in external channels run after the local notice is safely persisted.
    # Persistent, unique delivery records prevent ordinary timer reruns from
    # re-sending successfully delivered messages.
    from delivery import migrate as delivery_migrate, dispatch as delivery_dispatch
    delivery_migrate()
    delivery_dispatch(now.isoformat(timespec='seconds'))



def cleanup_old_notices(settings=None, now=None, dry_run=False):
    """Only *read* notices are deleted automatically; current fault state persists."""
    settings = settings or read_config()
    if not settings.get('notice_cleanup_enabled', False):
        return {'deleted': 0, 'disabled': True}
    now = now or datetime.now(timezone.utc)
    report_days = int(settings.get('notice_report_days', 30))
    fault_days = int(settings.get('notice_fault_days', 90))
    if not 1 <= report_days <= 3650 or not 1 <= fault_days <= 3650:
        raise ValueError('Notification retention out of range')
    report_cutoff=(now-timedelta(days=report_days)).isoformat(timespec='seconds')
    fault_cutoff=(now-timedelta(days=fault_days)).isoformat(timespec='seconds')
    with connection() as db:
        expr="""read_at IS NOT NULL AND
               ((category='digest' AND created_utc < ?) OR
                (category IN ('fault','recovery') AND created_utc < ?))"""
        if dry_run:
            count=db.execute('SELECT COUNT(*) FROM notices WHERE '+expr,(report_cutoff,fault_cutoff)).fetchone()[0]
        else:
            count=db.execute('DELETE FROM notices WHERE '+expr,(report_cutoff,fault_cutoff)).rowcount
    return {'deleted': 0 if dry_run else count, 'candidates': count, 'disabled':False}


if __name__=='__main__':
    try: run()
    except Exception as exc:
        print(f'Local notification check failed: {exc}', file=sys.stderr)
        raise
