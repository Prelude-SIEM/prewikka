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

from prewikka import Action
from prewikka import utils
import prewikka.User

from prewikka.modules.main import ActionParameters
from prewikka.modules.main.templates import \
     AlertListing, HeartbeatListing, MessageDetails, MessageListing, \
     MessageSummary, SensorAlertListing, SensorHeartbeatListing, \
     SensorListing



class _MyTime:
    def __init__(self, t=None):
        self._t = t or time.time()
        self._index = 5 # second index

    def __getitem__(self, key):
        try:
            self._index = [ "year", "month", "day", "hour", "min", "sec" ].index(key)
        except ValueError:
            raise KeyError
        
        return self

    def round(self, unit):
        t = list(time.localtime(self._t))
        if unit != "sec":
            t[5] = 0
            if unit != "min":
                t[4] = 0
                if unit != "hour":
                    t[3] = 0
                    if unit != "day":
                        t[2] = 1
                        if unit != "month":
                            t[1] = 1
                            t[0] += 1
                        else:
                            t[1] += 1
                    else:
                        t[2] += 1
                else:
                    t[3] += 1
            else:
                t[4] += 1
        else:
            t[5] += 1
        self._t = time.mktime(t)                

    def __add__(self, value):
        t = time.localtime(self._t)
        t = list(t)
        t[self._index] += value
        t = time.mktime(t)
        return _MyTime(t)

    def __sub__(self, value):
        return self + (-value)

    def __str__(self):
        return utils.time_to_ymdhms(self._t)
    
    def __int__(self):
        return self._t



def get_action_handler_name(name):
    import prewikka.modules.main.Actions
    action_class = getattr(prewikka.modules.main.Actions, name)
    object = action_class()

    return object.path
    
    

class AlertsView:
    def _setView(self, dataset):
        dataset["interface.active_section"] = "Alerts"
        dataset["interface.active_tab"] = "Alerts"
        dataset["interface.tabs"] = [("Alerts", \
                                      utils.create_link(get_action_handler_name("AlertListingAction")))]
                                  


class HeartbeatsView:
    def _setView(self, dataset):
        dataset["interface.active_section"] = "Heartbeats"
        dataset["interface.tabs"] = [("List", \
                                      utils.create_link(get_action_handler_name("HeartbeatListingAction")))]



class HeartbeatsAnalyzeView(HeartbeatsView):
    def _setView(self, dataset):
        HeartbeatsView._setView(self, dataset)
        dataset["interface.active_tab"] = "Analyze"



class HeartbeatListingView(HeartbeatsView):
    def _setView(self, dataset):
        HeartbeatsView._setView(self, dataset)
        dataset["interface.active_tab"] = "List"



class SensorsView:
    def _setView(self, dataset):
        dataset["interface.active_section"] = "Sensors"
        dataset["interface.active_tab"] = "Sensors"
        dataset["interface.tabs"] = [("Sensors", \
                                     utils.create_link(get_action_handler_name("SensorListingAction")))]



