#!/usr/bin/env python

#
# Copyright 2004 Miika Keskinen, Markus Alkio, Citadec Solutions OY
# Licensed under GPL
# 

import sys, os

import cgi

from prewikka.Core import Core


class Response:
    def write(self, content):
        sys.stdout.write(content)


class Query(dict):
    def __init__(self, field_storage):
        dict.__init__(self)
        for key in field_storage.keys():
            self[key] = field_storage.getvalue(key)



query = Query(cgi.FieldStorage())
response = Response()

core = Core()
core.process(query, response)
