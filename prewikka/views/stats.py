# Copyright (C) 2005 Nicolas Delon <nicolas@prelude-ids.org>
# All Rights Reserved
#
# This file is part of the Prelude program.
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

import time

from prewikka import User, view, Chart


class Stats(view.View):
    view_name = "stats"
    view_template = "Stats"
    view_permission = [ User.PERM_IDMEF_VIEW ]
    view_parameters = view.Parameters

    def _render_distribution(self, filename, title, path, limit):
        chart = Chart.Chart(filename)
        chart.setTitle(title)
        for value, count in self.env.prelude.getValues([ path + "/group_by",
                                                         "count(alert.messageid)/order_desc" ],
                                                       limit=limit):
            chart.addLabelValuePair(value, count)
        chart.renderPie()
        
        self.dataset["charts"].append(chart.getFilename())

    def render_sensor_distribution(self):
        self._render_distribution("sensor_distribution.png", "Sensor Distribution", "alert.analyzer.name", -1)

    def render_top10_attackers(self):
        self._render_distribution("top10_attackers.png", "Top 10 attackers",
                                  "alert.source.node.address.address", 10)

    def render_top10_targets(self):
        self._render_distribution("top10_targets.png", "Top 10 targets",
                                  "alert.target.node.address.address", 10)
        
    def render_top10_classifications(self):
        self._render_distribution("top10_classifications.png", "Top 10 classifications", "alert.classification.text", 10)

    def render_timeline(self):
        chart = Chart.Chart("timeline.png")
        chart.setTitle("Timeline")
        chart.setValuesTitle("Alerts count")
        chart.setLabelsTitle("Hours")
        
        for hour in range(24):
            count = self.env.prelude.getValues(["count(alert.messageid)"],
                                               criteria="alert.create_time == 'hour:%d'" % hour)[0][0]
            chart.addLabelValuePair(hour, count)
        chart.renderBar()

        self.dataset["charts"].append(chart.getFilename())

    def render(self):
        self.dataset["charts"] = [ ]
        self.render_top10_attackers()
        self.render_top10_targets()
        self.render_top10_classifications()
        self.render_sensor_distribution()
        self.render_timeline()



class LastHourTimeline(view.View):
    view_name = "last_hour_timeline"
    view_template = "Stats"
    view_permission = [ User.PERM_IDMEF_VIEW ]
    view_parameters = view.Parameters

    def render(self):
        t = time.time()
        chart = Chart.Chart("last_hour_timeline.png")
        chart.setTitle("Last hour timeline")
        chart.setLabelsTitle("Minutes")
        chart.setValuesTitle("Alerts count")
        t -= 3600
        for i in range(60):
            tm = time.localtime(t + i * 60)
            criteria = "alert.create_time >= '%d-%d-%d %d:%d:00' && alert.create_time <= '%d-%d-%d %d:%d:59'" % \
                       (tm.tm_year, tm.tm_mon, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_year, tm.tm_mon, tm.tm_mday, tm.tm_hour, tm.tm_min)

            count = self.env.prelude.countAlerts(criteria)

            chart.addLabelValuePair("", count)

        chart.renderBar()

        self.dataset["charts"] = [ chart.getFilename() ]
