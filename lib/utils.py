# encoding=UTF-8

# Copyright © 2011-2015 Jakub Wilk <jwilk@jwilk.net>
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

'''various helper functions'''

import os

debian = os.path.exists('/etc/debian_version')

def enhance_import_error(exception, package, debian_package, homepage):
    message = str(exception)
    if debian:
        package = debian_package
    message += '; please install the {pkg} package'.format(pkg=package)
    if not debian:
        message += ' <{url}>'.format(url=homepage)
    exception.args = [message]

class namespace():
    pass

class Proxy(object):

    def __init__(self, obj, wait_fn, temporaries):
        self._object = obj
        self._wait_fn = wait_fn
        self._temporaries = temporaries

    def __getattribute__(self, name):
        if name.startswith('_'):
            return object.__getattribute__(self, name)
        self._wait_fn()
        self._wait_fn = int
        return getattr(self._object, name)

    def __setattr__(self, name, value):
        if name.startswith('_'):
            return object.__setattr__(self, name, value)
        self._wait_fn()
        self._wait_fn = int
        setattr(self._object, name, value)

# vim:ts=4 sts=4 sw=4 et
