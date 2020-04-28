# -*- coding: utf-8 -*-
# Copyright (C) 2016-2020 CS-SI. All Rights Reserved.
# Author: Abdel ELMILI <abdel.elmili@c-s.fr>
# Author: François POIROTTE <francois.poirotte@c-s.fr>
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

import collections
import copy
import re

from prewikka import error
from prewikka.dataprovider import COMPOSITE_TIME_FIELD, Criterion, CriterionOperator
from prewikka.dataprovider.pathparser import _Path, SelectionObject, STRING_INDEX_REGEX


_OPERATORS = {
    "common": {
        CriterionOperator.GREATER: "%(left)s > %(right)s",
        CriterionOperator.LOWER: "%(left)s < %(right)s",
        CriterionOperator.LOWER_OR_EQUAL: "%(left)s <= %(right)s",
        CriterionOperator.GREATER_OR_EQUAL: "%(left)s >= %(right)s",
    },

    # Special cases when the right operand is None
    "special": {
        CriterionOperator.EQUAL: "%(left)s IS NULL",
        CriterionOperator.NOT_EQUAL: "%(left)s IS NOT NULL",
    },

    "mysql": {
        CriterionOperator.EQUAL: "%(left)s = BINARY %(right)s",
        CriterionOperator.EQUAL_NOCASE: "%(left)s = %(right)s",
        CriterionOperator.NOT_EQUAL: "%(left)s != BINARY %(right)s",
        CriterionOperator.NOT_EQUAL_NOCASE: "%(left)s != %(right)s",
        CriterionOperator.REGEX: "%(left)s REGEXP %(right)s",
        CriterionOperator.REGEX_NOCASE: "%(left)s REGEXP BINARY %(right)s",
        CriterionOperator.NOT_REGEX: "%(left)s NOT REGEXP %(right)s",
        CriterionOperator.NOT_REGEX_NOCASE: "%(left)s NOT REGEXP BINARY %(right)s",
        CriterionOperator.SUBSTR: "%(left)s LIKE BINARY %(right)s",
        CriterionOperator.SUBSTR_NOCASE: "%(left)s LIKE %(right)s",
        CriterionOperator.NOT_SUBSTR: "%(left)s NOT LIKE BINARY %(right)s",
        CriterionOperator.NOT_SUBSTR_NOCASE: "%(left)s NOT LIKE %(right)s",
    },

    "pgsql": {
        CriterionOperator.EQUAL: "%(left)s = %(right)s",
        CriterionOperator.EQUAL_NOCASE: "lower(%(left)s) = lower(%(right)s)",
        CriterionOperator.NOT_EQUAL: "%(left)s != %(right)s",
        CriterionOperator.NOT_EQUAL_NOCASE: "lower(%(left)s) != lower(%(right)s)",
        CriterionOperator.REGEX: "%(left)s ~ %(right)s",
        CriterionOperator.REGEX_NOCASE: "%(left)s ~* %(right)s",
        CriterionOperator.NOT_REGEX: "%(left)s !~ %(right)s",
        CriterionOperator.NOT_REGEX_NOCASE: "%(left)s !~* %(right)s",
        CriterionOperator.SUBSTR: "%(left)s LIKE %(right)s",
        CriterionOperator.SUBSTR_NOCASE: "%(left)s ILIKE %(right)s",
        CriterionOperator.NOT_SUBSTR: "%(left)s NOT LIKE %(right)s",
        CriterionOperator.NOT_SUBSTR_NOCASE: "%(left)s NOT ILIKE %(right)s",
    },

    # SQLite doesn't support case-insensitive comparison for unicode characters by default
    # (See https://www.sqlite.org/faq.html#q18)
    "sqlite": {
        CriterionOperator.EQUAL: "%s(left)s = %(right)s",
        CriterionOperator.EQUAL_NOCASE: "%s(left)s = %(right)s",
        CriterionOperator.NOT_EQUAL: "%(left)s != %(right)s",
        CriterionOperator.NOT_EQUAL_NOCASE: "%(left)s != %(right)s",
    },
}