class MessageListingAction(Action.Action):
    parameters = ActionParameters.MessageListing
    permissions = [ prewikka.User.PERM_MESSAGE_VIEW ]

    def _adjustCriteria(self, request, criteria):
        pass

    def getFilter(self, wanted):
        for name, object, filter in self.fields:
            if name == wanted:
                return filter

        raise Action.ActionParameterInvalidError(wanted)

    def _createLink(self, action, parameters, ignore=()):
        action = get_action_handler_name(action)
        action_parameters = copy.copy(parameters)
        for parameter in ignore:
            try:
                del action_parameters[parameter]
            except KeyError:
                pass
        
        return utils.create_link(action, action_parameters)

    def _setFilter(self, dataset, parameters):
        dataset["active_filter"] = parameters.getFilterName()
        dataset["remove_active_filter"] = self._createLink(self.listing_action,
                                                           parameters, ("filter_name", "filter_value", "offset"))

    def _setTimelineNext(self, dataset, parameters, next):
        tmp = copy.copy(parameters)
        tmp.setTimelineEnd(int(next))
        dataset["timeline.next"] = self._createLink(self.listing_action, tmp)

    def _setTimelinePrev(self, dataset, parameters, prev):
        tmp = copy.copy(parameters)
        tmp.setTimelineEnd(int(prev))
        dataset["timeline.prev"] = self._createLink(self.listing_action, tmp)

    def _getTimelineRange(self, parameters):
        if parameters.getTimelineEnd():
            end = _MyTime(parameters.getTimelineEnd())
        else:
            end = _MyTime()
            if not parameters.getTimelineUnit() in ("min", "hour"):
                end.round(parameters.getTimelineUnit())
        start = end[parameters.getTimelineUnit()] - parameters.getTimelineValue()

        return start, end        
        
    def _setTimeline(self, dataset, parameters, start, end):
        dataset["timeline.current"] = self._createLink(self.listing_action, parameters, ("timeline_end", ))

        dataset["timeline.value"] = parameters.getTimelineValue()
        dataset["timeline.%s_selected" % parameters.getTimelineUnit()] = "selected"
        dataset["timeline.hidden_parameters"] = [ ("action", get_action_handler_name(self.listing_action)) ]
        for name in parameters.getNames(ignore=("timeline_value", "timeline_unit", "limit")):
            dataset["timeline.hidden_parameters"].append((name, parameters[name]))
        dataset["timeline.start"] = str(start)
        dataset["timeline.end"] = str(end)

        if not parameters.getTimelineEnd() and parameters.getTimelineUnit() in ("min", "hour"):
            tmp = copy.copy(end)
            tmp.round(parameters.getTimelineUnit())
            tmp = tmp[parameters.getTimelineUnit()] - 1
            self._setTimelineNext(dataset, parameters,
                                  tmp[parameters.getTimelineUnit()] + parameters.getTimelineValue())
            self._setTimelinePrev(dataset, parameters,
                                  tmp[parameters.getTimelineUnit()] - (parameters.getTimelineValue() - 1))
        else:
            self._setTimelineNext(dataset, parameters,
                                  end[parameters.getTimelineUnit()] + parameters.getTimelineValue())
            self._setTimelinePrev(dataset, parameters,
                                  end[parameters.getTimelineUnit()] - parameters.getTimelineValue())

    def _setNavPrev(self, dataset, parameters, offset):
        if offset:
            dataset["nav.first"] = self._createLink(self.listing_action, parameters)
            tmp = copy.copy(parameters)
            tmp.setOffset(offset - parameters.getLimit())
            dataset["nav.prev"] = self._createLink(self.listing_action, tmp)
        else:
            dataset["nav.prev"] = None
            
    def _setNavNext(self, dataset, parameters, count):
        if count > parameters.getOffset() + parameters.getLimit():
            tmp = copy.copy(parameters)
            tmp.setOffset(parameters.getOffset() + parameters.getLimit())
            dataset["nav.next"] = self._createLink(self.listing_action, tmp)
            tmp.setOffset(count - ((count % parameters.getLimit()) or parameters.getLimit()))
            dataset["nav.last"] = self._createLink(self.listing_action, tmp)
        else:
            dataset["nav.next"] = None
        
    def _fetchMessages(self, parameters, prelude, criteria):
        messages = [ ]
        
        for analyzerid, ident in self.getMessageIdents(prelude, criteria, parameters.getLimit(), parameters.getOffset()):
            message = { "analyzerid": analyzerid, "ident": ident }
            messages.append(message)
            tmp = self.getMessage(prelude, analyzerid, ident)
            for name, object, filter  in self.fields:
                message[name] = tmp[object]
            message["time"] = self.getMessageTime(tmp)
        
        messages.sort(lambda x, y: int(y["time"]) - int(x["time"]))

        return messages

    def _createMessageTimeField(self, t):
        if not t:
            return "n/a"
        
        tmp = time.localtime(t)
        current = time.localtime()
        
        if tmp[:3] == current[:3]: # message time is today
            return utils.time_to_hms(t)

        return utils.time_to_ymdhms(t)

    def _createMessageField(self, parameters, name, value):
        if not value:
            return { "value": "n/a", "filter": None }
        
        parameters = copy.copy(parameters)
        parameters.setFilterName(name)
        parameters.setFilterValue(value)
        
        return { "value": value, "filter": self._createLink(self.listing_action, parameters) }

    def _createMessageLink(self, message, action):
        parameters = ActionParameters.Message()
        parameters.setAnalyzerid(message["analyzerid"])
        parameters.setMessageIdent(message["ident"])
        
        return self._createLink(action, parameters)

    def _addMessage(self, parameters, fields, message):
        fields["summary"] = self._createMessageLink(message, self.summary_action)
        fields["details"] = self._createMessageLink(message, self.details_action)
        fields["ident"] = message["ident"]
        fields["analyzerid"] = message["analyzerid"]
        self._addMessageFields(parameters, fields, message)

    def _setMessages(self, dataset, parameters, messages):
        dataset["messages"] = [ ]
        for message in messages:
            fields = { }
            dataset["messages"].append(fields)
            self._addMessage(parameters, fields, message)

        dataset["delete_form_hiddens"] = [("action", get_action_handler_name(self.delete_action))]
        for name in parameters.getNames():
            dataset["delete_form_hiddens"].append((name, parameters[name]))

    def process(self, request):
        dataset = request.dataset

        parameters = copy.copy(request.parameters)
        offset = parameters.getOffset()
        try:
            del parameters["offset"]
        except KeyError:
            pass

        if not parameters.getTimelineValue() or not parameters.getTimelineUnit():
            parameters.setTimelineValue(1)
            parameters.setTimelineUnit("hour")

        start, end = self._getTimelineRange(parameters)

        criteria = [ ]
        if parameters.getFilterName() and parameters.getFilterValue():
            criteria.append("%s == '%s'" % (self.getFilter(parameters.getFilterName()), parameters.getFilterValue()))
        criteria.append(self.time_criteria_format % (str(start), str(end)))
        self._adjustCriteria(request, criteria)
        criteria = " && ".join(criteria)

        self._setView(dataset)
        self._setFilter(dataset, parameters)
        self._setTimeline(dataset, parameters, start, end)
        self._setNavPrev(dataset, parameters, offset)

        count = self.countMessages(request.prelude, criteria)
        messages = self._fetchMessages(request.parameters, request.prelude, criteria)

        dataset["nav.from"] = parameters.getOffset() + 1
        dataset["nav.to"] = parameters.getOffset() + len(messages)
        dataset["limit"] = parameters.getLimit()
        dataset["total"] = count

        self._setNavNext(dataset, parameters, count)

        self._setMessages(dataset, parameters, messages)

        return self.template_class



