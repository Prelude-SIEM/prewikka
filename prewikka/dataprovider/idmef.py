# Copyright (C) 2016 CS-SI. All Rights Reserved.
# Author: Abdel ELMILI <abdel.elmili@c-s.fr>

from __future__ import absolute_import, division, print_function, unicode_literals

import prelude
from prewikka import pluginmanager, utils, version
from prewikka.dataprovider import DataProviderNormalizer


class IDMEFNormalizer(DataProviderNormalizer):

    @staticmethod
    def _value_adjust(operator, value):
        if operator not in ("<>*", "<>"):
            return value

        value = value.strip()

        has_wildcard = utils.find_unescaped_characters(value, ["*"])
        if has_wildcard:
            return value

        return "*%s*" % value

    def parse_criterion(self, path, operator, value, type):
        if not(value) and operator in ("=", "==", "!"):
            if prelude.IDMEFPath(path).getValueType() == prelude.IDMEFValue.TYPE_STRING:
                 return "(! %s || %s == '')" % (path, path)

            return "! %s" % (path)

        return DataProviderNormalizer.parse_criterion(self, path, operator, self._value_adjust(operator, value), type)


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
