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


import os.path
import urllib
import time
import copy
import re

from prewikka import view, User, utils
from prelude import idmef_path_new, idmef_path_get_value_type, IDMEF_VALUE_TYPE_STRING


class _MyTime:
    def __init__(self, t=None):
        self._t = t or time.time()
        self._index = 5 # second index

    def __getitem__(self, key):
        try:
            self._index = [ "year", "month", "day", "hour", "min", "sec" ].index(key)
        except ValueError:
            raise KeyError(key)
        
        return self

    def round(self, unit):
        t = list(time.localtime(self._t))
        if unit != "sec":
            t[5] = 0
            if unit != "min":
                t[4] = 0
                if unit != "hour":
                    t[3] = 0
                    if unit != "day":
                        t[2] = 1
                        if unit != "month":
                            t[1] = 1
                            t[0] += 1
                        else:
                            t[1] += 1
                    else:
                        t[2] += 1
                else:
                    t[3] += 1
            else:
                t[4] += 1
        else:
            t[5] += 1
        self._t = time.mktime(t)                

    def __add__(self, value):
        t = time.localtime(self._t)
        t = list(t)
        t[self._index] += value

        try:
            t = time.mktime(t)
            
        # Implementation specific: mktime might trigger an OverflowError
        # or a ValueError exception if the year member is out of range.
        # If this happen, we adjust the setting to a year known to work.

        except (OverflowError, ValueError):
            if t[0] >= 2038:
                # 2 ^ 31 - 1
                t = time.mktime(time.gmtime(2147483647))

            elif t[0] <= 1970:
                # Some implementation will fail with negative integer, we thus
                # set the minimum value to be the Epoch.  
                t = time.mktime(time.gmtime(0)) 

            else:
                raise OverflowError
        
        return _MyTime(t)

    def __sub__(self, value):
        return self + (-value)

    def __str__(self):
        return utils.time_to_ymdhms(time.localtime(self._t))
    
    def __int__(self):
        return int(self._t)



class MessageListingParameters(view.Parameters):
    def register(self):
        self.optional("timeline_value", int, default=1, save=True)
        self.optional("timeline_unit", str, default="hour", save=True)
        self.optional("timeline_end", long)
        self.optional("timeline_start", long)
        self.optional("offset", int, default=0)
        self.optional("limit", int, default=50, save=True)
        self.optional("timezone", str, "frontend_localtime", save=True)
        self.optional("delete", list, [ ])
        self.optional("apply", str)
        
        # submit with an image passes the x and y coordinate values
        # where the image was clicked
        self.optional("x", int)
        self.optional("y", int)
        
    def normalize(self, view_name, user):
        if len(self) == 0 or self.has_key("_load"):
            self["_load"] = True
            
            filter_set = self.has_key("filter")
            if not filter_set and self.has_key("timeline_value"):
                user.delConfigValue(view_name, "filter")

        # Filter out invalid limit which would trigger an exception.
        if self.has_key("limit") and int(self["limit"]) <= 0:
            self.pop("limit")
            
        view.Parameters.normalize(self, view_name, user)
        
        if self.has_key("timeline_value") ^ self.has_key("timeline_unit"):
            raise view.MissingParameterError(self.has_key("timeline_value") and "timeline_value" or "timeline_unit")
            
        if not self["timezone"] in ("frontend_localtime", "sensor_localtime", "utc"):
            raise view.InvalidValueError("timezone", self["timezone"])
        
        # remove the bulshit
        try:
            del self["x"]
            del self["y"]
        except KeyError:
            pass
        


class ListedMessage(dict):
    def __init__(self, env, parameters):
        self.env = env
        self.parameters = parameters
        self.timezone = parameters["timezone"]

    def createInlineFilteredField(self, object, value, direction=None):
        if value == None:
            return { "value": None, "inline_filter": None }

        if direction:
            index = self.parameters.max_index
            extra = { "%s_object_%d" % (direction, index): object,
                      "%s_operator_%d" % (direction, index): "=",
                      "%s_value_%d" % (direction, index): value }
        else:
            extra = { object: value }

        return { "value": value, "inline_filter": utils.create_link(self.view_name, self.parameters - ["_load", "_save"] + extra) }

    def createTimeField(self, t, timezone=None):
        if t:
            if timezone == "utc":
                t = time.gmtime(t)
                
            elif timezone == "sensor_localtime":
                t = time.gmtime(int(t) + t.gmt_offset)

            else: # timezone == "frontend_localtime"
                t = time.localtime(t)
            
            current = time.localtime()
        
            if t[:3] == current[:3]: # message time is today
                t = utils.time_to_hms(t)
            else:
                t = utils.time_to_ymdhms(t)
        else:
            t = "n/a"

        return { "value": t }

    def createHostField(self, object, value, category=None, direction=None):
        field = self.createInlineFilteredField(object, value, direction)
        field["host_commands"] = [ ]
        field["category"] = category
        
        for command in self.env.host_commands.keys():
            field["host_commands"].append((command.capitalize(),
                                           utils.create_link("Command",
                                                             { "origin": self.view_name, "command": command, "host": value })))

        return field
    
    def createMessageLink(self, ident, view):
        return utils.create_link(view, { "origin": self.view_name, "ident": ident })





