# Copyright (C) 2004,2005 PreludeIDS Technologies. All Rights Reserved.
# Author: Nicolas Delon <nicolas.delon@prelude-ids.com>
#
# This file is part of the Prewikka program.
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

import time
import struct
import socket
from prewikka import view, User, utils


def isFlagSet(bits, flag, shift=0):    
    if (bits & flag) >> shift:
        return "X"
    else:
        return "&nbsp;"


class Table:
    def __init__(self):
        self._current_table = None
        self._current_section = None

    def getCurrentSection(self):
        return self._current_section
    
    def beginSection(self, title, display="table"):    
        _current_section = { }
        _current_section["title"] = title
        _current_section["entries"] = [ ]
        _current_section["tables"] = [ ]
        _current_section["display"] = display
        _current_section["sections"] = []
        _current_section["parent"] = self._current_section
        
        self._current_section = _current_section
            
    def endSection(self):
        parent = self._current_section["parent"]

        if len(self._current_section["tables"]) == 0 and   \
           len(self._current_section["sections"]) == 0 and \
           len(self._current_section["entries"]) == 0:
            self._current_section = parent
            return
        
        if not parent:
            self.dataset["sections"].append(self._current_section)
            self._current_section = None
        else:
            parent["sections"].append(self._current_section)
            self._current_section = parent                
        
    def newSectionEntry(self, name, value, emphase=False):
        if value is None or value == "":
            return

        self._current_section["entries"].append({ "name": name,
                                                  "value": value,
                                                  "emphase": emphase })

    def beginTable(self, cl="", style="", odd_even=False):
        table = {}
        table["rows"] = []
        table["odd_even"] = odd_even
        table["class"] = cl
        table["style"] = style
        table["parent"] = self._current_table or self._current_section
        self._current_table = table

        
    def endTable(self):
        parent = self._current_table["parent"]
        has_data = False
        
        if len(self._current_table["rows"]) <= 1 :
            if not parent or not parent.has_key("rows"):
                self._current_table = None
            else:
                self._current_table = parent
            return
                
        if not parent:
            self._current_section["tables"].append(self._current_table)
            self._current_table = None
        else:
            if parent.has_key("rows"):                    
                col = { "name": None, "header": None, "emphase": None, "tables": [ self._current_table ] }
                if len(parent["rows"]):
                    parent["rows"][-1] += [col]
                else:
                    parent["rows"].append([col])
                self._current_table = parent
            else:
                parent["tables"].append(self._current_table)     
                self._current_table = None        

    def newTableRow(self):
        if len(self._current_table["rows"]) and self._current_table["rows"][-1] != []:
            self._current_table["rows"].append([])

        return len(self._current_table["rows"])
    
    def newTableCol(self, row_index, name, cl="", header=False, emphase=None):
        col = { "name": name, "header": header, "class": cl, "tables": [], "emphase": None }

        if row_index == -1:
            self._current_table["rows"].append([col])
           
        elif len(self._current_table["rows"]) <= row_index:
            self._current_table["rows"].insert(row_index, [col])

        else:            
            self._current_table["rows"][row_index] += [col]
                        
    def newTableEntry(self, name, value, cl="", emphase=False):        
        if not value:
            return
                    
        self.newTableCol(0, name, cl=cl, header=True)
        self.newTableCol(1, value, cl=cl, header=False, emphase=emphase)
        


class HeaderTable(Table):
    def __init__(self):
        self.field_list = [ ]
                
    def register_static(self, name, static):
        self.field_list.append((None, name, static, None, None))

    def register(self, name, field, func=None, arguments=()):
        self.field_list.append((field, name, None, func, arguments))

    def render_table(self, section, name, dataset):
        self._current_section = section._current_section
        self._current_table = section._current_table

        from_dataset = False
        self.newTableRow()
        self.newTableCol(-1, name, header=True)
        
        self.beginTable()
        
        for field in self.field_list:
                    
            if not dataset.has_key(field[0]) and not field[2]:
                continue
                
            if field[2]:
                # static
                s = field[2]
            else:
                value = dataset[field[0]]

                if field[3]:
                    # use func
                    s = field[3](value, *field[4])

                else:
                    from_dataset = True
                    s = value

            self.newTableEntry(field[1], s)

        if not from_dataset:
            section._current_table["rows"].pop()
            self._current_table = section._current_table
        else:
            self.endTable()
        

