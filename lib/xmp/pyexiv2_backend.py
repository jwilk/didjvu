# encoding=UTF-8

# Copyright © 2012-2021 Jakub Wilk <jwilk@jwilk.net>
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

'''XMP support (pyexiv2 backend)'''

import datetime
import itertools
import sys
import xml.etree.cElementTree as etree

import pyexiv2.xmp

from .. import temporary
from .. import timestamp

from . import namespaces as ns

def _get_versions():
    version = pyexiv2.__version__
    yield 'pyexiv2 {0}'.format(version)
    version = pyexiv2.__exiv2_version__
    yield '+ Exiv2 {0}'.format(version)
versions = list(_get_versions())

def xmp_register_namespace(prefix, uri):
    # work-around for <https://bugs.debian.org/662878>
    class fool_pyexiv2(str):
        def endswith(self, suffix, *args, **kwargs):
            return True
    try:
        pyexiv2.xmp.register_namespace(fool_pyexiv2(uri), prefix)
    except KeyError:
        if 'gi.repository.GExiv2' in sys.modules:
            # most likely the namespace was registered by the GExiv2 backend
            pass
        else:  # no coverage
            raise
xmp_register_namespace('didjvu', ns.didjvu)

etree.register_namespace('x', 'adobe:ns:meta/')

class XmpError(RuntimeError):
    pass

class datetime_for_pyexiv2(datetime.datetime):

    __almost_zero = 1.0
    while __almost_zero / 2 > 0:
        __almost_zero /= 2

    def __init__(self, year, month, day, hour, minute, second, microsecond=0, tzinfo=None):
        datetime.datetime.__init__(self)
        self.__second = second

    @property
    def second(self):
        # pyexiv2 uses HH:MM format (instead of HH:MM:SS) if .seconds is 0.
        # Let's fool it into thinking it's always non-zero.
        return self.__second or self.__almost_zero

def nstag(ns, tag):
    return '{{{ns}}}{tag}'.format(ns=ns, tag=tag)

class MetadataBase(object):

    def _reload(self):
        fp = self._fp
        fp.flush()
        fp.seek(0)
        self._meta = pyexiv2.ImageMetadata(fp.name)
        self._meta.read()

    def _add_history(self):
        try:
            self['xmpMM.History']
        except LookupError:
            pass
        else:
            return
        self._meta.write()
        fp = self._fp
        fp.seek(0)
        xmp = etree.parse(fp)
        description = None
        try:
            xmp_find = xmp.iterfind
        except AttributeError:  # no coverage
            # Python 2.6
            xmp_find = xmp.findall
        for description in xmp_find('.//' + nstag(ns.rdf, 'Description')):
            pass
        if description is None:
            raise XmpError('Cannot add xmpMM:History')  # no coverage
        e_description = etree.SubElement(description, nstag(ns.xmpmm, 'History'))
        etree.SubElement(e_description, nstag(ns.rdf, 'Seq'))
        fp.seek(0)
        fp.truncate()
        xmp.write(fp, encoding='UTF-8')
        fp.flush()
        fp.seek(0)
        self._reload()
        try:
            self['xmpMM.History']
        except LookupError:  # no coverage
            raise XmpError('Cannot add xmpMM:History')

    def __init__(self):
        self._fp = fp = temporary.file(suffix='.xmp')
        fp.write(
            '<x:xmpmeta xmlns:x="adobe:ns:meta/" xmlns:rdf="{ns.rdf}">'
            '<rdf:RDF/>'
            '</x:xmpmeta>'.format(ns=ns)
        )
        self._reload()

    def __del__(self):
        try:
            fp = self._fp
        except AttributeError:  # no coverage
            pass
        else:
            fp.close()

    def get(self, key, fallback=None):
        try:
            return self[key]
        except LookupError:
            return fallback

    def __getitem__(self, key):
        tag = self._meta['Xmp.' + key]
        if tag.type == 'MIMEType':
            value = tag.raw_value
        else:
            value = tag.value
        return value

    def __setitem__(self, key, value):
        if isinstance(value, timestamp.Timestamp):
            value = value.as_datetime(cls=datetime_for_pyexiv2)
        elif key.startswith('didjvu.'):
            value = str(value)
        elif key == 'dc.format' and isinstance(value, basestring):
            value = tuple(value.split('/', 1))
        self._meta['Xmp.' + key] = value

    def _add_to_history(self, event, index):
        for key, value in event.items:
            if value is None:
                continue
            self['xmpMM.History[{i}]/stEvt:{key}'.format(i=index, key=key)] = value

    def append_to_history(self, event):
        self._add_history()
        keys = self._meta.xmp_keys
        for i in itertools.count(1):
            key = 'Xmp.xmpMM.History[{i}]'.format(i=i)
            if key not in keys:
                break
        return self._add_to_history(event, i)

    def serialize(self):
        self._meta.write()
        fp = self._fp
        fp.seek(0)
        return fp.read()

    def read(self, file):
        data = file.read()
        fp = self._fp
        fp.seek(0)
        fp.truncate()
        fp.write(data)
        self._reload()

__all__ = [
    'MetadataBase',
    'versions',
]

# vim:ts=4 sts=4 sw=4 et
