#!/usr/bin/env python

#
# Copyright 2004 Miika Keskinen, Markus Alkio, Citadec Solutions OY
# Licensed under GPL
# 

import sys, os

import copy
import cgi

from prewikka import Core


class Request(Core.Request):
    def __init__(self):
        Core.Request.__init__(self)
        self._arguments = { }
        fs = cgi.FieldStorage()
        for key in fs.keys():
            self._arguments[key] = fs.getvalue(key)
    
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

    def getArguments(self):
        return copy.copy(self._arguments)



class Response(Core.Response):
    def write(self, content):
        sys.stdout.write(content)



request = Request()
response = Response()

core = Core.Core()
core.process(request, response)
