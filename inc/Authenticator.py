#
# Copyright 2004 Miika Keskinen, Markus Alkio, Citadec Solutions OY
# Licensed under GPL
# 

import database
import util

class Authenticator:
    def __init__(self):
        self.db, self.cur = database.getDB()

    def __del__(self):
        self.db.close()

    def authenticate(self, username, password):
        username = util.webify(username)
        password = util.webify(password)
        self.cur.execute("SELECT userid FROM Frontend_Users WHERE uname='%s' AND passwd='%s'" % (username, password))
        result = self.cur.fetchone()[0]
        self.userid = result
        return result

    def getUserId(self):
        return self.userid
