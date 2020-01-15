# -*- coding: utf-8 -*-
# Copyright (C) 2018-2020 CS-SI. All Rights Reserved.
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

""" ChartJS bar plugin """

from .. import ChartJSRenderer
from prewikka.renderer import RendererUtils, RendererNoDataException
from prewikka import version


class ChartJSBarPlugin(ChartJSRenderer):
    """ ChartJS bar plugin """

    renderer_type = "bar"

    plugin_name = "ChartJS : Bar"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("ChartJS Bar renderer type")

    def render(self, data, query=None, **kwargs):
        """ Return the HTML for this chart

        Keyword arguments:
        data -- List of tuple containing the data for this chart
                [(count, value, link), ]
        """

        rutils = RendererUtils(kwargs)
        labels = []
        bar_data = []
        mapping = {}

        for count, value, link in data[0]:
            label = rutils.get_label(value)
            bar_data.append(count)
            labels.append(label)
            mapping[label] = link

        color = rutils.get_color(0)

        if not bar_data:
            raise RendererNoDataException

        options = {
            "labels": labels,
            "datasets": [{
                "backgroundColor": self._rgba(color, 0.5),
                "borderColor": self._rgba(color, 0.8),
                "hoverBackgroundColor": self._rgba(color, 0.75),
                "hoverBorderColor": self._rgba(color, 1),
                "data": bar_data
            }]
        }

        return self.generate_html(kwargs, options, {"legend": {"display": False}}, "bar", mapping)
