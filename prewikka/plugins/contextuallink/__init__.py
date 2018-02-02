# Copyright (C) 2018 CS-SI. All Rights Reserved.
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

import functools

from prewikka import hookmanager, pluginmanager, resource, utils, version


class ContextualLink(pluginmanager.PluginBase):
    plugin_name = "Contextual links"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("Dynamic adding of contextual links")

    def __init__(self):
        pluginmanager.PluginBase.__init__(self)

        for i in env.config.url:
            self._init_url(i.get_instance_name() or "other", i)

    def _init_url(self, type, config):
        for option, value in config.items():
            if not self._check_option(option, value):
                continue

            hookmanager.register("HOOK_%s_LINK" % type.upper(), functools.partial(self._get_url_link, option, value))

            for path in config.get("paths", "").split(", "):
                hookmanager.register("HOOK_PATH_LINK", functools.partial(self._get_path_link, path, option, value))
                hookmanager.register("HOOK_%s_LINK" % path.upper(), functools.partial(self._get_url_link, option, value))

    def _check_option(self, option, value):
        return option != "paths"

    def _get_path_link(self, path, label, value):
        return (path, self._get_url_link(label, value, path=path))

    def _get_url_link(self, label, value, arg=None, path=None):
        d = {"data-path": path} if path else {}
        if arg:
            value = value.replace("$value", utils.url.quote_plus(arg.encode("utf-8")))

        return resource.HTMLNode("a", _(label.capitalize()), href=value, **d)
