import re
from datetime import datetime, timedelta, tzinfo


ISO8601_RE = re.compile(r"""
    (?P<YYYY>\d{2,4})
    (?:-?(?P<MM>[01]\d))?
    (?:-?(?P<DD>[0-3]\d))?
    (?:T
        (?P<hh>[0-2]\d)
        (?::?(?P<mm>[0-5]\d))?
        (?::?(?P<ss>[0-5]\d))?
        (?:[,.](?P<s>\d+))?
    )?
    (?P<TZD>Z|
        (?P<zh>[+-][0-2]\d)
        (?::?(?P<zm>[0-5]\d))?
    )?
    """, re.X
)

def to_int(str_or_none, default=0):
    if str_or_none is not None:
        return int(str_or_none)
    return default

def parse_iso8601(string):
    match = ISO8601_RE.match(string)
    if match is None:
        raise ValueError("Invalid ISO 8601 timestamp")
    d = match.groupdict()
    year, month, day = d['YYYY'], d['MM'], d['DD']
    hour, minute, second, fraction = d['hh'], d['mm'], d['ss'], d['s']
    zone, zone_hours, zone_minutes = d['TZD'], d['zh'], d['zm']
    if zone:
        if zone == 'Z':
            tz = TimeZone("UTC")
        else:
            hours = to_int(zone_hours, 0)
            minutes = to_int(zone_minutes, 0) * -int(hours < 0)
            tz = TimeZone(zone, timedelta(hours=hours, minutes=minutes))
    else:
        tz = None
    timestamp = datetime(
        int(year), to_int(month, 1), to_int(day, 1),
        to_int(hour, 0), to_int(minute, 0), to_int(second, 0), tzinfo=tz
    )
    fraction = fraction and float('.' + fraction) or 0
    if fraction:
        if second is not None:
            timestamp += timedelta(seconds=fraction)
        elif minute is not None:
            timestamp += timedelta(minutes=fraction)
        elif hour is not None:
            timestamp += timedelta(hours=fraction)
    return timestamp

class TimeZone(tzinfo):
    def __init__(self, name, offset=timedelta(0)):
        self.__name = name
        self.__offset = offset
    
    def utcoffset(self, dt):
        return self.__offset
    
    def tzname(self, dt):
        return self.__name
    
    def dst(self, dt):
        return timedelta(0)
