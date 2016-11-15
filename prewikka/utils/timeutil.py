from __future__ import absolute_import, division, print_function, unicode_literals

import calendar

from dateutil import parser
from dateutil.tz import tzlocal, tzoffset, tzutc
from pytz import timezone


def get_timestamp_from_string(s):
    return calendar.timegm(parser.parse(s).timetuple()) if s else None
