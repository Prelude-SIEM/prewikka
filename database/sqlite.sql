
CREATE TABLE Prewikka_Version (
	version TEXT NOT NULL
);
INSERT INTO Prewikka_Version (version) VALUES('0.9.1');




CREATE TABLE Prewikka_User (
	login TEXT NOT NULL PRIMARY KEY,
	lang TEXT NULL,
	password TEXT NULL,
	email TEXT NULL
);




CREATE TABLE Prewikka_Permission (
	login TEXT NOT NULL,
	permission TEXT NOT NULL
);

CREATE INDEX prewikka_permission_index_login ON Prewikka_Permission (login);



CREATE TABLE Prewikka_Session (
	sessionid TEXT NOT NULL PRIMARY KEY,
	login TEXT NOT NULL,
	time DATETIME NOT NULL
);

CREATE INDEX prewikka_session_index_login ON Prewikka_Session (login);



CREATE TABLE Prewikka_Filter (
	id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	login TEXT NOT NULL,
	name TEXT NOT NULL,
	comment TEXT NULL,
	formula TEXT NOT NULL
);

CREATE UNIQUE INDEX prewikka_filter_index_login_name ON Prewikka_Filter (login, name);



CREATE TABLE Prewikka_Filter_Criterion (
	id INTEGER NOT NULL,
	name TEXT NOT NULL,
	path TEXT NOT NULL,
	operator TEXT NULL,
	value TEXT NULL
);

CREATE INDEX prewikka_filter_criterion_index_id ON Prewikka_Filter_Criterion (id);


CREATE TABLE Prewikka_User_Configuration (
	login TEXT NOT NULL,
	view  TEXT NOT NULL,
	name  TEXT NOT NULL,
	value TEXT NULL
);

CREATE INDEX prewikka_user_configuration_index ON Prewikka_User_Configuration (name, login, view);
