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
import os, os.path

from prewikka import Config, Log, Prelude, Interface


class Request:
    def __init__(self):
        pass

    def getQueryString(self):
        pass

    def getClientAddr(self):
        pass

    def getClientPort(self):
        pass

    def getServerAddr(self):
        pass

    def getServerPort(self):
        pass

    def getUserAgent(self):
        pass

    def getMethod(self):
        pass

    def getURI(self):
        pass

    def getArguments(self):
        pass



class Response:
    pass



class Core:
    def __init__(self):
        self.content_modules = { }
        self._content_module_names = [ ]
        self._config = Config.Config()
        self.interface = Interface.Interface(self, self._config.get("interface", { }))
        self.log = Log.Log()
        self.prelude = Prelude.Prelude(self._config["prelude"])
        self._initModules()

    def _initModules(self):
        base_dir = "prewikka/modules/"
        files = os.listdir(base_dir)
        for file in files:
            if os.path.isdir(base_dir + file):
                name = os.path.basename(file)
                if os.path.isfile(base_dir + file + "/" + name + ".py"):
                    module = __import__(base_dir + file + "/" + name)
                    module.load(self, self._config.modules.get(name, {}))
        
    def process(self, request, response):
        args = request.getArguments()
        if args.has_key("action"):
            action = args["action"]
            del args["action"]
        else:
            action = None
        
        view = self.interface.process(action, args, request)
        response.write(view)
