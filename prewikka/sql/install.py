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


DROP TABLE IF EXISTS Prewikka_History_Query;
DROP TABLE IF EXISTS Prewikka_Crontab;
DROP TABLE IF EXISTS Prewikka_Session;
DROP TABLE IF EXISTS Prewikka_User_Configuration;
DROP TABLE IF EXISTS Prewikka_User_Permission;
DROP TABLE IF EXISTS Prewikka_User;


CREATE TABLE Prewikka_User (
    name VARCHAR(255) NOT NULL,
    userid VARCHAR(32) NOT NULL PRIMARY KEY
) ENGINE=InnoDB;

CREATE INDEX prewikka_user_index_name ON Prewikka_User (name);


CREATE TABLE Prewikka_User_Permission (
    userid VARCHAR(32) NOT NULL,
    permission VARCHAR(32) NOT NULL,
    PRIMARY KEY (userid, permission),
    FOREIGN KEY (userid) REFERENCES Prewikka_User(userid) ON DELETE CASCADE
) ENGINE=InnoDB;


DROP TABLE IF EXISTS Prewikka_Group_Permission;
DROP TABLE IF EXISTS Prewikka_Group;


CREATE TABLE Prewikka_Group (
    name VARCHAR(255) NOT NULL,
    groupid VARCHAR(32) NOT NULL PRIMARY KEY
) ENGINE=InnoDB;

CREATE INDEX prewikka_group_index_name ON Prewikka_Group (name);


CREATE TABLE Prewikka_Group_Permission (
    groupid VARCHAR(32) NOT NULL,
    permission VARCHAR(32) NOT NULL,
    PRIMARY KEY (groupid, permission),
    FOREIGN KEY (groupid) REFERENCES Prewikka_Group(groupid) ON DELETE CASCADE
) ENGINE=InnoDB;


CREATE TABLE Prewikka_Session (
    sessionid VARCHAR(48) NOT NULL PRIMARY KEY,
    userid VARCHAR(32) NOT NULL,
    login VARCHAR(255) NOT NULL,
    time DATETIME NOT NULL,
    FOREIGN KEY (userid) REFERENCES Prewikka_User(userid) ON DELETE CASCADE
) ENGINE=InnoDB;


CREATE TABLE Prewikka_User_Configuration (
    userid VARCHAR(255) NOT NULL,
    config TEXT NULL,
    PRIMARY KEY (userid),
    FOREIGN KEY (userid) REFERENCES Prewikka_User(userid) ON DELETE CASCADE
) ENGINE=InnoDB;


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
    error TEXT NULL,
    FOREIGN KEY (userid) REFERENCES Prewikka_User(userid) ON DELETE CASCADE
) ENGINE=InnoDB;


CREATE TABLE Prewikka_History_Query (
    userid VARCHAR(32) NOT NULL,
    formid VARCHAR(255) NOT NULL,
    query TEXT NOT NULL,
    query_hash VARCHAR(32) NOT NULL,
    timestamp DATETIME NOT NULL,
    PRIMARY KEY (userid, formid, query_hash),
    FOREIGN KEY (userid) REFERENCES Prewikka_User(userid) ON DELETE CASCADE
) ENGINE=InnoDB;
""")
