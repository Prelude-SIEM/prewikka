from __future__ import absolute_import, division, print_function, unicode_literals

import sys

if sys.version_info[0] >= 3:
    STRING_TYPES = str,
else:
    STRING_TYPES = basestring,
