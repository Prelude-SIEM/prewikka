from templates import Hideable

class _Node:
    def __init__(self, alert):
        self._alert = alert
        self._content = ""

    def _humanizeField(self, field):
        return field.replace("_", " ").capitalize()

    def _renderNormal(self, root, field):
        name = self._humanizeField(field)
        field = "%s.%s" % (root, field)
        value = self._alert[field]
        self._content += "%s: %s<br/>" % (name, value)

    def _renderNode(self, root, field):
        node = field(self._alert)
        self._content += node.render("%s.%s" % (root, node.name))
        
    def render(self, root):
        for field in self.fields:
            if type(field) is str:
                self._renderNormal(root, field)
            else:
                self._renderNode(root, field)

        return str(Hideable.Hideable(self._humanizeField(self.name), self._content))



class Analyzer(_Node):
    name = "analyzer"
    fields = ("analyzerid", "manufacturer", "model", "version", "class", "ostype", "osversion")
    


class AlertDetails(_Node):
    name = "alert"
    fields = ("ident", "create_time", "detect_time", "analyzer_time", Analyzer)

    def __str__(self):
        return self.render("alert")



## class AlertDetails:
##     def __init__(self, alert):
##         self._alert = alert

##     def _newFieldValuePair(self, root, field):
##         name = field.replace("_", " ").capitalize()
##         value = self._alert[root + "." + field]
##         return "%s: %s<br/>" % (name, value)

##     def _newFieldValuePairs(self, root, fields):
##         content = ""
##         for field in fields:
##             content += self._newFieldValuePair(root, field)
##         return content

##     def _processNode(self, root):
        
##         content = self._newFieldValuePairs("%s.%s" % (root, "analyzer"),
##                                            ("ident", "category", "location", "name"))
##         content += self._process

##     def _processAnalyzer(self, root):
##         content = self._newFieldValuePairs("%s.%s" % (root, "analyzer"),
##                                            ("analyzerid", "manufacturer", "model", "version", "class", "ostype", "osversion"))
##         return str(Hideable.Hideable("Analyzer", content))
        
##     def _processAlert(self):
##         fields = ("ident", "create_time", "detect_time", "analyzer_time")

##         content = self._newFieldValuePairs("alert", fields)
##         content += self._processAnalyzer("alert")

##         return str(Hideable.Hideable("Alert", content))
        
##     def __str__(self):
##         return self._processAlert()
