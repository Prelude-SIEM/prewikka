# Copyright (C) 2004-2017 CS-SI. All Rights Reserved.
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

from __future__ import absolute_import, division, print_function, unicode_literals
import time

import pkg_resources
from prewikka import hookmanager, localization, mainmenu, template, utils, view, response
from prewikka.dataprovider import Criterion
from prewikka.utils import html, json


class AgentsParameters(view.Parameters):
    def register(self):
        self.optional("types", list, default=[])
        self.optional("filter", json.loads)
        self.optional("status", list, default=[])


class Agents(view.View):
    view_parameters = AgentsParameters
    view_menu = (N_("Agents"), N_("Agents"))
    plugin_htdocs = (("agents", pkg_resources.resource_filename(__name__, 'htdocs')),)

    def __init__(self):
        view.View.__init__(self)
        self._heartbeat_count = int(env.config.general.get("heartbeat_count", 30))
        self._heartbeat_error_margin = int(env.config.general.get("heartbeat_error_margin", 3))

    def _get_analyzer(self, analyzerid):
        res = env.dataprovider.get(Criterion("heartbeat.analyzer(-1).analyzerid", "=", analyzerid), limit=1)
        heartbeat = res[0]["heartbeat"]
        analyzer = heartbeat["analyzer"][-1]

        return analyzer, heartbeat

    def _get_analyzers(self, reqstatus):
        criteria = env.request.parameters.get("filter")

        for (analyzerid,) in env.dataprovider.query(["heartbeat.analyzer(-1).analyzerid/group_by"], criteria):
            analyzer, heartbeat = self._get_analyzer(analyzerid)
            status, status_text = utils.get_analyzer_status_from_latest_heartbeat(
                heartbeat, self._heartbeat_error_margin
            )

            if reqstatus and status not in reqstatus:
                continue

            delta = float(heartbeat.get("create_time")) - time.time()

            heartbeat_listing = url_for("HeartbeatListing.render", **{"heartbeat.analyzer(-1).analyzerid": analyzerid})
            alert_listing = url_for("AlertListing.render", **{"analyzer_object_0": "alert.analyzer.analyzerid", "analyzer_operator_0": "=", "analyzer_value_0": analyzerid})
            heartbeat_analyze = url_for(".analyze", analyzerid=analyzerid)

            node_name = analyzer["node.name"] or _("Node name n/a")
            osversion = analyzer["osversion"] or _("OS version n/a")
            ostype = analyzer["ostype"] or _("OS type n/a")

            yield {"id": analyzerid,
                   "label": "%s - %s %s" % (node_name, ostype, osversion),
                   "location": analyzer["node.location"] or _("Node location n/a"),
                   "node": node_name,
                   "name": analyzer["name"],
                   "model": analyzer["model"],
                   "class": analyzer["class"],
                   "version": analyzer["version"],
                   "latest_heartbeat": localization.format_timedelta(delta, add_direction=True),
                   "status": status,
                   "status_text": status_text,
                   "links": [
                       {"text": _("Alert listing"), "link": alert_listing},
                       {"text": _("Heartbeat listing"), "link": heartbeat_listing},
                       {"text": _("Heartbeat analysis"), "link": heartbeat_analyze,
                        "class": "widget-link", "title": _("Heartbeat analysis")},
                   ]}

    @view.route("/agents/agents/<list:status>", permissions=[N_("IDMEF_VIEW")])
    @view.route("/agents/agents", permissions=[N_("IDMEF_VIEW")])
    def agents(self, status=[]):
        analyzer_data = list(self._get_analyzers(status))
        list(hookmanager.trigger("HOOK_AGENTS_EXTRA_CONTENT", analyzer_data))
        extra_columns = filter(None, hookmanager.trigger("HOOK_AGENTS_EXTRA_COLUMN"))

        return template.PrewikkaTemplate(__name__, "templates/agents.mak").render(data=analyzer_data, extra_columns=extra_columns)

    @view.route("/agents/delete", methods=["POST"], permissions=[N_("IDMEF_ALTER")])
    def delete(self):
        c = Criterion()

        for analyzerid in env.request.parameters["analyzerid"]:
            for i in env.request.parameters["types"]:
                if i in ("alert", "heartbeat"):
                    c |= Criterion("%s.analyzer.analyzerid" % i, "=", analyzerid)

        env.dataprovider.delete(c)
        return response.PrewikkaRedirectResponse(url_for(".agents"))

    @view.route("/agents/analyze/<analyzerid>", permissions=[N_("IDMEF_VIEW")])
    def analyze(self, analyzerid):
        analyzer, heartbeat = self._get_analyzer(analyzerid)
        delta = float(heartbeat["create_time"]) - time.time()
        analyzer.last_heartbeat_time = localization.format_timedelta(delta, add_direction=True)

        analyzer.status = None
        analyzer.events = [ ]

        res = env.dataprovider.get(Criterion("heartbeat.analyzer(-1).analyzerid", "=", analyzerid), limit=self._heartbeat_count)

        prev = None
        latest = True
        total_interval = 0

        for idx, cur in enumerate(res):
            cur = cur["heartbeat"]
            cur_status, cur_interval, cur_time = cur.get("additional_data('Analyzer status').data")[0], cur["heartbeat_interval"], cur["create_time"]
            cur_time_str = localization.format_datetime(float(cur_time))

            try:
                prev = res[idx + 1]["heartbeat"]
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
                    analyzer.events.append(utils.AttrObj(time=cur_time_str, value=_("Sensor is down since %s") % localization.format_timedelta(delta), type="down"))

            event = None
            if cur_status == "starting":
                if prev_status == "exiting":
                    event = utils.AttrObj(time=cur_time_str, value=_("Normal sensor start"), type="start")
                else:
                    event = utils.AttrObj(time=cur_time_str, value=_("Unexpected sensor restart"), type="unexpected_restart")

            elif cur_status == "running":
                delta = abs(int(cur_time) - int(prev_time) - int(cur_interval))
                if delta > self._heartbeat_error_margin:
                    delta = localization.format_timedelta(delta, granularity="second")
                    event = utils.AttrObj(time=cur_time_str, value=_("Unexpected heartbeat interval: %(delta)s") % {'delta': delta}, type="abnormal_heartbeat_interval")


            elif cur_status == "exiting":
                event = utils.AttrObj(time=cur_time_str, value=_("Normal sensor stop"), type="normal_stop")


            if event:
                analyzer.events.append(event)


        if not analyzer.status:
            analyzer.status, analyzer.status_meaning = "unknown", _("Unknown")

        if not analyzer.events:
            delta = localization.format_timedelta(total_interval / self._heartbeat_count)
            analyzer.events.append(utils.AttrObj(
                time="",
                value=_("No anomaly in the last %(count)d heartbeats (one heartbeat every %(delta)s average)") % {'count': self._heartbeat_count, 'delta': delta},
                type="no_anomaly"
            ))

        return template.PrewikkaTemplate(__name__, "templates/heartbeatanalyze.mak").render(analyzer=analyzer)
