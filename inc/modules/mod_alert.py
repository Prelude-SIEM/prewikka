import sys
from database import getDB
import prelude
import preludedb
import time
import util
import re
from templates.modules.mod_alert import AlertList, AlertSummary


class SectionAlertList:
    def __init__(self, query):
        self.query = query

    def __str__(self):
        display = AlertList.AlertList()
        preludedb.PreludeDB.init()
        db = preludedb.PreludeDB()
        db.connect()
        criteria = prelude.IDMEFCriteria("alert.detect_time >= 'month:current-1'")
        results = db.get_alert_ident_list(criteria)
        if results:
            for analyzerid, alert_ident in results:
                alert = db.get_alert(analyzerid, alert_ident)
                display.addAlert(alert)
        return str(display)



class SectionAlertView:
    def __init__(self, query):
        self.query = query

    def __str__(self):
        preludedb.PreludeDB.init()
        db = preludedb.PreludeDB()
        db.connect()
        return str(AlertSummary.AlertSummary(db.get_alert(self.query["analyzerid"], self.query["alert_ident"])))



def load(module):
    module.setName("Alert")
    module.registerSection("Alert list", SectionAlertList, default=True)
    module.registerSection("Alert view", SectionAlertView, parent="Alert list")
