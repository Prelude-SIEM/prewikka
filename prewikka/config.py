# Copyright (C) 2004-2015 CS-SI. All Rights Reserved.
# Author: Nicolas Delon <nicolas.delon@prelude-ids.com>
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


from prewikka import myconfigparser, siteconfig, utils


class Config(object):
    def __init__(self, filename=None):
        if not filename:
            filename=siteconfig.conf_dir + "/prewikka.conf"

        self.general = myconfigparser.ConfigParserSection("general")
        self.section_order = myconfigparser.ConfigParserSection("section_order")
        self.interface = myconfigparser.ConfigParserSection("interface")
        self.database = myconfigparser.ConfigParserSection("database")
        self.idmef_database = myconfigparser.ConfigParserSection("idmef_database")
        self.renderer_defaults = myconfigparser.ConfigParserSection("renderer_defaults")

        self.log = {}
        self.auth = None
        self.session = None
        self.url = { }

        file = myconfigparser.MyConfigParser(filename)
        file.load()

        for section in file.getSections():
            if " " in section.name:
                type, name = section.name.split(" ")
                self._set_generic_dict(type, name, section)
            else:
                self._set_generic(section.name, section)

    def _set_generic_dict(self, dtype, section_name, section_object):
        d = getattr(self, dtype, None)
        if not d:
            d = myconfigparser.ConfigParserSection(section_name)
            setattr(self, dtype, d)

        d[section_name] = section_object

    def _set_generic(self, section_name, section_object):
        setattr(self, section_name, section_object)
