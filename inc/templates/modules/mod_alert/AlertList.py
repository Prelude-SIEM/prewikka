import PyTpl

class AlertList(PyTpl.Template):
    def __init__(self):
        PyTpl.Template.__init__(self)
        self.alert_count = 0
    
    def addAlert(self,
                 alert_ident,
                 time,
                 description,
                 url,
                 source_ip,
                 destination_ip,
                 sensor_id,
                 severity,
                 type):
        self["alert"].ALERT_IDENT = alert_ident
        self["alert"].TIME = time
        self["alert"].DESCRIPTION = description
        self["alert"].URL = url
        self["alert"].SIP = source_ip
        self["alert"].DIP = destination_ip
        self["alert"].SENSORID = sensor_id
        self["alert"].SEVERITY = severity
        self["alert"].TYPE = type
        self["alert"].COLOR = ("#ffffff", "#eeeeee")[self.alert_count%2]
        self["alert"].parse()
        self.alert_count += 1
