import sys
import prelude
import time
import util
import re
from templates.modules.mod_alert import AlertList, AlertSummary, AlertDetails
from templates import Table
import module
import interface
import core


class ModuleInterface(interface.NormalInterface):
    def init(self):
        interface.NormalInterface.init(self)
        self.setModuleName("Alerts")
        self.setTabs([ ("alert list", "list") ])
        self.setActiveTab("alert list")



class ListInterface(ModuleInterface):
    def _createLink(self, request, name, class_):
        return "<a class='%s' href='index.py?%s'>%s</a>" % (class_, str(request), name)

    def _createAlertLink(self, alert, action):
        request = AlertRequest()
        request.module = "Alerts"
        request.action = action
        request.analyzerid = alert["alert.analyzer.analyzerid"]
        request.alert_ident = alert["alert.ident"]
        
        return "<a href='index.py?%s'>%s</a>" % (str(request), action)

    def _addAlertField(self, row, alert, field, filter_name=None, class_="alert_field_value"):
        if filter_name is None:
            filter_name = field
        
        value = alert[field]
        if value:
            request = ListRequest()
            request.module = "Alerts"
            request.action = "list"
            request.filter_name = filter_name
            request.filter_value = value
            field = self._createLink(request, value, class_)
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
        row.append(alert["alert.detect_time"])
        row.append(self._createAlertLink(alert, "summary"))
        row.append(self._createAlertLink(alert, "details"))

        table.addRow(row)
    
    def build(self):
        alerts = self._data
        table = Table.Table()
        table.setHeader(("Classification", "Source", "Target", "Sensor", "Time", "", ""))
        for alert in alerts:
            self._addAlert(table, alert)
        self.setMainContent(str(table))



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



class AlertModule(module.ContentModule):
    def __init__(self, _core, config):
        module.ContentModule.__init__(self, _core)
        self.setName("Alerts")
        self.registerAction("list", ListRequest, default=True)
        self.registerAction("summary", AlertRequest)
        self.registerAction("details", AlertRequest)

    def handle_list(self, request):
        prelude = self._core.prelude
        criteria = "alert.detect_time >= 'month:current-1'"
        if request.filter_name and request.filter_value:
            criteria += " && %s == '%s'" % (request.filter_name, request.filter_value)
        idents = prelude.getAlertIdents(criteria)
        alerts = [ ]
        if idents:
            for analyzerid, alert_ident in idents:
                alert = prelude.getAlert(analyzerid, alert_ident)
                alerts.append(alert)
        
        return ListInterface, alerts

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
