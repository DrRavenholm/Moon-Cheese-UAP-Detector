"""Backwards-compatible independent detection method selection and UI defaults."""
METHODS = ('general', 'sky_lights', 'mog2', 'transient')
LEGACY = {'general':('general',), 'sky_lights':('sky_lights',), 'combined':('general','sky_lights')}
DEFAULTS = {
    'pixel_threshold':32, 'min_changed_pixels':65,
    'sky_brightness':180, 'sky_min_area':2, 'sky_max_area':100,
    'sky_confirm_frames':3, 'sky_min_movement':2,
    'mog2_threshold':24, 'mog2_min_area':6, 'mog2_confirm_frames':2,
    'transient_threshold':45, 'transient_min_area':2,
    'transient_min_length':7,
}
PRESETS = {
    'balanced': dict(DEFAULTS),
    'faint': {**DEFAULTS, 'pixel_threshold':22,'min_changed_pixels':20,'sky_brightness':125,
              'sky_min_area':1,'sky_confirm_frames':2,'sky_min_movement':1,
              'mog2_threshold':18,'mog2_min_area':4,'transient_threshold':34},
    'fast': {**DEFAULTS, 'pixel_threshold':28,'min_changed_pixels':30,'sky_brightness':160,
             'sky_confirm_frames':2,'mog2_threshold':20,'transient_threshold':30,
             'transient_min_area':2,'transient_min_length':5},
}

def selected(config):
    """Old installations map the previous dropdown without losing either engine."""
    raw = config.get('detection_methods')
    if raw is None:
        return LEGACY.get(config.get('detection_profile','general'), ('general',))
    if not isinstance(raw,list) or not raw or len(raw)!=len(set(raw)) or any(x not in METHODS for x in raw):
        raise ValueError('Choose at least one valid detection method.')
    return tuple(x for x in METHODS if x in raw)

def legacy_label(methods):
    if methods==('general',): return 'general'
    if methods==('sky_lights',): return 'sky_lights'
    return 'combined'
