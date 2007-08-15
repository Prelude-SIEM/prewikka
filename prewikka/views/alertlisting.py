# Copyright (C) 2004,2005,2006,2007 PreludeIDS Technologies. All Rights Reserved.
# Author: Nicolas Delon <nicolas.delon@prelude-ids.com>
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
# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING.  If not, write to
# the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.

import copy, re, urllib, time, prelude, preludedb, operator
from prewikka import view, User, utils
from prewikka.views.messagelisting import MessageListingParameters, MessageListing, ListedMessage


def cmp_severities(x, y):
    d = { None: 0, "info": 1, "low": 2, "medium": 3, "high": 4 }
    return d[y] - d[x]


def _normalizeName(name):
    return "".join([ i.capitalize() for i in name.split("_") ])


def _getEnumValue(class_id):
    i = 0
    nlist = [ ]

    while True:
        value = prelude.idmef_class_enum_to_string(class_id, i)
        i += 1
        if value == None:
            if i == 1:
                continue

            break

        nlist += [ value ]

    return nlist


def _getPathList(class_id, path, add_index=None, depth=0):
    plist = []

    if depth == 0:
        if not add_index:
            path = path.replace("(0)", "").replace("(-1)", "")

        tmp = path[path.rfind(".") + 1:]
        elen = tmp.find("(")
        if elen == -1:
            plist += [( _normalizeName(tmp), None, None) ]
        else:
            plist += [( _normalizeName(tmp[:elen]), None, None) ]
        depth += 1

    i = 0
    child_list = []

    while True:
        name = prelude.idmef_class_get_child_name(class_id, i)
        if not name or (name == "file" and class_id == prelude.IDMEF_CLASS_ID_LINKAGE):
            break

        vtype = prelude.idmef_class_get_child_value_type(class_id, i)
        space = "\u00a0\u00a0" * depth

        if vtype == prelude.IDMEF_VALUE_TYPE_CLASS:
            if add_index and prelude.idmef_class_is_child_list(class_id, i):
                index = add_index
            else:
                index = ""

            child_list += [ (space + _normalizeName(name), None, None) ]
            child_list += _getPathList(prelude.idmef_class_get_child_class(class_id, i), path + "." + name + index, add_index, depth + 1)
        else:
            if vtype == prelude.IDMEF_VALUE_TYPE_ENUM:
                pval = _getEnumValue(prelude.idmef_class_get_child_class(class_id, i))
            else:
                pval = None

            plist += [( space + name, path + "." + name, pval) ]

        i += 1

    return plist + child_list


def _getClassificationPath(add_empty=False, add_index=None):
    empty = [ ]
    if add_empty:
        empty += [("", "none", None)]

    return empty + \
           [("messageid", "alert.messageid", None)] + \
           _getPathList(prelude.IDMEF_CLASS_ID_CLASSIFICATION, "alert.classification", add_index=add_index) + \
           _getPathList(prelude.IDMEF_CLASS_ID_ASSESSMENT, "alert.assessment", add_index=add_index) + \
           _getPathList(prelude.IDMEF_CLASS_ID_OVERFLOW_ALERT, "alert.overflow_alert", add_index=add_index) + \
           _getPathList(prelude.IDMEF_CLASS_ID_CORRELATION_ALERT, "alert.correlation_alert", add_index=add_index) + \
           _getPathList(prelude.IDMEF_CLASS_ID_TOOL_ALERT, "alert.tool_alert", add_index=add_index) + \
           _getPathList(prelude.IDMEF_CLASS_ID_ADDITIONAL_DATA, "alert.additional_data", add_index=add_index)

def _getSourcePath(add_empty=False, add_index=None):
    empty = [ ]
    if add_empty:
        empty += [("", "none", None)]

    return empty + _getPathList(prelude.IDMEF_CLASS_ID_SOURCE, "alert.source(0)", add_index=add_index)

def _getTargetPath(add_empty=False, add_index=None):
    empty = [ ]
    if add_empty:
        empty += [("", "none", None)]

    return empty + _getPathList(prelude.IDMEF_CLASS_ID_TARGET, "alert.target(0)", add_index=add_index)

