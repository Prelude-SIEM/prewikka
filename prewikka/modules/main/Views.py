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
    def __init__(self, core):
        Views.NormalView.__init__(self, core)
        self.setActiveSection("Alerts")
        self.setTabs([ ("Alerts", Actions().AlertListing()) ])
        self.setActiveTab("Alerts")



class HeartbeatsSection(Views.NormalView):
    def __init__(self, core):
        Views.NormalView.__init__(self, core)
        self.setActiveSection("Heartbeats")
        self.setTabs([ ("Analyze", Actions().HeartbeatsAnalyze()), ("List", Actions().HeartbeatListing()) ])



class HeartbeatsAnalyzeTab(HeartbeatsSection):
    def __init__(self, core):
        HeartbeatsSection.__init__(self, core)
        self.setActiveTab("Analyze")



class HeartbeatListingTab(HeartbeatsSection):
    def __init__(self, core):
        HeartbeatsSection.__init__(self, core)
        self.setActiveTab("List")



class SensorsSection(Views.NormalView):
    def __init__(self, core):
        Views.NormalView.__init__(self, core)
        self.setActiveSection("Sensors")
        self.setTabs([ ("Sensors", Actions().SensorListing()) ])
        self.setActiveTab("Sensors")



class MessageListingView:
    def _createLinkTag(self, action, parameters, name, class_=""):
        return "<a class='%s' href='%s'>%s</a>" % (class_, self.createLink(action, parameters), name)
    
    def _createMessageLink(self, message, name, action):
        parameters = ActionParameters.Message(self.core.log)
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
            parameters = copy.copy(self.data["parameters"])
            parameters.setFilterName(filter_name)
            parameters.setFilterValue(value)
            field = self._createLinkTag(self._getMessageListingAction(), parameters, value, class_)
        else:
            field = "n/a"
            
        row.append(field)
        
    def _createMessageTime(self, t):
        if not t:
            return "n/a"
        
        tmp = time.localtime(t)
        current = time.localtime()
        
        if tmp[:3] == current[:3]: # message time is today
            return utils.time_to_hms(t)
        
        return utils.time_to_ymdhms(t)
    
    def _buildEdition(self, template):
        # build step form
        template.addHidden("action", self._getMessageListingAction().getId())
        for key in self.data["parameters"].getNames(ignore=("timeline_value", "timeline_unit")):
            template.addHidden(key, self.data["parameters"][key])
        template.setTimelineValue(self.data["parameters"].getTimelineValue() or 1)
        template.setTimelineUnit(self.data["parameters"].getTimelineUnit() or "hour")
        
        # build "from" date
        template.setTimelineStart(str(self.data["start"]))
        
        # build "to" date
        template.setTimelineEnd(str(self.data["end"]))
        
        # build "current" link
        parameters = copy.copy(self.data["parameters"])
        if parameters.getTimelineEnd():
            del parameters["timeline_end"]
        template.setCurrent(self.createLink(self._getMessageListingAction(), parameters))
        
        # build "next" link
        parameters.setTimelineEnd(int(self.data["next"]))
        template.setNext(self.createLink(self._getMessageListingAction(), parameters))
        
        # build "prev" link
        parameters.setTimelineEnd(int(self.data["prev"]))
        template.setPrev(self.createLink(self._getMessageListingAction(), parameters))
        
    def _buildMessageListing(self, template):
        messages = self.data["messages"]
        table = Table.Table()
        footer = [ "" ] * 8
        
        table.setHeader(self.HEADER + ("", ) * 3)
        for message in messages:
            row = [ ]
            self._addMessageFields(row, message)
            row.append(self._createMessageLink(message, "summary", self._getMessageSummaryAction()))
            row.append(self._createMessageLink(message, "details", self._getMessageDetailsAction()))
            row.append(self._createDeleteLink(message))
            
            table.addRow(row)
            
        if self.data["parameters"].getFilterName():
            parameters = copy.copy(self.data["parameters"])
            filter_name = parameters["filter_name"]
            del parameters["filter_name"]
            del parameters["filter_value"]
            footer[self.FILTERS.index(filter_name)] = self._createLinkTag(self._getMessageListingAction(), parameters,
                                                                          "del filter")
            
        template.addDeleteHidden("action", self._getDeleteAction().getId())
        parameters = self.data["parameters"]
        for name in parameters.getNames(ignore=("idents", )):
            template.addDeleteHidden(name, parameters[name])
        
        footer[-1] = "<input type='submit' value='delete'/>"
        table.setFooter(footer)
        
        template.setMessageListing(str(table))
        
    def buildMainContent(self, data):
        self.data = data
        template = MessageListing.MessageListing()
        self._buildEdition(template)
        self._buildMessageListing(template)
        
        return str(template)



