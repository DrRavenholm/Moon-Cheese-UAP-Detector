"""Conservative, opt-in recording retention with protected reviewed events."""
import logging
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from common import DATA, RECORDINGS, THUMBS, connection, ensure_db, read_config

LOG = logging.getLogger('uap.storage')
AUTO_STATUSES = ('new', 'viewed', 'dismissed')
AGE_FIELDS = {'new': 'retention_new_days', 'viewed': 'retention_viewed_days',
              'dismissed': 'retention_dismissed_days'}


def safe_file(root, name, suffix):
    if not name or name != Path(name).name or name.startswith('.') or not name.lower().endswith(suffix):
        return None
    path = root / name
    return path if path.is_file() and not path.is_symlink() else None


def file_size(root, name, suffix):
    path = safe_file(root, name, suffix)
    return path.stat().st_size if path else 0


def storage_summary():
    space = shutil.disk_usage(DATA)
    bytes_recordings = sum(p.stat().st_size for p in RECORDINGS.glob('*.mp4')
                           if p.is_file() and not p.is_symlink())
    with connection() as db:
        total = db.execute('SELECT COUNT(*) FROM events').fetchone()[0]
        protected = db.execute("SELECT COUNT(*) FROM events WHERE pinned=1 OR public=1 OR status IN ('flagged','identified','unresolved')").fetchone()[0]
        pinned = db.execute('SELECT COUNT(*) FROM events WHERE pinned=1').fetchone()[0]
    return {
        'pinned_events': pinned,
        'video_bytes': bytes_recordings, 'video_gb': round(bytes_recordings / (1024 ** 3), 2),
        'free_gb': round(space.free / (1024 ** 3), 2),
        'disk_gb': round(space.total / (1024 ** 3), 2),
        'total_events': total, 'protected_events': protected,
    }


def cleanup_plan(settings, at=None):
    """Return candidates by oldest first; NEVER include explicitly reviewed status.

    Aging is calendar/UTC based. An optional storage cap (0=off) can delete
    eligible files younger than their age cutoff, but only when cleanup has
    been explicitly enabled. Retention is best-effort, not a hard disk quota.
    """
    at = at or datetime.now(timezone.utc)
    with connection() as db:
        rows = [dict(r) for r in db.execute(
            "SELECT id, time_utc, viewed_at, video, thumbnail, status FROM events "
            "WHERE pinned=0 AND public=0 AND status IN ('new','viewed','dismissed') ORDER BY time_utc, id")]
    chosen = []
    remaining = []
    cap_gb = float(settings.get('max_storage_gb', 0))
    cap_bytes = cap_gb * 1024 ** 3 if cap_gb > 0 else 0
    total_bytes = storage_summary()['video_bytes'] if cap_bytes else 0
    for row in rows:
        try:
            reference_time = row['viewed_at'] if row['status'] == 'viewed' and row['viewed_at'] else row['time_utc']
            created = datetime.fromisoformat(reference_time.replace('Z', '+00:00'))
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
        except ValueError:
            # An invalid timestamp never authorizes irreversible deletion.
            remaining.append(row)
            continue
        row['bytes'] = file_size(RECORDINGS, row['video'], '.mp4')
        limit_days = int(settings.get(AGE_FIELDS[row['status']], 0))
        if limit_days > 0 and created <= at - timedelta(days=limit_days):
            row['reason'] = 'age'
            chosen.append(row)
            total_bytes = max(0, total_bytes - row['bytes'])
        else:
            remaining.append(row)
    if cap_bytes and total_bytes > cap_bytes:
        for row in remaining:
            if 'bytes' not in row:
                row['bytes'] = file_size(RECORDINGS, row['video'], '.mp4')
            if total_bytes <= cap_bytes:
                break
            if row['bytes'] <= 0:
                continue
            row['reason'] = 'storage cap'
            chosen.append(row)
            total_bytes = max(0, total_bytes - row['bytes'])
    return chosen


def cleanup_expired(settings=None, dry_run=False):
    settings = settings or read_config()
    if not settings.get('cleanup_enabled', False):
        return {'deleted': 0, 'bytes': 0, 'disabled': True, 'candidates': 0}
    plan = cleanup_plan(settings)
    if dry_run:
        return {'deleted': 0, 'bytes': 0, 'disabled': False, 'candidates': len(plan)}
    deleted = []
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        for row in plan:
            # Preserve any event whose review status changed after planning.
            result = db.execute('DELETE FROM events WHERE id=? AND status=? AND pinned=0 AND public=0',
                                (row['id'], row['status']))
            if result.rowcount:
                deleted.append(row)
    # Database rows committed. Only unlink media with no other references.
    bytes_removed = 0
    with connection() as db:
        for row in deleted:
            for field, root, suffix in [('video', RECORDINGS, '.mp4'),
                                        ('thumbnail', THUMBS, '.jpg')]:
                path = safe_file(root, row[field], suffix)
                if path and not db.execute(f'SELECT 1 FROM events WHERE {field}=? LIMIT 1',
                                           (row[field],)).fetchone():
                    try:
                        if field == 'video':
                            bytes_removed += path.stat().st_size
                        path.unlink()
                    except OSError as ex:
                        LOG.warning('Could not remove old %s: %s', path.name, ex)
    return {'deleted': len(deleted), 'bytes': bytes_removed, 'disabled': False,
            'candidates': len(plan)}


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    ensure_db()
    if len(sys.argv) != 2 or sys.argv[1] not in ('run', 'dry-run'):
        raise SystemExit('Usage: storage.py [run|dry-run]')
    from management import photo_cleanup
    cfg=read_config()
    print('Recording cleanup:',cleanup_expired(cfg,dry_run=sys.argv[1]=='dry-run'))
    print('Photograph cleanup:',photo_cleanup(cfg,dry_run=sys.argv[1]=='dry-run'))
