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

'''XMP support'''

import datetime
import errno
import itertools
import time
import uuid
import xml.etree.cElementTree as etree

import pyexiv2.xmp

from . import temporary
from . import version

ns_rdf = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
ns_xmpmm = 'http://ns.adobe.com/xap/1.0/mm/'
ns_didjvu = 'http://jwilk.net/software/didjvu#'

def xmp_register_namespace(prefix, uri):
    # work-around for <http://bugs.debian.org/662878>
    class fool_pyexiv2(str):
        def endswith(self, suffix, *args, **kwargs):
            return True
    pyexiv2.xmp.register_namespace(fool_pyexiv2(uri), prefix)
xmp_register_namespace('didjvu', ns_didjvu)

try:
    etree.register_namespace
except AttributeError:
    def et_register_namespace(prefix, uri):
        import xml.etree.ElementTree as etree
        etree._namespace_map[uri] = prefix
    etree.register_namespace = et_register_namespace
    del et_register_namespace
etree.register_namespace('x', 'adobe:ns:meta/')

class rfc3339(object):

    def __init__(self, unixtime):
        self._localtime = time.localtime(unixtime)

    def _str(self):
        return time.strftime('%Y-%m-%dT%H:%M:%S', self._localtime)

    def _str_tz(self):
        offset = time.timezone if not self._localtime.tm_isdst else time.altzone
        hours, minutes  = divmod(abs(offset) // 60, 60)
        return '%s%02d:%02d' % ('+' if offset < 0 else '-', hours, minutes)

    def __str__(self):
        '''Format the timestamp object in accordance with RFC 3339.'''
        return self._str() + self._str_tz()

    def as_datetime(self):
        offset = time.timezone if not self._localtime.tm_isdst else time.altzone
        class tz(datetime.tzinfo):
            def utcoffset(self, dt):
                return datetime.timedelta(seconds=-offset)
            def dst(self, dt):
                return datetime.timedelta(0)
        return datetime.datetime(*self._localtime[:6], tzinfo=tz())

def gen_uuid():
    return 'uuid:' + str(uuid.uuid4()).replace('-', '')

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

    def add_to_history(self, metadata, index):
        for key, value in self._items:
            if value is None:
                continue
            metadata['xmpMM.History[%d]/stEvt:%s' % (index, key)] = value

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
        for description in xmp.iterfind('.//{%s}Description' % ns_rdf):
            pass
        if description is None:
            raise XmpError('Cannot add xmpMM:History')
        e_description = etree.SubElement(description, '{%s}History' % ns_xmpmm)
        etree.SubElement(e_description, '{%s}Seq' % ns_rdf)
        fp.seek(0)
        fp.truncate()
        xmp.write(fp, xml_declaration=True)
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
            '<rdf:RDF/></x:xmpmeta>' % ns_rdf
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
        return self._meta.get('Xmp.' + key, fallback)

    def __getitem__(self, key):
        return self._meta['Xmp.' + key]

    def __setitem__(self, key, value):
        if isinstance(value, rfc3339):
            value = value.as_datetime()
        elif key.startswith('didjvu.'):
            value = str(value)
        self._meta['Xmp.' + key] = value

    def add_to_history(self, event, index):
        return event.add_to_history(self, index)

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

class Metadata(MetadataBase):

    def update(self, media_type, internal_properties={}):
        instance_id = gen_uuid()
        now = rfc3339(time.time())
        original_media_type = self.get('dc.format')
        # TODO: try to guess original media type
        self['dc.format'] = tuple(media_type.split('/'))
        if original_media_type is not None:
            event_params = 'from %s to %s' % ('/'.join(original_media_type.value), media_type)
        else:
            event_params = 'to %s' % (media_type,)
        self['xmp.ModifyDate'] = now
        self['xmp.MetadataDate'] = now
        self['xmpMM.InstanceID'] = instance_id
        event = Event(
            action='converted',
            parameters=event_params,
            instance_id=instance_id,
            when=now,
        )
        self.append_to_history(event)
        for k, v in internal_properties:
            self['didjvu.' + k] = v

    def import_(self, image_filename):
        try:
            file = open(image_filename + '.xmp', 'rb')
        except (OSError, IOError), ex:
            if ex.errno == errno.ENOENT:
                return
            raise
        try:
            self.read(file)
        finally:
            file.close()

    def write(self, file):
        file.write(self.serialize())

__all__ = ['Metadata']

# vim:ts=4 sw=4 et
