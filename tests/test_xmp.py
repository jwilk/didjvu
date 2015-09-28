# encoding=UTF-8

# Copyright © 2012-2015 Jakub Wilk <jwilk@jwilk.net>
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

import io
import logging
import os
import sys
import xml.etree.cElementTree as etree

from .tools import (
    SkipTest,
    assert_equal,
    assert_greater,
    assert_is_none,
    assert_not_equal,
    assert_raises,
    assert_regex,
    assert_rfc3339_timestamp,
)

xmp_backends = []

from lib import ipc
from lib import temporary
from lib import xmp
from lib.xmp import namespaces as ns

if sys.version_info >= (2, 7):
    from importlib import import_module
else:
    def import_module(mod):
        return __import__(mod, fromlist=[''], level=0)

def import_backend(name):
    mod_name = 'lib.xmp.{0}_backend'.format(name)
    try:
        backend = import_module(mod_name)
    except ImportError as import_error:
        class backend:
            # dummy replacement
            class MetadataBase(object):
                def __init__(self):
                    raise SkipTest(import_error)
        backend.__name__ = mod_name
    return backend

xmp_backends = [
    import_backend(name)
    for name in [
        'gexiv2',
        'libxmp',
        'pyexiv2',
    ]
]
del name

try:
    import libxmp
    import libxmp.consts
except ImportError as libxmp_import_error:
    libxmp = None

def test_uuid():
    uuid1 = xmp.gen_uuid()
    assert_uuid_urn(uuid1)
    uuid2 = xmp.gen_uuid()
    assert_uuid_urn(uuid2)
    assert_not_equal(uuid1, uuid2)

def tag_backend(backend):
    class tag(object):
        def __repr__(self):
            return backend.__name__.split('.')[-1]
    return tag()

class tag_exiv2(object):
    def __repr__(self):
        return 'exiv2_checker'
tag_exiv2 = tag_exiv2()

class tag_libxmp(object):
    def __repr__(self):
        return 'libxmp_checker'
tag_libxmp = tag_libxmp()

def run_exiv2(filename, fail_ok=False):
    try:
        child = ipc.Subprocess(
            ['exiv2', 'print', '-P', 'Xkt', filename],
            stdout=ipc.PIPE,
            stderr=ipc.PIPE,
        )
    except OSError as ex:
        raise SkipTest(ex)
    for line in sorted(child.stdout):
        yield line
    stderr = child.stderr.read()
    if not fail_ok:
        assert_equal(stderr, '')
    try:
        child.wait()
    except ipc.CalledProcessError:
        if not fail_ok:
            raise

_uuid_regex = (
    r'\Aurn:uuid:XXXXXXXX-XXXX-4XXX-[89ab]XXX-XXXXXXXXXXXX\Z'
    .replace('X', '[0-9a-f]')
)

def assert_uuid_urn(uuid):
    return assert_regex(
        uuid,
        _uuid_regex,
    )

def assert_correct_software_agent(software_agent):
    return assert_regex(
        software_agent,
        '^didjvu [0-9.]+( [(]Gamera [0-9.]+[)])?',
    )

def test_namespaces():
    if libxmp is None:
        raise SkipTest(libxmp_import_error)
    assert_equal(libxmp.consts.XMP_NS_DC, ns.dc)
    assert_equal(libxmp.consts.XMP_NS_RDF, ns.rdf)
    assert_equal(libxmp.consts.XMP_NS_TIFF, ns.tiff)
    assert_equal(libxmp.consts.XMP_NS_XMP, ns.xmp)
    assert_equal(libxmp.consts.XMP_NS_XMP_MM, ns.xmpmm)