def _getAnalyzerPath(add_empty=False, add_index=None):
    empty = [ ]
    if add_empty:
        empty += [("", "none", None)]

    return empty + _getPathList(prelude.IDMEF_CLASS_ID_ANALYZER, "alert.analyzer(-1)", add_index=add_index)


CLASSIFICATION_FILTERS = _getClassificationPath()
CLASSIFICATION_AGGREGATIONS = _getClassificationPath(add_empty=True, add_index="(0)")

SOURCE_FILTERS = _getSourcePath()
SOURCE_AGGREGATIONS = _getSourcePath(add_empty=True, add_index="(0)")

TARGET_FILTERS = _getTargetPath()
TARGET_AGGREGATIONS = _getTargetPath(add_empty=True, add_index="(0)")

ANALYZER_FILTERS = _getAnalyzerPath()
ANALYZER_AGGREGATIONS = _getAnalyzerPath(add_empty=True, add_index="(0)")



class AlertListingParameters(MessageListingParameters):
    allow_extra_parameters = True

    def register(self):
        self.max_index = 0
        MessageListingParameters.register(self)
        self.optional("aggregated_source", list, [ "alert.source(0).node.address(0).address" ], save=True)
        self.optional("aggregated_target", list, [ "alert.target(0).node.address(0).address" ], save=True)
        self.optional("aggregated_classification", list, [ "none" ], save=True)
        self.optional("aggregated_analyzer", list, [ "none" ], save=True)
        self.optional("filter", str, save=True)
        self.optional("alert.classification.text", list, [ ], save=True)
        self.optional("alert.assessment.impact.severity", list, [ "info", "low", "medium", "high", "none" ], save=True)
        self.optional("alert.assessment.impact.completion", list, [ "succeeded", "failed", "none" ], save=True)
        self.optional("alert.assessment.impact.type", list, [ "other", "admin", "dos", "file", "recon", "user" ], save=True)
        self.optional("alert.type", list, ["alert.create_time", "alert.correlation_alert.name", "alert.overflow_alert.program", "alert.tool_alert.name"], save=True)

    def _checkOperator(self, operator):
        if operator[0] == "!":
            operator = operator[1:]

        if not operator in ("=", "<", ">", "<=", ">=", "~", "~*", "<>", "<>*"):
            raise view.InvalidParameterValueError("operator", operator)

    def _loadColumnParam(self, view_name, user, paramlist, column, do_save):
        ret = False
        sorted = [ ]

        for parameter, object in paramlist.items():
            idx = parameter.find(column + "_object_")
            if idx == -1:
                continue

            num = int(parameter.replace(column + "_object_", "", 1))
            if num >= self.max_index:
                self.max_index = num + 1

            ret = True
            operator = paramlist.get(column + "_operator_" + str(num), "=")
            self._checkOperator(operator)

            try:
                value = paramlist[column + "_value_" + str(num)]
            except KeyError:
                continue

            do_append = True
            for tmp in sorted:
                if tmp[1] == object and tmp[2] == operator and tmp[3] == value:
                    do_append = False
                    break

            if do_append:
                sorted.append((num, object, operator, value))

        sorted.sort()
        self[column] = [ (i[1], i[2], i[3]) for i in sorted ]


        if do_save:
            user.delConfigValueMatch(view_name, "%s_object_%%" % (column))
            user.delConfigValueMatch(view_name, "%s_operator_%%" % (column))
            user.delConfigValueMatch(view_name, "%s_value_%%" % (column))

            for num, obj, operator, value in sorted:
                user.setConfigValue(view_name, "%s_object_%d" % (column, num), obj)
                user.setConfigValue(view_name, "%s_operator_%d" % (column, num), operator)
                user.setConfigValue(view_name, "%s_value_%d" % (column, num), value)

        return ret


    def normalize(self, view_name, user):
        do_save = self.has_key("_save")
        do_load = MessageListingParameters.normalize(self, view_name, user)

        for severity in self["alert.assessment.impact.severity"]:
            if not severity in ("info", "low", "medium", "high", "none"):
                raise view.InvalidParameterValueError("alert.assessment.impact.severity", severity)

        for completion in self["alert.assessment.impact.completion"]:
            if not completion in ("succeeded", "failed", "none"):
                raise view.InvalidParameterValueError("alert.assessment.impact.completion", completion)

        for type in self["alert.assessment.impact.type"]:
            if not type in ("other", "admin", "dos", "file", "recon", "user"):
                raise view.InvalidParameterValueError("alert.assessment.impact.type", type)

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

        for category in "classification", "source", "target", "analyzer":
            i = 0
            for path in self["aggregated_%s" % category]:

                if self["aggregated_%s" % category].count(path) > 1:
                    self["aggregated_%s" % category].remove(path)

                if path[0] == "!":
                    self["aggregated_%s" % category][i] = path[1:]

                i += 1



