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


import time, types
from prelude import *
from preludedb import *

from prewikka.utils import escape_html_string, time_to_ymdhms



def escape_value(value):
    if type(value) is str:
        return escape_html_string(value)
    return value



class IDMEFTime(object):
    def __init__(self, res):
        self._res = res

    def __del__(self):
        idmef_time_destroy(self._res)

    def __str__(self):
        return idmef_time_to_string(self._res)

    def __int__(self):
        return idmef_time_get_sec(self._res)

    def __float__(self):
        return float(idmef_time_get_sec(self._res)) + float(idmef_time_get_usec(self._res)) / 10 ** 6

    def toYMDHMS(self):
        return time_to_ymdhms(time.localtime(idmef_time_get_sec(self._res)))

    def __getattribute__(self, name):
        if name is "sec":
            return idmef_time_get_sec(self._res)

        if name is "usec":
            return idmef_time_get_usec(self._res)

        if name is "gmt_offset":
            return idmef_time_get_gmt_offset(self._res)

        return object.__getattribute__(self, name)



def convert_idmef_value(value):
    def get_time(value):
        time = idmef_value_get_time(value)
        if not time:
            return None

        return IDMEFTime(idmef_time_clone(time))

    def get_enum(value):
        return idmef_class_enum_to_string(idmef_value_get_class(value), idmef_value_get_enum(value))

    try:
        return {
            IDMEF_VALUE_TYPE_INT8:          idmef_value_get_int8,
            IDMEF_VALUE_TYPE_UINT8:         idmef_value_get_uint8,
            IDMEF_VALUE_TYPE_INT16:         idmef_value_get_int16,
            IDMEF_VALUE_TYPE_UINT16:        idmef_value_get_uint16,
            IDMEF_VALUE_TYPE_INT32:         idmef_value_get_int32,
            IDMEF_VALUE_TYPE_UINT32:        idmef_value_get_uint32,
            IDMEF_VALUE_TYPE_INT64:         idmef_value_get_int64,
            IDMEF_VALUE_TYPE_UINT64:        idmef_value_get_uint64,
            IDMEF_VALUE_TYPE_FLOAT:         idmef_value_get_float,
            IDMEF_VALUE_TYPE_DOUBLE:        idmef_value_get_double,
            IDMEF_VALUE_TYPE_STRING:        idmef_value_get_string,
            IDMEF_VALUE_TYPE_DATA:          idmef_value_get_data,
	    IDMEF_VALUE_TYPE_CLASS:	    idmef_value_get_object,
            IDMEF_VALUE_TYPE_ENUM:          get_enum,
            IDMEF_VALUE_TYPE_TIME:          get_time
            }[idmef_value_get_type(value)](value)
    except KeyError:
        return None



class Message:
    def __init__(self, res, htmlsafe):
        self._res = res
        self._value_list = None
        self._htmlsafe = htmlsafe

    def __del__(self):
        idmef_message_destroy(self._res)

        if self._value_list:
            idmef_value_destroy(self._value_list)

    def __iter__(self):
        if not self._value_list:
            raise TypeError, "iteration over a non-sequence"

        self._list_iterator = 0
        return self

    def __len__(self):
        if self._value_list:
            return idmef_value_get_count(self._value_list)

        return 1

    def next(self):
        next = idmef_value_get_nth(self._value_list, self._list_iterate)
        if not next:
            raise StopIteration

        value = self._convert_value(next, self._root + "(%d)" % self._list_iterate)
        self._list_iterate += 1

        return value

    def _convert_value(self, idmef_value, key):
        if idmef_value_get_type(idmef_value) == IDMEF_VALUE_TYPE_LIST:
            value = Message(idmef_message_ref(self._res), self._htmlsafe)
            value._root = key
            value._list_iterate = 0
            value._value_list = idmef_value
            if self._value_list:
                idmef_value_ref(idmef_value)

        elif idmef_value_get_type(idmef_value) != IDMEF_VALUE_TYPE_CLASS:
            value = convert_idmef_value(idmef_value)
            if not self._value_list:
                idmef_value_destroy(idmef_value)

        else:
            if not self._value_list:
                idmef_value_destroy(idmef_value)

            value = Message(idmef_message_ref(self._res), self._htmlsafe)
            value._root = key

        return value

    def _get_raw_value(self, key):
        path = idmef_path_new_fast(key)
        idmef_value = idmef_path_get(path, self._res)

        if idmef_value:
            ret = self._convert_value(idmef_value, key)
        else:
            if idmef_path_is_ambiguous(path):
                ret = []
            else:
                ret = None

        idmef_path_destroy(path)
        return ret

    def __getitem__(self, key):
        if key.find("%s." % self._root) != 0:
            key = "%s." % self._root + key

        if self._htmlsafe:
            return escape_value(self._get_raw_value(key))
        else:
            return self._get_raw_value(key)

    def match(self, criteria):
        if type(criteria) is list:
            criteria = " && ".join(criteria)

        criteria = idmef_criteria_new_from_string(criteria)
        ret = idmef_criteria_match(criteria, self._res)
        idmef_criteria_destroy(criteria)

        return ret

    def get(self, key, default=None, htmlsafe=None):
        if htmlsafe != None:
            htmlsafe_bkp = self._htmlsafe
            self._htmlsafe = htmlsafe

        val = self[key]
        if val == None:
                val = default

        if htmlsafe != None:
            self._htmlsafe = htmlsafe_bkp

        return val

    def getAdditionalData(self, searched, many_values=False):
        values = [ ]
        i = 0
        while True:
            meaning = self["%s.additional_data(%d).meaning" % (self._root, i)]
            if meaning is None:
                break

            if meaning == searched:
                value = self["%s.additional_data(%d).data" % (self._root, i)]

                if not many_values:
                    return value

                values.append(value)

            i += 1

        if many_values:
            return values

        return None

    def getMessageID(self):
        return self["%s.messageid" % self._root]

    def getAnalyzerID(self):
        return self["%s.analyzer.analyzerid" % self._root]



