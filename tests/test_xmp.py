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
import os
import re
import time

from nose import SkipTest
from nose.tools import (
    assert_equal,
    assert_not_equal,
    assert_true,
)

from lib import ipc
from lib import temporary
from lib import xmp

try:
    import libxmp
    from libxmp.consts import (
        XMP_NS_RDF as ns_rdf,
        XMP_NS_DC as ns_dc,
        XMP_NS_XMP as ns_xmp,
        XMP_NS_XMP_MM as ns_xmp_mm,
        XMP_NS_TIFF as ns_tiff,
    )
except ImportError, libxmp_import_error:
    libxmp = None

def test_rfc3339():
    result = xmp.rfc3339(time.time())
    assert_correct_timestamp(str(result))

def test_uuid():
    uuid1 = xmp.gen_uuid()
    assert_correct_uuid(uuid1)
    uuid2 = xmp.gen_uuid()
    assert_correct_uuid(uuid2)
    assert_not_equal(uuid1, uuid2)

class tag_exiv2(object):
    def __repr__(self): return 'exiv2'
tag_exiv2 = tag_exiv2()

class tag_libxmp(object):
    def __repr__(self): return 'libxmp'
tag_libxmp = tag_libxmp()

def run_exiv2(filename, fail_ok=False):
    try:
        child = ipc.Subprocess(
            ['exiv2', 'print', '-P', 'Xkt', filename],
            stdout=ipc.PIPE
        )
    except OSError, ex:
        raise SkipTest(ex)
    for line in sorted(child.stdout):
        yield line
    try:
        child.wait()
    except ipc.CalledProcessError:
        if not fail_ok:
            raise

def assert_regexp_matches(regexp, text):
    if isinstance(regexp, basestring):
        regexp = re.compile(regexp)
    if not regexp.search(text):
        message = '''Regexp didn't match: %r not found in %r''' % (regexp.pattern, text)
        assert_true(0, message)

def assert_correct_uuid(uuid):
    return assert_regexp_matches(
        '^uuid:[0-9a-f]{32}$',
        uuid
    )

def assert_correct_software_agent(software_agent):
    return assert_regexp_matches(
        '^didjvu [0-9.]+( [(]Gamera [0-9.]+[)])?',
        software_agent
    )

def assert_correct_timestamp(timestamp):
    return assert_regexp_matches(
        '^[0-9]{4}(-[0-9]{2}){2}T[0-9]{2}(:[0-9]{2}){2}([+-][0-9]{2}:[0-9]{2}|Z)$',
        timestamp
    )

