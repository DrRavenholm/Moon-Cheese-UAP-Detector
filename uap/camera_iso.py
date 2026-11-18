"""Photographic ISO-equivalent labels derived from libcamera gain metadata.

These are Picamera2-style EXIF equivalents, not calibrated DSLR sensitivity.
AnalogueGain remains the hardware control; DigitalGain can vary with ISP/AE.
"""

def iso_equivalent(analogue_gain, digital_gain=1.0):
    try:
        gain=float(analogue_gain);digital=float(digital_gain)
        import math
        if not (math.isfinite(gain) and math.isfinite(digital)) or gain<=0 or digital<=0:return None
        return int(round(100*gain*digital))
    except (ValueError,TypeError):
        return None


def readings(metadata):
    if not isinstance(metadata,dict):return {}
    result={}
    for key,name in (('AnalogueGain','analogue_gain'),('DigitalGain','digital_gain')):
        try:result[name]=round(float(metadata[key]),3)
        except (KeyError,ValueError,TypeError):pass
    try:result['exposure_ms']=round(float(metadata['ExposureTime'])/1000,2)
    except (KeyError,ValueError,TypeError):pass
    iso=iso_equivalent(result.get('analogue_gain'),result.get('digital_gain',1))
    if iso is not None:result['iso_equivalent']=iso
    return result
