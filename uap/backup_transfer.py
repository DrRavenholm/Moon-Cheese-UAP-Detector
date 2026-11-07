"""Portable settings snapshots and authenticated, encrypted user-account exports.

Sensitive system secrets, API tokens and live sessions are never exported.
The encrypted backup is AES-256-GCM with scrypt-derived key (cryptography package).
"""
import hashlib
import json
import os
import re
import secrets
from datetime import datetime, timezone
from common import DEFAULTS, connection, read_config, save_settings
from time_display import valid_zone

VERSION=1
MAGIC=b'UAPENC1\n'
FORBIDDEN=('password','secret','token','api_key','smtp','cloudflare','session','credential')


def safe_settings(settings):
    if not isinstance(settings,dict):raise ValueError('Expected a settings object.')
    result={}
    for key,value in settings.items():
        if key not in DEFAULTS or any(frag in key.casefold() for frag in FORBIDDEN):continue
        default=DEFAULTS[key]
        if isinstance(default,bool):
            if type(value) is not bool:raise ValueError(f'Invalid setting: {key}')
        elif isinstance(default,int):
            if type(value) is not int or abs(value)>1000000:raise ValueError(f'Invalid setting: {key}')
        elif isinstance(default,float):
            if type(value) not in (float,int) or abs(value)>1000000:raise ValueError(f'Invalid setting: {key}')
        elif isinstance(default,str):
            if not isinstance(value,str) or len(value)>200:raise ValueError(f'Invalid setting: {key}')
        elif isinstance(default,dict):
            if not isinstance(value,dict) or len(json.dumps(value))>120000:raise ValueError(f'Invalid setting: {key}')
        elif value is not None and type(value) not in (int,float,str):
            raise ValueError(f'Invalid setting: {key}')
        result[key]=value
    if 'schedule_timezone' in result:valid_zone(result['schedule_timezone'])
    from common import RESOLUTIONS
    from scheduling import parse_clock
    from camera_profiles import MODES
    allowed={'detection_profile':('general','sky_lights','combined'),
             'operation_mode':('continuous','timed','solar'),
             'camera_profile_mode':tuple(MODES)}
    for key,choices in allowed.items():
        if key in result and result[key] not in choices:raise ValueError(f'Unsupported {key}')
    if 'resolution' in result and result['resolution'] not in RESOLUTIONS:raise ValueError('Unsupported resolution')
    for key in ('schedule_start','schedule_end'):
        if key in result:parse_clock(result[key])
    if result.get('operation_mode')=='solar' and result.get('latitude') is None:
        raise ValueError('Sunset schedule requires location coordinates')
    bounds={'fps':(1,60),'pixel_threshold':(1,255),'min_changed_pixels':(10,10000),
            'sky_brightness':(100,250),'sky_min_area':(1,40),'sky_max_area':(10,400),
            'sky_confirm_frames':(2,8),'sky_min_movement':(1,15),
            'pre_motion_seconds':(1,15),'post_motion_seconds':(1,60),'max_clip_seconds':(30,3600),
            'retention_new_days':(0,3650),'retention_viewed_days':(0,3650),
            'retention_dismissed_days':(0,3650),'retention_new_days':(0,3650),
            'max_storage_gb':(0,1000),'storm_trigger_minutes':(5,60),
            'storm_window_minutes':(5,120),'storm_cooldown_minutes':(5,180),
            'photo_retention_days':(0,3650),'notice_report_days':(0,3650),'notice_fault_days':(0,3650),
            'image_top_bearing':(0,359),'camera_elevation':(0,90),
            'latitude':(-89.8,89.8),'longitude':(-180,180)}
    for key,(low,high) in bounds.items():
        if key in result and result[key] is not None and not low<=result[key]<=high:
            raise ValueError(f'{key} must be between {low} and {high}')
    if 'camera_profiles' in result:
        if len(result['camera_profiles'])>12:raise ValueError('Too many camera profiles')
        for key,profile in result['camera_profiles'].items():
            if key not in ('auto','day','night','custom1','custom2') or not isinstance(profile,dict):
                raise ValueError('Invalid camera profile slot')
    return result


def export_document(users=False):
    doc={'format':'uap-detector-configuration','version':VERSION,'created_utc':datetime.now(timezone.utc).isoformat(),
         'settings':safe_settings(read_config()),'contains_users':bool(users)}
    if users:
        with connection() as db:
            doc['users']=[dict(r) for r in db.execute('SELECT username,password_hash,role,enabled FROM users ORDER BY id')]
            try:
                prefs=[dict(r) for r in db.execute('SELECT u.username,p.frequency,p.local_time,p.timezone,p.weekday FROM notice_preferences p JOIN users u ON u.id=p.user_id')]
            except Exception:prefs=[]
            doc['preferences']=prefs
            try:
                doc['delivery_preferences']=[dict(r) for r in db.execute('''
                   SELECT u.username,p.recipient_email,p.email_enabled,p.push_enabled
                   FROM delivery_preferences p JOIN users u ON u.id=p.user_id''')]
            except Exception:doc['delivery_preferences']=[]
    return doc


