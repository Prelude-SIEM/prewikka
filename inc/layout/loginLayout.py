#
# Copyright 2004 Miika Keskinen, Markus Alkio, Citadec Solutions OY
# Licensed under GPL
# 


from PyTpl import PyTpl
from genericLayout import genericLayout

class loginLayout(genericLayout):

    def __init__(self, views):
        self._views = views	
        tpl = PyTpl("tpl/loginLayout.tpl")

        if "message" in self._views: 
            tpl.MESSAGE = self._views["message"]
        tpl.parse(True)
        self._output = tpl.get()

    def getPage(self):
        return self._output

