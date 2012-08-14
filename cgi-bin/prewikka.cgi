#!/usr/bin/env python

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
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import sys, os
import copy
import cgi

from prewikka import Core, Request, Error, localization


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
        return os.environ.get("REQUEST_URI", "").strip()

    def getClientAddr(self):
        return os.environ.get("REMOTE_ADDR", "").strip()

    def getClientPort(self):
        return int(os.environ.get("REMOTE_PORT", "0").strip())

    def getServerAddr(self):
        return os.environ.get("SERVER_ADDR", "").strip()

    def getServerPort(self):
        return os.environ.get("SERVER_PORT", "").strip()

    def getUserAgent(self):
        return os.environ.get("USER_AGENT", "").strip()

    def getMethod(self):
        return os.environ.get("REQUEST_METHOD", "").strip()

    def getURI(self):
        return os.environ.get("REQUEST_URI", "").strip()
    
    def getCookieString(self):
        return os.environ.get("HTTP_COOKIE", "").strip()

    def getReferer(self):
        return os.environ.get("HTTP_REFERER", "").strip()

    def getRemoteUser(self):
        user = os.environ.get("REMOTE_USER", None)
        if user:
            user.strip()
            
        return user


request = CGIRequest()
request.init()

core = Core.get_core_from_config(os.environ.get("PREWIKKA_CONFIG", None), threaded=False)
core.process(request)
