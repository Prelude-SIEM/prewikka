# -*- coding: utf-8 -*-
# Copyright (C) 2018-2020 CS-SI. All Rights Reserved.
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

import re

from prewikka import resource
from prewikka.views.datasearch.datasearch import HighLighter, QueryParser


_HIGHLIGHT_PRE_TAG = "❤I💘PRELUDE❤"
_HIGHLIGHT_POST_TAG = "❥I💘PRELUDE❥"


class ElasticsearchHighLighter(HighLighter):
    _highlight_regex = re.compile(r"(%s.*?%s)" % (_HIGHLIGHT_PRE_TAG, _HIGHLIGHT_POST_TAG))

    @staticmethod
    def get_clean_value(value):
        return value.replace(_HIGHLIGHT_PRE_TAG, "").replace(_HIGHLIGHT_POST_TAG, "")

    @staticmethod
    def _highlighted(word):
        return (_HIGHLIGHT_PRE_TAG in word) and (_HIGHLIGHT_POST_TAG in word)

    @classmethod
    def split_phrase(self, phrase):
        return filter(None, self._highlight_regex.split(phrase))

    @classmethod
    def word_prepare(cls, word):
        if not cls._highlighted(word):
            return resource.HTMLNode("span", word)

        return resource.HTMLNode("span", cls.get_clean_value(word), _class="hl")


class ElasticsearchQueryParser(QueryParser):
    def _query(self):
        hl = {"pre_tags": [_HIGHLIGHT_PRE_TAG], "post_tags": [_HIGHLIGHT_POST_TAG], "number_of_fragments": 0}

        if env.request.user and env.request.user.get_property("anonymize"):
            hl = {}

        return env.dataprovider.query(self.get_paths(), self.all_criteria, limit=self.limit, offset=self.offset, type=self.type, highlight=hl)
