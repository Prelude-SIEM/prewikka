from __future__ import absolute_import, division, print_function, unicode_literals

from datetime import timedelta

from babel.core import Locale

from prewikka.localization import translation


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
                     add_direction=False, format='long',
                     locale=None):
    """Return a time delta according to the rules of the given locale.
    >>> format_timedelta(timedelta(weeks=12), locale='en_US')
    u'3 months'
    >>> format_timedelta(timedelta(seconds=1), locale='es')
    u'1 segundo'
    The granularity parameter can be provided to alter the lowest unit
    presented, which defaults to a second.
    >>> format_timedelta(timedelta(hours=3), granularity='day',
    ...                  locale='en_US')
    u'1 day'
    The threshold parameter can be used to determine at which value the
    presentation switches to the next higher unit. A higher threshold factor
    means the presentation will switch later. For example:
    >>> format_timedelta(timedelta(hours=23), threshold=0.9, locale='en_US')
    u'1 day'
    >>> format_timedelta(timedelta(hours=23), threshold=1.1, locale='en_US')
    u'23 hours'
    In addition directional information can be provided that informs
    the user if the date is in the past or in the future:
    >>> format_timedelta(timedelta(hours=1), add_direction=True, locale='en')
    u'in 1 hour'
    >>> format_timedelta(timedelta(hours=-1), add_direction=True, locale='en')
    u'1 hour ago'
    The format parameter controls how compact or wide the presentation is:
    >>> format_timedelta(timedelta(hours=3), format='short', locale='en')
    u'3 hr'
    >>> format_timedelta(timedelta(hours=3), format='narrow', locale='en')
    u'3h'
    :param delta: a ``timedelta`` object representing the time difference to
                  format, or the delta in seconds as an `int` value
    :param granularity: determines the smallest unit that should be displayed,
                        the value can be one of "year", "month", "week", "day",
                        "hour", "minute" or "second"
    :param threshold: factor that determines at which point the presentation
                      switches to the next higher unit
    :param add_direction: if this flag is set to `True` the return value will
                          include directional information.  For instance a
                          positive timedelta will include the information about
                          it being in the future, a negative will be information
                          about the value being in the past.
    :param format: the format, can be "narrow", "short" or "long". (
                   "medium" is deprecated, currently converted to "long" to
                   maintain compatibility)
    :param locale: a `Locale` object or a locale identifier
    """
    if format not in ('narrow', 'short', 'medium', 'long'):
        raise TypeError('Format must be one of "narrow", "short" or "long"')
    if format == 'medium':
        format = 'long'
    if isinstance(delta, timedelta):
        seconds = int((delta.days * 86400) + delta.seconds)
    else:
        seconds = delta
    if locale is None:
        locale = translation.getLocale()
    locale = Locale.parse(locale)

    def _iter_patterns(a_unit):
        if add_direction:
            unit_rel_patterns = locale._data['date_fields'][a_unit]
            if seconds >= 0:
                yield unit_rel_patterns['future']
            else:
                yield unit_rel_patterns['past']
        a_unit = 'duration-' + a_unit
        yield locale._data['unit_patterns'].get(a_unit, {}).get(format)

    for unit, secs_per_unit in TIMEDELTA_UNITS:
        value = abs(seconds) / secs_per_unit
        if value >= threshold or unit == granularity:
            if unit == granularity and value > 0:
                value = max(1, value)
            value = int(round(value))
            plural_form = locale.plural_form(value)
            pattern = None
            for patterns in _iter_patterns(unit):
                if patterns is not None:
                    pattern = patterns[plural_form]
                    break
            # This really should not happen
            if pattern is None:
                return u''
            return pattern.replace('{0}', str(value))

    return u''
