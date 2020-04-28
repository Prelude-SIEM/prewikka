# coding: utf-8
# Copyright (C) 2015-2020 CS-SI. All Rights Reserved.
# Author: Sélim Menouar <selim.menouar@c-s.fr>
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

"""DataSearch log view."""

from __future__ import absolute_import, division, print_function, unicode_literals

import collections

from prewikka import hookmanager, localization, resource, utils, version, view
from prewikka.views.datasearch import datasearch

from . import elasticsearch


class LogFormatter(datasearch.Formatter):
    highlighter = elasticsearch.ElasticsearchHighLighter
    ignore_fields = frozenset(["raw_message"])


class LogDataSearch(datasearch.DataSearch):
    plugin_name = "DataSearch: Logs"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("Log listing page")

    view_permissions = [N_("LOG_VIEW")]

    type = "log"
    name = "logs"
    section = N_("Logs")
    tabs = (N_("Logs"), N_("Aggregated logs"))
    formatter = LogFormatter
    query_parser = elasticsearch.ElasticsearchQueryParser
    groupby_default = ["host"]
    sort_path_default = "timestamp"
    default_columns = collections.OrderedDict([
        ("log.timestamp", N_("Date")),
        ("log.host", N_("Host")),
        ("log.program", N_("Program")),
        ("log.message", N_("Message"))
    ])

    def __init__(self, *args, **kwargs):
        datasearch.DataSearch.__init__(self, *args, **kwargs)

        self.columns_properties["message"].width = 100
        self.columns_properties["message"].align = "left"

        paths = [
            "alert.source.node.address.address",
            "alert.source.node.name",
            "alert.target.node.address.address",
            "alert.target.node.name",
            "host"
        ]
        env.linkmanager.add_link(N_("Search in logs"), paths, lambda x: url_for("LogDataSearch.forensic", query='"%s"' % x, query_mode="lucene"))
        env.linkmanager.add_link(N_("View logs"), paths, lambda x: url_for("LogDataSearch.forensic", query="host:%s" % x, query_mode="lucene"))

    @hookmanager.register("HOOK_RISKOVERVIEW_DATA", _order=2)
    def _set_logs_summary(self):
        count = localization.format_number(env.dataprovider.query(["count(1)"], env.request.menu.get_criteria(), type="log")[0][0], short=True)
        data = resource.HTMLNode("a", count, title=_("Log"), _class="label label-info", href=url_for("LogDataSearch.dashboard", **env.request.menu_parameters))
        return utils.AttrObj(
            name="archive",
            title=resource.HTMLNode("span", _("Archive")),
            data=[data]
        )

    def _get_column_property(self, field, pi):
        return datasearch.COLUMN_PROPERTIES(label=field.capitalize(), name=field, index=field, width=20, hidden=field not in ("timestamp", "host", "program", "message"))

    @hookmanager.register("HOOK_ALERTSUMMARY_MEANING_LINK")
    def _add_original_log_link(self, alert, meaning, value):
        detect_time = alert.get("detect_time")
        if meaning != "Original Log" or not detect_time:
            return

        query = []

        host = next(hookmanager.trigger("HOOK_LOG_EXTRACT_IDMEF_HOST", alert), None)
        if host:
            query.append('host:"%s"' % host)

        detect_time = utils.timeutil.get_timestamp_from_datetime(detect_time)
        return resource.HTMLNode("a", _("Context"), href=url_for(
            "LogDataSearch.forensic",
            query=" ".join(query),
            query_mode="lucene",
            timeline_start=detect_time - 5,
            timeline_end=detect_time + 30,
            timeline_mode="custom")
        )

    def get_forensic_actions(self):
        return datasearch.DataSearch.get_forensic_actions(self) + \
            [resource.HTMLNode("button", _("Syslog export"),
             formaction=url_for(".syslog_download"), type="submit", form="datasearch_export_form",
             _class="btn btn-default needone", _icon="fa-file-text-o", _sortkey="download")]

    @view.route("/logs/syslog_download", methods=["POST"])
    def syslog_download(self):
        grid = utils.json.loads(env.request.parameters["datasearch_grid"], object_pairs_hook=collections.OrderedDict)
        with utils.mkdownload("journal.log") as dl:
            for row in grid:
                dl.write((" ".join([row["raw_message"], "\n"])).encode("utf8"))

        return dl
