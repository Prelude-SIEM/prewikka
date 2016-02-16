# Copyright (C) 2014-2015 CS-SI. All Rights Reserved.
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

import prelude
from prewikka.utils import OrderedDict, escape_html_string

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

    return out + "</ul>"


def _get_path_list(rootcl=prelude.IDMEFClass("alert")):
    for node in rootcl:
        if node.getValueType() == prelude.IDMEFValue.TYPE_CLASS:
            for subnode in _get_path_list(node):
                yield subnode
        else:
            yield node.getPath()

def _gen_option_list(iterator, selected):
    out = ""
    for name, path in iterator:
        if path in selected:
            out += "<option value='{0}' selected>{1}</option>".format(path, name)
        else:
            out += "<option value='{0}'>{1}</option>".format(path, name)

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

    html = """
<link rel="stylesheet" type="text/css" href="prewikka/css/chosen.min.css">
<link rel="stylesheet" type="text/css" href="prewikka/css/bootstrap-chosen.css">"""

    html += """<select class="data-paths chosen-sortable form-control" %s name="selected_path" data-placeholder="%s">""" % (
        "multiple" if max_paths != 1 else "",
        escape_html_string(_("Select paths..."))
    )

    html += """
    <optgroup label="%s">
    %s
    </optgroup>
""" % (escape_html_string(_("Default paths")), _html_default_value)

    if all_paths:
        _html_all_value = _gen_option_list(((i, i) for i in _get_path_list() if i not in _default_paths.values()), selected_paths)
        html += """
    <optgroup label="%s">
    %s
    </optgroup>""" % (escape_html_string(_("All paths")), _html_all_value)

    html += """
</select>

<script type="text/javascript">
    $LAB.script("prewikka/js/chosen.jquery.min.js").wait()
        .script("prewikka/js/jquery-chosen-sortable.js").wait(function() {
            $(".data-paths").chosen({
                max_selected_options: %d,
                width: "100%%",
                search_contains: true
             }).chosenSortable();

            var select = $(".data-paths");
            var container = select.siblings('.chosen-container');
            var list = container.find('.chosen-choices');
            var sorted_elements = %s;

            for (var i = 0; i < sorted_elements.length; ++i) {
                var value = sorted_elements[i];
                var elem = select.find('option[value="' + value + '"]');
                var index = elem[0].index;

                index = index + elem.parent().index() + 1;
                list.find('a.search-choice-close[data-option-array-index="' + index + '"]')
                    .parent()
                    .detach()
                    .prependTo(list);
            }
         });
</script>
""" % (max_paths, list(reversed(selected_paths)))

    return html