class TcpIpOptions(Table):
    def _decodeOption8(self, data):
        return str(struct.unpack(">B", data)[0])

    def _decodeOption16(self, data):
        return str(struct.unpack(">H", data)[0])

    def _decodeOption32(self, data):
        return str(struct.unpack(">L", data)[0])

    def _decodeOptionTimestamp(self, data):
        x = struct.unpack(">LL", data)
        return "TS Value (%d)<br/>TS Echo Reply (%d)" % (x[0], x[1])

    def _decodeOptionSack(self, data):
        x = struct.unpack(">" + "L" * (len(data) / 4), data)
        
        s = ""
        for i in x:
            if len(s):
                s += "<br/>"

            s += str(i)

        return s


    def _decodeOptionMd5(self, data):
        md = md5.md5(struct.unpack(">B" * 16, data)[0])
        return md.hexdigest()

    def _decodeOptionPartialOrderProfile(self, data):
        x = struct.unpack(">B", data)
        return "Start_Flags=%d End_Flags=%d" % (data & 0x80, data & 0x40)

    def _decodeOptionTcpAltChecksumRequest(self, data):
        x = struct.unpack(">B", data)
        if x == 0:
            return "TCP checksum"

        elif x == 1:
            return "8-bit Fletcher's algorithm"

        elif x == 2:
            return "16-bit Fletcher's algorithm"

        else:
            return "%d (Invalid)" % x

    
    def _tcpOptionToName(self, opt):
        h = {}
        h[0] = ("End of Option List", 0)
        h[1] = ("No-Option", 0)
        h[2] = ("Maximum Segment Size", 2, self._decodeOption16)
        h[3] = ("Window Scaling", 1, self._decodeOption8)
        h[4] = ("Sack Permitted", 0)
        h[5] = ("Sack", -1, self._decodeOptionSack)
        h[6] = ("Echo", 4, self._decodeOption32)
        h[7] = ("Echo Reply", 4, self._decodeOption32)
        h[8] = ("Timestamp", 8, self._decodeOptionTimestamp)
        h[9] = ("Partial Order Permitted", 0)
        h[10] = ("Partial Order Profile", 1, self._decodeOptionPartialOrderProfile)
        h[11] = ("Connection Count", 4, self._decodeOption32)
        h[12] = ("Connection Count New", 4, self._decodeOption32)
        h[13] = ("Connection Count Echo", 4, self._decodeOption32)
        h[14] = ("TCP Alternate Checksum Request", 1, self._decodeOptionTcpAltChecksumRequest)
        h[15] = ("TCP Alternate Checksum",)
        h[16] = ("Skeeter",)
        h[17] = ("Bubba",)
        h[18] = ("Trailer Checksum",)
        h[19] = ("MD5 Signature", 16, self._decodeOptionMd5)
        h[20] = ("Capabilities",)
        h[21] = ("Selective Negative Acknowledgements",)
        h[22] = ("Record Boundaries",)
        h[23] = ("Corruption experienced",)
        h[24] = ("Snap",)
        h[25] = ("Unassigned",)
        h[26] = ("TCP Compression Filter",)

        return h.get(opt, ("Unknown",))

    
    def _ipOptionToName(self, opt):
        h = {}
        h[0] = ("End of Option List", 0)
        h[1] = ("No-Option", 0)
        h[7] = ("RR",)
        h[20] = ("RTRALT",)
        h[68] = ("Timestamp",)
        h[130] = ("Security", )
        h[131] = ("LSRR", 0)
        h[132] = ("LSRR_E", 0)
        h[136] = ("SATID", 0)
        h[137] = ("SSRR", 0)
            
        return h.get(opt, ("Unknown",))

    def _optionRender(self, options, to_name_func):
        self.beginTable()
        self.newTableCol(0, "Name", header=True)
        self.newTableCol(0, "Code", header=True)
        self.newTableCol(0, "Data length", header=True)
        self.newTableCol(0, "Data", header=True)
        
        for option in options:
            dec = to_name_func(option[0])
            
            idx = self.newTableRow()
            self.newTableCol(idx, dec[0])
            self.newTableCol(idx, option[0])
            
            if len(dec) == 2 and dec[1] != -1 and dec[1] != option[1]:
                self.newTableCol(idx, "<b style='color:red;'>%d</b> (expected %d)" % (option[1], dec[1]))
            else:
                self.newTableCol(idx, "%d" % option[1])

            if len(dec) == 3 and (dec[1] == -1 or dec[1] == option[1]):
                self.newTableCol(idx, "%s" % dec[2](option[2]))
            else:
                self.newTableCol(idx, "&nbsp;")
                        
        self.endTable()

    def ipOptionRender(self, ip_options):
        if not ip_options:
            return

        self.newTableRow()
        self.newTableCol(-1, "IP options", header=True)

        self._optionRender(ip_options, self._ipOptionToName)

        
    def tcpOptionRender(self, tcp_options):
        if not tcp_options:
            return

        self.newTableRow()
        self.newTableCol(-1, "TCP options", header=True)

        self._optionRender(tcp_options, self._tcpOptionToName)


        
