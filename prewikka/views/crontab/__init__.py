# Copyright (C) 2017-2019 CS-SI. All Rights Reserved.
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

import datetime
import pkg_resources

from prewikka import crontab, localization, resource, response, template, utils, version, view
from prewikka.utils.viewhelpers import GridAjaxResponse, GridParameters


class CrontabView(view.View):
    plugin_name = N_("Scheduling management")
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("Scheduled jobs management page")
    plugin_htdocs = (("crontab", pkg_resources.resource_filename(__name__, 'htdocs')),)
    view_permissions = [N_("USER_MANAGEMENT")]

    @view.route("/settings/scheduler/disable", methods=["POST"])
    def disable(self):
        crontab.update(env.request.parameters.getlist("id", type=int), enabled=False)
        return response.PrewikkaResponse({"type": "reload", "target": "view"})

    @view.route("/settings/scheduler/enable", methods=["POST"])
    def enable(self):
        crontab.update(env.request.parameters.getlist("id", type=int), enabled=True)
        return response.PrewikkaResponse({"type": "reload", "target": "view"})

    @view.route("/settings/scheduler/<int:id>/save", methods=["POST"])
    def save(self, id=None):
        crontab.update_from_parameters(id, env.request.parameters)
        return response.PrewikkaResponse({"type": "reload", "target": "view"})

    @view.route("/settings/scheduler/<int:id>/edit")
    def edit(self, id=None):

        dataset = template.PrewikkaTemplate(__name__, "templates/cronjob.mak").dataset()
        dataset["job"] = crontab.get(id)

        return dataset.render()

    @view.route("/settings/scheduler", menu=(N_("Configuration"), N_("Scheduling")), help="#scheduling", parameters=GridParameters("cronjobs"))
    def list(self):
        dataset = template.PrewikkaTemplate(__name__, "templates/crontab.mak").dataset()
        return dataset.render()

    @view.route("/settings/scheduler/ajax_listing")
    def ajax_listing(self):
        now = utils.timeutil.utcnow()

        sort_index = env.request.parameters.get("sort_index", "name")
        sort_order = env.request.parameters.get("sort_order", "asc")
        sort_func = {
            "name": lambda x: _(x.name).lower(),
            "user": lambda x: text_type(x.user) if x.user else _("SYSTEM"),
            "last": lambda x: x.base,
            "next": lambda x: x.next_schedule - now if x.enabled else datetime.timedelta.max,
        }
        sort_key = sort_func.get(sort_index, sort_func["name"])

        rows = []
        for i in sorted(crontab.list(), key=sort_key, reverse=(sort_order == "desc")):
            if not i.enabled:
                next = _("Disabled")
            else:
                next = i.next_schedule - now
                if next.total_seconds() < 0:
                    next = _("Pending")
                else:
                    next = localization.format_timedelta(next, granularity="minute")

            if i.runcnt > 0:
                last = localization.format_timedelta(i.base - now, add_direction=True)
            else:
                last = _("n/a")

            if i.error:
                last = resource.HTMLNode("a", _("Error"), _class="cronjob-error")

            rows.append({
                "id": i.id,
                "name": resource.HTMLNode("a", _(i.name), href=url_for(".edit", id=i.id)),
                "schedule": crontab.format_schedule(i.schedule),
                "user": text_type(i.user) if i.user else _("SYSTEM"),
                "last": last,
                "next": next,
                "error": i.error
            })

        return GridAjaxResponse(rows, len(rows))
