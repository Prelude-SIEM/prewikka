#!/bin/sh
sed \
	-e 's/#.*//' \
	-e '/^DROP /d' \
    	-e 's/[a-zA-Z]*INT /INTEGER /' \
	-e 's/UNSIGNED //' \
	-e 's/ENUM([^)]\+)/TEXT/' \
	-e 's/VARCHAR([^)]\+)/TEXT/' \
	-e 's/AUTO_INCREMENT/AUTOINCREMENT/' \
	-e 's/TYPE=InnoDB//' \
	-e 's/([0-9]\+)//g' \
	$1 
