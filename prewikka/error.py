# Copyright (C) 2004-2015 CS-SI. All Rights Reserved.
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

import sys, traceback, StringIO
from prewikka import template, log
from prewikka.templates import ErrorTemplate



class PrewikkaError(Exception):
    pass


class RedirectionError(PrewikkaError):
    def __init__(self, location, code):
        self.location = location
        self.code = code


class PrewikkaUserError(PrewikkaError):
    template = ErrorTemplate.ErrorTemplate
    name = None
    message = ""
    code = 500
    log_priority = log.ERROR

    def __init__(self, name, message, display_traceback=False, log_priority=None, log_user=None, template=None, code=None):
        if template:
            self.template = template

        PrewikkaError.__init__(self, message)

        if name:
            self.name = name

        if message:
            self.message = str(message)

        if code:
            self.code = code

        if log_priority:
            self.log_priority = log_priority

        self.log_user = log_user
        self.traceback = None
        if display_traceback:
            exc_type, exc_value, exc_tb = sys.exc_info()
            if exc_tb:
                self.traceback = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))

    def setupDataset(self):
        dataset = template.PrewikkaTemplate(self.template)
        dataset["name"] = self.name
        dataset["message"] = self.message
        dataset["code"] = self.code
        dataset["traceback"] = self.traceback

        return dataset

    def __str__(self):
        return self.message


class PrewikkaInvalidQueryError(PrewikkaUserError):
    def __init__(self, message):
        PrewikkaUserError.__init__(self, _("Invalid query"), message, log_priority=log.ERROR)
