# encoding=UTF-8

# Copyright © 2012 Jakub Wilk <jwilk@jwilk.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

from . common import assert_rfc3339_timestamp

from lib import timestamp

def test_now():
    result = timestamp.now()
    assert_rfc3339_timestamp(str(result))

def test_explicit_construct():
    result = timestamp.Timestamp(100000)
    assert_rfc3339_timestamp(str(result))

# vim:ts=4 sts=4 sw=4 et
