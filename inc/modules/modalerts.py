
#
# Copyright 2004 Miika Keskinen, Markus Alkio, Citadec Solutions OY
# Licensed under GPL
# 


from PyTpl import PyTpl
from lib.alerthandler import alerthandler
from lib.sensorhandler import sensorhandler
import util

class alerts:
    __r = ""
    def __init__(self, r, data):
        self.__r = r
        self.tpl = None
        if self.__r == "main": 
            self.__r = "alerts"
        self.__data = data
        self.__active = self.__r

        self.__alerthandler = alerthandler()
        self.__sensorhandler = sensorhandler()

    def request(self):
        if self.__r == "filters":
            self.tpl = PyTpl("tpl/filters.tpl")
            self.getFilters()
            
        if self.__r == "alerts": 
            self.tpl = PyTpl("tpl/alerts.tpl")
            self.getAlerts()

        if self.__r =="monitoring":
            self.tpl = PyTpl("tpl/monitoring.tpl")
            self.getAlertsmonitor()

        if self.__r == "viewalert":
            self.tpl = PyTpl("tpl/viewalert.tpl")
            self.getAlert()

        self.tpl.parse(True)

    def get(self):
        self.request()
        self.__alerthandler.closeDB()
        view = {
            "layout":"normal", 
            "views":{
                "main":self.tpl.get(),
                "active":self.__active, 
                "sid":self.__data['sid'],
                "pages":[
                    ("alerts","Alerts"),
                    ("filters", "Filters")
                    ]
                }
            }
        return view

    def getAlert(self):
        params = self.__alerthandler.getAlert(self.__data["alert_ident"])
        i=0
        colors = ["#ffffff", "#eeeeee"]

        for var in params["header"]:
            self.tpl.setVar(var.upper(), util.webify(params["header"][var]))

        for var in params["data"]:
            for value in var:
                self.tpl['alert'].setVar(value.upper(), util.webify(var[value].strip()))

            self.tpl['alert'].COLOR = colors[i%2]
            i += 1
            self.tpl['alert'].parse()

    def getAlerts(self):
        self.tpl.setVar("SID", self.__data['sid'])
        params = self.__alerthandler.getAlerts()
        i = 0
        colors = ["#ffffff", "#eeeeee"]
        for param in params:
            for var in param: 
                self.tpl['alert'].setVar(var.upper(), param[var])
            self.tpl['alert'].COLOR = colors[i%2]
            self.tpl['alert'].SID = self.__data['sid']
            i += 1
            self.tpl['alert'].parse()

    def getFilters(self):
        pass

