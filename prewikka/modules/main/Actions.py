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


import sys

import time
import copy

from prewikka import Action
from prewikka import utils
from prewikka import User

from prewikka.modules.main import ActionParameters


def View(name):
    import prewikka.modules.main.Views
    
    return getattr(prewikka.modules.main.Views, name)
    

class _MyTime:
    def __init__(self, t=None):
        self._t = t or time.time()
        self._index = 5 # second index

    def __getitem__(self, key):
        try:
            self._index = [ "year", "month", "day", "hour", "min", "sec" ].index(key)
        except ValueError:
            raise KeyError
        
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
        return utils.time_to_ymdhms(self._t)
    
    def __int__(self):
        return self._t



class MessageListing(Action.Action):
    parameters = ActionParameters.MessageListing
    permissions = [ User.PERM_MESSAGE_VIEW ]

    def _adjustCriteria(self, request, criteria):
        pass

    def getFilter(self, wanted):
        for name, object, filter in self.fields:
            if name == wanted:
                return filter

        raise Action.ActionParameterInvalidError(wanted)
    
    def process(self, request):
        parameters = request.parameters
        prelude = request.prelude
        view = View(self.view_name)()
        view.setParameters(parameters)
        criteria = [ ]
        
        if parameters.getFilterName() and parameters.getFilterValue():
            criteria.append("%s == '%s'" % (self.getFilter(parameters.getFilterName()), parameters.getFilterValue()))
        
        if not parameters.getTimelineValue() or not parameters.getTimelineUnit():
            parameters.setTimelineValue(1)
            parameters.setTimelineUnit("hour")
        
        if parameters.getTimelineEnd():
            end = _MyTime(parameters.getTimelineEnd())
        else:
            end = _MyTime()
            if not parameters.getTimelineUnit() in ("min", "hour"):
                end.round(parameters.getTimelineUnit())

        if parameters.getOffset():
            view.setOffsetPrev(parameters.getOffset() - parameters.getLimit())
        
        start = end[parameters.getTimelineUnit()] - parameters.getTimelineValue()

        view.setTimeline(parameters.getTimelineValue(), parameters.getTimelineUnit())
        view.setTimelineStart(start)
        view.setTimelineEnd(end)

        if not parameters.getTimelineEnd() and parameters.getTimelineUnit() in ("min", "hour"):
            tmp = copy.copy(end)
            tmp.round(parameters.getTimelineUnit())
            tmp = tmp[parameters.getTimelineUnit()] - 1
            view.setTimelineNext(tmp[parameters.getTimelineUnit()] + parameters.getTimelineValue())
            view.setTimelinePrev(tmp[parameters.getTimelineUnit()] - (parameters.getTimelineValue() - 1))
        else:
            view.setTimelineNext(end[parameters.getTimelineUnit()] + parameters.getTimelineValue())
            view.setTimelinePrev(end[parameters.getTimelineUnit()] - parameters.getTimelineValue())
        
        criteria.append(self.time_criteria_format % (str(start), str(end)))
        self._adjustCriteria(request, criteria)
        criteria = " && ".join(criteria)

        messages = [ ]
        tmp = { }
        count = self.countMessages(prelude, criteria)

        for analyzerid, ident in self.getMessageIdents(prelude, criteria, parameters.getLimit(), parameters.getOffset()):
            message = { "analyzerid": analyzerid, "ident": ident }
            messages.append(message)
            tmp = self.getMessage(prelude, analyzerid, ident)
            for name, object, filter  in self.fields:
                message[name] = tmp[object]
            message["time"] = self.getMessageTime(tmp)

        view.setRange(parameters.getOffset() + 1, parameters.getOffset() + len(messages), parameters.getLimit(), count)

        if count > parameters.getOffset() + parameters.getLimit():
            view.setOffsetNext(parameters.getOffset() + parameters.getLimit(),
                               count - ((count % parameters.getLimit()) or parameters.getLimit()))
            
        messages.sort(lambda x, y: int(y["time"]) - int(x["time"]))
        
        view.setMessages(messages)
        
        return view



