import sys
import copy
import prelude
import time
import util
import re
from templates.modules.mod_alert import MessageList, MessageSummary, MessageDetails
from templates import Table
import module
import Interface
import Views


class MyTime:
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
        return MyTime(t)

    def __sub__(self, value):
        return self + (-value)

    def __str__(self):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self._t))

    def __int__(self):
        return self._t



class AlertsView(Views.NormalView):
    def init(self):
        Views.NormalView.init(self)
        self.setActiveSection("Alerts")
        self.setTabs([ ("Alerts", AlertListAction()) ])
        self.setActiveTab("Alerts")



class HeartbeatsView(Views.NormalView):
    def init(self):
        Views.NormalView.init(self)
        self.setActiveSection("Heartbeats")
        self.setTabs([ ("Heartbeats", HeartbeatListAction()) ])
        self.setActiveTab("Heartbeats")



class MessageListDisplay:
    def _createLinkTag(self, action, parameters, name, class_=""):
        return "<a class='%s' href='%s'>%s</a>" % (class_, self.createLink(action, parameters), name)
    
    def _createMessageLink(self, message, name, action):
        parameters = MessageActionParameters()
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



class AlertListTabInstance(MessageListDisplay, AlertsView):
    ROOT = "alert"
    HEADER = "Classification", "Source", "Target", "Sensor", "Time"
    FILTERS = [ "alert.classification.name", "alert.source.node.address.address", "alert.target.node.address.address",
                "alert.analyzer.model" ]

    def _getMessageListAction(self):
        return AlertListAction()
    
    def _getDeleteAction(self):
        return DeleteAlertsAction()
    
    def _addMessage(self, table, alert):
        row = [ ]
        
        impact_severity = "impact_severity_" + (alert["assessment.impact.severity"] or "low")
        self._addMessageField(row, alert, "classification(0).name", "alert.classification.name", class_=impact_severity)
        self._addMessageField(row, alert, "source(0).node.address(0).address", "alert.source.node.address.address")
        self._addMessageField(row, alert, "target(0).node.address(0).address", "alert.target.node.address.address")
        self._addMessageField(row, alert, "analyzer.model", "alert.analyzer.model")
        row.append(self._createMessageTime(alert["detect_time"] or alert["create_time"]))
        row.append(self._createMessageLink(alert, "summary", AlertSummaryAction()))
        row.append(self._createMessageLink(alert, "details", AlertDetailsAction()))
        row.append(self._createDeleteLink(alert))
        
        table.addRow(row)



class HeartbeatListTabInstance(MessageListDisplay, HeartbeatsView):
    ROOT = "heartbeat"
    HEADER = "Analyzerid", "Address", "Name", "Type", "Time"
    FILTERS = [ "heartbeat.analyzer.analyzerid", "heartbeat.analyzer.node.address.address", "heartbeat.analyzer.node.name",
                "heartbeat.analyzer.model", "heartbeat.create_time" ]

    def _getMessageListAction(self):
        return HeartbeatListAction()

    def _getDeleteAction(self):
        return DeleteHeartbeatsAction()

    def _addMessage(self, table, heartbeat):
        row = [ ]
        
        self._addMessageField(row, heartbeat, "analyzer.analyzerid", "heartbeat.analyzer.analyzerid")
        self._addMessageField(row, heartbeat, "analyzer.node.address(0).address", "heartbeat.analyzer.node.address.address")
        self._addMessageField(row, heartbeat, "analyzer.node.name", "heartbeat.analyzer.node.name")
        self._addMessageField(row, heartbeat, "analyzer.model", "heartbeat.analyzer.model")
        row.append(self._createMessageTime(heartbeat["create_time"]))
        row.append(self._createMessageLink(heartbeat, "summary", HeartbeatSummaryAction()))
        row.append(self._createMessageLink(heartbeat, "details", HeartbeatDetailsAction()))
        row.append(self._createDeleteLink(heartbeat))
        
        table.addRow(row)