class MessageParameters(view.RelativeViewParameters):
    def register(self):
        view.RelativeViewParameters.register(self)
        self.mandatory("ident", long)



class MessageSummary(Table):
    view_parameters = MessageParameters
    view_permissions = [ User.PERM_IDMEF_VIEW ]
    view_template = "MessageSummary"

    def getUrlLink(self, url):
        if not url:
            return None
        
        external_link_new_window = self.env.config.general.getOptionValue("external_link_new_window", "true")

        if (not external_link_new_window and self.env.config.general.has_key("external_link_new_window")) or \
               (external_link_new_window == None or external_link_new_window.lower() in [ "true", "yes" ]):
            target = "_blank"
        else:
            target = "_self"
                
        return "<a target='%s' href='%s'>%s</a>" % (target, url, url)
                
    def getTime(self, t):
        if not t:
            return None

        s = t.toYMDHMS()
        if t.usec:
            s += ".%d" % t.usec

        if t.gmt_offset:
            s += " %+.2d:00" % (t.gmt_offset / (60 * 60))

        return s
    
    def buildTime(self, msg):
        self.beginTable()

        self.newTableEntry("Create time", self.getTime(msg["create_time"]))

        try:
            self.newTableEntry("Detect time", self.getTime(msg["detect_time"]), cl="section_alert_entry_value_emphasis")
        except:
            pass
        
        if msg["analyzer_time"]:
            self.newTableEntry("Analyzer time", self.getTime(msg["analyzer_time"]))
            
        self.endTable()

    def buildProcess(self, process):
        self.beginTable()
        self.newTableEntry("Process", process["name"])
        self.newTableEntry("Process Path", process["path"])
        self.newTableEntry("Process Pid", process["pid"])
        self.endTable()

        
    def buildNode(self, node):
        if not node:
            return
        
        self.newTableEntry("Node name", node["name"])
        self.newTableEntry("Node location", node["location"])
        
        addr_list = ""
        for addr in node["address"]:
            address = addr["address"]
            if not address:
                continue

            if len(addr_list) > 0:
                addr_list += "<br/>"
                
            addr_list += address
                        
        self.newTableEntry("Node address", addr_list)
                
    def buildAnalyzer(self, analyzer):
        self.beginTable()
        
        self.beginTable()
        self.newTableEntry("Model", analyzer["model"], cl="section_alert_entry_value_emphasis")
        self.newTableEntry("Name", analyzer["name"], cl="section_alert_entry_value_emphasis")
        self.newTableEntry("Analyzerid", analyzer["analyzerid"])
        self.newTableEntry("Version", analyzer["version"])
        self.newTableEntry("Class", analyzer["class"])
            
        self.newTableEntry("Manufacturer", self.getUrlLink(analyzer["manufacturer"]))                
        self.endTable()
        self.newTableRow()
                
        self.beginTable()
        
        self.buildNode(analyzer["node"])
        if analyzer["ostype"] or analyzer["osversion"]:
                self.newTableEntry("Operating System", "%s %s" % (analyzer["ostype"] or "", analyzer["osversion"] or ""))

        self.endTable()
        self.newTableRow()
        
        if analyzer["process"]:
            self.buildProcess(analyzer["process"])
            self.newTableRow()

        self.endTable()
        
    def buildAnalyzerList(self, alert):
        l = []
        for analyzer in alert["analyzer"]:
            l.insert(0, analyzer)

        l.pop(0)

        self.beginSection("Analyzer Path (%d not shown)" % len(l), display="none")
        
        self.beginTable()
        i = 1
        for analyzer in l:
            self.newTableCol(i - 1, "Analyzer #%d" % i, None, header=True)
            self.buildAnalyzer(analyzer)
            self.newTableRow()
            i += 1

        self.endTable()
        self.endSection()
        
    def buildAdditionalData(self, alert, ignore=[], ignored={}, ip_options=[], tcp_options=[]):
        self.beginSection("Additional data")
        
        self.beginTable()
        self.newTableCol(0, "Meaning", header=True)
        self.newTableCol(0, "Value", header=True)
        
        index = 1
        for ad in alert["additional_data"]:
            value = None
            meaning = ad["meaning"]
            
            if meaning == "ip_option_code":
                ip_options.append((ad["data"], 0, None))
                ignored[meaning] = ""
                
            if meaning == "ip_option_data":
                data = ad["data"]
                ip_options[-1] = (ip_options[-1][0], len(data), data)
                ignored[meaning] = ""
                
            if meaning == "tcp_option_code":
                tcp_options.append((ad["data"], 0, None))
                ignored[meaning] = ""
                
            if meaning == "tcp_option_data":
                data = ad["data"]
                tcp_options[-1] = (tcp_options[-1][0], len(data), data)
                ignored[meaning] = ""
                
            if ad["data"] != None:
                if ad["type"] == "byte-string":
                    value = utils.hexdump(ad.get("data", escape=False))
                else:
                    value = ad.get("data")

            for field in ignore:
                if meaning == field[0]:
                    ignored[meaning] = value
                    break
                
            if not ignored.has_key(meaning):
                self.newTableCol(index, meaning or "Data content")
                self.newTableCol(index, value)
                index += 1
                
        self.endTable()
        self.endSection()
        
    def buildIpHeaderTable(self, alert):
        ip = HeaderTable()
        ip.register("Version", "ip_ver")
        ip.register("Header length", "ip_hlen")
        ip.register("TOS", "ip_tos")
        ip.register("Length", "ip_len")
        ip.register("Id", "ip_id")
        ip.register("R<br/>F", "ip_off", isFlagSet, (0x8000, 15))
        ip.register("D<br/>F", "ip_off", isFlagSet, (0x4000, 14))
        ip.register("M<br/>F", "ip_off", isFlagSet, (0x2000, 13))
        ip.register("Ip offset", "ip_off", (lambda x: x & 0x1fff))
        ip.register("TTL", "ip_ttl")
        ip.register("Protocol", "ip_proto")
        ip.register("Checksum", "ip_csum")
        ip.register_static("Source address", alert["source(0).node.address(0).address"])
        ip.register_static("Target address", alert["target(0).node.address(0).address"])
        return ip

    def buildTcpHeaderTable(self, alert):
        tcp = HeaderTable()
        tcp.register_static("Source port", alert["source(0).service.port"])
        tcp.register_static("Target port", alert["target(0).service.port"])
        tcp.register("Seq #", "tcp_seq")
        tcp.register("Ack #", "tcp_ack")
        tcp.register("Header length", "tcp_off")
        tcp.register("Reserved", "tcp_res")
        tcp.register("R<br/>1", "tcp_flags", isFlagSet, (0x80,))
        tcp.register("R<br/>2", "tcp_flags", isFlagSet, (0x40,))
        tcp.register("U<br/>R<br/>G", "tcp_flags", isFlagSet, (0x20,))
        tcp.register("A<br/>C<br/>K", "tcp_flags", isFlagSet, (0x10,))
        tcp.register("P<br/>S<br/>H", "tcp_flags", isFlagSet, (0x08,))
        tcp.register("R<br/>S<br/>T", "tcp_flags", isFlagSet, (0x04,))
        tcp.register("S<br/>Y<br/>N", "tcp_flags", isFlagSet, (0x02,))
        tcp.register("F<br/>I<br/>N", "tcp_flags", isFlagSet, (0x01,))
        tcp.register("Window", "tcp_win")
        tcp.register("Checksum", "tcp_sum")
        tcp.register("URP", "tcp_urp")
        return tcp
    
    def buildUdpHeaderTable(self, alert):
        udp = HeaderTable()
        udp.register_static("Source port", alert["source(0).service.port"])
        udp.register_static("Target port", alert["target(0).service.port"])
        udp.register("Length", "udp_len")
        udp.register("Checksum", "udp_sum")
        return udp 

    def buildIcmpHeaderTable(self, alert):
        icmp = HeaderTable()
        icmp.register("Type", "icmp_type")
        icmp.register("Code", "icmp_code")
        icmp.register("Checksum", "icmp_sum")
        icmp.register("Id", "icmp_id")
        icmp.register("Seq #", "icmp_seq")
        
        return icmp
    
    def buildPayloadTable(self, alert):
        data = HeaderTable()
        data.register("Payload", "payload")
        return data

    
