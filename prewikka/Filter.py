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


import re

class Error(Exception):
    pass


ALERT_OBJECTS = ("alert.ident",
                 "alert.assessment.impact.severity",
                 "alert.assessment.impact.completion",
                 "alert.assessment.impact.type",
                 "alert.assessment.impact.description",
                 "alert.assessment.action.category",
                 "alert.assessment.action.description",
                 "alert.assessment.confidence.rating",
                 "alert.assessment.confidence.confidence",
                 "alert.analyzer.analyzerid",
                 "alert.analyzer.manufacturer",
                 "alert.analyzer.model",
                 "alert.analyzer.version",
                 "alert.analyzer.class",
                 "alert.analyzer.ostype",
                 "alert.analyzer.osversion",
                 "alert.analyzer.node.ident",
                 "alert.analyzer.node.category",
                 "alert.analyzer.node.location",
                 "alert.analyzer.node.name",
                 "alert.analyzer.node.address.ident",
                 "alert.analyzer.node.address.category",
                 "alert.analyzer.node.address.vlan_name",
                 "alert.analyzer.node.address.vlan_num",
                 "alert.analyzer.node.address.address",
                 "alert.analyzer.node.address.netmask",
                 "alert.analyzer.process.ident",
                 "alert.analyzer.process.name",
                 "alert.analyzer.process.pid",
                 "alert.analyzer.process.path",
                 "alert.analyzer.process.arg.string",
                 "alert.analyzer.process.env.string",
                 "alert.create_time.sec",
                 "alert.create_time.usec",
                 "alert.detect_time.sec",
                 "alert.detect_time.usec",
                 "alert.analyzer_time.sec",
                 "alert.analyzer_time.usec",
                 "alert.source.ident",
                 "alert.source.spoofed",
                 "alert.source.interface",
                 "alert.source.node.ident",
                 "alert.source.node.category",
                 "alert.source.node.location",
                 "alert.source.node.name",
                 "alert.source.node.address.ident",
                 "alert.source.node.address.category",
                 "alert.source.node.address.vlan_name",
                 "alert.source.node.address.vlan_num",
                 "alert.source.node.address.address",
                 "alert.source.node.address.netmask",
                 "alert.source.user.ident",
                 "alert.source.user.category",
                 "alert.source.user.userid.ident",
                 "alert.source.user.userid.type",
                 "alert.source.user.userid.name",
                 "alert.source.user.userid.number",
                 "alert.source.process.ident",
                 "alert.source.process.name",
                 "alert.source.process.pid",
                 "alert.source.process.path",
                 "alert.source.process.arg.string",
                 "alert.source.process.env.string",
                 "alert.source.service.ident",
                 "alert.source.service.name",
                 "alert.source.service.port",
                 "alert.source.service.portlist",
                 "alert.source.service.protocol",
                 "alert.source.service.type",
                 "alert.source.service.web.url",
                 "alert.source.service.web.cgi",
                 "alert.source.service.web.http_method",
                 "alert.source.service.web.arg.arg",
                 "alert.source.service.snmp.oid",
                 "alert.source.service.snmp.community",
                 "alert.source.service.snmp.command",
                 "alert.target.ident",
                 "alert.target.decoy",
                 "alert.target.interface",
                 "alert.target.node.ident",
                 "alert.target.node.category",
                 "alert.target.node.location",
                 "alert.target.node.name",
                 "alert.target.node.address.ident",
                 "alert.target.node.address.category",
                 "alert.target.node.address.vlan_name",
                 "alert.target.node.address.vlan_num",
                 "alert.target.node.address.address",
                 "alert.target.node.address.netmask",
                 "alert.target.user.ident",
                 "alert.target.user.category",
                 "alert.target.user.userid.ident",
                 "alert.target.user.userid.type",
                 "alert.target.user.userid.name",
                 "alert.target.user.userid.number",
                 "alert.target.process.ident",
                 "alert.target.process.name",
                 "alert.target.process.pid",
                 "alert.target.process.path",
                 "alert.target.process.arg.string",
                 "alert.target.process.env.string",
                 "alert.target.service.ident",
                 "alert.target.service.name",
                 "alert.target.service.port",
                 "alert.target.service.portlist",
                 "alert.target.service.protocol",
                 "alert.target.service.type",
                 "alert.target.service.web.url",
                 "alert.target.service.web.cgi",
                 "alert.target.service.web.http_method",
                 "alert.target.service.web.arg.arg",
                 "alert.target.service.snmp.oid",
                 "alert.target.service.snmp.community",
                 "alert.target.service.snmp.command",
                 "alert.target.file.ident",
                 "alert.target.file.category",
                 "alert.target.file.fstype",
                 "alert.target.file.name",
                 "alert.target.file.path",
                 "alert.target.file.create_time.sec",
                 "alert.target.file.create_time.usec",
                 "alert.target.file.modify_time.sec",
                 "alert.target.file.modify_time.usec",
                 "alert.target.file.access_time.sec",
                 "alert.target.file.access_time.usec",
                 "alert.target.file.data_size",
                 "alert.target.file.disk_size",
                 "alert.target.file.file_access.userid.ident",
                 "alert.target.file.file_access.userid.type",
                 "alert.target.file.file_access.userid.name",
                 "alert.target.file.file_access.userid.number",
                 "alert.target.file.file_access.permission.string",
                 "alert.target.file.file_linkage",
                 "alert.target.file.inode.change_time.sec",
                 "alert.target.file.inode.change_time.usec",
                 "alert.target.file.inode.number",
                 "alert.target.file.inode.major_device",
                 "alert.target.file.inode.minor_device",
                 "alert.target.file.inode.c_major_device",
                 "alert.target.file.inode.c_minor_device",
                 "alert.classification.origin",
                 "alert.classification.name",
                 "alert.classification.url",
                 "alert.additional_data.type",
                 "alert.additional_data.meaning",
                 "alert.additional_data.dlen",
                 "alert.additional_data.data",
                 "alert.type",
                 "alert.tool_alert.name",
                 "alert.tool_alert.command",
                 "alert.tool_alert.alertident.alertident",
                 "alert.tool_alert.alertident.analyzerid",
                 "alert.correlation_alert.name",
                 "alert.correlation_alert.alertident.alertident",
                 "alert.correlation_alert.alertident.analyzerid",
                 "alert.overflow_alert.program",
                 "alert.overflow_alert.size",
                 "alert.overflow_alert.buffer")

