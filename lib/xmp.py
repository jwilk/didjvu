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

import errno
import time
import re
import uuid

import libxmp

ns_didjvu = 'http://jwilk.net/software/didjvu#'

from . import version

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

    @property
    def items(self):
        return iter(self._items)

class MetadataBase(object):

    from libxmp.consts import XMP_NS_DC as ns_dc
    from libxmp.consts import XMP_NS_XMP as ns_xmp
    from libxmp.consts import XMP_NS_XMP_MM as ns_xmp_mm
    ns_didjvu = ns_didjvu

    def __init__(self):
        backend = self._backend = libxmp.XMPMeta()
        prefix = backend.register_namespace(self.ns_didjvu, 'didjvu')
        if prefix is None:
            raise XmpError('Cannot register namespace for didjvu internal properties')

    @classmethod
    def _expand_key(cls, key):
        namespace, key = key.split('.', 1)
        if namespace == 'xmpMM':
            namespace = 'xmp_mm'
        namespace = getattr(cls, 'ns_' + namespace)
        return namespace, key

    def __setitem__(self, key, value):
        namespace, key = self._expand_key(key)
        backend = self._backend
        if isinstance(value, bool):
            rc = backend.set_property_bool(namespace, key, value)
        elif isinstance(value, int):
            rc = backend.set_property_int(namespace, key, value)
        elif isinstance(value, list) and len(value) == 0:
            rc = backend.set_property(namespace, key, '',
                 prop_value_is_array=True,
                 prop_array_is_ordered=True
            )
        else:
            if isinstance(value, rfc3339):
                value = str(value)
            rc = backend.set_property(namespace, key, value)
        if rc is None:
            raise XmpError('Cannot set property')

    def __getitem__(self, key):
        namespace, key = self._expand_key(key)
        backend = self._backend
        return backend.get_property(namespace, key)

    def add_to_history(self, event, index):
        for key, value in event.items:
            if value is None:
                continue
            self['xmpMM.History[%d]/stEvt:%s' % (index, key)] = value

    def append_to_history(self, event):
        backend = self._backend
        def count_history():
            return backend.count_array_items(self.ns_xmp_mm, 'History')
        count = count_history()
        if count == 0:
            self['xmpMM.History'] = []
            assert count_history() == 0
        result = self.add_to_history(event, count + 1)
        assert count_history() == count + 1
        return result

    def serialize(self):
        backend = self._backend
        return backend.serialize_and_format(omit_packet_wrapper=True, tabchr='    ')

    def read(self, file):
        backend = self._backend
        xmp = file.read()
        backend.parse_from_str(xmp)

class Metadata(MetadataBase):

    def update(self, media_type, internal_properties={}):
        instance_id = gen_uuid()
        now = rfc3339(time.time())
        original_media_type = self['dc.format']
        # TODO: try to guess original media type
        self['dc.format'] = media_type
        if original_media_type is not None:
            event_params = 'from %s to %s' % (original_media_type, media_type)
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
