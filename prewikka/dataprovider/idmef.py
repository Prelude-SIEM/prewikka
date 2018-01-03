# Copyright (C) 2016-2018 CS-SI. All Rights Reserved.
# Author: Abdel ELMILI <abdel.elmili@c-s.fr>

from __future__ import absolute_import, division, print_function, unicode_literals

import datetime
import prelude

from prewikka import utils, version
from prewikka.dataprovider import DataProviderBase


class _IDMEFProvider(DataProviderBase):
    plugin_version = version.__version__
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_copyright = version.__copyright__

    def __init__(self):
        DataProviderBase.__init__(self, "create_time")

    def get_path_type(self, path):
        _typemap = {
            prelude.IDMEFValue.TYPE_DATA: bytes,
            prelude.IDMEFValue.TYPE_STRING: text_type,
            prelude.IDMEFValue.TYPE_TIME: datetime.datetime,
            prelude.IDMEFValue.TYPE_FLOAT: float,
            prelude.IDMEFValue.TYPE_DOUBLE: float,
            prelude.IDMEFValue.TYPE_ENUM: text_type,
            prelude.IDMEFValue.TYPE_INT8: int,
            prelude.IDMEFValue.TYPE_UINT8: int,
            prelude.IDMEFValue.TYPE_INT16: int,
            prelude.IDMEFValue.TYPE_UINT16: int,
            prelude.IDMEFValue.TYPE_INT32: int,
            prelude.IDMEFValue.TYPE_UINT32: int,
            prelude.IDMEFValue.TYPE_INT64: int,
            prelude.IDMEFValue.TYPE_UINT64: int,
            prelude.IDMEFValue.TYPE_CLASS: object,
        }

        return _typemap[prelude.IDMEFClass(path).getValueType()]

    def _get_paths(self, rootcl):
        for node in rootcl:
            if node.getValueType() == prelude.IDMEFValue.TYPE_CLASS:
                for subnode in self._get_paths(node):
                    yield subnode
            else:
                yield node.getPath()

    @staticmethod
    def _value_adjust(operator, value):
        if operator not in ("<>*", "<>", "!<>", "!<>*"):
            return value

        value = value.strip()

        has_wildcard = utils.find_unescaped_characters(value, ["*"])
        if has_wildcard:
            return value

        return "*%s*" % value

    def criterion_to_string(self, path, operator, value):
        if not(value) and operator == "==":
            if prelude.IDMEFPath(path).getValueType() == prelude.IDMEFValue.TYPE_STRING:
                return "(! %s || %s == '')" % (path, path)

            return "! %s" % (path)

        return DataProviderBase.criterion_to_string(self, path, operator, self._value_adjust(operator, value))

    def compile_criteria(self, criteria):
        if criteria:
            return prelude.IDMEFCriteria(criteria.to_string(self.dataprovider_type))


class IDMEFAlertProvider(_IDMEFProvider):
    plugin_name = "IDMEF Alert provider"
    plugin_description = N_("Provides an API to fetch IDMEF alerts")
    dataprovider_label = N_("Alerts")

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
    dataprovider_label = N_("Heartbeats")

    def get_paths(self):
        return self._get_paths(prelude.IDMEFClass("heartbeat"))
