#!/usr/bin/python
# encoding=UTF-8
# Copyright © 2009, 2010 Jakub Wilk <jwilk@jwilk.net>
#
# This package is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This package is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

'''
"*didjvu* uses the `Gamera <http://gamera.informatik.hsnr.de/>`_ framework to
separate foreground/background layers, which it can then encode into a `DjVu
<http://djvu.org/>`_ file."
'''

classifiers = '''
Development Status :: 4 - Beta
Environment :: Console
Intended Audience :: End Users/Desktop
License :: OSI Approved :: GNU General Public License (GPL)
Operating System :: OS Independent
Programming Language :: Python
Programming Language :: Python :: 2
Topic :: Text Processing
Topic :: Multimedia :: Graphics
'''.strip().split('\n')

import distutils.core
import glob
import os

from lib.version import __version__

os.putenv('TAR_OPTIONS', '--owner root --group root --mode a+rX')
distutils.core.setup(
    name = 'didjvu',
    version = __version__,
    license = 'GNU GPL 2',
    description = 'DjVu encoder with foreground/background separation',
    long_description = __doc__.strip(),
    classifiers = classifiers,
    url = 'http://jwilk.net/software/didjvu',
    author = 'Jakub Wilk',
    author_email = 'jwilk@jwilk.net',
    packages = ['didjvu'],
    package_dir = dict(didjvu='lib'),
    scripts = ['didjvu'],
    data_files = [('share/man/man1', glob.glob('doc/*.1'))],
)

# vim:ts=4 sw=4 et
