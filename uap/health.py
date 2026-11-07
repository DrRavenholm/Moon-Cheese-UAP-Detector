"""Read-only local Pi health and detector heartbeat for dashboard status."""
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from common import DATA, STATUS


def _read_number(path):
    try:
        return float(Path(path).read_text().split()[0])
    except (OSError, ValueError, IndexError):
        return None


def meminfo(path='/proc/meminfo'):
    try:
        content = Path(path).read_text()
        info = {}
        for line in content.splitlines():
            if ':' not in line:
                continue
            key, value = line.split(':', 1)
            info[key] = int(value.split()[0]) * 1024
        total = info['MemTotal']; available = info['MemAvailable']
        return {'total_mb': round(total / 1048576),
                'used_mb': round((total-available) / 1048576),
                'available_mb': round(available / 1048576)}
    except (OSError, ValueError, KeyError, IndexError):
        return None


def detector_state(now=None):
    import json
    now = now or datetime.now(timezone.utc)
    try:
        state = json.loads(STATUS.read_text())
        updated = datetime.fromisoformat(state['updated'].replace('Z', '+00:00'))
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
        age = (now - updated).total_seconds()
        if age < -30 or age > 75:
            return {'state': 'offline', 'message': 'Detector heartbeat missing or stale', 'age_seconds': max(0, round(age))}
        return {'state': str(state.get('state', 'unknown'))[:32],
                'message': str(state.get('message', ''))[:160],
                'age_seconds': max(0, round(age))}
    except (OSError, ValueError, TypeError, KeyError):
        return {'state': 'offline', 'message': 'Waiting for detector heartbeat', 'age_seconds': None}


def system_health():
    space = shutil.disk_usage(DATA)
    try:
        load = tuple(round(x, 2) for x in os.getloadavg())
    except OSError:
        load = None
    temp_milli = _read_number('/sys/class/thermal/thermal_zone0/temp')
    temp = round(temp_milli / 1000, 1) if temp_milli is not None else None
    uptime_secs = _read_number('/proc/uptime')
    img = DATA / 'latest.jpg'
    image_age = max(0, round(datetime.now(timezone.utc).timestamp() - img.stat().st_mtime)) if img.is_file() else None
    free_percent = 100 * space.free / space.total if space.total else 0
    # Soft warning, not a hard reservation; a Pi can have other uses on its disk.
    disk_warning = space.free < 2 * 1024**3 or free_percent < 10
    return {
        'detector': detector_state(), 'disk_total_gb': round(space.total / 1024**3, 2),
        'disk_free_gb': round(space.free / 1024**3, 2),
        'disk_free_percent': round(free_percent, 1), 'disk_warning': disk_warning,
        'memory': meminfo(), 'cpu_temp_c': temp, 'load_average': load,
        'uptime_hours': round(uptime_secs / 3600, 1) if uptime_secs is not None else None,
        'snapshot_age_seconds': image_age,
    }
