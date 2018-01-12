# Copyright (C) 2004-2018 CS-SI. All Rights Reserved.
# Author: Nicolas Delon <nicolas.delon@prelude-ids.com>
# Author: Yoann Vandoorselaere <yoannv@gmail.com>
#
# This file is part of the Prewikka program.
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
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from __future__ import absolute_import, division, print_function, unicode_literals

import copy
import datetime
import functools
import itertools
import re
import sys
import prelude

from prewikka import crontab, hookmanager, localization, resource, template, utils, view
from prewikka.dataprovider import Criterion

from .messagelisting import AttrDict, ListedMessage, MessageListing, MessageListingParameters

if sys.version_info >= (3, 0):
    from urllib.parse import quote
else:
    from urllib import quote


def cmp_severities(x, y):
    d = {None: 0, "info": 1, "low": 2, "medium": 3, "high": 4}
    return d[y] - d[x]


def _normalizeName(name):
    return "".join([i.capitalize() for i in name.split("_")])


COLUMN_LIST = [
    "classification",
    "source",
    "target",
    "analyzer"
]

CLASSIFICATION_GENERIC_SEARCH_FIELDS = [
    "alert.classification.text",
    "alert.classification.reference.name"
]

SOURCE_GENERIC_SEARCH_FIELDS = [
    "alert.source.node.address.address",
    "alert.source.node.name",
    "alert.source.user.user_id.name",
    "alert.source.user.user_id.number",
    "alert.source.process.name",
    "alert.source.process.pid",
    "alert.source.service.protocol",
    "alert.source.service.iana_protocol_name",
    "alert.source.service.iana_protocol_number",
    "alert.source.service.port"
]

TARGET_GENERIC_SEARCH_FIELDS = [
    "alert.target.node.address.address",
    "alert.target.node.name",
    "alert.target.user.user_id.number",
    "alert.target.user.user_id.name",
    "alert.target.process.name",
    "alert.target.process.pid",
    "alert.target.service.protocol",
    "alert.target.service.iana_protocol_name",
    "alert.target.service.iana_protocol_number",
    "alert.target.service.port"
]

ANALYZER_GENERIC_SEARCH_FIELDS = ["alert.analyzer.name", "alert.analyzer.node.name"]

GENERIC_SEARCH_TABLE = {
    "classification": CLASSIFICATION_GENERIC_SEARCH_FIELDS,
    "source": SOURCE_GENERIC_SEARCH_FIELDS,
    "target": TARGET_GENERIC_SEARCH_FIELDS,
    "analyzer": ANALYZER_GENERIC_SEARCH_FIELDS
}


