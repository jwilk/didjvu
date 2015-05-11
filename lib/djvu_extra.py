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

'''wrappers for the DjVuLibre utilities'''

import os
import re
import struct

from . import ipc
from . import temporary

DPI_MIN = 72
DPI_DEFAULT = 300
DPI_MAX = 6000

LOSS_LEVEL_MIN = 0
LOSS_LEVEL_CLEAN = 1
LOSS_LEVEL_LOSSY = 100
LOSS_LEVEL_MAX = 200

SUBSAMPLE_MIN = 1
SUBSAMPLE_DEFAULT = 3
SUBSAMPLE_MAX = 12

IW44_SLICES_DEFAULT = (74, 89, 99)
IW44_N_SLICES_MAX = 63
# http://sourceforge.net/p/djvu/djvulibre-git/ci/release.3.5.27.1/tree/tools/c44.cpp#l246

class Crcb(object):

    def __init__(self, sort_key, name):
        self._sort_key = sort_key
        self._name = name

    def __cmp__(self, other):
        if not isinstance(other, Crcb):
            return NotImplemented
        return cmp(self._sort_key, other._sort_key)

    def __str__(self):
        return self._name

    def __repr__(self):
        return '%s.CRCB.%s' % (type(self).__module__, self._name)

class CRCB:

    values = [
        Crcb(3, 'full'),
        Crcb(2, 'normal'),
        Crcb(1, 'half'),
        Crcb(0, 'none'),
    ]

for _value in CRCB.values:
    setattr(CRCB, str(_value), _value)
del _value

def bitonal_to_djvu(image, dpi=300, loss_level=0):
    pbm_file = temporary.file(suffix='.pbm')
    image.save(pbm_file.name)
    djvu_file = temporary.file(suffix='.djvu', mode='r+b')
    args = [
        'cjb2',
        '-dpi', str(dpi),
        '-losslevel', str(loss_level),
        pbm_file.name,
        djvu_file.name
    ]
    return ipc.Proxy(djvu_file, ipc.Subprocess(args).wait, [pbm_file])

def photo_to_djvu(image, dpi=100, slices=IW44_SLICES_DEFAULT, gamma=2.2, mask_image=None, crcb=CRCB.normal):
    ppm_file = temporary.file(suffix='.ppm')
    image.save(ppm_file.name)
    if not isinstance(crcb, Crcb):
        raise TypeError
    with temporary.directory() as djvu_dir:
        args = [
            'c44',
            '-dpi', str(dpi),
            '-slice', ','.join(map(str, slices)),
            '-gamma', '%.1f' % gamma,
            '-crcb%s' % crcb,
        ]
        if mask_image is not None:
            pbm_file = temporary.file(suffix='.pbm')
            mask_image.save(pbm_file.name)
            args += ['-mask', pbm_file.name]
        djvu_path = os.path.join(djvu_dir, 'result.djvu')
        args += [ppm_file.name, djvu_path]
        ipc.Subprocess(args).wait()
        return temporary.hardlink(djvu_path, suffix='.djvu')

def djvu_to_iw44(djvu_file):
    # TODO: Use Multichunk.
    iw44_file = temporary.file(suffix='.iw44')
    args = ['djvuextract', djvu_file.name, 'BG44=%s' % iw44_file.name]
    with open(os.devnull, 'wb') as dev_null:
        return ipc.Proxy(iw44_file, ipc.Subprocess(args, stderr=dev_null).wait, [djvu_file])

def _int_or_none(x):
    if x is None:
        return
    if isinstance(x, int):
        return x
    raise ValueError

def _chunk_order(key):
    # INCL must go before Sjbz.
    if key[0] == 'incl':
        return -2
    # djvuextract expects Sjbz before PPM.
    if key[0] == 'sjbz':
        return -1
    return 0

