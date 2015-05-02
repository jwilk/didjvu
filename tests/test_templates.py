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

from . common import (
    assert_equal,
)

from lib import templates

def test_simple():
    path = '/path/to/eggs.png'
    memo = {}
    assert_equal(
        templates.expand('{name}', path, 0, memo),
        '/path/to/eggs.png'
    )
    assert_equal(
        templates.expand('{base}', path, 0, memo),
        'eggs.png'
    )
    assert_equal(
        templates.expand('{name-ext}.djvu', path, 0, memo),
        '/path/to/eggs.djvu'
    )
    assert_equal(
        templates.expand('{base-ext}.djvu', path, 0, memo),
        'eggs.djvu'
    )
    assert_equal(
        templates.expand('{page}', path, 0, memo),
        '1'
    )
    assert_equal(
        templates.expand('{page:04}', path, 0, memo),
        '0001'
    )
    assert_equal(
        templates.expand('{page}', path, 42, memo),
        '43'
    )
    assert_equal(
        templates.expand('{page+26}', path, 42, memo),
        '69'
    )
    assert_equal(
        templates.expand('{page-26}', path, 42, memo),
        '17'
    )

# vim:ts=4 sw=4 et
