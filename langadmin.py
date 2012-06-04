#!/usr/bin/env python
# Copyright (C) 2004,2005 by SICEm S.L.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.


"""
This script makes easy all the boring steps to use gettext with a python
application.

For localization you need to:

  1 Mark the strings in the source code as translatable
  2 Use xgettext to get a pot file from it
  3 Use a copy of this pot file for every language you want to have
  translations
  4 Translate these po files
  5 Use msgmerge every time you change the source code and the strings you
  need to translate change
  6 Generate the mo binary files for every po file you have

To use this script you need to:

  - have a directory where you put the po files: the PO_DIR
  - have a directory where you put the mo files: the LANG_DIR
  - choose a name for the pot file: the POT_FILE
  - choose a name for the mo files: the MO_FILE

Note that you have only one POT_FILE but you have one po file in the PO_DIR for
every language you have translations. Then you have a MO_FILE for every po file
and they are stored in LANG_DIR/lang/LC_MESSAGES/ where lang is the language
this MO_FILE belongs to.
"""

from distutils.dep_util import newer
from glob import glob
import os
from os.path import join, splitext, basename, exists, isdir
from optparse import OptionParser
import sys
from shutil import copyfile

class LangAdmin:

    def __init__(self, po_dir, pot_file, mo_file, lang_dir):
        # where to put the po files (one for each language)
        self.po_dir = po_dir

        # name of the pot (po template) file (it is stored in the cwd)        
        self.pot_file = pot_file
        
        # name of the mo file (one for each directory)
        self.mo_file = mo_file
        
        # name of the directory where the mo files are stored
        self.lang_dir = lang_dir
        
    def get_languages(self):
        """Gives a list of all the languages that have translation"""
        languages = []
        for lang in glob(join(self.po_dir, '*.po')):
            languages.append(splitext(basename(lang))[0])

        return languages

    def _list_files(self, directory, recurse=True, ext="py"):
        files = glob(join(directory, "*." + ext))
        if recurse:
            dirs = [join(directory, filename) for filename \
                    in os.listdir(directory)
                    if isdir(join(directory, filename))]
            for d in dirs:
                files += self._list_files(d, recurse, ext)
        return files

    def generate_pot_file(self, recurse=True, directories=[]):
        """Get all the python files in the directories parameter and create
        a pot file using xgettext. If the recurse parameter is True it search
        for more .py files in the subdirectories of the directories list
        """
        files = []
        for dirname in directories:
            files += self._list_files(dirname, recurse)

        cmd = 'xgettext --copyright-holder="CS-SI" -k_ -kN_ -o %s %s' % (self.pot_file, ' '.join(files))
        print cmd
        os.system(cmd)

    def add_language(self, lang):
        """Create another language by copying the self.pot_file into the
        self.po_dir using the lang parameter for its name. You need to fill at
        least the charset property of the prolog of this new file if you don't
        want the other commands to fail
        """
        if not exists(self.pot_file):
            print 'ERROR: You need to generate the pot file before adding '\
                  'any language.\n' \
                  'Use the command pot for that'
            sys.exit(1)
        copyfile(self.pot_file, join(self.po_dir, lang+'.po'))
        print 'Please fill the prolog information of the file', \
              join(self.po_dir, lang+'.po')

    def merge_translations(self):
        """Merge the new self.pot_file with the existing po files in the
        self.po_dir directory using the command msgmerge
        """
        for lang_file in glob(join(self.po_dir, '*.po')):
            cmd = 'msgmerge -U %s %s' % (lang_file, self.pot_file)
            print cmd
            os.system(cmd)

    def generate_mo_files(self, verbose=True):
        """For every po file in the self.po_dir directory generates a
        self.mo_file using msgfmt. It guess the language name from the po file
        and creates the directories needed under self.lang_dir to put the final
        self.mo_file in the right place
        """
        if not exists(self.lang_dir):
            os.mkdir(self.lang_dir)
        
        for lang in self.get_languages():
            src = join(self.po_dir, lang+'.po')
            dst = join(self.lang_dir, lang, 'LC_MESSAGES', self.mo_file)
            if not exists(join(self.lang_dir, lang, 'LC_MESSAGES')):
                if not exists(join(self.lang_dir, lang)):
                    os.mkdir(join(self.lang_dir, lang))
                os.mkdir(join(self.lang_dir, lang, 'LC_MESSAGES'))
       		
	    # Skip files which are not modified
            if not newer(src, dst):
                continue
            cmd = 'msgfmt -o %s %s' % (dst, src)
            if verbose:
                print 'running', cmd
            os.system(cmd)

if __name__ == '__main__':
    usage = """usage: %prog [options] command
    
    where command can be one of:

       list       List all the languages supported
       add LANG   Add the language LANG
       pot DIRS   Get the translatable strings for every file in DIRS that
                  is a .py file and creates the .pot file from them
       merge      Merge all the languages files with the POT file
       mo         Create a .mo file for every .po file and put it in the right
                  place"""
    
    parser = OptionParser(usage)
    parser.add_option('--po-dir',
                      action='store',
                      dest='po_dir',
                      default='po',
                      help='directory to store the po files')
    parser.add_option('--pot-file',
                      action='store',
                      dest='pot_file',
                      default='prewikka.pot',
                      help='name of the pot (po template) file. It is stored in the cwd')
    parser.add_option('--mo-file',
                      action='store',
                      dest='mo_file',
                      default='prewikka.mo',
                      help='name of the mo file')
    parser.add_option('--lang-dir',
                      action='store',
                      dest='lang_dir',
                      default='locale',
                      help='directory to store the mo files')

    options, args = parser.parse_args()

    if len(args) == 0:
        parser.print_help()
        print '\nERROR: You should provide one command'
        sys.exit(1)

    langadmin = LangAdmin(options.po_dir, options.pot_file, options.mo_file,
                          options.lang_dir)
    
    command = args.pop(0)
    if command == 'list':
        langs = langadmin.get_languages()
        print ' '.join(langs)

    elif command == 'pot':
        if len(args) == 0:
            parser.print_help()
            print '\nERROR: The pot command needs at least one directory to '\
            'look for .py files with translatable strings'
            sys.exit(1)
        langadmin.generate_pot_file(True, args)

    elif command == 'add':
        if len(args) != 1:
            parser.print_help()
            print '\nERROR: You need to specify one and only one language '\
                  'to add'
            sys.exit(1)
        langadmin.add_language(args[0])

    elif command == 'merge':
        langadmin.merge_translations()

    elif command == 'mo':
        langadmin.generate_mo_files()

    else:
        parser.print_help()
        print '\nERROR: Unknown command'
        sys.exit(1)
