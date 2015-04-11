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

import urllib
import prelude

def urlencode(parameters, doseq=False):
    return urllib.urlencode(parameters, doseq).replace('&', '&amp;')


def create_link(path, parameters=None):
    link = urllib.pathname2url(path)

    if parameters:
        link += "?%s" % urlencode(parameters, doseq=True)

    return link


def idmef_criteria_to_urlparams(paths, values, operators=None, index=0):
    params = {}

    if not operators:
        operators = ['='] * len(paths)

    for path, value, operator in zip(paths, values, operators):

        # FIXME: The column type is alertlisting specific, in the long run, we need
        # to suppress this, and standardize all IDMEF parameters handling accross view
        ctype = prelude.IDMEFPath(path).getName(1)
        if ctype == "assessment" or ctype == "correlation_alert":
            ctype = "classification"

        if ctype not in ("classification", "source", "target", "analyzer"):
            raise Exception, _("The path '%s' cannot be mapped to a column") % path

        params["%s_object_%d" % (ctype, index)] = path
        params["%s_operator_%d" % (ctype, index)] = operator if value else "!"
        params["%s_value_%d" % (ctype, index)] = value if value else ""

        index += 1

    return urlencode(params)
