# encoding=UTF-8

# Copyright © 2009-2021 Jakub Wilk <jwilk@jwilk.net>
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
didjvu's command-line interface
'''

import functools

from . import utils

try:
    import argparse
except ImportError as ex:  # no coverage
    utils.enhance_import_error(ex,
        'argparse',
        'python-argparse',
        'https://pypi.org/project/argparse/'
    )
    raise

from . import djvu_support as djvu
from . import version
from . import xmp

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

def slice_type(max_slices=djvu.IW44_N_SLICES_MAX):

    def slices(value):
        result = []
        if ',' in value:
            prev_slc = 0
            for slc in value.split(','):
                slc = int(slc)
                if slc <= prev_slc:
                    raise ValueError('non-increasing slice value')
                result += [slc]
                prev_slc = slc
            slc = 0
        elif '+' in value:
            slc = 0
            for slcinc in value.split('+'):
                slcinc = int(slcinc)
                if slcinc <= 0:
                    raise ValueError('non-increasing slice value')
                slc += slcinc
                result += [slc]
        else:
            slc = int(value)
            if slc < 0:
                raise ValueError('invalid slice value')
            result = [slc]
        assert len(result) > 0
        if len(result) > max_slices:
            raise ValueError('too many slices')
        return result
    return slices

def get_slice_repr(lst):
    def fold(lst, obj):
        return lst + [obj - sum(lst)]
    plus_lst = functools.reduce(fold, lst[1:], lst[:1])
    return '+'.join(map(str, plus_lst))

class intact(object):

    def __init__(self, x):
        self.x = x

    def __call__(self):
        return self.x

def replace_underscores(s):
    return s.replace('_', '-')

def _get_method_params_help(methods):
    result = ['binarization methods and their parameters:']
    for name, method in sorted(methods.iteritems()):
        result += ['  ' + name]
        for arg in method.args.itervalues():
            arg_help = arg.name
            if arg.type in {int, float}:
                arg_help += '=' + 'NX'[arg.type is float]
                arg_help_paren = []
                if (arg.min is None) != (arg.max is None):
                    message = 'inconsistent limits for {method}.{arg}: min={min}, max={max}'.format(
                        method=name, arg=arg.name,
                        min=arg.min, max=arg.max
                    )
                    raise NotImplementedError(message)
                if arg.min is not None:
                    arg_help_paren += ['{0} .. {1}'.format(arg.min, arg.max)]
                if arg.default is not None:
                    arg_help_paren += ['default: {0}'.format(arg.default)]
                if arg_help_paren:
                    arg_help += ' ({0})'.format(', '.join(arg_help_paren))
            elif arg.type is bool:
                if arg.default is not False:
                    message = 'unexpected default value for {method}.{arg}: {default}'.format(
                        method=name, arg=arg.name,
                        default=arg.default
                    )
                    raise NotImplementedError(message)
            else:
                message = 'unexpected type for {method}.{arg}: {tp}'.format(method=name, arg=arg.name, tp=arg.type.__name__)
                raise NotImplementedError(message)
            result += ['  - ' + arg_help]
    return '\n'.join(result)

class TestAction(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        import nose
        argv = ['nosetests']
        argv += values
        nose.main(argv=argv)

class ArgumentParser(argparse.ArgumentParser):

    class defaults(object):
        page_id_template = '{base-ext}.djvu'
        pages_per_dict = 1
        dpi = None
        fg_slices = [100]
        fg_crcb = djvu.CRCB.full
        fg_subsample = 6
        bg_slices = [74, 84, 90, 97]
        bg_crcb = djvu.CRCB.normal
        bg_subsample = 3

    def __init__(self, methods, default_method):
        argparse.ArgumentParser.__init__(self, formatter_class=argparse.RawDescriptionHelpFormatter)
        self.add_argument('--version', action=version.VersionAction)
        # --test is used internally to implement “make test(-installed)”; do not use directly
        self.add_argument('--test', nargs=argparse.REMAINDER, action=TestAction, help=argparse.SUPPRESS)
        p_separate = self.add_subparser('separate', help='generate masks for images')
        p_encode = self.add_subparser('encode', help='convert images to single-page DjVu documents')
        p_bundle = self.add_subparser('bundle', help='convert images to bundled multi-page DjVu document')
        epilog = []
        default = self.defaults
        for p in p_separate, p_encode, p_bundle:
            epilog += ['{prog} --help'.format(prog=p.prog)]
            p.add_argument('-o', '--output', metavar='FILE', help='output filename')
            if p is p_bundle:
                p.add_argument(
                    '--page-id-template', metavar='TEMPLATE', default=default.page_id_template,
                    help='naming scheme for page identifiers (default: "{template}")'.format(template=default.page_id_template)
                )
                p.add_argument(
                    '--pageid-template', dest='page_id_template', metavar='TEMPLATE',
                    help=argparse.SUPPRESS
                )  # obsolete alias
            else:
                p.add_argument(
                    '--output-template', metavar='TEMPLATE',
                    help='naming scheme for output file (e.g. "{template}")'.format(template=default.page_id_template)
                )
            p.add_argument('--losslevel', dest='loss_level', type=losslevel_type, help=argparse.SUPPRESS)
            p.add_argument(
                '--loss-level', dest='loss_level', type=losslevel_type, metavar='N',
                help='aggressiveness of lossy compression'
            )
            p.add_argument(
                '--lossless', dest='loss_level', action='store_const', const=djvu.LOSS_LEVEL_MIN,
                help='lossless compression (default)'
            )
            p.add_argument(
                '--clean', dest='loss_level', action='store_const', const=djvu.LOSS_LEVEL_CLEAN,
                help='lossy compression: remove flyspecks'
            )
            p.add_argument(
                '--lossy', dest='loss_level', action='store_const', const=djvu.LOSS_LEVEL_LOSSY,
                help='lossy compression: substitute patterns with small variations'
            )
            if p is not p_separate:
                p.add_argument('--masks', nargs='+', metavar='MASK', help='use pre-generated masks')
                p.add_argument('--mask', action='append', dest='masks', metavar='MASK', help='use a pre-generated mask')
                for layer, layer_name in ('fg', 'foreground'), ('bg', 'background'):
                    if layer == 'fg':
                        def_slices = get_slice_repr(default.fg_slices)
                        p.add_argument(
                            '--fg-slices', type=slice_type(1), metavar='N',
                            help='number of slices for foreground (default: {slices})'.format(slices=def_slices)
                        )
                    else:
                        def_slices = get_slice_repr(default.bg_slices)
                        p.add_argument(
                            '--bg-slices', type=slice_type(), metavar='N+...+N',
                            help='number of slices in each background chunk (default: {slices})'.format(slices=def_slices)
                        )
                    default_crcb = getattr(default, '{lr}_crcb'.format(lr=layer))
                    p.add_argument(
                        '--{lr}-crcb'.format(lr=layer), choices=map(str, djvu.CRCB.values),
                        help='chrominance encoding for {layer} (default: {crcb})'.format(layer=layer_name, crcb=default_crcb)
                    )
                    default_subsample = getattr(default, '{lr}_subsample'.format(lr=layer))
                    p.add_argument(
                        '--{lr}-subsample'.format(lr=layer), type=subsample_type, metavar='N',
                        help='subsample ratio for {layer} (default: {n})'.format(layer=layer_name, n=default_subsample)
                    )
                p.add_argument('--fg-bg-defaults', help=argparse.SUPPRESS, action='store_const', const=1)
            if p is not p_separate:
                p.add_argument(
                    '-d', '--dpi', type=dpi_type, metavar='N',
                    help='image resolution (default: {dpi})'.format(dpi=djvu.DPI_DEFAULT)
                )
            if p is p_bundle:
                p.add_argument(
                    '-p', '--pages-per-dict', type=int, metavar='N',
                    help='how many pages to compress in one pass (default: {n})'.format(n=default.pages_per_dict)
                )
            p.add_argument(
                '-m', '--method', choices=methods, metavar='METHOD', type=replace_underscores, default=default_method,
                help='binarization method (default: {method})'.format(method=default_method)
            )
            p.add_argument(
                '-x', '--param', action='append', dest='params', metavar='NAME[=VALUE]',
                help='binarization method parameter (can be given more than once)'
            )
            if p is p_encode or p is p_bundle:
                p.add_argument('--xmp', action='store_true', help='create sidecar XMP metadata (experimental!)')
            p.add_argument(
                '-v', '--verbose', dest='verbosity', action='append_const', const=None,
                help='more informational messages'
            )
            p.add_argument(
                '-q', '--quiet', dest='verbosity', action='store_const', const=[],
                help='no informational messages'
            )
            p.add_argument('input', metavar='IMAGE', nargs='+')
            p.set_defaults(
                masks=[],
                fg_bg_defaults=None,
                loss_level=djvu.LOSS_LEVEL_MIN,
                pages_per_dict=default.pages_per_dict,
                dpi=default.dpi,
                fg_slices=intact(default.fg_slices),
                bg_slices=intact(default.bg_slices),
                fg_crcb=intact(default.fg_crcb),
                bg_crcb=intact(default.bg_crcb),
                fg_subsample=intact(default.fg_subsample),
                bg_subsample=intact(default.bg_subsample),
                verbosity=[None],
                xmp=False,
            )
            p.epilog = _get_method_params_help(methods)
        self.epilog = 'more help:\n  ' + '\n  '.join(epilog)
        self.__methods = methods

    def add_subparser(self, name, **kwargs):
        try:
            self.__subparsers
        except AttributeError:
            self.__subparsers = self.add_subparsers(parser_class=argparse.ArgumentParser)
        kwargs.setdefault('formatter_class', argparse.RawDescriptionHelpFormatter)
        p = self.__subparsers.add_parser(name, **kwargs)
        p.set_defaults(_action_=name)
        return p

    def _parse_params(self, options):
        o = options
        result = {}
        for param in o.params or ():
            if '=' not in param:
                if param.isdigit() and len(o.method.args) == 1:
                    [pname] = o.method.args
                    pvalue = param
                else:
                    pname = param
                    pvalue = True
            else:
                [pname, pvalue] = param.split('=', 1)
            pname = replace_underscores(pname)
            try:
                arg = o.method.args[pname]
            except KeyError:
                self.error('invalid parameter name {0!r}'.format(pname))
            try:
                if (pvalue is True) and (arg.type is not bool):
                    raise ValueError
                pvalue = arg.type(pvalue)
            except ValueError:
                self.error('invalid parameter {0} value: {1!r}'.format(pname, pvalue))
            if (arg.min is not None) and pvalue < arg.min:
                self.error('parameter {0} must be >= {1}'.format(pname, arg.min))
            if (arg.max is not None) and pvalue > arg.max:
                self.error('parameter {0} must be <= {1}'.format(pname, arg.max))
            result[arg.name] = pvalue
        for arg in o.method.args.itervalues():
            if (not arg.has_default) and (arg.name not in result):
                self.error('parameter {0} is not set'.format(arg.name))
        return result

    def parse_args(self, actions):
        o = argparse.ArgumentParser.parse_args(self)
        if o.fg_bg_defaults is None:
            for layer in 'fg', 'bg':
                namespace = argparse.Namespace()
                setattr(o, '{lr}_options'.format(lr=layer), namespace)
                for facet in 'slices', 'crcb', 'subsample':
                    attrname = '{lr}_{facet}'.format(lr=layer, facet=facet)
                    value = getattr(o, attrname)
                    if isinstance(value, intact):
                        value = value()
                    else:
                        o.fg_bg_defaults = False
                    setattr(namespace, facet, value)
                    delattr(o, attrname)
                if isinstance(namespace.crcb, str):
                    namespace.crcb = getattr(djvu.CRCB, namespace.crcb)
        if o.fg_bg_defaults is not False:
            o.fg_bg_defaults = True
        o.verbosity = len(o.verbosity)
        if o.pages_per_dict <= 1:
            o.pages_per_dict = 1
        action = getattr(actions, vars(o).pop('_action_'))
        o.method = self.__methods[o.method]
        o.params = self._parse_params(o)
        try:
            if o.xmp and not xmp.backend:
                raise xmp.import_error  # pylint: disable=raising-bad-type
        except AttributeError:
            pass
        return action(o)

def dump_options(o, multipage=False):
    method_name = o.method.name
    if o.params:
        method_name += ' '
        method_name += ' '.join(
            '{0}={1}'.format(pname, pvalue)
            for pname, pvalue
            in sorted(o.params.iteritems())
        )
    yield ('method', method_name)
    if multipage:
        yield ('pages-per-dict', o.pages_per_dict)
    yield ('loss-level', o.loss_level)
    if o.fg_bg_defaults:
        yield ('fg-bg-defaults', True)
    else:
        for layer_name in 'fg', 'bg':
            layer = getattr(o, layer_name + '_options')
            yield (layer_name + '-crcb', str(layer.crcb))
            yield (layer_name + '-slices', get_slice_repr(layer.slices))
            yield (layer_name + '-subsample', layer.subsample)

__all__ = ['ArgumentParser', 'dump_options']

# vim:ts=4 sts=4 sw=4 et
