# Copyright (C) 2004,2005 Nicolas Delon <nicolas@prelude-ids.org>
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


from prewikka import User, view

import matplotlib
matplotlib.use("Agg")

from pylab import *


GRADIENT_COLOR_START = (17.0/255, 17.0/255, 191.0/255)
GRADIENT_COLOR_END = (209.0/255, 209.0/255, 209.0/255)


def get_color_gradient(steps):
    colors = [ GRADIENT_COLOR_START ]
    if steps == 1:
        return colors
    step = [ (e - s) / (steps - 1) for e, s in zip(GRADIENT_COLOR_END, GRADIENT_COLOR_START) ]
    prev = GRADIENT_COLOR_START
    for i in range(steps - 1):
        new = [ x + s for x, s in zip(prev, step) ]
        colors.append(new)
        prev = new

    return colors


class Chart:
    def __init__(self, filename):
        self._filename = "img/generated/" + filename
        self._title = ""
        self._values = [ ]
        self._labels = [ ]
        self._values_title = None
        self._labels_title = None

    def getFilename(self):
        return self._filename

    def setValuesTitle(self, title):
        self._values_title = title

    def setLabelsTitle(self, title):
        self._labels_title = title

    def setTitle(self, title):
        self._title = title        

    def setValues(self, values):
        self._values = values

    def setLabels(self, labels):
        self._labels = labels

    def addLabelValuePair(self, label, value):
        self._labels.append(label)
        self._values.append(value)
    
    def _render(self):
        title(self._title, verticalalignment="center")
        if self._values_title:
            ylabel(self._values_title)
        if self._labels_title:
            xlabel(self._labels_title)
        savefig(self._filename)
        clf()
    
    def renderPie(self):
        figure(figsize=(7,7))
        total = float(reduce(lambda x, y: x + y, self._values))
        values = [ ]
        i = 0
        for value in self._values:
            if value / total < 0.007 and len(self._values) - len(values):
                break
            values.append(value)
        colors = get_color_gradient(len(values))
        patches, texts, autotexts = pie(values, labels=self._labels[:len(values)], colors=colors, autopct=lambda x: "", shadow=True)
        for text in texts:
            text.set_text("")
        labels = [ "%s: %d (%.1f%%)" % (label, value, value / total * 100) for label, value in zip(self._labels, self._values) ]
        l = legend(labels, loc=(0,0), shadow=True)
        i = 0
        for patch in l.get_patches():
            if i < len(values):
                color = colors[i]
            else:
                color = colors[-1]
            patch.set_fc(color)
            i += 1
        l.set_alpha(0.75)
        self._render()

    def _setYticks(self):
        locs, labels = yticks()
        step = int(locs[1] / 2)
        ymin, ymax = ylim()
        r = range(int(ymin), int(ymax + step), step)
        yticks(r, r)

    def _setXticks(self):
        xticks(arange(len(self._values)), self._labels, horizontalalignment="center")

    def _setTicks(self):
        self._setXticks()
        self._setYticks()

    def renderPlot(self):
        plot(self._values)
        self._setTicks()
        self._render()

    def renderBar(self):
        bar(arange(len(self._values)), self._values)
        self._setTicks()
        self._render()



class Stats(view.View):
    view_name = "stats"
    view_template = "Stats"
    view_permission = [ User.PERM_IDMEF_VIEW ]
    view_parameters = view.Parameters

    def _render_distribution(self, filename, title, path, limit):
        chart = Chart(filename)
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
        chart = Chart("timeline.png")
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
