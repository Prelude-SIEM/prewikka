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

import sys
import traceback
import json
import abc

from prewikka import template, log, env, response
from prewikka.templates import ErrorTemplate


class PrewikkaException(Exception):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def respond(self):
        pass



class RedirectionError(PrewikkaException):
    def __init__(self, location, code):
        self.location = location
        self.code = code

    def respond(self):
        return response.PrewikkaRedirectResponse(self.location, code=self.code)



class PrewikkaUserError(PrewikkaException):
    template = ErrorTemplate.ErrorTemplate
    name = None
    message = ""
    code = 500
    log_priority = log.ERROR

    def __init__(self, name, message, display_traceback=False, log_priority=None, log_user=None, template=None, code=None):
        if template:
            self.template = template

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

    def _html_respond(self):
        from prewikka import baseview

        v = baseview.BaseView()
        v.dataset = template.PrewikkaTemplate(self.template)

        for i in ("name", "message", "code", "traceback"):
            v.dataset[i] = getattr(self, i)

        ret = v.respond()
        ret.code = self.code

        return ret

    def respond(self):
        if str(self):
            env.log.log(self.log_priority, self)

        if not (env.request.web.is_stream or env.request.web.is_xhr):
            # This case should only occur in case of auth error (and viewmgr might not exist at this time)
            return self._html_respond()

        return response.PrewikkaResponse(self, code=self.code)

    def __str__(self):
        return self.message

    def __json__(self):
        return {
            "name": self.name,
            "message": _(self.message),
            "code": self.code,
            "traceback": self.traceback
        }


class PrewikkaInvalidQueryError(PrewikkaUserError):
    def __init__(self, message):
        PrewikkaUserError.__init__(self, _("Invalid query"), message, log_priority=log.ERROR)
