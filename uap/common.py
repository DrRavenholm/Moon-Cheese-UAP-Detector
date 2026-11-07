"""Small shared database, runtime preferences and file helpers for UAP Detector."""
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DATA = Path(os.environ.get('UAP_DATA_DIR', '/var/lib/uap-detector'))
ETC = Path(os.environ.get('UAP_ETC_DIR', '/etc/uap-detector'))
DB = DATA / 'events.sqlite3'
RECORDINGS = DATA / 'recordings'
THUMBS = DATA / 'thumbnails'
STATUS = DATA / 'status.json'
CONFIG = ETC / 'config.json'
SETTINGS = DATA / 'settings.json'  # dashboard may update this, base config stays root-owned
STATUSES = ('new', 'viewed', 'flagged', 'identified', 'dismissed', 'unresolved')
# Standard video output sizes supported by the camera settings page.
RESOLUTIONS = {
    '640x480': (640, 480),
    '1280x720': (1280, 720),
    '1920x1080': (1920, 1080),
}

DEFAULTS = {
    'fps': 15, 'resolution': '1280x720',
    'detection_profile': 'general', 'sky_brightness': 180,
    'sky_min_area': 2, 'sky_max_area': 100,
    'sky_confirm_frames': 3, 'sky_min_movement': 2,
    'pixel_threshold': 32, 'min_changed_pixels': 65,
    'pre_motion_seconds': 5, 'post_motion_seconds': 5, 'max_clip_seconds': 300,
    # Destructive clean-up is opt-in; reviewed/flagged entries are always protected.
    'cleanup_enabled': False, 'retention_new_days': 60,
    'retention_viewed_days': 30, 'retention_dismissed_days': 7,
    'max_storage_gb': 0,
    'storm_enabled': True, 'storm_trigger_minutes': 10,
    'storm_window_minutes': 15, 'storm_cooldown_minutes': 15,
    'photo_cleanup_enabled': False, 'photo_retention_days': 30,
    'notice_cleanup_enabled': False, 'notice_report_days': 30,
    'notice_fault_days': 90,
    'detection_paused': False, 'operation_mode': 'continuous',
    'schedule_start': '20:00', 'schedule_end': '06:00',
    'schedule_timezone': 'Europe/London',
    'location_name': '', 'latitude': None, 'longitude': None,
    'camera_profile_mode': 'auto', 'camera_profiles': {},
    'rotate_180': False, 'image_top_bearing': 0, 'camera_elevation': 90,
    'public_enabled': False, 'public_title': 'Sky Camera',
    'public_show_location_name': False, 'public_show_orientation': False,
}


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def connection():
    conn = sqlite3.connect(DB, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA busy_timeout=10000')
    return conn


def ensure_db():
    for path in (DATA, RECORDINGS, THUMBS):
        path.mkdir(parents=True, exist_ok=True)
    with connection() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time_utc TEXT NOT NULL,
            kind TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'new',
            video TEXT,
            thumbnail TEXT,
            score REAL NOT NULL DEFAULT 0,
            trigger_source TEXT NOT NULL DEFAULT '',
            note TEXT NOT NULL DEFAULT '',
            demo INTEGER NOT NULL DEFAULT 0,
            viewed_at TEXT,
            pinned INTEGER NOT NULL DEFAULT 0
        )''')
        if 'trigger_source' not in {row[1] for row in db.execute('PRAGMA table_info(events)')}:
            db.execute("ALTER TABLE events ADD COLUMN trigger_source TEXT NOT NULL DEFAULT ''")
        if 'viewed_at' not in {row[1] for row in db.execute('PRAGMA table_info(events)')}:
            try:
                db.execute('ALTER TABLE events ADD COLUMN viewed_at TEXT')
            except sqlite3.OperationalError as exc:
                if 'duplicate column name' not in str(exc).lower():
                    raise
        # Individual event notes require a separate opt-in to appear publicly.
        if 'public_note' not in {row[1] for row in db.execute('PRAGMA table_info(events)')}:
            db.execute('ALTER TABLE events ADD COLUMN public_note INTEGER NOT NULL DEFAULT 0')
        # Public sharing is a per-event explicit opt-in, disabled on upgrades.
        if 'public' not in {row[1] for row in db.execute('PRAGMA table_info(events)')}:
            db.execute('ALTER TABLE events ADD COLUMN public INTEGER NOT NULL DEFAULT 0')
        for field, type_and_default in (
            ('image_top_bearing', 'INTEGER'),
            ('camera_elevation', 'INTEGER'),
            ('camera_rotated', 'INTEGER'),
            ('camera_profile', 'TEXT')):
            if field not in {r[1] for r in db.execute('PRAGMA table_info(events)')}:
                db.execute(f'ALTER TABLE events ADD COLUMN {field} {type_and_default}')
        db.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL COLLATE NOCASE UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin','viewer')),
            enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0,1)),
            session_version INTEGER NOT NULL DEFAULT 0
        )''')
        if 'pinned' not in {row[1] for row in db.execute('PRAGMA table_info(events)')}:
            try:
                db.execute('ALTER TABLE events ADD COLUMN pinned INTEGER NOT NULL DEFAULT 0')
            except sqlite3.OperationalError as exc:
                if 'duplicate column name' not in str(exc).lower():
                    raise


def add_event(kind, video=None, thumbnail=None, score=0, demo=False, trigger_source='', image_top_bearing=None, camera_elevation=None, camera_rotated=None, camera_profile=None):
    with connection() as conn:
        cursor = conn.execute(
            'INSERT INTO events(time_utc,kind,status,video,thumbnail,score,demo,trigger_source,image_top_bearing,camera_elevation,camera_rotated,camera_profile) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
            (now_iso(), kind, 'new', video, thumbnail, float(score), int(demo), trigger_source,
             image_top_bearing, camera_elevation, camera_rotated, camera_profile))
        return cursor.lastrowid


def write_status(state, message=''):
    DATA.mkdir(parents=True, exist_ok=True)
    temp = DATA / 'status.json.tmp'
    temp.write_text(json.dumps({'state': state, 'message': message, 'updated': now_iso()}))
    os.replace(temp, STATUS)


def read_config():
    base = DEFAULTS.copy()
    if CONFIG.is_file():
        base.update(json.loads(CONFIG.read_text()))
    if SETTINGS.is_file():
        base.update(json.loads(SETTINGS.read_text()))
    return base


def save_settings(data):
    """Atomically commit validated, administrator-selected settings."""
    DATA.mkdir(parents=True, exist_ok=True)
    temp = DATA / f'.settings.{os.getpid()}.tmp'
    try:
        with temp.open('x') as f:
            os.chmod(temp, 0o600)
            json.dump(data, f, indent=2)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, SETTINGS)
    finally:
        temp.unlink(missing_ok=True)
