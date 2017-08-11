from __future__ import absolute_import, division, print_function, unicode_literals

from datetime import timedelta

TIMEDELTA_UNITS = (
    ('year',   3600 * 24 * 365),
    ('month',  3600 * 24 * 30),
    ('week',   3600 * 24 * 7),
    ('day',    3600 * 24),
    ('hour',   3600),
    ('minute', 60),
    ('second', 1)
)


def format_timedelta(delta, granularity='second', threshold=.85,
                     add_direction=False, format='medium',
                     locale=""):
    if format not in ('short', 'medium'):
        raise TypeError('Format can only be one of "short" or "medium"')
    if isinstance(delta, timedelta):
        seconds = int((delta.days * 86400) + delta.seconds)
    else:
        seconds = delta

    for unit, secs_per_unit in TIMEDELTA_UNITS:
        value = abs(seconds) / secs_per_unit
        if value >= threshold or unit == granularity:
            if unit == granularity and value > 0:
                value = max(1, value)
            value = int(round(value))

            if not add_direction:
                return u"%d %s" % (value, unit)

            elif seconds >= 0:
                return u"in %d %s" % (value, unit)

            else:
                return u"%d %s ago" % (value, unit)

    return u''
