import json

from prewikka.database import SQLScript


class SQLUpdate(SQLScript):
    type = "update"
    branch = "4.1"
    version = "1"

    def run(self):
        all_values = {}
        for userid, view, name, value in self.db.query("SELECT userid, view, name, value FROM Prewikka_User_Configuration"):
            all_values.setdefault(userid, {}).setdefault(view, {})[name] = json.loads(value)

        self.query("""
DROP TABLE IF EXISTS Prewikka_User_Configuration;
CREATE TABLE Prewikka_User_Configuration (
    userid VARCHAR(255) NOT NULL,
    config TEXT NULL,
    PRIMARY KEY(userid)
) ENGINE=InnoDB;
        """)

        if all_values:
            self.db.query("INSERT INTO Prewikka_User_Configuration (userid, config) "
                          "VALUES %s", [(key, json.dumps(value)) for key, value in all_values.items()])