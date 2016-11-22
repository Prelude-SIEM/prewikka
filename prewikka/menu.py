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

from copy import copy

from prewikka import hookmanager, utils
from prewikka.utils import AttrObj


class MenuManager(object):
    """
    Handle section placement in the menus.
    """
    _DEFAULT_MENU = "ADMIN"
    _DEFAULT_ICON = "sliders"

    def __init__(self):
        self._all_sections = set()
        self._loaded_sections = {}
        self._sections_path = {}

    def get_sections(self, user=None):
        def _merge(d1, d2):
            for section, tabs in d2.items():
                d1[section] = copy(d1.get(section, {}))
                for tab, views in tabs.items():
                    d1[section][tab] = views

        d = copy(self._loaded_sections)
        [_merge(d, i) for i in hookmanager.trigger("HOOK_MENU_LOAD", user) if i]

        return d

    def get_sections_path(self):
        return self._sections_path

    def add_section(self, section):
        self._all_sections.add(section)

    def add_section_info(self, view):
        self._loaded_sections.setdefault(view.view_section, utils.OrderedDict()) \
                             .setdefault(view.view_name, utils.OrderedDict())[view.view_id] = view

        self._sections_path.setdefault(utils.nameToPath(view.view_section), {}) \
                           .setdefault(utils.nameToPath(view.view_name), utils.OrderedDict())[utils.nameToPath(view.view_id)] = view.view_path

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
        loaded_sections = self.get_sections(user)
        menus = utils.OrderedDict()
        default_menu = AttrObj(icon=self._DEFAULT_ICON, entries=[], default=True)

        section_order_instance = env.config.general.get("section_order")
        section_order = next((sec for sec in env.config.section_order
                                      if sec.get_instance_name() == section_order_instance), {})

        for section, icon in section_order.items():
            if section in self._all_sections:
                # Sections that are declared in section_order but not loaded
                # should appear in the menu, but with an empty link
                views = self._get_display_views(loaded_sections.get(section))

                # Put the section in the previous menu (or in the default one if there is none)
                current_menu = next(reversed(menus.values())) if menus else default_menu
                current_menu.entries.append(AttrObj(name=section, views=views, icon=icon.value))

            else:
                # Create a new menu if the section_order entry does not match a section
                is_default = section == self._DEFAULT_MENU
                menus[section] = AttrObj(icon=icon.value, entries=[], default=is_default)

        for section in loaded_sections:
            # Put the sections not declared in section_order in the default menu
            if section not in section_order:
                views = self._get_display_views(loaded_sections.get(section))
                default_menu.entries.append(AttrObj(name=section, views=views, icon=None))

        if self._DEFAULT_MENU in menus:
            menus[self._DEFAULT_MENU].entries += default_menu.entries
        else:
            menus[self._DEFAULT_MENU] = default_menu

        return menus

    @classmethod
    def _get_display_views(cls, section):
        if not section:
            return None

        viewlist = []

        for views in section.values():
            view = next(iter(views.values()))
            if view.view_subsection:
                viewlist.append(view)

        return viewlist or [cls._get_first_view(section)]

    @staticmethod
    def _get_first_view(section):
        if not section:
            return None

        # Take the parent of the first view
        return next(iter(next(iter(section.values())).values()))
