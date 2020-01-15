# coding: utf-8
# Copyright (C) 2018-2020 CS-SI. All Rights Reserved.
# Author: Camille Gardet <camille.gardet@c-s.fr>
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

"""DataSearch threat view."""

from __future__ import absolute_import, division, print_function, unicode_literals

import collections
import prelude

from prewikka import dataprovider, resource, version

from . import alert, datasearch


class ThreatFormatter(alert.AlertFormatter):
    def __init__(self, data_type):
        alert.AlertFormatter.__init__(self, data_type)
        self._objects["alert.classification.text"] = self._format_classification

    def _format_classification(self, root, obj, finfo):
        return resource.HTMLNode("ul", self._format_value(
            root.get("alert.classification"),
            prelude.IDMEFClass("alert.classification.text"),
            label=False,
            tooltip=root.get("alert.assessment.impact.description")
        ))


class ThreatQueryParser(alert.AlertQueryParser):
    def __init__(self, query, parent, groupby=[], offset=0, limit=50):
        alert.AlertQueryParser.__init__(self, query, parent, groupby, offset, limit)

        threat_criterion = dataprovider.Criterion("alert.assessment.impact.severity", "=", "high") | (
            dataprovider.Criterion("alert.assessment.impact.severity", ">=", "medium") &
            dataprovider.Criterion("alert.correlation_alert.name", "!=", None)
        )

        self.criteria += threat_criterion
        self.all_criteria = self.criteria + env.request.menu.get_criteria()


class ThreatDataSearch(alert.AlertDataSearch):
    plugin_name = "DataSearch: Threats"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("Threat listing page")

    name = "threats"
    section = N_("Threats")
    tabs = (N_("Threats"), N_("Aggregated threats"))
    formatter = ThreatFormatter
    query_parser = ThreatQueryParser
    default_columns = collections.OrderedDict([
        ("alert.create_time", N_("Date")),
        ("alert.classification.text", N_("Classification")),
        ("alert.source(0).node.address(0).address", N_("Source")),
        ("alert.target(0).node.address(0).address", N_("Target")),
        ("alert.analyzer(-1).name", N_("Program"))
    ])

    def _get_column_property(self, field, pi):
        pi.column_index = pi.path

        hidden = pi.path not in self._main_fields
        if hidden and pi.path not in self._extra_table_fields:
            return None

        return datasearch.COLUMN_PROPERTIES(label=self.default_columns.get('alert.%s' % field, field.capitalize()),
                                            name=field,
                                            index=field,
                                            hidden=hidden,
                                            sortable=True,
                                            align="left" if pi.path == "alert.classification.text" else "center")
