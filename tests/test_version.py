# encoding=UTF-8

# Copyright © 2015-2018 Jakub Wilk <jwilk@jwilk.net>
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

import os
import re
import xml.etree.cElementTree as etree

from .tools import (
    assert_equal,
    assert_is_instance,
    assert_is_not_none,
    assert_true,
)

from lib import version

here = os.path.dirname(__file__)
docdir = os.path.join(here, os.pardir, 'doc')

def test_changelog():
    path = os.path.join(docdir, 'changelog')
    with open(path, 'rt') as file:
        line = file.readline()
    changelog_version = line.split()[1].strip('()')
    assert_equal(changelog_version, version.__version__)

def test_manpage():
    path = os.path.join(docdir, 'manpage.xml')
    for event, elem in etree.iterparse(path):
        if elem.tag == 'refmiscinfo' and elem.get('class') == 'version':
            assert_equal(elem.text, version.__version__)
            break
    else:
        assert_true(False, msg="missing <refmiscinfo class='version'>")

def test_get_software_agent():
    r = version.get_software_agent()
    assert_is_instance(r, str)
    match = re.match('^didjvu [0-9.]+ [(]Gamera [0-9.]+[)]$', r)
    assert_is_not_none(match)

# vim:ts=4 sts=4 sw=4 et
