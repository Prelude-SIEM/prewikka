# Copyright (C) 2016 CS-SI. All Rights Reserved.
# Author: Abdel ELMILI <abdel.elmili@c-s.fr>

from prewikka import pluginmanager, version, env, dataprovider, usergroup


class IDMEFAlertPlugin(dataprovider.DataProviderBackend):
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
        return dataprovider.QueryResults(rows=results)
