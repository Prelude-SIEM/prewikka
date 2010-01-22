# Copyright (C) 2004,2005,2006,2007 PreludeIDS Technologies. All Rights Reserved.
# Author: Nicolas Delon <nicolas.delon@prelude-ids.com>
# Author: Yoann Vandoorselaere <yoann.v@prelude-ids.com>
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

import re
import time
import struct
import socket
import urllib

from prewikka import view, User, utils, resolve


def getUriCriteria(parameters):
    if not parameters.has_key("messageid"):
            return None

    if parameters.has_key("analyzerid"):
        criteria = "alert.analyzer(-1).analyzerid = '%s' &&" % utils.escape_criteria(parameters["analyzerid"])
    else:
        criteria = ""

    criteria += "alert.messageid = '%s'" % utils.escape_criteria(parameters["messageid"])

    return criteria


class Table:
    def __init__(self):
        self._current_table = None
        self._current_section = None

    def getCurrentSection(self):
        return self._current_section

    def beginSection(self, title, display="block"):
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

    def beginTable(self, cl="message_summary", style="", odd_even=False):
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
        if value == None:
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
    def _isFlagSet(self, bits, flag, shift=0):
        if (bits & flag) >> shift:
            return "X"
        else:
            return "&nbsp;"

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
        self.newTableCol(0, _("Name"), header=True)
        self.newTableCol(0, _("Code"), header=True)
        self.newTableCol(0, _("Data length"), header=True)
        self.newTableCol(0, _("Data"), header=True)

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
        self.optional("ident", long)
        self.optional("analyzerid", str)
        self.optional("messageid", str)



