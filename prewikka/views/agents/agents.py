# Copyright (C) 2004-2016 CS-SI. All Rights Reserved.
# Author: Yoann Vandoorselaere <yoannv@gmail.com>
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
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import pkg_resources
import time

from prewikka import view, usergroup, utils, localization, env, mainmenu
from . import templates


class SensorListingParameters(mainmenu.MainMenuParameters):
    def register(self):
        mainmenu.MainMenuParameters.register(self)
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


class SensorListing(view.View):
    view_name = "Agents"
    view_section = "Agents"
    view_parameters = SensorListingParameters
    view_permissions = [ N_("IDMEF_VIEW") ]
    view_template = templates.SensorListing
    view_order = 0
    plugin_htdocs = (("agents", pkg_resources.resource_filename(__name__, 'htdocs')),)

    def __init__(self):
        view.View.__init__(self)
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

        for (analyzerid,) in env.idmef_db.getValues(["heartbeat.analyzer(-1).analyzerid/group_by"], criteria):
            analyzer, heartbeat = env.idmef_db.getAnalyzer(analyzerid)

            parameters = {"heartbeat.analyzer(-1).analyzerid": analyzer["analyzerid"]}
            analyzer.heartbeat_listing = utils.create_link(view.getViewPath("HeartbeatListing"), parameters)
            parameters = {"analyzer_object_0": "alert.analyzer.analyzerid",
                          "analyzer_operator_0": "=",
                          "analyzer_value_0": analyzer["analyzerid"]}
            analyzer.alert_listing = utils.create_link(view.getViewPath("AlertListing"), parameters)
            parameters = {"analyzerid": analyzer["analyzerid"]}
            analyzer.heartbeat_analyze = utils.create_link(self.view_path + "/HeartbeatAnalyze", parameters)

            node_key = ""
            addresses = []
            for addr in analyzer["node.address(*).address"]:
                node_key += addr

                address = {}
                address["value"] = addr
                address["inline_filter"] = utils.create_link(self.view_path,
                                                             { "filter_path": "heartbeat.analyzer(-1).node.address(*).address",
                                                               "filter_value": addr })

                address["host_links"] = []
                for typ, linkname, link, widget in env.hookmgr.trigger("HOOK_LINK", addr):
                    if typ == "host":
                        address["host_links"].append((linkname, link, widget))

                if "host" in env.url:
                    for urlname, url in env.url["host"].items():
                        address["host_links"].append((urlname.capitalize(), url.replace("$host", addr), False))

                addresses.append(address)

            analyzer.model_inline_filter = utils.create_link(self.view_path, { "filter_path": "heartbeat.analyzer(-1).model",
                                                                               "filter_value": analyzer["model"] })

            analyzer.status, analyzer.status_meaning = \
                utils.get_analyzer_status_from_latest_heartbeat(heartbeat, self._heartbeat_error_margin)

            delta = float(heartbeat.get("create_time")) - time.time()
            analyzer.last_heartbeat_time = localization.format_timedelta(delta, add_direction=True)

            node_location = analyzer["node.location"] or _("Node location n/a")
            node_name = analyzer.get("node.name") or _("Node name n/a")
            osversion = analyzer["osversion"] or _("OS version n/a")
            ostype = analyzer["ostype"] or _("OS type n/a")

            node_key = node_name + osversion + ostype

            if not locations.has_key(node_location):
                locations[node_location] = { "total": 1, "missing": 0, "unknown": 0, "offline": 0, "online": 0, "nodes": { } }
            else:
                locations[node_location]["total"] += 1

            if not locations[node_location]["nodes"].has_key(node_key):
                locations[node_location]["nodes"][node_key] = { "total": 1, "missing": 0, "unknown": 0, "offline": 0, "online": 0,
                                                                "analyzers": [ ],
                                                                "node.name": node_name, "node.location": node_location,
                                                                "ostype": ostype, "osversion": osversion,
                                                                "node_addresses": addresses }
            else:
                locations[node_location]["nodes"][node_key]["total"] += 1

            locations[node_location][analyzer.status] += 1
            locations[node_location]["nodes"][node_key][analyzer.status] += 1

            if analyzer.status in ["missing", "unknown"]:
                locations[node_location]["nodes"][node_key]["analyzers"].insert(0, analyzer)
            else:
                locations[node_location]["nodes"][node_key]["analyzers"].append(analyzer)

        self.dataset["locations"] = locations


