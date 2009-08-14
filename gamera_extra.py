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

'''Bridge to the Gamera framework'''

from gamera.core import load_image, init_gamera as _init_gamera
from gamera.core import RGB, Dim
from gamera.plugins.pil_io import from_pil

def _load_methods():
    import re
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
        methods[name] = plugin
    return methods

methods = _load_methods()

def to_pil_1bpp(image):
    return image.to_greyscale().to_pil()

def init():
    import os
    import sys
    _old_stdout = sys.stdout
    sys.stdout = file(os.devnull, 'w')
    _init_gamera()
    sys.stdout = _old_stdout

# vim:ts=4 sw=4 et
