# Copyright (C) 2004,2005 PreludeIDS Technologies. All Rights Reserved.
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
        self.optional("timeline_end", int)
        self.optional("timeline_start", int)
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
        
        for p1, p2 in [ ("timeline_value", "timeline_unit") ]:
            if self.has_key(p1) ^ self.has_key(p2):
                raise view.MissingParameterError(self.has_key(p1) and p1 or p2)
            
        if not self["timezone"] in ("frontend_localtime", "sensor_localtime", "utc"):
            raise view.InvalidValueError("timezone", self["timezone"])

        # remove the bulshit
        try:
            del self["x"]
            del self["y"]
        except KeyError:
            pass



class AlertListingParameters(MessageListingParameters):
    allow_extra_parameters = True

    def register(self):
        self.max_index = 0
        MessageListingParameters.register(self)
        self.optional("aggregated_source", list, [ "alert.source(0).node.address(0).address" ], save=True)
        self.optional("aggregated_target", list, [ "alert.target(0).node.address(0).address" ], save=True)
        self.optional("aggregated_classification", list, [ "none" ], save=True)
        self.optional("filter", str, save=True)
        self.optional("alert.classification.text", list, [ ], save=True)
        self.optional("alert.assessment.impact.severity", list, [ ], save=True)
        self.optional("alert.assessment.impact.completion", list, [ ], save=True)
        self.optional("alert.assessment.impact.type", list, [ ], save=True)

    def _loadColumnParam(self, view_name, user, paramlist, column):
        ret = False
        sorted = [ ]

        for parameter, object in paramlist.items():
            idx = parameter.find(column + "_object_")
            if idx == -1:
                continue

            num = int(parameter.replace(column + "_object_", "", 1))
            if num >= self.max_index:
                self.max_index = num + 1

            ret = True
            
            try:
                value = paramlist["%s_value_%s" % (column, num)]
            except KeyError:
                continue

            do_append = True
            for tmp in sorted:
                if tmp[1] == object and tmp[2] == value:
                    do_append = False
                    break

            if do_append:
                sorted.append((num, object, value))

        sorted.sort()
        self[column] = [ (i[1], i[2]) for i in sorted ]


        if self.has_key("_save"):
            user.delConfigValueMatch(view_name, "%s_object_%%" % (column))
            user.delConfigValueMatch(view_name, "%s_value_%%" % (column))

            for num, obj, value in sorted:
                user.setConfigValue(view_name, "%s_object_%d" % (column, num), obj)
                user.setConfigValue(view_name, "%s_value_%d" % (column, num), value)

        return ret
    
    def normalize(self, view_name, user):
        MessageListingParameters.normalize(self, view_name, user)

        for severity in self["alert.assessment.impact.severity"]:
            if not severity in ("info", "low", "medium", "high", "none"):
                raise view.InvalidParameterValueError("alert.assessment.impact.severity", severity)
        
        for completion in self["alert.assessment.impact.completion"]:
            if not completion in ("succeeded", "failed", "none"):
                raise view.InvalidParameterValueError("alert.assessment.impact.completion", completion)

        for type in self["alert.assessment.impact.type"]:
            if not type in ("other", "admin", "dos", "file", "recon", "user"):
                raise view.InvalidParameterValueError("alert.assessment.impact.type", type)

        load_saved = True
        for column in "classification", "source", "target", "analyzer":
            ret = self._loadColumnParam(view_name, user, self, column)
            if ret:
                load_saved = False
        
        if load_saved and self.has_key("_load") and user.configuration.has_key(view_name):
            for column in "classification", "source", "target", "analyzer":
                self._loadColumnParam(view_name, user, user.configuration[view_name], column)
            
        for category in "classification", "source", "target":
            i = 0
            for path in self["aggregated_%s" % category]:
                
                if self["aggregated_%s" % category].count(path) > 1:
                    self["aggregated_%s" % category].remove(path)
                    
                if path[0] == "!":
                    self["aggregated_%s" % category][i] = path[1:]
                
                i += 1

class HeartbeatListingParameters(MessageListingParameters):
    def register(self):
        MessageListingParameters.register(self)
        self.optional("heartbeat.analyzer(-1).name", str)
        self.optional("heartbeat.analyzer(-1).node.address.address", str)
        self.optional("heartbeat.analyzer(-1).node.name", str)
        self.optional("heartbeat.analyzer(-1).model", str)



class SensorAlertListingParameters(AlertListingParameters):
    def register(self):
        AlertListingParameters.register(self)
        self.mandatory("analyzerid", long)

    def normalize(self, view_name, user):
        AlertListingParameters.normalize(self, view_name, user)
        self["analyzer"].insert(0, ("alert.analyzer.analyzerid", str(self["analyzerid"])))


