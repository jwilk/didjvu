# encoding=UTF-8

# Copyright © 2011, 2012 Jakub Wilk <jwilk@jwilk.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

__version__ = '0.2.5'

def get_software_agent():
    try:
        import gamera
    except ImportError:
        gamera = None
    result = 'didjvu ' + __version__
    try:
        result += ' (Gamera %s)' % gamera.__version__
    except (AttributeError, TypeError, ValueError):
        pass
    return result

# vim:ts=4 sw=4 et
