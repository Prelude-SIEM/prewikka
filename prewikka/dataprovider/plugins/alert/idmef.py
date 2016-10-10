# Copyright (C) 2016 CS-SI. All Rights Reserved.
# Author: Abdel ELMILI <abdel.elmili@c-s.fr>

from datetime import datetime

from prelude import IDMEFTime

from prewikka import pluginmanager, version, env, usergroup, utils
from prewikka.dataprovider import QueryResults, DataProviderBackend, QueryResultsRow


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


class IDMEFAlertPlugin(DataProviderBackend):
    type = "alert"
    plugin_name = "IDMEF Alerts Plugin"
    plugin_version = version.__version__
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_copyright = version.__copyright__
    plugin_description = N_("Plugin for fetching IDMEF alerts from the Prelude database")

    @usergroup.permissions_required(["IDMEF_VIEW"])
    def get_values(self, paths, criteria, distinct, limit, offset):
        # This method acts as a pass-through to libpreludedb.
        return IDMEFQueryResults(env.idmef_db.getValues(paths, criteria, distinct, limit, offset))
