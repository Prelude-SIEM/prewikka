# Copyright (C) 2004 Nicolas Delon <nicolas@prelude-ids.org>
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
        self.optional("inline_filter_name", str)
        self.optional("inline_filter_value", str)
        self.optional("filter", str)
        self.optional("timeline_value", int, default=1)
        self.optional("timeline_unit", str, default="hour")
        self.optional("timeline_end", int)
        self.optional("offset", int, default=0)
        self.optional("limit", int, default=50)
        self.optional("timezone", str, "frontend_localtime")

    def normalize(self):
        view.Parameters.normalize(self)

        for p1, p2 in ("inline_filter_name", "inline_filter_value"), ("timeline_value", "timeline_unit"):
            if self.has_key(p1) ^ self.has_key(p2):
                raise view.MissingParameterError(self.has_key(p1) and p1 or p2)

        if not self["timezone"] in ("frontend_localtime", "sensor_localtime", "utc"):
            raise view.InvalidValueError("timezone", self["timezone"])



class SensorMessageListingParameters(MessageListingParameters):
    def register(self):
        MessageListingParameters.register(self)
        self.mandatory("analyzerid", long)



class DeleteParameters:
    def register(self):
        self.optional("idents", list, default=[])

    def normalize(self):
        if not self.has_key("idents"):
            return
        
        idents = [ ]
        for ident in self["idents"]:
            try:
                analyzerid, message_ident = map(lambda x: long(x), ident.split(":"))
            except ValueError:
                raise ParametersNormalizer.InvalidValueError("idents", self["idents"])
            
            idents.append((analyzerid, message_ident))

        self["idents"] = idents



class MessageListingDeleteParameters(MessageListingParameters, DeleteParameters):
    def register(self):
        MessageListingParameters.register(self)
        DeleteParameters.register(self)

    def normalize(self):
        MessageListingParameters.normalize(self)
        DeleteParameters.normalize(self)



class SensorMessageListingDeleteParameters(SensorMessageListingParameters, DeleteParameters):
    def register(self):
        SensorMessageListingParameters.register(self)
        DeleteParameters.register(self)

    def normalize(self):
        SensorMessageListingParameters.normalize(self)
        DeleteParameters.normalize(self)



