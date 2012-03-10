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

import time
import datetime

class Timestamp(object):

    def __init__(self, unixtime):
        self._localtime = time.localtime(unixtime)

    def _str(self):
        return time.strftime('%Y-%m-%dT%H:%M:%S', self._localtime)

    def _str_tz(self):
        offset = time.timezone if not self._localtime.tm_isdst else time.altzone
        hours, minutes  = divmod(abs(offset) // 60, 60)
        return '%s%02d:%02d' % ('+' if offset < 0 else '-', hours, minutes)

    def __str__(self):
        '''Format the timestamp object in accordance with RFC 3339.'''
        return self._str() + self._str_tz()

    def as_datetime(self, cls=datetime.datetime):
        offset = time.timezone if not self._localtime.tm_isdst else time.altzone
        class tz(datetime.tzinfo):
            def utcoffset(self, dt):
                return datetime.timedelta(seconds=-offset)
            def dst(self, dt):
                return datetime.timedelta(0)
        return cls(*self._localtime[:6], tzinfo=tz())

def now():
    return Timestamp(time.time())

# vim:ts=4 sw=4 et