class SensorAlertListingParameters(AlertListingParameters):
    def register(self):
        AlertListingParameters.register(self)
        self.mandatory("analyzerid", str)

    def normalize(self, view_name, user):
        AlertListingParameters.normalize(self, view_name, user)
        self["analyzer"].insert(0, ("alert.analyzer.analyzerid", "=", str(self["analyzerid"])))


class CorrelationAlertListingParameters(AlertListingParameters):
    def register(self):
        AlertListingParameters.register(self)
        self.optional("aggregated_source", list, [ ], save=True)
        self.optional("aggregated_target", list, [ ], save=True)
        self.optional("alert.type", list, ["alert.correlation_alert.name"], save=True)

    def normalize(self, view_name, user):
        AlertListingParameters.normalize(self, view_name, user)


class ToolAlertListingParameters(AlertListingParameters):
    def register(self):
        AlertListingParameters.register(self)
        self.optional("aggregated_source", list, [ ], save=True)
        self.optional("aggregated_target", list, [ ], save=True)
        self.optional("alert.type", list, ["alert.tool_alert.name"], save=True)

    def normalize(self, view_name, user):
        AlertListingParameters.normalize(self, view_name, user)


class ListedAlert(ListedMessage):
    def __init__(self, *args, **kwargs):
        apply(ListedMessage.__init__, (self, ) + args, kwargs)
        self.reset()

    def _getKnownValue(self, direction, key):
        return { "alert.%s.service.port" % direction: ("service", None),
                 "alert.%s.node.address.address" % direction: ("addresses", self._setMessageDirectionAddress),
                 "alert.%s.node.name" % direction: ("addresses", self._setMessageDirectionNodeName),
                 }[key]

    def _initValue(self, dataset, name, value):
        dataset[name] = value

    def _initDirection(self, dataset):
        self._initValue(dataset, "protocol", { "value": None })
        self._initValue(dataset, "service", { "value": None })
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
        if category == None:
            category = self._guessAddressCategory(address)

        hfield = self.createHostField("alert.%s.node.address.address" % direction, address, category=category, direction=direction)
        dataset["addresses"].append(hfield)

    def _setMessageDirectionNodeName(self, dataset, direction, name):
        dataset["addresses"].append(self.createHostField("alert.%s.node.name" % direction, name, direction=direction))

    def _setMessageDirectionOther(self, dataset, direction, path, value, extra_path=None, extra=None):
        if value == None:
           if extra == None:
                return

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

        item = (name, self.createInlineFilteredField(path, value, direction), extra)
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

        proto = None
        if obj["service.iana_protocol_name"]:
            proto = obj["service.iana_protocol_name"]

        elif obj["service.iana_protocol_number"]:
            num = obj["service.iana_protocol_number"]
            proto = utils.protocol_number_to_name(num)

        if not proto:
            proto = obj["service.protocol"]

        self._setMainAndExtraValues(dataset, "protocol", proto, None)
        self._setMainAndExtraValues(dataset, "service", obj["service.port"], None)

        dataset["files"] = []

    def _lookupDataset(self, dlist, dataset):
        for dset in dlist:
           if dset.items() == dataset.items():
                return dset

        return None

    def _setMessageSource(self, message):
        total = 0
        index = 0
        for source in message["alert.source"]:
            dataset = { }
            self._initDirection(dataset)
            self._setMessageDirection(dataset, "source", source)

            if not self._lookupDataset(self["source"], dataset):
                total += 1
                if self._source_index == self.env.max_aggregated_source:
                        continue

                index += 1
                self._source_index += 1
                self["source"].append(dataset)

        self["aggregated_source_total"] += total
        self["aggregated_source_hidden"] += (total - index)

    def _setMessageTarget(self, message):
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
                if self._target_index == self.env.max_aggregated_target:
                        continue

                index += 1
                self._target_index += 1
                self["target"].append(dataset)

        self["aggregated_target_total"] += total
        self["aggregated_target_hidden"] += (total - index)

    def _setMessageClassificationReferences(self, dataset, message):
        dataset["classification_references"] = [ ]
        for ref in message["alert.classification.reference"]:
            fstr = ""

            origin = ref["origin"]
            if origin:
                fstr += origin

            name = ref["name"]
            if name:
                fstr += ":" + name

            urlstr = "https://www.prelude-ids.com/reference_details.php?origin=%s&name=%s" % (ref["origin"], ref["name"])
            if ref["origin"] in ("vendor-specific", "user-specific"):
                urlstr += "&url=" + ref["url"]

            dataset["classification_references"].append((urlstr, fstr))

    def _setMessageClassification(self, dataset, message):
        self._setMessageClassificationReferences(dataset, message)
        dataset["classification"] = self.createInlineFilteredField("alert.classification.text",
                                                                   message["alert.classification.text"])

    def _fetchInfoFromLinkedMessage(self, criteria, source, target):
        result = self.env.idmef_db.getAlertIdents(criteria)
        for ident in result:
            idmef = self.env.idmef_db.getAlert(ident)

            if not source:
                self._setMessageSource(idmef)

            if not target:
                self._setMessageTarget(idmef)


    def _setMessageAlertIdentInfo(self, message, alert, ident):
        fetch_classification_info = fetch_source_info = fetch_target_info = True

        i = 0
        params = { }
        criteria = [ ]
        source_analyzer = None

        for alertident in alert["alertident"]:
            i += 1

            # IDMEF draft 14 page 27
            # If the "analyzerid" is not provided, the alert is assumed to have come
            # from the same analyzer that is sending the Alert.

            analyzerid = alertident["analyzerid"]
            if not analyzerid:
                if source_analyzer:
                    analyzerid = source_analyzer
                else:
                    for a in message["analyzer"]:
                        if a["analyzerid"]:
                            source_analyzer = analyzerid = a["analyzerid"]
                            break

            params["analyzer_object_%d" % i] = "alert.analyzer.analyzerid"
            params["analyzer_value_%d" % i] = analyzerid
            params["classification_object_%d" % i] = "alert.messageid"
            params["classification_value_%d" % i] = alertident["alertident"]

            criteria.append("(alert.messageid = '%s' && alert.analyzer.analyzerid = '%s')" % (utils.escape_criteria(alertident["alertident"]), utils.escape_criteria(analyzerid)))

        source = message["alert.source"]
        target = message["alert.target"]
        if not source or not target:
            self._fetchInfoFromLinkedMessage(" || ".join(criteria), source, target)

        self["sub_alert_number"] = i
        self["sub_alert_name"] = alert["name"]
        self["sub_alert_link"] = self.createMessageLink(ident, "alert_summary")

        tmp = self.parameters
        tmp -= [ "timeline_unit", "timeline_value", "offset",
                 "aggregated_classification", "aggregated_source",
                 "aggregated_target", "aggregated_analyzer", "alert.type", "alert.assessment.impact.severity",
                 "alert.assessment.impact.completion" ]

        tmp["aggregated_target"] = tmp["aggregated_source"] = \
        tmp["aggregated_classification"] = tmp["aggregated_analyzer"] = "none"

        params["timeline_unit"] = "unlimited"
        self["sub_alert_display"] = utils.create_link("alert_listing", tmp + params)

    def _setClassificationInfos(self, dataset, message, ident):
        dataset["count"] = 1
        dataset["display"] = self.createMessageLink(ident, "alert_summary")
        dataset["severity"] = { "value": message["alert.assessment.impact.severity"] }
        dataset["completion"] = { "value": message["alert.assessment.impact.completion"] }

    def _setMessageTime(self, message):
        self["time"] = self.createTimeField(message["alert.create_time"], self.timezone)
    if (message["alert.analyzer_time"] != None and
        abs(int(message["alert.create_time"]) - int(message["alert.analyzer_time"])) > 60):
        self["analyzer_time"] = self.createTimeField(message["alert.analyzer_time"], self.timezone)
    else:
        self["analyzer_time"] = { "value": None }

    def addSensor(self, name, model, node_name):
        sensor = { }
        self["sensors"].append(sensor)

        if name:
            sensor["name"] = self.createInlineFilteredField("alert.analyzer.name", name, direction="analyzer")

        elif model:
            sensor["name"] = self.createInlineFilteredField("alert.analyzer.model", model, direction="analyzer")

        sensor["node_name"] = self.createInlineFilteredField("alert.analyzer.node.name", node_name, direction="analyzer")

    def setMessage(self, message, ident):
        self["infos"] = [ { } ]

        self.addSensor(message["alert.analyzer(-1).name"], message["alert.analyzer(-1).model"], message["alert.analyzer(-1).node.name"])
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
            self._setMessageSource(message)

        if not self["target"]:
            self._setMessageTarget(message)

    def setMessageDirectionGeneric(self, direction, object, value):
        self._initDirectionIfNeeded(direction)
        dataset = self[direction][-1]

        try:
            dset_name, function = self._getKnownValue(direction, object.replace("(0)", ""))
        except KeyError:
            return self._setMessageDirectionOther(dataset, direction, object, value)

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

    def setCriteriaForDeletion(self, delete_criteria):
        self["delete"] = urllib.quote_plus(" && ".join(delete_criteria))

    def setInfos(self, count, classification, severity, completion):
        infos = {
            "classification_references": "",
            "count": count,
            "classification": self.createInlineFilteredField("alert.classification.text", classification),
            "severity": { "value": severity },
            "completion": { "value": completion }
            }

        self["infos"].append(infos)

        return infos



