UPDATE Prewikka_Version SET version="0.9.1";

DROP TABLE IF EXISTS Prewikka_User_Configuration;
CREATE TABLE Prewikka_User_Configuration (
	login VARCHAR(32) NOT NULL,
	view  VARCHAR(32) NOT NULL,
	name  VARCHAR(255) NOT NULL,
	value VARCHAR(255) NULL
);

CREATE INDEX prewikka_user_configuration_index ON Prewikka_User_Configuration (name, login, view);
