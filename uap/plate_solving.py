"""Optional offline ASTAP plate solving. No camera is opened by this module.

All image selections are validated against saved Moon Cheese photographs. Solutions
are provisional until an administrator explicitly saves the calibration.
"""
import json
import math
import os
import re
import secrets
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from common import DATA, read_config
from photography import ROOT as PHOTO_ROOT, output_path, result_path
from sky_map_data import ROOT as SKY_DATA

ROOT = DATA / 'plate-solving'
REQUESTS = ROOT / 'requests'
RESULTS = ROOT / 'results'
CALIBRATION = ROOT / 'camera-calibration.json'
SETUP_REQUEST = ROOT / 'install-request.json'
SETUP_STATUS = ROOT / 'install-status.json'
TOKEN = re.compile(r'^[0-9a-f]{32}$')
W08 = SKY_DATA / 'plate_solver' / 'w08_0101.001'


def _write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o750)
    tmp = path.parent / ('.'+path.name+'.'+secrets.token_hex(8))
    try:
        with tmp.open('x', encoding='utf-8') as stream:
            os.chmod(tmp, 0o600)
            json.dump(obj, stream, ensure_ascii=False)
            stream.flush(); os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally: tmp.unlink(missing_ok=True)


def _read(path):
    try:
        obj=json.loads(path.read_text(encoding='utf-8'))
        return obj if isinstance(obj,dict) else {}
    except (ValueError,OSError):return {}


def solver_path():
    return shutil.which('astap_cli') or shutil.which('astap')


def setup_status():
    status=_read(SETUP_STATUS)
    return {'solver_installed':bool(solver_path()), 'index_installed':W08.is_file() and W08.stat().st_size>100000,
            'setup':status,'calibration':_read(CALIBRATION)}


def photo_source(token):
    if not isinstance(token,str) or not TOKEN.fullmatch(token):raise ValueError('Invalid photograph reference')
    # Safe exact filenames, only files produced by Moon Cheese Photography.
    for ext in ('jpg','png'):
        source=output_path(token,ext)
        if source.is_file() and not source.is_symlink() and 10_000 < source.stat().st_size < 80_000_000:
            return source
    raise ValueError('The saved full-resolution photograph is no longer available')


def photograph_date(token, path):
    try:
        payload=_read(result_path(token))
        if payload.get('created_utc'):
            dt=datetime.fromisoformat(payload['created_utc'])
            if dt.tzinfo: return dt.astimezone(timezone.utc)
    except (TypeError,ValueError,KeyError):pass
    return datetime.fromtimestamp(path.stat().st_mtime,timezone.utc)


def queue_solve(token, *, field_height=67.0):
    source=photo_source(token)
    if not 20 <= float(field_height) <= 85: raise ValueError('Choose a plausible vertical field of view, 20–85 degrees')
    if not solver_path():raise ValueError('Install ASTAP before solving a photograph')
    if not W08.is_file():raise ValueError('Download the W08 wide-field star index first')
    REQUESTS.mkdir(parents=True,exist_ok=True,mode=0o750)
    if list(REQUESTS.glob('*.json')):raise ValueError('A calibration solve is already queued')
    jobid=secrets.token_hex(16)
    _write(RESULTS/(jobid+'.json'),{'state':'queued','message':'Waiting for offline plate solver','token':token})
    _write(REQUESTS/(jobid+'.json'),{'token':token,'field_height':float(field_height),'created':time.time()})
    return jobid


def result(jobid):
    if not TOKEN.fullmatch(str(jobid)):raise ValueError('Invalid calibration job')
    obj=_read(RESULTS/(jobid+'.json'))
    if not obj:raise ValueError('Calibration job not found')
    return obj


