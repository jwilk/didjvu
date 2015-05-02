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
    assert_raises,
)

from lib import templates

def test_name():
    path = '/path/to/eggs.png'
    memo = {}
    s = templates.expand('{name}', path, 0, memo)
    assert_equal(s, '/path/to/eggs.png')
    s = templates.expand('{base}', path, 0, memo)
    assert_equal(s, 'eggs.png')
    s = templates.expand('{name-ext}.djvu', path, 0, memo)
    assert_equal(s, '/path/to/eggs.djvu')
    s = templates.expand('{base-ext}.djvu', path, 0, memo)
    assert_equal(s, 'eggs.djvu')

def test_page():
    path = '/path/to/eggs.png'
    memo = {}
    s = templates.expand('{page}', path, 0, memo)
    assert_equal(s, '1')
    s = templates.expand('{page:04}', path, 0, memo)
    assert_equal(s, '0001')
    s = templates.expand('{page}', path, 42, memo)
    assert_equal(s, '43')
    s = templates.expand('{page+26}', path, 42, memo)
    assert_equal(s, '69')
    s = templates.expand('{page-26}', path, 42, memo)
    assert_equal(s, '17')

def test_bad_offset():
    path = '/path/to/eggs.png'
    with assert_raises(KeyError):
        templates.expand('{page+ham}', path, 42, {})

def test_bad_type_offset():
    path = '/path/to/eggs.png'
    with assert_raises(KeyError):
        templates.expand('{base-37}', path, 42, {})

def test_bad_var_offset():
    path = '/path/to/eggs.png'
    with assert_raises(KeyError):
        templates.expand('{eggs-37}', path, 42, {})

def test_duplicates():
    path = '/path/to/eggs.png'
    memo = {}
    s = templates.expand('{base-ext}.djvu', path, 0, memo)
    assert_equal(s, 'eggs.djvu')
    s = templates.expand('{base-ext}.djvu', path, 0, memo)
    assert_equal(s, 'eggs.1.djvu')
    s = templates.expand('{base-ext}.djvu', path, 0, memo)
    assert_equal(s, 'eggs.2.djvu')
    s = templates.expand('{base-ext}.2.djvu', path, 0, memo)
    assert_equal(s, 'eggs.2.1.djvu')
    s = templates.expand('{base-ext}.2.djvu', path, 0, memo)
    assert_equal(s, 'eggs.2.2.djvu')

# vim:ts=4 sts=4 sw=4 et
