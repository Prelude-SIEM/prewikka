
#
# Copyright 2004 Miika Keskinen, Markus Alkio, Citadec Solutions OY
# Licensed under GPL
# 


from PyTpl import PyTpl
from lib.sensorhandler import sensorhandler
from lib.grouphandler import grouphandler

class sensors:
    __r = ""
    def __init__(self, r, data):
        self.__r = r
        self.tpl = None
        if self.__r == "main": self.__r = "registeredsensors"
        self.__data = data
        self.__active = self.__r
        self.__sensorhandler = sensorhandler()
        self.__grouphandler = grouphandler()
        self.headers = []

    def request(self):
        if self.__r == "addsensor":
            self.__sensorhandler.addsensor(self.__data)
            self.headers = ["Location:?mod=sensors&amp;sid=%s" % self.__data['sid']]

        if self.__r == "delsensor":
            self.__sensorhandler.delsensor(self.__data)
            self.headers = ["Location:?mod=sensors&amp;sid=%s" % self.__data['sid']]

        if self.__r == "registeredsensors": 
            self.tpl = PyTpl("tpl/registeredsensors.tpl")
            self.getSensors()

        if self.__r =="unregisteredsensors":
            self.tpl = PyTpl("tpl/unregisteredsensors.tpl")
            self.getSensor()

        if self.__r == "regsensor":
            self.tpl = PyTpl("tpl/regsensor.tpl")
            self.regSensor()

        if self.__r == "heartbeat":
            self.tpl = PyTpl("tpl/heartbeat.tpl")
            self.heartbeat()

        if self.tpl:	
            self.tpl.parse(True)

    def get(self):
        self.request()
        self.__sensorhandler.closeDB()
        view = {
            "layout":"normal", 
            "views":{
                "main":self.tpl and self.tpl.get() or "",
                "pagename":"testijoo", 
                "active":self.__active, 
                "sid":self.__data['sid'],
                "pages":[
                    ("registeredsensors","Registered Sensors"),
                    ("unregisteredsensors","Unregistered Sensors"),
                    ("heartbeat","Heartbeat")]
                }
            }
        if len(self.headers):
            view['headers'] = self.headers
        return view

    def regSensor(self):
        self.tpl.SID = self.__data['sid']
        self.tpl.SENSORID = self.__data['analyzerid']
        groups = self.__grouphandler.getGroups()
        for group in groups:
            self.tpl['groups'].GID = group['groupid']
            self.tpl['groups'].GNAME = group['groupname']
            self.tpl['groups'].parse()
        
    def delSensor(self):
        self.tpl.SID = self.__data['sid']
        self.tpl.ANALYZERID = self.__data['analyzerid']

    def getSensor(self):
        self.tpl.SID = self.__data['sid']
        params = self.__sensorhandler.getSensor()
        i = 0
        colors = ["#ffffff", "#eeeeee"]
        for param in params:
            for var in param: 
                self.tpl['alert'].setVar(var.upper(), param[var])
            self.tpl['alert'].COLOR = colors[i%2]
            self.tpl['alert'].SID = self.__data['sid']
            i += 1
            self.tpl['alert'].parse()

    def getSensors(self):
        self.tpl.SID = self.__data['sid']
        params = self.__sensorhandler.getSensors()
        i = 0
        colors = ["#ffffff", "#eeeeee"]
        for param in params:
            for var in param: 
                self.tpl['alert'].setVar(var.upper(), param[var])
            self.tpl['alert'].COLOR = colors[i%2]
            self.tpl['alert'].SID = self.__data['sid']
            i += 1
            self.tpl['alert'].parse()

    def heartbeat(self):
        pass