class AlertListingView(MessageListingView, AlertsSection):
    ROOT = "alert"
    HEADER = "Classification", "Source", "Target", "Sensor", "Time"
    FILTERS = [ "alert.classification.name", "alert.source.node.address.address", "alert.target.node.address.address",
                "alert.analyzer.model" ]
    
    def _getMessageListingAction(self):
        return Actions().AlertListing()
    
    def _getDeleteAction(self):
        return Actions().DeleteAlerts()

    def _getMessageSummaryAction(self):
        return Actions().AlertSummary()
    
    def _getMessageDetailsAction(self):
        return Actions().AlertDetails()
    
    def _addMessageFields(self, row, alert):
        impact_severity = "impact_severity_" + (alert["assessment.impact.severity"] or "low")
        self._addMessageField(row, alert, "classification(0).name", "alert.classification.name", class_=impact_severity)
        self._addMessageField(row, alert, "source(0).node.address(0).address", "alert.source.node.address.address")
        self._addMessageField(row, alert, "target(0).node.address(0).address", "alert.target.node.address.address")
        self._addMessageField(row, alert, "analyzer.model", "alert.analyzer.model")
        row.append(self._createMessageTime(alert["detect_time"] or alert["create_time"]))



class HeartbeatListingView(MessageListingView, HeartbeatListingTab):
    ROOT = "heartbeat"
    HEADER = "Analyzerid", "Address", "Name", "Type", "Time"
    FILTERS = [ "heartbeat.analyzer.analyzerid", "heartbeat.analyzer.node.address.address", "heartbeat.analyzer.node.name",
                "heartbeat.analyzer.model", "heartbeat.create_time" ]

    def _getMessageListingAction(self):
        return Actions().HeartbeatListing()

    def _getDeleteAction(self):
        return Actions().DeleteHeartbeats()

    def _getMessageSummaryAction(self):
        return Actions().HeartbeatSummary()

    def _getMessageDetailsAction(self):
        return Actions().HeartbeatDetails()
    
    def _addMessageFields(self, row, heartbeat):
        self._addMessageField(row, heartbeat, "analyzer.analyzerid", "heartbeat.analyzer.analyzerid")
        self._addMessageField(row, heartbeat, "analyzer.node.address(0).address", "heartbeat.analyzer.node.address.address")
        self._addMessageField(row, heartbeat, "analyzer.node.name", "heartbeat.analyzer.node.name")
        self._addMessageField(row, heartbeat, "analyzer.model", "heartbeat.analyzer.model")
        row.append(self._createMessageTime(heartbeat["create_time"]))



class AlertSummaryView(AlertsSection):
    def buildMainContent(self, data):
        return str(MessageSummary.AlertSummary(data))



class HeartbeatSummaryView(HeartbeatListingTab):
    def buildMainContent(self, data):
        return str(MessageSummary.HeartbeatSummary(data))



class AlertDetailsView(AlertsSection):
    def buildMainContent(self, data):
        return str(MessageDetails.AlertDetails(data))



class HeartbeatDetailsView(HeartbeatListingTab):
    def buildMainContent(self, data):
        return str(MessageDetails.HeartbeatDetails(data))



