import sys
import prelude
from preludedb import PreludeDB
import time
import util
import re
from templates.modules.mod_alert import AlertList, AlertSummary, AlertDetails


PRELUDE = None


class Prelude(PreludeDB):
    def __init__(self, config):
        PreludeDB.init()
        PreludeDB.__init__(self,
                           type=config.get("type", "mysql"),
                           host=config.get("host", "127.0.0.1"),
                           port=config.get("port", 0),
                           name=config.get("name", "prelude"),
                           user=config.get("user", "prelude"),
                           password=config.get("password", "prelude"))
        self.connect()



class SectionAlertList:
    def __init__(self, query):
        self.query = query

    def __str__(self):
        display = AlertList.AlertList()
        criteria = prelude.IDMEFCriteria("alert.detect_time >= 'month:current-1'")
        results = PRELUDE.get_alert_ident_list(criteria)
        if results:
            for analyzerid, alert_ident in results:
                alert = PRELUDE.get_alert(analyzerid, alert_ident)
                display.addAlert(alert)
        return str(display)



class SectionAlert:
    def __init__(self, query):
        self._alert = PRELUDE.get_alert(query["analyzerid"], query["alert_ident"])
        


class SectionAlertSummary(SectionAlert):
    def __str__(self):
        return str(AlertSummary.AlertSummary(self._alert))



class SectionAlertDetails(SectionAlert):
    def __str__(self):
        return str(AlertDetails.AlertDetails(self._alert))



def load(module, config):
    global PRELUDE
    PRELUDE = Prelude(config)
    module.setName("Alert")
    module.registerSection("Alert list", SectionAlertList, default=True)
    module.registerSection("Alert summary", SectionAlertSummary, parent="Alert list")
    module.registerSection("Alert details", SectionAlertDetails, parent="Alert list")
