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


import prelude
from preludedb import PreludeDB


class Message:
    def __init__(self, message):
        self._message = message

    def __getitem__(self, key):
        return self._message[key]
    
    def get(self, key, default=None):
        value = self[key]
        return value is None and default or value



class Alert(Message):
    def __getitem__(self, key):
        if key.find("alert.") != 0:
            key = "alert." + key
        return Message.__getitem__(self, key)



class Heartbeat(Message):
    def __getitem__(self, key):
        if key.find("heartbeat.") != 0:
            key = "heartbeat." + key
        return Message.__getitem__(self, key)



class Prelude(PreludeDB):
    def __init__(self, config):
        PreludeDB.init()
        PreludeDB.__init__(self,
                           type=config.get("type", "mysql"),
                           host=config.get("host", "127.0.0.1"),
                           port=config.get("port", 0),
                           name=config.get("name", "prelude"),
                           user=config.get("user", "prelude"),
                           password=config.get("password", "prelude"))
        self.connect()

    def getAlertIdents(self, criteria=None):
        if criteria:
            criteria = prelude.IDMEFCriteria(criteria)
        return self.get_alert_ident_list(criteria)

    def getHeartbeatIdents(self, criteria=None):
        if criteria:
            criteria = prelude.IDMEFCriteria(criteria)
        return self.get_heartbeat_ident_list(criteria)
    
    def getAlert(self, analyzerid, alert_ident):
        return Alert(self.get_alert(analyzerid, alert_ident))
    
    def deleteAlert(self, analyzerid, alert_ident):
        return self.delete_alert(analyzerid, alert_ident)
    
    def getHeartbeat(self, analyzerid, heartbeat_ident):
        return Heartbeat(self.get_heartbeat(analyzerid, heartbeat_ident))
    
    def deleteHeartbeat(self, analyzerid, heartbeat_ident):
        return self.delete_heartbeat(analyzerid, heartbeat_ident)

    def getValues(self, selection, criteria=None, distinct=0, limit=-1, offset=-1):
        if criteria:
            criteria = prelude.IDMEFCriteria(criteria)
        
        return self.get_values(selection, criteria, distinct, limit, offset)

    def getAnalyzerids(self):
        analyzerids = [ ]
        rows = self.getValues(selection=[ "alert.analyzer.analyzerid/group_by" ])
        for row in rows:
            analyzerid = row[0]
            analyzerids.append(analyzerid)

        return analyzerids

    def getAnalyzer(self, analyzerid):
        rows = self.getValues(selection=["max(alert.ident)"],
                              criteria="alert.analyzer.analyzerid == %d" % analyzerid)
        row = rows[0]
        ident = row[0]
        
        alert = self.getAlert(analyzerid, ident)
        
        analyzer = { }
        analyzer["analyzerid"] = analyzerid
        analyzer["model"] = alert.get("alert.analyzer.model", "n/a") 
        analyzer["version"] = alert.get("alert.analyzer.version", "n/a")
        analyzer["ostype"] = alert.get("alert.analyzer.ostype", "n/a")
        analyzer["osversion"] = alert.get("alert.analyzer.osversion", "n/a")
        analyzer["name"] = alert.get("alert.analyzer.node.name", "n/a")
        analyzer["location"] = alert.get("alert.analyzer.node.location", "n/a")
        analyzer["address"] = alert.get("alert.analyzer.node.address(0).address", "n/a")
        
        return analyzer
