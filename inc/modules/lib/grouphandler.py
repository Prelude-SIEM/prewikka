#
# Copyright 2004 Miika Keskinen, Markus Alkio, Citadec Solutions OY
# Licensed under GPL
# 

from database import getDB
import time

class grouphandler:
    """
    grouphandler is the one who is responsible with everytinh related 
    with groups
    """
    def __init__(self):
        self.__DB, self.__db = getDB()

    def getGroups(self):
        """
        returns a list of groups
        """
        self.__db.execute("""
        SELECT 
            gid, 
            gname, 
            notes
        FROM 
            Frontend_Group
        """)
        results = self.__db.fetchall()
        output = []
        for result in results:
            output.append({
                    "groupid":result[0],
                    "groupname":result[1],
                    "notes":result[2]})
        return output

    def getUsers(self):
        """
        returns a list of users
        """
        self.__db.execute("""
        SELECT DISTINCT
            a.userid,
            b.gname,
            a.uname,
            a.realname,
            a.email
        FROM
            Frontend_Users a LEFT JOIN Frontend_Group b USING(gid)
        ORDER BY a.realname DESC
        """)
        results = self.__db.fetchall()
        output = []
        for result in results:
            output.append({
                    "userid":result[0],
                    "gname":result[1],
                    "uname":result[2],
                    "realname":result[3],
                    "email":result[4]
                    })
        return output

    def adduser(self, data):
        """
        adds a new user
        """
        self.__db.execute("INSERT INTO Frontend_Users VALUES('0', '%(gid)s','%(uname)s','%(passwd)s','%(realname)s','%(email)s')" % data)

    def addgroup(self, data):
        """
        adds a new group
        """
        self.__db.execute("INSERT INTO Frontend_Group VALUES('%(gid)s','%(name)s','%(notes)s')" % data)

    def delgroup(self, data):
        """
        Deletes group
        """
        self.__db.execute("DELETE FROM Frontend_Group WHERE gid='%s'" % data['timestamp'])

    def deluser(self, data):
        """
        Deletes group
        """
        self.__db.execute("DELETE FROM Frontend_Users WHERE userid='%s'" % data['userid'])

    def updatevalues(self, data):
        self.__db.execute("UPDATE Frontend_Users SET realname='%s', email='%s' WHERE userid='%d'" % (data['realname'], data['email'], data['session']['userid']))

    def changepasswd(self, data):
        state = True

        self.__db.execute("SELECT passwd from Frontend_Users WHERE userid='%d'" % data['session']['userid'])
        old = self.__db.fetchone()[0]
        if old != data['old']:
            state = False
            data['OLD_ERROR'] = "Password mismatch"

        if data['new'] != data['again']:
            state = False
            data['AGAIN_ERROR'] = "Password mismatch"

        if state:
            self.__db.execute("UPDATE Frontend_Users SET passwd='%s' WHERE userid='%d'" % (data['new'], data['session']['userid']))

        return state, data

    def getUserDetails(self, userid):
        self.__db.execute("SELECT realname, email FROM Frontend_Users WHERE userid='%s'" % userid)
        realname, email = self.__db.fetchall()[0]
        return realname, email

    def closeDB(self):
        self.__DB.close()

