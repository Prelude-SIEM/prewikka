import sys

from prewikka.templates import Hideable
from prewikka.modules.main.templates import MessageDetailsEntries
from prewikka import PyTpl


class _Element:
    is_list = False
    check_field = None
    top_element = False
    
    def __init__(self, alert):
        self._alert = alert
        self._entries = MessageDetailsEntries.AlertDetailsEntries()

    def _humanizeField(self, field):
        return field.replace("_", " ").capitalize()

    def _renderNormal(self, root, field):
##         if field[-1] == "(":
##             count = 0
##             while True:
##                 if self._alert["%s.%s%d)" % (root, field, count)] is None:
##                     break
##                 self._renderNormal(root, "%s%d)" % (field, count))
##                 count += 1
##             return
        
        name = self._humanizeField(field)
        field = "%s.%s" % (root, field)
        value = self._alert[field]
        value = str(value)
        if value == "":
            value = "n/a"

        self._entries.newEntry(name, value)

    def _renderElement(self, root, field):
        element = field(self._alert)
        if element.check_field:
            if self._alert["%s.%s.%s" % (root, element.name, element.check_field)] is None:
                return
        self._entries.newSection(element.render("%s.%s" % (root, element.name)))

    def _renderList(self, root, field):
        count = 0
        
        while True:
            if self._alert["%s.%s(%d).%s" % (root, field.name, count, field.check_field)] is None:
                break
            element = field(self._alert)
            self._entries.newSection(element.render("%s.%s(%d)" % (root, field.name, count)))
            count += 1
        
    def render(self, root=None):
        for field in self.fields:
            if type(field) is str:
                self._renderNormal(root, field)
            else:
                if field.is_list:
                    self._renderList(root, field)
                else:
                    self._renderElement(root, field)

        return str(Hideable.Hideable(self._humanizeField(self.name), str(self._entries), not self.top_element))



class Web(_Element):
    name = "web"
    fields = "url", "cgi", "http_method"#, "arg("
    check_field = "url"



class SNMP(_Element):
    name = "snmp"
    fields = "oid", "community", "command"
    check_field = "oid"



class Service(_Element):
    name = "service"
    fields = "ident", "name", "port", "portlist", "protocol", Web, SNMP
    check_field = "ident"


class UserID(_Element):
    name = "userid"
    fields = "ident", "type", "name", "number"
    check_field = "ident"
    is_list = True



class User(_Element):
    name = "user"
    fields = "ident", "category", UserID
    check_field = "ident"



class Address(_Element):
    name = "address"
    fields = "ident", "category", "vlan_name", "vlan_num", "address", "netmask"
    is_list = True
    check_field = "ident"



class Node(_Element):
    name = "node"
    fields = "ident", "category", "location", "name", Address
    check_field = "ident"
    


class Process(_Element):
    name = "process"
    fields = "ident", "name", "pid", "path"#, "arg(", "env("
    check_field = "ident"



class FileAccess(_Element):
    name = "file_access"
    fields = "userid", "permission("
    check_field = "userid"
    is_list = True



class File(_Element):
    name = "file"
    fields = "ident", "category", "fstype", "name", "path", "create_time", "modify_time", \
             "access_time", "data_size", "disk_size", FileAccess
    check_field = "ident"



class Files(File):
    is_list = True



class Target(_Element):
    name = "target"
    fields = "ident", "decoy", "interface", Node, User, Process, Service, Files
    check_field = "ident"
    is_list = True



class Source(_Element):
    name = "source"
    fields = "ident", "spoofed", "interface", Node, User, Process, Service
    check_field = "ident"
    is_list = True

    

class Confidence(_Element):
    name = "confidence"
    fields = "rating", "confidence"
    check_field = "confidence"


class Action(_Element):
    name = "action"
    fields = "category", "description"
    is_list = True
    check_field = "description"



class Impact(_Element):
    name = "impact"
    fields = "severity", "completion", "type", "description"



class Classification(_Element):
    name = "classification"
    fields = ("origin", "name", "url")
    is_list = True
    check_field = "origin"



class AdditionalData(_Element):
    name = "additional_data"
    fields = "type", "meaning", "data"
    is_list = True
    check_field = "type"



class Assessment(_Element):
    name = "assessment"
    fields = Impact, Action, Confidence



class Analyzer(_Element):
    name = "analyzer"
    fields = "analyzerid", "manufacturer", "model", "version", "class", "ostype", "osversion", \
             Node, Process



class AlertIdent(_Element):
    name = "alertident"
    fields = "alertident", "analyzerid"
    is_list = True
    check_field = "alertident"
    


class ToolAlert(_Element):
    name = "tool_alert"
    fields = "name", "command", AlertIdent
    check_field = "name"



class CorrelationAlert(_Element):
    name = "correlation_alert"
    fields = "name", AlertIdent
    check_field = "name"



class OverflowAlert(_Element):
    name = "overflow_alert"
    fields = "program", "size", "buffer"
    check_field = "program"



class AlertDetails(_Element):
    name = "alert"
    fields = "ident", Assessment, Analyzer, "create_time", "detect_time", "analyzer_time", \
             Source, Target, Classification, AdditionalData, ToolAlert, CorrelationAlert, \
             OverflowAlert
    top_element = True

    def __str__(self):
        return self.render("alert")



class HeartbeatDetails(_Element):
    name = "heartbeat"
    fields = "ident", Analyzer, "create_time", "analyzer_time", AdditionalData
    top_element = True

    def __str__(self):
        return self.render("heartbeat")
