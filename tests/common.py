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

import re

from nose import SkipTest
from nose.tools import (
    assert_equal,
    assert_not_equal,
    assert_true,
)

def assert_regexp_matches(regexp, text):
    if isinstance(regexp, basestring):
        regexp = re.compile(regexp)
    if not regexp.search(text):
        message = '''Regexp didn't match: %r not found in %r''' % (regexp.pattern, text)
        assert_true(0, message)

def assert_rfc3339_timestamp(timestamp):
    return assert_regexp_matches(
        '^[0-9]{4}(-[0-9]{2}){2}T[0-9]{2}(:[0-9]{2}){2}([+-][0-9]{2}:[0-9]{2}|Z)$',
        timestamp
    )

# vim:ts=4 sw=4 et
