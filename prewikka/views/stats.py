# Copyright (C) 2005-2009 PreludeIDS Technologies. All Rights Reserved.
# Author: Nicolas Delon <nicolas.delon@prelude-ids.com>
# Author: Yoann Vandoorselaere <yoann.v@prelude-ids.com>
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

import sys
import time
import copy
import urllib
import datetime

from prewikka import User, view, Chart, utils, resolve

try:
    import GeoIP
    geoip = GeoIP.new(GeoIP.GEOIP_MEMORY_CACHE)
except:
    geoip = None


DEFAULT_WIDTH = 800
DEFAULT_HEIGHT = 450


class DistributionStatsParameters(view.Parameters):
    def register(self):
        self.optional("timeline_type", str, default="hour", save=True)
        self.optional("from_year", int, save=True)
        self.optional("from_month", int, save=True)
        self.optional("from_day", int, save=True)
        self.optional("from_hour", int, save=True)
        self.optional("from_min", int, save=True)
        self.optional("to_year", int, save=True)
        self.optional("to_month", int, save=True)
        self.optional("to_day", int, save=True)
        self.optional("to_hour", int, save=True)
        self.optional("to_min", int, save=True)
        self.optional("filter", str, save=True)
        self.optional("idmef_filter", str)
        self.optional("apply", str)

    def normalize(self, view_name, user):
        do_save = self.has_key("_save")

        view.Parameters.normalize(self, view_name, user)

        if do_save and not self.has_key("filter"):
            user.delConfigValue(view_name, "filter")


class StatsSummary(view.View):
    view_name = "stats_summary"
    view_template = "StatsSummary"
    view_permission = [ ]
    view_parameters = view.Parameters

    def render(self):
        pass




