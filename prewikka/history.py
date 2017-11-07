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

from hashlib import md5

from prewikka import crontab, database, log, utils, hookmanager

logger = log.getLogger(__name__)


class HistoryDatabase(database.DatabaseHelper):
    def __init__(self):
        database.DatabaseHelper.__init__(self)

    def init(self):
        # This should not be executed if env.db fails to initialize
        crontab.schedule("search_history", N_("Search history deletion"), "0 * * * *", _regfunc=history._history_cron, enabled=True)

    def create(self, user, form):
        return utils.AttrObj(
            content=self.get_queries(user, form),
            url={
                "save": url_for('BaseView.history_save', form=form),
                "delete": url_for('BaseView.history_delete', form=form),
                "get": url_for('BaseView.history_get', form=form)
            }
        )

    def _where(self, user=True, form=True, query_hash=True):
        where = []

        if user:
            where.append("userid = %(user)s")
        if form:
            where.append("formid = %(form)s")
        if query_hash:
            where.append("query_hash = %(query_hash)s")

        return "" if not where else " WHERE %s" % " AND ".join(where)

    def get_queries(self, user, form):
        query = ("SELECT query FROM Prewikka_History_Query %s ORDER BY timestamp DESC" %
                 self._where(query_hash=False))

        return [row[0] for row in self.query(query, user=user.id, form=form)]

    def save(self, user, form, query):
        query_hash = md5(query.encode("utf8")).hexdigest()
        rows = [(user.id, form, query, query_hash, utils.timeutil.utcnow())]
        self.upsert("Prewikka_History_Query", ("userid", "formid", "query", "query_hash", "timestamp"), rows, pkey=("userid", "formid", "query_hash"))

        logger.info("Query saved: %s by %s on form %s", query, user.name, form)

    def delete(self, user, form, query=False):
        query_hash = md5(query.encode("utf8")).hexdigest() if query else False
        self.query("DELETE FROM Prewikka_History_Query" + self._where(query_hash=query_hash), user=user.id, query_hash=query_hash, form=form)

        logger.info("Query deleted: %s by %s on form %s", query or "all queries", user.name, form)

    @hookmanager.register("HOOK_USER_DELETE")
    def _clear_on_delete(self, user):
        self.query("DELETE FROM Prewikka_History_Query " + self._where(query_hash=False, form=False), user=user.id)

    def _history_cron(self, job):
        config = env.config.cron.get_instance_by_name("search_history")
        if config is None:
            return

        size = int(config.get("size", 10))
        query = "SELECT userid, formid, COUNT(query) FROM Prewikka_History_Query GROUP BY userid, formid"
        for userid, formid, count in self.query(query):
            if int(count) <= size:
                continue

            rows = self.query("SELECT query FROM Prewikka_History_Query WHERE userid = %s AND formid = %s "
                              "ORDER BY timestamp DESC LIMIT %s", userid, formid, size)
            self.query("DELETE FROM Prewikka_History_Query WHERE userid = %s AND formid = %s AND query NOT IN %s",
                       userid, formid, [row[0] for row in rows])


history = HistoryDatabase()

init = history.init
create = history.create
delete = history.delete
get = history.get_queries
save = history.save
