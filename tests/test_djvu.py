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

import StringIO as stringio
import os
import shutil

from . common import (
    assert_equal,
    assert_true
)

from PIL import Image as pil

from lib import djvu_extra as djvu
from lib import ipc
from lib import temporary

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
    if isinstance(djvu_file, basestring):
        djvu_path = djvu_file
    else:
        djvu_path = djvu_file.name
    ddjvu = ipc.Subprocess(
        ['ddjvu', '-1', '-format=' + fmt, djvu_path],
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

def test_multichunk():
    path = os.path.join(datadir, 'onebit.bmp')
    in_image = pil.open(path)
    [width, height] = in_image.size
    sjbz_path = os.path.join(datadir, 'onebit.djvu')
    incl_path = os.path.join(datadir, 'shared_anno.iff')
    multichunk = djvu.Multichunk(width, height, 100, sjbz=sjbz_path, incl=incl_path)
    djvu_file = multichunk.save()
    with temporary.directory() as tmpdir:
        tmp_djvu_path = os.path.join(tmpdir, 'index.djvu')
        tmp_incl_path = os.path.join(tmpdir, 'shared_anno.iff')
        os.link(djvu_file.name, tmp_djvu_path)
        shutil.copyfile(incl_path, tmp_incl_path)
        out_image = ddjvu(tmp_djvu_path, fmt='pbm')
        assert_images_equal(in_image, out_image)

# vim:ts=4 sts=4 sw=4 et
