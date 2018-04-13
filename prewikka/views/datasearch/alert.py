# coding: utf-8
# Copyright (C) 2017-2018 CS-SI. All Rights Reserved.
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

"""DataSearch alert view."""

from __future__ import absolute_import, division, print_function, unicode_literals

import collections
import prelude

from prewikka import resource, utils, version

from . import idmef


class AlertFormatter(idmef.IDMEFFormatter):
    type = "alert"

    def __init__(self):
        idmef.IDMEFFormatter.__init__(self)
        self._objects = {"alert.create_time": self._format_time,
                         "alert.classification": self._format_classification}

    def _format_classification(self, root, obj, finfo):
        severity = root.get("alert.assessment.impact.severity")
        severity = "impact_severity_%s" % severity if severity else ""

        r = resource.HTMLNode("ul", self._format_value(
            root.get("alert.classification"),
            prelude.IDMEFClass("alert.classification.text"),
            _class=severity,
            tooltip=root.get("alert.assessment.impact.description")
        ))

        for i in ("alert.assessment", "alert.correlation_alert", "alert.tool_alert", "alert.overflow_alert"):
            obj = root.get(i)
            if obj:
                r += self._format_object(root, obj, prelude.IDMEFClass(i))

        return r


class AlertQueryParser(idmef.IDMEFQueryParser):
    _sort_order = ["alert.create_time/order_desc"]

    def add_order(self, field, order="asc"):
        self._sort_order = ["alert.%s/order_%s" % (field, order)]


class AlertDataSearch(idmef.IDMEFDataSearch):
    plugin_name = "DataSearch: Alerts"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("Alert listing page")

    type = "alert"
    name = "alerts"
    section = N_("Alerts")
    tabs = (N_("Alerts"), N_("Aggregated alerts"))
    formatter = AlertFormatter
    query_parser = AlertQueryParser
    criterion_config_default = "criterion"
    sort_path_default = "create_time"
    groupby_default = ["source(0).node.address(0).address"]
    path_translate = {"classification": (("alert.classification.text", "alert.correlation_alert.name"), None),
                      "source": (("alert.source(*).node.name", "alert.source(*).node.address(*).address"), None),
                      "target": (("alert.target(*).node.name", "alert.target(*).node.address(*).address"), None),
                      "analyzer(-1)": (("alert.analyzer(-1).node.name", "alert.analyzer(-1).node.location", "alert.analyzer(-1).node.address(*).address"), None)}
    default_columns = collections.OrderedDict([
        ("alert.create_time", N_("Date")),
        ("alert.classification", N_("Classification")),
        ("alert.source", N_("Source")),
        ("alert.target", N_("Target")),
        ("alert.analyzer(-1)", N_("Analyzer"))
    ])
    lucene_search_fields = ["classification", "source", "target", "analyzer(-1)"]
    _delete_confirm = N_("Delete the selected alerts?")

    def _get_default_cells(self, obj):
        cells = idmef.IDMEFDataSearch._get_default_cells(self, obj)

        severity = obj.get("alert.assessment.impact.severity")
        if severity:
            cells["_classes"] = "assessment_impact_severity_%s" % severity

        return cells

    def _build_table(self, idmefd):
        rows = []

        for key, value in sorted(idmefd.items()):
            colkey = resource.HTMLNode("td", key)
            colval = resource.HTMLNode("td", ", ".join(value) if isinstance(value, list) else value)
            rows.append(resource.HTMLNode("tr", colkey, colval))

        return resource.HTMLNode("table", *rows, _class="table table-condensed")

    def _build_classification(self, alert):
        idmef = {}
        self._recurse_idmef(idmef, alert["classification"])
        self._recurse_idmef(idmef, alert["assessment"])

        return self._build_table(idmef)

    def _generic_builder(self, alert, path):
        idmef = {}
        self._recurse_idmef(idmef, alert[path])

        return self._build_table(idmef)

    def _get_extra_infos(self):
        builders = {
            "classification": self._build_classification,
            "assessment": self._build_classification
        }

        field = env.request.parameters["field"]
        parent_field = field.split('.', 1)[0]
        criteria = utils.json.loads(env.request.parameters["_criteria"])
        alert = env.dataprovider.get(criteria)[0]["alert"]

        builder = next((v for k, v in builders.items() if k in field), None)
        if builder:
            html = builder(alert)
        else:
            try:
                html = self._generic_builder(alert, parent_field)
            except RuntimeError:
                return

        return [("idmef", utils.AttrObj(label=_("IDMEF"), info=html))]
