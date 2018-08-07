# encoding=UTF-8

# Copyright © 2009-2018 Jakub Wilk <jwilk@jwilk.net>
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
*didjvu* uses the Gamera framework to separate foreground/background layers,
which it can then encode into a DjVu file.
'''

b''  # Python >= 2.6 is required
exec b''  # Python 2.X is required

import glob

import distutils.command
import distutils.core
from distutils.command.sdist import sdist as distutils_sdist

def get_version():
    with open('doc/changelog', 'r') as file:
        line = file.readline()
    return line.split()[1].strip('()')

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

class sdist(distutils_sdist):

    def run(self):
        raise NotImplementedError

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

distutils.core.setup(
    name='didjvu',
    version=get_version(),
    license='GNU GPL 2',
    description='DjVu encoder with foreground/background separation',
    long_description=__doc__.strip(),
    classifiers=classifiers,
    url='http://jwilk.net/software/didjvu',
    author='Jakub Wilk',
    author_email='jwilk@jwilk.net',
    packages=['didjvu', 'didjvu.xmp'],
    package_dir=dict(didjvu='lib'),
    scripts=['didjvu'],
    data_files=[('share/man/man1', glob.glob('doc/*.1'))],
    cmdclass=dict(
        sdist=sdist,
        test=test,
    ),
)

# vim:ts=4 sts=4 sw=4 et
