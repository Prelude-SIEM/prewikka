# Copyright (C) 2016-2017 CS-SI. All Rights Reserved.
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
import os
import yaml
from copy import copy

from prewikka import error, hookmanager, siteconfig


class MenuManager(object):
    """
    Handle section placement in the menus.
    """
    def __init__(self):
        self._all_sections = set()
        self._declared_sections = {}
        self._loaded_sections = {}
        self._sorted = False
        self._default_view = None
        self._default_section = None
        self._default_tab = None

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
                        if self._default_section:
                            raise error.PrewikkaUserError(N_("Menu error"), N_("Multiple default views"))
                        self._default_section, self._default_tab = (section["name"], section["default_tab"])

                    self._declared_sections[section["name"]] = section.get("tabs", [])

        if not default_menu:
            self._menus[-1]["default"] = True

    def get_sections(self):
        self._sort_tabs()
        return self._loaded_sections

    def get_menus(self):
        return self._menus

    def get_declared_sections(self):
        return self._declared_sections

    def get_default_view(self):
        return self._default_view

    def add_section(self, name):
        self._all_sections.add(name)

    def add_section_info(self, view):
        self.add_section(view.view_menu[0])

        self._loaded_sections.setdefault(view.view_menu[0], collections.OrderedDict()) \
                             .setdefault(view.view_menu[1], collections.OrderedDict())[view.view_id] = view

        if view.view_menu[:2] == (self._default_section, self._default_tab):
            self._default_view = view

    def _tab_index(self, section, tab):
        try:
            return self._declared_sections[section].index(tab)
        except ValueError:
            # Arbitrary big number to put the tab at the end
            return 100

    def _sort_tabs(self):
        if self._sorted:
            return

        ret = {}

        for section, views in self._loaded_sections.items():
            if section not in self._declared_sections:
                ret[section] = views
            else:
                ret[section] = collections.OrderedDict()
                for name in sorted(views.keys(), key=lambda tab: self._tab_index(section, tab)):
                    ret[section][name] = views[name]

        self._sorted = True
        self._loaded_sections = ret
