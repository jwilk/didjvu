# encoding=UTF-8

# Copyright © 2012-2016 Jakub Wilk <jwilk@jwilk.net>
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

'''XMP support'''

import errno
import uuid

from .. import timestamp
from .. import version

import_error = None
backend = None

try:
    from . import gexiv2_backend as backend
except ImportError as import_error:  # no coverage
    pass

if backend is None:  # no coverage
    try:
        from . import libxmp_backend as backend
    except ImportError:
        pass

if backend is None:  # no coverage
    try:
        from . import pyexiv2_backend as backend
    except ImportError:
        pass

def gen_uuid():
    '''
    generate a UUID URN, in accordance with RFC 4122
    '''
    # https://www.rfc-editor.org/rfc/rfc4122.html#section-3
    return 'urn:uuid:{uuid}'.format(uuid=uuid.uuid4())

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

def metadata(backend=backend):

    class Metadata(backend.MetadataBase):

        def update(self, media_type, internal_properties=()):
            instance_id = gen_uuid()
            document_id = gen_uuid()
            now = timestamp.now()
            original_media_type = self.get('dc.format')
            # TODO: try to guess original media type
            self['dc.format'] = media_type
            if original_media_type is not None:
                event_params = 'from {0} to {1}'.format(original_media_type, media_type)
            else:
                event_params = 'to {0}'.format(media_type)
            self['xmp.ModifyDate'] = now
            self['xmp.MetadataDate'] = now
            self['xmpMM.InstanceID'] = instance_id
            try:
                self['xmpMM.OriginalDocumentID']
            except KeyError:
                try:
                    original_document_id = self['xmpMM.DocumentID']
                except KeyError:
                    pass
                else:
                    self['xmpMM.OriginalDocumentID'] = original_document_id
            self['xmpMM.DocumentID'] = document_id
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
            except (OSError, IOError) as ex:
                if ex.errno == errno.ENOENT:
                    return
                raise
            try:
                self.read(file)
            finally:
                file.close()

        def write(self, file):
            file.write(self.serialize())

    return Metadata()

__all__ = [
    'backend',
    'import_error',
    'metadata',
]

# vim:ts=4 sts=4 sw=4 et
