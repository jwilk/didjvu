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

'''Command line interface for *didjvu*'''

import argparse

from . import djvu_extra as djvu

def range_int(x, y, typename):
    class rint(int):
        def __new__(cls, n):
            n = int(n)
            if not (x <= n <= y):
                raise ValueError
            return n
    return type(typename, (rint,), {})

dpi_type = range_int(djvu.DPI_MIN, djvu.DPI_MAX, 'dpi')
losslevel_type = range_int(djvu.LOSS_LEVEL_MIN, djvu.LOSS_LEVEL_MAX, 'loss level')
subsample_type = range_int(djvu.SUBSAMPLE_MIN, djvu.SUBSAMPLE_MAX, 'subsample')

def slice_type(max_slices=99):

    def slices(value):
        if ',' in value:
            result = map(int, value.split(','))
        elif '+' in value:
            result = []
            accum = 0
            for slice in value.split('+'):
                accum += int(slice)
                result += accum,
        else:
            result = [int(value)]
        if not result:
            raise cli.BadOption('invalid slice specification')
        if len(result) > max_slices:
            raise cli.BadOption('too many slices')
        return result
    return slices

class intact(object):

    def __init__(self, x):
        self.x = x

    def __call__(self):
        return self.x

class ArgumentParser(argparse.ArgumentParser):

    def __init__(self, methods, default_method):
        argparse.ArgumentParser.__init__(self)
        p_separate = self.add_subparser('separate')
        p_encode = self.add_subparser('encode')
        p_bundle = self.add_subparser('bundle')
        for p in p_encode, p_separate, p_bundle:
            p.add_argument('-o', '--output')
            if p is p_bundle:
                p.add_argument('--pageid-template', metavar='TEMPLATE', default='{base}.djvu')
            else:
                p.add_argument('--output-template', metavar='TEMPLATE')
            p.add_argument('--losslevel', dest='loss_level', type=losslevel_type, help=argparse.SUPPRESS)
            p.add_argument('--loss-level', dest='loss_level', type=losslevel_type, metavar='N')
            p.add_argument('--lossless', dest='loss_level', action='store_const', const=0)
            p.add_argument('--clean', dest='loss_level', action='store_const', const=1)
            p.add_argument('--lossy', dest='loss_level', action='store_const', const=100)
            if p is not p_separate:
                p.add_argument('--masks', nargs='+', metavar='MASK') 
                p.add_argument('--mask', action='append', dest='masks', metavar='MASK')
                for layer in 'fg', 'bg':
                    p.add_argument('--%s-slices' % layer, type=slice_type(), metavar='N+...+N')
                    p.add_argument('--%s-crcb' % layer, choices='normal half full none'.split())
                    p.add_argument('--%s-subsample' % layer, type=subsample_type, metavar='N')
                p.add_argument('--fg-bg-defaults', help=argparse.SUPPRESS, action='store_const', const=1)
            if p is not p_encode:
                p.add_argument('-d', '--dpi', type=dpi_type, metavar='N')
            p.add_argument('-m', '--method', choices=methods, default=default_method)
            p.add_argument('-v', '--verbose', dest='verbosity', action='append_const', const=None)
            p.add_argument('-q', '--quiet', dest='verbosity', action='store_const', const=[])
            p.add_argument('input', metavar='<input-image>', nargs='+')
            p.set_defaults(
                masks=[],
                fg_bg_defaults=None,
                loss_level=djvu.LOSS_LEVEL_DEFAULT,
                dpi=djvu.DPI_DEFAULT,
                fg_slices=intact([100]), fg_crcb=intact('full'), fg_subsample=intact(6),
                bg_slices=intact([72, 82, 88, 95]), bg_crcb=intact('normal'), bg_subsample=intact(3),
                verbosity=[None],
            )

    def add_subparser(self, name):
        try:
            self.__subparsers
        except AttributeError:
            self.__subparsers = self.add_subparsers(parser_class=argparse.ArgumentParser)
        p = self.__subparsers.add_parser(name)
        p.set_defaults(_action_=name)
        return p

    def parse_args(self, actions):
        o = argparse.ArgumentParser.parse_args(self)
        if o.fg_bg_defaults is None:
            for layer in 'fg', 'bg':
                namespace = argparse.Namespace()
                setattr(o, '%s_options' % layer, namespace)
                for facet in 'slices', 'crcb', 'subsample':
                    attrname = '%s_%s' % (layer, facet)
                    value = getattr(o, attrname)
                    if isinstance(value, intact):
                        value = value()
                    else:
                        o.fg_bg_defaults = False
                    setattr(namespace, facet, value)
                    delattr(o, attrname)
                namespace.crcb = getattr(djvu,'CRCB_%s' % namespace.crcb.upper())
        if o.fg_bg_defaults is not False:
            o.fg_bg_defaults = True
        o.verbosity = len(o.verbosity)
        action = getattr(actions, vars(o).pop('_action_'))
        return action(o)

__all__ = ['ArgumentParser']

# vim:ts=4 sw=4 et
