#!/usr/bin/python
# encoding=UTF-8

# Copyright © 2009 Jakub Wilk <ubanus@users.sf.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.

import sys

class DevNull(object):

    write = read = close = flush = lambda *args, **kwargs: None

class Log(object):

    dev_null = DevNull()
    log = sys.stderr

    def __init__(self, threshold):
        self._threshold = threshold

    def __call__(self, n):
        if n <= self._threshold:
            return self.log
        else:
            return self.dev_null

# vim:ts=4 sw=4 et
