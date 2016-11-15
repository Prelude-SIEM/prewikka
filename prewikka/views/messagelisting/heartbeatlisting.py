# Copyright (C) 2004-2016 CS-SI. All Rights Reserved.
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

from prewikka import mainmenu, template, usergroup, utils, view
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
        self["summary"] = self.createMessageIdentLink(ident, "HeartbeatSummary")
        self["agent"] = self.createInlineFilteredField("heartbeat.analyzer(-1).name",
                                                       message["heartbeat.analyzer(-1).name"])
        self["model"] = self.createInlineFilteredField("heartbeat.analyzer(-1).model",
                                                       message["heartbeat.analyzer(-1).model"])
        self["node.name"] = self.createInlineFilteredField("heartbeat.analyzer(-1).node.name",
                                                           message["heartbeat.analyzer(-1).node.name"])

        self["node.address(*).address"] = [ ]

        for address in message["heartbeat.analyzer(-1).node.address"]:
            hfield = self.createHostField("heartbeat.analyzer(-1).node.address.address", address["address"], address["category"])
            self["node.address(*).address"].append(hfield)

        self["time"] = self.createTimeField(message["heartbeat.create_time"])



class HeartbeatListing(MessageListing):
    view_name = N_("Heartbeats")
    view_parameters = HeartbeatListingParameters
    view_permissions = [ N_("IDMEF_VIEW") ]
    view_template = template.PrewikkaTemplate(__name__, "templates/heartbeatlisting.mak")
    view_extensions = (("menu", mainmenu.MainMenuHeartbeat),)
    view_section = N_("Agents")
    view_order = 1

    root = "heartbeat"
    filters = { }
    listed_heartbeat = ListedHeartbeat

    def _setMessage(self, message, ident):
        msg = self.listed_heartbeat(self.view_path, self.parameters)
        msg.view_name = self.view_name
        msg.setMessage(message, ident)

        return msg

    def _applyInlineFilters(self, criteria):
        filter_found = False
        for column, path in (("analyzerid", "heartbeat.analyzer(-1).analyzerid"),
                             ("name", "heartbeat.analyzer(-1).name"),
                             ("model", "heartbeat.analyzer(-1).model"),
                             ("address", "heartbeat.analyzer(-1).node.address.address"),
                             ("node_name", "heartbeat.analyzer(-1).node.name")):
            self.dataset[column + "_filtered"] = False
            if not filter_found:
                if self.parameters.has_key(path):
                    criteria += Criterion(path, "=", self.parameters[path])
                    self.dataset[column + "_filtered"] = True
                    filter_found = True

    def render(self):
        MessageListing.render(self)

        criteria = self.menu.get_criteria()
        start = end = None

        self._applyInlineFilters(criteria)
        self._adjustCriteria(criteria)

        self._updateMessages(env.dataprovider.delete, criteria)

        self._setNavPrev(self.parameters["offset"])

        count = self._setMessages(criteria)

        self.dataset["nav"]["from"] = self.parameters["offset"] + 1
        self.dataset["nav"]["to"] = self.parameters["offset"] + len(self.dataset["messages"])
        self.dataset["limit"] = self.parameters["limit"]
        self.dataset["total"] = count

        self._setNavNext(self.parameters["offset"], count)
