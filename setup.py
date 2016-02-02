#!/usr/bin/env python

# Copyright (C) 2005-2015 CS-SI. All Rights Reserved.
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

import sys, re
import os, os.path
import stat, fnmatch
from glob import glob

from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

from distutils.dist import Distribution
from distutils.command.build import build
from distutils.command.build_py import build_py
from distutils.command.install import install
from distutils.command.install_scripts import install_scripts
from distutils.command.install_data import install_data
from distutils.command.sdist import sdist
from distutils.errors import *
from distutils import util

LIBPRELUDE_REQUIRED_VERSION = "1.2.6"
LIBPRELUDEDB_REQUIRED_VERSION = "1.2.6"

from distutils.dep_util import newer

def listfiles(*dirs):
    dir, pattern = os.path.split(os.path.join(*dirs))
    return [os.path.join(dir, filename)
            for filename in os.listdir(os.path.abspath(dir))
                if filename[0] != '.' and fnmatch.fnmatch(filename, pattern)]


def template_compile(input, output_dir):
    from Cheetah.CheetahWrapper import CheetahWrapper
    CheetahWrapper().main([ sys.argv[0], "compile", "--nobackup", input ])


class my_build_py(build_py):

    def _generic_compile(self, compile_fmt, template, outfile):
        if not os.path.exists(outfile) or any([newer(tmpl, outfile) for tmpl in template]):
            directory = os.path.dirname(outfile)
            if not os.path.exists(directory):
                print "creating %s" % directory
                os.makedirs(directory)

            cmd = compile_fmt % (template + (outfile,))
            print "compiling %s -> %s" % (template, outfile)
            if os.system(cmd) != 0:
                raise SystemExit("Error while running command")

    def _compile_po_files(self):
        for po in listfiles("po", "*.po"):
            lang = os.path.basename(po[:-3])
            mo = os.path.join(self.build_lib, "prewikka", "locale", lang, "LC_MESSAGES", "prewikka.mo")
            self._generic_compile("msgfmt %s -o %s", (po,), mo)


    def _compile_less_files(self):
        style = os.path.join("prewikka", "htdocs", "css", "style.less")

        for less in listfiles("themes", "*.less"):
            theme = os.path.basename(less[:-5])
            css = os.path.join(self.build_lib, "prewikka", "htdocs", "css", "themes", "%s.css" % theme)
            self._generic_compile("lesscpy -I %s %s > %s", (less, style), css)

    def initialize_options(self):
        build_py.initialize_options(self)

    def finalize_options(self):
        build_py.finalize_options(self)
        self.outfiles = [ ]

    def get_outputs(self, *args, **kwargs):
        return self.outfiles + apply(build_py.get_outputs, (self, ) + args, kwargs)

    def build_templates(self):
        for package in self.packages:
            package_dir = self.get_package_dir(package)
            templates = glob(package_dir + '/*.tmpl')
            for template in templates:
                compiled = self.build_lib + "/" + template.replace(".tmpl", ".py")
                self.outfiles.append(compiled)
                if os.path.exists(compiled):
                    template_stat = os.stat(template)
                    compiled_stat = os.stat(compiled)
                    if compiled_stat.st_mtime > template_stat.st_mtime:
                        continue
                template_compile(template, self.build_lib)

    def check_package(self, package, package_dir):
        return None

    def copy_file(self, infile, outfile, **kwargs):
        return apply(build_py.copy_file, (self, infile, outfile), kwargs)

    def get_module_outfile(self, dir, package, module):
        ret = build_py.get_module_outfile(self, dir, package, module)

        return ret

    def run(self):
        self._compile_po_files()
        self._compile_less_files()
        self.build_templates()
        build_py.run(self)



class MyDistribution(Distribution):
    def __init__(self, attrs):
        try:
            os.remove("prewikka/siteconfig.py")
        except:
            pass

        self.conf_files = [ ]
        self.closed_source = os.path.exists("PKG-INFO")
        Distribution.__init__(self, attrs)



class my_bdist(sdist):
    def copy_file(self, infile, outfile, **kwargs):
        if outfile[-5:] == ".tmpl":
            output_dir = os.path.split(outfile)[0]
            output_dir = output_dir[:output_dir.find(os.path.dirname(infile))]
            template_compile(infile, output_dir)
            outfile = output_dir + "/" + infile.replace(".tmpl", ".pyc")
        else:
            apply(sdist.copy_file, (self, infile, outfile), kwargs)

        if infile[:7] != "Cheetah" and outfile[-3:] == ".py":
            util.byte_compile([ outfile ])
            print "delete", outfile, "after byte compiling"
            os.remove(outfile)



