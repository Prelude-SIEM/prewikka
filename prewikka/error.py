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

from prewikka import template, log, env, response, localization
from prewikka.templates import ErrorTemplate, AJAXErrorTemplate


class RedirectionError(Exception):
    def __init__(self, location, code):
        self.location = location
        self.code = code


class PrewikkaError(Exception):
    template = ErrorTemplate.ErrorTemplate
    name = N_("An unexpected condition happened")
    message = ""
    details = ""
    code = 500
    log_priority = log.ERROR
    display_traceback = True

    def __init__(self, message, name=None, details=None, log_priority=None, log_user=None, template=None, code=None):
        if name is not None:
            self.name = name

        if message is not None:
            self.message = message

        if details is not None:
            self.details = details

        self._untranslated_details = str(self.details)
        self._untranslated_message = str(self.message)

        if self.name:
            self.name = _(self.name)

        if self.message:
            self.message = _(self._untranslated_message)

        if self.details:
            self.details = _(self._untranslated_details)

        if template:
            self.template = template

        if code:
            self.code = code

        if log_priority:
            self.log_priority = log_priority

        self.traceback = self._get_traceback()
        self.log_user = log_user

    def _setup_template(self, tmpl, ajax_error):
        dataset = template.PrewikkaTemplate(tmpl)

        for i in ("name", "message", "details", "code", "traceback"):
            dataset[i] = getattr(self, i)

        dataset["is_ajax_error"] = ajax_error
        dataset["document.base_url"] = env.request.web.get_baseurl()

        return dataset

    def _html_respond(self):
        from prewikka import baseview

        v = baseview.BaseView()
        v.dataset = self._setup_template(self.template, False)

        ret = v.respond()
        ret.code = self.code

        return ret

    def _get_traceback(self):
        if self.display_traceback and env.config.general.get("enable_error_traceback") not in ('no', 'false'):
            exc = sys.exc_info()
            if exc[0]:
                return "".join(traceback.format_exception(*exc))

    def respond(self):
        if self.message:
            env.log.log(self.log_priority, self)

        if not self.traceback:
            self.traceback = self._get_traceback()

        if not (env.request.web.is_stream or env.request.web.is_xhr):
            # This case should only occur in case of auth error (and viewmgr might not exist at this time)
            return self._html_respond()

        return response.PrewikkaResponse(self, code=self.code)

    @staticmethod
    def _format_error(message, details):
        if details:
            return message + ": " + details

        return message

    def __str__(self):
        return self._format_error(self._untranslated_message, self._untranslated_details)

    def __json__(self):
        dset = self._setup_template(AJAXErrorTemplate.AJAXErrorTemplate, True)
        return { "html": dset.render() }



class PrewikkaUserError(PrewikkaError):
    display_traceback = False

    def __init__(self, name=None, message=None, **kwargs):
        PrewikkaError.__init__(self, message, name=name, **kwargs)


class NotImplementedError(PrewikkaError):
    name = N_("Not implemented")

    def __init__(self, message=N_("Backend does not implement this operation")):
        PrewikkaError.__init__(self, message, log_priority=log.ERROR)
