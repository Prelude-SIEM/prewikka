import prelude
from preludedb import PreludeDB


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

    def getAlertIdents(self, criteria=None):
        if criteria:
            criteria = prelude.IDMEFCriteria(criteria)
        return self.get_alert_ident_list(criteria)

    def getAlert(self, analyzerid, alert_ident):
        return self.get_alert(analyzerid, alert_ident)

    def deleteAlert(self, analyzerid, alert_ident):
        return self.delete_alert(analyzerid, alert_ident)
