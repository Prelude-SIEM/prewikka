# Copyright (C) 2004-2016 CS-SI. All Rights Reserved.
# Author: Rob Holland <tigger@gentoo.org>

import Cheetah

from Cheetah.Filters import *
from prewikka import utils


class CleanOutput(Cheetah.Filters.Filter):
    def filter(self, val, **kw):
        s = Cheetah.Filters.Filter.filter(self, val, **kw)
        return utils.escape_html_string(s)


class JSONOutput(Cheetah.Filters.Filter):
    def filter(self, val, **kw):
        # If a JS string contains "</script>", it will be interpreted as a closing tag.
        # See http://stackoverflow.com/questions/1659749/script-tag-in-javascript-string
        s = Cheetah.Filters.Filter.filter(self, val, **kw)
        return s.replace("</script>", "<\\/script>")
