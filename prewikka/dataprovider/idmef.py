# Copyright (C) 2016-2018 CS-SI. All Rights Reserved.
# Author: Abdel ELMILI <abdel.elmili@c-s.fr>

from __future__ import absolute_import, division, print_function, unicode_literals

import datetime
import prelude

from prewikka import utils, version
from prewikka.dataprovider import DataProviderBase, Criterion, InvalidCriterionError, InvalidPathError


class _IDMEFPath(prelude.IDMEFPath):
    def __init__(self, path):
        try:
            prelude.IDMEFPath.__init__(self, path)
        except RuntimeError as e:
            raise InvalidPathError(path, details=e)


class _IDMEFCriterion(prelude.IDMEFCriteria):
    def __init__(self, criteria):
        try:
            prelude.IDMEFCriteria.__init__(self, criteria)
        except RuntimeError as e:
            raise InvalidCriterionError(details=e)


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

    @staticmethod
    def _path_adjust(path):
        """
        Automatically add indexes to IDMEF listed fields
        FIXME: to be removed when libpreludedb supports != for listed fields
        """
        fields = []
        for elem in path.split("."):
            p = ".".join(fields + [elem])

            if elem == "analyzer":
                fields.append("%s(-1)" % elem)
            elif _IDMEFPath(p).isAmbiguous():
                fields.append("%s(0)" % elem)
            else:
                fields.append(elem)

        return ".".join(fields)

    def compile_criterion(self, criterion):
        if criterion.right:
            criterion.right = self._value_adjust(criterion.operator, criterion.right)

        elif criterion.operator == "==":
            criterion = Criterion(criterion.left, "==", None)
            if _IDMEFPath(criterion.left).getValueType() == prelude.IDMEFValue.TYPE_STRING:
                criterion |= Criterion(criterion.left, "==", "''")

        if criterion.operator.startswith("!") and _IDMEFPath(criterion.left).isAmbiguous():
            criterion.left = self._path_adjust(criterion.left)

        return DataProviderBase.compile_criterion(self, criterion)

    def compile_criteria(self, criteria):
        if criteria:
            return _IDMEFCriterion(criteria.to_string())


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
