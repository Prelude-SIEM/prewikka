# Copyright (C) 2004,2005,2006 PreludeIDS Technologies. All Rights Reserved.
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

import copy, re, urllib
from prelude import idmef_path_new, idmef_path_get_value_type, IDMEF_VALUE_TYPE_STRING
from prewikka import view, User, utils
from prewikka.views.messagelisting import MessageListingParameters, MessageListing, ListedMessage



def cmp_severities(x, y):
    d = { None: 0, "info": 1, "low": 2, "medium": 3, "high": 4 }
    return d[y] - d[x]



class AlertListingParameters(MessageListingParameters):
    allow_extra_parameters = True

    def register(self):
        self.max_index = 0
        MessageListingParameters.register(self)
        self.optional("aggregated_source", list, [ "alert.source(0).node.address(0).address" ], save=True)
        self.optional("aggregated_target", list, [ "alert.target(0).node.address(0).address" ], save=True)
        self.optional("aggregated_classification", list, [ "none" ], save=True)
        self.optional("filter", str, save=True)
        self.optional("alert.classification.text", list, [ ], save=True)
        self.optional("alert.assessment.impact.severity", list, [ ], save=True)
        self.optional("alert.assessment.impact.completion", list, [ ], save=True)
        self.optional("alert.assessment.impact.type", list, [ ], save=True)

    def _loadColumnParam(self, view_name, user, paramlist, column):
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
            
            try:
                value = paramlist["%s_value_%s" % (column, num)]
            except KeyError:
                continue

            do_append = True
            for tmp in sorted:
                if tmp[1] == object and tmp[2] == value:
                    do_append = False
                    break

            if do_append:
                sorted.append((num, object, value))

        sorted.sort()
        self[column] = [ (i[1], i[2]) for i in sorted ]


        if self.has_key("_save"):
            user.delConfigValueMatch(view_name, "%s_object_%%" % (column))
            user.delConfigValueMatch(view_name, "%s_value_%%" % (column))

            for num, obj, value in sorted:
                user.setConfigValue(view_name, "%s_object_%d" % (column, num), obj)
                user.setConfigValue(view_name, "%s_value_%d" % (column, num), value)

        return ret
    
    def normalize(self, view_name, user):
        MessageListingParameters.normalize(self, view_name, user)

        for severity in self["alert.assessment.impact.severity"]:
            if not severity in ("info", "low", "medium", "high", "none"):
                raise view.InvalidParameterValueError("alert.assessment.impact.severity", severity)
        
        for completion in self["alert.assessment.impact.completion"]:
            if not completion in ("succeeded", "failed", "none"):
                raise view.InvalidParameterValueError("alert.assessment.impact.completion", completion)

        for type in self["alert.assessment.impact.type"]:
            if not type in ("other", "admin", "dos", "file", "recon", "user"):
                raise view.InvalidParameterValueError("alert.assessment.impact.type", type)

        load_saved = True
        for column in "classification", "source", "target", "analyzer":
            ret = self._loadColumnParam(view_name, user, self, column)
            if ret:
                load_saved = False
        
        if load_saved and self.has_key("_load") and user.configuration.has_key(view_name):
            for column in "classification", "source", "target", "analyzer":
                self._loadColumnParam(view_name, user, user.configuration[view_name], column)
            
        for category in "classification", "source", "target":
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
        self.mandatory("analyzerid", long)

    def normalize(self, view_name, user):
        AlertListingParameters.normalize(self, view_name, user)
        self["analyzer"].insert(0, ("alert.analyzer.analyzerid", str(self["analyzerid"])))





