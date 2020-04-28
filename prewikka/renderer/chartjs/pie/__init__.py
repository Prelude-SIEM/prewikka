# -*- coding: utf-8 -*-
# Copyright (C) 2020 CS-SI. All Rights Reserved.
# Author: Antoine Luong <antoine.luong@c-s.fr>
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

""" ChartJS pie plugin """

from .. import ChartJSRenderer
from prewikka.renderer import RendererUtils, RendererNoDataException
from prewikka import version


class ChartJSCircularPlugin(ChartJSRenderer):
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__

    def render(self, data, query=None, **kwargs):
        """ Return the HTML for this chart

        Keyword arguments:
        data -- List of tuple containing the data for this chart
                [(count, value, link), ]
        """

        rutils = RendererUtils(kwargs)
        labels = []
        colors = []
        pie_data = []
        mapping = {}

        for i, d in enumerate(data):
            for count, value, link in d:
                label = rutils.get_label(value)
                pie_data.append(count)
                labels.append(label)
                mapping[label] = link
                colors.append(self._rgba(rutils.get_color(value), 1))

        if not pie_data:
            raise RendererNoDataException

        options = {
            "labels": labels,
            "datasets": [{
                "backgroundColor": colors,
                "data": pie_data
            }]
        }

        return self.generate_html(kwargs, options, {"layout": {"padding": {"bottom": 20}}}, self.renderer_type, mapping)


class ChartJSPiePlugin(ChartJSCircularPlugin):
    """ ChartJS pie plugin """

    renderer_type = "pie"

    plugin_name = "ChartJS : Pie"
    plugin_description = N_("ChartJS Pie renderer type")


class ChartJSDoughnutPlugin(ChartJSCircularPlugin):
    """ ChartJS doughnut plugin """

    renderer_type = "doughnut"

    plugin_name = "ChartJS : Doughnut"
    plugin_description = N_("ChartJS Doughnut renderer type")
