# encoding=UTF-8

# Copyright © 2009, 2010 Jakub Wilk <jwilk@jwilk.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

'''temporary files and directories'''

import contextlib
import functools
import shutil
import tempfile

file = functools.partial(tempfile.NamedTemporaryFile, prefix='didjvu.')
name = functools.partial(tempfile.mktemp, prefix='didjvu.')
wrapper = tempfile._TemporaryFileWrapper

@contextlib.contextmanager
def directory(*args, **kwargs):
    kwargs = dict(kwargs)
    kwargs.setdefault('prefix', 'didjvu.')
    tmpdir = tempfile.mkdtemp(*args, **kwargs)
    try:
        yield tmpdir
    finally:
        shutil.rmtree(tmpdir)

__all__ = ['file', 'directory', 'name', 'wrapper']

# vim:ts=4 sw=4 et
