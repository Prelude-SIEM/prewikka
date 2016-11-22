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

from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import logging.handlers
import os
import stat
import sys

DEBUG = logging.DEBUG
INFO = logging.INFO
ERROR = logging.ERROR
WARNING = logging.WARNING
CRITICAL = logging.CRITICAL

class Log:
    def __init__(self, conf):
        self._logger = None

        for logconfig in getattr(conf, "log", ()):

            config = { }
            for key, value in logconfig.items():
                config[key] = text_type(value)

            self._logger = logging.getLogger()
            self._logger.setLevel(logging.NOTSET)
            self._logger.addHandler(self._getHandler(config, logconfig.get_instance_name()))

    def _getSyslogHandlerAddress(self):
        for f in ("/dev/log", "/var/run/log", "/var/run/syslog"):
            try:
                if stat.S_ISSOCK(os.stat(f).st_mode):
                    return str(f)
            except:
                pass

        return ("localhost", 514)


    def _getHandler(self, config, logtype='syslog'):
        logtype = logtype.lower()
        level = config.get("level", "")

        if logtype == 'file':
            hdlr = logging.FileHandler(config["file"])

        elif logtype == 'nteventlog':
            hdlr = logging.handlers.NTEventLogHandler("Prewikka", logtype='Application')

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


    def _format_header(self):
        if not env.request.web:
            return ""

        hdr = "".join(("[", env.request.web.get_remote_addr()))

        port = env.request.web.get_remote_port()
        if port:
            hdr = ":".join((hdr, text_type(port)))

        hdr = " ".join((hdr, "%s@" % (env.request.user) if env.request.user else ""))

        flags = ""
        if env.request.web.is_xhr:
           flags = " (xhr)"
        elif env.request.web.is_stream:
           flags = " (sse)"

        return "".join((hdr, env.request.web.path, flags, "]"))


    def _get_log(self, details):
        hdr = self._format_header()
        hdr = [ hdr ] if hdr else []

        if isinstance(details, Exception):
            details = " ".join([text_type(getattr(details, "code", 500)), text_type(details)])

        return " ".join(hdr + [text_type(details)])

    def debug(self, message):
        if self._logger:
            self._logger.debug(self._get_log(message))

    def info(self, message):
        if self._logger:
            self._logger.info(self._get_log(message))

    def warning(self, message):
        if self._logger:
            self._logger.warning(self._get_log(message))

    def error(self, message):
        if self._logger:
            self._logger.error(self._get_log(message))

    def critical(self, message):
        if self._logger:
            self._logger.critical(self._get_log(message))

    def log(self, priority, message):
        return { DEBUG: self.debug,
                 INFO: self.info,
                 WARNING: self.warning,
                 ERROR: self.error,
                 CRITICAL: self.critical }[priority](message)

def getLogger(name=__name__):
        return logging.getLogger(name)
