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

from prewikka import Views, Interface
from prewikka.modules.main import ActionParameters
from prewikka.modules.main.templates import MessageSummary, MessageDetails
from prewikka import utils



def template(name):
    return getattr(__import__("prewikka/modules/main/templates/" + name), name)



def Action(name):
    # workaround: we cannot do a simple "from modules.main import Actions" statement
    # because Actions imports View, which means that we would have an indirect recursive
    # module import (View -> Actions -> View -> ...)
    # TODO: find a cleaner way to solve this problem
    from prewikka.modules.main import Actions
    return getattr(Actions, name)



class AlertsSection:
    active_section = "Alerts"
    tabs = [("Alerts", Action("AlertListing")())]
    active_tab = "Alerts"



class HeartbeatsSection(Views.NormalView):
    active_section = "Heartbeats"
    tabs = [("List", Action("HeartbeatListing")())]
    


class HeartbeatsAnalyzeTab(HeartbeatsSection):
    active_tab = "Analyzer"



class HeartbeatListingTab(HeartbeatsSection):
    active_tab = "List"



class SensorsSection:
    active_section = "Sensors"
    tabs = [("Sensors", Action("SensorListing")())]
    active_tab = "Sensors"
    


class MessageListingView(template("MessageListing")):
    def __init__(self, core):
        template("MessageListing").__init__(self, core)
        self.timeline = { }
        self.messages = [ ]
        
        for unit in "sec", "min", "hour", "day", "month", "year":
            self.timeline[unit + "_selected"] = ""
        
    def setParameters(self, parameters):
        self._parameters = parameters
        
        parameters = copy.copy(parameters)
        if parameters.getTimelineEnd():
            del parameters["timeline_end"]
        self.timeline["current"] = self.createLink(self._getMessageListingAction(), parameters)
        
        self.active_filter = self._parameters.getFilterName()
        if self.active_filter:
            parameters = copy.copy(self._parameters)
            del parameters["filter_name"]
            del parameters["filter_value"]
            self.remove_active_filter = self.createLink(self._getMessageListingAction(), parameters)
            
    def setTimeline(self, value, unit):
        self.timeline["value"] = value
        self.timeline[unit + "_selected"] = "selected"
        self.timeline["form_hiddens"] = form_hiddens = [ ]
        form_hiddens.append(("action", Interface.get_action_name(self._getMessageListingAction())))
        for name in self._parameters.getNames(ignore=("timeline_value", "timeline_unit")):
            form_hiddens.append((name, self._parameters[name]))
        
    def setTimelineStart(self, start):
        self.timeline["start"] = str(start)

    def setTimelineEnd(self, end):
        self.timeline["end"] = str(end)

    def setTimelinePrev(self, prev):
        parameters = copy.copy(self._parameters)
        parameters.setTimelineEnd(int(prev))
        self.timeline["prev"] = self.createLink(self._getMessageListingAction(), parameters)
        
    def setTimelineNext(self, next):
        parameters = copy.copy(self._parameters)
        parameters.setTimelineEnd(int(next))
        self.timeline["next"] = self.createLink(self._getMessageListingAction(), parameters)

    def _createMessageField(self, value, filter):
        if not value:
            return { "value": "n/a", "filter": None }
        
        parameters = copy.copy(self._parameters)
        parameters.setFilterName(filter)
        parameters.setFilterValue(value)
        
        return { "value": value, "filter": self.createLink(self._getMessageListingAction(), parameters) }

    def _createMessageTimeField(self, t):
        if not t:
            return "n/a"
        
        tmp = time.localtime(t)
        current = time.localtime()
        
        if tmp[:3] == current[:3]: # message time is today
            return utils.time_to_hms(t)

        return utils.time_to_ymdhms(t)
    
    def _createMessageLink(self, message, action):
        parameters = ActionParameters.Message()
        parameters.setAnalyzerid(message["analyzer.analyzerid"])
        parameters.setMessageIdent(message["ident"])
        
        return self.createLink(action, parameters)
    
    def addMessage(self, message):
        fields = { }
        self.messages.append(fields)
        fields["summary"] = self._createMessageLink(message, self._getMessageSummaryAction())
        fields["details"] = self._createMessageLink(message, self._getMessageDetailsAction())
        fields["ident"] = message["ident"]
        fields["analyzerid"] = message["analyzer.analyzerid"]
        self._addMessageFields(message, fields)
        
    def setMessages(self, messages):
        for message in messages:
            self.addMessage(message)
        self.delete_form_hiddens = [ ]
        self.delete_form_hiddens.append(("action", Interface.get_action_name(self._getDeleteAction())))
        for name in self._parameters.getNames():
            self.delete_form_hiddens.append((name, self._parameters[name]))