class my_install_scripts (install_scripts):
    def initialize_options (self):
        install_scripts.initialize_options(self)
        self.install_data = None

    def finalize_options (self):
        install_scripts.finalize_options(self)
        self.set_undefined_options('install',
                                   ('install_data', 'install_data'))

    def run (self):
        if not self.skip_build:
            self.run_command('build_scripts')

        self.outfiles = []

        self.mkpath(os.path.normpath(self.install_dir))
        ofile, copied = self.copy_file(os.path.join(self.build_dir, 'prewikka-httpd'), self.install_dir)
        if copied:
            self.outfiles.append(ofile)

        share_dir = os.path.join(self.install_data, 'share', 'prewikka')
        if not os.path.exists(share_dir):
            os.makedirs(share_dir)

        ofile, copied = self.copy_file(os.path.join(self.build_dir, 'prewikka.wsgi'), share_dir)
        if copied:
            self.outfiles.append(ofile)


class my_install(install):
    def finalize_options(self):
        ### if no prefix is given, configuration should go to /etc or in {prefix}/etc otherwise
        if self.prefix:
            self.conf_prefix = self.prefix + "/etc/prewikka"
        else:
            self.conf_prefix = "/etc/prewikka"

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

    def init_siteconfig(self):
        config = open("prewikka/siteconfig.py", "w")
        print >> config, "conf_dir = '%s'" % os.path.abspath((self.conf_prefix))
        print >> config, "libprelude_required_version = '%s'" % LIBPRELUDE_REQUIRED_VERSION
        print >> config, "libpreludedb_required_version = '%s'" % LIBPRELUDEDB_REQUIRED_VERSION
        config.close()

    def run(self):
        os.umask(022)
        self.install_conf()
        self.init_siteconfig()
        install.run(self)

        os.chmod((self.root or "") + self.conf_prefix, 0755)

        if not self.dry_run:
            for filename in self.get_outputs():
                if filename.find(".conf") != -1:
                    continue
                mode = os.stat(filename)[stat.ST_MODE]
                mode |= 044
                if mode & 0100:
                    mode |= 011
                os.chmod(filename, mode)



exec(open('prewikka/version.py').read())

setup(name="prewikka",
      version=__version__,
      maintainer = "Equipe Prelude",
      maintainer_email = "support.prelude@c-s.fr",
      url = "http://www.prelude-siem.com",
      packages = find_packages(),
      entry_points = {
                'prewikka.renderer.backend': [
                ],

                'prewikka.renderer.type': [
                ],

                'prewikka.dataprovider.backend': [
                        'IDMEFAlert = prewikka.dataprovider.plugins.alert.idmef:IDMEFAlertPlugin',
                ],

                'prewikka.dataprovider.type': [
                        'Alert = prewikka.dataprovider.alert:AlertDataProvider',
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
                        'MessageSummary = prewikka.views.messagesummary:MessageSummary',
                        'MessageListing = prewikka.views.messagelisting:MessageListing',
                        'AgentPlugin = prewikka.views.agents:AgentPlugin',
                        'Filter = prewikka.views.filter:AlertFilterEdition',
                        'UserManagement = prewikka.views.usermanagement:UserManagement',
                        'Warning = prewikka.views.warning:Warning',
                ],
      },

      package_data= { '': ["htdocs/images/*.*",
                           "htdocs/js/*.js",
                           "htdocs/css/*.*", "htdocs/css/themes/*.*",
                           "htdocs/css/images/*.*", "htdocs/css/images/*.*",
                           "htdocs/fonts/*.*",
                           "locale/*.pot",
                           "locale/*/LC_MESSAGES/*.mo",
                           "sql/*.py"],
                      'prewikka.views.messagelisting': [ "htdocs/css/*.css", "htdocs/js/*.js" ],
                      'prewikka.views.messagesummary': [ "htdocs/css/*.css", "htdocs/js/*.js" ],
      },

      scripts=[ "scripts/prewikka-httpd", "scripts/prewikka.wsgi" ],
      conf_files=[ "conf/prewikka.conf" ],
      cmdclass={ 'build_py': my_build_py,
                 'install': my_install,
                 'install_scripts': my_install_scripts,
                 'my_bdist': my_bdist
      },
      distclass=MyDistribution)
