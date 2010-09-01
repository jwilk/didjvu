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

'''Wrappers for the DjVuLibre utilities'''

import os
import shutil
import tempfile

from . import ipc
from . import temporary

DPI_MIN = 72
DPI_DEFAULT = 300
DPI_MAX = 6000

LOSS_LEVEL_MIN = 0
LOSS_LEVEL_DEFAULT = 100
LOSS_LEVEL_MAX = 200

SUBSAMPLE_MIN = 1
SUBSAMPLE_DEFAULT = 3
SUBSAMPLE_MAX = 12

IW44_SLICES_DEFAULT = (74, 89, 99)

CRCB_FULL = 3
CRCB_NORMAL = 2
CRCB_HALF = 1
CRCB_NONE = 0

def bitonal_to_djvu(image, dpi=300, loss_level=0):
    pbm_file = temporary.file(suffix='.pbm')
    image.save(pbm_file.name)
    djvu_file = temporary.file(suffix='.djvu', mode='r+b')
    args = ['cjb2', '-losslevel', str(loss_level), pbm_file.name, djvu_file.name]
    return ipc.Proxy(djvu_file, ipc.Subprocess(args).wait, [pbm_file])

_crcb_map = {
    CRCB_FULL: 'full',
    CRCB_NORMAL: 'normal',
    CRCB_HALF: 'half',
    CRCB_NONE: 'none',
}

def photo_to_djvu(image, dpi=100, slices=IW44_SLICES_DEFAULT, gamma=2.2, mask_image=None, crcb=CRCB_NORMAL):
    ppm_file = temporary.file(suffix='.ppm')
    temporaries = [ppm_file]
    image.save(ppm_file.name)
    djvu_file = temporary.file(suffix='.djvu', mode='r+b')
    args = [
        'c44',
        '-dpi', str(dpi),
        '-slice', ','.join(map(str, slices)),
        '-gamma', '%.1f' % gamma,
        '-crcb%s' % _crcb_map[crcb],
    ]
    if mask_image is not None:
        pbm_file = temporary.file(suffix='.pbm')
        mask_image.save(pbm_file.name)
        args += ['-mask', pbm_file.name]
        temporaries += [pbm_file]
    args += [ppm_file.name, djvu_file.name]
    return ipc.Proxy(djvu_file, ipc.Subprocess(args).wait, temporaries)

def djvu_to_iw44(djvu_file):
    iw44_file = temporary.file(suffix='.iw44')
    args = ['djvuextract', djvu_file.name, 'BG44=%s' % iw44_file.name]
    return ipc.Proxy(iw44_file, ipc.Subprocess(args).wait, [djvu_file])

def assemble_djvu(width, height, dpi=300, sjbz=None, smmr=None, bg44=None, bg44_nchunks=None, bgjp=None, bg2k=None, fgbz=None, fg44=None, fgjp=None, fg2k=None, incl=None, djbz=None, image=None):
    args = ['djvumake', None, 'INFO=%d,%d,%d' % (width, height, dpi)]
    if sjbz is not None:
        args += 'Sjbz=%s' % sjbz.name,
    if smmr is not None:
        args += 'Smmr=%s' % smrr.name,
    if bg44 is not None:
        arg = 'BG44=%s' % bg44.name
        if bg44_nchunks is not None:
            arg += ':%d' % bg44_nchunks
        args += arg,
    if bgjp is not None:
        args += 'BGjp=%s' % bgjp.name,
    if bg2k is not None:
        args += 'BG2k=%s' % bg2k.name,
    if fgbz is not None:
        if isinstance(fgbz, str):
            arg = fbgz
        else:
            arg = fgbz.name
        args += 'FGbz=%s' % arg,
    if fg44 is not None:
        args += 'FG44=%s' % fg44.name,
    if fgjp is not None:
        args += 'FGjp=%s' % fgjp.name,
    if fg2k is not None:
        args += 'FG2k=%s' % fg2k.name,
    if incl is not None:
        args += 'INCL=%s' % incl,
    if djbz is not None:
        args += 'Djbz=%s' % djbz.name,
    if image is not None:
        ppm_file = temporary.file(suffix='.ppm')
        image.save(ppm_file.name)
        args += 'PPM=%s' % ppm_file.name,
    tmpdir = temporary.directory()
    try:
        djvu_filename = args[1] = os.path.join(tmpdir, 'result.djvu')
        ipc.Subprocess(args).wait()
        djvu_new_filename = tempfile.mktemp(prefix='didjvu', suffix='.djvu')
        os.link(djvu_filename, djvu_new_filename)
        return tempfile._TemporaryFileWrapper(file(djvu_new_filename, mode='r+b'), djvu_new_filename)
    finally:
        shutil.rmtree(tmpdir)

def bundle_djvu(*component_filenames):
    djvu_file = temporary.file(suffix='.djvu')
    args = ['djvm', '-c', djvu_file.name]
    args += component_filenames
    return ipc.Proxy(djvu_file, ipc.Subprocess(args).wait, None)

__all__ = [
    'bitonal_to_djvu', 'photo_to_djvu', 'djvu_to_iw44', 'assemble_djvu',
    'DEBUG',
    'DPI_MIN', 'DPI_DEFAULT', 'DPI_MAX',
    'LOSS_LEVEL_MIN', 'LOSS_LEVEL_DEFAULT', 'LOSS_LEVEL_MAX',
    'SUBSAMPLE_MIN', 'SUBSAMPLE_DEFAULT', 'SUBSAMPLE_MAX',
    'IW44_SLICES_DEFAULT',
    'CRCB_FULL', 'CRCB_NORMAL', 'CRCB_HALF', 'CRCB_NONE',
]

# vim:ts=4 sw=4 et
