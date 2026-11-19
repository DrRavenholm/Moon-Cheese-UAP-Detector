"""Offline-first astronomical dataset registry and bounded, administrator-controlled downloads.

No data or public API key ships in the installer. Files belong under the persistent
/var/lib/uap-detector tree and are never modified during application upgrades.
"""
import csv
import hashlib
import io
import zipfile
import json
import os
import secrets
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
from common import DATA, read_config

ROOT = DATA / 'sky-map-data'
REQUESTS = ROOT / 'requests'
MANIFEST = ROOT / 'manifest.json'
CONFIG = ROOT / 'preferences.json'
ALLOW_HOSTS = {'raw.githubusercontent.com', 'naif.jpl.nasa.gov', 'celestrak.org', 'www.celestrak.org', 'downloads.sourceforge.net', 'sourceforge.net'}


def approved_host(host):
    return host in ALLOW_HOSTS or bool(host and host.endswith('.dl.sourceforge.net'))
RAW = 'https://raw.githubusercontent.com/ofrohn/d3-celestial/master/data/'
SOURCES = {
    'stars': {'label':'Stars and star names','files':{'stars.8.json': RAW+'stars.8.json', 'starnames.json':RAW+'starnames.json'}, 'max':18_000_000},
    'constellations': {'label':'Constellations','files':{n:RAW+n for n in ('constellations.lines.json','constellations.json','constellations.bounds.json')}, 'max':8_000_000},
    'planets': {'label':'Sun, Moon and planets','files':{'de440s.bsp':'https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440s.bsp'}, 'max':42_000_000},
    'satellites': {'label':'Satellites and orbital objects','files':{'active.csv':'https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=CSV'}, 'max':20_000_000},
    'world': {'label':'World map','files':{'world.geojson':'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_land.geojson'}, 'max':5_000_000},
    'deep_sky': {'label':'Bright deep-sky objects','files':{n:RAW+n for n in ('messier.json','dsos.bright.json')}, 'max':10_000_000},
    'plate_solver': {'label':'Plate solving: W08 wide-field star index','files':{'w08.001':'https://downloads.sourceforge.net/project/astap-program/star_databases/w08_star_database_mag08_astap.zip'}, 'max':5_000_000},
}


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o750)
    tmp = path.with_name('.'+path.name+'.'+secrets.token_hex(8))
    try:
        with tmp.open('x', encoding='utf-8') as f:
            os.chmod(tmp, 0o600)
            json.dump(value,f,ensure_ascii=False,indent=2)
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    finally: tmp.unlink(missing_ok=True)


def _read_json(path, fallback):
    try:
        obj=json.loads(path.read_text(encoding='utf-8'))
        return obj if isinstance(obj,dict) else fallback
    except (OSError,ValueError):return fallback


def prefs():
    result={'satellite_hour':3,'satellite_minute':0,'auto_satellites':True}
    result.update(_read_json(CONFIG,{}))
    return result


def save_prefs(hour, minute, enabled):
    if not isinstance(hour,int) or not 0<=hour<24 or not isinstance(minute,int) or not 0<=minute<60:
        raise ValueError('Choose a valid satellite download time.')
    _write_json(CONFIG,{'satellite_hour':hour,'satellite_minute':minute,'auto_satellites':bool(enabled)})


def manifest():return _read_json(MANIFEST,{})


def dataset_status():
    m=manifest()
    results={}
    for kind,item in SOURCES.items():
        meta=m.get(kind,{})
        filenames=list(item['files'])
        installed=bool(filenames) and all((ROOT/kind/name).is_file() for name in filenames)
        results[kind]={**meta,'label':item['label'],'installed':installed,
                       'files':filenames, 'source':list(item['files'].values()),
                       'bytes':sum((ROOT/kind/n).stat().st_size for n in filenames if (ROOT/kind/n).is_file())}
    return results


