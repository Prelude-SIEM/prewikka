# Copyright (C) 2004 Nicolas Delon <nicolas@prelude-ids.org>
# All Rights Reserved
#
# This file is part of the Prelude program.
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
# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING.  If not, write to
# the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.


import ConfigParser


class Config:
    def __init__(self, filename="prewikka.conf"):
        self._global = { }
        self.modules = { }
        conf = ConfigParser.ConfigParser()
        conf.readfp(open(filename))
        for option in conf.options("prewikka"):
            self._global[option] = conf.get("prewikka", option)
        for section in conf.sections():
            if section.find("module ") == 0:
                module = self.modules[section.replace("module ", "")] = { }
                for option in conf.options(section):
                    value = conf.get(section, option)
                    module[option] = value

    def __getitem__(self, key):
        return self._global[key]

    def __str__(self):
        content = "global: %s\n" % self._global
        for name, module in self.modules.items():
            content += "module %s: %s\n" % (name, module)
        return content
