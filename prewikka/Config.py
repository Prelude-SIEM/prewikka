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


class Config(dict):
    def __init__(self, filename="prewikka.conf"):
        dict.__init__(self)
        self.modules = { }
        input = ConfigParser.ConfigParser()
        input.readfp(open(filename))
        for section in input.sections():
            if section.find("module ") == 0:
                mod_name = section.replace("module ", "")
                subconfig = self.modules[mod_name] = { }
            else:
                subconfig = self[section] = { }
            for option in input.options(section):
                subconfig[option] = input.get(section, option)

    def __str__(self):
        content = dict.__str__(self)
        for name, value in self.modules.items():
            content += "\n%s: %s" % (name, value)
        return content


if __name__ == "__main__":
    print Config()
