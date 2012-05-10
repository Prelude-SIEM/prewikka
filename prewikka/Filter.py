# Copyright (C) 2004-2012 CS-SI. All Rights Reserved.
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
# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING.  If not, write to
# the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.


import re
import prelude

from prewikka import utils

class Error(Exception):
    pass


class CriteriaIDMEF:
    def __init__(self, root=prelude.IDMEF_CLASS_ID_MESSAGE, text=""):
        self.CriteriaList = []
        self._idmef_class_tree(root, text, self.CriteriaList)

    def _idmef_class_tree(self, root, criteria_root, outlist):

        i = 0
        while True:
            name = prelude.idmef_class_get_child_name(root, i)
            if name == None:
                break

            if criteria_root != None:
                criteria = "%s.%s" % (criteria_root, name)
            else:
                criteria = "%s" % (name)

            if criteria == "alert.target.file.linkage":
                break

            if prelude.idmef_class_get_child_value_type(root, i) == prelude.IDMEF_VALUE_TYPE_CLASS:
                self._idmef_class_tree(prelude.idmef_class_get_child_class(root, i), criteria, outlist)
            else:
                outlist.append(criteria)

            i = i + 1


class Filter:
    def __init__(self, name, comment, elements, formula):
        self.name = name
        self.comment = comment
        self.elements = elements
        self.formula = formula

        crit = prelude.idmef_criteria_new_from_string(unicode(self).encode("utf8"))
        prelude.idmef_criteria_destroy(crit)

    def _replace(self, element):
        element = element.group(1)
        if element in ("and", "AND", "&&"):
            return "&&"

        if element in ("or", "OR", "||"):
            return "||"

        if not self.elements.has_key(element):
            raise Error(_("Invalid filter element '%s' referenced from filter formula") % element)

        criteria, operator, value = self.elements[element]
        return "%s %s '%s'" % (criteria, operator, utils.escape_criteria(value))

    def __str__(self):
        return re.sub("(\w+)", self._replace, self.formula)



AlertFilterList = CriteriaIDMEF(prelude.IDMEF_CLASS_ID_ALERT, "alert").CriteriaList
HeartbeatFilterList = CriteriaIDMEF(prelude.IDMEF_CLASS_ID_HEARTBEAT, "heartbeat").CriteriaList


if __name__ == "__main__":
    print Filter("foo", "",
                 { "A": ("alert.source(0).node.category", "=", "blah"),
                   "B": ("alert.messageid", "=", "2") },
                 "(A or B)")
