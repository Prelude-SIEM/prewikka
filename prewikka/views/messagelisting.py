# Copyright (C) 2004,2005 Nicolas Delon <nicolas@prelude-ids.org>
# All Rights Reserved
#
# This file is part of the Prelude program.
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


import time
import copy

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
        self.optional("offset", int, default=0)
        self.optional("limit", int, default=50)
        self.optional("timezone", str, "frontend_localtime")
        self.optional("idents", list, [])
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
        
        idents = [ ]
        for ident in self["idents"]:
            try:
                analyzerid, message_ident = map(lambda x: long(x), ident.split(":"))
            except ValueError:
                raise view.InvalidParameterValueError("idents", self["idents"])
            
            idents.append((analyzerid, message_ident))

        self["idents"] = idents

        # remove the bulshit
        try:
            del self["x"]
            del self["y"]
        except KeyError:
            pass



class AlertListingParameters(MessageListingParameters):
    allow_extra_parameters = True

    def register(self):
        MessageListingParameters.register(self)
        self.optional("filter", str)
        self.optional("alert.classification.text", list, [ ])
        self.optional("alert.assessment.impact.severity", list, [ ])
        self.optional("alert.assessment.impact.completion", list, [ ])
        

    def normalize(self):
        MessageListingParameters.normalize(self)
        
        for severity in self["alert.assessment.impact.severity"]:
            if not severity in ("info", "low", "medium", "high", "none"):
                raise view.InvalidParameterValueError("alert.assessment.impact.severity", severity)
        
        for completion in self["alert.assessment.impact.completion"]:
            if not completion in ("succeeded", "failed", "none"):
                raise view.InvalidParameterValueError("alert.assessment.impact.completion", completion)
        
        for column in "source", "target", "analyzer":
            self[column] = [ ]
            for parameter, object in self.items():
                idx = parameter.find(column + "_object_")
                if idx == -1:
                    continue
                num = parameter.replace(column + "_object_", "", 1)

                try:
                    self[column].append((object, self["%s_value_%s" % (column, num)]))
                except KeyError:
                    pass # ignore empty inputs



class HeartbeatListingParameters(MessageListingParameters):
    pass



class SensorAlertListingParameters(AlertListingParameters):
    def register(self):
        AlertListingParameters.register(self)
        self.mandatory("analyzerid", long)



class SensorHeartbeatListingParameters(HeartbeatListingParameters):
    def register(self):
        HeartbeatListingParameters.register(self)
        self.mandatory("analyzerid", long)



