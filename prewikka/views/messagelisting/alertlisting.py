# Copyright (C) 2004-2015 CS-SI. All Rights Reserved.
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

import json, copy, re, urllib, prelude, time, pkg_resources, datetime
from prewikka import view, usergroup, utils, error, mainmenu, localization, env
from . import templates
from messagelisting import MessageListingParameters, MessageListing, ListedMessage


def cmp_severities(x, y):
    d = { None: 0, "info": 1, "low": 2, "medium": 3, "high": 4 }
    return d[y] - d[x]


def _normalizeName(name):
    return "".join([ i.capitalize() for i in name.split("_") ])



COLUMN_LIST = [ "classification", "source", "target", "analyzer" ]

CLASSIFICATION_GENERIC_SEARCH_FIELDS = [ "alert.classification.text", "alert.classification.reference.name", "alert.classification.reference.origin", "alert.assessment.impact.completion" ]

SOURCE_GENERIC_SEARCH_FIELDS = [ "alert.source.node.address.address", "alert.source.user.user_id.name",
                                 "alert.source.user.user_id.number", "alert.source.process.name", "alert.source.process.pid",
                                 "alert.source.service.protocol", "alert.source.service.iana_protocol_name", "alert.source.service.iana_protocol_number",
                                 "alert.source.service.port" ]

TARGET_GENERIC_SEARCH_FIELDS = [ "alert.target.node.address.address", "alert.target.user.user_id.name",
                                 "alert.target.user.user_id.number", "alert.target.process.name", "alert.target.process.pid",
                                 "alert.target.service.protocol", "alert.target.service.iana_protocol_name", "alert.target.service.iana_protocol_number",
                                 "alert.target.service.port" ]

ANALYZER_GENERIC_SEARCH_FIELDS = [ "alert.analyzer.name", "alert.analyzer.node.name" ]

GENERIC_SEARCH_TABLE = { "classification": CLASSIFICATION_GENERIC_SEARCH_FIELDS,
                         "source": SOURCE_GENERIC_SEARCH_FIELDS,
                         "target": TARGET_GENERIC_SEARCH_FIELDS,
                         "analyzer": ANALYZER_GENERIC_SEARCH_FIELDS }


