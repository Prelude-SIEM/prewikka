# Copyright (C) 2018 CS-SI. All Rights Reserved.
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

"""
Tests for `prewikka.resource`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from prewikka.resource import Link, CSSLink, JSLink, HTMLSource, CSSSource, JSSource, HTMLNode
from prewikka.utils import json


def test_link():
    """
    Test `prewikka.resource.Link` class.
    """
    Link()


def test_css_link():
    """
    Test `prewikka.resource.CSSLink` class.
    """
    assert text_type(CSSLink('style.css')) == '<link rel="stylesheet" type="text/css" href="style.css" />'


def test_js_link():
    """
    Test `prewikka.resource.JSLink` class.
    """
    assert text_type(JSLink('script.js')) == '<script type="text/javascript" src="script.js"></script>'


def test_html_source():
    """
    Test `prewikka.resource.HTMLSource` class.
    """
    HTMLSource()


def test_css_source():
    """
    Test `prewikka.resource.CSSSource` class.
    """
    assert text_type(CSSSource('body > div {overflow: auto;}')) == '<style type="text/css">body > div {overflow: auto;}</style>'


def test_js_source():
    """
    Test `prewikka.resource.JSSource` class.
    """
    assert text_type(JSSource('var foo = bar.baz() > 0;')) == '<script type="text/javascript">var foo = bar.baz() > 0;</script>'


def test_html_node():
    """
    Test `prewikka.resource.HTMLNode` class.
    """
    node = HTMLNode('a')

    assert node.to_string() == str(node)
    assert json.dumps(node)

    node2 = HTMLNode('a', **{'_icon': 'gears', 'class': 'foobar', 'test': 'true'})

    assert str(node2)

    assert not node == node2

    assert node < node2