def parse_ini(content):
    fields={}
    for line in content.splitlines():
        if '=' in line:
            k,v=line.split('=',1)
            k=k.strip().upper()
            if re.fullmatch(r'[A-Z][A-Z0-9_]{0,20}',k): fields[k]=v.split(' // ',1)[0].strip()
    if fields.get('PLTSOLVD','').upper() not in ('T','TRUE'):
        detail=fields.get('ERROR','No reliable matching star pattern was found')[:180]
        raise ValueError('Plate solving failed: '+detail)
    keys=['CRVAL1','CRVAL2','CRPIX1','CRPIX2','CD1_1','CD1_2','CD2_1','CD2_2']
    try: output={k:float(fields[k]) for k in keys}
    except (KeyError,ValueError,OverflowError):raise ValueError('ASTAP returned an incomplete astrometric solution')
    if not all(math.isfinite(v) for v in output.values()):raise ValueError('ASTAP returned invalid coordinates')
    if not 0<=output['CRVAL1']<360 or not -90<=output['CRVAL2']<=90:
        raise ValueError('Plate-solved celestial coordinates are out of range')
    determinant=output['CD1_1']*output['CD2_2']-output['CD1_2']*output['CD2_1']
    if abs(determinant)<1e-13 or abs(determinant)>1:
        raise ValueError('Plate-solved image scale is invalid')
    output['CROTA2']=float(fields.get('CROTA2',0)) if 'CROTA2' in fields else None
    return output


def _orientation(solution, captured, lat, lon):
    """Convert J2000 WCS central coordinates to local horizon using Skyfield."""
    from skyfield.api import load, load_file, wgs84, Star
    ephemeris=SKY_DATA/'planets'/'de440s.bsp'
    if not ephemeris.is_file():raise ValueError('Download the planetary ephemeris to determine bearing and elevation')
    earth=load_file(str(ephemeris))['earth']
    skytime=load.timescale(builtin=True).from_datetime(captured)
    place=earth+wgs84.latlon(latitude_degrees=lat, longitude_degrees=lon)
    ra=solution['CRVAL1'];dec=solution['CRVAL2']
    def altaz(a,d):
        star=Star(ra_hours=a/15.0, dec_degrees=d)
        alt,az,_=place.at(skytime).observe(star).apparent().altaz()
        return float(alt.degrees),float(az.degrees)
    alt,az=altaz(ra,dec)
    # Small offset toward *top* of original solved image, derived from WCS.
    ystep=-12.0
    north_dec=max(-89.99,min(89.99,dec+solution['CD2_2']*ystep))
    up_ra=(ra+solution['CD1_2']*ystep/max(0.02,math.cos(math.radians(dec))))%360
    up_alt,up_az=altaz(up_ra,north_dec)
    east=math.radians(((up_az-az+180)%360)-180)*math.cos(math.radians(alt))
    north=math.radians(up_alt-alt)
    bearing_up=math.degrees(math.atan2(east,north))%360 if abs(east)+abs(north)>1e-12 else None
    return {'bearing_deg':round(az,3),'elevation_deg':round(alt,3),
            'image_up_heading_deg':round(bearing_up,3) if bearing_up is not None else None}


