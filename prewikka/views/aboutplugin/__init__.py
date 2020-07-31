# Copyright (C) 2014-2020 CS GROUP - France. All Rights Reserved.
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

import collections
import itertools
import json
import pkg_resources

from prewikka import cli, database, error, response, template, utils, version, view
from prewikka.utils import html


class AboutPlugin(view.View):
    plugin_name = "Plugin management"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("Plugin installation and activation management page")
    plugin_mandatory = True
    plugin_htdocs = (("aboutplugin", pkg_resources.resource_filename(__name__, 'htdocs')),)

    view_permissions = [N_("USER_MANAGEMENT")]

    _all_plugins = ((N_("Apps: API"), "prewikka.plugins"),
                    (N_("Apps: View"), "prewikka.views"),
                    (N_("Apps: Dataprovider backend"), "prewikka.dataprovider.backend"),
                    (N_("Apps: Dataprovider type"), "prewikka.dataprovider.type"),
                    (N_("Apps: Authentication"), "prewikka.auth"),
                    (N_("Apps: Identification"), "prewikka.session"),
                    (N_("Apps: Renderer backend"), "prewikka.renderer.backend"),
                    (N_("Apps: Renderer type"), "prewikka.renderer.type"))

    def _add_plugin_info(self, data, catname, mod):
        dbup = database.DatabaseUpdateHelper(mod.full_module_name, mod.plugin_database_version, mod.plugin_database_branch)
        curversion = dbup.get_schema_version()

        try:
            upinfo = dbup.list()
            if upinfo:
                data.maintenance_total += len(upinfo)
                data.maintenance.setdefault(catname, []).append((mod, curversion, upinfo))
            else:
                data.installed.setdefault(catname, []).append((mod, env.db.is_plugin_active(mod)))

        except error.PrewikkaUserError as e:
            data.maintenance.setdefault(catname, []).append((mod, curversion, [e]))

    def _iter_plugin(self):
        for catname, entrypoint in self._all_plugins:
            for plugin in env.all_plugins[entrypoint].values():
                yield catname, plugin

    def _get_plugin_infos(self):
        # FIXME: for some reason, the cache gets desynchronized at initialization.
        # This is a temporary fix.
        env.db.modinfos_cache.clear()

        data = utils.AttrObj(installed=collections.OrderedDict(), maintenance=collections.OrderedDict(), maintenance_total=0)
        for catname, plugin in self._iter_plugin():
            self._add_plugin_info(data, catname, plugin)

        return data

    @cli.register("list", "plugin", help=N_("list plugin: list installed plugins"))
    def _list_plugins(self):
        ret = []
        for plugins in self._get_plugin_infos().installed.values():
            for mod, active in plugins:
                ret.append(mod.full_module_name)

        return sorted(ret)

    @view.route("/settings/apps", methods=["GET"], menu=(N_("Apps"), N_("Apps")), help="#apps")
    def render_get(self):
        dset = template.PrewikkaTemplate(__name__, "templates/aboutplugin.mak").dataset()
        data = self._get_plugin_infos()

        dset["installed"] = data.installed
        dset["maintenance"] = data.maintenance
        dset["maintenance_total"] = data.maintenance_total

        return dset.render()

    @view.route("/settings/apps/enable", methods=["POST"])
    def enable(self):
        upsrt = []

        for catname, plugin in self._iter_plugin():
            enabled = plugin.plugin_mandatory or plugin.full_module_name in env.request.parameters["enable_plugin"]
            upsrt.append((plugin.full_module_name, enabled))

        if upsrt:
            env.db.upsert("Prewikka_Module_Registry", ["module", "enabled"], upsrt, pkey=["module"])
            env.db.trigger_plugin_change()

        return response.PrewikkaResponse({"type": "reload", "target": "window"})

    @view.route("/settings/apps/update", methods=["GET"])
    def update(self):
        self._update(env.request.web.send_stream)

    @cli.register("sync", "plugin", help=N_("sync plugin: initialize the plugin database schemas"))
    def _update_plugins(self):
        self._update(lambda *args, **kwargs: None)

    def _update(self, send_stream):
        data = self._get_plugin_infos()

        send_stream(json.dumps({"total": data.maintenance_total}), event="begin", sync=True)

        for mod, fromversion, uplist in itertools.chain.from_iterable(data.maintenance.values()):
            for upscript in uplist:
                if isinstance(upscript, Exception):
                    continue

                label = _("Applying %(module)s %(script)s...") % {'module': mod.full_module_name, 'script': text_type(upscript)}
                send_stream(json.dumps({"label": html.escape(label), 'module': html.escape(mod.full_module_name), 'script': html.escape(text_type(upscript))}), sync=True)

                try:
                    upscript.apply()
                except Exception as e:
                    send_stream(json.dumps({"logs": "\n".join(html.escape(x) for x in upscript.query_logs), "error": html.escape(text_type(e))}), sync=True)
                    break
                else:
                    send_stream(json.dumps({"logs": "\n".join(html.escape(x) for x in upscript.query_logs), "success": True}), sync=True)

        send_stream(data=json.dumps({"label": _("All updates applied")}), event="finish", sync=True)
        send_stream("close", event="close")

        env.db.trigger_plugin_change()
