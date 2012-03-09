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
import uuid

ns_didjvu = 'http://jwilk.net/software/didjvu#'

from .. import timestamp
from .. import version

from . libxmp_backend import MetadataBase

def gen_uuid():
    return 'uuid:' + str(uuid.uuid4()).replace('-', '')

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

class Metadata(MetadataBase):

    ns_didjvu = ns_didjvu

    def update(self, media_type, internal_properties={}):
        instance_id = gen_uuid()
        now = timestamp.now()
        original_media_type = self.get('dc.format')
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