class Multichunk(object):

    _chunk_names = 'Sjbz Smmr BG44 BGjp BG2k FGbz FG44 FGjp FG2k INCL Djbz'
    _chunk_names = dict((x.lower(), x) for x in _chunk_names.split())
    _info_re = re.compile(' ([0-9]+)x([0-9]+),.* ([0-9]+) dpi,').search

    def __init__(self, width=None, height=None, dpi=None, **chunks):
        self.width = _int_or_none(width)
        self.height = _int_or_none(height)
        self.dpi = _int_or_none(dpi)
        self._chunks = {}
        self._dirty = set()  # Chunks that need to be re-read from the file.
        self._pristine = False  # Should save() be a no-op?
        self._file = None
        for (k, v) in chunks.iteritems():
            self[k] = v

    def _load_file(self):
        args = ['djvudump', self._file.name]
        dump = ipc.Subprocess(args, stdout=ipc.PIPE)
        self.width = self.height = self.dpi = None
        keys = set()
        try:
            header = dump.stdout.readline()
            if not header.startswith('  FORM:DJVU '):
                raise ValueError
            for line in dump.stdout:
                if line[:4] == '    ' and line[8:9] == ' ':
                    key = line[4:8]
                    if key == 'INFO':
                        m = self._info_re(line[8:])
                        self.width, self.height, self.dpi = m.groups()
                    else:
                        keys.add(key.lower())
                else:
                    raise ValueError
        finally:
            dump.wait()
        self._chunks = dict((key, None) for key in keys)
        self._dirty.add(self._chunks)
        self._pristine = True

    @classmethod
    def from_file(cls, djvu_file):
        self = cls()
        self._file = djvu_file
        self._load_file()
        return self

    def __contains__(self, key):
        key = key.lower()
        if key in self._chunks:
            return True

    def __setitem__(self, key, value):
        if key == 'image':
            ppm_file = temporary.file(suffix='.ppm')
            value.save(ppm_file.name)
            key = 'PPM'
            value = ppm_file
        else:
            key = key.lower()
            if key not in self._chunk_names:
                raise ValueError
        self._chunks[key] = value
        self._dirty.discard(key)
        self._pristine = False

    def __getitem__(self, key):
        key = key.lower()
        value = self._chunks[key]
        if key in self._dirty:
            self.save()
            self._load_file()
            self._update_chunks()
            value = self._chunks[key]
            assert value is not None
        return value

    def _update_chunks(self):
        assert self._file is not None
        args = ['djvuextract', self._file.name]
        chunk_files = {}
        for key in self._dirty:
            chunk_file = temporary.file(suffix='.%s-chunk' % key)
            args += ['%s=%s' % (self._chunk_names[key], chunk_file.name)]
            chunk_files[key] = chunk_file
        djvuextract = ipc.Subprocess(args, stderr=open(os.devnull, 'wb'))
        for key in self._chunks:
            self._chunks[key] = ipc.Proxy(chunk_files[key], djvuextract.wait, [self._file])
            self._dirty.discard(key)
        assert not self._dirty
        # The file reference is not needed anymore.
        self._file = None

    def save(self):
        if (self._file is not None) and self._pristine:
            return self._file
        if self.width is None:
            raise ValueError
        if self.height is None:
            raise ValueError
        if self.dpi is None:
            raise ValueError
        if len(self._chunks) == 0:
            raise ValueError
        args = ['djvumake', None, 'INFO=%d,%d,%d' % (self.width, self.height, self.dpi)]
        incl_dir = None
        for key, value in sorted(self._chunks.iteritems(), key=_chunk_order):
            try:
                key = self._chunk_names[key]
            except KeyError:
                pass
            if key == 'INCL':
                # This is tricky. DjVuLibre used to require (at least until v3.5.27) full path for INCL,
                # but now it requires just basename:
                # http://sourceforge.net/p/djvu/djvulibre-git/ci/2fea3cdd3eb2b9ae60a43a851dbd838b6939af4b/
                # Let's work around this inconsistency.
                new_incl_dir = os.path.dirname(value)
                if incl_dir is None:
                    incl_dir = new_incl_dir
                elif incl_dir != new_incl_dir:
                    raise ValueError
                value = os.path.basename(value)
            if not isinstance(value, basestring):
                value = value.name
            if key == 'BG44':
                value += ':99'
            args += ['%s=%s' % (key, value)]
        def chdir():
            os.chdir(incl_dir or '.')
        with temporary.directory() as tmpdir:
            djvu_filename = args[1] = os.path.join(tmpdir, 'result.djvu')
            ipc.Subprocess(args, preexec_fn=chdir).wait()
            self._chunks.pop('PPM', None)
            assert 'PPM' not in self._dirty
            self._file = temporary.hardlink(djvu_filename)
            self._pristine = True
            return self._file