class AlertListingParameters(MessageListingParameters):
    allow_extra_parameters = True

    def __init__(self, *args, **kwargs):
        MessageListingParameters.__init__(self, *args, **kwargs)
        self._dynamic_param = { "classification": {}, "source": {}, "target": {}, "analyzer": {} }
        self._default_param = { "classification": {}, "source": {}, "target": {}, "analyzer": {} }
        self._saved = { "classification": [], "source": [], "target": [], "analyzer": [] }
        self._linked_alerts = []

        if "aggregated_alert_id" in self:
            alert = env.idmef_db.getAlert(int(self.get("aggregated_alert_id")))
            if alert["alert.correlation_alert"]:
                aggreg_type = "alert.correlation_alert"
            elif alert["alert.tool_alert"]:
                aggreg_type = "alert.tool_alert"
            else:
                pass
            for alertident in alert[aggreg_type]["alertident"]:
                self._linked_alerts.append("alert.messageid=%s" % alertident["alertident"])

    def register(self):
        self.max_index = 0
        MessageListingParameters.register(self)
        self.optional("aggregated_source", list, [ "alert.source(0).node.address(0).address" ], save=True)
        self.optional("aggregated_target", list, [ "alert.target(0).node.address(0).address" ], save=True)
        self.optional("aggregated_classification", list, [ "none" ], save=True)
        self.optional("aggregated_analyzer", list, [ "none" ], save=True)
        self.optional("alert.assessment.impact.severity", list, [ "info", "low", "medium", "high", "n/a" ], save=True)
        self.optional("alert.assessment.impact.completion", list, [ "succeeded", "failed", "n/a" ], save=True)
        self.optional("alert.type", list, ["alert.create_time", "alert.correlation_alert.name", "alert.overflow_alert.program", "alert.tool_alert.name"], save=True)

    def _checkOperator(self, operator):
        if not operator in ("=", "<", ">", "<=", ">=", "~", "~*", "<>", "<>*", "!"):
            raise view.InvalidParameterValueError("operator", operator)

    def _setParam(self, view_name, user, column, param, value, is_default=False):
        self._dynamic_param[column][param] = value

        if is_default:
            self._default_param[column][param] = value
            user.set_property(param, value, view=view_name)

        elif user.configuration.has_key(view_name) and user.configuration[view_name].has_key(param) and user.configuration[view_name][param] != value:
            self._default_param[column][param] = value

        if not self.has_key(param):
            # the parameter is loaded from config
            self[param] = value

    def _paramDictToList(self, params_dict, column):
        sorted = []
        ret = False

        for parameter, object in params_dict.items():
            idx = parameter.find(column + "_object_")
            if idx == -1:
                continue

            num = int(parameter.replace(column + "_object_", "", 1))
            if num >= self.max_index:
                self.max_index = num + 1

            ret = True
            operator = params_dict.get(column + "_operator_" + str(num), "=")
            self._checkOperator(operator)

            try:
                value = params_dict[column + "_value_" + str(num)]
            except KeyError:
                if operator != "!":
                    continue
                value = ""

            do_append = True
            for tmp in sorted:
                if tmp[1] == object and tmp[2] == operator and tmp[3] == value:
                    do_append = False
                    break

            if do_append:
                sorted.append((num, object, operator, value))

        sorted.sort()
        return ret, sorted

    def _loadColumnParam(self, view_name, user, paramlist, column, do_save):
        is_saved = False

        if do_save:
            paramlist = copy.copy(paramlist)
            user.del_property_match("%s_object_" % (column), view=view_name)
            user.del_property_match("%s_operator_" % (column), view=view_name)
            user.del_property_match("%s_value_" % (column), view=view_name)

        self[column] = []
        ret, sorted = self._paramDictToList(paramlist, column)
        for i in sorted:
            self._setParam(view_name, user, column, "%s_object_%d" % (column, i[0]), i[1], is_default=do_save)
            self._setParam(view_name, user, column, "%s_operator_%d" % (column, i[0]), i[2], is_default=do_save)
            self._setParam(view_name, user, column, "%s_value_%d" % (column, i[0]), i[3], is_default=do_save)
            self[column].append(i[1:]);

        return ret

    def normalize(self, view_name, user):

        do_save = self.has_key("_save")
        do_load = MessageListingParameters.normalize(self, view_name, user)

        for severity in self["alert.assessment.impact.severity"]:
            if not severity in ("info", "low", "medium", "high", "n/a"):
                raise view.InvalidParameterValueError("alert.assessment.impact.severity", severity)

        for completion in self["alert.assessment.impact.completion"]:
            if not completion in ("succeeded", "failed", "n/a"):
                raise view.InvalidParameterValueError("alert.assessment.impact.completion", completion)

        for type in self["alert.type"]:
            if not type in ("alert.create_time", "alert.correlation_alert.name", "alert.overflow_alert.program", "alert.tool_alert.name"):
                raise view.InvalidParameterValueError("alert.type", type)

        load_saved = True
        for column in "classification", "source", "target", "analyzer":
            ret = self._loadColumnParam(view_name, user, self, column, do_save)
            if ret:
                load_saved = False

        if load_saved and do_load and user.configuration.has_key(view_name):
            for column in "classification", "source", "target", "analyzer":
                self._loadColumnParam(view_name, user, user.configuration[view_name], column, do_save)

        for column in COLUMN_LIST:
            if user.configuration.has_key(view_name):
                for i in self._paramDictToList(user.configuration[view_name], column)[1]:
                    self._saved[column].append(i[1:])

                for i in user.configuration[view_name].keys():
                    if i.find(column + "_object_") != -1 or i.find(column + "_operator_") != -1 or i.find(column + "_value_") != -1:
                        self._default_param[column][i] = user.configuration[view_name][i]

            i = 0
            for path in self["aggregated_%s" % column]:
                if self["aggregated_%s" % column].count(path) > 1:
                    self["aggregated_%s" % column].remove(path)

                if path[0] == "!":
                    self["aggregated_%s" % column][i] = path[1:]

                i += 1

    def getDefaultParams(self, column):
        return self._default_param[column]

    def getDynamicParams(self, column):
        return self._dynamic_param[column]

    def _isSaved(self, column, param):
        if not self._default_param[column].has_key(param):
            return False

        if not self.has_key(param):
            return False

        if self._default_param[column][param] == self[param]:
            return True

        return False

    def isSaved(self, column, param):
        if self._isSaved(column, param):
            return True

        return MessageListingParameters.isSaved(self, param)


class SensorAlertListingParameters(AlertListingParameters):
    def register(self):
        AlertListingParameters.register(self)
        self.mandatory("analyzerid", str)

    def normalize(self, *args, **kwargs):
        AlertListingParameters.normalize(self, *args, **kwargs)
        self["analyzer"].insert(0, ("alert.analyzer.analyzerid", "=", self["analyzerid"]))


class CorrelationAlertListingParameters(AlertListingParameters):
    def register(self):
        AlertListingParameters.register(self)
        self.optional("aggregated_source", list, [ "none" ], save=True)
        self.optional("aggregated_target", list, [ "none" ], save=True)
        self.optional("alert.type", list, ["alert.correlation_alert.name"], save=True)