def solve(token, field_height, *, executable=None, root=None, timeout=150):
    source=photo_source(token)
    exe=executable or solver_path()
    if not exe:raise ValueError('ASTAP command-line solver is not installed')
    dbroot=Path(root) if root is not None else W08.parent
    if not (dbroot/'w08_0101.001').is_file():raise ValueError('ASTAP W08 wide-field star index is missing')
    exposure_date=photograph_date(token,source)
    with tempfile.TemporaryDirectory(prefix='mc-plates-',dir=str(ROOT)) as tmp:
        prefix=str(Path(tmp)/'solution')
        cmd=[exe,'-f',str(source),'-fov',str(float(field_height)), '-r','90',
             '-D','w08','-d',str(dbroot),'-z','0','-o',prefix]
        try:
            completed=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout,
                                     stdin=subprocess.DEVNULL,check=False)
        except subprocess.TimeoutExpired:raise ValueError('Plate solver exceeded the time limit; try a clearer image')
        ini=Path(prefix+'.ini')
        if not ini.is_file():
            # Do not expose arbitrary subprocess diagnostics to visitors.
            raise ValueError('ASTAP did not produce a plate-solving result (exit '+str(completed.returncode)+')')
        solution=parse_ini(ini.read_text(encoding='utf-8',errors='replace')[:20000])
    # Optional genuine reference-star crosscheck (not ASTAP's internal quad list).
    # Missing star catalogues must not turn a valid ASTAP solution into a failure.
    from plate_overlay import crosscheck
    overlay=crosscheck(source,solution)
    lat,lon=None,None
    try:
        from sky_map_engine import coordinates
        lat,lon=coordinates()
        orientation=_orientation(solution,exposure_date,lat,lon)
    except (ValueError,ImportError,KeyError,OSError) as exc:
        orientation={'bearing_deg':None,'elevation_deg':None,'image_up_heading_deg':None}
    # FOV is a local tangent-plane approximation, NOT a validated wide-lens distortion model.
    try:
        import cv2
        dimensions=cv2.imread(str(source),cv2.IMREAD_GRAYSCALE)
        if dimensions is None:raise ValueError('Cannot inspect photograph dimensions')
        h,w=dimensions.shape[:2]
        # Reduced read keeps same aspect, enough for qualitative FOV label only.
        vscale=math.hypot(solution['CD1_2'],solution['CD2_2'])
        hscale=math.hypot(solution['CD1_1'],solution['CD2_1'])
        approx_hfov=round(w*hscale,2)
        approx_vfov=round(h*vscale,2)
    except Exception:
        approx_hfov=approx_vfov=None
    return {'state':'solved','message':'ASTAP matched the photograph against its offline star index',
            'token':token,'capture_utc':exposure_date.isoformat(), 'solved_utc':datetime.now(timezone.utc).isoformat(),
            'latitude':lat,'longitude':lon,'ra_deg':round(solution['CRVAL1'],6),
            'dec_deg':round(solution['CRVAL2'],6),**orientation,
            'rotation_deg':solution.get('CROTA2'),'approx_hfov_deg':approx_hfov,'approx_vfov_deg':approx_vfov,
            'wcs':{key:value for key,value in solution.items() if key!='CROTA2'},
            'overlay':overlay,
            'warning':('The sky location was solved, but local bearing/elevation are unavailable. Check detector location and download the JPL planetary ephemeris. ' if orientation['bearing_deg'] is None else '') + 'Wide-angle lens distortion is not yet calibrated. Angular measurements are approximate, especially near image edges. Existing camera settings have not changed.'}


def process_requests():
    REQUESTS.mkdir(parents=True,exist_ok=True,mode=0o750)
    ROOT.mkdir(parents=True,exist_ok=True,mode=0o750)
    for task in sorted(REQUESTS.glob('*.json')):
        if task.is_symlink() or task.stat().st_size>2048:task.unlink(missing_ok=True);continue
        jobid=task.stem
        if not TOKEN.fullmatch(jobid):task.unlink(missing_ok=True);continue
        job=_read(task);task.unlink(missing_ok=True)
        token=job.get('token','')
        try:
            if not isinstance(token,str) or not TOKEN.fullmatch(token):raise ValueError('Invalid image reference')
            _write(RESULTS/(jobid+'.json'),{'state':'running','message':'ASTAP is matching stars offline','token':token})
            payload=solve(token,float(job.get('field_height',67)))
            _write(RESULTS/(jobid+'.json'),payload)
        except Exception as exc:
            _write(RESULTS/(jobid+'.json'),{'state':'error','message':str(exc)[:240],'token':token})


def save_calibration(jobid):
    payload=result(jobid)
    if payload.get('state')!='solved':raise ValueError('Only a successful plate solution can be saved')
    photo_source(payload['token'])
    selected={k:payload[k] for k in ('token','capture_utc','solved_utc','latitude','longitude',
        'ra_deg','dec_deg','bearing_deg','elevation_deg','image_up_heading_deg','rotation_deg',
        'approx_hfov_deg','approx_vfov_deg','wcs','overlay','warning')}
    selected['saved_utc']=datetime.now(timezone.utc).isoformat()
    _write(CALIBRATION,selected)
    return selected
