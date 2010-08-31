# encoding=UTF-8

# Copyright © 2009, 2010 Jakub Wilk <jwilk@jwilk.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.

import os
import re
import sys
import signal
import subprocess

from subprocess import CalledProcessError

DEBUG = False

def get_signal_names():
    _signame_pattern = re.compile('^SIG[A-Z0-9]*$')
    data = dict(
        (name, getattr(signal, name))
        for name in dir(signal)
        if _signame_pattern.match(name)
    )
    try:
        if data['SIGABRT'] == data['SIGIOT']:
            del data['SIGIOT']
    except KeyError:
        pass
    try:
        if data['SIGCHLD'] == data['SIGCLD']:
            del data['SIGCLD']
    except KeyError:
        pass
    return dict((no, name) for name, no in data.iteritems())

class CalledProcessInterrupted(CalledProcessError):

    _signal_names = get_signal_names()

    def __init__(self, signal_id, command):
        Exception.__init__(self, command, signal_id)
    def __str__(self):
        signal_name = self._signal_names.get(self.args[1], self.args[1])
        return 'Command %r was interrputed by signal %s' % (self.args[0], signal_name)

del get_signal_names

PIPE = subprocess.PIPE
from subprocess import CalledProcessError

def shell_escape(s, safe=re.compile('^[a-zA-Z0-9_+/=.,-]+$').match):
    if safe(s):
        return s
    return "'%s'" % s.replace("'", r"'\''")

class Subprocess(subprocess.Popen):

    def __init__(self, *args, **kwargs):
        env_override = kwargs.pop('env', {})
        if env_override.get('LC_ALL', '') is None:
            # Reset all locale variables
            env = dict(
                (k, v)
                for k, v in os.environ.iteritems()
                if not (k.startswith('LC_') or k in ('LANG', 'LANGUAGES'))
            )
            del env_override['LC_ALL']
        else:
            env = dict(os.environ)
        env.update(env_override)
        kwargs['env'] = env
        if os.name == 'posix':
            kwargs.update(close_fds=True)
        try:
            commandline = kwargs['args']
        except KeyError:
            commandline = args[0]
        if DEBUG:
            print >>sys.stderr, '+', ' '.join(shell_escape(s) for s in commandline)
        self.__command = commandline[0]
        subprocess.Popen.__init__(self, *args, **kwargs)

    def wait(self):
        return_code = subprocess.Popen.wait(self)
        if return_code > 0:
            raise CalledProcessError(return_code, self.__command)
        if return_code < 0:
            raise CalledProcessInterrupted(-return_code, self.__command)

class Proxy(object):

    def __init__(self, object, wait_fn, temporaries):
        self._object = object
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

__all__ = [
    'DEBUG',
    'PIPE', 'Subprocess', 'Proxy',
]

# vim:ts=4 sw=4 et
