
#
# Copyright 2004 Miika Keskinen, Markus Alkio, Citadec Solutions OY
# Licensed under GPL
# 


import md5
import time
import random
import database
import pickle
import base64
from log import log

class sessionError(Exception): pass

class session:
    def __init__(self, sid=""):
        self.db, self.cur = database.getDB()
        self.cleanup()
        if sid == "":
            self.__sid = md5.new(str(time.time() * random.random())).hexdigest()
            self.data = {}
        else:
            self.data = self.recv(sid)
            self.__sid = sid

    def __del__(self):
        self.db.close()
        
    def getAll(self):
        return self.data

    def cleanup(self):
        self.cur.execute("DELETE FROM Frontend_sessions WHERE timestamp < '%s'" % str(int(time.time()) - 3600)) 

    def getSid(self):
        return self.__sid

    def get(self, key):
        return self.data[key]

    def __getitem__(self, key):
        return self.get(key)
    
    def __setitem__(self, key, data):
        self.set(key, data)
    
    def set(self, key, data):
        self.data[key] = data

    def storeSession(self):
        data = base64.encodestring(pickle.dumps(self.data))
        self.cur.execute("INSERT INTO Frontend_sessions VALUES('%s','%s','%d')" % (self.__sid, data, int(time.time())))
    
    def recv(self, sid):
        self.cur.execute("SELECT data FROM Frontend_sessions WHERE sid='%s'" % sid)
        data = self.cur.fetchone()[0]
        data = pickle.loads(base64.decodestring(data))
        return data
    
