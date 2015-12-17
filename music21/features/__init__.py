# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         features/__init__.py
# Purpose:      Feature extractors
#
# Authors:      Christopher Ariza
#
# Copyright:    Copyright © 2011 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
# __init__ can wildcard import base; it's how it is designed.
from music21.features.base import * # pylint: disable=wildcard-import

from music21.features import base

from music21.features import jSymbolic
from music21.features import native

# pylint: disable=redefined-builtin
__doc__ = base.__doc__ #@ReservedAssignment @UndefinedVariable

#------------------------------------------------------------------------------
# eof