class test_metadata():

    def test_empty(self):
        with temporary.file() as xmp_file:
            meta = xmp.Metadata()
            meta.write(xmp_file)
            xmp_file.flush()
            xmp_file.seek(0)
            yield self._test_empty_exiv2(xmp_file), tag_exiv2
            yield self._test_empty_libxmp(xmp_file), tag_libxmp

    def _test_empty_exiv2(self, xmp_file):
        def test(dummy):
            for line in run_exiv2(xmp_file.name, fail_ok=True):
                assert_equal(line, '')
        return test

    def _test_empty_libxmp(self, xmp_file):
        def test(dummy):
            if libxmp is None:
                raise SkipTest(libxmp_import_error)
            import xml.etree.cElementTree as etree
            import cStringIO as io
            meta = libxmp.XMPMeta()
            meta.parse_from_str(xmp_file.read())
            xml_meta = meta.serialize_to_str(omit_all_formatting=True, omit_packet_wrapper=True)
            xml_meta = io.StringIO(xml_meta)
            iterator = etree.iterparse(xml_meta, events=('start', 'end'))
            iterator = iter(iterator) # odd, but needed for Python 2.6
            pop = lambda: next(iterator)
            event, element = pop()
            assert_equal(event, 'start')
            assert_equal(element.tag, '{adobe:ns:meta/}xmpmeta')
            event, element = pop()
            assert_equal(event, 'start')
            assert_equal(element.tag, '{%s}RDF' % ns_rdf)
            event, element = pop()
            assert_equal(event, 'start')
            assert_equal(element.tag, '{%s}Description' % ns_rdf)
            assert_equal(element.attrib['{%s}about' % ns_rdf], '')
            event, element = pop()
            assert_equal(event, 'end')
            event, element = pop()
            assert_equal(event, 'end')
            event, element = pop()
            assert_equal(event, 'end')
            try:
                event, element = pop()
            except StopIteration:
                event, element = None, None
            assert_true(event is None)
        return test

    def test_new(self):
        with temporary.file() as xmp_file:
            meta = xmp.Metadata()
            meta.update(
                media_type='image/x-test',
                internal_properties=[
                    ('test_int', 42),
                    ('test_str', 'eggs'),
                    ('test_bool', True),
                ]
            )
            meta.write(xmp_file)
            xmp_file.flush()
            xmp_file.seek(0)
            yield self._test_new_exiv2(xmp_file), tag_exiv2
            yield self._test_new_libxmp(xmp_file), tag_libxmp

    def _test_new_exiv2(self, xmp_file):
        def test(dummy):
            output = run_exiv2(xmp_file.name)
            def pop():
                return tuple(next(output).rstrip('\n').split(None, 1))
            # Dublin Core:
            assert_equal(pop(), ('Xmp.dc.format', 'image/x-test'))
            # internal properties:
            assert_equal(pop(), ('Xmp.didjvu.test_bool', 'True'))
            assert_equal(pop(), ('Xmp.didjvu.test_int', '42'))
            assert_equal(pop(), ('Xmp.didjvu.test_str', 'eggs'))
            # XMP:
            key, metadata_date = pop()
            assert_correct_timestamp(metadata_date)
            assert_equal(key, 'Xmp.xmp.MetadataDate')
            key, modify_date = pop()
            assert_equal(key, 'Xmp.xmp.ModifyDate')
            assert_correct_timestamp(modify_date)
            assert_equal(metadata_date, modify_date)
            # XMP Media Management:
            assert_equal(pop(), ('Xmp.xmpMM.History', 'type="Seq"'))
            # - History[1]:
            assert_equal(pop(), ('Xmp.xmpMM.History[1]', 'type="Struct"'))
            assert_equal(pop(), ('Xmp.xmpMM.History[1]/stEvt:action', 'converted'))
            key, evt_uuid = pop()
            assert_correct_uuid(evt_uuid)
            assert_equal(key, 'Xmp.xmpMM.History[1]/stEvt:instanceID')
            assert_equal(pop(), ('Xmp.xmpMM.History[1]/stEvt:parameters', 'to image/x-test'))
            key, software_agent = pop()
            assert_equal(key, 'Xmp.xmpMM.History[1]/stEvt:softwareAgent')
            assert_correct_software_agent(software_agent)
            key, evt_date = pop()
            assert_equal((key, evt_date), ('Xmp.xmpMM.History[1]/stEvt:when', modify_date))
            # - InstanceID:
            key, uuid = pop()
            assert_equal(key, 'Xmp.xmpMM.InstanceID')
            assert_correct_uuid(uuid)
            assert_equal(uuid, evt_uuid)
            try:
                line = pop()
            except StopIteration:
                line = None
            assert_true(line is None)
        return test

    def _test_new_libxmp(self, xmp_file):
        def test(dummy):
            if libxmp is None:
                raise SkipTest(libxmp_import_error)
            meta = libxmp.XMPMeta()
            def get(namespace, key):
                return meta.get_property(namespace, key)
            meta.parse_from_str(xmp_file.read())
            assert_equal(get(ns_dc, 'format'), 'image/x-test')
            mod_date = get(ns_xmp, 'ModifyDate')
            metadata_date = get(ns_xmp, 'MetadataDate')
            assert_equal(mod_date, metadata_date)
            uuid = get(ns_xmp_mm, 'InstanceID')
            assert_correct_uuid(uuid)
            assert_equal(get(ns_xmp_mm, 'History[1]/stEvt:action'), 'converted')
            software_agent = get(ns_xmp_mm, 'History[1]/stEvt:softwareAgent')
            assert_correct_software_agent(software_agent)
            assert_equal(get(ns_xmp_mm, 'History[1]/stEvt:parameters'), 'to image/x-test')
            assert_equal(get(ns_xmp_mm, 'History[1]/stEvt:instanceID'), uuid)
            assert_equal(get(ns_xmp_mm, 'History[1]/stEvt:when'), str(mod_date))
            assert_equal(get(xmp.ns_didjvu, 'test_int'), '42')
            assert_equal(get(xmp.ns_didjvu, 'test_str'), 'eggs')
            assert_equal(get(xmp.ns_didjvu, 'test_bool'), 'True')
        return test

    def test_updated(self):
        image_path = os.path.join(os.path.dirname(__file__), 'example.png')
        with temporary.file() as xmp_file:
            meta = xmp.Metadata()
            meta.import_(image_path)
            meta.update(
                media_type='image/x-test',
                internal_properties=[
                    ('test_int', 42),
                    ('test_str', 'eggs'),
                    ('test_bool', True),
                ]
            )
            meta.write(xmp_file)
            xmp_file.flush()
            xmp_file.seek(0)
            yield self._test_updated_exiv2(xmp_file), tag_exiv2
            yield self._test_updated_libxmp(xmp_file), tag_libxmp

    _original_software_agent = 'scanhelper 0.2.4'
    _original_create_date = '2012-02-01T16:28:00+01:00'
    _original_uuid = 'uuid:a2686c01b50e4b6aab2cccdef40f6286'

    def _test_updated_exiv2(self, xmp_file):
        def test(dummy):
            output = run_exiv2(xmp_file.name)
            def pop():
                return tuple(next(output).rstrip('\n').split(None, 1))
            # Dublin Core:
            assert_equal(pop(), ('Xmp.dc.format', 'image/x-test'))
            # internal properties:
            assert_equal(pop(), ('Xmp.didjvu.test_bool', 'True'))
            assert_equal(pop(), ('Xmp.didjvu.test_int', '42'))
            assert_equal(pop(), ('Xmp.didjvu.test_str', 'eggs'))
            # TIFF:
            assert_equal(pop(), ('Xmp.tiff.ImageHeight', '42'))
            assert_equal(pop(), ('Xmp.tiff.ImageWidth', '69'))
            # XMP:
            key, create_date = pop()
            assert_equal((key, create_date), ('Xmp.xmp.CreateDate', self._original_create_date))
            assert_equal(pop(), ('Xmp.xmp.CreatorTool', self._original_software_agent))
            key, metadata_date = pop()
            assert_equal(key, 'Xmp.xmp.MetadataDate')
            assert_correct_timestamp(metadata_date)
            key, modify_date = pop()
            assert_equal(key, 'Xmp.xmp.ModifyDate')
            assert_correct_timestamp(modify_date)
            assert_equal(metadata_date, modify_date)
            # XMP Media Management:
            assert_equal(pop(), ('Xmp.xmpMM.History', 'type="Seq"'))
            # - History[1]:
            assert_equal(pop(), ('Xmp.xmpMM.History[1]', 'type="Struct"'))
            assert_equal(pop(), ('Xmp.xmpMM.History[1]/stEvt:action', 'created'))
            key, original_uuid = pop()
            assert_equal(key, 'Xmp.xmpMM.History[1]/stEvt:instanceID')
            assert_correct_uuid(original_uuid)
            assert_equal(original_uuid, self._original_uuid)
            assert_equal(pop(), ('Xmp.xmpMM.History[1]/stEvt:softwareAgent', self._original_software_agent))
            assert_equal(pop(), ('Xmp.xmpMM.History[1]/stEvt:when', create_date))
            # - History[2]
            assert_equal(pop(), ('Xmp.xmpMM.History[2]', 'type="Struct"'))
            assert_equal(pop(), ('Xmp.xmpMM.History[2]/stEvt:action', 'converted'))
            key, evt_uuid = pop()
            assert_equal(key, 'Xmp.xmpMM.History[2]/stEvt:instanceID')
            assert_correct_uuid(evt_uuid)
            assert_equal(pop(), ('Xmp.xmpMM.History[2]/stEvt:parameters', 'from image/png to image/x-test'))
            key, software_agent = pop()
            assert_equal(key, 'Xmp.xmpMM.History[2]/stEvt:softwareAgent')
            assert_correct_software_agent(software_agent)
            assert_equal(pop(), ('Xmp.xmpMM.History[2]/stEvt:when', metadata_date))
            # - InstanceID:
            key, uuid = pop()
            assert_equal(key, 'Xmp.xmpMM.InstanceID')
            assert_correct_uuid(evt_uuid)
            assert_equal(uuid, evt_uuid)
            assert_not_equal(uuid, original_uuid)
            try:
                line = pop()
            except StopIteration:
                line = None
            assert_true(line is None)
        return test

    def _test_updated_libxmp(self, xmp_file):
        def test(dummy):
            if libxmp is None:
                raise SkipTest(libxmp_import_error)
            meta = libxmp.XMPMeta()
            def get(namespace, key):
                return meta.get_property(namespace, key)
            meta.parse_from_str(xmp_file.read())
            assert_equal(get(ns_dc, 'format'), 'image/x-test')
            assert_equal(get(ns_tiff, 'ImageWidth'), '69')
            assert_equal(get(ns_tiff, 'ImageHeight'), '42')
            assert_equal(get(ns_xmp, 'CreatorTool'), self._original_software_agent)
            create_date = get(ns_xmp, 'CreateDate')
            assert_equal(create_date, self._original_create_date)
            mod_date = get(ns_xmp, 'ModifyDate')
            assert_true(mod_date > create_date)
            metadata_date = get(ns_xmp, 'MetadataDate')
            assert_equal(mod_date, metadata_date)
            uuid = get(ns_xmp_mm, 'InstanceID')
            assert_correct_uuid(uuid)
            # History[1]
            assert_equal(get(ns_xmp_mm, 'History[1]/stEvt:action'), 'created')
            assert_equal(get(ns_xmp_mm, 'History[1]/stEvt:softwareAgent'), self._original_software_agent)
            original_uuid = get(ns_xmp_mm, 'History[1]/stEvt:instanceID')
            assert_correct_uuid(original_uuid)
            assert_equal(original_uuid, self._original_uuid)
            assert_not_equal(uuid, original_uuid)
            assert_equal(get(ns_xmp_mm, 'History[1]/stEvt:when'), create_date)
            # History[2]
            assert_equal(get(ns_xmp_mm, 'History[2]/stEvt:action'), 'converted')
            software_agent = get(ns_xmp_mm, 'History[2]/stEvt:softwareAgent')
            assert_correct_software_agent(software_agent)
            assert_equal(get(ns_xmp_mm, 'History[2]/stEvt:parameters'), 'from image/png to image/x-test')
            assert_equal(get(ns_xmp_mm, 'History[2]/stEvt:instanceID'), uuid)
            assert_equal(get(ns_xmp_mm, 'History[2]/stEvt:when'), mod_date)
            # internal properties
            assert_equal(get(xmp.ns_didjvu, 'test_int'), '42')
            assert_equal(get(xmp.ns_didjvu, 'test_str'), 'eggs')
            assert_equal(get(xmp.ns_didjvu, 'test_bool'), 'True')
        return test

# vim:ts=4 sw=4 et
