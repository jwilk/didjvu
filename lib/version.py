# encoding=UTF-8

# Copyright © 2011-2016 Jakub Wilk <jwilk@jwilk.net>
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

import argparse
import sys

__version__ = '0.8.2'

def get_software_agent():
    try:
        import gamera
    except ImportError:  # no coverage
        gamera = None
    result = 'didjvu ' + __version__
    try:
        result += ' (Gamera {0})'.format(gamera.__version__)
    except (AttributeError, TypeError, ValueError):  # no coverage
        pass
    return result

class VersionAction(argparse.Action):
    '''
    argparse --version action
    '''

    def __init__(self, option_strings, dest=argparse.SUPPRESS):
        super(VersionAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            nargs=0,
            help="show program's version information and exit"
        )

    def __call__(self, parser, namespace, values, option_string=None):
        print('{prog} {0}'.format(__version__, prog=parser.prog))
        print('+ Python {0}.{1}.{2}'.format(*sys.version_info))
        try:
            import gamera
        except ImportError:  # no coverage
            pass
        else:
            print('+ Gamera {0}'.format(gamera.__version__))
        parser.exit()

__all__ = [
    'VersionAction',
    '__version__',
    'get_software_agent',
]

# vim:ts=4 sts=4 sw=4 et