class AlertListing(MessageListing, view.View):
    view_name = "alert_listing"
    view_parameters = AlertListingParameters
    view_permissions = [ User.PERM_IDMEF_VIEW ]
    view_template = "AlertListing"

    root = "alert"
    summary_view = "alert_summary"
    details_view = "alert_details"
    listed_alert = ListedAlert
    listed_aggregated_alert = ListedAggregatedAlert
    alert_type_default = ["alert.create_time", "alert.correlation_alert.name", "alert.overflow_alert.program", "alert.tool_alert.name"]

    def init(self, env):
        self._max_aggregated_classifications = int(env.config.general.getOptionValue("max_aggregated_classifications", 10))

    def _getMessageIdents(self, criteria, limit=-1, offset=-1):
        return self.env.idmef_db.getAlertIdents(criteria, limit, offset)

    def _fetchMessage(self, ident):
        return self.env.idmef_db.getAlert(ident)

    def _setMessage(self, message, ident):
        msg = self.listed_alert(self.view_name, self.env, self.parameters)
        msg.setMessage(message, ident)
        msg["aggregated"] = False
        msg["delete"] = ident

        return msg

    def _deleteMessage(self, ident):
        self.env.idmef_db.deleteAlert(ident)

    def _lists_have_same_content(self, l1, l2):
        l1 = copy.copy(l1)
        l2 = copy.copy(l2)
        l1.sort()
        l2.sort()

        return l1 == l2

    def _applyOptionalEnumFilter(self, criteria, column, object, values):
        if ( self.parameters.has_key(object) and not self._lists_have_same_content(self.parameters[object], values) ):
            new = [ ]
            for value in values:
                if value in self.parameters[object]:
                    if value == "none":
                        new.append("!%s" % (object))
                    else:
                        new.append("%s = '%s'" % (object, utils.escape_criteria(value)))

            criteria.append("(" + " || ".join(new) + ")")
            self.dataset[object] = self.parameters[object]
            self.dataset[column + "_filtered"] = True
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

        if not self._lists_have_same_content(self.parameters["alert.type"], self.alert_type_default):
            self.dataset["classification_filtered"] = True

    def _applyClassificationFilters(self, criteria):
        self._applyAlertTypeFilters(criteria)

        self._applyOptionalEnumFilter(criteria, "classification", "alert.assessment.impact.severity",
                                      ["info", "low", "medium", "high", "none"])
        self._applyOptionalEnumFilter(criteria, "classification", "alert.assessment.impact.completion",
                                      ["failed", "succeeded", "none"])
        self._applyOptionalEnumFilter(criteria, "classification", "alert.assessment.impact.type",
                                      ["other", "admin", "dos", "file", "recon", "user"])


    def _applyCheckboxFilters(self, criteria, type):
        def get_string((object, operator, value)):
            return "%s %s '%s'" % (object, operator, utils.escape_criteria(value))

        if self.parameters[type]:

            # If one object is specified more than one time, and since this object
            # can not have two different value, we want to apply an OR operator.
            #
            # We apply an AND operator between the different objects.

            merge = { }
            for obj in self.parameters[type]:
                if merge.has_key(obj[0]):
                    merge[obj[0]] += [ obj ]
                else:
                    merge[obj[0]] =  [ obj ]

            newcrit = ""
            for key in iter(merge):
                if len(newcrit) > 0:
                    newcrit += " && "

                newcrit += "(" + " || ".join(map(get_string, merge[key])) + ")"

            if newcrit:
                criteria.append(newcrit)

            self.dataset[type] = [ (path.replace("(0)", "").replace("(-1)", ""), operator, value) for path, operator, value in self.parameters[type] ]
            self.dataset["%s_filtered" % type] = True
        else:
            self.dataset[type] = [ ("", "", "") ]
            self.dataset["%s_filtered" % type] = False

    def _applyFilters(self, criteria):
        self._applyCheckboxFilters(criteria, "classification")
        self._applyClassificationFilters(criteria)

        self._applyCheckboxFilters(criteria, "source")
        self._applyCheckboxFilters(criteria, "target")
        self._applyCheckboxFilters(criteria, "analyzer")


    def _getMissingAggregatedInfos(self, message, path_value_hash, parameters, criteria2, aggregated_count):
        selection = [ ]
        index = 0
        selection_list = [ ]

        for path in ("alert.classification.text", "alert.analyzer(-1).node.name",
                     "alert.analyzer(-1).name", "alert.analyzer(-1).model", "alert.assessment.impact.severity",
                     "alert.assessment.impact.completion"):

            if not path_value_hash.has_key(path):
                selection_list += [ (path, index) ]
                index += 1

        selection = [ "%s/group_by" % i[0] for i in selection_list ]

        alert_list = self.env.idmef_db.getValues( selection + ["max(alert.messageid)", "count(alert.messageid)" ], criteria2)
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
               message.addSensor(analyzer_name, analyzer_model, analyzer_node_name)
               nodesraw[nodekey] = True

        res = alertsraw.values()
        res.sort(lambda x, y: cmp_severities(x[1], y[1]))

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
                    ident = self.env.idmef_db.getAlertIdents("alert.messageid = '%s'" % utils.escape_criteria(messageid))[0]
                    message.setMessage(self._fetchMessage(ident), ident)
                else:
                    infos["display"] = message.createMessageIdentLink(messageid, "alert_summary")
            else:
                entry_param = {}

                if classification:
                    entry_param["classification_object_%d" % self.parameters.max_index] = "alert.classification.text"
                    entry_param["classification_operator_%d" % self.parameters.max_index] = "="
                    entry_param["classification_value_%d" % self.parameters.max_index] = utils.escape_criteria(classification)

                entry_param["alert.assessment.impact.severity"] = severity or "none"
                entry_param["alert.assessment.impact.completion"] = completion or "none"

                entry_param["aggregated_target"] = \
                entry_param["aggregated_source"] = \
                entry_param["aggregated_analyzer"] = \
                entry_param["aggregated_classification"] = "none"

                infos["display"] = utils.create_link(self.view_name, self.parameters -
                                                     [ "offset", "aggregated_classification",
                                                       "aggregated_source", "aggregated_target", "aggregated_analyzer" ] +
                                                     parameters + entry_param)


    def _getPathValueType(self, path):
        p = prelude.idmef_path_new(path)
        t = prelude.idmef_path_get_value_type(p, -1)
        prelude.idmef_path_destroy(p)
        return t

    def _setAggregatedMessagesNoValues(self, criteria, ag_s, ag_t, ag_c, ag_a):
        ag_list = ag_s + ag_t + ag_c + ag_a

        ##
        selection = [ "%s/group_by" % path for path in ag_list ] + \
                    [ "count(alert.create_time)", "max(alert.create_time)/order_desc" ]

        results = self.env.idmef_db.getValues(selection, criteria)
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
            time_min = values[start + 1]

            criteria2 = criteria[:]
            delete_criteria = [ ]
            message = self.listed_aggregated_alert(self.view_name, self.env, self.parameters)

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
                    if self._getPathValueType(path) != prelude.IDMEF_VALUE_TYPE_STRING:
                        criterion = "! %s" % (path)
                    else:
                        criterion = "(! %s || %s == '')" % (path, path)
                else:
                    criterion = "%s == '%s'" % (path, utils.escape_criteria(str(value)))
                    if direction != None:
                        message.setMessageDirectionGeneric(direction, path, value)

                criteria2.append(criterion)
                delete_criteria.append(criterion)

            time_min = self.env.idmef_db.getValues(["alert.create_time/order_asc"], criteria2, limit=1)[0][0]
            time_max = self.env.idmef_db.getValues(["alert.create_time/order_desc"], criteria2, limit=1)[0][0]

            parameters = self._createAggregationParameters(aggregated_classification_values,
                                                           aggregated_source_values, aggregated_target_values, aggregated_analyzer_values)

            message["aggregated_classifications_total"] = aggregated_count
            message["aggregated_classifications_hidden"] = aggregated_count
            message["aggregated_classifications_hidden_expand"] = utils.create_link(self.view_name,
                                                                                    self.parameters -
                                                                                    [ "offset",
                                                                                      "aggregated_source",
                                                                                      "aggregated_target",
                                                                                      "aggregated_analyzer" ]
                                                                                    + parameters +
                                                                                    { "aggregated_classification":
                                                                                      "alert.classification.text" } )

            self._getMissingAggregatedInfos(message, valueshash, parameters, criteria2, aggregated_count)

            delete_criteria.append("alert.create_time >= '%s'" % time_min.toYMDHMS())
            delete_criteria.append("alert.create_time <= '%s'" % time_max.toYMDHMS())

            self.dataset["messages"].append(message)
            message.setTime(time_min, time_max)
            message.setCriteriaForDeletion(delete_criteria)

        return total_results


    def _createAggregationParameters(self, aggregated_classification_values, aggregated_source_values, aggregated_target_values, aggregated_analyzer_values):
        parameters = { }

        for values, column in ((aggregated_classification_values, "classification"),
                               (aggregated_source_values, "source"),
                               (aggregated_target_values, "target"),
                               (aggregated_analyzer_values, "analyzer")):
            i = self.parameters.max_index
            for path, value in zip(self.parameters["aggregated_%s" % column], values):
                if value == None:
                    continue

                parameters["%s_object_%d" % (column, i)] = path.replace("(0)", "").replace("(-1)", "")
                parameters["%s_operator_%d" % (column, i)] = "="
                parameters["%s_value_%d" % (column, i)] = value
                i += 1


        return parameters

    def _setMessages(self, criteria):
        self.dataset["messages"] = [ ]
        self.dataset["aggregated_source"] = self.parameters["aggregated_source"]
        self.dataset["aggregated_target"] = self.parameters["aggregated_target"]
        self.dataset["aggregated_classification"] = self.parameters["aggregated_classification"]
        self.dataset["aggregated_analyzer"] = self.parameters["aggregated_analyzer"]

        ag_s = self.parameters["aggregated_source"][:]
        ag_t = self.parameters["aggregated_target"][:]
        ag_c = self.parameters["aggregated_classification"][:]
        ag_a = self.parameters["aggregated_analyzer"][:]

        for l in ag_s, ag_t, ag_c, ag_a:
            while "none" in l:
                l.remove("none")

        if len(ag_s + ag_t + ag_c + ag_a) > 0:
            return self._setAggregatedMessagesNoValues(criteria, ag_s, ag_t, ag_c, ag_a)

        results = self.env.idmef_db.getAlertIdents(criteria)

        for ident in results[self.parameters["offset"] : self.parameters["offset"] + self.parameters["limit"]]:
            message = self.env.idmef_db.getAlert(ident)
            dataset = self._setMessage(message, ident)
            self.dataset["messages"].append(dataset)

        return len(results)

    def _setDatasetConstants(self):
        self.dataset["classification_filters"] = CLASSIFICATION_FILTERS
        self.dataset["classification_aggregations"] = CLASSIFICATION_AGGREGATIONS
        self.dataset["source_filters"] = SOURCE_FILTERS
        self.dataset["source_aggregations"] = SOURCE_AGGREGATIONS
        self.dataset["target_filters"] = TARGET_FILTERS
        self.dataset["target_aggregations"] = TARGET_AGGREGATIONS
        self.dataset["analyzer_filters"] = ANALYZER_FILTERS
        self.dataset["analyzer_aggregations"] = ANALYZER_AGGREGATIONS

    def render(self):
        MessageListing.render(self)

        self._deleteMessages()
        self._setDatasetConstants()

        self.dataset["filters"] = self.env.db.getAlertFilterNames(self.user.login)
        self.dataset["current_filter"] = self.parameters.get("filter", "")

        criteria = [ ]

        if self.parameters.has_key("filter"):
            filter = self.env.db.getAlertFilter(self.user.login, self.parameters["filter"])
            if filter:
                criteria.append("(%s)" % str(filter))

        start = end = None
        if self.parameters.has_key("timeline_unit") and self.parameters["timeline_unit"] != "unlimited":
            start, end = self._getTimelineRange()
            criteria.append("alert.create_time >= '%s' && alert.create_time < '%s'" % (str(start), str(end)))

        self._applyFilters(criteria)
        self._adjustCriteria(criteria)

        self._setTimeline(start, end)
        self._setNavPrev(self.parameters["offset"])

        self._setHiddenParameters()

        self.dataset["messages"] = [ ]
        total = self._setMessages(criteria)

        self.dataset["nav.from"] = self.parameters["offset"] + 1
        self.dataset["nav.to"] = self.parameters["offset"] + len(self.dataset["messages"])
        self.dataset["limit"] = self.parameters["limit"]
        self.dataset["total"] = total
        self.dataset["correlation_alert_view"] = False

        self._setNavNext(self.parameters["offset"], total)
        self._setTimezone()


