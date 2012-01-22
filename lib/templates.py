# encoding=UTF-8

# Copyright © 2010, 2011 Jakub Wilk <jwilk@jwilk.net>
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
import os
import sys

try:
    from string import Formatter
except ImportError:
    # This is very rough, incomplete backport of string.Formatter class.
    # It's provided here to allow basic functionality of didjvu even with
    # Python 2.5.

    import warnings
    warnings.warn(RuntimeWarning('Python %d.%d is not supported, please use Python >= 2.6' % sys.version_info[:2]), stacklevel=999)

    class Formatter():

        _split = re.compile('''
            ( [{][{] | [}][}] | [{][^}]*[}] )
        ''', re.VERBOSE).split

        @staticmethod
        def _not_implemented():
            raise NotImplementedError('Please use Python >= 2.6')

        def format(self, format_string, *args, **kwargs):
            return self.vformat(format_string, args, kwargs)

        def vformat(self, format_string, args, kwargs):
            result = []
            for literal_text, field_name, format_spec, conversion in self.parse(format_string):
                if conversion is not None:
                    self._not_implemented()
                if literal_text:
                    result += [literal_text]
                if field_name is not None:
                    obj, _ = self.get_field(field_name, args, kwargs)
                    obj = self.convert_field(obj, conversion)
                    result += [self.format_field(obj, format_spec)]
            return ''.join(result)

        def convert_field(self, value, conversion):
            if conversion is None:
                return value
            else:
                self._not_implemented()

        def get_field(self, field_name, args, kwargs):
            return self.get_value(field_name, args, kwargs), field_name

        def format_field(self, value, format_spec):
            if format_spec is not None:
                self._not_implemented()
            return str(value)

        def parse(self, format_string):
            for token in self._split(format_string):
                if token in ('{{', '}}'):
                    yield token[0], None, None, None
                elif token[:1] + token[-1:] == '{}':
                    if (':' in token) or ('!' in token) or ('.' in token):
                        self._not_implemented()
                    yield '', token[1:-1], None, None
                elif token:
                    yield token, None, None, None

        def get_value(self, key, args, kwargs):
            if isinstance(key, (int, long)):
                return args[key]
            else:
                return kwargs[key]

formatter = Formatter()
del Formatter

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
