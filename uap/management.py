"""Safe administration of event clips and privately saved photography files."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
from common import RECORDINGS, THUMBS, connection, ensure_db
from storage import safe_file
from photography import ROOT as PHOTO_ROOT, output_path, result_path

PROTECTED_STATUSES = ('flagged', 'identified', 'unresolved')
TOKEN = re.compile(r'^[0-9a-f]{32}$')


def eligible_events(ids):
    """Return eligible rows only, even if a malicious client submits protected IDs."""
    ids = sorted({int(i) for i in ids if str(i).isdigit() and int(i) > 0})[:200]
    if not ids:
        return []
    with connection() as db:
        rows = db.execute('SELECT id,kind,status,time_utc,video,thumbnail,pinned,public FROM events '
                          'WHERE id IN (' + ','.join('?' for _ in ids) + ')', ids).fetchall()
    return [dict(r) | {'bytes': (safe_file(RECORDINGS, r['video'], '.mp4').stat().st_size
                                    if safe_file(RECORDINGS, r['video'], '.mp4') else 0)}
            for r in rows if not r['pinned'] and not r['public'] and
            r['status'] not in PROTECTED_STATUSES]


def delete_eligible_events(ids):
    """Recheck every protection *inside* the deletion transaction."""
    wanted = sorted({int(i) for i in ids if str(i).isdigit() and int(i) > 0})[:200]
    if not wanted:
        return {'count': 0, 'bytes': 0}
    removed = []
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        for eid in wanted:
            row = db.execute('SELECT video,thumbnail FROM events WHERE id=? AND pinned=0 AND public=0 '
                             "AND status NOT IN ('flagged','identified','unresolved')", (eid,)).fetchone()
            if row is not None:
                if db.execute('DELETE FROM events WHERE id=? AND pinned=0 AND public=0 '
                              "AND status NOT IN ('flagged','identified','unresolved')", (eid,)).rowcount:
                    removed.append(dict(row))
    count_bytes = 0
    with connection() as db:
        for row in removed:
            for col, base, suffix in [('video',RECORDINGS,'.mp4'),('thumbnail',THUMBS,'.jpg')]:
                path = safe_file(base, row[col], suffix)
                if path and not db.execute(f'SELECT 1 FROM events WHERE {col}=? LIMIT 1', (row[col],)).fetchone():
                    try:
                        if col == 'video': count_bytes += path.stat().st_size
                        path.unlink()
                    except OSError:
                        pass
    return {'count': len(removed), 'bytes': count_bytes}


def photos():
    PHOTO_ROOT.mkdir(parents=True, exist_ok=True)
    output = []
    for path in PHOTO_ROOT.iterdir():
        if not path.is_file() or path.is_symlink():
            continue
        match = re.fullmatch(r'photo-([0-9a-f]{32})\.(jpg|png)', path.name)
        if not match:
            continue
        token, fmt = match.groups()
        # A photo may be kept even if the associated status JSON expired.
        output.append({'token':token, 'format':fmt,'bytes':path.stat().st_size,
                       'modified':datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).isoformat(),
                       'pinned':photo_pinned(token), 'public': bool(details_for_photo(token)['public']),
                       'title':details_for_photo(token)['title'], 'note':details_for_photo(token)['note'],
                       'public_note': bool(details_for_photo(token)['public_note'])})
    return sorted(output,key=lambda x:x['modified'],reverse=True)


def photo_pinned(token):
    if not TOKEN.fullmatch(token): return False
    return (PHOTO_ROOT / ('pin-'+token)).is_file()


def set_photo_pin(token, pin):
    if not TOKEN.fullmatch(token): raise ValueError('Invalid photo ID')
    if not any(output_path(token,x).is_file() for x in ('jpg','png')):raise ValueError('Photograph not found')
    ensure_photo_details()
    # Serialize pin changes with public-sharing edits and deletion checks.
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        marker=PHOTO_ROOT/('pin-'+token)
        if pin:marker.touch(exist_ok=True)
        else:marker.unlink(missing_ok=True)


def delete_photo(token):
    if not TOKEN.fullmatch(token):raise ValueError('Invalid photo ID')
    ensure_photo_details()
    # Hold the same SQLite writer lock used by publishing and pinning while
    # final protection checks and the irreversible file deletion take place.
    removed=False
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        row=db.execute('SELECT public FROM photo_details WHERE token=?',(token,)).fetchone()
        if (row and row['public']) or photo_pinned(token):return False
        for ext in ('jpg','png'):
            file=output_path(token,ext)
            if file.is_file() and not file.is_symlink():
                file.unlink();removed=True
        if removed:
            db.execute('DELETE FROM photo_details WHERE token=?',(token,))
            result_path(token).unlink(missing_ok=True)
            (PHOTO_ROOT/('thumb-'+token+'.jpg')).unlink(missing_ok=True)
            (PHOTO_ROOT/('public-'+token+'.jpg')).unlink(missing_ok=True)
    return removed


def protected_photo(token):
    if photo_pinned(token):return True
    return bool(details_for_photo(token)['public'])


def delete_photos(tokens):
    """Every photo deletion rechecks pins and public sharing under a writer lock."""
    chosen=list(dict.fromkeys(t for t in tokens if isinstance(t,str) and TOKEN.fullmatch(t)))[:200]
    count=total=0
    for token in chosen:
        paths=[p for ext in ('jpg','png') if (p:=output_path(token,ext)).is_file() and not p.is_symlink()]
        size=sum(p.stat().st_size for p in paths)
        if delete_photo(token):count+=1;total+=size
    return {'count':count,'bytes':total}


def expired_photos(days, at=None):
    at=at or datetime.now(timezone.utc)
    cutoff=at-timedelta(days=int(days))
    return [p for p in photos() if not p['pinned'] and not p['public'] and datetime.fromisoformat(p['modified']) < cutoff]


def photo_cleanup(settings, dry_run=False):
    if not settings.get('photo_cleanup_enabled',False):
        return {'deleted':0,'disabled':True}
    todo=expired_photos(settings.get('photo_retention_days',30))
    if not dry_run:
        for entry in todo: delete_photo(entry['token'])
    return {'deleted':0 if dry_run else len(todo),'candidates':len(todo),'disabled':False}

# Photo metadata is maintained separately from saved image files. An original
# photo can exist without an associated camera request status JSON.
def ensure_photo_details():
    with connection() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS photo_details (
            token TEXT PRIMARY KEY, title TEXT NOT NULL DEFAULT '',
            note TEXT NOT NULL DEFAULT '', public INTEGER NOT NULL DEFAULT 0,
            public_note INTEGER NOT NULL DEFAULT 0,
            updated_utc TEXT NOT NULL DEFAULT '')''')


def details_for_photo(token):
    if not TOKEN.fullmatch(token): raise ValueError('Invalid photo ID')
    ensure_photo_details()
    with connection() as db:
        item=db.execute('SELECT * FROM photo_details WHERE token=?',(token,)).fetchone()
    return dict(item) if item else {'token':token,'title':'','note':'','public':0,'public_note':0}


def set_photo_details(token, title, note, public, public_note):
    if not TOKEN.fullmatch(token): raise ValueError('Invalid photo ID')
    if not any(output_path(token,ext).is_file() for ext in ('jpg','png')): raise ValueError('Photo not found')
    title=(title or '').strip()[:120]
    note=(note or '')[:8000]
    ensure_photo_details()
    from datetime import datetime, timezone
    with connection() as db:
        db.execute('''INSERT INTO photo_details(token,title,note,public,public_note,updated_utc)
                      VALUES(?,?,?,?,?,?) ON CONFLICT(token) DO UPDATE SET
                      title=excluded.title,note=excluded.note,public=excluded.public,
                      public_note=excluded.public_note,updated_utc=excluded.updated_utc''',
                   (token,title,note,int(bool(public)),int(bool(public and public_note)),datetime.now(timezone.utc).isoformat()))
    if not public:(PHOTO_ROOT/('public-'+token+'.jpg')).unlink(missing_ok=True)

