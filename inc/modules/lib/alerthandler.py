#
# Copyright 2004 Miika Keskinen, Markus Alkio, Citadec Solutions OY
# Licensed under GPL
# 


from database import getDB
from string import strip
import time
import re

class alerthandler:
    """
    alerthandler is the one who is fidling with alertlistings & details 
    """
    def __init__(self):
        self.__DB, self.__db = getDB()

    def getAlerts(self):
        """
        returns a list of maxximum 30 alerts in last 24 hours ordered by time
        """
        a = time.localtime(int(time.time())-24*60*60)
        ti = "%d-%d-%d-%d-%d" % (a[0],a[1],a[2],a[3],a[4])
        count = self.__db.execute("""
        SELECT 
            a.alert_ident, 
            b.name, 
            a.severity, 
            a.type, 
            c.time,
            b.url,
            f.sname,
            e.analyzerid
        FROM 
            Prelude_Impact a, 
            Prelude_Classification b,
            Prelude_DetectTime c,
            Prelude_Analyzer e left join Frontend_Sensor f USING(analyzerid)
        WHERE
            c.time > '%s' AND
            a.alert_ident=b.alert_ident AND 
            a.alert_ident=c.alert_ident AND 
            a.alert_ident=e.parent_ident
        ORDER BY c.time DESC
        LIMIT 30
        """ % ti)
        results = self.__db.fetchall()
        output = []
        query = "SELECT parent_ident, data FROM Prelude_AdditionalData WHERE meaning='Ip header' AND parent_ident in ("
        first = True
        for result in results:
            if not first:
                query += ",'%s'"%(result[0])
            else:
                first = False
                query += "'%s' "%(result[0])
        query += ")"
        ipdata = {}
        
        if count:
            self.__db.execute(query)
            _ipdata = self.__db.fetchall()
            rep  = re.compile(r"\s*([0-9]*[.][0-9]*[.][0-9]*[.][0-9]*)\s*->\s*([0-9]*[.][0-9]*[.][0-9]*[.][0-9]*).*")
            for ident, data in _ipdata:
                src, dst = rep.match(data).groups()
                ipdata[ident] = (src, dst)

        for result in results:
            src, dst = "- HIDS -","- HIDS -"
            if result[0] in ipdata:
                src = ipdata[result[0]][0]
                dst = ipdata[result[0]][1]

            output.append({"alert_ident":result[0],"description":result[1],"severity":result[2],"type":result[3],"time":result[4],"url":result[5],"sip":src,"dip":dst,"sensorid":result[6]})
        return output


    def getAlert(self, alert_ident):
        """
        return alert details by given alert_ident
        """
        self.__db.execute("""
        SELECT 
            b.name, 
            a.severity, 
            a.type, 
            c.time,
            b.url,
            e.analyzerid,
            e.analyzerid
        FROM 
            Prelude_Impact a, 
            Prelude_Classification b,
            Prelude_DetectTime c,
            Prelude_Analyzer e
        WHERE
            a.alert_ident='%s' AND
            a.alert_ident=b.alert_ident AND 
            a.alert_ident=c.alert_ident AND 
            a.alert_ident=e.parent_ident
        ORDER BY c.time DESC
        """%(alert_ident))
        result = self.__db.fetchall()[0]
        sname = result[6]
        try:
            self.__db.execute("""
            SELECT
                sname
            FROM
                Frontend_Sensor
            WHERE
                analyzerid='%s'
            """ % (result[6]))
            sname = self.__db.fetchone()[0]

        except (Exception), e:
            pass
        src, dst = "This alert is from HIDS","This alert is from HIDS"
        try:
            self.__db.execute("""
            SELECT
                data
            FROM
                Prelude_AdditionalData
            WHERE
                parent_ident='%s' AND
                meaning="Ip header"
            """ % (alert_ident))
            data = self.__db.fetchone()[0]
            src, dst = re.match(r"\s*([0-9]*[.][0-9]*[.][0-9]*[.][0-9]*)\s*->\s*([0-9]*[.][0-9]*[.][0-9]*[.][0-9]*).*", data).groups()
        except:
            pass


        output2 = {
            "description":result[0],
            "severity":result[1],
            "type":result[2],
            "time":result[3],
            "url":result[4],
            "sip":src,
            "dip":dst,
            "sensorid":sname}
        self.__db.execute("""
        SELECT 
            meaning,
            data
        FROM 
            Prelude_AdditionalData 
        WHERE 
            parent_ident='%s'"""%(alert_ident))

        results = self.__db.fetchall()
        output = []
        for result in results:
            output.append({"type":result[0],"data":result[1]})
        return {"header":output2, "data":output}

    def closeDB(self):
        self.__DB.close()

