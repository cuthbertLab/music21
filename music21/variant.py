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



    def __getattr__(self, attr):
        '''This will call all already-defined 
        '''
        environLocal.pd(['relaying unmatched attribute request to private Stream'])
        try:
            return getattr(self._stream, attr)
        except:
            raise
        

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


    def show(self, fmt=None, app=None):
        '''Must override manually, otherwise Music21Object.show() is called.
        '''
        self._stream.show(fmt=fmt, app=app)


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


    def testBasicB(self):
        '''Testing relaying attributes requests to private Stream with __getattr__
        '''
        from music21 import variant, stream, note

        v = variant.Variant()
        v.append(note.Note('G3', quarterLength=2.0))
        v.append(note.Note('f3', quarterLength=2.0))
        # these are Stream attributes
        self.assertEqual(v.highestOffset, 0.0)
        self.assertEqual(v.highestTime, 0.0)

        self.assertEqual(len(v.notes), 2)
        self.assertEqual(len(v.pitches), 2)
        self.assertEqual(v.hasElementOfClass('Note'), True)
        v.pop(1) # remove the last tiem

        self.assertEqual(v.highestOffset, 0.0)
        self.assertEqual(v.highestTime, 0.0)
        self.assertEqual(len(v.notes), 1)
        self.assertEqual(len(v.pitches), 1)

        v.show('t')


if __name__ == "__main__":
    music21.mainTest(Test)




