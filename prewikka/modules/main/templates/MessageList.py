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
import urllib

from prewikka import PyTpl
from prewikka.templates import Table


class MessageList(PyTpl.Template):
    def setMessageList(self, content):
        self.MESSAGE_LIST = content
        
    def setTimelineValue(self, value):        
        self.TIMELINE_VALUE = value

    def setTimelineUnit(self, unit):
        setattr(self, unit.upper() + "_SELECTED", "selected")

    def setTimelineStart(self, start):
        self.TIMELINE_START = start

    def setTimelineEnd(self, end):
        self.TIMELINE_END = end

    def setPrev(self, prev):
        self.PREV = prev

    def setNext(self, next):
        self.NEXT = next

    def setCurrent(self, current):
        self.CURRENT = current

    def addHidden(self, name, value):
        self["hidden"].NAME = name
        self["hidden"].VALUE = value
        self["hidden"].parse()

    def addDeleteHidden(self, name, value):
        self["delete_hidden"].NAME = name
        self["delete_hidden"].VALUE = value
        self["delete_hidden"].parse()