class AlertSummaryTabInstance(AlertsView):
    def build(self):
        self.setMainContent(MessageSummary.AlertSummary(self._data))



class HeartbeatSummaryTabInstance(HeartbeatsView):
    def build(self):
        self.setMainContent(MessageSummary.HeartbeatSummary(self._data))



class AlertDetailsTabInstance(AlertsView):
    def build(self):
        self.setMainContent(MessageDetails.AlertDetails(self._data))



class HeartbeatDetailsTabInstance(HeartbeatsView):
    def build(self):
        self.setMainContent(MessageDetails.HeartbeatDetails(self._data))



class MessageActionParameters(Interface.ActionParameters):
    def register(self):
        Interface.ActionParameters.register(self)
        self.registerParameter("analyzerid", long)
        self.registerParameter("message_ident", long)

    def setAnalyzerid(self, analyzerid):
        self["analyzerid"] = analyzerid

    def getAnalyzerid(self):
        return self["analyzerid"]

    def setMessageIdent(self, alert_ident):
        self["message_ident"] = alert_ident

    def getMessageIdent(self):
        return self["message_ident"]



class ListActionParameters(Interface.ActionParameters):
    def register(self):
        self.registerParameter("filter_name", str)
        self.registerParameter("filter_value", str)
        self.registerParameter("timeline_value", int)
        self.registerParameter("timeline_unit", str)
        self.registerParameter("timeline_end", int)
        
    def setFilterName(self, name):
        self["filter_name"] = name

    def getFilterName(self):
        return self.get("filter_name")

    def setFilterValue(self, value):
        self["filter_value"] = value

    def getFilterValue(self):
        return self.get("filter_value")

    def setTimelineValue(self, value):
        self["timeline_value"] = value

    def getTimelineValue(self):
        return self.get("timeline_value")

    def setTimelineUnit(self, unit):
        self["timeline_unit"] = unit

    def getTimelineUnit(self):
        return self.get("timeline_unit")

    def setTimelineEnd(self, end):
        self["timeline_end"] = end

    def getTimelineEnd(self):
        return self.get("timeline_end")



class DeleteActionParameters(ListActionParameters):
    def register(self):
        ListActionParameters.register(self)
        self.registerParameter("idents", list)
        
    def getIdents(self):
        idents = [ ]
        if self.hasParameter("idents"):
            for ident in self["idents"]:
                analyzerid, alert_ident = ident.split(":")
                idents.append((analyzerid, alert_ident))
        
        return idents



class MessageListAction(Interface.Action):
    def process(self, core, parameters):
        result = { "parameters": parameters }
        prelude = core.prelude
        criteria = [ ]
        
        if parameters.getFilterName() and parameters.getFilterValue():
            criteria.append("%s == '%s'" % (parameters.getFilterName(), parameters.getFilterValue()))
        
        if not parameters.getTimelineValue() or not parameters.getTimelineUnit():
            parameters.setTimelineValue(1)
            parameters.setTimelineUnit("hour")

        if parameters.getTimelineEnd():
            end = MyTime(parameters.getTimelineEnd())
        else:
            end = MyTime()
            if not parameters.getTimelineUnit() in ("min", "hour"):
                end.round(parameters.getTimelineUnit())
        
        start = end[parameters.getTimelineUnit()] - parameters.getTimelineValue()
        
        result["start"], result["end"] = start, end
        
        if not parameters.getTimelineEnd() and parameters.getTimelineUnit() in ("min", "hour"):
            tmp = copy.copy(end)
            tmp.round(parameters.getTimelineUnit())
            tmp = tmp[parameters.getTimelineUnit()] - 1
            result["next"] = tmp[parameters.getTimelineUnit()] + parameters.getTimelineValue()
            result["prev"] = tmp[parameters.getTimelineUnit()] - (parameters.getTimelineValue() - 1)
        else:
            result["next"] = end[parameters.getTimelineUnit()] + parameters.getTimelineValue()
            result["prev"] = end[parameters.getTimelineUnit()] - parameters.getTimelineValue()
        
        criteria.append(self._createTimeCriteria(start, end))
        criteria = " && ".join(criteria)
        
        idents = self._getMessageIdents(prelude, criteria)
        messages = [ ]
        if idents:
            for analyzerid, alert_ident in idents:
                message = self._getMessage(prelude, analyzerid, alert_ident)
                messages.append(message)
        
        self._sortMessages(messages)
        
        result["messages"] = messages
        
        return self._getView(), result



