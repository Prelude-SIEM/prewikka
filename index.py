#!/usr/bin/env python

#
# Copyright 2004 Miika Keskinen, Markus Alkio, Citadec Solutions OY
# Licensed under GPL
# 

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
        return os.getenv("QUERY_STRING")

    def getClientAddr(self):
        return os.getenv("REMOTE_ADDR")

    def getClientPort(self):
        return os.getenv("REMOTE_PORT")

    def getServerAddr(self):
        return os.getenv("SERVER_ADDR")

    def getServerPort(self):
        return os.getenv("SERVER_PORT")

    def getUserAgent(self):
        return os.getenv("USER_AGENT")

    def getMethod(self):
        return os.getenv("REQUEST_METHOD")

    def getURI(self):
        return os.getenv("REQUEST_URI")
    
    def getCookieString(self):
        return os.getenv("HTTP_COOKIE")



request = CGIRequest()
request.init()

core = Core.Core()

try:
    core.process(request)
finally:
    core.shutdown()
