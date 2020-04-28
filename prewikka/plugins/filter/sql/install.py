from __future__ import absolute_import, division, print_function, unicode_literals

from prewikka import version
from prewikka.database import SQLScript


class SQLUpdate(SQLScript):
    type = "install"
    branch = version.__branch__
    version = "0"

    def run(self):
        self.query("""
DROP TABLE IF EXISTS Prewikka_Filter;

CREATE TABLE Prewikka_Filter (
        id BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
        userid VARCHAR(32) NOT NULL,
        name VARCHAR(64) NOT NULL,
        category VARCHAR(64) NULL,
        description TEXT NULL,
        value TEXT NOT NULL,
        FOREIGN KEY (userid) REFERENCES Prewikka_User(userid) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE UNIQUE INDEX prewikka_filter_index_login_name ON Prewikka_Filter (userid, name);
""")
