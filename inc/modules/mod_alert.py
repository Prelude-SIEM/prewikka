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
        self.setViewNames([ ("alert list", "list") ])
        self.setViewName("alert list")



class ListInterface(ModuleInterface):
    def _createAlertLink(self, action, alert):
        request = AlertRequest()
        request.module = "Alerts"
        request.action = action
        request.analyzerid = alert["alert.analyzer.analyzerid"]
        request.alert_ident = alert["alert.ident"]
        return self.createLink(request, action)
    
    def build(self):
        table = Table.Table()
        table.setHeader(("Classification", "Source", "Target", "Sensor", "Time", "", ""))
        for alert in self._data:
            impact_severity = "impact_severity_" + alert["alert.assessment.impact.severity"]
            table.addRow(("<span class=\"%s\">%s</span>" % (impact_severity, alert["alert.classification(0).name"]),
                          alert["alert.source(0).node.address(0).address"] or "n/a",
                          alert["alert.target(0).node.address(0).address"] or "n/a",
                          alert["alert.analyzer.model"],
                          alert["alert.detect_time"],
                          self._createAlertLink("summary", alert),
                          self._createAlertLink("details", alert)));
        
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



class AlertModule(module.ContentModule):
    def __init__(self, _core, config):
        module.ContentModule.__init__(self, _core)
        self.setName("Alerts")
        self.registerAction("list", core.CoreRequest, default=True)
        self.registerAction("summary", AlertRequest)
        self.registerAction("details", AlertRequest)

    def handle_list(self, request):
        prelude = self._core.prelude
        idents = prelude.getAlertIdents("alert.detect_time >= 'month:current-1'")
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
