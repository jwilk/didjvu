# encoding=UTF-8

# Copyright © 2011-2024 Jakub Wilk <jwilk@jwilk.net>
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

'''
didjvu version information
'''

from __future__ import print_function

import argparse
import sys

__version__ = '0.9.2'

def get_software_agent():
    import gamera
    result = 'didjvu ' + __version__
    result += ' (Gamera {0})'.format(gamera.__version__)
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
        from . import gamera_support as gs
        print('+ Gamera {0}'.format(gs.gamera.__version__))
        pil_name = 'Pillow'
        try:
            pil_version = gs.PIL.PILLOW_VERSION
        except AttributeError:
            try:
                pil_version = gs.PIL.__version__
            except AttributeError:
                pil_name = 'PIL'
                pil_version = gs.PIL.VERSION
        print('+ {PIL} {0}'.format(pil_version, PIL=pil_name))
        from . import xmp
        if xmp.backend:
            for version in xmp.backend.versions:
                prefix = '+'
                if version[0] == '+':
                    prefix = ' '
                print(prefix, version)
        parser.exit()

__all__ = [
    'VersionAction',
    '__version__',
    'get_software_agent',
]

# vim:ts=4 sts=4 sw=4 et
