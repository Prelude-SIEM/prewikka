# Copyright (C) 2016 CS-SI. All Rights Reserved.
# Author: Abdel ELMILI <abdel.elmili@c-s.fr>

from datetime import datetime

from prelude import IDMEFTime

from prewikka import pluginmanager, version, env, usergroup, utils
from prewikka.dataprovider import QueryResults, DataProviderBackend


class IDMEFQueryResults(QueryResults):
    def _convert_values(self, row):
        res = []
        for elt in row:
            if isinstance(elt, IDMEFTime):
                elt = datetime.fromtimestamp(elt, utils.timeutil.tzoffset(None, elt.getGmtOffset()))

            res.append(elt)

        return res


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
        results = env.idmef_db.getValues(paths, criteria, distinct, limit, offset)
        return IDMEFQueryResults(rows=results)