class ListedSensorAlert(ListedAlert):
    view_name = "sensor_alert_listing"



class ListedSensorAggregatedAlert(ListedAggregatedAlert):
    view_name = "sensor_alert_listing"


class CorrelationAlertListing(AlertListing, view.View):
    view_name = "correlation_alert_listing"
    view_parameters = CorrelationAlertListingParameters
    alert_type_default = [ "alert.correlation_alert.name" ]


class ToolAlertListing(AlertListing, view.View):
    view_name = "tool_alert_listing"
    view_parameters = ToolAlertListingParameters
    alert_type_default = [ "alert.tool_alert.name" ]



class SensorAlertListing(AlertListing, view.View):
    view_name = "sensor_alert_listing"
    view_parameters = SensorAlertListingParameters
    view_permissions = [ User.PERM_IDMEF_VIEW ]
    view_template = "SensorAlertListing"

    listed_alert = ListedSensorAlert
    listed_aggregated_alert = ListedSensorAggregatedAlert

    def _setHiddenParameters(self):
        AlertListing._setHiddenParameters(self)
        self.dataset["hidden_parameters"].append(("analyzerid", self.parameters["analyzerid"]))

    def render(self):
        AlertListing.render(self)
        self.dataset["analyzer_infos"] = self.env.idmef_db.getAnalyzer(self.parameters["analyzerid"])
