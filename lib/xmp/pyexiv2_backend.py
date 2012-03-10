# encoding=UTF-8

# Copyright © 2012 Jakub Wilk <jwilk@jwilk.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

'''XMP support (pyexiv2 backend)'''

import datetime
import itertools
import xml.etree.cElementTree as etree

import pyexiv2.xmp

from .. import temporary
from .. import timestamp
from .. import version

from . import namespaces as ns

def xmp_register_namespace(prefix, uri):
    # work-around for <http://bugs.debian.org/662878>
    class fool_pyexiv2(str):
        def endswith(self, suffix, *args, **kwargs):
            return True
    pyexiv2.xmp.register_namespace(fool_pyexiv2(uri), prefix)
xmp_register_namespace('didjvu', ns.didjvu)

try:
    etree.register_namespace
except AttributeError:
    def et_register_namespace(prefix, uri):
        import xml.etree.ElementTree as etree
        etree._namespace_map[uri] = prefix
    etree.register_namespace = et_register_namespace
    del et_register_namespace
etree.register_namespace('x', 'adobe:ns:meta/')

class XmpError(RuntimeError):
    pass

class Event(object):

    def __init__(self,
        action=None,
        software_agent=None,
        parameters=None,
        instance_id=None,
        changed=None,
        when=None,
    ):
        if software_agent is None:
            software_agent = version.get_software_agent()
        self._items = [
            ('action', action),
            ('softwareAgent', software_agent),
            ('parameters', parameters),
            ('instanceID', instance_id),
            ('changed', changed),
            ('when', str(when)),
        ]

    @property
    def items(self):
        return iter(self._items)

class datetime_for_pyexiv2(datetime.datetime):

    __almost_zero = 1.0
    while __almost_zero / 2 > 0:
        __almost_zero /= 2

    def __init__(self, year, month, day, hour, minute, second, microsecond=0, tzinfo=None):
        datetime.datetime.__init__(self, year, month, day, hour, minute, second, microsecond, tzinfo=tzinfo)
        self.__second = second

    @property
    def second(self):
        # pyexiv2 uses HH:MM format (instead of HH:MM:SS) if .seconds is 0.
        # Let's fool it into thinking it's always non-zero.
        return self.__second or self.__almost_zero

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
        except AttributeError:
            # Python 2.6
            xmp_find = xmp.findall
        for description in xmp_find('.//{%s}Description' % ns.rdf):
            pass
        if description is None:
            raise XmpError('Cannot add xmpMM:History')
        e_description = etree.SubElement(description, '{%s}History' % ns.xmpmm)
        etree.SubElement(e_description, '{%s}Seq' % ns.rdf)
        fp.seek(0)
        fp.truncate()
        xmp.write(fp, encoding='UTF-8')
        fp.flush()
        fp.seek(0)
        self._reload()
        try:
            self['xmpMM.History']
        except LookupError:
            raise XmpError('Cannot add xmpMM:History')

    def __init__(self):
        self._fp = fp = temporary.file(suffix='.xmp')
        fp.write('<x:xmpmeta xmlns:x="adobe:ns:meta/" xmlns:rdf="%s">'
            '<rdf:RDF/></x:xmpmeta>' % ns.rdf
        )
        self._reload()
        self._original_meta = self._meta

    def __del__(self):
        try:
            fp = self._fp
        except AttributeError:
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

    def add_to_history(self, event, index):
        for key, value in event.items:
            if value is None:
                continue
            self['xmpMM.History[%d]/stEvt:%s' % (index, key)] = value

    def append_to_history(self, event):
        self._add_history()
        keys = self._meta.xmp_keys
        for i in itertools.count(1):
            key = 'Xmp.xmpMM.History[%d]' % i
            if key not in keys:
                break
        return self.add_to_history(event, i)

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

__all__ = ['MetadataBase']

# vim:ts=4 sw=4 et
