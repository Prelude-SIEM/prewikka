from database import getDB
from string import strip
import time
import re
from PyTpl import PyTpl


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
        self.__data = []
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

            self.__data.append({"alert_ident": result[0],
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
        tpl = PyTpl("tpl/alerts.tpl")
        i = 0
        colors = ["#ffffff", "#eeeeee"]
        for param in self.__data:
            for var in param: 
                tpl['alert'].setVar(var.upper(), param[var])
            tpl['alert'].COLOR = colors[i%2]
            tpl['alert'].parse()
            i += 1
        return str(tpl)



class SectionAlertView:
    def __init__(self, query):
        db, DB = getDB()
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
        """ % query.input()["ident"])
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
            """ % (alert_ident))
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
            parent_ident='%s'"""%(alert_ident))

        results = db.fetchall()
        output = []
        for result in results:
            output.append({"type":result[0],"data":result[1]})
        
        self.__data = {"header": output2, "data": output}

    def __str__(self):
        tpl = PyTpl("tpl/viewalert.tpl")

        i = 0
        colors = ["#ffffff", "#eeeeee"]

        for var in self.__data["header"]:
            tpl.setVar(var.upper(), util.webify(self.__data["header"][var]))

        for var in params["data"]:
            for value in var:
                tpl['alert'].setVar(value.upper(), util.webify(var[value].strip()))

            self.tpl['alert'].COLOR = colors[i%2]
            self.tpl['alert'].parse()
            i += 1

        return str(tpl)


def load(module):
    module.registerSection("Alert list", SectionAlertList, default=True)
    module.registerSection("Alert view", SectionAlertView, parent="Alert list")
