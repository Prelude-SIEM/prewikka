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
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


import os, subprocess
from prewikka import view, User, utils

class Error(Exception):
    pass


class HostCommandParameters(view.RelativeViewParameters):
    def register(self):
        view.RelativeViewParameters.register(self)
        self.mandatory("host", str)
        self.mandatory("command", str)


class Command(view.View):
    view_name = "Command"
    view_template = "Command"
    view_permissions = [ User.PERM_COMMAND ]
    view_parameters = HostCommandParameters

    def render(self):
        cmd = self.parameters["command"]

        try:
            command = self.env.host_commands[cmd]
        except KeyError:
            raise Error(_("Attempt to execute unregistered command '%s'") % cmd)

        command = command.replace("$host", self.parameters["host"]).split(" ")

        output = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True).communicate()[0]
        output = utils.toUnicode(output)

        output = utils.escape_html_string(output).replace(" ", "&nbsp;").replace("\n", "<br/>")
        self.dataset["command_output"] = output