class ListedAlert(ListedMessage):
    def __init__(self, *args, **kwargs):
        apply(ListedMessage.__init__, (self, ) + args, kwargs)
        self.reset()

        self._max_aggregated_source = int(env.config.general.getOptionValue("max_aggregated_source", 10))
        self._max_aggregated_target = int(env.config.general.getOptionValue("max_aggregated_target", 10))

    def _getKnownValue(self, direction, key):
        return { "alert.%s.service.port" % direction: ("service", None),
                 "alert.%s.node.address.address" % direction: ("addresses", self._setMessageDirectionAddress),
                 "alert.%s.node.name" % direction: ("addresses", self._setMessageDirectionNodeName),
                 }[key]

    def _initValue(self, dataset, name, value):
        dataset[name] = value

    def _initDirection(self, dataset):
        self._initValue(dataset, "port", { "value": None })
        self._initValue(dataset, "protocol", { "value": None })
        self._initValue(dataset, "service", { "value": None, "inline_filter": None, "already_filtered": False })
        self._initValue(dataset, "addresses", [ ])
        self._initValue(dataset, "listed_values", [ ])
        self._initValue(dataset, "aggregated_hidden", 0)
        return dataset

    def _initDirectionIfNeeded(self, direction):
        if len(self[direction]) == 0:
            self[direction].append(self._initDirection({ }))

    def _setMainAndExtraValues(self, dataset, name, object_main, object_extra):
        if object_main != None:
            dataset[name] = { "value": object_main }
            dataset[name + "_extra"] = { "value": object_extra }

        else:
            dataset[name] = { "value": object_extra }
            dataset[name + "_extra"] = { "value": None }

    def _guessAddressCategory(self, address):
        if re.compile("\d\.\d\.\d\.\d").match(address):
            return "ipv4-addr"

        elif re.compile(".*@.*").match(address):
            return "e-mail"

        elif address.count(":") > 1:
            return "ipv6-addr"

        return None

    def _setMessageDirectionAddress(self, dataset, direction, address, category=None):
        if (category == None or category == "unknown") and address:
            category = self._guessAddressCategory(address)

        if dataset.has_key("no_dns"):
            dns = False
        else:
            dns = True

        hfield = self.createHostField("alert.%s(0).node.address(0).address" % direction, address,
                                      category=category, direction=direction, dns=dns)
        dataset["addresses"].append(hfield)

    def _setMessageDirectionNodeName(self, dataset, direction, name):
        dataset["no_dns"] = True
        dataset["addresses"].append(self.createHostField("alert.%s.node.name" % direction, name, direction=direction))

    def _setMessageDirectionOther(self, dataset, direction, path, value, extra_path=None, extra=None, allow_empty_value=False):
        if path == "__all__":
                return

        if value == None:
           if allow_empty_value is False and extra is None:
               return

           if extra is not None:
               value = extra
               path = extra_path
               extra = extra_path = None

        l = path.split(".")
        l[-2] = l[-2].replace("(0)", "")

        if l[-2] != direction:
            name = _normalizeName(l[-2]) + " "
        else:
            name = ""

        name += l[-1]

        item = (name, self.createInlineFilteredField(path, value, direction, real_value=value or "n/a"), extra)
        if not item in dataset["listed_values"]:
            dataset["listed_values"].append(item)

    def _setMessageDirection(self, dataset, direction, obj):
        dataset["interface"] = { "value": obj["interface"] }

        for userid in obj["user.user_id"]:
            self._setMessageDirectionOther(dataset, direction, "alert.%s.user.user_id.name" % direction, userid["name"],
                                                               "alert.%s.user.user_id.number" % direction, userid["number"])

        name = obj["node.name"]
        if name != None:
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
            ppath = "alert.%s.service.iana_protocol_name" % direction
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
                pstr = str(obj["service.port"])
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
            dataset = { }
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
            self["aggregated_source_expand"] = self.createMessageLink(ident, "AlertSummary")

    def _setMessageTarget(self, message, ident):
        index = 0
        total = 0

        for target in message["alert.target"]:
            dataset = { }
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
            self["aggregated_source_expand"] = self.createMessageLink(ident, "AlertSummary")


    def _setMessageClassificationReferences(self, dataset, message):
        dataset["classification_references"] = [ ]
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

            urlstr = "%s?origin=%s&name=%s" % (env.reference_details_url, urllib.quote(ref["origin"]), urllib.quote(ref["name"]))
            if ref["origin"] in ("vendor-specific", "user-specific"):
                urlstr += "&url=" + urllib.quote(ref["url"], safe="")

            fstr = self.createInlineFilteredField(pl, vl, "classification", fstr)
            dataset["classification_references"].append((urlstr, fstr))

    def _setMessageClassificationURL(self, dataset, classification):
        dataset["classification_url"] = [ ]
        if "classification" in env.url:
            for urlname, url in env.url["classification"].items():
                dataset["classification_url"].append((urlname.capitalize(), url.replace("$classification", classification)))

    def _setMessageClassification(self, dataset, message):
        self._setMessageClassificationReferences(dataset, message)
        self._setMessageClassificationURL(dataset, message["alert.classification.text"])
        dataset["classification"] = self.createInlineFilteredField("alert.classification.text", message["alert.classification.text"], "classification")

    def _setMessageAlertIdentInfo(self, message, alert, ident):
        self["sub_alert_number"] = len(alert["alertident"])
        self["sub_alert_name"] = alert["name"]
        self["sub_alert_link"] = self.createMessageLink(ident, "AlertSummary")

        params = { }
        params["timeline_unit"] = "unlimited"
        params["aggregated_source"] = params["aggregated_target"] = params["aggregated_classification"] = params["aggregated_analyzer"] = "none"
        params["aggregated_alert_id"] = ident
        self["sub_alert_display"] = utils.create_link(view.getViewPath("AlertListing"), params)

    def _setClassificationInfos(self, dataset, message, ident):
        dataset["count"] = 1
        dataset["display"] = self.createMessageLink(ident, "AlertSummary")
        dataset["severity"] = { "value": message["alert.assessment.impact.severity"] }
        dataset["completion"] = self.createInlineFilteredField("alert.assessment.impact.completion", message["alert.assessment.impact.completion"])

    def _setMessageTimeURL(self, t, host):
        ret = []
        if "time" in env.url and t:
            t = str(int(t))

            for urlname, url in env.url["time"].items():
                url = url.replace("$time", t)
                if host:
                    url = url.replace("$host", host)
                ret.append((urlname.capitalize(), url))

        return ret

    def _setMessageTime(self, message):
        self["time"] = self.createTimeField(message["alert.create_time"], self.timezone)
        self["time"]["time_url"] = self._setMessageTimeURL(message["alert.analyzer_time"], message["alert.analyzer(-1).node.name"])
        if (message["alert.analyzer_time"] is not None and
            abs(int(message["alert.create_time"]) - int(message["alert.analyzer_time"])) > 60):
            self["analyzer_time"] = self.createTimeField(message["alert.analyzer_time"], self.timezone)
        else:
            self["analyzer_time"] = { "value": None }

    def addSensor(self, message):
        sensor = { }
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
        self["infos"] = [ { } ]
        self["aggregated"] = False
        self["selection"] = ident

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
            self["extra_link"] = env.hookmgr.trigger("HOOK_MESSAGELISTING_EXTRA_LINK", param)

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
                dataset[dset_name].append({ "value": value })
            else:
                dataset[dset_name]["value"] = value

    def reset(self):
        self["sensors"] = [ ]
        self["source"] = [ ]
        self["target"] = [ ]
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
        apply(ListedAlert.__init__, (self,) + args, kwargs)
        self["aggregated"] = True
        self["aggregated_classification_hidden"] = 0
        self["infos"] = [ ]
        self["source"] = [ ]
        self["target"] = [ ]

    def setTime(self, time_min, time_max):
        self["time_min"] = self.createTimeField(time_min, self.parameters["timezone"])
        self["time_max"] = self.createTimeField(time_max, self.parameters["timezone"])

    def setCriteriaForSelection(self, select_criteria):
        self["selection"] = urllib.quote_plus(" && ".join(select_criteria))

    def setInfos(self, count, classification, severity, completion):
        infos = {
            "classification_references": "",
            "classification_url": "",
            "count": count,
            "classification": self.createInlineFilteredField("alert.classification.text", classification, direction="classification"),
            "severity": { "value": severity },
            "completion": self.createInlineFilteredField("alert.assessment.impact.completion", completion)
            }
        self._setMessageClassificationURL(infos, classification)

        self["infos"].append(infos)

        return infos