def _key(passphrase,salt):
    if len(passphrase)<12:raise ValueError('Backup passphrase needs at least 12 characters.')
    return hashlib.scrypt(passphrase.encode('utf8'),salt=salt,n=2**14,r=8,p=1,dklen=32)


def encode(doc,passphrase=''):
    payload=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode('utf8')
    if len(payload)>2000000:raise ValueError('Export too large.')
    if not doc['contains_users']:return payload
    try:from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError as e:raise ValueError('Encrypted user backups require the python3-cryptography package.') from e
    salt=secrets.token_bytes(16);nonce=secrets.token_bytes(12)
    return MAGIC+salt+nonce+AESGCM(_key(passphrase,salt)).encrypt(nonce,payload,MAGIC)


def decode(payload,passphrase=''):
    if len(payload)>3000000:raise ValueError('Backup file too large.')
    encrypted=payload.startswith(MAGIC)
    if encrypted:
        try:from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError as e:raise ValueError('Encrypted user imports require python3-cryptography.') from e
        if len(payload)<len(MAGIC)+28:raise ValueError('Truncated encrypted archive.')
        start=len(MAGIC);salt=payload[start:start+16];nonce=payload[start+16:start+28]
        try:payload=AESGCM(_key(passphrase,salt)).decrypt(nonce,payload[start+28:],MAGIC)
        except Exception as exc:raise ValueError('Wrong passphrase or damaged encrypted archive.') from exc
    try:doc=json.loads(payload)
    except (UnicodeDecodeError,json.JSONDecodeError) as exc:raise ValueError('Not a valid UAP Detector backup.') from exc
    if not isinstance(doc,dict) or doc.get('format')!='uap-detector-configuration' or doc.get('version')!=VERSION:
        raise ValueError('Unsupported backup format or version.')
    if doc.get('contains_users') and not encrypted:
        raise ValueError('User-account backups must be encrypted.')
    settings=safe_settings(doc.get('settings'))
    if doc.get('contains_users'):
        if not isinstance(doc.get('users'),list) or len(doc['users'])>100:raise ValueError('Invalid user backup.')
        for user in doc['users']:
            if (not isinstance(user,dict) or not re.fullmatch(r'[A-Za-z0-9_.-]{3,32}',str(user.get('username','')))
                    or user.get('role') not in ('viewer','admin') or not isinstance(user.get('password_hash'),str)
                    or len(user['password_hash'])>512 or type(user.get('enabled')) is not int):
                raise ValueError('Invalid user record in backup.')
    doc['settings']=settings
    return doc


def apply(doc,users=False):
    settings=safe_settings(doc['settings'])
    # Update user accounts only by adding previously unseen usernames. Existing admin
    # accounts and credentials must not be replaced by a foreign device's export.
    added=0
    if users and doc.get('contains_users'):
        with connection() as db:
            db.execute('BEGIN IMMEDIATE')
            preexisting_names={r['username'].casefold() for r in db.execute('SELECT username FROM users')}
            for item in doc['users']:
                if db.execute('SELECT 1 FROM users WHERE username=?',(item['username'],)).fetchone():continue
                db.execute('INSERT INTO users(username,password_hash,role,enabled) VALUES (?,?,?,?)',
                           (item['username'],item['password_hash'],item['role'],int(bool(item['enabled']))))
                added+=1
            # Restore recipient addresses for newly imported users; keep all
            # external delivery opt-ins disabled until each owner confirms.
            added_names={item['username'] for item in doc['users']
                         if item['username'].casefold() not in preexisting_names}
            for pref in doc.get('delivery_preferences',[]):
                if not isinstance(pref,dict) or pref.get('username') not in added_names:continue
                try:
                    from delivery import valid_email
                    email=valid_email(pref.get('recipient_email')) if pref.get('recipient_email') else ''
                except ValueError:continue
                row=db.execute('SELECT id FROM users WHERE username=?',(pref['username'],)).fetchone()
                if row:
                    db.execute('''INSERT OR IGNORE INTO delivery_preferences(user_id,recipient_email)
                                  VALUES (?,?)''',(row['id'],email))
            for pref in doc.get('preferences',[]):
                if not isinstance(pref,dict):continue
                row=db.execute('SELECT id FROM users WHERE username=?',(pref.get('username'),)).fetchone()
                if not row:continue
                # Existing user's notification preferences are left untouched.
                if db.execute('SELECT 1 FROM notice_preferences WHERE user_id=?',(row['id'],)).fetchone():continue
                if pref.get('frequency') not in ('off','daily','weekly') or not re.fullmatch(r'\d\d:\d\d',str(pref.get('local_time',''))):continue
                try:valid_zone(pref.get('timezone',''))
                except Exception:continue
                day=pref.get('weekday',0)
                if type(day) is not int or not 0<=day<=6:continue
                db.execute('INSERT INTO notice_preferences(user_id,frequency,local_time,timezone,weekday) VALUES (?,?,?,?,?)',
                           (row['id'],pref['frequency'],pref['local_time'],pref['timezone'],day))
    # App settings change takes effect for the dashboard immediately; detector uses
    # its ordinary reload/restart path as configured by the app.
    save_settings({**read_config(),**settings})
    return added
