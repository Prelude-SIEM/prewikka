# Copyright (C) 2004-2016 CS-SI. All Rights Reserved.
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
        self.parameters = parameters
        self.view_path = view_path

    def _isAlreadyFiltered(self, column, path, criterion, value):
        col = self.parameters.get(column)
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

                index = self.parameters.max_index
                extra["%s_object_%d" % (direction, index)] = p
                extra["%s_operator_%d" % (direction, index)] = operator
                extra["%s_value_%d" % (direction, index)] = v or ""
                self.parameters.max_index += 1

            else:
                val = self.parameters.get(p)
                if alreadyf is not False and (val and val == [v]):
                        alreadyf = True

                extra[p] = v or ""

        link = utils.create_link(self.view_path, self.parameters + extra - [ "offset" ])
        return AttrDict(value=real_value, inline_filter=link, already_filtered=alreadyf)

    def createTimeField(self, timeobj):
        if not timeobj:
            return { "value": "n/a" }

        return AttrDict(value=localization.format_datetime(timeobj, format="short"))

    def createHostField(self, object, value, category=None, direction=None, dns=True):
        field = self.createInlineFilteredField(object, value, direction)
        field["host_links"] = [ ]
        field["category"] = category

        field["url_infos"] = utils.create_link("hostinfoajax", {"host": value}) if "HOOK_HOST_TOOLTIP" in hookmanager.hookmgr else None
        field["url_popup"] = utils.create_link("AjaxHostURL", {"host": value})

        if value and dns is True:
            field["hostname"] = resolve.AddressResolve(value)
        else:
            field["hostname"] = value or _("n/a")

        if not value:
            return field

        for typ, linkname, link, widget in hookmanager.trigger("HOOK_LINK", value):
            if typ == "host":
                field["host_links"].append((linkname, link, widget))

        return field

    def createMessageIdentLink(self, messageid, view):
        if messageid:
            return utils.create_link("/".join((self.view_path, view)), { "messageid": messageid })

class HostInfoAjax(view.View):
    class HostInfoAjaxParameters(view.Parameters):
        def register(self):
            self.mandatory("host", text_type)

    view_parameters = HostInfoAjaxParameters

    def render(self):
        infos = []
        for info in hookmanager.trigger("HOOK_HOST_TOOLTIP", self.parameters["host"]):
            infos.extend(info)

        return infos

class MessageListing(view.View):
    plugin_htdocs = (("messagelisting", pkg_resources.resource_filename(__name__, 'htdocs')),)

    def _adjustCriteria(self, criteria):
        pass

    def render(self):
        view.View.render(self)
        self.dataset["order_by"] = self.parameters["orderby"]
        self.dataset["nav"] = {}

    def _setNavPrev(self, offset):
        if offset:
            self.dataset["nav"]["first"] = utils.create_link(self.view_path, self.parameters - [ "offset" ])
            self.dataset["nav"]["prev"] = utils.create_link(self.view_path,
                                                         self.parameters +
                                                         { "offset": offset - self.parameters["limit"] })
        else:
            self.dataset["nav"]["prev"] = None

    def _setNavNext(self, offset, count):
        if count > offset + self.parameters["limit"]:
            offset = offset + self.parameters["limit"]
            self.dataset["nav"]["next"] = utils.create_link(self.view_path, self.parameters + { "offset": offset })
            offset = count - ((count % self.parameters["limit"]) or self.parameters["limit"])
            self.dataset["nav"]["last"] = utils.create_link(self.view_path, self.parameters + { "offset": offset })
        else:
            self.dataset["nav"]["next"] = None

    def _getInlineFilter(self, name):
        return name, self.parameters.get(name)

    def _setMessages(self, criteria):
        self.dataset["messages"] = [ ]
        offset, limit = self.parameters["offset"], self.parameters["limit"]

        # count_asc and count_desc methods are not valid for message enumeration
        order_by = "time_asc" if self.parameters["orderby"] in ("count_asc", "count_desc") else self.parameters["orderby"]

        results = env.dataprovider.get(criteria=criteria, offset=offset, limit=offset+limit, order_by=order_by, type=self.root)
        for obj in results:
            dataset = self._setMessage(obj, obj["%s.messageid" % self.root])
            self.dataset["messages"].append(dataset)

        return env.dataprovider.query(["count(1)"], criteria=criteria, type=self.root)[0][0]

    def _updateMessages(self, action, criteria):
        if not self.parameters["selection"]:
            return

        if not env.request.user.has("IDMEF_ALTER"):
            raise usergroup.PermissionDeniedError(["IDMEF_ALTER"], self.current_view)

        action(functools.reduce(lambda x,y: x | y, self.parameters["selection"]))
        del self.parameters["selection"]
