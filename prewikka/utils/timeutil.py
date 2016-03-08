from pytz import timezone
from dateutil import parser
from dateutil.tz import tzutc, tzoffset, tzlocal

import calendar

def get_timestamp_from_string(s):
    return calendar.timegm(parser.parse(s).timetuple()) if s else None
