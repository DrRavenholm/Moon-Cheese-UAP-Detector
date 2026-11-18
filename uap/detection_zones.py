"""Resolution-independent include/exclude polygons for the two detector trigger paths.

The mask is never applied to video, photographs or the public camera preview.
"""
import json
import os
import secrets
from pathlib import Path
from common import DATA

PATH=DATA/'detection-zones.json'
MAX_ZONES=24
MAX_POINTS=36


def validate(raw):
    if not isinstance(raw,dict):raise ValueError('Invalid zone configuration.')
    zones=raw.get('zones',[])
    if not isinstance(zones,list) or len(zones)>MAX_ZONES:raise ValueError('Too many detection zones (maximum 24).')
    checked=[]
    for z in zones:
        if not isinstance(z,dict) or z.get('type') not in ('include','exclude'):
            raise ValueError('Choose a monitoring or exclusion zone.')
        points=z.get('points',[])
        if not isinstance(points,list) or not 3<=len(points)<=MAX_POINTS:
            raise ValueError('Each detection polygon requires 3–36 vertices.')
        normal=[]
        for p in points:
            if not isinstance(p,list) or len(p)!=2 or not all(type(a) in (int,float) and 0<=a<=1 for a in p):
                raise ValueError('Zone coordinates must stay inside the image.')
            normal.append([round(float(p[0]),6),round(float(p[1]),6)])
        checked.append({'type':z['type'],'points':normal})
    return {'enabled':raw.get('enabled') is True,'zones':checked}


def read():
    try:return validate(json.loads(PATH.read_text()))
    except (OSError,ValueError,TypeError):return {'enabled':False,'zones':[]}


def write(value):
    value=validate(value)
    PATH.parent.mkdir(parents=True,exist_ok=True,mode=0o750)
    tmp=PATH.with_name('.zones-'+secrets.token_hex(8))
    try:
        with tmp.open('x') as f:
            os.chmod(tmp,0o600)
            json.dump(value,f)
            f.flush();os.fsync(f.fileno())
        os.replace(tmp,PATH)
    finally:tmp.unlink(missing_ok=True)
    return value


def mask(width,height,config):
    import cv2
    import numpy as np
    width,height=int(width),int(height)
    if width<1 or height<1:raise ValueError('Invalid detector frame dimensions.')
    config=validate(config)
    result=np.full((height,width),255,dtype=np.uint8)
    if not config['enabled'] or not config['zones']:return result
    includes=[z for z in config['zones'] if z['type']=='include']
    if includes:result.fill(0)
    for zone in includes+[z for z in config['zones'] if z['type']=='exclude']:
        points=np.array([[round(p[0]*(width-1)),round(p[1]*(height-1))] for p in zone['points']],dtype=np.int32)
        cv2.fillPoly(result,[points],255 if zone['type']=='include' else 0)
    return result
