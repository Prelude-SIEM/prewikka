# Copyright (C) 2014-2020 CS GROUP - France. All Rights Reserved.
# Author: Abdel ELMILI <abdel.elmili@c-s.fr>
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

import datetime

from prewikka import version
from .pathparser import PathParser

_LOG_PATHS = {"log": {"timestamp": datetime.datetime,
                      "message": text_type,
                      "raw_message": text_type,
                      "_raw_query": text_type
                      }
              }


class LogAPI(PathParser):
    plugin_name = "Log API"
    plugin_version = version.__version__
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_copyright = version.__copyright__
    plugin_description = N_("Provides an API to fetch logs")
    dataprovider_label = N_("Logs")

    def __init__(self):
        PathParser.__init__(self, _LOG_PATHS, "timestamp")

    def get_common_paths(self, index=False):
        return [
            (N_("Message"), "log.message"),
            (N_("Host"), "log.host"),
            (N_("Program"), "log.program"),
            (N_("Timestamp"), "log.timestamp")
        ]
