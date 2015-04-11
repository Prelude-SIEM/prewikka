from babel.core import Locale
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

    def _iter_choices(unit):
        if add_direction:
            if seconds >= 0:
                yield unit + '-future'
            else:
                yield unit + '-past'
        yield unit + ':' + format
        yield unit

    for unit, secs_per_unit in TIMEDELTA_UNITS:
        value = abs(seconds) / secs_per_unit
        if value >= threshold or unit == granularity:
            if unit == granularity and value > 0:
                value = max(1, value)
            value = int(round(value))

            return u"%d %s ago" % (value, unit)

    return u''