class HeartbeatsAnalyzeView(HeartbeatsAnalyzeTab):
    def _createErrorMessage(self, error):
        if error["type"] == "sooner":
            delta = error["delta"]
            hours = delta / 3600
            mins = (delta - hours * 3600) / 60
            secs = delta % 60
            return "Sensor was restarted prematurely on %s (after %02d:%02d:%02d)" % \
                   (utils.time_to_ymdhms(int(error["date"])), hours, mins, secs)
        # later
        return "Sensor went down after %s and went back online on %s" % (str(error["after"]), str(error["back"]))
    
    def buildMainContent(self, data):
        template = HeartbeatsAnalyze.HeartbeatsAnalyze(data["heartbeat_number"],
                                                       data["heartbeat_value"],
                                                       data["heartbeat_error_tolerance"])
        
        for analyzer in data["analyzers"]:
            messages = [ ]
            for error in analyzer["errors"]:
                message = self._createErrorMessage(error)
                messages.append(message)
            template.addAnalyzer(analyzer, messages)
            
        return str(template)



class SensorMessageListingView(SensorsSection):
    def buildAnalyzerHeader(self, analyzer):
        table = Table.Table()
        table.setHeader(("Analyzerid", "Type", "OS", "Name", "Location", "Address"))
        table.addRow((analyzer["analyzerid"],
                      "%s %s" % (analyzer["model"], analyzer["version"]),
                      "%s %s" % (analyzer["ostype"], analyzer["osversion"]),
                      analyzer["name"],
                      analyzer["location"],
                      analyzer["address"]))
        
        return str(table)
        
        


class SensorAlertListingView(SensorMessageListingView, AlertListingView):
    def _getMessageListingAction(self):
        return Actions().SensorAlertListing()

    def _getDeleteAction(self):
        return Actions().SensorDeleteAlerts()

    def _getMessageSummaryAction(self):
        return Actions().SensorAlertSummary()

    def _getMessageDetailsAction(self):
        return Actions().SensorAlertDetails()
    
    def buildMainContent(self, data):
        return self.buildAnalyzerHeader(data["analyzer"]) + "<br/>" + AlertListingView.buildMainContent(self, data["alerts"])



class SensorHeartbeatListingView(SensorMessageListingView, HeartbeatListingView):
    def _getMessageListingAction(self):
        return Actions().SensorHeartbeatListing()

    def _getDeleteAction(self):
        return Actions().SensorDeleteHeartbeats()

    def _getMessageSummaryAction(self):
        return Actions().SensorHeartbeatSummary()

    def _getMessageDetailsAction(self):
        return Actions().SensorHeartbeatDetails()
    
    def buildMainContent(self, data):
        return self.buildAnalyzerHeader(data["analyzer"]) + "<br/>" + HeartbeatListingView.buildMainContent(self, data["heartbeats"])



class SensorAlertSummaryView(SensorsSection, AlertSummaryView):
    pass



class SensorAlertDetailsView(SensorsSection, AlertDetailsView):
    pass



class SensorHeartbeatSummaryView(SensorsSection, HeartbeatSummaryView):
    pass



class SensorHeartbeatDetailsView(SensorsSection, HeartbeatDetailsView):
    pass



class SensorListingView(MessageListingView, SensorsSection):
    def buildMainContent(self, analyzers):
        table = Table.Table()
        
        table.setHeader(("Analyzerid", "Type", "OS", "Name", "Location", "Address", "", ""))
        
        for analyzer in analyzers:
            parameters = ActionParameters.SensorMessageListing(self.core.log)
            parameters.setAnalyzerid(analyzer["analyzerid"])
            table.addRow((analyzer["analyzerid"],
                          "%s %s" % (analyzer["model"], analyzer["version"]),
                          "%s %s" % (analyzer["ostype"], analyzer["osversion"]),
                          analyzer["name"],
                          analyzer["location"],
                          analyzer["address"],
                          self._createLinkTag(Actions().SensorAlertListing(), parameters, "alerts"),
                          self._createLinkTag(Actions().SensorHeartbeatListing(), parameters, "heartbeats")))
            
        return str(table)
