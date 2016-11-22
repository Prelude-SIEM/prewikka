# Copyright (C) 2015-2016 CS-SI. All Rights Reserved.
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

import os
import sys
import traceback

import pkg_resources
from prewikka import database, env, error, hookmanager, log, usergroup, utils
from prewikka.localization import translation

logger = log.getLogger(__name__)


class PluginBase(hookmanager.HookRegistrar):
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

    plugin_deprecate = []
    plugin_mandatory = False


class PluginPreload(PluginBase):
    plugin_classes = []


class PluginManager:
    @staticmethod
    def _handle_attributes(plugin_class, autoupdate):
        if plugin_class.plugin_htdocs:
            env.htdocs_mapping.update(plugin_class.plugin_htdocs)

        if plugin_class.plugin_locale:
            translation.addDomain(*plugin_class.plugin_locale)

        for permission in getattr(plugin_class, "view_permissions", []):
            usergroup.ALL_PERMISSIONS.declare(permission)

        for permission in getattr(plugin_class, "additional_permissions", []):
            usergroup.ALL_PERMISSIONS.declare(permission)

        dh = database.DatabaseUpdateHelper(plugin_class.full_module_name, plugin_class.plugin_database_version, plugin_class.plugin_database_branch)
        if autoupdate or plugin_class.plugin_database_autoupdate:
            dh.apply()
        else:
            dh.check()

    @staticmethod
    def _handle_section(plugin_class):
        if hasattr(plugin_class, "view_section") and plugin_class.view_section:
            env.menumanager.add_section(plugin_class.view_section)

    def _addPlugin(self, plugin_class, autoupdate, name=None):
        self._handle_attributes(plugin_class, autoupdate)
        self[name or plugin_class.__name__] = plugin_class
        self._count += 1

    @staticmethod
    def iter_plugins(entrypoint):
        plist = []
        ignore = []

        for i in pkg_resources.iter_entry_points(entrypoint):
            if i.module_name in ignore:
                continue

            logger.debug("loading plugin '%s'" % i.name)
            try:
                plugin_class = i.load()
            except Exception as e:
                logger.exception("%s: %s", i.module_name, e)
                continue

            plugin_class._assigned_name = i.name
            plugin_class.full_module_name = ":".join((plugin_class.__module__, i.attrs[0]))

            plist.append(plugin_class)
            ignore.extend(plugin_class.plugin_deprecate)

        return (i for i in plist if i.__module__ not in ignore)

    def _handle_preload(self, plugin_class, autoupdate):
        # Get sections from all views before testing plugin database version
        for x in plugin_class.plugin_classes:
            self._handle_section(x)

        self._handle_attributes(plugin_class, autoupdate)

        for i in plugin_class().plugin_classes:
            i.full_module_name = ":".join((i.__module__, i.__name__))
            self._addPlugin(i, autoupdate)

    def __init__(self, entrypoint, autoupdate=False):
        self._count = 0
        self.__instances = []
        self.__dinstances = {}

        for plugin_class in self.iter_plugins(entrypoint):
            try:
                if issubclass(plugin_class, PluginPreload):
                    self._handle_preload(plugin_class, autoupdate)
                else:
                    self._handle_section(plugin_class)
                    self._addPlugin(plugin_class, autoupdate, name=plugin_class._assigned_name)

            except error.PrewikkaUserError as e:
                logger.warning("%s: plugin loading failed: %s", plugin_class.full_module_name, e)

            except Exception as e:
                logger.exception("%s: plugin loading failed: %s", plugin_class.full_module_name, e)

    def getPluginCount(self):
        return self._count

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
