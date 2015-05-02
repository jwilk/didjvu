# encoding=UTF-8

# Copyright © 2010-2015 Jakub Wilk <jwilk@jwilk.net>
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
import string

formatter = string.Formatter()

def expand(template, name, page, memo):
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
            base_var, offset = var.split('+', 1)
        elif '-' in var:
            sign = -1
            base_var, offset = var.split('-', 1)
        else:
            continue  # <no-coverage>
            # https://bitbucket.org/ned/coveragepy/issue/198
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
    ident = formatter.vformat(template, (), d)
    while True:
        n = memo.get(ident, 0)
        if n == 0:
            break
        memo[ident] += 1
        ident_base, ident_ext = os.path.splitext(ident)
        ident = '{base}.{n}{ext}'.format(base=ident_base, n=n, ext=ident_ext)
    assert ident not in memo
    memo[ident] = 1
    return ident

# vim:ts=4 sts=4 sw=4 et
