import PyTpl

class AlertDetails(PyTpl.Template):
    def __init__(self):
        PyTpl.Template.__init__(self)
        self.additional_data_count = 0

    def setTime(self, time):
        self.TIME = time

    def setDescription(self, description, url=""):
        self.DESCRIPTION = description
        self.URL = url

    def setSourceIP(self, source_ip):
        self.SIP = source_ip

    def setDestinationIP(self, destination_ip):
        self.DIP = destination_ip

    def setSensorID(self, sensor_id):
        self.SENSORID = sensor_id

    def setSeverity(self, severity):
        self.SEVERITY = severity

    def setType(self, type):
        self.TYPE = type
    
    def setData(self, type, data):
        self["additional_data"].TYPE = type
        self["additional_data"].DATA = data
        self["additional_data"].COLOR = ("#ffffff", "#eeeeee")[self.additional_data_count%2]
        self["additional_data"].parse()
        self.additional_data_count += 1
