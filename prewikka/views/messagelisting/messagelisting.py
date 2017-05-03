# Copyright (C) 2004-2017 CS-SI. All Rights Reserved.
# Author: Nicolas Delon <nicolas.delon@prelude-ids.com>
# Author: Yoann Vandoorselaere <yoannv@gmail.com>
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

import copy
import functools
import time
import urllib

import pkg_resources
from prewikka import hookmanager, localization, mainmenu, resolve, usergroup, utils, view
from prewikka.dataprovider import Criterion
from prewikka.utils import json


class AttrDict(dict):
    def __init__(self, *a, **kw):
        dict.__init__(self, *a, **kw)
        self.__dict__ = self


class MessageListingParameters(mainmenu.MainMenuParameters):
    def register(self):
        mainmenu.MainMenuParameters.register(self)

        self.optional("offset", int, default=0)
        self.optional("limit", int, default=50, save=True)
        self.optional("selection", [ json.loads ], Criterion())
        self.optional("listing_apply", text_type)
        self.optional("action", text_type)


class ListedMessage(AttrDict):
    def __init__(self, view_path, parameters):
        AttrDict.__init__(self)
        self.view_path = view_path

    def _isAlreadyFiltered(self, column, path, criterion, value):
        col = env.request.parameters.get(column)
        if not column:
            return False

        return (path, criterion, value) in col

    def createInlineFilteredField(self, path, value, direction=None, real_value=None):
        if type(path) is not list and type(path) is not tuple:
            path = [ path ]
        else:
            if not path:
                return AttrDict(value=None, inline_filter=None, already_filtered=False)

        if type(value) is not list and type(value) is not tuple:
            if not real_value:
                real_value = value
            value = [ value ]

        extra = { }
        alreadyf = None

        for p, v in zip(path, value):
            if direction:
                if v is not None:
                    operator = "="
                else:
                    operator = "!"

                if alreadyf is not False:
                    alreadyf = self._isAlreadyFiltered(direction, p, operator, v or "")

                index = env.request.parameters.max_index
                extra["%s_object_%d" % (direction, index)] = p
                extra["%s_operator_%d" % (direction, index)] = operator
                extra["%s_value_%d" % (direction, index)] = v or ""
                env.request.parameters.max_index += 1

            else:
                val = env.request.parameters.get(p)
                if alreadyf is not False and (val and val == [v]):
                        alreadyf = True

                extra[p] = v or ""

        link = url_for(".", **(env.request.parameters + extra - [ "offset" ]))
        return AttrDict(value=real_value, inline_filter=link, already_filtered=alreadyf)

    def createTimeField(self, timeobj):
        if not timeobj:
            return { "value": "n/a" }

        return AttrDict(value=localization.format_datetime(timeobj, format="short"))

    def createHostField(self, object, value, category=None, direction=None, dns=True):
        field = self.createInlineFilteredField(object, value, direction)
        field["category"] = category

        field["url_infos"] = url_for("HostInfoAjax", host=value) if value and "HOOK_HOST_TOOLTIP" in hookmanager.hookmgr else None
        field["url_popup"] = url_for("AjaxHostURL", host=value) if value else None

        if value and dns is True:
            field["hostname"] = resolve.AddressResolve(value)
        else:
            field["hostname"] = value or _("n/a")

        if not value:
            return field

        field["host_links"] = list(hookmanager.trigger("HOOK_HOST_LINK", value))

        return field


class HostInfoAjax(view.View):
    class HostInfoAjaxParameters(view.Parameters):
        def register(self):
            self.mandatory("host", text_type)

    view_parameters = HostInfoAjaxParameters

    def render(self):
        infos = []
        for info in hookmanager.trigger("HOOK_HOST_TOOLTIP", env.request.parameters["host"]):
            infos.extend(info)

        return infos

class MessageListing(view.View):
    plugin_htdocs = (("messagelisting", pkg_resources.resource_filename(__name__, 'htdocs')),)

    def _adjustCriteria(self, criteria):
        pass

    def render(self):
        view.View.render(self)
        env.request.dataset["order_by"] = env.request.parameters["orderby"]
        env.request.dataset["nav"] = {}

    def _setNavPrev(self, offset):
        env.request.dataset["nav"]["first"] = None
        env.request.dataset["nav"]["prev"] = None
        if offset:
            env.request.dataset["nav"]["first"] = url_for(".", **(env.request.parameters - [ "offset" ]))
            env.request.dataset["nav"]["prev"] = url_for(".", **(env.request.parameters + { "offset": offset - env.request.parameters["limit"] }))

    def _setNavNext(self, offset, count):
        env.request.dataset["nav"]["next"] = None
        env.request.dataset["nav"]["last"] = None
        if count > offset + env.request.parameters["limit"]:
            offset = offset + env.request.parameters["limit"]
            env.request.dataset["nav"]["next"] = url_for(".", **(env.request.parameters + { "offset": offset }))
            offset = count - ((count % env.request.parameters["limit"]) or env.request.parameters["limit"])
            env.request.dataset["nav"]["last"] = url_for(".", **(env.request.parameters + { "offset": offset }))

    def _getInlineFilter(self, name):
        return name, env.request.parameters.get(name)

    def _setMessages(self, criteria):
        env.request.dataset["messages"] = [ ]
        offset, limit = env.request.parameters["offset"], env.request.parameters["limit"]

        # count_asc and count_desc methods are not valid for message enumeration
        order_by = "time_asc" if env.request.parameters["orderby"] in ("count_asc", "count_desc") else env.request.parameters["orderby"]

        results = env.dataprovider.get(criteria=criteria, offset=offset, limit=limit, order_by=order_by, type=self.root)
        for obj in results:
            dataset = self._setMessage(obj, obj["%s.messageid" % self.root])
            env.request.dataset["messages"].append(dataset)

        return env.dataprovider.query(["count(1)"], criteria=criteria, type=self.root)[0][0]

    def _updateMessages(self, action, criteria):
        if not env.request.parameters["selection"]:
            return

        if not env.request.user.has("IDMEF_ALTER"):
            raise usergroup.PermissionDeniedError(["IDMEF_ALTER"], self.current_view)

        action(functools.reduce(lambda x,y: x | y, env.request.parameters["selection"]))
        del env.request.parameters["selection"]