class test_metadata():

    def test_empty(self):
        for backend in xmp_backends:
            with temporary.file() as xmp_file:
                exc = None
                try:
                    meta = xmp.metadata(backend=backend)
                    meta.write(xmp_file)
                    xmp_file.flush()
                    xmp_file.seek(0)
                except Exception as exc:
                    pass
                yield self._test_empty_exiv2(xmp_file, exception=exc), tag_backend(backend), tag_exiv2
                yield self._test_empty_libxmp(xmp_file, exception=exc), tag_backend(backend), tag_libxmp

    def _test_empty_exiv2(self, xmp_file, exception=None):
        def test(*dummy):
            if exception is not None:
                raise exception
            for line in run_exiv2(xmp_file.name, fail_ok=True):
                assert_equal(line, '')
        return test

    def _test_empty_libxmp(self, xmp_file, exception=None):
        def test(*dummy):
            if exception is not None:
                raise exception
            if libxmp is None:
                raise SkipTest(libxmp_import_error)
            meta = libxmp.XMPMeta()
            meta.parse_from_str(xmp_file.read())
            xml_meta = meta.serialize_to_str(omit_all_formatting=True, omit_packet_wrapper=True)
            logging.debug(repr(xml_meta))
            xml_meta = io.StringIO(xml_meta)
            iterator = etree.iterparse(xml_meta, events=('start', 'end'))
            iterator = iter(iterator)  # odd, but needed for Python 2.6
            pop = lambda: next(iterator)
            event, element = pop()
            assert_equal(event, 'start')
            assert_equal(element.tag, '{adobe:ns:meta/}xmpmeta')
            event, element = pop()
            assert_equal(event, 'start')
            assert_equal(element.tag, '{%s}RDF' % ns.rdf)
            event, element = pop()
            assert_equal(event, 'start')
            assert_equal(element.tag, '{%s}Description' % ns.rdf)
            assert_equal(element.attrib['{%s}about' % ns.rdf], '')
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
            assert_is_none(event)
        return test

    def test_new(self):
        for backend in xmp_backends:
            with temporary.file() as xmp_file:
                exc = None
                try:
                    meta = xmp.metadata(backend=backend)
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
                except Exception as exc:
                    pass
                yield self._test_new_exiv2(xmp_file, exception=exc), tag_backend(backend), tag_exiv2
                yield self._test_new_libxmp(xmp_file, exception=exc), tag_backend(backend), tag_libxmp

    def _test_new_exiv2(self, xmp_file, exception=None):
        def test(*dummy):
            if exception is not None:
                raise exception
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
            assert_rfc3339_timestamp(metadata_date)
            assert_equal(key, 'Xmp.xmp.MetadataDate')
            key, modify_date = pop()
            assert_equal(key, 'Xmp.xmp.ModifyDate')
            assert_rfc3339_timestamp(modify_date)
            assert_equal(metadata_date, modify_date)
            # XMP Media Management:
            # - DocumentID:
            key, document_id = pop()
            assert_equal(key, 'Xmp.xmpMM.DocumentID')
            assert_uuid_urn(document_id)
            # - History:
            assert_equal(pop(), ('Xmp.xmpMM.History', 'type="Seq"'))
            # - History[1]:
            assert_equal(pop(), ('Xmp.xmpMM.History[1]', 'type="Struct"'))
            assert_equal(pop(), ('Xmp.xmpMM.History[1]/stEvt:action', 'converted'))
            key, evt_instance_id = pop()
            assert_uuid_urn(evt_instance_id)
            assert_equal(key, 'Xmp.xmpMM.History[1]/stEvt:instanceID')
            assert_equal(pop(), ('Xmp.xmpMM.History[1]/stEvt:parameters', 'to image/x-test'))
            key, software_agent = pop()
            assert_equal(key, 'Xmp.xmpMM.History[1]/stEvt:softwareAgent')
            assert_correct_software_agent(software_agent)
            key, evt_date = pop()
            assert_equal((key, evt_date), ('Xmp.xmpMM.History[1]/stEvt:when', modify_date))
            # - InstanceID:
            key, instance_id = pop()
            assert_equal(key, 'Xmp.xmpMM.InstanceID')
            assert_uuid_urn(instance_id)
            assert_equal(instance_id, evt_instance_id)
            try:
                line = pop()
            except StopIteration:
                line = None
            assert_is_none(line)
        return test

    def _test_new_libxmp(self, xmp_file, exception=None):
        def test(*dummy):
            if exception is not None:
                raise exception
            if libxmp is None:
                raise SkipTest(libxmp_import_error)
            meta = libxmp.XMPMeta()
            def get(namespace, key):
                return meta.get_property(namespace, key)
            meta.parse_from_str(xmp_file.read())
            assert_equal(get(ns.dc, 'format'), 'image/x-test')
            mod_date = get(ns.xmp, 'ModifyDate')
            metadata_date = get(ns.xmp, 'MetadataDate')
            assert_equal(mod_date, metadata_date)
            document_id = get(ns.xmpmm, 'DocumentID')
            assert_uuid_urn(document_id)
            instance_id = get(ns.xmpmm, 'InstanceID')
            assert_uuid_urn(instance_id)
            assert_equal(get(ns.xmpmm, 'History[1]/stEvt:action'), 'converted')
            software_agent = get(ns.xmpmm, 'History[1]/stEvt:softwareAgent')
            assert_correct_software_agent(software_agent)
            assert_equal(get(ns.xmpmm, 'History[1]/stEvt:parameters'), 'to image/x-test')
            assert_equal(get(ns.xmpmm, 'History[1]/stEvt:instanceID'), instance_id)
            assert_equal(get(ns.xmpmm, 'History[1]/stEvt:when'), str(mod_date))
            assert_equal(get(ns.didjvu, 'test_int'), '42')
            assert_equal(get(ns.didjvu, 'test_str'), 'eggs')
            assert_equal(get(ns.didjvu, 'test_bool'), 'True')
        return test

    def test_updated(self):
        image_path = os.path.join(os.path.dirname(__file__), 'data', 'example.png')
        for backend in xmp_backends:
            with temporary.file() as xmp_file:
                exc = None
                try:
                    meta = xmp.metadata(backend=backend)
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
                except Exception as exc:
                    pass
                yield self._test_updated_exiv2(xmp_file, exception=exc), tag_backend(backend), tag_exiv2
                yield self._test_updated_libxmp(xmp_file, exception=exc), tag_backend(backend), tag_libxmp

    _original_software_agent = 'scanhelper 0.6'
    _original_create_date = '2012-02-01T16:28:00+01:00'
    _original_document_id = 'urn:uuid:04fa0637-2b6e-417c-9fff-d6f0f02c08a6'
    _original_instance_id = 'urn:uuid:c3745412-65c0-4db4-880f-34fb57beddc0'

    def _test_updated_exiv2(self, xmp_file, exception=None):
        def test(*dummy):
            if exception is not None:
                raise exception
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
            assert_rfc3339_timestamp(metadata_date)
            key, modify_date = pop()
            assert_equal(key, 'Xmp.xmp.ModifyDate')
            assert_rfc3339_timestamp(modify_date)
            assert_equal(metadata_date, modify_date)
            # XMP Media Management:
            # - DocumentID:
            key, document_id = pop()
            assert_equal(key, 'Xmp.xmpMM.DocumentID')
            assert_uuid_urn(document_id)
            assert_not_equal(document_id, self._original_document_id)
            # - History:
            assert_equal(pop(), ('Xmp.xmpMM.History', 'type="Seq"'))
            # - History[1]:
            assert_equal(pop(), ('Xmp.xmpMM.History[1]', 'type="Struct"'))
            assert_equal(pop(), ('Xmp.xmpMM.History[1]/stEvt:action', 'created'))
            key, original_instance_id = pop()
            assert_equal(key, 'Xmp.xmpMM.History[1]/stEvt:instanceID')
            assert_equal(original_instance_id, self._original_instance_id)
            assert_equal(pop(), ('Xmp.xmpMM.History[1]/stEvt:softwareAgent', self._original_software_agent))
            assert_equal(pop(), ('Xmp.xmpMM.History[1]/stEvt:when', create_date))
            # - History[2]:
            assert_equal(pop(), ('Xmp.xmpMM.History[2]', 'type="Struct"'))
            assert_equal(pop(), ('Xmp.xmpMM.History[2]/stEvt:action', 'converted'))
            key, evt_instance_id = pop()
            assert_equal(key, 'Xmp.xmpMM.History[2]/stEvt:instanceID')
            assert_uuid_urn(evt_instance_id)
            assert_equal(pop(), ('Xmp.xmpMM.History[2]/stEvt:parameters', 'from image/png to image/x-test'))
            key, software_agent = pop()
            assert_equal(key, 'Xmp.xmpMM.History[2]/stEvt:softwareAgent')
            assert_correct_software_agent(software_agent)
            assert_equal(pop(), ('Xmp.xmpMM.History[2]/stEvt:when', metadata_date))
            # - InstanceID:
            key, instance_id = pop()
            assert_equal(key, 'Xmp.xmpMM.InstanceID')
            assert_uuid_urn(instance_id)
            assert_equal(instance_id, evt_instance_id)
            assert_not_equal(instance_id, original_instance_id)
            # - OriginalDocumentID:
            key, original_document_id = pop()
            assert_equal(key, 'Xmp.xmpMM.OriginalDocumentID')
            assert_equal(original_document_id, self._original_document_id)
            try:
                line = pop()
            except StopIteration:
                line = None
            assert_is_none(line)
        return test

    def _test_updated_libxmp(self, xmp_file, exception=None):
        def test(*dummy):
            if exception is not None:
                raise exception
            if libxmp is None:
                raise SkipTest(libxmp_import_error)
            meta = libxmp.XMPMeta()
            def get(namespace, key):
                return meta.get_property(namespace, key)
            meta.parse_from_str(xmp_file.read())
            assert_equal(get(ns.dc, 'format'), 'image/x-test')
            assert_equal(get(ns.tiff, 'ImageWidth'), '69')
            assert_equal(get(ns.tiff, 'ImageHeight'), '42')
            assert_equal(get(ns.xmp, 'CreatorTool'), self._original_software_agent)
            create_date = get(ns.xmp, 'CreateDate')
            assert_equal(create_date, self._original_create_date)
            mod_date = get(ns.xmp, 'ModifyDate')
            assert_greater(mod_date, create_date)
            metadata_date = get(ns.xmp, 'MetadataDate')
            assert_equal(mod_date, metadata_date)
            # (Original)DocumentID:
            original_document_id = get(ns.xmpmm, 'OriginalDocumentID')
            assert_equal(original_document_id, self._original_document_id)
            document_id = get(ns.xmpmm, 'DocumentID')
            assert_uuid_urn(document_id)
            assert_not_equal(document_id, original_document_id)
            assert_uuid_urn(document_id)
            # InstanceID:
            instance_id = get(ns.xmpmm, 'InstanceID')
            assert_uuid_urn(instance_id)
            # History[1]:
            assert_equal(get(ns.xmpmm, 'History[1]/stEvt:action'), 'created')
            assert_equal(get(ns.xmpmm, 'History[1]/stEvt:softwareAgent'), self._original_software_agent)
            original_instance_id = get(ns.xmpmm, 'History[1]/stEvt:instanceID')
            assert_equal(original_instance_id, self._original_instance_id)
            assert_not_equal(instance_id, original_instance_id)
            assert_equal(get(ns.xmpmm, 'History[1]/stEvt:when'), create_date)
            # History[2]:
            assert_equal(get(ns.xmpmm, 'History[2]/stEvt:action'), 'converted')
            software_agent = get(ns.xmpmm, 'History[2]/stEvt:softwareAgent')
            assert_correct_software_agent(software_agent)
            assert_equal(get(ns.xmpmm, 'History[2]/stEvt:parameters'), 'from image/png to image/x-test')
            assert_equal(get(ns.xmpmm, 'History[2]/stEvt:instanceID'), instance_id)
            assert_equal(get(ns.xmpmm, 'History[2]/stEvt:when'), mod_date)
            # internal properties:
            assert_equal(get(ns.didjvu, 'test_int'), '42')
            assert_equal(get(ns.didjvu, 'test_str'), 'eggs')
            assert_equal(get(ns.didjvu, 'test_bool'), 'True')
        return test

    def test_io_error(self):
        def t(*dummy):
            image_path = os.path.join(os.path.dirname(__file__), 'data', 'nonexistent.png')
            meta = xmp.metadata(backend=backend)
            meta.import_(image_path)
            with temporary.directory() as tmpdir:
                os.chmod(tmpdir, 0o000)
                try:
                    image_path = os.path.join(tmpdir, 'example.png')
                    meta = xmp.metadata(backend=backend)
                    with assert_raises(IOError):
                        meta.import_(image_path)
                finally:
                    os.chmod(tmpdir, 0o700)
        for backend in xmp_backends:
            yield t, tag_backend(backend)

# vim:ts=4 sts=4 sw=4 et