class SensorHeartbeatListingParameters(HeartbeatListingParameters):
    def register(self):
        HeartbeatListingParameters.register(self)
        self.mandatory("analyzerid", long)



class ListedMessage(dict):
    def __init__(self, env, parameters):
        self.env = env
        self.parameters = parameters
        self.timezone = parameters["timezone"]

    def createInlineFilteredField(self, object, value, type=None):
        if not value:
            return { "value": None, "inline_filter": None }

        if type:
            index = self.parameters.max_index
            extra = { "%s_object_%d" % (type, index): object, "%s_value_%d" % (type, index): value }
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

    def createHostField(self, object, value, type=None):
        field = self.createInlineFilteredField(object, value, type)
        field["host_commands"] = [ ]
        for command in "whois", "traceroute":
            if self.env.host_commands.has_key(command):
                field["host_commands"].append((command.capitalize(),
                                               utils.create_link(command,
                                                                 { "origin": self.view_name, "host": value })))

        return field
    
    def createMessageLink(self, ident, view):
        return utils.create_link(view, { "origin": self.view_name, "ident": ident })



class ListedHeartbeat(ListedMessage):
    view_name = "heartbeat_listing"
    
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
            self["node_addresses"].append(
                self.createHostField("heartbeat.analyzer(-1).node.address.address", address["address"]))
            
        self["time"] = self.createTimeField(message["heartbeat.create_time"], self.parameters["timezone"])



class ListedSensorHeartbeat(ListedHeartbeat):
    view_name = "sensor_heartbeat_listing"



