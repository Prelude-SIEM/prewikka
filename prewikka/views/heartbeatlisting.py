# Copyright (C) 2004,2005,2006 PreludeIDS Technologies. All Rights Reserved.
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
# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING.  If not, write to
# the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.

from prewikka import view, User, utils
from prewikka.views.messagelisting import MessageListing, MessageListingParameters, ListedMessage


class HeartbeatListingParameters(MessageListingParameters):
    def register(self):
        MessageListingParameters.register(self)
        self.optional("heartbeat.analyzer(-1).name", str)
        self.optional("heartbeat.analyzer(-1).node.address.address", str)
        self.optional("heartbeat.analyzer(-1).node.name", str)
        self.optional("heartbeat.analyzer(-1).model", str)



class SensorHeartbeatListingParameters(HeartbeatListingParameters):
    def register(self):
        HeartbeatListingParameters.register(self)
        self.mandatory("analyzerid", str)



class ListedHeartbeat(ListedMessage):    
    def setMessage(self, message, ident):
        
        self["delete"] = ident
        self["summary"] = self.createMessageLink(ident, "heartbeat_summary")
        self["details"] = self.createMessageLink(ident, "heartbeat_details")
        self["agent"] = self.createInlineFilteredField("heartbeat.analyzer(-1).name",
                                                       message["heartbeat.analyzer(-1).name"])
        self["model"] = self.createInlineFilteredField("heartbeat.analyzer(-1).model",
                                                       message["heartbeat.analyzer(-1).model"])
        self["node_name"] = self.createInlineFilteredField("heartbeat.analyzer(-1).node.name",
                                                           message["heartbeat.analyzer(-1).node.name"])

        self["node_addresses"] = [ ]

        for address in message["heartbeat.analyzer(-1).node.address"]:
            hfield = self.createHostField("heartbeat.analyzer(-1).node.address.address", address["address"], address["category"])
            self["node_addresses"].append(hfield)
            
        self["time"] = self.createTimeField(message["heartbeat.create_time"], self.parameters["timezone"])



class HeartbeatListing(MessageListing, view.View):
    view_name = "heartbeat_listing"
    view_parameters = HeartbeatListingParameters
    view_permissions = [ User.PERM_IDMEF_VIEW ]
    view_template = "HeartbeatListing"

    root = "heartbeat"
    filters = { }
    summary_view = "heartbeat_summary"
    details_view = "heartbeat_details"
    listed_heartbeat = ListedHeartbeat

    def _getMessageIdents(self, criteria, limit=-1, offset=-1, order_by="time_desc"):
        return self.env.idmef_db.getHeartbeatIdents(criteria, limit, offset, order_by)

    def _fetchMessage(self, ident):
        return self.env.idmef_db.getHeartbeat(ident)

    def _setMessage(self, message, ident):
        msg = self.listed_heartbeat(self.view_name, self.env, self.parameters)
        msg.view_name = self.view_name
        msg.setMessage(message, ident)

        return msg

    def _applyInlineFilters(self, criteria):
        filter_found = False
        for column, path in (("name", "heartbeat.analyzer(-1).name"),
                             ("model", "heartbeat.analyzer(-1).model"),
                             ("address", "heartbeat.analyzer(-1).node.address.address"),
                             ("node_name", "heartbeat.analyzer(-1).node.name")):
            self.dataset[column + "_filtered"] = False
            if not filter_found:
                if self.parameters.has_key(path):
                    criteria.append("%s == '%s'" % (path, utils.escape_criteria(self.parameters[path])))
                    self.dataset[column + "_filtered"] = True
                    filter_found = True
        
    def _deleteMessage(self, ident):
        self.env.idmef_db.deleteHeartbeat(ident)

    def render(self):
        MessageListing.render(self)

        self._deleteMessages()
        criteria = [ ]
        start = end = None

        if self.parameters.has_key("timeline_unit") and self.parameters["timeline_unit"] != "unlimited":
            start, end = self._getTimelineRange()
            criteria.append("heartbeat.create_time >= '%s' && heartbeat.create_time < '%s'" % (str(start), str(end)))
        self._applyInlineFilters(criteria)
        self._adjustCriteria(criteria)

        self._setTimeline(start, end)
        self._setNavPrev(self.parameters["offset"])

        count = self._setMessages(criteria)
        self._setHiddenParameters()
        
        self.dataset["nav.from"] = self.parameters["offset"] + 1
        self.dataset["nav.to"] = self.parameters["offset"] + len(self.dataset["messages"])
        self.dataset["limit"] = self.parameters["limit"]
        self.dataset["total"] = count

        self._setNavNext(self.parameters["offset"], count)
        self._setTimezone()



class SensorHeartbeatListing(HeartbeatListing, view.View):
    view_name = "sensor_heartbeat_listing"
    view_parameters = SensorHeartbeatListingParameters
    view_permissions = [ User.PERM_IDMEF_VIEW ]
    view_template = "SensorHeartbeatListing"

    listed_heartbeat = ListedHeartbeat

    def _adjustCriteria(self, criteria):
        criteria.append("heartbeat.analyzer.analyzerid == '%s'" % self.parameters["analyzerid"])

    def _setHiddenParameters(self):
        HeartbeatListing._setHiddenParameters(self)
        self.dataset["hidden_parameters"].append(("analyzerid", self.parameters["analyzerid"]))

    def render(self):
        HeartbeatListing.render(self)
        self.dataset["analyzer"] = self.env.idmef_db.getAnalyzer(self.parameters["analyzerid"])
