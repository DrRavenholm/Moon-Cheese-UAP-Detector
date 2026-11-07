"""Admin-only event-storm history and fault/recovery notices."""
from datetime import datetime, timezone
from common import connection, ensure_db


def migrate():
    ensure_db()
    with connection() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS storm_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, start_utc TEXT NOT NULL,
            end_utc TEXT, state TEXT NOT NULL DEFAULT 'active',
            cooldown_seconds INTEGER NOT NULL)''')
        db.execute('CREATE INDEX IF NOT EXISTS ix_storm_recent ON storm_history(start_utc DESC)')


def notify(db, category, title, body, identifier, instant):
    for row in db.execute("SELECT id FROM users WHERE role='admin' AND enabled=1"):
        db.execute('''INSERT OR IGNORE INTO notices(user_id,created_utc,category,title,body,unique_key)
          VALUES (?,?,?,?,?,?)''',(row['id'],instant,category,title,body,identifier))


def activated(seconds):
    migrate()
    timestamp=datetime.now(timezone.utc).isoformat(timespec='seconds')
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        cursor=db.execute('INSERT INTO storm_history(start_utc,cooldown_seconds) VALUES (?,?)',
                          (timestamp,int(seconds)))
        ident=cursor.lastrowid
        notify(db,'fault','Event-storm protection activated',
               f'New motion recordings are suppressed for about {round(seconds/60)} minutes. Camera snapshots remain available.',
               f'storm:activated:{ident}',timestamp)
    return ident


def recovered(ident, reason='Cooldown completed'):
    if not ident: return
    migrate()
    instant=datetime.now(timezone.utc).isoformat(timespec='seconds')
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        changed=db.execute("UPDATE storm_history SET end_utc=?, state=? WHERE id=? AND end_utc IS NULL",
                           (instant,reason,ident)).rowcount
        if changed:
            notify(db,'recovery','Event-storm monitoring resumed',reason,
                   f'storm:recovered:{ident}',instant)


def latest(limit=20):
    migrate()
    with connection() as db:
        return [dict(r) for r in db.execute('SELECT * FROM storm_history ORDER BY id DESC LIMIT ?', (int(limit),))]


def close_orphaned_on_startup():
    """Mark incomplete histories after an unexpected detector restart."""
    migrate()
    instant=datetime.now(timezone.utc).isoformat(timespec='seconds')
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        entries=[row['id'] for row in db.execute('SELECT id FROM storm_history WHERE end_utc IS NULL')]
        for ident in entries:
            db.execute("UPDATE storm_history SET end_utc=?,state='Detector restarted' WHERE id=? AND end_utc IS NULL",(instant,ident))
            notify(db,'recovery','Event-storm cooldown interrupted by restart',
                   'The detector restarted during cooldown. Check System Health to confirm normal monitoring.',
                   f'storm:restarted:{ident}',instant)
