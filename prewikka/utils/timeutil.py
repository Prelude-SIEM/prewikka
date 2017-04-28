from __future__ import absolute_import, division, print_function, unicode_literals

import calendar

from datetime import datetime
from dateutil import parser
from dateutil.tz import tzlocal, tzoffset, tzutc
from pytz import timezone


def now():
    return datetime.now(env.request.user.timezone)


def utcnow():
    return datetime.now(timezone("UTC"))


def get_timestamp_from_string(s):
    return calendar.timegm(parser.parse(s).timetuple()) if s else None


def get_timestamp_from_datetime(dt):
    return calendar.timegm(dt.utctimetuple())
