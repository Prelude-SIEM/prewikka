# Copyright (C) 2004,2005 PreludeIDS Technologies. All Rights Reserved.
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


import os

from prewikka import view, User



class HostCommandParameters(view.RelativeViewParameters):
    def register(self):
        view.RelativeViewParameters.register(self)
        self.mandatory("host", str)



class Command(view.View):
    view_template = "Command"



class HostCommand(Command):
    view_parameters = HostCommandParameters
    view_permissions = [ User.PERM_COMMAND ]

    def render(self):
        command = self.env.host_commands[self.command]
        stdin, stdout = os.popen2((command, self.parameters["host"]))
        output = stdout.read()
        output = output.replace(" ", "&nbsp;").replace("\n", "<br/>\n")
        self.dataset["command_output"] = output



class Whois(HostCommand):
    view_name = "whois"
    command = "whois"



class Traceroute(HostCommand):
    view_name = "traceroute"
    command = "traceroute"