class MessageSummary(Table):
    view_parameters = MessageParameters
    view_permissions = [ User.PERM_IDMEF_VIEW ]
    view_template = "MessageSummary"

    def getUrlLink(self, name, url=None):
        if not name:
            return None

        if not url:
            if name.find("http://") != -1:
                url = name

            elif re.compile("\.[^\s]+\.[^\s+]").search(name):
                url = "http://" + name

            else:
                return name

        external_link_new_window = self.env.config.general.getOptionValue("external_link_new_window", "true")

        if (not external_link_new_window and self.env.config.general.has_key("external_link_new_window")) or \
               (external_link_new_window == None or external_link_new_window.lower() in [ "true", "yes" ]):
            target = "_blank"
        else:
            target = "_self"

        return "<a target='%s' href='%s'>%s</a>" % (target, url, name)

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

        self.newTableEntry(_("Create time"), self.getTime(msg["create_time"]))

        try:
            self.newTableEntry(_("Detect time"), self.getTime(msg["detect_time"]), cl="section_alert_entry_value_emphasis")
        except:
            pass

        if msg["analyzer_time"]:
            self.newTableEntry(_("Analyzer time"), self.getTime(msg["analyzer_time"]))

        self.endTable()

    def buildProcess(self, process):
        self.beginTable()
        self.newTableEntry(_("Process"), process["name"])
        self.newTableEntry(_("Process Path"), process["path"])
        self.newTableEntry(_("Process PID"), process["pid"])
        self.endTable()


    def buildNode(self, node):
        if not node:
            return

        self.newTableEntry(_("Node location"), node["location"])

        addr_list = None
        node_name = None
        for addr in node["address"]:
            address = addr["address"]
            if not address:
                continue

            node_name = resolve.AddressResolve(address)

            if addr_list:
                addr_list += "<br/>"
            else:
                addr_list = ""

            if addr["category"] in ("ipv4-addr", "ipv6-addr", "ipv4-net", "ipv6-net"):
                addr_list += self.getUrlLink(address, "https://www.prelude-ids.com/host_details.php?host=%s" % address)
            else:
                addr_list += address

        if node["name"]:
            self.newTableEntry(_("Node name"), node["name"])

        elif node_name.resolveSucceed():
            self.newTableEntry(_("Node name (resolved)"), node_name)

        self.newTableEntry(_("Node address"), addr_list)

    def buildAnalyzer(self, analyzer):
        self.beginTable(cl="message_summary_no_border")

        self.beginTable()
        self.newTableEntry(_("Model"), analyzer["model"], cl="section_alert_entry_value_emphasis")
        self.newTableEntry(_("Name"), analyzer["name"], cl="section_alert_entry_value_emphasis")
        self.newTableEntry(_("Analyzerid"), analyzer["analyzerid"])
        self.newTableEntry(_("Version"), analyzer["version"])
        self.newTableEntry(_("Class"), analyzer["class"])

        self.newTableEntry(_("Manufacturer"), self.getUrlLink(analyzer["manufacturer"]))
        self.endTable()
        self.newTableRow()

        self.beginTable()

        self.buildNode(analyzer["node"])
        if analyzer["ostype"] or analyzer["osversion"]:
                self.newTableEntry(_("Operating System"), "%s %s" % (analyzer["ostype"] or "", analyzer["osversion"] or ""))

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

        self.beginSection(_("Analyzer Path (%d not shown)") % len(l), display="none")

        self.beginTable(cl="message_summary_no_border")

        i = 1
        index = len(l) - 1
        for analyzer in l:
            self.newTableCol(i - 1, _("Analyzer #%d") % index, None, header=True)
            self.buildAnalyzer(analyzer)
            self.newTableRow()
            i += 1
            index -= 1

        self.endTable()
        self.endSection()

    def buildAdditionalData(self, alert, ignore=[], ignored={}, ip_options=[], tcp_options=[]):
        self.beginSection(_("Additional data"))

        self.beginTable()
        self.newTableCol(0, _("Meaning"), header=True)
        self.newTableCol(0, _("Value"), header=True)

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
                    value = ad.get("data", htmlsafe=False)
                    if meaning != "payload":
                        value = utils.hexdump(value)
                else:
                    value = ad.get("data")
                    if isinstance(value, str):
                        value = utils.toUnicode(value)

            for field in ignore:
                if meaning != None and meaning == field[0]:
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
        ip.register(_("Version"), "ip_ver")
        ip.register(_("Header length"), "ip_hlen")
        ip.register(_("TOS"), "ip_tos")
        ip.register(_("Length"), "ip_len")
        ip.register(_("Id"), "ip_id")
        ip.register("R<br/>F", "ip_off", self._isFlagSet, (0x8000, 15))
        ip.register("D<br/>F", "ip_off", self._isFlagSet, (0x4000, 14))
        ip.register("M<br/>F", "ip_off", self._isFlagSet, (0x2000, 13))
        ip.register(_("Ip offset"), "ip_off", (lambda x: x & 0x1fff))
        ip.register(_("TTL"), "ip_ttl")
        ip.register(_("Protocol"), "ip_proto")
        ip.register(_("Checksum"), "ip_sum")
        ip.register_static(_("Source address"), alert["source(0).node.address(0).address"])
        ip.register_static(_("Target address"), alert["target(0).node.address(0).address"])
        return ip

    def buildTcpHeaderTable(self, alert):
        tcp = HeaderTable()
        tcp.register_static(_("Source port"), alert["source(0).service.port"])
        tcp.register_static(_("Target port"), alert["target(0).service.port"])
        tcp.register("Seq #", "tcp_seq")
        tcp.register("Ack #", "tcp_ack")
        tcp.register(_("Header length"), "tcp_off")
        tcp.register(_("Reserved"), "tcp_res")
        tcp.register("R<br/>1", "tcp_flags", self._isFlagSet, (0x80,))
        tcp.register("R<br/>2", "tcp_flags", self._isFlagSet, (0x40,))
        tcp.register("U<br/>R<br/>G", "tcp_flags", self._isFlagSet, (0x20,))
        tcp.register("A<br/>C<br/>K", "tcp_flags", self._isFlagSet, (0x10,))
        tcp.register("P<br/>S<br/>H", "tcp_flags", self._isFlagSet, (0x08,))
        tcp.register("R<br/>S<br/>T", "tcp_flags", self._isFlagSet, (0x04,))
        tcp.register("S<br/>Y<br/>N", "tcp_flags", self._isFlagSet, (0x02,))
        tcp.register("F<br/>I<br/>N", "tcp_flags", self._isFlagSet, (0x01,))
        tcp.register(_("Window"), "tcp_win")
        tcp.register(_("Checksum"), "tcp_sum")
        tcp.register(_("URP"), "tcp_urp")
        return tcp

    def buildUdpHeaderTable(self, alert):
        udp = HeaderTable()
        udp.register_static(_("Source port"), alert["source(0).service.port"])
        udp.register_static(_("Target port"), alert["target(0).service.port"])
        udp.register(_("Length"), "udp_len")
        udp.register(_("Checksum"), "udp_sum")
        return udp

    def buildIcmpHeaderTable(self, alert):
        icmp = HeaderTable()
        icmp.register(_("Type"), "icmp_type")
        icmp.register(_("Code"), "icmp_code")
        icmp.register(_("Checksum"), "icmp_sum")
        icmp.register(_("Id"), "icmp_id")
        icmp.register(_("Seq #"), "icmp_seq")
        icmp.register(_("Mask"), "icmp_mask");
        icmp.register(_("Gateway Address"), "icmp_gwaddr")
        icmp.register(_("Num address"), "icmp_num_addrs")
        icmp.register(_("Wpa"), "icmp_wpa")
        icmp.register(_("Lifetime"), "icmp_lifetime")
        icmp.register(_("Otime"), "icmp_otime")
        icmp.register(_("Rtime"), "icmp_rtime")
        icmp.register(_("Ttime"), "icmp_ttime")

        return icmp

    def buildPayloadTable(self, alert):
        data = HeaderTable()
        data.register(_("Payload"), "payload")
        #data.register("ASCII Payload", "payload", utils.escape_html_string)
        return data


