# Copyright (C) 2004-2015 CS-SI. All Rights Reserved.
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

import copy, time, urllib, pkg_resources
from prewikka import view, usergroup, utils, resolve, mainmenu, localization, env

class MessageListingParameters(mainmenu.MainMenuParameters):
    def register(self):
        mainmenu.MainMenuParameters.register(self)

        self.optional("offset", int, default=0)
        self.optional("limit", int, default=50, save=True)
        self.optional("selection", list, [ ])
        self.optional("listing_apply", str)
        self.optional("action", str)

        # submit with an image passes the x and y coordinate values
        # where the image was clicked
        self.optional("x", int)
        self.optional("y", int)

    def normalize(self, *args, **kwargs):
          # Filter out invalid limit which would trigger an exception.
          if self.has_key("limit") and int(self["limit"]) <= 0:
                self.pop("limit")

          return mainmenu.MainMenuParameters.normalize(self, *args, **kwargs)

class ListedMessage(dict):
    def __init__(self, view_path, parameters):
        self.parameters = parameters
        self.timezone = parameters["timezone"]
        self.view_path = view_path

    def _isAlreadyFiltered(self, column, path, criterion, value):
        if not self.parameters.has_key(column):
            return False

        return (path, criterion, value) in self.parameters[column]

    def createInlineFilteredField(self, path, value, direction=None, real_value=None):
        if type(path) is not list and type(path) is not tuple:
            path = [ path ]
        else:
            if not path:
                return { "value": None, "inline_filter": None, "already_filtered": False }

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
                if alreadyf is not False and (self.parameters.has_key(p) and self.parameters[p] == [v]):
                        alreadyf = True

                extra[p] = v or ""

        link = utils.create_link(self.view_path, self.parameters + extra - [ "offset" ])
        return { "value": utils.escape_html_string(real_value), "inline_filter": link, "already_filtered": alreadyf }

    def createTimeField(self, timeobj, timezone=None):
        if not timeobj:
            return { "value": "n/a" }

        timeval = float(timeobj)

        tzobj = { "utc": utils.timeutil.tzutc,
                  "sensor_localtime": lambda: utils.timeutil.tzoffset("UTC", timeobj.getGmtOffset()),
                  "frontend_localtime": utils.timeutil.tzlocal
        }[timezone]()

        time_value = localization.format_time(timeval, format="short", tzinfo=tzobj)

        value = localization.format_datetime(timeval, format="short", tzinfo=tzobj)
        if isinstance(tzobj, utils.timeutil.tzoffset):
            value += " (" + localization.format_time(timeval, format="z", tzinfo=tzobj) + ")"

        return { "value": value or "n/a" }

    def createHostField(self, object, value, category=None, direction=None, dns=True):
        field = self.createInlineFilteredField(object, value, direction)
        field["host_links"] = [ ]
        field["category"] = category

        if value and dns is True:
            field["hostname"] = resolve.AddressResolve(value)
        else:
            field["hostname"] = value or _("n/a")

        if not value:
            return field

        for typ, linkname, link, widget in env.hookmgr.trigger("HOOK_LINK", value):
            if typ == "host":
                field["host_links"].append((linkname, link, widget))

        if "host" in env.url:
            for urlname, url in env.url["host"].items():
                field["host_links"].append((urlname.capitalize(), url.replace("$host", value), False))

        return field

    def createMessageIdentLink(self, messageid, view):
        return utils.create_link("/".join((self.view_path, view)), { "messageid": messageid })

    def createMessageLink(self, ident, view):
        return utils.create_link("/".join((self.view_path, view)), { "ident": ident })


class MessageListing(view.View):
    plugin_htdocs = (("messagelisting", pkg_resources.resource_filename(__name__, 'htdocs')),)

    def _adjustCriteria(self, criteria):
        pass

    def render(self):
        view.View.render(self)
        self.dataset["order_by"] = self.parameters["orderby"]

    def _setNavPrev(self, offset):
        if offset:
            self.dataset["nav.first"] = utils.create_link(self.view_path, self.parameters - [ "offset" ])
            self.dataset["nav.prev"] = utils.create_link(self.view_path,
                                                         self.parameters +
                                                         { "offset": offset - self.parameters["limit"] })
        else:
            self.dataset["nav.prev"] = None

    def _setNavNext(self, offset, count):
        if count > offset + self.parameters["limit"]:
            offset = offset + self.parameters["limit"]
            self.dataset["nav.next"] = utils.create_link(self.view_path, self.parameters + { "offset": offset })
            offset = count - ((count % self.parameters["limit"]) or self.parameters["limit"])
            self.dataset["nav.last"] = utils.create_link(self.view_path, self.parameters + { "offset": offset })
        else:
            self.dataset["nav.next"] = None

    def _getInlineFilter(self, name):
        return name, self.parameters.get(name)

    def _setMessages(self, criteria):
        self.dataset["messages"] = [ ]

        # count_asc and count_desc methods are not valid for message enumeration
        order_by = "time_asc" if self.parameters["orderby"] in ("count_asc", "count_desc") else self.parameters["orderby"]

        results = self._getMessageIdents(criteria, order_by=order_by)
        for ident in results[self.parameters["offset"] : self.parameters["offset"] + self.parameters["limit"]]:
            message = self._fetchMessage(ident)
            dataset = self._setMessage(message, ident)
            self.dataset["messages"].append(dataset)

        return len(results)

    def _updateMessages(self, action, crit_and_ident=False):
        if len(self.parameters["selection"]) == 0:
            return

        if not self.user.has(usergroup.PERM_IDMEF_ALTER):
            raise usergroup.PermissionDeniedError(self.current_view)

        idents = [ ]
        criterial = []
        for item in self.parameters["selection"]:
            if item.isdigit():
                idents += [ long(item) ]
            else:
                criteria = urllib.unquote_plus(item)
                if not crit_and_ident:
                        idents += self._getMessageIdents(criteria)
                else:
                        criterial.append(criteria)

        action((idents, criterial) if crit_and_ident else idents, is_ident=crit_and_ident)
        del self.parameters["selection"]
