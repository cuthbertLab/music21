# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         exceptions21.py
# Purpose:      music21 Exceptions (called out to not require import music21 to access)
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright ©2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
#-------------------------------------------------------------------------------

class Music21Exception(Exception):
    pass

# should be renamed:
class DefinedContextsException(Music21Exception):
    pass

class Music21ObjectException(Music21Exception):
    pass

class ElementException(Music21Exception):
    pass

class GroupException(Music21Exception):
    pass
