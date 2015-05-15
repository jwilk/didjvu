# encoding=UTF-8

# Copyright © 2012-2015 Jakub Wilk <jwilk@jwilk.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

import time

from . common import (
    assert_equal,
    assert_rfc3339_timestamp,
    fork_isolation,
    interim_environ,
)

from lib import timestamp

def test_now():
    result = timestamp.now()
    assert_rfc3339_timestamp(str(result))


def test_timezones():
    uts = 1261171514
    @fork_isolation
    def t(tz, expected):
        with interim_environ(TZ=tz):
            time.tzset()
            result = timestamp.Timestamp(uts)
            assert_rfc3339_timestamp(str(result))
            assert_equal(str(result), expected)
    t('UTC', '2009-12-18T21:25:14Z')
    t('Europe/Warsaw', '2009-12-18T22:25:14+01:00')
    t('America/New_York', '2009-12-18T16:25:14-05:00')
    t('Asia/Kathmandu', '2009-12-19T03:10:14+05:45')
    t('HAM+4:37', '2009-12-18T16:48:14-04:37')

# vim:ts=4 sts=4 sw=4 et
