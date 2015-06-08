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

import glob
import os
import re

from . common import (
    assert_equal,
    assert_images_equal,
    assert_is_instance,
    assert_is_none,
    fork_isolation,
)

from PIL import Image as pil

from lib import gamera_support as gamera

datadir = os.path.join(os.path.dirname(__file__), 'data')

def test_load_image():
    paths = []
    for ext in ['tiff', 'png', 'pgm', 'bmp']:
        paths += map(os.path.basename,
            glob.glob(os.path.join(datadir, '*.' + ext))
        )
    @fork_isolation
    def t(path):
        dpi_match = re.search('dpi([0-9]+)', path)
        path = os.path.join(datadir, path)
        gamera.init()
        image = gamera.load_image(path)
        assert_is_instance(image, gamera.Image)
        if dpi_match is None:
            assert_is_none(image.dpi)
        else:
            dpi = int(dpi_match.group(1))
            assert_is_instance(image.dpi, int)
            assert_equal(image.dpi, dpi)
    for path in paths:
        yield t, path

class test_methods():

    @fork_isolation
    def _test_one_method(self, path, method, args):
        method = gamera.methods[method]
        path = os.path.join(datadir, path)
        gamera.init()
        in_image = gamera.load_image(path)
        bin_image = method(in_image, **args)
        assert_is_instance(bin_image, gamera.Image)
        assert_equal(bin_image.data.pixel_type, gamera.ONEBIT)
        assert_equal(in_image.dim, bin_image.dim)

    def _test_methods(self, path):
        def t(method, args={}):
            return self._test_one_method(path, method, args)
        for method in gamera.methods:
            if method == 'global':
                yield t, method, dict(threshold=42)
            else:
                yield t, method

    def test_color(self):
        for x in self._test_methods('ycbcr-jpeg.tiff'):
            yield x

    def test_grey(self):
        for x in self._test_methods('greyscale-packbits.tiff'):
            yield x

class test_to_pil_rgb():

    @fork_isolation
    def _test(self, path):
        path = os.path.join(datadir, path)
        in_image = pil.open(path)
        if in_image.mode != 'RGB':
            in_image = in_image.convert('RGB')
        assert_equal(in_image.mode, 'RGB')
        gamera.init()
        gamera_image = gamera.load_image(path)
        out_image = gamera.to_pil_rgb(gamera_image)
        assert_images_equal(in_image, out_image)

    def test_color(self):
        self._test('ycbcr-jpeg.tiff')

    def test_grey(self):
        self._test('greyscale-packbits.tiff')

# vim:ts=4 sts=4 sw=4 et