class AlertSummary(TcpIpOptions, MessageSummary, view.View):
    view_name = "alert_summary"
            
    def buildCorrelationAlert(self, alert):
        ca = alert["correlation_alert"]
        if not ca:
            return

        self.beginSection("Correlation Alert")
        self.newSectionEntry("Reason", ca["name"])

        for alertident in ca["alertident"]:
        
            # IDMEF draft 14 page 27
            # If the "analyzerid" is not provided, the alert is assumed to have come
            # from the same analyzer that is sending the CorrelationAlert.

            analyzerid = alertident["analyzerid"]
            if not analyzerid:
                analyzerid = alert["analyzer(-1).analyzerid"]

            criteria = ""
            if analyzerid:
                criteria += "alert.analyzer.analyzerid = %s && " % analyzerid
            
            criteria += "alert.messageid = %s" % alertident["alertident"]
            
            results = self.env.idmef_db.getAlertIdents(criteria)
            if len(results) == 0:
                text = "Invalid analyzerid:messageid pair: %s:%s" % (analyzerid, alertident["alertident"])
            else:
                alert = self.env.idmef_db.getAlert(results[0])
                link = utils.create_link("alert_summary", { "origin": "alert_listing", "ident": results[0] })
                text = "%s: <a href=\"%s\">%s</a>" % (alert["analyzer(-1).name"], link, alert["classification.text"])
                
            self.newSectionEntry("Correlated", text)

        self.endSection()
        
    def buildClassification(self, alert):
        if not alert["classification.text"]:
            return

        self.newTableEntry("Text", alert["classification.text"],
                           cl="section_alert_entry_value_emphasis impact_severity_%s" % alert["assessment.impact.severity"])
        self.newTableEntry("Ident", alert["classification.ident"])
        
    def buildReference(self, alert):
        self.beginTable()

        self.newTableCol(0, "Origin", header=True)
        self.newTableCol(0, "Name", header=True)
        self.newTableCol(0, "Meaning", header=True)
        self.newTableCol(0, "Url", header=True)

        index = 1
        for reference in alert["classification.reference"]:                
            self.newTableCol(index, reference["origin"])
            self.newTableCol(index, reference["name"])
            self.newTableCol(index, reference["meaning"])
            self.newTableCol(index, self.getUrlLink(reference["url"]))
            index += 1
            
        self.endTable()
        
    def buildImpact(self, alert):        
        self.newTableEntry("Severity", alert["assessment.impact.severity"],
                           cl="impact_severity_%s" % alert["assessment.impact.severity"])

        self.newTableEntry("Completion", alert["assessment.impact.completion"],
                           cl="impact_completion_%s" % alert["assessment.impact.completion"])
        
        self.newTableEntry("Type", alert["assessment.impact.type"])
        self.newTableEntry("Description", alert["assessment.impact.description"])
        
    def buildChecksum(self, checksum):
        self.newTableEntry(checksum["algorithm"], checksum["value"])
        self.newTableEntry("%s key" % checksum["algorithm"], checksum["key"])

    def _joinUserInfos(self, user, number, tty=None):
        user_str = user or ""
        if user != None and number != None:
            user_str += "(%d)" % number

        elif number:
            user_str = str(number)

        if tty:
            user_str += " on tty " + tty
            
        return user_str
    
    def buildUser(self, user):
        self.beginTable()  
        self.newTableEntry("User category", user["category"])

        self.beginTable()
        self.newTableCol(0, "Type", header=True)
        self.newTableCol(0, "Name", header=True)
        self.newTableCol(0, "Number", header=True)
        self.newTableCol(0, "Tty", header=True)
        
        index = 1
        for user_id in user["user_id"]:
            #user_str = self._joinUserInfos(user_id["name"], user_id["number"], user_id["tty"])
            self.newTableCol(index, user_id["type"])
            self.newTableCol(index, user_id["name"])
            self.newTableCol(index, user_id["number"])
            self.newTableCol(index, user_id["tty"])
            index += 1
            
        self.endTable()
        self.endTable()
        
    def buildFileAccess(self, file):
        self.beginTable()
        self.newTableCol(0, "Type", header=True)
        self.newTableCol(0, "Name", header=True)
        self.newTableCol(0, "Number", header=True)
        self.newTableCol(0, "Permission", header=True)

        index = 1
        for fa in file["file_access"]:
            pstr = ""
            for perm in fa["permission"]:
                if pstr:
                    pstr += ", "
                
                pstr += perm
                
            self.newTableCol(index, fa["user_id.type"])
            self.newTableCol(index, fa["user_id.name"])
            self.newTableCol(index, fa["user_id.number"])
            self.newTableCol(index, perm)

            index += 1
            
        self.endTable()
        
    def buildInode(self, inode):
        self.beginTable()
        self.newTableEntry("Change time", self.getTime(inode["change_time"]))
        self.newTableEntry("Inode Number", inode["number"])
        self.newTableEntry("Major device", inode["major_device"])
        self.newTableEntry("Minor device", inode["minor_device"])
        self.newTableEntry("C Major device", inode["c_major_device"])
        self.newTableEntry("C Minor device", inode["c_minor_device"])
        self.endTable()
        
    def buildFile(self, file):
        self.beginSection("Target file %s" % file["category"])
        
        self.beginTable()
        self.newTableEntry("Name", file["name"])
        self.newTableEntry("Path", file["path"])
        self.newTableEntry("Create time", self.getTime(file["create_time"]))
        self.newTableEntry("Modify time", self.getTime(file["modify_time"]))
        self.newTableEntry("Access time", self.getTime(file["access_time"]))
        self.newTableEntry("Data size", file["data_size"])
        self.newTableEntry("Disk size", file["disk_size"])
        self.endTable()

        self.beginTable()
        for checksum in file["checksum"]:
            self.buildChecksum(checksum)
        self.endTable()
        
        self.buildFileAccess(file)
        
        if file["inode"]:
            self.buildInode(file["inode"])
            
        self.endSection()

    def buildService(self, service):
        if not service:
            return
        
        if service["port"]:
            self.newTableEntry("Port", str(service["port"]))

        ipn = service["iana_protocol_number"]
        if ipn and utils.protocol_number_to_name(ipn) != None:
            self.newTableEntry("Protocol", utils.protocol_number_to_name(ipn))

        elif service["iana_protocol_name"]:
             self.newTableEntry("Protocol", service["iana_protocol_name"])
                             
        elif service["protocol"]:
            self.newTableEntry("Protocol", service["protocol"])
                    
    def buildDirection(self, alert, direction):
        self.beginTable()
        self.buildNode(alert["%s(0).node" % direction])
        self.buildService(alert["%s(0).service" % direction])
        self.endTable()
        
        user = alert["%s(0).user" % direction]
        if user:
            self.buildUser(user)
        
        process = alert["%s(0).process" % direction]
        if process:
            self.buildProcess(process)
        
    def buildSource(self, alert):
        self.buildDirection(alert, "source")

    def buildTarget(self, alert):
        self.buildDirection(alert, "target")

        for f in alert["target(0).file"]:
            self.buildFile(f)

    def buildSourceTarget(self, alert):
        self.beginSection("Source")
        self.buildSource(alert)
        self.endSection()

        self.beginSection("Target")
        self.buildTarget(alert)
        self.endSection()
        
    def render(self):
        alert = self.env.idmef_db.getAlert(self.parameters["ident"])
        self.dataset["sections"] = [ ]

        self.beginSection(alert["classification.text"])

        self.buildTime(alert)

        self.beginTable()
        self.buildClassification(alert)
        self.buildImpact(alert)
        self.endTable()
        
        self.buildReference(alert)

        self.beginSection("Analyzer #0")
        self.buildAnalyzer(alert["analyzer(-1)"])
                
        self.buildAnalyzerList(alert)
        self.endSection()
        
        self.endSection()
        
        self.buildCorrelationAlert(alert)
        self.buildSourceTarget(alert)
        
        ip = self.buildIpHeaderTable(alert)
        tcp = self.buildTcpHeaderTable(alert)
        udp = self.buildUdpHeaderTable(alert)
        icmp = self.buildIcmpHeaderTable(alert)
        data = self.buildPayloadTable(alert)
        
        ignored_value = {}
        ip_options = []
        tcp_options = []

        group = ip.field_list + tcp.field_list + udp.field_list + icmp.field_list + data.field_list
        self.buildAdditionalData(alert, ignore=group, ignored=ignored_value, ip_options=ip_options, tcp_options=tcp_options)
        
        if len(ignored_value.keys()) > 0:
            self.beginSection("Network centric information")

            self.beginTable()
            ip.render_table(self, "IP", ignored_value)
            self.ipOptionRender(ip_options)
            
            tcp.render_table(self, "TCP", ignored_value)
            self.tcpOptionRender(tcp_options)
            
            udp.render_table(self, "UDP", ignored_value)
            icmp.render_table(self, "ICMP", ignored_value)
            data.render_table(self, "Payload", ignored_value)

            self.endTable()
            self.endSection()
        

class HeartbeatSummary(MessageSummary, view.View):
    view_name = "heartbeat_summary"
    
    def render(self):
        heartbeat = self.env.idmef_db.getHeartbeat(self.parameters["ident"])
        self.dataset["sections"] = [ ]

        self.beginSection("Heartbeat")
        self.buildTime(heartbeat)

        self.beginSection("Analyzer #0")
        self.buildAnalyzer(heartbeat["analyzer(-1)"])
    
        self.buildAnalyzerList(heartbeat)
    
        self.endSection()
        self.endSection()

        self.buildAdditionalData(heartbeat)
        
