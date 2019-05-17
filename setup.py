#!/usr/bin/env python

# Copyright (C) 2005-2019 CS-SI. All Rights Reserved.
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
import sys
import tempfile

from setuptools import Command, setup, find_packages
from setuptools.command.test import test as TestCommand
from distutils.dist import Distribution
from distutils.command.install import install
from distutils.dep_util import newer
from distutils.command.build import build as _build


LIBPRELUDE_REQUIRED_VERSION = "5.0.0"
LIBPRELUDEDB_REQUIRED_VERSION = "5.0.0"


def init_siteconfig(conf_prefix, data_prefix):
    """
    Initialize configuration file (prewikka/siteconfig.py).

    :param str conf_prefix: configuration path
    :param str data_prefix: data path
    """
    configuration = (
        ('tmp_dir', os.path.join(tempfile.gettempdir(), 'prewikka')),
        ('conf_dir', os.path.abspath(conf_prefix)),
        ('data_dir', os.path.abspath(data_prefix)),
        ('libprelude_required_version', LIBPRELUDE_REQUIRED_VERSION),
        ('libpreludedb_required_version', LIBPRELUDEDB_REQUIRED_VERSION),
    )

    with open('prewikka/siteconfig.py', 'w') as config_file:
        for option, value in configuration:
            config_file.write("%s = '%s'\n" % (option, value))


class MyDistribution(Distribution):
    def __init__(self, attrs):
        try:
            os.remove("prewikka/siteconfig.py")
        except:
            pass

        self.conf_files = []
        self.closed_source = os.path.exists("PKG-INFO")
        Distribution.__init__(self, attrs)


class my_install(install):
    def finalize_options(self):
        # if no prefix is given, configuration should go to /etc or in {prefix}/etc otherwise
        if self.prefix:
            self.conf_prefix = self.prefix + "/etc/prewikka"
            self.data_prefix = self.prefix + "/var/lib/prewikka"
        else:
            self.conf_prefix = "/etc/prewikka"
            self.data_prefix = "/var/lib/prewikka"

        install.finalize_options(self)

    def get_outputs(self):
        tmp = [self.conf_prefix + "/prewikka.conf"] + install.get_outputs(self)
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
        init_siteconfig(self.conf_prefix, self.data_prefix)
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


class PrewikkaTest(TestCommand):
    """
    Custom command for Prewikka test suite with pytest.

    Based on
    https://docs.pytest.org/en/2.7.3/goodpractises.html#integration-with-setuptools-test-commands
    """
    user_options = [
        ('pytest-args=', 'a', 'Arguments to pass to pytest')
    ]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        init_siteconfig('conf', 'tests/downloads')

        import pytest  # import here, cause outside the eggs aren't loaded

        if not isinstance(self.pytest_args, list):
            self.pytest_args = self.pytest_args.split()

        errno = pytest.main(self.pytest_args + ['tests'])
        sys.exit(errno)


class PrewikkaCoverage(Command):
    """
    Coverage command.
    """
    user_options = [
        ('run-args=', None, 'Arguments to pass to coverage during run'),
        ('report-args=', None, 'Arguments to pass to coverage for report')
    ]
    description = 'Run tests with coverage.'

    def initialize_options(self):
        self.run_args = []
        self.report_args = []

    def finalize_options(self):
        pass

    def run(self):
        subprocess.call(['coverage', 'run', 'setup.py', 'test'] + self.run_args)
        subprocess.call(['coverage', 'report'] + self.report_args)


