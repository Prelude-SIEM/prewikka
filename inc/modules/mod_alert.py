import sys
import copy
import prelude
import time
import util
import re
from templates.modules.mod_alert import AlertList, AlertSummary, AlertDetails
from templates import Table
import module
import interface
import core


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

    
        
class ModuleInterface(interface.NormalInterface):
    def init(self):
        interface.NormalInterface.init(self)
        self.setModuleName("Alerts")
        self.setTabs([ ("alert list", "list") ])
        self.setActiveTab("alert list")



class ListInterface(ModuleInterface):
    def _createLinkTag(self, request, name, class_=""):
        return "<a class='%s' href='%s'>%s</a>" % (class_, self.createLink(request), name)

    def _createAlertLink(self, alert, action):
        request = AlertRequest()
        request.module = "Alerts"
        request.action = action
        request.analyzerid = alert["alert.analyzer.analyzerid"]
        request.alert_ident = alert["alert.ident"]
        
        return "<a href='%s'>%s</a>" % (self.createLink(request), action)

    def _addAlertField(self, row, alert, field, filter_name=None, class_="alert_field_value"):
        if filter_name is None:
            filter_name = field
        
        value = alert[field]
        if value:
            request = copy.copy(self._request)
            request.filter_name = filter_name
            request.filter_value = value
            field = self._createLinkTag(request, value, class_)
        else:
            field = "n/a"

        row.append(field)

    def _addAlert(self, table, alert):
        row = [ ]

        impact_severity = "impact_severity_" + (alert["alert.assessment.impact.severity"] or "low")
        self._addAlertField(row, alert, "alert.classification(0).name", "alert.classification.name", class_=impact_severity)
        self._addAlertField(row, alert, "alert.source(0).node.address(0).address", "alert.source.node.address.address")
        self._addAlertField(row, alert, "alert.target(0).node.address(0).address", "alert.target.node.address.address")
        self._addAlertField(row, alert, "alert.analyzer.model")
        row.append(str(MyTime(int(alert["alert.detect_time"]))))
        row.append(self._createAlertLink(alert, "summary"))
        row.append(self._createAlertLink(alert, "details"))

        table.addRow(row)

    def _buildEdition(self, template):
        template.addHidden("module", "Alerts")
        template.addHidden("action", "list")
        if self._request.timeline_end:
            template.addHidden("timeline_end", self._request.timeline_end)
        
        template.setTimelineStart(str(self._data["start"]))
        template.setTimelineEnd(str(self._data["end"]))

        request = copy.copy(self._request)

        if request.timeline_end:
            del request["timeline_end"]
        template.setCurrent(self.createLink(request))

        request = copy.copy(self._request)
        
        request.timeline_end = int(self._data["end"][self._request.timeline_unit] + self._request.timeline_value)
        template.setNext(self.createLink(request))

        request.timeline_end = int(self._data["end"][self._request.timeline_unit] - self._request.timeline_value)
        template.setPrev(self.createLink(request))
        
        template.setTimelineValue(self._request.timeline_value or 1)
        template.setTimelineUnit(self._request.timeline_unit or "hour")
    
    def _buildAlertList(self, template):
        alerts = self._data["alerts"]
        table = Table.Table()
        table.setHeader(("Classification", "Source", "Target", "Sensor", "Time", "", ""))
        for alert in alerts:
            self._addAlert(table, alert)

        print >> sys.stderr, "###", str(self._request)

        if self._request.filter_name:
            #print >> sys.stderr, "###", self._request.filter_name
            filters = [ "alert.classification.name", "alert.source.node.address.address", "alert.target.node.address.address", \
                        "alert.analyzer.model" ]
            footer = [ "" ] * 7
            request = copy.copy(self._request)
            filter_name = request["filter_name"]
            del request["filter_name"]
            del request["filter_value"]
            footer[filters.index(filter_name)] = self._createLinkTag(request, "del filter")
            table.setFooter(footer)

        template.setAlertList(str(table))

    def build(self):
        template = AlertList.AlertList()
        self._buildEdition(template)
        self._buildAlertList(template)
        self.setMainContent(str(template))

        



class SummaryInterface(ModuleInterface):
    def build(self):
        self.setMainContent(AlertSummary.AlertSummary(self._data))



class DetailsInterface(ModuleInterface):
    def build(self):
        self.setMainContent(AlertDetails.AlertDetails(self._data))



class AlertRequest(core.CoreRequest):
    def __init__(self):
        core.CoreRequest.__init__(self)
        self.registerField("analyzerid", long)
        self.registerField("alert_ident", long)



class ListRequest(core.CoreRequest):
    def __init__(self):
        core.CoreRequest.__init__(self)
        self.registerField("filter_name", str)
        self.registerField("filter_value", str)
        self.registerField("timeline_value", int)
        self.registerField("timeline_unit", str)
        self.registerField("timeline_end", int)



class AlertModule(module.ContentModule):
    def __init__(self, _core, config):
        module.ContentModule.__init__(self, _core)
        self.setName("Alerts")
        self.registerAction("list", ListRequest, default=True)
        self.registerAction("summary", AlertRequest)
        self.registerAction("details", AlertRequest)

    def handle_list(self, request):
        result = { }
        
        prelude = self._core.prelude

        criteria = [ ]
        
        if request.filter_name and request.filter_value:
            criteria.append("%s == '%s'" % (request.filter_name, request.filter_value))

        if not request.timeline_value or not request.timeline_unit:
            request.timeline_value = 1
            request.timeline_unit = "hour"

        if request.timeline_end:
            end = MyTime(request.timeline_end)
        else:
            end = MyTime()
            end.round(request.timeline_unit)
        
        start = end[request.timeline_unit] - request.timeline_value

        result["start"], result["end"] = start, end

        criteria.append("alert.detect_time >= '%s' && alert.detect_time < '%s'" % (str(start), str(end)))
            
        idents = prelude.getAlertIdents(" && ".join(criteria))
        alerts = [ ]
        if idents:
            for analyzerid, alert_ident in idents:
                alert = prelude.getAlert(analyzerid, alert_ident)
                alerts.append(alert)

        result["alerts"] = alerts
        
        return ListInterface, result

    def handle_default(self, request):
        return self.handle_list(request)

    def _getAlert(self, request):
        return self._core.prelude.getAlert(request.analyzerid, request.alert_ident)

    def handle_summary(self, request):
        return SummaryInterface, self._getAlert(request)

    def handle_details(self, request):
        return DetailsInterface, self._getAlert(request)



def load(_core, config):
    module = AlertModule(_core, config)
    _core.registerContentModule(module)
