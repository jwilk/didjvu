# encoding=UTF-8

'''
Helper module that allows to use command-line tools without installing them.
'''

import sys
import lib

sys.modules['didjvu'] = lib

# vim:ts=4 sw=4 et
