
#
# Copyright 2004 Miika Keskinen, Markus Alkio, Citadec Solutions OY
# Licensed under GPL
# 


import pprint
import time


class log:
	def __init__(self, message):
		fil = file("/tmp/alerts.log", "a")
		fil.write("%s %s\n" % (time.strftime("%H:%M:%S"), pprint.pformat(message)))
		fil.close()
