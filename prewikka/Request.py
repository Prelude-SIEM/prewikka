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


import sys
import os, os.path

import copy

import Cookie


class Request:
    def init(self):
        # all of this should be done in constructor __init__, but the way
        # BaseHTTPServer.BaseHTTPRequestHandler is designed forbid us to do so
        self.arguments = { }
        self.input_headers = { }
        self.output_headers = [ ("Content-type", "text/html"),
                                ("Pragma", "no-cache"),
                                ("Cache-control", "no-cache"),
                                ("Expires", "Fri, 01 Jan 1999 00:00:00 GMT") ]

        cookie = Cookie.SimpleCookie(self.getCookieString())
        self.input_cookie = { }
        for key, value in cookie.items():
            self.input_cookie[key] = value

        self.output_cookie = None

        self.content = None
        self.user = None
      
    def addCookie(self, param, value, expires):
    	if not self.output_cookie:
            self.output_cookie = Cookie.SimpleCookie()

    	self.output_cookie[param] = value
	self.output_cookie[param]["expires"] = expires
	
    def read(self, *args):
        pass

    def write(self, data):
        pass

    def sendHeader(self, name, value):
        self.write("%s: %s\r\n" % (name, value))

    def endHeaders(self):
        self.write("\r\n")

    def sendResponse(self):        
        for name, value in self.output_headers:
            self.sendHeader(name, value)
            
        if self.output_cookie:
            self.write(self.output_cookie.output() + "\r\n")
            
        self.endHeaders()
        
        if self.content:
            self.write(self.content)
        
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
