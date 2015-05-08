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

import os
import StringIO as stringio

from . common import (
    assert_equal,
    assert_true
)

from PIL import Image as pil

from lib import ipc
from lib import djvu_extra as djvu

datadir = os.path.join(os.path.dirname(__file__), 'data')

def assert_image_sizes_equal(i1, i2):
    assert_equal(i1.size, i2.size)

def assert_images_equal(i1, i2):
    assert_equal(i1.size, i2.size)
    assert_true(
        list(i1.getdata()) ==
        list(i2.getdata()),
        msg='images are not equal'
    )

def ddjvu(djvu_file, fmt='ppm'):
    ddjvu = ipc.Subprocess(
        ['ddjvu', '-1', '-format=' + fmt],
        stdin=djvu_file,
        stdout=ipc.PIPE,
        stderr=ipc.PIPE
    )
    stdout, stderr = ddjvu.communicate()
    if ddjvu.returncode != 0:
        raise RuntimeError('ddjvu failed')
    if stderr != '':
        raise RuntimeError('ddjvu stderr: ' + stderr)
    out_file = stringio.StringIO(stdout)
    return pil.open(out_file)

def test_bitonal_to_djvu():
    path = os.path.join(datadir, 'onebit.bmp')
    in_image = pil.open(path)
    djvu_file = djvu.bitonal_to_djvu(in_image)
    out_image = ddjvu(djvu_file, fmt='pbm')
    assert_images_equal(in_image, out_image)

def test_photo_to_djvu():
    path = os.path.join(datadir, 'ycbcr-jpeg.tiff')
    in_image = pil.open(path)
    in_image = in_image.convert('RGB')
    mask_image = in_image.convert('1')
    djvu_file = djvu.photo_to_djvu(in_image, mask_image=mask_image)
    out_image = ddjvu(djvu_file, fmt='ppm')
    assert_image_sizes_equal(in_image, out_image)

# vim:ts=4 sts=4 sw=4 et