class DistributionStats(view.View):
    view_template = "Stats"
    view_permissions = [ User.PERM_IDMEF_VIEW ]
    view_parameters = DistributionStatsParameters

    def _getNameFromMap(self, name, names_and_colors):
        if names_and_colors.has_key(name):
            return names_and_colors[name][0]

        return name

    def _namesAndColors2ColorMap(self, names_and_colors):
        d = utils.OrderedDict()
        for name, color in names_and_colors.values():
            d[name] = color

        return d

    def _getBaseURL(self):
        start = long(time.mktime(self._period_start))

        if self.parameters["timeline_type"] in ("month", "day", "hour"):
            unit = self.parameters["timeline_type"]
            value = 1
        else:
            delta = long(time.mktime(self._period_end)) - start
            if delta > 3600:
                unit = "day"
                value = delta / (24 * 3600) + 1
            else:
                unit = "hour"
                value = delta / 3600 + 1

        filter_str = ""
        if self.parameters.has_key("filter"):
            filter_str = "&amp;" + urllib.urlencode({"filter": self.parameters["filter"]})

        return utils.create_link("alert_listing", { "timeline_unit": unit,
                                                    "timeline_value": value,
                                                    "timeline_start": start }) + filter_str


    def _addDistributionChart(self, title, value_name, width, height, path, criteria, sub_url_handler, limit=-1, dns=False, names_and_colors={}):
        base_url = self._getBaseURL()
        chart = { "title": title, "value_name": value_name, "data": [ ] }

        distribution = Chart.DistributionChart(self.user, width, height)
        if names_and_colors:
            distribution.setColorMap(self._namesAndColors2ColorMap(names_and_colors))

        chart["chart"] = distribution
        chart["render"] = (distribution, title, base_url)

        results = self.env.idmef_db.getValues([ path + "/group_by", "count(%s)/order_desc" % path ],
                                              criteria=criteria + [ path ], limit=limit)
        if results:
            total = reduce(lambda x, y: x + y, [ count for value, count in results ])
            chart["total"] = total
            for value, count in results:
                if dns:
                    v = resolve.AddressResolve(value)
                else:
                    v = self._getNameFromMap(value, names_and_colors)

                chart["data"].append((v, base_url + "&amp;" + sub_url_handler(value), count, "%.1f" % (count / float(total) * 100)))
                distribution.addLabelValuePair(v, count, base_url + "&amp;" + sub_url_handler(value))

        distribution.render(title)
        self.dataset["charts"].append(chart)

    def _processTimeCriteria(self):
        now = time.time()
        self._period_end = time.localtime(now)

        if self.parameters["timeline_type"] == "hour":
            self.dataset["timeline_hour_selected"] = "selected=\"selected\""
            self._period_start = time.localtime(now - 3600)

        elif self.parameters["timeline_type"] == "day":
            self.dataset["timeline_day_selected"] = "selected=\"selected\""
            tm = time.localtime(now - 24 * 3600)
            self._period_start = time.localtime(now - 24 * 3600)

        elif self.parameters["timeline_type"] == "month":
            self.dataset["timeline_month_selected"] = "selected=\"selected\""
            tm = list(time.localtime(now))
            tm[1] -= 1
            self._period_start = time.localtime(time.mktime(tm))

        else:
            self.dataset["timeline_custom_selected"] = "selected=\"selected\""
            self._period_start = time.struct_time((self.parameters["from_year"], self.parameters["from_month"],
                                                   self.parameters["from_day"], self.parameters["from_hour"],
                                                   self.parameters["from_min"], 0, 0, 0, -1))
            self._period_end = time.struct_time((self.parameters["to_year"], self.parameters["to_month"],
                                                 self.parameters["to_day"], self.parameters["to_hour"],
                                                 self.parameters["to_min"], 0, 0, 0, -1))

        self.dataset["from_year"] = "%.4d" % self._period_start.tm_year
        self.dataset["from_month"] = "%.2d" % self._period_start.tm_mon
        self.dataset["from_day"] = "%.2d" % self._period_start.tm_mday
        self.dataset["from_hour"] = "%.2d" % self._period_start.tm_hour
        self.dataset["from_min"] = "%.2d" % self._period_start.tm_min

        self.dataset["to_year"] = "%.4d" % self._period_end.tm_year
        self.dataset["to_month"] = "%.2d" % self._period_end.tm_mon
        self.dataset["to_day"] = "%.2d" % self._period_end.tm_mday
        self.dataset["to_hour"] = "%.2d" % self._period_end.tm_hour
        self.dataset["to_min"] = "%.2d" % self._period_end.tm_min

        criteria = [ "alert.create_time >= '%d-%d-%d %d:%d:%d' && alert.create_time < '%d-%d-%d %d:%d:%d'" % \
                     (self._period_start.tm_year, self._period_start.tm_mon, self._period_start.tm_mday,
                      self._period_start.tm_hour, self._period_start.tm_min, self._period_start.tm_sec,
                      self._period_end.tm_year, self._period_end.tm_mon, self._period_end.tm_mday,
                      self._period_end.tm_hour, self._period_end.tm_min, self._period_end.tm_sec) ]

        return criteria

    def _processFilterCriteria(self):
        c = [ ]
        if self.parameters.has_key("idmef_filter"):
            c.append(unicode(self.parameters["idmef_filter"]))

        self.dataset["current_filter"] = self.parameters.get("filter", "")
        if self.parameters.has_key("filter"):
            f = self.env.db.getAlertFilter(self.user.login, self.parameters["filter"])
            if f:
                c.append(unicode(f))

        return c

    def _processCriteria(self):
        criteria = [ ]
        criteria += self._processTimeCriteria()
        criteria += self._processFilterCriteria()

        return criteria

    def render(self):
        self.dataset["hidden_parameters"] = [ ("view", self.view_name) ]
        self.dataset["charts"] = [ ]
        self.dataset["filters"] = self.env.db.getAlertFilterNames(self.user.login)
        self.dataset["timeline_hour_selected"] = ""
        self.dataset["timeline_day_selected"] = ""
        self.dataset["timeline_month_selected"] = ""
        self.dataset["timeline_custom_selected"] = ""

    def _setPeriod(self):
        tm = time.localtime()

        period = "from %s/%s/%s %s:%s to %s/%s/%s %s:%s" % \
                 (self.dataset["from_year"], self.dataset["from_month"], self.dataset["from_day"],
                  self.dataset["from_hour"], self.dataset["from_min"],
                  self.dataset["to_year"], self.dataset["to_month"], self.dataset["to_day"],
                  self.dataset["to_hour"], self.dataset["to_min"])

        if self.parameters["timeline_type"] == "month":
            self.dataset["period"] = "Period: current month (%s)" % period
        elif self.parameters["timeline_type"] == "day":
            self.dataset["period"] = "Period: today (%s)" % period
        elif self.parameters["timeline_type"] == "hour":
            self.dataset["period"] = "Period: current hour (%s)" % period
        else:
            self.dataset["period"] = "Period: %s" % period



