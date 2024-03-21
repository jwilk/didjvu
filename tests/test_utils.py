# encoding=UTF-8

# Copyright © 2010-2024 Jakub Wilk <jwilk@jwilk.net>
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

import gc
import sys

from .tools import (
    assert_equal,
    assert_false,
    assert_raises,
    assert_true,
    interim,
)

from lib import utils

class test_enhance_import:

    @classmethod
    def setup_class(cls):
        sys.modules['nonexistent'] = None

    def test_debian(self):
        with interim(utils, debian=True):
            with assert_raises(ImportError) as ecm:
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
            assert_equal(str(ecm.exception),
                'No module named nonexistent; '
                'please install the python-nonexistent package'
            )

    def test_nondebian(self):
        with interim(utils, debian=False):
            with assert_raises(ImportError) as ecm:
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
            assert_equal(str(ecm.exception),
                'No module named nonexistent; '
                'please install the PyNonexistent package <http://pynonexistent.example.net/>'
            )

def test_proxy():
    class obj:
        x = 42
    def wait():
        assert_true(wait.ok)
        wait.ok = False
    wait.ok = False
    class Del(object):
        ok = False
        def __del__(self):
            type(self).ok = False
    proxy = utils.Proxy(obj, wait, [Del()])
    wait.ok = True
    assert_equal(proxy.x, 42)
    assert_false(wait.ok)
    proxy.x = 37
    assert_equal(proxy.x, 37)
    assert_equal(obj.x, 37)
    Del.ok = True
    del proxy
    gc.collect()
    assert_false(Del.ok)

# vim:ts=4 sts=4 sw=4 et
