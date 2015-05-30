# encoding=UTF-8

# Copyright © 2015 Jakub Wilk <jwilk@jwilk.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

import cStringIO as io
import collections
import sys

from . common import (
    assert_equal,
    assert_greater,
    assert_is,
    assert_is_none,
    assert_multi_line_equal,
    assert_regexp_matches,
    assert_true,
    exception,
    interim,
)

from lib import cli

class test_range_int():

    def test_lt_min(self):
        t = cli.range_int(37, 42, 'eggs')
        with exception(ValueError, ''):
            t('36')

    def test_min(self):
        t = cli.range_int(37, 42, 'eggs')
        r = t('37')
        assert_equal(r, 37)

    def test_max(self):
        t = cli.range_int(37, 42, 'eggs')
        r = t('42')
        assert_equal(r, 42)

    def test_gt_max(self):
        t = cli.range_int(37, 42, 'eggs')
        with exception(ValueError, ''):
            t('43')

    def test_non_int(self):
        t = cli.range_int(37, 42, 'eggs')
        with exception(ValueError, "invalid literal for int() with base 10: ''"):
            t('')
        with exception(ValueError, "invalid literal for int() with base 10: 'ham'"):
            t('ham')

class test_slice_type():

    def test_non_int(self):
        t = cli.slice_type()
        with exception(ValueError, "invalid literal for int() with base 10: ''"):
            t('')
        with exception(ValueError, "invalid literal for int() with base 10: 'ham'"):
            t('ham')

    def test_negative(self):
        t = cli.slice_type()
        with exception(ValueError, 'invalid slice value'):
            t('-42')

    def test_zero(self):
        t = cli.slice_type()
        r = t('0')
        assert_equal(r, [0])

    def test_zero_1(self):
        t = cli.slice_type(1)
        r = t('0')
        assert_equal(r, [0])

    def test_positive(self):
        t = cli.slice_type()
        r = t('42')
        assert_equal(r, [42])

    def test_positive_1(self):
        t = cli.slice_type(1)
        r = t('42')
        assert_equal(r, [42])

    def test_comma(self):
        t = cli.slice_type()
        r = t('37,42')
        assert_equal(r, [37, 42])

    def test_comma_1(self):
        t = cli.slice_type(1)
        with exception(ValueError, string='too many slices'):
            t('37,42')

    def test_comma_eq(self):
        t = cli.slice_type()
        with exception(ValueError, string='non-increasing slice value'):
            t('37,37')

    def test_comma_lt(self):
        t = cli.slice_type()
        with exception(ValueError, string='non-increasing slice value'):
            t('42,37')

    def test_plus(self):
        t = cli.slice_type()
        r = t('37+5')
        assert_equal(r, [37, 42])

    def test_plus_1(self):
        t = cli.slice_type(1)
        with exception(ValueError, string='too many slices'):
            t('37+5')

    def test_plus_eq(self):
        t = cli.slice_type()
        with exception(ValueError, string='non-increasing slice value'):
            t('37+0')

    def test_plus_lt(self):
        t = cli.slice_type()
        with exception(ValueError, string='non-increasing slice value'):
            t('42+-5')

def test_slice_repr():

    def t(inp, exp):
        t = cli.slice_type()
        r = cli.get_slice_repr(inp)
        assert_equal(r, exp)
        assert_equal(t(r), inp)

    t([0], '0')
    t([42], '42')
    t([23, 37, 42], '23+14+5')

def test_intact():
    x = object()
    intact_x = cli.intact(x)
    assert_is(intact_x(), x)

def test_replace_underscores():
    assert_equal(
        cli.replace_underscores('eggs_ham_spam'),
        'eggs-ham-spam'
    )

class MockActions(object):
    def __getattr__(self, name):
        def f(options):
            return (name, options)
        return f

class MockMethod(object):
    def __init__(self):
        self.args = {}

