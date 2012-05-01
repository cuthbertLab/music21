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

'''The :class:`~music21.variant.Variant` and its subclasses.
'''


# variant objs as groups
# ossia1 as a group
# variant group
# idea of m5, m7; each have two variants, each belonging to one group

# Stream.activateVariant() , take a group name as arg
# if None is given, take first
# overlapped content becomes
# inPlace: replaces original; original becomes a variant
# idea of performanceScale that realizes 



class Variant(music21.Music21Object):
    '''A Music21Object that stores elements like a Stream, but does not represent itself externally a a Stream

    >>> from music21 import *
    >>> v = variant.Variant()
    >>> v.repeatAppend(note.Note(), 8)
    >>> len(v.notes)
    8
    >>> v.highestTime
    0.0
    >>> v.duration # handled by Music21Object
    <music21.duration.Duration 0.0>
    >>> v.isStream
    False

    >>> s = stream.Stream()
    >>> s.append(v)
    >>> s.append(note.Note())
    >>> s.highestTime
    1.0
    >>> s.show('t')
    {0.0} <music21.variant.Variant object at ...>
    {0.0} <music21.note.Note C>
    >>> s.flat.show('t')
    {0.0} <music21.variant.Variant object at ...>
    {0.0} <music21.note.Note C>
    '''

    classSortOrder = 0  # variants should always come first?


    # this copies the init of Streams
    def __init__(self, givenElements=None, *args, **keywords):
        music21.Music21Object.__init__(self)

        self.exposeTime = False
        self._stream = stream.Stream(givenElements=givenElements, 
                                    *args, **keywords)

# TODO
#     def __deepcopy__

    def __getattr__(self, attr):
        '''This defers all calls not defined in this Class to calls on the privately contained Stream.
        '''
        #environLocal.pd(['relaying unmatched attribute request to private Stream'])

        # must mask pitches so as not to recurse
        # TODO: check tt recurse does not go into this
        if attr in ['flat', 'pitches']: 
            raise AttributeError
        try:
            return getattr(self._stream, attr)
        except:
            raise
        

#     def append(self, others):
#         self._stream.append(others)
# 
#     def insert(self, offsetOrItemOrList, itemOrNone=None, 
#                      ignoreSort=False, setActiveSite=True):
#         '''This method delegates calls to the Stream.insert() method for the private Stream contained within this Variant.
#         '''
#         self._stream.insert(offsetOrItemOrList=offsetOrItemOrList, 
#                     itemOrNone=itemOrNone, ignoreSort=ignoreSort, 
#                     setActiveSite=setActiveSite)


    #---------------------------------------------------------------------------
    # Stream  simulation/overrides

    def _getHighestTime(self):
        if self.exposeTime:
            return self._stream.highestTime
        else:
            return 0.0

    highestTime = property(_getHighestTime, doc='''
        This property masks calls to Stream.highestTime. Assuming `exposeTime` is False, this always returns zero, making the Variant always take zero time. 

        >>> from music21 import *
        >>> v = variant.Variant()
        >>> v.append(note.Note(quarterLength=4))
        >>> v.highestTime
        0.0

        ''')

    def _getHighestOffset(self):
        if self.exposeTime:
            return self._stream.highestOffset
        else:
            return 0.0

    highestOffset = property(_getHighestOffset, doc='''
        This property masks calls to Stream.highestOffset. Assuming `exposeTime` is False, this always returns zero, making the Variant always take zero time. 

        >>> from music21 import *
        >>> v = variant.Variant()
        >>> v.append(note.Note(quarterLength=4))
        >>> v.highestOffset
        0.0

        ''')

    def show(self, fmt=None, app=None):
        '''
        Call show() on the Stream contained by this Variant. 

        This method must be overridden, otherwise Music21Object.show() is called.

        >>> from music21 import *
        >>> v = variant.Variant()
        >>> v.repeatAppend(note.Note(quarterLength=.25), 8)
        >>> v.show('t')
        {0.0} <music21.note.Note C>
        {0.25} <music21.note.Note C>
        {0.5} <music21.note.Note C>
        {0.75} <music21.note.Note C>
        {1.0} <music21.note.Note C>
        {1.25} <music21.note.Note C>
        {1.5} <music21.note.Note C>
        {1.75} <music21.note.Note C>
        '''
        self._stream.show(fmt=fmt, app=app)



    #---------------------------------------------------------------------------
    # particular to this class

    def _getContainedHighestTime(self):
        return self._stream.highestTime

    containedHighestTime = property(_getContainedHighestTime, doc='''
        This property calls the contained Stream.highestTime.

        >>> from music21 import *
        >>> v = variant.Variant()
        >>> v.append(note.Note(quarterLength=4))
        >>> v.containedHighestTime
        4.0
        ''')

    def _getContainedHighestOffset(self):
        return self._stream.highestOffset

    containedHighestOffset = property(_getContainedHighestOffset, doc='''
        This property calls the contained Stream.highestOffset.

        >>> from music21 import *
        >>> v = variant.Variant()
        >>> v.append(note.Note(quarterLength=4))
        >>> v.append(note.Note())
        >>> v.containedHighestOffset
        4.0

        ''')

    def _getContainedSite(self):
        return self._stream

    containedSite = property(_getContainedSite, doc='''
        Return a reference to the Stream contained in this Variant.
        ''')



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
        self.assertEqual(v.hasElementOfClass('Note'), True)
        v.pop(1) # remove the last tiem

        self.assertEqual(v.highestOffset, 0.0)
        self.assertEqual(v.highestTime, 0.0)
        self.assertEqual(len(v.notes), 1)

        #v.show('t')

    def testVariantGroupA(self):
        '''Variant groups are used to distinguish
        '''
        from music21 import variant
        v1 = variant.Variant()
        v1.groups.append('alt-a')

        v1 = variant.Variant()
        v1.groups.append('alt-b')
        self.assertEqual('alt-b' in v1.groups, True)


    def testVariantClassA(self):
        from music21 import stream, variant, note

        m1 = stream.Measure()
        v1 = variant.Variant()
        v1.append(m1)

        self.assertEqual(v1.isClassOrSubclass(['Variant']), True)

        self.assertEqual(v1.hasElementOfClass('Variant'), False)
        self.assertEqual(v1.hasElementOfClass('Measure'), True)

if __name__ == "__main__":
    music21.mainTest(Test)




