from __future__ import absolute_import, division, print_function, unicode_literals

import sys

if sys.version_info[0] >= 3:
    import collections

    STRING_TYPES = str,
    OrderedDict = collections.OrderedDict
else:
    from .ordereddict import OrderedDict
    STRING_TYPES = basestring,


if sys.version_info < (2,7):
    def timedelta_total_seconds(td):
        return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6
else:
    def timedelta_total_seconds(td):
        return td.total_seconds()
