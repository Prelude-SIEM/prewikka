# Copyright (C) 2004 Nicolas Delon <nicolas@prelude-ids.org>
# All Rights Reserved
#
# This file is part of the Prelude program.
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


from prewikka import PyTpl
from prewikka import utils


class HeartbeatsAnalyze(PyTpl.Template):
    def __init__(self, number, value, error_tolerance):
        PyTpl.Template.__init__(self)
        self._number = number
        self._value = value
        self._error_tolerance = error_tolerance
        
    def addAnalyzer(self, analyzer, messages):
        self["analyzer"].ANALYZERID = analyzer["analyzerid"]
        self["analyzer"].TYPE = "%s %s" % (analyzer["model"], analyzer["version"])
        self["analyzer"].OS = "%s %s" % (analyzer["ostype"], analyzer["osversion"])
        self["analyzer"].NAME = analyzer["name"]
        self["analyzer"].LOCATION = analyzer["location"]
        self["analyzer"].ADDRESS = analyzer["address"]
        self["analyzer"].LAST_HEARTBEAT = utils.time_to_ymdhms(int(analyzer["last_heartbeat"]))
        for message in messages:
            self["analyzer"]["heartbeat_message"].CONTENT = message
            self["analyzer"]["heartbeat_message"].parse()
        self["analyzer"].parse()
