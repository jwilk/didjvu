#!/usr/bin/python
# encoding=UTF-8

# Copyright © 2009 Jakub Wilk <jwilk@jwilk.net>
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

import string
import tempfile
import Image

from . import gamera_extra as gamera
from . import djvu_extra as djvu
from . import cli
from . import tinylog
from . import version

formatter = string.Formatter()

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

def get_output_filename(template, name, page):
    base = os.path.basename(name)
    name_ext, _ = os.path.splitext(name)
    base_ext, _ = os.path.splitext(base)
    d = {
        'name': name, 'name-ext': name_ext,
        'base': base, 'base-ext': base_ext,
        'page': page,
    }
    return formatter.format(template, **d)

class main():

    def __init__(self):
        parser = cli.ArgumentParser(gamera.methods, default_method=gamera.methods['djvu'])
        parser.parse_args(actions=self)

    def check_common(self, o):
        djvu.DEBUG = o.verbosity >= 2
        if len(o.masks) == 0:
            o.masks = [None for x in o.input]
        elif len(o.masks) != len(o.input):
            raise ValueError('%d input images != %d masks' % (len(o.input), len(o.masks)))
        self.log = tinylog.Log(o.verbosity)

    def check_multi_output(self, o):
        self.check_common(o)
        if o.output is None:
            if o.output_template is not None:
                o.output = [get_output_filename(o.output_template, f, n) for n, f in enumerate(o.input)]
            elif len(o.input) == 1:
                o.output = [sys.stdout]
                check_tty()
            else:
                raise ValueError("cannot output multiple files to stdout")
        else:
            if len(o.input) == 1:
                o.output = [o.output]
            else:
                raise ValueError("cannot output multiple files to a single file")
        assert len(o.masks) == len(o.output) == len(o.input)
        o.output = (
            open(f, 'wb') if isinstance(f, basestring) else f
            for f in o.output
        )

    def check_single_output(self, o):
        self.check_common(o)
        if o.output is None:
            o.output = [sys.stdout]
            check_tty()
        assert len(o.output) == 1

    def encode(self, o):
        self.check_multi_output(o)
        for input, mask, output in zip(o.input, o.masks, o.output):
            self.encode_one(o, input, mask, output)

    def encode_one(self, o, image_filename, mask_filename, output):
        gamera.init()
        bytes_in = os.path.getsize(image_filename)
        print >>self.log(1), '%s:' % image_filename
        print >>self.log(1), '- reading image'
        image = gamera.from_pil(Image.open(image_filename))
        width, height = image.ncols, image.nrows
        print >>self.log(2), '- image size: %d x %d' % (width, height)
        if mask_filename is None:
            method = o.method
            pixel_types = method.self_type.pixel_types
            t_image = image
            if image.data.pixel_type not in pixel_types:
                if gamera.RGB in pixel_types:
                    t_image = image.to_rgb()
                elif gamera.GREYSCALE in pixel_types:
                    t_image = image.to_greyscale()
            print >>self.log(1), '- thresholding'
            mask = method()(t_image)
        else:
            mask = gamera.load_image(mask_filename)
        print >>self.log(1), '- converting to DjVu'
        dpi = o.dpi
        sjbz_file = djvu.bitonal_to_djvu(gamera.to_pil_1bpp(mask), loss_level=o.loss_level)
        if o.fg_bg_defaults:
            image = image.to_pil()
            djvu_file = djvu.assemble_djvu(width, height, dpi, sjbz=sjbz_file, image=image)
        else:
            fg_djvu = make_layer(image, mask, subsample_fg, o.fg_options)
            bg_djvu = make_layer(image, mask, subsample_bg, o.bg_options)
            fg44, bg44 = map(djvu.djvu_to_iw44, [fg_djvu, bg_djvu])
            djvu_file = djvu.assemble_djvu(width, height, dpi, fg44=fg44, bg44=bg44, sjbz=sjbz_file)
        try:
            bytes_out = copy_file(djvu_file, output)
        finally:
            djvu_file.close()
        bits_per_pixel = 8.0 * bytes_out / (width * height)
        ratio = 1.0 * bytes_in / bytes_out
        percent_saved = (1.0 * bytes_in - bytes_out) * 100 / bytes_in;
        print >>self.log(2), '- %(bits_per_pixel).3f bits/pixel; %(ratio).3f:1, %(percent_saved).2f%% saved, %(bytes_in)d bytes in, %(bytes_out)d bytes out' % locals()

    def separate_one(self, o, image_filename, output):
        gamera.init()
        bytes_in = os.path.getsize(image_filename)
        print >>self.log(1), '%s:' % image_filename
        print >>self.log(1), '- reading image'
        image = gamera.from_pil(Image.open(image_filename))
        width, height = image.ncols, image.nrows
        print >>self.log(2), '- image size: %d x %d' % (width, height)
        method = o.method
        pixel_types = method.self_type.pixel_types
        t_image = image
        if image.data.pixel_type not in pixel_types:
            if gamera.RGB in pixel_types:
                t_image = image.to_rgb()
            elif gamera.GREYSCALE in pixel_types:
                t_image = image.to_greyscale()
        print >>self.log(1), '- thresholding'
        mask = method()(t_image)
        print >>self.log(1), '- saving'
        if output is not sys.stdout:
            # A real file
            mask.save_PNG(output.name)
        else:
            tmp_output = tempfile.NamedTemporaryFile(prefix='didjvu', suffix='.png')
            try:
                mask.save_PNG(tmp_output.name)
                copy_file(tmp_output.name, output)
            finally:
                tmp_output.close()
            mask = gamera.load_image(mask_filename)

    def separate(self, o):
        self.check_multi_output(o)
        for input, mask, output in zip(o.input, o.masks, o.output):
            assert mask is None
            self.separate_one(o, input, output)

    def bundle(self, o):
        self.check_single_output(o)
        [output] = o.output
        raise NotImplementedError

# vim:ts=4 sw=4 et