class MessageListing:
    def _adjustCriteria(self, criteria):
        pass

    def _getInlineFilter(self, wanted):
        for name, object, filter in self.fields:
            if name == wanted:
                return filter

        raise ParametersNormalizer.InvalidParameterError(wanted)

    def _setInlineFilter(self):
        self.dataset["active_inline_filter"] = self.parameters.get("inline_filter_name", "")
        self.dataset["remove_active_inline_filter"] = utils.create_link(self.view_name,
                                                                        self.parameters - \
                                                                        [ "inline_filter_name",
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
        self.dataset["timeline.hidden_parameters"] = { "view": self.view_name }
        for name in self.parameters.keys():
            if not name in ("timeline_value", "timeline_unit", "limit", "filter", "timezone"):
                self.dataset["timeline.hidden_parameters"][name] = self.parameters[name]

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

    def _copyMessageFields(self, dst, src):
        for name, object, filter  in self.fields:
            dst[name] = src[object]

    def _fetchMessages(self, criteria):
        messages = [ ]
        
        for analyzerid, ident in self.getMessageIdents(criteria,
                                                       self.parameters["limit"], self.parameters["offset"]):
            message = { "analyzerid": analyzerid, "ident": ident }
            messages.append(message)
            tmp = self.getMessage(analyzerid, ident)
            self._copyMessageFields(message, tmp)
            message["time"] = self.getMessageTime(tmp)
        
        messages.sort(lambda x, y: int(y["time"]) - int(x["time"]))

        return messages

    def _createMessageTimeField(self, t, timezone):
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

    def _createMessageField(self, name, value):
        if not value:
            return { "value": "n/a", "inline_filter": None }

        parameters = self.parameters + { "inline_filter_name": name, "inline_filter_value": value }

        return { "value": value, "inline_filter": utils.create_link(self.view_name, parameters) }

    def _createMessageHostField(self, name, value):
        field = self._createMessageField(name, value)
        field["host_commands"] = [ ]
        if not value:
            return field

        for command in "whois", "traceroute":
            if self.env.host_commands.has_key(command):
                field["host_commands"].append((command.capitalize(),
                                               utils.create_link(command,
                                                                 { "origin": self.view_name, "host": value })))

        return field
    
    def _createMessageLink(self, message, view):
        return utils.create_link(view, { "origin": self.view_name, "analyzerid": message["analyzerid"], "ident": message["ident"] })

    def _addMessage(self, fields, message):
        fields["summary"] = self._createMessageLink(message, self.summary_view)
        fields["details"] = self._createMessageLink(message, self.details_view)
        fields["ident"] = message["ident"]
        fields["analyzerid"] = message["analyzerid"]
        self._addMessageFields(fields, message)

    def _setMessages(self, messages):
        self.dataset["messages"] = [ ]
        for message in messages:
            fields = { }
            self.dataset["messages"].append(fields)
            self._addMessage(fields, message)

        self.dataset["delete_form_hiddens"] = self.parameters + { "view": self.delete_view }

    def _setTimezone(self):
        for timezone in "utc", "sensor_localtime", "frontend_localtime":
            if timezone == self.parameters["timezone"]:
                self.dataset["timeline.%s_selected" % timezone] = "selected"
            else:
                self.dataset["timeline.%s_selected" % timezone] = ""
        
    def render(self):
        start, end = self._getTimelineRange()

        criteria = [ ]
        if self.parameters.has_key("inline_filter_name") and self.parameters.has_key("inline_filter_value"):
            criteria.append("%s == '%s'" % (self._getInlineFilter(self.parameters["inline_filter_name"]),
                                            self.parameters["inline_filter_value"]))
        criteria.append(self.time_criteria_format % (str(start), str(end)))
        self._adjustCriteria(criteria)
        criteria = " && ".join(criteria)

        self._setInlineFilter()
        self._setTimeline(start, end)
        self._setNavPrev(self.parameters["offset"])

        count = self.countMessages(criteria)
        messages = self._fetchMessages(criteria)

        self.dataset["nav.from"] = self.parameters["offset"] + 1
        self.dataset["nav.to"] = self.parameters["offset"] + len(messages)
        self.dataset["limit"] = self.parameters["limit"]
        self.dataset["total"] = count

        self._setNavNext(self.parameters["offset"], count)
        self._setMessages(messages)
        self._setTimezone()



class AlertListing(MessageListing, view.View):
    view_name = "alert_listing"
    view_parameters = MessageListingParameters
    view_permissions = [ User.PERM_IDMEF_VIEW ]
    view_template = "AlertListing"
    
    delete_view = "alert_delete"
    summary_view = "alert_summary"
    details_view = "alert_details"
    time_criteria_format = "alert.create_time >= '%s' && alert.create_time < '%s'"
    message_criteria_format = "alert.analyzer.analyzerid == '%d' && alert.messageid == '%d'"
    fields = [ ("severity", "alert.assessment.impact.severity", "alert.assessment.impact.severity"),
               ("completion", "alert.assessment.impact.completion", "alert.assessment.impact.completion"),
               ("classification", "alert.classification.text", "alert.classification.text"),
               ("source", "alert.source(0).node.address(0).address", "alert.source.node.address.address"),
               ("sinterface", "alert.source(0).interface", "alert.source.interface"),
               ("sport", "alert.source(0).service.port", "alert.source.node.service.port"),
               ("suser_name", "alert.source(0).user.user_id(0).name", "alert.source.user.user_id.name"),
               ("suser_uid", "alert.source(0).user.user_id(0).number", "alert.source.user.user_id.number"),
               ("sprocess_name", "alert.source(0).process.name", "alert.source.process.name"),
               ("sprocess_pid", "alert.source(0).process.pid", "alert.source.process.pid"),
               ("target", "alert.target(0).node.address(0).address", "alert.target.node.address.address"),
               ("tinterface", "alert.target(0).interface", "alert.target.interface"),
               ("tport", "alert.target(0).service.port", "alert.target.node.service.port"),
               ("tuser_name", "alert.target(0).user.user_id(0).name", "alert.target.user.user_id.name"),
               ("tuser_uid", "alert.target(0).user.user_id(0).number", "alert.target.user.user_id.number"),
               ("tprocess_name", "alert.target(0).process.name", "alert.target.process.name"),
               ("tprocess_pid", "alert.target(0).process.pid", "alert.target.process.pid"),
               ("sensor", "alert.analyzer.name", "alert.analyzer.name"),
               ("sensor_node_name", "alert.analyzer.node.name", "alert.analyzer.node.name") ]

    def countMessages(self, criteria):
        return self.env.prelude.countAlerts(criteria)

    def getMessageIdents(self, *args, **kwargs):
        return apply(self.env.prelude.getAlertIdents, args, kwargs)

    def getMessage(self, analyzerid, ident):
        return self.env.prelude.getAlert(analyzerid, ident)

    def getMessageTime(self, message):
        return message["alert.create_time"] or 0

    def _copyMessageFields(self, dst, src):
        MessageListing._copyMessageFields(self, dst, src)
        
        urls = [ ]
        cnt = 0

        while True:
            origin = src["alert.classification.reference(%d).origin" % cnt]
            if origin is None:
                break
            
            name = src["alert.classification.reference(%d).name" % cnt]
            if not name:
                continue

            url = src["alert.classification.reference(%d).url" % cnt]
            if not url:
                continue
            
            urls.append("<a href='%s'>%s:%s</a>" % (url, origin, name))

            cnt += 1

        if urls:
            dst["classification_references"] = "(" + ", ".join(urls) + ")"
        else:
            dst["classification_references"] = ""
        
    def _addMessageFields(self, fields, alert):
        fields["severity"] = { "value": alert["severity"] or "low" }
        fields["completion"] = { "value": alert["completion"] }
        
        for name in ("analyzerid", "ident", "sensor_node_name",
                     "sinterface", "sport", "suser_name", "suser_uid", "sprocess_name", "sprocess_pid",
                     "tinterface", "tport", "tuser_name", "tuser_uid", "tprocess_name", "tprocess_pid"):
            fields[name] = { "value": alert[name] }
        
        for name in "classification", "sensor":
            fields[name] = self._createMessageField(name, alert[name])

        fields["classification_references"] = alert["classification_references"]
        
        for name in  "source", "target",:
            fields[name] = self._createMessageHostField(name, alert[name])
        
        fields["time"] = self._createMessageTimeField(alert["time"], self.parameters["timezone"])

    def getFilters(self, storage, login):
        return storage.getAlertFilters(login)

    def getFilter(self, storage, login, name):
        return storage.getAlertFilter(login, name)

    def _adjustCriteria(self, criteria):
        if self.parameters.has_key("filter"):
            filter = self.getFilter(self.storage, self.user.login, self.parameters["filter"])
            criteria.append("(%s)" % str(filter))

    def render(self):
        MessageListing.render(self)
        self.dataset["filters"] = self.env.storage.getAlertFilters(self.user.login)
        self.dataset["current_filter"] = self.parameters.get("filter", "")



class HeartbeatListing(MessageListing, view.View):
    view_name = "heartbeat_listing"
    view_parameters = MessageListingParameters
    view_permissions = [ User.PERM_IDMEF_VIEW ]
    view_template = "HeartbeatListing"
    
    delete_view = "heartbeat_delete"
    summary_view = "heartbeat_summary"
    details_view = "heartbeat_details"
    time_criteria_format = "heartbeat.create_time >= '%s' && heartbeat.create_time < '%s'"
    message_criteria_format = "heartbeat.analyzer.analyzerid == '%d' && heartbeat.messageid == '%d'"
    fields = [ ("agent", "heartbeat.analyzer.name", "heartbeat.analyzer.name"),
               ("node_address", "heartbeat.analyzer.node.address(0).address", "heartbeat.analyzer.node.address.address"),
               ("node_name", "heartbeat.analyzer.node.name", "heartbeat.analyzer.node.name"),
               ("type", "heartbeat.analyzer.model", "heartbeat.analyzer.model") ]

    def countMessages(self, criteria):
        return self.env.prelude.countHeartbeats(criteria)

    def getMessageIdents(self, *args, **kwargs):
        return apply(self.env.prelude.getHeartbeatIdents, args, kwargs)

    def getMessage(self, analyzerid, ident):
        return self.env.prelude.getHeartbeat(analyzerid, ident)

    def getMessageTime(self, message):
        return message["heartbeat.create_time"]

    def _addMessageFields(self, fields, heartbeat):
        for name in "ident", "analyzerid", "agent", "node_name", "type":
            fields[name] = self._createMessageField(name, heartbeat[name])
        fields["node_address"] = self._createMessageHostField("address", heartbeat["node_address"])
        fields["time"] = self._createMessageTimeField(heartbeat["time"], self.parameters["timezone"])



class SensorAlertListing(AlertListing, view.View):
    view_name = "sensor_alert_listing"
    view_parameters = SensorMessageListingParameters
    view_permissions = [ User.PERM_IDMEF_VIEW ]
    view_template = "SensorAlertListing"
    
    delete_view = "sensor_alert_delete"

    def _adjustCriteria(self, criteria):
        criteria.append("alert.analyzer.analyzerid == %d" % self.parameters["analyzerid"])
        
    def render(self):
        AlertListing.render(self)
        self.dataset["analyzer"] = self.env.prelude.getAnalyzer(self.parameters["analyzerid"])



class SensorHeartbeatListing(HeartbeatListing, view.View):
    view_name = "sensor_heartbeat_listing"
    view_parameters = SensorMessageListingParameters
    view_permissions = [ User.PERM_IDMEF_VIEW ]
    view_template = "SensorHeartbeatListing"
    
    delete_view = "sensor_heartbeat_delete"
    
    def _adjustCriteria(self, criteria):
        criteria.append("heartbeat.analyzer.analyzerid == %d" % self.parameters["analyzerid"])
    
    def render(self):
        HeartbeatListing.render(self)
        self.dataset["analyzer"] = self.env.prelude.getAnalyzer(self.parameters["analyzerid"])



class _AlertDelete:
    view_parameters = MessageListingDeleteParameters
    view_permissions = [ User.PERM_IDMEF_ALTER ]

    def _delete_message(self, analyzerid, messageid):
        self.env.prelude.deleteAlert(analyzerid, messageid)
    
    def _delete(self):
        for analyzerid, messageid in self.parameters["idents"]:
            self._delete_message(analyzerid, messageid)
        
        del self.parameters["idents"]



class _HeartbeatDelete(_AlertDelete):
    def _delete_message(self, analyzerid, messageid):
        self.env.prelude.deleteHeartbeat(analyzerid, messageid)



class AlertDelete(_AlertDelete, AlertListing):
    view_name = "alert_delete"

    def render(self):
        self._delete()
        AlertListing.render(self)



class HeartbeatDelete(_HeartbeatDelete, HeartbeatListing):
    view_name = "heartbeat_delete"

    def render(self):
        self._delete()
        HeartbeatListing.render(self)



class SensorAlertDelete(_AlertDelete, SensorAlertListing):
    view_name = "sensor_alert_delete"
    view_parameters = SensorMessageListingDeleteParameters

    def render(self):
        self._delete()
        SensorAlertListing.render(self)



class SensorHeartbeatDelete(_HeartbeatDelete, SensorHeartbeatListing):
    view_name = "sensor_heartbeat_delete"
    view_parameters = SensorMessageListingDeleteParameters

    def render(self):
        self._delete()
        SensorHeartbeatListing.render(self)
