# Copyright (C) 2004-2015 CS-SI. All Rights Reserved.
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

from prewikka import view, usergroup, utils, mainmenu, env
from . import templates
from messagelisting import MessageListing, MessageListingParameters, ListedMessage


class HeartbeatListingParameters(MessageListingParameters):
    def register(self):
        MessageListingParameters.register(self)
        self.optional("heartbeat.analyzer(-1).analyzerid", str)
        self.optional("heartbeat.analyzer(-1).name", str)
        self.optional("heartbeat.analyzer(-1).node.address.address", str)
        self.optional("heartbeat.analyzer(-1).node.name", str)
        self.optional("heartbeat.analyzer(-1).model", str)


class ListedHeartbeat(ListedMessage):
    def setMessage(self, message, ident):

        self["selection"] = ident
        self["summary"] = self.createMessageLink(ident, "HeartbeatSummary")
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
            
        self["time"] = self.createTimeField(message["heartbeat.create_time"], self.parameters["timezone"])



class HeartbeatListing(MessageListing):
    view_name = N_("Heartbeats")
    view_parameters = HeartbeatListingParameters
    view_permissions = [ "IDMEF_VIEW" ]
    view_template = templates.HeartbeatListing
    view_extensions = (("menu", mainmenu.MainMenuHeartbeat),)
    view_section = N_("Agents")
    view_order = 1

    root = "heartbeat"
    filters = { }
    listed_heartbeat = ListedHeartbeat

    def _getMessageIdents(self, criteria, limit=-1, offset=-1, order_by="time_desc"):
        return env.idmef_db.getHeartbeatIdents(criteria, limit, offset, order_by)

    def _fetchMessage(self, ident):
        return env.idmef_db.getHeartbeat(ident)

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
                             ("node.name", "heartbeat.analyzer(-1).node.name")):
            self.dataset[column + "_filtered"] = False
            if not filter_found:
                if self.parameters.has_key(path):
                    criteria.append("%s == '%s'" % (path, utils.escape_criteria(self.parameters[path])))
                    self.dataset[column + "_filtered"] = True
                    filter_found = True

    def _deleteMessage(self, ident, is_ident):
        env.idmef_db.deleteHeartbeat(ident)

    def render(self):
        MessageListing.render(self)

        self._updateMessages(self._deleteMessage)
        criteria = [ ]
        start = end = None

        time_criteria = self.menu.get_criteria("heartbeat")
        if time_criteria:
            criteria.append(time_criteria)

        self._applyInlineFilters(criteria)
        self._adjustCriteria(criteria)

        self._setNavPrev(self.parameters["offset"])

        count = self._setMessages(criteria)

        self.dataset["nav.from"] = self.parameters["offset"] + 1
        self.dataset["nav.to"] = self.parameters["offset"] + len(self.dataset["messages"])
        self.dataset["limit"] = self.parameters["limit"]
        self.dataset["total"] = count

        self._setNavNext(self.parameters["offset"], count)
