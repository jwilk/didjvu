# encoding=UTF-8

# Copyright © 2011-2015 Jakub Wilk <jwilk@jwilk.net>
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

__version__ = '0.8'

def get_software_agent():
    try:
        import gamera
    except ImportError:  # <no-coverage>
        gamera = None
    result = 'didjvu ' + __version__
    try:
        result += ' (Gamera {0})'.format(gamera.__version__)
    except (AttributeError, TypeError, ValueError):  # <no-coverage>
        pass
    return result

# vim:ts=4 sts=4 sw=4 et
