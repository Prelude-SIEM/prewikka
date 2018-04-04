# coding: utf-8
# Copyright (C) 2018 CS-SI. All Rights Reserved.
# Author: Antoine Luong <antoine.luong@c-s.fr>
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

"""DataSearch heartbeat view."""

from __future__ import absolute_import, division, print_function, unicode_literals

import collections

from prewikka import version

from . import idmef


class HeartbeatFormatter(idmef.IDMEFFormatter):
    type = "heartbeat"

    def __init__(self):
        idmef.IDMEFFormatter.__init__(self)
        self._objects = {"heartbeat.create_time": self._format_time}


class HeartbeatQueryParser(idmef.IDMEFQueryParser):
    _sort_order = ["heartbeat.create_time/order_desc"]

    def add_order(self, field, order="asc"):
        self._sort_order = ["heartbeat.%s/order_%s" % (field, order)]


class HeartbeatDataSearch(idmef.IDMEFDataSearch):
    plugin_name = "DataSearch: Heartbeats"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("Heartbeat listing page")

    type = "heartbeat"
    name = "heartbeats"
    section = N_("Agents")
    tabs = (N_("Heartbeats"), N_("Aggregated heartbeats"))
    formatter = HeartbeatFormatter
    query_parser = HeartbeatQueryParser
    criterion_config_default = "criterion"
    sort_path_default = "create_time"
    groupby_default = ["analyzer(-1).name"]
    default_columns = collections.OrderedDict([
        ("heartbeat.create_time", N_("Date")),
        ("heartbeat.analyzer(-1).name", N_("Agent")),
        ("heartbeat.analyzer(-1).node.address(*).address", N_("Node address")),
        ("heartbeat.analyzer(-1).node.name", N_("Node name")),
        ("heartbeat.analyzer(-1).model", N_("Model"))
    ])
    _delete_confirm = N_("Delete the selected heartbeats?")
