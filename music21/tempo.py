#-------------------------------------------------------------------------------
# Name:         tempo.py
# Purpose:      Classes and tools relating to tempo
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009-10 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''This module defines objects for describing tempo and changes in tempo.
'''

import unittest, doctest

import music21
import music21.note

_MOD = "tempo.py"


class TempoMark(music21.Music21Object):
    '''
    >>> tm = TempoMark("adagio")
    >>> tm.value
    'adagio'
    '''
    
    classSortOrder = 1
    
    def __init__(self, value = None):
        music21.Music21Object.__init__(self)
        self.value = value
    
    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.value)



class MetronomeMark(TempoMark):
    '''
    >>> a = MetronomeMark(40)
    >>> a.number
    40
    '''
    def __init__(self, number = 60, referent = None):
        TempoMark.__init__(self, number)

        self.number = number
        self.referent = referent # should be a music21.note.Duration object
    
    def __repr__(self):
        return "<music21.tempo.MetronomeMark %s>" % str(self.number)

def interpolateElements(element1, element2, sourceStream, destinationStream, autoAdd = True):
    '''
    
    Assume that element1 and element2 are two elements in sourceStream 
    and destinationStream with other elements (say eA, eB, eC) between 
    them.  For instance, element1 could be the downbeat at offset 10
    in sourceStream (a Stream representing a score) and offset 20.5 
    in destinationStream (which might be a Stream representing the 
    timing of notes in particular recording at approximately but not 
    exactly qtr = 30). Element2 could be the following downbeat in 4/4, 
    at offset 14 in source but offset 25.0 in the recording:
    
    >>> from music21 import *
    >>> sourceStream = stream.Stream()
    >>> destinationStream = stream.Stream()
    >>> element1 = note.QuarterNote("C4")
    >>> element2 = note.QuarterNote("G4")
    >>> sourceStream.insert(10, element1)
    >>> destinationStream.insert(20.5, element1)
    >>> sourceStream.insert(14, element2)
    >>> destinationStream.insert(25.0, element2)
    
    
    If eA, eB, and eC are three quarter notes 
    between element1 and element2 in sourceStream
    and destinationStream:
    
    
    >>> eA = note.QuarterNote("D4")
    >>> eB = note.QuarterNote("E4")
    >>> eC = note.QuarterNote("F4")
    >>> sourceStream.insert(11, eA)
    >>> sourceStream.insert(12, eB)
    >>> sourceStream.insert(13, eC)
    >>> destinationStream.append([eA, eB, eC])  # not needed with autoAdd
    
    
    
    then running this function will cause eA, eB, and eC
    to have offsets 21.625, 22.75, and 23.875 respectively
    in destinationStream:
    
    
    
    >>> tempo.interpolateElements(element1, element2, sourceStream, destinationStream, autoAdd = False)
    >>> for el in [eA, eB, eC]:
    ...    print el.getOffsetBySite(destinationStream)
    21.625
    22.75
    23.875
    
    
    if the elements between element1 and element2 do not yet
    appear in destinationStream, they are automatically added
    unless autoAdd is False.
        
    
    (with the default autoAdd, elements are automatically added to new streams):
    
    
    >>> destStream2 = stream.Stream()
    >>> destStream2.insert(10.1, element1)
    >>> destStream2.insert(50.5, element2)
    >>> tempo.interpolateElements(element1, element2, sourceStream, destStream2)
    >>> for el in [eA, eB, eC]:
    ...    print el.getOffsetBySite(destStream2)
    20.2
    30.3
    40.4


    (unless autoAdd is set to false, in which case a Tempo Exception arises...)


    >>> destStream3 = stream.Stream()
    >>> destStream3.insert(100, element1)
    >>> destStream3.insert(500, element2)
    >>> tempo.interpolateElements(element1, element2, sourceStream, destStream3, autoAdd = False)
    Traceback (most recent call last):
    ...
    TempoException: Could not find element <music21.note.Note D> with id ...

    '''
    try:
        startOffsetSrc = element1.getOffsetBySite(sourceStream)
    except StreamException:
        raise TempoException("could not find element1 in sourceStream")
    try:
        startOffsetDest = element1.getOffsetBySite(destinationStream)
    except StreamException:
        raise TempoException("could not find element1 in destinationStream")
    
    try:
        endOffsetSrc = element2.getOffsetBySite(sourceStream)
    except StreamException:
        raise TempoException("could not find element2 in sourceStream")
    try:
        endOffsetDest = element2.getOffsetBySite(destinationStream)
    except StreamException:
        raise TempoException("could not find element2 in destinationStream")
    
    scaleAmount = ((endOffsetDest - startOffsetDest + 0.0)/(endOffsetSrc - startOffsetSrc + 0.0))
    
    interpolatedElements = sourceStream.getElementsByOffset(offsetStart = startOffsetSrc, offsetEnd = endOffsetSrc)
    
    for el in interpolatedElements:
        elOffsetSrc = el.getOffsetBySite(sourceStream)
        try:
            el.getOffsetBySite(destinationStream)
        except music21.DefinedContextsException:
            if autoAdd is True:
                destinationOffset = (scaleAmount * (elOffsetSrc - startOffsetSrc)) + startOffsetDest
                destinationStream.insert(destinationOffset, el)
            else:
                raise TempoException("Could not find element %s with id %d in destinationStream and autoAdd is false" % (repr(el), el.id))
        else:
            destinationOffset = (scaleAmount * (elOffsetSrc - startOffsetSrc)) + startOffsetDest
            el.setOffsetBySite(destinationStream, destinationOffset)
                
    

class TempoException(Exception):
    pass

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    def runTest(self):
        pass

    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
        '''
        import sys, types, copy
        for part in sys.modules[self.__module__].__dict__.keys():
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            obj = getattr(sys.modules[self.__module__], part)
            if callable(obj) and not isinstance(obj, types.FunctionType):
                a = copy.copy(obj)
                b = copy.deepcopy(obj)


    def setupTest(self):
        MM1 = MetronomeMark(60, music21.note.QuarterNote() )
        self.assertEqual(MM1.number, 60)

        TM1 = TempoMark("Lebhaft")
        self.assertEqual(TM1.value, "Lebhaft")
        


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [TempoMark, MetronomeMark, interpolateElements]


if __name__ == "__main__":
    music21.mainTest(Test)