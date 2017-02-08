# Copyright (C) 2016-2017 CS-SI. All Rights Reserved.
# Author: Abdel ELMILI <abdel.elmili@c-s.fr>

from __future__ import absolute_import, division, print_function, unicode_literals

import prelude
from prewikka import utils, version
from prewikka.dataprovider import DataProviderNormalizer, DataProviderBase


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


class _IDMEFProvider(DataProviderBase):
    plugin_version = version.__version__
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_copyright = version.__copyright__
    normalizer = IDMEFNormalizer('create_time')

    def get_path_type(self, path):
        return prelude.IDMEFClass(path).getValueType()

    def _get_paths(self, rootcl):
        for node in rootcl:
            if node.getValueType() == prelude.IDMEFValue.TYPE_CLASS:
                for subnode in self._get_paths(node):
                    yield subnode
            else:
                yield node.getPath()


class IDMEFAlertProvider(_IDMEFProvider):
    plugin_name = "IDMEF Alert provider"
    plugin_description = N_("Provides an API to fetch IDMEF alerts")
    label = N_("Alerts")

    def get_paths(self):
        return self._get_paths(prelude.IDMEFClass("alert"))

    def get_common_paths(self, index=False):
        return [
            (N_("Classification"), "alert.classification.text"),
            (N_("Source IP"), "alert.source(0).node.address(0).address" if index else "alert.source.node.address.address"),
            (N_("Source port"), "alert.source(0).service.port" if index else "alert.source.service.port"),
            (N_("Target IP"), "alert.target(0).node.address(0).address" if index else "alert.target.node.address.address"),
            (N_("Target port"), "alert.target(0).service.port" if index else "alert.target.service.port"),
            (N_("Analyzer name"), "alert.analyzer(-1).name" if index else "alert.analyzer.name")
        ]


class IDMEFHeartbeatProvider(_IDMEFProvider):
    plugin_name = "IDMEF Heartbeat provider"
    plugin_description = N_("Provides an API to fetch IDMEF heartbeats")
    label = N_("Heartbeats")

    def get_paths(self):
        return self._get_paths(prelude.IDMEFClass("heartbeat"))
