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


from prewikka import view, User, utils


class MessageParameters(view.RelativeViewParameters):
    def register(self):
        view.RelativeViewParameters.register(self)
        self.mandatory("ident", long)



class MessageSummary:
    view_parameters = MessageParameters
    view_permissions = [ User.PERM_IDMEF_VIEW ]
    view_template = "MessageSummary"
    
    def beginSection(self, title):
        self._current_section = { }
        self._current_section["title"] = title
        self._current_section["entries"] = [ ]

    def newSectionEntry(self, name, value, emphase=False):
        if value is None or value == "":
            return

        self._current_section["entries"].append({ "name": name,
                                                  "value": value,
                                                  "emphase": emphase })

    def endSection(self):
        if self._current_section["entries"]:
            self.dataset["sections"].append(self._current_section)

    def buildAnalyzer(self, alert):
        index = 0
        
        while True:
            if not alert["analyzer(%d).analyzerid" % index]:
                break
        
            self.beginSection("Analyzer")
            self.newSectionEntry("Analyzerid", alert["analyzer(%d).analyzerid" % index])
            self.newSectionEntry("Manufacturer", alert["analyzer(%d).manufacturer" % index])
            self.newSectionEntry("Model", alert["analyzer(%d).model" % index], emphase=True)
            self.newSectionEntry("Version", alert["analyzer(%d).version" % index])
            self.newSectionEntry("Class", alert["analyzer(%d).class" % index])
            self.newSectionEntry("Operating System", "%s %s" %
                                 (alert["analyzer(%d).ostype" % index], alert["analyzer(%d).osversion" % index]))
            self.newSectionEntry("Node name", alert["analyzer(%d).node.name" % index])
            self.newSectionEntry("Address", alert["analyzer(%d).node.address(0).address" % index])
            self.newSectionEntry("Process", alert["analyzer(%d).process.name" % index])
            self.newSectionEntry("Pid", alert["analyzer(%d).process.pid" % index])
            self.endSection()

            index += 1

    def buildAdditionalData(self, alert):
        self.beginSection("Additional Data")
        
        i= 0
        while True:
            meaning = alert["additional_data(%d).meaning" % i]
            if not meaning:
                break
            value = alert.get("additional_data(%d).data" % i, escape=False)
            if alert["additional_data(%d).type" % i] == "byte-string":
                value = utils.hexdump(value)
            emphase = (alert["analyzer.model"] == "Prelude LML" and
                       alert["additional_data(%d).meaning" % i] == "Original Log")
            self.newSectionEntry(meaning, value, emphase)
            i += 1
        
        self.endSection()



class AlertSummary(MessageSummary, view.View):
    view_name = "alert_summary"
    
    def buildTime(self, alert):
        self.beginSection("Dates")
        self.newSectionEntry("Create time", alert["create_time"])
        self.newSectionEntry("Detect time", alert["detect_time"], emphase=True)
        self.newSectionEntry("Analyzer time", alert["analyzer_time"])
        self.endSection()

    def buildClassification(self, alert):
        if not alert["classification.text"]:
            return

        self.beginSection("Classification")
        self.newSectionEntry("Text", alert["classification.text"])

        cnt = 0

        while True:
            origin = alert["classification.reference(%d).origin" % cnt]
            if origin == None:
                break

            content = alert["classification.reference(%d).name" % cnt]
            
            meaning = alert["classification.reference(%d).meaning" % cnt]
            if meaning:
                content += " (%s)" % meaning

            url = alert["classification.reference(%d).url" % cnt]
            if url:
                content += " <a href='%s'>%s</a>" % (url, url)

            self.newSectionEntry(origin, content)

            cnt += 1

        self.endSection()

    def buildImpact(self, alert):
        self.beginSection("Impact")
        self.newSectionEntry("Description", alert["assessment.impact.description"], emphase=True)
        self.newSectionEntry("Severity", alert["assessment.impact.severity"])
        self.newSectionEntry("Type", alert["assessment.impact.type"])
        self.newSectionEntry("Completion", alert["assessment.impact.completion"])
        self.endSection()

    def buildDirection(self, alert, direction):
        address = alert["%s(0).node.address(0).address" % direction]
        if address:
            port = alert["%s(0).service.port" % direction]
            if port != None:
                address += ":%d" % port
            protocol = alert["%s(0).service.protocol" % direction]
            if protocol:
                address += " (%s)" % protocol
            self.newSectionEntry("Address", address, emphase=True)

        self.newSectionEntry("Interface", alert["%s(0).interface" % direction])
        self.newSectionEntry("User", alert["%s(0).user.user_id(0).name" % direction])
        self.newSectionEntry("Uid", alert["%s(0).user.user_id(0).number" % direction])
        self.newSectionEntry("Process", alert["%s(0).process.name" % direction])

    def buildSource(self, alert):
        self.beginSection("Source")
        self.buildDirection(alert, "source")
        self.endSection()

    def buildTarget(self, alert):
        self.beginSection("Target")
        self.buildDirection(alert, "target")
        self.newSectionEntry("File", alert["target(0).file(0).name"])
        self.endSection()

    def render(self):
        alert = self.env.idmef_db.getAlert(self.parameters["ident"])
        self.dataset["sections"] = [ ]
        self.buildTime(alert)
        self.buildClassification(alert)
        self.buildImpact(alert)
        self.buildSource(alert)
        self.buildTarget(alert)
        self.buildAnalyzer(alert)
        self.buildAdditionalData(alert)



class HeartbeatSummary(MessageSummary, view.View):
    view_name = "heartbeat_summary"
    
    def buildTime(self, heartbeat):
        self.beginSection("Dates")
        self.newSectionEntry("Create time", heartbeat["create_time"])
        self.newSectionEntry("Analyzer time", heartbeat["analyzer_time"])
        self.endSection()

    def render(self):
        heartbeat = self.env.idmef_db.getHeartbeat(self.parameters["ident"])
        self.dataset["sections"] = [ ]
        self.buildAnalyzer(heartbeat)
        self.buildTime(heartbeat)
        self.buildAdditionalData(heartbeat)
