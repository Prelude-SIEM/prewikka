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
import time
import copy

from prewikka import Views
from prewikka.modules.main import ActionParameters
from prewikka.templates import Table
from prewikka.modules.main.templates import MessageListing, MessageSummary, MessageDetails,\
     HeartbeatsAnalyze
from prewikka import utils

def Actions():
    # workaround: we cannot do a simple "from modules.main import Actions" statement
    # because Actions imports View, which means that we would have an indirect recursive
    # module import (View -> Actions -> View -> ...)
    # TODO: find a cleaner way to solve this problem
    import prewikka.modules.main.Actions
    return prewikka.modules.main.Actions



class AlertsSection(Views.NormalView):
    def init(self):
        Views.NormalView.init(self)
        self.setActiveSection("Alerts")
        self.setTabs([ ("Alerts", Actions().AlertListing()) ])
        self.setActiveTab("Alerts")



class HeartbeatsSection(Views.NormalView):
    def init(self):
        Views.NormalView.init(self)
        self.setActiveSection("Heartbeats")
        self.setTabs([ ("Analyze", Actions().HeartbeatsAnalyze()), ("List", Actions().HeartbeatListing()) ])



class HeartbeatsAnalyzeTab(HeartbeatsSection):
    def init(self):
        HeartbeatsSection.init(self)
        self.setActiveTab("Analyze")



class HeartbeatListingTab(HeartbeatsSection):
    def init(self):
        HeartbeatsSection.init(self)
        self.setActiveTab("List")
    


class MessageListingView:
    def _createLinkTag(self, action, parameters, name, class_=""):
        return "<a class='%s' href='%s'>%s</a>" % (class_, self.createLink(action, parameters), name)
    
    def _createMessageLink(self, message, name, action):
        parameters = ActionParameters.Message()
        parameters.setAnalyzerid(message["analyzer.analyzerid"])
        parameters.setMessageIdent(message["ident"])
        
        return "<a href='%s'>%s</a>" % (self.createLink(action, parameters), name)
    
    def _createDeleteLink(self, message):
        return "<input type='checkbox' name='idents' value='%d:%d'/>" % \
               (message["analyzer.analyzerid"], message["ident"])
    
    def _addMessageField(self, row, message, field, filter_name=None, class_="alert_field_value"):
        if filter_name is None:
            filter_name = field
        
        value = message[field]
        if value:
            parameters = copy.copy(self._data["parameters"])
            parameters.setFilterName(filter_name)
            parameters.setFilterValue(value)
            field = self._createLinkTag(self._getMessageListingAction(), parameters, value, class_)
        else:
            field = "n/a"
            
        row.append(field)
        
    def _createMessageTime(self, t):
        if not t:
            return "n/a"
        
        t = time.localtime(t)
        current = time.localtime()
        
        if t[:3] == current[:3]: # message time is today
            return utils.time_to_hms(t)
        
        return utils.time_to_ymdhms(t)
    
    def _buildEdition(self, template):
        # build step form
        template.addHidden("action", self._getMessageListingAction().getId())
        for key in self._data["parameters"].getNames(ignore=("timeline_value", "timeline_unit")):
            template.addHidden(key, self._data["parameters"][key])
        template.setTimelineValue(self._data["parameters"].getTimelineValue() or 1)
        template.setTimelineUnit(self._data["parameters"].getTimelineUnit() or "hour")
        
        # build "from" date
        template.setTimelineStart(str(self._data["start"]))
        
        # build "to" date
        template.setTimelineEnd(str(self._data["end"]))
        
        # build "current" link
        parameters = copy.copy(self._data["parameters"])
        if parameters.getTimelineEnd():
            del parameters["timeline_end"]
        template.setCurrent(self.createLink(self._getMessageListingAction(), parameters))
        
        # build "next" link
        parameters.setTimelineEnd(int(self._data["next"]))
        template.setNext(self.createLink(self._getMessageListingAction(), parameters))
        
        # build "prev" link
        parameters.setTimelineEnd(int(self._data["prev"]))
        template.setPrev(self.createLink(self._getMessageListingAction(), parameters))
        
    def _buildMessageListing(self, template):
        messages = self._data["messages"]
        table = Table.Table()
        footer = [ "" ] * 8
        
        table.setHeader(self.HEADER + ("", ) * 3)
        for message in messages:
            self._addMessage(table, message)
            
        if self._data["parameters"].getFilterName():
            parameters = copy.copy(self._data["parameters"])
            filter_name = parameters["filter_name"]
            del parameters["filter_name"]
            del parameters["filter_value"]
            footer[self.FILTERS.index(filter_name)] = self._createLinkTag(self._getMessageListingAction(), parameters,
                                                                          "del filter")
            
        template.addDeleteHidden("action", self._getDeleteAction().getId())
        parameters = self._data["parameters"]
        for name in parameters.getNames(ignore=("idents", )):
            template.addDeleteHidden(name, parameters[name])
        
        footer[-1] = "<input type='submit' value='delete'/>"
        table.setFooter(footer)
        
        template.setMessageListing(str(table))
        
    def build(self):
        template = MessageListing.MessageListing()
        self._buildEdition(template)
        self._buildMessageListing(template)
        self.setMainContent(str(template))



