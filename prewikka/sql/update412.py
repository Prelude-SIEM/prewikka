import hashlib

from prewikka.database import SQLScript


class SQLUpdate(SQLScript):
    type = "update"
    branch = "4.1"
    version = "2"

    def run(self):
        rows = self.db.query("SELECT userid, formid, query, timestamp FROM Prewikka_History_Query")

        self.query("""
DROP TABLE IF EXISTS Prewikka_History_Query;
CREATE TABLE Prewikka_History_Query (
    userid VARCHAR(32) NOT NULL,
    formid VARCHAR(255) NOT NULL,
    query TEXT NOT NULL,
    query_hash VARCHAR(32) NOT NULL,
    timestamp DATETIME NOT NULL,
    PRIMARY KEY(userid, formid, query_hash)
) ENGINE=InnoDB;
        """)

        if rows:
            self.db.query("INSERT INTO Prewikka_History_Query (userid, formid, query, timestamp, query_hash) "
                          "VALUES %s", [list(row) + [hashlib.md5(row[2]).hexdigest()] for row in rows])