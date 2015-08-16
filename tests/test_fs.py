# encoding=UTF-8

# Copyright © 2015 Jakub Wilk <jwilk@jwilk.net>
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

import io

from .tools import (
    assert_equal,
    interim,
)

from lib import fs

def test_copy_file():
    def t(s):
        input_file = io.BytesIO(s)
        output_file = io.BytesIO()
        length = fs.copy_file(input_file, output_file)
        assert_equal(output_file.tell(), length)
        output_file.seek(0)
        r = output_file.read()
        assert_equal(s, r)
    t('eggs')
    with interim(fs, _block_size=1):
        t('eggs' + 'spam' * 42)

def test_replace_ext():
    r = fs.replace_ext('eggs', 'spam')
    assert_equal(r, 'eggs.spam')
    r = fs.replace_ext('eggs.', 'spam')
    assert_equal(r, 'eggs.spam')
    r = fs.replace_ext('eggs.ham', 'spam')
    assert_equal(r, 'eggs.spam')

# vim:ts=4 sts=4 sw=4 et