class MessageListing:
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
        if self.parameters.has_key("timeline_end"):
            end = _MyTime(self.parameters["timeline_end"])
        else:
            end = _MyTime()
            if not self.parameters["timeline_unit"] in ("min", "hour"):
                end.round(self.parameters["timeline_unit"])
        
        start = end[self.parameters["timeline_unit"]] - self.parameters["timeline_value"]

        return start, end
        
    def _setTimeline(self, start, end):
        self.dataset["timeline.current"] = utils.create_link(self.view_name, self.parameters - ["timeline_end"])

        self.dataset["timeline.value"] = self.parameters["timeline_value"]
        self.dataset["timeline.%s_selected" % self.parameters["timeline_unit"]] = "selected"

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

    def _createTimeField(self, t, timezone):
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

    def _createInlineFilteredField(self, object, value, type=None):
        if not value:
            return { "value": None, "inline_filter": None }

        if type:
            extra = { "%s_object_0" % type: object, "%s_value_0" % type: value }
        else:
            extra = { object: value }

        return { "value": value, "inline_filter": utils.create_link(self.view_name, self.parameters + extra) }

    def _createHostField(self, object, value, type=None):
        field = self._createInlineFilteredField(object, value, type)
        field["host_commands"] = [ ]
        if not value:
            return field

        for command in "whois", "traceroute":
            if self.env.host_commands.has_key(command):
                field["host_commands"].append((command.capitalize(),
                                               utils.create_link(command,
                                                                 { "origin": self.view_name, "host": value })))

        return field
    
    def _createMessageLink(self, ident, view):
        return utils.create_link(view, { "origin": self.view_name, "ident": ident })

    def _setMessages(self, criteria):
        self.dataset["messages"] = [ ]
        
        for ident in self._getMessageIdents(criteria, self.parameters["limit"], self.parameters["offset"]):
            message = self._fetchMessage(ident)
            dataset = {
                "summary": self._createMessageLink(ident, self.summary_view),
                "details": self._createMessageLink(ident, self.details_view),
                "analyzerid": { "value": message.getAnalyzerID() },
                "ident": { "value": message.getMessageID() }
                }
            self._setMessage(dataset, message)
            self.dataset["messages"].append(dataset)

    def _setTimezone(self):
        for timezone in "utc", "sensor_localtime", "frontend_localtime":
            if timezone == self.parameters["timezone"]:
                self.dataset["timeline.%s_selected" % timezone] = "selected"
            else:
                self.dataset["timeline.%s_selected" % timezone] = ""

    def _getInlineFilter(self, name):
        return name, self.parameters.get(name)

    def _deleteMessages(self):
        if len(self.parameters["idents"]) == 0:
            return

        idents = self.parameters["idents"]
        del self.parameters["idents"]
        
        if not self.user.has(User.PERM_IDMEF_ALTER):
            raise User.PermissionDeniedError(user.login, self.current_view)

        for analyzerid, messageid in self.parameters["idents"]:
            self._deleteMessage(analyzerid, messageid)

    def render(self, criteria=None):
        self._deleteMessages()
        
        start, end = self._getTimelineRange()

        if criteria is None:
            criteria = [ ]
        
        criteria.append(self.time_criteria_format % (str(start), str(end)))
        criteria = " && ".join(criteria)

        self._setInlineFilter()
        self._setTimeline(start, end)
        self._setNavPrev(self.parameters["offset"])

        count = self._countMessages(criteria)

        self._setMessages(criteria)

        self.dataset["current_view"] = self.view_name
        self.dataset["nav.from"] = self.parameters["offset"] + 1
        self.dataset["nav.to"] = self.parameters["offset"] + len(self.dataset["messages"])
        self.dataset["limit"] = self.parameters["limit"]
        self.dataset["total"] = count

        self._setNavNext(self.parameters["offset"], count)
        self._setTimezone()



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
    time_criteria_format = "alert.create_time >= '%s' && alert.create_time < '%s'"
    message_criteria_format = "alert.analyzer.analyzerid == '%d' && alert.messageid == '%d'"

    def _getMessageIdents(self, criteria, limit, offset):
        return self.env.prelude.getAlertIdents(criteria, limit, offset)

    def _countMessages(self, criteria):
        return self.env.prelude.countAlerts(criteria)

    def _fetchMessage(self, ident):
        return self.env.prelude.getAlert(ident)

    def _setMessageDirection(self, direction, dataset, message):
        empty = True
        
        def set_main_and_extra_values(dataset, message, name, object_main, object_extra):
            if message[object_main]:
                dataset[name] = { "value": message[object_main] }
                dataset[name + "_extra"] = { "value": message[object_extra] }
            else:
                dataset[name] = { "value": message[object_extra] }
                dataset[name + "_extra"] = { "value": None }

            if dataset[name]["value"] != None:
                empty = False
            
        dataset["interface"] = { "value": message["alert.%s(0).interface" % direction] }

        dataset["users"] = [ ]

        idx = 0
        while True:
            if message["alert.%s(0).user.user_id(%d).ident" % (direction, idx)] is None:
                break

            user = { }
            dataset["users"].append(user)

            set_main_and_extra_values(user, message, "user",
                                      "alert.%s(0).user.user_id(%d).name" % (direction, idx),
                                      "alert.%s(0).user.user_id(%d).number" % (direction, idx))
            
            idx += 1

        if idx:
            empty = False

        dataset["addresses"] = [ ]

        idx = 1
        while True:
            if message["alert.%s(0).node.address(%d).address" % (direction, idx)] is None:
                break

            dataset["addresses"].append({ "value": message["alert.%s(0).node.address(%d).address" %
                                                           (direction, idx)]})
            idx += 1

        if idx > 1:
            empty = False            

        set_main_and_extra_values(dataset, message, "process",
                                  "alert.%s(0).process.name" % direction,
                                  "alert.%s(0).process.pid" % direction)

        set_main_and_extra_values(dataset, message, "service",
                                  "alert.%s(0).service.port" % direction,
                                  "alert.%s(0).service.name" % direction)
        
        if message["alert.%s(0).node.address(0).address" % direction]:
            dataset["address"] = self._createHostField("alert.%s.node.address.address" % direction,
                                                       message["alert.%s(0).node.address(0).address" % direction],
                                                       type=direction)
            dataset["address_extra"] = { "value": message["alert.%s(0).node.name" % direction] }
        else:
            dataset["address"] = self._createHostField("alert.%s.node.name" % direction,
                                                       message["alert.%s(0).node.name" % direction],
                                                       type=direction)
            dataset["address_extra"] = { "value": None }

        if dataset["address"]["value"] != None:
            empty = False

        dataset["empty"] = empty

    def _setMessageSource(self, dataset, message):
        dataset["source"] = { }
        self._setMessageDirection("source", dataset["source"], message)

    def _setMessageTarget(self, dataset, message):
        dataset["target"] = { }
        self._setMessageDirection("target", dataset["target"], message)
        
    def _setMessageClassification(self, dataset, message):
        urls = [ ]
        cnt = 0

        while True:
            origin = message["alert.classification.reference(%d).origin" % cnt]
            if origin is None:
                break
            
            name = message["alert.classification.reference(%d).name" % cnt]
            if not name:
                continue

            url = message["alert.classification.reference(%d).url" % cnt]
            if not url:
                continue
            
            urls.append("<a href='%s'>%s:%s</a>" % (url, origin, name))

            cnt += 1

        if urls:
            dataset["classification_references"] = "(" + ", ".join(urls) + ")"
        else:
            dataset["classification_references"] = ""

        dataset["classification"] = self._createInlineFilteredField("alert.classification.text",
                                                                    message["alert.classification.text"])
        
    def _setMessageSensor(self, dataset, message):
        def get_analyzer_names(alert, root):
            analyzerid = alert[root + ".name"]
            if analyzerid != None:
                return [ alert[root + ".name"] ] + get_analyzer_names(alert, root + ".analyzer")
            return [ ]

        analyzers = get_analyzer_names(message, "alert.analyzer")

        if len(analyzers) > 0:
            analyzer_name = analyzers[0]
        else:
            analyzer_name = "n/a"

        dataset["sensor"] = self._createInlineFilteredField("alert.analyzer.name", analyzer_name, type="analyzer")
        dataset["sensor"]["value"] = "/".join(analyzers[:-1])

        dataset["sensor_node_name"] = { "value": message["alert.analyzer.node.name"] }
        
    def _setMessage(self, dataset, message):
        dataset["severity"] = { "value": message.get("alert.assessment.impact.severity", "low") }
        dataset["completion"] = { "value": message["alert.assessment.impact.completion"] }
        
        dataset["time"] = self._createTimeField(message["alert.create_time"], self.parameters["timezone"])
        if (message["alert.detect_time"] != None and
            abs(int(message["alert.create_time"]) - int(message["alert.detect_time"])) > 60):
            dataset["detect_time"] = self._createTimeField(message["alert.detect_time"], self.parameters["timezone"])
        else:
            dataset["detect_time"] = { "value": None }
        
        self._setMessageSource(dataset, message)
        self._setMessageTarget(dataset, message)
        self._setMessageSensor(dataset, message)
        self._setMessageClassification(dataset, message)
        self._setMessageSensor(dataset, message)

    def _getFilters(self, storage, login):
        return storage.getAlertFilters(login)

    def _getFilter(self, storage, login, name):
        return storage.getAlertFilter(login, name)

    def _deleteMessage(self, analyzerid, messageid):
        self.env.prelude.deleteAlert(analyzerid, messageid)

    def _applySimpleFilter(self, criteria, column, object):
        if len(self.parameters[object]) > 0:
            criteria.append(" || ".join(map(lambda value: "%s substr '%s'" % (object, value),
                                            self.parameters[object])))
            self.dataset[object] = self.parameters[object]
            self.dataset[column + "_filtered"] = True
        else:
            self.dataset[object] = [ "" ]

    def _applyOptionalEnumFilter(self, criteria, column, object, values):
        def lists_have_same_content(l1, l2):
            l1 = copy.copy(l1)
            l2 = copy.copy(l2)
            l1.sort()
            l2.sort()
            
            return l1 == l2
        
        if (len(self.parameters[object]) != 0 and
            not lists_have_same_content(self.parameters[object], values)):
            for value in self.parameters[object]:
                new = [ ]
                # FIXME: disable filter on none, it needs a fix in libpreludedb
