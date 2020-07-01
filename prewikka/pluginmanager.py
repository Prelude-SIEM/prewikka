# Copyright (C) 2015-2020 CS-SI. All Rights Reserved.
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
import pkg_resources

from prewikka import database, error, log, registrar
from prewikka.localization import translation

logger = log.get_logger(__name__)


class PluginBase(registrar.DelayedRegistrar):
    plugin_name = None
    plugin_version = None
    plugin_author = None
    plugin_license = None
    plugin_copyright = None
    plugin_description = None

    plugin_database_branch = None
    plugin_database_version = None
    plugin_database_autoupdate = False

    plugin_htdocs = None
    plugin_locale = None

    plugin_after = []
    plugin_require = []
    plugin_deprecate = []
    plugin_mandatory = False
    plugin_enabled = True

    @classmethod
    def _handle_attributes(cls, autoupdate):
        if cls.plugin_htdocs:
            env.htdocs_mapping.update(cls.plugin_htdocs)

        if cls.plugin_locale:
            translation.add_domain(*cls.plugin_locale)

        dh = database.DatabaseUpdateHelper(cls.full_module_name, cls.plugin_database_version, cls.plugin_database_branch, cls.plugin_enabled)
        if autoupdate or cls.plugin_database_autoupdate:
            dh.apply()
        else:
            dh.check()


class PluginPreload(PluginBase):
    plugin_classes = []


class PluginManager(object):
    def __init__(self, entrypoint, autoupdate=False):
        self.__instances = []
        self.__dinstances = {}

        loaded = {}
        for value in env.all_plugins.values():
            for name, plugin in value.items():
                loaded[name] = not(plugin.error)

        plugins = self.iter_plugins(entrypoint)
        plist = [(p, False) for p in plugins]
        self._load_plugin_list(plist, plugins, autoupdate, loaded, [])
        env.all_plugins[entrypoint] = collections.OrderedDict((name, plugins[name]) for name in loaded if name in plugins)

    def _add_plugin(self, plugin_class, autoupdate, name=None):
        plugin_class._handle_attributes(autoupdate)
        self[name or plugin_class.__name__] = plugin_class

    @staticmethod
    def initialize_plugin(plugin_class):
        try:
            return plugin_class()
        except error.PrewikkaUserError as e:
            plugin_class.error = e
            logger.warning("%s: plugin loading failed: %s", plugin_class.__name__, e)
            raise
        except Exception as e:
            plugin_class.error = e
            logger.exception("%s: plugin loading failed: %s", plugin_class.__name__, e)
            raise

    @staticmethod
    def iter_plugins(entrypoint):
        plist = {}
        ignore = {}
        module_map = {}

        for i in pkg_resources.iter_entry_points(entrypoint):
            if i.module_name in ignore:
                continue

            logger.debug("loading plugin '%s'" % i.name)
            try:
                plugin_class = i.load()
            except Exception as e:
                logger.exception("%s: %s", i.module_name, e)
                continue

            plugin_class.error = None
            plugin_class._assigned_name = i.name
            plugin_class.full_module_name = ":".join((plugin_class.__module__, i.attrs[0]))

            if plugin_class.full_module_name in ignore:
                continue

            plist[plugin_class.full_module_name] = plugin_class
            module_map.setdefault(plugin_class.__module__, {})[plugin_class.full_module_name] = True

            for j in plugin_class.plugin_deprecate:
                ignore[j] = True

                ret = plist.pop(j, None)
                if ret:
                    continue

                for mod in module_map.get(j, []):
                    plist.pop(mod, None)

        return plist

    def _handle_preload(self, plugin_class, autoupdate):
        plugin_class._handle_attributes(autoupdate)

        for i in plugin_class().plugin_classes:
            i.full_module_name = ":".join((i.__module__, i.__name__))
            self._add_plugin(i, autoupdate)

    def _load_single(self, plugin_class, autoupdate):
        try:
            if issubclass(plugin_class, PluginPreload):
                self._handle_preload(plugin_class, autoupdate)
            else:
                self._add_plugin(plugin_class, autoupdate, name=plugin_class._assigned_name)

        except error.PrewikkaUserError as e:
            plugin_class.error = e
            logger.warning("%s: plugin loading failed: %s", plugin_class.full_module_name, e)
            return False

        except Exception as e:
            plugin_class.error = e
            logger.exception("%s: plugin loading failed: %s", plugin_class.full_module_name, e)
            return False

        return True

    def _load_plugin_with_dependencies(self, mname, pmap, autoupdate, loaded, deplist):
        if mname in loaded:
            return loaded[mname]

        plugin_class = pmap.get(mname)
        if not plugin_class:
            return False

        if mname in deplist:
            plugin_class.error = N_("Circular dependencies detected: %s", " -> ".join(deplist + [mname]))
            logger.warning("%s: plugin loading failed, circular dependencies detected: %s" % (mname, " -> ".join(deplist + [mname])))
            return False

        plist = [(p, True) for p in plugin_class.plugin_require] + [(p, False) for p in plugin_class.plugin_after]
        ret = self._load_plugin_list(plist, pmap, autoupdate, loaded, deplist + [mname])
        if ret is not True:
            if not plugin_class.error:
                plugin_class.error = N_("Missing dependency: %s", ret)
                logger.warning("%s: plugin loading failed: missing dependency '%s'" % (mname, ret))

            return False

        ret = self._load_single(plugin_class, autoupdate)
        if not ret:
            return False

        return True

    def _load_plugin_list(self, plist, pmap, autoupdate, loaded, deplist):
        for mname, needed in plist:
            ret = self._load_plugin_with_dependencies(mname, pmap, autoupdate, loaded, deplist)
            loaded[mname] = ret
            if not ret and needed:
                return mname

        return True

    def keys(self):
        return self.__dinstances.keys()

    def __iter__(self):
        return iter(self.__instances)

    def __setitem__(self, key, value):
        self.__instances.append(value)
        self.__dinstances[key.lower()] = value

    def __getitem__(self, key):
        return self.__dinstances[key.lower()]

    def __contains__(self, item):
        return item in self.__dinstances
