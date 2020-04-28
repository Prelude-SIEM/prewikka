from __future__ import absolute_import, division, print_function, unicode_literals

from prewikka.database import SQLScript

from prewikka import version


class SQLUpdate(SQLScript):
    type = "install"
    branch = version.__branch__
    version = "0"

    def run(self):
        self.query("""
DROP TABLE IF EXISTS Prewikka_User_Group;

CREATE TABLE Prewikka_User_Group (
        groupid VARCHAR(32) NOT NULL,
        userid VARCHAR(32) NOT NULL,
        PRIMARY KEY (groupid, userid),
        FOREIGN KEY (groupid) REFERENCES Prewikka_Group(groupid) ON DELETE CASCADE,
        FOREIGN KEY (userid) REFERENCES Prewikka_User(userid) ON DELETE CASCADE
) ENGINE=InnoDB;
""")