class AlertListingAction(MessageListingAction, AlertsView):
    template_class = AlertListing.AlertListing
    listing_action = "AlertListingAction"
    delete_action = "DeleteAlertsAction"
    summary_action = "AlertSummaryAction"
    details_action = "AlertDetailsAction"
    time_criteria_format = "alert.detect_time >= '%s' && alert.detect_time < '%s'"
    message_criteria_format = "alert.analyzer.analyzerid == '%d' && alert.ident == '%d'"
    fields = [ ("severity", "alert.assessment.impact.severity", "alert.assessment.impact.severity"),
               ("classification", "alert.classification(0).name", "alert.classification.name"),
               ("source", "alert.source(0).node.address(0).address", "alert.source.node.address.address"),
               ("target", "alert.target(0).node.address(0).address", "alert.target.node.address.address"),
               ("sensor", "alert.analyzer.model", "alert.analyzer.model") ]

    def countMessages(self, prelude, criteria):
        return prelude.countAlerts(criteria)

    def getMessageIdents(self, prelude, *args, **kwargs):
        return apply(prelude.getAlertIdents, args, kwargs)

    def getMessage(self, prelude, analyzerid, ident):
        return prelude.getAlert(analyzerid, ident)

    def getMessageTime(self, message):
        return message["alert.detect_time"] or message["alert.create_time"] or 0

    def _addMessageFields(self, parameters, fields, alert):
        fields["severity"] = alert["severity"] or "low"
        for name in "analyzerid", "ident":
            fields[name] = alert[name]
        for name in "classification", "source", "target", "sensor":
            fields[name] = self._createMessageField(parameters, name, alert[name])
        fields["time"] = self._createMessageTimeField(alert["time"])



class HeartbeatListingAction(MessageListingAction, HeartbeatListingView):
    template_class = HeartbeatListing.HeartbeatListing
    listing_action = "HeartbeatListingAction"
    delete_action = "DeleteHeartbeatsAction"
    summary_action = "HeartbeatSummaryAction"
    details_action = "HeartbeatDetailsAction"
    time_criteria_format = "heartbeat.create_time >= '%s' && heartbeat.create_time < '%s'"
    message_criteria_format = "heartbeat.analyzer.analyzerid == '%d' && heartbeat.ident == '%d'"
    fields = [ ("address", "heartbeat.analyzer.node.address(0).address", "heartbeat.analyzer.node.address.address"),
               ("name", "heartbeat.analyzer.node.name", "heartbeat.analyzer.node.name"),
               ("type", "heartbeat.analyzer.model", "heartbeat.analyzer.model") ]

    def countMessages(self, prelude, criteria):
        return prelude.countHeartbeats(criteria)

    def getMessageIdents(self, prelude, *args, **kwargs):
        return apply(prelude.getHeartbeatIdents, args, kwargs)

    def getMessage(self, prelude, analyzerid, ident):
        return prelude.getHeartbeat(analyzerid, ident)

    def getMessageTime(self, message):
        return message["heartbeat.create_time"]

    def _addMessageFields(self, parameters, fields, heartbeat):
        for name in "analyzerid", "address", "name", "type":
            fields[name] = self._createMessageField(parameters, name, heartbeat[name])
        fields["time"] = self._createMessageTimeField(heartbeat["time"])



