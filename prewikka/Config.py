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


from prewikka import MyConfigParser


class Config:
    def __init__(self, filename="prewikka.conf"):
        self.prelude = None
        self.interface = None
        self.auth = None
        self.storage = None
        self.logs = [ ]
        self.contents = [ ]

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

    def _set_auth(self, auth):
        self.auth = auth

    def _set_storage(self, storage):
        self.storage = storage

    def _set_log(self, log):
        self.logs.append(log)

    def _set_content(self, content):
        self.contents.append(content)
