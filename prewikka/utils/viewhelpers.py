# Copyright (C) 2016 CS-SI. All Rights Reserved.
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

import json
from string import Template

from prewikka import view, env, utils, hookmanager, response


class GridAjaxParameters(view.Parameters):
    """Handle parameters sent by jqGrid."""
    def register(self):
        self.optional("query", str)  # query string
        self.optional("page", int, 1)  # requested page
        self.optional("rows", int, 10)  # number of rows requested
        self.optional("sort_index", str)  # sorting column
        self.optional("sort_order", str)  # sort order (asc or desc)

    def get_response(self, total_results):
        # Ceil division (use // instead of / for Python3 compatibility):
        nb_pages = (total_results - 1) // self["rows"] + 1
        return {"total": nb_pages, "page": self["page"], "rows": [], "records": total_results}


class AjaxHostURL(view.View):
    class AjaxHostURLParameters(view.Parameters):
        def register(self):
            self.mandatory("host", str)

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
            yield '<a href="%(url)s" target="_%(urlname)s">%(urlname)s</a>' % {
                "urlname": utils.escape_html_string(urlname),
                "url": utils.escape_html_string(url)
            }

    def render(self):
        infos = {"host": self.parameters["host"]}

        for info in hookmanager.trigger("HOOK_HOST_INFO", self.parameters["host"]):
            infos.update(info)

        return response.PrewikkaDirectResponse(list(self._link_generator(infos)))

