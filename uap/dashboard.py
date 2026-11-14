#!/usr/bin/python3
"""Password-protected Moon Cheese UAP Detector dashboard."""
import json
import io
import math
import os
import secrets
import re
import sqlite3
import shutil
import smtplib
import subprocess
from fractions import Fraction
import time
from datetime import datetime, timezone, date, timedelta
from collections import defaultdict, deque
import calendar as cal_module
from pathlib import Path

from flask import (Flask, Response, jsonify, abort, redirect, render_template_string, request,
                   send_file, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from time_display import local_label, valid_zone
from zoneinfo import available_timezones
from filename_helpers import job_filename, photo_filename
from common import (DATA, ETC, STATUS, RECORDINGS, THUMBS, STATUSES, RESOLUTIONS, DEFAULTS,
                    connection, ensure_db, read_config, save_settings, now_iso)
from storage import cleanup_plan, storage_summary
from storage_views import STORAGE_PAGE, GALLERY, PHOTO_DETAIL
from storage_support import media_rows, disk_report, JOB_STATUSES, RECORD_STATUSES, TABS
from delivery_pages import USER_DELIVERY, ADMIN_DELIVERY
from network_ui import NETWORK_PANEL, CONFIRM_PAGE
import network_setup
from release import VERSION as APP_VERSION
from software_updates import latest_info as software_latest_info, enqueue as software_enqueue
import delivery
from backup_transfer import export_document, encode as encode_backup, decode as decode_backup, apply as apply_backup
from job_pages import JOBS_LIST, JOB_DETAIL, JOB_STORAGE
import observation_jobs as oj
from storm_events import latest as storm_recent, migrate as storm_migrate
from management import (eligible_events, delete_eligible_events, photos, set_photo_pin, delete_photo,
                        expired_photos, photo_cleanup, details_for_photo, set_photo_details,
                        protected_photo, delete_photos, ensure_photo_details)
from scheduling import detection_window, parse_clock, zone, sun_times
from pages import HELP, HISTORY, RELEASES
from help_docs import help_html
from health import system_health
from observations import calendar_month, day_range, recordings_between, summarize, timezone_for
from notifications import (migrate as migrate_notices, preferences as notice_preferences,
                           update_preferences, WEEKDAYS)
from hardware import capture_capabilities
from trigger_logic import SOURCE_LABELS
from draft_preview import enqueue, result_path, image_path, pending_request, expire_old_files
from photography import queue_capture, result_path as photo_result_path, output_path as photo_output_path, state as photo_set_state
from camera_profiles import (SLOTS, MODES, get_profiles, validate_profile, base_profiles,
                             exposure_within_frame, selected_profile, compass_name)

app = Flask(__name__)
app.jinja_env.globals['source_labels'] = SOURCE_LABELS
# Render stored UTC instants into the detector's configured local timezone.
# Users' personal report preferences can override it for notification timestamps.
def _localdt(value, tzname=None):
    return local_label(value, tzname or read_config().get('schedule_timezone') or 'Europe/London')

def _localday(value, tzname=None):
    return local_label(value, tzname or read_config().get('schedule_timezone') or 'Europe/London', date_only=True)
app.jinja_env.filters['localdt'] = _localdt
app.jinja_env.filters['localday'] = _localday
app.secret_key = (ETC / 'secret.key').read_text().strip()
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
                  PERMANENT_SESSION_LIFETIME=3600 * 12, MAX_CONTENT_LENGTH=64 * 1024)
# For initial HTTP LAN testing only. Set to True after verifying HTTPS-only access.
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('UAP_HTTPS_ONLY') == '1'
AUTH = json.loads((ETC / 'auth.json').read_text())
ensure_db()
migrate_notices()
delivery.migrate()
ensure_photo_details()
storm_migrate()
oj.migrate()
# One-time migration of existing admin login into SQLite. Existing credentials
# continue to work, and future username/password changes live in the users table.
with connection() as db:
    db.execute('BEGIN IMMEDIATE')
    if not db.execute('SELECT 1 FROM users LIMIT 1').fetchone():
        db.execute('INSERT INTO users(username, password_hash, role, enabled) VALUES (?,?,?,1)',
                   (AUTH['username'], AUTH['password_hash'], 'admin'))
ATTEMPTS = defaultdict(deque)

