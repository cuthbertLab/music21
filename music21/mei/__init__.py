# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         mei/__init__.py
# Purpose:      Initialize the MEI module
#
# Authors:      Christopher Antila
#
# Copyright:    Copyright © 2014 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------
'''
This is the documentation for the "mei" module.

I'm going to write it soon, I promise.
'''

# NOTE: in the end, I'll only want to import things that will be accessible under the
#       music21.mei.* namespace. This should be almost nothing---only the things used by the
#       SubConverter. Everything else should be imported through its submodule, like
#       "music21.mei.functions.*" or whatever.
from music21.mei.base import MeiToM21Converter