##                 if value == "none":
##                     new.append("! %s" % object)
##                 else:
                new.append("%s == '%s'" % (object, value))
            criteria.append("(" + " || ".join(new) + ")")
            self.dataset[object] = self.parameters[object]
            self.dataset[column + "_filtered"] = True
        else:
            self.dataset[object] = values

    def _applyClassificationFilters(self, criteria):
        self.dataset["classification_filtered"] = False
        self._applySimpleFilter(criteria, "classification", "alert.classification.text")
        self._applyOptionalEnumFilter(criteria, "classification", "alert.assessment.impact.severity",
                                      ["info", "low", "medium", "high", "none"])
        self._applyOptionalEnumFilter(criteria, "classification", "alert.assessment.impact.completion",
                                      ["failed", "succeeded", "none"])
        

    def _applyCheckboxFilters(self, criteria, type):
        def get_operator(object):
            if object in ("alert.source.service.port", "alert.target.service.port"):
                return "=="
            return "substr"
        
        if self.parameters[type]:
            criteria.append("(" + " || ".join(map(lambda (object, value): "%s %s '%s'" %
                                                  (object, get_operator(object), value),
                                                  self.parameters[type])) + ")")
            self.dataset[type] = self.parameters[type]
            self.dataset["%s_filtered" % type] = True
        else:
            self.dataset[type] = [ ("", "") ]
            self.dataset["%s_filtered" % type] = False
        
    def _applyFilters(self, criteria):
        self._applyClassificationFilters(criteria)
        self._applyCheckboxFilters(criteria, "source")
        self._applyCheckboxFilters(criteria, "target")
        self._applyCheckboxFilters(criteria, "analyzer")

    def render(self):
        criteria = [ ]

        if self.parameters.has_key("filter"):
            filter = self.env.storage.getAlertFilter(self.user.login, self.parameters["filter"])
            criteria.append("(%s)" % str(filter))

        self._applyFilters(criteria)

        MessageListing.render(self, criteria)
        
        self.dataset["filters"] = self.env.storage.getAlertFilters(self.user.login)
        self.dataset["current_filter"] = self.parameters.get("filter", "")



