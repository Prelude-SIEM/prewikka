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
        t = time.mktime(t)
        return _MyTime(t)

    def __sub__(self, value):
        return self + (-value)

    def __str__(self):
        return utils.time_to_ymdhms(time.localtime(self._t))
    
    def __int__(self):
        return int(self._t)



class MessageListingParameters(view.Parameters):
    def register(self):
        self.optional("timeline_value", int, default=1)
        self.optional("timeline_unit", str, default="hour")
        self.optional("timeline_end", int)
        self.optional("timeline_start", int)
        self.optional("offset", int, default=0)
        self.optional("limit", int, default=50)
        self.optional("timezone", str, "frontend_localtime")
        self.optional("delete", list, [ ])
        # submit with an image passes the x and y coordinate values
        # where the image was clicked
        self.optional("x", int)
        self.optional("y", int)
        
    def normalize(self):
        view.Parameters.normalize(self)
        
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
        self.optional("aggregated_source", list, [ ])
        self.optional("aggregated_source_values", list, [ ])
        self.optional("aggregated_target", list, [ ])
        self.optional("aggregated_target_values", list, [ ])
        self.optional("aggregated_classification", list, [ ])
        self.optional("aggregated_severity_value", str)
        self.optional("aggregated_classification_value", str)
        self.optional("filter", str)
        self.optional("alert.classification.text", list, [ ])
        self.optional("alert.assessment.impact.severity", list, [ ])
        self.optional("alert.assessment.impact.completion", list, [ ])
        self.optional("alert.assessment.impact.type", list, [ ])
        
    def normalize(self):
        #
        # Default to aggregated view
        if len(self) == 0:
            self["aggregated_source"] =[ "alert.source(0).node.address(0).address" ]
            self["aggregated_target"] = [ "alert.target(0).node.address(0).address" ]
            
        MessageListingParameters.normalize(self)

        for severity in self["alert.assessment.impact.severity"]:
            if not severity in ("info", "low", "medium", "high", "none"):
                raise view.InvalidParameterValueError("alert.assessment.impact.severity", severity)
        
        for completion in self["alert.assessment.impact.completion"]:
            if not completion in ("succeeded", "failed", "none"):
                raise view.InvalidParameterValueError("alert.assessment.impact.completion", completion)

        for type in self["alert.assessment.impact.type"]:
            if not type in ("other", "admin", "dos", "file", "recon", "user"):
                raise view.InvalidParameterValueError("alert.assessment.impact.type", type)
        
        for column in "classification", "source", "target", "analyzer":
            sorted = [ ]
            for parameter, object in self.items():
                idx = parameter.find(column + "_object_")
                if idx == -1:
                    continue
                
                num = int(parameter.replace(column + "_object_", "", 1))
                if num >= self.max_index:
                    self.max_index = num + 1

                try:
                    value = self["%s_value_%s" % (column, num)]
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
                                         
            
        for category in "classification", "source", "target":
            i = 0
            for path in self["aggregated_%s" % category]:
                if path == "none":
                    del self["aggregated_%s" % category][i]

                if path[0] == "!":
                    self["aggregated_%s" % category][i] = path[1:]
                    self["aggregated_%s_values" % category].insert(i, None)
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

        return { "value": value, "inline_filter": utils.create_link(self.view_name, self.parameters + extra) }

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

    def __init__(self, *args, **kwargs):
        apply(ListedMessage.__init__, (self, ) + args, kwargs)
        self["sensors"] = [ ]    
    
    def _setMessageDirection(self, dataset, message, direction):
        empty = True
        
        def set_main_and_extra_values(dataset, message, name, object_main, object_extra):
            if message[object_main] != None:
                dataset[name] = { "value": message[object_main] }
                dataset[name + "_extra"] = { "value": message[object_extra] }
            else:
                dataset[name] = { "value": message[object_extra] }
                dataset[name + "_extra"] = { "value": None }

            if dataset[name]["value"] != None:
                empty = False
            
        dataset["interface"] = { "value": message["alert.%s(0).interface" % direction] }

        dataset["users"] = [ ]
        for userid in message["alert.%s(0).user.user_id" % direction]:
            user = { }
            empty = False
            dataset["users"].append(user)
            set_main_and_extra_values(user, userid, "user", "name", "number")

        
        dataset["addresses"] = [ ]
        name = message["alert.%s(0).node.name" % direction]
        if name != None:
            empty = False
            dataset["addresses"].append(
                self.createHostField("alert.%s(0).node.name" % direction, name, type=direction))
        
        for addr in message["alert.%s(0).node.address" % direction]:
            empty = False
            dataset["addresses"].append(
                self.createHostField("alert.%s(0).node.address.address" % direction, addr["address"], type=direction))
            
        set_main_and_extra_values(dataset, message, "process",
                                  "alert.%s(0).process.name" % direction,
                                  "alert.%s(0).process.pid" % direction)

        set_main_and_extra_values(dataset, message, "service",
                                  "alert.%s(0).service.port" % direction,
                                  "alert.%s(0).service.protocol" % direction)

        dataset["files"] = []
        dataset["empty"] = empty

    def setMessageSource(self, message):
        self["source"] = { }
        self._setMessageDirection(self["source"], message, "source")

    def setMessageTarget(self, message):
        self["target"] = { }
        self._setMessageDirection(self["target"], message, "target")

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
                fstr="<a href='%s'>" % url

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
    def setMessageInfo(self, message, ident):
        self["infos"] = [ { } ]
        dataset = self["infos"][0]

        dataset["count"] = 1
        dataset["display"] = self.createMessageLink(ident, "alert_summary")
        dataset["severity"] = { "value": message.get("alert.assessment.impact.severity", "low") }
        dataset["completion"] = { "value": message["alert.assessment.impact.completion"] }
        self.setMessageClassification(dataset, message)

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
        
    def _setInlineFilter(self):
        if self.parameters.has_key("inline_filter_object"):
            self.dataset["active_inline_filter"] = self.inline_filters[self.parameters["inline_filter_object"]]
        else:
            self.dataset["active_inline_filter"] = ""
        self.dataset["remove_active_inline_filter"] = utils.create_link(self.view_name,
                                                                        self.parameters - \
                                                                        [ "inline_filter_object",
                                                                          "inline_filter_value",
                                                                          "offset"])

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
        for unit in "min", "hour", "day", "month", "year":
            self.dataset["timeline.%s_selected" % unit] = ""
        
        self.dataset["timeline.current"] = utils.create_link(self.view_name, self.parameters - ["timeline_end"])

        self.dataset["timeline.value"] = self.parameters["timeline_value"]
        self.dataset["timeline.%s_selected" % self.parameters["timeline_unit"]] = "selected='selected'"

        if self.parameters["timezone"] == "utc":
            self.dataset["timeline.start"] = utils.time_to_ymdhms(time.gmtime(int(start)))
            self.dataset["timeline.end"] = utils.time_to_ymdhms(time.gmtime(int(end)))
            self.dataset["timeline.range_timezone"] = "UTC"
        else:
            self.dataset["timeline.start"] = utils.time_to_ymdhms(time.localtime(int(start)))
            self.dataset["timeline.end"] = utils.time_to_ymdhms(time.localtime(int(end)))
            self.dataset["timeline.range_timezone"] = "%+.2d:%.2d" % utils.get_gmt_offset()

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

        for delete in self.parameters["delete"]:
            if delete.isdigit():
                idents = [ delete ]
            else:
                criteria = urllib.unquote_plus(delete)
                idents = self._getMessageIdents(criteria)

            for ident in idents:
                self._deleteMessage(long(ident))
        
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
            if object in ("alert.source.service.port", "alert.target.service.port"):
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

    def _setAggregatedMessagesNoValues(self, criteria):
        filter_on = []
        filter_values = []

        for column in "source", "target", "classification":
            if len(self.parameters[column]):
                for item in self.parameters[column]:
                      filter_on.append(item[0])
                      filter_values.append(item[1])
                    
        aggregated_on = self.parameters["aggregated_source"] + \
                        self.parameters["aggregated_target"] + \
                        self.parameters["aggregated_classification"]

        selection = [ "%s/group_by" % path for path in aggregated_on ] + \
                    [ "count(alert.create_time)", "max(alert.create_time)/order_desc" ]
        
        results = self.env.idmef_db.getValues(selection, criteria)
        total_results = len(results)
            
        for values in results[self.parameters["offset"]:self.parameters["offset"]+self.parameters["limit"]]:
            start = 0
            aggregated_source_values = []
            aggregated_target_values = []
            aggregated_classification_values = []
            
            if len(self.parameters["aggregated_source"]):
                start = len(self.parameters["aggregated_source"])
                aggregated_source_values = values[:len(self.parameters["aggregated_source"])]

            if len(self.parameters["aggregated_target"]):
                last = start + len(self.parameters["aggregated_target"])
                aggregated_target_values = values[start:last]
                start = last

            if len(self.parameters["aggregated_classification"]):
                last = start + len(self.parameters["aggregated_classification"])
                if values[start:last]:
                    aggregated_classification_values = values[start:last]
                start = last

            aggregated_count = values[start]

            criteria2 = criteria[:]
            delete_criteria = [ ]
            source_address = None
            target_address = None
            classification = None
            
            for path, value in zip(filter_on, filter_values):
                if path == "alert.classification.text":
                    classification = value
                    
                if path == "alert.source.node.address.address":
                    source_address = value

                if path == "alert.target.node.address.address":
                    target_address = value
                    
            for path, value in zip(aggregated_on, values[:start]):
                if path == "alert.classification.text":
                    classification = value
                    
                if path == "alert.source(0).node.address(0).address":
                    source_address = value

                if path == "alert.target(0).node.address(0).address":
                    target_address = value

                if value:
                    criterion = "%s == '%s'" % (path, utils.escape_criteria(value))
                else:
                    criterion = "(! %s || %s == '')" % (path, path)

                criteria2.append(criterion)
                delete_criteria.append(criterion)
            
            time_min = self.env.idmef_db.getValues(["alert.create_time/order_asc"], criteria2, limit=1)[0][0]
            time_max = self.env.idmef_db.getValues(["alert.create_time/order_desc"], criteria2, limit=1)[0][0]
            
            delete_criteria.append("alert.create_time >= '%s'" % time_min.toYMDHMS())
            delete_criteria.append("alert.create_time <= '%s'" % time_max.toYMDHMS())

            for ident in self.env.idmef_db.getAlertIdents(criteria2, limit=1):
                idmef = self._fetchMessage(ident)
                message = self.listed_aggregated_alert(self.env, self.parameters)
                self.dataset["messages"].append(message)
                message.setTime(time_min, time_max)
                message.setMessageCommon(idmef)
                message.setCriteriaForDeletion(delete_criteria)

                results = self.env.idmef_db.getValues(["alert.analyzer(-1).name/group_by",
                                                       "alert.analyzer(-1).node.name/group_by"],
                                                      criteria2)

                for analyzer_name, analyzer_node_name in results:
                    message.addSensor(analyzer_name, analyzer_node_name)

                results = self.env.idmef_db.getValues(["alert.classification.text/group_by",
                                                       "alert.assessment.impact.severity/group_by",
                                                       "alert.assessment.impact.completion/group_by",
                                                       "count(alert.create_time)"], criteria2)
                results.sort(lambda x, y: cmp_severities(x[1], y[1]))
                                
                parameters = self._createAggregationParameters(aggregated_classification_values,
                                                               aggregated_source_values, aggregated_target_values)

                message["aggregated_classifications_total"] = aggregated_count
                message["aggregated_classifications_hidden"] = aggregated_count
                message["aggregated_classifications_hidden_expand"] = utils.create_link("alert_listing",
                                                                                        self.parameters -
                                                                                        [ "offset",
                                                                                          "aggregated_source",
                                                                                          "aggregated_target" ]
                                                                                        + parameters +
                                                                                        { "aggregated_classification":
                                                                                          "alert.classification.text" } )

                if len(results[:self._max_aggregated_classifications]) > 1:
                    classification = None
                else:
                    classification = results[0][0] or ""

                result_count = 0

                for classification, severity, completion, count in results:
                    if result_count >= self._max_aggregated_classifications:
                        result_count += 1
                        continue
                    result_count += 1
                    
                    message["aggregated_classifications_hidden"] -= count
                    infos = message.setInfos(count, classification, severity, completion)
                    
                    if count == 1:
                        if aggregated_count == 1:
                            message.setMessageClassificationReferences(infos, idmef)
                        
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
                            entry_param["classification_object_0"] = "alert.classification.text"
                            entry_param["classification_value_0"] = classification

                        if severity:
                            entry_param["alert.assessment.impact.severity"] = severity

                        if completion:
                            entry_param["alert.assessment.impact.completion"] = completion
             
                        infos["display"] = utils.create_link("alert_listing",
                                                             self.parameters - [ "offset",
                                                                                 "aggregated_classification",
                                                                                 "aggregated_source", "aggregated_target" ] +
                                                             parameters + entry_param)
                

        return total_results
    

    def _createAggregationParameters(self, aggregated_classification_values, aggregated_source_values, aggregated_target_values):
        parameters = { }
                
        i = 0
        for value in aggregated_classification_values:
            if value == None:
                continue
            
            parameters["classification_object_%d" % i] = "alert.classification.text"
            parameters["classification_value_%d" % i] = value
            i += 1
            
        i = 0
        for value in aggregated_source_values:
            if value == None:
                continue
            
            parameters["source_object_%d" % i] = "alert.source.node.address.address"
            parameters["source_value_%d" % i] = value
            i += 1
        
        i = 0
        for value in aggregated_target_values:
            if value == None:
                continue
            
            parameters["target_object_%d" % i] = "alert.target.node.address.address"
            parameters["target_value_%d" % i] = value
            i += 1
            
        return parameters
    
    def _setMessages(self, criteria):
        self.dataset["messages"] = [ ]

        self.dataset["aggregated_source"] = self.parameters["aggregated_source"] or [ "none" ]
        self.dataset["aggregated_source_values"] = self.parameters["aggregated_source_values"]
        self.dataset["aggregated_target"] = self.parameters["aggregated_target"] or [ "none" ]
        self.dataset["aggregated_target_values"] = self.parameters["aggregated_target_values"]
        self.dataset["aggregated_classification"] = self.parameters["aggregated_classification"] or [ "none"]

        if self.parameters["aggregated_source"] + \
           self.parameters["aggregated_target"] + \
           self.parameters["aggregated_classification"]:
            return self._setAggregatedMessagesNoValues(criteria)
        
        for ident in self.env.idmef_db.getAlertIdents(criteria, self.parameters["limit"], self.parameters["offset"]):
            message = self.env.idmef_db.getAlert(ident)
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
                   ("name", "alert.%s(0).node.name" % category),
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

        self._applyFilters(criteria)
        
        start, end = self._getTimelineRange()
        
        criteria.append("alert.create_time >= '%s' && alert.create_time < '%s'" % (str(start), str(end)))

        self._adjustCriteria(criteria)

        self._setInlineFilter()
        self._setTimeline(start, end)
        self._setNavPrev(self.parameters["offset"])

        self._setHiddenParameters()

        self.dataset["messages"] = [ ]
        total = self._setMessages(criteria)

        if self.parameters.has_key("timeline_start"):
            self.dataset["hidden_parameters"].append(("timeline_start", self.parameters["timeline_start"]))
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

        start, end = self._getTimelineRange()
        
        criteria = [ "heartbeat.create_time >= '%s' && heartbeat.create_time < '%s'" % (str(start), str(end)) ]
        self._applyInlineFilters(criteria)
        self._adjustCriteria(criteria)

        self._setInlineFilter()
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

    def _adjustCriteria(self, criteria):
        criteria.append("alert.analyzer.analyzerid == %d" % self.parameters["analyzerid"])

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
