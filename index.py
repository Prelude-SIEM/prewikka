#!/usr/bin/env python

#
# Copyright 2004 Miika Keskinen, Markus Alkio, Citadec Solutions OY
# Licensed under GPL
# 

"""
Main module
"""

import cgi, sys, os 
sys.path.append(os.path.abspath("inc"))

from main import Main
from OwnFS import OwnFS

print (Main(OwnFS(cgi.FieldStorage()).get()).get())

