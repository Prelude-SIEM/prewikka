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
            IDMEF_VALUE_TYPE_ENUM:          get_enum,
            IDMEF_VALUE_TYPE_TIME:          get_time
            }[idmef_value_get_type(value)](value)
    except KeyError:
        return None



class Message:
    def __init__(self, res):
        self._res = res

    def _get_raw_value(self, key):
        path = idmef_path_new_fast(key)
        idmef_value = idmef_path_get(path, self._res)
        if idmef_value is None:
            value = None
        else:
            value = convert_idmef_value(idmef_value)
            idmef_value_destroy(idmef_value)
        idmef_path_destroy(path)

        return value

    def __getitem__(self, key):
        if key.find("%s." % self._root) != 0:
            key = "%s." % self._root + key
        
        return escape_value(self._get_raw_value(key))
        
    def get(self, key, default=None, escape=True):
        if key.find("%s." % self._root) != 0:
            key = "%s." % self._root + key
        
        value = self._get_raw_value(key)
        if value is None:
            value = default
        
        if escape:
            value = escape_value(value)
            
        return value

    def getAdditionalData(self, searched, many_values=False, escape=True):
        values = [ ]
        i = 0
        while True:
            meaning = self["%s.additional_data(%d).meaning" % (self._root, i)]
            if meaning is None:
                break
            
            if meaning == searched:
                value = self.get("%s.additional_data(%d).data" % (self._root, i))
                
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



class Prelude:
    def __init__(self, config):
        settings = preludedb_sql_settings_new()
        for param in "host", "port", "name", "user", "password":
            if config.getOptionValue(param):
                preludedb_sql_settings_set(settings, param, config.getOptionValue(param))

        sql = preludedb_sql_new(config.getOptionValue("type", "mysql"), settings)
        if config.getOptionValue("log"):
            preludedb_sql_enable_query_logging(sql, config.getOptionValue("log"))

        self._db = preludedb_new(sql, None)

    def _getMessageIdents(self, get_message_idents, criteria, limit, offset):
        if type(criteria) is list:
            criteria = " && ".join(criteria)
        
        if criteria:
            criteria = idmef_criteria_new_from_string(criteria)

        idents = [ ]
        
        result = get_message_idents(self._db, criteria, limit, offset,
                                    PRELUDEDB_RESULT_IDENTS_ORDER_BY_CREATE_TIME_DESC)
        if result:
            while True:
                ident = preludedb_result_idents_get_next(result)
                if ident is None:
                    break
                idents.append(ident)
            preludedb_result_idents_destroy(result)

        if type(criteria) is list:
            criteria = " && ".join(criteria)
        
        if criteria:
            idmef_criteria_destroy(criteria)

        return idents        

    def getAlertIdents(self, criteria=None, limit=-1, offset=-1):
        return self._getMessageIdents(preludedb_get_alert_idents, criteria, limit, offset)

    def getHeartbeatIdents(self, criteria=None, limit=-1, offset=-1):
        return self._getMessageIdents(preludedb_get_heartbeat_idents, criteria, limit, offset)

    def _getLastMessageIdent(self, type, get_message_idents, analyzerid):
        criteria = None
        if analyzerid != None:
            criteria = "%s.analyzer.analyzerid == '%s'" % (type, str(analyzerid))

        idents = get_message_idents(criteria, limit=1)

        return idents[0]

    def getLastAlertIdent(self, analyzer=None):
        return self._getLastMessageIdent("alert", self.getAlertIdents, analyzer)

    def getLastHeartbeatIdent(self, analyzer=None):
        return self._getLastMessageIdent("heartbeat", self.getHeartbeatIdents, analyzer)

    def getAlert(self, ident):
        return Alert(preludedb_get_alert(self._db, ident))

    def deleteAlert(self, ident):
        preludedb_delete_alert(self._db, ident)

    def getHeartbeat(self, ident):
        return Heartbeat(preludedb_get_heartbeat(self._db, ident))

    def deleteHeartbeat(self, ident):
        preludedb_delete_heartbeat(self._db, ident)

    def getValues(self, selection, criteria=None, distinct=0, limit=-1, offset=-1):
        if type(criteria) is list:
            criteria = " && ".join(criteria)
        
        if criteria:
            criteria = idmef_criteria_new_from_string(criteria)

        my_selection = preludedb_path_selection_new()
        for selected in selection:
            my_selected = preludedb_selected_path_new_string(selected)
            preludedb_path_selection_add(my_selection, my_selected)

        rows = [ ]

        result = preludedb_get_values(self._db, my_selection, criteria, distinct, limit, offset)
        if result != None:
            while True:
                values = preludedb_result_values_get_next(result)
                if values is None:
                    break

                row = [ ]
                rows.append(row)
                for value in values:
                    if value is None:
                        row.append(None)
                    else:
                        row.append(convert_idmef_value(value))
                        idmef_value_destroy(value)
            preludedb_result_values_destroy(result)

        if criteria:
            idmef_criteria_destroy(criteria)
        
        preludedb_path_selection_destroy(my_selection)

        return rows

    def _countMessages(self, root, criteria):
        return self.getValues(["count(%s.create_time)" % root], criteria)[0][0]

    def countAlerts(self, criteria=None):
        return self._countMessages("alert", criteria)

    def countHeartbeats(self, criteria=None):
        return self._countMessages("heartbeat", criteria)

    def getAnalyzerids(self):
        analyzerids = [ ]
        rows = self.getValues(selection=[ "heartbeat.analyzer.analyzerid/group_by" ],
                              criteria="heartbeat.analyzer.analyzerid != 0")
        for row in rows:
            analyzerid = row[0]
            analyzerids.append(analyzerid)

        return analyzerids

    def getAnalyzerPaths(self):
        analyzer_paths = [ ]
        for analyzerid in self.getAnalyzerids():
            ident = self.getLastHeartbeatIdent(analyzerid)
            heartbeat = self.getHeartbeat(ident)
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

        index = 0
        while True:
            if not heartbeat["heartbeat.analyzer(%d).name" % (index + 1)]:
                break
            index += 1
        
        analyzer = { }
        analyzer["analyzerid"] = analyzerid
        analyzer["name"] = heartbeat.get("heartbeat.analyzer(%d).name" % index, "n/a")
        analyzer["model"] = heartbeat.get("heartbeat.analyzer(%d).model" % index, "n/a") 
        analyzer["version"] = heartbeat.get("heartbeat.analyzer(%d).version" % index, "n/a")
        analyzer["ostype"] = heartbeat.get("heartbeat.analyzer(%d).ostype" % index, "n/a")
        analyzer["osversion"] = heartbeat.get("heartbeat.analyzer(%d).osversion" % index, "n/a")
        analyzer["node_name"] = heartbeat.get("heartbeat.analyzer(%d).node.name" % index, "n/a")
        analyzer["node_location"] = heartbeat.get("heartbeat.analyzer(%d).node.location" % index, "n/a")
        analyzer["node_address"] = heartbeat.get("heartbeat.analyzer(%d).node.address(0).address" % index, "n/a")
        analyzer["last_heartbeat_time"] = heartbeat.get("heartbeat.create_time")
        analyzer["last_heartbeat_interval"] = heartbeat["heartbeat.heartbeat_interval"]
        analyzer["last_heartbeat_status"] = heartbeat.getAdditionalData("Analyzer status")
        
        return analyzer
