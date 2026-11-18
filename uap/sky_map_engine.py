"""Local astronomical projection inputs. Never opens the camera or downloads data."""
import csv
import json
import math
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from common import read_config
from sky_map_data import ROOT

BODIES={'Sun':'sun','Moon':'moon','Mercury':'mercury','Venus':'venus','Mars':'mars',
        'Jupiter':'jupiter barycenter','Saturn':'saturn barycenter',
        'Uranus':'uranus barycenter','Neptune':'neptune barycenter'}


def when(value):
    try:
        dt=datetime.fromisoformat(value.replace('Z','+00:00')) if value else datetime.now(timezone.utc)
        if dt.tzinfo is None:raise ValueError()
        dt=dt.astimezone(timezone.utc)
        if not 1849<=dt.year<=2150:raise ValueError()
        return dt
    except (TypeError,ValueError):raise ValueError('Choose a valid date and time between 1849 and 2150.')


def coordinates():
    config=read_config()
    lat,lon=config.get('latitude'),config.get('longitude')
    if lat is None or lon is None:raise ValueError('Configure the detector latitude and longitude in Detector Settings before using Sky Maps.')
    lat,lon=float(lat),float(lon)
    if not -90<=lat<=90 or not -180<=lon<=180:raise ValueError('Detector coordinates are invalid.')
    return lat,lon


def _skyfield():
    try:
        from skyfield.api import load, load_file, wgs84, EarthSatellite
        return load,load_file,wgs84,EarthSatellite
    except ImportError as exc:
        raise ValueError('Skyfield astronomy package is not installed. Run the Moon Cheese installer with network access.') from exc


@lru_cache(maxsize=1)
def _timescale():
    # Loading Skyfield's built-in timescale per browser poll needlessly consumes
    # CPU/disk on a Raspberry Pi; cache the immutable object in the map worker.
    load,_,_,_=_skyfield()
    return load.timescale(builtin=True)


def _time(dt):
    ts=_timescale()
    return ts.from_datetime(dt), ts


@lru_cache(maxsize=2)
def _ephemeris(modified_at_ns):
    # Cache the opened SPK kernel; never mmap/reopen 32 MB every two seconds.
    _,load_file,_,_=_skyfield()
    return load_file(str(ROOT/'planets'/'de440s.bsp'))


def catalogue():
    """Browser projectors only need lightweight, capped coordinate lists."""
    signature=tuple((ROOT/k/n).stat().st_mtime_ns if (ROOT/k/n).is_file() else 0
                    for k,n in (('stars','stars.8.json'),('stars','starnames.json'),
                                ('constellations','constellations.lines.json'),
                                ('constellations','constellations.json'),('deep_sky','messier.json'),
                                ('deep_sky','dsos.bright.json'),('world','world.geojson')))
    return _cached_catalogue(signature)

@lru_cache(maxsize=2)
def _cached_catalogue(signature):
    output={'stars':[],'lines':[],'constellations':[],'deep_sky':[],'world':[]}
    def features(group,name):
        try:
            obj=json.loads((ROOT/group/name).read_text())
            return obj.get('features',[]) if isinstance(obj,dict) else []
        except (OSError,ValueError):return []
    try:
        names=json.loads((ROOT/'stars'/'starnames.json').read_text())
        if not isinstance(names,dict):names={}
    except (OSError,ValueError):names={}
    for f in features('stars','stars.8.json'):
        coords=f.get('geometry',{}).get('coordinates',[])
        p=f.get('properties') or {}
        if len(coords)<2 or not all(isinstance(x,(int,float)) for x in coords[:2]):continue
        try:mag=float(p.get('mag',p.get('magnitude',8)))
        except (ValueError,TypeError):continue
        if mag>6.5:continue
        nameinfo=names.get(str(f.get('id','')),{})
        if not isinstance(nameinfo,dict):nameinfo={}
        proper=nameinfo.get('iau') or nameinfo.get('name') or nameinfo.get('desig') or p.get('desig') or p.get('name') or ''
        output['stars'].append([coords[0],coords[1],round(mag,2),str(proper)[:60]])
        if len(output['stars'])>=6500:break
    for f in features('constellations','constellations.lines.json'):
        geo=f.get('geometry') or {}
        if geo.get('type')=='MultiLineString':segments=geo.get('coordinates',[])
        elif geo.get('type')=='LineString':segments=[geo.get('coordinates',[])]
        else:continue
        for segment in segments:
            if len(segment)>=2:output['lines'].append(segment[:100])
    for f in features('constellations','constellations.json'):
        geo=f.get('geometry') or {}
        p=f.get('properties') or {}
        if geo.get('type')=='Point' and len(geo.get('coordinates',[]))>=2:
            output['constellations'].append([*geo['coordinates'][:2],str(p.get('name') or p.get('id') or f.get('id') or '')[:50]])
    for name in ('messier.json','dsos.bright.json'):
        for f in features('deep_sky',name):
            geo=f.get('geometry') or {};p=f.get('properties') or {}
            if geo.get('type')=='Point' and len(geo.get('coordinates',[]))>=2:
                output['deep_sky'].append([*geo['coordinates'][:2],str(p.get('desig') or p.get('name') or f.get('id') or '')[:60]])
                if len(output['deep_sky'])>=300:break
    for f in features('world','world.geojson'):
        geo=f.get('geometry') or {}
        if geo.get('type')=='Polygon':polys=[geo.get('coordinates',[])]
        elif geo.get('type')=='MultiPolygon':polys=geo.get('coordinates',[])
        else:continue
        for poly in polys:
            if poly and len(poly[0])>=3:output['world'].append(poly[0])
    return output


