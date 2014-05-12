# encoding=UTF-8

# Copyright © 2009, 2010, 2011, 2012, 2013 Jakub Wilk <jwilk@jwilk.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

from __future__ import with_statement

import itertools
import os
import re
import logging
import sys

from . import cli
from . import djvu_extra as djvu
from . import filetype
from . import gamera_extra as gamera
from . import ipc
from . import templates
from . import temporary

try:
    from . import xmp
except ImportError:
    xmp = None

logger = None

def setup_logging():
    global logger
    logger = logging.getLogger('didjvu.main')
    ipc_logger = logging.getLogger('didjvu.ipc')
    logging.NOSY = (logging.INFO + logging.DEBUG) // 2
    def nosy(msg, *args, **kwargs):
        logger.log(logging.NOSY, msg, *args, **kwargs)
    logger.nosy = nosy
    # Main handler:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    # IPC handler:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('+ %(message)s')
    handler.setFormatter(formatter)
    ipc_logger.addHandler(handler)

def parallel_for(o, f, *iterables):
    for args in zip(*iterables):
        f(o, *args)

def check_tty():
    if sys.stdout.isatty():
        print >>sys.stderr, 'I won\'t write binary data to a terminal.'
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
    # TODO: Optimize, perhaps using Cython.
    ratio = options.subsample
    subsampled_size = get_subsampled_dim(mask, ratio)
    mask = mask.to_greyscale()
    mask = mask.threshold(254)
    mask = mask.erode()
    subsampled_image = gamera.Image((0, 0), subsampled_size, pixel_type=gamera.RGB)
    subsampled_mask = gamera.Image((0, 0), subsampled_size, pixel_type=gamera.ONEBIT)
    y0 = 0
    width, height = image.ncols, image.nrows
    image = image.to_rgb()
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
                    pt = gamera.Point(x, y)
                    if mask_get(pt):
                        n += 1
                        pixel = image_get(pt)
                        r += pixel.red
                        g += pixel.green
                        b += pixel.blue
                    x += 1
                y += 1
            pt = gamera.Point(sx, sy)
            if n > 0:
                r = (r + n // 2) // n
                g = (g + n // 2) // n
                b = (b + n // 2) // n
                subsampled_image_set(pt, gamera.RGBPixel(r, g , b))
            else:
                subsampled_mask_set(pt, 1)
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
        image=gamera.to_pil_rgb(image), mask_image=gamera.to_pil_1bpp(mask),
        slices=options.slices, crcb=options.crcb
    )

def image_to_djvu(width, height, image, mask, options):
    dpi = options.dpi
    loss_level = options.loss_level
    if options.pages_per_dict > 1:
        # XXX This should probably go the other way round: we run minidjvu
        # first, and then reuse its masks.
        loss_level = 0
    sjbz = djvu.bitonal_to_djvu(gamera.to_pil_1bpp(mask), loss_level=loss_level)
    if options.fg_bg_defaults:
        image = gamera.to_pil_rgb(image)
        return djvu.Multichunk(width, height, dpi, image=image, sjbz=sjbz)
    else:
        fg_djvu = make_layer(image, mask, subsample_fg, options.fg_options)
        bg_djvu = make_layer(image, mask, subsample_bg, options.bg_options)
        fg44, bg44 = map(djvu.djvu_to_iw44, [fg_djvu, bg_djvu])
        return djvu.Multichunk(width, height, dpi, fg44=fg44, bg44=bg44, sjbz=sjbz)

def generate_mask(filename, image, method):
    '''
    Generate mask using the provided method (if filename is not None);
    or simply load it from file (if filename is not None).
    '''
    if filename is None:
        return method(image)
    else:
        return gamera.load_image(filename)

_pageid_chars = re.compile('^[A-Za-z0-9_+.-]+$').match

def check_pageid_sanity(pageid):
    if not _pageid_chars(pageid):
        raise ValueError('Pageid must consist only of lowercase ASCII letters, digits, _, +, - and dot.')
    if pageid[:1] in ('.', '+', '-'):
        raise ValueError('Pageid cannot start with +, - or a dot.')
    if '..' in pageid:
        raise ValueError('Pageid cannot contain two consecutive dots.')
    assert pageid == os.path.basename(pageid)
    if pageid.endswith('.djvu'):
        return pageid
    else:
        raise ValueError('Pageid must end with the .djvu extension.')

def replace_ext(filename, ext):
    return '%s.%s' % (os.path.splitext(filename)[0], ext)

class namespace():
    pass

class main():

    compression_info_template = \
        '%(bits_per_pixel).3f bits/pixel; ' \
        '%(ratio).3f:1, %(percent_saved).2f%% saved, ' \
        '%(bytes_in)d bytes in, %(bytes_out)d bytes out'

    def __init__(self):
        setup_logging()
        parser = cli.ArgumentParser(gamera.methods, default_method='djvu')
        parser.parse_args(actions=self)

    def check_common(self, o):
        if len(o.masks) == 0:
            o.masks = [None for x in o.input]
        elif len(o.masks) != len(o.input):
            raise ValueError('%d input images != %d masks' % (len(o.input), len(o.masks)))
        ipc_logger = logging.getLogger('didjvu.ipc')
        assert logger is not None
        log_level = {
            0: logging.WARNING,
            1: logging.INFO,
            2: logging.NOSY,
        }.get(o.verbosity, logging.DEBUG)
        logger.setLevel(log_level)
        ipc_logger.setLevel(log_level)
        gamera.init()

    def check_multi_output(self, o):
        self.check_common(o)
        if o.output is None:
            if o.output_template is not None:
                o.output = [templates.expand(o.output_template, f, n) for n, f in enumerate(o.input)]
                o.xmp_output = [s + '.xmp' if o.xmp else None for s in o.output]
            elif len(o.input) == 1:
                o.output = [sys.stdout]
                o.xmp_output = [None]
                check_tty()
            else:
                raise ValueError("cannot output multiple files to stdout")
        else:
            if len(o.input) == 1:
                o.xmp_output = [o.output + '.xmp'] if o.xmp else [None]
                o.output = [o.output]
            else:
                raise ValueError("cannot output multiple files to a single file")
        assert len(o.masks) == len(o.output) == len(o.input)
        o.output = (
            open(f, 'wb') if isinstance(f, basestring) else f
            for f in o.output
        )
        o.xmp_output = (
            open(f, 'wb') if isinstance(f, basestring) else f
            for f in o.xmp_output
        )

    def check_single_output(self, o):
        self.check_common(o)
        if o.output is None:
            o.output = [sys.stdout]
            o.xmp_output = [None]
            check_tty()
        else:
            filename = o.output
            o.output = [file(filename, 'wb')]
            o.xmp_output = [file(filename + '.xmp', 'wb')] if o.xmp else [None]
        assert len(o.output) == len(o.xmp_output) == 1

    def encode(self, o):
        self.check_multi_output(o)
        parallel_for(o, self.encode_one, o.input, o.masks, o.output, o.xmp_output)

    def encode_one(self, o, image_filename, mask_filename, output, xmp_output):
        bytes_in = os.path.getsize(image_filename)
        logger.info('%s:' % image_filename)
        ftype = filetype.check(image_filename)
        if ftype.like(filetype.djvu):
            if ftype.like(filetype.djvu_single):
                logger.info('- copying DjVu as is')
                with open(image_filename, 'rb') as djvu_file:
                    copy_file(djvu_file, output)
            else:
                # TODO: Figure out how many pages the multi-page document
                # consist of. If it's only one, continue.
                raise NotImplementedError("I don't know what to do with this file")
            return
        logger.info('- reading image')
        image = gamera.load_image(image_filename)
        width, height = image.ncols, image.nrows
        logger.nosy('- image size: %d x %d', width, height)
        mask = generate_mask(mask_filename, image, o.method)
        if xmp_output:
            n_connected_components = len(mask.cc_analysis())
        logger.info('- converting to DjVu')
        djvu_doc = image_to_djvu(width, height, image, mask, options=o)
        djvu_file = djvu_doc.save()
        try:
            bytes_out = copy_file(djvu_file, output)
        finally:
            djvu_file.close()
        bits_per_pixel = 8.0 * bytes_out / (width * height)
        ratio = 1.0 * bytes_in / bytes_out
        percent_saved = (1.0 * bytes_in - bytes_out) * 100 / bytes_in
        logger.info('- %s', self.compression_info_template % locals())
        if xmp_output:
            logger.info('- saving XMP metadata')
            metadata = xmp.metadata()
            metadata.import_(image_filename)
            internal_properties = list(cli.dump_options(o)) + [
                ('n-connected-components', str(n_connected_components))
            ]
            metadata.update(
                media_type='image/vnd.djvu',
                internal_properties=internal_properties,
            )
            metadata.write(xmp_output)

    def separate_one(self, o, image_filename, output):
        logger.info('%s:', image_filename)
        ftype = filetype.check(image_filename)
        if ftype.like(filetype.djvu):
            # TODO: Figure out how many pages the document consist of.
            # If it's only one, extract the existing mask.
            raise NotImplementedError("I don't know what to do with this file")
        logger.info('- reading image')
        image = gamera.load_image(image_filename)
        width, height = image.ncols, image.nrows
        logger.nosy('- image size: %d x %d' % (width, height))
        logger.info('- thresholding')
        mask = generate_mask(None, image, o.method)
        logger.info('- saving')
        if output is not sys.stdout:
            # A real file
            mask.save_PNG(output.name)
        else:
            tmp_output = temporary.file(suffix='.png')
            try:
                mask.save_PNG(tmp_output.name)
                copy_file(tmp_output, output)
            finally:
                tmp_output.close()

    def separate(self, o):
        self.check_multi_output(o)
        for mask in o.masks:
            assert mask is None
        parallel_for(o, self.separate_one, o.input, o.output)

    def bundle(self, o):
        self.check_single_output(o)
        if o.pages_per_dict <= 1:
            self.bundle_simple(o)
        else:
            self.bundle_complex(o)
        [xmp_output] = o.xmp_output
        if xmp_output:
            logger.info('saving XMP metadata')
            metadata = xmp.metadata()
            internal_properties = list(cli.dump_options(o, multipage=True))
            metadata.update(
                media_type='image/vnd.djvu',
                internal_properties=internal_properties,
            )
            metadata.write(xmp_output)

    def _bundle_simple_page(self, o, input, mask, component_name):
        with open(component_name, 'wb') as component:
            self.encode_one(o, input, mask, component, None)

    def bundle_simple(self, o):
        [output] = o.output
        with temporary.directory() as tmpdir:
            bytes_in = 0
            component_filenames = []
            for page, (input, mask) in enumerate(zip(o.input, o.masks)):
                bytes_in += os.path.getsize(input)
                pageid = templates.expand(o.pageid_template, input, page)
                # TODO: Check for filename conflicts.
                check_pageid_sanity(pageid)
                component_filenames += os.path.join(tmpdir, pageid),
            parallel_for(o, self._bundle_simple_page, o.input, o.masks, component_filenames)
            logger.info('bundling')
            djvu_file = djvu.bundle_djvu(*component_filenames)
            try:
                bytes_out = copy_file(djvu_file, output)
            finally:
                djvu_file.close()
        bits_per_pixel = float('nan') # FIXME!
        ratio = 1.0 * bytes_in / bytes_out
        percent_saved = (1.0 * bytes_in - bytes_out) * 100 / bytes_in
        logger.nosy(self.compression_info_template % locals())

    def _bundle_complex_page(self, o, page, minidjvu_in_dir, image_filename, mask_filename, pixels):
        logger.info('%s:', image_filename)
        ftype = filetype.check(image_filename)
        if ftype.like(filetype.djvu):
            # TODO: Allow to merge existing documents (even multi-page ones).
            raise NotImplementedError("I don't know what to do with this file")
        logger.info('- reading image')
        image = gamera.load_image(image_filename)
        width, height = image.ncols, image.nrows
        pixels[0] += width * height
        logger.nosy('- image size: %d x %d', width, height)
        mask = generate_mask(mask_filename, image, o.method)
        logger.info('- converting to DjVu')
        page.djvu = image_to_djvu(width, height, image, mask, options=o)
        image = mask = None
        page.sjbz = djvu.Multichunk(width, height, o.dpi, sjbz=page.djvu['sjbz'])
        page.sjbz_symlink = os.path.join(minidjvu_in_dir, page.pageid)
        os.symlink(page.sjbz.save().name, page.sjbz_symlink)

    def bundle_complex(self, o):
        [output] = o.output
        with temporary.directory() as minidjvu_in_dir:
            bytes_in = 0
            pixels = [0]
            page_info = []
            for pageno, (image_filename, mask_filename) in enumerate(zip(o.input, o.masks)):
                page = namespace()
                page_info += page,
                bytes_in += os.path.getsize(image_filename)
                page.pageid = templates.expand(o.pageid_template, image_filename, pageno)
                check_pageid_sanity(page.pageid)
                # TODO: Check for filename conflicts.
            parallel_for(o, self._bundle_complex_page,
                page_info,
                itertools.repeat(minidjvu_in_dir),
                o.input,
                o.masks,
                itertools.repeat(pixels)
            )
            [pixels] = pixels
            with temporary.directory() as minidjvu_out_dir:
                logger.info('creating shared dictionaries')
                def chdir():
                    os.chdir(minidjvu_out_dir)
                arguments = ['minidjvu',
                    '--indirect',
                    '--aggression', str(o.loss_level),
                    '--pages-per-dict', str(o.pages_per_dict),
                ]
                arguments += [page.sjbz_symlink for page in page_info]
                index_filename = temporary.name(prefix='__index__.', suffix='.djvu', dir=minidjvu_out_dir)
                index_filename = os.path.basename(index_filename) # FIXME: Name conflicts are still possible!
                arguments += [index_filename]
                ipc.Subprocess(arguments, preexec_fn=chdir).wait()
                os.remove(os.path.join(minidjvu_out_dir, index_filename))
                component_filenames = []
                for pageno, page in enumerate(page_info):
                    if pageno % o.pages_per_dict == 0:
                        iff_name = replace_ext(page_info[pageno].pageid, 'iff')
                        iff_name = os.path.join(minidjvu_out_dir, iff_name)
                        component_filenames += [iff_name]
                    sjbz_name = os.path.join(minidjvu_out_dir, page.pageid)
                    component_filenames += [sjbz_name]
                    page.djvu['sjbz'] = sjbz_name
                    page.djvu['incl'] = iff_name
                    page.djvu = page.djvu.save()
                    page.djvu_symlink = os.path.join(minidjvu_out_dir, page.pageid)
                    os.unlink(page.djvu_symlink)
                    os.symlink(page.djvu.name, page.djvu_symlink)
                logger.info('bundling')
                djvu_file = djvu.bundle_djvu(*component_filenames)
                try:
                    bytes_out = copy_file(djvu_file, output)
                finally:
                    djvu_file.close()
        bits_per_pixel = 8.0 * bytes_out / pixels
        ratio = 1.0 * bytes_in / bytes_out
        percent_saved = (1.0 * bytes_in - bytes_out) * 100 / bytes_in
        logger.nosy('%s', self.compression_info_template % locals())

# vim:ts=4 sw=4 et
