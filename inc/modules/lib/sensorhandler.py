
#
# Copyright 2004 Miika Keskinen, Markus Alkio, Citadec Solutions OY
# Licensed under GPL
# 

from database import getDB
import time

class sensorhandler:
    """
    sensorhandler is the one who is responsible with 
    sensor management, registering and such.
    Possibly new sensors could be registered via this?
    """
    def __init__(self):
        self.__DB, self.__db = getDB()

    def getSensors(self):
        """
        returns a list of sensors
        """
        self.__db.execute("""
        SELECT DISTINCT
            a.analyzerid, 
            a.sname, 
            a.notes,
            b.gname, 
            c.model, 
            c.version,
            c.osversion
        FROM 
            Frontend_Sensor a left join Frontend_Group b USING(gid), Prelude_Analyzer c
        WHERE
            c.analyzerid=a.analyzerid
        LIMIT 30
        """)
        results = self.__db.fetchall()
        output = []
        for result in results:
            output.append({
                    "analyzerid":result[0],
                    "sensorname":result[1],
                    "notes":result[2],
                    "group":result[3],
                    "model":result[4],
                    "version":result[5],
                    "osversion":result[6]})
        return output

    def getSensor(self):
        """
        returns a list of unregistered sensors
        """
        self.__db.execute("""
                SELECT DISTINCT 
                        a.analyzerid,
                        a.model,
                        a.version,
                        a.osversion
                FROM 
                        Prelude_Analyzer a left join Frontend_Sensor b USING(analyzerid)
                WHERE
                        b.sname is NULL
                """)
        results = self.__db.fetchall()
        output = []
        for result in results:
            output.append({
                    "analyzerid":result[0],
                    "model":result[1],
                    "version":result[2],
                    "osversion":result[3]})
        return output

    def addsensor(self, data):
        """
        registers new sensor
        """
        self.__db.execute("INSERT INTO Frontend_Sensor VALUES('%(group)s','%(name)s','%(notes)s','%(sensorid)s')" % data)

    def delsensor(self, data):
        """
        unregister sensor
        """
        self.__db.execute("DELETE FROM Frontend_Sensor WHERE analyzerid='%s'" % data['sensorid'])

    def closeDB(self):
        self.__DB.close()

