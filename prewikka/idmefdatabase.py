# Copyright (C) 2004-2016 CS-SI. All Rights Reserved.
# Author: Yoann Vandoorselaere <yoannv@gmail.com>
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
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import time, types
import prelude, preludedb

from prewikka import hookmanager
from prewikka.utils import escape_html_string

class Message(object):
    def __init__(self, idmef, ident, htmlsafe=False):
        self._idmef = idmef
        self._htmlsafe = htmlsafe

    def _escape_idmef(self, obj):
        if isinstance(obj, prelude.IDMEF):
            return Message(obj, self.ident, htmlsafe=True)

        elif isinstance(obj, str):
            return escape_html_string(obj)

        elif isinstance(obj, tuple):
            return tuple((self._escape_idmef(o) for o in obj))

        return obj

    def get(self, default=None, htmlsafe=False):
        try:
            if htmlsafe or self._htmlsafe:
                return self._escape_idmef(self._idmef.get(default))
            else:
                return self._idmef.get(default)
        except IndexError as exc:
            return default

    def __getitem__(self, k):
       return self.get(k)


class IDMEFDatabase(preludedb.DB):
    def __init__(self, config):
        sql = preludedb.SQL(dict((k, str(v)) for k, v in config.items()))
        preludedb.DB.__init__(self, sql)