_EXTRACTION = {
    "mysql": {
        "quarter": "QUARTER(%s)",
        "year": "EXTRACT(YEAR FROM %s)",
        "month": "EXTRACT(MONTH FROM %s)",
        "yday": "DAYOFYEAR(%s)",
        "mday": "DAYOFMONTH(%s)",
        "wday": "WEEKDAY(%s)",
        "hour": "EXTRACT(HOUR FROM %s)",
        "min": "EXTRACT(MINUTE FROM %s)",
        "sec": "EXTRACT(SECOND FROM %s)",
        "msec": "EXTRACT(MICROSECOND FROM %s) / 1000",
        "usec": "EXTRACT(MICROSECOND FROM %s)",
    },

    "pgsql": {
        "quarter": "EXTRACT(QUARTER FROM %s)",
        "year": "EXTRACT(YEAR FROM %s)",
        "month": "EXTRACT(MONTH FROM %s)",
        "yday": "EXTRACT(DOY FROM %s)",
        "mday": "EXTRACT(DAY FROM %s)",
        "wday": "(EXTRACT(ISODOW FROM %s) - 1)",
        "hour": "EXTRACT(HOUR FROM %s)",
        "min": "EXTRACT(MINUTE FROM %s)",
        "sec": "EXTRACT(SECOND FROM %s)",
        "msec": "EXTRACT(MILLISECOND FROM %s)",
        "usec": "EXTRACT(MICROSECOND FROM %s)",
    },

    "sqlite": {
        "quarter": "((STRFTIME('%%m', %s) + 2) / 3)",
        "year": "STRFTIME('%%Y', %s) + 0",
        "month": "STRFTIME('%%m', %s) + 0",
        "yday": "STRFTIME('%%j', %s) + 0",
        "mday": "STRFTIME('%%d', %s) + 0",
        "wday": "((STRFTIME('%%w', %s) + 6) %% 7)",
        "hour": "STRFTIME('%%H', %s) + 0",
        "min": "STRFTIME('%%M', %s) + 0",
        "sec": "STRFTIME('%%S', %s) + 0",
        "msec": "(STRFTIME('%%f', %s) - STRFTIME('%%S', %s)) * 1000",
        # SQLite's date/time precision does not support microseconds;
        # we make "usec" an alias for "msec" instead.
        "usec": "(STRFTIME('%%f', %s) - STRFTIME('%%S', %s)) * 1000",
    },
}

_FUNCTIONS_MAP = {
    "mysql": {
        "timezone": "CONVERT_TZ({0}, 'GMT', '{1}')",
        "date": "TIMESTAMP('{0}')",
        "add_date": "DATE_ADD({0}, '{1}')",
        "sub_date": "DATE_SUB({0}, '{1}')",
    },

    "pgsql": {
        "timezone": "timezone('{1}', timezone('UTC', {0}))",
        "date": "TIMESTAMP '{0}'",
        "add_date": "{0} + INTERVAL '{1}'",
        "sub_date": "{0} - INTERVAL '{1}'",
    },

    "sqlite": {
        "timezone": "{0}",  # timezone is not supported in sqlite
        "date": "datetime('{0}')",
        "add_date": "datetime({0}, '+{1}')",
        "sub_date": "datetime({0}, '-{1}')",
    },
}

_TIME_UNITS = {
    "year": (0, "year"),
    "quarter": (1, "quarter"),
    "month": (2, "month"),
    "yday": (3, "day"),
    "mday": (3, "day"),
    "wday": (3, "day"),
    "hour": (4, "hour"),
    "min": (5, "min"),
    "sec": (6, "sec"),
    "msec": (7, "msec"),
    "usec": (8, "usec"),
}

_SPECIAL_TABLES = set(["_intervals", "_main"])


class CTETimeBoundsError(error.PrewikkaUserError):
    name = N_("Dataprovider error")
    message = N_("Could not find time bounds in CTE query")


class SQLTable(object):
    def __init__(self, name, pkey=None):
        self._name = name
        self.pkey = pkey

    def __str__(self):
        return self._name


