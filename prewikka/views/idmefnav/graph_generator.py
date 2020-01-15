# -*- coding: utf-8 -*-
# Copyright (C) 2016-2020 CS-SI. All Rights Reserved.
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

import cgi
import glob
import io
import sys
import yaml

try:
    import pydot
    WITH_PYDOT = True
except ImportError:
    WITH_PYDOT = False

_LINK_TAG = 'IDMEF_NAV_LINK_TAG'


class Schema(dict):
    def __init__(self, folder):
        self.folder = folder

    def image_load(self):
        self.data_load()

        for struct in self._data_load():
            with io.open("%s/graph/%s.svg" % (self.folder, struct["name"]), 'r', encoding="utf8") as stream:
                self[struct["name"]]["svg"] = stream.read()

    def data_load(self):
        for struct in self._data_load():
            self[struct["name"]] = struct

    def _data_load(self):
        for f in glob.glob("%s/yaml/*.yml" % self.folder):
            with io.open(f, 'r', encoding='utf-8') as stream:
                yield yaml.safe_load(stream)

    @staticmethod
    def quote_val(val):
        return '"%s"' % val

    def graphviz(self, idmef_class, direction='LR', link_format=None, format='svg'):
        dot = pydot.Dot(graph_name=self.quote_val(idmef_class), format=format, bgcolor='transparent')
        dot.set_graph_defaults(rankdir=direction)
        dot.set_node_defaults(shape='plaintext')

        self.add_node(dot, idmef_class, link_format)

        return dot

    def gen_all(self, direction='LR', link_format=None):
        for name in self:
            self.graphviz(name, direction, link_format, 'svg').write("%s/graph/%s.svg" % (self.folder, name), format='svg')

    def add_node(self, dot, node_name, link_format=None, nodes=None):
        if node_name not in self:
            return

        if not nodes:
            nodes = {}

        nodes[node_name] = True

        color = self[node_name].get("color", "#FFFFFF")
        link = link_format % node_name if link_format else "#"

        label = """<
        <table BORDER="0" CELLBORDER="1" CELLSPACING="0">
        <tr>
            <td BGCOLOR="{color}" HREF="{link}" TITLE="{title}">{name}</td>
        </tr>
        """.format(
            color=self.darken_color(color),
            link=link,
            title=cgi.escape(self[node_name].get("description"), quote=True),
            name=node_name
        )

        for key, value in self[node_name].get("childs", {}).items():
            if key not in self:
                continue

            if key not in nodes:
                self.add_node(dot, key, link_format, nodes)

            args = {'dir': 'back',
                    'arrowtail': 'invempty'}
            if value.get("multiplicity"):
                args['label'] = value.get("multiplicity")

            dot.add_edge(pydot.Edge(self.quote_val(node_name), self.quote_val(key), **args))

        for key, value in self[node_name].get("aggregates", {}).items():
            if key in self:
                if key not in nodes:
                    self.add_node(dot, key, link_format, nodes)

                args = {'dir': 'forward'}
                if value.get("multiplicity"):
                    args['label'] = value.get("multiplicity")

                dot.add_edge(pydot.Edge(self.quote_val(node_name), self.quote_val(key), **args))
                continue

            label += self.graph_attr(key, value, color, link)

        for key, value in self[node_name].get("attributes", {}).items():
            label += self.graph_attr(key, value, color, link)

        label += "</table>>"
        dot.add_node(pydot.Node(self.quote_val(node_name), label=label))

    @staticmethod
    def darken_color(hex_color, amount=0.6):
        hex_color = hex_color.replace('#', '')
        rgb = []
        rgb.append(int(hex_color[0:2], 16) * amount)
        rgb.append(int(hex_color[2:4], 16) * amount)
        rgb.append(int(hex_color[4:6], 16) * amount)

        return "#" + ''.join(["{0:02x}".format(int(c)) for c in rgb])

    @staticmethod
    def graph_attr(name, value, color, link):
        return """<tr><td BGCOLOR="{color}" HREF="{link}" TITLE="{title}" >[{type}] {name} ({mult})</td></tr>""".format(
            color=color,
            link=link,
            title=cgi.escape(value.get("description"), quote=True),
            name=name,
            mult=value.get("multiplicity"),
            type=value.get("type"),
        )

if __name__ == "__main__":
    if not WITH_PYDOT:
        print('You need pydot to update graphs.')
        sys.exit(1)

    schema = Schema('htdocs')
    schema.data_load()
    schema.gen_all(link_format="%s?idmef_class=%%s" % _LINK_TAG)
