# encoding=UTF-8

# Copyright © 2009 Jakub Wilk <ubanus@users.sf.net>
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

import sys

from . import cli_framework as cli
from . import djvu_extra as djvu

class DpiType(cli.IntType):

    min = 72
    max = 6000

class SubsampleType(cli.IntType):

    min = 1
    max = 12

class LossLevelType(cli.IntType):

    min = 0
    max = 200

class CrcbType(cli.ChoiceType):

    metavar = 'crcb'
    choices = dict(
        normal = djvu.CRCB_NORMAL,
        half = djvu.CRCB_HALF,
        full = djvu.CRCB_FULL,
        none = djvu.CRCB_NONE
    )

class SlicesType(cli.ArgType):

    metavar = 'n+...+n'
    max_slices = None

    def __init__(self, parser):
        cli.ArgType.__init__(self, parser)

    def __call__(self, value):
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
        if self.max_slices is not None and len(result) > self.max_slices:
            raise cli.BadOption('too many slices')
        return result

class SingleSliceType(SlicesType):

    metavar = 'n'
    max_slices = 1

class MethodType(cli.ChoiceType):

    metavar = 'method'

    @property
    def choices(self):
        return self.parser.methods

class IW44Options(object):

    subsample = 3
    slices = djvu.IW44_DEFAULT_SLICES
    crcb = djvu.CRCB_NORMAL

    def __init__(self, **options):
        self.__dict__.update(options)

class OptionParser(cli.OptionParser):

    usage_template = '''%(argv0)s [options] <input-image> [mask-image]'''

    @property
    def show_all_options(self):
        return self.verbosity > 1

    def __init__(self, argv, version, methods, default_method):
        self.version = version
        self.jb2_loss_level = 1
        self.fg_bg_defaults = True
        self.fg_options = IW44Options(slices=[100], crcb=djvu.CRCB_FULL, subsample=6)
        self.bg_options = IW44Options(slices=[72, 82, 88, 95])
        self.output = sys.stdout
        self.method = default_method
        self.dpi = None
        self.verbosity = 1
        try:
            cli.OptionParser.__init__(self, argv)
        except cli.BadOption, ex:
            print >>sys.stderr, 'Error: %s\n' % ex
            self.display_help(sys.stderr, options=True)
            sys.exit(1)
        except cli.BadArguments, ex:
            print >>sys.stderr, 'Error: %s\n' % ex
            self.display_help(sys.stderr, options=False)
            sys.exit(1)

    def handle_args(self, image_filename, mask_filename=None):
        self.image_filename = image_filename
        self.mask_filename = mask_filename

    @cli.option('-o', '--output', type=cli.StringType, metavar='file')
    def set_output(self, value):
        self.output = file(value, 'w+b')

    @cli.option('--losslevel', type=LossLevelType, hidden=True)
    @cli.option('--loss-level', type=LossLevelType)
    def opt_loss_level(self, value):
        self.jb2_loss_level = value

    @cli.option('--lossless', hidden=True)
    def opt_lossless(self):
        self.jb2_loss_level = 0

    @cli.option('--clean', hidden=True)
    def opt_clean(self):
        self.jb2_loss_level = 1

    @cli.option('--lossy', hidden=True)
    def opt_lossy(self):
        self.jb2_loss_level = 100

    @cli.option('--fg-slices', type=SingleSliceType)
    def opt_fg_slices(self, value):
        self.fg_options.slices = value
        self.fg_bg_defaults = False

    @cli.option('--bg-slices', type=SlicesType)
    def opt_bg_slices(self, value):
        self.bg_options.slices = value
        self.fg_bg_defaults = False

    @cli.option('--fg-subsample', type=SubsampleType)
    def opt_fg_subsample(self, value):
        self.fg_options.subsample = value
        self.fg_bg_defaults = False

    @cli.option('--bg-subsample', type=SubsampleType)
    def opt_bg_subsample(self, value):
        self.bg_options.subsample = value
        self.fg_bg_defaults = False

    @cli.option('--fg-crcb', type=CrcbType)
    def opt_fg_crcb(self, value):
        self.fg_options.crcb = value
        self.fg_bg_defaults = False

    @cli.option('--bg-crcb', type=CrcbType)
    def opt_bg_crcb(self, value):
        self.bg.options.crcb = value
        self.fg_bg_defaults = False

    @cli.option('--crcb', type=CrcbType)
    def opt_crcb(self, value):
        self.fg_options.crcb = value
        self.bg_options.crcb = value
        self.fg_bg_defaults = False

    @cli.option('--fg-bg-defaults', hidden=True)
    def opt_fg_bg_defaults(self):
        self.fg_bg_defaults = True

    @cli.option('-d', '--dpi', type=DpiType)
    def opt_dpi(self, value):
        self.dpi = value

    @cli.option('-m', '--method', type=MethodType)
    def set_method(self, value):
        self.method = value

    @cli.option('-v', '--verbose')
    def set_verbose(self):
        self.verbosity += 1

    @cli.option('-q', '--quiet')
    def set_quiet(self):
        self.verbosity = 0

__all__ = ['OptionParser']

# vim:ts=4 sw=4 et
