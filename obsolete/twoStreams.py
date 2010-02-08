#-------------------------------------------------------------------------------
# Name:         twoStreams.py
# Purpose:      music21 classes for dealing with combining two streams
#
# Authors:      Michael Scott Cuthbert
#               Jackie Rogoff
#               Amy Hailes
#
# Copyright:    (c) 2009 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''
Much of this module might be better moved into Stream.  Nonetheless, it
will be useful for now to have this module while counterpoint and trecento
are being completely converted to the new system
'''

import unittest, doctest

import music21
from music21.stream import Stream

    
if __name__ == "__main__":
    music21.mainTest(Test)