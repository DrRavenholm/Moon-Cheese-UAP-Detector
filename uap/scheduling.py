"""Determine whether to record now, using local wall time or civil twilight.

Solar calculation based on the NOAA sunrise/sunset approximation (zenith 90.833°),
no network request or third-party location service needed. Valid up to normal
astronomical accuracy (~a few minutes); polar-day/night returns unavailable.
"""
import math
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def parse_clock(value):
    if not isinstance(value, str) or len(value) != 5 or value[2] != ':':
        raise ValueError('Time must be HH:MM (24-hour clock)')
    try:
        h, m = int(value[:2]), int(value[3:])
    except ValueError as exc:
        raise ValueError('Time must be HH:MM (24-hour clock)') from exc
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError('Invalid clock time')
    return time(h, m)


def zone(name):
    try:
        return ZoneInfo(str(name))
    except (ZoneInfoNotFoundError, ValueError, TypeError) as exc:
        raise ValueError('Timezone must be a valid name like Europe/London') from exc


def sun_event_utc(day, latitude, longitude, sunset):
    """Approximate solar event for an input calendar date (UTC estimate).

    The returned datetime may be outside the input UTC day; callers must match
    the requested *local* calendar date before using it.
    """
    if not (-89.8 <= latitude <= 89.8 and -180 <= longitude <= 180):
        raise ValueError('Latitude/longitude out of supported range')
    n = day.timetuple().tm_yday
    lng_hour = longitude / 15.0
    t = n + ((18.0 if sunset else 6.0) - lng_hour) / 24.0
    mean = (0.9856 * t) - 3.289
    true_long = (mean + 1.916 * math.sin(math.radians(mean)) +
                 0.020 * math.sin(2 * math.radians(mean)) + 282.634) % 360
    right_asc = (math.degrees(math.atan(0.91764 * math.tan(math.radians(true_long)))) % 360)
    right_asc += math.floor(true_long / 90) * 90 - math.floor(right_asc / 90) * 90
    right_asc /= 15
    sin_dec = 0.39782 * math.sin(math.radians(true_long))
    cos_dec = math.cos(math.asin(sin_dec))
    cos_hour = (math.cos(math.radians(90.833)) -
                sin_dec * math.sin(math.radians(latitude))) / (cos_dec * math.cos(math.radians(latitude)))
    if cos_hour < -1 or cos_hour > 1:
        return None  # No ordinary sunrise or sunset on this day (polar latitudes).
    hour = (math.degrees(math.acos(cos_hour)) if sunset else
            360 - math.degrees(math.acos(cos_hour))) / 15
    local_mean = hour + right_asc - (0.06571 * t) - 6.622
    utc_hour = local_mean - lng_hour
    # Some UTC dates cross a boundary; we select by local date in sun_times.
    return datetime(day.year, day.month, day.day, tzinfo=timezone.utc) + timedelta(hours=utc_hour)


def sun_times(local_day, latitude, longitude, timezone_name):
    tz = zone(timezone_name)
    matches = []
    for is_sunset in (False, True):
        found = []
        for offset in (-1, 0, 1):
            day = local_day + timedelta(days=offset)
            event = sun_event_utc(day, latitude, longitude, is_sunset)
            if event is not None and event.astimezone(tz).date() == local_day:
                found.append(event.astimezone(tz))
        if not found:
            return None
        # Rare date-line ambiguity: use earliest matching occurrence.
        matches.append(min(found))
    return tuple(matches)  # sunrise, sunset in local timezone


def detection_window(settings, now=None):
    """Return (enabled, short_reason) without changing detector service state."""
    if settings.get('detection_paused', False):
        return False, 'Paused manually — no new detections'
    mode = settings.get('operation_mode', 'continuous')
    if mode == 'continuous':
        return True, 'Continuous monitoring'
    tz = zone(settings.get('schedule_timezone', 'Europe/London'))
    current = (now or datetime.now(timezone.utc)).astimezone(tz)
    if mode == 'timed':
        start = parse_clock(settings.get('schedule_start', '20:00'))
        end = parse_clock(settings.get('schedule_end', '06:00'))
        if start == end:
            return False, 'Invalid schedule: start and end are identical'
        clock = current.time().replace(tzinfo=None)
        active = start <= clock < end if start < end else (clock >= start or clock < end)
        return active, 'Within scheduled hours' if active else 'Waiting for scheduled hours'
    if mode == 'solar':
        latitude = settings.get('latitude')
        longitude = settings.get('longitude')
        if latitude is None or longitude is None:
            return False, 'Sunset mode needs latitude and longitude'
        today = sun_times(current.date(), float(latitude), float(longitude), settings.get('schedule_timezone', 'Europe/London'))
        if today is None:
            return False, 'No ordinary sunrise/sunset today at this location'
        sunrise, sunset = today
        active = current < sunrise or current >= sunset
        return active, ('Night-time monitoring (sunset to sunrise)' if active
                        else 'Daytime — waiting for sunset')
    return False, 'Unknown operating mode; recording disabled'
