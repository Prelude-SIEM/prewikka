# Copyright (C) 2014-2016 CS-SI. All Rights Reserved.
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

import prelude
from prewikka import resource
from prewikka.utils.html import Markup
from prewikka.utils import OrderedDict, json


def _normalizeName(name):
    return "".join([ i.capitalize() for i in name.split("_") ])


def getOperatorList(type):
    if type == prelude.IDMEFValue.TYPE_STRING:
        return ["<>*", "<>", "=", "~*", "~", "!" ]

    elif type == prelude.IDMEFValue.TYPE_DATA:
        return ["<>*", "<>", "~", "~*", "=", "<", ">", "!" ]

    else:
        return ["=", "<", ">", "<=", ">=" ]


def getHTML(rootcl, rootidx=0):
    out = "<ul>"
    for subcl in rootcl:
        if subcl.getValueType() == prelude.IDMEFValue.TYPE_CLASS:
            out += '<li><a href="#">%s</a>' % subcl.getName()
        else:
            out += '<li class="idmef-leaf" id="%s"><a href="#">%s</a>' % (subcl.getPath(rootidx=rootidx), subcl.getName())

        if subcl.getValueType() == prelude.IDMEFValue.TYPE_CLASS:
            out += getHTML(subcl, rootidx)

        out += '</li>'

    return resource.HTMLSource(out + "</ul>")


def _get_path_list(rootcl=prelude.IDMEFClass("alert")):
    for node in rootcl:
        if node.getValueType() == prelude.IDMEFValue.TYPE_CLASS:
            for subnode in _get_path_list(node):
                yield subnode
        else:
            yield node.getPath()

def _gen_option_list(iterator, selected):
    out = resource.HTMLSource()

    for name, path in iterator:
        if path in selected:
            out += resource.HTMLSource("<option value='{0}' selected>{1}</option>").format(path, name)
        else:
            out += resource.HTMLSource("<option value='{0}'>{1}</option>").format(path, name)

    return out

def get_html_select(selected_paths=None, default_paths=None, all_paths=True, max_paths=0):
    _default_paths = default_paths or {
        "Source IP": "alert.source(0).node.address(0).address",
        "Source Port": "alert.source(0).service.port",
        "Target IP": "alert.target(0).node.address(0).address",
        "Target Port": "alert.target(0).service.port",
        "Classification": "alert.classification.text",
        "Analyzer": "alert.analyzer(-1).name"
    }

    if selected_paths is None:
        selected_paths = []

    _html_default_value = _gen_option_list(_default_paths.items(), selected_paths)
    if all_paths:
        _html_all_value = _gen_option_list(((i, i) for i in _get_path_list() if i not in _default_paths.values()), selected_paths)
        all_paths = resource.HTMLSource('<optgroup label="%s">%s</optgroup>') % (_("All paths"), _html_all_value)

    html = resource.HTMLSource("""
<link rel="stylesheet" type="text/css" href="prewikka/css/chosen.min.css">
<link rel="stylesheet" type="text/css" href="prewikka/css/bootstrap-chosen.css">

<select class="data-paths chosen-sortable form-control" %s name="selected_path" data-placeholder="%s">
    <optgroup label="%s">
    %s
    </optgroup>

    %s
</select>

<script type="text/javascript">
    $LAB.script("prewikka/js/chosen.jquery.min.js").wait()
        .script("prewikka/js/jquery-chosen-sortable.js").wait(function() {
            $(".data-paths").chosen({
                max_selected_options: %d,
                width: "100%%",
                search_contains: true
             }).chosenSortable();

            $(".data-paths").chosenSetOrder(%s);
         });
</script>
""") % (resource.HTMLSource('multiple') if max_paths != 1 else "", _("Select paths..."),
        _("Default paths"), _html_default_value, all_paths or "", max_paths, Markup(json.dumps(selected_paths)))

    return html
