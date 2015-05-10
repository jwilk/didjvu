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

'''
filetype detection
'''

class generic(object):

    def __new__(self, *args, **kwargs):
        raise NotImplementedError

    @classmethod
    def like(cls, other):
        return issubclass(cls, other)

class djvu(generic):
    pass

class djvu_single(djvu):
    pass

def check(filename):
    cls = generic
    with open(filename, 'rb') as file:
        header = file.read(16)
        if header.startswith('AT&TFORM'):
            cls = djvu
            if header.endswith('DJVU'):
                cls = djvu_single
    return cls

# vim:ts=4 sts=4 sw=4 et
