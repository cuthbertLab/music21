#-*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         common.py
# Purpose:      Basic Utilties
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Common is a collection of utility functions, objects, constants and dictionaries used 
throughout music21.

functions in common/ can import from music21.defaults, music21.exceptions21, and music21.ext
and that is all (except in tests and doctests).

For historical reasons all the (non-private) functions etc. of the common/
folder are available by importing common. 

split according to function -- September 2015
'''

__all__ = ['classTools', 'decorators', 'fileTools', 'formats', 'misc',
           'numberTools', 'objects', ]

from music21 import defaults
from music21 import exceptions21
from music21.ext import six

# pylint: disable=wildcard-import
from music21.common.classTools import * #including isNum, isListLike 
from music21.common.decorators import * # gives the deprecated decorator
from music21.common.fileTools import * # file tools.
from music21.common.formats import * # most are deprecated!
from music21.common.misc import * # most are deprecated!
from music21.common.numberTools import * #including opFrac
from music21.common.objects import *
from music21.common.pathTools import *
from music21.common.parallel import * 
from music21.common.stringTools import * 
from music21.common.weakrefTools import * # including wrapWeakref


#### This is used in FreezeThaw and elsewhere as
#### a standard way to get cPickle w/ fallback. Do not remove.
if six.PY2:
    try:
        import cPickle as pickleMod # much faster on Python 2
    except ImportError:
        import pickle as pickleMod # @UnusedImport
else:
    import pickle as pickleMod # @Reimport
    # on python 3 -- do NOT import _pickle directly. it will be used if 
    #     it exists, and _pickle lacks HIGHEST_PROTOCOL constant.
DEBUG_OFF = 0
DEBUG_USER = 1
DEBUG_DEVEL = 63
DEBUG_ALL = 255

#-------------------------------------------------------------------------------
# define presented order in documentation

#------------------------------------------------------------------------------
# eof

