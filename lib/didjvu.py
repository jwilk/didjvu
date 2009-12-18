#!/usr/bin/python
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

import os
import sys

import Image

from . import gamera_extra as gamera
from . import djvu_extra as djvu
from . import cli
from . import tinylog

__version__ = '0.1'

def check_tty():
    if sys.stdout.isatty():
        print >>sys.stderr, 'I won\'t write DjVu data to a terminal.'
        sys.exit(1)

def copy_file(input_file, output_file):
    length = 0
    while 1:
        block = input_file.read(0x1000)
        if not block:
            break
        length += len(block)
        output_file.write(block)
    return length

def get_subsampled_dim(image, subsample):
    width = (image.ncols + subsample - 1) // subsample
    height = (image.nrows + subsample - 1) // subsample
    return gamera.Dim(width, height)

def subsample_fg(image, mask, options):
    ratio = options.subsample
    subsampled_size = get_subsampled_dim(mask, ratio)
    mask = mask.to_greyscale()
    mask = mask.threshold(254)
    mask = mask.erode()
    subsampled_image = gamera.Image((0, 0), subsampled_size, pixel_type=gamera.RGB)
    subsampled_mask = gamera.Image((0, 0), subsampled_size, pixel_type=gamera.ONEBIT)
    y0 = 0
    width, height = image.ncols, image.nrows
    image_get = image.get
    mask_get = mask.get
    subsampled_image_set = subsampled_image.set
    subsampled_mask_set = subsampled_mask.set
    for sy in xrange(0, subsampled_image.nrows):
        x0 = 0
        for sx in xrange(0, subsampled_image.ncols):
            n = r = g = b = 0
            y = y0
            for dy in xrange(ratio):
                if y >= height:
                    break
                x = x0
                for dx in xrange(ratio):
                    if x >= width:
                        break
                    pt = (x, y)
                    if mask_get(pt):
                        n += 1
                        pixel = image_get(pt)
                        r += pixel.red
                        g += pixel.green
                        b += pixel.blue
                    x += 1
                y += 1
            if n > 0:
                r = (r + n // 2) // n
                g = (g + n // 2) // n
                b = (b + n // 2) // n
                subsampled_image_set((sx, sy), gamera.RGBPixel(r, g , b))
            else:
                subsampled_mask_set((sx, sy), 1)
            x0 += ratio
        y0 += ratio
    return subsampled_image, subsampled_mask

def subsample_bg(image, mask, options):
    dim = get_subsampled_dim(mask, options.subsample)
    mask = mask.to_greyscale()
    mask = mask.resize(dim, 0)
    mask = mask.dilate().dilate()
    mask = mask.threshold(254)
    image = image.resize(dim, 1)
    return image, mask

def make_layer(image, mask, subsampler, options):
    image, mask = subsampler(image, mask, options)
    return djvu.photo_to_djvu(
        image=image.to_pil(), mask_image=gamera.to_pil_1bpp(mask),
        slices=options.slices, crcb=options.crcb
    )

def main():
    options = cli.OptionParser(
        argv=sys.argv, version=__version__,
        methods=gamera.methods, default_method=gamera.methods['djvu']
    )
    djvu.DEBUG = options.verbosity >= 2
    log = tinylog.Log(options.verbosity)
    if options.output is sys.stdout:
        check_tty()
    gamera.init()
    image_filename = options.image_filename
    bytes_in = os.path.getsize(image_filename)
    print >>log(1), '%s:' % image_filename
    print >>log(1), '- reading image'
    image = gamera.from_pil(Image.open(image_filename))
    width, height = image.ncols, image.nrows
    print >>log(2), '- image size: %d x %d' % (width, height)
    if options.mask_filename is None:
        method = options.method
        pixel_types = method.self_type.pixel_types
        t_image = image
        if image.data.pixel_type not in pixel_types:
            if gamera.RGB in pixel_types:
                t_image = image.to_rgb()
            elif gamera.GREYSCALE in pixel_types:
                t_image = image.to_greyscale()
        print >>log(1), '- thresholding'
        mask = options.method()(t_image)
    else:
        mask = gamera.load_image(options.mask_filename)
    print >>log(1), '- converting to DjVu'
    dpi = options.dpi or 300
    sjbz_file = djvu.bitonal_to_djvu(gamera.to_pil_1bpp(mask), loss_level=options.jb2_loss_level)
    if options.fg_bg_defaults:
        image = image.to_pil()
        djvu_file = djvu.assemble_djvu(width, height, dpi, sjbz=sjbz_file, image=image)
    else:
        fg_djvu = make_layer(image, mask, subsample_fg, options.fg_options)
        bg_djvu = make_layer(image, mask, subsample_bg, options.bg_options)
        fg44, bg44 = map(djvu.djvu_to_iw44, [fg_djvu, bg_djvu])
        djvu_file = djvu.assemble_djvu(width, height, dpi, fg44=fg44, bg44=bg44, sjbz=sjbz_file)
    try:
        bytes_out = copy_file(djvu_file, options.output)
    finally:
        djvu_file.close()
    bits_per_pixel = 8.0 * bytes_out / (width * height)
    ratio = 1.0 * bytes_in / bytes_out
    percent_saved = (1.0 * bytes_in - bytes_out) * 100 / bytes_in;
    print >>log(2), '- %(bits_per_pixel).3f bits/pixel; %(ratio).3f:1, %(percent_saved).2f%% saved, %(bytes_in)d bytes in, %(bytes_out)d bytes out' % locals()

# vim:ts=4 sw=4 et
