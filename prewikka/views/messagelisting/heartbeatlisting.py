# Copyright (C) 2004-2017 CS-SI. All Rights Reserved.
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
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from __future__ import absolute_import, division, print_function, unicode_literals

from prewikka import mainmenu, template
from prewikka.dataprovider import Criterion
from prewikka.utils import json

from .messagelisting import ListedMessage, MessageListing, MessageListingParameters


class HeartbeatListingParameters(MessageListingParameters):
    def register(self):
        MessageListingParameters.register(self)
        self.optional("heartbeat.analyzer(-1).analyzerid", text_type)
        self.optional("heartbeat.analyzer(-1).name", text_type)
        self.optional("heartbeat.analyzer(-1).node.address.address", text_type)
        self.optional("heartbeat.analyzer(-1).node.name", text_type)
        self.optional("heartbeat.analyzer(-1).model", text_type)


class ListedHeartbeat(ListedMessage):
    def setMessage(self, message, ident):
        self["selection"] = json.dumps(Criterion("heartbeat.messageid", "=", ident))
        self["summary"] = url_for("HeartbeatSummary", messageid=ident) if ident else None
        self["agent"] = self.createInlineFilteredField("heartbeat.analyzer(-1).name",
                                                       message["heartbeat.analyzer(-1).name"])
        self["model"] = self.createInlineFilteredField("heartbeat.analyzer(-1).model",
                                                       message["heartbeat.analyzer(-1).model"])
        self["node.name"] = self.createInlineFilteredField("heartbeat.analyzer(-1).node.name",
                                                           message["heartbeat.analyzer(-1).node.name"])

        self["node.address(*).address"] = []

        for address in message["heartbeat.analyzer(-1).node.address"]:
            hfield = self.createHostField("heartbeat.analyzer(-1).node.address.address", address["address"], address["category"])
            self["node.address(*).address"].append(hfield)

        self["time"] = self.createTimeField(message["heartbeat.create_time"])


class HeartbeatListing(MessageListing):
    view_menu = (N_("Agents"), N_("Heartbeats"))
    view_parameters = HeartbeatListingParameters
    view_permissions = [N_("IDMEF_VIEW")]
    view_template = template.PrewikkaTemplate(__name__, "templates/heartbeatlisting.mak")
    view_extensions = (("menu", mainmenu.MainMenuHeartbeat),)

    root = "heartbeat"
    filters = {}
    listed_heartbeat = ListedHeartbeat

    def _setMessage(self, message, ident):
        msg = self.listed_heartbeat(self.view_path, env.request.parameters)
        msg.setMessage(message, ident)

        return msg

    def _applyInlineFilters(self, criteria):
        for column, path in (("analyzerid", "heartbeat.analyzer(-1).analyzerid"),
                             ("name", "heartbeat.analyzer(-1).name"),
                             ("model", "heartbeat.analyzer(-1).model"),
                             ("address", "heartbeat.analyzer(-1).node.address.address"),
                             ("node_name", "heartbeat.analyzer(-1).node.name")):
            env.request.dataset[column + "_filtered"] = False
            if path in env.request.parameters:
                criteria += Criterion(path, "=", env.request.parameters[path])
                env.request.dataset[column + "_filtered"] = True

    def render(self):
        MessageListing.render(self)

        criteria = env.request.menu.get_criteria()

        self._applyInlineFilters(criteria)
        self._adjustCriteria(criteria)

        self._updateMessages(env.dataprovider.delete, criteria)

        self._setNavPrev(env.request.parameters["offset"])

        count = self._setMessages(criteria)

        env.request.dataset["nav"]["from"] = env.request.parameters["offset"] + 1
        env.request.dataset["nav"]["to"] = env.request.parameters["offset"] + len(env.request.dataset["messages"])
        env.request.dataset["limit"] = env.request.parameters["limit"]
        env.request.dataset["total"] = count

        self._setNavNext(env.request.parameters["offset"], count)
