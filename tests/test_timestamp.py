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

import datetime
import time

from . common import (
    assert_equal,
    assert_is_none,
    assert_rfc3339_timestamp,
    fork_isolation,
    interim_environ,
)

from lib import timestamp

def test_now():
    result = timestamp.now()
    assert_rfc3339_timestamp(str(result))
    dt = result.as_datetime()
    assert_equal(dt.dst(), datetime.timedelta(0))
    assert_is_none(dt.tzname())

def test_timezones():
    @fork_isolation
    def t(uts, tz, expected):
        dt_expected = expected.replace('T', ' ').replace('Z', '+00:00')
        with interim_environ(TZ=tz):
            time.tzset()
            result = timestamp.Timestamp(uts)
            assert_rfc3339_timestamp(str(result))
            assert_equal(str(result), expected)
            dt = result.as_datetime()
            assert_equal(dt.dst(), datetime.timedelta(0))
            assert_is_none(dt.tzname())
            assert_equal(str(dt), dt_expected)
    # winter:
    t(1261171514, 'UTC', '2009-12-18T21:25:14Z')
    t(1261171514, 'Europe/Warsaw', '2009-12-18T22:25:14+01:00')
    t(1261171514, 'America/New_York', '2009-12-18T16:25:14-05:00')
    t(1261171514, 'Asia/Kathmandu', '2009-12-19T03:10:14+05:45')
    t(1261171514, 'HAM+4:37', '2009-12-18T16:48:14-04:37')
    # summer:
    t(1337075844, 'Europe/Warsaw', '2012-05-15T11:57:24+02:00')
    # Offset changes:
    t(1394737792, 'Europe/Moscow', '2014-03-13T23:09:52+04:00')  # used to be +04:00, but it's +03:00 now

# vim:ts=4 sts=4 sw=4 et
