from __future__ import absolute_import, division, print_function, unicode_literals

import calendar

from datetime import datetime, timedelta
from dateutil import parser
from dateutil.tz import tzlocal, tzoffset, tzutc  # noqa: imported but unused
from pytz import timezone


_TRUNCATE_VALUES = ["year", "month", "day", "hour", "minute", "second", "microsecond"]


def now():
    return datetime.now(env.request.user.timezone)


def utcnow():
    return datetime.now(timezone("UTC"))


def truncate(dtime, timeunit):
    if timeunit == 'week':
        from prewikka import localization  # avoid circular imports
        days_to_remove = (dtime.weekday() - localization.get_first_week_day()) % 7
        return dtime.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_to_remove)

    d = {}

    idx = _TRUNCATE_VALUES.index(timeunit) + 1
    for i, unit in enumerate(_TRUNCATE_VALUES[idx:]):
        d[unit] = 1 if idx + i <= 2 else 0  # months and days start from 1, hour/min/sec start from 0

    return dtime.replace(**d)


def get_timestamp_from_string(s):
    return calendar.timegm(parser.parse(s).timetuple()) if s else None


def get_timestamp_from_datetime(dt):
    return calendar.timegm(dt.utctimetuple())
