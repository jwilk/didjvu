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

from nose import SkipTest
from nose.tools import assert_true, assert_equal

from lib import ipc
from lib import temporary
from lib import xmp

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
            ['exiv2', 'pr', '-p', 'x', filename],
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

class test_metadata():

    def test_empty(self):
        with temporary.file() as xmp_file:
            meta = xmp.Metadata()
            meta.write(xmp_file)
            xmp_file.flush()
            yield self._test_empty_exiv2(xmp_file), tag_exiv2
            yield self._test_empty_libxmp(xmp_file), tag_libxmp

    def _test_empty_exiv2(self, xmp_file):
        def test(dummy):
            for line in run_exiv2(xmp_file.name, fail_ok=True):
                assert_equal(line, '')
        return test

    def _test_empty_libxmp(self, xmp_file):
        def test(dummy):
            try:
                import libxmp
                import xml.etree.cElementTree as etree
                import cStringIO as io
            except ImportError, ex:
                raise SkipTest(ex)
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
            assert_equal(element.tag, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF')
            event, element = pop()
            assert_equal(event, 'start')
            assert_equal(element.tag, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description')
            assert_equal(element.attrib['{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about'], '')
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

# vim:ts=4 sw=4 et
