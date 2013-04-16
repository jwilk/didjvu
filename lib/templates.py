# encoding=UTF-8

# Copyright © 2010, 2011, 2012, 2013 Jakub Wilk <jwilk@jwilk.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

'''filename templates'''

import os
import re
import string
import sys

formatter = string.Formatter()

def expand(template, name, page):
    '''
    >>> path = '/path/to/eggs.png'
    >>> expand('{name}', path, 0)
    '/path/to/eggs.png'
    >>> expand('{base}', path, 0)
    'eggs.png'
    >>> expand('{name-ext}.djvu', path, 0)
    '/path/to/eggs.djvu'
    >>> expand('{base-ext}.djvu', path, 0)
    'eggs.djvu'
    >>> expand('{page}', path, 0)
    '1'
    >>> expand('{page:04}', path, 0)
    '0001'
    >>> expand('{page}', path, 42)
    '43'
    >>> expand('{page+26}', path, 42)
    '69'
    >>> expand('{page-26}', path, 42)
    '17'
    '''
    base = os.path.basename(name)
    name_ext, _ = os.path.splitext(name)
    base_ext, _ = os.path.splitext(base)
    d = {
        'name': name, 'name-ext': name_ext,
        'base': base, 'base-ext': base_ext,
        'page': page + 1,
    }
    for _, var, _, _ in formatter.parse(template):
        if var is None:
            continue
        if '+' in var:
            sign = +1
            base_var, offset = var.split('+')
        elif '-' in var:
            sign = -1
            base_var, offset = var.split('-')
        else:
            continue
        try:
            offset = sign * int(offset, 10)
        except ValueError:
            continue
        try:
            base_value = d[base_var]
        except LookupError:
            continue
        if not isinstance(base_value, int):
            continue
        d[var] = d[base_var] + offset
    return formatter.vformat(template, (), d)

# vim:ts=4 sw=4 et
