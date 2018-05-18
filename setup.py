#!/usr/bin/env python

# Copyright (C) 2005-2017 CS-SI. All Rights Reserved.
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

from glob import glob
import io
import os
import stat
import subprocess
import tempfile

from ez_setup import use_setuptools
use_setuptools()

from setuptools import Command, setup, find_packages
from distutils.dist import Distribution
from distutils.command.install import install
from distutils.dep_util import newer
from distutils.command.build import build as _build


LIBPRELUDE_REQUIRED_VERSION = "4.1.0"
LIBPRELUDEDB_REQUIRED_VERSION = "4.1.0"




class MyDistribution(Distribution):
    def __init__(self, attrs):
        try:
            os.remove("prewikka/siteconfig.py")
        except:
            pass

        self.conf_files = [ ]
        self.closed_source = os.path.exists("PKG-INFO")
        Distribution.__init__(self, attrs)



class my_install(install):
    def finalize_options(self):
        ### if no prefix is given, configuration should go to /etc or in {prefix}/etc otherwise
        if self.prefix:
            self.conf_prefix = self.prefix + "/etc/prewikka"
            self.data_prefix = self.prefix + "/var/lib/prewikka"
        else:
            self.conf_prefix = "/etc/prewikka"
            self.data_prefix = "/var/lib/prewikka"

        install.finalize_options(self)

    def get_outputs(self):
        tmp = [ self.conf_prefix + "/prewikka.conf" ] + install.get_outputs(self)
        return tmp

    def install_conf(self):
        self.mkpath((self.root or "") + self.conf_prefix)
        for file in self.distribution.conf_files:
            dest = (self.root or "") + self.conf_prefix + "/" + os.path.basename(file)
            if os.path.exists(dest):
                dest += "-dist"
            self.copy_file(file, dest)

    def create_datadir(self):
        self.mkpath((self.root or "") + self.data_prefix)

    def init_siteconfig(self):
        config = open("prewikka/siteconfig.py", "w")
        config.write("tmp_dir = '%s'\n" % (os.path.join(tempfile.gettempdir(), "prewikka")))
        config.write("conf_dir = '%s'\n" % (os.path.abspath(self.conf_prefix)))
        config.write("data_dir = '%s'\n" % (os.path.abspath(self.data_prefix)))
        config.write("libprelude_required_version = '%s'\n" % (LIBPRELUDE_REQUIRED_VERSION))
        config.write("libpreludedb_required_version = '%s'\n" % (LIBPRELUDEDB_REQUIRED_VERSION))
        config.close()

    def install_wsgi(self):
        share_dir = os.path.join(self.install_data, 'share', 'prewikka')
        if not os.path.exists(share_dir):
            os.makedirs(share_dir)

        ofile, copied = self.copy_file('scripts/prewikka.wsgi', share_dir)

    def run(self):
        os.umask(0o22)
        self.install_conf()
        self.install_wsgi()
        self.create_datadir()
        self.init_siteconfig()
        install.run(self)

        os.chmod((self.root or "") + self.conf_prefix, 0o755)

        if not self.dry_run:
            for filename in self.get_outputs():
                if filename.find(".conf") != -1:
                    continue
                mode = os.stat(filename)[stat.ST_MODE]
                mode |= 0o44
                if mode & 0o100:
                    mode |= 0o11
                os.chmod(filename, mode)


class build(_build):
    sub_commands = [('compile_catalog', None), ('build_custom', None)] + _build.sub_commands


class build_custom(Command):
    @staticmethod
    def _need_compile(template, outfile):
        if os.path.exists(outfile) and not any(newer(tmpl, outfile) for tmpl in template):
            return False

        directory = os.path.dirname(outfile)
        if not os.path.exists(directory):
            print("creating %s" % directory)
            os.makedirs(directory)

        print("compiling %s -> %s" % (template, outfile))
        return True

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        style = os.path.join("prewikka", "htdocs", "css", "style.less")

        for less in glob("themes/*.less"):
            css = os.path.join("prewikka", "htdocs", "css", "themes", "%s.css" % os.path.basename(less[:-5]))
            if self._need_compile([less, style], css):
                io.open(css, "wb").write(subprocess.check_output(["lesscpy", "-I", less, style]))



setup(name="prewikka",
      version="4.1.10",
      maintainer = "Prelude Team",
      maintainer_email = "support.prelude@c-s.fr",
      url = "http://www.prelude-siem.com",
      packages = find_packages(),
      setup_requires=['Babel'],
      entry_points = {
                'prewikka.renderer.backend': [
                ],

                'prewikka.renderer.type': [
                ],

                'prewikka.dataprovider.backend': [
                        'IDMEFAlert = prewikka.dataprovider.plugins.idmef:IDMEFAlertPlugin',
                        'IDMEFHeartbeat = prewikka.dataprovider.plugins.idmef:IDMEFHeartbeatPlugin',
                ],

                'prewikka.dataprovider.type': [
                        'alert = prewikka.dataprovider.idmef:IDMEFAlertProvider',
                        'heartbeat = prewikka.dataprovider.idmef:IDMEFHeartbeatProvider',
                ],

                'prewikka.plugins': [
                ],

                'prewikka.session': [
                        'Anonymous = prewikka.session.anonymous:AnonymousSession',
                ],

                'prewikka.auth': [
                ],

                'prewikka.views': [
                        'About = prewikka.views.about:About',
                        'AboutPlugin = prewikka.views.aboutplugin:AboutPlugin',
                        'CrontabView = prewikka.views.crontab:CrontabView',
                        'MessageSummary = prewikka.views.messagesummary:MessageSummary',
                        'MessageListing = prewikka.views.messagelisting:MessageListing',
                        'AgentPlugin = prewikka.views.agents:AgentPlugin',
                        'FilterView = prewikka.views.filter.filter:FilterView',
                        'UserManagement = prewikka.views.usermanagement:UserManagement',
                        'Warning = prewikka.plugins.warning:Warning',
                ],

                'prewikka.updatedb': [
                        'prewikka = prewikka.sql',
                        'prewikka.views.filter.filter = prewikka.views.filter.sql'
                ]

      },

      package_data= { '': ["htdocs/images/*.*",
                           "htdocs/js/*.js", "htdocs/js/locales/*.js", "htdocs/js/*.map", "htdocs/js/locales/*.map",
                           "htdocs/css/*.*", "htdocs/css/themes/*.css",
                           "htdocs/css/images/*.*", "htdocs/css/images/*.*",
                           "htdocs/fonts/*.*",
                           "locale/*.pot", "locale/*/LC_MESSAGES/*.mo",
                           "sql/*.py",
                           "*.mak", "templates/*.mak"],
                      'prewikka.views.about': ["htdocs/css/*.css", "htdocs/images/*.png"],
                      'prewikka.views.aboutplugin': ["htdocs/css/*.css"],
                      'prewikka.views.messagelisting': [ "htdocs/css/*.css", "htdocs/js/*.js" ],
      },

      scripts=[ "scripts/prewikka-crontab", "scripts/prewikka-httpd" ],
      conf_files=[ "conf/prewikka.conf", "conf/menu.yml" ],
      cmdclass={ 'build': build,
                 'build_custom': build_custom,
                 'install': my_install },
      distclass=MyDistribution,
      message_extractors={
          'prewikka': [('**.py', 'python', None), ('**/templates/*.mak', 'mako', None)]
      })