setup(
    name="prewikka",
    version="5.1.0alpha6",
    maintainer="Prelude Team",
    maintainer_email="support.prelude@c-s.fr",
    url="http://www.prelude-siem.com",
    packages=find_packages(exclude=[
        'tests',
        'tests.*'
    ]),
    setup_requires=[
        'Babel'
    ],
    entry_points={
        'prewikka.renderer.backend': [
            'ChartJS = prewikka.renderer.chartjs:ChartJSPlugin',
        ],
        'prewikka.renderer.type': [
            'ChartJSBar = prewikka.renderer.chartjs.bar:ChartJSBarPlugin',
            'ChartJSTimebar = prewikka.renderer.chartjs.timeline:ChartJSTimebarPlugin',
        ],
        'prewikka.dataprovider.backend': [
            'IDMEFAlert = prewikka.dataprovider.plugins.idmef:IDMEFAlertPlugin',
            'IDMEFHeartbeat = prewikka.dataprovider.plugins.idmef:IDMEFHeartbeatPlugin',
        ],
        'prewikka.dataprovider.type': [
            'alert = prewikka.dataprovider.idmef:IDMEFAlertProvider',
            'heartbeat = prewikka.dataprovider.idmef:IDMEFHeartbeatProvider',
        ],
        'prewikka.plugins': [],
        'prewikka.session': [
            'Anonymous = prewikka.session.anonymous:AnonymousSession',
        ],
        'prewikka.auth': [],
        'prewikka.views': [
            'About = prewikka.views.about:About',
            'AboutPlugin = prewikka.views.aboutplugin:AboutPlugin',
            'AgentPlugin = prewikka.views.agents:AgentPlugin',
            'AlertDataSearch = prewikka.views.datasearch.alert:AlertDataSearch',
            'CrontabView = prewikka.views.crontab:CrontabView',
            'FilterView = prewikka.views.filter.filter:FilterView',
            'HeartbeatDataSearch = prewikka.views.datasearch.heartbeat:HeartbeatDataSearch',
            "IDMEFnav = prewikka.views.idmefnav:IDMEFNav",
            'MessageSummary = prewikka.views.messagesummary:MessageSummary',
            'ThreatDataSearch = prewikka.views.datasearch.threat:ThreatDataSearch',
            'UserManagement = prewikka.views.usermanagement:UserManagement',
            'Warning = prewikka.plugins.warning:Warning',
        ],
        'prewikka.updatedb': [
            'prewikka = prewikka.sql',
            'prewikka.views.filter.filter = prewikka.views.filter.sql'
        ]
    },
    package_data={
        '': [
            "htdocs/css/*.*",
            "htdocs/css/themes/*.css",
            "htdocs/css/images/*.*",
            "htdocs/fonts/*.*",
            "htdocs/images/*.*",
            "htdocs/js/*.js",
            "htdocs/js/locales/*.js",
            "htdocs/js/locales/*/*.js",
            "htdocs/js/*.map",
            "htdocs/js/locales/*.map",
            "locale/*.pot",
            "locale/*/LC_MESSAGES/*.mo",
            "sql/*.py",
            "templates/*.mak"
        ],
        'prewikka.renderer.chartjs': [
            "htdocs/js/*.js"
        ],
        'prewikka.views.about': [
            "htdocs/css/*.css",
            "htdocs/images/*.png"
        ],
        'prewikka.views.aboutplugin': [
            "htdocs/css/*.css"
        ],
        "prewikka.views.idmefnav": [
            "htdocs/yaml/*.yml",
            "htdocs/graph/*",
        ],
    },
    scripts=[
        "scripts/prewikka-crontab",
        "scripts/prewikka-httpd"
    ],
    conf_files=[
        "conf/prewikka.conf",
        "conf/menu.yml"
    ],
    cmdclass={
        'build': build,
        'build_custom': build_custom,
        'coverage': PrewikkaCoverage,
        'install': my_install,
        'test': PrewikkaTest,
    },
    tests_require=[
        'pytest'
    ],
    distclass=MyDistribution,
    message_extractors={
        'scripts': [
            ('prewikka-httpd', 'python', None),
            ('prewikka-crontab', 'python', None)
        ],
        'prewikka': [
            ('**.py', 'python', None),
            ('**/templates/*.mak', 'mako', None)
        ]
    }
)