class Alert(Message):
    _root = "alert"



class Heartbeat(Message):
    _root = "heartbeat"



class DbResult:
    def __init__(self, results):
        self._rows = [ ]
        self._has_cache = False
        self._res, self._len = results

    def __iter__(self):
        if self._has_cache:
            return iter(self._rows)
        else:
            return self

    def __len__(self):
        return self._len

    def __del__(self):
        if self._res:
            self._db_delete(self._res)

    def __getitem__(self, key):
        if isinstance(key, types.SliceType):
            start, stop, step = key.start, key.stop, key.step
            index = start + stop
        else:
            index = key

        if not self._has_cache:
            for r in self:
                if len(self._rows) >= index:
                    break

        return self._rows[key]

    def next(self):
        if self._res == None:
            raise StopIteration

        values = self._db_get_next()
        if values is None:
            self._has_cache = True
            self._db_delete(self._res)
            self._res = None
            raise StopIteration

        row = self._db_convert_row(values)

        self._rows.append(row)
        return row


class DbResultValues(DbResult):
    def __init__(self, selection, results):
        self._selection = selection
        DbResult.__init__(self, results)

    def _db_get_next(self):
        return preludedb_result_values_get_next(self._res)

    def _db_delete(self, result):
        if self._selection:
            preludedb_path_selection_destroy(self._selection)

        if result:
            preludedb_result_values_destroy(result)

    def _db_convert_row(self, values):
        row = []
        for value in values:
           if value is None:
               row.append(None)
           else:
               row.append(convert_idmef_value(value))
               idmef_value_destroy(value)

        return row

class DbResultIdents(DbResult):
    def _db_get_next(self):
        return preludedb_result_idents_get_next(self._res)

    def _db_delete(self, result):
        if result:
            preludedb_result_idents_destroy(result)

    def _db_convert_row(self, value):
        return value

