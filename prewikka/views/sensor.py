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

from prewikka import view, User, utils


class SensorListingParameters(view.Parameters):
    def register(self):
        self.optional("filter_path", str)
        self.optional("filter_value", str)



class HeartbeatAnalyzeParameters(view.Parameters):
    def register(self):
        self.mandatory("analyzerid", str)



class SensorMessagesDelete(SensorListingParameters):
    def register(self):
        SensorListingParameters.register(self)
        self.optional("analyzerid", list, default=[])
        self.optional("alerts", str, default=None)
        self.optional("heartbeats", str, default=None)



def get_analyzer_status_from_latest_heartbeat(heartbeat_status, heartbeat_time,
                                              heartbeat_interval, error_margin):
    if heartbeat_status == "exiting":
        return "offline", _("Offline")

    if heartbeat_interval is None:
        return "unknown", _("Unknown")

    if time.time() - int(heartbeat_time) > int(heartbeat_interval) + error_margin:
        return "missing", _("Missing")

    return "online", _("Online")


def analyzer_cmp(x, y):
    xmiss = x["status"] == "missing"
    ymiss = y["status"] == "missing"

    if xmiss and ymiss:
        return cmp(x["name"], y["name"])

    elif xmiss or ymiss:
        return ymiss - xmiss

    else:
        return cmp(x["name"], y["name"])

def node_cmp(x, y):
    xmiss = x["missing"]
    ymiss = y["missing"]

    if xmiss or ymiss:
        return ymiss - xmiss
    else:
        return cmp(x["node_name"], y["node_name"])


def getDominantStatus(d):
    if d["missing"] > 0 or d["unknown"] > 0:
        return "missing"

    return "online"


class SensorListing(view.View):
    view_name = "sensor_listing"
    view_parameters = SensorListingParameters
    view_permissions = [ User.PERM_IDMEF_VIEW ]
    view_template = "SensorListing"

    def init(self, env):
        self._heartbeat_count = int(env.config.general.getOptionValue("heartbeat_count", 30))
        self._heartbeat_error_margin = int(env.config.general.getOptionValue("heartbeat_error_margin", 3))

    def render(self):
        analyzers = { }

        criteria = None
        if self.parameters.has_key("filter_path"):
            criteria = "%s == '%s'" % (self.parameters["filter_path"],
                                       utils.escape_criteria(self.parameters["filter_value"]))

        locations = { }
        nodes = { }

        for analyzerid in self.env.idmef_db.getAnalyzerids():
            analyzer = self.env.idmef_db.getAnalyzer(analyzerid)

            parameters = { "analyzerid": analyzer["analyzerid"] }
            analyzer["alert_listing"] = utils.create_link("sensor_alert_listing", parameters)
            analyzer["heartbeat_listing"] = utils.create_link("sensor_heartbeat_listing", parameters)
            analyzer["heartbeat_analyze"] = utils.create_link("heartbeat_analyze", parameters)

            if analyzer["node_name"]:
                analyzer["node_name_link"] = utils.create_link(self.view_name,
                                                               { "filter_path": "heartbeat.analyzer(-1).node.name",
                                                                 "filter_value": analyzer["node_name"] })

            if analyzer["node_location"]:
                analyzer["node_location_link"] = utils.create_link(self.view_name,
                                                                   { "filter_path": "heartbeat.analyzer(-1).node.location",
                                                                     "filter_value": analyzer["node_location"] })

            node_key = ""
            for i in range(len(analyzer["node_addresses"])):
                addr = analyzer["node_addresses"][i]
                node_key += addr

                analyzer["node_addresses"][i] = {}
                analyzer["node_addresses"][i]["value"] = addr
                analyzer["node_addresses"][i]["inline_filter"] = utils.create_link(self.view_name,
                                                                   { "filter_path": "heartbeat.analyzer(-1).node.address.address",
                                                                     "filter_value": addr })

                analyzer["node_addresses"][i]["host_commands"] = []
                for command in self.env.host_commands.keys():
                    analyzer["node_addresses"][i]["host_commands"].append((command.capitalize(),
                                                                           utils.create_link("Command",
                                                                                             { "origin": self.view_name,
                                                                                               "command": command, "host": addr })))

            analyzer["status"], analyzer["status_meaning"] = \
                                get_analyzer_status_from_latest_heartbeat(analyzer["last_heartbeat_status"],
                                                                          analyzer["last_heartbeat_time"],
                                                                          analyzer["last_heartbeat_interval"],
                                                                          self._heartbeat_error_margin)

            analyzer["last_heartbeat_time"] = utils.time_to_ymdhms(time.localtime(int(analyzer["last_heartbeat_time"]))) + \
                                              " %+.2d:%.2d" % utils.get_gmt_offset()

            node_location = analyzer["node_location"] or _("Node location n/a")
            node_name = analyzer.get("node_name") or _("Node name n/a")
            osversion = analyzer["osversion"] or _("OS version n/a")
            ostype = analyzer["ostype"] or _("OS type n/a")
            addresses = analyzer["node_addresses"]

            node_key = node_name + osversion + ostype

            if not locations.has_key(node_location):
                locations[node_location] = { "total": 1, "missing": 0, "unknown": 0, "offline": 0, "online": 0, "nodes": { } }
            else:
                locations[node_location]["total"] += 1

            if not locations[node_location]["nodes"].has_key(node_key):
                locations[node_location]["nodes"][node_key] = { "total": 1, "missing": 0, "unknown": 0, "offline": 0, "online": 0,
                                                                "analyzers": [ ],
                                                                "node_name": node_name, "node_location": node_location,
                                                                "ostype": ostype, "osversion": osversion,
                                                                "node_addresses": addresses, "node_key": node_key }
            else:
                locations[node_location]["nodes"][node_key]["total"] += 1

            status = analyzer["status"]
            locations[node_location][status] += 1
            locations[node_location]["nodes"][node_key][status] += 1

            if status == "missing" or status == "unknown":
                locations[node_location]["nodes"][node_key]["analyzers"].insert(0, analyzer)
            else:
                locations[node_location]["nodes"][node_key]["analyzers"].append(analyzer)

        self.dataset["locations"] = locations


