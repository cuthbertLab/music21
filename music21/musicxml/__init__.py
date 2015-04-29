# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         musicxml/__init__.py
# Purpose:      Access to musicxml library
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

_all_ = ['mxObjects', 'm21ToString', 'toMxObjects', 'fromMxObjects', 'xmlHandler']

import sys
from music21.musicxml import mxObjects
from music21.musicxml import m21ToString
from music21.musicxml import toMxObjects
from music21.musicxml import fromMxObjects
from music21.musicxml import xmlHandler
#------------------------------------------------------------------------------
# eof