class GenericTimelineStats(DistributionStats):
    def _getAlertCount(self, criteria, link):
        d = {}

        results = self.env.idmef_db.getValues(self._getSelection(), criteria)
        if not results:
            return d

        for name, count in results:
            d[self._getNameFromMap(name, self._names_and_colors)] = (count, link)

        return d

    def _newTimeline(self, user, width, height, stacked=False):
        if stacked:
            timeline = Chart.StackedTimelineChart(user, width, height)
        else:
            timeline = Chart.TimelineChart(user, width, height)

        if not self.parameters.has_key("idmef_filter"):
            timeline.enableMultipleValues(self._namesAndColors2ColorMap(self._names_and_colors))

        return timeline

    def _getTimeCrit(self, start, step):
        tm1 = start #time.localtime(start)
        tm2 = start+step #time.localtime(start + step)

        c = [ "alert.create_time >= '%d-%d-%d %d:%d:%d' && alert.create_time < '%d-%d-%d %d:%d:%d'" % \
              (tm1.year, tm1.month, tm1.day, tm1.hour, tm1.minute, tm1.second,
               tm2.year, tm2.month, tm2.day, tm2.hour, tm2.minute, tm2.second) ]

        return c

    def _getStep(self, type, absolute=False):
        start = None

        if type == "custom":
                type = self.getCustomUnit()
                start = datetime.datetime(*self._period_start[:6])
                end = datetime.datetime(*self._period_end[:6])
        else:
                end = datetime.datetime.today()

        if type == "min":
                if not start:
                        start = end - datetime.timedelta(seconds=60)
                step = datetime.timedelta(seconds=1)
                label_tm_index = "%Hh%M:%S"
                zoom_view = "alert_listing"
                timeline_type = "min"
                timeline_unit = ""

        elif type == "hour":
                if not start:
                        start = end - datetime.timedelta(minutes=60)
                step = datetime.timedelta(minutes=1)
                label_tm_index = "%Hh%M"
                zoom_view = "alert_listing"
                timeline_type = "min"
                timeline_unit = ""

        elif type == "day":
                if not start:
                        start = end - datetime.timedelta(hours=24)
                step = datetime.timedelta(hours=1)
                label_tm_index = "%d/%Hh"
                zoom_view = "stats_timeline"
                timeline_type = "custom"
                timeline_unit = "hour"

        elif type == "month":
                if not start:
                        start = end - datetime.timedelta(days=31)
                step = datetime.timedelta(days=1)
                label_tm_index = "%m/%d"
                zoom_view = "stats_timeline"
                timeline_type = "custom"
                timeline_unit = "day"

        elif type == "year":
                if not start:
                        start = end - datetime.timedelta(days=365)
                step = datetime.timedelta(days=31)
                label_tm_index = "%m/%d"
                zoom_view = "stats_timeline"
                timeline_type = "custom"
                timeline_unit = "day"

        return start, end, step, label_tm_index, zoom_view, timeline_type, timeline_unit


    def _setTimelineZoom(self, base_parameters, start, end):
        #tm = time.localtime(start)
        base_parameters["from_year"] = start.year
        base_parameters["from_month"] = start.month
        base_parameters["from_day"] = start.day
        base_parameters["from_hour"] = start.hour
        base_parameters["from_min"] = start.minute

        #tm = time.localtime(end)
        base_parameters["to_year"] = end.year
        base_parameters["to_month"] = end.month
        base_parameters["to_day"] = end.day
        base_parameters["to_hour"] = end.hour
        base_parameters["to_min"] = end.minute

    def _generateTimeline(self, user, width, height):
        start, end, step, format, zoom_view, timeline_type, timeline_time = self._getStep(self.parameters["timeline_type"])
        timeline = self._newTimeline(user, width, height)

        if timeline_type != "custom":
            base_parameters = { "timeline_unit": "min" }
        else:
            base_parameters = { "timeline_type": timeline_type }

        self.dataset["timeline_user_type"] = self.parameters.get("timeline_type")

        while start < end:
            c = self._getTimeCrit(start, step) + self._criteria

            if timeline_type != "custom":
                base_parameters["timeline_start"] = long(time.mktime(start.timetuple())) #long(start)
            else:
                self._setTimelineZoom(base_parameters, start, start + step)

            link = utils.create_link(zoom_view, base_parameters)
            count = self._getAlertCount(c, link)
            label = start.strftime(format)

            start += step
            timeline.addLabelValuePair(label, count, link)

        return timeline

    def getCustomUnit(self):
        start = long(time.mktime(self._period_start))
        delta = long(time.mktime(self._period_end)) - start

        if delta > 86400:
            unit = "month"
        elif delta > 3600:
            unit = "day"
        elif delta > 60:
            unit = "hour"
        else:
            unit = "min"

        return unit

    def _getSelection(self):
        return ("%s/group_by" % self._path, "count(%s)/order_desc" % self._path)

    def _addTimelineChart(self, title, value_name, width, height, path, criteria, limit=-1, names_and_colors={}, allow_stacked=False, value_callback=None, zoom_type=None):
        self._path = path
        self._limit = limit
        self._value_callback = value_callback
        self._criteria = criteria
        self._zoom_type = zoom_type
        self._names_and_colors = names_and_colors

        base_url = self._getBaseURL()
        chart = { "title": title, "value_name": value_name, "data": [ ] }

        if limit > 0:
            res = self.env.idmef_db.getValues(self._getSelection(), criteria = criteria, limit=self._limit)

            c = u""
            for name, count in res:
                if c:
                    c += " || "

                if name:
                    c += "%s = '%s'" % (self._path, utils.escape_criteria(name))
                else:
                    c += "! %s" % (self._path)
            if c:
                criteria.append(c)

        timeline = self._generateTimeline(self.user, width, height)
        timeline.render(title)

        chart["chart"] = timeline
        self.dataset["charts"].append(chart)
        self.dataset["zoom"] = self.parameters.get("zoom", None)


