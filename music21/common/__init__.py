# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         common.py
# Purpose:      Basic Utilities
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2015 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Common is a collection of utility functions, objects, constants and dictionaries used
throughout music21.

functions in common/ can import from music21.defaults, music21.exceptions21, and music21.ext
and that is all (except in tests and doctests).

For historical reasons all the (non-private) functions etc. of the common/
folder are available by importing common.

split according to function -- September 2015
'''

__all__ = [
    'classTools',
    'decorators',
    'fileTools',
    'formats',
    'misc',
    'numberTools',
    'objects',
]

from music21 import defaults
from music21 import exceptions21
# pylint: disable=wildcard-import
from music21.common.classTools import *  # including isNum, isListLike
from music21.common.decorators import *  # gives the deprecated decorator
from music21.common.fileTools import *  # file tools.
from music21.common.formats import *  # most are deprecated!
from music21.common.misc import *  # most are deprecated!
from music21.common.numberTools import *  # including opFrac
from music21.common.objects import *
from music21.common.pathTools import *
from music21.common.parallel import *
from music21.common.stringTools import *
from music21.common.weakrefTools import *  # including wrapWeakref


DEBUG_OFF = 0
DEBUG_USER = 1
DEBUG_DEVEL = 63
DEBUG_ALL = 255

