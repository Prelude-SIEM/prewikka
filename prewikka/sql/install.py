from __future__ import absolute_import, division, print_function, unicode_literals

from prewikka import version
from prewikka.database import SQLScript


class SQLUpdate(SQLScript):
    type = "install"
    branch = version.__branch__
    version = "0"

    def run(self):
        self.query("""
DROP TABLE IF EXISTS Prewikka_Module_Changed;
CREATE TABLE Prewikka_Module_Changed (
    time DATETIME NOT NULL
) ENGINE=InnoDB;

INSERT INTO Prewikka_Module_Changed (time) VALUES(current_timestamp);


DROP TABLE IF EXISTS Prewikka_Module_Registry;
CREATE TABLE Prewikka_Module_Registry (
        module VARCHAR(255) NOT NULL PRIMARY KEY,
        enabled TINYINT DEFAULT 1,
        branch VARCHAR(16) NULL,
        version VARCHAR(16) NULL
) ENGINE=InnoDB;


DROP TABLE IF EXISTS Prewikka_Session;
CREATE TABLE Prewikka_Session (
    sessionid VARCHAR(48) NOT NULL PRIMARY KEY,
    userid VARCHAR(32) NOT NULL,
    login VARCHAR(255) NOT NULL,
    time DATETIME NOT NULL
) ENGINE=InnoDB;


DROP TABLE IF EXISTS Prewikka_User_Configuration;
CREATE TABLE Prewikka_User_Configuration (
    userid VARCHAR(255) NOT NULL,
    view VARCHAR(32) NULL,
    name VARCHAR(255) NOT NULL,
    value VARCHAR(255) NULL,
    PRIMARY KEY(userid, view, name)
) ENGINE=InnoDB;

DROP TABLE IF EXISTS Prewikka_Crontab;
CREATE TABLE Prewikka_Crontab (
    id BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    userid VARCHAR(32) NULL,
    schedule VARCHAR(32) NULL,
    ext_type VARCHAR(255) NULL,
    ext_id INTEGER NULL,
    base DATETIME NOT NULL,
    enabled TINYINT DEFAULT 1,
    runcnt  INTEGER DEFAULT 0,
    error TEXT NULL
) ENGINE=InnoDB;
""")
