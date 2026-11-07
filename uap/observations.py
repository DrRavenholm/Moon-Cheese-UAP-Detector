"""Calendar and report summaries based on actual saved recordings."""
import calendar
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from common import connection
from trigger_logic import SOURCE_LABELS


def timezone_for(value):
    try:
        return ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        return timezone.utc


def day_range(day, timezone_name):
    tz = timezone_for(timezone_name)
    start = datetime.combine(day, time.min, tzinfo=tz).astimezone(timezone.utc)
    end = datetime.combine(day + timedelta(days=1), time.min, tzinfo=tz).astimezone(timezone.utc)
    return start, end


def recordings_between(start, end):
    # Includes ISO forms with fractional seconds and/or Z suffixes; convert to datetime
    # to avoid relying on inconsistent textual datetime sorting in older releases.
    # Bounding by the UTC dates first would be faster but could omit offset formats.
    with connection() as db:
        rows = db.execute('SELECT id,time_utc,kind,status,trigger_source,thumbnail,video,pinned,public FROM events WHERE video IS NOT NULL AND demo=0 ORDER BY id DESC').fetchall()
    out=[]
    for row in rows:
        try:
            moment = datetime.fromisoformat(row['time_utc'].replace('Z','+00:00'))
            if moment.tzinfo is None:
                moment = moment.replace(tzinfo=timezone.utc)
            if start <= moment.astimezone(timezone.utc) < end:
                out.append(dict(row))
        except (ValueError, TypeError):
            continue
    return out


def summarize(rows):
    return dict(total=len(rows),
                statuses=dict(Counter(r['status'] for r in rows)),
                triggers=dict(Counter(SOURCE_LABELS.get(r['trigger_source'], 'Not recorded') for r in rows)),
                public=sum(bool(r.get('public')) for r in rows),
                pinned=sum(bool(r.get('pinned')) for r in rows))


def calendar_month(year, month, timezone_name):
    first=date(year,month,1)
    last=date(year,month,calendar.monthrange(year,month)[1])
    start,_ = day_range(first, timezone_name)
    _,end = day_range(last, timezone_name)
    tz=timezone_for(timezone_name)
    counts=Counter()
    for row in recordings_between(start,end):
        moment=datetime.fromisoformat(row['time_utc'].replace('Z','+00:00'))
        if moment.tzinfo is None: moment=moment.replace(tzinfo=timezone.utc)
        counts[moment.astimezone(tz).day]+=1
    return counts
