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

from pylab import *


class Chart:
    def __init__(self, filename):
        self._filename = "img/generated/" + filename
        self._title = ""
        self._values = [ ]
        self._labels = [ ]

    def getFilename(self):
        return self._filename

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
        figure(facecolor="b")
        title(self._title)
        savefig(self._filename)
        clf()
    
    def renderPie(self):
        total = float(reduce(lambda x, y: x + y, self._values))
        patches, texts, autotexts = pie(self._values, labels=self._labels, autopct=lambda x: "%f" % x)
        for autotext, value in zip(autotexts, self._values):
            autotext.set_text("%d (%.1f%%)" % (value, value / total * 100))
        self._render()

    def renderPlot(self):
        plot(self._values)
        xticks(arange(len(self._values)), self._labels)
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
        chart = Chart("top10_attackers.png")
        chart.setTitle("Top 10 attackers")
        for address, count in self.env.prelude.getValues(["alert.source.node.address.address/group_by",
                                                          "count(alert.messageid)/order_desc"],
                                                         limit=10):
            
            chart.addLabelValuePair(address, count)
        chart.renderPie()

        self.dataset["charts"].append(chart.getFilename())

    def render_top10_classifications(self):
        chart = Chart("top10_classifications.png")
        chart.setTitle("Top 10 classifications")
        for classification, count in self.env.prelude.getValues(["alert.classification.text/group_by",
                                                                 "count(alert.messageid)/order_desc"],
                                                                limit=10):
            
            chart.addLabelValuePair(classification, count)
        chart.renderPie()

        self.dataset["charts"].append(chart.getFilename())

    def render(self):
        self.dataset["charts"] = [ ]
        self.render_top10_attackers()
        self.render_top10_classifications()
        self.render_sensor_distribution()