class AlertListingView(AlertsSection, template("AlertListing")):
    def __init__(self, core):
        template("AlertListing").__init__(self, core)
        
    def _getMessageListingAction(self):
        return Action("AlertListing")()
    
    def _getDeleteAction(self):
        return Action("DeleteAlerts")()

    def _getMessageSummaryAction(self):
        return Action("AlertSummary")()
    
    def _getMessageDetailsAction(self):
        return Action("AlertDetails")()
    
    def _addMessageFields(self, alert, fields):
        fields["severity"] = alert["alert.assessment.impact.severity"] or "low"
        
        fields["classification"] = self._createMessageField(alert["alert.classification(0).name"],
                                                            "alert.classification.name")
        
        fields["source"] = self._createMessageField(alert["alert.source(0).node.address(0).address"],
                                                    "alert.source.node.address.address")
        
        fields["target"] = self._createMessageField(alert["alert.target(0).node.address(0).address"],
                                                     "alert.target.node.address.address")
        
        fields["sensor"] = self._createMessageField(alert["alert.analyzer.model"], "alert.analyzer.model")
        
        fields["time"] = self._createMessageTimeField(alert["alert.detect_time"] or alert["alert.create_time"])



class HeartbeatListingView(HeartbeatListingTab, template("HeartbeatListing")):
    def __init__(self, core):
        template("HeartbeatListing").__init__(self, core)
        
    def _getMessageListingAction(self):
        return Action("HeartbeatListing")()

    def _getDeleteAction(self):
        return Action("DeleteHeartbeats")()

    def _getMessageSummaryAction(self):
        return Action("HeartbeatSummary")()

    def _getMessageDetailsAction(self):
        return Action("HeartbeatDetails")()
    
    def _addMessageFields(self, heartbeat, fields):
        fields["analyzerid"] = self._createMessageField(heartbeat["heartbeat.analyzer.analyzerid"],
                                                        "heartbeat.analyzer.analyzerid")
        
        fields["address"] = self._createMessageField(heartbeat["heartbeat.analyzer.node.address(0).address"],
                                                     "heartbeat.analyzer.node.address.address")
        
        fields["name"] = self._createMessageField(heartbeat["heartbeat.analyzer.node.name"], "heartbeat.analyzer.node.name")
        
        fields["type"] = self._createMessageField(heartbeat["heartbeat.analyzer.model"], "heartbeat.analyzer.model")
        
        fields["time"] = self._createMessageTimeField(heartbeat["heartbeat.create_time"])



