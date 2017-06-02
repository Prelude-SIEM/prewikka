# Copyright (C) 2017 CS-SI. All Rights Reserved.
# Author: Camille Gardet <camille.gardet@c-s.fr>
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

from prewikka import database, log, utils, hookmanager

logger = log.getLogger(__name__)


class HistoryDatabase(database.DatabaseHelper):
    def __init__(self):
        database.DatabaseHelper.__init__(self)

    def create(self, user, form):
        return utils.AttrObj(
            content=self.get_queries(user, form),
            url={
                "save": url_for('BaseView.history_save', form=form),
                "delete": url_for('BaseView.history_delete', form=form),
                "get": url_for('BaseView.history_get', form=form)
            }
        )

    def _where(self, user=True, form=True, query=True):
        where = []

        if user:
            where.append("userid = %(user)s")
        if form:
            where.append("formid = %(form)s")
        if query:
            where.append("query = %(query)s")

        return "" if not where else " WHERE %s" % " AND ".join(where)

    def get_queries(self, user, form):
        query = ("SELECT query FROM Prewikka_History_Query %s ORDER BY timestamp DESC" %
                 self._where(query=False))

        return [row[0] for row in self.query(query, user=user.id, form=form)]

    def save(self, user, form, query):
        rows = [(user.id, form, query, utils.timeutil.utcnow())]
        self.upsert("Prewikka_History_Query", ("userid", "formid", "query", "timestamp"), rows, pkey=("userid", "formid", "query"))

        logger.info("Query saved: %s by %s on form %s", query, user.name, form)

    def delete(self, user, form, query=False):
        self.query("DELETE FROM Prewikka_History_Query" + self._where(query=query), user=user.id, query=query, form=form)

        logger.info("Query deleted: %s by %s on form %s", query or "all queries", user.name, form)

    @hookmanager.register("HOOK_USER_DELETE")
    def _clear_on_delete(self, user):
        self.query("DELETE FROM Prewikka_History_Query " + self._where(query=False, form=False), user=user.id)


history = HistoryDatabase()

create = history.create
delete = history.delete
get = history.get_queries
save = history.save