def _verify(kind, name, data):
    if kind=='plate_solver':
        if name!='w08.001' or len(data)!=4+41246*12 or int.from_bytes(data[:4],'little')!=41246:
            raise ValueError('ASTAP W08 index is incomplete or invalid.')
    elif kind=='planets':
        if len(data)<20_000_000 or not data.startswith(b'DAF/SPK '):
            raise ValueError('JPL ephemeris file has an invalid SPK header or size.')
    elif kind=='satellites':
        reader=csv.DictReader(io.StringIO(data.decode('utf-8-sig')))
        if not reader.fieldnames or not {'NORAD_CAT_ID','EPOCH','MEAN_MOTION','ECCENTRICITY','INCLINATION','RA_OF_ASC_NODE','ARG_OF_PERICENTER','MEAN_ANOMALY'}.issubset(reader.fieldnames):
            raise ValueError('CelesTrak CSV is missing required OMM columns.')
        if sum(1 for _ in reader)<100:
            raise ValueError('Satellite orbital catalogue is unexpectedly empty.')
    else:
        obj=json.loads(data.decode('utf-8-sig'))
        if not isinstance(obj,(dict,list)) or not obj:
            raise ValueError('Astronomical catalogue is missing or malformed.')
        if name=='stars.8.json' and (not isinstance(obj,dict) or obj.get('type')!='FeatureCollection' or len(obj.get('features',[]))<100):
            raise ValueError('Star catalogue does not contain the expected GeoJSON stars.')
        if name=='world.geojson' and (not isinstance(obj,dict) or obj.get('type')!='FeatureCollection' or len(obj.get('features',[]))<5):
            raise ValueError('World-map coastline catalogue is invalid.')


def download(kind):
    if kind not in SOURCES:raise ValueError('Unknown astronomical dataset.')
    item=SOURCES[kind]
    info=manifest();last=info.get(kind,{})
    if kind=='satellites' and last.get('attempt_utc'):
        try:
            age=(datetime.now(timezone.utc)-datetime.fromisoformat(last['attempt_utc'])).total_seconds()
            if age<(14400 if last.get('state')=='error' else 7200):
                raise ValueError('CelesTrak refresh postponed to respect provider update/retry limits.')
        except (TypeError,ValueError) as exc:
            if str(exc).startswith('CelesTrak refresh postponed'):raise

    current={**last,'attempt_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'),'state':'downloading','error':''}
    info[kind]=current;_write_json(MANIFEST,info)
    newfiles=[]
    try:
        for name,url in item['files'].items():
            parts=urlparse(url)
            if parts.scheme!='https' or not approved_host(parts.hostname):
                raise ValueError('Astronomical data source is not approved.')
            req=urllib.request.Request(url,headers={'User-Agent':'MoonCheeseSkyMap/1.0 (cached daily or on demand)','Accept':'application/octet-stream,application/json,text/csv,*/*'})
            temp=ROOT/kind/('.'+name+'.'+secrets.token_hex(8)+'.part')
            temp.parent.mkdir(mode=0o750,parents=True,exist_ok=True)
            newfiles.append((name,temp))
            size=0
            with urllib.request.urlopen(req,timeout=45) as resp:
                if not approved_host(urlparse(resp.geturl()).hostname):
                    raise ValueError('Astronomical data download redirected to an unapproved host.')
                if resp.status!=200:raise ValueError('Astronomical data provider returned HTTP '+str(resp.status))
                with temp.open('xb') as out:
                    os.chmod(temp,0o600)
                    while True:
                        buf=resp.read(256*1024)
                        if not buf:break
                        size+=len(buf)
                        if size>item['max']:raise ValueError('Astronomical data exceeds its size limit.')
                        out.write(buf)
                    out.flush();os.fsync(out.fileno())
            if kind=='plate_solver':
                try:
                    with zipfile.ZipFile(io.BytesIO(temp.read_bytes())) as archive:
                        names=[entry for entry in archive.namelist() if Path(entry).name.lower()=='w08.001']
                        if len(names)!=1 or archive.getinfo(names[0]).file_size>2_000_000:
                            raise ValueError('W08 download has an unexpected archive layout.')
                        contents=archive.read(names[0])
                    _verify(kind,name,contents)
                    temp.write_bytes(contents)  # Verified data only; no archive extraction paths.
                except (zipfile.BadZipFile,KeyError,RuntimeError) as exc:
                    raise ValueError('W08 download is not a valid ASTAP star database archive.') from exc
            else:
                _verify(kind,name,temp.read_bytes())
        # Commit only after every file in this dataset has downloaded and validated.
        # Multi-file datasets retain old files until each replacement is ready.
        checks={}
        for name,temp in newfiles:
            checks[name]=hashlib.sha256(temp.read_bytes()).hexdigest()
        for name,temp in newfiles:
            os.replace(temp,ROOT/kind/name)
        info=manifest()
        info[kind]={'state':'installed','attempt_utc':current['attempt_utc'],
                    'download_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'),
                    'sha256':checks,'error':''}
        _write_json(MANIFEST,info)
        return True
    except Exception as exc:
        info=manifest();info[kind]={**last,'state':'error','attempt_utc':current['attempt_utc'],
                                    'error':('HTTP '+str(exc.code) if isinstance(exc,urllib.error.HTTPError)
                                             else str(exc)[:220])}
        _write_json(MANIFEST,info)
        raise
    finally:
        for _,part in newfiles:part.unlink(missing_ok=True)


