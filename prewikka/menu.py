# Copyright (C) 2016 CS-SI. All Rights Reserved.
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

import os
import yaml
from copy import copy

from prewikka import error, hookmanager, siteconfig
from prewikka.utils import AttrObj, OrderedDict


class MenuManager(object):
    """
    Handle section placement in the menus.
    """
    _DEFAULT_MENU = "ADMIN"
    _DEFAULT_ICON = "sliders"

    def __init__(self):
        self._all_sections = set()
        self._declared_sections = {}
        self._loaded_sections = {}
        self._sorted = False

        filename = env.config.general.get("menu_order", "menu.yml")
        if not os.path.isabs(filename):
            filename = os.path.join(siteconfig.conf_dir, filename)

        with open(filename, "r") as f:
            self._menu_order = yaml.load(f)

        for menu in self._menu_order:
            if "name" not in menu:
                raise error.PrewikkaUserError(N_("Menu error"), N_("Menu without a name in %s") % filename)

            for section in menu.get("sections", []):
                if "name" not in section:
                    raise error.PrewikkaUserError(N_("Menu error"), N_("Section without a name in %s") % filename)

                self._declared_sections[section["name"]] = section.get("tabs", [])

    def get_sections(self, user=None):
        def _merge(d1, d2):
            for section, tabs in d2.items():
                d1[section] = copy(d1.get(section, {}))
                for tab, views in tabs.items():
                    d1[section][tab] = views

        d = copy(self._loaded_sections)
        [_merge(d, i) for i in hookmanager.trigger("HOOK_MENU_LOAD", user) if i]

        return d

    def add_section(self, name):
        self._all_sections.add(name)

    def add_section_info(self, view):
        self.add_section(view.view_menu[0])

        self._loaded_sections.setdefault(view.view_menu[0], OrderedDict()) \
                             .setdefault(view.view_menu[1], OrderedDict())[view.view_id] = view

    def _sort_tabs_key(self, section, tab):
        try:
            return self._declared_sections[section].index(tab)
        except ValueError:
            # Arbitrary big number to put the tab at the end
            return 100

    def _sort_tabs(self):
        ret = {}

        for section, views in self._loaded_sections.items():
            if section not in self._declared_sections:
                ret[section] = views
            else:
                ret[section] = OrderedDict((name, views[name]) for name in sorted(views.keys(), key=lambda tab: self._sort_tabs_key(section, tab)))

        self._loaded_sections = ret

    def get_menus(self, user):
        """
        Return the menu structure in the following form:
        {
            menu1: {
                icon: icon1,
                entries: [
                    {name: name11, link: link11, icon: icon11},
                    {name: name12, link: link12, icon: icon12}
                ]
            },
            menu2: {
                icon: icon2,
                entries: [
                    ...
                ]
            }
        }
        """
        if not self._sorted:
            self._sort_tabs()
            self._sorted = True

        loaded_sections = self.get_sections(user)
        menus = OrderedDict()
        default_menu = AttrObj(icon=self._DEFAULT_ICON, entries=[], default=True)

        for menu in self._menu_order:
            current_menu = AttrObj(icon=menu.get("icon"), entries=[], default=(menu["name"] == self._DEFAULT_MENU))

            for section in menu.get("sections", []):
                name = section["name"]
                if name not in self._all_sections:
                    continue

                if name in loaded_sections:
                    views = self._get_display_views(loaded_sections[name], expand=section.get("expand", False))
                else:
                    # Sections that are declared in the YAML file but not loaded
                    # should appear in the menu, but with an empty link
                    views = None

                # Put the section in the current menu
                current_menu.entries.append(AttrObj(name=name, views=views, icon=section.get("icon")))

            menus[menu["name"]] = current_menu

        for section_name in loaded_sections:
            # Put the sections not declared in the YAML file into the default menu
            if section_name not in self._declared_sections:
                views = self._get_display_views(loaded_sections[section_name])
                default_menu.entries.append(AttrObj(name=section_name, views=views, icon=None))

        if self._DEFAULT_MENU in menus:
            menus[self._DEFAULT_MENU].entries += default_menu.entries
        else:
            menus[self._DEFAULT_MENU] = default_menu

        return menus

    @classmethod
    def _get_display_views(cls, section, expand=False):
        if expand:
            return [next(iter(views.values())) for views in section.values()]

        return [cls._get_first_view(section)]

    @staticmethod
    def _get_first_view(section):
        # Take the parent of the first view
        return next(iter(next(iter(section.values())).values()))
