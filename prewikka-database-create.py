#!/usr/bin/python

# Copyright (C) 2004,2005 PreludeIDS Technologies. All Rights Reserved.
# Author: Nicolas Delon <nicolas.delon@prelude-ids.com>
#
# This file is part of the Prewikka program.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING.  If not, write to
# the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.


import sys
import getopt

from prewikka.Database import Database


config = {
    "type": "mysql",
    "host": "localhost",
    "port":  None,
    "user": "prewikka",
    "password": "prewikka",
    "name": "prewikka"
    }

opts, args = getopt.getopt(sys.argv[1:],
                           "t:h:o:u:p:",
                           [ "type=", "host=", "port=", "user=", "password=" ])


for opt, value in opts:
    if opt in ("-t", "--type"):
        config["type"] = value
    elif opt in ("-h", "--host"):
        config["host"] = value
    elif opt in ("-o", "--port"):
        config["port"] = value
    elif opt in ("-u", "--user"):
        config["user"] = value
    elif opt in ("-p", "--password"):
        config["password"] = value


if len(args) > 0:
    config["name"] = args[0]


db = Database(config)

content = open(config["type"] + ".sql").read()
for query in content.split(";"):
    query = query.strip()
    if len(query) > 0:
        db.query(query)
