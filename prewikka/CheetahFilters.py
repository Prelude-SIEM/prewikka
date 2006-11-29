# Copyright (C) 2004,2005 PreludeIDS Technologies. All Rights Reserved.
# Author: Rob Holland <tigger@gentoo.org>
#
# This file is part of the Prewikka program.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING.  If not, write to
# the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.


import Cheetah
import prelude

from Cheetah.Filters import *
from prewikka import utils


class CleanOutput(Cheetah.Filters.Filter):
    def filter(self, val, **kw):
        s = Filter.filter(self, val, **kw)
        return utils.escape_html_string(s)