class HeartbeatListing(MessageListing, view.View):
    view_name = "heartbeat_listing"
    view_parameters = HeartbeatListingParameters
    view_permissions = [ User.PERM_IDMEF_VIEW ]
    view_template = "HeartbeatListing"

    root = "heartbeat"
    filters = { }
    summary_view = "heartbeat_summary"
    details_view = "heartbeat_details"
    time_criteria_format = "heartbeat.create_time >= '%s' && heartbeat.create_time < '%s'"
    message_criteria_format = "heartbeat.analyzer.analyzerid == '%d' && heartbeat.messageid == '%d'"

    def _getMessageIdents(self, criteria, limit, offset):
        return self.env.prelude.getHeartbeatIdents(criteria, limit, offset)

    def _countMessages(self, criteria):
        return self.env.prelude.countHeartbeats(criteria)

    def _fetchMessage(self, ident):
        return self.env.prelude.getHeartbeat(ident)

    def _setMessage(self, dataset, message):
        dataset["agent"] = self._createInlineFilteredField("heartbeat.analyzer.name",
                                                           message["heartbeat.analyzer.name"])
        dataset["model"] = self._createInlineFilteredField("heartbeat.analyzer.model",
                                                           message["heartbeat.analyzer.model"])
        dataset["node_name"] = self._createInlineFilteredField("heartbeat.analyzer.node.name",
                                                               message["heartbeat.analyzer.node.name"])
        dataset["node_address"] = self._createHostField("heartbeat.analyzer.node.address.address",
                                                        message["heartbeat.analyzer.node.address(0).address"])
        dataset["time"] = self._createTimeField(message["heartbeat.create_time"], self.parameters["timezone"])

    def _deleteMessage(self, analyzerid, messageid):
        self.env.prelude.deleteHeartbeat(analyzerid, messageid)



class SensorAlertListing(AlertListing, view.View):
    view_name = "sensor_alert_listing"
    view_parameters = SensorAlertListingParameters
    view_permissions = [ User.PERM_IDMEF_VIEW ]
    view_template = "SensorAlertListing"

    def _adjustCriteria(self, criteria):
        criteria.append("alert.analyzer.analyzerid == %d" % self.parameters["analyzerid"])

    def render(self):
        AlertListing.render(self)
        self.dataset["analyzer_infos"] = self.env.prelude.getAnalyzer(self.parameters["analyzerid"])



class SensorHeartbeatListing(HeartbeatListing, view.View):
    view_name = "sensor_heartbeat_listing"
    view_parameters = SensorHeartbeatListingParameters
    view_permissions = [ User.PERM_IDMEF_VIEW ]
    view_template = "SensorHeartbeatListing"

    def _adjustCriteria(self, criteria):
        criteria.append("heartbeat.analyzer.analyzerid == %d" % self.parameters["analyzerid"])

    def render(self):
        HeartbeatListing.render(self)
        self.dataset["analyzer"] = self.env.prelude.getAnalyzer(self.parameters["analyzerid"])
