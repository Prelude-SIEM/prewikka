BEGIN;

ALTER TABLE Prewikka_User RENAME TO Prewikka_UserOld;

CREATE TABLE Prewikka_User (
        login TEXT NOT NULL PRIMARY KEY,
        lang TEXT NULL,
        password TEXT NULL,
        email TEXT NULL
);

INSERT INTO Prewikka_User(login, password, email) SELECT login, password, email FROM Prewikka_UserOld;
DROP TABLE Prewikka_UserOld;

UPDATE Prewikka_Version SET version='0.9.11';

COMMIT;

