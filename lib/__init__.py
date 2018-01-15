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
didjvu's private modules
'''

import sys

if sys.version_info < (2, 6):
    raise RuntimeError('Python >= 2.6 is required')  # no coverage
if sys.version_info >= (3, 0):
    raise RuntimeError('Python 2.X is required')  # no coverage

# vim:ts=4 sts=4 sw=4 et
