# Copyright © 2012-2019 Jakub Wilk <jwilk@jwilk.net>
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

PYTHON = python

PREFIX = /usr/local
DESTDIR =

bindir = $(PREFIX)/bin
basedir = $(PREFIX)/share/didjvu

.PHONY: all
all: ;

python_exe = $(shell $(PYTHON) -c 'import sys; print(sys.executable)')

.PHONY: install
install: didjvu
	$(PYTHON) - < lib/__init__.py  # Python version check
	install -d $(DESTDIR)$(bindir)
	sed \
		-e "1 s@^#!.*@#!$(python_exe)@" \
		-e "s#^basedir = .*#basedir = '$(basedir)/'#" \
		$(<) > $(<).tmp
	install $(<).tmp $(DESTDIR)$(bindir)/$(<)
	rm $(<).tmp
	install -d $(DESTDIR)$(basedir)/lib/xmp
	install -p -m644 lib/xmp/*.py $(DESTDIR)$(basedir)/lib/xmp/
	install -p -m644 lib/*.py $(DESTDIR)$(basedir)/lib/
ifeq "$(DESTDIR)" ""
	umask 022 && $(PYTHON) -m compileall -q $(basedir)/lib/
endif
ifeq "$(wildcard doc/*.1)" ""
	# run "$(MAKE) -C doc" to build the manpage
else
	install -d $(DESTDIR)$(PREFIX)/share/man/man1
	install -m644 doc/$(<).1 $(DESTDIR)$(PREFIX)/share/man/man1/
endif

.PHONY: test
test: didjvu
	$(PYTHON) $(<) --test --verbose tests/

.PHONY: test-installed
test-installed: $(or $(shell command -v didjvu;),$(bindir)/didjvu)
	didjvu --test --verbose tests/

.PHONY: clean
clean:
	find . -type f -name '*.py[co]' -delete
	find . -type d -name '__pycache__' -delete
	rm -f .coverage
	rm -f *.tmp

.error = GNU make is required

# vim:ts=4 sts=4 sw=4 noet
