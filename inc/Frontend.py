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

import sys
import glob

import Config
from layout import layoutManager
from Module import Module
from Query import Query


class Frontend:
    def __init__(self):
        self.modules = { }
        self.module_names = [ ]
        self.config = Config.Config()
        self.__loadModules()
        
    def __loadModules(self):
        modules = [ "mod_alert", "mod_test" ]
        for mod_name in modules:
            self.module_names.append(mod_name)
            self.modules[mod_name] = Module(mod_name, self.config.modules.get(mod_name, { }))
    
    def build(self, query):
        try:
            mod_name = query["mod"]
        except KeyError:
            mod_name = "mod_alert"

        mod = self.modules[mod_name]
        views = mod.build(query)

        if "headers" not in views:
            views['headers'] = ["Content-Type: text/html"]

        views['views']['modules'] = map(lambda name: (name, self.modules[name].getName()), self.module_names)
        views['views']['module'] = mod_name
        views['views']["software"] = self.config['software']
        views['views']['place'] = self.config['company']
        views['views']['title'] = self.config['title']
        views['views']['sid'] = ""

        layout = layoutManager.getLayout(views['layout'], views['views'], query)
        
        return "\n".join(views['headers']) + "\n\n" + str(layout)


if __name__ == "__main__":
    print Config()
