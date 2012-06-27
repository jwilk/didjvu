# encoding=UTF-8

'''
helper module that allows using the command-line tool without installing it
'''

import sys
import lib

sys.modules['didjvu'] = lib

# vim:ts=4 sw=4 et