class MessageSummaryView(template("MessageSummary")):
    def __init__(self, core):
        template("MessageSummary").__init__(self, core)
        self.sections = [ ]

    def beginSection(self, title):
        self._current_section = { }
        self._current_section["title"] = title
        self._current_section["entries"] = [ ]

    def newSectionEntry(self, name, value, emphase=False):
        if value is None or value == "":
            return

        self._current_section["entries"].append({ "name": name, "value": value, "emphase": emphase })

    def endSection(self):
        if self._current_section["entries"]:
            self.sections.append(self._current_section)
        
    def buildAnalyzer(self, alert):
        self.beginSection("Analyzer")
        self.newSectionEntry("Analyzerid", alert["analyzer.analyzerid"])
        self.newSectionEntry("Manufacturer", alert["analyzer.manufacturer"])
        self.newSectionEntry("Model", alert["analyzer.model"], emphase=True)
        self.newSectionEntry("Version", alert["analyzer.version"])
        self.newSectionEntry("Class", alert["analyzer.class"])
        self.newSectionEntry("Operating System", "%s %s" % (alert["analyzer.ostype"], alert["analyzer.osversion"]))
        self.newSectionEntry("Node name", alert["analyzer.node.name"])
        self.newSectionEntry("Address", alert["analyzer.node.address(0).address"])
        self.newSectionEntry("Process", alert["analyzer.process.name"])
        self.newSectionEntry("Pid", alert["analyzer.process.pid"])
        self.endSection()

    def buildAdditionalData(self, alert):
        self.beginSection("Additional Data")
        
        i= 0
        while True:
            meaning = alert["additional_data(%d).meaning" % i]
            if not meaning:
                break
            value = alert["additional_data(%d).data" % i]
            emphase = (alert["analyzer.model"] == "Prelude LML" and alert["additional_data(%d).meaning" % i] == "Original Log")
            self.newSectionEntry(meaning, value, emphase)
            i += 1
        
        self.endSection()



class AlertSummaryView(AlertsSection, MessageSummaryView):
    def __init__(self, core, alert):
        MessageSummaryView.__init__(self, core)
        self.buildTime(alert)
        self.buildClassification(alert)
        self.buildImpact(alert)
        self.buildSource(alert)
        self.buildTarget(alert)
        self.buildAnalyzer(alert)
        self.buildAdditionalData(alert)

    def buildTime(self, alert):
        self.beginSection("Dates")
        self.newSectionEntry("Create time", alert["create_time"])
        self.newSectionEntry("Detect time", alert["detect_time"], emphase=True)
        self.newSectionEntry("Analyzer time", alert["analyzer_time"])
        self.endSection()

    def buildClassification(self, alert):
        if not alert["classification(0).name"]:
            return
        
        self.beginSection("Classification")
        self.newSectionEntry("Name", alert["classification(0).name"], emphase=True)
        self.newSectionEntry("Url", alert["classification(0).url"])
        self.newSectionEntry("Origin", alert["classification(0).origin"])
        self.endSection()

    def buildImpact(self, alert):
        self.beginSection("Impact")
        self.newSectionEntry("Description", alert["assessment.impact.description"], emphase=True)
        self.newSectionEntry("Severity", alert["assessment.impact.severity"])
        self.newSectionEntry("Type", alert["assessment.impact.type"])
        self.newSectionEntry("Completion", alert["assessment.impact.completion"])
        self.endSection()

    def buildDirection(self, alert, direction):
        address = alert["%s(0).node.address(0).address" % direction]
        if address:
            port = alert["%s(0).service.port" % direction]
            if port:
                address += ":%d" % port
            protocol = alert["%s(0).service.protocol" % direction]
            if protocol:
                address += " (%s)" % protocol
            self.newSectionEntry("Address", address, emphase=True)

        self.newSectionEntry("Interface", alert["%s(0).interface" % direction])
        self.newSectionEntry("User", alert["%s(0).user.userid(0).name" % direction])
        self.newSectionEntry("Uid", alert["%s(0).user.userid(0).number" % direction])
        self.newSectionEntry("Process", alert["%s(0).process.name" % direction])

    def buildSource(self, alert):
        self.beginSection("Source")
        self.buildDirection(alert, "source")
        self.endSection()

    def buildTarget(self, alert):
        self.beginSection("Target")
        self.buildDirection(alert, "target")
        self.newSectionEntry("File", alert["target(0).file(0).name"])
        self.endSection()



class HeartbeatSummaryView(HeartbeatListingTab, MessageSummaryView):
    def __init__(self, core, heartbeat):
        MessageSummaryView.__init__(self, core)
        self.buildAnalyzer(heartbeat)
        self.buildTime(heartbeat)
        self.buildAdditionalData(heartbeat)
        
    def buildTime(self, heartbeat):
        self.beginSection("Dates")
        self.newSectionEntry("Create time", heartbeat["create_time"])
        self.newSectionEntry("Analyzer time", heartbeat["analyzer_time"])
        self.endSection()



