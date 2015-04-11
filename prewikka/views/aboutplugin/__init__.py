# Copyright (C) 2014-2015 CS-SI. All Rights Reserved.
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

import pkg_resources, os, json

from . import templates
from prewikka import view, database, usergroup, version, env



class AboutPlugin(view.View):
    plugin_name = "Plugin management"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = _("Plugin installation and activation management page")

    view_name = N_("Plugins")
    view_template = templates.aboutplugin
    view_section = N_("Settings")
    view_permissions = [ usergroup.PERM_USER_MANAGEMENT ]
    view_order = 6

    class AboutPluginParameters(view.Parameters):
        def register(self):
            self.optional("apply_update", str)
            self.optional("enable_plugin", [str])

    view_parameters = AboutPluginParameters
    _all_plugins = ((_("View plugins"), "prewikka.views"),
                    (_("API plugins"), "prewikka.plugins"),
                    (_("Authentication plugins"), "prewikka.auth"),
                    (_("Session plugins"), "prewikka.session"),
                    (_("Renderer plugins"), "prewikka.renderer.backend"),
                    (_("Renderer type"), "prewikka.renderer.type"))

    def _apply_update(self, data):
        self.dataset = None
        self.request.sendStream(json.dumps({"total": data.maintenance_total}), event="begin", sync=True)

        for lst in data.maintenance.values():

            for mod, fromversion, toversion in lst:
                dbup = database.DatabaseUpdateHelper(mod.__module__, mod.plugin_database_version, mod.plugin_database_branch)
                try:
                    l = dbup.list()
                except Exception as e:
                    continue

                for upscript in l:
                    label = _("Applying %(module)s %(script)s...") % {'module': mod.__module__, 'script': str(upscript)}
                    self.request.sendStream(json.dumps({"label": label}), sync=True)

                    try:
                        upscript.apply()
                    except Exception as e:
                        self.request.sendStream(json.dumps({"error": str(e)}), sync=True)
                        continue

        self.request.sendStream(data=json.dumps({"label": _("All updates applied")}), event="finish", sync=True)


    def _add_plugin_info(self, data, catname, mod):
        upinfo = uperror = None

        dbup = database.DatabaseUpdateHelper(mod.__module__, mod.plugin_database_version, mod.plugin_database_branch)
        upinfo = dbup.list()

        if uperror:
            data.maintenance.setdefault(catname, []).append((mod, dbup.get_schema_version(), uperror))

        elif upinfo:
            data.maintenance_total += len(upinfo)
            data.maintenance.setdefault(catname, []).append((mod, dbup.get_schema_version(), ", ".join([str(i) for i in upinfo])))

        else:
            if "enable_plugin" in self.parameters:
                self._dbup(mod, mod.__module__ in self.parameters["enable_plugin"])

            data.installed.setdefault(catname, []).append((mod, env.db.is_plugin_active(mod.__module__)))


    def _dbup(self, mod, enabled):
        mname = env.db.escape(mod.__module__)

        if env.db.query("SELECT module FROM Prewikka_Module_Registry WHERE module = %s" % (mname)):
            env.db.query("UPDATE Prewikka_Module_Registry SET enabled=%d WHERE module=%s" % (enabled, mname))
        else:
            assert(not mod.plugin_database_version)
            env.db.query("INSERT INTO Prewikka_Module_Registry(module, enabled) VALUES(%s, %d)" % (mname, enabled))

    def render(self):
        class _data:
            pass

        data = _data()
        data.installed = {}
        data.maintenance = {}
        data.maintenance_total = 0

        for catname, entrypoint in self._all_plugins:
            for p in pkg_resources.iter_entry_points(entrypoint):
                try:
                    mod = p.load()
                    self._add_plugin_info(data, catname, mod)
                except Exception as e:
                    env.log.error("[%s]: error loading plugin, %s" % (p.module_name, e))

        if "apply_update" in self.parameters or "enable_plugin" in self.parameters:
            env.db.trigger_plugin_change()

        if "apply_update" in self.parameters:
            return self._apply_update(data)

        self.dataset["installed"] = data.installed
        self.dataset["maintenance"] = data.maintenance
        self.dataset["maintenance_total"] = data.maintenance_total
