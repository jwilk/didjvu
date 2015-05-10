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

from . common import (
    assert_equal,
)

from lib import fs

def test_replace_ext():
    r = fs.replace_ext('eggs', 'spam')
    assert_equal(r, 'eggs.spam')
    r = fs.replace_ext('eggs.', 'spam')
    assert_equal(r, 'eggs.spam')
    r = fs.replace_ext('eggs.ham', 'spam')
    assert_equal(r, 'eggs.spam')

# vim:ts=4 sts=4 sw=4 et
