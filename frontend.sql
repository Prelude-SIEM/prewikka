CREATE TABLE Frontend_Group(
    gid INT,
    gname VARCHAR(255),
    notes TEXT
);


CREATE TABLE Frontend_Sensor(
    gid INT,
    sname VARCHAR(255),
    notes TEXT,
    analyzerid VARCHAR(255)
);

CREATE TABLE Frontend_Users(
    userid INT PRIMARY KEY AUTO_INCREMENT,
    gid INT,
    uname VARCHAR(255),
    passwd VARCHAR(255),
    realname VARCHAR(255),
    email VARCHAR(255)
);

CREATE TABLE Frontend_sessions(
    sid VARCHAR(255) PRIMARY KEY UNIQUE,
    data TEXT,
    timestamp INT UNSIGNED
);

INSERT INTO Frontend_Group VALUES(0,'default','default group');
INSERT INTO Frontend_Users VALUES(0,0,'admin', 'admin', 'admin', 'admin');

