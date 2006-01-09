DROP TABLE IF EXISTS Prewikka_Version;

CREATE TABLE Prewikka_Version (
	version VARCHAR(255) NOT NULL
);
INSERT INTO Prewikka_Version (version) VALUES('0.9.1');



DROP TABLE IF EXISTS Prewikka_User;

CREATE TABLE Prewikka_User (
	login VARCHAR(32) NOT NULL PRIMARY KEY,
	password VARCHAR(32) NULL,
	email VARCHAR(64) NULL
);



DROP TABLE IF EXISTS Prewikka_Permission;

CREATE TABLE Prewikka_Permission (
	login VARCHAR(32) NOT NULL,
	permission VARCHAR(32) NOT NULL
);

CREATE INDEX prewikka_permission_index_login ON Prewikka_Permission (login);


DROP TABLE IF EXISTS Prewikka_Session;

CREATE TABLE Prewikka_Session (
	sessionid VARCHAR(128) NOT NULL PRIMARY KEY,
	login VARCHAR(32) NOT NULL,
	time DATETIME NOT NULL
);

CREATE INDEX prewikka_session_index_login ON Prewikka_Session (login);


DROP TABLE IF EXISTS Prewikka_Filter;

CREATE TABLE Prewikka_Filter (
	id BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
	login VARCHAR(32) NOT NULL,
	name VARCHAR(64) NOT NULL,
	comment VARCHAR(255) NULL,
	formula VARCHAR(255) NOT NULL
);

CREATE UNIQUE INDEX prewikka_filter_index_login_name ON Prewikka_Filter (login, name);


DROP TABLE IF EXISTS Prewikka_Filter_Criterion;

CREATE TABLE Prewikka_Filter_Criterion (
	id BIGINT UNSIGNED NOT NULL,
	name VARCHAR(16) NOT NULL,
	path VARCHAR(255) NOT NULL,
	operator VARCHAR(8) NULL,
	value VARCHAR(255) NULL
);

CREATE INDEX prewikka_filter_criterion_index_id ON Prewikka_Filter_Criterion (id);


DROP TABLE IF EXISTS Prewikka_User_Configuration;
CREATE TABLE Prewikka_User_Configuration (
	login VARCHAR(32) NOT NULL,
	view  VARCHAR(32) NOT NULL,
	name  VARCHAR(255) NOT NULL,
	value VARCHAR(255) NULL
);

CREATE INDEX prewikka_user_configuration_index ON Prewikka_User_Configuration (name, login, view);
