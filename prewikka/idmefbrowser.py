# Copyright (C) 2014-2018 CS-SI. All Rights Reserved.
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
from prewikka.utils import html


def getOperatorList(type):
    if type == prelude.IDMEFValue.TYPE_STRING:
        return ["<>*", "<>", "=", "~*", "~", "!"]

    elif type == prelude.IDMEFValue.TYPE_DATA:
        return ["<>*", "<>", "~", "~*", "=", "<", ">", "!"]

    else:
        return ["=", "<", ">", "<=", ">="]


def _gen_option_list(iterator, selected):
    out = resource.HTMLSource()

    for name, path in iterator:
        if path in selected:
            out += resource.HTMLSource("<option value='{0}' selected>{1}</option>").format(path, name)
        else:
            out += resource.HTMLSource("<option value='{0}'>{1}</option>").format(path, name)

    return out


def get_html_select(selected_paths=None, default_paths=None, all_paths=True, max_paths=0):
    if default_paths is None:
        default_paths = env.dataprovider.get_common_paths("alert", index=True)

    if selected_paths is None:
        selected_paths = []

    _html_default_value = _gen_option_list(default_paths, selected_paths)
    if all_paths:
        _html_all_value = _gen_option_list(((i, i) for i in env.dataprovider.get_paths("alert") if i not in zip(default_paths)[1]), selected_paths)
        all_paths = resource.HTMLSource('<optgroup label="%s">%s</optgroup>') % (_("All paths"), _html_all_value)

    htm = resource.HTMLSource("""
<link rel="stylesheet" type="text/css" href="prewikka/css/chosen.min.css">
<link rel="stylesheet" type="text/css" href="prewikka/css/bootstrap-chosen.css">

<select class="data-paths chosen-sortable form-control" %s name="selected_path[]" data-placeholder="%s">
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
        _("Default paths"), _html_default_value, all_paths or "", max_paths, html.escapejs(selected_paths))

    return htm