class AlertListingParameters(MessageListingParameters):
    allow_extra_parameters = True

    def _get_aggregated_alert(self, ident):
        aggreg_type = ""

        alert = env.dataprovider.get(criteria=Criterion("alert.messageid", "=", ident))[0]["alert"]
        if alert["correlation_alert"]:
            aggreg_type = "correlation_alert"

        elif alert["tool_alert"]:
            aggreg_type = "tool_alert"

        return alert, aggreg_type

    def __init__(self, *args, **kwargs):
        MessageListingParameters.__init__(self, *args, **kwargs)
        self._dynamic_param = {"classification": {}, "source": {}, "target": {}, "analyzer": {}}
        self._default_param = {"classification": {}, "source": {}, "target": {}, "analyzer": {}}
        self._saved = {"classification": [], "source": [], "target": [], "analyzer": []}
        self._linked_alerts = []

        if "aggregated_alert_id" in self:
            alert, aggreg_type = self._get_aggregated_alert(self.get("aggregated_alert_id"))
            for alertident in alert[aggreg_type]["alertident"]:
                self._linked_alerts.append("alert.messageid=%s" % alertident["alertident"])

    def register(self):
        self.max_index = 0
        MessageListingParameters.register(self)
        self.optional("aggregated_source", list, ["alert.source(0).node.address(0).address"], save=True)
        self.optional("aggregated_target", list, ["alert.target(0).node.address(0).address"], save=True)
        self.optional("aggregated_classification", list, ["none"], save=True)
        self.optional("aggregated_analyzer", list, ["none"], save=True)
        self.optional("alert.assessment.impact.severity", list, ["info", "low", "medium", "high", "n/a"], save=True)
        self.optional("alert.assessment.impact.completion", list, ["succeeded", "failed", "n/a"], save=True)
        self.optional("alert.type", list, ["alert.create_time", "alert.correlation_alert.name", "alert.overflow_alert.program", "alert.tool_alert.name"], save=True)

    def _checkOperator(self, operator):
        if operator not in ("=", "==", "<", ">", "<=", ">=", "~", "~*", "<>", "<>*", "!"):
            raise view.InvalidParameterValueError("operator", operator)

    def _check_value(self, obj, operator, value):
        if operator != "!" and obj != "__all__":
            try:
                Criterion(obj, operator, value).compile("alert")
            except RuntimeError:
                raise view.InvalidParameterValueError(obj, value)

    def _setParam(self, view_name, user, column, param, value, is_default=False):
        self._dynamic_param[column][param] = value

        if is_default:
            self._default_param[column][param] = value
            user.set_property(param, value, view=view_name)

        elif view_name in user.configuration and param in user.configuration[view_name] and user.configuration[view_name][param] != value:
            self._default_param[column][param] = value

        if param not in self:
            # the parameter is loaded from config
            self[param] = value

    def _paramDictToList(self, params_dict, column):
        sorted = []
        ret = False

        for parameter, obj in params_dict.items():
            idx = parameter.find(column + "_object_")
            if idx == -1:
                continue

            num = int(parameter.replace(column + "_object_", "", 1))
            if num >= self.max_index:
                self.max_index = num + 1

            ret = True
            operator = params_dict.get(column + "_operator_" + text_type(num), "=")
            self._checkOperator(operator)

            try:
                value = params_dict[column + "_value_" + text_type(num)]
            except KeyError:
                if operator != "!":
                    continue
                value = ""

            self._check_value(obj, operator, value)

            do_append = True
            for tmp in sorted:
                if tmp[1] == obj and tmp[2] == operator and tmp[3] == value:
                    do_append = False
                    break

            if do_append:
                sorted.append((num, obj, operator, value))

        sorted.sort()
        return ret, sorted

    def _loadColumnParam(self, view_name, user, paramlist, column, do_save):
        if do_save:
            paramlist = copy.copy(paramlist)

        self[column] = []
        ret, sorted = self._paramDictToList(paramlist, column)

        if do_save:
            user.del_property_match("%s_object_" % column, view=view_name)
            user.del_property_match("%s_operator_" % column, view=view_name)
            user.del_property_match("%s_value_" % column, view=view_name)

        for i in sorted:
            self._setParam(view_name, user, column, "%s_object_%d" % (column, i[0]), i[1], is_default=do_save)
            self._setParam(view_name, user, column, "%s_operator_%d" % (column, i[0]), i[2], is_default=do_save)
            self._setParam(view_name, user, column, "%s_value_%d" % (column, i[0]), i[3], is_default=do_save)
            self[column].append(i[1:])

        return ret

    def normalize(self, view_name, user):
        MessageListingParameters.normalize(self, view_name, user)
        do_save = env.request.web.method in ("POST", "PUT", "PATCH")

        for severity in self["alert.assessment.impact.severity"]:
            if severity not in ("info", "low", "medium", "high", "n/a"):
                raise view.InvalidParameterValueError("alert.assessment.impact.severity", severity)

        for completion in self["alert.assessment.impact.completion"]:
            if completion not in ("succeeded", "failed", "n/a"):
                raise view.InvalidParameterValueError("alert.assessment.impact.completion", completion)

        for type in self["alert.type"]:
            if type not in ("alert.create_time", "alert.correlation_alert.name", "alert.overflow_alert.program", "alert.tool_alert.name"):
                raise view.InvalidParameterValueError("alert.type", type)

        load_saved = True
        for column in "classification", "source", "target", "analyzer":
            ret = self._loadColumnParam(view_name, user, self, column, do_save)
            if ret:
                load_saved = False

        if load_saved and view_name in user.configuration:
            for column in "classification", "source", "target", "analyzer":
                self._loadColumnParam(view_name, user, user.configuration[view_name], column, do_save)

        for column in COLUMN_LIST:
            if view_name in user.configuration:
                for i in self._paramDictToList(user.configuration[view_name], column)[1]:
                    self._saved[column].append(i[1:])

                for i in user.configuration[view_name].keys():
                    if i.find(column + "_object_") != -1 or i.find(column + "_operator_") != -1 or i.find(column + "_value_") != -1:
                        self._default_param[column][i] = user.configuration[view_name][i]

            i = 0
            for path in self["aggregated_%s" % column]:
                if list(self["aggregated_%s" % column]).count(path) > 1:
                    self["aggregated_%s" % column].remove(path)

                if path[0] == "!":
                    self["aggregated_%s" % column][i] = path[1:]

                i += 1

    def getDefaultParams(self, column):
        return self._default_param[column]

    def getDynamicParams(self, column):
        return self._dynamic_param[column]

    def _isSaved(self, column, param):
        if param not in self._default_param[column]:
            return False

        if param not in self:
            return False

        if self._default_param[column][param] == self[param]:
            return True

        return False

    def isSaved(self, column, param):
        if self._isSaved(column, param):
            return True

        return MessageListingParameters.isSaved(self, param)


class CorrelationAlertListingParameters(AlertListingParameters):
    def register(self):
        AlertListingParameters.register(self)
        self.optional("aggregated_source", list, ["none"], save=True)
        self.optional("aggregated_target", list, ["none"], save=True)
        self.optional("alert.type", list, ["alert.correlation_alert.name"], save=True)


