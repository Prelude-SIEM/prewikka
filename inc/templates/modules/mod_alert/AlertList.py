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

    def setPrevQuery(self, query):
        self.PREV_QUERY = query

    def setNextQuery(self, query):
        self.NEXT_QUERY = query

    def setCurrentQuery(self, query):
        self.CURRENT_QUERY = query

    def addHidden(self, name, value):
        self["hidden"].NAME = name
        self["hidden"].VALUE = value
        self["hidden"].parse()
