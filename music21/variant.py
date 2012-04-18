# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         variant.py
# Purpose:      Translate MusicXML and music21 objects
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2012 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import unittest

import music21

from music21 import stream
from music21 import environment
_MOD = "variant.py" # TODO: call variant
environLocal = environment.Environment(_MOD)



# Variant as base class Variant, as a subclass
# try to use __getattr__ 
# __setattr__
# automatically defer all calls except flat, highest time


class Variant(music21.Music21Object):
    '''A Music21Object that stores elements like a Stream, but does not represent itself externally a a Stream

    >>> from music21 import variant
    >>> o = variant.Variant()
    '''
    # this copies the init of Streams
    def __init__(self, givenElements=None, *args, **keywords):
        music21.Music21Object.__init__(self)

        self.exposeTime = False

        self._stream = stream.Stream(givenElements=givenElements, 
                                    *args, **keywords)


    def append(self, others):
        self._stream.append(others)

    def insert(self, offsetOrItemOrList, itemOrNone=None, 
                     ignoreSort=False, setActiveSite=True):
        self._stream.insert(offsetOrItemOrList=offsetOrItemOrList, 
                    itemOrNone=itemOrNone, ignoreSort=ignoreSort, 
                    setActiveSite=setActiveSite)


    def _getHighestTime(self):
        if self.exposeTime:
            return self._stream.highestTime
        else:
            return 0.0

    highestTime = property(_getHighestTime, doc='''
        ''')


    def _getHighestOffset(self):
        if self.exposeTime:
            return self._stream.highestOffset
        else:
            return 0.0

    highestOffset = property(_getHighestOffset, doc='''
        ''')




# variant objs as groups
# ossia1 as a group
# variant group
# idea of m5, m7; each have two variants, each belonging to one group

# Stream.activateVariant() , take a group name as arg
# if None is given, take first
# overlapped content becomes
# inPlace: replaces original; original becomes a variant
# idea of performanceScale that realizes 

class Test(unittest.TestCase):

    def runTest(self):
        pass


    def testBasicA(self):
        from music21 import variant, stream, note

        o = variant.Variant()
        o.append(note.Note('G3', quarterLength=2.0))
        o.append(note.Note('f3', quarterLength=2.0))
        
        self.assertEqual(o.highestOffset, 0)
        self.assertEqual(o.highestTime, 0)

        o.exposeTime = True

        self.assertEqual(o.highestOffset, 2.0)
        self.assertEqual(o.highestTime, 4.0)


if __name__ == "__main__":
    music21.mainTest(Test)




