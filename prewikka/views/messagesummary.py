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


from prewikka import view, User, utils


def isFlagSet(bits, flag):
    if bits & flag:
        return "X"
    else:
        return "&nbsp;"


class SubTable:
    def __init__(self):
        self.field_list = [ ]

    def register_static(self, name, static, mask=None):
        self.field_list.append((None, name, static, None, None, mask))

    def register_func(self, name, field, func, extra, mask=None):
        self.field_list.append((field, name, None, func, extra, mask))

    def register(self, name, field, mask=None):
        self.field_list.append((field, name, None, None, None, mask))
        
    def get_string(self, dataset, style=""):
        content = ""
        hdr_content = ""
        from_dataset = False

        
        for field in self.field_list:
                    
            if not dataset.has_key(field[0]) and not field[2]:
                continue

            if field[2]:
                # static
                s = field[2]
            else:
                if field[5]: #mask
                    value = dataset[field[0]] & field[5]
                else:
                    value = dataset[field[0]]

                if field[3]:
                    # use func
                    s = field[3](value, field[4])

                else:
                    from_dataset = True
                    s = value

            content += "<td>%s</td>" % s            
            hdr_content += "<th>%s</th>" % field[1]

        if not from_dataset:
            return None
        
        return "<table class='%s'><tr>" % style + hdr_content + "</tr><tr>" + content + "</tr></table>"
        

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

    def buildProcess(self, process):
        self.newSectionEntry("Process", process["name"])
        self.newSectionEntry("Process Path", process["path"])
        self.newSectionEntry("Process Pid", process["pid"])
            
    def buildAnalyzer(self, alert):
        index = 0
        
        while alert["analyzer(%d)" % index] :
            analyzer = alert["analyzer(%d)" % index]
            
            self.beginSection("Analyzer")
            self.newSectionEntry("Analyzerid", analyzer["analyzerid"])
            self.newSectionEntry("Name", analyzer["name"], emphase=True)
            self.newSectionEntry("Model", analyzer["model"], emphase=True)
            self.newSectionEntry("Version", analyzer["version"])
            self.newSectionEntry("Class", analyzer["class"])
            self.newSectionEntry("Manufacturer", analyzer["manufacturer"])

            if analyzer["ostype"] or analyzer["osversion"]:
                self.newSectionEntry("Operating System", "%s %s" %
                                     (analyzer["ostype"] or "", analyzer["osversion"] or ""))
                
            self.newSectionEntry("Node name", analyzer["node.name"])
            self.newSectionEntry("Node location", analyzer["node.location"])

            i = 0
            while True:
                address = alert["analyzer(%d).node.address(%d).address" % (index, i)]
                if not address:
                    break
                self.newSectionEntry("Address", address)
                i += 1

            if alert["analyzer(%d).process" % index]:
                self.buildProcess(alert["analyzer(%d).process" % index])
                
            self.endSection()

            index += 1

    def buildAdditionalData(self, alert, ignore=[], ignored={}):
        self.beginSection("Additional Data")
        
        for ad in alert["additional_data"]:
            value = None
            meaning = ad["meaning"]
            
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
                emphase = (alert["analyzer.model"] == "Prelude LML" and meaning == "Original Log")
                self.newSectionEntry(meaning or "Data content", value, emphase)
        
        self.endSection()

    def buildIpHeaderTable(self, alert):
        ip = SubTable()
        ip.register("Version", "ip_ver")
        ip.register("Header length", "ip_hlen")
        ip.register("TOS", "ip_tos")
        ip.register("Length", "ip_len")
        ip.register("Id", "ip_id")
        #ip.register_func("M<br/>F", "ip_flags", isFlagSet, 0x2000, mask=0xe000)
        #ip.register_func("D<br/>F", "ip_flags", isFlagSet, 0x4000, mask=0xe000)
        #ip.register_func("R<br/>F", "ip_flags", isFlagSet, 0x8000, mask=0xe000)
        ip.register("Flags", "ip_flags")
        ip.register("Offset", "ip_off")
        ip.register("TTL", "ip_ttl")
        ip.register("Protocol", "ip_proto")
        ip.register("Checksum", "ip_csum")
        ip.register_static("Source address", alert["source(0).node.address(0).address"])
        ip.register_static("Target address", alert["target(0).node.address(0).address"])
        return ip
        
    def buildTcpHeaderTable(self, alert):
        tcp = SubTable()
        tcp.register_static("Source port", alert["source(0).service.port"])
        tcp.register_static("Target port", alert["target(0).service.port"])
        tcp.register("Seq #", "tcp_seq")
        tcp.register("Ack #", "tcp_ack")
        tcp.register("Header length", "tcp_off")
        tcp.register("Reserved", "tcp_res")
        tcp.register_func("U<br/>R<br/>G", "tcp_flags", isFlagSet, 0x20)
        tcp.register_func("A<br/>C<br/>K", "tcp_flags", isFlagSet, 0x10)
        tcp.register_func("P<br/>S<br/>H", "tcp_flags", isFlagSet, 0x08)
        tcp.register_func("R<br/>S<br/>T", "tcp_flags", isFlagSet, 0x04)
        tcp.register_func("S<br/>Y<br/>N", "tcp_flags", isFlagSet, 0x02)
        tcp.register_func("F<br/>I<br/>N", "tcp_flags", isFlagSet, 0x01)
        tcp.register("Window", "tcp_win")
        tcp.register("Checksum", "tcp_sum")
        tcp.register("URP", "tcp_urp")
        return tcp
    
    def buildUdpHeaderTable(self, alert):
        udp = SubTable()
        udp.register_static("Source port", alert["source(0).service.port"])
        udp.register_static("Target port", alert["target(0).service.port"])
        udp.register("Length", "udp_len")
        udp.register("Checksum", "udp_sum")
        return udp 

    def buildIcmpHeaderTable(self, alert):
        icmp = SubTable()
        icmp.register("Type", "icmp_type")
        icmp.register("Code", "icmp_code")
        icmp.register("Checksum", "icmp_sum")
        icmp.register("Id", "icmp_id")
        icmp.register("Seq #", "icmp_seq")
        
        return icmp
    
    def buildPayloadTable(self, alert):
        data = SubTable()
        data.register("Payload", "payload")
        return data

    