class AlertSummary(TcpIpOptions, MessageSummary, view.View):
    view_name = "alert_summary"

    def buildAlertIdent(self, alert, parent):
        calist = { }

        for alertident in parent["alertident"]:

            # IDMEF draft 14 page 27
            # If the "analyzerid" is not provided, the alert is assumed to have come
            # from the same analyzer that is sending the Alert.

            analyzerid = alertident["analyzerid"]
            if not analyzerid:
                for a in alert["analyzer"]:
                    if a["analyzerid"]:
                        analyzerid = a["analyzerid"]
                        break

            if not calist.has_key(analyzerid):
                calist[analyzerid] = []

            calist[analyzerid].append(alertident["alertident"])

        idx = 1
        for analyzerid in calist.keys():

            content = ""
            missing = 0
            for ident in calist[analyzerid]:
                criteria = "alert.analyzer.analyzerid = '%s' && alert.messageid = '%s'" % (analyzerid, ident)

                results = self.env.idmef_db.getAlertIdents(criteria)
                if len(results) == 0:
                    missing += 1
                    #content += "<li>" + _("Invalid 'analyzerid:messageid' pair, '%(analyzerid):%(messageid)'") % { "analyzerid": analyzerid, "messageid": ident } + "</li>"
                else:
                    alert = self.env.idmef_db.getAlert(results[0], htmlsafe=True)
                    link = utils.create_link("alert_summary", { "origin": self.parameters["origin"], "ident": results[0] })
                    content += "<li><a href=\"%s\">%s</a></li>" % (link, alert["classification.text"])

            if missing > 0:
                content += "<li>" + (_("%d linked alerts missing (probably deleted)") % missing) + "</li>"

            self.newTableCol(idx, "<ul style='padding: 0px; margin: 0px 0px 0px 10px;'>%s</ul>" % content)
            self.buildAnalyzer(alert["analyzer(-1)"])
            self.newTableRow()

            idx += 1


    def buildCorrelationAlert(self, alert):
        ca = alert["correlation_alert"]
        if not ca:
            return

        self.beginSection(_("Correlation Alert"))
        self.beginTable()
        self.newTableEntry(_("Name"), ca["alert.correlation_alert.name"])
        self.endTable()

        self.beginTable()
        self.newTableCol(0, _("Correlated Alert"), header=True)
        self.newTableCol(0, _("Source Analyzer"), header=True)
        self.buildAlertIdent(alert, ca)
        self.endTable()
        self.endSection()

    def buildToolAlert(self, alert):
        ta = alert["tool_alert"]
        if not ta:
            return

        self.beginSection(_("Tool Alert"))
        self.beginTable()
        self.newTableEntry(_("Name"), ta["alert.tool_alert.name"])
        self.endTable()

        self.beginTable()
        self.newTableCol(0, _("Linked Alert"), header=True)
        self.newTableCol(0, _("Source Analyzer"), header=True)
        self.buildAlertIdent(alert, ta)
        self.endTable()

        self.endSection()

    def buildClassification(self, alert):
        if not alert["classification.text"]:
            return

        self.newTableEntry(_("Text"), alert["classification.text"],
                           cl="section_alert_entry_value_emphasis impact_severity_%s" % alert["assessment.impact.severity"])
        self.newTableEntry(_("Ident"), alert["classification.ident"])

    def buildReference(self, alert):
        self.beginTable()

        self.newTableCol(0, _("Origin"), header=True)
        self.newTableCol(0, _("Name"), header=True)
        self.newTableCol(0, _("Meaning"), header=True)

        index = 1
        for reference in alert["classification.reference"]:
            self.newTableCol(index, reference["origin"])
            if reference["origin"] in ("user-specific", "vendor-specific"):
                urlstr="&url=" + urllib.quote(reference["url"], safe="")
            else:
                urlstr=""

            self.newTableCol(index, self.getUrlLink(reference["name"], "http://www.prelude-ids.com/reference_details.php?origin=%s&name=%s%s" % (urllib.quote(reference["origin"]), urllib.quote(reference["name"]), urlstr)))
            self.newTableCol(index, reference["meaning"])
            index += 1

        self.endTable()

    def buildImpact(self, alert):
        self.newTableEntry(_("Severity"), alert["assessment.impact.severity"],
                           cl="impact_severity_%s" % alert["assessment.impact.severity"])

        self.newTableEntry(_("Completion"), alert["assessment.impact.completion"],
                           cl="impact_completion_%s" % alert["assessment.impact.completion"])

        self.newTableEntry(_("Type"), alert["assessment.impact.type"])
        self.newTableEntry(_("Description"), alert["assessment.impact.description"])

    def buildAction(self, action):
        self.beginTable()

        self.newTableEntry(_("Category"), action["category"])
        self.newTableEntry(_("Description"), action["description"])

        self.endTable()

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
        self.newTableEntry(_("User category"), user["category"])

        self.beginTable()
        self.newTableCol(0, _("Type"), header=True)
        self.newTableCol(0, _("Name"), header=True)
        self.newTableCol(0, _("Number"), header=True)
        self.newTableCol(0, _("Tty"), header=True)

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
        self.newTableCol(0, _("Type"), header=True)
        self.newTableCol(0, _("Name"), header=True)
        self.newTableCol(0, _("Number"), header=True)
        self.newTableCol(0, _("Permission"), header=True)

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
            self.newTableCol(index, pstr)

            index += 1

        self.endTable()

    def buildInode(self, inode):
        self.beginTable()
        self.newTableEntry(_("Change time"), self.getTime(inode["change_time"]))
        self.newTableEntry(_("Inode Number"), inode["number"])
        self.newTableEntry(_("Major device"), inode["major_device"])
        self.newTableEntry(_("Minor device"), inode["minor_device"])
        self.newTableEntry(_("C Major device"), inode["c_major_device"])
        self.newTableEntry(_("C Minor device"), inode["c_minor_device"])
        self.endTable()

    def buildFile(self, file):
        self.beginSection(_("Target file %s") % file["category"])

        self.beginTable()
        self.newTableEntry(_("Name"), file["name"])
        self.newTableEntry(_("Path"), file["path"])
        self.newTableEntry(_("Create time"), self.getTime(file["create_time"]))
        self.newTableEntry(_("Modify time"), self.getTime(file["modify_time"]))
        self.newTableEntry(_("Access time"), self.getTime(file["access_time"]))
        self.newTableEntry(_("Data size"), file["data_size"])
        self.newTableEntry(_("Disk size"), file["disk_size"])
        self.endTable()

        self.beginTable()
        for checksum in file["checksum"]:
            self.buildChecksum(checksum)
        self.endTable()

        self.buildFileAccess(file)

        if file["inode"]:
            self.buildInode(file["inode"])

        self.endSection()

    def buildWebService(self, webservice):
        if not webservice:
            return

        self.beginSection(_("Web Service"))
        self.beginTable()

        self.newTableEntry(_("Url"), webservice["url"])
        self.newTableEntry(_("Cgi"), webservice["cgi"])
        self.newTableEntry(_("Http Method"), webservice["http_method"])

        for arg in webservice["arg"]:
            self.newTableEntry(_("CGI Argument"), arg)

        self.endTable()
        self.endSection()

    def buildSnmpService(self, service):
        if not service:
            return

        self.beginSection(_("SNMP Service"))
        self.beginTable()

        self.newTableEntry(_("oid"), service["oid"])
        self.newTableEntry(_("messageProcessingModel"), service["message_processing_model"])
        self.newTableEntry(_("securityModel"), service["security_model"])
        self.newTableEntry(_("securityName"), service["security_name"])
        self.newTableEntry(_("securityLevel"), service["security_level"])
        self.newTableEntry(_("contextName"), service["context_name"])
        self.newTableEntry(_("contextEngineID"), service["context_engine_id"])
        self.newTableEntry(_("command"), service["command"])

        self.endTable()
        self.endSection()


    def buildService(self, service):
        if not service:
            return

        if service["port"]:
            port = str(service["port"])
            self.newTableEntry(_("Port"), self.getUrlLink(port, "https://www.prelude-ids.com/port_details.php?port=%s" % port))

        portlist = service["portlist"]
        if portlist:
            out = ""
            for port in portlist.replace(" ", "").split(","):
                if len(out) > 0:
                    out += ", "

                if port.find("-") != -1:
                    left, right = port.split("-")
                    out += self.getUrlLink(left, "https://www.prelude-ids.com/port_details.php?port=%s" % left)
                    out += " - "
                    out += self.getUrlLink(right, "https://www.prelude-ids.com/port_details.php?port=%s" % right)
                else:
                    out += self.getUrlLink(port, "https://www.prelude-ids.com/port_details.php?port=%s" % port)

            self.newTableEntry(_("PortList"), out)

        if service["ip_version"]:
            self.newTableEntry(_("ip_version"), service["ip_version"])

        ipn = service["iana_protocol_number"]
        if ipn and utils.protocol_number_to_name(ipn) != None:
            self.newTableEntry(_("Protocol"), utils.protocol_number_to_name(ipn))

        elif service["iana_protocol_name"]:
             self.newTableEntry(_("Protocol"), service["iana_protocol_name"])

        elif service["protocol"]:
            self.newTableEntry(_("Protocol"), service["protocol"])

    def buildDirection(self, direction):
        self.beginTable()
        self.buildNode(direction["node"])
        self.buildService(direction["service"])
        self.endTable()

        user = direction["user"]
        if user:
            self.buildUser(user)

        process = direction["process"]
        if process:
            self.buildProcess(process)

        self.buildWebService(direction["service.web_service"])
        self.buildSnmpService(direction["service.snmp_service"])

    def buildSource(self, alert):
        i = 0

        for source in alert["source"]:
            self.beginSection(_("Source(%d)") % i)
            self.buildDirection(source)
            self.endSection()
            i += 1

    def buildTarget(self, alert):
        i = 0

        for target in alert["target"]:
            self.beginSection(_("Target(%d)") % i)
            self.buildDirection(target)

            for f in target["file"]:
                self.buildFile(f)

            self.endSection()
            i += 1

    def buildSourceTarget(self, alert):
        self.buildSource(alert)
        self.buildTarget(alert)

    def getSectionName(self, alert):
        if alert["correlation_alert"]:
            section = _("Correlation Alert")

        elif alert["tool_alert"]:
            section = _("Tool Alert")

        elif alert["overflow_alert"]:
            section = _("Overflow Alert")

        else:
            section = _("Alert")

        return section

    def render(self):
        criteria = getUriCriteria(self.parameters)
        if criteria is not None:
            ident = self.env.idmef_db.getAlertIdents(criteria)[0]
        else:
            ident = self.parameters["ident"]

        alert = self.env.idmef_db.getAlert(ident, htmlsafe=True)
        self.dataset["sections"] = [ ]

        self.beginSection(self.getSectionName(alert))

        self.buildTime(alert)

        self.beginTable()
        self.newTableEntry(_("MessageID"), alert["messageid"])
        self.endTable()

        self.beginTable()
        self.buildClassification(alert)
        self.buildImpact(alert)
        self.endTable()

        self.beginSection(_("Actions"))
        for action in alert["assessment.action"]:
            self.buildAction(action)
        self.endSection()

        self.buildCorrelationAlert(alert)
        self.buildToolAlert(alert)
        self.buildReference(alert)

        self.beginSection(_("Analyzer #%d") % (len(alert["analyzer"]) - 1))
        self.buildAnalyzer(alert["analyzer(-1)"])

        self.buildAnalyzerList(alert)
        self.endSection()

        self.endSection()

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
            def blah(b):
                if b >= 32 and b < 127:
                    return chr(b)
                else:
                    return "."

            self.beginSection(_("Network centric information"))

            self.beginTable(cl="message_summary_no_border")
            ip.render_table(self, "IP", ignored_value)
            self.ipOptionRender(ip_options)

            tcp.render_table(self, "TCP", ignored_value)
            self.tcpOptionRender(tcp_options)

            udp.render_table(self, "UDP", ignored_value)
            icmp.render_table(self, "ICMP", ignored_value)

            if ignored_value.has_key("payload"):
                val = {}

                payload = utils.escape_html_string(utils.hexdump(ignored_value["payload"])).replace(" ", "&nbsp;")
                val["payload"] = "<span class='fixed'>%s</span>" % payload
                data.render_table(self, _("Payload"), val)

                val["payload"] = "<div style='overflow: auto;'>%s</div>" % utils.escape_html_string(utils.toUnicode(ignored_value["payload"])).replace("\n", "<br/>")
                data.render_table(self, _("ASCII Payload"), val)

            self.endTable()
            self.endSection()


class HeartbeatSummary(MessageSummary, view.View):
    view_name = "heartbeat_summary"

    def render(self):
        criteria = getUriCriteria(self.parameters)
        if criteria is not None:
            ident = self.env.idmef_db.getHeartbeatIdents(criteria)[0]
        else:
            ident = self.parameters["ident"]

        heartbeat = self.env.idmef_db.getHeartbeat(ident, htmlsafe=True)
        self.dataset["sections"] = [ ]

        self.beginSection(_("Heartbeat"))
        self.buildTime(heartbeat)

        self.beginSection(_("Analyzer #%d") % (len(heartbeat["analyzer"]) - 1))
        self.buildAnalyzer(heartbeat["analyzer(-1)"])

        self.buildAnalyzerList(heartbeat)

        self.endSection()
        self.endSection()

        self.buildAdditionalData(heartbeat)

