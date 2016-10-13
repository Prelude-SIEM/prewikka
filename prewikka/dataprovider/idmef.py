# Copyright (C) 2016 CS-SI. All Rights Reserved.
# Author: Abdel ELMILI <abdel.elmili@c-s.fr>

import prelude
from prewikka import pluginmanager, version, utils
from prewikka.dataprovider import DataProviderNormalizer


class IDMEFNormalizer(DataProviderNormalizer):
    def parse_criterion(self, path, operator, value):
        if not(value) and operator in ("=", "==", "!"):
            if prelude.IDMEFPath(path).getValueType() == prelude.IDMEFValue.TYPE_STRING:
                 return "(! %s || %s == '')" % (path, path)

            return "! %s" % (path)

        return DataProviderNormalizer.parse_criterion(self, path, operator, value)


class _IDMEFProvider(pluginmanager.PluginBase):
    plugin_version = version.__version__
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_copyright = version.__copyright__
    normalizer = IDMEFNormalizer('create_time')


class IDMEFAlertProvider(_IDMEFProvider):
    plugin_name = "IDMEF Alert provider"
    plugin_description = N_("Provides an API to fetch IDMEF alerts")


class IDMEFHeartbeatProvider(_IDMEFProvider):
    plugin_name = "IDMEF Heartbeat provider"
    plugin_description = N_("Provides an API to fetch IDMEF heartbeats")