class CategorizationStats(DistributionStats, GenericTimelineStats):
    view_name = "stats_categorization"

    def _renderClassifications(self, criteria, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
        self._addDistributionChart(_("Top 10 Classifications"), _("Classification"), width, height,
                                   "alert.classification.text",
                                   criteria,
                                   lambda value: utils.urlencode({"classification_object_0": "alert.classification.text",
                                                                  "classification_value_0": value}),
                                   10)

    def _renderReferences(self, criteria, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
        self._addDistributionChart(_("Top 10 Alert References"), _("References"), width, height,
                                   "alert.classification.reference.name",
                                   criteria,
                                   lambda value: utils.urlencode({"classification_object_0": "alert.classification.reference.name",
                                                                  "classification_value_0": value}),
                                   10)

    def _renderImpactSeverities(self, criteria, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
        _severity_maps = utils.OrderedDict()
        _severity_maps["high"] = (_("High"), Chart.RED_STD)
        _severity_maps["medium"] = (_("Medium"), Chart.ORANGE_STD)
        _severity_maps["low"] = (_("Low"), Chart.GREEN_STD)
        _severity_maps["info"] = (_("Informational"), Chart.BLUE_STD)
        _severity_maps[None] = (_("N/a"), "000000")

        self._addDistributionChart(_("Severities"), _("Severity"), width, height,
                                   "alert.assessment.impact.severity",
                                   criteria,
                                   lambda value: utils.urlencode({"classification_object_0": "alert.assessment.impact.severity",
                                                                  "classification_value_0": value}), names_and_colors=_severity_maps)

    def _renderImpactTypes(self, criteria, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
        self._addDistributionChart(_("Alert Impact Types"), _("Impact Types"), width, height,
                                   "alert.assessment.impact.type",
                                   criteria,
                                   lambda value: utils.urlencode({"classification_object_0": "alert.assessment.impact.type",
                                                                  "classification_value_0": value}))

    def _renderClassificationsTrend(self, criteria, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
        GenericTimelineStats._addTimelineChart(self, "Top 10 Classifications Trend", None, width, height,
                                               "alert.classification.text", criteria, limit = 10, zoom_type="classifications_trend")

    def render(self):
        DistributionStats.render(self)

        self.dataset["title"] = "Alerts categorization"

        criteria = self._processCriteria()

        self._setPeriod()

        self._renderClassificationsTrend(criteria)
        self._renderClassifications(criteria)
        self._renderReferences(criteria)
        self._renderImpactSeverities(criteria)
        self._renderImpactTypes(criteria)



class SourceStats(DistributionStats, GenericTimelineStats):
    view_name = "stats_source"

    def _countryDistributionChart(self, criteria, width, height):

        base_url = self._getBaseURL()
        distribution = Chart.WorldChart(self.user, width, height)

        chart = { "title": _("Top Source Country"), "value_name": _("Country"), "data": [ ], "chart": distribution }

        results = self.env.idmef_db.getValues([ "alert.source.node.address.address/group_by",
                                                "count(alert.source.node.address.address)"],
                                              criteria=criteria, limit=-1)

        if results:
            total = reduce(lambda x, y: x + y, [ count for value, count in results ])
            chart["total"] = total

            merge = { }
            for value, count in results:
                if not value:
                        continue

                if distribution.needCountryCode():
                    nvalue = geoip.country_code_by_addr(value)
                else:
                    nvalue = geoip.country_name_by_addr(value)
                if not nvalue:
                    nvalue = "Unknown"

                if not merge.has_key(nvalue):
                   url_index = 0
                   merge[nvalue] = (0, 0, nvalue, "")
                else:
                   url_index = merge[nvalue][1]

                encode = "&amp;" + utils.urlencode({"source_object_%d" % url_index: "alert.source.node.address.address",
                                                    "source_value_%d" % url_index: value})
                merge[nvalue] = (merge[nvalue][0] + count, url_index + 1, nvalue, merge[nvalue][3] + encode)

            s = [ t[1] for t in merge.items() ]
            s.sort()
            s.reverse()
            results = s #[0:10]

            for item in results:
                distribution.addLabelValuePair(item[2], item[0])
                chart["data"].append((item[2], base_url + item[3], item[0], "%.1f" % (item[0] / float(total) * 100)))

        distribution.render("Top 10 Source Country")
        chart["filename"] = distribution.getHref()
        chart["type"] = distribution.getType()
        self.dataset["charts"].append(chart)


    def _renderCountry(self, criteria, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
        if geoip is not None:
            self._countryDistributionChart(criteria, width, height)

    def _renderAddresses(self, criteria, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
        self._addDistributionChart(_("Top 10 Source Addresses"), _("Address"), width, height,
                                   "alert.source.node.address.address",
                                   criteria,
                                   lambda value: utils.urlencode({"source_object_0": "alert.source.node.address.address",
                                                                   "source_value_0": value}),
                                   10, dns=True)

    def _renderUsers(self, criteria, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
        self._addDistributionChart(_("Top 10 Source Users"), _("User"), width, height,
                                   "alert.source.user.user_id.name",
                                   criteria,
                                   lambda value: utils.urlencode({"source_object_0": "alert.source.user.user_id.name",
                                                                   "source_value_0": value}),
                                   10)

    def _renderSourcesTrend(self, criteria, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
        GenericTimelineStats._addTimelineChart(self, "Top 10 Sources Trend", None, DEFAULT_WIDTH, DEFAULT_HEIGHT,
                                               "alert.source.node.address.address", criteria, 10, zoom_type="sources_trend")

    def render(self):
        DistributionStats.render(self)

        self.dataset["title"] = "Top Alert Sources"

        criteria = self._processCriteria()

        self._setPeriod()

        self._renderCountry(criteria)
        self._renderSourcesTrend(criteria)
        self._renderAddresses(criteria)
        self._renderUsers(criteria)

        resolve.process(self.env.dns_max_delay)

class TargetStats(DistributionStats):
    view_name = "stats_target"

    def _renderPorts(self, criteria, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
        base_url = self._getBaseURL()
        title = "Top 10 Targeted Ports"
        distribution = Chart.DistributionChart(self.user, width, height)
        chart = { "title": title, "value_name": "Port", "data": [ ], "chart": distribution }

        criteria = criteria[:] + [ "(alert.target.service.iana_protocol_number == 6  ||"
                                   "alert.target.service.iana_protocol_number == 17  ||"
                                   "alert.target.service.iana_protocol_name =* 'tcp' ||"
                                   "alert.target.service.iana_protocol_name =* 'udp' ||"
                                   "alert.target.service.protocol =* 'udp'           ||"
                                   "alert.target.service.protocol =* 'tcp')" ]

        results = self.env.idmef_db.getValues([ "alert.target.service.port/group_by",
                                                "alert.target.service.iana_protocol_number/group_by",
                                                "alert.target.service.iana_protocol_name/group_by",
                                                "alert.target.service.protocol/group_by",
                                                "count(alert.target.service.port)/order_desc" ],
                                              criteria=criteria, limit=10)
        if not results:
            return

        merge = { "TCP": { }, "UDP": { } }

        for port, iana_protocol_number, iana_protocol_name, protocol, count in results:
            if not port:
                continue

            if iana_protocol_number:
                protocol = utils.protocol_number_to_name(iana_protocol_number)

            elif iana_protocol_name:
                protocol = iana_protocol_name

            protocol = protocol.upper()
            if not merge.has_key(protocol):
                continue

            if not merge[protocol].has_key(port):
                merge[protocol][port] = 0

            merge[protocol][port] += count

        results = [ ]

        for protocol, values in merge.items():
            for port, count in values.items():
                results.append((port, protocol, count))

        results.sort(lambda x, y: int(y[2] - x[2]))

        total = reduce(lambda x, y: x + y, [ count for port, protocol, count in results ])
        chart["total"] = total

        for port, protocol, count in results:
            name = "%d (%s)" % (port, protocol)
            chart["data"].append((name, base_url + "&amp;" + "target_object_0=alert.target.service.port&amp;target_value_0=%d" % port,
                                  count, "%.1f" % (count / float(total) * 100)))

            distribution.addLabelValuePair(name, count, base_url + "&amp;" + "target_object_0=alert.target.service.port&amp;target_value_0=%d" % port)

        distribution.render(title)
        self.dataset["charts"].append(chart)

    def _renderAddresses(self, criteria, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
        self._addDistributionChart(_("Top 10 Targeted Addresses"), _("Address"), width, height,
                                   "alert.target.node.address.address",
                                   criteria,
                                   lambda value: utils.urlencode({"target_object_0": "alert.target.node.address.address",
                                                                   "target_value_0": value}),
                                   10, dns=True)

    def _renderUsers(self, criteria, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
        self._addDistributionChart(_("Top 10 Targeted Users"), _("User"), width, height,
                                   "alert.target.user.user_id.name",
                                   criteria,
                                   lambda value: utils.urlencode({"target_object_0": "alert.target.user.user_id.name",
                                                                  "target_value_0": value}),
                                   10)

    def render(self):
        DistributionStats.render(self)

        self.dataset["title"] = "Top Alert Targets"

        criteria = self._processCriteria()

        self._setPeriod()

        self._renderAddresses(criteria)
        self._renderPorts(criteria)
        self._renderUsers(criteria)

        resolve.process(self.env.dns_max_delay)


class AnalyzerStats(DistributionStats, GenericTimelineStats):
    view_name = "stats_analyzer"

    def _renderAnalyzers(self, criteria, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
        base_url = self._getBaseURL()
        title = "Top 10 analyzers"
        distribution = Chart.DistributionChart(self.user, width, height)
        chart = { "title": title, "value_name": "Analyzer", "data": [ ], "chart": distribution }

        results = self.env.idmef_db.getValues([ "alert.analyzer(-1).name/group_by", "alert.analyzer(-1).node.name/group_by",
                                                "count(alert.analyzer(-1).name)/order_desc" ],
                                              criteria=criteria + [ "alert.analyzer(-1).name" ], limit=10)
        if results:
            total = reduce(lambda x, y: x + y, [ row[-1] for row in results ])
            chart["total"] = total
            for analyzer_name, node_name, count in results:
                if node_name:
                    value = "%s on %s"  % (analyzer_name, node_name)
                else:
                    value = analyzer_name

                analyzer_criteria = utils.urlencode({ "analyzer_object_0": "alert.analyzer(-1).name",
                                                       "analyzer_value_0": analyzer_name })

                chart["data"].append((value,
                                      base_url + "&amp;" + analyzer_criteria,
                                      count,
                                      "%.1f" % (count / float(total) * 100)))

                distribution.addLabelValuePair(value, count, base_url + "&amp;" + analyzer_criteria)

            distribution.render(title)
            self.dataset["charts"].append(chart)

    def _renderModels(self, criteria, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
        self._addDistributionChart(_("Top 10 Analyzer Models"), _("Model"), width, height,
                                   "alert.analyzer(-1).model",
                                   criteria,
                                   lambda value: utils.urlencode({ "analyzer_object_0": "alert.analyzer(-1).model",
                                                                    "analyzer_value_0": value }),
                                   10)

    def _renderClasses(self, criteria, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
        self._addDistributionChart(_("Top 10 Analyzer Classes"), _("Class"), width, height,
                                   "alert.analyzer(-1).class",
                                   criteria,
                                   lambda value: utils.urlencode({ "analyzer_object_0": "alert.analyzer(-1).class",
                                                                    "analyzer_value_0": value }),
                                   10)

    def _renderNodeAddresses(self, criteria, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
        self._addDistributionChart(_("Top 10 Analyzer Node Addresses"), _("Address"), width, height,
                                   "alert.analyzer(-1).node.address.address",
                                   criteria,
                                   lambda value: utils.urlencode({ "analyzer_object_0": "alert.analyzer(-1).node.address.address",
                                                                    "analyzer_value_0": value }),
                                   10)

    def _renderNodeLocations(self, criteria, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
        self._addDistributionChart(_("Analyzer Locations"), _("Location"), width, height,
                                   "alert.analyzer(-1).node.location",
                                   criteria,
                                   lambda value: utils.urlencode({ "analyzer_object_0": "alert.analyzer(-1).node.location",
                                                                    "analyzer_value_0": value }))

    def _renderClassesTrend(self, criteria, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
        GenericTimelineStats._addTimelineChart(self, "Top 10 Analyzer Classes Trend", None, width, height,
                                               "alert.analyzer(-1).class", criteria, limit = 10, zoom_type="analyzer_classes_trend")

    def render(self):
        DistributionStats.render(self)

        self.dataset["title"] = "Top Analyzers"

        criteria = self._processCriteria()

        self._setPeriod()

        self._renderClassesTrend(criteria)
        self._renderAnalyzers(criteria)
        self._renderModels(criteria)
        self._renderClasses(criteria)
        self._renderNodeAddresses(criteria)
        self._renderNodeLocations(criteria)



class TimelineStats(GenericTimelineStats, AnalyzerStats, CategorizationStats, SourceStats):
    view_name = "stats_timeline"

    def _renderTimelineChart(self, criteria, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
        _severity_maps = utils.OrderedDict()
        _severity_maps["high"] = (_("High"), Chart.RED_STD)
        _severity_maps["medium"] = (_("Medium"), Chart.ORANGE_STD)
        _severity_maps["low"] = (_("Low"), Chart.GREEN_STD)
        _severity_maps["info"] = (_("Informational"), Chart.BLUE_STD)
        _severity_maps[None] = (_("N/a"), "000000")

        GenericTimelineStats._addTimelineChart(self, "Timeline", None, width, height,
                                               "alert.assessment.impact.severity", criteria, names_and_colors=_severity_maps)

    def render(self):
        DistributionStats.render(self)
        self.dataset["title"] = "Timeline"

        criteria = self._processCriteria()
        self._setPeriod()

        type = self.parameters.get("type", None)
        if type == "analyzer_classes_trend":
                AnalyzerStats._renderClassesTrend(self, criteria)

        elif type == "classifications_trend":
                CategorizationStats._renderClassificationsTrend(self, criteria)

        elif type == "sources_trend":
                SourceStats._renderSourcesTrend(self, criteria)
        else:
                self._renderTimelineChart(criteria)




class AnalyzerTrendStats(GenericTimelineStats, AnalyzerStats):
    view_name = "stats_analyzer_trend"

    def render(self):
        DistributionStats.render(self)
        self.dataset["title"] = "Timeline"

        criteria = self._processCriteria()
        self._setPeriod()

        title = "Top 10 Analyzer Trend " + self.dataset["period"]
        AnalyzerStats._renderClassesTrend(self, criteria, width, height)