class AlertListAction(MessageListAction):
    def _createTimeCriteria(self, start, end):
        return "alert.detect_time >= '%s' && alert.detect_time < '%s'" % (str(start), str(end))

    def _getMessageIdents(self, prelude, criteria):
        return prelude.getAlertIdents(criteria)

    def _getMessage(self, prelude, analyzerid, alert_ident):
        return prelude.getAlert(analyzerid, alert_ident)

    def _sortMessages(self, alerts):
        alerts.sort(lambda a1, a2: int(a2["detect_time"]) - int(a1["detect_time"]))

    def _getView(self):
        return AlertListTabInstance



class HeartbeatListAction(MessageListAction):
    def _createTimeCriteria(self, start, end):
        return "heartbeat.create_time >= '%s' && heartbeat.create_time < '%s'" % (str(start), str(end))
    
    def _getMessageIdents(self, prelude, criteria):
        return prelude.getHeartbeatIdents(criteria)
    
    def _getMessage(self, prelude, analyzerid, alert_ident):
        return prelude.getHeartbeat(analyzerid, alert_ident)
    
    def _sortMessages(self, heartbeats):
        heartbeats.sort(lambda hb1, hb2: int(hb2["create_time"]) - int(hb1["create_time"]))
        
    def _getView(self):
        return HeartbeatListTabInstance



class AlertAction(Interface.Action):
    def _getAlert(self, core, parameters):
        return core.prelude.getAlert(parameters.getAnalyzerid(), parameters.getMessageIdent())



class HeartbeatAction(Interface.Action):
    def _getHeartbeat(self, core, parameters):
        return core.prelude.getHeartbeat(parameters.getAnalyzerid(), parameters.getMessageIdent())



class AlertSummaryAction(AlertAction):
    def process(self, core, parameters):
        return AlertSummaryTabInstance, self._getAlert(core, parameters)


class HeartbeatSummaryAction(HeartbeatAction):
    def process(self, core, parameters):
        return HeartbeatSummaryTabInstance, self._getHeartbeat(core, parameters)



class AlertDetailsAction(AlertAction):
    def process(self, core, parameters):
        return AlertDetailsTabInstance, self._getAlert(core, parameters)



class HeartbeatDetailsAction(HeartbeatAction):
    def process(self, core, parameters):
        return HeartbeatDetailsTabInstance, self._getHeartbeat(core, parameters)



class DeleteAlertsAction(AlertListAction):
    def process(self, core, parameters):
        for analyzerid, alert_ident in parameters.getIdents():
            core.prelude.deleteAlert(analyzerid, alert_ident)
        
        parameters = ListActionParameters(parameters)
        
        return AlertListAction.process(self, core, parameters)



class DeleteHeartbeatsAction(HeartbeatListAction):
    def process(self, core, parameters):
        for analyzerid, heartbeat_ident in parameters.getIdents():
            core.prelude.deleteHeartbeat(analyzerid, heartbeat_ident)
        
        parameters = ListActionParameters(parameters)
        
        return HeartbeatListAction.process(self, core, parameters)
        



## class AlertModule(module.ContentModule):
##     def __init__(self, _core, config):
##         module.ContentModule.__init__(self, _core)
##         self.setName("Alerts")
##         self.addSection("Alerts", "alert_list")
##         self.addSection("Heartbeats", "heartbeat_list")
##         self.registerAction("alert_list", ListRequest, default=True)
##         self.registerAction("alert_summary", AlertRequest)
##         self.registerAction("alert_details", AlertRequest)
##         self.registerAction("alert_delete", DeleteRequest)

