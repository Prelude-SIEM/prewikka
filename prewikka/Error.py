# Copyright (C) 2004-2014 CS-SI. All Rights Reserved.
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
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


import traceback
import StringIO

from prewikka import DataSet, Log
from prewikka.templates import ErrorTemplate



class PrewikkaError(Exception):
    pass


class PrewikkaUserError(PrewikkaError):
    template = "ErrorTemplate"

    def __init__(self, name, message, display_traceback=False, log=None, log_user=None):
        PrewikkaError.__init__(self, message)

        self.name = name
        self.message = str(message)
        self.log_priority = log or Log.ERROR
        self.log_user = log_user

        if display_traceback:
            output = StringIO.StringIO()
            traceback.print_exc(file=output)
            output.seek(0)
            tmp = output.read()
            self.traceback = tmp
        else:
            self.traceback = None

    def setupDataset(self):
        self.dataset = DataSet.DataSet()
        self.dataset["name"] = self.name
        self.dataset["message"] = self.message
        self.dataset["traceback"] = self.traceback

        return self.dataset

    def __str__(self):
        return self.message


class PrewikkaInvalidQueryError(PrewikkaUserError):
    def __init__(self, message):
        PrewikkaUserError.__init__(self, "Invalid query", message, log_priority=Log.ERROR)