class ListedAlert(ListedMessage):
    view_name = "alert_listing"

    def _initValue(self, name, value):
        import copy
        
        self["source"][name] = value
        self["target"][name] = copy.copy(value)

    def reset(self):
        self["sensors"] = [ ]    
        self["correlation_alert_name"] = None
        self["source"] = { }
        self["target"] = { }
        self._initValue("interface", { "value": None })
        self._initValue("protocol", { "value": None })
        self._initValue("service", { "value": None })
        self._initValue("process", { "value": None })
        self._initValue("users", [ ])
        self._initValue("files", [ ])
        self._initValue("addresses", [ ])
        self._initValue("empty", True)
        
    def __init__(self, *args, **kwargs):        
        apply(ListedMessage.__init__, (self, ) + args, kwargs)
        self.reset()
        
    def _setMessageDirectionAddress(self, direction, address):
        self[direction]["empty"] = False
        self[direction]["addresses"].append(self.createHostField("alert.%s.node.address.address" % direction, address, type=direction))

    def _setMessageDirectionNodeName(self, direction, name):
        self[direction]["empty"] = False
        self[direction]["addresses"].append(self.createHostField("alert.%s.node.name" % direction, name, type=direction))

    def _setMessageDirectionGeneric(self, direction, object, value):
        self[direction]["empty"] = False            
        self[direction][object]["value"] = value

            
    def _setMessageDirection(self, dataset, direction, obj):        
        empty = dataset["empty"]
        
        def set_main_and_extra_values(dataset, name, object_main, object_extra):
            if object_main != None:
                dataset[name] = { "value": object_main }
                dataset[name + "_extra"] = { "value": object_extra }
            else:
                dataset[name] = { "value": object_extra }
                dataset[name + "_extra"] = { "value": None }

            if dataset[name]["value"] != None:
                empty = False
            
        dataset["interface"] = { "value": obj["interface"] }

        for userid in obj["user.user_id"]:
            user = { }
            empty = False
            dataset["users"].append(user)
            set_main_and_extra_values(user, "user", userid["name"], userid["number"])

        name = obj["node.name"]
        if name != None:
            self._setMessageDirectionNodeName(direction, name)
            
        for addr in obj["node.address"]:
            empty = False            
            self._setMessageDirectionAddress(direction, addr["address"])
                        
        set_main_and_extra_values(dataset, "process", obj["process.name"], obj["process.pid"])

        proto = None
        if obj["service.iana_protocol_name"]:
            proto = obj["service.iana_protocol_name"]
            
        elif obj["service.iana_protocol_number"]:
            num = obj["service.iana_protocol_number"]
            proto = utils.protocol_number_to_name(num)

        if not proto:
            proto = obj["service.protocol"]
       
        set_main_and_extra_values(dataset, "protocol", proto, None)
        set_main_and_extra_values(dataset, "service", obj["service.port"], None)

        dataset["files"] = []
        dataset["empty"] = empty

    def setMessageSource(self, message):
        self["source"]["empty"] = True
        for source in message["alert.source"]:
            self._setMessageDirection(self["source"], "source", source)

    def setMessageTarget(self, message):
        self["target"]["empty"] = True
        for target in message["alert.target"]:
            self._setMessageDirection(self["target"], "target", target)
            
        flist = []
        empty = self["target"]["empty"]
        
        for f in message["alert.target(0).file"]:
            if f["path"] in flist:
                continue

            empty = False
            flist.append(f["path"])
            self["target"]["files"].append(self.createInlineFilteredField("alert.target.file.path",
                                                                          f["path"], type="target"))

        self["target"]["empty"] = empty
        

    def setMessageClassificationReferences(self, dataset, message):
        urls = [ ]

        for ref in message["alert.classification.reference"]:
            fstr = ""

            url = ref["url"]
            if url:
                external_link_new_window = self.env.config.general.getOptionValue("external_link_new_window", "true")
                if (not external_link_new_window and self.env.config.general.has_key("external_link_new_window")) or \
                   (external_link_new_window == None or external_link_new_window.lower() in [ "true", "yes" ]):
                    target = "_blank"
                else:
                    target = "_self"
                    
                fstr="<a target='%s' href='%s'>" % (target, url)

            origin = ref["origin"]
            if origin:
                fstr += origin

            name = ref["name"]
            if name:
                fstr += ":" + name

            if url:
                fstr += "</a>"

            urls.append(fstr)

        if urls:
            dataset["classification_references"] = "(" + ", ".join(urls) + ")"
        else:
            dataset["classification_references"] = ""

    def setMessageClassification(self, dataset, message):
        self.setMessageClassificationReferences(dataset, message)
        dataset["classification"] = self.createInlineFilteredField("alert.classification.text",
                                                                   message["alert.classification.text"])

    def setMessageCorrelationAlertInfo(self, dataset, message, ident):
        fetch_source_info=True
        fetch_target_info=True
        fetch_classification_info=True
                
        if not message["alert.correlation_alert"]:
            return

        if message["alert.source"]:
            fetch_source_info = False

        if message["alert.target"]:
            fetch_target_info = False

        if message["alert.classification"]:
            fetch_classification_info = False

        i = 0
        ca_params = { }

        for alertident in message["alert.correlation_alert.alertident"]:
            # IDMEF draft 14 page 27
            # If the "analyzerid" is not provided, the alert is assumed to have come
            # from the same analyzer that is sending the CorrelationAlert.
            
            analyzerid = alertident["analyzerid"]
            if not analyzerid:
                analyzerid = message["alert.analyzer(-1).analyzerid"]
                
            ca_params["analyzer_object_%d" % i] = "alert.analyzer.analyzerid"
            ca_params["analyzer_value_%d" % i] = analyzerid
            
            ca_params["classification_object_%d" % i] = "alert.messageid"
            ca_params["classification_value_%d" % i] = alertident["alertident"]

            criteria = "alert.messageid = '%s' && alert.analyzer.analyzerid = '%s'" % (alertident["alertident"], analyzerid)
            result = self.env.idmef_db.getAlertIdents(criteria, 1, -1)
            if len(result) == 0:
                continue
            
            i += 1
            if i > 1:
                continue
            
            ca_idmef = self.env.idmef_db.getAlert(result[0])

            if fetch_classification_info:
                self.setMessageClassification(dataset, ca_idmef)
                
            if fetch_source_info:
                self.setMessageSource(ca_idmef)

            if fetch_target_info:
                self.setMessageTarget(ca_idmef)

        ca_params["timeline_unit"] = "unlimited"

        self["correlation_alert_name"] = message["alert.correlation_alert.name"]
        self["correlation_alert_link"] = self.createMessageLink(ident, "alert_summary")
        self["correlated_alert_number"] = i
                        
        tmp = self.parameters
        tmp -= [ "timeline_unit", "timeline_value", "offset",
                 "aggregated_classification", "aggregated_source",
                 "aggregated_target", "alert.assessment.impact.severity",
                 "alert.assessment.impact.completion", "_load", "_save" ]

        tmp["aggregated_target"] = \
        tmp["aggregated_source"] = \
        tmp["aggregated_classification"] = "none"
        
        self["correlated_alert_display"] = utils.create_link(self.view_name, tmp + ca_params)

    def setMessageInfo(self, message, ident):
        self["infos"] = [ { } ]

        dataset = self["infos"][0]
        dataset["count"] = 1
        dataset["display"] = self.createMessageLink(ident, "alert_summary")
        dataset["severity"] = { "value": message.get("alert.assessment.impact.severity") }
        dataset["completion"] = { "value": message["alert.assessment.impact.completion"] }

        self.setMessageClassification(dataset, message)
        self.setMessageCorrelationAlertInfo(dataset, message, ident)

    def addSensor(self, name, node_name):
        sensor = { }
        self["sensors"].append(sensor)
        sensor["name"] = self.createInlineFilteredField("alert.analyzer.name", name, type="analyzer")
        sensor["node_name"] = { "value": node_name }
        
    def setMessageTime(self, message):
        self["time"] = self.createTimeField(message["alert.create_time"], self.timezone)
	if (message["alert.analyzer_time"] != None and
	    abs(int(message["alert.create_time"]) - int(message["alert.analyzer_time"])) > 60):
	    self["analyzer_time"] = self.createTimeField(message["alert.analyzer_time"], self.timezone)
	else:
	    self["analyzer_time"] = { "value": None }

    def setMessageCommon(self, message):
        self["correlated_alert_display"] = None            
        self["correlation_alert_name"] = None
        
        self.setMessageSource(message)
        self.setMessageTarget(message)

    def setMessage(self, message, ident):
        self.setMessageCommon(message)
        self.addSensor(message["alert.analyzer(-1).name"], message["alert.analyzer(-1).node.name"])
        self.setMessageTime(message)
        self.setMessageInfo(message, ident)


