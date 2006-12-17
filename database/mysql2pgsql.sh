#!/bin/sh
sed \
	-e 's/#.*//' \
	-e 's/ INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT/ SERIAL PRIMARY KEY/' \
	-e 's/BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT/BIGSERIAL PRIMARY KEY/' \
	-e 's/DROP TABLE IF EXISTS/DROP TABLE/' \
	-e 's/BLOB/BYTEA/' \
        -e 's/ TINYINT UNSIGNED / INT4 /g' \
        -e 's/ TINYINT / INT2 /g' \
        -e 's/ SMALLINT UNSIGNED / INT8 /g' \
        -e 's/ SMALLINT / INT4 /g' \
	-e 's/ BIGINT UNSIGNED / NUMERIC(20) /g' \
	-e 's/ BIGINT / INT8 /g' \
	-e 's/ INT\(EGER\)\? UNSIGNED / INT8 /g' \
	-e 's/ INT\(EGER\)\? / INT4 /g' \
	-e 's/DATETIME/TIMESTAMP/' \
	-e 's/TYPE=InnoDB//' \
	-e "s/\"\([^\"]*\)\"/'\1'/g" \
	-e 's/\_parent_type ENUM(\(.*\))/_parent_type VARCHAR(1) CHECK \(_parent_type IN \(\1\)\)/' \
	-e 's/\(.*\) ENUM(\(.*\))/\1 VARCHAR(32) CHECK \(\1 IN \(\2\)\)/' \
	-e 's/\([[:lower:]_]\+\)([0-9]\+)/\1/g' \
	$1 
