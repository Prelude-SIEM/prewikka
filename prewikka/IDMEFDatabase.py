# Copyright (C) 2004-2014 CS-SI. All Rights Reserved.
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
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


import time, types
import prelude, preludedb

from prewikka.utils import escape_html_string, time_to_ymdhms

class Message(object):
    def __init__(self, idmef, htmlsafe=False):
        self._idmef = idmef
        self._htmlsafe = htmlsafe

    def match(self, criteria):
        if type(criteria) is list:
            criteria = " && ".join(criteria)

        return prelude.IDMEFCriteria(criteria).match(self._idmef)

    def get(self, default=None, htmlsafe=False):
        try:
            ret = self._idmef.get(default)
            if isinstance(ret, prelude.IDMEF):
                ret = Message(ret, self._htmlsafe)

            if (htmlsafe or self._htmlsafe) and isinstance(ret, str):
                ret = escape_html_string(ret)
        except IndexError as exc:
            ret = default

        return ret

    def __getitem__(self, k):
       return self.get(k)


class IDMEFDatabase(preludedb.DB):
    _ORDER_MAP = { "time_asc": preludedb.DB.ORDER_BY_CREATE_TIME_ASC, "time_desc": preludedb.DB.ORDER_BY_CREATE_TIME_DESC }

    def _prepare_criteria(self, criteria, criteria_type):
        if not criteria:
            criteria = []

        if type(criteria) is not list:
            criteria = [ criteria ]

        criteria = " && ".join(criteria)
        if len(criteria) > 0:
            return prelude.IDMEFCriteria(criteria)

        return None

    def __init__(self, config):
        preludedb.checkVersion("0.9.12")

        d = {}
        for k,v in config.items():
                d[k] = str(v)

        self._sql = preludedb.SQL(d)
        preludedb.DB.__init__(self, self._sql)


    def getAlertIdents(self, criteria=None, limit=-1, offset=-1, order_by="time_desc"):
        return preludedb.DB.getAlertIdents(self, self._prepare_criteria(criteria, "alert"), limit, offset, self._ORDER_MAP[order_by])

    def getHeartbeatIdents(self, criteria=None, limit=-1, offset=-1, order_by="time_desc"):
        return preludedb.DB.getHeartbeatIdents(self, self._prepare_criteria(criteria, "heartbeat"), limit, offset, self._ORDER_MAP[order_by])

    def _getLastMessageIdent(self, type, get_message_idents, analyzerid):
        criteria = None
        if analyzerid is not False:
            if analyzerid is None:
                criteria = "! %s.analyzer(-1).analyzerid" % (type)
            else:
                criteria = "%s.analyzer(-1).analyzerid == '%s'" % (type, analyzerid)

        return get_message_idents(criteria, limit=1)[0]

    def getLastAlertIdent(self, analyzer=False):
        return self._getLastMessageIdent("alert", self.getAlertIdents, analyzer)

    def getLastHeartbeatIdent(self, analyzer=False):
        return self._getLastMessageIdent("heartbeat", self.getHeartbeatIdents, analyzer)

    def getAlert(self, ident, htmlsafe=False):
        return Message(preludedb.DB.getAlert(self, ident), htmlsafe)

    def getHeartbeat(self, ident, htmlsafe=False):
        return Message(preludedb.DB.getHeartbeat(self, ident), htmlsafe)

    def getValues(self, selection, criteria=None, distinct=0, limit=-1, offset=-1):
        if type(criteria) is list:
            if len(criteria) == 0:
                criteria = None
            else:
                criteria = " && ".join([ "(%s)" % c for c in criteria ])

        if selection[0].find("alert") != -1:
            ctype = "alert"
        else:
            ctype = "heartbeat"

        criteria = self._prepare_criteria(criteria, ctype)
        return preludedb.DB.getValues(self, selection, criteria=criteria, distinct=bool(distinct), limit=limit, offset=offset)

    def getAnalyzerids(self, criteria=None):
        analyzerids = [ ]
        rows = self.getValues([ "heartbeat.analyzer(-1).analyzerid/group_by" ])
        for row in rows:
            analyzerid = row[0]
            ident = self.getLastHeartbeatIdent(analyzerid)
            heartbeat = self.getHeartbeat(ident)
            if not criteria or heartbeat.match(criteria):
                analyzerids.append(analyzerid)

        return analyzerids

    def getAnalyzerPaths(self, criteria=None):
        analyzer_paths = [ ]
        for analyzerid in self.getAnalyzerids():
            ident = self.getLastHeartbeatIdent(analyzerid)
            heartbeat = self.getHeartbeat(ident)
            if criteria and not heartbeat.match(criteria):
                continue
            path = [ ]
            index = 0
            while True:
                analyzerid = heartbeat["heartbeat.analyzer(%d).analyzerid" % index]
                if not analyzerid:
                    break
                path.append(analyzerid)
                index += 1
            analyzer_paths.append(path)

        return analyzer_paths

    def getAnalyzer(self, analyzerid):
        ident = self.getLastHeartbeatIdent(analyzerid)
        heartbeat = self.getHeartbeat(ident)["heartbeat"]

        path = []
        analyzer = None
        analyzerd = { "path": path }

        for a in heartbeat["analyzer"]:
            path.append(a["analyzerid"])
            analyzer = a

        for column in "analyzerid", "name", "model", "version", "class", "ostype", "osversion", "node.name", "node.location", "node.address.address":
            analyzerd[column] = analyzer.get(column)

        analyzerd["last_heartbeat_time"] = heartbeat.get("create_time")
        analyzerd["last_heartbeat_interval"] = heartbeat.get("heartbeat_interval")
        analyzerd["last_heartbeat_status"] = heartbeat.get("additional_data('Analyzer status')")

        return analyzerd
