
#
# Copyright 2004 Miika Keskinen, Markus Alkio, Citadec Solutions OY
# Licensed under GPL
# 


from PyTpl import PyTpl
import util

class reports:
    __r = ""
    def __init__(self, r, data):
        self.__r = r == "main" and "templates" or r
        self.tpl = None
        self.__data = data
        self.__active = self.__r

    def request(self):
        if self.__r == "templates" or self.__r == "main":
            self.tpl = PyTpl("tpl/templates.tpl")
            self.getTemplates()
        if self.__r == "history":
            self.tpl = PyTpl("tpl/reportHistory.tpl")
            
        self.tpl.parse(True)

    def get(self):
        self.request()
        view = {
            "layout":"normal", 
            "views":{
                "main":self.tpl.get(),
                "active":self.__active, 
                "sid":self.__data['sid'],
                "pages":[
                    ("templates","Templates"),
                    ("history", "Report history"),
                    ]
                }
            }
        return view
    
    def getTemplates(self):
        pass

