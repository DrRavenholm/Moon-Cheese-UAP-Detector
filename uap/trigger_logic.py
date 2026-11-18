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

METHOD_LABELS={'general':'General motion','sky_lights':'Moving sky lights',
               'mog2':'Adaptive background','transient':'Transient / streak'}
from itertools import combinations
for size in range(1,len(METHOD_LABELS)+1):
    for group in combinations(METHOD_LABELS,size):
        SOURCE_LABELS['+'.join(group)]=' + '.join(METHOD_LABELS[k] for k in group)

def combined_source(candidates):
    return '+'.join(k for k in METHOD_LABELS if candidates.get(k))