##     def handle_alert_list(self, request):
##         result = { "request": request }
##         prelude = self._core.prelude
##         criteria = [ ]
        
##         if request.getFilterName() and request.getFilterValue():
##             criteria.append("%s == '%s'" % (request.getFilterName(), request.getFilterValue()))

##         if not request.getTimelineValue() or not request.getTimelineUnit():
##             request.setTimelineValue(1)
##             request.setTimelineUnit("hour")

##         if request.getTimelineEnd():
##             end = MyTime(request.getTimelineEnd())
##         else:
##             end = MyTime()
##             if not request.getTimelineUnit() in ("min", "hour"):
##                 end.round(request.getTimelineUnit())
        
##         start = end[request.getTimelineUnit()] - request.getTimelineValue()
        
##         result["start"], result["end"] = start, end

##         if not request.getTimelineEnd() and request.getTimelineUnit() in ("min", "hour"):
##             tmp = copy.copy(end)
##             tmp.round(request.getTimelineUnit())
##             tmp = tmp[request.getTimelineUnit()] - 1
##             result["next"] = tmp[request.getTimelineUnit()] + request.getTimelineValue()
##             result["prev"] = tmp[request.getTimelineUnit()] - (request.getTimelineValue() - 1)
##         else:
##             result["next"] = end[request.getTimelineUnit()] + request.getTimelineValue()
##             result["prev"] = end[request.getTimelineUnit()] - request.getTimelineValue()
        
##         criteria.append("alert.detect_time >= '%s' && alert.detect_time < '%s'" % (str(start), str(end)))
        
##         idents = prelude.getAlertIdents(" && ".join(criteria))
##         alerts = [ ]
##         if idents:
##             for analyzerid, alert_ident in idents:
##                 alert = prelude.getAlert(analyzerid, alert_ident)
##                 alerts.append(alert)
        
##         alerts.sort(lambda alert1, alert2: (int(alert2["detect_time"] or alert2["create_time"]) -
##                                             int(alert1["detect_time"] or alert1["create_time"])))

##         result["messages"] = alerts
        
##         return AlertListViewInstance, result

##     def handle_default(self, request):
##         return self.handle_list(request)

##     def _getAlert(self, request):
##         return self._core.prelude.getAlert(request.getAnalyzerid(), request.getAlertIdent())

##     def handle_alert_summary(self, request):
##         return SummaryViewInstance, self._getAlert(request)

##     def handle_alert_details(self, request):
##         return DetailsViewInstance, self._getAlert(request)

##     def handle_alert_delete(self, request):
##         for analyzerid, alert_ident in request.getIdents():
##             self._core.prelude.deleteAlert(analyzerid, alert_ident)

##         request = ListRequest(request)
##         request.setAction("alert_list")
        
##         return self.handle_alert_list(request)



## def load(_core, config):
##     module = AlertModule(_core, config)
##     _core.registerContentModule(module)

def load(_core, config):
    # Alerts
    _core.interface.registerSection("Alerts", AlertListAction())
    _core.interface.registerAction(AlertListAction(), ListActionParameters, default=True)
    _core.interface.registerAction(AlertSummaryAction(), MessageActionParameters)
    _core.interface.registerAction(AlertDetailsAction(), MessageActionParameters)
    _core.interface.registerAction(DeleteAlertsAction(), DeleteActionParameters)

    # Heartbeats
    _core.interface.registerSection("Heartbeats", HeartbeatListAction())
    _core.interface.registerAction(HeartbeatListAction(), ListActionParameters)
    _core.interface.registerAction(HeartbeatSummaryAction(), MessageActionParameters)
    _core.interface.registerAction(HeartbeatDetailsAction(), MessageActionParameters)
    _core.interface.registerAction(DeleteHeartbeatsAction(), DeleteActionParameters)