class AlertListing(MessageListing):
    view_name = "AlertListingView"
    time_criteria_format = "alert.detect_time >= '%s' && alert.detect_time < '%s'"
    message_criteria_format = "alert.analyzer.analyzerid == '%d' && alert.ident == '%d'"
    fields = [ ("severity", "alert.assessment.impact.severity", "alert.assessment.impact.severity"),
               ("classification", "alert.classification(0).name", "alert.classification.name"),
               ("source", "alert.source(0).node.address(0).address", "alert.source.node.address.address"),
               ("target", "alert.target(0).node.address(0).address", "alert.target.node.address.address"),
               ("sensor", "alert.analyzer.model", "alert.analyzer.model") ]

    def countMessages(self, prelude, criteria):
        return prelude.countAlerts(criteria)

    def getMessageIdents(self, prelude, *args, **kwargs):
        return apply(prelude.getAlertIdents, args, kwargs)

    def getMessage(self, prelude, analyzerid, ident):
        return prelude.getAlert(analyzerid, ident)

    def getMessageTime(self, message):
        return message["alert.detect_time"] or message["alert.create_time"] or 0



class HeartbeatListing(MessageListing):
    view_name = "HeartbeatListingView"
    time_criteria_format = "heartbeat.create_time >= '%s' && heartbeat.create_time < '%s'"
    message_criteria_format = "heartbeat.analyzer.analyzerid == '%d' && heartbeat.ident == '%d'"
    fields = [ ("address", "heartbeat.analyzer.node.address(0).address", "heartbeat.analyzer.node.address.address"),
               ("name", "heartbeat.analyzer.node.name", "heartbeat.analyzer.node.name"),
               ("type", "heartbeat.analyzer.model", "heartbeat.analyzer.model") ]

    def countMessages(self, prelude, criteria):
        return prelude.countHeartbeats(criteria)

    def getMessageIdents(self, prelude, *args, **kwargs):
        return apply(prelude.getHeartbeatIdents, args, kwargs)

    def getMessage(self, prelude, analyzerid, ident):
        return prelude.getHeartbeat(analyzerid, ident)

    def getMessageTime(self, message):
        return message["heartbeat.create_time"]



class DisplayMessageAction(Action.Action):
    parameters = ActionParameters.Message
    permissions = [ User.PERM_MESSAGE_VIEW ]
    
    def process(self, request, get_message):
        alert = get_message(request.parameters.getAnalyzerid(), request.parameters.getMessageIdent())
        view = View(self.view_name)()
        view.setMessage(alert)
        return view
    


class DisplayAlertAction(DisplayMessageAction):
    def process(self, request):
        return DisplayMessageAction.process(self, request, request.prelude.getAlert)



class DisplayHeartbeatAction(Action.Action):
    def process(self, request):
        return DisplayMessageAction.process(self, request, request.prelude.getHeartbeat)
        heartbeat = request.prelude.getHeartbeat(request.parameters.getAnalyzerid(), request.parameters.getMessageIdent())
        view = View(self.view_name)()
        view.setMessage(heartbeat)
        return view



class AlertSummary(DisplayAlertAction):
    view_name = "AlertSummaryView"



class HeartbeatSummary(DisplayHeartbeatAction):
    view_name = "HeartbeatSummaryView"



class AlertDetails(DisplayAlertAction):
    view_name = "AlertDetailsView"



class HeartbeatDetails(DisplayHeartbeatAction):
    view_name = "HeartbeatDetailsView"



class DeleteMessages:
    parameters = ActionParameters.MessageListingDelete
    permissions = [ User.PERM_MESSAGE_ALTER ]

    

class DeleteAlerts(DeleteMessages, AlertListing):
    
    def process(self, request):
        for analyzerid, alert_ident in request.parameters.getIdents():
            request.prelude.deleteAlert(analyzerid, alert_ident)
        
        request.parameters = ActionParameters.MessageListing(request.parameters)
        
        return AlertListing.process(self, request)



class DeleteHeartbeats(DeleteMessages, HeartbeatListing):
    def process(self, request):
        for analyzerid, heartbeat_ident in request.parameters.getIdents():
            request.prelude.deleteHeartbeat(analyzerid, heartbeat_ident)
        
        request.parameters = ActionParameters.MessageListing(request.parameters)
        
        return HeartbeatListing.process(self, request)