class MessageListing:    
    def _adjustCriteria(self, criteria):
        pass
    
    def _setHiddenParameters(self):
        self.dataset["hidden_parameters"] = [ [ "view", self.view_name ] ]
        if self.parameters.has_key("timeline_end"):
            self.dataset["hidden_parameters"].append(("timeline_end", self.parameters["timeline_end"]))

        if self.parameters.has_key("_load"):
            self.dataset["hidden_parameters"].append(("_load", "True"))

    def _setTimelineNext(self, next):
        parameters = self.parameters - [ "offset" ] + { "timeline_end": int(next) }
        self.dataset["timeline.next"] = utils.create_link(self.view_name, parameters)

    def _setTimelinePrev(self, prev):
        parameters = self.parameters - [ "offset" ] + { "timeline_end": int(prev) }
        self.dataset["timeline.prev"] = utils.create_link(self.view_name, parameters)
        
    def _getTimelineRange(self):
        if self.parameters.has_key("timeline_start"):  
            start = _MyTime(self.parameters["timeline_start"])  
            end = start[self.parameters["timeline_unit"]] + self.parameters["timeline_value"]  
        elif self.parameters.has_key("timeline_end"):  
            end = _MyTime(self.parameters["timeline_end"])  
            start = end[self.parameters["timeline_unit"]] - self.parameters["timeline_value"]  
        else:  
            end = _MyTime()  
            if not self.parameters["timeline_unit"] in ("min", "hour"):  
                end.round(self.parameters["timeline_unit"])  
            start = end[self.parameters["timeline_unit"]] - self.parameters["timeline_value"]  

        return start, end
        
    def _setTimeline(self, start, end):
        for unit in "min", "hour", "day", "month", "year", "unlimited":
            self.dataset["timeline.%s_selected" % unit] = ""

        self.dataset["timeline.value"] = self.parameters["timeline_value"]
        self.dataset["timeline.%s_selected" % self.parameters["timeline_unit"]] = "selected='selected'"

        if self.parameters["timezone"] == "utc":
            func = time.gmtime
            self.dataset["timeline.range_timezone"] = "UTC"
        else:
            func = time.localtime
            self.dataset["timeline.range_timezone"] = "%+.2d:%.2d" % utils.get_gmt_offset()

        if not start and not end:
            return
        
        self.dataset["timeline.start"] = utils.time_to_ymdhms(func(int(start)))
        self.dataset["timeline.end"] = utils.time_to_ymdhms(func(int(end)))
        self.dataset["timeline.current"] = utils.create_link(self.view_name, self.parameters - ["timeline_end"])        

        if not self.parameters.has_key("timeline_end") and self.parameters["timeline_unit"] in ("min", "hour"):
            tmp = copy.copy(end)
            tmp.round(self.parameters["timeline_unit"])
            tmp = tmp[self.parameters["timeline_unit"]] - 1
            self._setTimelineNext(tmp[self.parameters["timeline_unit"]] + self.parameters["timeline_value"])
            self._setTimelinePrev(tmp[self.parameters["timeline_unit"]] - (self.parameters["timeline_value"] - 1))
        else:
            self._setTimelineNext(end[self.parameters["timeline_unit"]] + self.parameters["timeline_value"])
            self._setTimelinePrev(end[self.parameters["timeline_unit"]] - self.parameters["timeline_value"])

    def _setNavPrev(self, offset):
        if offset:
            self.dataset["nav.first"] = utils.create_link(self.view_name, self.parameters - [ "offset" ])
            self.dataset["nav.prev"] = utils.create_link(self.view_name,
                                                         self.parameters +
                                                         { "offset": offset - self.parameters["limit"] })
        else:
            self.dataset["nav.prev"] = None
            
    def _setNavNext(self, offset, count):
        if count > offset + self.parameters["limit"]:
            offset = offset + self.parameters["limit"]
            self.dataset["nav.next"] = utils.create_link(self.view_name, self.parameters + { "offset": offset })
            offset = count - ((count % self.parameters["limit"]) or self.parameters["limit"])
            self.dataset["nav.last"] = utils.create_link(self.view_name, self.parameters + { "offset": offset })
        else:
            self.dataset["nav.next"] = None

    def _setTimezone(self):
        for timezone in "utc", "sensor_localtime", "frontend_localtime":
            if timezone == self.parameters["timezone"]:
                self.dataset["timeline.%s_selected" % timezone] = "selected='selected'"
            else:
                self.dataset["timeline.%s_selected" % timezone] = ""

    def _getInlineFilter(self, name):
        return name, self.parameters.get(name)

    def _setMessages(self, criteria):
        self.dataset["messages"] = [ ]
        
        for ident in self._getMessageIdents(criteria, self.parameters["limit"], self.parameters["offset"]):
            message = self._fetchMessage(ident)
            dataset = self._setMessage(message, ident)
            self.dataset["messages"].append(dataset)

    def _deleteMessages(self):        
        if len(self.parameters["delete"]) == 0:
            return

        if not self.user.has(User.PERM_IDMEF_ALTER):
            raise User.PermissionDeniedError(self.current_view)

        idents = [ ]
        for delete in self.parameters["delete"]:
            if delete.isdigit():
                idents += [ long(delete) ]
            else:
                criteria = urllib.unquote_plus(delete)
                idents += self._getMessageIdents(criteria)

        self._deleteMessage(idents)
        del self.parameters["delete"]