class _Element:
    id = 1
    is_list = False
    check_field = None
    top_element = False
    
    def __init__(self, alert):
        self._alert = alert
        
    def _humanizeField(self, field):
        return field.replace("_", " ").capitalize()

    def _renderNormal(self, root, field):
        name = self._humanizeField(field)
        field = "%s.%s" % (root, field)
        value = self._alert[field]
        value = str(value)
        if value == "":
            value = "n/a"
            
        return { "name": name, "value": value }

    def _renderElement(self, root, field, idx=None):
        element = field(self._alert)
        
        if idx is None:
            name = element.name
        else:
            name = "%s(%d)" % (element.name, idx)
        
        if element.check_field:
            if self._alert["%s.%s.%s" % (root, name, element.check_field)] is None:
                return
        
        humanized = self._humanizeField(element.name)
        id = _Element.id
        _Element.id += 1
        entries = element.render("%s.%s" % (root, name))

        return { "name": humanized, "value": { "name": humanized, "id": id, "hidden": True, "entries": entries } }
    
    def _renderList(self, root, field):
        elements = [ ]
        count = 0
        
        while True:
            element = self._renderElement(root, field, count)
            if not element:
                break
            
            elements.append(element)
            count += 1

        return elements
    
    def render(self, root=None):
        entries = [ ]
        
        for field in self.fields:
            if type(field) is str:
                entries.append(self._renderNormal(root, field))
            else:
                if field.is_list:
                    entries += self._renderList(root, field)
                else:
                    element = self._renderElement(root, field)
                    if element:
                        entries.append(element)

        return entries



class Web(_Element):
    name = "web"
    fields = "url", "cgi", "http_method"#, "arg("
    check_field = "url"



class SNMP(_Element):
    name = "snmp"
    fields = "oid", "community", "command"
    check_field = "oid"



class Service(_Element):
    name = "service"
    fields = "ident", "name", "port", "portlist", "protocol", Web, SNMP
    check_field = "ident"


class UserID(_Element):
    name = "userid"
    fields = "ident", "type", "name", "number"
    check_field = "ident"
    is_list = True



class User(_Element):
    name = "user"
    fields = "ident", "category", UserID
    check_field = "ident"



class Address(_Element):
    name = "address"
    fields = "ident", "category", "vlan_name", "vlan_num", "address", "netmask"
    is_list = True
    check_field = "ident"



class Node(_Element):
    name = "node"
    fields = "ident", "category", "location", "name", Address
    check_field = "ident"
    


class Process(_Element):
    name = "process"
    fields = "ident", "name", "pid", "path"#, "arg(", "env("
    check_field = "ident"



class FileAccess(_Element):
    name = "file_access"
    fields = "userid", "permission("
    check_field = "userid"
    is_list = True



class File(_Element):
    name = "file"
    fields = "ident", "category", "fstype", "name", "path", "create_time", "modify_time", \
             "access_time", "data_size", "disk_size", FileAccess
    check_field = "ident"



class Files(File):
    is_list = True



class Target(_Element):
    name = "target"
    fields = "ident", "decoy", "interface", Node, User, Process, Service, Files
    check_field = "ident"
    is_list = True



class Source(_Element):
    name = "source"
    fields = "ident", "spoofed", "interface", Node, User, Process, Service
    check_field = "ident"
    is_list = True

    

class Confidence(_Element):
    name = "confidence"
    fields = "rating", "confidence"
    check_field = "confidence"


class Action_(_Element):
    name = "action"
    fields = "category", "description"
    is_list = True
    check_field = "description"



class Impact(_Element):
    name = "impact"
    fields = "severity", "completion", "type", "description"



class Classification(_Element):
    name = "classification"
    fields = ("origin", "name", "url")
    is_list = True
    check_field = "origin"