class SQLQuery(object):
    def __init__(self, base_table, distinct=False, limit=-1, offset=0):
        self.base_table = base_table
        self.select = []
        self.joins = []
        self.joined = [base_table]
        self.where = None
        self.group_by = []
        self.order_by = []
        self.distinct = distinct
        self.limit = limit
        self.offset = offset

    def __str__(self):
        query = "SELECT %s %s FROM %s %s" % (
            "DISTINCT" if self.distinct else "",
            ", ".join(self.select),
            "%s AS t0" % self.base_table,
            " ".join("LEFT JOIN %s ON %s" % (table, condition) for table, condition in self.joins),
        )

        if self.where:
            query += " WHERE %s" % self.where
        if self.group_by:
            query += " GROUP BY %s" % ", ".join(self.group_by)
        if self.order_by:
            query += " ORDER BY %s" % ", ".join(self.order_by)
        if self.offset > 0 or self.limit > -1:
            query += " LIMIT %s OFFSET %d" % (self.limit, self.offset)

        return query


class SQLBuilder(object):
    def __init__(self, paths_map, tables, joins, handle_wildcards=False, db=None, time_paths=()):
        self._paths_map = paths_map
        self._tables = tables
        self._base_table = tables[0]
        self._handle_wildcards = handle_wildcards
        self._db = db or env.db
        self._joins = joins
        self._time_paths = time_paths

        self._init_relations()

        self._reverse_paths_map = dict((v, k) for k, v in paths_map.items())
        for table1, relation in self._relations.items():
            for table2, rel in relation.items():
                if (table2, rel["dest_pkey"][0]) not in self._reverse_paths_map:
                    self._reverse_paths_map[(table2, rel["dest_pkey"][0])] = self._reverse_paths_map[(table1, rel["src_pkey"][0])]

    def _init_relations(self):
        self._relations = collections.OrderedDict()
        for (t1, c1), (t2, c2) in self._joins:
            if not isinstance(c1, tuple):
                c1 = (c1,)
            if not isinstance(c2, tuple):
                c2 = (c2,)

            self._relations.setdefault(t1, {})[t2] = dict(src_pkey=c1, dest_pkey=c2)
            self._relations.setdefault(t2, {})[t1] = dict(src_pkey=c2, dest_pkey=c1)

        self._join_paths = {}
        for table in self._tables:
            self._join_paths[table] = self._find_paths(table)

    def _find_paths(self, source):
        ret = {source: [source]}
        remaining = [source]
        while remaining:
            table = remaining.pop(0)
            for t in self._relations.get(table, []):
                if t not in ret:
                    remaining.append(t)
                    ret[t] = ret[table] + [t]

        ret.pop(source)
        return ret

    def _get_field_info(self, path):
        return self._paths_map[path.path]

    def _get_base_table(self, selection):
        for index, candidate in enumerate(selection):
            # Exclude things like "count(1)"
            # which cannot be used for JOINs.
            path = candidate.get_path()
            if path:
                return self._get_field_info(path)[0]

        return self._base_table

    def _process_function(self, function, query, with_aliases=True):
        args = []
        for i in function.args:
            args.append(self._process_object(i, query, with_aliases))

        sql_func = _FUNCTIONS_MAP[self._db.get_type()].get(function.name)
        if sql_func:
            return sql_func.format(*args)

        return "%s(%s)" % (function.name.upper(), ", ".join(args))

    def _process_commands(self, selection, index, query):
        for command in selection.commands:
            if command == "order_asc":
                query.order_by.append("%d ASC" % index)
            elif command == "order_desc":
                query.order_by.append("%d DESC" % index)
            elif command == "group_by":
                query.group_by.append("%d" % index)

    def _process_path(self, path, aliases):
        table, attr = self._paths_map[path]

        if not aliases:
            return attr

        for i, alias in enumerate(reversed(aliases)):
            # Use the last matching alias for the string-index support
            if alias == table:
                return "t%d.%s" % (len(aliases) - i - 1, attr)

        raise ValueError

    def _process_value(self, value):
        return self._db.escape(value) if value is not None else None

    def _process_object(self, obj, query, with_aliases=True):
        if obj.is_function:
            return self._process_function(obj, query, with_aliases)

        elif obj.is_path:
            if obj.klass in _SPECIAL_TABLES:
                return obj.path

            table, attr = self._get_field_info(obj)

            # Handle table JOINs for selection.
            self._add_join(table, query)

            # Make sure we also support things like "COUNT(1)".
            return "t%s.%s" % (query.joined.index(table), attr) if with_aliases else attr

        elif obj.is_constant:
            return obj.value

    def _gen_selection(self, selection, query, with_aliases=True):
        selected = self._process_object(selection.object, query, with_aliases)
        if not selection.extract:
            return selected

        # This method expects all timestamps stored in the database to be in UTC.
        return _EXTRACTION[self._db.get_type()][selection.extract] % selected

    def _process_criterion(self, criterion, aliases):
        lhs = self._process_path(criterion.left, aliases)
        rhs = self._process_value(criterion.right)

        # Binary operator.
        op = criterion.operator
        if criterion.right is None:
            op = _OPERATORS["special"][op]
        elif op in _OPERATORS["common"]:
            op = _OPERATORS["common"][op]
        else:
            # Handle "%" wildcard for SQL LIKE operator
            if self._handle_wildcards and op.is_substring and isinstance(rhs, text_type):
                rhs = self._handle_like_pattern(rhs)

            op = _OPERATORS[self._db.get_type()][op]

        return op % {"left": lhs, "right": rhs}

    def _handle_like_pattern(self, pattern):
        # pattern is a string with quotes around
        return "'%%%s%%'" % pattern[1:-1]

    def _add_join(self, table, query, string_index=None):
        if not table or table in query.joined and not string_index:
            return

        table_paths = self._join_paths[query.base_table]
        for i, dest in enumerate(table_paths[table][1:]):
            src = table_paths[table][i]

            if dest in query.joined and not (table == dest and string_index):
                continue

            # The left-hand side table always has an alias.
            # Create a new alias on the fly if necessary
            # for the right-hand side table.
            query.joined.append(dest)
            alias_src = "t%d" % query.joined.index(src)
            alias_dest = "t%d" % (len(query.joined) - 1)

            # Retrieve the names of the fields forming the join key.
            fields = zip(self._relations[src][dest]["src_pkey"], self._relations[src][dest]["dest_pkey"])

            # Add the join key's fields to the join filters.
            join_crit = ["%s.%s = %s.%s" % (alias_src, i, alias_dest, j) for (i, j) in fields]
            if string_index:
                path, value = string_index
                join_crit.append("%s = %s" % (self._process_path(path, query.joined), self._db.escape(value)))

            query.joins.append(("%s AS %s" % (dest, alias_dest), " AND ".join(join_crit)))

    def _process_selection(self, paths, query, with_aliases=True):
        for i, selection in enumerate(paths):
            selected = self._gen_selection(selection, query, with_aliases)
            query.select.append("%s AS %s" % (selected, "c%d" % i) if with_aliases else selected)

            # Handle ORDER BY/GROUP BY directives.
            self._process_commands(selection, len(query.select), query)

    def _process_criteria(self, criteria, query, with_aliases=True):
        if not criteria:
            return

        if criteria.operator == CriterionOperator.NOT:
            return "NOT(%s)" % self._process_criteria(criteria.right, query, with_aliases)

        elif criteria.operator.is_boolean:
            op = " AND " if criteria.operator == CriterionOperator.AND else " OR "
            return "(%s)" % op.join(self._process_criteria(term, query, with_aliases) for term in (criteria.left, criteria.right))

        ret = self._handle_indexation_by_string(criteria, query, with_aliases)
        if ret:
            return ret

        self._add_join(self._paths_map[criteria.left][0], query)
        return self._process_criterion(criteria, query.joined if with_aliases else [])

    def _handle_indexation_by_string(self, criteria, query, with_aliases):
        matches = re.findall(STRING_INDEX_REGEX, criteria.left)
        if matches:
            path = re.sub(STRING_INDEX_REGEX, "", criteria.left)
            string_index = (env.dataprovider.get_indexation_path(criteria.left), matches[0][1])
            self._add_join(self._paths_map[path][0], query, string_index=string_index)
            return self._process_criteria(Criterion(path, criteria.operator, criteria.right),
                                          query, with_aliases)

    def build_query(self, paths, criteria, distinct, limit, offset):
        cte = False
        for path in paths:
            p = path.get_path()
            if p and p.name == COMPOSITE_TIME_FIELD:
                cte = True
                break

        if cte:
            return self._build_cte_query(paths, criteria, distinct, limit, offset)
        else:
            return self._build_query(paths, criteria, distinct, limit, offset)

    def _build_query(self, paths, criteria, distinct, limit, offset):
        query = SQLQuery(self._get_base_table(paths), distinct=distinct, limit=limit, offset=offset)

        self._process_selection(paths, query)
        query.where = self._process_criteria(criteria, query)

        return text_type(query)

    def _build_cte_query(self, paths, criteria, distinct, limit, offset):
        step = None
        start, end = self._get_time_bounds(criteria)
        inner_paths = [SelectionObject(_Path(p)) for p in self._time_paths]
        outer_paths = []
        index = len(inner_paths)

        for p in paths:
            if not p.get_path():
                # Aggregation function without a path (e.g. COUNT(1))
                outer_paths.append(p)
            elif p.get_path().name == COMPOSITE_TIME_FIELD:
                # Composite time field with extract
                outer_paths.append(SelectionObject(_Path("_intervals.start"), extract=p.extract, commands=p.commands))
                if not step or _TIME_UNITS[p.extract] > _TIME_UNITS[step]:
                    step = p.extract
            else:
                # Remove the commands/functions from the inner query
                inner_paths.append(SelectionObject(p.get_path()))
                # Use aliases for the outer query
                copied = copy.deepcopy(p)
                copied.get_path().name = "c%d" % index
                copied.get_path().path = "_main.c%d" % index
                copied.get_path().klass = "_main"
                outer_paths.append(copied)
                index += 1

        inner_query = SQLQuery(self._base_table, distinct=distinct, limit=limit, offset=offset)
        self._process_selection(inner_paths, inner_query)
        inner_query.where = self._process_criteria(criteria, inner_query)

        outer_query = SQLQuery(self._base_table)
        self._process_selection(outer_paths, outer_query, with_aliases=False)

        dbtype = self._db.get_type()

        return """
            WITH RECURSIVE nums AS (
                SELECT %(start)s AS value UNION ALL SELECT %(value_incr)s FROM nums WHERE value < %(end)s
            )
            SELECT %(selection)s FROM (
                SELECT value AS start, %(value_incr)s AS end FROM nums
            ) AS _intervals JOIN (
                %(inner_query)s
            ) AS _main ON c0 < _intervals.end AND c1 >= _intervals.start
            GROUP BY %(group_by)s
            ORDER BY %(order)s
        """ % {
            "start": _FUNCTIONS_MAP[dbtype]["date"].format(start),
            "value_incr": _FUNCTIONS_MAP[dbtype]["add_date"].format("value", "1 %s" % _TIME_UNITS[step][1]),
            "end": _FUNCTIONS_MAP[dbtype]["sub_date"].format("TIMESTAMP '%s'" % end, "1 %s" % _TIME_UNITS[step][1]),
            "selection": ", ".join(outer_query.select),
            "inner_query": text_type(inner_query),
            "group_by": ", ".join(outer_query.group_by),
            "order": ", ".join(outer_query.order_by)
        }

    def _get_time_bounds(self, criteria):
        # Try finding the mainmenu criteria
        crit = criteria.flatten()
        if not crit or crit.operator != CriterionOperator.AND:
            raise CTETimeBoundsError()

        start = None
        end = None
        for operand in crit.operands:
            if operand.operator in (CriterionOperator.LOWER, CriterionOperator.LOWER_OR_EQUAL) and operand.left == self._time_paths[0]:
                end = operand.right
            elif operand.operator in (CriterionOperator.GREATER, CriterionOperator.GREATER_OR_EQUAL) and operand.left == self._time_paths[1]:
                start = operand.right

        if not start or not end:
            raise CTETimeBoundsError()

        return start, end

    def _get_primary_paths(self):
        # FIXME: take the whole pkey into account
        paths = {}
        for table in self._tables:
            if table.pkey:
                paths[table] = self._reverse_paths_map[(table, table.pkey[0])]

        return zip(*sorted(paths.items(), key=lambda x: self._tables.index(x[0])))

    def execute_delete(self, criteria, paths):
        """Delete objects from the database based on the provided criteria."""
        query = SQLQuery(self._get_base_table(paths))
        query.where = self._process_criteria(criteria, query, with_aliases=False)

        if len(query.joined) == 1:
            return self._db.query("DELETE FROM %s" % query.base_table + (" WHERE %s" % query.where if query.where else ""))

        paths = [self._reverse_paths_map[(query.base_table, p)] for p in query.base_table.pkey]
        path_objects = [SelectionObject(_Path(p)) for p in paths]
        select_query = self.build_query(path_objects, criteria, 0, -1, 0)

        # We suppose other tables to be taken care of by cascading delete
        # An additional SELECT is necessary for MySQL
        # FIXME: this is not SQLite-compatible
        self._db.query("DELETE FROM %s WHERE (%s) IN (SELECT * FROM (%s) AS dummy)" %
                       (query.base_table, ", ".join(query.base_table.pkey), select_query))

    def _browse_data(self, data):
        tables = {}
        for path, value in data:
            table, attr = self._get_field_info(path.object)
            tables.setdefault(table, {})[attr] = value

        return tables

    def execute_insert(self, data, criteria):
        """Insert a single object into the database."""
        ret = None
        ids = {}
        data = self._browse_data(data)

        if criteria:
            tables, paths = self._get_primary_paths()
            results = env.dataprovider.query(paths, criteria)
            if not results:
                return

            for i, table in enumerate(tables):
                if results[0][i] is not None:
                    ids[table] = results[0][i]

        for table, values in sorted(data.items(), key=lambda x: self._tables.index(x[0])):
            # Handle foreign keys
            autoincr = False
            for t, rel in self._relations.get(table, {}).items():
                # Only single-field primary keys supported
                pk = rel["src_pkey"][0]
                if t in ids:
                    values[pk] = ids[t]
                elif pk in values:
                    ids[t] = values[pk]
                else:
                    autoincr = True

            self._db.query("INSERT INTO %s (%s) VALUES %%s" % (table, ", ".join(values.keys())), values.values())
            if autoincr:
                ids[table] = self._db.get_last_insert_ident()

            if ret is None and table in ids:
                ret = ids[table]

        return ret

    def execute_update(self, data, criteria):
        """Update root objects matching the provided criteria in database."""
        paths, values = zip(*data)
        query = SQLQuery(self._get_base_table(paths))

        self._process_selection(paths, query, with_aliases=False)
        query.where = self._process_criteria(criteria, query, with_aliases=False)

        if len(query.joined) == 1:
            assign = ", ".join("%s = %s" % (query.select[i], self._db.escape(value)) for i, value in enumerate(values))
            update_query = "UPDATE %s SET %s" % (query.base_table, assign)
            if query.where:
                update_query += " WHERE %s" % query.where
            self._db.query(update_query)
            return

        ids = {}
        tables, paths = self._get_primary_paths()

        for row in env.dataprovider.query(paths, criteria):
            for i, table in enumerate(tables):
                ids.setdefault(table, set()).add(row[i])

        for table, values in self._browse_data(data).items():
            if not ids.get(table):
                continue

            # FIXME: take the whole pkey into account
            assign = ", ".join("%s = %s" % (column, self._db.escape(value)) for column, value in values.items())
            self._db.query("UPDATE %s SET %s WHERE (%s) IN %%s" % (table, assign, table.pkey[0]), ids[table])