class AlertListingView(MessageListingView, AlertsSection):
    ROOT = "alert"
    HEADER = "Classification", "Source", "Target", "Sensor", "Time"
    FILTERS = [ "alert.classification.name", "alert.source.node.address.address", "alert.target.node.address.address",
                "alert.analyzer.model" ]
    
    def _getMessageListingAction(self):
        return Actions().AlertListing()
    
    def _getDeleteAction(self):
        return Actions().DeleteAlerts()
    
    def _addMessage(self, table, alert):
        row = [ ]
        
        impact_severity = "impact_severity_" + (alert["assessment.impact.severity"] or "low")
        self._addMessageField(row, alert, "classification(0).name", "alert.classification.name", class_=impact_severity)
        self._addMessageField(row, alert, "source(0).node.address(0).address", "alert.source.node.address.address")
        self._addMessageField(row, alert, "target(0).node.address(0).address", "alert.target.node.address.address")
        self._addMessageField(row, alert, "analyzer.model", "alert.analyzer.model")
        row.append(self._createMessageTime(alert["detect_time"] or alert["create_time"]))
        row.append(self._createMessageLink(alert, "summary", Actions().AlertSummary()))
        row.append(self._createMessageLink(alert, "details", Actions().AlertDetails()))
        row.append(self._createDeleteLink(alert))
        
        table.addRow(row)



class HeartbeatListingView(MessageListingView, HeartbeatListingTab):
    ROOT = "heartbeat"
    HEADER = "Analyzerid", "Address", "Name", "Type", "Time"
    FILTERS = [ "heartbeat.analyzer.analyzerid", "heartbeat.analyzer.node.address.address", "heartbeat.analyzer.node.name",
                "heartbeat.analyzer.model", "heartbeat.create_time" ]

    def _getMessageListingAction(self):
        return Actions().HeartbeatListing()

    def _getDeleteAction(self):
        return Actions().DeleteHeartbeats()

    def _addMessage(self, table, heartbeat):
        row = [ ]
        
        self._addMessageField(row, heartbeat, "analyzer.analyzerid", "heartbeat.analyzer.analyzerid")
        self._addMessageField(row, heartbeat, "analyzer.node.address(0).address", "heartbeat.analyzer.node.address.address")
        self._addMessageField(row, heartbeat, "analyzer.node.name", "heartbeat.analyzer.node.name")
        self._addMessageField(row, heartbeat, "analyzer.model", "heartbeat.analyzer.model")
        row.append(self._createMessageTime(heartbeat["create_time"]))
        row.append(self._createMessageLink(heartbeat, "summary", Actions().HeartbeatSummary()))
        row.append(self._createMessageLink(heartbeat, "details", Actions().HeartbeatDetails()))
        row.append(self._createDeleteLink(heartbeat))
        
        table.addRow(row)



class AlertSummaryView(AlertsSection):
    def build(self):
        self.setMainContent(MessageSummary.AlertSummary(self._data))



class HeartbeatSummaryView(HeartbeatListingTab):
    def build(self):
        self.setMainContent(MessageSummary.HeartbeatSummary(self._data))



class AlertDetailsView(AlertsSection):
    def build(self):
        self.setMainContent(MessageDetails.AlertDetails(self._data))



class HeartbeatDetailsView(HeartbeatListingTab):
    def build(self):
        self.setMainContent(MessageDetails.HeartbeatDetails(self._data))



class HeartbeatsAnalyzeView(HeartbeatsAnalyzeTab):
    def _createErrorMessage(self, error):
        if error["type"] == "sooner":
            delta = error["delta"]
            hours = delta / 3600
            mins = (delta - hours * 3600) / 60
            secs = delta % 60
            return "Sensor was restarted prematurely on %s (after %02d:%02d:%02d %d)" % \
                   (utils.time_to_ymdhms(int(error["date"])), hours, mins, secs, delta)
        # later
        return "Sensor went down after %s and went back online on %s" % (str(error["after"]), str(error["back"]))
        
    
    def build(self):
        template = HeartbeatsAnalyze.HeartbeatsAnalyze(self._data["heartbeat_number"],
                                                       self._data["heartbeat_value"],
                                                       self._data["heartbeat_error_tolerance"])
        
        for analyzer in self._data["analyzers"]:
            messages = [ ]
            for error in analyzer["errors"]:
                message = self._createErrorMessage(error)
                messages.append(message)
            template.addAnalyzer(analyzer, messages)
        
        self.setMainContent(str(template))