class IDMEFDatabase:
    _db_destroy = preludedb_destroy
    _db = None

    def __init__(self, config):
        settings = preludedb_sql_settings_new()
        for param in "file", "host", "port", "name", "user", "pass":
            if config.getOptionValue(param):
                preludedb_sql_settings_set(settings, param, config.getOptionValue(param))

        sql = preludedb_sql_new(config.getOptionValue("type", "mysql"), settings)
        if config.getOptionValue("log"):
            preludedb_sql_enable_query_logging(sql, config.getOptionValue("log"))

        cur = ver = None
        wanted_version = "0.9.12"
        try:
            cur = preludedb_check_version(None)
            ver = preludedb_check_version(wanted_version)
            if not ver:
                raise
        except:
            if cur:
                raise "libpreludedb %s or higher is required (%s found)." % (wanted_version, cur)
            else:
                raise "libpreludedb %s or higher is required." % wanted_version

        self._db = preludedb_new(sql, None)

    def __del__(self):
        if self._db:
            self._db_destroy(self._db)

    def _getMessageIdents(self, get_message_idents, criteria, limit, offset, order_by):
        if len(criteria) == 0:
            criteria = None

        if type(criteria) is list:
            criteria = " && ".join(criteria)

        if criteria:
            criteria = idmef_criteria_new_from_string(criteria)

        idents = [ ]

        if order_by == "time_asc":
            order_by = PRELUDEDB_RESULT_IDENTS_ORDER_BY_CREATE_TIME_ASC
        else:
            order_by = PRELUDEDB_RESULT_IDENTS_ORDER_BY_CREATE_TIME_DESC

        try:
            result = get_message_idents(self._db, criteria, limit, offset, order_by)
        except:
            self._freeDbParams(criteria=criteria)
            raise

        if criteria:
            idmef_criteria_destroy(criteria)

        if not result:
            return [ ]

        return DbResultIdents(result)

    def getAlertIdents(self, criteria=None, limit=-1, offset=-1, order_by="time_desc"):
        return self._getMessageIdents(preludedb_get_alert_idents2, criteria, limit, offset, order_by)

    def getHeartbeatIdents(self, criteria=None, limit=-1, offset=-1, order_by="time_desc"):
        return self._getMessageIdents(preludedb_get_heartbeat_idents2, criteria, limit, offset, order_by)

    def _getLastMessageIdent(self, type, get_message_idents, analyzerid):
        criteria = None
        if analyzerid is not False:
            if analyzerid is None:
                criteria = "! %s.analyzer(-1).analyzerid" % (type)
            else:
                criteria = "%s.analyzer(-1).analyzerid == '%s'" % (type, str(analyzerid))

        idents = get_message_idents(criteria, limit=1)

        return idents[0]

    def getLastAlertIdent(self, analyzer=False):
        return self._getLastMessageIdent("alert", self.getAlertIdents, analyzer)

    def getLastHeartbeatIdent(self, analyzer=False):
        return self._getLastMessageIdent("heartbeat", self.getHeartbeatIdents, analyzer)

    def getAlert(self, ident, htmlsafe=False):
        return Alert(preludedb_get_alert(self._db, ident), htmlsafe)

    def deleteAlert(self, identlst):
        # we need to cast the value to list since we might get
        # a DbResultIdent() class as input.
        preludedb_transaction_start(self._db)
        preludedb_delete_alert_from_list(self._db, list(identlst))
        preludedb_transaction_end(self._db)

    def getHeartbeat(self, ident, htmlsafe=False):
        return Heartbeat(preludedb_get_heartbeat(self._db, ident), htmlsafe)

    def deleteHeartbeat(self, identlst):
        # we need to cast the value to list since we might get
        # a DbResultIdent() class as input.
        preludedb_transaction_start(self._db)
        preludedb_delete_heartbeat_from_list(self._db, list(identlst))
        preludedb_transaction_end(self._db)

    def _freeDbParams(self, selection=None, criteria=None):
        if selection:
            preludedb_path_selection_destroy(selection)

        if criteria:
            idmef_criteria_destroy(criteria)

    def getValues(self, selection, criteria=None, distinct=0, limit=-1, offset=-1):
        if type(criteria) is list:
            if len(criteria) == 0:
                criteria = None
            else:
                criteria = " && ".join([ "(" + c + ")" for c in criteria ])

        if criteria:
            criteria = idmef_criteria_new_from_string(criteria)

        my_selection = preludedb_path_selection_new()
        for selected in selection:
            my_selected = preludedb_selected_path_new_string(selected)
            preludedb_path_selection_add(my_selection, my_selected)

        try:
            result = preludedb_get_values2(self._db, my_selection, criteria, distinct, limit, offset)
        except:
            self._freeDbParams(my_selection, criteria)
            raise

        if criteria:
            idmef_criteria_destroy(criteria)

        if not result:
            preludedb_path_selection_destroy(my_selection)
            return [ ]

        return DbResultValues(my_selection, result)

    def _countMessages(self, root, criteria):
        return self.getValues(["count(%s.create_time)" % root], criteria)[0][0]

    def countAlerts(self, criteria=None):
        return self._countMessages("alert", criteria)

    def countHeartbeats(self, criteria=None):
        return self._countMessages("heartbeat", criteria)

    def getAnalyzerids(self):
        analyzerids = [ ]
        rows = self.getValues([ "heartbeat.analyzer(-1).analyzerid/group_by" ])
        for row in rows:
            analyzerid = row[0]
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
        heartbeat = self.getHeartbeat(ident)

        path = []
        analyzer = {}
        analyzerd = { "path": path, "node_addresses": [], "node_name": None, "node_location": None }

        for a in heartbeat["analyzer"]:
            path.append(a["analyzerid"])
            analyzer = a

        for column in "analyzerid", "name", "model", "version", "class", "ostype", "osversion":
            analyzerd[column] = analyzer.get(column, None)

        analyzerd["node_name"] = analyzer.get("node.name")
        analyzerd["node_location"] = analyzer.get("node.location")

        for addr in analyzer.get("node.address.address", []):
            analyzerd["node_addresses"].append(addr)

        analyzerd["last_heartbeat_time"] = heartbeat.get("heartbeat.create_time")
        analyzerd["last_heartbeat_interval"] = heartbeat.get("heartbeat.heartbeat_interval")
        analyzerd["last_heartbeat_status"] = heartbeat.getAdditionalData("Analyzer status")

        return analyzerd
