# -*- coding: utf-8 -*-
# Copyright (C) 2018 CS-SI. All Rights Reserved.
# Author: Sélim Menouar <selim.menouar@c-s.fr>
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

""" ChartJS renderer plugin """

import pkg_resources

from prewikka import pluginmanager, version
from prewikka.renderer import RendererBackend
from prewikka.utils import json


class ChartJSRenderer(RendererBackend):
    """ ChartJS renderer plugin """

    renderer_backend = "chartjs"
    _chartjs_filename = "chartjs/js/Chart.min.js"

    def _rgba(self, color, alpha=1):
        return "rgba(%s, %s, %s, %s)" % (
            int(color[0:2], 16),
            int(color[2:4], 16),
            int(color[4:6], 16),
            alpha)

    def generate_html(self, kwargs, data, options, chart_type, mapping=None, multiple=False):
        """ Generate HTML used in all ChartJS charts

        Keyword arguments:
        kwargs -- kwargs
        options -- Specific options for the chart
        element_type -- Type of ChartJS element (Point, Segment, ...)
        mapping -- Array use for onclick event (default None)
        """

        html = """<div id="chartjs-%(cssid)s"><canvas id="canvas-%(cssid)s"></canvas></div>""" % {"cssid": kwargs["cssid"]}

        script = """
 $LAB.script("%(chartjs_js)s").wait(function() {
    var size = prewikka_getRenderSize("#%(cssid)s", %(kwargs)s);
    var ctx = $("#canvas-%(cssid)s")
    var dom = $("#chartjs-%(cssid)s");

    Chart.defaults.global.maintainAspectRatio = false;

    dom.css("width", size[0]);
    dom.css("height", size[1]);

    $("#%(cssid)s").attr('resizeable', true);

    var myChart = new Chart(ctx, {type: '%(chart_type)s', data: %(data)s, options: %(options)s});

    $("#%(cssid)s").on('resize', function() {
        myChart.resize();
    });

    var mapping = %(mapping)s;
    if ( ! mapping )
        return;

    $("#canvas-%(cssid)s").click(function(evt) {
        var activePoint = myChart.getElementAtEvent(evt)[0];
        var value = %(multiple)s ? mapping[activePoint._view.datasetLabel][activePoint._view.label] : mapping[activePoint._view.label];
        if ( activePoint )
            prewikka_ajax({url: value});
    });

 });""" % {"cssid": kwargs["cssid"],
           "chartjs_js": self._chartjs_filename,
           "chart_type": chart_type,
           "kwargs": json.dumps(kwargs),
           "data": json.dumps(data),
           "options": json.dumps(options),
           "mapping": json.dumps(mapping),
           "multiple": json.dumps(multiple)}

        return {"html": html, "script": script}


class ChartJSPlugin(pluginmanager.PluginPreload):
    """ ChartJS plugin informations"""
    plugin_name = "ChartJS renderer"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = _("ChartJS renderer backend")
    plugin_htdocs = (("chartjs", pkg_resources.resource_filename(__name__, 'htdocs')),)
