#!/usr/bin/env python

# Copyright (C) 2005 PreludeIDS Technologies. All Rights Reserved.
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

import sys
import os, os.path
import stat
import glob

from distutils.dist import Distribution
from distutils.core import setup
from distutils.command.build import build
from distutils.command.build_py import build_py
from distutils.command.install import install
from distutils.command.install_scripts import install_scripts
from distutils.command.install_data import install_data
from distutils.core import Command

from Cheetah.CheetahWrapper import CheetahWrapper


PREWIKKA_VERSION = "0.9.16"
LIBPRELUDE_REQUIRED_VERSION = "0.9.23"
LIBPRELUDEDB_REQUIRED_VERSION = "0.9.12"

from fnmatch import fnmatch
from distutils.dep_util import newer

def listfiles(*dirs):
    dir, pattern = os.path.split(os.path.join(*dirs))
    return [os.path.join(dir, filename)
            for filename in os.listdir(os.path.abspath(dir))
                if filename[0] != '.' and fnmatch(filename, pattern)]

class my_install_data(install_data):
    def run(self):
        self.data_files.extend(self._compile_po_files())
        install_data.run(self)

    def _compile_po_files(self):
        data_files = []

        for po in listfiles("po", "*.po"):
            lang = os.path.basename(po[:-3])
            mo = os.path.join("locale", lang, "LC_MESSAGES", "prewikka.mo")

            if not os.path.exists(mo) or newer(po, mo):
                directory = os.path.dirname(mo)
                if not os.path.exists(directory):
                    print "creating %s" % directory
                    os.makedirs(directory)

                cmd = 'msgfmt -o %s %s' % (mo, po)
                print "compiling %s -> %s" % (po, mo)
                if os.system(cmd) != 0:
                    raise SystemExit("Error while running msgfmt")

            dest = os.path.dirname(os.path.join('share', mo))
            data_files.append((dest, [mo]))

        return data_files



class my_build_py(build_py):
    def finalize_options(self):
        build_py.finalize_options(self)
        self.outfiles = [ ]

    def get_outputs(self, *args, **kwargs):
        return self.outfiles + apply(build_py.get_outputs, (self, ) + args, kwargs)

    def build_templates(self):
        cheetah = CheetahWrapper()
        argbkp = sys.argv[0][:]

        for package in self.packages:
            package_dir = self.get_package_dir(package)
            templates = glob.glob(package_dir + '/*.tmpl')

            for template in templates:
                compiled = self.build_lib + "/" + template.replace(".tmpl", ".py")
                self.outfiles.append(compiled)
                if os.path.exists(compiled):
                    template_stat = os.stat(template)
                    compiled_stat = os.stat(compiled)
                    if compiled_stat.st_mtime > template_stat.st_mtime:
                        continue

                argv = [ sys.argv[0], "compile", "--nobackup", template ]
                cheetah.main(argv)
                sys.argv[0] = argbkp

    def run(self):
        self.build_templates()
        build_py.run(self)



class MyDistribution(Distribution):
    def __init__(self, attrs):
        try:
            os.remove("prewikka/siteconfig.py")
        except:
            pass

        self.conf_files = [ ]
        Distribution.__init__(self, attrs)


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

        cgi_dir = os.path.join(self.install_data, 'share', 'prewikka', 'cgi-bin')
        if not os.path.exists(cgi_dir):
            os.makedirs(cgi_dir)

        ofile, copied = self.copy_file(os.path.join(self.build_dir, 'prewikka.cgi'), cgi_dir)
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

    def install_conf(self):
        self.mkpath((self.root or "") + self.conf_prefix)
        for file in self.distribution.conf_files:
            dest = (self.root or "") + self.conf_prefix + "/" + os.path.basename(file)
            if os.path.exists(dest):
                dest += "-dist"
            self.copy_file(file, dest)

    def init_siteconfig(self):
        config = open("prewikka/siteconfig.py", "w")
        print >> config, "htdocs_dir = '%s'" % os.path.abspath((self.prefix + "/share/prewikka/htdocs"))
        print >> config, "database_dir = '%s'" % os.path.abspath((self.prefix + "/share/prewikka/database"))
        print >> config, "locale_dir = '%s'" % os.path.abspath((self.prefix + "/share/locale"))
        print >> config, "conf_dir = '%s'" % os.path.abspath((self.conf_prefix))
        print >> config, "version = '%s'" % PREWIKKA_VERSION
        print >> config, "libprelude_required_version = '%s'" % LIBPRELUDE_REQUIRED_VERSION
        print >> config, "libpreludedb_required_version = '%s'" % LIBPRELUDEDB_REQUIRED_VERSION
        config.close()

    def run(self):
        os.umask(022)
        self.install_conf()
        self.init_siteconfig()
        install.run(self)

        for dir in ("/",
                    "share/prewikka",
                    "share/prewikka/htdocs",
                    "share/prewikka/htdocs/images", "share/prewikka/htdocs/js", "share/prewikka/htdocs/css",
                    "share/prewikka/database", "share/prewikka/cgi-bin"):
            os.chmod((self.root or "") + self.prefix + "/" + dir, 0755)
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


sqlite = open("database/sqlite.sql", "w")
for line in os.popen("database/mysql2sqlite.sh database/mysql.sql"):
    print >> sqlite, line.rstrip()
sqlite.close()

pgsql = open("database/pgsql.sql", "w")
for line in os.popen("database/mysql2pgsql.sh database/mysql.sql"):
    print >> pgsql, line.rstrip()
pgsql.close()


setup(name="prewikka",
      version=PREWIKKA_VERSION,
      maintainer = "Yoann Vandoorselaere",
      maintainer_email = "yoann.v@prelude-ids.com",
      url = "http://www.prelude-ids.org",
      packages=[ 'prewikka', 'prewikka.views', 'prewikka.templates',
                 'prewikka.modules',
                 'prewikka.modules.auth', 'prewikka.modules.auth.anonymous', 'prewikka.modules.auth.loginpassword', 'prewikka.modules.auth.cgi' ],
      data_files=[ ("share/prewikka/cgi-bin", [ "cgi-bin/prewikka.cgi" ]),
                   ("share/prewikka/htdocs/images", glob.glob("htdocs/images/*")),
                   ("share/prewikka/htdocs/css", glob.glob("htdocs/css/*.css")),
                   ("share/prewikka/htdocs/js", glob.glob("htdocs/js/*.js")),
                   ("share/prewikka/database", glob.glob("database/*.sql") + glob.glob("database/*.sh") )],
      scripts=[ "scripts/prewikka-httpd", "cgi-bin/prewikka.cgi" ],
      conf_files=[ "conf/prewikka.conf" ],
      cmdclass={ 'build_py': my_build_py,
                 'install': my_install,
                 'install_scripts': my_install_scripts,
                 'install_data': my_install_data },
      distclass=MyDistribution)