class MessageSummaryAction(Action.Action):
    parameters = ActionParameters.Message
    permissions = [ prewikka.User.PERM_MESSAGE_VIEW ]

    def beginSection(self, title):
        self._current_section = { }
        self._current_section["title"] = title
        self._current_section["entries"] = [ ]

    def newSectionEntry(self, name, value, emphase=False):
        if value is None or value == "":
            return

        self._current_section["entries"].append({ "name": name, "value": value, "emphase": emphase })

    def endSection(self, dataset):
        if self._current_section["entries"]:
            dataset["sections"].append(self._current_section)

    def buildAnalyzer(self, dataset, alert):
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
        self.endSection(dataset)

    def buildAdditionalData(self, dataset, alert):
        self.beginSection("Additional Data")
        
        i= 0
        while True:
            meaning = alert["additional_data(%d).meaning" % i]
            if not meaning:
                break
            value = alert["additional_data(%d).data" % i]
            if alert["additional_data(%d).type" % i] == "byte":
                value = utils.hexdump(value)
            emphase = (alert["analyzer.model"] == "Prelude LML" and alert["additional_data(%d).meaning" % i] == "Original Log")
            self.newSectionEntry(meaning, value, emphase)
            i += 1
        
        self.endSection(dataset)
    


class AlertSummaryAction(MessageSummaryAction, AlertsView):
    def buildTime(self, dataset, alert):
        self.beginSection("Dates")
        self.newSectionEntry("Create time", alert["create_time"])
        self.newSectionEntry("Detect time", alert["detect_time"], emphase=True)
        self.newSectionEntry("Analyzer time", alert["analyzer_time"])
        self.endSection(dataset)

    def buildClassification(self, dataset, alert):
        if not alert["classification(0).name"]:
            return
        
        self.beginSection("Classification")
        self.newSectionEntry("Name", alert["classification(0).name"], emphase=True)
        self.newSectionEntry("Url", alert["classification(0).url"])
        self.newSectionEntry("Origin", alert["classification(0).origin"])
        self.endSection(dataset)

    def buildImpact(self, dataset, alert):
        self.beginSection("Impact")
        self.newSectionEntry("Description", alert["assessment.impact.description"], emphase=True)
        self.newSectionEntry("Severity", alert["assessment.impact.severity"])
        self.newSectionEntry("Type", alert["assessment.impact.type"])
        self.newSectionEntry("Completion", alert["assessment.impact.completion"])
        self.endSection(dataset)

    def buildDirection(self, dataset, alert, direction):
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

    def buildSource(self, dataset, alert):
        self.beginSection("Source")
        self.buildDirection(dataset, alert, "source")
        self.endSection(dataset)

    def buildTarget(self, dataset, alert):
        self.beginSection("Target")
        self.buildDirection(dataset, alert, "target")
        self.newSectionEntry("File", alert["target(0).file(0).name"])
        self.endSection(dataset)

    def process(self, request):
        alert = request.prelude.getAlert(request.parameters.getAnalyzerid(), request.parameters.getMessageIdent())
        dataset = request.dataset
        dataset["sections"] = [ ]
        self.buildTime(dataset, alert)
        self.buildClassification(dataset, alert)
        self.buildImpact(dataset, alert)
        self.buildSource(dataset, alert)
        self.buildTarget(dataset, alert)
        self.buildAnalyzer(dataset, alert)
        self.buildAdditionalData(dataset, alert)
        self._setView(dataset)

        return MessageSummary.MessageSummary



