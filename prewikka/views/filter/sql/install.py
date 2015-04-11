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
        type ENUM("alert", "heartbeat", "generic") NULL,
        name VARCHAR(64) NOT NULL,
        comment VARCHAR(255) NULL,
        formula VARCHAR(255) NOT NULL
) ENGINE=InnoDB;

CREATE UNIQUE INDEX prewikka_filter_index_login_name ON Prewikka_Filter (userid, name);


DROP TABLE IF EXISTS Prewikka_Filter_Criterion;

CREATE TABLE Prewikka_Filter_Criterion (
        id BIGINT UNSIGNED NOT NULL,
        name VARCHAR(16) NOT NULL,
        path VARCHAR(255) NOT NULL,
        operator VARCHAR(8) NULL,
        value VARCHAR(255) NULL
) ENGINE=InnoDB;

CREATE INDEX prewikka_filter_criterion_index_id ON Prewikka_Filter_Criterion (id);
""")
