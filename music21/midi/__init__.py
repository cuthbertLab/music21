# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         midi/__init__.py
# Purpose:      Access to MIDI library
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2010-12 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

__all__ = ['translate', 'realtime']

from music21.midi.base import *

import base
__doc__ = base.__doc__

import realtime

#------------------------------------------------------------------------------
# eof

