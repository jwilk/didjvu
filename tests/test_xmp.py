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
import re

from nose import SkipTest
from nose.tools import assert_true, assert_equal

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
    )
except ImportError, libxmp_import_error:
    libxmp = None

def test_rfc3339():
    timestamp = datetime.datetime(2012, 3, 7, 12, 43, 26, 23692)
    result = xmp.rfc3339(timestamp)
    assert_equal(result, '2012-03-07T12:43:26Z')

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
    for line in child.stdout:
        yield line
    try:
        child.wait()
    except ipc.CalledProcessError:
        if not fail_ok:
            raise

def assert_correct_uuid(uuid):
    return assert_true(re.match(
        '^uuid:[0-9a-f]{32}$',
        uuid
    ))

def assert_correct_software_agent(software_agent):
    return assert_true(re.match(
        'didjvu [0-9.]+( [(]Gamera [0-9.]+[)])?',
        software_agent
    ))

def assert_correct_timestamp(timestamp):
    return assert_true(re.match(
        '[0-9]{4}(-[0-9]{2}){2}T[0-9]{2}(:[0-9]{2}){2}$',
        timestamp
    ))
    # FIXME: what about timezone?

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
            assert_equal(pop(), ('Xmp.dc.format', 'image/x-test'))
            key, mod_date = pop()
            assert_equal(key, 'Xmp.xmp.ModifyDate')
            assert_correct_timestamp(mod_date)
            assert_equal(pop(), ('Xmp.xmp.MetadataDate', mod_date))
            key, uuid = pop()
            assert_equal(key, 'Xmp.xmpMM.InstanceID')
            assert_correct_uuid(uuid)
            assert_equal(pop(), ('Xmp.xmpMM.History', 'type="Seq"'))
            assert_equal(pop(), ('Xmp.xmpMM.History[1]', 'type="Struct"'))
            assert_equal(pop(), ('Xmp.xmpMM.History[1]/stEvt:action', 'converted'))
            key, software_agent = pop()
            assert_equal(key, 'Xmp.xmpMM.History[1]/stEvt:softwareAgent')
            assert_correct_software_agent(software_agent)
            assert_equal(pop(), ('Xmp.xmpMM.History[1]/stEvt:parameters', 'to image/x-test'))
            assert_equal(pop(), ('Xmp.xmpMM.History[1]/stEvt:instanceID', uuid))
            assert_equal(pop(), ('Xmp.xmpMM.History[1]/stEvt:when', mod_date + 'Z')) # FIXME: what about timezone?
            assert_equal(pop(), ('Xmp.didjvu.test_int', '42'))
            assert_equal(pop(), ('Xmp.didjvu.test_str', 'eggs'))
            assert_equal(pop(), ('Xmp.didjvu.test_bool', 'True'))
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
            assert_true(type(mod_date), datetime.datetime)
            metadata_date = get(ns_xmp, 'MetadataDate')
            assert_true(type(metadata_date), datetime.datetime)
            assert_equal(mod_date, metadata_date)
            uuid = get(ns_xmp_mm, 'InstanceID')
            assert_correct_uuid(uuid)
            assert_equal(get(ns_xmp_mm, 'History[1]/stEvt:action'), 'converted')
            software_agent = get(ns_xmp_mm, 'History[1]/stEvt:softwareAgent')
            assert_correct_software_agent(software_agent)
            assert_equal(get(ns_xmp_mm, 'History[1]/stEvt:parameters'), 'to image/x-test')
            assert_equal(get(ns_xmp_mm, 'History[1]/stEvt:instanceID'), uuid)
            assert_equal(get(ns_xmp_mm, 'History[1]/stEvt:when'), str(mod_date) + 'Z') # FIXME: what about timezone?
            assert_equal(get(xmp.ns_didjvu, 'test_int'), '42')
            assert_equal(get(xmp.ns_didjvu, 'test_str'), 'eggs')
            assert_equal(get(xmp.ns_didjvu, 'test_bool'), 'True')
        return test

# vim:ts=4 sw=4 et
