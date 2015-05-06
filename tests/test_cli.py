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

from . common import (
    assert_equal,
    exception,
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

# vim:ts=4 sts=4 sw=4 et