class ListedAlert(ListedMessage):
    def __init__(self, *args, **kwargs):
        ListedMessage.__init__(self, *args, **kwargs)
        self.reset()

        self._max_aggregated_source = env.config.general.get_int("max_aggregated_source", 3)
        self._max_aggregated_target = env.config.general.get_int("max_aggregated_target", 3)

    def _getKnownValue(self, direction, key):
        return {
            "alert.%s.service.port" % direction: ("service", None),
            "alert.%s.node.address.address" % direction: ("addresses", self._setMessageDirectionAddress),
            "alert.%s.node.name" % direction: ("addresses", self._setMessageDirectionNodeName),
        }[key]

    def _initValue(self, dataset, name, value):
        dataset[name] = value

    def _initDirection(self, dataset):
        self._initValue(dataset, "port", AttrDict(value=None))
        self._initValue(dataset, "protocol", AttrDict(value=None))
        self._initValue(dataset, "service", AttrDict(value=None, inline_filter=None, already_filtered=False))
        self._initValue(dataset, "addresses", [])
        self._initValue(dataset, "listed_values", [])
        self._initValue(dataset, "aggregated_hidden", 0)
        return dataset

    def _initDirectionIfNeeded(self, direction):
        if len(self[direction]) == 0:
            self[direction].append(self._initDirection(AttrDict()))

    def _setMainAndExtraValues(self, dataset, name, object_main, object_extra):
        if object_main is not None:
            dataset[name] = AttrDict(value=object_main)
            dataset[name + "_extra"] = AttrDict(value=object_extra)

        else:
            dataset[name] = AttrDict(value=object_extra)
            dataset[name + "_extra"] = AttrDict(value=None)

    def _guessAddressCategory(self, address):
        if re.compile("\d\.\d\.\d\.\d").match(address):
            return "ipv4-addr"

        elif re.compile(".*@.*").match(address):
            return "e-mail"

        elif address.count(":") > 1:
            return "ipv6-addr"

        return None

    def _setMessageDirectionAddress(self, dataset, direction, address, category=None):
        if (category is None or category == "unknown") and address:
            category = self._guessAddressCategory(address)

        dns = "no_dns" not in dataset
        hfield = self.createHostField("alert.%s.node.address.address" % direction, address,
                                      category=category, direction=direction, dns=dns)
        dataset["addresses"].append(hfield)

    def _setMessageDirectionNodeName(self, dataset, direction, name):
        dataset["no_dns"] = True
        dataset["addresses"].append(self.createHostField("alert.%s.node.name" % direction, name, direction=direction))

    def _setMessageDirectionOther(self, dataset, direction, path, value, extra_path=None, extra=None, allow_empty_value=False):
        if path == "__all__":
                return

        if value is None:
            if allow_empty_value is False and extra is None:
                return

            if extra is not None:
                value = extra
                path = extra_path
                extra = None

        l = path.split(".")
        l[-2] = l[-2].replace("(0)", "")

        if l[-2] != direction:
            name = _normalizeName(l[-2]) + " "
        else:
            name = ""

        name += l[-1]

        item = (name, self.createInlineFilteredField(path, value, direction, real_value=value or "n/a"), extra)
        if item not in dataset["listed_values"]:
            dataset["listed_values"].append(item)

    def _setMessageDirection(self, dataset, direction, obj):
        dataset["interface"] = AttrDict(value=obj["interface"])

        for userid in obj["user.user_id"]:
            self._setMessageDirectionOther(dataset, direction, "alert.%s.user.user_id.name" % direction, userid["name"],
                                                               "alert.%s.user.user_id.number" % direction, userid["number"])

        name = obj["node.name"]
        if name is not None:
            self._setMessageDirectionNodeName(dataset, direction, name)

        for addr in obj["node.address"]:
            self._setMessageDirectionAddress(dataset, direction, addr["address"], addr["category"])

        self._setMessageDirectionOther(dataset, direction, "alert.%s.process.name" % direction, obj["process.name"],
                                                           "alert.%s.process.pid" % direction, extra=obj["process.pid"])

        pl = []
        vl = []

        proto = None
        if obj["service.iana_protocol_name"]:
            proto = obj["service.iana_protocol_name"]
            pl.append("alert.%s.service.iana_protocol_name" % direction)
            vl.append(proto)

        elif obj["service.iana_protocol_number"]:
            num = obj["service.iana_protocol_number"]
            proto = utils.protocol_number_to_name(num)
            pl.append("alert.%s.service.iana_protocol_number" % direction)
            vl.append(num)

        if not proto and obj["service.protocol"]:
            proto = obj["service.protocol"]
            pl.append("alert.%s.service.protocol" % direction)
            vl.append(proto)

        pstr = None
        if proto or obj["service.port"]:
            if obj["service.port"]:
                pl.append("alert.%s.service.port" % direction)
                vl.append(obj["service.port"])
                pstr = text_type(obj["service.port"])
                if proto:
                    pstr += "/" + proto
            elif proto:
                pstr = proto

        dataset["service"] = self.createInlineFilteredField(pl, vl, direction, real_value=pstr)
        self._setMainAndExtraValues(dataset, "protocol", proto, None)
        self._setMainAndExtraValues(dataset, "port", obj["service.port"], None)

        dataset["files"] = []

    def _lookupDataset(self, dlist, dataset):
        for dset in dlist:
            if dset.items() == dataset.items():
                return dset

        return None

    def _setMessageSource(self, message, ident):
        total = 0
        index = 0
        for source in message["alert.source"]:
            dataset = AttrDict()
            self._initDirection(dataset)
            self._setMessageDirection(dataset, "source", source)

            if not self._lookupDataset(self["source"], dataset):
                total += 1
                if self._source_index == self._max_aggregated_source:
                        continue

                index += 1
                self._source_index += 1
                self["source"].append(dataset)

        if total == 0:
            self._initDirectionIfNeeded("source")
            self._setMessageDirectionAddress(self["source"][-1], "source", None)

        self["aggregated_source_total"] += total
        self["aggregated_source_hidden"] += (total - index)

        if message["alert.correlation_alert.name"]:
            self["aggregated_source_expand"] = self["sub_alert_display"]
        else:
            self["aggregated_source_expand"] = url_for("AlertSummary", messageid=ident)

    def _setMessageTarget(self, message, ident):
        index = 0
        total = 0

        for target in message["alert.target"]:
            dataset = AttrDict()
            self._initDirection(dataset)
            self._setMessageDirection(dataset, "target", target)

            flist = []
            for f in target["file"]:
                if f["path"] in flist:
                    continue

                flist.append(f["path"])
                self._setMessageDirectionOther(dataset, "target", "alert.target.file.path", f["path"])

            if not self._lookupDataset(self["target"], dataset):
                total += 1
                if self._target_index == self._max_aggregated_target:
                        continue

                index += 1
                self._target_index += 1
                self["target"].append(dataset)

        if total == 0:
            self._initDirectionIfNeeded("target")
            self._setMessageDirectionAddress(self["target"][-1], "target", None)

        self["aggregated_target_total"] += total
        self["aggregated_target_hidden"] += (total - index)

        if message["alert.correlation_alert.name"]:
            self["aggregated_target_expand"] = self["sub_alert_display"]
        else:
            self["aggregated_target_expand"] = url_for("AlertSummary", messageid=ident)

    def _setMessageClassificationReferences(self, dataset, message):
        dataset["classification_references"] = []
        for ref in message["alert.classification.reference"]:
            pl = []
            vl = []
            fstr = ""

            origin = ref["origin"]
            if origin:
                pl.append("alert.classification.reference.origin")
                vl.append(origin)
                fstr += origin

            name = ref["name"]
            if name:
                pl.append("alert.classification.reference.name")
                vl.append(name)
                fstr += ":" + name

            urlstr = "%s?origin=%s&name=%s" % (env.reference_details_url, quote(ref["origin"]), quote(ref["name"]))
            if ref["origin"] in ("vendor-specific", "user-specific"):
                urlstr += "&url=" + quote(ref["url"], safe=b"")

            fstr = self.createInlineFilteredField(pl, vl, "classification", fstr)
            dataset["classification_references"].append((urlstr, fstr))

    def _setMessageClassificationURL(self, dataset, classification):
        dataset["classification_url"] = []
        if "classification" in env.url:
            for urlname, url in env.url["classification"].items():
                dataset["classification_url"].append((_(urlname), url.replace("$classification", classification)))

    def _setMessageClassification(self, dataset, message):
        self._setMessageClassificationReferences(dataset, message)
        self._setMessageClassificationURL(dataset, message["alert.classification.text"])
        dataset["classification"] = self.createInlineFilteredField("alert.classification.text", message["alert.classification.text"], "classification")

    def _setMessageAlertIdentInfo(self, message, alert, ident):
        self["sub_alert_number"] = len(alert["alertident"])
        self["sub_alert_name"] = alert["name"]
        self["sub_alert_link"] = url_for("AlertSummary", messageid=ident)

        params = {}
        params["timeline_unit"] = "unlimited"
        params["aggregated_source"] = params["aggregated_target"] = params["aggregated_classification"] = params["aggregated_analyzer"] = "none"
        params["aggregated_alert_id"] = ident
        self["sub_alert_display"] = url_for("AlertListing", **params)

    def _setClassificationInfos(self, dataset, message, ident):
        dataset["count"] = 1
        dataset["severity"] = AttrDict(value=message["alert.assessment.impact.severity"])
        dataset["links"] = [resource.HTMLNode("a", _("Alert details"), href=url_for("AlertSummary", messageid=ident))]
        dataset["links"] += list(hookmanager.trigger("HOOK_MESSAGEID_LINK", ident))

        dataset["completion"] = self.createInlineFilteredField("alert.assessment.impact.completion", message["alert.assessment.impact.completion"])
        dataset["description"] = message["alert.assessment.impact.description"]

    def _setMessageTimeURL(self, t, host):
        ret = []

        if "time" in env.url and t:
            epoch = datetime.datetime.utcfromtimestamp(0).replace(tzinfo=utils.timeutil.tzutc())
            t = text_type(int((t - epoch).total_seconds() * 1000))

            for urlname, url in env.url["time"].items():
                url = url.replace("$time", t)
                if host:
                    url = url.replace("$host", host)
                ret.append((_(urlname), url))

        return ret

    def _setMessageTime(self, message):
        self["time"] = self.createTimeField(message["alert.create_time"])
        self["time"]["time_url"] = self._setMessageTimeURL(message["alert.analyzer_time"], message["alert.analyzer(-1).node.name"])
        if message["alert.analyzer_time"] is not None and abs((message["alert.create_time"] - message["alert.analyzer_time"]).total_seconds()) > 60:
            self["analyzer_time"] = self.createTimeField(message["alert.analyzer_time"])
        else:
            self["analyzer_time"] = AttrDict(value=None)

    def addSensor(self, message):
        sensor = AttrDict()
        self["sensors"].append(sensor)

        for path in ("alert.analyzer(-1).name", "alert.analyzer(-1).model"):
                val = message[path]
                if val:
                        sensor["name"] = self.createInlineFilteredField(path, val, direction="analyzer")
                        break
        if not val:
                sensor["name"] = self.createInlineFilteredField("alert.analyzer(-1).name", val, direction="analyzer")

        sensor["node.name"] = self.createInlineFilteredField("alert.analyzer(-1).node.name", message["alert.analyzer(-1).node.name"], direction="analyzer")

    def setMessage(self, message, ident, extra_link=True):
        self["infos"] = [AttrDict()]
        self["aggregated"] = False
        self["selection"] = Criterion("alert.messageid", "=", ident)

        self.addSensor(message)
        self._setMessageTime(message)

        dataset = self["infos"][0]
        self._setClassificationInfos(dataset, message, ident)
        self._setMessageClassification(dataset, message)

        if message["alert.correlation_alert"]:
            self["sub_alert_type"] = _("Correlation Alert")
            self._setMessageAlertIdentInfo(message, message["alert.correlation_alert"], ident)

        elif message["alert.tool_alert"]:
            self["sub_alert_type"] = _("Tool Alert")
            self._setMessageAlertIdentInfo(message, message["alert.tool_alert"], ident)

        if not self["source"]:
            self._setMessageSource(message, ident)

        if not self["target"]:
            self._setMessageTarget(message, ident)

        classification = message.get("alert.classification.text", "")
        source_address = message.get("alert.source(0).node.address(0).address", "")
        target_address = message.get("alert.target(0).node.address(0).address", "")
        ctime = message["alert.create_time"]

        if extra_link:
            param = {
                'classification': [classification],
                'source': source_address,
                'target': target_address,
                'time_min': ctime,
                'time_max': ctime
            }
            self["extra_link"] = filter(lambda x: x is not None, hookmanager.trigger("HOOK_MESSAGELISTING_EXTRA_LINK", param))

    def setMessageDirectionGeneric(self, direction, object, value, allow_empty_value=True):
        self._initDirectionIfNeeded(direction)
        dataset = self[direction][-1]

        try:
            dset_name, function = self._getKnownValue(direction, object.replace("(0)", ""))
        except KeyError:
            return self._setMessageDirectionOther(dataset, direction, object, value, allow_empty_value=allow_empty_value)

        if function:
            function(dataset, direction, value)
        else:
            if type(dataset[dset_name]) is list:
                dataset[dset_name].append(AttrDict(value=value))
            else:
                dataset[dset_name]["value"] = value

    def reset(self):
        self["sensors"] = []
        self["source"] = []
        self["target"] = []
        self["sub_alert_name"] = None
        self["aggregated_source_total"] = 0
        self["aggregated_source_hidden"] = 0
        self["aggregated_source_expand"] = 0
        self["aggregated_target_total"] = 0
        self["aggregated_target_hidden"] = 0
        self["aggregated_target_expand"] = 0
        self._source_index = 0
        self._target_index = 0


