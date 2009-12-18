# encoding=UTF-8
# Copyright © 2009 Jakub Wilk <ubanus@users.sf.net>
#
# This package is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This package is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

import sys
import imp

class Loader(object):

    def __init__(self, *args):
        self.args = args

    def load_module(self, fullname):
        return imp.load_module(fullname, *self.args)

class Importer(object):

    def find_module(self, fullname, path=None):
        if fullname != 'didjvu':
            return
        args = imp.find_module('lib', path)
        return Loader(*args)

sys.meta_path = [Importer()]

# vim:ts=4 sw=4 et
