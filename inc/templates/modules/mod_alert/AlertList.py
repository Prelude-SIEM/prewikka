import sys
import urllib

import PyTpl
from templates import Table


class AlertList(PyTpl.Template):
    def setAlertList(self, content):
        self.ALERT_LIST = content

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