def _orbital_rows():
    source=ROOT/'satellites'/'active.csv'
    try:signature=source.stat().st_mtime_ns
    except OSError:return []
    return _cached_orbital_rows(signature)


@lru_cache(maxsize=2)
def _cached_orbital_rows(modified_at_ns):
    # Reparse only when a validated orbital file is replaced by the data worker.
    source=ROOT/'satellites'/'active.csv'
    try:
        with source.open(encoding='utf-8-sig',newline='') as f:
            return [row for row in csv.DictReader(f) if row.get('NORAD_CAT_ID') and row.get('MEAN_MOTION')]
    except OSError:return []


def search(query):
    query=query.strip().casefold()
    if len(query)<2:return []
    matches=[]
    for name in BODIES:
        if query in name.casefold():matches.append({'id':'planet:'+name,'name':name,'kind':'planet'})
    for row in _orbital_rows():
        name=row.get('OBJECT_NAME') or row.get('NORAD_CAT_ID')
        if query in name.casefold() or query in row.get('NORAD_CAT_ID',''):
            matches.append({'id':'sat:'+row['NORAD_CAT_ID'],'name':name[:90],'kind':'satellite'})
            if len(matches)>=30:break
    for kind, entries in (('star',catalogue()['stars']),('deep_sky',catalogue()['deep_sky'])):
        for obj in entries:
            if obj[3] and query in obj[3].casefold():
                matches.append({'id':kind+':'+obj[3],'name':obj[3],'kind':kind,'ra':obj[0],'dec':obj[1]})
                if len(matches)>=30:break
    return matches[:30]


def positions(at, selected='', lat=None, lon=None):
    if lat is None or lon is None:lat,lon=coordinates()
    load,load_file,wgs84,EarthSatellite=_skyfield()
    t,ts=_time(at)
    observer=wgs84.latlon(latitude_degrees=lat,longitude_degrees=lon)
    result={'time':at.isoformat(),'latitude':lat,'longitude':lon,'planets':[], 'satellites':[], 'selected':None,'track':[]}
    eph=ROOT/'planets'/'de440s.bsp'
    if eph.is_file():
        planets=_ephemeris(eph.stat().st_mtime_ns)
        place=planets['earth']+observer
        for name,key in BODIES.items():
            try:
                apparent=place.at(t).observe(planets[key]).apparent()
                alt,az,distance=apparent.altaz();ra,dec,_=apparent.radec()
                result['planets'].append({'id':'planet:'+name,'name':name,'kind':'planet','alt':round(alt.degrees,3),
                        'az':round(az.degrees,3),'ra':round(ra.hours*15,4),'dec':round(dec.degrees,4)})
            except (KeyError,ValueError):continue
    orbital=_orbital_rows()
    # Selected-object precision is independent from the capped general satellite display.
    # Cap ambient propagation to protect Raspberry Pi CPU while allowing search across the full catalogue.
    key=selected.removeprefix('sat:') if selected.startswith('sat:') else ''
    if orbital:
        focus=[r for r in orbital if r.get('NORAD_CAT_ID')==key] if key else []
        # Sort in a stable, source-independent fashion: first active items are an overview,
        # not a claim to display every catalogue object. All entries remain searchable.
        preview=orbital[:240]
        entries={r['NORAD_CAT_ID']:r for r in preview+focus}
        for row in entries.values():
            try:
                sat=EarthSatellite.from_omm(ts,row)
                topocentric=(sat-observer).at(t)
                alt,az,distance=topocentric.altaz()
                if alt.degrees<-5 and row['NORAD_CAT_ID']!=key:continue
                sub=wgs84.subpoint_of(sat.at(t))
                obj={'id':'sat:'+row['NORAD_CAT_ID'],'name':row.get('OBJECT_NAME','Satellite')[:90],
                     'kind':'satellite','alt':round(alt.degrees,3),'az':round(az.degrees,3),
                     'lat':round(sub.latitude.degrees,4),'lon':round(sub.longitude.degrees,4),
                     'epoch':row.get('EPOCH','')}
                result['satellites'].append(obj)
                if row['NORAD_CAT_ID']==key:
                    result['selected']=obj
                    for minutes in range(-50,51,5):
                        tt=ts.tt_jd(t.tt+minutes/1440)
                        tp=wgs84.subpoint_of(sat.at(tt))
                        result['track'].append([round(tp.longitude.degrees,3),round(tp.latitude.degrees,3)])
            except (ValueError,KeyError,OverflowError,TypeError):continue
    if selected.startswith('planet:'):
        result['selected']=next((p for p in result['planets'] if p['id']==selected),None)
    return result
