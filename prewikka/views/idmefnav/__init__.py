# Copyright (C) 2016-2020 CS-SI. All Rights Reserved.
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

from __future__ import absolute_import, division, print_function, unicode_literals

import pkg_resources

from prewikka import template, version, view
from . import graph_generator


class IDMEFNav(view.View):
    _HTDOCS_DIR = pkg_resources.resource_filename(__name__, 'htdocs')

    plugin_name = "IDMEFNav"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("IDMEF navigator")
    plugin_htdocs = (("idmefnav", _HTDOCS_DIR),)

    def __init__(self):
        view.View.__init__(self)
        self.schema = graph_generator.Schema(self._HTDOCS_DIR)
        self.schema.image_load()

    @view.route("/help/idmefnav", methods=['GET'], menu=(N_("Help"), N_("IDMEF")))
    def render(self):
        idmef_class = env.request.parameters.get("idmef_class", "IDMEF-Message")
        if idmef_class not in self.schema:
            raise view.InvalidParameterValueError("idmef_class", idmef_class)

        dset = template.PrewikkaTemplate(__name__, "templates/idmefnav.mak").dataset()
        dset["schema"] = self.schema[idmef_class]
        dset["schema"]['svg'] = dset["schema"]['svg'].replace(graph_generator._LINK_TAG, url_for('idmefnav.render'))
        dset["full_schema"] = self.schema

        return dset.render()
