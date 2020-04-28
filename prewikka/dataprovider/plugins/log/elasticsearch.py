# -*- coding: utf-8 -*-
# Copyright (C) 2015-2020 CS-SI. All Rights Reserved.
# Author: Sélim Menouar <selim.menouar@c-s.fr>
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

from prewikka import hookmanager

from prewikka import version
from prewikka.dataprovider.helpers.elasticsearch import ElasticsearchPlugin


class ElasticsearchLogPlugin(ElasticsearchPlugin):
    plugin_name = "Elasticsearch Log API"
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("Plugin for querying logs from Elasticsearch")
    type = "log"

    @hookmanager.register("HOOK_LOG_EXTRACT_IDMEF_HOST")
    def _get_idmef_host_value(self, alert):
        return alert.get("analyzer(-1).node.name") or alert.get("analyzer(-1).node.address(-1).address")
