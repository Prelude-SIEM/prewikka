
#
# Copyright 2004 Miika Keskinen, Markus Alkio, Citadec Solutions OY
# Licensed under GPL
# 


import MySQLdb
from config import config

def getDB():
	CON = MySQLdb.Connect(user=config['dbuser'],passwd=config['dbpasswd'],db=config['database'])
	return CON, CON.cursor()
