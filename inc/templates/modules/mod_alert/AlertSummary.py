import PyTpl
from templates import Table

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



class AlertSummary(PyTpl.Template):
    def __init__(self, alert):
        PyTpl.Template.__init__(self)
        self.buildTime(alert)
        self.buildClassification(alert)
        self.buildImpact(alert)
        self.buildSource(alert)
        self.buildTarget(alert)
        self.buildAnalyzer(alert)
        self.buildAdditionalData(alert)

    def createKeyValueListSection(self, title, fields):
        section = KeyValueListSection(fields)
        if len(section) > 0:
            self.newSection(title, str(section))

    def createTableSection(self, title, header, rows):
        self.newSection(title, str(TableSection(header, rows)))

    def newTable(self):
        table = Table.Table()
        table.setWidth(["15%", "*"])
        return table

    def createKeyValueListSection(self, title, fields):
        count = 0
        table = Table.Table()
        table.setWidth(["15%", "*"])
        for name, value, emphasis in fields:
            if not value:
                continue
            count += 1

            if emphasis:
                value = _emphasis(value)

            table.addRow((name, value))

        if count:
            self.newSection(title, str(table))

    def createTableSection(self, title, header, rows):
        table = Table.Table()
        table.setWidth(["15%", "*"])
        for row in [ header ] + rows:
            table.addRow(row)
        
        self.createSection(title, str(table))

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

    def buildTime(self, alert):
        self.beginSection("Dates")
        self.newSectionEntry("Create time", alert["alert.create_time"])
        self.newSectionEntry("Detect time", alert["alert.detect_time"], emphasis=True)
        self.newSectionEntry("Analyzer time", alert["alert.analyzer_time"])
        self.endSection()

    def buildClassification(self, alert):
        if not alert["alert.classification(0).name"]:
            return
        
        self.beginSection("Classification")
        self.newSectionEntry("Name", alert["alert.classification(0).name"], emphasis=True)
        self.newSectionEntry("Url", alert["alert.classification(0).url"])
        self.newSectionEntry("Origin", alert["alert.classification(0).origin"])
        self.endSection()

    def buildImpact(self, alert):
        self.beginSection("Impact")
        self.newSectionEntry("Description", alert["alert.assessment.impact.description"], emphasis=True)
        self.newSectionEntry("Severity", alert["alert.assessment.impact.severity"])
        self.newSectionEntry("Type", alert["alert.assessment.impact.type"])
        self.newSectionEntry("Completion", alert["alert.assessment.impact.completion"])
        self.endSection()

    def buildDirection(self, alert, direction):
        address = alert["alert.%s(0).node.address(0).address" % direction]
        if address:
            port = alert["alert.%s(0).service.port" % direction]
            if port:
                address += ":%d" % port
            protocol = alert["alert.%s(0).service.protocol" % direction]
            if protocol:
                address += " (%s)" % protocol
            self.newSectionEntry("Address", address, emphasis=True)

        self.newSectionEntry("Interface", alert["alert.%s(0).interface" % direction])
        self.newSectionEntry("User", alert["alert.%s(0).user.userid(0).name" % direction])
        self.newSectionEntry("Uid", alert["alert.%s(0).user.userid(0).number" % direction])
        self.newSectionEntry("Process", alert["alert.%s(0).process.name" % direction])

    def buildSource(self, alert):
        self.beginSection("Source")
        self.buildDirection(alert, "source")
        self.endSection()

    def buildTarget(self, alert):
        self.beginSection("Target")
        self.buildDirection(alert, "target")
        self.newSectionEntry("File", alert["alert.target(0).file(0).name"])
        self.endSection()

    def buildAnalyzer(self, alert):
        self.beginSection("Analyzer")
        self.newSectionEntry("Analyzerid", alert["alert.analyzer.analyzerid"])
        self.newSectionEntry("Manufacturer", alert["alert.analyzer.manufacturer"])
        self.newSectionEntry("Model", alert["alert.analyzer.model"], emphasis=True)
        self.newSectionEntry("Version", alert["alert.analyzer.version"])
        self.newSectionEntry("Class", alert["alert.analyzer.class"])
        self.newSectionEntry("Operating System", "%s %s" % (alert["alert.analyzer.ostype"], alert["alert.analyzer.osversion"]))
        self.newSectionEntry("Node name", alert["alert.analyzer.node.name"])
        self.newSectionEntry("Address", alert["alert.analyzer.node.address(0).address"])
        self.newSectionEntry("Process", alert["alert.analyzer.process.name"])
        self.newSectionEntry("Pid", alert["alert.analyzer.process.pid"])
        self.endSection()

    def buildAdditionalData(self, alert):
        self.beginSection("Additional Data")

        i= 0
        while True:
            meaning = alert["alert.additional_data(%d).meaning" % i]
            if not meaning:
                break
            value = alert["alert.additional_data(%d).data" % i]
            emphasis = (alert["alert.analyzer.model"] == "Prelude LML" and alert["alert.additional_data(%d).meaning" % i] == "Original Log")
            self.newSectionEntry(meaning, value, emphasis)
            i += 1
        
        self.endSection()

    def buildDetails(self, alert):
        alert_node = Node("Alert")
        alert_node.addKeyValue("Ident", alert["alert.ident"])
        alert_node.addKeyValue("Create Time", alert["alert.create_time"])
        alert_node.addKeyValue("Detect Time", alert["alert.detect_time"])
        fake_node = alert_node.newNode("Fake Node")
        fake_node.addKeyValue("fake key", "fake node")
        fake_node = fake_node.newNode("Fake Node")
        fake_node.addKeyValue("fake key", "fake node")
        self.TEST = str(alert_node)