class ListedAggregatedAlert(ListedAlert):
    def __init__(self, *args, **kwargs):
        ListedAlert.__init__(self, *args, **kwargs)

        self["aggregated"] = True
        self["aggregated_classification_hidden"] = 0
        self["infos"] = []
        self["source"] = []
        self["target"] = []

    def setTime(self, time_min, time_max):
        self["time_min"] = self.createTimeField(time_min)
        self["time_max"] = self.createTimeField(time_max)

    def setCriteriaForSelection(self, select_criteria):
        self["selection"] = select_criteria

    def setInfos(self, count, classification, severity, completion):
        infos = AttrDict(
            classification_references="",
            classification_url="",
            count=count,
            description="",
            classification=self.createInlineFilteredField("alert.classification.text",
                                                          classification, direction="classification"),
            severity=AttrDict(value=severity),
            completion=self.createInlineFilteredField("alert.assessment.impact.completion", completion))

        self._setMessageClassificationURL(infos, classification)

        self["infos"].append(infos)

        return infos


class AlertListing(MessageListing):
    view_menu = (N_("Alerts"), N_("Alerts"))
    view_parameters = AlertListingParameters
    view_permissions = [N_("IDMEF_VIEW")]
    view_template = template.PrewikkaTemplate(__name__, "templates/alertlisting.mak")
    view_datatype = "alert"
    view_help = "#alerts"

    root = "alert"
    listed_alert = ListedAlert
    listed_aggregated_alert = ListedAggregatedAlert
    alert_type_default = [
        "alert.create_time",
        "alert.correlation_alert.name",
        "alert.overflow_alert.program",
        "alert.tool_alert.name"
    ]

    def __init__(self):
        MessageListing.__init__(self)
        self._max_aggregated_classification = env.config.general.get_int("max_aggregated_classification", 10)

    def _setMessage(self, message, ident):
        msg = self.listed_alert(self.view_path, env.request.parameters)
        msg.setMessage(message, ident)
        msg["aggregated"] = False
        msg["selection"] = Criterion("alert.messageid", "=", ident)

        return msg

    def _applyOptionalEnumFilter(self, criteria, column, object, values, objpath=None, unsetval="n/a"):
        obj = env.request.parameters.get(object)

        if obj and set(obj) != set(values):
            new = Criterion()
            for value in obj:
                new |= Criterion(objpath or object, "=", value if value != unsetval else None)

            criteria += new
            env.request.dataset[object] = obj
        else:
            env.request.dataset[object] = values

    def _applyAlertTypeFilters(self, criteria):
        if "alert.create_time" in env.request.parameters["alert.type"]:
            have_base = True
        else:
            have_base = False

        new = Criterion()

        for param in ["alert.correlation_alert.name", "alert.overflow_alert.program", "alert.tool_alert.name"]:
            if not have_base:
                if param in env.request.parameters["alert.type"]:
                    new |= Criterion(param, "!=", None)
            else:
                if param not in env.request.parameters["alert.type"]:
                    new &= Criterion(param, "=", None)

        env.request.dataset["alert.type"] = env.request.parameters["alert.type"]
        criteria += new

    def _applyClassificationFilters(self, criteria):
        self._applyAlertTypeFilters(criteria)

        self._applyOptionalEnumFilter(criteria, "classification", "alert.assessment.impact.severity",
                                      ["info", "low", "medium", "high", "n/a"])

    def _filterTupleToString(self, filtertpl):
        return Criterion(*filtertpl)

    def _getOperatorForPath(self, path, value):
        # Check whether the path can handle substring comparison
        # this need to be done first, since enum check with * won't work with "=" operator.
        try:
            Criterion(path, "<>*", value).compile("alert")
        except:
            # Check whether this path can handle the provided value.
            try:
                Criterion(path, "=", value).compile("alert")
            except:
                return None

            return "="

        return "<>*"

    def _adjustCriteria(self, criteria):
        if "aggregated_alert_id" in env.request.parameters:
            alert, aggreg_type = env.request.parameters._get_aggregated_alert(env.request.parameters.get("aggregated_alert_id"))

            source_analyzer = None
            newcrit = Criterion()

            for alertident in alert[aggreg_type]["alertident"]:
                # IDMEF draft 14 page 27
                # If the "analyzerid" is not provided, the alert is assumed to have come
                # from the same analyzer that is sending the [Correlation|Tool]Alert.
                analyzerid = alertident["analyzerid"]
                if not analyzerid:
                    if source_analyzer:
                        analyzerid = source_analyzer
                    else:
                        for a in alert["analyzer"]:
                            if a["analyzerid"]:
                                source_analyzer = analyzerid = a["analyzerid"]
                                break

                newcrit |= Criterion("alert.messageid", "=", alertident["alertident"]) + Criterion("alert.analyzer.analyzerid", "=", analyzerid)

            criteria += newcrit

    def _applyFiltersForCategory(self, criteria, type):
        if not env.request.parameters[type]:
            env.request.dataset[type] = [("__all__", "", "")]
            return

        # If one object is specified more than one time, and since this object
        # can not have two different value, we want to apply an OR operator.
        #
        # We apply an AND operator between the different objects.

        merge = {}
        newcrit = Criterion()
        for obj in env.request.parameters[type]:
            if obj[0] == "__all__":
                # We want to lookup the value in our set of predefined path, but also in aggregated
                # value (which the user can see in the filtered columns).
                for path in GENERIC_SEARCH_TABLE[type] + env.request.parameters.get("aggregated_%s" % type):
                    op = self._getOperatorForPath(path, obj[2])
                    if op:
                        newcrit |= Criterion(path, op, obj[2])
            else:
                c = Criterion(obj[0], "==", None) if obj[1] == "!" else Criterion(*obj)
                if obj[0] in merge:
                    merge[obj[0]] += [c]
                else:
                    merge[obj[0]] = [c]

        for value in merge.values():
            newcrit += functools.reduce(lambda x, y: x | y, value)

        criteria += newcrit
        env.request.dataset[type] = [(path.replace("(0)", "").replace("(-1)", ""), operator, value) for path, operator, value in env.request.parameters[type]]

    def _applyFilters(self, criteria):
        self._applyFiltersForCategory(criteria, "classification")
        self._applyClassificationFilters(criteria)

        self._applyFiltersForCategory(criteria, "source")
        self._applyFiltersForCategory(criteria, "target")
        self._applyFiltersForCategory(criteria, "analyzer")

    def _getMissingAggregatedInfos(self, message, path_value_hash, parameters, criteria2, aggregated_count, time_min, time_max):
        index = 0
        selection_list = []

        path_list = [
            "alert.classification.text",
            "alert.analyzer(-1).node.name",
            "alert.analyzer(-1).name",
            "alert.analyzer(-1).model",
            "alert.assessment.impact.severity"
        ]

        for path in path_list:

            if path not in path_value_hash:
                selection_list += [(path, index)]
                index += 1

        selection = ["%s/group_by" % i[0] for i in selection_list]
        alert_list = env.dataprovider.query(selection + ["max(alert.messageid)", "count(alert.messageid)"], criteria2)
        alertsraw = {}
        nodesraw = {}

        for values in alert_list:
            for path, index in selection_list:
                path_value_hash[path] = values[index]

            max_messageid = values[-2]
            alert_count = values[-1]

            classification = path_value_hash["alert.classification.text"]
            analyzer_name = path_value_hash["alert.analyzer(-1).name"]
            analyzer_model = path_value_hash["alert.analyzer(-1).model"]
            analyzer_node_name = path_value_hash["alert.analyzer(-1).node.name"]
            severity = path_value_hash["alert.assessment.impact.severity"]
            completion = None

            alertkey = (classification or "") + "-" + (severity or "") + "-" + (completion or "")

            if alertkey in alertsraw:
                alertsraw[alertkey][-2] += alert_count
            else:
                alertsraw[alertkey] = ([classification, severity, completion, alert_count, max_messageid])

            nodekey = (analyzer_name or analyzer_model or "") + "-" + (analyzer_node_name or "")
            if nodekey not in nodesraw:
                message.addSensor(path_value_hash)
                nodesraw[nodekey] = True

        res = sorted(alertsraw.values(), key=lambda y: {None: 4, "info": 3, "low": 2, "medium": 1, "high": 0}[y[1]])

        source_value = path_value_hash.get("alert.source(0).node.address(0).address", None)
        target_value = path_value_hash.get("alert.target(0).node.address(0).address", None)

        param = {
            'classification': [r[0] for r in res],
            'source': source_value,
            'target': target_value,
            'time_min': time_min,
            'time_max': time_max
        }
        message.extra_link = filter(lambda x: x is not None, hookmanager.trigger("HOOK_MESSAGELISTING_EXTRA_LINK", param))

        result_count = 0
        for classification, severity, completion, count, messageid in res:
            if result_count >= self._max_aggregated_classification:
                continue

            result_count += 1

            message["aggregated_classifications_hidden"] -= count
            infos = message.setInfos(count, classification, severity, completion)

            if count == 1:
                if aggregated_count == 1:
                    message.reset()
                    res = env.dataprovider.get(Criterion("alert.messageid", "=", messageid))[0]
                    message.setMessage(res, messageid, extra_link=False)
                else:
                    infos["links"] = [resource.HTMLNode("a", _("Alert details"), href=url_for("AlertSummary", messageid=messageid))]
                    infos["links"] += list(hookmanager.trigger("HOOK_MESSAGEID_LINK", messageid))
            else:
                entry_param = {}

                if classification is not None:
                    entry_param["classification_object_%d" % env.request.parameters.max_index] = "alert.classification.text"
                    entry_param["classification_operator_%d" % env.request.parameters.max_index] = "="
                    entry_param["classification_value_%d" % env.request.parameters.max_index] = classification

                entry_param["alert.assessment.impact.severity"] = severity or "n/a"
                entry_param["alert.assessment.impact.completion"] = completion or "n/a"

                entry_param["aggregated_target"] = \
                    entry_param["aggregated_source"] = \
                    entry_param["aggregated_analyzer"] = \
                    entry_param["aggregated_classification"] = "none"

                infos["display"] = url_for(
                    ".", **(env.request.parameters - [
                        "offset", "aggregated_classification",
                        "aggregated_source",
                        "aggregated_target",
                        "aggregated_analyzer"
                    ] + parameters + entry_param))

    def _setAggregatedMessagesNoValues(self, criteria, ag_s, ag_t, ag_c, ag_a):
        ag_list = ag_s + ag_t + ag_c + ag_a

        selection = ["%s/group_by" % path for path in ag_list]

        if env.request.parameters["orderby"] == "time_asc":
            selection += ["count(alert.create_time)", "max(alert.create_time)", "min(alert.create_time)/order_asc"]
        elif env.request.parameters["orderby"] == "time_desc":
            selection += ["count(alert.create_time)", "max(alert.create_time)/order_desc", "min(alert.create_time)"]
        elif env.request.parameters["orderby"] == "count_desc":
            selection += ["count(alert.create_time)/order_desc", "max(alert.create_time)", "min(alert.create_time)"]
        elif env.request.parameters["orderby"] == "count_asc":
            selection += ["count(alert.create_time)/order_asc", "max(alert.create_time)", "min(alert.create_time)"]

        results = env.dataprovider.query(selection, criteria)
        total_results = len(results)

        for values in results[env.request.parameters["offset"]:env.request.parameters["offset"]+env.request.parameters["limit"]]:
            start = 0
            aggregated_source_values = []
            aggregated_target_values = []
            aggregated_classification_values = []
            aggregated_analyzer_values = []

            if len(ag_s) > 0:
                start = len(ag_s)
                aggregated_source_values = values[:len(ag_s)]

            if len(ag_t) > 0:
                last = start + len(ag_t)
                aggregated_target_values = values[start:last]
                start = last

            if len(ag_c) > 0:
                last = start + len(ag_c)
                if values[start:last]:
                    aggregated_classification_values = values[start:last]
                start = last

            if len(ag_a) > 0:
                last = start + len(ag_a)
                if values[start:last]:
                    aggregated_analyzer_values = values[start:last]
                start = last

            aggregated_count = values[start]

            select_criteria = Criterion()
            message = self.listed_aggregated_alert(self.view_path, env.request.parameters)

            valueshash = {}
            for path, value in zip(ag_list, values[:start]):
                valueshash[path] = value

                if path.find("source") != -1:
                    direction = "source"
                elif path.find("target") != -1:
                    direction = "target"
                else:
                    direction = None

                if direction:
                    message.setMessageDirectionGeneric(direction, path, value)

                select_criteria += Criterion(path, "==", value)

            time_max = values[start + 1]
            time_min = values[start + 2]

            parameters = self._createAggregationParameters(aggregated_classification_values,
                                                           aggregated_source_values, aggregated_target_values, aggregated_analyzer_values)

            message["aggregated_classifications_total"] = aggregated_count
            message["aggregated_classifications_hidden"] = aggregated_count
            message["aggregated_classifications_hidden_expand"] = url_for(
                ".", **(env.request.parameters - [
                    "offset",
                    "aggregated_source",
                    "aggregated_target",
                    "aggregated_analyzer"
                ] + parameters + {"aggregated_classification": "alert.classification.text"})
            )

            self._getMissingAggregatedInfos(message, valueshash, parameters, criteria + select_criteria, aggregated_count, time_min, time_max)

            env.request.dataset["messages"].append(message)
            message.setTime(time_min, time_max)

            if "selection" not in message:
                message.setCriteriaForSelection(select_criteria + Criterion("alert.create_time", ">=", time_min) + Criterion("alert.create_time", "<=", time_max))

        return total_results

    def _createAggregationParameters(self, aggregated_classification_values, aggregated_source_values, aggregated_target_values, aggregated_analyzer_values):
        parameters = {}

        for values, column in ((aggregated_classification_values, "classification"),
                               (aggregated_source_values, "source"),
                               (aggregated_target_values, "target"),
                               (aggregated_analyzer_values, "analyzer")):
            i = env.request.parameters.max_index
            for path, value in zip(env.request.parameters["aggregated_%s" % column], values):
                parameters["%s_object_%d" % (column, i)] = path.replace("(0)", "").replace("(-1)", "")

                if value:
                    parameters["%s_operator_%d" % (column, i)] = "="
                else:
                    parameters["%s_operator_%d" % (column, i)] = "!"

                parameters["%s_value_%d" % (column, i)] = value or ""
                i += 1

        return parameters

    def _setMessages(self, criteria):
        env.request.dataset["aggregated_source"] = env.request.parameters["aggregated_source"]
        env.request.dataset["aggregated_target"] = env.request.parameters["aggregated_target"]
        env.request.dataset["aggregated_classification"] = env.request.parameters["aggregated_classification"]
        env.request.dataset["aggregated_analyzer"] = env.request.parameters["aggregated_analyzer"]

        env.request.dataset["extra_column"] = filter(None, hookmanager.trigger("HOOK_MESSAGELISTING_EXTRA_COLUMN"))

        def cmp(x):
            return x != "none"

        ag_s = list(filter(cmp, env.request.parameters["aggregated_source"]))
        ag_t = list(filter(cmp, env.request.parameters["aggregated_target"]))
        ag_c = list(filter(cmp, env.request.parameters["aggregated_classification"]))
        ag_a = list(filter(cmp, env.request.parameters["aggregated_analyzer"]))

        if len(ag_s + ag_t + ag_c + ag_a) > 0:
            return self._setAggregatedMessagesNoValues(criteria, ag_s, ag_t, ag_c, ag_a)

        return MessageListing._setMessages(self, criteria)

    def _paramChanged(self, column, paramlist):
        ret = 0

        cd = env.request.parameters.getDefaultParams(column)
        default = env.request.parameters.getDefaultValues()
        default.update(cd)

        for param in itertools.chain(paramlist, cd.keys()):
            if ret != 2 and env.request.parameters.isSaved(column, param):
                ret = 1

            if param not in default:
                if param in env.request.parameters:
                    if env.request.parameters[param] != []:
                        ret = 2
                        break

                    continue

            if param not in env.request.parameters:
                ret = 2
                break

            if type(default[param]) is list:
                default[param].sort()

            if type(env.request.parameters[param]) is list:
                env.request.parameters[param].sort()

            if default[param] != env.request.parameters[param]:
                ret = 2
                break

        return ret

    def _setDatasetConstants(self):
        d = {}
        for i in COLUMN_LIST:
            d[i] = env.request.dataset.get(i)
            n = "aggregated_" + i
            d[n] = env.request.dataset.get(n)
            d[n + "_saved"] = env.request.dataset[n + "_saved"] = env.request.parameters.getDefault(n, usedb=True)
            d[n + "_default"] = env.request.dataset[n + "_default"] = env.request.parameters.getDefault(n, usedb=False)
            d[i + "_saved"] = env.request.dataset[i + "_saved"] = env.request.parameters._saved[i]

        d["special"] = {}
        for i in ("alert.type", "alert.assessment.impact.severity", "alert.assessment.impact.completion"):
            d["special"].setdefault("classification", []).append(i)
            d[i] = env.request.dataset.get(i)
            d[i + "_saved"] = env.request.dataset[i + "_saved"] = env.request.parameters.getDefault(i, usedb=True)
            d[i + "_default"] = env.request.dataset[i + "_default"] = env.request.parameters.getDefault(i, usedb=False)

        root = prelude.IDMEFClass().get("alert")
        env.request.dataset["all_filters"] = {
            "classification": [
                root.get("messageid"),
                root.get("classification"),
                root.get("assessment"),
                root.get("correlation_alert"),
                root.get("overflow_alert"),
                root.get("tool_alert"),
                root.get("additional_data")
            ],
            "source": [root.get("source")],
            "target": [root.get("target")],
            "analyzer": [root.get("analyzer")]
        }

        env.request.dataset["checkbox_fields"] = ["alert.type", "alert.assessment.impact.severity", "alert.assessment.impact.completion"]

        c_params = itertools.chain(["aggregated_classification"], env.request.parameters.getDynamicParams("classification").keys(), env.request.dataset["checkbox_fields"])
        s_params = itertools.chain(["aggregated_source"], env.request.parameters.getDynamicParams("source").keys())
        t_params = itertools.chain(["aggregated_target"], env.request.parameters.getDynamicParams("target").keys())
        a_params = itertools.chain(["aggregated_analyzer"], env.request.parameters.getDynamicParams("analyzer").keys())

        d["column_names"] = COLUMN_LIST[:]

        env.request.dataset["columns_data"] = d

        env.request.dataset["classification_filtered"] = self._paramChanged("classification", c_params)
        env.request.dataset["source_filtered"] = self._paramChanged("source", s_params)
        env.request.dataset["target_filtered"] = self._paramChanged("target", t_params)
        env.request.dataset["analyzer_filtered"] = self._paramChanged("analyzer", a_params)

    def render(self):
        MessageListing.render(self)
        if "aggregated_analyzer" in env.request.parameters:
            env.request.parameters["aggregated_analyzer"] = [i.replace("alert.analyzer(0)", "alert.analyzer(-1)") for i in env.request.parameters["aggregated_analyzer"]]

        criteria = env.request.menu.get_criteria()

        self._applyFilters(criteria)
        self._adjustCriteria(criteria)

        if "listing_apply" in env.request.parameters:
            if env.request.parameters["action"] == "delete_message":
                self._updateMessages(env.dataprovider.delete, criteria)

        self._setNavPrev(env.request.parameters["offset"])

        env.request.dataset["messages"] = []
        total = self._setMessages(criteria)
        self._setDatasetConstants()

        env.request.dataset["nav"]["from"] = localization.format_number(env.request.parameters["offset"] + 1)
        env.request.dataset["nav"]["to"] = localization.format_number(env.request.parameters["offset"] + len(env.request.dataset["messages"]))
        env.request.dataset["limit"] = localization.format_number(env.request.parameters["limit"])
        env.request.dataset["total"] = localization.format_number(total)
        env.request.dataset["correlation_alert_view"] = False

        self._setNavNext(env.request.parameters["offset"], total)

    def _criteria_to_urlparams(self, criteria):
        params = {}

        for index, criterion in enumerate(criteria.format("alert").to_list()):
            path, operator, value = criterion.left, criterion.operator, criterion.right

            # Special case for classification checkboxes
            if path in ("alert.type", "alert.assessment.impact.severity", "alert.assessment.impact.completion"):
                # Operators other than '=' are not supported
                params.setdefault(path, []).append(value or "n/a")
                continue

            ctype = prelude.IDMEFPath(path).getName(1)
            if ctype in ("messageid", "assessment", "correlation_alert", "overflow_alert", "tool_alert", "additional_data"):
                ctype = "classification"

            if ctype not in ("classification", "source", "target", "analyzer"):
                raise Exception(_("The path '%s' cannot be mapped to a column") % path)

            if value is None:
                if operator == "==":
                    operator = "!"
                    value = ""
                else:
                    # Unsupported
                    continue

            params["%s_object_%d" % (ctype, index)] = path
            params["%s_operator_%d" % (ctype, index)] = operator
            params["%s_value_%d" % (ctype, index)] = value

        return params

    @crontab.schedule("alert", N_("Alert deletion"), "0 0 * * *", enabled=False)
    def _alert_cron(self, job):
        config = env.config.cron.get_instance_by_name("alert")
        if config is None:
            return

        criteria = Criterion()
        age = int(config.get("age", 0))
        now = utils.timeutil.utcnow()
        for severity in ("info", "low", "medium", "high"):
            days = int(config.get(severity, age))
            if days < 1:
                continue

            criteria |= (Criterion("alert.assessment.impact.severity", "==", severity) &
                         Criterion("alert.create_time", "<", now - datetime.timedelta(days=days)))

        if not criteria:
            return

        env.dataprovider.delete(criteria, type="alert")


class CorrelationAlertListing(AlertListing, view.View):
    view_menu = (N_("Alerts"), N_("Threats"))
    view_parameters = CorrelationAlertListingParameters
    view_datatype = None
    view_help = "#threats"
    alert_type_default = ["alert.correlation_alert.name"]
