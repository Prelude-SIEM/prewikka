import sys
import urllib

import PyTpl
from templates import Table



class Link:
    def __init__(self, module, section, content):
        self._module = module
        self._section = section
        self._content = content
        self._arguments = { }

    def __setitem__(self, key, value):
        self._arguments[key] = value

    def __str__(self):
        self._arguments["mod"] = self._module
        self._arguments["section"] = self._section
        query = urllib.urlencode(self._arguments)

        return "<a href=\"index.py?%s\">%s</a>" % (query, self._content)



class AlertList:
    def __init__(self):
        self._table = Table.Table()
        self._table.setHeader(("Classification", "Source", "Target", "Sensor", "Time", ""))

    def addAlert(self, alert):
        link = Link("mod_alert", "Alert view", "view")
        link["Alert view.analyzerid"] = alert["alert.analyzer.analyzerid"]
        link["Alert view.alert_ident"] = alert["alert.ident"]

        impact_severity = "impact_severity_" + alert["alert.assessment.impact.severity"]
        
        self._table.addRow(("<span class=\"%s\">%s</span>" % (impact_severity, alert["alert.classification(0).name"]),
                            alert["alert.source(0).node.address(0).address"] or "n/a",
                            alert["alert.target(0).node.address(0).address"] or "n/a",
                            alert["alert.analyzer.model"],
                            alert["alert.detect_time"],
                            str(link)))

    def __str__(self):
        return str(self._table)
