# encoding=UTF-8

# Copyright © 2010-2015 Jakub Wilk <jwilk@jwilk.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

import sys

from . common import (
    exception,
    interim,
)

from lib import utils

class test_enhance_import():

    @classmethod
    def setup_class(cls):
        sys.modules['nonexistent'] = None

    def test_debian(self):
        with interim(utils, debian=True):
            msg = (
                'No module named nonexistent; '
                'please install the python-nonexistent package'
            )
            with exception(ImportError, msg):
                try:
                    import nonexistent
                except ImportError as ex:
                    utils.enhance_import_error(ex,
                        'PyNonexistent',
                        'python-nonexistent',
                        'http://pynonexistent.example.net/'
                    )
                    raise
                nonexistent.f()  # quieten pyflakes

    def test_nondebian(self):
        with interim(utils, debian=False):
            msg = (
                'No module named nonexistent; '
                'please install the PyNonexistent package <http://pynonexistent.example.net/>'
            )
            with exception(ImportError, msg):
                try:
                    import nonexistent
                except ImportError as ex:
                    utils.enhance_import_error(ex,
                        'PyNonexistent',
                        'python-nonexistent',
                        'http://pynonexistent.example.net/'
                    )
                    raise
                nonexistent.f()  # quieten pyflakes

# vim:ts=4 sts=4 sw=4 et
