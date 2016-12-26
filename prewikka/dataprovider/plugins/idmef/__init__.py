# Copyright (C) 2016 CS-SI. All Rights Reserved.
# Author: Abdel ELMILI <abdel.elmili@c-s.fr>

from __future__ import absolute_import, division, print_function, unicode_literals

from datetime import datetime

import preludedb
from prelude import IDMEFTime, IDMEFValue
from prewikka import env, pluginmanager, usergroup, utils, version
from prewikka.dataprovider import DataProviderBackend, QueryResults, QueryResultsRow, ResultObject

_ORDER_MAP = { "time_asc": preludedb.DB.ORDER_BY_CREATE_TIME_ASC, "time_desc": preludedb.DB.ORDER_BY_CREATE_TIME_DESC }


class IDMEFResultObject(ResultObject):
    def preprocess_value(self, value):
        if isinstance(value, IDMEFTime):
            return datetime.fromtimestamp(value, utils.timeutil.tzoffset(None, value.getGmtOffset()))

        return ResultObject.preprocess_value(self, value)


class IDMEFQueryResultsRow(QueryResultsRow):
    __slots__ = ()

    def preprocess_value(self, value):
        if isinstance(value, IDMEFTime):
            return datetime.fromtimestamp(value, utils.timeutil.tzoffset(None, value.getGmtOffset()))

        return QueryResultsRow.preprocess_value(self, value)


class IDMEFQueryResults(QueryResults):
    __slots__ = ()

    def preprocess_value(self, value):
        return IDMEFQueryResultsRow(self, value)


class _IDMEFPlugin(DataProviderBackend):
    plugin_version = version.__version__
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_copyright = version.__copyright__

    def _iterate_object(self, results):
        for ident in results:
            res = IDMEFResultObject(self._get_object(ident))
            res.ident = ident

            yield res

    def update(self, data, criteria):
        paths, values = zip(*data)
        env.idmef_db.update(list(paths), [IDMEFValue(v) for v in values], criteria)

    def get(self, criteria, order_by, limit, offset):
        results = self._get_idents(criteria, limit, offset, _ORDER_MAP[order_by])
        return utils.CachingIterator(self._iterate_object(results))

    @usergroup.permissions_required(["IDMEF_VIEW"])
    def get_values(self, paths, criteria, distinct, limit, offset):
        return IDMEFQueryResults(env.idmef_db.getValues(paths, criteria, bool(distinct), limit, offset))

    @usergroup.permissions_required(["IDMEF_ALTER"])
    def delete(self, criteria, paths):
        env.idmef_db.remove(criteria)
        env.log.info("Deleted alerts with criteria \"{0}\"".format(criteria))


class IDMEFAlertPlugin(_IDMEFPlugin):
    type = "alert"
    plugin_name = "IDMEF Alert Plugin"
    plugin_description = N_("Plugin for fetching IDMEF messages from the Prelude database")

    @property
    def _get_object(self):
        return env.idmef_db.getAlert

    @property
    def _get_idents(self):
        return env.idmef_db.getAlertIdents


class IDMEFHeartbeatPlugin(_IDMEFPlugin):
    type = "heartbeat"
    plugin_name = "IDMEF Heartbeat Plugin"
    plugin_description = N_("Plugin for fetching IDMEF heartbeat from the Prelude database")

    @property
    def _get_object(self):
        return env.idmef_db.getHeartbeat

    @property
    def _get_idents(self):
        return env.idmef_db.getHeartbeatIdents
