#!/usr/bin/python
# encoding=UTF-8

# Copyright © 2009-2015 Jakub Wilk <jwilk@jwilk.net>
#
# This file is part of didjvu.
#
# didjvu is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# didjvu is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.

'''
*didjvu* uses the `Gamera <http://gamera.informatik.hsnr.de/>`_ framework to
separate foreground/background layers, which it can then encode into a `DjVu
<http://djvu.org/>`_ file.
'''

from __future__ import with_statement
# Let's keep this __future__ import here, even though Python 2.5 is no longer
# supported, so that people running setup.py against the unsupported version
# get a nice error message instead of SyntaxError.

classifiers = '''
Development Status :: 4 - Beta
Environment :: Console
Intended Audience :: End Users/Desktop
License :: OSI Approved :: GNU General Public License (GPL)
Operating System :: OS Independent
Programming Language :: Python
Programming Language :: Python :: 2
Programming Language :: Python :: 2.6
Programming Language :: Python :: 2.7
Topic :: Text Processing
Topic :: Multimedia :: Graphics
'''.strip().splitlines()

import glob
import os
import re

import distutils.command
import distutils.core
from distutils.command.build import build as distutils_build
from distutils.command.clean import clean as distutils_clean
from distutils.command.sdist import sdist as distutils_sdist

from lib.version import __version__

class test(distutils.core.Command):

    description = 'run tests'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import nose
        nose.main(argv=['nosetests', '--verbose', 'tests'])

class build_doc(distutils_build):

    description = 'build documentation'

    _url_regex = re.compile(
        r'^(\\%https?://.*)',
        re.MULTILINE
    )

    _date_regex = re.compile(
        '"(?P<month>[0-9]{2})/(?P<day>[0-9]{2})/(?P<year>[0-9]{4})"'
    )

    def build_man(self, manname, commandline):
        self.spawn(commandline)
        with open(manname, 'r+') as file:
            contents = file.read()
            # Format URLs consistently:
            contents = self._url_regex.sub(
                lambda m: r'\m[blue]\fI{0}\fR\m[]'.format(*m.groups()),
                contents,
            )
            # Use RFC 3339 date format:
            contents = self._date_regex.sub(
                lambda m: '{year}-{month}-{day}'.format(**m.groupdict()),
                contents
            )
            file.seek(0)
            file.truncate()
            file.write(contents)

    def run(self):
        for xmlname in glob.iglob(os.path.join('doc', '*.xml')):
            manname = os.path.splitext(xmlname)[0] + '.1'
            command = [
                'xsltproc', '--nonet',
                '--param', 'man.authors.section.enabled', '0',
                '--param', 'man.charmap.use.subset', '0',
                '--param', 'man.font.links', '"I"',
                '--output', 'doc/',
                'http://docbook.sourceforge.net/release/xsl/current/manpages/docbook.xsl',
                xmlname,
            ]
            self.make_file([xmlname], manname, self.build_man, [manname, command])

distutils_build.sub_commands[:0] = [('build_doc', None)]

class clean(distutils_clean):

    def run(self):
        distutils_clean.run(self)
        if not self.all:
            return
        for manname in glob.iglob(os.path.join('doc', '*.1')):
            with open(manname, 'r') as file:
                stamp = file.readline()
            if stamp != sdist.manpage_stamp:
                self.execute(os.unlink, [manname], 'removing {0}'.format(manname))

class sdist(distutils_sdist):

    manpage_stamp = '''.\\" [created by setup.py sdist]\n'''

    def run(self):
        self.run_command('build_doc')
        return distutils_sdist.run(self)

    def _rewrite_manpage(self, manname):
        with open(manname, 'r') as file:
            contents = file.read()
        os.unlink(manname)
        with open(manname, 'w') as file:
            file.write(self.manpage_stamp)
            file.write(contents)

    def make_release_tree(self, base_dir, files):
        distutils_sdist.make_release_tree(self, base_dir, files)
        for manname in glob.iglob(os.path.join(base_dir, 'doc', '*.1')):
            self.execute(self._rewrite_manpage, [manname], 'rewriting {0}'.format(manname))

distutils.core.setup(
    name='didjvu',
    version=__version__,
    license='GNU GPL 2',
    description='DjVu encoder with foreground/background separation',
    long_description=__doc__.strip(),
    classifiers=classifiers,
    url='http://jwilk.net/software/didjvu',
    author='Jakub Wilk',
    author_email='jwilk@jwilk.net',
    packages=['didjvu'],
    package_dir=dict(didjvu='lib'),
    scripts=['didjvu'],
    data_files=[('share/man/man1', glob.glob('doc/*.1'))],
    cmdclass=dict(
        build_doc=build_doc,
        clean=clean,
        sdist=sdist,
        test=test,
    ),
)

# vim:ts=4 sts=4 sw=4 et
