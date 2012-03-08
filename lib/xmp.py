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
import time
import uuid

import libxmp

from libxmp.consts import XMP_NS_RDF as ns_rdf
from libxmp.consts import XMP_NS_DC as ns_dc
from libxmp.consts import XMP_NS_XMP as ns_xmp
from libxmp.consts import XMP_NS_XMP_MM as ns_xmp_mm
from libxmp.consts import XMP_NS_XMP_ResourceEvent as ns_xmp_event
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

class Metadata(libxmp.XMPMeta):

    def __init__(self):
        libxmp.XMPMeta.__init__(self)
        self.register_namespace(ns_didjvu, 'didjvu')

    def add_to_history(self, event, index):
        for key, value in event.items:
            if value is None:
                continue
            self.set_property(ns_xmp_mm, 'History[%d]/stEvt:%s' % (index, key), value)

    def append_to_history(self, event):
        count = self.count_array_items(ns_xmp_mm, 'History')
        if self.count_array_items(ns_xmp_mm, 'History') == 0:
            self.set_property(ns_xmp_mm, 'History', '',
                prop_value_is_array=True,
                prop_array_is_ordered=True
            )
            count = 0
            assert count == self.count_array_items(ns_xmp_mm, 'History')
        return self.add_to_history(event, count + 1)

    def update(self, media_type, internal_properties={}):
        substitutions = {}
        instance_id = 'uuid:' + str(uuid.uuid4()).replace('-', '')
        now = rfc3339(time.time())
        original_media_type = self.get_property(ns_dc, 'format')
        # TODO: try to guess original media type
        self.set_property(ns_dc, 'format', media_type)
        if original_media_type is not None:
            event_params = 'from %s to %s' % (original_media_type, media_type)
        else:
            event_params = 'to %s' % (media_type,)
        self.set_property(ns_xmp, 'ModifyDate', str(now))
        self.set_property(ns_xmp, 'MetadataDate', str(now))
        self.set_property(ns_xmp_mm, 'InstanceID', instance_id)
        event = Event(
            action='converted',
            parameters=event_params,
            instance_id=instance_id,
            when=now,
        )
        self.append_to_history(event)
        for k, v in internal_properties:
            if isinstance(v, bool):
                self.set_property_bool(ns_didjvu, k, v)
            elif isinstance(v, int):
                self.set_property_int(ns_didjvu, k, v)
            else:
                self.set_property(ns_didjvu, k, v)

    def serialize(self):
        return self.serialize_and_format(omit_packet_wrapper=True, tabchr='    ')

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

    def read(self, file):
        xmp = file.read()
        self.parse_from_str(xmp)

    def write(self, file):
        file.write(self.serialize())

__all__ = ['Metadata']

# vim:ts=4 sw=4 et
