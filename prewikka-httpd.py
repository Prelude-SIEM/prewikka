#!/usr/bin/python

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
import time

import cgi
import urllib
import mimetypes
import shutil

import SocketServer
import BaseHTTPServer

from prewikka import Core, Request


class PrewikkaServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    def __init__(self, *args, **kwargs):
        apply(BaseHTTPServer.HTTPServer.__init__, (self,) + args, kwargs)
        self.core = Core.Core()
        


class PrewikkaRequestHandler(Request.Request, BaseHTTPServer.BaseHTTPRequestHandler):
    def getCookieString(self):
        return self.headers.get("Cookie")

    def getQueryString(self):
        return self.path

    def getReferer(self):
        try:
            return self.input_headers["referer"]
        except KeyError:
            return ""

    def write(self, data):
        self.wfile.write(data)
    
    def read(self, *args, **kwargs):
        return apply(self.rfile.read, args, kwargs)
    
    def log_request(self, *args, **kwargs):
        pass

    def log_error(self, *args, **kwargs):
        pass

    def _processDynamic(self, arguments):
        self.input_headers.update(self.headers)
        
        for name, value in arguments.items():
            self.arguments[name] = (len(value) == 1) and value[0] or value
            
        self.server.core.process(self)
        
    def sendResponse(self):
        self.send_response(200)
        Request.Request.sendResponse(self)

    def _processStatic(self):
        filename = os.path.abspath(urllib.unquote(self.path[1:]))
        if filename.find(os.getcwd()) != 0:
            self.send_error(403, filename)
            return
        
        # the following piece of code is from tracd of the trac project
        # (http://www.edgewall.com/products/trac/)
        try:
            f = open(filename, 'r')
        except IOError:
            self.send_error(404, filename)
            return
        
        self.send_response(200)
        mtype, enc = mimetypes.guess_type(filename)
        stat = os.fstat(f.fileno())
        content_length = stat[6]
        last_modified = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(stat[8]))
        self.send_header('Content-Type', mtype)
        self.send_header('Content-Length', str(content_length))
        self.send_header('Last-Modified', last_modified)
        self.end_headers()
        shutil.copyfileobj(f, self.wfile)
        
    def do_GET(self):
        self.init()
        if self.path == "/":
            self._processDynamic({ })
        elif self.path.find("?") == 1:
            self._processDynamic(cgi.parse_qs(self.path[2:]))
        else:
            self._processStatic()

    def do_HEAD(self):
        self.do_GET()

    def do_POST(self):
        self.init()
        self._processDynamic(cgi.parse_qs(self.rfile.read(int(self.headers["Content-Length"]))))


server = PrewikkaServer(("0.0.0.0", 8000), PrewikkaRequestHandler)
server.serve_forever()
