# coding: utf-8
# Copyright (C) 2017-2020 CS-SI. All Rights Reserved.
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

from prewikka import hookmanager, localization, resource, utils, version
from prewikka.dataprovider import Criterion

from .datasearch import COLUMN_PROPERTIES
from . import idmef


class AlertFormatter(idmef.IDMEFFormatter):
    def __init__(self, data_type):
        idmef.IDMEFFormatter.__init__(self, data_type)
        self._objects = {
            "alert.create_time": self._format_time,
            "alert.classification": self._format_classification,
        }

    def format_value(self, field, value):
        node = idmef.IDMEFFormatter.format_value(self, field, value)
        if field != "assessment.impact.severity":
            return node

        classes = {"info": "btn-info", "low": "btn-success", "medium": "btn-warning", "high": "btn-danger"}
        node._extra = {"_classes": classes.get(value, "btn-default")}
        return node

    def _format_classification(self, finfo, root, obj):
        return resource.HTMLNode("ul", self._format_value(
            root.get("alert.classification"),
            prelude.IDMEFClass("alert.classification.text"),
            label=False,
            tooltip=root.get("alert.assessment.impact.description")
        ))

    def _get_best_path(self, root, field):
        for nidx, node in enumerate(root.get("%s(*).node" % field)):
            for aidx, addr in enumerate(node.get("address(*)")):
                if addr.get("category") in ("unknown", "ipv4-addr", "ipv6-addr") and addr.get("address"):
                    return "%s(%d).node.address(%d).address" % (field, nidx, aidx)

            if node.get("name"):
                return "%s(%d).node.name" % (field, nidx)

        return "%s(0).node.address(0).address" % field

    def format(self, finfo, root, obj):
        ret = idmef.IDMEFFormatter.format(self, finfo, root, obj)
        if not ret:
            return ret

        basic_fields = {
            "alert.source": self._get_best_path(root, "alert.source"),
            "alert.target": self._get_best_path(root, "alert.target"),
            "alert.analyzer(-1)": "alert.analyzer(-1).name",
        }

        if finfo.path in basic_fields:
            finfo = env.dataprovider.get_path_info(basic_fields[finfo.path])
            obj = root.get(finfo.path)
            simple_fmt = idmef.IDMEFFormatter.format(self, finfo, root, obj)
            if "class" in ret.attrs:
                ret.attrs["class"] += " expert-mode"
            else:
                ret.attrs["class"] = "expert-mode"

            if "class" in simple_fmt.attrs:
                simple_fmt.attrs["class"] += " basic-mode"
            else:
                simple_fmt.attrs["class"] = "basic-mode"

            return ret + simple_fmt
        else:
            return ret


class AlertQueryParser(idmef.IDMEFQueryParser):
    _default_sort_order = ["alert.create_time/order_desc"]


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
        ("alert.assessment.impact.severity", N_("Severity")),
        ("alert.create_time", N_("Date")),
        ("alert.classification", N_("Classification")),
        ("alert.source", N_("Source")),
        ("alert.target", N_("Target")),
        ("alert.analyzer(-1)", N_("Analyzer"))
    ])
    lucene_search_fields = ["classification", "source", "target", "analyzer(-1)"]
    _delete_confirm = N_("Delete the selected alerts?")

    def __init__(self, *args, **kwargs):
        idmef.IDMEFDataSearch.__init__(self, *args, **kwargs)
        self.columns_properties["assessment.impact.severity"].width = 50

    def _get_default_cells(self, obj, search):
        cells = idmef.IDMEFDataSearch._get_default_cells(self, obj, search)

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
                return []

        return [("idmef", utils.AttrObj(label=_("IDMEF"), info=html))]

    def _get_column_property(self, field, pi):
        pi.column_index = pi.path

        hidden = pi.path not in self._main_fields
        if hidden and pi.path not in self._extra_table_fields:
            return None

        return COLUMN_PROPERTIES(label=self.default_columns.get('alert.%s' % field, field.capitalize()),
                                 name=field,
                                 index=field,
                                 hidden=hidden,
                                 sortable=True,
                                 align="left" if pi.path == "alert.classification" else "center")

    @hookmanager.register("HOOK_RISKOVERVIEW_DATA", _order=3)
    def _set_alerts_summary(self):
        severities = ["info", "low", "medium", "high"]
        alerts = dict(env.dataprovider.query(
            ["alert.assessment.impact.severity/group_by", "count(alert.messageid)"],
            env.request.menu.get_criteria()
        ))

        labels = {
            "info": utils.AttrObj(title=_("Minimal severity"), label="label-info"),
            "low": utils.AttrObj(title=_("Low severity"), label="label-success"),
            "medium": utils.AttrObj(title=_("Medium severity"), label="label-warning"),
            "high": utils.AttrObj(title=_("High severity"), label="label-danger")
        }

        data = []
        for i in reversed(severities):
            data.append(
                resource.HTMLNode("a", localization.format_number(alerts.get(i, 0), short=True),
                                  title=labels[i].title, _class="label " + labels[i].label,
                                  href=url_for("AlertDataSearch.forensic", criteria=Criterion("alert.assessment.impact.severity", "==", i)))
            )

        return utils.AttrObj(
            name="alerts",
            title=resource.HTMLNode("a", _("Alerts"), href=url_for("AlertDataSearch.forensic")),
            data=data
        )
