# Copyright (C) 2004-2015 CS-SI. All Rights Reserved.
# Author: Rob Holland <tigger@gentoo.org>

import Cheetah

from Cheetah.Filters import *
from prewikka import utils


class CleanOutput(Cheetah.Filters.Filter):
    def filter(self, val, **kw):
        s = Cheetah.Filters.Filter.filter(self, val, **kw)
        return utils.escape_html_string(s)
