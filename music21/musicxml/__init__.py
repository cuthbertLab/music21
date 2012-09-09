# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         musicxml/__init__.py
# Purpose:      Access to musicxml library
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
#-------------------------------------------------------------------------------

_all_ = ['base', 'm21ToString', 'toMxObjects', 'fromMxObjects']

from music21.musicxml.base import *

import m21ToString
import toMxObjects
import fromMxObjects
#------------------------------------------------------------------------------
# eof