BASE = '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }} · {{ site_title }} · Moon Cheese UAP Detector</title>
<link rel="icon" type="image/png" sizes="32x32" href="{{url_for('moon_icon',name='moon-cheese-32.png')}}">
<link rel="apple-touch-icon" sizes="180x180" href="{{url_for('moon_icon',name='moon-cheese-180.png')}}">
<link rel="manifest" href="{{url_for('moon_manifest')}}">
<meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="Moon Cheese">
<meta name="theme-color" content="#0c1929">
<script src="{{ url_for('theme_init_js') }}"></script>
<style>
:root{color-scheme:dark;--bg:#080d19;--panel:#141f31;--edge:#25354b;--text:#e6edf6;--muted:#99abc2;--cyan:#75dbed;--red:#ff829a}
*{box-sizing:border-box}body{font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;margin:0;background:radial-gradient(circle at 85% 0%,#1a3146,#080d19 50%);color:var(--text);min-height:100vh}
a{color:var(--cyan)}.shell{max-width:1100px;margin:auto;padding:25px 18px}.bar{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;margin-bottom:24px}.logo{font-weight:750;letter-spacing:.5px;font-size:21px}.sub{color:var(--muted);font-size:13px}h1{font-size:27px;line-height:1.2;margin:8px 0 20px}h2{font-size:17px;margin:0 0 12px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.cols{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(0,.8fr);gap:14px}.panel{background:var(--panel);border:1px solid var(--edge);border-radius:13px;padding:18px;margin-bottom:14px;min-width:0}.value{font-size:18px;font-weight:700}.muted{color:var(--muted)}.pill{display:inline-block;border:1px solid #567085;color:#b9d9e9;border-radius:100px;padding:2px 9px;font-size:12px;text-transform:capitalize}.pill.new{border-color:#bf9654;color:#ffdb8a}.pill.flagged{border-color:#ce7080;color:#ff9cac}.pill.paused{border-color:#d9a063;color:#f2c380}.pill.scheduled{border-color:#7488b9;color:#becff6}.pill.viewed{border-color:#67a3c9;color:#a7d7f3}table{border-collapse:collapse;width:100%}td,th{text-align:left;padding:11px 5px;border-bottom:1px solid var(--edge)}th{font-size:12px;color:var(--muted)}.preview{display:block;width:100%;max-height:340px;object-fit:contain;background:#070a11;border-radius:9px}.button,button{display:inline-block;border:1px solid #4c7189;border-radius:7px;background:#25485b;color:#f3faff;font:inherit;padding:8px 14px;cursor:pointer;text-decoration:none}button:hover,.button:hover{background:#316179}input,select,textarea{font:inherit;background:#091423;color:#fff;border:1px solid #425a71;border-radius:7px;padding:10px;max-width:100%;width:100%}label{display:block;margin:12px 0 5px}.auth{max-width:430px;margin:9vh auto}.row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.error{color:var(--red)}.note{font-size:13px;color:var(--muted)}.foot{padding:20px 0 35px;color:var(--muted);font-size:12px}img.thumb{width:76px;border-radius:6px;max-height:45px;object-fit:cover}.forminline{display:inline-flex;gap:6px;align-items:center}textarea{min-height:95px}.eventimg{width:100%;max-height:450px;object-fit:contain;border-radius:9px;background:#090d17}.danger{border-color:#bf6473;background:#5a202f}.danger:hover{background:#762a3d}.hint{font-size:13px;color:var(--muted)}.between{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap}.options{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 14px}.checkline{display:flex;align-items:center;gap:9px}.checkline input{width:auto}.notice{border:1px solid #446478;background:#172b3c;padding:12px;border-radius:7px;margin:12px 0}.sr-only{position:absolute;width:1px;height:1px;padding:0;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}.tight{margin:0}.help-anchor{scroll-margin-top:20px}.change-item summary{cursor:pointer;list-style:none}.change-item summary::-webkit-details-marker{display:none}.change-title{display:grid;grid-template-columns:minmax(0,1fr) 205px 16px;align-items:center;gap:16px}.release-about{min-width:0}.release-when{display:block;min-height:1em;text-align:right;white-space:nowrap;font-size:13px;color:var(--muted);font-variant-numeric:tabular-nums}.change-title::after{content:'▾';color:var(--cyan)}.change-item[open] .change-title::after{content:'▴'}.change-details{border-top:1px solid var(--edge);margin-top:16px;padding-top:16px}.change-details li{margin:6px 0}.pin{color:#ffd482;font-weight:bold}.investigator{display:grid;gap:12px}.investigator-stage{position:relative;background:#000;border:1px solid var(--edge);border-radius:10px;overflow:hidden;aspect-ratio:16/9;touch-action:none;cursor:grab}.investigator-stage.dragging{cursor:grabbing}.investigator-stage video{width:100%;height:100%;display:block;object-fit:contain;transform-origin:center center}.investigator-tools{display:flex;gap:8px;flex-wrap:wrap;align-items:center}.investigator-tools button{min-width:54px}.investigator-tools select{width:auto;min-width:110px}.investigator-tools input[type=range]{width:145px;max-width:100%;padding:0;accent-color:var(--cyan)}.investigator-timeline{width:100%!important}.investigator-tools label{display:flex;align-items:center;gap:7px;margin:0;font-size:13px;color:var(--muted)}.investigator-time{font-variant-numeric:tabular-nums}.investigator-status{color:var(--muted);font-size:13px}.investigator-panels{display:flex;gap:12px;flex-wrap:wrap}.investigator-group{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.investigator-stage:focus-visible{outline:3px solid var(--cyan);outline-offset:3px}.investigator-stage:fullscreen{width:100vw!important;height:100vh!important;height:100dvh!important;aspect-ratio:auto!important;max-height:none!important;max-width:none!important;border:0;border-radius:0;background:#000;display:block}
.investigator-stage:fullscreen .investigator-media{inset:0!important;width:100%;height:100%}
.investigator-stage:fullscreen video{object-fit:contain!important}
.investigator-fullscreen-controls{display:none;position:absolute;right:16px;top:16px;z-index:12;gap:8px;align-items:center}
.investigator-stage:fullscreen .investigator-fullscreen-controls{display:flex}
.investigator-fullscreen-controls button{width:auto;background:rgba(14,33,51,.9);border:1px solid #6698ae;box-shadow:0 1px 10px #0009}
.investigator-media{position:absolute;inset:0;transform-origin:center center}
.investigator-stage .investigator-media video{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;transform:none}
.investigator-stage .investigator-compare{position:absolute;inset:0;pointer-events:none}
.investigator-stage .investigator-compare[hidden],.investigator-stage .compare-ui[hidden]{display:none!important}
.investigator-stage .compare-canvas,.investigator-stage .compare-right{position:absolute;inset:0;width:100%;height:100%}
.investigator-stage .compare-canvas{object-fit:contain;display:block}
.investigator-stage .compare-right{overflow:hidden;clip-path:inset(0 0 0 50%)}
.investigator-stage .compare-label{position:absolute;top:12px;z-index:3;padding:5px 10px;background:rgba(6,13,26,.87);border:1px solid #7693a4;border-radius:6px;font-size:13px;pointer-events:none}
.investigator-stage .compare-label-left{left:12px}
.investigator-stage .compare-label-right{right:12px}
.investigator-stage .compare-divider{position:absolute;top:0;bottom:0;left:50%;width:2px;background:#d6f6ff;transform:translateX(-50%);z-index:2;pointer-events:none;box-shadow:0 0 4px #000}
.investigator-stage .compare-divider:after{content:'↔';position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);border-radius:50%;border:2px solid white;background:#154c65;color:white;font-size:18px;width:38px;height:38px;display:grid;place-items:center}
.investigator-stage .compare-slider{position:absolute;inset:0;width:100%;height:100%;margin:0;padding:0;opacity:0;z-index:4;cursor:ew-resize;touch-action:auto}
.investigator-stage .compare-slider:focus-visible{opacity:.18;outline:4px solid var(--cyan);outline-offset:-4px}
.investigator-tools select{max-width:min(260px,100%)}
.investigator-compare-controls{display:flex;gap:10px;align-items:center;flex-wrap:wrap;padding:12px;border:1px solid var(--edge);border-radius:9px;background:#0e1b2a}
.investigator-compare-controls label{display:flex;gap:6px;align-items:center;margin:0;font-size:13px}
.investigator-compare-controls select{width:auto;min-width:155px}
.investigator-stage.comparing{cursor:ew-resize}

.setting-section{padding:0!important;overflow:hidden}.setting-section>summary{padding:16px 18px;cursor:pointer;list-style:none;display:flex;gap:10px;align-items:center;justify-content:space-between;font-weight:700;font-size:17px}.setting-section>summary::-webkit-details-marker{display:none}.setting-section>summary:after{content:"▾";color:var(--cyan)}.setting-section[open]>summary:after{content:"▴"}.setting-section>.setting-content{padding:0 18px 18px}.camera-orientation{display:grid;grid-template-columns:minmax(180px,.85fr) minmax(250px,1.25fr);gap:16px;align-items:start}.camera-orientation .orientation-fields label:first-child{margin-top:0}.camera-orientation .orientation-help{margin:0;border-left:2px solid var(--edge);padding-left:14px}.camera-profile-edit .row{margin-top:12px}.camera-profile-edit button{font-size:13px}.investigator-compare-row{display:grid;grid-template-columns:auto minmax(110px,1fr) minmax(110px,1fr);gap:10px;align-items:center}.investigator-compare-row label{min-width:0!important;display:flex;gap:6px}.investigator-compare-row select{width:100%;min-width:0}.investigator-compare-row #investigator-compare-info{grid-column:1 / -1}.investigator-compare-row button{white-space:nowrap}.camera-settings-preview .row{flex-wrap:wrap}@media(max-width:620px){.camera-orientation{grid-template-columns:1fr}.camera-orientation .orientation-help{border-left:none;border-top:2px solid var(--edge);padding:12px 0 0}.investigator-compare-row{grid-template-columns:1fr 1fr}.investigator-compare-row button{grid-column:1 / -1}.investigator-compare-row label{flex-direction:column;align-items:stretch}}
.camera-settings-preview{border:1px solid var(--edge);border-radius:9px;padding:12px;margin:12px 0;background:#0b1727}.camera-settings-preview .row{justify-content:space-between;margin-bottom:8px}.camera-settings-preview img{max-height:280px}
.calendar-grid{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:6px}.calendar-cell{display:block;text-align:center;border:1px solid var(--edge);background:#0d1a2a;border-radius:8px;min-height:66px;padding:9px 3px;text-decoration:none;color:var(--text)}.calendar-cell.selected{border-color:var(--cyan);background:#153348}.calendar-cell .sub{font-size:12px}.calendar-blank{min-height:66px}.stats{display:flex;gap:8px;flex-wrap:wrap}.stats span{padding:6px 9px;background:#0c192b;border-radius:6px;border:1px solid var(--edge)}.notices-list{display:grid;gap:12px}.notice-unread{border-color:#539fb0}.public-detail-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;align-items:start}
.camera-profile-edit{border:1px solid var(--edge);border-radius:8px;padding:12px;margin:12px 0}.camera-profile-edit>summary{cursor:pointer;padding:4px}.camera-profile-edit .options{margin-top:10px}

.event-detail-cols{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(280px,1fr);gap:14px}.event-detail-cols .panel{min-width:0}.event-thumb{width:100%;max-height:220px;object-fit:contain;border-radius:8px;background:#090d17}.readable{word-wrap:break-word;overflow-wrap:anywhere}.public-clip{border:1px solid var(--edge);border-radius:9px;margin:10px 0;overflow:hidden;background:#111b2c}.public-clip summary{display:grid;grid-template-columns:minmax(0,1.5fr) 190px 86px 18px;gap:12px;align-items:center;padding:11px 12px;cursor:pointer;list-style:none}.public-clip summary::-webkit-details-marker{display:none}.public-clip summary::after{content:"▾";color:var(--cyan);text-align:right}.public-clip[open] summary::after{content:"▴"}.public-clip[open] summary{border-bottom:1px solid var(--edge)}.public-clip .public-video{padding:15px}.public-clip .public-video.with-notes{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(200px,1fr);align-items:start;gap:16px}.public-clip .public-video video{display:block;width:100%;aspect-ratio:16/9;max-height:480px;object-fit:contain;background:#05070c;border-radius:8px}.public-clip .public-notes{background:#0c1624;border:1px solid var(--edge);border-radius:8px;padding:14px;white-space:pre-wrap;overflow-wrap:anywhere;max-height:480px;overflow:auto}.public-clip .public-notes h3{margin:0 0 10px;font-size:15px}.public-clip .public-notes p{margin:0}.public-clip-title{font-weight:650;overflow-wrap:anywhere}.public-clip-date{font-size:13px;color:var(--muted);white-space:nowrap}.public-clip-preview{display:block;width:76px;height:46px;object-fit:cover;border-radius:5px;background:#0a111f}@media(max-width:760px){.calendar-cell{min-height:54px;padding:6px 2px}.public-clip .public-video{grid-template-columns:1fr}.cols,.event-detail-cols{grid-template-columns:1fr}.grid{grid-template-columns:1fr}table{font-size:13px}th,td{padding:9px 3px}.shell{padding:18px 12px}.options{grid-template-columns:1fr}.change-title{grid-template-columns:minmax(0,1fr) 16px;gap:10px}.release-when{grid-column:1;grid-row:2;text-align:left}.change-title::after{grid-column:2;grid-row:1}.public-clip summary{grid-template-columns:minmax(0,1fr) 76px 18px;gap:8px}.public-clip-date{grid-column:1;grid-row:2}.public-clip-preview{grid-column:2;grid-row:1 / span 2}.public-clip summary::after{grid-column:3;grid-row:1}}

/* Fixed two-row header: brand/actions above one stable row of floating menus. */
.site-header{position:relative;z-index:50;background:#102034;border:1px solid #2a4058;border-radius:12px;padding:14px 16px;margin-bottom:25px}
.header-top{display:flex;justify-content:space-between;align-items:center;gap:12px}
.header-actions{display:flex;align-items:center;gap:9px;flex-shrink:0}
.site-nav{display:flex;align-items:center;justify-content:flex-start;gap:9px;margin-top:14px;position:relative;z-index:2}
.site-nav .nav-link,.header-actions .nav-bell,.header-actions .nav-account>summary{font-size:13px;white-space:nowrap;padding:8px 12px;background:#162b40;border-color:#3c5469}
.site-nav .nav-dashboard{background:#e8f1f7;color:#102034;border-color:#e8f1f7;font-weight:650}
.site-nav .nav-dashboard:hover{background:#cde3f0}
.nav-menu{position:relative}.nav-menu>summary{list-style:none;cursor:pointer;user-select:none}
.nav-menu>summary::-webkit-details-marker{display:none}
.nav-menu[open]>summary{background:#284963;border-color:#73a1b9}
.nav-dropdown{position:absolute;left:0;top:calc(100% + 7px);background:#132438;border:1px solid #39566a;border-radius:9px;box-shadow:0 12px 35px rgba(0,0,0,.65);padding:7px;min-width:215px;max-width:290px;z-index:110;display:grid;gap:3px}
.nav-dropdown a,.mobile-panel a{display:block;text-decoration:none;padding:10px 12px;border-radius:6px;color:var(--text);font-size:14px}
.nav-dropdown a:hover,.mobile-panel a:hover,.nav-dropdown a:focus-visible,.mobile-panel a:focus-visible{background:#29495d}
.nav-dropdown form{margin:2px}.nav-dropdown form button{width:100%}
.nav-account .nav-dropdown{left:auto;right:0;min-width:185px}
.nav-count{display:inline-grid;place-items:center;min-width:20px;height:20px;border-radius:99px;background:#a85d53;color:#fff;padding:0 5px;font-size:12px}
.nav-mobile{display:none;position:relative}
.mobile-panel{position:absolute;right:0;top:calc(100% + 8px);background:#14263b;border:1px solid #39566a;border-radius:10px;width:min(340px,calc(100vw - 24px));max-height:min(70vh,550px);overflow:auto;z-index:120;padding:10px;box-shadow:0 10px 40px #0009}
.mobile-panel form button{width:100%}
@media(max-width:760px){.site-header{padding:12px;margin-bottom:18px}.header-top .logo{font-size:17px}.header-actions .nav-account{display:none}.site-nav{display:none}.nav-mobile{display:block}.header-actions .nav-bell{padding:8px}.live-photo-grid{grid-template-columns:1fr}}
#live-back-to-camera[hidden]{display:none!important}
.live-surface{position:relative;width:100%;aspect-ratio:16/9;background:#070c14;border:1px solid var(--edge);border-radius:10px;overflow:hidden;touch-action:none}
.live-surface canvas{display:block;width:100%;height:100%;object-fit:contain}.live-mark{position:absolute;top:12px;padding:5px 10px;border:1px solid #668aa1;border-radius:5px;background:#071423df;font-size:12px;pointer-events:none}
.live-mark.left{left:12px}.live-mark.right{right:12px}.live-photo-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.live-photo-grid label{font-size:13px}
.live-controls{display:flex;align-items:center;flex-wrap:wrap;gap:10px;margin:10px 0}.live-controls label{display:flex;align-items:center;gap:6px;margin:0;font-size:13px}.live-controls input[type=range]{width:130px;padding:0}.live-controls select{width:auto}


/* Searchable product documentation */
.help-searchbar{display:flex;gap:8px;margin:18px 0 8px}.help-searchbar input{min-width:0;flex:1}.help-searchbar button{flex-shrink:0}
.help-doc-layout{display:grid;grid-template-columns:260px minmax(0,1fr);align-items:start;gap:18px;margin-top:18px}
.help-doc-sidebar{position:sticky;top:12px;max-height:calc(100vh - 24px);overflow-y:auto;padding:15px 12px;border:1px solid var(--edge);border-radius:12px;background:#121e30}
.help-doc-side-title{font-weight:750;color:var(--muted);letter-spacing:.08em;font-size:12px;margin-bottom:12px}
.help-doc-group{margin:5px 0;border-bottom:1px solid var(--edge);padding-bottom:6px}
.help-doc-category{border-bottom:1px solid var(--edge);padding:3px 0}.help-doc-category>summary{font-weight:750;cursor:pointer;padding:10px 4px;list-style:none}.help-doc-category>summary::-webkit-details-marker{display:none}.help-doc-category .help-doc-group{margin-left:10px}.help-doc-category[hidden],.help-doc-subcategory[hidden]{display:none!important}.help-doc-subcategory{margin-left:7px;padding-left:6px;border-left:1px solid var(--edge)}.help-doc-subcategory>summary{font-weight:650;cursor:pointer;padding:8px 4px;list-style:none}.help-doc-subcategory>summary::-webkit-details-marker{display:none}.help-doc-path{font-size:12px;color:var(--muted);margin:0 0 7px}
.help-doc-group summary{font-weight:650;cursor:pointer;padding:8px 4px;display:flex;justify-content:space-between;gap:4px;list-style:none}
.help-doc-group summary::-webkit-details-marker{display:none}.help-doc-group summary span{font-weight:400;color:var(--muted)}
.help-doc-links{display:grid;gap:2px;padding:2px 4px 8px}.help-doc-links a{padding:5px 8px;border-radius:5px;text-decoration:none;color:#cbddec;font-size:13px}.help-doc-links a:hover{background:#2a4357;color:#fff}
.help-doc-chapter{margin:0 0 18px;background:var(--panel);border:1px solid var(--edge);border-radius:12px;padding:18px}
.help-doc-chapter>h2{font-size:21px;margin-bottom:14px;padding-bottom:12px;border-bottom:1px solid var(--edge)}
.help-doc-item{padding:12px 0;border-bottom:1px solid #28374a;scroll-margin-top:15px}.help-doc-item:last-child{border-bottom:0}.help-doc-item h3{font-size:16px;margin:0 0 5px}.help-doc-item p{color:#b7c8d8;margin:0;line-height:1.7}
.help-doc-item:target{outline:2px solid var(--cyan);outline-offset:3px;border-radius:4px}
.help-doc-item[hidden],.help-doc-chapter[hidden],.help-doc-group[hidden],.help-doc-link[hidden],#help-no-results[hidden]{display:none!important}
@media(max-width:760px){.help-doc-layout{grid-template-columns:1fr}.help-doc-sidebar{position:static;max-height:280px}.help-doc-chapter{padding:12px}.help-searchbar{flex-wrap:wrap}}


.public-media-tabs{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0 18px}.public-media-tabs .button{background:transparent;border-color:var(--edge)}.public-media-tabs .active{background:#25485b;border-color:var(--cyan)}.public-media-pagination{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-top:16px}.photo-gallery-filters{align-items:end}.photo-gallery-filters label{flex:1 1 175px;margin:0}.photo-gallery-filters button{flex:0 0 auto}.photo-gallery-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin:16px 0}
.photo-gallery-card{display:flex;flex-direction:column;gap:8px;padding:10px;background:var(--panel);border:1px solid var(--edge);border-radius:10px;text-decoration:none;color:var(--text);min-width:0}
.photo-gallery-card img{width:100%;aspect-ratio:4/3;object-fit:cover;border-radius:7px}
/* Scheduled job preview slots never collapse when no thumbnail exists. */
.job-estimate-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.job-estimate-grid>div{min-width:0}@media(max-width:760px){.job-estimate-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
#job-estimate{min-height:160px}
.job-thumbnail{position:relative;width:100%;aspect-ratio:16/9;overflow:hidden;border-radius:7px;background:#0b1828}
.photo-gallery-card .job-thumbnail img{width:100%;height:100%;aspect-ratio:auto;display:block;object-fit:cover;border-radius:0}
.job-thumb-placeholder{width:100%;height:100%;display:flex;flex-direction:column;justify-content:center;align-items:center;gap:6px;text-align:center;color:#adbed0;padding:12px}
.job-thumbnail img[hidden]{display:none!important}.job-thumb-placeholder[hidden]{display:none!important}.job-thumb-icon{font-size:28px;line-height:1.2}
.photo-gallery-card:hover{border-color:var(--cyan)}.photo-detail-image{width:100%;max-height:75vh;object-fit:contain;background:#000;border-radius:9px}
.storage-selection-bar{position:sticky;bottom:0;background:#182c41;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;padding:12px;border:1px solid #516a80;border-radius:9px;z-index:10}
.storage-modal{border:1px solid #6d8195;background:#17283d;color:#f2f8ff;max-width:min(520px,92vw);border-radius:12px;padding:24px}.storage-modal::backdrop{background:#020914ce}
@media(max-width:760px){.photo-gallery-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
.context-help{float:right;margin:7px 0 0 14px}.context-help .button{font-size:13px;padding:5px 12px}.storage-tab-active{background:#376d82;border-color:#75dbed}.storage-filters label{flex:1 1 135px;min-width:125px}.storage-filters button{margin-top:24px}.help-doc-chapter{scroll-margin-top:15px}
.about-link-groups{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}
.about-link-groups>div{background:#0b192b;border:1px solid var(--edge);border-radius:9px;padding:14px}
.about-link-groups h3{margin:0 0 8px;font-size:15px}.about-link-groups p{line-height:1.9;margin:0}
#software-updates button:disabled{opacity:.48;cursor:not-allowed}

/* About page: responsive cards, self-hosted brand marks and readable names. */
.about-hero{display:grid;grid-template-columns:minmax(155px,210px) minmax(0,1fr);align-items:center;gap:26px}
.about-hero-art{display:flex;justify-content:center;align-items:center}
.about-hero-art img{display:block;width:min(100%,210px);height:auto;aspect-ratio:1;object-fit:contain;border-radius:24px;border:2px solid #39a5ff;box-shadow:0 0 22px #148de477}
.about-hero-text{min-width:0;border-left:2px solid #38566f;padding-left:24px}
.about-hero-text h2{margin-top:0}.about-hero-text p:last-child{margin-bottom:0}
.about-biography p{line-height:1.65;max-width:100ch}.about-biography p:last-child{margin-bottom:0}
.about-card-grid{display:grid;grid-template-columns:1fr 1.14fr 1fr;gap:14px;align-items:stretch}
.about-card{min-width:0;margin:0;padding:17px 17px 20px}
.about-card-title{display:flex;align-items:center;gap:11px;font-size:19px;margin:0 0 14px;line-height:1.2}
.about-heading-icon{width:24px;height:24px;display:inline-flex;flex:0 0 24px;align-items:center;justify-content:center}
.about-heading-icon img{width:22px;height:22px;filter:brightness(0) invert(1);opacity:.8}
.about-link{display:flex;align-items:center;gap:10px;margin:9px 0;color:#75c9ff;text-decoration:none;min-height:30px;min-width:0;line-height:1.35}
.about-link>span:last-child{text-decoration:underline;text-underline-offset:2px;overflow-wrap:anywhere}
.about-link:hover>span:last-child,.about-link:focus-visible>span:last-child{color:#d5efff}
.about-symbol{width:30px;height:30px;flex:0 0 30px;display:inline-flex;justify-content:center;align-items:center;border-radius:8px;background:#34506b}
.about-symbol img{width:19px;height:19px;object-fit:contain;filter:brightness(0) invert(1)}
.about-symbol-youtube{background:#e62117}.about-symbol-twitch{background:#9146ff}
.about-symbol-discord{background:#5865f2}.about-symbol-tiktok{background:#191919}
.about-symbol-bluesky{background:#1686ed}.about-symbol-instagram{background:#d34e9a}
.about-symbol-facebook{background:#0866ff}.about-symbol-threads{background:#262a32}
.about-symbol-spotify{background:#1db954}.about-symbol-apple{background:#e94b72}
.about-symbol-github{background:#313e52}.about-social-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.about-media-card{display:flex;flex-direction:column;gap:17px}.about-music-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
.about-support{border-top:1px solid #3a536d;padding-top:16px}
@media(max-width:1080px){.about-card-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.about-media-card{grid-column:1/-1}.about-media-card .about-music-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:720px){.about-hero{grid-template-columns:1fr;gap:20px}.about-hero-text{border-left:0;border-top:2px solid #38566f;padding:16px 0 0}.about-card-grid{grid-template-columns:1fr}.about-media-card{grid-column:auto}}
@media(max-width:390px){.about-social-grid,.about-music-grid{grid-template-columns:1fr}}
.software-password{display:block;max-width:430px;margin-bottom:10px}
.software-password input{max-width:420px;width:100%;display:block;margin-top:6px}

/* Browser-local colour themes. No server-side user state is modified. */
:root{--theme-grad:#1a3146;--theme-header:#102034;--theme-control:#162b40;--theme-choice:#25485b;--theme-hover:#316179;--theme-field:#091423;--theme-dropdown:#132438;--theme-notice:#172b3c;--theme-hair:#39566a}
:root[data-moon-theme="red"]{--bg:#0c080c;--panel:#231219;--edge:#5c303a;--text:#ffe6e9;--muted:#d2a5ac;--cyan:#ff7789;--theme-grad:#431a25;--theme-header:#28111c;--theme-control:#381b26;--theme-choice:#673040;--theme-hover:#844052;--theme-field:#190b13;--theme-dropdown:#2d1520;--theme-notice:#3a202b;--theme-hair:#77404d}
:root[data-moon-theme="green"]{--bg:#08120f;--panel:#13281f;--edge:#2a5744;--text:#e1f9eb;--muted:#a1cdb5;--cyan:#79e3aa;--theme-grad:#164b34;--theme-header:#102d23;--theme-control:#174032;--theme-choice:#286c4f;--theme-hover:#338665;--theme-field:#091f17;--theme-dropdown:#143729;--theme-notice:#1a4231;--theme-hair:#3b7756}
:root[data-moon-theme="yellow"]{--bg:#141007;--panel:#2a2416;--edge:#605032;--text:#fff3d2;--muted:#d4bd8b;--cyan:#f6d36b;--theme-grad:#51401d;--theme-header:#2e291a;--theme-control:#41351e;--theme-choice:#6c5427;--theme-hover:#896d32;--theme-field:#201a10;--theme-dropdown:#382e1c;--theme-notice:#473b25;--theme-hair:#836a3b}
body{background:radial-gradient(circle at 85% 0%,var(--theme-grad),var(--bg) 50%)}
.site-header{background:var(--theme-header);border-color:var(--edge)}
.site-nav .nav-link,.header-actions .nav-bell,.header-actions .nav-account>summary{background:var(--theme-control);border-color:var(--edge)}
.site-nav .nav-dashboard{background:var(--text);color:var(--bg);border-color:var(--text)}
.site-nav .nav-dashboard:hover{background:var(--muted)}
button,.button{background:var(--theme-choice);border-color:var(--edge);color:var(--text)}
button:hover,.button:hover{background:var(--theme-hover)}
/* Destructive and status actions keep their warning semantics in every visitor palette. */
button.danger,.button.danger{background:#5a202f;border-color:#bf6473;color:#fff}
button.danger:hover,.button.danger:hover{background:#762a3d}
input,select,textarea{background:var(--theme-field);border-color:var(--edge);color:var(--text)}
.nav-dropdown,.mobile-panel{background:var(--theme-dropdown);border-color:var(--theme-hair)}
.nav-dropdown a:hover,.mobile-panel a:hover,.nav-dropdown a:focus-visible,.mobile-panel a:focus-visible{background:var(--theme-hover)}
.nav-menu[open]>summary{background:var(--theme-hover);border-color:var(--edge)}
.notice{background:var(--theme-notice);border-color:var(--edge)}
@media(max-width:760px){.header-actions{gap:6px}.header-top .logo{font-size:16px}}

/* Theme palette consistency: do not recolour actual camera/video imagery or semantic warnings. */
.investigator-compare-controls,.camera-settings-preview,.help-doc-sidebar,.public-clip,
.public-clip .public-notes,.storage-selection-bar,.storage-modal,.about-link-groups>div,
.about-symbol:not([class*="about-symbol-"]){background:var(--theme-dropdown)}
.calendar-cell,.stats span,.job-thumbnail{background:var(--theme-control)}
.calendar-cell.selected,.storage-tab-active,.public-media-tabs .active{background:var(--theme-choice);border-color:var(--cyan)}
.help-doc-links a:hover,.help-doc-links a:focus-visible{background:var(--theme-hover)}
.about-link{color:var(--cyan)}.about-link:hover>span:last-child,.about-link:focus-visible>span:last-child{color:var(--text)}
.about-hero-text{border-color:var(--edge)}.about-support{border-color:var(--edge)}
.about-hero-art img{border-color:var(--cyan);box-shadow:0 0 18px var(--edge)}
.live-mark{background:var(--theme-dropdown);border-color:var(--edge)}
.investigator-stage .compare-label{background:var(--theme-dropdown);border-color:var(--edge)}
.investigator-stage .compare-divider:after{background:var(--theme-control)}
/* Public theme menu: compact current-colour marker, accessible options on demand. */
.theme-menu{position:relative}
.theme-menu>summary{display:flex;align-items:center;justify-content:center;min-width:38px;min-height:38px;padding:6px 8px!important;background:var(--theme-control);border:1px solid var(--edge);border-radius:7px;cursor:pointer}
.theme-menu>summary:focus-visible{outline:2px solid var(--cyan);outline-offset:2px}
.theme-menu .nav-dropdown{left:auto;right:0;min-width:208px;max-width:calc(100vw - 30px)}
.theme-menu .nav-dropdown>strong{padding:6px 10px;color:var(--text)}
.theme-swatch{width:17px;height:17px;border-radius:50%;display:inline-block;flex:0 0 17px;border:1px solid rgba(255,255,255,.32);background:var(--cyan)}
.theme-swatch-blue{background:#75dbed}.theme-swatch-red{background:#ff7789}.theme-swatch-green{background:#79e3aa}.theme-swatch-yellow{background:#f6d36b}
.theme-menu .theme-current{background:var(--cyan)}
.theme-choice{display:flex;align-items:center;gap:10px;width:100%;padding:9px 10px;text-align:left;font-size:14px;color:var(--text);background:transparent;border:1px solid transparent;border-radius:6px}
.theme-choice:hover,.theme-choice:focus-visible{background:var(--theme-hover)}
.theme-choice[aria-pressed="true"]{border-color:var(--cyan);background:var(--theme-control)}
.theme-choice .theme-check{margin-left:auto;font-weight:700;color:var(--cyan)}
/* Exposure countdown is a visual status, not a shutter control. */
.photo-progress{border:1px solid var(--edge);border-radius:9px;padding:12px;margin:10px 0;background:var(--theme-dropdown)}
.photo-progress[hidden]{display:none!important}.photo-progress .between{font-size:14px}.photo-progress strong{font-variant-numeric:tabular-nums;font-size:20px}
.photo-progress progress{width:100%;height:12px;accent-color:var(--cyan);margin:9px 0 2px}
</style></head><body><main class="shell"><header class="site-header">
  <div class="header-top">
    <div><div class="logo"><img src="{{url_for('moon_icon',name='moon-cheese-48.png')}}" width="26" height="26" style="vertical-align:middle;border-radius:6px;margin-right:7px" alt="">MOON CHEESE <span style="color:var(--cyan)">/ {{ site_title }}</span></div><div class="sub">Sky monitoring · Observation system</div></div>
    <div class="header-actions">
    <details class="nav-menu theme-menu" data-nav-menu>
      <summary class="button" aria-label="Select colour theme" title="Colour theme"><span class="theme-swatch theme-current" id="moon-theme-current" aria-hidden="true"></span></summary>
      <div class="nav-dropdown" role="group" aria-label="Select theme"><strong>Select theme</strong>
        <button type="button" class="theme-choice" data-theme-choice="blue" aria-pressed="false"><span class="theme-swatch theme-swatch-blue" aria-hidden="true"></span>Blue<span class="theme-check" aria-hidden="true"></span></button>
        <button type="button" class="theme-choice" data-theme-choice="red" aria-pressed="false"><span class="theme-swatch theme-swatch-red" aria-hidden="true"></span>Red<span class="theme-check" aria-hidden="true"></span></button>
        <button type="button" class="theme-choice" data-theme-choice="green" aria-pressed="false"><span class="theme-swatch theme-swatch-green" aria-hidden="true"></span>Green<span class="theme-check" aria-hidden="true"></span></button>
        <button type="button" class="theme-choice" data-theme-choice="yellow" aria-pressed="false"><span class="theme-swatch theme-swatch-yellow" aria-hidden="true"></span>Cheese Yellow<span class="theme-check" aria-hidden="true"></span></button>
      </div>
    </details>
    {% if public_view and not user %}<a class="button" href="{{ url_for('login') }}">Log in</a>{% endif %}
    {% if user %}
      <a class="button nav-bell" href="{{ url_for('notices_page') }}" aria-label="Notifications: {{ unread_notices }} unread" title="Notifications"><span aria-hidden="true">🔔</span>{% if unread_notices %} <span class="nav-count">{{ unread_notices }}</span>{% endif %}</a>
      <details class="nav-menu nav-account" data-nav-menu><summary class="button nav-link">Account ▾</summary><div class="nav-dropdown"><a href="{{ url_for('account') }}">My account</a><form method="post" action="{{ url_for('logout') }}"><input type="hidden" name="csrf" value="{{ csrf }}"><button type="submit">Sign out</button></form></div></details>
      <details class="nav-mobile" data-nav-menu><summary class="button" aria-label="Open menu">☰ Menu</summary><div class="mobile-panel"><a href="{{ url_for('home') }}">Dashboard</a>{% if admin %}<a href="{{ url_for('live_camera') }}">Photography</a>{% endif %}<a href="{{ url_for('home') }}#recordings">Recordings</a><a href="{{ url_for('calendar_page') }}">Calendar</a><a href="{{ url_for('photo_gallery') }}">Photograph Gallery</a><a href="{{url_for('jobs_list',kind='scheduled_video')}}">Scheduled Video</a><a href="{{url_for('jobs_list',kind='timelapse')}}">Time-lapse Studio</a><a href="{{ url_for('notices_page') }}">Notifications ({{ unread_notices }})</a>{% if admin %}<a href="{{ url_for('settings') }}">Settings</a><a href="{{ url_for('users') }}">Users & Access</a><a href="{{ url_for('system_page') }}">System Health</a><a href="{{ url_for('storage_page') }}">Storage Management</a><a href="{{ url_for('system_admin') }}">System Administration</a>{% endif %}{% if public_enabled and admin %}<a href="{{ url_for('public_page') }}" target="_blank" rel="noopener">Public page ↗</a>{% endif %}<a href="{{ url_for('account') }}">My account</a><a href="{{ url_for('help_page') }}">Help</a><a href="{{ url_for('history') }}">Version History</a><a href="{{url_for('about_moon_cheese')}}">About Moon Cheese</a><form method="post" action="{{ url_for('logout') }}"><input type="hidden" name="csrf" value="{{ csrf }}"><button type="submit">Sign out</button></form></div></details>
    {% endif %}
    </div>
  </div>
  {% if user %}<nav class="site-nav" aria-label="Main navigation">
    <a class="button nav-link nav-dashboard" href="{{ url_for('home') }}">▦ Dashboard</a>
    <details class="nav-menu" data-nav-menu><summary class="button nav-link">◉ Observations ▾</summary><div class="nav-dropdown">{% if admin %}<a href="{{ url_for('live_camera') }}">Photography</a>{% endif %}<a href="{{ url_for('home') }}#recordings">Recordings</a><a href="{{ url_for('calendar_page') }}">Calendar</a><a href="{{ url_for('photo_gallery') }}">Photograph Gallery</a><a href="{{url_for('jobs_list',kind='scheduled_video')}}">Scheduled Video</a><a href="{{url_for('jobs_list',kind='timelapse')}}">Time-lapse Studio</a>{% if public_enabled and admin %}<a href="{{ url_for('public_page') }}" target="_blank" rel="noopener">Public page ↗</a>{% endif %}</div></details>
    {% if admin %}<details class="nav-menu" data-nav-menu><summary class="button nav-link">⚙ Administration ▾</summary><div class="nav-dropdown"><a href="{{ url_for('settings') }}">Camera &amp; Detector Settings</a><a href="{{ url_for('users') }}">Users &amp; Access</a><a href="{{ url_for('system_page') }}">System Health</a><a href="{{ url_for('storage_page') }}">Storage Management</a><a href="{{ url_for('system_admin') }}">System Administration</a></div></details>{% endif %}
    <details class="nav-menu" data-nav-menu><summary class="button nav-link">▤ Information ▾</summary><div class="nav-dropdown"><a href="{{ url_for('help_page') }}">Help</a><a href="{{ url_for('history') }}">Version History</a><a href="{{url_for('about_moon_cheese')}}">About Moon Cheese</a></div></details>
  </nav>{% endif %}
  </header>
<script src="{{ url_for('theme_js') }}" defer></script>
<script src="{{ url_for('navigation_js') }}" defer></script>
{% if help_anchor and user %}<div class="context-help"><a class="button" href="{{ url_for('help_page') }}#chapter-{{ help_anchor }}" title="Open help for this page" aria-label="Help for {{ title }}">? Help</a></div>{% endif %}
{{ content|safe }}<div class="foot">Moon Cheese UAP Detector by Dr Ravenholm · <a href="https://transparent-aluminium.net/" target="_blank" rel="noopener noreferrer">Transparent-Aluminium.net</a> · v{{app_version}} · A motion detection is not proof of an unidentified object.</div></main></body></html>'''


def current_user():
    uid = session.get('uid')
    version = session.get('sv')
    if not isinstance(uid, int) or not isinstance(version, int):
        return None
    with connection() as db:
        row = db.execute('SELECT id, username, role, enabled, session_version FROM users WHERE id=?',
                         (uid,)).fetchone()
    if not row or not row['enabled'] or row['session_version'] != version:
        return None
    return dict(row)


def logged_in():
    return current_user() is not None


def is_admin():
    user = current_user()
    return bool(user and user['role'] == 'admin')


ADMIN_ENDPOINTS = {
    'detector_control', 'pin_event', 'update_event', 'delete_event',
    'settings', 'system_page', 'users', 'create_user', 'edit_user',
    'storage_page', 'photo_gallery_delete', 'storage_js', 'system_power', 'system_admin',
    'publish_event', 'test_profile_preview', 'profile_preview_status', 'profile_preview_image',
    'network_action','network_status','network_confirm','network_ui_js','network_confirm_js',
    'software_action','software_status','software_update_js', 'jobs_js', 'job_storage', 'job_cancel', 'live_camera', 'photo_request', 'photo_status', 'photo_download', 'photo_image', 'hd_preview', 'live_js'
}


@app.before_request
def restrict_admin_pages():
    if request.endpoint in ADMIN_ENDPOINTS and not is_admin():
        if not logged_in():
            return redirect(url_for('login', next='network_confirm') if request.endpoint == 'network_confirm' else url_for('login'))
        abort(403)


def csrf_token():
    if 'csrf' not in session:
        session['csrf'] = secrets.token_urlsafe(24)
    return session['csrf']


def check_csrf():
    if not secrets.compare_digest(request.form.get('csrf', ''), session.get('csrf', '_')):
        abort(403)


def effective_site_title(config=None):
    """A shared camera name across login, private and public pages."""
    config = config if config is not None else read_config()
    return str(config.get('public_title') or '').strip() or 'Sky Camera'


HELP_CHAPTER_BY_ENDPOINT = {
    'home':'Dashboard', 'event':'Recorded events', 'delete_event':'Recorded events',
    'settings':'Camera settings', 'live_camera':'Photography', 'calendar_page':'Observation calendar',
    'photo_gallery':'Photograph Gallery', 'photo_detail':'Photograph Gallery',
    'notices_page':'Notifications and reports', 'system_page':'System health and troubleshooting',
    'storage_page':'Storage Management', 'job_storage':'Storage Management', 'system_admin':'System Administration',
    'users':'Accounts and access', 'edit_user':'Accounts and access', 'account':'Accounts and access',
    'public_page':'Public observation pages', 'public_job_detail':'Public observation pages',
    'history':'Version history', 'about_moon_cheese':'About Moon Cheese', 'network_action':'System Administration', 'network_confirm':'System Administration',
}


def page_help_anchor():
    endpoint=request.endpoint or ''
    if endpoint in ('jobs_list', 'job_detail'):
        kind=request.view_args.get('kind') if request.view_args else None
        if endpoint=='job_detail':
            try:
                job=oj.item(request.view_args.get('job_id'))
                kind=job['kind'] if job else None
            except (KeyError, TypeError, ValueError):kind=None
        return 'time-lapse-studio' if kind=='timelapse' else 'scheduled-video'
    chapter=HELP_CHAPTER_BY_ENDPOINT.get(endpoint)
    return ''.join(x if x.isalnum() else '-' for x in chapter.lower()).strip('-') if chapter and endpoint!='help_page' else None


def render_page(content, title='Dashboard', public_view=False, **kwargs):
    user = current_user()
    with connection() as db:
        unread_notices = (db.execute('SELECT COUNT(*) FROM notices WHERE user_id=? AND read_at IS NULL', (user['id'],)).fetchone()[0] if user else 0)
    page = render_template_string(content, csrf=csrf_token(), admin=is_admin(), **kwargs)
    return render_template_string(BASE, content=page, title=title,
                                  csrf=csrf_token(), admin=is_admin(), user=current_user(),
                                  public_view=public_view, site_title=effective_site_title(), unread_notices=unread_notices,
                                  help_anchor=page_help_anchor(),
                                  public_enabled=public_allowed(),app_version=APP_VERSION)


@app.after_request
def headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Cache-Control'] = ('public, max-age=86400' if request.endpoint in ('moon_icon','about_icon') else 'no-store')
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    return response



def login_destination():
    # IP changes are confirmed only by an authenticated administrator reaching
    # the pending NEW IP. Never redirect users logging in at the old address.
    if is_admin():
        pending = network_setup.pending_change()
        if pending and pending.get('expires',0)>time.time() and request.host.split(':',1)[0] == pending.get('new_ip'):
            return url_for('network_confirm')
    return url_for('home')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if logged_in():
        return redirect(login_destination())
    msg = ''
    if request.method == 'POST':
        check_csrf()
        key = request.remote_addr or 'unknown'
        q = ATTEMPTS[key]
        now = time.monotonic()
        while q and now - q[0] > 300:
            q.popleft()
        if len(q) >= 10:
            msg = 'Too many attempts. Try again in a few minutes.'
        else:
            q.append(now)
            with connection() as db:
                found = db.execute('SELECT id, password_hash, enabled, session_version FROM users WHERE username=?',
                                   (request.form.get('username', ''),)).fetchone()
            # Use the same error for unknown, disabled and incorrectly authenticated accounts.
            valid_pass = bool(found and check_password_hash(found['password_hash'], request.form.get('password', '')))
            if found and found['enabled'] and valid_pass:
                session.clear()
                session['uid'] = found['id']
                session['sv'] = found['session_version']
                session.permanent = True
                return redirect(login_destination())
            msg = 'Invalid username or password.'
    return render_page('''<div class="panel auth"><h1>Secure sign in</h1>{% if public_enabled %}<p><a href="{{ url_for('home') }}">← Back to sky camera</a></p>{% endif %}{% if request.args.get('changed') %}<p class="notice">Account updated. Please sign in again.</p>{% endif %}{% if pending_login_confirmation %}<p class="notice"><strong>Confirm the new IP address:</strong> sign in as an administrator to open the confirmation screen. The earlier network settings will return automatically if you do not confirm before the deadline.</p>{% endif %}<p class="muted">Your camera events and recordings stay private.</p>
    {% if msg %}<p class="error">{{ msg }}</p>{% endif %}
    <form method="post"><input type="hidden" name="csrf" value="{{ csrf }}"><label>Username</label><input name="username" required autofocus autocomplete="username"><label>Password</label><input name="password" type="password" required autocomplete="current-password"><p><button type="submit">Sign in</button></p></form></div>''', title='Login', msg=msg, public_enabled=public_allowed(),
                    pending_login_confirmation=(network_setup.pending_change().get('expires',0)>time.time() and network_setup.pending_change().get('new_ip') == request.host.split(':',1)[0]))


@app.route('/logout', methods=['POST'])
def logout():
    check_csrf()
    session.clear()
    return redirect(url_for('home'))


def require_login():
    if not logged_in():
        return redirect(url_for('login'))
    return None


@app.route('/')
def home():
    if not logged_in():
        if public_allowed():
            return public_page()
        return redirect(url_for('login'))
    camera_job = oj.active()
    q = request.args.get('q', '').strip()[:100]
    selected = request.args.get('status', 'all').lower()
    pinned_only = request.args.get('pinned') == '1'
    sharing = request.args.get('sharing', 'all')
    if sharing not in ('all', 'public', 'private'):
        sharing = 'all'
    if selected not in STATUSES and selected != 'all':
        selected = 'all'
    try:
        page = max(1, int(request.args.get('page', '1')))
    except ValueError:
        page = 1
    # Escape SQL LIKE wildcards so searching e.g. 100% behaves literally.
    pattern = '%' + q.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
    where, params = [], []
    if pinned_only:
        where.append('pinned=1')
    if sharing == 'public':
        where.append('public=1')
    elif sharing == 'private':
        where.append('public=0')
    if q:
        where.append("(kind LIKE ? ESCAPE '\\' COLLATE NOCASE OR note LIKE ? ESCAPE '\\' COLLATE NOCASE)")
        params.extend((pattern, pattern))
    if selected != 'all':
        where.append('status=?')
        params.append(selected)
    clause = (' WHERE ' + ' AND '.join(where)) if where else ''
    with connection() as conn:
        total = conn.execute('SELECT COUNT(*) FROM events' + clause, params).fetchone()[0]
        page_count = max(1, (total + 49) // 50)
        page = min(page, page_count)
        events = [dict(r) for r in conn.execute('SELECT * FROM events' + clause +
                  ' ORDER BY id DESC LIMIT 50 OFFSET ?', [*params, (page - 1) * 50])]
        unseen = conn.execute("SELECT COUNT(*) FROM events WHERE status='new'").fetchone()[0]
        pinned_count = conn.execute("SELECT COUNT(*) FROM events WHERE pinned=1").fetchone()[0]
        recordings = conn.execute('SELECT COUNT(*) FROM events WHERE video IS NOT NULL').fetchone()[0]
    try:
        status = json.loads(STATUS.read_text())
        delta = (datetime.now(timezone.utc) - datetime.fromisoformat(status.get('updated', ''))).total_seconds()
        if delta > 75:
            status = {'state': 'offline', 'message': 'Detector heartbeat is stale'}
    except Exception:
        status = {'state': 'starting', 'message': 'Waiting for detector service'}
    cfg = read_config()
    return render_page('''<h1>Dashboard</h1>
    <div class="grid">
      <div class="panel"><div class="sub">Camera / detector</div><div class="value">{{ status.state|title }}</div><div class="note">{{ status.message }}</div>{% if status.state == "storm" %}<p class="hint">Event-storm protection is temporarily preventing repetitive clips. The camera preview continues.</p>{% endif %}
      {% if admin %}<form method="post" action="{{ url_for('detector_control') }}" style="margin-top:12px"><input type="hidden" name="csrf" value="{{ csrf }}">
      <input type="hidden" name="action" value="{{ 'resume' if cfg.detection_paused else 'pause' }}">
      <button type="submit" {% if not cfg.detection_paused %}class="danger"{% endif %}>{{ 'Resume detection' if cfg.detection_paused else 'Pause new detections' }}</button></form>
      <p class="hint">Pausing finishes any current clip and keeps the camera preview available.</p>{% endif %}</div>
      <div class="panel"><div class="sub">New detections</div><div class="value">{{ unseen }}</div><div class="note">Opening New changes it to Viewed</div></div>
      <div class="panel"><div class="sub">Saved recordings</div><div class="value">{{ recordings }}</div><div class="note">Across all events · {{ pinned_count }} pinned</div><div class="sub" style="margin-top:10px">Operating mode: {{ cfg.operation_mode|title }}</div></div>
    </div>
    <div class="cols"><div class="panel"><div class="between"><h2>Last camera preview</h2><button type="button" data-preview-refresh>↻ Refresh preview</button></div>
    {% if preview %}<img id="preview-image" class="preview" src="{{ url_for('preview') }}" alt="Most recent camera frame">{% else %}<p class="muted">No camera frame yet.</p>{% endif %}
    <p class="note" id="preview-note" role="status">Camera snapshot updates roughly every 4 seconds. This is not a live video stream.</p><script src="{{ url_for('ui_js') }}" defer></script></div>
    <div class="panel"><h2>Review your recordings</h2><p>Motion recordings appear as <strong>New</strong>. Open an event to see its clip, rename it, add notes or identify the object.</p>
    {% if admin %}<p class="note">Choose <a href="{{ url_for('settings') }}">Settings</a> to change the camera or schedule, or <a href="{{ url_for('storage_page') }}">Storage Management</a> to clean up recordings and photographs.</p>{% endif %}<p class="note">See <a href="{{ url_for('help_page') }}">Help</a> for explanations.</p></div></div>
    <div class="panel"><h2>Find recordings</h2>
    <form method="get" action="{{ url_for('home') }}" class="row" role="search">
    <div style="flex:2;min-width:200px"><label for="event-search">Search titles and notes</label><input id="event-search" type="search" name="q" value="{{ q }}" maxlength="100" placeholder="e.g. meteor, chicken or aircraft"></div>
    <div style="flex:1;min-width:140px"><label for="event-status">Review status</label><select id="event-status" name="status"><option value="all">All statuses</option>{% for item in statuses %}<option value="{{ item }}" {% if selected==item %}selected{% endif %}>{{ item|title }}</option>{% endfor %}</select></div>
    <div style="flex:1;min-width:140px"><label for="sharing-filter">Public sharing</label><select name="sharing" id="sharing-filter"><option value="all" {% if sharing == 'all' %}selected{% endif %}>All recordings</option><option value="public" {% if sharing == 'public' %}selected{% endif %}>Public only</option><option value="private" {% if sharing == 'private' %}selected{% endif %}>Private only</option></select></div>
    <label class="checkline" style="align-self:end"><input type="checkbox" name="pinned" value="1" {% if pinned_only %}checked{% endif %}> Pinned only</label><button type="submit" style="align-self:end">Search / filter</button><a class="button" style="align-self:end" href="{{ url_for('home') }}">Clear</a></form></div>
    {% if camera_job %}<section class="panel"><h2>Camera activity — {{'Time-lapse' if camera_job.kind=='timelapse' else 'Scheduled Video'}}</h2><p><a href="{{url_for('job_detail',job_id=camera_job.id)}}"><strong>{{camera_job.title}}</strong></a> · {{camera_job.phase}}</p><p class="note">Normal detection and dedicated photography is suspended during this session.</p>{% if camera_job.planned_frames %}<progress style="width:100%" max="{{camera_job.planned_frames}}" value="{{camera_job.completed_frames}}"></progress><p class="note">{{camera_job.completed_frames}} / {{camera_job.planned_frames}} source frames</p>{% endif %}</section>{% endif %}
    <div class="panel"><div class="between"><h2>Saved detections</h2><span class="note">{{ total }} matching event{{ '' if total==1 else 's' }}{% if total %} · page {{ page }} of {{ page_count }}{% endif %}</span></div>
    {% if events %}<table><thead><tr><th>Event</th><th>Time (local)</th><th>Status</th><th>Preview</th></tr></thead><tbody>
    {% for e in events %}<tr><td><a href="{{ url_for('event', event_id=e.id) }}">{{ e.kind }}</a>{% if e.pinned %} <span class="pin" title="Protected from automatic cleanup">★ Pinned</span>{% endif %}{% if e.public %} <span class="pill" title="Approved for the public camera page">Public</span>{% endif %}<div class="note">Event #{{ e.id }}{% if e.trigger_source %} · {{ source_labels.get(e.trigger_source, 'Detector') }}{% endif %}</div>{% if e.demo %}<div class="note">DEMO · no camera footage</div>{% endif %}</td>
    <td>{{ e.time_utc|localdt }}</td><td><span class="pill {{ e.status }}">{{ e.status }}</span></td><td>{% if e.thumbnail %}<a href="{{ url_for('event', event_id=e.id) }}"><img class="thumb" src="{{ url_for('thumbnail', event_id=e.id) }}" alt="Detection thumbnail"></a>{% else %}—{% endif %}</td></tr>{% endfor %}
    </tbody></table>
    <div class="between" style="margin-top:14px"><div>{% if page>1 %}<a class="button" href="{{ url_for('home', q=q, status=selected, pinned='1' if pinned_only else None, sharing=sharing, page=page-1) }}">← Previous</a>{% endif %}</div><div>{% if page<page_count %}<a class="button" href="{{ url_for('home', q=q, status=selected, pinned='1' if pinned_only else None, sharing=sharing, page=page+1) }}">Next →</a>{% endif %}</div></div>
    {% else %}<p class="muted">No matching recordings. Try another search or clear the filter.</p>{% endif %}</div>''', status=status, events=events, unseen=unseen, recordings=recordings, cfg=cfg,
                       q=q, selected=selected, pinned_only=pinned_only, sharing=sharing, pinned_count=pinned_count, total=total, page=page, page_count=page_count,
                       statuses=STATUSES, camera_job=camera_job, preview=(DATA / 'latest.jpg').is_file())


@app.route('/detector/control', methods=['POST'])
def detector_control():
    if not logged_in():
        return redirect(url_for('login'))
    check_csrf()
    action = request.form.get('action')
    if action not in ('pause', 'resume'):
        abort(400)
    cfg = read_config()
    cfg['detection_paused'] = action == 'pause'
    save_settings(cfg)
    return redirect(url_for('home'))

def probe_video_fps(path):
    """Read the actual file's average frame rate; do not trust event metadata."""
    try:
        result = subprocess.run(
            ['/usr/bin/ffprobe', '-v', 'error', '-select_streams', 'v:0',
             '-show_entries', 'stream=avg_frame_rate', '-of', 'default=nw=1:nk=1', str(path)],
            check=False, capture_output=True, text=True, timeout=3)
        if result.returncode != 0:
            return None
        first = result.stdout.strip().splitlines()[0]
        rate = float(Fraction(first))
        return round(rate, 3) if 1 <= rate <= 240 else None
    except (OSError, ValueError, IndexError, ZeroDivisionError, subprocess.TimeoutExpired):
        return None


def get_event_fps(event_id):
    fallback = float(read_config().get('fps', 15))
    try:
        path = file_for_event(event_id, 'video', RECORDINGS)
    except Exception:
        return fallback, True
    rate = probe_video_fps(path)
    return (rate, False) if rate else (fallback, True)


@app.route('/event/<int:event_id>')
def event(event_id):
    if not logged_in():
        return redirect(url_for('login'))
    with connection() as conn:
        # Only New changes on viewing; previously chosen statuses are untouched.
        if is_admin():
            conn.execute("UPDATE events SET status='viewed', viewed_at=? WHERE id=? AND status='new'",
                         (now_iso(), event_id))
        row = conn.execute('SELECT * FROM events WHERE id=?', (event_id,)).fetchone()
    if row is None:
        abort(404)
    e = dict(row)
    analysis_fps, fps_estimated = get_event_fps(event_id) if e['video'] else (0, True)
    return render_page('''<p><a href="{{ url_for('home') }}">← Back to Dashboard</a></p><h1>{{ e.kind }}</h1><p class="muted">Event #{{ e.id }} · Trigger: {{ source_labels.get(e.trigger_source or '', 'Not recorded') }} {% if e.pinned %}<span class="pin">★ Pinned — protected from cleanup</span>{% endif %}</p>
    {% if e.camera_profile is not none %}<p class="muted">Camera profile: {{ e.camera_profile|replace('custom1','Custom 1')|replace('custom2','Custom 2')|capitalize }} · Image top: {{ e.image_top_bearing }}° · Camera elevation: {{ e.camera_elevation }}°{% if e.camera_rotated %} · Rotated 180°{% endif %} <span class="note">(Manual orientation estimate)</span></p>{% endif %}
    {% if e.demo %}<p class="error">DEMO EVENT · not recorded by a camera.</p>{% endif %}
    <div class="event-detail-cols"><div class="panel"><h2>Video investigation</h2>
    {% if not e.video %}<p class="muted">No video recording is available for this event.</p>{% endif %}
    {% if e.video %}
    <section class="investigator" aria-label="Video investigation player" data-investigator data-event-id="{{ e.id }}" data-fps="{{ analysis_fps }}">
      <div class="investigator-stage" id="investigator-stage" tabindex="0" aria-label="Video image; use the comparison slider when paused">
        <div class="investigator-media" id="investigator-media">
          <video id="investigator-video" playsinline preload="metadata" src="{{ url_for('video', event_id=e.id) }}" aria-label="Event recording"></video>
          <div class="investigator-compare" id="investigator-compare" hidden aria-hidden="true">
            <canvas class="compare-canvas" id="investigator-compare-left"></canvas>
            <div class="compare-right" id="investigator-compare-right-clip"><canvas class="compare-canvas" id="investigator-compare-right"></canvas></div>
          </div>
        </div>
        <div class="compare-ui" id="investigator-compare-ui" hidden>
          <span class="compare-label compare-label-left" id="investigator-label-left">Original</span>
          <span class="compare-label compare-label-right" id="investigator-label-right">Enhanced</span>
          <span class="compare-divider" id="investigator-compare-divider"></span>
          <input class="compare-slider" type="range" min="0" max="100" step="1" value="50" id="investigator-compare-slider" aria-label="Slide to reveal left or right image">
        </div>
        <div class="investigator-fullscreen-controls"><button type="button" id="investigator-fullscreen-play" aria-label="Play or pause video">▶ / ❚❚</button><button type="button" id="investigator-exit-fullscreen" aria-label="Exit fullscreen">Exit fullscreen ✕</button></div>
      </div>
      <div class="row between"><span id="investigator-time" class="investigator-time">00:00.000 / --:--.---</span><span class="note">Source frame rate: {{ '%.2f'|format(analysis_fps) }} fps{% if fps_estimated %} (estimated){% endif %}</span></div>
      <label class="sr-only" for="investigator-seek">Seek through recording</label>
      <input type="range" class="investigator-timeline" id="investigator-seek" min="0" max="1000" step="1" value="0" aria-label="Seek through recording">
      <div class="investigator-tools" role="group" aria-label="Playback controls">
        <button type="button" id="investigator-play">▶ Play</button>
        <button type="button" id="investigator-back" title="Step back by one nominal frame">◀ Frame</button>
        <button type="button" id="investigator-next" title="Step forward by one nominal frame">Frame ▶</button>
        <label for="investigator-speed">Speed <select id="investigator-speed"><option value="0.25">0.25×</option><option value="0.5">0.5×</option><option value="1" selected>1×</option><option value="1.5">1.5×</option><option value="2">2×</option></select></label>
      </div>
      <div class="investigator-tools" role="group" aria-label="Playback view">
        <label for="investigator-view">Playback view
          <select id="investigator-view"><option value="original">Original</option><option value="detection">Detection (grayscale)</option><option value="enhanced">Low-light enhanced</option></select>
        </label>
        <span class="note">Selected view plays as one video; the source MP4 is unchanged.</span>
      </div>
      <div class="investigator-compare-controls investigator-compare-row" aria-label="Paused-frame comparison settings">
        <button type="button" id="investigator-compare-toggle" aria-pressed="false" disabled>Compare frame</button>
        <label for="investigator-view-left">Left
          <select id="investigator-view-left"><option value="original">Original</option><option value="detection">Detection (grayscale)</option><option value="enhanced">Low-light enhanced</option></select>
        </label>
        <label for="investigator-view-right">Right
          <select id="investigator-view-right"><option value="original">Original</option><option value="detection">Detection (grayscale)</option><option value="enhanced" selected>Low-light enhanced</option></select>
        </label>
        <span id="investigator-compare-info" class="note" role="status">Pause the recording to compare a frame.</span>
      </div>
      <div class="investigator-tools" role="group" aria-label="Image investigation controls">
        <label for="investigator-zoom">Zoom <input type="range" id="investigator-zoom" min="1" max="4" step="0.25" value="1"><span id="investigator-zoom-label">1×</span></label>
        <button type="button" id="investigator-reset">Reset image</button>
        <button type="button" id="investigator-fullscreen">Fullscreen</button>
      </div>
      <div class="investigator-tools" role="group" aria-label="Image enhancement controls">
        <label for="investigator-brightness">Brightness <input type="range" id="investigator-brightness" min="50" max="200" value="100" step="5"><span id="investigator-brightness-label">100%</span></label>
        <label for="investigator-contrast">Contrast <input type="range" id="investigator-contrast" min="50" max="200" value="100" step="5"><span id="investigator-contrast-label">100%</span></label>
      </div>
      <div class="investigator-tools"><button type="button" id="investigator-snapshot">Save current frame PNG</button>
        <a class="button" href="{{ url_for('video', event_id=e.id) }}?download=1">Download original MP4</a></div>
      <p class="investigator-status" id="investigator-status" role="status">Player loading…</p>
      <p class="note">Comparison appears only while paused and returns after you pause again. Frame stepping seeks approximately one recorded frame; browser decoding can limit precision. Low-light enhancement is image processing of the mixed visible/infrared NoIR recording, <strong>not</strong> a separate infrared image. Zoom, processing, and saved PNGs do not modify the source MP4.</p>
      <script src="{{ url_for('investigator_js') }}" defer></script>
    </section>{% endif %}</div>
    <div class="panel"><h2>Review event</h2><p class="note">Recorded {{ e.time_utc|localdt }} · motion score {{ e.score|int }}</p>
    {% if admin %}<form method="post" action="{{ url_for('pin_event', event_id=e.id) }}"><input type="hidden" name="csrf" value="{{ csrf }}"><input type="hidden" name="action" value="{{ 'unpin' if e.pinned else 'pin' }}"><button type="submit">{{ '★ Unpin recording' if e.pinned else '☆ Pin and protect recording' }}</button></form>
    <p class="hint">Pinned clips are protected from automatic cleanup, regardless of their review status. Unpin before manual deletion.</p>
    <form action="{{ url_for('update_event', event_id=e.id) }}" method="post"><input type="hidden" name="csrf" value="{{ csrf }}">
    <label>Event name</label><input name="title" maxlength="100" required value="{{ e.kind }}"><p class="hint">This name appears on the dashboard too.</p>
    <label>Status</label><select name="status">{% for name in statuses %}<option value="{{ name }}" {% if e.status == name %}selected{% endif %}>{{ name|title }}</option>{% endfor %}</select>
    <label>Notes</label><textarea name="note" maxlength="4000">{{ e.note }}</textarea><p><button type="submit">Save changes</button></p></form>
    <hr style="border:0;border-top:1px solid var(--edge);margin:24px 0">
    <form method="post" action="{{ url_for('publish_event', event_id=e.id) }}"><input type="hidden" name="csrf" value="{{ csrf }}">
      <label class="checkline"><input type="checkbox" name="public" value="1" {% if e.public %}checked{% endif %} {% if not e.video or e.demo %}disabled{% endif %}> Allow this clip on the public page</label>
      <label class="checkline"><input type="checkbox" name="public_note" value="1" {% if e.public_note %}checked{% endif %} {% if not e.video or e.demo %}disabled{% endif %}> Show my saved notes beside this public video</label>
      <button type="submit" {% if not e.video or e.demo %}disabled{% endif %}>Save sharing choice</button>
      <p class="hint">If notes are shared, anyone visiting the public page can read them. Previously published clips keep their notes private until you enable this separately. Published clips are excluded from automatic cleanup.</p>
    </form>
    <hr style="border:0;border-top:1px solid var(--edge);margin:24px 0">{% if e.pinned %}<p class="note">Unpin this recording before deleting it.</p>{% else %}<p><a class="button danger" href="{{ url_for('delete_event', event_id=e.id) }}">Delete event and clip…</a></p>{% endif %}<p class="note">Deleting removes the entry, video and thumbnail permanently.</p>
    {% else %}<p class="note"><strong>Status:</strong> {{ e.status|title }}</p><p class="note readable">{{ e.note }}</p>{% endif %}
    <div style="margin-top:20px"><h2>Still thumbnail</h2>
    {% if e.thumbnail %}<img class="event-thumb" src="{{ url_for('thumbnail', event_id=e.id) }}" alt="Event frame">{% else %}<p class="muted">No still image for this event.</p>{% endif %}</div></div></div>''',
                       title=e['kind'], e=e, statuses=STATUSES, analysis_fps=analysis_fps, fps_estimated=fps_estimated)


@app.route('/event/<int:event_id>/pin', methods=['POST'])
def pin_event(event_id):
    if not logged_in():
        return redirect(url_for('login'))
    check_csrf()
    action = request.form.get('action')
    if action not in ('pin', 'unpin'):
        abort(400)
    with connection() as conn:
        row = conn.execute('UPDATE events SET pinned=? WHERE id=?',
                           (1 if action == 'pin' else 0, event_id))
        if row.rowcount == 0:
            abort(404)
    return redirect(url_for('event', event_id=event_id))


@app.route('/event/<int:event_id>/update', methods=['POST'])
def update_event(event_id):
    if not logged_in():
        return redirect(url_for('login'))
    check_csrf()
    status = request.form.get('status', '')
    note = request.form.get('note', '')[:4000]
    title = request.form.get('title', '').strip()
    # Keep names short, readable, and free from control characters.
    if status not in STATUSES or not 1 <= len(title) <= 100 or any(ord(ch) < 32 for ch in title):
        abort(400)
    with connection() as conn:
        cursor = conn.execute('UPDATE events SET status=?, note=?, kind=? WHERE id=?',
                              (status, note, title, event_id))
        if cursor.rowcount == 0:
            abort(404)
    return redirect(url_for('event', event_id=event_id))


@app.route('/event/<int:event_id>/delete', methods=['GET', 'POST'])
def delete_event(event_id):
    if not logged_in():
        return redirect(url_for('login'))
    with connection() as conn:
        row = conn.execute('SELECT * FROM events WHERE id=?', (event_id,)).fetchone()
    if row is None:
        abort(404)
    e = dict(row)
    if e.get('pinned'):
        abort(409, description='Unpin the recording before deleting it.')
    if request.method == 'GET':
        return render_page('''<p><a href="{{ url_for('event', event_id=e.id) }}">← Cancel, keep event</a></p>
        <div class="panel auth"><h1>Delete {{ e.kind }}?</h1>
        <p>Event #{{ e.id }} and its video and thumbnail will be <strong>permanently deleted</strong>.</p>
        <p>This cannot be undone.</p>
        <form method="post"><input type="hidden" name="csrf" value="{{ csrf }}">
        <input type="hidden" name="confirm" value="DELETE">
        <div class="row"><button type="submit" class="danger">Yes, delete event and clip</button>
        <a class="button" href="{{ url_for('event', event_id=e.id) }}">Cancel</a></div></form></div>''',
                           title='Confirm deletion', e=e)
    check_csrf()
    if request.form.get('confirm') != 'DELETE':
        abort(400)
    # Only the server-created bare names under our recording directories can be
    # removed. Avoid deleting a file referenced by another event.
    with connection() as conn:
        row = conn.execute('SELECT video, thumbnail, pinned FROM events WHERE id=?',
                           (event_id,)).fetchone()
        if row is None:
            abort(404)
        if row['pinned']:
            abort(409, description='Unpin the recording before deleting it.')
        conn.execute('DELETE FROM events WHERE id=? AND pinned=0', (event_id,))
        for column, root in (('video', RECORDINGS), ('thumbnail', THUMBS)):
            name = row[column]
            if not name or name != Path(name).name or name.startswith('.'):
                continue
            if Path(name).suffix.lower() != ('.mp4' if column == 'video' else '.jpg'):
                continue
            still_used = conn.execute(f'SELECT 1 FROM events WHERE {column}=? LIMIT 1',
                                      (name,)).fetchone()
            if not still_used:
                candidate = root / name
                # Don't follow symlinks; all legitimate files are regular files.
                if not candidate.is_symlink():
                    candidate.unlink(missing_ok=True)
    return redirect(url_for('home'))


@app.route('/live-camera')
def live_camera():
    camera_job = oj.active()
    if camera_job:
        return render_page('''<h1>Photography temporarily unavailable</h1>
        <section class="panel"><p>The camera is being used for <strong>{{job.title}}</strong>.</p>
        <p>{{job.phase}} · Motion detection suspended</p>
        <a class="button" href="{{url_for('job_detail',job_id=job.id)}}">View observation progress</a></section>''',
        title='Photography busy',job=camera_job)
    """Admin only: the same cached detector image, not a second live stream."""
    return render_page('''<h1>Photography</h1><p class="note">Camera preview snapshots update approximately every ten seconds. Image adjustments run in your browser and do not change detection settings.</p>
    <section class="panel" id="live-root" data-csrf="{{ csrf }}"><div class="between"><h2>Camera snapshot</h2><div class="row"><button id="live-freeze" type="button">Freeze</button><button id="live-refresh" type="button">Refresh now</button></div></div>
    <div class="live-surface" id="live-stage"><canvas id="live-canvas" width="1280" height="720" aria-label="Camera snapshot"></canvas><span class="live-mark left" id="live-left-label" hidden>Original</span><span class="live-mark right" id="live-right-label" hidden>Low-light enhanced</span></div>
    <p class="note" id="live-status" role="status">Loading latest snapshot…</p>
    <p class="note" id="live-source-info" role="status">The Photography preview uses the detector's current video resolution. The Dashboard and public preview remain lightweight.</p>
    <div class="live-controls"><label>View <select id="live-view"><option value="original">Original</option><option value="detection">Detection (grayscale)</option><option value="lowlight">Low-light enhanced</option></select></label>
    <button type="button" id="live-compare">Compare frame</button><label>Left <select id="live-left"><option value="original">Original</option><option value="detection">Detection (grayscale)</option><option value="lowlight">Low-light enhanced</option></select></label><label>Right <select id="live-right"><option value="lowlight">Low-light enhanced</option><option value="original">Original</option><option value="detection">Detection (grayscale)</option></select></label></div>
    <div class="live-controls" id="live-split-row" hidden><label style="flex:1">Reveal <input id="live-split" type="range" min="0" max="100" value="50" style="flex:1;width:100%"></label><span id="live-split-value">50%</span></div>
    <div class="live-controls"><label>Zoom <input id="live-zoom" type="range" min="1" max="4" step="0.1" value="1"></label><label>Brightness <input id="live-brightness" type="range" min="40" max="200" value="100"></label><label>Contrast <input id="live-contrast" type="range" min="40" max="200" value="100"></label><button type="button" id="live-reset">Reset image</button></div>
    <div class="live-controls"><button type="button" id="live-save">Save current view PNG</button><button type="button" id="live-back-to-camera" hidden>Return to live snapshot</button></div>
    <p class="note">Saving includes the selected processing, zoom and comparison split. At 1080p recording resolution the snapshot export is 1920 × 1080; a lower-resolution source is never artificially enlarged.</p>
    </section>
    <section class="panel"><h2>Full-resolution photography</h2><p class="note">The detector keeps recording while you adjust these temporary settings. Clicking Capture finishes an active MP4, temporarily switches the camera to still mode, then restores the saved detection profile. A long exposure creates a recording gap.</p>
    <details id="live-advanced"><summary class="button">Advanced photography controls</summary>
      <div class="live-photo-grid" style="margin-top:14px"><label>Exposure mode<select id="photo-mode"><option value="auto">Automatic</option><option value="manual">Manual long exposure</option></select></label>
      <label>Exposure / shutter (milliseconds, max 112000)<input id="photo-exposure" type="number" min="0.1" max="112000" step="0.1" value="1000"></label>
      <label>Analogue gain (1–16×)<input id="photo-gain" type="number" min="1" max="16" step="0.1" value="4"></label>
      <label>Focus<select id="photo-focus"><option value="infinity">Infinity</option><option value="auto">Autofocus</option></select></label>
      <label>White balance<select id="photo-awb"><option value="auto">Automatic</option><option value="manual">Manual</option></select></label>
      <label>Red gain<input id="photo-red" type="number" min="0.1" max="8" step="0.1" value="1.5"></label>
      <label>Blue gain<input id="photo-blue" type="number" min="0.1" max="8" step="0.1" value="1.5"></label>
      <label>Brightness (-1 to 1)<input id="photo-brightness" type="number" min="-1" max="1" step="0.1" value="0"></label>
      <label>Contrast (0.25 to 4)<input id="photo-contrast" type="number" min="0.25" max="4" step="0.1" value="1"></label>
      <label>Saturation (0 to 3)<input id="photo-saturation" type="number" min="0" max="3" step="0.1" value="1"></label>
      </div>
    </details>
    <div class="live-controls"><label>Photo format<select id="photo-format"><option value="jpg">JPEG (high quality)</option><option value="png">PNG (larger lossless file)</option></select></label><button id="photo-capture" type="button">Capture full resolution</button></div>
    <p id="photo-status" class="note" role="status">Camera remains in normal recording mode until Capture is pressed.</p>
    <div id="photo-progress" class="photo-progress" hidden aria-label="Photograph exposure progress"><div class="between"><span id="photo-phase">Exposure in progress</span><strong id="photo-countdown" role="timer">—</strong></div><progress id="photo-exposure-progress" max="100" value="0"></progress><p class="note tight">Approximate shutter countdown; camera timing and saving can take longer.</p></div>
    <div id="photo-download"></div>
    <p class="note">After capture, select <strong>Review captured photo</strong> to apply Original, Detection, Low-light enhanced or comparison processing to the saved photograph. Save current view PNG exports a processed Full HD copy, while Download original photo keeps its full sensor resolution.</p>
    </section>
    <script src="{{ url_for('live_js') }}" defer></script>''', title='Photography')


@app.route('/live-camera/capture', methods=['POST'])
def photo_request():
    check_csrf()
    fields={key:request.form.get(key) for key in ('mode','format','exposure_ms','gain','focus','awb',
                                      'red_gain','blue_gain','brightness','contrast','saturation')}
    # A normal still only needs a short exclusive window. For manual long exposures,
    # reserve the requested shutter duration plus camera transition/recovery time.
    try:
        exposure_seconds=(float(fields['exposure_ms'])/1000 if fields.get('mode')=='manual'
                          and fields.get('exposure_ms') else 0.0)
        if not math.isfinite(exposure_seconds) or exposure_seconds<0: raise ValueError('Invalid shutter duration.')
        required_window=max(25,exposure_seconds+20)
        if oj.busy_soon(grace_seconds=required_window):
            return jsonify(error='A scheduled camera job is starting too soon for this photograph. Try again after it finishes or use a shorter shutter exposure.'),409
        token=queue_capture(fields)
    except ValueError as exc:
        return jsonify(error=str(exc)),400
    except OSError:
        app.logger.exception('Cannot queue full-resolution photograph')
        return jsonify(error='Photograph could not be queued. Check camera service and photo storage permissions in System Health.'),503
    except Exception:
        app.logger.exception('Unexpected failure queuing full-resolution photograph')
        return jsonify(error='Photograph request failed on the detector. Review dashboard service logs before retrying.'),500
    return jsonify(token=token),202


@app.route('/live-camera/photo/<token>/status')
def photo_status(token):
    try:
        value=json.loads(photo_result_path(token).read_text())
    except (ValueError, FileNotFoundError, OSError): abort(404)
    # A failed/stopped camera owner can leave a queued request behind. A photo
    # accepted for capture moves to 'preparing' immediately, so long exposures
    # are NOT subject to this short queue watchdog.
    if value.get('state') == 'queued':
        queue = DATA / 'photography' / 'request.json'
        try:
            pending_job = json.loads(queue.read_text())
            if pending_job.get('id') == token and time.time() - float(pending_job['created']) > 65:
                value = {'state': 'error', 'message': 'Camera did not accept the photo request within 65 seconds. Check System Health and camera service.'}
                # Stale requests must not block the next user attempt.
                queue.unlink(missing_ok=True)
                photo_set_state(token, 'error', value['message'])
        except (OSError, ValueError, KeyError, TypeError):
            pass
    if value.get('state')=='exposing':
        try:
            duration=float(value['exposure_seconds'])
            start=float(value['exposure_started_epoch'])
            value['remaining_seconds']=max(0.0,duration-(time.time()-start))
        except (TypeError,ValueError,KeyError):
            value.pop('remaining_seconds',None)
    return jsonify(value)


@app.route('/live-camera/photo/<token>/download')
def photo_download(token):
    try:
        item=json.loads(photo_result_path(token).read_text())
        if item.get('state')!='done': abort(404)
        fmt=item.get('format')
        path=photo_output_path(token,fmt)
        if not path.is_file() or path.is_symlink(): abort(404)
    except (ValueError, FileNotFoundError, OSError): abort(404)
    details=next((item for item in photos() if item['token']==token),None)
    return send_file(path,as_attachment=True,
                     download_name=photo_filename(token[:8],details['title'] if details else 'Camera-capture',fmt))


@app.route('/assets/theme-init.js')
def theme_init_js():
    return send_file(Path(__file__).with_name('theme_init.js'),mimetype='application/javascript')


@app.route('/assets/theme.js')
def theme_js():
    return send_file(Path(__file__).with_name('theme.js'),mimetype='application/javascript')


@app.route('/assets/navigation.js')
def navigation_js():
    return send_file(Path(__file__).with_name('navigation.js'),mimetype='application/javascript')


@app.route('/assets/live.js')
def live_js():
    return send_file(Path(__file__).with_name('live.js'),mimetype='application/javascript')


@app.route('/live-camera/hd.jpg')
def hd_preview():
    if oj.active(): abort(503, 'Camera busy with scheduled observation')
    """Only an admin can request the existing video stream's full-size JPEG.

    The recorder checks a short-lived request marker during its ordinary
    preview loop; no second Picamera2 process, and no camera configuration
    changes are involved. Non-admin users never receive the HD cache.
    """
    marker = DATA / 'hd-preview-request'
    marker.touch()
    path = DATA / 'latest-hd.jpg'
    if not path.is_file() or time.time()-path.stat().st_mtime > 18:
        return jsonify(error='Waiting for camera HD snapshot'), 503, {'Cache-Control':'no-store'}
    response=send_file(path,mimetype='image/jpeg',conditional=False)
    response.headers['Cache-Control']='private, no-store'
    return response


@app.route('/live-camera/photo/<token>/image')
def photo_image(token):
    """Private inline original photo for optional client-side comparison."""
    try:
        info = json.loads(photo_result_path(token).read_text())
        if info.get('state') != 'done' or info.get('format') not in ('jpg','png'):
            abort(404)
        fmt=info['format']
        path=photo_output_path(token,fmt)
        if not path.is_file() or path.is_symlink(): abort(404)
    except (ValueError, FileNotFoundError, OSError): abort(404)
    response=send_file(path,mimetype='image/png' if fmt=='png' else 'image/jpeg',conditional=False)
    response.headers['Cache-Control']='private, no-store'
    response.headers['X-Content-Type-Options']='nosniff'
    return response


@app.route('/preview.jpg')
def preview():
    if not logged_in():
        return redirect(url_for('login'))
    image = DATA / 'latest.jpg'
    if not image.is_file():
        abort(404)
    return send_file(image, mimetype='image/jpeg')


def file_for_event(event_id, field, base):
    with connection() as conn:
        row = conn.execute(f'SELECT {field} FROM events WHERE id=?', (event_id,)).fetchone()
    if not row or not row[field]:
        abort(404)
    name = row[field]
    # Files are basenames produced by our detector, never arbitrary paths.
    if name != Path(name).name or name.startswith('.'):
        abort(404)
    path = base / name
    if not path.is_file():
        abort(404)
    return path


@app.route('/event/<int:event_id>/thumb.jpg')
def thumbnail(event_id):
    if not logged_in():
        return redirect(url_for('login'))
    return send_file(file_for_event(event_id, 'thumbnail', THUMBS), mimetype='image/jpeg')


@app.route('/event/<int:event_id>/video.mp4')
def video(event_id):
    if not logged_in():
        return redirect(url_for('login'))
    return send_file(file_for_event(event_id, 'video', RECORDINGS),
                     mimetype='video/mp4', conditional=True,
                     as_attachment=request.args.get('download') == '1')


@app.route('/assets/investigator.js')
def investigator_js():
    if not logged_in():
        abort(403)
    return send_file(Path(__file__).with_name('investigator.js'), mimetype='application/javascript')


@app.route('/assets/uap.js')
def ui_js():
    if not logged_in():
        abort(403)
    script = r'''document.addEventListener('DOMContentLoaded', () => {
      const geoButton = document.querySelector('[data-location-fill]');
      if (geoButton) geoButton.addEventListener('click', () => {
        const note = document.getElementById('location-note');
        if (!navigator.geolocation) { note.textContent = 'Your browser cannot obtain a location; type coordinates and timezone instead.'; return; }
        geoButton.disabled = true;
        note.textContent = 'Requesting permission to use this device location…';
        navigator.geolocation.getCurrentPosition(pos => {
          document.getElementById('latitude').value = pos.coords.latitude.toFixed(6);
          document.getElementById('longitude').value = pos.coords.longitude.toFixed(6);
          try { document.getElementById('schedule_timezone').value = Intl.DateTimeFormat().resolvedOptions().timeZone || 'Europe/London'; } catch (_) {}
          note.textContent = 'Location fields filled. Check that this is where the detector is installed, then press Save settings.';
          geoButton.disabled = false;
        }, err => {note.textContent = 'Location unavailable or permission denied. Please type coordinates and timezone manually.'; geoButton.disabled = false;},
        {enableHighAccuracy:false, timeout:15000, maximumAge:600000});
      });
      const button = document.querySelector('[data-preview-refresh]');
      if (button) button.addEventListener('click', () => {
        const image = document.getElementById('preview-image');
        const note = document.getElementById('preview-note');
        if (!image) { note.textContent = 'No camera image has been captured yet.'; return; }
        button.disabled = true;
        image.onload = () => { button.disabled = false; note.textContent = 'Preview refreshed.'; };
        image.onerror = () => { button.disabled = false; note.textContent = 'Camera snapshot unavailable. Please try again.'; };
        image.src = '/preview.jpg?t=' + Date.now();
      });
      const form = document.getElementById('uap-settings-form');
      if (form) form.addEventListener('invalid', event => {
        for (let parent = event.target.parentElement; parent; parent = parent.parentElement) {
          if (parent.tagName === 'DETAILS') parent.open = true;
        }
      }, true);
      const testButtons = Array.from(document.querySelectorAll('[data-preview-profile], [data-preview-profile-choice]')); 
      const previewImage = document.getElementById('preview-image');
      const previewNote = document.getElementById('preview-note');
      const resetButtons = document.querySelectorAll('[data-reset-profile]');
      for (const btn of resetButtons) btn.addEventListener('click', () => {
        const key = btn.dataset.resetProfile;
        const defaults = window.UAP_PROFILE_DEFAULTS && window.UAP_PROFILE_DEFAULTS[key];
        if (!defaults || !form) return;
        if (!confirm('Restore the default values in ' + key + '? They will not be saved until you press Save settings.')) return;
        for (const [name, value] of Object.entries(defaults)) {
          const el = form.elements.namedItem('cam_' + key + '_' + name);
          if (!el) continue;
          el.value = name === 'auto_exposure' || name === 'awb' ? (value ? 'auto' : 'manual') : value;
        }
        previewNote.textContent = 'Default values loaded into ' + key + '. Test the profile or save to keep it.';
      });
      function wait(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
      for (const btn of testButtons) btn.addEventListener('click', async () => {
        if (!form || !previewImage) return;
        const chosen = btn.dataset.previewProfile || document.getElementById('preview-profile-choice').value;
        const data = new FormData(form);
        data.set('preview_slot', chosen);
        // No settings are saved here; the detector owns the physical camera.
        testButtons.forEach(b => b.disabled = true);
        previewNote.textContent = 'Testing unsaved ' + chosen + ' settings. Waiting for the camera…';
        try {
          const started = await fetch('/settings/preview-test', {method:'POST', body:data, credentials:'same-origin'});
          const initial = await started.json();
          if (!started.ok) throw Error(initial.error || 'Cannot start camera preview');
          let result;
          for (let i=0; i<110; i++) {
            await wait(500);
            const r = await fetch('/settings/preview-status/' + initial.id, {credentials:'same-origin'});
            result = await r.json();
            if (!r.ok) throw Error(result.error || 'Preview unavailable');
            if (result.state === 'done') break;
            if (result.state === 'error') throw Error(result.message || 'Preview failed');
          }
          if (!result || result.state !== 'done') throw Error('Timed out waiting for camera. Check the detector status and try again.');
          await new Promise((resolve, reject) => {
            previewImage.onload = resolve;
            previewImage.onerror = reject;
            previewImage.src = '/settings/preview-image/' + initial.id + '?t=' + Date.now();
          });
          previewNote.textContent = 'Unsaved test image: ' + chosen + '. Active recording settings have been restored. Press Save settings to keep any changes.';
        } catch (e) { previewNote.textContent = String(e.message || e); }
        finally { testButtons.forEach(b => b.disabled = false); }
      });
    });'''
    return Response(script, mimetype='application/javascript')


@app.route('/assets/camera-reset.js')
def camera_reset_js():
    return send_file(Path(__file__).with_name('camera_reset.js'), mimetype='application/javascript')


@app.route('/assets/profile-defaults.js')
def profile_defaults_js():
    if not is_admin():
        abort(403)
    return Response('window.UAP_PROFILE_DEFAULTS=' + json.dumps(base_profiles()) + ';', mimetype='application/javascript')


def _draft_from_form(form):
    slot=form.get('preview_slot', '')
    if slot not in ('auto',) + tuple(SLOTS):
        raise ValueError('Choose a camera profile to test')
    try:
        fps=int(read_config().get('fps', 15))  # Physical stream frame rate; unsaved fps needs a camera restart.
    except (TypeError, ValueError):
        fps=15
    if slot=='auto':
        profile=None
    else:
        prefix='cam_' + slot + '_'
        def number(name):
            return float(form.get(prefix+name, ''))
        profile=validate_profile({
            'name':form.get(prefix+'name', ''),
            'auto_exposure':form.get(prefix+'auto_exposure')=='auto',
            'exposure_ms':number('exposure_ms'),
            'gain':number('gain'), 'ev':number('ev'),
            'awb':form.get(prefix+'awb')=='auto',
            'red_gain':number('red_gain'), 'blue_gain':number('blue_gain'),
            'focus':form.get(prefix+'focus', 'infinity'),
            'brightness':number('brightness'), 'contrast':number('contrast'),
            'saturation':number('saturation'),
        })
        if not exposure_within_frame(profile, fps):
            raise ValueError(f'Manual exposure exceeds the active {fps} fps frame duration. Lower exposure or save a lower frame rate first.')
    rotate=form.get('rotate_180')=='on'
    return profile, rotate, fps


@app.route('/settings/preview-test', methods=['POST'])
def test_profile_preview():
    check_csrf()
    try:
        p, rotate, fps=_draft_from_form(request.form)
        token=enqueue(p, rotate, fps)
    except (ValueError, KeyError, TypeError) as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(id=token), 202


@app.route('/settings/preview-status/<token>')
def profile_preview_status(token):
    try:
        path=result_path(token)
        if path.exists():
            return jsonify(json.loads(path.read_text()))
        request=pending_request()
        if request and request['id']==token:
            return jsonify(state='pending')
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        pass
    return jsonify(error='Preview expired or unavailable'), 404


@app.route('/settings/preview-image/<token>')
def profile_preview_image(token):
    try:
        if result_path(token).is_file() and json.loads(result_path(token).read_text()).get('state')=='done':
            p=image_path(token)
            if p.is_file():
                return send_file(p, mimetype='image/jpeg')
    except (OSError, ValueError, json.JSONDecodeError):
        pass
    abort(404)


def validated_settings(form):
    def integer(name, lo, hi):
        try:
            value = int(form.get(name, ''))
        except (TypeError, ValueError):
            raise ValueError(f'{name} must be a whole number')
        if not lo <= value <= hi:
            raise ValueError(f'{name} must be between {lo} and {hi}')
        return value

    timezone_name = form.get('schedule_timezone', '').strip()
    zone(timezone_name)  # Valid IANA timezone, including daylight-saving rules.
    start_text = form.get('schedule_start', '')
    end_text = form.get('schedule_end', '')
    parse_clock(start_text)
    parse_clock(end_text)
    mode = form.get('operation_mode', '')
    if mode not in ('continuous', 'timed', 'solar'):
        raise ValueError('Choose a valid detector operating mode')
    if mode == 'timed' and start_text == end_text:
        raise ValueError('Scheduled start and end must not be the same')
    lat_text = form.get('latitude', '').strip()
    lon_text = form.get('longitude', '').strip()
    if bool(lat_text) != bool(lon_text):
        raise ValueError('Enter both latitude and longitude, or neither')
    try:
        lat = float(lat_text) if lat_text else None
        lon = float(lon_text) if lon_text else None
    except ValueError as exc:
        raise ValueError('Latitude and longitude must be decimal numbers') from exc
    import math
    if lat is not None and (not math.isfinite(lat) or not -89.8 <= lat <= 89.8):
        raise ValueError('Latitude must be between -89.8 and 89.8')
    if lon is not None and (not math.isfinite(lon) or not -180 <= lon <= 180):
        raise ValueError('Longitude must be between -180 and 180')
    if mode == 'solar' and lat is None:
        raise ValueError('Sunset mode needs latitude and longitude for the detector')
    public_title = form.get('public_title', '').strip() or 'Sky Camera'
    if len(public_title) > 80 or any(ord(ch) < 32 or ord(ch) == 127 for ch in public_title):
        raise ValueError('Camera name must be 80 printable characters or fewer')
    resolution = form.get('resolution', '')
    if resolution not in RESOLUTIONS:
        raise ValueError('Choose a supported camera resolution')
    detection_profile = form.get('detection_profile', 'general')
    if detection_profile not in ('general', 'sky_lights', 'combined'):
        raise ValueError('Choose a supported detection profile')
    location_name = form.get('location_name', '').strip()[:100]
    if any(ord(ch) < 32 for ch in location_name):
        raise ValueError('Location name contains invalid characters')
    current = read_config()
    camera_profile_mode = form.get('camera_profile_mode', current.get('camera_profile_mode', 'auto'))
    if camera_profile_mode not in MODES:
        raise ValueError('Choose a supported camera profile mode')
    if camera_profile_mode == 'solar' and lat is None:
        raise ValueError('Sunrise/sunset camera profiles need the detector location')
    camera_profiles = get_profiles(current)
    for slot in SLOTS:
        prefix = f'cam_{slot}_'
        if prefix + 'name' not in form:
            continue
        def profile_number(field):
            try:
                return float(form.get(prefix + field, ''))
            except (ValueError, TypeError):
                raise ValueError(f'{slot}: {field} must be numeric')
        camera_profiles[slot] = validate_profile({
            'name': form.get(prefix + 'name', ''),
            'auto_exposure': form.get(prefix + 'auto_exposure') == 'auto',
            'exposure_ms': profile_number('exposure_ms'),
            'gain': profile_number('gain'), 'ev': profile_number('ev'),
            'awb': form.get(prefix + 'awb') == 'auto',
            'red_gain': profile_number('red_gain'),
            'blue_gain': profile_number('blue_gain'),
            'focus': form.get(prefix + 'focus', 'infinity'),
            'brightness': profile_number('brightness'),
            'contrast': profile_number('contrast'),
            'saturation': profile_number('saturation'),
        })
    fps_value = integer('fps', 5, capture_capabilities()['max_fps'])
    for slot in SLOTS:
        if not exposure_within_frame(camera_profiles[slot], fps_value):
            raise ValueError(f'{camera_profiles[slot]["name"]}: manual exposure is too long at {fps_value} fps. Lower exposure or frame rate.')
    rotate_180 = form.get('rotate_180') == 'on' if 'camera_profile_mode' in form else bool(current.get('rotate_180', False))
    bearing = integer('image_top_bearing', 0, 359) if 'image_top_bearing' in form else int(current.get('image_top_bearing', 0))
    elevation = integer('camera_elevation', 0, 90) if 'camera_elevation' in form else int(current.get('camera_elevation', 90))
    result = {
        'camera_profile_mode': camera_profile_mode,
        'camera_profiles': camera_profiles,
        'rotate_180': rotate_180,
        'image_top_bearing': bearing,
        'camera_elevation': elevation,
        'operation_mode': mode,
        'schedule_timezone': timezone_name,
        'schedule_start': start_text,
        'schedule_end': end_text,
        'latitude': lat,
        'longitude': lon,
        'location_name': location_name,
        'detection_paused': read_config().get('detection_paused', False),
        'fps': fps_value,
        'resolution': resolution,
        'detection_profile': detection_profile,
        'sky_brightness': integer('sky_brightness', 100, 250),
        'sky_min_area': integer('sky_min_area', 1, 40),
        'sky_max_area': integer('sky_max_area', 10, 400),
        'sky_confirm_frames': integer('sky_confirm_frames', 2, 8),
        'sky_min_movement': integer('sky_min_movement', 1, 15),
        'pixel_threshold': integer('pixel_threshold', 1, 255),
        'min_changed_pixels': integer('min_changed_pixels', 10, 10000),
        'pre_motion_seconds': integer('pre_motion_seconds', 1, 15),
        'post_motion_seconds': integer('post_motion_seconds', 1, 60),
        'max_clip_seconds': integer('max_clip_seconds', 30, 3600),
        'cleanup_enabled': form.get('cleanup_enabled') == 'on',
        'retention_new_days': integer('retention_new_days', 1, 3650),
        'retention_viewed_days': integer('retention_viewed_days', 1, 3650),
        'retention_dismissed_days': integer('retention_dismissed_days', 1, 3650),
        'max_storage_gb': integer('max_storage_gb', 0, 1000),
        'storm_enabled': form.get('storm_enabled') == 'on',
        'storm_trigger_minutes': integer('storm_trigger_minutes', 5, 60),
        'storm_window_minutes': integer('storm_window_minutes', 5, 120),
        'storm_cooldown_minutes': integer('storm_cooldown_minutes', 5, 180),
        'photo_cleanup_enabled': form.get('photo_cleanup_enabled') == 'on',
        'photo_retention_days': integer('photo_retention_days', 1, 3650),
        'notice_cleanup_enabled': form.get('notice_cleanup_enabled') == 'on',
        'notice_report_days': integer('notice_report_days', 1, 3650),
        'notice_fault_days': integer('notice_fault_days', 1, 3650),
        'public_enabled': form.get('public_enabled') == 'on',
        'public_title': public_title,
        'public_show_location_name': form.get('public_show_location_name') == 'on',
        'public_show_orientation': form.get('public_show_orientation') == 'on',
    }
    if result['storm_trigger_minutes'] > result['storm_window_minutes']:
        raise ValueError('Storm trigger period cannot exceed its monitoring window')
    if result['sky_max_area'] < result['sky_min_area']:
        raise ValueError('Maximum light size must be at least the minimum light size')
    if result['max_clip_seconds'] < result['pre_motion_seconds'] + result['post_motion_seconds'] + 2:
        raise ValueError('Maximum clip length must exceed the pre- and post-recording windows')
    return result


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if not logged_in():
        return redirect(url_for('login'))
    error = ''
    if request.method == 'POST':
        check_csrf()
        try:
            new_settings = validated_settings(request.form)
            save_settings(new_settings)
        except (ValueError, OSError) as exc:
            error = str(exc)
        else:
            return redirect(url_for('settings', saved=1))
    cfg = read_config()
    capabilities = capture_capabilities()
    solar_info = None
    if cfg.get('latitude') is not None and cfg.get('longitude') is not None:
        try:
            z = zone(cfg.get('schedule_timezone'))
            local_day = datetime.now(z).date()
            solar_pair = sun_times(local_day, float(cfg['latitude']), float(cfg['longitude']), cfg['schedule_timezone'])
            if solar_pair:
                solar_info = tuple(item.strftime('%H:%M') for item in solar_pair)
        except (ValueError, TypeError):
            pass
    usage = storage_summary()
    plan = cleanup_plan(cfg)
    due_size = sum(int(r.get('bytes', 0)) for r in plan)
    return render_page('''<p><a href="{{ url_for('home') }}">← Back to Dashboard</a></p>
    <h1>Detector settings</h1>
    {% if saved %}<div class="notice" role="status">Settings saved. Camera changes apply automatically after the current recording finishes.</div>{% endif %}
    {% if error %}<p class="error">{{ error }}</p>{% endif %}
    <script src="{{ url_for('profile_defaults_js') }}" defer></script>
    <script src="{{ url_for('camera_reset_js') }}" defer></script>
    <form id="uap-settings-form" method="post"><input type="hidden" name="csrf" value="{{ csrf }}">
    <div class="between" style="margin-bottom:12px"><span class="note">Open a section to adjust settings. Test camera changes before saving.</span><button type="submit">Save settings</button></div>
    <div class="cols"><div>
      <details class="panel setting-section"><summary>Camera and recording</summary><div class="setting-content" id="camera-recording-settings">
      <p class="note">Motion sensitivity may need different values indoors and under the night sky.</p>
      <div class="options">
      <div><label for="camera_resolution">Recording resolution</label><select name="resolution" id="camera_resolution" required>
      <option value="640x480" {% if cfg.resolution == '640x480' %}selected{% endif %}>640 × 480 (VGA)</option>
      <option value="1280x720" {% if cfg.resolution == '1280x720' %}selected{% endif %}>1280 × 720 (HD)</option>
      <option value="1920x1080" {% if cfg.resolution == '1920x1080' %}selected{% endif %}>1920 × 1080 (Full HD)</option></select></div>
      <div><label for="camera_fps">Camera frame rate</label><select name="fps" id="camera_fps" required>
      {% for rate in fps_options %}<option value="{{ rate }}" {% if cfg.fps|int == rate %}selected{% endif %}>{{ rate }} fps{% if rate > 30 %} — experimental{% endif %}</option>{% endfor %}
      </select></div>
      <div><label>Pixel difference threshold (1–255)</label><input type="number" name="pixel_threshold" min="1" max="255" value="{{ cfg.pixel_threshold }}" required></div>
      <div><label>Changed pixels to trigger (10–10000)</label><input type="number" name="min_changed_pixels" min="10" max="10000" value="{{ cfg.min_changed_pixels }}" required></div>
      <div><label>Seconds before motion (1–15)</label><input type="number" name="pre_motion_seconds" min="1" max="15" value="{{ cfg.pre_motion_seconds }}" required></div>
      <div><label>Seconds after motion (1–60)</label><input type="number" name="post_motion_seconds" min="1" max="60" value="{{ cfg.post_motion_seconds }}" required></div>
      <div><label>Maximum clip length (30–3600 sec)</label><input type="number" name="max_clip_seconds" min="30" max="3600" value="{{ cfg.max_clip_seconds }}" required></div>
      </div><p class="note">Detected hardware: {{ capabilities.pi_model }} · camera: {{ capabilities.camera_model }}. Higher frame rates are only offered on detected compatible devices. {% if capabilities.experimental %}Rates above 30 fps are experimental; check real MP4 frame rate and CPU load before leaving the recorder unattended.{% endif %}</p>
      <p class="note">Higher resolutions use more processing power and disk space. Changes take effect after the current recording has finished. Lower the changed-pixel value to detect smaller movement; too low will increase false alarms.</p>
      <div class="row"><button type="button" id="camera-recording-reset" data-defaults='{{ camera_reset_defaults|tojson }}'>Reset to defaults</button><span class="note" id="camera-recording-reset-result" role="status">Resets only Camera and recording. Review the values and press Save settings to apply.</span></div></div></details>

      <details class="panel setting-section"><summary>Camera profiles &amp; orientation</summary><div class="setting-content">
      <p class="note">Choose a camera profile. Automatic lets the camera adapt to the light. Sunrise/sunset changes between Day and Night using the detector location above. Custom 1 and Custom 2 let you save your own settings.</p>
      <label for="camera_profile_mode">Active camera profile</label>
      <select id="camera_profile_mode" name="camera_profile_mode" required>
      <option value="auto" {% if cfg.camera_profile_mode == 'auto' %}selected{% endif %}>Automatic exposure and gain</option>
      {% for key, label in [('day','Day'),('night','Night'),('custom1','Custom 1'),('custom2','Custom 2')] %}
      <option value="{{ key }}" {% if cfg.camera_profile_mode == key %}selected{% endif %}>{{ camera_profiles[key].name }}</option>{% endfor %}
      <option value="solar" {% if cfg.camera_profile_mode == 'solar' %}selected{% endif %}>Automatic Day / Night at sunrise and sunset</option></select>
      <p class="note"><strong>Currently selected:</strong> {{ active_profile }}. Manual settings only affect profiles with Manual exposure selected.</p>
      <div class="camera-settings-preview">
        <div class="row"><strong>Camera preview</strong><button type="button" data-preview-refresh>Refresh active image</button></div>
        <div class="row"><label for="preview-profile-choice" style="margin:0">Preview profile</label><select id="preview-profile-choice" style="width:auto;flex:1;min-width:140px">
        <option value="auto" {% if active_profile == 'auto' %}selected{% endif %}>Automatic</option>
        {% for key in ['day','night','custom1','custom2'] %}<option value="{{ key }}" {% if active_profile == key %}selected{% endif %}>{{ camera_profiles[key].name }}</option>{% endfor %}</select>
        <button type="button" data-preview-profile-choice>Preview unsaved changes</button></div>
        <img class="preview" id="preview-image" src="{{ url_for('preview') }}" alt="Latest camera image">
        <p class="note" id="preview-note">Choose a profile below and press Test unsaved profile to see your adjustments before saving. This privately tests camera settings, then restores the active profile. Detection briefly pauses while the buffer refills. Normal Refresh shows the currently active camera image.</p>
      </div>
      <label class="checkline"><input type="checkbox" name="rotate_180" {% if cfg.rotate_180 %}checked{% endif %}> Rotate recorded image and preview 180°</label>
      <div class="camera-orientation"><div class="orientation-fields">
        <label for="image_top_bearing">Top-edge compass bearing (0–359°)</label>
        <input id="image_top_bearing" name="image_top_bearing" type="number" min="0" max="359" value="{{ cfg.image_top_bearing }}" required>
        <label for="camera_elevation">Elevation above horizon (0–90°)</label>
        <input id="camera_elevation" name="camera_elevation" type="number" min="0" max="90" value="{{ cfg.camera_elevation }}" required>
      </div><p class="note orientation-help">North = 0°, East = 90°, South = 180°, West = 270°. Elevation: 0° is horizontal and 90° points straight up. Bearing refers to the top of the rotated image. These values describe orientation; precise sky mapping will require calibration.</p></div>
      <p class="note">The encoder, motion analysis and saved camera preview use the same 180° orientation. Existing recordings are not altered.</p>
      {% for key in ['day','night','custom1','custom2'] %}
      {% set p = camera_profiles[key] %}
      <details class="camera-profile-edit"><summary><strong>{{ p.name }}</strong> — Exposure, colour and focus</summary>
      <div class="options">
      <div><label>Profile name</label><input name="cam_{{ key }}_name" value="{{ p.name }}" maxlength="48" required></div>
      <div><label>Exposure control</label><select name="cam_{{ key }}_auto_exposure"><option value="auto" {% if p.auto_exposure %}selected{% endif %}>Automatic exposure and gain</option><option value="manual" {% if not p.auto_exposure %}selected{% endif %}>Manual exposure and gain</option></select></div>
      <div><label>Manual exposure (ms)</label><input type="number" name="cam_{{ key }}_exposure_ms" step="0.1" min="0.1" max="1000" value="{{ p.exposure_ms }}" required></div>
      <div><label>Manual analogue gain (1–16)</label><input type="number" name="cam_{{ key }}_gain" step="0.1" min="1" max="16" value="{{ p.gain }}" required></div>
      <div><label>Automatic exposure compensation (-4 to 4)</label><input type="number" name="cam_{{ key }}_ev" step="0.1" min="-4" max="4" value="{{ p.ev }}" required></div>
      <div><label>White balance</label><select name="cam_{{ key }}_awb"><option value="auto" {% if p.awb %}selected{% endif %}>Automatic</option><option value="manual" {% if not p.awb %}selected{% endif %}>Manual red/blue gains</option></select></div>
      <div><label>Red colour gain (0.1–8)</label><input type="number" name="cam_{{ key }}_red_gain" step="0.1" min="0.1" max="8" value="{{ p.red_gain }}" required></div>
      <div><label>Blue colour gain (0.1–8)</label><input type="number" name="cam_{{ key }}_blue_gain" step="0.1" min="0.1" max="8" value="{{ p.blue_gain }}" required></div>
      <div><label>Focus</label><select name="cam_{{ key }}_focus"><option value="infinity" {% if p.focus == 'infinity' %}selected{% endif %}>Manual — infinity (stars)</option><option value="auto" {% if p.focus == 'auto' %}selected{% endif %}>Continuous autofocus</option></select></div>
      <div><label>Brightness (-1 to 1)</label><input type="number" name="cam_{{ key }}_brightness" step="0.1" min="-1" max="1" value="{{ p.brightness }}" required></div>
      <div><label>Contrast (0.25–4)</label><input type="number" name="cam_{{ key }}_contrast" step="0.05" min="0.25" max="4" value="{{ p.contrast }}" required></div>
      <div><label>Saturation (0–3)</label><input type="number" name="cam_{{ key }}_saturation" step="0.1" min="0" max="3" value="{{ p.saturation }}" required></div>
      </div><p class="note">At the current {{ cfg.fps }} fps, a manual exposure can be at most {{ '%.1f'|format(1000 / cfg.fps|int) }} ms. Test unsaved values to see them before saving.</p><div class="row"><button type="button" data-preview-profile="{{ key }}">Test unsaved profile</button><button type="button" data-reset-profile="{{ key }}">Reset to defaults</button></div></details>
      {% endfor %}
      <button type="submit">Save and apply camera profiles</button>
      </div></details>
      <details class="panel setting-section"><summary>Detection profile</summary><div class="setting-content">
      <label for="detection_profile">What to look for</label>
      <select id="detection_profile" name="detection_profile" required>
        <option value="general" {% if cfg.detection_profile == 'general' %}selected{% endif %}>General motion — people, objects and movement</option>
        <option value="sky_lights" {% if cfg.detection_profile == 'sky_lights' %}selected{% endif %}>Moving sky lights — experimental</option>
        <option value="combined" {% if cfg.detection_profile == 'combined' %}selected{% endif %}>Combined — general motion or moving sky lights</option>
      </select>
      <p class="note">General motion responds to changes in the image. Moving sky lights looks for compact moving bright points. Combined records when either detects activity, using the same recorder without duplicate clips. It may produce more false alerts than either mode alone.</p>
      <div class="options">
        <div><label for="sky_brightness">Minimum light brightness (100–250)</label><input id="sky_brightness" name="sky_brightness" type="number" min="100" max="250" value="{{ cfg.sky_brightness }}" required></div>
        <div><label for="sky_confirm_frames">Frames required to confirm (2–8)</label><input id="sky_confirm_frames" name="sky_confirm_frames" type="number" min="2" max="8" value="{{ cfg.sky_confirm_frames }}" required></div>
        <div><label for="sky_min_area">Minimum bright area (1–40 pixels)</label><input id="sky_min_area" name="sky_min_area" type="number" min="1" max="40" value="{{ cfg.sky_min_area }}" required></div>
        <div><label for="sky_max_area">Maximum bright area (10–400 pixels)</label><input id="sky_max_area" name="sky_max_area" type="number" min="10" max="400" value="{{ cfg.sky_max_area }}" required></div>
        <div><label for="sky_min_movement">Minimum movement (1–15 pixels/frame)</label><input id="sky_min_movement" name="sky_min_movement" type="number" min="1" max="15" value="{{ cfg.sky_min_movement }}" required></div>
      </div>
      <p class="note">Sky-light values use the small 320 × 240 analysis image, not the video resolution. Lower brightness and smaller areas detect more candidates but produce more false alerts. These controls apply to Moving sky lights and Combined.</p>
      </div></details>
      <details class="panel setting-section"><summary>When to detect</summary><div class="setting-content">
      <p class="note">Choose when to record. A manual Pause overrides every schedule. The camera preview remains available while detections are paused or outside the recording window.</p>
      <label for="operation_mode">Detector operating mode</label>
      <select id="operation_mode" name="operation_mode" required>
      <option value="continuous" {% if cfg.operation_mode == 'continuous' %}selected{% endif %}>Continuous — all day and night</option>
      <option value="timed" {% if cfg.operation_mode == 'timed' %}selected{% endif %}>Scheduled hours</option>
      <option value="solar" {% if cfg.operation_mode == 'solar' %}selected{% endif %}>Sunset to sunrise — automatically changes through the year</option></select>
      <div class="options">
      <div><label for="schedule_start">Start time (24-hour)</label><input id="schedule_start" name="schedule_start" type="time" value="{{ cfg.schedule_start }}" required></div>
      <div><label for="schedule_end">End time (24-hour)</label><input id="schedule_end" name="schedule_end" type="time" value="{{ cfg.schedule_end }}" required></div>
      <div><label for="schedule_timezone">Detector time zone</label><input id="schedule_timezone" name="schedule_timezone" value="{{ cfg.schedule_timezone }}" required maxlength="80" placeholder="Europe/London"></div>
      <div><label for="location_name">Location name (optional)</label><input id="location_name" name="location_name" value="{{ cfg.location_name }}" maxlength="100" placeholder="Garden camera"></div>
      <div><label for="latitude">Latitude (decimal degrees)</label><input id="latitude" type="number" step="any" name="latitude" min="-89.8" max="89.8" value="{{ cfg.latitude if cfg.latitude is not none else '' }}" placeholder="51.50"></div>
      <div><label for="longitude">Longitude (decimal degrees)</label><input id="longitude" type="number" step="any" name="longitude" min="-180" max="180" value="{{ cfg.longitude if cfg.longitude is not none else '' }}" placeholder="-0.12"></div>
      </div>
      <p class="note">Scheduled hours use the detector timezone. If start is later than end (e.g. 20:00 to 06:00), the window continues past midnight. Sunrise/sunset needs the location coordinates and timezone; it recalculates every day.</p>
      <p><button type="button" data-location-fill>Use this device's location</button></p><p id="location-note" class="note" role="status">Only use this option while physically at the detector. Otherwise enter its location manually. Browsers may ask permission or require HTTPS.</p>
      {% if solar_info %}<p class="notice">Today's local sunrise: <strong>{{ solar_info[0] }}</strong> · sunset: <strong>{{ solar_info[1] }}</strong> (approximate).</p>{% endif %}
      <p class="note">If no ordinary sunrise or sunset occurs at a polar location, this mode suspends new recordings for safety until a valid window returns.</p>
      <script src="{{ url_for('ui_js') }}" defer></script></div></details>
      <details class="panel setting-section"><summary>Camera name and public viewing</summary><div class="setting-content">
      <p class="note">This is not needed for private use. Enabling it allows anonymous visitors to open /public and see a recent camera still and only the individual recordings you approve. Observation notes stay private unless you separately approve them on the recording. Anyone able to reach that route can see its content.</p>
      <label for="public_title">Camera name</label>
      <input id="public_title" name="public_title" maxlength="80" value="{{ cfg.public_title or '' }}" placeholder="Sky Camera">
      <p class="note">Appears in the header across the dashboard, sign-in screen and public camera page. Leave blank to use Sky Camera.</p>
      <label class="checkline"><input type="checkbox" name="public_enabled" {% if cfg.public_enabled %}checked{% endif %}> Enable anonymous public viewing</label>
      <h3>Public location details</h3>
      <p class="note">The location name is set under When to detect. Keep these options off if you do not want visitors to know where the camera is located.</p>
      <label class="checkline"><input type="checkbox" name="public_show_location_name" {% if cfg.public_show_location_name %}checked{% endif %}> Show location name in the public page heading</label>
      <label class="checkline"><input type="checkbox" name="public_show_orientation" {% if cfg.public_show_orientation %}checked{% endif %}> Show precise latitude, longitude, time zone, compass bearing and elevation on the public page</label>
      <p class="note">Coordinates can reveal the exact installation location. Both sharing options are off by default, including when upgrading an existing installation.</p>
      <p class="note">The still image can reveal people and private surroundings. Test outdoors first. Keep any public hostname separated and access-controlled appropriately by your reverse proxy. Public video delivery may have additional CDN restrictions.</p>
      {% if cfg.public_enabled %}<a href="{{ url_for('public_page') }}">Open the public page</a>{% else %}<p class="note">Save settings with this option enabled before the public page can be opened.</p>{% endif %}</div></details>
      <details class="panel setting-section"><summary>Event-storm protection</summary><div class="setting-content">
      <p class="note">Prevents a sunrise, moving clouds or branches from producing hours of repetitive recordings. The active MP4 is saved, a cooling period begins, then recording resumes automatically. Previews continue during cooldown.</p>
      <label class="checkline"><input type="checkbox" name="storm_enabled" {% if cfg.storm_enabled %}checked{% endif %}> Enable event-storm protection (recommended)</label>
      <div class="options">
      <div><label>Recorded minutes to trigger</label><input type="number" min="5" max="60" name="storm_trigger_minutes" value="{{ cfg.storm_trigger_minutes }}" required></div>
      <div><label>Monitoring window (minutes)</label><input type="number" min="5" max="120" name="storm_window_minutes" value="{{ cfg.storm_window_minutes }}" required></div>
      <div><label>Pause new recordings (minutes)</label><input type="number" min="5" max="180" name="storm_cooldown_minutes" value="{{ cfg.storm_cooldown_minutes }}" required></div></div>
      <p class="note">Default: 10 minutes recorded during any 15 minutes triggers a 15-minute cooldown. This intentionally prioritises storage over continuous footage during high activity; genuine events during cooldown may be missed.</p></div></details>
      <details class="panel setting-section"><summary>Automatic storage cleanup</summary><div class="setting-content">
      <p class="note">Cleanup is OFF by default. Enable it only if you accept automatic permanent deletion.</p>
      <label class="checkline"><input type="checkbox" name="cleanup_enabled" {% if cfg.cleanup_enabled %}checked{% endif %}> Enable daily automatic deletion</label>
      <div class="options"><div><label>Keep New events (days)</label><input type="number" name="retention_new_days" min="1" max="3650" value="{{ cfg.retention_new_days }}" required></div>
      <div><label>Keep Viewed events (days)</label><input type="number" name="retention_viewed_days" min="1" max="3650" value="{{ cfg.retention_viewed_days }}" required></div>
      <div><label>Keep Dismissed events (days)</label><input type="number" name="retention_dismissed_days" min="1" max="3650" value="{{ cfg.retention_dismissed_days }}" required></div>
      <div><label>Maximum video storage (GB, 0 = off)</label><input type="number" name="max_storage_gb" min="0" max="1000" value="{{ cfg.max_storage_gb }}" required></div></div>
      <p class="note"><strong>Always protected:</strong> Flagged, Identified, Unresolved, publicly approved and manually pinned events. New and Viewed events CAN be deleted if retention is enabled. A storage cap can remove eligible events before their age limit. This is a soft limit, not a guarantee that the SD card cannot fill up.</p>
      <p class="note">With current settings: {{ plan|length }} events ({{ '%.2f'|format(due_size / 1048576) }} MB) would qualify for cleanup. {% if not cfg.cleanup_enabled %}Nothing will be deleted while cleanup is disabled.{% endif %}</p>
      </div></details>
      <details class="panel setting-section"><summary>Photograph and notification retention</summary><div class="setting-content">
      <p class="note">Both kinds of automatic deletion are disabled by default. Pinned photos and unread notifications are excluded from automatic cleanup.</p>
      <label class="checkline"><input type="checkbox" name="photo_cleanup_enabled" {% if cfg.photo_cleanup_enabled %}checked{% endif %}> Automatically delete unpinned old photographs</label>
      <label>Keep photographs for (days)</label><input type="number" min="1" max="3650" name="photo_retention_days" value="{{ cfg.photo_retention_days }}" required>
      <label class="checkline"><input type="checkbox" name="notice_cleanup_enabled" {% if cfg.notice_cleanup_enabled %}checked{% endif %}> Automatically delete old <strong>read</strong> notices</label>
      <div class="options"><div><label>Keep read summaries (days)</label><input type="number" min="1" max="3650" name="notice_report_days" value="{{ cfg.notice_report_days }}" required></div>
      <div><label>Keep read fault/recovery notices (days)</label><input type="number" min="1" max="3650" name="notice_fault_days" value="{{ cfg.notice_fault_days }}" required></div></div>
      <p><a href="{{ url_for('storage_page') }}">Manage recordings &amp; photographs</a></p></div></details>
      <button type="submit">Save settings</button>
    </div><div>
      <div class="panel"><h2>Storage overview</h2>
      <div class="sub">Video recordings</div><div class="value">{{ usage.video_gb }} GB</div>
      <div class="sub">Free disk space</div><div class="value">{{ usage.free_gb }} GB / {{ usage.disk_gb }} GB</div>
      <div class="sub">Total events</div><div class="value">{{ usage.total_events }}</div>
      <p class="note">{{ usage.protected_events }} events are protected by review status or pinning; {{ usage.pinned_events }} pinned.</p>
      <p class="note">Cleanup checks once a day, including after reboot. It removes eligible events and their associated files.</p></div>
      <div class="panel"><h2>How statuses work</h2>
      <p><strong>New:</strong> not yet opened.</p><p><strong>Viewed:</strong> opened in the dashboard, but not otherwise reviewed; its retention age starts when first viewed.</p>
      <p><strong>Flagged, Identified, Unresolved:</strong> saved decisions and protected from automatic deletion.</p>
      <p><strong>Dismissed:</strong> can be automatically removed after your chosen time.</p>
      </div>
    </div></div></form>''', title='Settings', cfg=cfg, usage=usage, plan=plan,
                       due_size=due_size, solar_info=solar_info,
                       saved=request.args.get('saved') == '1', error=error,
                       capabilities=capabilities, camera_profiles=get_profiles(cfg),
                       active_profile=selected_profile(cfg)[0], compass_label=compass_name(cfg.get('image_top_bearing', 0)),
                       fps_options=sorted(set(capabilities['fps_options']) | {int(cfg.get('fps', 15))}),
                       camera_reset_defaults={**{key:DEFAULTS[key] for key in (
                           'resolution','fps','pixel_threshold','min_changed_pixels',
                           'pre_motion_seconds','post_motion_seconds','max_clip_seconds')},
                           'fps':min(capabilities['fps_options'],key=lambda fps:abs(int(fps)-int(DEFAULTS['fps'])))
                           if capabilities['fps_options'] else int(cfg.get('fps',15))})


# Accounts are stored in SQLite, so changing a password does not require sudo
# or editing credentials files. Legacy auth.json is migrated once at startup.
USERNAME_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]{2,31}$')


def valid_credentials(username, password):
    if not USERNAME_RE.fullmatch(username):
        raise ValueError('Username must have 3–32 letters, numbers, dots, dashes or underscores.')
    if len(password) < 12 or len(password) > 200:
        raise ValueError('Password must contain 12–200 characters.')


@app.route('/account', methods=['GET', 'POST'])
def account():
    me = current_user()
    if not me:
        return redirect(url_for('login'))
    error = ''
    if request.method == 'POST':
        check_csrf()
        username = request.form.get('username', '').strip()
        current_pw = request.form.get('current_password', '')
        password = request.form.get('new_password', '')
        try:
            if not USERNAME_RE.fullmatch(username):
                raise ValueError('Username must have 3–32 allowed characters.')
            with connection() as db:
                row = db.execute('SELECT password_hash FROM users WHERE id=?', (me['id'],)).fetchone()
                if not row or not check_password_hash(row['password_hash'], current_pw):
                    raise ValueError('Current password is incorrect.')
                if password:
                    valid_credentials(username, password)
                db.execute('UPDATE users SET username=?, password_hash=?, session_version=session_version+1 WHERE id=?',
                           (username, generate_password_hash(password) if password else row['password_hash'], me['id']))
            session.clear()
            return redirect(url_for('login', changed=1))
        except (ValueError, sqlite3.IntegrityError) as exc:
            error = 'That username is already in use.' if 'UNIQUE' in str(exc) else str(exc)
    return render_page('''<h1>My account</h1><div class="panel auth"><p>Change your login name or password. Your current password is required. Other sessions will be signed out.</p>
      {% if error %}<p class="error">{{ error }}</p>{% endif %}
      <form method="post"><input type="hidden" name="csrf" value="{{ csrf }}">
      <label>Login name</label><input name="username" autocomplete="username" maxlength="32" value="{{ username }}" required>
      <label>Current password</label><input name="current_password" type="password" autocomplete="current-password" required>
      <label>New password (leave blank to keep it)</label><input name="new_password" type="password" minlength="12" autocomplete="new-password">
      <button type="submit">Save account</button></form></div>''', title='My account', username=me['username'], error=error)


@app.route('/users')
def users():
    with connection() as db:
        accounts = [dict(r) for r in db.execute('SELECT id,username,role,enabled FROM users ORDER BY id')]
    return render_page('''<h1>User accounts</h1><p class="note">Administrators can edit settings, review/share/delete events and manage users. Viewers can watch private recordings but cannot change any data.</p>
      <div class="panel"><h2>Accounts</h2><table><tr><th>Name</th><th>Role</th><th>Access</th><th></th></tr>{% for a in accounts %}<tr><td>{{ a.username }}</td><td>{{ a.role|title }}</td><td>{{ 'Enabled' if a.enabled else 'Disabled' }}</td><td><a href="{{ url_for('edit_user', user_id=a.id) }}">Manage</a></td></tr>{% endfor %}</table></div>
      <div class="panel"><h2>Add user</h2><form method="post" action="{{ url_for('create_user') }}"><input type="hidden" name="csrf" value="{{ csrf }}"><label>Username</label><input name="username" required maxlength="32"><label>Password (12+ characters)</label><input name="password" type="password" required minlength="12"><label>Role</label><select name="role"><option value="viewer">Viewer — read only</option><option value="admin">Administrator — full access</option></select><p><button type="submit">Create user</button></p></form></div>''', title='User accounts', accounts=accounts)


@app.route('/users/create', methods=['POST'])
def create_user():
    check_csrf()
    username = request.form.get('username','').strip()
    password = request.form.get('password','')
    role = request.form.get('role')
    if role not in ('admin','viewer'):
        abort(400)
    try:
        valid_credentials(username, password)
        with connection() as db:
            db.execute('INSERT INTO users(username,password_hash,role) VALUES (?,?,?)',
                       (username,generate_password_hash(password),role))
    except (ValueError, sqlite3.IntegrityError) as exc:
        return render_page('<div class="panel"><h1>Could not create account</h1><p class="error">{{ error }}</p><a href="{{ url_for(\'users\') }}">Go back</a></div>', title='Account error', error=str(exc)), 400
    return redirect(url_for('users'))


@app.route('/users/<int:user_id>', methods=['GET','POST'])
def edit_user(user_id):
    me = current_user()
    error = ''
    if request.method == 'POST':
        check_csrf()
        action = request.form.get('action')
        try:
            with connection() as db:
                db.execute('BEGIN IMMEDIATE')
                row = db.execute('SELECT id,role,enabled FROM users WHERE id=?',(user_id,)).fetchone()
                if row is None: abort(404)
                if action == 'access':
                    role = request.form.get('role')
                    enabled = 1 if request.form.get('enabled') == 'on' else 0
                    if role not in ('admin','viewer'): abort(400)
                    if user_id == me['id'] and (role != 'admin' or not enabled):
                        raise ValueError('You cannot disable or demote your own account.')
                    active_admins = db.execute("SELECT COUNT(*) FROM users WHERE role='admin' AND enabled=1").fetchone()[0]
                    if row['role']=='admin' and row['enabled'] and (role!='admin' or not enabled) and active_admins <= 1:
                        raise ValueError('At least one active administrator must remain.')
                    db.execute('UPDATE users SET role=?,enabled=?,session_version=session_version+1 WHERE id=?',
                               (role,enabled,user_id))
                elif action == 'reset_password':
                    password = request.form.get('password','')
                    if not 12 <= len(password) <= 200:
                        raise ValueError('Use a password with 12–200 characters.')
                    db.execute('UPDATE users SET password_hash=?,session_version=session_version+1 WHERE id=?',
                               (generate_password_hash(password),user_id))
                else: abort(400)
        except ValueError as exc:
            error = str(exc)
        else:
            # Updating your own account invalidates your current session.
            if user_id == me['id']:
                session.clear()
                return redirect(url_for('login'))
            return redirect(url_for('edit_user',user_id=user_id,saved=1))
    with connection() as db:
        account = db.execute('SELECT id,username,role,enabled FROM users WHERE id=?',(user_id,)).fetchone()
    if not account: abort(404)
    return render_page('''<p><a href="{{ url_for('users') }}">← User accounts</a></p><h1>Manage {{ account.username }}</h1>
      {% if error %}<p class="error">{{ error }}</p>{% endif %}{% if saved %}<p class="notice">Changes saved.</p>{% endif %}
      <div class="panel"><h2>Account access</h2><form method="post"><input type="hidden" name="csrf" value="{{ csrf }}"><input type="hidden" name="action" value="access"><label>Role</label><select name="role"><option value="viewer" {% if account.role=='viewer' %}selected{% endif %}>Viewer</option><option value="admin" {% if account.role=='admin' %}selected{% endif %}>Administrator</option></select><label class="checkline"><input type="checkbox" name="enabled" {% if account.enabled %}checked{% endif %}> Account enabled</label><p><button type="submit">Save access</button></p></form></div>
      <div class="panel"><h2>Set a new password</h2><p class="note">The new password takes effect immediately and signs out existing sessions.</p><form method="post"><input type="hidden" name="csrf" value="{{ csrf }}"><input type="hidden" name="action" value="reset_password"><label>New password</label><input type="password" name="password" minlength="12" autocomplete="new-password" required><p><button type="submit">Update password</button></p></form></div>''', title='Manage user', account=dict(account), error=error, saved=request.args.get('saved')=='1')


@app.route('/event/<int:event_id>/publish', methods=['POST'])
def publish_event(event_id):
    check_csrf()
    approved = 1 if request.form.get('public') == '1' else 0
    publish_note = 1 if approved and request.form.get('public_note') == '1' else 0
    with connection() as db:
        row = db.execute('SELECT video,demo FROM events WHERE id=?', (event_id,)).fetchone()
        if not row: abort(404)
        if approved and (not row['video'] or row['demo']): abort(400)
        db.execute('UPDATE events SET public=?,public_note=? WHERE id=?',(approved,publish_note,event_id))
    return redirect(url_for('event',event_id=event_id))


def public_allowed():
    return bool(read_config().get('public_enabled',False))


def published_event(event_id, field):
    if not public_allowed(): abort(404)
    with connection() as db:
        row = db.execute(f'SELECT {field} FROM events WHERE id=? AND public=1 AND video IS NOT NULL AND demo=0',(event_id,)).fetchone()
    if not row or not row[field]: abort(404)
    name = row[field]
    path = (THUMBS if field == 'thumbnail' else RECORDINGS) / name
    if name != Path(name).name or name.startswith('.') or not path.is_file() or path.is_symlink():
        abort(404)
    if path.suffix.lower() != ('.jpg' if field=='thumbnail' else '.mp4'):
        abort(404)
    return path


def public_location_details(config):
    """Return only explicitly approved public metadata, never all settings."""
    if not config.get('public_show_orientation', False):
        return []
    items = []
    if config.get('latitude') is not None and config.get('longitude') is not None:
        items.append(('Latitude', f"{float(config['latitude']):.6f}°"))
        items.append(('Longitude', f"{float(config['longitude']):.6f}°"))
    if config.get('schedule_timezone'):
        items.append(('Time zone', str(config['schedule_timezone'])))
    items.append(('Top-edge bearing', f"{int(config.get('image_top_bearing', 0))}°"))
    items.append(('Camera elevation', f"{int(config.get('camera_elevation', 90))}°"))
    return items


@app.route('/calendar')
def calendar_page():
    if not logged_in(): return redirect(url_for('login'))
    cfg = read_config()
    tzname = cfg.get('schedule_timezone') or 'Europe/London'
    local_today = datetime.now(timezone_for(tzname)).date()
    month_text = request.args.get('month', local_today.strftime('%Y-%m'))
    try:
        if not re.fullmatch(r'\d{4}-\d{2}',month_text): raise ValueError()
        year, month = (int(i) for i in month_text.split('-'))
        if not 2020 <= year <= 2100 or not 1 <= month <= 12: raise ValueError()
    except ValueError:
        abort(400)
    first=date(year,month,1)
    prev=(first-timedelta(days=1)).strftime('%Y-%m')
    following=(date(year+1,1,1) if month==12 else date(year,month+1,1)).strftime('%Y-%m')
    chosen=request.args.get('day',local_today.isoformat() if (year,month)==(local_today.year,local_today.month) else '')
    if chosen:
        try:
            selected=date.fromisoformat(chosen)
            if (selected.year,selected.month)!=(year,month):raise ValueError()
        except ValueError: abort(400)
    else: selected=None
    counts=calendar_month(year,month,tzname)
    job_counts={}
    with connection() as db:
        all_jobs=[dict(r) for r in db.execute("SELECT id,kind,title,start_utc,status FROM observation_jobs")]
    tz=timezone_for(tzname)
    for j in all_jobs:
        day=datetime.fromisoformat(j['start_utc']).astimezone(tz).date()
        if (day.year,day.month)==(year,month):
            job_counts[day.day]=job_counts.get(day.day,0)+1
    boxes=[]
    for week in cal_module.monthcalendar(year,month):
        boxes.extend(week)
    events=[]; info=None; scheduled_jobs=[]
    if selected:
        start,end=day_range(selected,tzname)
        events=recordings_between(start,end)
        info=summarize(events)
        scheduled_jobs=[j for j in all_jobs if datetime.fromisoformat(j['start_utc']).astimezone(tz).date()==selected]
    return render_page('''<h1>Observation Calendar</h1>
    <p class="note">Recording dates are shown in {{ tzname }}. Counts include saved camera recordings, not demonstrations.</p>
    <section class="panel"><div class="between"><a class="button" href="{{ url_for('calendar_page',month=prev) }}">← Previous</a>
    <h2>{{ first.strftime('%B %Y') }}</h2><a class="button" href="{{ url_for('calendar_page',month=following) }}">Next →</a></div>
    <div class="calendar-grid">{% for name in ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'] %}<strong style="text-align:center" class="sub">{{ name }}</strong>{% endfor %}
    {% for d in boxes %}{% if d %}{% set key='%04d-%02d-%02d'|format(first.year, first.month, d) %}
      <a class="calendar-cell {% if selected and d==selected.day %}selected{% endif %}" href="{{ url_for('calendar_page',month=month_text,day=key) }}"><strong>{{ d }}</strong><div class="sub">{{ counts.get(d,0) }} clips · {{job_counts.get(d,0)}} jobs</div></a>
    {% else %}<span class="calendar-blank"></span>{% endif %}{% endfor %}</div></section>
    {% if selected %}<section class="panel"><h2>{{ selected.strftime('%A %d %B %Y') }} — {{ info.total }} recordings</h2>
    <div class="stats"><span>Public: {{ info.public }}</span><span>Pinned: {{ info.pinned }}</span>
    {% for status,count in info.statuses|dictsort %}<span>{{ status|title }}: {{ count }}</span>{% endfor %}</div>
    <h2 style="margin-top:20px">Detection types</h2><div class="stats">{% for kind,count in info.triggers|dictsort %}<span>{{ kind }}: {{ count }}</span>{% else %}<span>No recordings</span>{% endfor %}</div>
    <p class="note">These are detection trigger types, not measured compass movement directions.</p>
    <h2>Scheduled videos and time-lapses</h2>
    {% for j in scheduled_jobs %}<p><a href="{{url_for('job_detail',job_id=j.id)}}">{{j.title}}</a> · {{j.kind|replace('_',' ')|title}} · {{j.status|title}}</p>
    {% else %}<p class="note">No scheduled sessions starting on this date.</p>{% endfor %}
    <h2>Motion recordings</h2>{% if events %}<table><thead><tr><th>Event</th><th>Local time</th><th>Status</th></tr></thead><tbody>
    {% for e in events %}<tr><td><a href="{{ url_for('event',event_id=e.id) }}">{{ e.kind }}</a><div class="note">#{{ e.id }}</div></td><td>{{ e.time_utc|localdt }}</td><td><span class="pill {{ e.status }}">{{ e.status|title }}</span></td></tr>{% endfor %}
    </tbody></table>{% else %}<p>No recordings on this date.</p>{% endif %}</section>{% endif %}''',
    title='Observation Calendar', tzname=tzname, prev=prev, following=following, first=first,
    selected=selected, boxes=boxes, counts=counts, job_counts=job_counts, scheduled_jobs=scheduled_jobs, events=events, info=info, month_text=month_text)


@app.route('/assets/storage-ui.js')
def storage_js():
    if not is_admin(): abort(403)
    return Response((Path(__file__).parent/'storage_ui.js').read_text(),mimetype='application/javascript')


@app.route('/storage', methods=['GET', 'POST'])
def storage_page():
    if not is_admin(): abort(403)
    tab=request.args.get('tab','overview')
    if tab not in TABS: tab='overview'
    if request.method=='POST':
        check_csrf()
        if request.form.get('confirm')!='DELETE':abort(400)
        action=request.form.get('action')
        if action=='delete' and tab=='recordings':
            result=delete_eligible_events(request.form.getlist('event_ids'))
        elif action=='delete_photos' and tab=='photos':
            result=delete_photos(request.form.getlist('photo_tokens'))
        elif action in ('delete_jobs','delete_sources') and tab in oj.KINDS:
            # Check tab, protection and terminal status inside oj.delete's writer transaction.
            ids=[]
            for value in request.form.getlist('job_ids')[:25]:
                try: ids.append(int(value))
                except (TypeError,ValueError):abort(400)
            count=0;reclaimed=0
            for job_id in dict.fromkeys(ids):
                job=oj.item(job_id)
                if not job or job['kind']!=tab: continue
                from storage_support import job_bytes
                sizes=job_bytes(job)
                if oj.delete(job_id,source_only=action=='delete_sources'):
                    count+=1;reclaimed+=sizes['zip'] if action=='delete_sources' else sizes['total']
            result={'count':count,'bytes':reclaimed}
        else:abort(400)
        return redirect(url_for('storage_page',tab=tab,deleted=result['count'],reclaimed=result['bytes']))
    status=request.args.get('status','all')
    statuses=RECORD_STATUSES if tab=='recordings' else JOB_STATUSES if tab in oj.KINDS else ('all',)
    if status not in statuses:status='all'
    visibility=request.args.get('visibility','all')
    if visibility not in ('all','public','private'):visibility='all'
    sort=request.args.get('sort','newest')
    if sort not in ('newest','oldest','largest'):sort='newest'
    older=request.args.get('older','0')
    if older not in ('0','7','30','60','90','180'):older='0'
    query=request.args.get('q','').strip()[:100]
    try:page=max(1,int(request.args.get('page',1)))
    except (ValueError,TypeError):page=1
    protection=request.args.get('protection','all')
    if protection not in ('all','protected','unprotected'):protection='all'
    all_rows=media_rows(tab,query,status,visibility,sort,older,protection) if tab!='overview' else []
    total=len(all_rows);tab_bytes=sum(row['bytes'] for row in all_rows)
    pages=max(1,(total+24)//25);page=min(page,pages)
    rows=all_rows[(page-1)*25:page*25]
    space=shutil.disk_usage(DATA)
    report=disk_report() if tab=='overview' else None
    return render_page(STORAGE_PAGE,title='Storage Management',tab=tab,rows=rows,total=total,
        page=page,pages=pages,status=status,statuses=statuses,visibility=visibility,sort=sort,older=older,query=query,protection=protection,
        space=space,report=report,tab_bytes=tab_bytes,terminal=oj.TERMINAL,
        deleted=int(request.args['deleted']) if request.args.get('deleted','').isdigit() else None,
        reclaimed=int(request.args.get('reclaimed',0)) if request.args.get('reclaimed','0').isdigit() else 0)


@app.route('/storage/photos')
def photo_gallery():
    if not logged_in():return redirect(url_for('login'))
    query=request.args.get('q','').strip()[:100]
    visibility=request.args.get('visibility','all')
    pin=request.args.get('pin','all')
    if visibility not in ('all','public','private'):visibility='all'
    if pin not in ('all','pinned','unpinned'):pin='all'
    entries=[p for p in photos() if query.casefold() in (p['title']+' '+p['note']).casefold()
             and (visibility=='all' or bool(p['public'])==(visibility=='public'))
             and (pin=='all' or bool(p['pinned'])==(pin=='pinned'))]
    try:page=max(1,int(request.args.get('page',1)))
    except (ValueError,TypeError):page=1
    pages=max(1,(len(entries)+11)//12);page=min(page,pages)
    return render_page(GALLERY,title='Photograph Gallery',entries=entries[(page-1)*12:page*12],total=len(entries),page=page,pages=pages,query=query,visibility=visibility,pin=pin)


@app.route('/storage/photos/<token>/',methods=['GET','POST'])
def photo_detail(token):
    if not logged_in():return redirect(url_for('login'))
    if not re.fullmatch(r'[0-9a-f]{32}',token):abort(404)
    photo=next((p for p in photos() if p['token']==token),None)
    if photo is None:abort(404)
    if request.method=='POST':
        if not is_admin():abort(403)
        check_csrf()
        action=request.form.get('action')
        try:
            if action=='details':
                set_photo_details(token,request.form.get('title',''),request.form.get('note',''),
                                  request.form.get('public')=='1',request.form.get('public_note')=='1')
            elif action in ('pin','unpin'):
                set_photo_pin(token,action=='pin')
            else:abort(400)
        except ValueError:abort(400)
        return redirect(url_for('photo_detail',token=token))
    return render_page(PHOTO_DETAIL,title='Photograph',photo=photo,detail=details_for_photo(token))


@app.route('/storage/photos/<token>/original')
def photo_original(token):
    if not logged_in():abort(403)
    if not re.fullmatch(r'[0-9a-f]{32}',token):abort(404)
    source=next((photo_output_path(token,x) for x in ('jpg','png') if photo_output_path(token,x).is_file()),None)
    if source is None or source.is_symlink():abort(404)
    downloading=request.args.get('download')=='1'
    details=next((item for item in photos() if item['token']==token),None)
    return send_file(source,mimetype='image/png' if source.suffix=='.png' else 'image/jpeg',
                     conditional=True,as_attachment=downloading,
                     download_name=photo_filename(token[:8], details['title'] if details else 'Camera-capture',source.suffix) if downloading else None)


@app.route('/storage/photos/<token>/delete',methods=['GET','POST'])
def photo_gallery_delete(token):
    if not is_admin():abort(403)
    # All deletion operations go through Storage Management's confirmation modal.
    return redirect(url_for('storage_page',tab='photos'))


@app.route('/storage/photos/<token>/thumbnail.jpg')
def photo_gallery_thumb(token):
    if not logged_in(): abort(403)
    import re
    if not re.fullmatch(r'[0-9a-f]{32}',token): abort(404)
    from photography import ROOT as PHOTO_ROOT
    source = next((photo_output_path(token,fmt) for fmt in ('jpg','png') if photo_output_path(token,fmt).is_file()),None)
    if source is None or source.is_symlink(): abort(404)
    thumb = PHOTO_ROOT / ('thumb-'+token+'.jpg')
    try:
        if not thumb.is_file() or thumb.stat().st_mtime < source.stat().st_mtime:
            import cv2
            arr=cv2.imread(str(source),cv2.IMREAD_COLOR)
            if arr is None: abort(404)
            height,width=arr.shape[:2]
            scale=min(320/width,200/height,1)
            smaller=cv2.resize(arr,(max(1,int(width*scale)),max(1,int(height*scale))))
            target=PHOTO_ROOT/('thumb-'+token+'.pending.jpg')
            if not cv2.imwrite(str(target),smaller,[cv2.IMWRITE_JPEG_QUALITY,78]): abort(500)
            target.replace(thumb)
    except OSError: abort(404)
    return send_file(thumb,mimetype='image/jpeg')


@app.route('/notifications',methods=['GET','POST'])
def notices_page():
    user=current_user()
    if not user: return redirect(url_for('login'))
    error=''
    if request.method=='POST':
        check_csrf()
        if request.form.get('action')=='preferences':
            try:
                update_preferences(user['id'], request.form.get('frequency','off'),request.form.get('local_time','08:00'),
                                   request.form.get('timezone','Europe/London').strip(),request.form.get('weekday','0'))
                return redirect(url_for('notices_page',saved=1))
            except ValueError as exc: error=str(exc)
        elif request.form.get('action')=='delivery':
            try:
                delivery.save_user_settings(user['id'],request.form.get('recipient_email',''),
                                            request.form.get('email_enabled')=='1',request.form.get('push_enabled')=='1')
                return redirect(url_for('notices_page',saved=1)+'#delivery')
            except ValueError as exc:error=str(exc)
        elif request.form.get('action')=='remove_push':
            try: sid=int(request.form.get('sub_id',''))
            except ValueError:abort(400)
            delivery.remove_subscription(user['id'],sid)
            return redirect(url_for('notices_page')+'#delivery')
        elif request.form.get('action') in ('test_email','test_push'):
            if time.monotonic()-session.get('last_delivery_test',-999999)<45:
                error='Please wait at least 45 seconds between delivery tests.'
            else:
                session['last_delivery_test']=time.monotonic()
                try:
                    if request.form['action']=='test_email':
                        recipient=delivery.user_settings(user['id'])['recipient_email']
                        delivery.smtp_send(recipient,'Moon Cheese test email',
                                           'This is a test. Your detector is able to hand email to the configured SMTP provider.',
                                           url=delivery.dashboard_url()[0],remote=delivery.dashboard_url()[1])
                    else:
                        sub_id=int(request.form.get('sub_id','0'))
                        with connection() as db:
                            sub=db.execute('SELECT * FROM push_subscriptions WHERE id=? AND user_id=?',(sub_id,user['id'])).fetchone()
                        if not sub:raise ValueError('Browser device not found.')
                        delivery.push_send(dict(sub),'Moon Cheese test notification','Browser Push is configured.')
                    return redirect(url_for('notices_page',test=1)+'#delivery')
                except Exception as exc:
                    error=(delivery.smtp_failure_message(exc,delivery.smtp_settings()) if request.form['action']=='test_email'
                           else 'Browser push test failed. Check HTTPS, browser permission and device subscription.')
        elif request.form.get('action')=='read':
            try: nid=int(request.form.get('notice_id',''))
            except ValueError: abort(400)
            with connection() as db:
                db.execute('UPDATE notices SET read_at=? WHERE id=? AND user_id=? AND read_at IS NULL',
                           (datetime.now(timezone.utc).isoformat(timespec='seconds'),nid,user['id']))
            return redirect(url_for('notices_page'))
        elif request.form.get('action')=='delete':
            try: nid=int(request.form.get('notice_id',''))
            except ValueError: abort(400)
            with connection() as db:
                db.execute('DELETE FROM notices WHERE id=? AND user_id=?',(nid,user['id']))
            return redirect(url_for('notices_page'))
        elif request.form.get('action')=='delete_read':
            with connection() as db:
                db.execute('DELETE FROM notices WHERE user_id=? AND read_at IS NOT NULL',(user['id'],))
            return redirect(url_for('notices_page'))
        elif request.form.get('action')=='read_all':
            with connection() as db:
                db.execute('UPDATE notices SET read_at=? WHERE user_id=? AND read_at IS NULL',
                           (datetime.now(timezone.utc).isoformat(timespec='seconds'),user['id']))
            return redirect(url_for('notices_page'))
        else: abort(400)
    cfg=read_config()
    pref=notice_preferences(user['id'],cfg.get('schedule_timezone') or 'Europe/London')
    category=request.args.get('category','all').lower()
    if category not in ('all','unread','digest','fault','recovery'): category='all'
    try: page=max(1,int(request.args.get('page','1')))
    except ValueError: page=1
    clause='user_id=?' + (" AND read_at IS NULL" if category=='unread' else ' AND category=?' if category!='all' else '')
    arguments=(user['id'],category) if category not in ('all','unread') else (user['id'],)
    with connection() as db:
        total=db.execute('SELECT COUNT(*) FROM notices WHERE '+clause,arguments).fetchone()[0]
        pages=max(1,(total+9)//10)
        page=min(pages,page)
        notices=[dict(r) for r in db.execute('SELECT * FROM notices WHERE '+clause+' ORDER BY id DESC LIMIT 10 OFFSET ?',(*arguments,(page-1)*10))]
    pref_delivery=delivery.user_settings(user['id'])
    delivery_sections=render_template_string(USER_DELIVERY,csrf=csrf_token(),pref=pref,
        delivery_pref=pref_delivery,mail_ready=bool(delivery.smtp_settings().get('enabled')),
        browser_subs=delivery.subscriptions(user['id']),own_delivery=delivery.recent_delivery(user['id'],limit=10))
    return render_page('''<h1>Notifications</h1><p class="note">Times shown in {{pref.timezone}}.</p><p class="note">Reports and important notices appear here after you sign in. You may optionally enable email and browser delivery below.</p>
      {% if saved %}<div class="notice">Your preferences were saved.</div>{% endif %}{% if test_ok %}<div class="notice">The test was accepted by your delivery provider. Check the recipient inbox or device.</div>{% endif %}
      {% if error %}<p class="error">{{ error }}</p>{% endif %}
      <section class="panel" id="notification-centre"><div class="between"><h2>Notification centre</h2><form method="post"><input type="hidden" name="csrf" value="{{ csrf }}"><input type="hidden" name="action" value="read_all"><button type="submit">Mark all read</button></form></div>
      <div class="between"><form method="get" class="row"><label>Filter <select name="category" >{% for c in ['all','unread','digest','fault','recovery'] %}<option value="{{ c }}" {% if c==category %}selected{% endif %}>{{ c|title }}</option>{% endfor %}</select></label><button type="submit">Apply</button></form>
      <form method="post" onsubmit="return confirm('Delete all read notifications?')"><input type="hidden" name="csrf" value="{{ csrf }}"><input type="hidden" name="action" value="delete_read"><button type="submit" class="danger">Delete all read</button></form></div>
      <p class="note">{{ total }} notice(s) · page {{ page }} of {{ pages }} · 10 per page</p>
      <div class="notices-list">{% for n in notices %}<article class="panel {% if not n.read_at %}notice-unread{% endif %}" style="margin:0">
      <div class="between"><h2>{{ n.title }}</h2><span class="note">{{ n.created_utc|localdt(pref.timezone) }}</span></div>
      <p class="note">{{ 'Scheduled job' if n.unique_key.startswith('observation-job:') else n.category|title }}{% if not n.read_at %} · Unread{% endif %}</p>
      <p style="white-space:pre-wrap;overflow-wrap:anywhere">{{ n.body }}</p>
      {% if not n.read_at %}<form method="post"><input type="hidden" name="csrf" value="{{ csrf }}"><input type="hidden" name="action" value="read"><input type="hidden" name="notice_id" value="{{ n.id }}"><button type="submit">Mark read</button></form>{% endif %}
      <form method="post" style="margin-top:8px" onsubmit="return confirm('Delete this notification?')"><input type="hidden" name="csrf" value="{{ csrf }}"><input type="hidden" name="action" value="delete"><input type="hidden" name="notice_id" value="{{ n.id }}"><button type="submit" class="danger">Delete</button></form></article>
      {% else %}<p>No notifications match this filter.</p>{% endfor %}</div>
      <div class="between" style="margin-top:12px">{% if page>1 %}<a class="button" href="{{ url_for('notices_page',page=page-1,category=category) }}">← Previous</a>{% endif %}
      {% if page<pages %}<a class="button" href="{{ url_for('notices_page',page=page+1,category=category) }}">Next →</a>{% endif %}</div></section>
      <details class="panel setting-section" id="summary-preferences"><summary>Observation summary preferences</summary><div class="setting-content"><form method="post">
      <input type="hidden" name="csrf" value="{{ csrf }}"><input type="hidden" name="action" value="preferences">
      <div class="options"><div><label for="frequency">Frequency</label><select name="frequency" id="frequency">
      {% for item in ['off','daily','weekly'] %}<option value="{{ item }}" {% if pref.frequency==item %}selected{% endif %}>{{ item|title }}</option>{% endfor %}</select></div>
      <div><label for="local_time">Report time</label><input id="local_time" name="local_time" type="time" required value="{{ pref.local_time }}"></div>
      <div><label for="timezone">My report timezone</label><select name="timezone" id="timezone" required>{% for zone in timezone_options %}<option value="{{zone}}" {% if zone==pref.timezone %}selected{% endif %}>{{zone}}</option>{% endfor %}</select><div class="row" style="margin-top:8px"><button type="button" id="detect-timezone">Use my browser timezone</button><span id="timezone-note" class="note" role="status">Only this account's report delivery schedule is affected.</span></div></div>
      <div><label for="weekday">Weekly report day</label><select id="weekday" name="weekday">{% for day in weekdays %}
      <option value="{{ loop.index0 }}" {% if pref.weekday==loop.index0 %}selected{% endif %}>{{ day }}</option>{% endfor %}</select></div></div>
      <p class="note">Daily summaries cover the most recent 24 hours ending at your report time; weekly summaries cover the most recent 168 hours ending at your report time. These are private in-dashboard reports. You can turn them off at any time.</p>
      <button type="submit">Save preferences</button></form><script src="{{url_for('notification_timezone_js')}}" defer></script></div></details>
      {{delivery_sections|safe}}''',
      title='Notifications', pref=pref, notices=notices, weekdays=WEEKDAYS,
      total=total,pages=pages,page=page,category=category,
      saved=request.args.get('saved')=='1', test_ok=request.args.get('test')=='1',
      delivery_sections=delivery_sections,error=error,timezone_options=sorted(available_timezones()))


@app.route('/assets/notification-tz.js')
def notification_timezone_js():
    if not logged_in():abort(403)
    return send_file(Path(__file__).with_name('notification_tz.js'),mimetype='application/javascript')


@app.route('/assets/push-ui.js')
def push_ui_js():
    if not logged_in():abort(403)
    return send_file(Path(__file__).with_name('push_ui.js'),mimetype='application/javascript')


@app.route('/push-sw.js')
def push_sw_js():
    return send_file(Path(__file__).with_name('push_sw.js'),mimetype='application/javascript',
                     max_age=0)


@app.route('/notifications/push/key')
def push_public_key():
    if not logged_in():abort(403)
    try:return jsonify(publicKey=delivery.vapid_keys()['public'])
    except (ImportError,OSError):return jsonify(error='Encrypted Web Push prerequisites unavailable.'),503


@app.route('/notifications/push/subscribe',methods=['POST'])
def push_subscribe():
    user=current_user()
    if not user:abort(403)
    payload=request.get_json(silent=True)
    if not isinstance(payload,dict):abort(400)
    if not secrets.compare_digest(str(payload.get('csrf','')),session.get('csrf','_')):abort(403)
    try:delivery.register_subscription(user['id'],payload.get('endpoint',''),payload.get('p256dh',''),
                                        payload.get('auth',''),payload.get('device','Browser'))
    except (ValueError,OSError) as exc:return jsonify(error=str(exc)),400
    return jsonify(success=True)


@app.route('/public')
def public_page():
    if not public_allowed():
        abort(404)
    public_cfg = read_config()
    camera_busy = oj.active()
    public_location = (str(public_cfg.get('location_name') or '').strip()
                       if public_cfg.get('public_show_location_name', False) else '')
    public_details = public_location_details(public_cfg)
    # Only one media tab is rendered per request. Both tabs are individually
    # paginated; this caps image/video elements on the public landing page.
    media = request.args.get('media', 'recordings')
    if media not in ('recordings', 'photographs','scheduled','timelapses'):
        media = 'recordings'
    try:
        page = max(1, int(request.args.get('page', 1)))
    except (ValueError, TypeError):
        page = 1
    with connection() as db:
        count_sql = ("SELECT COUNT(*) FROM events WHERE public=1 "
                     "AND video IS NOT NULL AND demo=0")
        clip_count = db.execute(count_sql).fetchone()[0]
        clip_pages = max(1, (clip_count + 4) // 5)
        photo_page_items = [p for p in photos() if p['public']]
        photo_count = len(photo_page_items)
        photo_pages = max(1, (photo_count + 5) // 6)
        job_counts={row['kind']:row['total'] for row in db.execute("SELECT kind,COUNT(*) AS total FROM observation_jobs WHERE status='complete' AND public=1 GROUP BY kind")}
        scheduled_count=job_counts.get('scheduled_video',0)
        timelapse_count=job_counts.get('timelapse',0)
        job_kind = ('scheduled_video' if media=='scheduled' else 'timelapse')
        if media in ('scheduled','timelapses'):
            job_count = db.execute("SELECT COUNT(*) FROM observation_jobs WHERE kind=? AND status='complete' AND public=1",(job_kind,)).fetchone()[0]
            job_pages=max(1,(job_count+4)//5)
        else:
            job_count=0
            job_pages=1
        pages = clip_pages if media == 'recordings' else photo_pages if media == 'photographs' else job_pages
        page = min(page, pages)
        events = []
        shared_photos = []
        shared_jobs = []
        if media in ('scheduled','timelapses'):
            shared_jobs = [dict(r) for r in db.execute("SELECT id,kind,title,note,start_utc,public_note FROM observation_jobs WHERE kind=? AND status='complete' AND public=1 ORDER BY id DESC LIMIT 5 OFFSET ?",(job_kind,(page-1)*5))]
        if media == 'recordings':
            events = [dict(r) for r in db.execute(
                "SELECT id,kind,time_utc,thumbnail,"
                "CASE WHEN public_note=1 THEN note ELSE '' END AS shared_note "
                "FROM events WHERE public=1 AND video IS NOT NULL AND demo=0 "
                "ORDER BY id DESC LIMIT 5 OFFSET ?", ((page-1)*5,))]
        elif media == 'photographs':
            shared_photos = photo_page_items[(page-1)*6:page*6]
    return render_page('''<h1>Sky camera{% if public_location %} - {{ public_location }}{% endif %}</h1>
      {% if public_details %}<section class="panel" aria-label="Camera location and orientation"><h2>Camera location &amp; orientation</h2><div class="public-detail-grid">
      {% for label, value in public_details %}<div><span class="note">{{ label }}</span><br><strong>{{ value }}</strong></div>{% endfor %}
      </div></section>{% endif %}
      <p class="note">Recent camera image updates approximately every 10 seconds. This is not a live video stream.</p>
      <section class="panel"><h2>Recent camera still</h2>
      {% if camera_busy %}<p class="note">Camera busy: a scheduled recording or time-lapse is running. Snapshot updates will resume afterwards.</p>
      {% else %}<img id="public-preview" class="preview" src="{{ url_for('public_snapshot') }}" alt="Latest camera frame"><p class="note" id="public-note">If unavailable, the camera may not have captured a still yet.</p><script src="{{ url_for('public_js') }}" defer></script>{% endif %}</section>
      <section class="panel" id="shared-media"><h2>Shared observations</h2>
        <nav class="public-media-tabs" aria-label="Shared media categories">
          <a class="button {% if media=='recordings' %}active{% endif %}" {% if media=='recordings' %}aria-current="page"{% endif %} href="{{url_for('public_page',media='recordings',page=1)}}#shared-media">Recordings ({{clip_count}})</a>
          <a class="button {% if media=='photographs' %}active{% endif %}" {% if media=='photographs' %}aria-current="page"{% endif %} href="{{url_for('public_page',media='photographs',page=1)}}#shared-media">Photographs ({{photo_count}})</a>
          <a class="button {% if media=='scheduled' %}active{% endif %}" href="{{url_for('public_page',media='scheduled',page=1)}}#shared-media">Scheduled Videos ({{scheduled_count}})</a>
          <a class="button {% if media=='timelapses' %}active{% endif %}" href="{{url_for('public_page',media='timelapses',page=1)}}#shared-media">Time-lapses ({{timelapse_count}})</a>
        </nav>
        {% if media=='recordings' %}
          <p class="note">Select a recording to expand and play it.</p>
          {% if events %}<div class="public-clip-list">
            {% for e in events %}<details class="public-clip">
              <summary aria-label="Expand {{ e.kind }} recording">
                <span class="public-clip-title">{{ e.kind }}</span>
                <span class="public-clip-date">{{ e.time_utc|localdt }}</span>
                {% if e.thumbnail %}<img class="public-clip-preview" src="{{ url_for('public_thumbnail',event_id=e.id) }}" alt="Shared clip thumbnail" loading="lazy">{% else %}<span class="public-clip-preview" aria-hidden="true"></span>{% endif %}
              </summary>
              <div class="public-video {% if e.shared_note %}with-notes{% endif %}">
                <div><video controls controlslist="nodownload" disablepictureinpicture playsinline preload="none" src="{{ url_for('public_video',event_id=e.id) }}" aria-label="{{ e.kind }} recording"></video>
                <p class="note">Recorded {{ e.time_utc|localdt }}</p></div>
                {% if e.shared_note %}<aside class="public-notes" aria-label="Recording notes"><h3>Observation notes</h3><p>{{ e.shared_note }}</p></aside>{% endif %}
              </div>
            </details>{% endfor %}
          </div>{% else %}<p class="muted">No recordings have been shared.</p>{% endif %}
        {% elif media in ('scheduled','timelapses') %}
          {% for j in shared_jobs %}<details class="public-clip"><summary><span class="public-clip-title">{{j.title}}</span><span class="public-clip-date">{{j.start_utc|localdt}}</span>
          <img loading="lazy" class="public-clip-preview" src="{{url_for('public_job_thumb',job_id=j.id)}}" alt="Observation thumbnail"></summary>
          <div class="public-video {% if j.public_note and j.note %}with-notes{% endif %}">
          <div>{% if j.kind=='timelapse' %}<video controls controlslist="nodownload" playsinline preload="none" src="{{url_for('public_job_media',job_id=j.id,filename='timelapse.mp4')}}"></video>
          {% else %}{% set segments=job_segment_names(j.id) %}{% if segments %}<video controls controlslist="nodownload" playsinline preload="none" src="{{url_for('public_job_media',job_id=j.id,filename=segments[0])}}"></video><p><a href="{{url_for('public_job_detail',job_id=j.id)}}">View all {{segments|length}} recording segments →</a></p>{% endif %}{% endif %}</div>
          {% if j.public_note and j.note %}<aside class="public-notes"><h3>Observation notes</h3><p>{{j.note}}</p></aside>{% endif %}</div></details>
          {% else %}<p class="note">No shared observations in this category.</p>{% endfor %}
        {% else %}
          {% if shared_photos %}<div class="photo-gallery-grid">
            {% for photo in shared_photos %}<div class="photo-gallery-card"><img loading="lazy" src="{{url_for('public_photo',token=photo.token)}}" alt="Shared photograph"><strong>{{photo.title or 'Photograph '+photo.token[:8]}}</strong><span class="note">{{photo.modified|localday}}</span>
            {% if photo.public_note and photo.note %}<p style="white-space:pre-wrap">{{photo.note}}</p>{% endif %}</div>{% endfor %}
          </div>{% else %}<p class="muted">No photographs have been shared.</p>{% endif %}
        {% endif %}
        <nav class="public-media-pagination" aria-label="Shared media pages">
          <span class="note">Page {{page}} of {{pages}}</span>
          <div class="row">
          {% if page>1 %}<a class="button" href="{{url_for('public_page',media=media,page=page-1)}}#shared-media">← Previous</a>{% endif %}
          {% if page<pages %}<a class="button" href="{{url_for('public_page',media=media,page=page+1)}}#shared-media">Next →</a>{% endif %}
          </div>
        </nav>
      </section>''',
      title='Public sky camera', events=events, public_view=True,
      public_location=public_location, public_details=public_details,
      camera_busy=camera_busy, shared_photos=shared_photos, shared_jobs=shared_jobs, job_segment_names=lambda jid:[x.name for x in oj.files(jid)], media=media, clip_count=clip_count,
      photo_count=photo_count, scheduled_count=scheduled_count, timelapse_count=timelapse_count, page=page, pages=pages)

@app.route('/public/photo/<token>.jpg')
def public_photo(token):
    if not public_allowed() or not re.fullmatch(r'[0-9a-f]{32}',token):abort(404)
    if not details_for_photo(token)['public']:abort(404)
    source=next((photo_output_path(token,ext) for ext in ('jpg','png') if photo_output_path(token,ext).is_file()),None)
    if source is None or source.is_symlink():abort(404)
    # Never deliver the original's EXIF, GPS or other embedded metadata publicly.
    # Cache the reduced, EXIF-free copy. Don't decode a 12 MP original for
    # every public visitor or repeatedly reveal original embedded metadata.
    from photography import ROOT as PHOTO_ROOT
    safe=PHOTO_ROOT/('public-'+token+'.jpg')
    if not safe.is_file() or safe.is_symlink() or safe.stat().st_mtime < source.stat().st_mtime:
        import cv2
        frame=cv2.imread(str(source),cv2.IMREAD_COLOR)
        if frame is None:abort(404)
        height,width=frame.shape[:2]
        scale=min(1600/width,900/height,1)
        if scale<1:frame=cv2.resize(frame,(max(1,round(width*scale)),max(1,round(height*scale))))
        pending=PHOTO_ROOT/('public-'+token+'-'+secrets.token_hex(8)+'.tmp.jpg')
        ok=cv2.imwrite(str(pending),frame,[cv2.IMWRITE_JPEG_QUALITY,82])
        if not ok:abort(500)
        os.replace(pending,safe)
    return send_file(safe,mimetype='image/jpeg',conditional=True)


@app.route('/public/snapshot.jpg')
def public_snapshot():
    if not public_allowed(): abort(404)
    if oj.active(): abort(503, 'Camera in use by scheduled observation')
    image = DATA/'latest.jpg'
    if not image.is_file() or image.is_symlink(): abort(404)
    return send_file(image,mimetype='image/jpeg')


@app.route('/public/<int:event_id>/thumb.jpg')
def public_thumbnail(event_id):
    return send_file(published_event(event_id,'thumbnail'),mimetype='image/jpeg')


@app.route('/public/<int:event_id>/video.mp4')
def public_video(event_id):
    return send_file(published_event(event_id,'video'),mimetype='video/mp4',conditional=True)


@app.route('/assets/public.js')
def public_js():
    return Response("""document.addEventListener('DOMContentLoaded',()=>{const img=document.getElementById('public-preview'); if(!img)return;setInterval(()=>{const next=new Image();next.onload=()=>{img.src=next.src;img.style.display='block';};next.src='/public/snapshot.jpg?t='+Date.now();},10000);});""",mimetype='application/javascript')

@app.route('/assets/help.js')
def help_js():
    if not logged_in(): abort(403)
    return send_file(Path(__file__).with_name('help.js'),mimetype='application/javascript')


@app.route('/help')
def help_page():
    if not logged_in():
        return redirect(url_for('login'))
    return render_page(help_html(), title='Help')


def release_timeline():
    return RELEASES


@app.route('/assets/network-ui.js')
def network_ui_js():
    if not is_admin():abort(403)
    return send_file(Path(__file__).with_name('network_ui.js'),mimetype='application/javascript')


@app.route('/assets/network-confirm.js')
def network_confirm_js():
    if not is_admin():abort(403)
    return send_file(Path(__file__).with_name('network_confirm.js'),mimetype='application/javascript')

@app.route('/system/network/status')
def network_status():
    if not is_admin():abort(403)
    return jsonify({'operations':network_setup.all_statuses(),
                    'network':network_setup.public_status('ip_change'),
                    'pending':network_setup.pending_change(),
                    'wifi_scan':network_setup.public_status('wifi_scan'),
                    'wifi_radio':network_setup.wifi_radio_state(), 'interfaces':network_setup.network_interfaces(), 'server_time':time.time()})


@app.route('/system/network/action',methods=['POST'])
def network_action():
    if not is_admin():return jsonify(error='Administrator session expired. Sign in again and reopen System Administration.'),403
    if not secrets.compare_digest(request.form.get('csrf',''), session.get('csrf','_')):
        return jsonify(error='The page security token expired. Reload System Administration and try again.'),403
    action=request.form.get('action','')
    if action not in ('local','npm','tunnel','ip_change','ddns_check','external','wifi_scan','wifi_connect','wifi_radio','npm_preview','npm_change','npm_retire_old','tunnel_abandon','tunnel_cleanup','tunnel_disable','tunnel_remove','npm_apply','tunnel_apply'):
        abort(400)
    if not verify_current_admin_password(request.form.get('password','')):
        # DDNS 'Check now' can be triggered without a second password because it
        # doesn't change settings; the other operations require reauthentication.
        if action not in ('ddns_check','wifi_scan'):
            return jsonify(error='Administrator password was not accepted.'),403
    if action in ('npm','tunnel','ip_change','wifi_connect','wifi_radio','npm_change','tunnel_abandon') and request.form.get('ack')!='yes':
        return jsonify(error='Confirm that you understand and authorise this change.'),400
    fields={'hostname','zone','token','email','account','mode','ip','gateway','prefix','dns',
            'adopt_dns','replace_incomplete','sync_contact','interface','enabled','ssid','wifi_password','preview_id','reuse_certificate','retire_old','recover_tunnel','replace_tunnel','ack'}
    try:
        params={k:request.form.get(k,'')[:650] for k in fields}
        if action in ('npm_apply','tunnel_apply','npm_retire_old','tunnel_remove','tunnel_disable'):
            params['ack']='yes'
        if action in ('npm','npm_preview','npm_change','npm_apply'):
            if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", params['email']) or len(params['email'])>254:
                raise ValueError("Enter a valid Let's Encrypt contact email address.")
        if action in ('npm','tunnel','npm_preview','npm_change','npm_apply','tunnel_apply'):
            network_setup.valid_hostname(params['hostname'])
            network_setup.valid_id(params['zone'])
            if params['token']:network_setup.valid_token(params['token'])
            elif action not in ('npm_apply','tunnel_apply'):network_setup.valid_token(params['token'])
            if action in ('tunnel','tunnel_apply'):network_setup.valid_id(params['account'],'Account ID')
        if action=='ip_change' and params['mode']=='static':
            network_setup.valid_ipv4(params['ip'])
        if action=='ip_change' and (params['mode'] not in ('dhcp','static') or not params['interface']):
            raise ValueError('Select an active interface and either DHCP or static IPv4.')
        if action=='npm_change' and not re.fullmatch(r'[a-f0-9]{32}',params['preview_id']):
            raise ValueError('Check and review the replacement domain before applying it.')
        request_id=network_setup.queue_action(action,params)
    except (ValueError,OSError) as exc:
        return jsonify(error=str(exc)),400
    if 'application/json' in request.headers.get('Accept','') or action=='ip_change':
        return jsonify(queued=True,request_id=request_id),202
    return redirect(url_for('system_admin',network=action)+'#network-admin')


@app.route('/system/network/confirm',methods=['GET','POST'])
def network_confirm():
    if not logged_in():
        return redirect(url_for('login',next='network_confirm'))
    if not is_admin():abort(403)
    pending=network_setup.pending_change()
    if request.method=='POST':
        check_csrf()
        if not pending or pending.get('expires',0)<=time.time():
            return render_page('<div class="notice">No pending network change. It may already have reverted.</div>',title='Network confirmation')
        # The host must be the new IP; old browser tabs may not confirm.
        host=request.host.split(':',1)[0]
        if host!=pending.get('new_ip'):
            abort(403,'Confirmation must come through the new IP address.')
        if not verify_current_admin_password(request.form.get('password','')):
            abort(403,'Administrator password not accepted.')
        network_setup.queue_action('ip_confirm',{'new_ip':pending['new_ip']})
        return render_page('<div class="notice">Confirmation submitted. Refresh System Administration to verify that the change was confirmed before closing the original tab.</div>',title='Network confirmation')
    return render_page(render_template_string(CONFIRM_PAGE,csrf=csrf_token(),pending=pending),title='Network confirmation')


@app.route('/system/administration',methods=['GET','POST'])
def system_admin():
    if not is_admin():abort(403)
    error=None;notice=None;preview=None
    if request.method=='POST':
        check_csrf()
        action=request.form.get('action')
        try:
            if action=='smtp_save':
                delivery.save_smtp(request.form.get('smtp_host'),request.form.get('smtp_port'),
                    request.form.get('smtp_username'),request.form.get('smtp_secret'),
                    request.form.get('smtp_from'),request.form.get('smtp_security','starttls'),
                    request.form.get('smtp_enabled')=='1')
                notice='Outgoing email configuration saved. No email was sent; use Send test email to verify your provider.'
            elif action=='dashboard_links_save':
                delivery.save_dashboard_links(request.form.get('local_url',''),request.form.get('public_url',''))
                notice='Dashboard notification links saved. Public HTTPS URLs take priority over local links.'
            elif action=='push_contact_save':
                delivery.save_push_contact(request.form.get('push_contact_email',''))
                notice='Web Push contact address saved. Browsers may now subscribe independently of SMTP.'
            elif action=='smtp_test':
                config=delivery.smtp_settings()
                if not config:raise ValueError('Save outgoing SMTP settings first.')
                delivery.smtp_send(config['from_email'],'Moon Cheese SMTP test',
                    'This is a test email sent by the detector.',config={**config,'enabled':True},
                    url=delivery.dashboard_url()[0],remote=delivery.dashboard_url()[1])
                notice='SMTP provider accepted the test message. Check the sender inbox.'
            elif action=='delivery_retention_save':
                days=delivery.save_delivery_retention(request.form.get('days','90'))
                notice=f'Technical delivery history retention set to {days} days. Actual notifications are unaffected.'
            elif action=='retry_delivery':
                try: ident=int(request.form.get('delivery_id',''))
                except ValueError:raise ValueError('Invalid delivery reference.')
                notice=('Delivery queued for another attempt.' if delivery.retry_failed(ident)
                        else 'Delivery was not in a failed state; nothing changed.')
            elif action=='export':
                with_users=request.form.get('scope')=='users'
                if with_users and not verify_current_admin_password(request.form.get('password','')):
                    raise ValueError('Confirm your current administrator password to export user accounts.')
                payload=encode_backup(export_document(users=with_users),request.form.get('passphrase',''))
                name=('UAP-Settings-and-Users-' if with_users else 'UAP-Settings-')+datetime.now(timezone.utc).strftime('%Y%m%d')+('.uapenc' if with_users else '.json')
                return send_file(io.BytesIO(payload),as_attachment=True,download_name=name,
                                 mimetype='application/octet-stream' if with_users else 'application/json')
            elif action=='preview':
                archive=request.files.get('archive')
                if not archive or not archive.filename:raise ValueError('Choose a UAP configuration file.')
                payload=archive.read(64*1024+1)
                if len(payload)>64*1024:raise ValueError('Configuration file must be no larger than 64 KB.')
                document=decode_backup(payload,request.form.get('passphrase',''))
                folder=DATA/'draft-previews';folder.mkdir(mode=0o700,parents=True,exist_ok=True)
                token=secrets.token_hex(20)
                path=folder/('import-'+token+'.backup')
                with path.open('xb') as f:
                    os.chmod(path,0o600);f.write(payload)
                session['config_import']=token
                before=read_config();changed=sum(before.get(k)!=v for k,v in document['settings'].items())
                preview={'changes':changed,'users':len(document.get('users',[])),
                         'encrypted':bool(document.get('contains_users')),'settings':len(document['settings'])}
            elif action=='apply':
                token=session.pop('config_import',None)
                if not token or not re.fullmatch(r'[0-9a-f]{40}',token):raise ValueError('Preview a backup before importing it.')
                path=DATA/'draft-previews'/('import-'+token+'.backup')
                try:payload=path.read_bytes()
                except OSError:raise ValueError('Import preview expired. Select the file again.')
                finally:path.unlink(missing_ok=True)
                document=decode_backup(payload,request.form.get('passphrase',''))
                if not verify_current_admin_password(request.form.get('password','')):
                    raise ValueError('Confirm your current administrator password before applying the import.')
                if request.form.get('acknowledge')!='YES':raise ValueError('Please confirm the import.')
                count=apply_backup(document,users=request.form.get('include_users')=='1')
                notice=f'Imported {len(document["settings"])} settings and added {count} new user accounts. Existing accounts and their passwords were preserved.'
            else:abort(400)
        except (ValueError,OSError) as exc:error=str(exc)
        except (smtplib.SMTPException,TimeoutError,ConnectionError,OSError) as exc:error=delivery.smtp_failure_message(exc,delivery.smtp_settings())
    smtp_config=delivery.smtp_settings()
    smtp_public={k:v for k,v in smtp_config.items() if k!='password'}
    smtp_public['has_password']=bool(smtp_config.get('password'))
    admin_delivery_sections=render_template_string(ADMIN_DELIVERY,csrf=csrf_token(),
                                                    smtp=smtp_public,admin_delivery=delivery.recent_delivery(limit=10),retention_days=delivery.delivery_retention_days(),
                                                    push_contact=delivery.push_contact(),dashboard_links=delivery.dashboard_links(),
                                                    detected_local=delivery.detected_local_url())
    return render_page('''<h1>System Administration</h1>
<p class="note">Administrator-only configuration, backups and future installation tools. Camera and detection settings remain on their existing page.</p>
{% if error %}<div class="notice error" role="alert">{{error}}</div>{% endif %}{% if notice %}<div class="notice">{{notice}}</div>{% endif %}
<details class="panel setting-section" id="settings-backup" {% if preview %}open{% endif %}><summary>Settings export and import</summary><div class="setting-content">
<p class="note"><strong>Settings Only:</strong> All supported Detector Settings (detection thresholds, frame rate, resolution, operating schedule, detector timezone, Day/Night/Custom camera profiles, sunrise/sunset location, storm and retention rules, camera orientation and public sharing settings). <strong>It excludes</strong> observation records, MP4s, photographs, source ZIPs, users, passwords and device-specific network credentials.</p>
<p class="note"><strong>Settings + Users:</strong> Adds account names, roles, password hashes, report schedules and personal timezone/recipient settings. It requires an encrypted backup passphrase. Imported accounts do not automatically opt in to outgoing delivery. Neither export includes live sessions, SMTP app passwords, Cloudflare keys, NPM credentials, Docker data or media.</p>
<form method="post"><input type="hidden" name="csrf" value="{{csrf}}"><input type="hidden" name="action" value="export">
<label>Backup contents<select name="scope"><option value="settings">Settings only (JSON)</option><option value="users">Settings + Users (encrypted)</option></select></label>
<label>Current administrator password (required for Users)<input type="password" name="password" autocomplete="current-password"></label>
<label>Backup passphrase (12+ characters for Users)<input type="password" name="passphrase" autocomplete="new-password" minlength="12"></label>
<button type="submit">Export backup</button></form>
<hr style="border:0;border-top:1px solid var(--edge);margin:24px 0">
<h2>Preview an import</h2><p class="note">Choose a previously exported JSON or encrypted backup. Review changes before applying. Existing user accounts are never overwritten; new accounts can be added from an encrypted backup.</p>
<form method="post" enctype="multipart/form-data"><input type="hidden" name="csrf" value="{{csrf}}"><input type="hidden" name="action" value="preview">
<label>Backup file<input name="archive" type="file" accept=".json,.uapenc" required></label>
<label>Backup passphrase (for encrypted backups)<input name="passphrase" type="password" autocomplete="off"></label>
<button type="submit">Preview import</button></form>
{% if preview %}<div class="notice"><strong>Import preview:</strong> {{preview.settings}} settings, {{preview.changes}} different from current settings; {{preview.users}} user accounts in file.</div>
<form method="post"><input type="hidden" name="csrf" value="{{csrf}}"><input type="hidden" name="action" value="apply">
{% if preview.encrypted %}<label>Backup passphrase<input type="password" name="passphrase" required></label>
<label class="checkline"><input type="checkbox" name="include_users" value="1"> Add missing users from backup (do not overwrite existing users)</label>{% endif %}
<label>Current administrator password<input type="password" name="password" required autocomplete="current-password"></label>
<label class="checkline"><input type="checkbox" name="acknowledge" value="YES" required> Apply imported settings. Camera settings can take effect on the recorder's next configuration refresh.</label>
<button class="danger" type="submit">Apply imported configuration</button></form>{% endif %}</div></details>
{{ admin_delivery_sections|safe }}
<details class="panel setting-section" id="email-dashboard-links"><summary>Notification email links</summary><div class="setting-content">
<p class="note">Set the trusted dashboard addresses used in notification emails. The public HTTPS domain takes priority; otherwise the email uses the local address. A local-only link works on your home network or VPN. Links require normal login and never contain credentials. If you have not configured a local address, the Pi will attempt to detect one.</p>
<form method="post"><input type="hidden" name="csrf" value="{{csrf}}"><input type="hidden" name="action" value="dashboard_links_save">
<label>Local dashboard address <input name="local_url" type="url" placeholder="http://192.168.1.100:8000" value="{{dashboard_links.local}}"></label>
<label>Optional HTTPS domain <input name="public_url" type="url" placeholder="https://camera.example.com" value="{{dashboard_links.public}}"></label>
<p class="note">Detected local URL (if blank): {{detected_local or 'Not available — enter the local address manually'}}. This does not change NPM or Cloudflare settings.</p>
<button type="submit">Save notification links</button></form></div></details>
{{ network_panel|safe }}

<details class="panel setting-section" id="maintenance-admin"><summary>Maintenance and updates</summary><div class="setting-content"><p class="note">Open <a href="{{url_for('system_page')}}#software-updates">System Health → Software updates</a> to check for official releases or request an administrator-password-confirmed update or repair. Updates are never installed automatically. Raspberry Pi OS, Docker and NPM updates are managed separately.</p></div></details>''',title='System Administration',error=error,notice=notice,preview=preview,
                             admin_delivery_sections=admin_delivery_sections,
                             dashboard_links=delivery.dashboard_links(),detected_local=delivery.detected_local_url(),
                             network_panel=render_template_string(NETWORK_PANEL,csrf=csrf_token(),
                                network_status_map={action:network_setup.public_status(action) for action in
                                    ('local','npm','npm_preview','npm_change','ddns_check','tunnel','tunnel_abandon','tunnel_cleanup','tunnel_disable','tunnel_remove','npm_apply','tunnel_apply','wifi_scan','wifi_connect','wifi_radio','ip_change','npm_retire_old')},
                                pi_lan=network_setup.local_ip(),
                                network_interfaces=network_setup.network_interfaces(),
                                wifi_networks=network_setup.public_status('wifi_scan').get('networks',[]),
                                wifi_radio_state=network_setup.wifi_radio_state(),
                                show_network=bool(request.args.get('network')),focus_network=request.args.get('network',''),
                                pending_network=network_setup.pending_change(),
                                managed_tunnel=network_setup.managed_tunnel(),
                                managed_domain={k:v for k,v in network_setup.managed_domain().items() if k in ('mode','hostname','setup_step','npm_host_enabled','previous_hostname','zone','certificate_contact_email','credentials_saved')}))


def verify_current_admin_password(password):
    me=current_user()
    if not me or me['role']!='admin':return False
    with connection() as db:
        row=db.execute('SELECT password_hash FROM users WHERE id=? AND role=? AND enabled=1',(me['id'],'admin')).fetchone()
    return bool(row and check_password_hash(row['password_hash'],password or ''))


@app.route('/system/delivery-history')
def delivery_history():
    if not is_admin():abort(403)
    channel=request.args.get('channel','all')
    if channel not in ('all','email','push'):channel='all'
    state=request.args.get('state','all')
    if state not in ('all','sent','failed','retry','pending','sending'):state='all'
    try:page=max(1,int(request.args.get('page','1')))
    except (TypeError,ValueError):page=1
    data=delivery.delivery_history(page,channel,state)
    return render_page('''<h1>Delivery history</h1><p><a href="{{url_for('system_admin')}}#delivery-diagnostics">← System Administration</a></p>
    <p class="note">Technical SMTP/Web Push attempts only. Routine completed delivery metadata is retained for 90 days; actual notifications are separate.</p>
    <form method="get" class="row"><label>Channel<select name="channel">{% for c in ['all','email','push'] %}<option value="{{c}}" {% if c==channel %}selected{% endif %}>{{c|title}}</option>{% endfor %}</select></label>
    <label>State<select name="state">{% for st in ['all','sent','failed','retry','pending','sending'] %}<option value="{{st}}" {% if st==state %}selected{% endif %}>{{st|title}}</option>{% endfor %}</select></label><button type="submit">Filter</button></form>
    <section class="panel"><p class="note">{{data.total}} matching · page {{data.page}} of {{data.pages}} · 20 per page</p>
    <div style="overflow-x:auto"><table><thead><tr><th>User</th><th>Notice</th><th>Method</th><th>State</th><th>Attempts</th><th>Updated</th><th>Action</th></tr></thead><tbody>
    {% for d in data.rows %}<tr><td>{{d.username}}</td><td>{{d.title}}{% if d.error %}<p class="note">{{d.error}}</p>{% endif %}</td><td>{{d.channel|title}}</td><td>{{d.state|title}}</td><td>{{d.attempts}}</td><td>{{d.changed_utc|localdt}}</td><td>{% if d.state=='failed' %}<form method="post" action="{{url_for('system_admin')}}"><input type="hidden" name="csrf" value="{{csrf}}"><input type="hidden" name="action" value="retry_delivery"><input type="hidden" name="delivery_id" value="{{d.id}}"><button type="submit">Retry</button></form>{% endif %}</td></tr>{% else %}<tr><td colspan="7">No matching delivery attempts.</td></tr>{% endfor %}</tbody></table></div>
    <div class="between" style="margin-top:12px">{% if data.page>1 %}<a class="button" href="{{url_for('delivery_history',page=data.page-1,channel=channel,state=state)}}">← Previous</a>{% endif %}
    {% if data.page<data.pages %}<a class="button" href="{{url_for('delivery_history',page=data.page+1,channel=channel,state=state)}}">Next →</a>{% endif %}</div></section>''',title='Delivery history',data=data,channel=channel,state=state)


@app.route('/system')
def system_page():
    if not is_admin(): abort(403)
    h = system_health()
    from job_diagnostics import recent_jobs
    job_health=recent_jobs()
    software_info=software_latest_info()
    try:
        from service_repair import inspect as inspect_service_units
        service_units=inspect_service_units()
        service_drift={k:v for k,v in service_units.items() if v in ('missing','modified')}
        service_warning=any(v.startswith('symlink') for v in service_units.values())
        service_error=''
    except (OSError,RuntimeError,ValueError) as exc:
        service_drift={}
        service_warning=True
        service_error='Moon Cheese service definitions could not be inspected. Run service_repair.py --check from PuTTY.'
    return render_page('''<h1>System health</h1><p class="muted">Device diagnostics and administrator maintenance. Health readings refresh when you reload this page.</p>
    {% if health.disk_warning %}<div class="notice" role="alert"><strong>Low free disk space.</strong> Review recordings and storage settings before the SD card fills up.</div>{% endif %}
    <div class="grid"><div class="panel"><div class="sub">Detector heartbeat</div><div class="value">{{ health.detector.state|title }}</div><p class="note">{{ health.detector.message }}</p><p class="note">Last update: {{ health.detector.age_seconds if health.detector.age_seconds is not none else 'Unavailable' }} seconds ago</p></div>
    <div class="panel"><div class="sub">Disk free</div><div class="value">{{ health.disk_free_gb }} GB</div><p class="note">{{ health.disk_free_percent }}% free of {{ health.disk_total_gb }} GB</p></div>
    <div class="panel"><div class="sub">RAM available</div><div class="value">{{ (health.memory.available_mb|string + ' MB') if health.memory else 'Unavailable' }}</div><p class="note">{% if health.memory %}{{ health.memory.used_mb }} MB used of {{ health.memory.total_mb }} MB{% else %}No memory reading{% endif %}</p></div></div>
    <div class="cols"><section class="panel"><h2>Hardware</h2><p><strong>CPU temperature:</strong> {{ (health.cpu_temp_c|string + ' °C') if health.cpu_temp_c is not none else 'Unavailable' }}</p><p><strong>System uptime:</strong> {{ (health.uptime_hours|string + ' hours') if health.uptime_hours is not none else 'Unavailable' }}</p><p><strong>CPU load average:</strong> {{ health.load_average|join(' / ') if health.load_average else 'Unavailable' }} (1, 5 and 15 minutes)</p><p><strong>Latest camera snapshot:</strong> {{ (health.snapshot_age_seconds|string + ' seconds ago') if health.snapshot_age_seconds is not none else 'Not captured yet' }}</p></section>
    <section class="panel"><h2>Understanding the health page</h2><p>Web access can work even if the camera service has stopped. A stale detector heartbeat or old snapshot deserves investigation.</p><p>Temperatures, loads and free storage are indicators, not guarantees of reliable recording.</p><p>For recording protection and cleanup, see <a href="{{ url_for('settings') }}">Settings</a> and the <a href="{{ url_for('help_page') }}">Help guide</a>.</p></section></div>
    <section class="panel"><h2>Event-storm history</h2><p class="note">Recent cooldowns and recoveries are logged for administrators.</p>
    <table><tr><th>Started (local)</th><th>Ended (local)</th><th>State</th></tr>
    {% for e in storms %}<tr><td>{{e.start_utc|localdt}}</td><td>{{e.end_utc|localdt if e.end_utc else '—'}}</td><td>{{e.state}}</td></tr>{% else %}<tr><td colspan="3">No storm cooldowns recorded yet.</td></tr>{% endfor %}</table></section>
    <section class="panel"><h2>Scheduled job health</h2><p class="note">Read-only progress checks. A warning means a job has stopped reporting updates for longer than expected; it does not automatically cancel the camera job. Partial files remain protected.</p>
    <table><thead><tr><th>Job</th><th>Status</th><th>Last update</th><th>Progress</th></tr></thead><tbody>
    {% for job in job_health %}<tr><td><a href="{{url_for('job_detail',job_id=job.id)}}">#{{job.id}} {{job.title}}</a></td><td>{{job.status|title}}{% if job.suspect %}<span class="pill flagged"> · Investigate</span>{% endif %}</td><td>{{job.age_minutes}} min ago</td><td>{{job.phase or job.error or '—'}}</td></tr>
    {% else %}<tr><td colspan="4">No scheduled jobs recorded yet.</td></tr>{% endfor %}</tbody></table></section>
    <section class="panel" id="software-updates"><h2>Software updates</h2>
      <div class="row" style="gap:32px;margin:10px 0"><div><div class="note">Installed version</div><strong>v{{software.installed}}</strong></div>
      <div><div class="note">Latest {{'private testing' if software.channel == 'private-prerelease' else 'stable'}} release</div><strong>{{('v'+software.latest) if software.latest else 'Not checked / unavailable'}}</strong></div></div>
      <p class="note" id="software-update-result" role="status">{{software.message or 'Use Check for updates to contact the official GitHub repository.'}}</p>
      {% if software.worker and software.worker.get('state') %}<p class="note" id="software-worker-result" role="status">{{software.worker.action|title}} — {{software.worker.state|title}}: {{software.worker.message}}</p>{% else %}<p class="note" id="software-worker-result" role="status" hidden></p>{% endif %}
      {% if software_error %}<p class="error" id="software-auth-error" role="alert">{{software_error}}</p>{% endif %}
      <form method="post" action="{{url_for('software_action')}}" id="software-update-form" autocomplete="off">
        <input type="hidden" name="csrf" value="{{csrf}}">
        <label class="software-password">Confirm your administrator password for Update, Repair or Service repair
          <input id="software-admin-password" type="password" name="password" autocomplete="off" placeholder="Current administrator password">
        </label>
        <div class="row" style="gap:8px">
          <button name="action" value="check" type="submit">Check for updates</button>
          <button name="action" value="update" type="submit" {% if not (software.available and software.has_assets) %}disabled title="No installable newer release in the selected channel"{% endif %}>Update now</button>
          <button name="action" value="repair" type="submit" {% if not software.repair_ready %}disabled title="Current version has no verified GitHub release"{% endif %}>Repair current version</button>
          <button name="action" value="services" type="submit" {% if not service_drift or service_warning %}disabled{% endif %} title="Back up and restore modified or missing Moon Cheese-owned service files; no service restarts">Repair services</button>
        </div>
      </form>
      <details class="service-inspection"><summary>Service definitions: {% if service_error %}inspection unavailable{% elif service_warning %}manual inspection required{% elif service_drift %}{{service_drift|length}} difference(s) detected{% else %}matching official files{% endif %}</summary>
        {% if service_error %}<p class="note">{{service_error}}</p>{% endif %}
        <p class="note">Repair services requires your administrator password. It restores only missing or changed Moon Cheese systemd unit files, backs them up first, reloads systemd, and never restarts a running camera or another application. Optional unused Cloudflare units are not treated as faults.</p>
        {% if service_drift %}<ul>{% for name, state in service_drift.items() %}<li><code>{{name}}</code> — {{state}}</li>{% endfor %}</ul>{% endif %}
        {% if service_warning %}<p class="note">Symbolic links or unavailable service templates must be checked manually before repair.</p>{% endif %}
      </details>
      <p class="note">Updates and repair use the complete versioned release installer, preserving configuration, user accounts, recordings and credentials. Camera recordings must finish first. The normal channel offers stable releases. Private prerelease testing can be temporarily enabled by an administrator on the device; no automatic installation occurs.</p>
      <p class="note"><a href="https://github.com/DrRavenholm/Moon-Cheese-UAP-Detector/releases" rel="noopener noreferrer" target="_blank">View official release notes on GitHub</a></p>
      <script src="{{url_for('software_update_js')}}" defer></script>
    </section>
    <section class="panel"><h2>System power</h2><p class="note">Reboot restarts the Raspberry Pi. Shutdown powers it down and requires physical power-on afterwards.</p>
    <form method="post" action="{{url_for('system_power')}}"><input type="hidden" name="csrf" value="{{csrf}}">
    <label>Confirm your administrator password <input type="password" name="password" required autocomplete="current-password"></label>
    <label class="checkline"><input type="checkbox" name="acknowledge" value="YES" required> I understand that this stops recording and may disconnect the web interface.</label>
    <div class="row"><button name="action" value="reboot" type="submit">Reboot Pi</button>
    <button class="danger" name="action" value="shutdown" type="submit">Shutdown Pi</button></div></form></section>''', title='System health', health=h,storms=storm_recent(),job_health=job_health, app_version=APP_VERSION,software=software_info,
                       service_drift=service_drift, service_warning=service_warning, service_error=service_error,
                       software_error={'missing':'Enter your current administrator password for the requested maintenance action.',
                                       'incorrect':'Incorrect administrator password. No maintenance action was started.',
                                       'services':'Service repair is unavailable or not needed; check the service definitions below.'}.get(request.args.get('software_error', ''), ''))


@app.route('/system/software/action',methods=['POST'])
def software_action():
    if not is_admin():abort(403)
    check_csrf()
    action=request.form.get('action','')
    if action=='check':
        software_latest_info(force=True)
    elif action in ('update','repair','services'):
        password=request.form.get('password','')
        if not password:
            return redirect(url_for('system_page',software_error='missing')+'#software-updates',code=303)
        if not verify_current_admin_password(password):
            return redirect(url_for('system_page',software_error='incorrect')+'#software-updates',code=303)
        try:
            if action=='services':
                from software_updates import enqueue_service_repair
                enqueue_service_repair(current_user()['username'])
            else:
                software_enqueue(action,current_user()['username'])
        except (ValueError, OSError, RuntimeError) as exc:
            from software_updates import CHECK, _write, latest_info
            # Use the same inline status area; do not expose worker traces.
            # Do not overwrite a valid cached latest version when reporting errors.
            info=latest_info()
            info.pop('worker',None)
            info.pop('installed',None)
            info['message']=str(exc)[:350]
            _write(CHECK,info)
    else:abort(400)
    return redirect(url_for('system_page')+'#software-updates')


@app.route('/system/software/status')
def software_status():
    if not is_admin():abort(403)
    from software_updates import STATUS, _read
    return jsonify(_read(STATUS))


@app.route('/system/software/updates.js')
def software_update_js():
    if not is_admin():abort(403)
    return send_file(Path(__file__).parent/'software_update_ui.js',mimetype='application/javascript')


@app.route('/system/power',methods=['POST'])
def system_power():
    if not is_admin():abort(403)
    check_csrf()
    action=request.form.get('action')
    if action not in ('reboot','shutdown') or request.form.get('acknowledge')!='YES':abort(400)
    me=current_user()
    with connection() as db:
        row=db.execute('SELECT password_hash FROM users WHERE id=? AND role=? AND enabled=1',
                       (me['id'],'admin')).fetchone()
    if not row or not check_password_hash(row['password_hash'],request.form.get('password','')):
        return render_page('<h1>Authentication failed</h1><p>The power request was not submitted.</p><a class="button" href="{{url_for(\'system_page\')}}">Return to System Health</a>',title='Power request refused'),403
    root=DATA/'power-requests'
    root.mkdir(mode=0o700,parents=True,exist_ok=True)
    if list(root.glob('*.json')):abort(409,description='A power request is already pending.')
    item=secrets.token_hex(16)
    tmp=root/(item+'.pending')
    final=root/(item+'.json')
    payload={'action':action,'admin':me['username'],'utc':now_iso()}
    with tmp.open('x') as stream:
        os.chmod(tmp,0o600)
        json.dump(payload,stream)
        stream.flush();os.fsync(stream.fileno())
    os.replace(tmp,final)
    return render_page('<h1>Power request received</h1><p>The Raspberry Pi will {{action}} after the camera recording service stops safely.</p><p class="note">If shutdown was selected, physical power-on is required to restore service.</p>',
                       title='Power request',action=action)


@app.route('/assets/jobs-ui.js')
def jobs_js():
    if not logged_in(): abort(403)
    return Response((Path(__file__).parent/'jobs_ui.js').read_text(),mimetype='application/javascript')


@app.route('/observations/timelapse/estimate')
def timelapse_estimate():
    """Read-only preview; scheduling performs the authoritative space check."""
    if not is_admin():abort(403)
    try:
        minutes=int(request.args.get('duration_minutes','60'))
        interval=int(request.args.get('interval_seconds','15'))
        if minutes<1 or minutes>480 or interval<5 or interval>3600:raise ValueError()
    except (ValueError,TypeError):return jsonify(error='Enter a duration from 1 to 480 minutes and a valid capture interval.'),400
    from storage_estimator import estimate_space
    try:plan=estimate_space(frames=(minutes*60+interval-1)//interval,kind='timelapse')
    except OSError:return jsonify(error='Disk space could not be read; scheduling may not be available.'),503
    return jsonify({**{name:plan[name] for name in ('bytes','reserve','required','available','bytes_per_frame','samples','fits')},
                    'frames':(minutes*60+interval-1)//interval})


@app.route('/observations/<kind>', methods=['GET','POST'])
def jobs_list(kind):
    if kind not in oj.KINDS: abort(404)
    user=current_user()
    if not user:return redirect(url_for('login'))
    error=''
    form_values=request.form.to_dict() if request.method=='POST' else {}
    if request.method=='POST':
        if not is_admin():abort(403)
        check_csrf()
        try:
            job_id=oj.create(request.form,user['id'])
            return redirect(url_for('job_detail',job_id=job_id))
        except ValueError as exc:error=str(exc)
    query=request.args.get('q','').strip()[:120]
    selected_status=request.args.get('status','all')
    if selected_status not in ('all','queued','capturing','rendering','archiving','finalising','complete','failed','cancelled','interrupted','missed'):selected_status='all'
    visibility=request.args.get('visibility','all')
    if visibility not in ('all','public','private'):visibility='all'
    pinned_only=request.args.get('pinned')=='1'
    clause=['kind=?'];args=[kind]
    if query:
        clause.append('(title LIKE ? OR note LIKE ?)');args+=['%'+query+'%','%'+query+'%']
    if selected_status!='all':clause.append('status=?');args.append(selected_status)
    if pinned_only:clause.append('pinned=1')
    if visibility!='all':clause.append('public=?');args.append(1 if visibility=='public' else 0)
    where=' AND '.join(clause)
    try:page=max(1,int(request.args.get('page',1)))
    except ValueError:page=1
    per_page=12 if kind=='timelapse' else 20
    with connection() as db:
        total=db.execute('SELECT COUNT(*) FROM observation_jobs WHERE '+where,args).fetchone()[0]
        pages=max(1,(total+per_page-1)//per_page);page=min(page,pages)
        rows=[dict(r) for r in db.execute('SELECT * FROM observation_jobs WHERE '+where+' ORDER BY id DESC LIMIT ? OFFSET ?', (*args,per_page,(page-1)*per_page))]
    tzname=read_config().get('schedule_timezone','Europe/London')
    from zoneinfo import ZoneInfo
    try:tz=ZoneInfo(tzname)
    except Exception:tzname='Europe/London';tz=ZoneInfo(tzname)
    suggested_start=(datetime.now(tz)+timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
    return render_page(JOBS_LIST,title='Scheduled Video' if kind=='scheduled_video' else 'Time-lapse Studio',
                       heading='Scheduled Video' if kind=='scheduled_video' else 'Time-lapse Studio',
                       error=error,kind=kind,rows=rows,total=total,pages=pages,page=page,
                       tzname=tzname,suggested_start=suggested_start,form_values=form_values,query=query,selected_status=selected_status,visibility=visibility,pinned_only=pinned_only)


@app.route('/observations/job/<int:job_id>',methods=['GET','POST'])
def job_detail(job_id):
    if not logged_in():return redirect(url_for('login'))
    job=oj.item(job_id)
    if job is None:abort(404)
    if request.method=='POST':
        if not is_admin():abort(403)
        check_csrf()
        try:
            oj.set_meta(job_id, request.form.get('title'),request.form.get('note'),
                        request.form.get('pinned')=='1',request.form.get('public')=='1',
                        request.form.get('public_note')=='1')
        except ValueError as exc:abort(400,str(exc))
        return redirect(url_for('job_detail',job_id=job_id))
    segments=oj.files(job_id)
    try:part=max(1,min(len(segments),int(request.args.get('part',1)))) if segments else 1
    except ValueError:part=1
    filename=(segments[part-1].name if segments else 'timelapse.mp4') if job['kind']=='scheduled_video' else 'timelapse.mp4'
    media_url=url_for('job_media',job_id=job_id,filename=filename) if oj.download(job_id,filename) else ''
    return render_page(JOB_DETAIL,title=job['title'],job=job,segments=segments,media_url=media_url,
                       zip_ready=bool(oj.download(job_id,'source-frames.zip')),video_fps=job['output_fps'] if job['kind']=='timelapse' else read_config().get('fps',15))


@app.route('/observations/job/<int:job_id>/cancel',methods=['POST'])
def job_cancel(job_id):
    if not is_admin(): abort(403)
    check_csrf()
    try:oj.cancel(job_id)
    except ValueError as exc:abort(400,str(exc))
    return redirect(url_for('job_detail',job_id=job_id))


@app.route('/observations/job/<int:job_id>/thumb.jpg')
def job_thumb(job_id):
    if not logged_in():return redirect(url_for('login'))
    if not oj.item(job_id):abort(404)
    path=oj.download(job_id,'thumbnail.jpg')
    if not path:abort(404)
    return send_file(path,mimetype='image/jpeg',conditional=True)


@app.route('/observations/job/<int:job_id>/media/<filename>')
def job_media(job_id,filename):
    if not logged_in():return redirect(url_for('login'))
    path=oj.download(job_id,filename)
    if not oj.item(job_id) or not path:abort(404)
    if filename=='source-frames.zip' and not is_admin():abort(403)
    job=oj.item(job_id)
    download=(request.args.get('download')=='1' or filename.endswith('.zip'))
    return send_file(path,conditional=True,as_attachment=download,
                     download_name=job_filename(job,filename) if download else None)


@app.route('/storage/observations/<kind>',methods=['GET','POST'])
def job_storage(kind):
    """Legacy storage links remain valid; the management interface is now unified."""
    if not is_admin():abort(403)
    if kind not in oj.KINDS:abort(404)
    if request.method=='POST':
        check_csrf()
        try:job_id=int(request.form.get('job_id',''))
        except ValueError:abort(400)
        action=request.form.get('action')
        if action not in ('delete','delete_sources'):abort(400)
        selected=oj.item(job_id)
        if not selected or selected['kind']!=kind:abort(404)
        # Backward compatible with older bookmarks/forms, retains protection checks.
        oj.delete(job_id,source_only=action=='delete_sources')
    return redirect(url_for('storage_page',tab=kind))


@app.route('/public/observation/<int:job_id>')
def public_job_detail(job_id):
    if not public_allowed():abort(404)
    j=oj.item(job_id)
    if not j or j['status']!='complete' or not j['public']:abort(404)
    if j['kind']!='scheduled_video':return redirect(url_for('public_page',media='timelapses'))
    segments=oj.files(job_id)
    try:page=max(1,int(request.args.get('page',1)))
    except ValueError:page=1
    pages=max(1,(len(segments)+4)//5);page=min(page,pages)
    return render_page('''<p><a href="{{url_for('public_page',media='scheduled')}}#shared-media">← Scheduled Videos</a></p><h1>{{job.title}}</h1>
    <p class="note">{{job.start_utc|localdt}} · Part {{page}} of {{pages}} · {{segments|length}} segments</p>
    <section class="panel">{% for item in segments[(page-1)*5:page*5] %}<h2>Part {{(page-1)*5+loop.index}}</h2>
    <video controls controlslist="nodownload" preload="none" playsinline style="display:block;width:100%;aspect-ratio:16/9;background:#000;margin-bottom:14px" src="{{url_for('public_job_media',job_id=job.id,filename=item.name)}}"></video>{% endfor %}
    <div class="row">{% if page>1 %}<a class="button" href="{{url_for('public_job_detail',job_id=job.id,page=page-1)}}">← Previous</a>{% endif %}
    {% if page<pages %}<a class="button" href="{{url_for('public_job_detail',job_id=job.id,page=page+1)}}">Next →</a>{% endif %}</div>
    {% if job.public_note and job.note %}<aside class="public-notes"><h2>Observation notes</h2><p style="white-space:pre-wrap">{{job.note}}</p></aside>{% endif %}</section>''',
      title= j['title'],public_view=True,job=j,segments=segments,page=page,pages=pages)


@app.route('/public/observation/<int:job_id>/media/<filename>')
def public_job_media(job_id,filename):
    if not public_allowed():abort(404)
    j=oj.item(job_id)
    if not j or j['status']!='complete' or not j['public']:abort(404)
    if filename=='source-frames.zip' or (filename!='timelapse.mp4' and not filename.startswith('segment-')):abort(404)
    path=oj.download(job_id,filename)
    if not path:abort(404)
    return send_file(path,conditional=True,mimetype='video/mp4')


@app.route('/public/observation/<int:job_id>/thumb.jpg')
def public_job_thumb(job_id):
    if not public_allowed():abort(404)
    j=oj.item(job_id)
    if not j or j['status']!='complete' or not j['public']:abort(404)
    path=oj.download(job_id,'thumbnail.jpg')
    if not path:abort(404)
    return send_file(path,mimetype='image/jpeg',conditional=True)


@app.route('/history')
def history():
    if not logged_in():
        return redirect(url_for('login'))
    return render_page(HISTORY, title='Version history', releases=release_timeline())


@app.route('/app-icons/<name>')
def moon_icon(name):
    if name not in {'moon-cheese-32.png','moon-cheese-48.png','moon-cheese-180.png','moon-cheese-192.png','moon-cheese-512.png'}:
        abort(404)
    return send_file(Path(__file__).parent / name, mimetype='image/png')


@app.route('/manifest.webmanifest')
def moon_manifest():
    response=jsonify(name='Moon Cheese UAP Detector',short_name='Moon Cheese',start_url='/',
                    scope='/',display='standalone',background_color='#091423',theme_color='#0c1929',
                    icons=[{'src':url_for('moon_icon',name=f'moon-cheese-{size}.png'),
                            'sizes':f'{size}x{size}','type':'image/png','purpose':'any'}
                           for size in (192,512)])
    response.mimetype='application/manifest+json'
    return response


ABOUT_ICON_NAMES = frozenset({
    'link','users','music','heart','globe','file-lines','cart-shopping',
    'github','youtube','twitch','discord','tiktok','bluesky','instagram',
    'facebook','threads','spotify','apple'
})

@app.route('/about/icons/<name>.svg')
def about_icon(name):
    if name not in ABOUT_ICON_NAMES:
        abort(404)
    return send_file(Path(__file__).with_name('about-icon-'+name+'.svg'),
                     mimetype='image/svg+xml',conditional=True)


@app.route('/about')
def about_moon_cheese():
    return render_page(ABOUT_MOON_CHEESE,title='About Moon Cheese')


ABOUT_MOON_CHEESE = '''<h1>ⓘ &nbsp;About Moon Cheese</h1>
<section class="panel about-hero">
  <div class="about-hero-art"><img src="{{url_for('moon_icon',name='moon-cheese-512.png')}}" alt="Moon Cheese UAP Detector official artwork" width="200" height="200"></div>
  <div class="about-hero-text"><h2>What is Moon Cheese?</h2>
  <p>Moon Cheese UAP Detector is an independent, camera-based sky-monitoring and observation system designed to help enthusiasts and researchers record, review and organise unusual activity in the sky.</p>
  <p>It combines live monitoring, motion/light detection, still capture, scheduled recording, time-lapse creation, event review and optional remote-access tools into one self-hosted system for Raspberry Pi.</p>
  <p class="note">A detection is a starting point for investigation, not proof that an unusual aerial object has been identified.</p></div>
</section>
<section class="panel about-biography"><h2>About Me</h2>
<p>I'm Dr Ravenholm, the creator of Moon Cheese UAP Detector and the person behind <a href="https://transparent-aluminium.net/" target="_blank" rel="noopener noreferrer">Transparent-Aluminium.net</a>.</p>
<p>My background spans IT, computing, telecommunications, networking, photography and software development. Outside of that, I also enjoy music, live streaming, content creation and exploring new technologies.</p>
<p>I've always been interested in astronomy, photography and the unexplained. Moon Cheese brings those interests together in a project that makes sky monitoring, recording and investigation more accessible to enthusiasts and independent researchers.</p>
<p>My aim is to provide practical tools that help people capture and examine unusual activity in the sky, while allowing the evidence to speak for itself.</p>
<p>Moon Cheese is an ongoing project, and I hope it continues to grow with new features, hardware support and contributions from the community.</p>
</section>
<div class="about-card-grid">
  <section class="panel about-card">
  <h2 class="about-card-title"><span class="about-heading-icon"><img src="{{url_for('about_icon',name='link')}}" alt="" aria-hidden="true" width="19" height="19"></span>Creator &amp; Project</h2>
    <a class="about-link" href="https://transparent-aluminium.net/" target="_blank" rel="noopener noreferrer"><span class="about-symbol about-symbol-globe"><img src="{{url_for('about_icon',name='globe')}}" alt="" aria-hidden="true" width="19" height="19"></span><span>Transparent-Aluminium.net</span></a>
    <a class="about-link" href="https://transparent-aluminium.net/blog/" target="_blank" rel="noopener noreferrer"><span class="about-symbol about-symbol-file-lines"><img src="{{url_for('about_icon',name='file-lines')}}" alt="" aria-hidden="true" width="19" height="19"></span><span>Blog</span></a>
    <a class="about-link" href="https://github.com/DrRavenholm/Moon-Cheese-UAP-Detector" target="_blank" rel="noopener noreferrer"><span class="about-symbol about-symbol-github"><img src="{{url_for('about_icon',name='github')}}" alt="" aria-hidden="true" width="19" height="19"></span><span>GitHub — Moon Cheese UAP Detector</span></a>
  </section>
  <section class="panel about-card">
  <h2 class="about-card-title"><span class="about-heading-icon"><img src="{{url_for('about_icon',name='users')}}" alt="" aria-hidden="true" width="19" height="19"></span>Socials</h2>
  <div class="about-social-grid"><div>
    <a class="about-link" href="https://www.youtube.com/@Dr_Ravenholm" target="_blank" rel="noopener noreferrer"><span class="about-symbol about-symbol-youtube"><img src="{{url_for('about_icon',name='youtube')}}" alt="" aria-hidden="true" width="19" height="19"></span><span>YouTube</span></a>
    <a class="about-link" href="https://www.twitch.tv/dr_ravenholm" target="_blank" rel="noopener noreferrer"><span class="about-symbol about-symbol-twitch"><img src="{{url_for('about_icon',name='twitch')}}" alt="" aria-hidden="true" width="19" height="19"></span><span>Twitch</span></a>
    <a class="about-link" href="https://discord.gg/yTj2ucM" target="_blank" rel="noopener noreferrer"><span class="about-symbol about-symbol-discord"><img src="{{url_for('about_icon',name='discord')}}" alt="" aria-hidden="true" width="19" height="19"></span><span>Discord</span></a>
    <a class="about-link" href="https://www.tiktok.com/@dr_ravenholm" target="_blank" rel="noopener noreferrer"><span class="about-symbol about-symbol-tiktok"><img src="{{url_for('about_icon',name='tiktok')}}" alt="" aria-hidden="true" width="19" height="19"></span><span>TikTok</span></a>
  </div><div>
    <a class="about-link" href="https://bsky.app/profile/dr-ravenholm.bsky.social" target="_blank" rel="noopener noreferrer"><span class="about-symbol about-symbol-bluesky"><img src="{{url_for('about_icon',name='bluesky')}}" alt="" aria-hidden="true" width="19" height="19"></span><span>Bluesky</span></a>
    <a class="about-link" href="https://www.instagram.com/dr_ravenholm/" target="_blank" rel="noopener noreferrer"><span class="about-symbol about-symbol-instagram"><img src="{{url_for('about_icon',name='instagram')}}" alt="" aria-hidden="true" width="19" height="19"></span><span>Instagram</span></a>
    <a class="about-link" href="https://www.facebook.com/Dr.Ravenholm/" target="_blank" rel="noopener noreferrer"><span class="about-symbol about-symbol-facebook"><img src="{{url_for('about_icon',name='facebook')}}" alt="" aria-hidden="true" width="19" height="19"></span><span>Facebook</span></a>
    <a class="about-link" href="https://www.threads.com/@dr_ravenholm" target="_blank" rel="noopener noreferrer"><span class="about-symbol about-symbol-threads"><img src="{{url_for('about_icon',name='threads')}}" alt="" aria-hidden="true" width="19" height="19"></span><span>Threads</span></a>
  </div></div></section>
  <section class="panel about-card about-media-card">
    <div><h2 class="about-card-title"><span class="about-heading-icon"><img src="{{url_for('about_icon',name='music')}}" alt="" aria-hidden="true" width="19" height="19"></span>Music</h2>
      <div class="about-music-grid">
    <a class="about-link" href="https://open.spotify.com/artist/3ASlECL9rplcDrltdl4tlv" target="_blank" rel="noopener noreferrer"><span class="about-symbol about-symbol-spotify"><img src="{{url_for('about_icon',name='spotify')}}" alt="" aria-hidden="true" width="19" height="19"></span><span>Spotify</span></a>
    <a class="about-link" href="https://music.apple.com/gb/artist/dr-ravenholm/6796683688" target="_blank" rel="noopener noreferrer"><span class="about-symbol about-symbol-apple"><img src="{{url_for('about_icon',name='apple')}}" alt="" aria-hidden="true" width="19" height="19"></span><span>Apple Music</span></a>
      </div>
    </div>
    <div class="about-support"><h2 class="about-card-title"><span class="about-heading-icon"><img src="{{url_for('about_icon',name='heart')}}" alt="" aria-hidden="true" width="19" height="19"></span>Support</h2>
    <a class="about-link" href="https://dr-ravenholm-shop.fourthwall.com" target="_blank" rel="noopener noreferrer"><span class="about-symbol about-symbol-cart-shopping"><img src="{{url_for('about_icon',name='cart-shopping')}}" alt="" aria-hidden="true" width="19" height="19"></span><span>Shop</span></a>
    <a class="about-link" href="https://streamlabs.com/dr_ravenholm/tip" target="_blank" rel="noopener noreferrer"><span class="about-symbol about-symbol-heart"><img src="{{url_for('about_icon',name='heart')}}" alt="" aria-hidden="true" width="19" height="19"></span><span>Donations</span></a>
    </div>
  </section>
</div>'''
@app.route('/healthz')
def healthz():
    return {'web': 'ok'}


if __name__ == '__main__':
    ensure_db()
    app.run(host='127.0.0.1', port=8000)
