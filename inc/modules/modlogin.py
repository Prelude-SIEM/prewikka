
#
# Copyright 2004 Miika Keskinen, Markus Alkio, Citadec Solutions OY
# Licensed under GPL
# 

import Session
from Authenticator import Authenticator

class login:
    __r = ""
    def __init__(self, r, data):
        self.__r = r
        self.__data = data
        self.__sid = ""
        ses = Session.session()
        try:	
            self.__uname = self.__data['username']
            self.__pwd = self.__data['password']
            self.auth = Authenticator()
            if self.auth.authenticate(self.__uname, self.__pwd):
                self.__sid = ses.getSid()
                ses['authenticated'] = True
                ses['userid']=self.auth.getUserId()
                ses['username']=self.__uname
                ses['password']=self.__pwd
                ses.storeSession()
        except (Exception), message:
            pass


    def get(self):
        view = {"views":{"main":"LOGIN"}}
        if self.__sid != "":
            view['headers'] = ["Location:index.py?mod=alerts&amp;sid=%s" % self.__sid]
            view['layout']='normal'
            view['views']['sid']=self.__sid
        else:
            view['layout']='login'
        return view


