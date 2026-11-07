"""UTC storage; detector-local presentation and validated wall-clock scheduling."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def valid_zone(name):
    try:
        if not isinstance(name, str) or not name.strip():
            raise ValueError('Missing time zone')
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError, TypeError) as exc:
        raise ValueError('Choose a valid IANA time zone in Settings.') from exc


def schedule_utc(wall_time, zone_name):
    """No silent guesses at nonexistent or twice-occurring DST clock times."""
    zone = valid_zone(zone_name)
    try:
        naive = datetime.strptime(str(wall_time), '%Y-%m-%dT%H:%M')
    except (ValueError, TypeError) as exc:
        raise ValueError('Enter a date and time in the detector’s local time zone.') from exc
    possible = []
    for fold in (0, 1):
        aware = naive.replace(tzinfo=zone, fold=fold)
        result = aware.astimezone(timezone.utc)
        if result.astimezone(zone).replace(tzinfo=None) == naive:
            possible.append(result)
    if not possible:
        raise ValueError('This local time does not exist because the clocks change. Choose a different time.')
    if possible[0] != possible[-1]:
        raise ValueError('This local time occurs twice when the clocks change. Choose an unambiguous time.')
    return possible[0]


def local_label(instant, zone_name='Europe/London', date_only=False):
    if instant is None or instant == '': return '—'
    try:
        if isinstance(instant, datetime):
            parsed=instant
        else:
            parsed=datetime.fromisoformat(str(instant).replace('Z','+00:00'))
        # Existing records with no suffix are historic UTC timestamps.
        if parsed.tzinfo is None: parsed=parsed.replace(tzinfo=timezone.utc)
        here=parsed.astimezone(valid_zone(zone_name))
        return here.strftime('%d %b %Y' if date_only else '%d %b %Y, %H:%M:%S %Z')
    except (ValueError, TypeError, OverflowError):
        return 'Unknown time'