HEARTBEAT_OBJECTS = ("heartbeat.ident",
                     "heartbeat.analyzer.analyzerid",
                     "heartbeat.analyzer.manufacturer",
                     "heartbeat.analyzer.model",
                     "heartbeat.analyzer.version",
                     "heartbeat.analyzer.class",
                     "heartbeat.analyzer.ostype",
                     "heartbeat.analyzer.osversion",
                     "heartbeat.analyzer.node.ident",
                     "heartbeat.analyzer.node.category",
                     "heartbeat.analyzer.node.location",
                     "heartbeat.analyzer.node.name",
                     "heartbeat.analyzer.node.address.ident",
                     "heartbeat.analyzer.node.address.category",
                     "heartbeat.analyzer.node.address.vlan_name",
                     "heartbeat.analyzer.node.address.vlan_num",
                     "heartbeat.analyzer.node.address.address",
                     "heartbeat.analyzer.node.address.netmask",
                     "heartbeat.analyzer.process.ident",
                     "heartbeat.analyzer.process.name",
                     "heartbeat.analyzer.process.pid",
                     "heartbeat.analyzer.process.path",
                     "heartbeat.analyzer.process.arg.string",
                     "heartbeat.analyzer.process.env.string",
                     "heartbeat.create_time.sec",
                     "heartbeat.create_time.usec",
                     "heartbeat.analyzer_time.sec",
                     "heartbeat.analyzer_time.usec",
                     "heartbeat.additional_data.type",
                     "heartbeat.additional_data.meaning",
                     "heartbeat.additional_data.dlen",
                     "heartbeat.additional_data.data")



class _Filter:
    def __init__(self, name, comment, elements, formula):
        for element in elements.values():
            if not element[0] in self._objects:
                raise Error("invalid object %s" % element[0])
        
        self.name = name
        self.comment = comment
        self.elements = elements
        self.formula = formula

    def _replace(self, element):
        element = element.group(1)
        if element in ("and", "AND", "&&"):
            return "&&"
        if element in ("or", "OR", "||"):
            return "||"
        return "%s %s '%s'" % tuple(self.elements[element])

    def __str__(self):
        return re.sub("(\w+)", self._replace, self.formula)



class AlertFilter(_Filter):
    type = "alert"
    _objects = ALERT_OBJECTS



class HeartbeatFilter(_Filter):
    type = "heartbeat"
    _objects = HEARTBEAT_OBJECTS
        


if __name__ == "__main__":
    print Filter("foo", "",
                 { "A": ("alert.ident", "=", "1"),
                   "B": ("alert.ident", "=", "2") },
                 "(A or B)")
