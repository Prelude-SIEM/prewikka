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


from prewikka import view, User
from prewikka.views.messagesummary import MessageParameters


class _Element:
    id = 1
    is_list = False
    check_field = None
    top_element = False
        
    def _humanizeField(self, field):
        return field.replace("_", " ").capitalize()

    def _renderNormal(self, root, field):
        name = self._humanizeField(field)
        field = "%s.%s" % (root, field)
        value = self._alert[field]
        if value is None:
            return None
        
        value = str(value)
        if value == "":
            value = "n/a"
            
        return { "name": name, "value": value }

    def _renderElement(self, root, field, idx=None):
        element = field()
        element._alert = self._alert
        
        if idx is None:
            name = element.name
        else:
            name = "%s(%d)" % (element.name, idx)
        
        if element.check_field:
            if self._alert["%s.%s.%s" % (root, name, element.check_field)] is None:
                return
        
        humanized = self._humanizeField(element.name)
        id = _Element.id
        _Element.id += 1
        entries = element.render("%s.%s" % (root, name))

        return { "name": humanized, "value": { "name": humanized, "id": id, "hidden": True, "entries": entries } }
    
    def _renderList(self, root, field):
        elements = [ ]
        count = 0
        
        while True:
            element = self._renderElement(root, field, count)
            if not element:
                break
            
            elements.append(element)
            count += 1

        return elements
    
    def render(self, root=None):
        entries = [ ]
        
        for field in self.fields:
            if type(field) is str:
                field = self._renderNormal(root, field)
                if field:
                    entries.append(field)
            else:
                if field.is_list:
                    entries += self._renderList(root, field)
                else:
                    element = self._renderElement(root, field)
                    if element:
                        entries.append(element)

        return entries



class WebService(_Element):
    name = "web_service"
    fields = "url", "cgi", "http_method", "arg("
    check_field = "url"



class SNMPService(_Element):
    name = "snmp_service"
    fields = "oid", "community", "security_name", "context_name", "context_engine_id", "command"
    check_field = "oid"



class Service(_Element):
    name = "service"
    fields = "ident", "ip_version", "name", "port", "iana_protocol_number", "iana_protocol_name", "portlist", \
             "protocol", WebService, SNMPService
    check_field = "ident"


class UserID(_Element):
    name = "user_id"
    fields = "ident", "type", "name", "number"
    check_field = "ident"
    is_list = True



class User_(_Element):
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
    fields = "ident", "name", "pid", "path", "arg(", "env("
    check_field = "ident"



class FileAccess(_Element):
    name = "file_access"
    fields = "userid", "permission("
    check_field = "userid"
    is_list = True



class Linkage(_Element):
    name = "linkage"
    fields = "category", "name", "path"
    check_field = "category"
    is_list = True



class Inode(_Element):
    name = "inode"
    fields = "change_time", "number", "major_device", "minor_device", "c_major_device", "c_minor_device"
    check_field = "change_time"



class Checksum(_Element):
    name = "checksum"
    fields = "value", "key", "algorithm"
    check_field = "value"
    is_list = True



class File(_Element):
    name = "file"
    fields = "ident", "category", "fstype", "name", "path", "create_time", "modify_time", \
             "access_time", "data_size", "disk_size", FileAccess, Linkage, Inode, Checksum
    check_field = "ident"
    is_list = True



class Target(_Element):
    name = "target"
    fields = "ident", "decoy", "interface", Node, User_, Process, Service, File
    check_field = "ident"
    is_list = True



class Source(_Element):
    name = "source"
    fields = "ident", "spoofed", "interface", Node, User_, Process, Service
    check_field = "ident"
    is_list = True

    

class Confidence(_Element):
    name = "confidence"
    fields = "rating", "confidence"
    check_field = "confidence"



class Action_(_Element):
    name = "action"
    fields = "category", "description"
    is_list = True
    check_field = "description"



class Impact(_Element):
    name = "impact"
    fields = "severity", "completion", "type", "description"



class Reference(_Element):
    name = "reference"
    fields = "origin", "name", "url", "meaning"
    is_list = True
    check_field = "origin"



class Classification(_Element):
    name = "classification"
    fields = "ident", "text", Reference
    check_field = "ident"



class AdditionalData(_Element):
    name = "additional_data"
    fields = "type", "meaning"
    is_list = True
    check_field = "type"

    def render(self, root):
        entries = _Element.render(self, root)
        value = self._alert["%s.data" % root]
        if self._alert["%s.type" % root] == "byte-string":
            value = utils.hexdump(value)
        entries.append({"name": "Data", "value": value})

        return entries



class Assessment(_Element):
    name = "assessment"
    fields = Impact, Action_, Confidence



class Analyzer(_Element):
    name = "analyzer"
    fields = [ "analyzerid", "manufacturer", "model", "version", "class", "ostype", "osversion", \
               Node, Process ]
    check_field = "analyzerid"

    def __init__(self):
        if not Analyzer in Analyzer.fields:
            Analyzer.fields.append(Analyzer)



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



class AlertDetails(_Element, view.View):
    view_name = "alert_details"
    view_parameters = MessageParameters
    view_permissions = [ User.PERM_IDMEF_VIEW ]
    view_template = "MessageDetails"
    name = "alert"
    fields = "messageid", Assessment, Analyzer, "create_time", "detect_time", "analyzer_time", \
             Source, Target, Classification, AdditionalData, ToolAlert, CorrelationAlert, \
             OverflowAlert
    top_element = True

    def render(self):
        self._alert = self.env.prelude.getAlert(self.parameters["analyzerid"], self.parameters["ident"])
        self.dataset["node"] = { "name": "Alert", "id": 0, "hidden": False, "entries": _Element.render(self, "alert") }



class HeartbeatDetails(_Element, view.View):
    view_name = "heartbeat_details"
    view_parameters = MessageParameters
    view_permissions = [ User.PERM_IDMEF_VIEW ]
    view_template = "MessageDetails"
    name = "heartbeat"
    fields = "messageid", Analyzer, "create_time", "analyzer_time", AdditionalData
    top_element = True

    def render(self):
        self._alert = self.env.prelude.getHeartbeat(self.parameters["analyzerid"], self.parameters["ident"])
        self.dataset["node"] = { "name": "Heartbeat", "id": 0, "hidden": False, "entries": _Element.render(self, "heartbeat") }
