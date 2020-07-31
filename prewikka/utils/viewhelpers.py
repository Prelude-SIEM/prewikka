# Copyright (C) 2016-2020 CS GROUP - France. All Rights Reserved.
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

from prewikka import response, utils, view


def GridParameters(name):
    class _GridParameters(view.Parameters):
        def register(self):
            self.optional("jqgrid_params_%s" % name, utils.json.loads, {}, persist=True)

    return _GridParameters


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


class GridAjaxResponse(response.PrewikkaResponse):
    def __init__(self, rows, total_results, **kwargs):
        response.PrewikkaResponse.__init__(self)

        # Ceil division (use // instead of / for Python3 compatibility):
        kwargs["total"] = (total_results - 1) // int(env.request.parameters.get("rows", 10)) + 1
        kwargs["rows"] = rows
        kwargs["records"] = total_results
        self.data = kwargs