class ListedSensorAlert(ListedAlert):
    view_name = "sensor_alert_listing"



class ListedAggregatedAlert(ListedAlert):
    def __init__(self, *args, **kwargs):
        apply(ListedAlert.__init__, (self,) + args, kwargs)
        self["aggregated"] = True
        self["aggregated_classification_hidden"] = 0
        self["infos"] = [ ]
        
    def setTime(self, time_min, time_max):
        self["time_min"] = self.createTimeField(time_min, self.parameters["timezone"])
        self["time_max"] = self.createTimeField(time_max, self.parameters["timezone"])

    def setCriteriaForDeletion(self, delete_criteria):
        self["delete"] = urllib.quote_plus(" && ".join(delete_criteria))

    def setInfos(self, count, classification, severity, completion):
        infos = {
            "classification_references": "",
            "count": count,
            "classification": self.createInlineFilteredField("alert.classification.text", classification),
            "severity": { "value": severity },
            "completion": { "value": completion }
            }

        self["infos"].append(infos)

        return infos



class ListedSensorAggregatedAlert(ListedAggregatedAlert):
    view_name = "sensor_alert_listing"



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
        for ident in self._getMessageIdents(criteria, self.parameters["limit"], self.parameters["offset"]):
            message = self._fetchMessage(ident)
            dataset = {
                "summary": self.createMessageLink(ident, self.summary_view),
                "details": self.createMessageLink(ident, self.details_view),
                "analyzerid": { "value": message.getAnalyzerID() },
                "ident": { "value": message.getMessageID() }
                }
            self._setMessage(dataset, message)
            self.dataset["messages"].append(dataset)

    def _deleteMessages(self):
        if len(self.parameters["delete"]) == 0:
            return
        
        if not self.user.has(User.PERM_IDMEF_ALTER):
            raise User.PermissionDeniedError(user.login, self.current_view)

        idents = [ ]
        for delete in self.parameters["delete"]:
            if delete.isdigit():
                idents += [ long(delete) ]
            else:
                criteria = urllib.unquote_plus(delete)
                idents += self._getMessageIdents(criteria)

        self._deleteMessage(idents)
        del self.parameters["delete"]



def cmp_severities(x, y):
    d = { None: 0, "info": 1, "low": 2, "medium": 3, "high": 4 }

    return d[y] - d[x]



