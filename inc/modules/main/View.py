import sys
import time
import copy

import Views
from modules.main import ActionParameters
from inc.templates import Table
from modules.main.templates import MessageList, MessageSummary, MessageDetails

def Actions():
    # workaround: we cannot do a simple "from modules.main import Actions" statement
    # because Actions imports View, which means that we would have an indirect recursive
    # module import (View -> Actions -> View -> ...)
    # TODO: find a cleaner way to solve this problem
    import modules.main.Actions
    return modules.main.Actions



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
        self.setTabs([ ("Heartbeats", Actions().HeartbeatListing()) ])
        self.setActiveTab("Heartbeats")



class MessageListing:
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
            field = self._createLinkTag(self._getMessageListAction(), parameters, value, class_)
        else:
            field = "n/a"
            
        row.append(field)
        
    def _createMessageTime(self, t):
        if not t:
            return "n/a"
        
        t = time.localtime(t)
        current = time.localtime()
        
        if t[:3] == current[:3]: # message time is today
            format = "%H:%M:%S"
        else:
            format = "%Y-%m-%d %H:%M:%S"
        
        return time.strftime(format, t)

    def _buildEdition(self, template):
        # build step form
        template.addHidden("action", self._getMessageListAction().getId())
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
        template.setCurrent(self.createLink(self._getMessageListAction(), parameters))
        
        # build "next" link
        parameters.setTimelineEnd(int(self._data["next"]))
        template.setNext(self.createLink(self._getMessageListAction(), parameters))
        
        # build "prev" link
        parameters.setTimelineEnd(int(self._data["prev"]))
        template.setPrev(self.createLink(self._getMessageListAction(), parameters))
        
    def _buildMessageList(self, template):
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
            footer[self.FILTERS.index(filter_name)] = self._createLinkTag(self._getMessageListAction(), parameters, "del filter")
            
        template.addDeleteHidden("action", self._getDeleteAction().getId())
        parameters = self._data["parameters"]
        for name in parameters.getNames(ignore=("idents", )):
            template.addDeleteHidden(name, parameters[name])
        
        footer[-1] = "<input type='submit' value='delete'/>"
        table.setFooter(footer)
        
        template.setMessageList(str(table))
        
    def build(self):
        template = MessageList.MessageList()
        self._buildEdition(template)
        self._buildMessageList(template)
        self.setMainContent(str(template))



class AlertListing(MessageListing, AlertsSection):
    ROOT = "alert"
    HEADER = "Classification", "Source", "Target", "Sensor", "Time"
    FILTERS = [ "alert.classification.name", "alert.source.node.address.address", "alert.target.node.address.address",
                "alert.analyzer.model" ]
    
    def _getMessageListAction(self):
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



class HeartbeatListing(MessageListing, HeartbeatsSection):
    ROOT = "heartbeat"
    HEADER = "Analyzerid", "Address", "Name", "Type", "Time"
    FILTERS = [ "heartbeat.analyzer.analyzerid", "heartbeat.analyzer.node.address.address", "heartbeat.analyzer.node.name",
                "heartbeat.analyzer.model", "heartbeat.create_time" ]

    def _getMessageListAction(self):
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



class AlertSummary(AlertsSection):
    def build(self):
        self.setMainContent(MessageSummary.AlertSummary(self._data))



class HeartbeatSummary(HeartbeatsSection):
    def build(self):
        self.setMainContent(MessageSummary.HeartbeatSummary(self._data))



class AlertDetails(AlertsSection):
    def build(self):
        self.setMainContent(MessageDetails.AlertDetails(self._data))



class HeartbeatDetails(HeartbeatsSection):
    def build(self):
        self.setMainContent(MessageDetails.HeartbeatDetails(self._data))
