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
import os.path
import glob

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



class my_install(install):
    def run(self):
        site = os.path.abspath(self.prefix + "/share/prewikka/site/")
        database = os.path.abspath(self.prefix + "/share/prewikka/database/")
        conf = os.path.abspath(self.prefix + "/share/prewikka/conf/")
        f = open("prewikka/siteconfig.py", "w")
        print >> f, "site = '%s'" % site
        print >> f, "database = '%s'" % database
        print >> f, "conf = '%s'" % conf
        f.close()
        install.run(self)



setup(name="Prewikka",
      version="0.9.0",
      packages=[ 'prewikka', 'prewikka.views', 'prewikka.templates',
                 'prewikka.modules',
                 'prewikka.modules.log', 'prewikka.modules.log.stderr',
                 'prewikka.modules.auth', 'prewikka.modules.auth.loginpassword' ],
      data_files=[ ("share/prewikka/site", [ "index.py" ]),
                   ("share/prewikka/site/images", glob.glob("images/*.gif") + glob.glob("images/*.png")),
                   ("share/prewikka/site/css", glob.glob("css/*.css")),
                   ("share/prewikka/site/js", glob.glob("js/*.js")),
                   ("share/prewikka/database", glob.glob("*.sql")),
                   ("share/prewikka/conf", glob.glob("*.conf")) ],
      scripts=[ "prewikka-database-create.py", "prewikka-httpd.py" ],
      cmdclass={ 'build_py': my_build_py,
                 'install': my_install })
      
