"""Camera profile selection and validated Picamera2 controls.

Exposure values are milliseconds in the UI, microseconds in libcamera.
These are real camera controls, not video post-processing filters.
"""
from datetime import datetime, timezone
from scheduling import sun_times, zone

SLOTS = ('day', 'night', 'custom1', 'custom2')
MODES = ('auto', 'day', 'night', 'custom1', 'custom2', 'solar')


def base_profiles():
    return {
        'day': {'name': 'Day', 'auto_exposure': True, 'exposure_ms': 10.0, 'gain': 1.0, 'ev': 0.0, 'awb': True, 'red_gain': 1.5, 'blue_gain': 1.5, 'focus': 'infinity', 'brightness': 0.0, 'contrast': 1.0, 'saturation': 1.0},
        'night': {'name': 'Night', 'auto_exposure': False, 'exposure_ms': 28.0, 'gain': 6.0, 'ev': 0.0, 'awb': True, 'red_gain': 1.5, 'blue_gain': 1.5, 'focus': 'infinity', 'brightness': 0.0, 'contrast': 1.0, 'saturation': 1.0},
        'custom1': {'name': 'Custom 1', 'auto_exposure': True, 'exposure_ms': 15.0, 'gain': 2.0, 'ev': 0.0, 'awb': True, 'red_gain': 1.5, 'blue_gain': 1.5, 'focus': 'infinity', 'brightness': 0.0, 'contrast': 1.0, 'saturation': 1.0},
        'custom2': {'name': 'Custom 2', 'auto_exposure': True, 'exposure_ms': 15.0, 'gain': 2.0, 'ev': 0.0, 'awb': True, 'red_gain': 1.5, 'blue_gain': 1.5, 'focus': 'infinity', 'brightness': 0.0, 'contrast': 1.0, 'saturation': 1.0},
    }


def validate_profile(profile):
    p = dict(profile)
    for key, a, b in [('exposure_ms', .1, 1000), ('gain', 1, 16), ('ev', -4, 4),
                       ('red_gain', .1, 8), ('blue_gain', .1, 8), ('brightness', -1, 1),
                       ('contrast', .25, 4), ('saturation', 0, 3)]:
        try:
            n = float(p[key])
        except (ValueError, TypeError, KeyError):
            raise ValueError(f'{key} must be a number')
        import math
        if not math.isfinite(n) or not a <= n <= b:
            raise ValueError(f'{key} must be between {a} and {b}')
        p[key] = n
    for key in ('auto_exposure', 'awb'):
        if type(p.get(key)) is not bool:
            raise ValueError(f'{key} must be enabled or disabled')
    if p.get('focus') not in ('infinity', 'auto'):
        raise ValueError('Choose automatic focus or infinity')
    name = str(p.get('name', '')).strip()
    if not name or len(name) > 48 or any(ord(c) < 32 for c in name):
        raise ValueError('Profile names must be 1–48 printable characters')
    p['name'] = name
    return p


def get_profiles(cfg):
    defaults = base_profiles()
    supplied = cfg.get('camera_profiles', {})
    if not isinstance(supplied, dict):
        supplied = {}
    for key in SLOTS:
        if isinstance(supplied.get(key), dict):
            defaults[key].update(supplied[key])
        defaults[key] = validate_profile(defaults[key])
    return defaults


def effective_slot(cfg, now=None):
    mode = cfg.get('camera_profile_mode', 'auto')
    if mode not in MODES:
        raise ValueError('Unrecognised camera profile selection')
    if mode != 'solar':
        return mode
    lat, lon = cfg.get('latitude'), cfg.get('longitude')
    if lat is None or lon is None:
        return 'auto'  # Safe fallback when coordinates have not been configured.
    tzname = cfg.get('schedule_timezone', 'Europe/London')
    local = (now or datetime.now(timezone.utc)).astimezone(zone(tzname))
    pair = sun_times(local.date(), float(lat), float(lon), tzname)
    if pair is None:
        return 'auto'  # Polar day/night: avoid guessing.
    sunrise, sunset = pair
    return 'night' if local < sunrise or local >= sunset else 'day'


def selected_profile(cfg, now=None):
    key = effective_slot(cfg, now=now)
    return key, None if key == 'auto' else get_profiles(cfg)[key]


def exposure_within_frame(profile, fps):
    return bool(profile['auto_exposure'] or float(profile['exposure_ms']) <= 1000.0 / float(fps))


def camera_controls(profile, fps, allowed, libcontrols=None):
    """Compose controls and use focus only when hardware supports it."""
    c = {'FrameRate': int(fps)}
    if profile is None:
        c.update(AeEnable=True, AwbEnable=True)
        return c
    if profile['auto_exposure']:
        c.update(AeEnable=True, ExposureValue=profile['ev'])
    else:
        missing = {'AeEnable', 'ExposureTime', 'AnalogueGain'} - set(allowed)
        if missing:
            raise ValueError('Manual exposure/gain controls unavailable on this camera: ' + ', '.join(sorted(missing)))
        if not exposure_within_frame(profile, fps):
            raise ValueError('Exposure exceeds the available time per video frame; reduce fps or exposure')
        c.update(AeEnable=False, ExposureTime=int(profile['exposure_ms'] * 1000), AnalogueGain=profile['gain'])
    if profile['awb']:
        c['AwbEnable'] = True
    else:
        if 'ColourGains' not in allowed:
            raise ValueError('Manual white balance is not supported on this camera')
        c.update(AwbEnable=False, ColourGains=(profile['red_gain'], profile['blue_gain']))
    c.update(Brightness=profile['brightness'], Contrast=profile['contrast'], Saturation=profile['saturation'])
    if libcontrols is not None and 'AfMode' in allowed:
        c['AfMode'] = (libcontrols.AfModeEnum.Continuous if profile['focus'] == 'auto'
                       else libcontrols.AfModeEnum.Manual)
        if profile['focus'] == 'infinity' and 'LensPosition' in allowed:
            c['LensPosition'] = 0.0
    return {key: value for key, value in c.items() if key == 'FrameRate' or key in allowed}


def compass_name(deg):
    return ('N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW')[int((float(deg) + 22.5) // 45) % 8]
