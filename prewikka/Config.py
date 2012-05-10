# Copyright (C) 2004-2012 CS-SI. All Rights Reserved.
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
# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING.  If not, write to
# the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.


from prewikka import MyConfigParser, siteconfig


class Config:
    def __init__(self, filename=None):
        if not filename:
            filename=siteconfig.conf_dir + "/prewikka.conf"
            
        self.general = MyConfigParser.ConfigParserSection("general")
        self.interface = MyConfigParser.ConfigParserSection("interface")
        self.host_commands = MyConfigParser.ConfigParserSection("host_commands")
        self.database = MyConfigParser.ConfigParserSection("database")
        self.idmef_database = MyConfigParser.ConfigParserSection("idmef_database")
        self.admin = None
        self.auth = None
        self.logs = [ ]
        self.views = [ ]

        file = MyConfigParser.MyConfigParser(filename)
        file.load()

        for section in file.getSections():            
            if " " in section.name:
                type, name = section.name.split(" ")
                section.name = name
                handler = "_set_" + type
                if hasattr(self, handler):
                    getattr(self, handler)(section)
            else:
                setattr(self, section.name, section)

    def _set_general(self, general):
        self.general = general

    def _set_interface(self, interface):
        self.interface = interface

    def _set_database(self, database):
        self.database = database
        
    def _set_idmef_database(self, idmef_database):
        self.idmef_database = idmef_database

    def _set_admin(self, admin):
        self.admin = admin

    def _set_auth(self, auth):
        self.auth = auth

    def _set_log(self, log):
        self.logs.append({log.name: log})

    def _set_view(self, view):
        self.views.append(view)
