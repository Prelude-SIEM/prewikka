from database import getDB
import time
import util
import re
from templates.modules.mod_alert import AlertList, AlertDetails

class SectionAlertList:
    def __init__(self, query):
        """
        returns a list of maxximum 30 alerts in last 24 hours ordered by time
        """
        DB, db = getDB()
        a = time.localtime(int(time.time())-24*60*60)
        ti = "%d-%d-%d-%d-%d" % (a[0],a[1],a[2],a[3],a[4])
        count = db.execute("""
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
        results = db.fetchall()
        self.__alerts = []
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
            db.execute(query)
            _ipdata = db.fetchall()
            rep  = re.compile(r"\s*([0-9]*[.][0-9]*[.][0-9]*[.][0-9]*)\s*->\s*([0-9]*[.][0-9]*[.][0-9]*[.][0-9]*).*")
            for ident, data in _ipdata:
                src, dst = rep.match(data).groups()
                ipdata[ident] = (src, dst)

        for result in results:
            src, dst = "- HIDS -","- HIDS -"
            if result[0] in ipdata:
                src = ipdata[result[0]][0]
                dst = ipdata[result[0]][1]

            self.__alerts.append({"alert_ident": result[0],
                                  "description": result[1],
                                  "severity": result[2],
                                  "type": result[3],
                                  "time": result[4],
                                  "url": result[5],
                                  "sip": src,
                                  "dip": dst,
                                  "sensorid": result[6]})

        DB.close()
        
    def __str__(self):
        alert_list = AlertList.AlertList()
        for alert in self.__alerts:
            alert_list.addAlert(alert["alert_ident"], alert["time"], alert["description"],
                                alert["url"], alert["sip"], alert["dip"],
                                alert["sensorid"], alert["severity"], alert["type"])
        return str(alert_list)



class SectionAlertView:
    def __init__(self, query):
        DB, db = getDB()
        """
        return alert details by given alert_ident
        """
        db.execute("""
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
        """ % query["alert_ident"])
        result = db.fetchall()[0]
        sname = result[6]
        try:
            db.execute("""
            SELECT
                sname
            FROM
                Frontend_Sensor
            WHERE
                analyzerid='%s'
            """ % (result[6]))
            sname = db.fetchone()[0]

        except (Exception), e:
            pass
        src, dst = "This alert is from HIDS","This alert is from HIDS"
        try:
            db.execute("""
            SELECT
                data
            FROM
                Prelude_AdditionalData
            WHERE
                parent_ident='%s' AND
                meaning="Ip header"
            """ % query["alert_ident"])
            data = db.fetchone()[0]
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
        db.execute("""
        SELECT 
            meaning,
            data
        FROM 
            Prelude_AdditionalData 
        WHERE 
            parent_ident='%s'""" % query["alert_ident"])

        results = db.fetchall()
        output = []
        for result in results:
            output.append((result[0], result[1]))
        
        self.__alert = {"header": output2, "data": output}

    def __str__(self):
        alert = AlertDetails.AlertDetails()
        alert.setTime(self.__alert["header"]["time"])
        alert.setDescription(self.__alert["header"]["description"], self.__alert["header"]["url"])
        alert.setSourceIP(self.__alert["header"]["sip"])
        alert.setDestinationIP(self.__alert["header"]["dip"])
        alert.setSensorID(self.__alert["header"]["sensorid"])
        alert.setSeverity(self.__alert["header"]["severity"])
        alert.setType(self.__alert["header"]["type"])

        for type, data in self.__alert["data"]:
            alert.setData(type, util.webify(data))

        return str(alert)



def load(module):
    module.registerSection("Alert list", SectionAlertList, default=True)
    module.registerSection("Alert view", SectionAlertView, parent="Alert list")