class AlertListing(MessageListing, view.View):
    view_name = "alert_listing"
    view_parameters = AlertListingParameters
    view_permissions = [ User.PERM_IDMEF_VIEW ]
    view_template = "AlertListing"

    root = "alert"
    messageid_object = "alert.messageid"
    analyzerid_object = "alert.analyzer.analyzerid"
    summary_view = "alert_summary"
    details_view = "alert_details"
    listed_alert = ListedAlert
    listed_aggregated_alert = ListedAggregatedAlert

    def init(self, env):
        self._max_aggregated_classifications = int(env.config.general.getOptionValue("max_aggregated_classifications", 10))

    def _getMessageIdents(self, criteria, limit=-1, offset=-1):
        return self.env.idmef_db.getAlertIdents(criteria, limit, offset)

    def _countMessages(self, criteria):
        return self.env.idmef_db.countAlerts(criteria)

    def _fetchMessage(self, ident):
        return self.env.idmef_db.getAlert(ident)

    def _setMessage(self, message, ident):
        msg = self.listed_alert(self.env, self.parameters)
        msg.setMessage(message, ident)
        msg["aggregated"] = False
        msg["delete"] = ident
        
        return msg
    
    def _getFilters(self, storage, login):
        return storage.getAlertFilters(login)

    def _getFilter(self, storage, login, name):
        return storage.getAlertFilter(login, name)

    def _deleteMessage(self, ident):
        self.env.idmef_db.deleteAlert(ident)

    def _applyOptionalEnumFilter(self, criteria, column, object, values):
            
        def lists_have_same_content(l1, l2):
            l1 = copy.copy(l1)
            l2 = copy.copy(l2)
            l1.sort()
            l2.sort()

            return l1 == l2
        
        if ( len(self.parameters[object]) != 0 and
             not lists_have_same_content(self.parameters[object], values)):

            new = [ ]
            for value in self.parameters[object]:
                if value == "none":
                    new.append("! %s" % object)
                else:
                    new.append("%s == '%s'" % (object, utils.escape_criteria(value)))

            criteria.append("(" + " || ".join(new) + ")")
            self.dataset[object] = self.parameters[object]
            self.dataset[column + "_filtered"] = True
        else:
            self.dataset[object] = values

    def _applyClassificationFilters(self, criteria):
        self._applyOptionalEnumFilter(criteria, "classification", "alert.assessment.impact.severity",
                                      ["info", "low", "medium", "high", "none"])
        self._applyOptionalEnumFilter(criteria, "classification", "alert.assessment.impact.completion",
                                      ["failed", "succeeded", "none"])
        self._applyOptionalEnumFilter(criteria, "classification", "alert.assessment.impact.type",  
                                      ["other", "admin", "dos", "file", "recon", "user"])  

    def _applyCheckboxFilters(self, criteria, type):
            
        def get_operator(object):
            if object in ("alert.source.service.port", "alert.target.service.port", "alert.messageid", "alert.analyzerid"):
                return "="

            return "<>*"
        
        if self.parameters[type]:

            # If one object is specified more than one time, and since this object
            # can not have two different value, we want to apply an OR operator.
            #
            # We apply an AND operator between the different objects.
            
            merge = { }
            for obj in self.parameters[type]:
                if merge.has_key(obj[0]):
                    merge[obj[0]] += [ obj ]
                else:
                    merge[obj[0]] =  [ obj ]

            newcrit = ""
            for key in iter(merge):
                if len(newcrit) > 0:
                    newcrit += " && "

                newcrit += "(" + " || ".join(map(lambda (object, value): "%s %s '%s'" %
                                                 (object, get_operator(object), utils.escape_criteria(value)),
                                                 merge[key])) + ")"

            if newcrit:
                criteria.append(newcrit)

            self.dataset[type] = self.parameters[type]
            self.dataset["%s_filtered" % type] = True
        else:
            self.dataset[type] = [ ("", "") ]
            self.dataset["%s_filtered" % type] = False
        
    def _applyFilters(self, criteria):
        self._applyCheckboxFilters(criteria, "classification")
        self._applyClassificationFilters(criteria)
        
        self._applyCheckboxFilters(criteria, "source")
        self._applyCheckboxFilters(criteria, "target")
        self._applyCheckboxFilters(criteria, "analyzer")

    def _ignoreAtomicIfNeeded(self, idmef, ignore_list):

        for ad in idmef["alert.additional_data"]:
            if ad["data"] != "ignore_atomic_event":
                continue
            
            for ca in idmef["alert.correlation_alert.alertident"]:
                # See FIXME ahead.
                # ignore_list.append((ca["analyzerid"] or idmef["alert.analyzer(-1).analyzerid"], ca["alertident"]))
                ignore_list.append(ca["alertident"])
                
            break

    def _isAtomicEventIgnored(self, idmef, atomic_ignore_list):
        #
        # FIXME: LML really need to set analyzerid at the tail.
        # if ( idmef["alert.analyzer(-1).analyzerid"], idmef["alert.messageid"]) in atomic_ignore_list:            
        if idmef["alert.messageid"] in atomic_ignore_list:
            return True
        else:                
            return False
                
    def _setAggregatedMessagesNoValues(self, criteria, aggregated_on):
        filter_on = []
        filter_values = []
        atomic_ignore_list = []

        for column in "source", "target", "classification":
            if len(self.parameters[column]):
                for item in self.parameters[column]:
                      filter_on.append(item[0])
                      filter_values.append(item[1])

        selection = [ "alert.messageid", "alert.create_time" ]
        results2 = self.env.idmef_db.getValues(selection, criteria + ["alert.correlation_alert.name"])

        results = []
        for row in results2:
            ca_ident = self.env.idmef_db.getAlertIdents(criteria + [ "alert.messageid = %s" % row[0] ], 1, -1)[0]
            message = self.env.idmef_db.getAlert(ca_ident)
            self._ignoreAtomicIfNeeded(message, atomic_ignore_list)
            results += [ [ row[0] ] + [None for i in aggregated_on] + [ca_ident] + [message] + [ row[1] ] ]
            
        ignore_criteria = [ ]
        for messageid in atomic_ignore_list:
            ignore_criteria += [ "alert.messageid != '%s'" % messageid ]
            
        ##
        selection = [ "%s/group_by" % path for path in aggregated_on ] + \
                    [ "count(alert.create_time)", "max(alert.create_time)/order_desc" ]

        results += self.env.idmef_db.getValues(selection, criteria + [ "! alert.correlation_alert.name"] + ignore_criteria)
        results.sort(lambda x, y: int(int(y[-1]) - int(x[-1])))
        total_results = len(results)
            
        for values in results[self.parameters["offset"]:self.parameters["offset"]+self.parameters["limit"]]:
            start = 0
            aggregated_source_values = []
            aggregated_target_values = []
            aggregated_classification_values = []
            
            if self.parameters["aggregated_source"] != ["none"]:
                start = len(self.parameters["aggregated_source"])
                aggregated_source_values = values[:len(self.parameters["aggregated_source"])]

            if self.parameters["aggregated_target"] != ["none"]:
                last = start + len(self.parameters["aggregated_target"])
                aggregated_target_values = values[start:last]
                start = last

            if self.parameters["aggregated_classification"] != ["none"]:
                last = start + len(self.parameters["aggregated_classification"])
                if values[start:last]:
                    aggregated_classification_values = values[start:last]
                start = last

            aggregated_count = values[start]
            if aggregated_count == None:
                message = values[-2]
                dataset = self._setMessage(message, values[-3])
                self.dataset["messages"].append(dataset)
                continue
            
            criteria2 = criteria[:]
            delete_criteria = [ ]
            message = self.listed_aggregated_alert(self.env, self.parameters)

                
            for path, value in zip(aggregated_on, values[:start]):
                if path.find("source") != -1:
                    direction = "source"
                else:
                    direction = "target"

                if not value:
                    if idmef_path_get_value_type(idmef_path_new(path), -1) != IDMEF_VALUE_TYPE_STRING:
                        criterion = "! %s" % (path)
                    else:
                        criterion = "(! %s || %s == '')" % (path, path)
                        

                else:
                    criterion = "%s == '%s'" % (path, utils.escape_criteria(str(value)))
                    
                    if path.find("address") != -1 or path.find("node.name") != -1:
                        message._setMessageDirectionAddress(direction, value)
                    
                    for var in [ ("user", None), ("process", None), ("service", None), ("port", "service") ]:
                        if path.find(var[0]) != -1:
                            message._setMessageDirectionGeneric(direction, var[1] or var[0], value)
               
                criteria2.append(criterion)
                delete_criteria.append(criterion)
            
            time_min = self.env.idmef_db.getValues(["alert.create_time/order_asc"], criteria2, limit=1)[0][0]
            time_max = self.env.idmef_db.getValues(["alert.create_time/order_desc"], criteria2, limit=1)[0][0]
            
            delete_criteria.append("alert.create_time >= '%s'" % time_min.toYMDHMS())
            delete_criteria.append("alert.create_time <= '%s'" % time_max.toYMDHMS())

            ident = self.env.idmef_db.getAlertIdents(criteria2 + ignore_criteria, limit=1)[0]
            
            self.dataset["messages"].append(message)
            message.setTime(time_min, time_max)
            message.setCriteriaForDeletion(delete_criteria)

            res = self.env.idmef_db.getValues(["alert.analyzer(-1).name/group_by",
                                               "alert.analyzer(-1).node.name/group_by"],
                                              criteria2)

            for analyzer_name, analyzer_node_name in res:
                message.addSensor(analyzer_name, analyzer_node_name)

            res = self.env.idmef_db.getValues(["alert.classification.text/group_by",
                                               "alert.assessment.impact.severity/group_by",
                                               "alert.assessment.impact.completion/group_by",
                                               "count(alert.create_time)"], criteria2 + ignore_criteria)
                
            res.sort(lambda x, y: cmp_severities(x[1], y[1]))

            parameters = self._createAggregationParameters(aggregated_classification_values,
                                                           aggregated_source_values, aggregated_target_values)

            message["aggregated_classifications_total"] = aggregated_count
            message["aggregated_classifications_hidden"] = aggregated_count
            message["aggregated_classifications_hidden_expand"] = utils.create_link(self.view_name,
                                                                                    self.parameters -
                                                                                    [ "offset",
                                                                                      "aggregated_source",
                                                                                      "aggregated_target" ]
                                                                                    + parameters +
                                                                                    { "aggregated_classification":
                                                                                      "alert.classification.text" } )

            if len(res[:self._max_aggregated_classifications]) > 1:
                classification = None
            else:
                classification = res[0][0] or ""

            result_count = 0

            for classification, severity, completion, count in res:
                if result_count >= self._max_aggregated_classifications:
                    result_count += 1
                    continue
                result_count += 1

                message["aggregated_classifications_hidden"] -= count
                infos = message.setInfos(count, classification, severity, completion)
                    
                if count == 1:
                    if aggregated_count == 1:                            
                        message.reset()
                        message.setMessage(self._fetchMessage(ident), ident)
                                                    
                    criteria3 = criteria2[:]

                    for path, value, is_string in (("alert.classification.text", classification, True),
                                                       ("alert.assessment.impact.severity", severity, False),
                                                       ("alert.assessment.impact.completion", completion, False)):
                        if value:
                            criteria3.append("%s == '%s'" % (path, utils.escape_criteria(value)))
                        else:
                            if is_string:
                                criteria3.append("(! %s || %s == '')" % (path, path))
                            else:
                                criteria3.append("! %s" % path)

                    ident = self.env.idmef_db.getAlertIdents(criteria3, limit=1)[0]
                    infos["display"] = message.createMessageLink(ident, "alert_summary")
                else:
                    entry_param = {}
                        
                    if classification:
                        entry_param["classification_object_%d" % self.parameters.max_index] = "alert.classification.text"
                        entry_param["classification_value_%d" % self.parameters.max_index] = utils.escape_criteria(classification)

                    if severity:
                        entry_param["alert.assessment.impact.severity"] = severity

                    if completion:
                        entry_param["alert.assessment.impact.completion"] = completion

                    entry_param["aggregated_target"] = \
                    entry_param["aggregated_source"] = \
                    entry_param["aggregated_classification"] = "none"
                        
                    infos["display"] = utils.create_link(self.view_name, self.parameters -
                                                         [ "offset", "aggregated_classification",
                                                           "aggregated_source", "aggregated_target", "_load", "_save" ] +
                                                         parameters + entry_param)
                        
        return total_results
    

    def _createAggregationParameters(self, aggregated_classification_values, aggregated_source_values, aggregated_target_values):
        parameters = { }
                
        i = self.parameters.max_index
        for path, value in zip(self.parameters["aggregated_classification"], aggregated_classification_values):
            if value == None:
                continue
            
            parameters["classification_object_%d" % i] = path.replace("(0)", "")
            parameters["classification_value_%d" % i] = value
            i += 1
            
        i = self.parameters.max_index
        for path, value in zip(self.parameters["aggregated_source"], aggregated_source_values):
            if value == None:
                continue
            
            parameters["source_object_%d" % i] = path.replace("(0)", "")
            parameters["source_value_%d" % i] = value
            i += 1
        
        i = self.parameters.max_index
        for path, value in zip(self.parameters["aggregated_target"], aggregated_target_values):
            if value == None:
                continue
            
            parameters["target_object_%d" % i] = path.replace("(0)", "")
            parameters["target_value_%d" % i] = value
            i += 1
            
        return parameters
    
    def _setMessages(self, criteria):
        self.dataset["messages"] = [ ]

        self.dataset["aggregated_source"] = self.parameters["aggregated_source"]
        self.dataset["aggregated_target"] = self.parameters["aggregated_target"]
        self.dataset["aggregated_classification"] = self.parameters["aggregated_classification"]

        aggregated_on = []
        if self.parameters["aggregated_source"] != ["none"]:
            aggregated_on += self.parameters["aggregated_source"]

        if self.parameters["aggregated_target"] != ["none"]:
            aggregated_on += self.parameters["aggregated_target"]

        if self.parameters["aggregated_classification"] != ["none"]:
            aggregated_on += self.parameters["aggregated_classification"]

        if len(aggregated_on) > 0:
            return self._setAggregatedMessagesNoValues(criteria, aggregated_on)

        atomic_ignore_list = []
        for ident in self.env.idmef_db.getAlertIdents(criteria, self.parameters["limit"], self.parameters["offset"]):
            message = self.env.idmef_db.getAlert(ident)

            if self._isAtomicEventIgnored(message, atomic_ignore_list):
                continue
            
            self._ignoreAtomicIfNeeded(message, atomic_ignore_list)

            dataset = self._setMessage(message, ident)
            self.dataset["messages"].append(dataset)

        return self.env.idmef_db.countAlerts(criteria)
            
    def _setDatasetConstants(self):
        self.dataset["available_aggregations"] = { }
        self.dataset["available_aggregations"]["classification"] = ( ("", "none"),
                                                                     ("text", "alert.classification.text"))
        
        for category in "source", "target":
            tmp = (("", "none"),
                   ("address", "alert.%s(0).node.address(0).address" % category),
                   ("name", "alert.%s(0).node.name" % category),
                   ("user", "alert.%s(0).user.user_id(0).name" % category),
                   ("process", "alert.%s(0).process.name" % category),
                   ("service", "alert.%s(0).service.name" % category),
                   ("port", "alert.%s(0).service.port" % category),
                   ("interface", "alert.%s(0).interface" % category))
            self.dataset["available_aggregations"][category] = tmp
            
    def render(self):
        self._deleteMessages()
        self._setDatasetConstants()
        
        self.dataset["filters"] = self.env.db.getAlertFilterNames(self.user.login)
        self.dataset["current_filter"] = self.parameters.get("filter", "")
        
        criteria = [ ]
        
        if self.parameters.has_key("filter"):
            filter = self.env.db.getAlertFilter(self.user.login, self.parameters["filter"])
            criteria.append("(%s)" % str(filter))

        start = end = None
        if self.parameters.has_key("timeline_unit") and self.parameters["timeline_unit"] != "unlimited":
            start, end = self._getTimelineRange()
            criteria.append("alert.create_time >= '%s' && alert.create_time < '%s'" % (str(start), str(end)))
        
        self._applyFilters(criteria)
        self._adjustCriteria(criteria)

        self._setTimeline(start, end)
        self._setNavPrev(self.parameters["offset"])

        self._setHiddenParameters()

        self.dataset["messages"] = [ ]
        total = self._setMessages(criteria)

        self.dataset["nav.from"] = self.parameters["offset"] + 1
        self.dataset["nav.to"] = self.parameters["offset"] + len(self.dataset["messages"])
        self.dataset["limit"] = self.parameters["limit"]
        self.dataset["total"] = total

        self._setNavNext(self.parameters["offset"], total)
        self._setTimezone()



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

    def _getMessageIdents(self, criteria, limit=-1, offset=-1):
        return self.env.idmef_db.getHeartbeatIdents(criteria, limit, offset)

    def _countMessages(self, criteria):
        return self.env.idmef_db.countHeartbeats(criteria)

    def _fetchMessage(self, ident):
        return self.env.idmef_db.getHeartbeat(ident)

    def _setMessages(self, criteria):
        self.dataset["messages"] = [ ]
        
        for ident in self.env.idmef_db.getHeartbeatIdents(criteria, self.parameters["limit"], self.parameters["offset"]):
            message = self.env.idmef_db.getHeartbeat(ident)
            dataset = self._setMessage(message, ident)
            self.dataset["messages"].append(dataset)

    def _setMessage(self, message, ident):
        msg = self.listed_heartbeat(self.env, self.parameters)
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

        count = self.env.idmef_db.countHeartbeats(criteria and " && ".join(criteria) or None)

        self._setMessages(criteria)

        self._setHiddenParameters()
        
        self.dataset["nav.from"] = self.parameters["offset"] + 1
        self.dataset["nav.to"] = self.parameters["offset"] + len(self.dataset["messages"])
        self.dataset["limit"] = self.parameters["limit"]
        self.dataset["total"] = count

        self._setNavNext(self.parameters["offset"], count)
        self._setTimezone()



