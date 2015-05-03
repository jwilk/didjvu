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

from . common import (
    assert_is_instance,
    fork_isolation,
)

from lib import gamera_extra as gamera

def test_load_image():
    datadir = os.path.join(os.path.dirname(__file__), 'data')
    paths = []
    for ext in ['tiff', 'bmp']:
        paths += map(os.path.basename,
            glob.glob(os.path.join(datadir, '*.' + ext))
        )
    @fork_isolation
    def t(path):
        path = os.path.join(datadir, path)
        gamera.init()
        image = gamera.load_image(path)
        assert_is_instance(image, gamera.Image)
    for path in paths:
        yield t, path

# vim:ts=4 sts=4 sw=4 et
