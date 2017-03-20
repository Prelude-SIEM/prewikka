# Copyright (C) 2016-2017 CS-SI. All Rights Reserved.
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

from string import Template

from prewikka import hookmanager, resource, response, utils, view


class GridAjaxParameters(view.Parameters):
    """Handle parameters sent by jqGrid."""
    def register(self):
        self.optional("query", text_type)  # query string
        self.optional("page", int, 1)  # requested page
        self.optional("rows", int, 10)  # number of rows requested
        self.optional("sort_index", text_type)  # sorting column
        self.optional("sort_order", text_type)  # sort order (asc or desc)

    @utils.deprecated
    def get_response(self, total_results):
        # Ceil division (use // instead of / for Python3 compatibility):
        nb_pages = (total_results - 1) // self["rows"] + 1
        return {"total": nb_pages, "page": self["page"], "rows": [], "records": total_results}


class GridAjaxResponse(response.PrewikkaDirectResponse):
    def __init__(self, rows, total_results):
        response.PrewikkaDirectResponse.__init__(self)

        # Ceil division (use // instead of / for Python3 compatibility):
        nb_pages = (total_results - 1) // int(env.request.parameters.get("rows", 10)) + 1
        self.data = {"total": nb_pages, "rows": rows, "records": total_results}


class AjaxHostURL(view.View):
    class AjaxHostURLParameters(view.Parameters):
        def register(self):
            self.mandatory("host", text_type)

    view_parameters = AjaxHostURLParameters

    @staticmethod
    def _value_generator(infos):
        for urlname, url in env.url.get("host", {}).items():
            try:
                url = Template(url).substitute(infos)
            except KeyError:
                continue

            yield _(urlname), url

    @classmethod
    def _link_generator(cls, infos):
        for urlname, url in cls._value_generator(infos):
            yield resource.Link('<a href="{url}" target="{urlname}">{urlname}</a>').format(urlname=urlname, url=url)

    def render(self):
        infos = {"host": env.request.parameters["host"]}

        for info in hookmanager.trigger("HOOK_HOST_INFO", env.request.parameters["host"]):
            infos.update(info)

        return response.PrewikkaDirectResponse(list(self._link_generator(infos)))