## class HeartbeatsAnalyze(Action.Action):
##     def process(self, core, parameters, request):
##         heartbeat_number = 48
##         heartbeat_value = 3600
##         heartbeat_error_tolerance = 3
        
##         prelude = core.prelude
        
##         data = { }
##         data["analyzers"] = [ ]
##         data["heartbeat_number"] = heartbeat_number
##         data["heartbeat_value"] = heartbeat_value
##         data["heartbeat_error_tolerance"] = heartbeat_error_tolerance
        
##         analyzers = data["analyzers"]

##         for analyzerid in prelude.getAnalyzerids():
##             analyzer = prelude.getAnalyzer(analyzerid)
##             analyzer["errors"] = [ ]
##             analyzers.append(analyzer)
            
##             previous_date = 0
            
##             rows = prelude.getValues(selection=["heartbeat.create_time/order_desc"],
##                                      criteria="heartbeat.analyzer.analyzerid == %d" % analyzerid,
##                                      limit=heartbeat_number)
            
##             for row in rows:
##                 date = row[0]
##                 if previous_date:
##                     delta = int(previous_date) - int(date)
##                     if delta > heartbeat_value + heartbeat_error_tolerance:
##                         analyzer["errors"].append({ "type": "later", "after": date, "back": previous_date })
##                     elif delta < heartbeat_value - heartbeat_error_tolerance:
##                         analyzer["errors"].append({ "type": "sooner", "date": previous_date, "delta": delta })
##                 else:
##                     analyzer["last_heartbeat"] = date
##                 previous_date = date
        
##         return View("HeartbeatsAnalyzeView"), data



class SensorMessageListing:
    parameters = ActionParameters.SensorMessageListing



class SensorAlertListing(SensorMessageListing, AlertListing):
    view_name = "SensorAlertListingView"
    
    def _adjustCriteria(self, request, criteria):
        criteria.append("alert.analyzer.analyzerid == %d" % request.parameters.getAnalyzerid())
        
    def process(self, request):
        view = AlertListing.process(self, request)
        view.setAnalyzer(request.prelude.getAnalyzer(request.parameters.getAnalyzerid()))
        
        return view



class SensorDeleteAlerts(SensorAlertListing):
    def process(self, request):
        for analyzerid, alert_ident in request.parameters.getIdents():
            request.prelude.deleteAlert(analyzerid, alert_ident)

        request.parameters = ActionParameters.SensorMessageListing(request.parameters)

        return SensorAlertListing.process(self, request)



class SensorHeartbeatListing(SensorMessageListing, HeartbeatListing):
    view_name = "SensorHeartbeatListingView"
    
    def _adjustCriteria(self, request, criteria):
        criteria.append("heartbeat.analyzer.analyzerid == %d" % request.parameters.getAnalyzerid())
    
    def process(self, request):
        view = HeartbeatListing.process(self, request)
        view.setAnalyzer(request.prelude.getAnalyzer(request.parameters.getAnalyzerid()))
        
        return view



class SensorDeleteHeartbeats(SensorHeartbeatListing):
    def process(self, request):
        for analyzerid, alert_ident in request.parameters.getIdents():
            request.prelude.deleteHeartbeat(analyzerid, alert_ident)

        request.parameters = ActionParameters.SensorMessageListing(request.parameters)

        return SensorHeartbeatListing.process(self, request)



class SensorAlertSummary(AlertSummary):
    view_name = "SensorAlertSummaryView"



class SensorAlertDetails(AlertDetails):
    view_name = "SensorAlertDetailsView"



class SensorHeartbeatSummary(HeartbeatSummary):
    view_name = "SensorHeartbeatSummaryView"



class SensorHeartbeatDetails(HeartbeatDetails):
    view_name = "SensorHeartbeatDetailsView"



class SensorListing(Action.Action):
    permissions = [ User.PERM_MESSAGE_VIEW ]
    
    def process(self, request):
        view = View("SensorListingView")()
        
        prelude = request.prelude
        analyzerids = prelude.getAnalyzerids()
        for analyzerid in analyzerids:
            analyzer = prelude.getAnalyzer(analyzerid)
            view.addAnalyzer(analyzer)
            
        return view