_djvu_header = 'AT&TFORM\0\0\0\0DJVMDIRM\0\0\0\0\1'

def bundle_djvu_via_indirect(*component_filenames):
    with temporary.directory() as tmpdir:
        pageids = []
        page_sizes = []
        for filename in component_filenames:
            pageid = os.path.basename(filename)
            os.symlink(filename, os.path.join(tmpdir, pageid))
            pageids += [pageid]
            page_size = os.path.getsize(filename)
            if page_size >= 1 << 24:
                # Would overflow; but 0 is fine, too.
                page_size = 0
            page_sizes += [page_size]
        with temporary.file(dir=tmpdir, suffix='djvu') as index_file:
            index_file.write(_djvu_header)
            index_file.write(struct.pack('>H', len(pageids)))
            index_file.flush()
            bzz = ipc.Subprocess(['bzz', '-e', '-', '-'], stdin=ipc.PIPE, stdout=index_file)
            try:
                for page_size in page_sizes:
                    bzz.stdin.write(struct.pack('>I', page_size)[1:])
                for pageid in pageids:
                    bzz.stdin.write(struct.pack('B', not pageid.endswith('.iff')))
                for pageid in pageids:
                    bzz.stdin.write(pageid)
                    bzz.stdin.write('\0')
            finally:
                bzz.stdin.close()
                bzz.wait()
            index_file_size = index_file.tell()
            i = 0
            while True:
                i = _djvu_header.find('\0' * 4, i)
                if i < 0:
                    break
                index_file.seek(i)
                index_file.write(struct.pack('>I', index_file_size - i - 4))
                i += 4
            index_file.flush()
            djvu_file = temporary.file(suffix='.djvu')
            ipc.Subprocess(['djvmcvt', '-b', index_file.name, djvu_file.name]).wait()
    return djvu_file

def bundle_djvu(*component_filenames):
    assert len(component_filenames) > 0
    if any(c.endswith('.iff') for c in component_filenames):
        # We can't use ``djvm -c``.
        return bundle_djvu_via_indirect(*component_filenames)
    else:
        djvu_file = temporary.file(suffix='.djvu')
        args = ['djvm', '-c', djvu_file.name]
        args += component_filenames
        return ipc.Proxy(djvu_file, ipc.Subprocess(args).wait, None)

def require_cli():
    ipc.require(
        'cjb2',
        'c44',
        'djvuextract',
        'djvudump',
        'djvumake',
        'bzz',
        'djvmcvt',
    )

__all__ = [
    'bitonal_to_djvu', 'photo_to_djvu', 'djvu_to_iw44',
    'bundle_djvu',
    'require_cli',
    'Multichunk',
    'DPI_MIN', 'DPI_DEFAULT', 'DPI_MAX',
    'LOSS_LEVEL_MIN', 'LOSS_LEVEL_CLEAN', 'LOSS_LEVEL_LOSSY', 'LOSS_LEVEL_MAX',
    'SUBSAMPLE_MIN', 'SUBSAMPLE_DEFAULT', 'SUBSAMPLE_MAX',
    'IW44_SLICES_DEFAULT',
    'CRCB',
]

# vim:ts=4 sts=4 sw=4 et
