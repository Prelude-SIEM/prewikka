# Copyright (C) 2004-2017 CS-SI. All Rights Reserved.
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

import sys
import prelude

if sys.version_info >= (3,0):
    from urllib.parse import quote, unquote, urlsplit, urlunsplit, urlencode as _urlencode
else:
    from urllib import quote, unquote, urlencode as __urlencode
    from urlparse import urlsplit, urlunsplit

    def _convert(d):
        if isinstance(d, (list, tuple)):
            return [_convert(i) for i in d]

        elif isinstance(d, text_type):
            return d.encode("utf8")

        else:
            return d

    def _urlencode(parameters, doseq=False):
        if hasattr(parameters, "items"):
            parameters = parameters.items()

        return __urlencode([(k.encode("utf8"), _convert(v)) for k, v in parameters], doseq)


def iri2uri(iri, encoding="utf8"):
    # Character list compiled from RFC 3986, section 2.2
    safe = b":/?#[]@!$&'()*+,;="
    scheme, authority, path, query, frag = urlsplit(iri)

    tpl = authority.split(":", 1)
    if len(tpl) == 1:
        authority = authority.encode('idna')
    else:
        authority = tpl[0].encode('idna') + ":%s" % tpl[1]

    return urlunsplit((scheme.encode(encoding), authority,
                       quote(path.encode(encoding), safe),
                       quote(query.encode(encoding), safe),
                       quote(frag.encode(encoding), safe)))


def urlencode(parameters, doseq=False):
    return _urlencode(parameters, doseq).replace('&', '&amp;')


def idmef_criteria_to_urlparams(paths, values, operators=None, index=0):
    params = []

    if not operators:
        operators = ['='] * len(paths)

    for path, value, operator in zip(paths, values, operators):

        # Special case for classification checkboxes
        if path in ("alert.type", "alert.assessment.impact.severity", "alert.assessment.impact.completion"):
            # Operators other than '=' are not supported
            params.append((path, value))
            continue

        # FIXME: The column type is alertlisting specific, in the long run, we need
        # to suppress this, and standardize all IDMEF parameters handling accross view
        ctype = prelude.IDMEFPath(path).getName(1)
        if ctype in ("messageid", "assessment", "correlation_alert", "overflow_alert", "tool_alert", "additional_data"):
            ctype = "classification"

        if ctype not in ("classification", "source", "target", "analyzer"):
            raise Exception(_("The path '%s' cannot be mapped to a column") % path)

        params.append(("%s_object_%d" % (ctype, index), path))
        params.append(("%s_operator_%d" % (ctype, index), operator if value else "!"))
        params.append(("%s_value_%d" % (ctype, index), value if value else ""))

        index += 1

    return urlencode(params)
