# Copyright (C) 2014-2020 CS GROUP - France. All Rights Reserved.
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

from __future__ import absolute_import, division, print_function, unicode_literals

import collections
import pkg_resources

from prewikka import hookmanager, resource, template, version, view


class RiskOverview(view.View):
    plugin_name = "Risk Overview"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("Top page risk overview")
    plugin_htdocs = (("riskoverview", pkg_resources.resource_filename(__name__, 'htdocs')),)

    """ Retrieving info for risk overview table """
    def __init__(self):
        self._widgets = env.config.riskoverview.keys()
        view.View.__init__(self)

    @hookmanager.register("HOOK_TOPLAYOUT_EXTRA_CONTENT")
    def _toplayout_extra_content(self):
        # Don't show the risk overview if the user is not logged in
        if not env.request.user:
            return

        return resource.HTMLSource(template.PrewikkaTemplate(__name__, "templates/riskoverview.mak").render())

    @view.route("/riskoverview")
    def riskoverview(self):
        # Don't show the risk overview if the user is not logged in
        if not env.request.user:
            return

        # We don't use groupby because the result won't be sorted then.
        objs = collections.OrderedDict((w, None) for w in self._widgets)

        for i in filter(None, hookmanager.trigger("HOOK_RISKOVERVIEW_DATA", _except=env.log.debug)):
            if i.name not in objs and self._widgets:
                continue
            elif objs.get(i.name) is None:
                objs[i.name] = i
            else:
                for j in i.data:
                    objs[i.name].data.append(j)

        return view.ViewResponse(template.PrewikkaTemplate(__name__, "templates/table.mak").render(data=filter(None, objs.values())))