class AdditionalData(_Element):
    name = "additional_data"
    fields = "type", "meaning", "data"
    is_list = True
    check_field = "type"



class Assessment(_Element):
    name = "assessment"
    fields = Impact, Action_, Confidence



class Analyzer(_Element):
    name = "analyzer"
    fields = "analyzerid", "manufacturer", "model", "version", "class", "ostype", "osversion", \
             Node, Process



class AlertIdent(_Element):
    name = "alertident"
    fields = "alertident", "analyzerid"
    is_list = True
    check_field = "alertident"
    


class ToolAlert(_Element):
    name = "tool_alert"
    fields = "name", "command", AlertIdent
    check_field = "name"



class CorrelationAlert(_Element):
    name = "correlation_alert"
    fields = "name", AlertIdent
    check_field = "name"



class OverflowAlert(_Element):
    name = "overflow_alert"
    fields = "program", "size", "buffer"
    check_field = "program"



class AlertDetails(_Element):
    name = "alert"
    fields = "ident", Assessment, Analyzer, "create_time", "detect_time", "analyzer_time", \
             Source, Target, Classification, AdditionalData, ToolAlert, CorrelationAlert, \
             OverflowAlert
    top_element = True

    def render(self):
        entries = _Element.render(self, "alert")
        return { "name": "Alert", "id": 0, "hidden": False, "entries": entries }



class HeartbeatDetails(_Element):
    name = "heartbeat"
    fields = "ident", Analyzer, "create_time", "analyzer_time", AdditionalData
    top_element = True

    def render(self):
        entries = _Element.render(self, "heartbeat")
        return { "name": "Heartbeat", "id": 0, "hidden": False, "entries": entries }



class AlertDetailsView(AlertsSection, template("MessageDetails")):
    def __init__(self, core, alert):
        template("MessageDetails").__init__(self, core)
        details = AlertDetails(alert)
        self.node = details.render()



class HeartbeatDetailsView(HeartbeatListingTab, template("MessageDetails")):
    def __init__(self, core, heartbeat):
        template("MessageDetails").__init__(self, core)
        details = HeartbeatDetails(heartbeat)
        self.node = details.render()



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
    def setAnalyzer(self, analyzer):
        self.analyzer = analyzer



class SensorAlertListingView(SensorMessageListingView, template("SensorAlertListing")):
    def _getMessageListingAction(self):
        return Action("SensorAlertListing")()

    def _getDeleteAction(self):
        return Action("SensorDeleteAlerts")()

    def _getMessageSummaryAction(self):
        return Action("SensorAlertSummary")()

    def _getMessageDetailsAction(self):
        return Action("SensorAlertDetails")()



class SensorHeartbeatListingView(SensorMessageListingView, template("SensorHeartbeatListing")):
    def _getMessageListingAction(self):
        return Action("SensorHeartbeatListing")()

    def _getDeleteAction(self):
        return Action("SensorDeleteHeartbeats")()

    def _getMessageSummaryAction(self):
        return Action("SensorHeartbeatSummary")()

    def _getMessageDetailsAction(self):
        return Action("SensorHeartbeatDetails")()



class SensorAlertSummaryView(SensorsSection, AlertSummaryView):
    pass



class SensorAlertDetailsView(SensorsSection, AlertDetailsView):
    pass



class SensorHeartbeatSummaryView(SensorsSection, HeartbeatSummaryView):
    pass



class SensorHeartbeatDetailsView(SensorsSection, HeartbeatDetailsView):
    pass



class SensorListingView(SensorsSection, template("SensorListing")):
    def __init__(self, core):
        template("SensorListing").__init__(self, core)
        self.analyzers = [ ]
        
    def addAnalyzer(self, analyzer):
        parameters = ActionParameters.SensorMessageListing()
        parameters.setAnalyzerid(analyzer["analyzerid"])
        analyzer["alerts"] = self.createLink(Action("SensorAlertListing")(), parameters)
        analyzer["heartbeats"] = self.createLink(Action("SensorHeartbeatListing")(), parameters)
        self.analyzers.append(analyzer)
