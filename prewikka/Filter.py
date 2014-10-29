# Copyright (C) 2004-2014 CS-SI. All Rights Reserved.
# Author: Nicolas Delon <nicolas.delon@prelude-ids.com>
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


import re
import prelude

from prewikka import utils

class Error(Exception):
    pass


class Filter:
    def __init__(self, name, comment, elements, formula):
        self.name = name
        self.comment = comment
        self.elements = elements
        self.formula = formula
        crit = prelude.IDMEFCriteria(str(self))

    def _replace(self, element):
        element = element.group(1)
        if element in ("and", "AND", "&&"):
            return "&&"

        if element in ("or", "OR", "||"):
            return "||"

        if not self.elements.has_key(element):
            raise Error(_("Invalid filter element '%s' referenced from filter formula") % element)

        criteria, operator, value = self.elements[element]
        return "alert.%s %s '%s'" % (criteria, operator, utils.escape_criteria(value))

    def __str__(self):
        return re.sub("(\w+)", self._replace, self.formula)



AlertFilterList = prelude.IDMEFClass("alert")
HeartbeatFilterList = prelude.IDMEFClass("heartbeat")


if __name__ == "__main__":
    print Filter("foo", "",
                 { "A": ("alert.source(0).node.category", "=", "blah"),
                   "B": ("alert.messageid", "=", "2") },
                 "(A or B)")
