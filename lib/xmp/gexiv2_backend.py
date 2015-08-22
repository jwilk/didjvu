# encoding=UTF-8

# Copyright © 2012-2015 Jakub Wilk <jwilk@jwilk.net>
#
# This file is part of didjvu.
#
# didjvu is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# didjvu is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.

'''XMP support (GExiv2 backend)'''

import re

from gi.repository import GExiv2

from .. import temporary
from .. import timestamp

from . import namespaces as ns

GExiv2.Metadata.register_xmp_namespace(ns.didjvu, 'didjvu')

class XmpError(RuntimeError):
    pass

class MetadataBase(object):

    _empty_xmp = (
        '<x:xmpmeta xmlns:x="adobe:ns:meta/" xmlns:rdf="{ns.rdf}">'
        '<rdf:RDF/>'
        '</x:xmpmeta>'.format(ns=ns)
    )

    def _read_data(self, data):
        fp = temporary.file(suffix='.xmp')
        try:
            fp.write(data)
            fp.flush()
            self._meta = GExiv2.Metadata(fp.name)
        finally:
            fp.close()

    def __init__(self):
        self._read_data(self._empty_xmp)

    def get(self, key, fallback=None):
        try:
            return self[key]
        except LookupError:
            return fallback

    def __getitem__(self, key):
        return self._meta['Xmp.' + key]

    def __setitem__(self, key, value):
        if isinstance(value, timestamp.Timestamp):
            value = str(value)
        elif key.startswith('didjvu.'):
            value = str(value)
        self._meta['Xmp.' + key] = value

    def _add_to_history(self, event, index):
        for key, value in event.items:
            if value is None:
                continue
            self['xmpMM.History[{i}]/stEvt:{key}'.format(i=index, key=key)] = value

    def append_to_history(self, event):
        regex = re.compile(r'^Xmp[.]xmpMM[.]History\[([0-9]+)\]/')
        n = 0
        for key in self._meta.get_xmp_tags():
            match = regex.match(key)
            if match is None:
                continue
            i = int(match.group(1))
            n = max(i, n)
        if n == 0:
            self._meta.set_xmp_tag_struct('Xmp.xmpMM.History', GExiv2.StructureType.SEQ)
        return self._add_to_history(event, n + 1)

    def serialize(self):
        return '<?xml version="1.0"?>\n' + (
            self._meta.generate_xmp_packet(
                GExiv2.XmpFormatFlags.OMIT_PACKET_WRAPPER,
                0
            ) or self._empty_xmp
        )

    def read(self, file):
        data = file.read()
        self._read_data(data)

__all__ = ['MetadataBase']

# vim:ts=4 sts=4 sw=4 et
