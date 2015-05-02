# encoding=UTF-8

# Copyright © 2010-2012 Jakub Wilk <jwilk@jwilk.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

from __future__ import with_statement

import sys

from . common import (
	interim,
    exception,
)

from lib import utils

class test_enhance_import():

    @classmethod
    def setup_class(cls):
        sys.modules['nonexistent'] = None

    def test_debian(self):
        with interim(utils, debian=True):
            with exception(ImportError, 'No module named nonexistent; please install the python-nonexistent package'):
                try:
                    import nonexistent
                except ImportError, ex:
                    utils.enhance_import_error(ex, 'PyNonexistent', 'python-nonexistent', 'http://pynonexistent.example.net/')
                    raise
                nonexistent.f() # quieten pyflakes

    def test_nondebian(self):
        with interim(utils, debian=False):
            with exception(ImportError, 'No module named nonexistent; please install the PyNonexistent package <http://pynonexistent.example.net/>'):
                try:
                    import nonexistent
                except ImportError, ex:
                    utils.enhance_import_error(ex, 'PyNonexistent', 'python-nonexistent', 'http://pynonexistent.example.net/')
                    raise
                nonexistent.f() # quieten pyflakes

# vim:ts=4 sw=4 et
