# encoding=UTF-8

# Copyright © 2009, 2010 Jakub Wilk <jwilk@jwilk.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.

import functools
import tempfile

file = functools.partial(tempfile.NamedTemporaryFile, prefix='didjvu')
directory = functools.partial(tempfile.mkdtemp, prefix='didjvu')
name = functools.partial(tempfile.mktemp, prefix='didjvu')

__all__ = ['file', 'directory', 'name']

# vim:ts=4 sw=4 et
