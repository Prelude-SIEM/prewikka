import PyTpl

class AlertList(PyTpl.Template):
    def __init__(self):
        PyTpl.Template.__init__(self)
        self.alert_count = 0
    
    def addAlert(self, alert):
        self["alert"].ANALYZERID = alert["alert.analyzer.analyzerid"]
        self["alert"].ALERT_IDENT = alert["alert.ident"]
        self["alert"].CLASSIFICATION = alert["alert.classification(0).name"]
        self["alert"].SEVERITY = { "low": "green", "medium": "orange", "high": "red" }[alert["alert.assessment.impact.severity"]]
        self["alert"].SOURCE = alert["alert.source(0).node.address(0).address"] or "n/a"
        self["alert"].TARGET = alert["alert.target(0).node.address(0).address"] or "n/a"
        self["alert"].SENSOR = alert["alert.analyzer.model"]
        self["alert"].TIME = alert["alert.detect_time"]
        self["alert"].COLOR = ("#ffffff", "#eeeeee")[self.alert_count%2]
        self["alert"].parse()
        self.alert_count += 1