class AlertListing(MessageListing):
    view_name = N_("Alerts")
    view_parameters = AlertListingParameters
    view_permissions = [ usergroup.PERM_IDMEF_VIEW ]
    view_template = templates.AlertListing
    view_extensions = (("menu", mainmenu.MainMenuAlert),)
    view_section = N_("Alerts")
    view_order = 0

    root = "alert"
    listed_alert = ListedAlert
    listed_aggregated_alert = ListedAggregatedAlert
    alert_type_default = ["alert.create_time", "alert.correlation_alert.name", "alert.overflow_alert.program", "alert.tool_alert.name"]

    def __init__(self):
        MessageListing.__init__(self)

        env.hookmgr.declare_once("HOOK_MESSAGELISTING_EXTRA_COLUMN")
        env.hookmgr.declare_once("HOOK_MESSAGELISTING_EXTRA_LINK")

        # This hook is usually declared/triggered from the filter plugin, but since we
        # also trigger it here, make sure it is available by declaring it anyway.
        env.hookmgr.declare_once("HOOK_FILTER_CRITERIA_LOAD")

        self._max_aggregated_classifications = int(env.config.general.getOptionValue("max_aggregated_classifications", 10))

    def _getMessageIdents(self, criteria, limit=-1, offset=-1, order_by="time_desc"):
        return env.idmef_db.getAlertIdents(criteria, limit, offset, order_by)

    def _fetchMessage(self, ident):
        return env.idmef_db.getAlert(ident)

    def _setMessage(self, message, ident):
        msg = self.listed_alert(self.view_path, self.parameters)
        msg.setMessage(message, ident)
        msg["aggregated"] = False
        msg["selection"] = ident

        return msg

    def _deleteMessage(self, ident, is_ident):
        env.idmef_db.deleteAlert(ident)

    def _lists_have_same_content(self, l1, l2):
        l1 = copy.copy(l1)
        l2 = copy.copy(l2)
        l1.sort()
        l2.sort()

        return l1 == l2

    def _applyOptionalEnumFilter(self, criteria, column, object, values, objpath=None, unsetval="n/a"):
        if ( self.parameters.has_key(object) and not self._lists_have_same_content(self.parameters[object], values) ):
            new = [ ]
            for value in set(values) | set(self.parameters[object]):
                if value in self.parameters[object]:
                    if value == unsetval:
                        new.append("!%s" % (objpath or object))
                    else:
                        new.append("%s = '%s'" % (objpath or object, utils.escape_criteria(value)))

            if new:
                criteria.append("(" + " || ".join(new) + ")")
            self.dataset[object] = self.parameters[object]
        else:
            self.dataset[object] = values


    def _applyAlertTypeFilters(self, criteria):
        if "alert.create_time" in self.parameters["alert.type"]:
            have_base = True
        else:
            have_base = False

        new = [ ]

        for param in ["alert.correlation_alert.name", "alert.overflow_alert.program", "alert.tool_alert.name"]:
            if not have_base:
                if param in self.parameters["alert.type"]:
                    new.append("%s" % param)
            else:
                if not param in self.parameters["alert.type"]:
                    new.append("!%s" % param)

        self.dataset["alert.type"] = self.parameters["alert.type"]

        if len(new) == 0:
            return

        if not have_base:
            criteria.append("(" + " || ".join(new) + ")")
        else:
            criteria.append("(" + " && ".join(new) + ")")

    def _applyClassificationFilters(self, criteria):
        self._applyAlertTypeFilters(criteria)

        self._applyOptionalEnumFilter(criteria, "classification", "alert.assessment.impact.severity",
                                      ["info", "low", "medium", "high", "n/a"])
        self._applyOptionalEnumFilter(criteria, "classification", "alert.assessment.impact.completion",
                                      ["failed", "succeeded", "n/a"])


    def _criteriaValueFind(self, str, clist=[]):
        out=""
        found = False
        escaped = False

        for c in str:
            if escaped:
                escaped = False
            else:
                if c in clist:
                    found = True

                if c == '\\':
                    escaped = True

            out += c

        return out, found

    def _adjustFilterValue(self, op, value):
        if op != "<>*" and op != "<>":
            return value

        value = value.strip()

        value, has_wildcard = self._criteriaValueFind(value, ["*"])
        if has_wildcard:
            return value

        return "*" + value + "*"

    def _filterTupleToString(self, filtertpl):
        prev_val = filtertpl

        for i in env.hookmgr.trigger("HOOK_FILTER_CRITERIA_LOAD", filtertpl):
            if i:
                filtertpl = i

        object, operator, value = filtertpl

        if operator == "!":
            return "! %s" % (object)

        if prev_val == filtertpl:
            value = "'" + utils.escape_criteria(self._adjustFilterValue(operator, filtertpl[2])) + "'"

        return "%s %s %s" % (object, operator, value)

    def _getOperatorForPath(self, path, value):
        # Check whether the path can handle substring comparison
        # this need to be done first, since enum check with * won't work with "=" operator.
        try:
            c = prelude.IDMEFCriteria(path + " <>* '" + utils.escape_criteria(value) + "'")
        except:
            # Check whether this path can handle the provided value.
            try:
                c = prelude.IDMEFCriteria(path + "  = '" + utils.escape_criteria(value) + "'")
            except:
                return None

            return "="

        return "<>*"

    def _adjustCriteria(self, criteria):
        if "aggregated_alert_id" in self.parameters:
            alert = env.idmef_db.getAlert(int(self.parameters["aggregated_alert_id"]))["alert"]
            if alert["correlation_alert"]:
                aggreg_type = "correlation_alert"
            elif alert["tool_alert"]:
                aggreg_type = "tool_alert"
            else:
                pass

            source_analyzer = None
            newcrit = [ ]

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

                newcrit.append("(alert.messageid = '%s' && alert.analyzer.analyzerid = '%s')" %
                               (utils.escape_criteria(alertident["alertident"]),
                                utils.escape_criteria(analyzerid)))
            criteria.append("(" + " || ".join(newcrit) + ")")

    def _applyFiltersForCategory(self, criteria, type):
        if not self.parameters[type]:
            self.dataset[type] = [ ("__all__", "", "") ]
            return

        # If one object is specified more than one time, and since this object
        # can not have two different value, we want to apply an OR operator.
        #
        # We apply an AND operator between the different objects.

        merge = { }
        newcrit = ""
        for obj in self.parameters[type]:
            if obj[0] == "__all__":
                # We want to lookup the value in our set of predefined path, but also in aggregated
                # value (which the user can see in the filtered columns).
                for path in GENERIC_SEARCH_TABLE[type] + self.parameters.get("aggregated_%s" % type):
                    op = self._getOperatorForPath(path, obj[2])
                    if op:
                        if len(newcrit) > 0:
                            newcrit += " || "
                        newcrit += self._filterTupleToString((path, op, obj[2]))
            else:
                if merge.has_key(obj[0]):
                    merge[obj[0]] += [ obj ]
                else:
                    merge[obj[0]] =  [ obj ]

        if len(newcrit):
            newcrit = "(" + newcrit + ")"

        for key in iter(merge):
            if len(newcrit) > 0:
                newcrit += " && "

            newcrit += "(" + " || ".join(map(self._filterTupleToString, merge[key])) + ")"

        if newcrit:
            criteria.append(newcrit)

        self.dataset[type] = [ (path.replace("(0)", "").replace("(-1)", ""), operator, value) for path, operator, value in self.parameters[type] ]

    def _applyFilters(self, criteria):
        self._applyFiltersForCategory(criteria, "classification")
        self._applyClassificationFilters(criteria)

        self._applyFiltersForCategory(criteria, "source")
        self._applyFiltersForCategory(criteria, "target")
        self._applyFiltersForCategory(criteria, "analyzer")

    def _getMissingAggregatedInfos(self, message, path_value_hash, parameters, criteria2, aggregated_count, time_min, time_max):
        selection = [ ]
        index = 0
        selection_list = [ ]

        path_list = ["alert.classification.text", "alert.analyzer(-1).node.name",
                     "alert.analyzer(-1).name", "alert.analyzer(-1).model",
                     "alert.assessment.impact.severity", "alert.assessment.impact.completion"]

        for path in path_list:

            if not path_value_hash.has_key(path):
                selection_list += [ (path, index) ]
                index += 1

        selection = [ "%s/group_by" % i[0] for i in selection_list ]
        alert_list = env.idmef_db.getValues( selection + ["max(alert.messageid)", "count(alert.messageid)" ], criteria2)
        alertsraw = { }
        nodesraw = { }

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
            completion = path_value_hash["alert.assessment.impact.completion"]

            alertkey = (classification or "") + "-" + (severity or "") + "-" + (completion or "")

            if alertsraw.has_key(alertkey):
               alertsraw[alertkey][-2] += alert_count
            else:
               alertsraw[alertkey] = ( [classification, severity, completion, alert_count, max_messageid] )

            nodekey = (analyzer_name or analyzer_model or "") + "-" + (analyzer_node_name or "")
            if not nodesraw.has_key(nodekey):
               message.addSensor(path_value_hash)
               nodesraw[nodekey] = True

        res = alertsraw.values()
        res.sort(lambda x, y: cmp_severities(x[1], y[1]))

        source_value = path_value_hash.get("alert.source(0).node.address(0).address", None)
        target_value = path_value_hash.get("alert.target(0).node.address(0).address", None)

        param = {
            'classification': [r[0] for r in res],
            'source': source_value,
            'target': target_value,
            'time_min': time_min,
            'time_max': time_max
        }
        message.extra_link = env.hookmgr.trigger("HOOK_MESSAGELISTING_EXTRA_LINK", param)

        result_count = 0
        for classification, severity, completion, count, messageid in res:
            if result_count >= self._max_aggregated_classifications:
                continue

            result_count += 1

            message["aggregated_classifications_hidden"] -= count
            infos = message.setInfos(count, classification, severity, completion)

            if count == 1:
                if aggregated_count == 1:
                    message.reset()
                    ident = env.idmef_db.getAlertIdents("alert.messageid = '%s'" % utils.escape_criteria(messageid))[0]
                    message.setMessage(self._fetchMessage(ident), ident, extra_link=False)
                else:
                    infos["display"] = message.createMessageIdentLink(messageid, "AlertSummary")
            else:
                entry_param = {}

                if classification is not None:
                    entry_param["classification_object_%d" % self.parameters.max_index] = "alert.classification.text"
                    entry_param["classification_operator_%d" % self.parameters.max_index] = "="
                    entry_param["classification_value_%d" % self.parameters.max_index] = classification

                entry_param["alert.assessment.impact.severity"] = severity or "n/a"
                entry_param["alert.assessment.impact.completion"] = completion or "n/a"

                entry_param["aggregated_target"] = \
                entry_param["aggregated_source"] = \
                entry_param["aggregated_analyzer"] = \
                entry_param["aggregated_classification"] = "none"

                infos["display"] = utils.create_link(self.view_path, self.parameters -
                                                     [ "offset", "aggregated_classification",
                                                       "aggregated_source", "aggregated_target", "aggregated_analyzer" ] +
                                                     parameters + entry_param)

    def _setAggregatedMessagesNoValues(self, criteria, ag_s, ag_t, ag_c, ag_a):
        ag_list = ag_s + ag_t + ag_c + ag_a

        ##
        selection = [ "%s/group_by" % path for path in ag_list ]

        if self.parameters["orderby"] == "time_asc":
            selection += [ "count(alert.create_time)", "max(alert.create_time)/order_asc" ]
        elif self.parameters["orderby"] == "time_desc":
            selection += [ "count(alert.create_time)", "max(alert.create_time)/order_desc" ]
        elif self.parameters["orderby"] == "count_desc":
            selection += [ "count(alert.create_time)/order_desc", "max(alert.create_time)" ]
        elif self.parameters["orderby"] == "count_asc":
            selection += [ "count(alert.create_time)/order_asc", "max(alert.create_time)" ]

        use_sensor_localtime = self.parameters["timezone"] == "sensor_localtime"
        if not use_sensor_localtime:
            selection += [ "min(alert.create_time)" ]

        results = env.idmef_db.getValues(selection, criteria)
        total_results = len(results)

        for values in results[self.parameters["offset"]:self.parameters["offset"]+self.parameters["limit"]]:
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

            criteria2 = criteria[:]
            select_criteria = [ ]
            message = self.listed_aggregated_alert(self.view_path, self.parameters)

            valueshash = {}
            for path, value in zip(ag_list, values[:start]):
                valueshash[path] = value

                if path.find("source") != -1:
                    direction = "source"
                elif path.find("target") != -1:
                    direction = "target"
                else:
                    direction = None

                if value == None:
                    if prelude.IDMEFPath(path).getValueType() != prelude.IDMEFValue.TYPE_STRING:
                        criterion = "! %s" % (path)
                    else:
                        criterion = "(! %s || %s == '')" % (path, path)
                else:
                    criterion = "%s == '%s'" % (path, utils.escape_criteria(value))

                if direction != None:
                    message.setMessageDirectionGeneric(direction, path, value)

                criteria2.append(criterion)
                select_criteria.append(criterion)

            if use_sensor_localtime:
                time_min = env.idmef_db.getValues(["alert.create_time/order_asc"], criteria2, limit=1)[0][0]
                time_max = env.idmef_db.getValues(["alert.create_time/order_desc"], criteria2, limit=1)[0][0]
            else:
                time_max = values[start + 1]
                time_min = values[start + 2]

            parameters = self._createAggregationParameters(aggregated_classification_values,
                                                           aggregated_source_values, aggregated_target_values, aggregated_analyzer_values)

            message["aggregated_classifications_total"] = aggregated_count
            message["aggregated_classifications_hidden"] = aggregated_count
            message["aggregated_classifications_hidden_expand"] = utils.create_link(self.view_path,
                                                                                    self.parameters -
                                                                                    [ "offset",
                                                                                      "aggregated_source",
                                                                                      "aggregated_target",
                                                                                      "aggregated_analyzer" ]
                                                                                    + parameters +
                                                                                    { "aggregated_classification":
                                                                                      "alert.classification.text" } )

            self._getMissingAggregatedInfos(message, valueshash, parameters, criteria2, aggregated_count, time_min, time_max)
            select_criteria.append("alert.create_time >= '%s'" % time_min.toString())
            select_criteria.append("alert.create_time <= '%s'" % time_max.toString())

            self.dataset["messages"].append(message)
            message.setTime(time_min, time_max)

            if not message.has_key("selection"):
                message.setCriteriaForSelection(select_criteria)

        return total_results


    def _createAggregationParameters(self, aggregated_classification_values, aggregated_source_values, aggregated_target_values, aggregated_analyzer_values):
        parameters = { }

        for values, column in ((aggregated_classification_values, "classification"),
                               (aggregated_source_values, "source"),
                               (aggregated_target_values, "target"),
                               (aggregated_analyzer_values, "analyzer")):
            i = self.parameters.max_index
            for path, value in zip(self.parameters["aggregated_%s" % column], values):
                parameters["%s_object_%d" % (column, i)] = path.replace("(0)", "").replace("(-1)", "")

                if value:
                    parameters["%s_operator_%d" % (column, i)] = "="
                else:
                    parameters["%s_operator_%d" % (column, i)] = "!"

                parameters["%s_value_%d" % (column, i)] = value or ""
                i += 1


        return parameters

    def _setMessages(self, criteria):
        self.dataset["aggregated_source"] = self.parameters["aggregated_source"]
        self.dataset["aggregated_target"] = self.parameters["aggregated_target"]
        self.dataset["aggregated_classification"] = self.parameters["aggregated_classification"]
        self.dataset["aggregated_analyzer"] = self.parameters["aggregated_analyzer"]

        self.dataset["extra_column"] = set(env.hookmgr.trigger("HOOK_MESSAGELISTING_EXTRA_COLUMN"))

        ag_s = self.parameters["aggregated_source"][:]
        ag_t = self.parameters["aggregated_target"][:]
        ag_c = self.parameters["aggregated_classification"][:]
        ag_a = self.parameters["aggregated_analyzer"][:]

        for l in ag_s, ag_t, ag_c, ag_a:
            while "none" in l:
                l.remove("none")

        if len(ag_s + ag_t + ag_c + ag_a) > 0:
            return self._setAggregatedMessagesNoValues(criteria, ag_s, ag_t, ag_c, ag_a)

        return MessageListing._setMessages(self, criteria)

    def _paramChanged(self, column, paramlist):
        ret = 0

        cd = self.parameters.getDefaultParams(column)
        default = self.parameters.getDefaultValues()
        default.update(cd)

        for param in paramlist + cd.keys():
            if ret != 2 and self.parameters.isSaved(column, param):
                ret = 1

            if not default.has_key(param):
                if self.parameters.has_key(param):
                    if self.parameters[param] != []:
                        ret = 2
                        break

                    continue

            if not self.parameters.has_key(param):
                ret = 2
                break

            if type(default[param]) is list:
                default[param].sort()

            if type(self.parameters[param]) is list:
                self.parameters[param].sort()

            if default[param] != self.parameters[param]:
                ret = 2
                break

        return ret

    def _setDatasetConstants(self):
        d = {}
        for i in COLUMN_LIST:
            d[i] = self.dataset[i]
            n = "aggregated_" + i
            d[n] = self.dataset[n]
            d[n + "_saved"] = self.dataset[n + "_saved"] = self.parameters.getDefault(n, usedb=True)
            d[n + "_default"] = self.dataset[n + "_default"] = self.parameters.getDefault(n, usedb=False)
            d[i + "_saved"] = self.dataset[i + "_saved"] = self.parameters._saved[i]

        d["special"] = {}
        for i in ("alert.type", "alert.assessment.impact.severity", "alert.assessment.impact.completion"):
            d["special"].setdefault("classification", []).append(i)
            d[i] = self.dataset[i]
            d[i + "_saved"] = self.dataset[i + "_saved"] = self.parameters.getDefault(i, usedb=True)
            d[i + "_default"] =self.dataset[i + "_default"] = self.parameters.getDefault(i, usedb=False)

        root = prelude.IDMEFClass().get("alert")
        self.dataset["all_filters"] = { "classification" : [root.get("classification"),
                                                            root.get("correlation_alert"),
                                                            root.get("overflow_alert"),
                                                            root.get("tool_alert"),
                                                            root.get("additional_data")],
                                        "source": [root.get("source")],
                                        "target": [root.get("target")],
                                        "analyzer": [root.get("analyzer")]}

        c_params = ["aggregated_classification"] + self.parameters.getDynamicParams("classification").keys()
        c_params += ["alert.type", "alert.assessment.impact.severity", "alert.assessment.impact.completion" ]
        s_params = ["aggregated_source"] + self.parameters.getDynamicParams("source").keys()
        t_params = ["aggregated_target"] + self.parameters.getDynamicParams("target").keys()
        a_params = ["aggregated_analyzer"] + self.parameters.getDynamicParams("analyzer").keys()

        d["column_names"] = COLUMN_LIST[:]

        self.dataset["columns_data"] = json.dumps(d)

        self.dataset["classification_filtered"] = self._paramChanged("classification", c_params)
        self.dataset["source_filtered"] = self._paramChanged("source", s_params)
        self.dataset["target_filtered"] = self._paramChanged("target", t_params)
        self.dataset["analyzer_filtered"] = self._paramChanged("analyzer", a_params)

    def _setTimelineChart(self):
        if self.parameters["timeline_unit"] in ("month", "year"):
            unit = "month"
        elif self.parameters["timeline_unit"] == "day":
            unit = "day"
        else:
            unit = "hour"

    def render(self):
        MessageListing.render(self)
        if "listing_apply" in self.parameters:
            if self.parameters["action"] == "delete_message":
                self._updateMessages(self._deleteMessage)

        self._setTimelineChart()

        criteria = [ ]

        time_criteria = self.menu.get_criteria()
        if time_criteria:
                criteria.append(time_criteria)

        self._applyFilters(criteria)
        self._adjustCriteria(criteria)

        self._setNavPrev(self.parameters["offset"])

        self._setHiddenParameters()

        self.dataset["messages"] = [ ]
        total = self._setMessages(criteria)
        self._setDatasetConstants()

        self.dataset["nav.from"] = localization.format_number(self.parameters["offset"] + 1)
        self.dataset["nav.to"] = localization.format_number(self.parameters["offset"] + len(self.dataset["messages"]))
        self.dataset["limit"] = localization.format_number(self.parameters["limit"])
        self.dataset["total"] = localization.format_number(total)
        self.dataset["correlation_alert_view"] = False

        self._setNavNext(self.parameters["offset"], total)


class CorrelationAlertListing(AlertListing, view.View):
    view_name = N_("CorrelationAlerts")
    view_parameters = CorrelationAlertListingParameters
    alert_type_default = [ "alert.correlation_alert.name" ]
    view_order = 1


class SensorAlertListing(AlertListing, view.View):
    view_parameters = SensorAlertListingParameters
    view_permissions = [ usergroup.PERM_IDMEF_VIEW ]
    view_template = templates.SensorAlertListing
    view_parent = AlertListing

    listed_alert = ListedAlert
    listed_aggregated_alert = ListedAggregatedAlert

    def _setHiddenParameters(self):
        AlertListing._setHiddenParameters(self)
        self.dataset["hidden_parameters"].append(("analyzerid", self.parameters["analyzerid"]))

    def render(self):
        AlertListing.render(self)
        self.dataset["analyzer_infos"], _ = env.idmef_db.getAnalyzer(self.parameters["analyzerid"], htmlsafe=True)
