import PyTpl
import sys

class AlertDetails(PyTpl.Template):
    def __init__(self, alert):
        PyTpl.Template.__init__(self)
	self.buildTime(alert)
	self.buildClassifications(alert)
        self.buildImpact(alert)

    def buildTime(self, alert):
        self.CREATE_TIME = alert["alert.create_time"] or "n/a"
        self.DETECT_TIME = alert["alert.detect_time"] or "n/a"
        self.ANALYZER_TIME = alert["alert.analyzer_time"] or "n/a"

    def buildClassifications(self, alert):
        i = 0
        while True:
            name = alert["alert.classification(%d).name" % i]
            if not name:
                break
            self["classification"].ORIGIN = alert["alert.classification(%d).origin" % i] or "n/a"
            url = alert["alert.classification(%d).url" % i]
            if url:
                sys.stderr.write("url: %s\n" % url)
                self["classification"]["linked"].NAME = name
                self["classification"]["linked"].URL = url
                self["classification"]["linked"].parse()
            else:
                self["classification"]["normal"].NAME = name
                self["classification"]["normal"].parse()
            self["classification"].parse()
            i += 1

    def buildImpact(self, alert):
        self["impact"].SEVERITY = alert["alert.assessment.impact.severity"]
        self["impact"].COMPLETION = alert["alert.assessment.impact.completion"]
        self["impact"].TYPE = alert["alert.assessment.impact.type"]
        self["impact"].DESCRIPTION = alert["alert.assessment.impact.description"]
        self["impact"].parse()

    def buildNode(self, alert, source):
        return """
        <>

        

        
        """
        

    def buildSource(self, alert):
        

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
