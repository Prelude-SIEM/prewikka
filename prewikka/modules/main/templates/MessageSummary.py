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


from prewikka import PyTpl
from prewikka.templates import Table


class Node:
    ID = 0
    
    def __init__(self, name, level=0):
        self._name = name
        self._level = 0
        self._elements = [ ]

    def addKeyValue(self, key, value):
        self._elements.append((key, value))

    def newNode(self, name):
        node = Node(name, self._level + 1)
        self._elements.append(node)
        return node

    def __str__(self):
        content = """
        <div class='tree_node_label'>
                <p><a href='#' onClick=\"return toggleVisibility('section_%d')\">%s</a></p>
        </div>
        <div class='tree_node_level%d' id='section_%d'>
        """ % (Node.ID, self._name, self._level + 1, Node.ID)
        Node.ID += 1
        
        for element in self._elements:
            if element.__class__.__name__ == "Node":
                content += str(element)
            else:
                content += "<font color=black>%s %s</font><br/>" % (element[0], element[1])

        content += "</div>"

        return content 



class MessageSummary(PyTpl.Template):
    def __init__(self):
        PyTpl.Template.__init__(self)
        
    def beginSection(self, title):
        self._section_title = title
        self._section_entries = [ ]

    def newSectionEntry(self, name, value, emphasis=False):
        if value is None or value == "":
            return
        
        self._section_entries.append((name, value, emphasis))

    def endSection(self):
        if not self._section_entries:
            return

        row = 0

        self["section"].TITLE = self._section_title

        for name, value, emphasis in self._section_entries:
            entry_type = ("even", "odd")[row % 2]
            value_type = ("normal", "emphasis")[emphasis]
            self["section"]["entry"][entry_type]["name"].CONTENT = name
            self["section"]["entry"][entry_type]["name"].parse()
            self["section"]["entry"][entry_type]["value"][value_type].CONTENT = value
            self["section"]["entry"][entry_type]["value"][value_type].parse()
            self["section"]["entry"][entry_type]["value"].parse()
            self["section"]["entry"][entry_type].parse()
            self["section"]["entry"].parse()
            row += 1

        self["section"].parse()

    def buildAnalyzer(self, alert):
        self.beginSection("Analyzer")
        self.newSectionEntry("Analyzerid", alert["analyzer.analyzerid"])
        self.newSectionEntry("Manufacturer", alert["analyzer.manufacturer"])
        self.newSectionEntry("Model", alert["analyzer.model"], emphasis=True)
        self.newSectionEntry("Version", alert["analyzer.version"])
        self.newSectionEntry("Class", alert["analyzer.class"])
        self.newSectionEntry("Operating System", "%s %s" % (alert["analyzer.ostype"], alert["analyzer.osversion"]))
        self.newSectionEntry("Node name", alert["analyzer.node.name"])
        self.newSectionEntry("Address", alert["analyzer.node.address(0).address"])
        self.newSectionEntry("Process", alert["analyzer.process.name"])
        self.newSectionEntry("Pid", alert["analyzer.process.pid"])
        self.endSection()

    def buildAdditionalData(self, alert):
        self.beginSection("Additional Data")

        i= 0
        while True:
            meaning = alert["additional_data(%d).meaning" % i]
            if not meaning:
                break
            value = alert["additional_data(%d).data" % i]
            emphasis = (alert["analyzer.model"] == "Prelude LML" and alert["additional_data(%d).meaning" % i] == "Original Log")
            self.newSectionEntry(meaning, value, emphasis)
            i += 1
        
        self.endSection()

    


class AlertSummary(MessageSummary):
    def __init__(self, alert):
        MessageSummary.__init__(self)
        self.buildTime(alert)
        self.buildClassification(alert)
        self.buildImpact(alert)
        self.buildSource(alert)
        self.buildTarget(alert)
        self.buildAnalyzer(alert)
        self.buildAdditionalData(alert)

    def buildTime(self, alert):
        self.beginSection("Dates")
        self.newSectionEntry("Create time", alert["create_time"])
        self.newSectionEntry("Detect time", alert["detect_time"], emphasis=True)
        self.newSectionEntry("Analyzer time", alert["analyzer_time"])
        self.endSection()

    def buildClassification(self, alert):
        if not alert["classification(0).name"]:
            return
        
        self.beginSection("Classification")
        self.newSectionEntry("Name", alert["classification(0).name"], emphasis=True)
        self.newSectionEntry("Url", alert["classification(0).url"])
        self.newSectionEntry("Origin", alert["classification(0).origin"])
        self.endSection()

    def buildImpact(self, alert):
        self.beginSection("Impact")
        self.newSectionEntry("Description", alert["assessment.impact.description"], emphasis=True)
        self.newSectionEntry("Severity", alert["assessment.impact.severity"])
        self.newSectionEntry("Type", alert["assessment.impact.type"])
        self.newSectionEntry("Completion", alert["assessment.impact.completion"])
        self.endSection()

    def buildDirection(self, alert, direction):
        address = alert["%s(0).node.address(0).address" % direction]
        if address:
            port = alert["%s(0).service.port" % direction]
            if port:
                address += ":%d" % port
            protocol = alert["%s(0).service.protocol" % direction]
            if protocol:
                address += " (%s)" % protocol
            self.newSectionEntry("Address", address, emphasis=True)

        self.newSectionEntry("Interface", alert["%s(0).interface" % direction])
        self.newSectionEntry("User", alert["%s(0).user.userid(0).name" % direction])
        self.newSectionEntry("Uid", alert["%s(0).user.userid(0).number" % direction])
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



class HeartbeatSummary(MessageSummary):
    def __init__(self, heartbeat):
        MessageSummary.__init__(self)
        self.buildAnalyzer(heartbeat)
        self.buildTime(heartbeat)
        self.buildAdditionalData(heartbeat)
        
    def buildTime(self, heartbeat):
        self.beginSection("Dates")
        self.newSectionEntry("Create time", heartbeat["create_time"])
        self.newSectionEntry("Analyzer time", heartbeat["analyzer_time"])
        self.endSection()
