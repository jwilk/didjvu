# encoding=UTF-8

# Copyright © 2009, 2010 Jakub Wilk <jwilk@jwilk.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.

'''Bridge to the Gamera framework'''

import os
import re
import sys

from gamera.core import load_image as _load_image
from gamera.core import init_gamera as init
from gamera.core import Image, RGB, GREYSCALE, ONEBIT, Dim, RGBPixel
from gamera.plugins.pil_io import from_pil as _from_pil

try:
    import Image as PIL
except ImportError:
    load_image = _load_image
else:
    def load_image(filename):
        pil_image = PIL.open(filename)
        if pil_image.mode == '1':
            # Gamera supports importing only 8-bit and RGB from PIL:
            pil_image = pil_image.convert('L')
        # TODO: Try to load image without PIL, even if it is imported.
        return _from_pil(pil_image)

def colorspace_wrapper(plugin):

    pixel_types = plugin.self_type.pixel_types

    def new_plugin(image, method=[None]):
        if image.data.pixel_type not in pixel_types:
            if RGB in pixel_types:
                image = image.to_rgb()
            elif GREYSCALE in pixel_types:
                image = image.to_greyscale()
        if method[0] is None:
            method[0] = plugin()
        return method[0](image)

    new_plugin.__name__ = plugin.__name__
    return new_plugin

def _load_methods():
    replace_suffix = re.compile('_threshold$').sub
    class _methods:
        from gamera.plugins.threshold import abutaleb_threshold
        from gamera.plugins.threshold import bernsen_threshold
        from gamera.plugins.threshold import djvu_threshold
        from gamera.plugins.threshold import otsu_threshold
        from gamera.plugins.threshold import tsai_moment_preserving_threshold as tsai
        from gamera.plugins.binarization import gatos_threshold
        from gamera.plugins.binarization import niblack_threshold
        from gamera.plugins.binarization import sauvola_threshold
        from gamera.plugins.binarization import white_rohrer_threshold
    methods = {}
    for name, plugin in vars(_methods).items():
        if name.startswith('_'):
            continue
        name = replace_suffix('', name)
        methods[name] = colorspace_wrapper(plugin)
    return methods

methods = _load_methods()

def to_pil_1bpp(image):
    return image.to_greyscale().to_pil()

# vim:ts=4 sw=4 et
