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


import sys
import os

import copy
import urllib
import cgi

from prewikka import Views, Log


class ConfigView:
    def __init__(self, core):
        self.active_section = "Configuration"
        self.tabs = core.interface._configuration



class Interface:
    def __init__(self, core, config):
        self._sections = [ ]
        self._quick_accesses = [ ]
        self._software = config.getOptionValue("software", "Prewikka")
        self._place = config.getOptionValue("place", "")
        self._title = config.getOptionValue("title", "Prelude management")
        self._configuration = [ ]

    def registerQuickAccess(self, name, action, parameters):
        self._quick_accesses.append((name, action, parameters))

    def getQuickAccesses(self):
        return self._quick_accesses

    def getSections(self):
        return self._sections

    def getSoftware(self):
        return self._software

    def getPlace(self):
        return self._place

    def getTitle(self):
        return self._title

    def registerSection(self, name, action):
        self._sections.append((name, action))

    def registerConfigurationSection(self, name, action):
        if not self._configuration:
            self.registerSection("Configuration", action)
        self._configuration.append((name, action))
