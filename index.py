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

query = Query(cgi.FieldStorage())

frontend = Frontend()

print frontend.build(query)
