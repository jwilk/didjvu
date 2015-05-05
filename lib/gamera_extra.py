# encoding=UTF-8

# Copyright © 2009-2015 Jakub Wilk <jwilk@jwilk.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

'''bridge to the Gamera framework'''

import ctypes
import math
import re
import sys
import warnings

from . import utils

try:
    from PIL import Image as PIL
except ImportError, ex:  # <no-coverage>
    utils.enhance_import_error(ex, 'Python Imaging Library', 'python-imaging', 'http://www.pythonware.com/products/pil/')
    raise
else:
    # Gamera (<< 3.4.0) still expects that PIL can be imported as Image
    sys.modules['Image'] = PIL

try:
    import gamera
except ImportError, ex:  # <no-coverage>
    utils.enhance_import_error(ex, 'Gamera', 'python-gamera', 'http://gamera.sourceforge.net/')
    raise
del gamera  # quieten pyflakes

from gamera import __version__ as version
from gamera.core import load_image as _load_image
from gamera.core import init_gamera as _init
from gamera.core import Image, RGB, GREYSCALE, ONEBIT, Point, Dim, RGBPixel
from gamera.plugins.pil_io import from_pil as _from_pil

def has_version(*req_version):
    return tuple(map(int, version.split('.'))) >= req_version

def load_image(filename):
    pil_image = PIL.open(filename)
    [xdpi, ydpi] = pil_image.info.get('dpi', (0, 0))
    if xdpi <= 1 or ydpi <= 1:
        # not reliable
        dpi = None
    else:
        dpi = int(round(
            math.hypot(xdpi, ydpi) /
            math.hypot(1, 1)
        ))
    try:
        # Gamera handles only a few TIFF color modes correctly.
        # https://bugs.debian.org/784374
        if pil_image.mode not in ['1', 'I;16', 'L', 'RGB']:
            raise IOError
        # Gamera supports more TIFF compression formats that PIL.
        # https://mail.python.org/pipermail/image-sig/2003-July/002354.html
        image = _load_image(filename)
    except IOError:
        # Gamera supports importing only 8-bit and RGB from PIL:
        if pil_image.mode == '1':
            pil_image = pil_image.convert('L')
        elif pil_image.mode not in ('RGB', 'L'):
            pil_image = pil_image.convert('RGB')
        assert pil_image.mode in ('RGB', 'L')
        image = _from_pil(pil_image)
    image.dpi = dpi
    return image

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
        # TODO: from gamera.plugins.binarization import gatos_threshold
        from gamera.plugins.binarization import niblack_threshold
        from gamera.plugins.binarization import sauvola_threshold
        from gamera.plugins.binarization import white_rohrer_threshold
        if has_version(3, 3, 1):
            from gamera.plugins.binarization import shading_subtraction
        if has_version(3, 4, 0):
            from gamera.plugins.binarization import brink_threshold
    methods = {}
    for name, plugin in vars(_methods).items():
        if name.startswith('_'):
            continue
        name = replace_suffix('', name)
        name = name.replace('_', '-')
        method = colorspace_wrapper(plugin)
        method.didjvu_name = name
        methods[name] = method
    return methods

methods = _load_methods()

def to_pil_rgb(image):
    # About 20% faster than the standard .to_pil() method of Gamera 3.2.6.
    buffer = ctypes.create_string_buffer(3 * image.ncols * image.nrows)
    image.to_buffer(buffer)
    return PIL.frombuffer('RGB', (image.ncols, image.nrows), buffer, 'raw', 'RGB', 0, 1)

def to_pil_1bpp(image):
    return image.to_greyscale().to_pil()

def _decref(o):  # <no-coverage>
    '''
    Forcibly decrease refcount of the object by 1.
    '''
    libc = ctypes.cdll.LoadLibrary(None)
    memmove = libc.memmove
    memmove.argtypes = [ctypes.py_object, ctypes.py_object, ctypes.c_size_t]
    memmove.restype = ctypes.py_object
    return memmove(o, None, 0)

def _monkeypatch_to_raw_string():  # <no-coverage>
    '''
    Monkey-patch to _to_raw_string plugin function to return objects with
    correct refcounts.
    '''
    from gamera.plugins import _string_io
    old_to_raw_string = _string_io._to_raw_string
    def fixed_to_raw_string(*args, **kwargs):
        o = old_to_raw_string(*args, **kwargs)
        assert sys.getrefcount(o) == 3
        o = _decref(o)
        assert sys.getrefcount(o) == 2
        return o
    _string_io._to_raw_string = fixed_to_raw_string
    Image._to_raw_string = fixed_to_raw_string

def init():
    sys.modules['numpy'] = None
    result = _init()
    test_image = Image((0, 0), (5, 5), RGB)
    test_string = test_image._to_raw_string()
    refcount = sys.getrefcount(test_string)
    if refcount == 3:  # <no-coverage>
        # See: https://tech.groups.yahoo.com/group/gamera-devel/message/2068
        warnings.warn(RuntimeWarning('Working around memory leak in the Gamera library'), stacklevel=2)
        _monkeypatch_to_raw_string()
        fixed_test_string = test_image._to_raw_string()
        assert sys.getrefcount(fixed_test_string) == 2
        assert test_string == fixed_test_string
    else:
        assert refcount == 2
    return result

__all__ = [
# classes:
    'Dim',
    'Image',
    'Point',
    'RGBPixel',
# pixel types:
    'ONEBIT',
    'GREYSCALE',
    'RGB',
# functions:
    'init',
    'load_image',
    'methods',
    'to_pil_1bpp',
    'to_pil_rgb',
]

# vim:ts=4 sts=4 sw=4 et
