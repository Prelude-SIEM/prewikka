
#
# Copyright 2004 Miika Keskinen, Markus Alkio, Citadec Solutions OY
# Licensed under GPL
# 


import modlogin
import modreports
import modalerts
import modsensors
import modgroups

def load(modname):
    modules = {
        "login":modlogin.login,
        "alerts":modalerts.alerts,
        "sensors":modsensors.sensors,
        "reports":modreports.reports,
        "groups":modgroups.groups
    }
    return modules[modname]

