# Copyright (C) 2016-2018 CS-SI. All Rights Reserved.
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

import collections
import copy
import itertools
import os
import yaml

from prewikka import error, hookmanager, siteconfig
from prewikka.utils import cache


class MenuManager(object):
    default_endpoint = None

    """
    Handle section placement in the menus.
    """
    def __init__(self):
        self._declared_sections = {}
        self._loaded_sections = {}
        self._default_menu = None

        filename = env.config.interface.get("menu_order", "menu.yml")
        if not os.path.isabs(filename):
            filename = os.path.join(siteconfig.conf_dir, filename)

        with open(filename, "r") as f:
            self._menus = yaml.load(f)

        if not self._menus:
            raise error.PrewikkaUserError(N_("Menu error"), N_("Empty menu"))

        default_menu = False

        for menu in self._menus:
            if "name" not in menu and "icon" not in menu:
                raise error.PrewikkaUserError(N_("Menu error"), N_("Menu without a name in %s", filename))

            if menu.get("default"):
                if default_menu:
                    raise error.PrewikkaUserError(N_("Menu error"), N_("Multiple default menus"))

                default_menu = True

            for category in menu.get("categories", []):

                for section in category.get("sections", []):
                    if "name" not in section:
                        raise error.PrewikkaUserError(N_("Menu error"), N_("Section without a name in %s", filename))

                    if "default_tab" in section:
                        if self._default_menu:
                            raise error.PrewikkaUserError(N_("Menu error"), N_("Multiple default views"))

                        self._default_menu = (section["name"], section["default_tab"])

                    self._declared_sections[section["name"]] = collections.OrderedDict((v, idx) for idx, v in enumerate(section.get("tabs", [])))

        if not default_menu:
            self._menus[-1]["default"] = True

    @cache.request_memoize("get_sections")
    def get_sections(self):
        ret = {}
        _loaded_sections = copy.deepcopy(self._loaded_sections)

        for section, tab, endpoint in itertools.chain.from_iterable(hookmanager.trigger("HOOK_MENU_LOAD")):
            _loaded_sections.setdefault(section, collections.OrderedDict())[tab] = endpoint

        for section, tabs in _loaded_sections.items():
            if section not in self._declared_sections:
                ret[section] = tabs
            else:
                ret[section] = collections.OrderedDict()
                for name in sorted(tabs.keys(), key=lambda tab: self._declared_sections[section].get(tab, 100)):
                    ret[section][name] = tabs[name]

        return ret

    def get_menus(self):
        return self._menus

    def get_declared_sections(self):
        return self._declared_sections

    def add_section_info(self, section, tab, endpoint, **kwargs):
        self._loaded_sections.setdefault(section, collections.OrderedDict())[tab] = (endpoint, kwargs)

        if (section, tab) == self._default_menu:
            self.default_endpoint = endpoint
