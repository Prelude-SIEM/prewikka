
#
# Copyright 2004 Miika Keskinen, Markus Alkio, Citadec Solutions OY
# Licensed under GPL
# 

from genericLayout import genericLayout

class noneLayout(genericLayout):

	def __init__(self, views):
		self._views = views
	
	def getPage(self):
		return self._views["main"]