class test_argument_parser():

    methods = dict(
        abutaleb=MockMethod(),
        djvu=MockMethod(),
    )
    actions = MockActions()

    if sys.version_info >= (2, 7):
        anames = collections.OrderedDict()
    else:
        anames = {}
    anames['separate'] = 1
    anames['encode'] = 1
    anames['bundle'] = 1

    def test_init(self):
        cli.ArgumentParser(self.methods, 'djvu')

    def test_no_args(self):
        stderr = io.StringIO()
        with interim(sys, argv=['didjvu'], stderr=stderr):
            ap = cli.ArgumentParser(self.methods, 'djvu')
            with exception(SystemExit, '2'):
                ap.parse_args({})
        assert_multi_line_equal(
            stderr.getvalue(),
            'usage: didjvu [-h] [--version] {{{actions}}} ...\n'
            'didjvu: error: too few arguments\n'.format(actions=','.join(self.anames))
        )

    def _test_action_no_args(self, action):
        stderr = io.StringIO()
        with interim(sys, argv=['didjvu', action], stderr=stderr):
            ap = cli.ArgumentParser(self.methods, 'djvu')
            with exception(SystemExit, '2'):
                ap.parse_args({})
        assert_regexp_matches(
            (r'(?s)\A'
            'usage: didjvu {action} .*\n'
            'didjvu {action}: error: too few arguments\n'
            r'\Z').format(action=action),
            stderr.getvalue()
        )

    def test_action_no_args(self):
        t = self._test_action_no_args
        yield t, 'separate'
        yield t, 'bundle'
        yield t, 'encode'

    def test_bad_action(self, action='eggs'):
        stderr = io.StringIO()
        with interim(sys, argv=['didjvu', action], stderr=stderr):
            ap = cli.ArgumentParser(self.methods, 'djvu')
            with exception(SystemExit, '2'):
                ap.parse_args({})
        assert_multi_line_equal(
            stderr.getvalue(),
            'usage: didjvu [-h] [--version] {{{actions}}} ...\n'.format(actions=','.join(self.anames)) +
            "didjvu: error: invalid choice: 'eggs' (choose from {actions})\n".format(actions=', '.join(map(repr, self.anames)))
        )

    def _test_action(self, action, *args):
        stderr = io.StringIO()
        argv = ['didjvu', action]
        argv += args
        with interim(sys, argv=argv, stderr=stderr):
            ap = cli.ArgumentParser(self.methods, 'djvu')
            [selected_action, options] = ap.parse_args(self.actions)
        assert_multi_line_equal(stderr.getvalue(), '')
        assert_equal(selected_action, action)
        return options

    def _test_action_defaults(self, action):
        path = 'eggs.png'
        options = self._test_action(action, path)
        assert_equal(options.input, [path])
        assert_equal(options.masks, [])
        assert_is_none(options.output)
        if action == 'bundle':
            assert_equal(options.pageid_template, '{base-ext}.djvu')
        else:
            assert_is_none(options.output_template)
        assert_is_none(options.dpi)
        assert_true(options.fg_bg_defaults)
        assert_equal(options.loss_level, 0)
        assert_equal(options.pages_per_dict, 1)
        assert_is(options.method, self.methods['djvu'])
        assert_equal(options.params, {})
        assert_equal(options.verbosity, 1)
        assert_is(options.xmp, False)

    def test_action_defaults(self):
        t = self._test_action_defaults
        yield t, 'bundle'
        yield t, 'encode'
        yield t, 'separate'

    def _test_help(self, action=None):
        argv = ['didjvu', action, '--help']
        argv = filter(None, argv)
        stdout = io.StringIO()
        with interim(sys, argv=argv, stdout=stdout):
            ap = cli.ArgumentParser(self.methods, 'djvu')
            with exception(SystemExit, '0'):
                ap.parse_args({})
        assert_greater(len(stdout.getvalue()), 0)

    def test_help(self):
        t = self._test_help
        yield t
        yield t, 'bundle'
        yield t, 'encode'
        yield t, 'separate'

# vim:ts=4 sts=4 sw=4 et
