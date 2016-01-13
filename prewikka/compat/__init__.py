import sys
from ordereddict import *

if sys.version_info[0] >= 3:
    STRING_TYPES = str,
else:
    STRING_TYPES = basestring,