class ListedAlert(ListedMessage):
    view_name = "alert_listing"

    def _getKnownValue(self, direction, key):
        return { "alert.%s.interface" % direction: ("interface", None),
                 "alert.%s.service.port" % direction: ("service", None),
                 "alert.%s.process.name" % direction: ("process", None),
                 "alert.%s.user.user_id.name" % direction: ("users", None),
                 "alert.%s.file.path" % direction: ("files", self._setMessageDirectionTargetFile),
                 "alert.%s.node.address.address" % direction: ("addresses", self._setMessageDirectionAddress),
                 "alert.%s.node.name" % direction: ("addresses", self._setMessageDirectionNodeName), 
                 }[key]
    
    def _initValue(self, dataset, name, value):
        dataset[name] = value

    def _initDirection(self, dataset):
        self._initValue(dataset, "interface", { "value": None })
        self._initValue(dataset, "protocol", { "value": None })
        self._initValue(dataset, "service", { "value": None })
        self._initValue(dataset, "process", { "value": None })
        self._initValue(dataset, "users", [ ])
        self._initValue(dataset, "files", [ ])
        self._initValue(dataset, "addresses", [ ])

        return dataset
    
    def _initDirectionIfNeeded(self, direction):
        if len(self[direction]) == 0:        
            self[direction].append(self._initDirection({ }))
            
    def reset(self):
        self["sensors"] = [ ]    
        self["correlation_alert_name"] = None
        self["source"] = [ ]
        self["target"] = [ ]
        
    def __init__(self, *args, **kwargs):        
        apply(ListedMessage.__init__, (self, ) + args, kwargs)
        self.reset()
        
    def _setMessageDirectionAddress(self, direction, address, category=None):        
        hfield = self.createHostField("alert.%s.node.address.address" % direction, address, category, direction=direction)
        self._initDirectionIfNeeded(direction)
        self[direction][-1]["addresses"].append(hfield)

    def _setMessageDirectionNodeName(self, direction, name, extra=None):
        self._initDirectionIfNeeded(direction)
        self[direction][-1]["addresses"].append(self.createHostField("alert.%s.node.name" % direction, name, None, direction=direction))

    def _setMessageDirectionTargetFile(self, direction, path, extra=None):
        self["target"][-1]["files"].append(self.createInlineFilteredField("alert.target.file.path", path, direction="target"))
        
    def _setMessageDirectionGeneric(self, direction, object, value, extra=None):
        dset_name, function = self._getKnownValue(direction, object.replace("(0)", ""))        
                        
        self._initDirectionIfNeeded(direction)
        if function:
            function(direction, value, extra)
        else:
            if type(self[direction][-1][dset_name]) is list:
                self[direction][-1][dset_name].append({ "value": value })
            else:
                self[direction][-1][dset_name]["value"] = value

            
    def _setMessageDirection(self, dataset, direction, obj):
        
        def set_main_and_extra_values(dataset, name, object_main, object_extra):
            if object_main != None:
                dataset[name] = { "value": object_main }
                dataset[name + "_extra"] = { "value": object_extra }
            else:
                dataset[name] = { "value": object_extra }
                dataset[name + "_extra"] = { "value": None }
            
        dataset["interface"] = { "value": obj["interface"] }
        
        for userid in obj["user.user_id"]:
            user = { }
            dataset["users"].append(user)
            set_main_and_extra_values(user, "user", userid["name"], userid["number"])

        name = obj["node.name"]
        if name != None:
            self._setMessageDirectionNodeName(direction, name)
            
        for addr in obj["node.address"]:
            self._setMessageDirectionAddress(direction, addr["address"], addr["category"])
                        
        set_main_and_extra_values(dataset, "process", obj["process.name"], obj["process.pid"])

        proto = None
        if obj["service.iana_protocol_name"]:
            proto = obj["service.iana_protocol_name"]
            
        elif obj["service.iana_protocol_number"]:
            num = obj["service.iana_protocol_number"]
            proto = utils.protocol_number_to_name(num)

        if not proto:
            proto = obj["service.protocol"]
       
        set_main_and_extra_values(dataset, "protocol", proto, None)
        set_main_and_extra_values(dataset, "service", obj["service.port"], None)

        dataset["files"] = []

    def setMessageSource(self, message):
        for source in message["alert.source"]:
            dataset = { }
            self["source"].append(dataset)
            
            self._initDirection(dataset)
            self._setMessageDirection(dataset, "source", source)
            
    def setMessageTarget(self, message):
        
        for target in message["alert.target"]:
            dataset = { }
            self["target"].append(dataset)
            
            self._initDirection(dataset)
            self._setMessageDirection(dataset, "target", target)

            flist = []
            for f in target["file"]:
                if f["path"] in flist:
                    continue
                
                flist.append(f["path"])
                self._setMessageDirectionTargetFile("target", f["path"])
        

    def setMessageClassificationReferences(self, dataset, message):
        val = self.env.config.general.getOptionValue("external_link_new_window", "true")
        if (not val and self.env.config.general.has_key("external_link_new_window")) or \
           (val == None or val.lower() in ["true", "yes"]):
            external_link_target = "_blank"
        else:
            external_link_target = "_self"

        dataset["classification_references"] = [ ]            
        for ref in message["alert.classification.reference"]:
            fstr = ""

            origin = ref["origin"]
            if origin:
                fstr += origin

            name = ref["name"]
            if name:
                fstr += ":" + name

            dataset["classification_references"].append((ref["url"], fstr))

    def setMessageClassification(self, dataset, message):
        self.setMessageClassificationReferences(dataset, message)
        dataset["classification"] = self.createInlineFilteredField("alert.classification.text",
                                                                   message["alert.classification.text"])
        
    def setMessageCorrelationAlertInfo(self, dataset, message, ident):
        fetch_source_info=True
        fetch_target_info=True
        fetch_classification_info=True
                
        if not message["alert.correlation_alert"]:
            return

        if message["alert.source"]:
            fetch_source_info = False

        if message["alert.target"]:
            fetch_target_info = False

        if message["alert.classification"]:
            fetch_classification_info = False

        i = 0
        ca_params = { }

        for alertident in message["alert.correlation_alert.alertident"]:
            # IDMEF draft 14 page 27
            # If the "analyzerid" is not provided, the alert is assumed to have come
            # from the same analyzer that is sending the CorrelationAlert.
            
            analyzerid = alertident["analyzerid"]
            if not analyzerid:
                analyzerid = message["alert.analyzer(-1).analyzerid"]
                
            ca_params["analyzer_object_%d" % i] = "alert.analyzer.analyzerid"
            ca_params["analyzer_value_%d" % i] = analyzerid
            
            ca_params["classification_object_%d" % i] = "alert.messageid"
            ca_params["classification_value_%d" % i] = alertident["alertident"]

            criteria = "alert.messageid = '%s' && alert.analyzer.analyzerid = '%s'" % (alertident["alertident"], analyzerid)
            result = self.env.idmef_db.getAlertIdents(criteria, 1, -1)
            if len(result) == 0:
                continue
            
            i += 1
            if i > 1:
                continue
            
            ca_idmef = self.env.idmef_db.getAlert(result[0])

            if fetch_classification_info:
                self.setMessageClassification(dataset, ca_idmef)
                
            if fetch_source_info:
                self.setMessageSource(ca_idmef)

            if fetch_target_info:
                self.setMessageTarget(ca_idmef)

        ca_params["timeline_unit"] = "unlimited"

        self["correlation_alert_name"] = message["alert.correlation_alert.name"]
        self["correlation_alert_link"] = self.createMessageLink(ident, "alert_summary")
        self["correlated_alert_number"] = i
                        
        tmp = self.parameters
        tmp -= [ "timeline_unit", "timeline_value", "offset",
                 "aggregated_classification", "aggregated_source",
                 "aggregated_target", "alert.assessment.impact.severity",
                 "alert.assessment.impact.completion", "_load", "_save" ]

        tmp["aggregated_target"] = \
        tmp["aggregated_source"] = \
        tmp["aggregated_classification"] = "none"
        
        self["correlated_alert_display"] = utils.create_link(self.view_name, tmp + ca_params)

    def setMessageInfo(self, message, ident):
        self["infos"] = [ { } ]

        dataset = self["infos"][0]
        dataset["count"] = 1
        dataset["display"] = self.createMessageLink(ident, "alert_summary")
        dataset["severity"] = { "value": message["alert.assessment.impact.severity"] }
        dataset["completion"] = { "value": message["alert.assessment.impact.completion"] }

        self.setMessageClassification(dataset, message)
        self.setMessageCorrelationAlertInfo(dataset, message, ident)

    def addSensor(self, name, node_name):
        sensor = { }
        self["sensors"].append(sensor)
        sensor["name"] = self.createInlineFilteredField("alert.analyzer.name", name, direction="analyzer")
        sensor["node_name"] = { "value": node_name }
        
    def setMessageTime(self, message):
        self["time"] = self.createTimeField(message["alert.create_time"], self.timezone)
	if (message["alert.analyzer_time"] != None and
	    abs(int(message["alert.create_time"]) - int(message["alert.analyzer_time"])) > 60):
	    self["analyzer_time"] = self.createTimeField(message["alert.analyzer_time"], self.timezone)
	else:
	    self["analyzer_time"] = { "value": None }

    def setMessageCommon(self, message):
        self["correlated_alert_display"] = None            
        self["correlation_alert_name"] = None
        
        self.setMessageSource(message)
        self.setMessageTarget(message)

    def setMessage(self, message, ident):
        self.setMessageCommon(message)
        self.addSensor(message["alert.analyzer(-1).name"], message["alert.analyzer(-1).node.name"])
        self.setMessageTime(message)
        self.setMessageInfo(message, ident)
        


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
    messageid_object = "alert.messageid"
    analyzerid_object = "alert.analyzer.analyzerid"
    summary_view = "alert_summary"
    details_view = "alert_details"
    listed_alert = ListedAlert
    listed_aggregated_alert = ListedAggregatedAlert

    def init(self, env):
        self._max_aggregated_classifications = int(env.config.general.getOptionValue("max_aggregated_classifications", 10))

    def _getMessageIdents(self, criteria, limit=-1, offset=-1):
        return self.env.idmef_db.getAlertIdents(criteria, limit, offset)

    def _countMessages(self, criteria):
        return self.env.idmef_db.countAlerts(criteria)

    def _fetchMessage(self, ident):
        return self.env.idmef_db.getAlert(ident)

    def _setMessage(self, message, ident):
        msg = self.listed_alert(self.env, self.parameters)
        msg.setMessage(message, ident)
        msg["aggregated"] = False
        msg["delete"] = ident
        
        return msg
    
    def _getFilters(self, storage, login):
        return storage.getAlertFilters(login)

    def _getFilter(self, storage, login, name):
        return storage.getAlertFilter(login, name)

    def _deleteMessage(self, ident):
        self.env.idmef_db.deleteAlert(ident)

    def _applyOptionalEnumFilter(self, criteria, column, object, values):
            
        def lists_have_same_content(l1, l2):
            l1 = copy.copy(l1)
            l2 = copy.copy(l2)
            l1.sort()
            l2.sort()

            return l1 == l2
        
        if ( len(self.parameters[object]) != 0 and
             not lists_have_same_content(self.parameters[object], values)):

            new = [ ]
            for value in self.parameters[object]:
                if value == "none":
                    new.append("! %s" % object)
                else:
                    new.append("%s == '%s'" % (object, utils.escape_criteria(value)))

            criteria.append("(" + " || ".join(new) + ")")
            self.dataset[object] = self.parameters[object]
            self.dataset[column + "_filtered"] = True
        else:
            self.dataset[object] = values

    def _applyClassificationFilters(self, criteria):
        self._applyOptionalEnumFilter(criteria, "classification", "alert.assessment.impact.severity",
                                      ["info", "low", "medium", "high", "none"])
        self._applyOptionalEnumFilter(criteria, "classification", "alert.assessment.impact.completion",
                                      ["failed", "succeeded", "none"])
        self._applyOptionalEnumFilter(criteria, "classification", "alert.assessment.impact.type",  
                                      ["other", "admin", "dos", "file", "recon", "user"])  

    def _applyCheckboxFilters(self, criteria, type):
            
        def get_operator(object):
            if object in ("alert.source.service.port", "alert.target.service.port", "alert.messageid", "alert.analyzerid"):
                return "="

            return "<>*"
        
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

                newcrit += "(" + " || ".join(map(lambda (object, value): "%s %s '%s'" %
                                                 (object, get_operator(object), utils.escape_criteria(value)),
                                                 merge[key])) + ")"

            if newcrit:
                criteria.append(newcrit)
            
            self.dataset[type] = self.parameters[type]
            self.dataset["%s_filtered" % type] = True
        else:
            self.dataset[type] = [ ("", "") ]
            self.dataset["%s_filtered" % type] = False
        
    def _applyFilters(self, criteria):
        self._applyCheckboxFilters(criteria, "classification")
        self._applyClassificationFilters(criteria)
        
        self._applyCheckboxFilters(criteria, "source")
        self._applyCheckboxFilters(criteria, "target")
        self._applyCheckboxFilters(criteria, "analyzer")

    def _ignoreAtomicIfNeeded(self, idmef, ignore_list):

        for ad in idmef["alert.additional_data"]:
            if ad["data"] != "ignore_atomic_event":
                continue
            
            for ca in idmef["alert.correlation_alert.alertident"]:
                # See FIXME ahead.
                # ignore_list.append((ca["analyzerid"] or idmef["alert.analyzer(-1).analyzerid"], ca["alertident"]))
                ignore_list.append(ca["alertident"])
                
            break

    def _isAtomicEventIgnored(self, idmef, atomic_ignore_list):
        #
        # FIXME: LML really need to set analyzerid at the tail.
        # if ( idmef["alert.analyzer(-1).analyzerid"], idmef["alert.messageid"]) in atomic_ignore_list:            
        if idmef["alert.messageid"] in atomic_ignore_list:
            return True
        else:                
            return False
                
    def _setAggregatedMessagesNoValues(self, criteria, ag_s, ag_t, ag_c):
        atomic_ignore_list = []
        ag_list = ag_s + ag_t + ag_c
        
        selection = [ "alert.messageid", "alert.create_time" ]
        results2 = self.env.idmef_db.getValues(selection, criteria + ["alert.correlation_alert.name"])

        results = []
        for row in results2:
            ca_ident = self.env.idmef_db.getAlertIdents(criteria + [ "alert.messageid = %s" % row[0] ], 1, -1)[0]
            message = self.env.idmef_db.getAlert(ca_ident)
            self._ignoreAtomicIfNeeded(message, atomic_ignore_list)
            results += [ [ row[0] ] + [None for i in ag_list] + [ca_ident] + [message] + [ row[1] ] ]
            
        ignore_criteria = [ ]
        for messageid in atomic_ignore_list:
            ignore_criteria += [ "alert.messageid != '%s'" % messageid ]
            
        ##
        selection = [ "%s/group_by" % path for path in ag_list ] + \
                    [ "count(alert.create_time)", "max(alert.create_time)/order_desc" ]

        results += self.env.idmef_db.getValues(selection, criteria + [ "! alert.correlation_alert.name"] + ignore_criteria)
        results.sort(lambda x, y: int(int(y[-1]) - int(x[-1])))
        total_results = len(results)
           
        for values in results[self.parameters["offset"]:self.parameters["offset"]+self.parameters["limit"]]:
            start = 0
            aggregated_source_values = []
            aggregated_target_values = []
            aggregated_classification_values = []
            
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

            aggregated_count = values[start]
            if aggregated_count == None:
                message = values[-2]
                dataset = self._setMessage(message, values[-3])
                self.dataset["messages"].append(dataset)
                continue
            
            criteria2 = criteria[:]
            delete_criteria = [ ]
            message = self.listed_aggregated_alert(self.env, self.parameters)

            for path, value in zip(ag_list, values[:start]):
                                
                if path.find("source") != -1:
                    direction = "source"
                    value_category = aggregated_source_values[-1]
                elif path.find("target") != -1:
                    direction = "target"
                    value_category = aggregated_target_values[-1]
                else:
                    direction = None
                    
                if re.compile("alert.%s(\([0-9\*]*\))?\.node\.address(\([0-9\*]*\))?\.category" % direction).match(path):
                    continue
                
                if not value:
                    if idmef_path_get_value_type(idmef_path_new(path), -1) != IDMEF_VALUE_TYPE_STRING:
                        criterion = "! %s" % (path)
                    else:
                        criterion = "(! %s || %s == '')" % (path, path)
                else:
                    criterion = "%s == '%s'" % (path, utils.escape_criteria(str(value)))
                    if direction in ("source", "target"):
                        message._setMessageDirectionGeneric(direction, path, value, value_category)
                       
                criteria2.append(criterion)
                delete_criteria.append(criterion)

            time_min = self.env.idmef_db.getValues(["alert.create_time/order_asc"], criteria2, limit=1)[0][0]
            time_max = self.env.idmef_db.getValues(["alert.create_time/order_desc"], criteria2, limit=1)[0][0]
            
            delete_criteria.append("alert.create_time >= '%s'" % time_min.toYMDHMS())
            delete_criteria.append("alert.create_time <= '%s'" % time_max.toYMDHMS())

            ident = self.env.idmef_db.getAlertIdents(criteria2 + ignore_criteria, limit=1)[0]
            
            self.dataset["messages"].append(message)
            message.setTime(time_min, time_max)
            message.setCriteriaForDeletion(delete_criteria)

            res = self.env.idmef_db.getValues(["alert.analyzer(-1).name/group_by",
                                               "alert.analyzer(-1).node.name/group_by"],
                                              criteria2)

            for analyzer_name, analyzer_node_name in res:
                message.addSensor(analyzer_name, analyzer_node_name)

            res = self.env.idmef_db.getValues(["alert.classification.text/group_by",
                                               "alert.assessment.impact.severity/group_by",
                                               "alert.assessment.impact.completion/group_by",
                                               "count(alert.create_time)"], criteria2 + ignore_criteria)
                
            res.sort(lambda x, y: cmp_severities(x[1], y[1]))

            parameters = self._createAggregationParameters(aggregated_classification_values,
                                                           aggregated_source_values, aggregated_target_values)

            message["aggregated_classifications_total"] = aggregated_count
            message["aggregated_classifications_hidden"] = aggregated_count
            message["aggregated_classifications_hidden_expand"] = utils.create_link(self.view_name,
                                                                                    self.parameters -
                                                                                    [ "offset",
                                                                                      "aggregated_source",
                                                                                      "aggregated_target" ]
                                                                                    + parameters +
                                                                                    { "aggregated_classification":
                                                                                      "alert.classification.text" } )

            if len(res[:self._max_aggregated_classifications]) > 1:
                classification = None
            else:
                classification = res[0][0] or ""

            result_count = 0

            for classification, severity, completion, count in res:
                if result_count >= self._max_aggregated_classifications:
                    result_count += 1
                    continue
                result_count += 1

                message["aggregated_classifications_hidden"] -= count
                infos = message.setInfos(count, classification, severity, completion)
                    
                if count == 1:
                    if aggregated_count == 1:                            
                        message.reset()
                        message.setMessage(self._fetchMessage(ident), ident)
                                                    
                    criteria3 = criteria2[:]

                    for path, value, is_string in (("alert.classification.text", classification, True),
                                                       ("alert.assessment.impact.severity", severity, False),
                                                       ("alert.assessment.impact.completion", completion, False)):
                        if value:
                            criteria3.append("%s == '%s'" % (path, utils.escape_criteria(value)))
                        else:
                            if is_string:
                                criteria3.append("(! %s || %s == '')" % (path, path))
                            else:
                                criteria3.append("! %s" % path)

                    ident = self.env.idmef_db.getAlertIdents(criteria3, limit=1)[0]
                    infos["display"] = message.createMessageLink(ident, "alert_summary")
                else:
                    entry_param = {}
                        
                    if classification:
                        entry_param["classification_object_%d" % self.parameters.max_index] = "alert.classification.text"
                        entry_param["classification_value_%d" % self.parameters.max_index] = utils.escape_criteria(classification)

                    if severity:
                        entry_param["alert.assessment.impact.severity"] = severity

                    if completion:
                        entry_param["alert.assessment.impact.completion"] = completion

                    entry_param["aggregated_target"] = \
                    entry_param["aggregated_source"] = \
                    entry_param["aggregated_classification"] = "none"
                        
                    infos["display"] = utils.create_link(self.view_name, self.parameters -
                                                         [ "offset", "aggregated_classification",
                                                           "aggregated_source", "aggregated_target", "_load", "_save" ] +
                                                         parameters + entry_param)
                        
        return total_results
    

    def _createAggregationParameters(self, aggregated_classification_values, aggregated_source_values, aggregated_target_values):
        parameters = { }
                
        i = self.parameters.max_index
        for path, value in zip(self.parameters["aggregated_classification"], aggregated_classification_values):
            if value == None:
                continue
            
            parameters["classification_object_%d" % i] = path.replace("(0)", "")
            parameters["classification_value_%d" % i] = value
            i += 1
            
        i = self.parameters.max_index
        for path, value in zip(self.parameters["aggregated_source"], aggregated_source_values):
            if value == None or path == "alert.source(0).node.address(0).category":
                continue
            
            parameters["source_object_%d" % i] = path.replace("(0)", "")
            parameters["source_value_%d" % i] = value
            i += 1
        
        i = self.parameters.max_index
        for path, value in zip(self.parameters["aggregated_target"], aggregated_target_values):
            if value == None or path == "alert.target(0).node.address(0).category":
                continue
            
            parameters["target_object_%d" % i] = path.replace("(0)", "")
            parameters["target_value_%d" % i] = value
            i += 1
            
        return parameters
    
    def _setMessages(self, criteria):
        self.dataset["messages"] = [ ]
        self.dataset["aggregated_source"] = self.parameters["aggregated_source"]
        self.dataset["aggregated_target"] = self.parameters["aggregated_target"]
        self.dataset["aggregated_classification"] = self.parameters["aggregated_classification"]
        
        if "alert.source(0).node.address(0).address" in self.parameters["aggregated_source"]:
            self.parameters["aggregated_source"] += [ "alert.source(0).node.address(0).category" ]

        if "alert.target(0).node.address(0).address" in self.parameters["aggregated_target"]:
            self.parameters["aggregated_target"] += [ "alert.target(0).node.address(0).category" ]

        ag_s = self.parameters["aggregated_source"][:]
        ag_t = self.parameters["aggregated_target"][:]
        ag_c = self.parameters["aggregated_classification"][:]

        for l in ag_s, ag_t, ag_c:
            while "none" in l:
                l.remove("none")

        if len(ag_s + ag_t + ag_c) > 0:
            ret = self._setAggregatedMessagesNoValues(criteria, ag_s, ag_t, ag_c)

            try: self.parameters["aggregated_source"].remove("alert.source(0).node.address(0).category")
            except: pass
            
            try: self.parameters["aggregated_target"].remove("alert.target(0).node.address(0).category")
            except: pass
            
            return ret
        
        atomic_ignore_list = []
        for ident in self.env.idmef_db.getAlertIdents(criteria, self.parameters["limit"], self.parameters["offset"]):
            message = self.env.idmef_db.getAlert(ident)

            if self._isAtomicEventIgnored(message, atomic_ignore_list):
                continue
            
            self._ignoreAtomicIfNeeded(message, atomic_ignore_list)

            dataset = self._setMessage(message, ident)
            self.dataset["messages"].append(dataset)

        return self.env.idmef_db.countAlerts(criteria)
            
    def _setDatasetConstants(self):
        self.dataset["available_aggregations"] = { }
        self.dataset["available_aggregations"]["classification"] = ( ("", "none"),
                                                                     ("classification", "alert.classification.text"))
        
        for category in "source", "target":
            tmp = (("", "none"),
                   ("address", "alert.%s(0).node.address(0).address" % category),
                   ("node name", "alert.%s(0).node.name" % category),
                   ("user", "alert.%s(0).user.user_id(0).name" % category),
                   ("process", "alert.%s(0).process.name" % category),
                   ("service", "alert.%s(0).service.name" % category),
                   ("port", "alert.%s(0).service.port" % category),
                   ("interface", "alert.%s(0).interface" % category))
            self.dataset["available_aggregations"][category] = tmp
            
    def render(self):
        self._deleteMessages()
        self._setDatasetConstants()
        
        self.dataset["filters"] = self.env.db.getAlertFilterNames(self.user.login)
        self.dataset["current_filter"] = self.parameters.get("filter", "")
        
        criteria = [ ]
        
        if self.parameters.has_key("filter"):
            filter = self.env.db.getAlertFilter(self.user.login, self.parameters["filter"])
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


        self._setNavNext(self.parameters["offset"], total)
        self._setTimezone()


class ListedSensorAlert(ListedAlert):
    view_name = "sensor_alert_listing"



class ListedSensorAggregatedAlert(ListedAggregatedAlert):
    view_name = "sensor_alert_listing"



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
