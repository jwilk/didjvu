# encoding=UTF-8

# Copyright © 2015 Jakub Wilk <jwilk@jwilk.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

import os

from .tools import (
    assert_true,
    assert_false,
)

from lib import filetype

datadir = os.path.join(os.path.dirname(__file__), 'data')

def test_djvu():
    path = os.path.join(datadir, 'ycbcr.djvu')
    tp = filetype.check(path)
    assert_true(tp.like(filetype.djvu))
    assert_true(tp.like(filetype.djvu_single))

def test_bad():
    path = os.path.join(datadir, os.devnull)
    tp = filetype.check(path)
    assert_false(tp.like(filetype.djvu))
    assert_false(tp.like(filetype.djvu_single))

# vim:ts=4 sts=4 sw=4 et
