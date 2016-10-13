# Copyright (C) 2004-2016 CS-SI. All Rights Reserved.
# Author: Yoann Vandoorselaere <yoannv@gmail.com>
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

from prewikka import hookmanager
from prewikka.utils import escape_html_string

class Message(object):
    def __init__(self, idmef, htmlsafe=False):
        self._idmef = idmef
        self._htmlsafe = htmlsafe

    def _escape_idmef(self, obj):
        if isinstance(obj, prelude.IDMEF):
            return Message(obj, htmlsafe=True)

        elif isinstance(obj, str):
            return escape_html_string(obj)

        elif isinstance(obj, tuple):
            return tuple((self._escape_idmef(o) for o in obj))

        return obj

    def get(self, default=None, htmlsafe=False):
        try:
            if htmlsafe or self._htmlsafe:
                return self._escape_idmef(self._idmef.get(default))
            else:
                return self._idmef.get(default)
        except IndexError as exc:
            return default

    def __getitem__(self, k):
       return self.get(k)


class IDMEFDatabase(preludedb.DB):
    _ORDER_MAP = { "time_asc": preludedb.DB.ORDER_BY_CREATE_TIME_ASC, "time_desc": preludedb.DB.ORDER_BY_CREATE_TIME_DESC }

    def _prepare_criteria(self, criteria, criteria_type):
        if not criteria:
            criteria = []

        if not isinstance(criteria, list):
            criteria = [ criteria ]

        all(hookmanager.trigger("HOOK_IDMEFDATABASE_CRITERIA_PREPARE", criteria, criteria_type))

        # Do not use string formatting to avoid errors when criteria contains '%'
        criteria = " && ".join(criteria).replace("%(backend)s", criteria_type).replace("%(time_field)s", "create_time")

        if len(criteria) > 0:
            return prelude.IDMEFCriteria(criteria)

        return None

    def __init__(self, config):
        preludedb.checkVersion("0.9.12")

        sql = preludedb.SQL(dict((k, str(v)) for k, v in config.items()))
        preludedb.DB.__init__(self, sql)

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

        ctype = self._guess_data_type(selection)
        criteria = self._prepare_criteria(criteria, ctype)
        return preludedb.DB.getValues(self, selection, criteria=criteria, distinct=bool(distinct), limit=limit, offset=offset)

    def getAnalyzerPaths(self, criteria=None):
        analyzer_paths = [ ]

        for (analyzerid,) in self.getValues(["heartbeat.analyzer(-1).analyzerid/group_by"], criteria):
            heartbeat = self.getHeartbeat(self.getLastHeartbeatIdent(analyzerid))
            analyzer_paths.append([i for i in heartbeat["heartbeat.analyzer(*).analyzerid"] if i is not None])

        return analyzer_paths

    def getAnalyzer(self, analyzerid, htmlsafe=False):
        heartbeat = self.getHeartbeat(self.getLastHeartbeatIdent(analyzerid), htmlsafe)["heartbeat"]
        analyzer = heartbeat["analyzer"][-1]
        return analyzer, heartbeat

    def update(self, fields, values, criteria=None, order=[], limit=-1, offset=-1):
        if type(criteria) is list:
            if len(criteria) == 0:
                criteria = None
            else:
                criteria = " || ".join([ "(%s)" % c for c in criteria ])

        ctype = self._guess_data_type(order)
        criteria = self._prepare_criteria(criteria, ctype)
        preludedb.DB.update(self, fields, values, criteria, order, limit, offset)

    def _guess_data_type(self, paths):
        """Guess IDMEF type (alert or heartbeat) from provided paths"""
        #FIXME: merge with the function in dataprovider?
        for path in paths:
            if "heartbeat" in path:
                return "heartbeat"
            elif "alert" in path:
                return "alert"

        return "alert"