class HeartbeatSummaryAction(MessageSummaryAction, HeartbeatsView):
    def buildTime(self, dataset, heartbeat):
        self.beginSection("Dates")
        self.newSectionEntry("Create time", heartbeat["create_time"])
        self.newSectionEntry("Analyzer time", heartbeat["analyzer_time"])
        self.endSection(dataset)

    def process(self, request):
        hearbeat = request.prelude.getHeartbeat(request.parameters.getAnalyzerid(), request.parameters.getMessageIdent())
        dataset = request.dataset
        dataset["sections"] = [ ]
        self.buildAnalyzer(dataset, heartbeat)
        self.buildTime(dataset, heartbeat)
        self.buildAdditionalData(dataset, heartbeat)
        self._setView(dataset)

        return MessageSummary.MessageSummary



class _Element:
    id = 1
    is_list = False
    check_field = None
    top_element = False
        
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
        element = field()
        element._alert = self._alert
        
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
    fields = "type", "meaning"
    is_list = True
    check_field = "type"

    def render(self, root):
        entries = _Element.render(self, root)
        value = self._alert["%s.data" % root]
        if self._alert["%s.type" % root] == "byte":
            value = utils.hexdump(value)
        entries.append({"name": "Data", "value": value})

        return entries



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



class MessageDetailsAction(Action.Action):
    parameters = ActionParameters.Message
    permissions = [ prewikka.User.PERM_MESSAGE_VIEW ]



class AlertDetailsAction(_Element, MessageDetailsAction, AlertsView):
    name = "alert"
    fields = "ident", Assessment, Analyzer, "create_time", "detect_time", "analyzer_time", \
             Source, Target, Classification, AdditionalData, ToolAlert, CorrelationAlert, \
             OverflowAlert
    top_element = True

    def render(self):
        entries = _Element.render(self, "alert")
        return { "name": "Alert", "id": 0, "hidden": False, "entries": entries }

    def process(self, request):
        self._alert = request.prelude.getAlert(request.parameters.getAnalyzerid(),
                                               request.parameters.getMessageIdent())
        request.dataset["node"] = self.render()

        self._setView(request.dataset)

        return MessageDetails.MessageDetails



class HeartbeatDetailsAction(_Element, MessageDetailsAction, HeartbeatsView):
    name = "heartbeat"
    fields = "ident", Analyzer, "create_time", "analyzer_time", AdditionalData
    top_element = True

    def render(self):
        entries = _Element.render(self, "heartbeat")
        return { "name": "Heartbeat", "id": 0, "hidden": False, "entries": entries }

    def process(self, request):
        self._alert = request.prelude.getHeartbeat(request.parameters.getAnalyzerid(),
                                                   request.parameters.getMessageIdent())
        request.dataset["node"] = self.render()

        self._setView(request.dataset)

        return MessageDetails.MessageDetails



class DeleteMessagesAction:
    parameters = ActionParameters.MessageListingDelete
    permissions = [ prewikka.User.PERM_MESSAGE_ALTER ]

    

class DeleteAlertsAction(DeleteMessagesAction, AlertListingAction):
    def process(self, request):
        for analyzerid, alert_ident in request.parameters.getIdents():
            request.prelude.deleteAlert(analyzerid, alert_ident)
        
        request.parameters = ActionParameters.MessageListing(request.parameters)
        
        return AlertListing.process(self, request)



class DeleteHeartbeatsAction(DeleteMessagesAction, HeartbeatListingAction):
    def process(self, request):
        for analyzerid, heartbeat_ident in request.parameters.getIdents():
            request.prelude.deleteHeartbeat(analyzerid, heartbeat_ident)
        
        request.parameters = ActionParameters.MessageListing(request.parameters)
        
        return HeartbeatListing.process(self, request)



## class HeartbeatsAnalyze(Action.Action):
##     def process(self, core, parameters, request):
##         heartbeat_number = 48
##         heartbeat_value = 3600
##         heartbeat_error_tolerance = 3
        
##         prelude = core.prelude
        
##         data = { }
##         data["analyzers"] = [ ]
##         data["heartbeat_number"] = heartbeat_number
##         data["heartbeat_value"] = heartbeat_value
##         data["heartbeat_error_tolerance"] = heartbeat_error_tolerance
        
##         analyzers = data["analyzers"]

##         for analyzerid in prelude.getAnalyzerids():
##             analyzer = prelude.getAnalyzer(analyzerid)
##             analyzer["errors"] = [ ]
##             analyzers.append(analyzer)
            
##             previous_date = 0
            
##             rows = prelude.getValues(selection=["heartbeat.create_time/order_desc"],
##                                      criteria="heartbeat.analyzer.analyzerid == %d" % analyzerid,
##                                      limit=heartbeat_number)
            
