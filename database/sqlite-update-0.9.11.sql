UPDATE Prewikka_Version SET version='0.9.11';
ALTER TABLE Prewikka_User ADD COLUMN lang VARCHAR(10) NULL;

BEGIN;

ALTER TABLE Prewikka_User RENAME TO Prewikka_UserOld;

CREATE TABLE Prewikka_User (
        login TEXT NOT NULL PRIMARY KEY,
        lang TEXT NULL,
        password TEXT NULL,
        email TEXT NULL
);

INSERT INTO Prewikka_User SELECT * FROM Prewikka_UserOld;
DROP TABLE Prewikka_UserOld;

COMMIT;

