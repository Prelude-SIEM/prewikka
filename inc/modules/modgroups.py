
#
# Copyright 2004 Miika Keskinen, Markus Alkio, Citadec Solutions OY
# Licensed under GPL
# 

from PyTpl import PyTpl
from lib.grouphandler import grouphandler
import time

class groups:
    __r = ""
    def __init__(self, r, data):
        self.__r = r
        self.tpl = None
        if self.__r == "main": self.__r = "registeredgroups"
        self.__data = data
        self.__active = self.__r
        self.__grouphandler = grouphandler()
        self.headers = []

    def request(self):
        if self.__r == "updatepasswd":
            success, data = self.__grouphandler.changepasswd(self.__data)
            if success:
                self.headers = ["Location:?mod=groups&amp;sid=%s&amp;r=users" % (self.__data['sid'])]
            else:
                self.tpl = PyTpl("tpl/changepasswd.tpl")
                self.getChangePasswd(data)

        if self.__r == "editPersonalSettings":
            self.tpl = PyTpl("tpl/editPersonalSettings.tpl")
            self.getPersonalSettings()
        
        if self.__r == "updatevalues":
            self.__grouphandler.updatevalues(self.__data)
            self.headers = ["Location:?mod=groups&amp;sid=%s&amp;r=users" % (self.__data['sid'])]
        
        if self.__r == "changepasswd":
            self.tpl = PyTpl("tpl/changepasswd.tpl")
            self.getChangePasswd({})
            
        if self.__r == "users":
            self.tpl = PyTpl("tpl/registeredusers.tpl")
            self.getUsers()
            
        if self.__r == "delgroup":
            self.__grouphandler.delgroup(self.__data)
            self.headers = ["Location:?mod=groups&amp;sid=%s" % self.__data['sid']]
        
        if self.__r == "deluser":
            self.__grouphandler.deluser(self.__data)
            self.headers = ["Location:?mod=groups&amp;r=users&amp;sid=%s" % self.__data['sid']]

        if self.__r =="addgroup":
            self.__grouphandler.addgroup(self.__data)
            self.headers = ["Location:?mod=groups&amp;sid=%s" % self.__data['sid']]

        if self.__r == "adduser":
            self.__grouphandler.adduser(self.__data)
            self.headers = ["Location:?mod=groups&amp;r=users&amp;sid=%s" % self.__data['sid']]

        if self.__r == "registeredgroups": 
            self.tpl = PyTpl("tpl/registeredgroups.tpl")
            self.getGroups()

        if self.__r =="addgrouppage":
            self.tpl = PyTpl("tpl/addgroup.tpl")
            self.addGrouppage()
        
        if self.__r =="adduserpage":
            self.tpl = PyTpl("tpl/adduser.tpl")
            self.addUserpage()
        
        if self.tpl:
            self.tpl.parse(True)

    def get(self):
        self.request()
        self.__grouphandler.closeDB()
        view = {
            "layout":"normal", 
            "views":{
                "main":self.tpl and self.tpl.get() or "",
                "pagename":"testijoo", 
                "active":self.__active, 
                "sid":self.__data['sid'],
                "pages":[
                    ("registeredgroups","Groups"),
                    ("addgrouppage","Add group"),
                    ("users","Users"),
                    ("adduserpage", "Add user"),
                    ("editPersonalSettings", "Personal"),]
                }
            }
        if len(self.headers):
            view['headers'] = self.headers
        return view

    def delGroup(self):
        self.tpl.SID = self.__data['sid']
        self.tpl.GROUPID = self.__data['timestamp']

    def addGrouppage(self):
        self.tpl.SID = self.__data['sid']
        gid = int(time.time())
        self.tpl.GID = gid
    
    def addUserpage(self):
        self.tpl.SID = self.__data['sid']
        groups = self.__grouphandler.getGroups()
        for group in groups:
            self.tpl['group'].GROUPID = group['groupid']
            self.tpl['group'].GROUPNAME = group['groupname']
            self.tpl['group'].parse()
        
    def addGroup(self, data):
        self.tpl.SID = self.__data['sid']
        self.tpl.GID = self.__data['gid']

    def getGroups(self):
        self.tpl.SID = self.__data['sid']
        params = self.__grouphandler.getGroups()
        i = 0
        colors = ["#ffffff", "#eeeeee"]
        for param in params:
            for var in param: 
                self.tpl['group'].setVar(var.upper(), param[var])
            self.tpl['group'].COLOR = colors[i%2]
            self.tpl['group'].SID = self.__data['sid']
            i += 1
            self.tpl['group'].parse()

    def getUsers(self):
        self.tpl.SID = self.__data['sid']
        params = self.__grouphandler.getUsers()
        i = 0
        colors = ["#ffffff", "#eeeeee"]
        for param in params:
            for var in param:
                self.tpl['user'].setVar(var.upper(), param[var])
            self.tpl['user'].COLOR = colors[i%2]
            self.tpl['user'].SID = self.__data['sid']
            i += 1
            self.tpl['user'].parse()

    def getChangePasswd(self, params):
        self.tpl.SID = self.__data['sid']
        for var in params:
            self.tpl.setVar(var.upper(), params[var])

    def getPersonalSettings(self):
        realname, email = self.__grouphandler.getUserDetails(self.__data['session']['userid'])
        self.tpl.SID = self.__data['sid']
        self.tpl.REALNAME = realname
        self.tpl.EMAIL = email
