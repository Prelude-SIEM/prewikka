#!/usr/bin/env python

#
# Copyright 2004 Miika Keskinen, Markus Alkio, Citadec Solutions OY
# Licensed under GPL
# 

"""
Main module
"""

import cgi, sys, os

for path in "inc/", "inc/modules":
    sys.path.append(os.path.abspath(path))

from Query import Query
from Frontend import Frontend
from core import Core


class Response:
    def write(self, content):
        sys.stdout.write(content)


query = Query(cgi.FieldStorage())
response = Response()

core = Core()
core.process(query, response)