class SensorMessagesDelete(SensorListing):
    view_parameters = SensorMessagesDelete
    view_permissions = [ N_("IDMEF_VIEW"), N_("IDMEF_ALTER") ]

    def render(self):
        for analyzerid in self.parameters["analyzerid"]:
            if self.parameters.has_key("alerts"):
                criteria = "alert.analyzer.analyzerid == '%s'" % utils.escape_criteria(analyzerid)
                env.idmef_db.deleteAlert(env.idmef_db.getAlertIdents(criteria))

            if self.parameters.has_key("heartbeats"):
                criteria = "heartbeat.analyzer(-1).analyzerid == '%s'" % utils.escape_criteria(analyzerid)
                env.idmef_db.deleteHeartbeat(env.idmef_db.getHeartbeatIdents(criteria))

        SensorListing.render(self)


class HeartbeatAnalyze(SensorListing):
    view_parameters = HeartbeatAnalyzeParameters
    view_permissions = [ N_("IDMEF_VIEW") ]
    view_template = templates.HeartbeatAnalyze

    def render(self):
        analyzerid = self.parameters["analyzerid"]

        analyzer, heartbeat = env.idmef_db.getAnalyzer(analyzerid)
        delta = float(heartbeat["create_time"]) - time.time()
        analyzer.last_heartbeat_time = localization.format_timedelta(delta, add_direction=True)

        analyzer.status = None
        analyzer.events = [ ]

        idents = env.idmef_db.getHeartbeatIdents(criteria="heartbeat.analyzer(-1).analyzerid == %s" % analyzerid,
                                                      limit=self._heartbeat_count)
        prev = None
        latest = True
        total_interval = 0

        for idx, ident in enumerate(idents):
            cur = env.idmef_db.getHeartbeat(ident)["heartbeat"]
            cur_status, cur_interval, cur_time = cur.get("additional_data('Analyzer status').data")[0], cur["heartbeat_interval"], cur["create_time"]
            cur_time_str = localization.format_datetime(float(cur_time))

            try:
                prev = env.idmef_db.getHeartbeat(idents[idx + 1])["heartbeat"]
                prev_status, prev_time = prev.get("additional_data('Analyzer status').data")[0], prev["create_time"]
            except:
                break

            if not cur_status or not cur_interval:
                continue

            total_interval += int(cur_interval)

            if latest:
                latest = False
                analyzer.status, analyzer.status_meaning = \
                    utils.get_analyzer_status_from_latest_heartbeat(cur, self._heartbeat_error_margin)
                if analyzer.status == "missing":
                    delta = time.time() - float(cur_time)
                    analyzer.events.append({ "time": cur_time_str, "value": _("Sensor is down since %s") % localization.format_timedelta(delta), "type": "down"})

            event = None
            if cur_status == "starting":
                if prev_status == "exiting":
                    event = { "time": cur_time_str, "value": _("Normal sensor start"), "type": "start" }
                else:
                    event = { "time": cur_time_str, "value": _("Unexpected sensor restart"), "type": "unexpected_restart" }

            elif cur_status == "running":
                delta = abs(int(cur_time) - int(prev_time) - int(cur_interval))
                if delta > self._heartbeat_error_margin:
                    delta = localization.format_timedelta(delta, granularity="second")
                    event = { "time": cur_time_str, "value": _("Unexpected heartbeat interval: %(delta)s") % {'delta': delta}, "type": "abnormal_heartbeat_interval" }


            elif cur_status == "exiting":
                event = { "time": cur_time_str, "value": _("Normal sensor stop"), "type": "normal_stop" }


            if event:
                analyzer.events.append(event)


        if not analyzer.status:
            analyzer.status, analyzer.status_meaning = "unknown", _("Unknown")

        if not analyzer.events:
            delta = localization.format_timedelta(total_interval / self._heartbeat_count)
            analyzer.events.append({ "time": "", "value":
                                     _("No anomaly in the last %(count)d heartbeats (one heartbeat every %(delta)s average)") %
                                       {'count': self._heartbeat_count, 'delta':delta}, "type": "no_anomaly" })

        self.dataset["analyzer"] = analyzer