class AlertSummary(MessageSummary, view.View):
    view_name = "alert_summary"
    
    def buildTime(self, alert):
        self.beginSection("Dates")
        self.newSectionEntry("Create time", alert["create_time"])
        self.newSectionEntry("Detect time", alert["detect_time"], emphase=True)
        self.newSectionEntry("Analyzer time", alert["analyzer_time"])
        self.endSection()

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

        self.beginSection("Classification")
        self.newSectionEntry("Text", alert["classification.text"])
        self.newSectionEntry("Ident", alert["classification.ident"])

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


    def buildChecksum(self, checksum):
        self.newSectionEntry(checksum["algorithm"], checksum["value"])
        self.newSectionEntry("%s key" % checksum["algorithm"], checksum["key"])


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
        self.newSectionEntry("User category", user["category"])

        for user_id in user["user_id"]:
            user_str = self._joinUserInfos(user_id["name"], user_id["number"], user_id["tty"])
            self.newSectionEntry(user_id["type"], user_str)
        
    def buildFileAccess(self, fa):
        pstr = ""
        for perm in fa["permission"]:
            if pstr:
                pstr += ", "
                
            pstr += perm

        user_str = self._joinUserInfos(fa["user_id.name"], fa["user_id.number"])
        if user_str:
            user_str = " " + user_str

        self.newSectionEntry(fa["user_id.type"] + user_str, pstr)

    def buildInode(self, inode):
        self.newSectionEntry("Change time", inode["change_time"])
        self.newSectionEntry("Inode Number", inode["number"])
        self.newSectionEntry("Major device", inode["major_device"])
        self.newSectionEntry("Minor device", inode["minor_device"])
        self.newSectionEntry("C Major device", inode["c_major_device"])
        self.newSectionEntry("C Minor device", inode["c_minor_device"])
        
    def buildFile(self, file):
        self.beginSection("Target file %s" % file["category"])
        self.newSectionEntry("Name", file["name"])
        self.newSectionEntry("Path", file["path"])
        self.newSectionEntry("Create time", file["create_time"])
        self.newSectionEntry("Modify time", file["modify_time"])
        self.newSectionEntry("Access time", file["access_time"])
        self.newSectionEntry("Data size", file["data_size"])
        self.newSectionEntry("Disk size", file["disk_size"])

        for checksum in file["checksum"]:
            self.buildChecksum(checksum)

        for fa in file["file_access"]:
            self.buildFileAccess(fa)

        if file["inode"]:
            self.buildInode(file["inode"])
            
        self.endSection()

    def buildDirection(self, alert, direction):
        for addr in alert["%s(0).node.address" % direction]:

            address = addr["address"]
            if not address:
                continue
            
            port = alert["%s(0).service.port" % direction]
            if port != None:
                address += ":%d" % port

            ipn = alert["%s(0).service.iana_protocol_number" % direction]
            if ipn and utils.protocol_number_to_name(ipn) != None:
                address += " (%s)" % utils.protocol_number_to_name(ipn)

            elif alert["%s(0).service.iana_protocol_name" % direction]:
                address += " (%s)" % alert["%s(0).service.iana_protocol_name" % direction]

            elif alert["%s(0).service.protocol" % direction]:
                address += " (%s)" % alert["%s(0).service.protocol" % direction]               

            self.newSectionEntry("Address", address, emphase=True)

        self.newSectionEntry("Interface", alert["%s(0).interface" % direction])
        
        user = alert["%s(0).user" % direction]
        if user:
            self.buildUser(user)

        process = alert["%s(0).process" % direction]
        if process:
            self.buildProcess(process)

    def buildSource(self, alert):
        self.beginSection("Source")
        self.buildDirection(alert, "source")
        self.endSection()

    def buildTarget(self, alert):
        self.beginSection("Target")
        self.buildDirection(alert, "target")
        self.endSection()
        
        for f in alert["target(0).file"]:
            self.buildFile(f)

    def render(self):
        alert = self.env.idmef_db.getAlert(self.parameters["ident"])
        self.dataset["sections"] = [ ]
        self.buildTime(alert)
        self.buildClassification(alert)
        self.buildCorrelationAlert(alert)
        self.buildImpact(alert)
        self.buildSource(alert)
        self.buildTarget(alert)
        self.buildAnalyzer(alert)

        ip = self.buildIpHeaderTable(alert)
        tcp = self.buildTcpHeaderTable(alert)
        udp = self.buildUdpHeaderTable(alert)
        icmp = self.buildIcmpHeaderTable(alert)
        data = self.buildPayloadTable(alert)
        
        ignored_value = {}

        group = ip.field_list + tcp.field_list + udp.field_list + icmp.field_list + data.field_list
        self.buildAdditionalData(alert, ignore=group, ignored=ignored_value)
        
        if len(ignored_value.keys()) > 0:
            self.beginSection("Network centric information")
            self.newSectionEntry("IP", ip.get_string(ignored_value, "network_centric"))
            self.newSectionEntry("TCP", tcp.get_string(ignored_value, "network_centric"))
            self.newSectionEntry("UDP", udp.get_string(ignored_value, "network_centric"))
            self.newSectionEntry("ICMP", icmp.get_string(ignored_value, "network_centric"))
            self.newSectionEntry("Payload", data.get_string(ignored_value, "network_centric"))
            self.endSection()
            

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
