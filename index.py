#!/usr/bin/python

# Copyright (C) 2004,2005 PreludeIDS Technologies. All Rights Reserved.
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


import sys, os

import copy
import cgi

from prewikka import Core, Request


class CGIRequest(Request.Request):
    def init(self):
        Request.Request.init(self)
        fs = cgi.FieldStorage()
        for key in fs.keys():
            self.arguments[key] = fs.getvalue(key)
        for key in fs.headers.keys():
            self.input_headers[key] = fs.headers.get(key)
        
    def read(self, *args):
        return apply(sys.stdin.read, args)
    
    def write(self, data):
        sys.stdout.write(data)
        
    def getQueryString(self):
        return os.getenv("QUERY_STRING").strip()

    def getClientAddr(self):
        return os.getenv("REMOTE_ADDR").strip()

    def getClientPort(self):
        return int(os.getenv("REMOTE_PORT").strip())

    def getServerAddr(self):
        return os.getenv("SExRVER_ADDR").strip()

    def getServerPort(self):
        return os.getenv("SERVER_PORT").strip()

    def getUserAgent(self):
        return os.getenv("USER_AGENT").strip()

    def getMethod(self):
        return os.getenv("REQUEST_METHOD").strip()

    def getURI(self):
        return os.getenv("REQUEST_URI").strip()
    
    def getCookieString(self):
        return os.getenv("HTTP_COOKIE").strip()

    def getReferer(self):
        return os.getenv("HTTP_REFERER", "").strip()



request = CGIRequest()
request.init()

core = Core.Core()
core.process(request)
