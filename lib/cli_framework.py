# encoding=UTF-8

# Copyright © 2009 Jakub Wilk <jwilk@jwilk.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.

'''Command line interface framework'''

import collections
import getopt
import inspect
import itertools
import os.path
import sys

class ArgType(object):

    metavar = 'value'

    def __init__(self, parser):
        self.parser = parser

    def __call__(self, value):
        raise NotImplementedError

class IntType(ArgType):

    metavar = 'n'
    min = None
    max = None

    def __init__(self, parser, min=None, max=None):
        ArgType.__init__(self, parser)
        if self.min is not None:
            self.min = min
        if self.max is not None:
            self.max = max

    def __call__(self, value):
        result = int(value)
        if self.min is not None and result < self.min:
            raise ValueError
        if self.max is not None and result > self.max:
            raise ValueError
        return result

class StringType(ArgType):

    def __call__(self, value):
        return value

class ChoiceType(ArgType):

    choices = {}

    def __init__(self, parser, choices=None):
        ArgType.__init__(self, parser)
        if choices is not None:
            self.choices = choices

    def __call__(self, value):
        return self.choices[value]

class UnicodeType(ArgType):

    metavar = 'text'

    def __init__(self, parser, errors='strict'):
        ArgType.__init__(self, parser)
        self._errors = errors

    def __call__(self, value):
        return value.decode(value, errors=self._errors)

class OptionGroup(object):

    def __init__(self, setter):
        self.setter = setter
        self._options = []

    def __iter__(self):
        return iter(self._options)

    def add(self, option):
        self._options.append(option)
        option.setter = self.setter

class Option(object):

    _counter = itertools.count()

    def __init__(self, *names, **kwargs):
        self._creation_order = self._counter.next()
        self.names = list(names)
        self.type = kwargs.pop('type', StringType)
        self.hidden = kwargs.pop('hidden', False)
        self.n_args = 0
        self.metavar = kwargs.pop('metavar', self.type.metavar)
        self._setter = None

    def __lt__(self, other):
        return self._creation_order < other._creation_order

    def _get_setter(self):
        return self._setter

    def _set_setter(self, setter):
        setter_args, _, _, _ = inspect.getargspec(setter)
        n_args = self.n_args = len(setter_args) - 1
        if n_args == 0:
            option_with_arg = False
        elif n_args == 1:
            option_with_arg = True
        else:
            raise '%s() should take at most 2 arguments' % (setter.__name__,)
        self._setter = setter

    setter = property(_get_setter, _set_setter)

    def __call__(self, setter):
        if isinstance(setter, OptionGroup):
            option_group = setter
            setter = option_group.setter
        else:
            option_group = OptionGroup(setter)
        option_group.add(self)
        return option_group

def option(*args, **kwargs):
    return Option(*args, **kwargs)

class BadCommandLine(Exception):
    pass

class BadOption(BadCommandLine):
    pass

class BadArguments(BadCommandLine):
    pass

class NotEnoughArguments(BadArguments):
    pass

class TooManyArguments(BadArguments):
    pass

class OptionParser(object):

    version = None
    getopt = staticmethod(getopt.gnu_getopt)

    help_fp = sys.stderr
    help_exitcode = 0
    usage_template = '%(argv0)s [options] [arguments]'
    show_all_options = False

    version_template = '%(argv0)s %(version)s'
    version_fp = sys.stderr
    version_exitcode = 0

    def __init__(self, argv):
        self._argv0 = os.path.basename(argv[0])
        self._options = set()
        option_names = {}
        setter_to_options = collections.defaultdict(list)
        getopt_short = []
        getopt_long = []
        for key, value in inspect.getmembers(self):
            if isinstance(value, OptionGroup):
                option_group = value
                for option in option_group:
                    self._options.add(option)
                    setter = option_group.setter
                    for option_name in option.names:
                        if option_name.startswith('--'):
                            getopt_long += option_name[2:] + ('=' if option.n_args else ''),
                        elif option_name.startswith('-') and len(option_name) == 2 and option_name[1].isalpha():
                            getopt_short += option_name[1] + (':' if option.n_args else ''),
                        else:
                            raise ValueError('Bad option name: %r' % (option_name))
                        option_names[option_name] = option
                    setter_to_options[setter].append(option)
        try:
            options, argv = self.getopt(argv[1:], ''.join(getopt_short), getopt_long)
        except getopt.GetoptError, ex:
            raise BadOption(str(ex))
        for option_name, option_argument in options:
            option = option_names[option_name]
            if option.n_args:
                option_args = [option.type(self)(option_argument)]
            else:
                option_args = []
            option.setter(self, *option_args)
        self.call_handle_args(*argv)

    def call_handle_args(self, *args):
        arg_names, var_arg_name, _, defaults = inspect.getargspec(self.handle_args)
        if len(args) + len(defaults) + 1 < len(arg_names):
            raise NotEnoughArguments('missing argument')
        if var_arg_name is None:
            if len(args) > len(arg_names):
                raise TooManyArguments('too many arguments')
        self.handle_args(*args)

    def handle_args(self, *args):
        raise NotImplementedError

    def display_help(self, fp, options=True):
        print >>fp, 'Usage: %s\n' % self.usage_template % dict(argv0=self._argv0, options='')
        if not options:
            return
        print >>fp, 'Options: '
        for option in sorted(option for option in self._options if self.show_all_options or not option.hidden):
            option_names = []
            for name in option.names:
                if option.n_args:
                    if name.startswith('--'):
                        name = '%s=%s' % (name, option.metavar.upper())
                    else:
                        name = '%s %s' % (name, option.metavar.upper())
                option_names.append(name)
            print >>fp, ' ', ', '.join(option_names)

    @option('-h', '--help')
    def opt_help(self):
        self.display_help(self.help_fp)
        sys.exit(self.help_exitcode)

    def display_version(self, fp):
        print >>fp, self.version_template % dict(argv0=self._argv0, version=self.version)

    @option('--version')
    def opt_version(self):
        self.display_version(self.help_fp)
        sys.exit(self.help_exitcode)

# vim:ts=4 sw=4 et
