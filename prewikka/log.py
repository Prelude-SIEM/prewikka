# Copyright (C) 2004-2016 CS-SI. All Rights Reserved.
# Author: Yoann Vandoorselaere <yoannv@gmail.com>
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
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import logging, logging.handlers, os, stat, sys

DEBUG = logging.DEBUG
INFO = logging.INFO
ERROR = logging.ERROR
WARNING = logging.WARNING
CRITICAL = logging.CRITICAL

class Log:
    def __init__(self, conf):
        self._logger = None

        for logtype, logvalues in getattr(conf, "log", {}).items():

            config = { }
            for key, value in logvalues.items():
                config[key] = str(value)

            self._logger = logging.getLogger()
            self._logger.setLevel(logging.NOTSET)
            self._logger.addHandler(self._getHandler(config, logtype))

    def _getSyslogHandlerAddress(self):
        for f in ("/dev/log", "/var/run/log", "/var/run/syslog"):
            try:
                if stat.S_ISSOCK(os.stat(f).st_mode):
                    return f
            except:
                pass

        return ("localhost", 514)


    def _getHandler(self, config, logtype='syslog'):
        logtype = logtype.lower()
        level = config.get("level", "")

        if logtype == 'file':
            hdlr = logging.FileHandler(config["file"])

        elif logtype == 'nteventlog':
            hdlr = logging.handlers.NTEventLogHandler(logid, logtype='Application')

        elif logtype in ['syslog', 'unix']:
            hdlr = logging.handlers.SysLogHandler(self._getSyslogHandlerAddress(), facility=logging.handlers.SysLogHandler.LOG_DAEMON)

        elif logtype in ['smtp']:
            hdlr = logging.handlers.SMTPHandler(config["host"], config["from"], config["to"].split(", "), config["subject"])

        elif logtype in ['stderr']:
            hdlr = logging.StreamHandler(sys.stderr)

        else:
            raise _("Unknown logtype specified: '%s'") % logtype

        format = 'prewikka (pid:%(process)d) %(name)s %(levelname)s: %(message)s'
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
        if not request:
            return details

        message = "[%s" % request.getClientAddr()

        port = request.getClientPort()
        if port:
            message += ":%d" % port

        if login:
            message += " %s@" % (login)
        else:
            message += " "

        flags = ""
        if request.is_xhr:
           flags += "xhr"
        elif request.is_stream:
           flags += "sse"

        if flags:
            flags = " (%s)" % flags

        message += "%s%s]" % (request.getView(), flags)

        if details:
            if isinstance(details, Exception):
                message += " %d" % getattr(details, "code", 500)

            message += " %s" % (details)

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

    def log(self, priority, message, request=None, user=None):
        return { DEBUG: self.debug,
                 INFO: self.info,
                 WARNING: self.warning,
                 ERROR: self.error,
                 CRITICAL: self.critical }[priority](message, request, user)

def getLogger(name=__name__):
        return logging.getLogger(name)