##             for row in rows:
##                 date = row[0]
##                 if previous_date:
##                     delta = int(previous_date) - int(date)
##                     if delta > heartbeat_value + heartbeat_error_tolerance:
##                         analyzer["errors"].append({ "type": "later", "after": date, "back": previous_date })
##                     elif delta < heartbeat_value - heartbeat_error_tolerance:
##                         analyzer["errors"].append({ "type": "sooner", "date": previous_date, "delta": delta })
##                 else:
##                     analyzer["last_heartbeat"] = date
##                 previous_date = date
        
##         return View("HeartbeatsAnalyzeView"), data



class SensorMessageListingAction:
    parameters = ActionParameters.SensorMessageListing



class SensorAlertListingAction(SensorsView,
                               SensorMessageListingAction,
                               AlertListingAction):
    listing_action = "SensorAlertListingAction"
    delete_action = "SensorDeleteAlertsAction"
    summary_action = "SensorAlertSummaryAction"
    details_action = "SensorAlertDetailsAction"

    def _adjustCriteria(self, request, criteria):
        criteria.append("alert.analyzer.analyzerid == %d" % request.parameters.getAnalyzerid())
        
    def process(self, request):
        AlertListingAction.process(self, request)
        request.dataset["analyzer"] = request.prelude.getAnalyzer(request.parameters.getAnalyzerid())
        
        return SensorAlertListing.SensorAlertListing



class SensorDeleteAlertsAction(SensorAlertListingAction):
    def process(self, request):
        for analyzerid, alert_ident in request.parameters.getIdents():
            request.prelude.deleteAlert(analyzerid, alert_ident)

        request.parameters = ActionParameters.SensorMessageListing(request.parameters)

        return SensorAlertListing.process(self, request)



class SensorHeartbeatListingAction(SensorsView,
                                   SensorMessageListingAction,
                                   HeartbeatListingAction):
    listing_action = "SensorHeartbeatListingAction"
    delete_action = "SensorDeleteHeartbeatsAction"
    summary_action = "SensorHeartbeatSummaryAction"
    details_action = "SensorHeartbeatDetailsAction"
    
    def _adjustCriteria(self, request, criteria):
        criteria.append("heartbeat.analyzer.analyzerid == %d" % request.parameters.getAnalyzerid())
    
    def process(self, request):
        HeartbeatListingAction.process(self, request)
        request.dataset["analyzer"] = request.prelude.getAnalyzer(request.parameters.getAnalyzerid())

        return SensorHeartbeatListing.SensorHeartbeatListing



class SensorDeleteHeartbeatsAction(SensorHeartbeatListingAction):
    def process(self, request):
        for analyzerid, alert_ident in request.parameters.getIdents():
            request.prelude.deleteHeartbeat(analyzerid, alert_ident)

        request.parameters = ActionParameters.SensorMessageListing(request.parameters)

        return SensorHeartbeatListing.process(self, request)



class SensorAlertSummaryAction(SensorsView, AlertSummaryAction):
    template_class = MessageSummary.MessageSummary



class SensorAlertDetailsAction(SensorsView, AlertDetailsAction):
    template_class = MessageDetails.MessageDetails



class SensorHeartbeatSummaryAction(SensorsView, HeartbeatSummaryAction):
    template_class = MessageSummary.MessageSummary



class SensorHeartbeatDetailsAction(SensorsView, HeartbeatDetailsAction):
    template_class = MessageDetails.MessageDetails



class SensorListingAction(Action.Action, SensorsView):
    permissions = [ prewikka.User.PERM_MESSAGE_VIEW ]
    
    def process(self, request):
        dataset = request.dataset
        prelude = request.prelude

        dataset["analyzers"] = [ ]
        
        analyzerids = prelude.getAnalyzerids()
        for analyzerid in analyzerids:
            analyzer = prelude.getAnalyzer(analyzerid)
            parameters = ActionParameters.SensorMessageListing()
            parameters.setAnalyzerid(analyzer["analyzerid"])
            analyzer["alerts"] = utils.create_link(get_action_handler_name("SensorAlertListingAction"),
                                                   parameters)
            analyzer["heartbeats"] = utils.create_link(get_action_handler_name("SensorHeartbeatListingAction"),
                                                       parameters)
            dataset["analyzers"].append(analyzer)

        self._setView(dataset)
            
        return SensorListing.SensorListing