def queue_download(kind):
    if kind!='all' and kind not in SOURCES:raise ValueError('Unknown astronomical dataset.')
    if kind=='satellites':
        meta=manifest().get('satellites',{})
        # Respect source update cadence and do not hammer a failed CelesTrak API.
        last=meta.get('attempt_utc','')
        if last:
            try:
                age=(datetime.now(timezone.utc)-datetime.fromisoformat(last)).total_seconds()
                min_age=14400 if meta.get('state')=='error' else 7200
                if age<min_age:
                    raise ValueError(f'Please wait before refreshing CelesTrak orbital data again (minimum {min_age//3600} hours between attempts).')
            except (ValueError,TypeError) as exc:
                if str(exc).startswith('Please wait'):raise

    REQUESTS.mkdir(mode=0o750,parents=True,exist_ok=True)
    if any(REQUESTS.glob('*.json')):
        raise ValueError('An astronomical data download is already queued.')
    ident=secrets.token_hex(12)
    _write_json(REQUESTS/(ident+'.json'),{'kind':kind,'created':time.time()})
    return ident


def process_requests():
    for path in sorted(REQUESTS.glob('*.json')):
        if path.is_symlink() or path.stat().st_size>1024:
            path.unlink(missing_ok=True);continue
        job=_read_json(path,{})
        path.unlink(missing_ok=True)
        kind=job.get('kind','')
        if kind not in SOURCES and kind!='all':continue
        for current in (SOURCES if kind=='all' else [kind]):
            if kind=='all' and dataset_status()[current]['installed']:
                # Download All means download what's missing, not redownload good 32MB files.
                continue
            try:download(current)
            except Exception:pass  # Individual error recorded for dashboard.


def due_for_satellites(moment=None):
    setting=prefs()
    if not setting.get('auto_satellites'):return False
    cfg=read_config()
    try:tz=ZoneInfo(cfg.get('schedule_timezone','UTC'))
    except (ValueError,KeyError):tz=timezone.utc
    now=moment or datetime.now(timezone.utc)
    local=now.astimezone(tz)
    if (local.hour,local.minute)<(int(setting['satellite_hour']),int(setting['satellite_minute'])):return False
    state=manifest().get('satellites',{})
    last=state.get('download_utc','')
    # After an HTTP/provider error halt automatic requests until an administrator
    # explicitly requests a fresh download; never hammer CelesTrak on future days.
    if state.get('state')=='error':return False
    if last:
        try:
            if datetime.fromisoformat(last).astimezone(tz).date()>=local.date():return False
        except ValueError:pass
    # One attempt per day including provider errors; do not hammer a failing source.
    attempt=state.get('attempt_utc','')
    if attempt:
        try:
            if datetime.fromisoformat(attempt).astimezone(tz).date()>=local.date():return False
        except ValueError:pass
    return True



def next_satellite_check(moment=None):
    """Human-visible schedule; earliest eligible local date, not a precise systemd tick."""
    config=prefs()
    if not config.get('auto_satellites'):return 'Disabled'
    status=manifest().get('satellites',{})
    if status.get('state')=='error':return 'Paused after provider error — manually retry when permitted'
    try:zone=ZoneInfo(read_config().get('schedule_timezone','UTC'))
    except (ValueError,KeyError):zone=timezone.utc
    local=(moment or datetime.now(timezone.utc)).astimezone(zone)
    target=local.replace(hour=int(config['satellite_hour']),minute=int(config['satellite_minute']),second=0,microsecond=0)
    if local>=target:target+=timedelta(days=1)
    last=status.get('download_utc','')
    if last:
        try:
            if datetime.fromisoformat(last).astimezone(zone).date()>=target.date():target+=timedelta(days=1)
        except ValueError:pass
    return target.strftime('%d %b %Y %H:%M')+' (local; next worker tick follows)'


def auto():
    process_requests()
    if due_for_satellites():
        try:download('satellites')
        except Exception:pass
