# encoding=UTF-8

# Copyright © 2011, 2012 Jakub Wilk <jwilk@jwilk.net>
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
import re

debian = os.path.exists('/etc/debian_version')

def enhance_import_error(exception, package, debian_package, homepage):
    message = str(exception)
    format = '%(message)s; please install the %(package)s package'
    if debian:
        package = debian_package
    else:
        format += ' <%(homepage)s>'
    exception.args = [format % locals()]

# vim:ts=4 sw=4 et
