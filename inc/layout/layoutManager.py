#
# Copyright 2004 Miika Keskinen, Markus Alkio, Citadec Solutions OY
# Licensed under GPL
# 

from normalLayout import normalLayout
from loginLayout import loginLayout
from noneLayout import noneLayout

def getLayout(layout, data, query):
	layouts = {
			"normal":normalLayout,
			"login":loginLayout,
			"none":noneLayout
	}

	return layouts[layout](data, query)
