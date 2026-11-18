"""Bounded atomic detector diagnostics; local administrators only."""
import json
import os
from datetime import datetime,timezone
from common import DATA
PATH=DATA/'detection-diagnostics.json'

def publish(frame,methods,scores,candidates,record_allowed,reason,recording,zone_fraction,fps,counts=None):
    # Values are measurements, not a claim that astronomical objects were identified.
    import numpy as np
    values={
        'updated':datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'brightness_mean':round(float(frame.mean()),1),
        'nearly_black_percent':round(float(np.mean(frame<6)*100),1),
        'nearly_white_percent':round(float(np.mean(frame>249)*100),1),
        'methods':list(methods),
        'scores':{k:int(v) for k,v in scores.items()},
        'candidates':{k:bool(v) for k,v in candidates.items()},
        'recording':bool(recording),
        'record_allowed':bool(record_allowed),
        'reason':str(reason)[:140],
        'active_zone_percent':round(float(zone_fraction*100),1),
        'analysis_fps':round(float(fps),1),
        'counts':dict(counts or {}),
    }
    PATH.parent.mkdir(parents=True,exist_ok=True)
    tmp=PATH.with_name('.detection-diagnostics-'+str(os.getpid())+'.tmp')
    try:
        with tmp.open('w') as f:
            os.chmod(tmp,0o600);json.dump(values,f);f.flush();os.fsync(f.fileno())
        os.replace(tmp,PATH)
    finally:tmp.unlink(missing_ok=True)
