
#
# Copyright 2004 Miika Keskinen, Markus Alkio, Citadec Solutions OY
# Licensed under GPL
# 

"""

Main module

"""

from modules import loader
from layout import layoutManager
import config
import Session

class UserNotAuthenticated(Exception):
    pass

class Main:
    """
    requesthandler
    """
    def __init__(self, fieldstorage):
        self.__fieldstorage = fieldstorage

        self.__mod = "mod" in self.__fieldstorage and \
                self.__fieldstorage['mod'] or "login"
        self.__request = "r" in self.__fieldstorage and \
                self.__fieldstorage['r'] or "main"

        self.__sid = ""
        
        if not self.__request in self.__fieldstorage:
            self.__fieldstorage[self.__request] = {}

        try:
            ses = Session.session(self.__fieldstorage['sid'])
            if not ses['authenticated']: 
                raise UserNotAuthenticated(), "current user is not authenticated yet"

            self.__fieldstorage[self.__request]['session'] = ses.getAll()
            self.__fieldstorage[self.__request]['sid'] = self.__fieldstorage['sid']
        except (Exception), message:
            self.__mod = "login"

        mod = loader.load(self.__mod)(self.__request, self.__fieldstorage[self.__request])

        self.views = mod.get()
        
        if "headers" not in self.views:
            self.views['headers'] = ["Content-Type: text/html"]
        
        self.views['views']['modules'] = config.config['modules']
        self.views['views']['module'] = self.__mod
        self.views['views']["software"] = config.config['software']
        self.views['views']['place'] = config.config['company']
        self.views['views']['title'] = config.config['title']
        
        if "sid" in self.__fieldstorage: 
            self.views['views']['sid'] = self.__fieldstorage['sid']
        
        self.L = layoutManager.getLayout( self.views['layout'], \
                self.views['views'])

    def get(self):
        """
        returns actual data.
        """
        return "\n".join(self.views['headers']) + "\n\n" + self.L.getPage()

