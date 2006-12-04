# Copyright (C) 2004,2005 PreludeIDS Technologies. All Rights Reserved.
# Author: Yoann Vandoorselaere <yoann.v@prelude-ids.com>
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


import logging, logging.handlers, sys


class Log:
    def __init__(self, conf):        
        self._logger = None
        
        for logconf in conf.logs:
            logtype = logconf.keys()[0]

            config = { }
            for key in logconf[logtype].keys():
                config[key] = logconf[logtype].getOptionValue(key)

            self._logger = logging.getLogger()
            self._logger.setLevel(logging.NOTSET)
            self._logger.addHandler(self._getHandler(config, logtype))

        
    def _getHandler(self, config, logtype='syslog'):
        logtype = logtype.lower()
        level = config.get("level", "")

        if logtype == 'file':
            hdlr = logging.FileHandler(config["file"])

        elif logtype == 'nteventlog':
            hdlr = logging.handlers.NTEventLogHandler(logid, logtype='Application')

        elif logtype in ['syslog', 'unix']:
            hdlr = logging.handlers.SysLogHandler('/dev/log')

        elif logtype in ['smtp']:
            hdlr = logging.handlers.SMTPHandler(config["host"], config["from"], config["to"].split(", "), config["subject"]) 

        elif logtype in ['stderr']:
            hdlr = logging.StreamHandler(sys.stderr)

        else:
            raise "Unknown logtype specified: '%s'" % logtype

        format = 'Prewikka %(levelname)s: %(message)s'
        if logtype in ['file', 'stderr']:
            format = '%(asctime)s ' + format 

        datefmt = ''
        if logtype == 'stderr':
            datefmt = '%X'        

        level = level.upper()
        if level in ['DEBUG', 'ALL']:
            hdlr.setLevel(logging.DEBUG)
        elif level == 'INFO':
            hdlr.setLevel(logging.INFO)
        elif level == 'ERROR':
            hdlr.setLevel(logging.ERROR)
        elif level == 'CRITICAL':
            hdlr.setLevel(logging.CRITICAL)
        else:
            hdlr.setLevel(logging.WARNING)
        
        formatter = logging.Formatter(format, datefmt)
        hdlr.setFormatter(formatter)

        return hdlr


    def _getLog(self, request, login, details):
        message = "["
        
        addr = request.getClientAddr()
        message += "%s" % (addr)

        port = request.getClientPort()
        if port:
            message += ":%d" % port

        if login:
            message += " %s@" % (login)
        else:
            message += " "
            
        message += "%s]" % (request.getView())

        if details:
            message += " " + details

        return message
        
    def debug(self, message, request=None, user=None):
        if self._logger:
            self._logger.debug(self._getLog(request, user, message))

    def info(self, message, request=None, user=None):
        if self._logger:
            self._logger.info(self._getLog(request, user, message))
    
    def warning(self, message, request=None, user=None):
        if self._logger:
            self._logger.warning(self._getLog(request, user, message))

    def error(self, message, request=None, user=None):
        if self._logger:
            self._logger.error(self._getLog(request, user, message))

    def critical(self, message, request=None, user=None):
        if self._logger:
            self._logger.critical(self._getLog(request, user, message))
