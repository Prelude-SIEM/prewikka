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

import copy

from prewikka import Config, Log, Prelude, Action, Interface


class Core:
    def __init__(self):
        self.content_modules = { }
        self._content_module_names = [ ]
        self._config = Config.Config()
        self.log = Log.Log()
        self.action_engine = Action.ActionEngine(self.log)
        self.interface = Interface.Interface(self, self._config.get("interface", { }))
        self.prelude = Prelude.Prelude(self._config["prelude"])
        self.auth = None
        self._initModules()
        
    def shutdown(self):
        # Core references objects that themself reference Core, those circular
        # references mean that garbage collector won't destroy those objects.
        # Thus, code that use Core must call the shutdown method (that remove
        # Core references) so that cleanup code (__del__ object methods) will be called
        self.content_modules = None
        self._content_module_names = None
        self._config = None
        self.interface = None
        self.log = None
        self.prelude = None
        self.auth = None
        
    def registerAuth(self, auth):
        self.auth = auth
        
    def _initModules(self):
        base_dir = "prewikka/modules/"
        for mod_name in self._config.getModuleNames():
            try:
                file = base_dir + mod_name + "/" + mod_name
                module = __import__(file)
                module.load(self, self._config.modules.get(mod_name, { }))
            except ImportError:
                print >> sys.stderr, "cannot load module named %s (%s)" % (mod_name, file)
                raise
        
    def process(self, request):
        self.log(Log.EVENT_QUERY, request, request.getQueryString())
        
        request.log = self.log
        request.prelude = self.prelude
        request.action_engine = self.action_engine

        arguments = copy.copy(request.arguments)
        if arguments.has_key("action"):
            action_name = arguments["action"]
            del arguments["action"]
        else:
            action_name = None

        registered_action = self.action_engine.getRegisteredActionFromName(action_name)

        if self.auth:
            if registered_action == self.action_engine.getLoginAction():
                view = self.action_engine.process(registered_action, arguments, request)
            else:
                view = self.auth.check(request)
                if not view:
                    view = self.action_engine.process(registered_action, arguments, request)
        else:
            view = self.action_engine.process(registered_action, arguments, request)

        interface = self.interface
        
        view.setInfoTitle(interface.getTitle())
        view.setInfoSoftware(interface.getSoftware())
        view.setInfoPlace(interface.getPlace())
        view.addSections(interface.getSections())
        view.setConfiguration(interface.getConfiguration())
        view.addQuickAccessors(interface.getQuickAccessors())
        
        request.content = str(view)
        request.sendResponse()
