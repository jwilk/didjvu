# encoding=UTF-8

# Copyright © 2012-2024 Jakub Wilk <jwilk@jwilk.net>
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

'''
timestamps
'''

import datetime
import time

class Timestamp(object):

    def __init__(self, unixtime):
        self._localtime = time.localtime(unixtime)
        self._tzdelta = (
            datetime.datetime.fromtimestamp(unixtime) -
            datetime.datetime.utcfromtimestamp(unixtime)
        )

    def _str(self):
        return time.strftime('%Y-%m-%dT%H:%M:%S', self._localtime)

    def _str_tz(self):
        offset = self._tzdelta.days * 3600 * 24 + self._tzdelta.seconds
        if offset == 0:
            # Apparently, pyexiv2 automatically converts 00:00 offsets to “Z”.
            # Let's always use “Z” for consistency.
            return 'Z'
        hours, minutes = divmod(abs(offset) // 60, 60)
        sign = '+' if offset >= 0 else '-'
        return '{s}{h:02}:{m:02}'.format(s=sign, h=hours, m=minutes)

    def __str__(self):
        '''Format the timestamp object in accordance with RFC 3339.'''
        return self._str() + self._str_tz()

    def as_datetime(self, cls=datetime.datetime):
        tzdelta = self._tzdelta
        class tz(datetime.tzinfo):
            def utcoffset(self, dt):
                del dt
                return tzdelta
            def dst(self, dt):
                del dt
                return datetime.timedelta(0)
            def tzname(self, dt):
                del dt
                return
        return cls(*self._localtime[:6], tzinfo=tz())

def now():
    return Timestamp(time.time())

__all__ = ['Timestamp', 'now']

# vim:ts=4 sts=4 sw=4 et
