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

import datetime
import errno

import libxmp

from libxmp.consts import XMP_NS_DC as ns_dc
from libxmp.consts import XMP_NS_XMP as ns_xmp
ns_didjvu = 'http://jwilk.net/software/didjvu#'

class Metadata(libxmp.XMPMeta):

    def __init__(self):
        libxmp.XMPMeta.__init__(self)
        self.register_namespace(ns_didjvu, 'didjvu')

    def update(self, media_type, internal_properties={}):
        now = datetime.datetime.utcnow()
        self.set_property(ns_dc, 'format', media_type)
        self.set_property_datetime(ns_xmp, 'ModifyDate', now)
        self.set_property_datetime(ns_xmp, 'MetadataDate', now)
        for k, v in internal_properties:
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

# vim:ts=4 sw=4 et
