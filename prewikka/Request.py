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


import sys
import os, os.path, time
import copy
import Cookie


class Request:
    def init(self):
        # all of this should be done in constructor __init__, but the way
        # BaseHTTPServer.BaseHTTPRequestHandler is designed forbid us to do so
        self.arguments = { }
        self.input_headers = { }
        self.output_headers = [ ("Content-type", "text/html"),
				("Last-Modified", time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())),
				("Expires", "Fri, 01 Jan 1999 00:00:00 GMT"),
				("Cache-control", "no-store, no-cache, must-revalidate"),
				("Cache-control", "post-check=0, pre-check=0"),
				("Pragma", "no-cache") ]

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

    def getView(self):
        return self.arguments.get("view", "alert_listing")
        
    def getQueryString(self):
        pass

    def getRemoteUser(self):
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
