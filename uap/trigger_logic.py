"""Record which detector(s) fired at the start of each motion event."""

SOURCE_LABELS = {
    'general': 'General motion',
    'sky_lights': 'Moving bright point',
    'both': 'General motion and moving bright point',
    '': 'Not recorded',
}


def source_for_trigger(profile, general_detected, sky_detected):
    if profile == 'general':
        return 'general' if general_detected else ''
    if profile == 'sky_lights':
        return 'sky_lights' if sky_detected else ''
    if profile == 'combined':
        if general_detected and sky_detected:
            return 'both'
        if general_detected:
            return 'general'
        if sky_detected:
            return 'sky_lights'
    return ''
