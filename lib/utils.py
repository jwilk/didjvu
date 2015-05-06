# encoding=UTF-8

# Copyright © 2011-2015 Jakub Wilk <jwilk@jwilk.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

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

# vim:ts=4 sts=4 sw=4 et