class SensorAlertListing(AlertListing, view.View):
    view_name = "sensor_alert_listing"
    view_parameters = SensorAlertListingParameters
    view_permissions = [ User.PERM_IDMEF_VIEW ]
    view_template = "SensorAlertListing"

    listed_alert = ListedSensorAlert
    listed_aggregated_alert = ListedSensorAggregatedAlert

    def _setHiddenParameters(self):
        AlertListing._setHiddenParameters(self)
        self.dataset["hidden_parameters"].append(("analyzerid", self.parameters["analyzerid"]))

    def render(self):
        AlertListing.render(self)
        self.dataset["analyzer_infos"] = self.env.idmef_db.getAnalyzer(self.parameters["analyzerid"])



class SensorHeartbeatListing(HeartbeatListing, view.View):
    view_name = "sensor_heartbeat_listing"
    view_parameters = SensorHeartbeatListingParameters
    view_permissions = [ User.PERM_IDMEF_VIEW ]
    view_template = "SensorHeartbeatListing"

    listed_heartbeat = ListedSensorHeartbeat

    def _adjustCriteria(self, criteria):
        criteria.append("heartbeat.analyzer.analyzerid == %d" % self.parameters["analyzerid"])

    def _setHiddenParameters(self):
        HeartbeatListing._setHiddenParameters(self)
        self.dataset["hidden_parameters"].append(("analyzerid", self.parameters["analyzerid"]))

    def render(self):
        HeartbeatListing.render(self)
        self.dataset["analyzer"] = self.env.idmef_db.getAnalyzer(self.parameters["analyzerid"])