class SensorMessagesDelete(SensorListing):
    view_name = "sensor_messages_delete"
    view_parameters = SensorMessagesDelete
    view_permissions = [ User.PERM_IDMEF_VIEW, User.PERM_IDMEF_ALTER ]

    def render(self):
        for analyzerid in self.parameters["analyzerid"]:
            if self.parameters.has_key("alerts"):
                criteria = "alert.analyzer.analyzerid == '%s'" % utils.escape_criteria(analyzerid)
                self.env.idmef_db.deleteAlert(self.env.idmef_db.getAlertIdents(criteria))

            if self.parameters.has_key("heartbeats"):
                criteria = "heartbeat.analyzer(-1).analyzerid == '%s'" % utils.escape_criteria(analyzerid)
                self.env.idmef_db.deleteHeartbeat(self.env.idmef_db.getHeartbeatIdents(criteria))

        SensorListing.render(self)



class HeartbeatAnalyze(view.View):
    view_name = "heartbeat_analyze"
    view_parameters = HeartbeatAnalyzeParameters
    view_permissions = [ User.PERM_IDMEF_VIEW ]
    view_template = "HeartbeatAnalyze"

    def init(self, env):
        self._heartbeat_count = int(env.config.general.getOptionValue("heartbeat_count", 30))
        self._heartbeat_error_margin = int(env.config.general.getOptionValue("heartbeat_error_margin", 3))

    def render(self):
        analyzerid = self.parameters["analyzerid"]

        analyzer = self.env.idmef_db.getAnalyzer(analyzerid)
        analyzer["last_heartbeat_time"] = unicode(analyzer["last_heartbeat_time"])
        analyzer["events"] = [ ]
        analyzer["status"] = "abnormal_offline"
        analyzer["status_meaning"] = "abnormal offline"

        start = time.time()
        idents = self.env.idmef_db.getHeartbeatIdents(criteria="heartbeat.analyzer(-1).analyzerid == %s" % analyzerid,
                                                      limit=self._heartbeat_count)
        newer = None
        latest = True
        total_interval = 0

        for ident in idents:
            older = self.env.idmef_db.getHeartbeat(ident)
            older_status = older.getAdditionalData("Analyzer status")
            older_interval = older["heartbeat.heartbeat_interval"]
            if not older_status or not older_interval:
                continue
            older_time = older["heartbeat.create_time"]
            total_interval += int(older_interval)

            if latest:
                latest = False
                analyzer["status"], analyzer["status_meaning"] = \
                                    get_analyzer_status_from_latest_heartbeat(older_status, older_time, older_interval,
                                                                              self._heartbeat_error_margin)
                if analyzer["status"] == "abnormal_offline":
                    analyzer["events"].append({ "value": "sensor is down since %s" % older_time, "type": "down"})
            if newer:
                event = None

                if newer_status == "starting":
                    if older_status == "exiting":
                        event = { "value": "normal sensor start at %s" % str(newer_time),
                                  "type": "start" }
                    else:
                        event = { "value": "unexpected sensor restart at %s" % str(newer_time),
                                  "type": "unexpected_restart" }

                if newer_status == "running":
                    if abs(int(newer_time) - int(older_time) - int(older_interval)) > self._heartbeat_error_margin:
                        event = { "value": "abnormal heartbeat interval between %s and %s" % (str(older_time), str(newer_time)),
                                  "type": "abnormal_heartbeat_interval" }


                if newer_status == "exiting":
                    event = { "value": "normal sensor stop at %s" % str(newer_time),
                              "type": "normal_stop" }

                if event:
                    analyzer["events"].append(event)

            newer = older
            newer_status = older_status
            newer_interval = older_interval
            newer_time = older_time

        if not analyzer["events"]:
            analyzer["events"].append({ "value":
                                        "No anomaly in the last %d heartbeats (1 heartbeat every %d s average)" %
                                        (self._heartbeat_count, total_interval / self._heartbeat_count),
                                        "type": "no_anomaly" })

        self.dataset["analyzer"] = analyzer
