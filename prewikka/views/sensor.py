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

from prewikka import view, User, utils


class HeartbeatAnalyzeParameters(view.Parameters):
    def register(self):
        self.mandatory("analyzerid", long)



class SensorMessagesDelete(view.Parameters):
    def register(self):
        self.optional("analyzerid", list, default=[])
        self.optional("alerts", str, default=None)
        self.optional("heartbeats", str, default=None)
    


def get_analyzer_status_from_latest_heartbeat(heartbeat_status, heartbeat_time,
                                              heartbeat_interval, error_margin):
    if heartbeat_status == "exiting":
        return "normal_offline", "normal offline"
    
    if time.time() - int(heartbeat_time) > int(heartbeat_interval) + error_margin:
        return "abnormal_offline", "abnormal offline"
    
    return "online", "online"



class SensorListing(view.View):
    view_name = "sensor_listing"
    view_parameters = view.Parameters
    view_permissions = [ User.PERM_IDMEF_VIEW ]
    view_template = "SensorListing"
    
    def render(self):
        analyzers = [ ]
        
        for analyzer_path in self.env.prelude.getAnalyzerPaths():
            analyzerid = analyzer_path[-1]
            analyzer = self.env.prelude.getAnalyzer(analyzerid)
            parameters = { "analyzerid": analyzer["analyzerid"] }
            analyzer["alert_listing"] = utils.create_link("sensor_alert_listing", parameters)
            analyzer["heartbeat_listing"] = utils.create_link("sensor_heartbeat_listing", parameters)
            analyzer["heartbeat_analyze"] = utils.create_link("heartbeat_analyze", parameters)

            analyzer["status"], analyzer["status_meaning"] = \
                                get_analyzer_status_from_latest_heartbeat(analyzer["last_heartbeat_status"],
                                                                          analyzer["last_heartbeat_time"],
                                                                          analyzer["last_heartbeat_interval"],
                                                                          3)

            analyzer["last_heartbeat_time"] = utils.time_to_ymdhms(time.localtime(int(analyzer["last_heartbeat_time"]))) + \
                                              " %+.2d:%.2d" % utils.get_gmt_offset()
            
            analyzers.append(analyzer)

        self.dataset["analyzers"] = [ ]
        for analyzer in analyzers:
            if analyzer["status"] == "ok":
                self.dataset["analyzers"].append(analyzer)
            else:
                self.dataset["analyzers"].insert(0, analyzer)



class SensorMessagesDelete(SensorListing):
    view_name = "sensor_messages_delete"
    view_parameters = SensorMessagesDelete
    view_permissions = [ User.PERM_IDMEF_VIEW, User.PERM_IDMEF_ALTER ]

    def render(self):
        for analyzerid in self.parameters["analyzerid"]:
            if self.parameters.has_key("alerts"):
                criteria = "alert.analyzer.analyzerid == %d || alert.analyzer.analyzer.analyzerid == %d" % \
                           (long(analyzerid), long(analyzerid))
                for ident in self.env.prelude.getAlertIdents(criteria):
                    self.env.prelude.deleteAlert(ident)
            if self.parameters.has_key("heartbeats"):
                criteria = "heartbeat.analyzer.analyzerid == %d" % long(analyzerid)
                for ident in self.env.prelude.getHeartbeatIdents(criteria):
                    self.env.prelude.deleteHeartbeat(ident)
            
        SensorListing.render(self)



class HeartbeatAnalyze(view.View):
    view_name = "heartbeat_analyze"
    view_parameters = HeartbeatAnalyzeParameters
    view_permissions = [ User.PERM_IDMEF_VIEW ]
    view_template = "HeartbeatAnalyze"

    def init(self, env):
        self._heartbeat_count = env.config.general.getOptionValue("heartbeat_count", 30)
        self._heartbeat_error_margin = env.config.general.getOptionValue("heartbeat_error_margin", 3)
    
    def render(self):
        analyzerid = self.parameters["analyzerid"]
        
        analyzer = self.env.prelude.getAnalyzer(analyzerid)
        analyzer["last_heartbeat_time"] = str(analyzer["last_heartbeat_time"])
        analyzer["events"] = [ ]
        analyzer["status"] = "abnormal_offline"
        analyzer["status_meaning"] = "abnormal offline"
        
        start = time.time()
        idents = self.env.prelude.getHeartbeatIdents(criteria="heartbeat.analyzer.analyzerid == %d" % analyzerid,
                                                     limit=self._heartbeat_count)
        newer = None
        latest = True
        total_interval = 0

        for ident in idents:
            older = self.env.prelude.getHeartbeat(ident)
            older_status = older.getAdditionalData("Analyzer status")
            older_interval = older["heartbeat.heartbeat_interval"]
            if not older_status or not older_interval:
                continue
            older_time = older["heartbeat.create_time"]
            total_interval += int(older_interval)

            if latest:
                latest = False
                analyzer["status"], analyzer["status_meaning"] = \
                                    get_analyzer_status_from_latest_heartbeat(older_status, older_time, older_interval,
                                                                              self._heartbeat_error_margin)
                if analyzer["status"] == "abnormal_offline":
                    analyzer["events"].append({ "value": "sensor is down since %s" % older_time, "type": "down"})
            if newer:
                event = None
                
                if newer_status == "starting":
                    if older_status == "exiting":
                        event = { "value": "normal sensor start at %s" % str(newer_time),
                                  "type": "start" }
                    else:
                        event = { "value": "unexpected sensor restart at %s" % str(newer_time),
                                  "type": "unexpected_restart" }

                if newer_status == "running":
                    if abs(int(newer_time) - int(older_time) - int(older_interval)) > self._heartbeat_error_margin:
                        event = { "value": "abnormal heartbeat interval between %s and %s" % (str(older_time), str(newer_time)),
                                  "type": "abnormal_heartbeat_interval" }
                                  

                if newer_status == "exiting":
                    event = { "value": "normal sensor stop at %s" % str(newer_time),
                              "type": "normal_stop" }

                if event:
                    analyzer["events"].append(event)

            newer = older
            newer_status = older_status
            newer_interval = older_interval
            newer_time = older_time

        if not analyzer["events"]:
            analyzer["events"].append({ "value":
                                        "No anomaly in the last %d heartbeats (1 heartbeat every %d s average)" %
                                        (self._heartbeat_count, total_interval / self._heartbeat_count),
                                        "type": "no_anomaly" })

        self.dataset["analyzer"] = analyzer
