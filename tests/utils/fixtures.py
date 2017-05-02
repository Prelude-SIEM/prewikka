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
Fixture utils for prewikka tests suite.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import shutil
import sys

from prewikka.utils import json
from prewikka.web.request import Request as InitialRequest


class FakeInitialRequest(InitialRequest):
    """
    Fake InitialRequest to load Prewikka out of browser.

    We just fake some methods to prevent exceptions during tests.
    """
    script_name = 'test_script'
    method = 'GET'
    headers = {}
    port = None

    def __init__(self, path):
        super(FakeInitialRequest, self).__init__(path)

    def get_script_name(self):
        """
        Fake script name.

        :return: script name
        :rtype: str
        """
        return self.script_name

    def get_remote_addr(self):
        return '127.0.0.1'

    def get_baseurl(self):
        return ''

    def get_cookie(self):
        return

    def get_raw_uri(self, include_qs=False):
        return

    def get_remote_port(self):
        return self.port

    def send_headers(self, headers=None, code=200, status_text=None):
        return

    def write(self, data):
        return

    @staticmethod
    def get_uri():
        """
        Fake get_uri() for test suite.
        """
        return ''

    def send_stream(self, data, event=None, evid=None, retry=None, sync=False):
        """
        Used to print message in stdout.
        """
        if len(data) == 0:
            return

        sys.stdout.write('env.web.request.send_stream():\n')

        try:
            for key, value in json.loads(data).iteritems():
                sys.stdout.write('    %s: %s\n' % (key, value))
        except ValueError:
            sys.stdout.write('    %s\n' % data)


def clean_directory(path):
    """
    Delete all content in a directory.

    :param str path: the path of directory to delete
    """
    shutil.rmtree(path)
    os.makedirs(path)


def load_view_for_fixtures(name):
    """
    Function used in fixtures to load a view.

    :param name: name of the view.
    :return: The view object.
    :rtype: prewikka.view.View
    """
    view = env.viewmanager.getView(name)

    assert view

    view.__init__()  # init view to load hooks
    env.request.parameters = view.view_parameters(view)
    env.request.view = view

    return view
