import sys
from database import getDB
import prelude
import preludedb
import time
import util
import re
from templates.modules.mod_alert import AlertList, AlertSummary, AlertDetails


class SectionAlertList:
    def __init__(self, query):
        self.query = query

    def __str__(self):
        display = AlertList.AlertList()
        preludedb.PreludeDB.init()
        db = preludedb.PreludeDB(name="test")
        db.connect()
        criteria = prelude.IDMEFCriteria("alert.detect_time >= 'month:current-1'")
        results = db.get_alert_ident_list(criteria)
        if results:
            for analyzerid, alert_ident in results:
                alert = db.get_alert(analyzerid, alert_ident)
                display.addAlert(alert)
        return str(display)



class SectionAlert:
    def __init__(self, query):
        preludedb.PreludeDB.init()
        db = preludedb.PreludeDB(name="test")
        db.connect()
        self._alert = db.get_alert(query["analyzerid"], query["alert_ident"])
        


class SectionAlertSummary(SectionAlert):
    def __str__(self):
        return str(AlertSummary.AlertSummary(self._alert))



class SectionAlertDetails(SectionAlert):
    def __str__(self):
        return str(AlertDetails.AlertDetails(self._alert))



def load(module):
    module.setName("Alert")
    module.registerSection("Alert list", SectionAlertList, default=True)
    module.registerSection("Alert summary", SectionAlertSummary, parent="Alert list")
    module.registerSection("Alert details", SectionAlertDetails, parent="Alert list")
