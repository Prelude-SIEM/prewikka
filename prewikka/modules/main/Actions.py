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
    def _adjustCriteria(self, core, parameters, criteria):
        pass
    
    def process(self, core, parameters, request):
        view = self._getView()()
        view.setParameters(parameters)
        prelude = core.prelude
        criteria = [ ]
        
        if parameters.getFilterName() and parameters.getFilterValue():
            criteria.append("%s == '%s'" % (parameters.getFilterName(), parameters.getFilterValue()))
        
        if not parameters.getTimelineValue() or not parameters.getTimelineUnit():
            parameters.setTimelineValue(1)
            parameters.setTimelineUnit("hour")
        
        if parameters.getTimelineEnd():
            end = _MyTime(parameters.getTimelineEnd())
        else:
            end = _MyTime()
            if not parameters.getTimelineUnit() in ("min", "hour"):
                end.round(parameters.getTimelineUnit())
        
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
        
        criteria.append(self._createTimeCriteria(start, end))
        self._adjustCriteria(core, parameters, criteria)
        criteria = " && ".join(criteria)
        
        idents = self._getMessageIdents(prelude, criteria)
        messages = [ ]
        if idents:
            for analyzerid, alert_ident in idents:
                message = self._getMessage(prelude, analyzerid, alert_ident)
                messages.append(message)
        
        self._sortMessages(messages)

        view.setMessages(messages)
        
        return view



class AlertListing(MessageListing):
    def _createTimeCriteria(self, start, end):
        return "alert.detect_time >= '%s' && alert.detect_time < '%s'" % (str(start), str(end))

    def _getMessageIdents(self, prelude, criteria):
        return prelude.getAlertIdents(criteria)

    def _getMessage(self, prelude, analyzerid, alert_ident):
        return prelude.getAlert(analyzerid, alert_ident)

    def _sortMessages(self, alerts):
        alerts.sort(lambda a1, a2: int(a2["detect_time"]) - int(a1["detect_time"]))

    def _getView(self):
        return View("AlertListingView")



class HeartbeatListing(MessageListing):
    def _createTimeCriteria(self, start, end):
        return "heartbeat.create_time >= '%s' && heartbeat.create_time < '%s'" % (str(start), str(end))
    
    def _getMessageIdents(self, prelude, criteria):
        return prelude.getHeartbeatIdents(criteria)
    
    def _getMessage(self, prelude, analyzerid, alert_ident):
        return prelude.getHeartbeat(analyzerid, alert_ident)
    
    def _sortMessages(self, heartbeats):
        heartbeats.sort(lambda hb1, hb2: int(hb2["create_time"]) - int(hb1["create_time"]))
        
    def _getView(self):
        return View("HeartbeatListingView")



class AlertAction(Action.Action):
    def process(self, core, parameters, request):
        alert = core.prelude.getAlert(parameters.getAnalyzerid(), parameters.getMessageIdent())
        view = View(self.view_name)()
        view.setMessage(alert)
        return view



class HeartbeatAction(Action.Action):
    def process(self, core, parameters, request):
        heartbeat = core.prelude.getHeartbeat(parameters.getAnalyzerid(), parameters.getMessageIdent())
        view = View(self.view_name)()
        view.setMessage(heartbeat)
        return view



class AlertSummary(AlertAction):
    view_name = "AlertSummaryView"



class HeartbeatSummary(HeartbeatAction):
    view_name = "HeartbeatSummaryView"



class AlertDetails(AlertAction):
    view_name = "AlertDetailsView"



class HeartbeatDetails(HeartbeatAction):
    view_name = "HeartbeatDetailsView"



class DeleteAlerts(AlertListing):
    def process(self, core, parameters, request):
        for analyzerid, alert_ident in parameters.getIdents():
            core.prelude.deleteAlert(analyzerid, alert_ident)
        
        parameters = ActionParameters.MessageListing(parameters)
        
        return AlertListing.process(self, core, parameters, request)



class DeleteHeartbeats(HeartbeatListing):
    def process(self, core, parameters, request):
        for analyzerid, heartbeat_ident in parameters.getIdents():
            core.prelude.deleteHeartbeat(analyzerid, heartbeat_ident)
        
        parameters = ActionParameters.MessageListing(parameters)
        
        return HeartbeatListing.process(self, core, parameters, request)



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



class SensorAlertListing(AlertListing):
    def _adjustCriteria(self, core, parameters, criteria):
        criteria.append("alert.analyzer.analyzerid == %d" % parameters.getAnalyzerid())

    def _getView(self):
        return View("SensorAlertListingView")

    def process(self, core, parameters, request):
        view = AlertListing.process(self, core, parameters, request)
        view.setAnalyzer(core.prelude.getAnalyzer(parameters.getAnalyzerid()))
        
        return view



class SensorDeleteAlerts(SensorAlertListing):
    def process(self, core, parameters, request):
        for analyzerid, alert_ident in parameters.getIdents():
            core.prelude.deleteAlert(analyzerid, alert_ident)

        parameters = ActionParameters.SensorMessageListing(parameters)

        return SensorAlertListing.process(self, core, parameters, request)



class SensorHeartbeatListing(HeartbeatListing):
    def _adjustCriteria(self, core, parameters, criteria):
        criteria.append("heartbeat.analyzer.analyzerid == %d" % parameters.getAnalyzerid())

    def _getView(self):
        return View("SensorHeartbeatListingView")

    def process(self, core, parameters, request):
        view = HeartbeatListing.process(self, core, parameters, request)
        view.setAnalyzer(core.prelude.getAnalyzer(parameters.getAnalyzerid()))

        return view



class SensorDeleteHeartbeats(SensorHeartbeatListing):
    def process(self, core, parameters, request):
        for analyzerid, alert_ident in parameters.getIdents():
            core.prelude.deleteHeartbeat(analyzerid, alert_ident)

        parameters = ActionParameters.SensorMessageListing(parameters)

        return SensorHeartbeatListing.process(self, core, parameters, request)



class SensorAlertSummary(AlertSummary):
    view_name = "SensorAlertSummaryView"



class SensorAlertDetails(AlertDetails):
    view_name = "SensorAlertDetailsView"



class SensorHeartbeatSummary(HeartbeatSummary):
    view_name = "SensorHeartbeatSummaryView"



class SensorHeartbeatDetails(HeartbeatDetails):
    view_name = "SensorHeartbeatDetailsView"



class SensorListing(Action.Action):
    def process(self, core, parameters, request):
        view = View("SensorListingView")()
        
        prelude = core.prelude
        for analyzerid in prelude.getAnalyzerids():
            analyzer = prelude.getAnalyzer(analyzerid)
            view.addAnalyzer(analyzer)
            
        return view
