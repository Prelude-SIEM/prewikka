#!/usr/bin/python

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
from distutils.core import Command

from Cheetah.CheetahWrapper import CheetahWrapper


class my_build_py(build_py):
    def build_templates(self):
        cheetah = CheetahWrapper()
        
        for package in self.packages:
            package_dir = self.get_package_dir(package)
            templates = glob.glob(package_dir + '/*.tmpl')
            for template in templates:
                compiled = self.build_lib + "/" + template.replace(".tmpl", ".py")
                if os.path.exists(compiled):
                    template_stat = os.stat(template)
                    compiled_stat = os.stat(compiled)
                    if compiled_stat.st_mtime > template_stat.st_mtime:
                        continue
                argv = [ sys.argv[0], "compile", "--odir", self.build_lib, "--nobackup", template ]
                cheetah.main(argv)
    
    def build_packages(self):
        self.build_templates()
        build_py.build_packages(self)



class MyDistribution(Distribution):
    def __init__(self, attrs):
        self.conf_files = [ ]
        Distribution.__init__(self, attrs)



class my_install(install):
    def finalize_options(self):
        ### if no prefix is given, configuration should go to /etc or in {prefix}/etc otherwise
        if self.prefix:
            self.conf_prefix = self.prefix + "/etc/prewikka"
        else:
            self.conf_prefix = "/etc/prewikka"

        install.finalize_options(self)

    def install_conf(self):
        self.mkpath(self.conf_prefix)
        for file in self.distribution.conf_files:
            dest = self.conf_prefix + "/" + os.path.basename(file)
            if os.path.exists(dest):
                dest += "-dist"
            self.copy_file(file, dest)
            
    def init_siteconfig(self):
        config = open("prewikka/siteconfig.py", "w")
        print >> config, "htdocs = '%s'" % (self.prefix + "/share/prewikka/htdocs/")
        print >> config, "database = '%s'" % (self.prefix + "/share/prewikka/database/")
        print >> config, "conf = '%s'" % (self.conf_prefix + "/")
        config.close()
        
    def run(self):
        self.install_conf()
        self.init_siteconfig()
        install.run(self)
        if not self.dry_run:
            for filename in self.get_outputs():
                if filename.find(".conf"):
                    continue
                mode = os.stat(filename)[stat.ST_MODE]
                mode |= 044
                if mode & 0100:
                    mode |= 011
                os.chmod(filename, mode)



setup(name="Prewikka",
      version="0.9.0-rc2",
      packages=[ 'prewikka', 'prewikka.views', 'prewikka.templates',
                 'prewikka.modules',
                 'prewikka.modules.log', 'prewikka.modules.log.stderr',
                 'prewikka.modules.auth', 'prewikka.modules.auth.loginpassword' ],
      data_files=[ ("share/prewikka/cgi-bin", [ "cgi-bin/prewikka.cgi" ]),
                   ("share/prewikka/htdocs/images", glob.glob("htdocs/images/*.gif") + glob.glob("htdocs/images/*.png")),
                   ("share/prewikka/htdocs/css", glob.glob("htdocs/css/*.css")),
                   ("share/prewikka/htdocs/js", glob.glob("htdocs/js/*.js")),
                   ("share/prewikka/database", glob.glob("database/*.sql")) ],
      scripts=[ "scripts/prewikka-httpd.py" ],
      conf_files=[ "conf/prewikka.conf" ],
      cmdclass={ 'build_py': my_build_py,
                 'install': my_install },
      distclass=MyDistribution)
