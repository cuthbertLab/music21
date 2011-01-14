# -*- coding: utf-8 -*-
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
import music21.common


from music21 import environment
_MOD = "tempo.py"
environLocal = environment.Environment(_MOD)


# all lowercase, even german
defaultTempoValues = {
     'molto adagio': 40,
     'adagio': 52,
     'slow': 52,
     'langsam': 52,
     'andante': 72,
     'moderato': 90,
     'moderate': 90,
     'allegretto': 108,
     'allegro': 132,
     'fast': 132,
     'schnell': 132,
     'molto allegro': 144,
     u'très vite': 144,
     'presto': 168,
     'prestissimo': 200
     }

class TempoMark(music21.Music21Object):
    '''
    >>> import music21
    >>> tm = music21.tempo.TempoMark("adagio")
    >>> tm.value
    'adagio'
    

    Common marks such as "adagio," "moderato," "molto allegro," etc.
    get sensible default values.  If not found, uses a default of 90:


    >>> tm.number
    52
    >>> tm2 = music21.tempo.TempoMark(u"très vite")
    >>> tm2.value.endswith('vite')
    True
    >>> tm2.value == u'très vite'   # TODO: Make sure is working again....
    True
    >>> tm3 = music21.tempo.TempoMark("extremely, wicked fast!")
    >>> tm3.number
    90
    
    '''
    
    classSortOrder = 1
    number = 90
    _DOC_ALL_INHERITED = False

    def __init__(self, value = None):
        music21.Music21Object.__init__(self)
        if music21.common.isNum(value):
            self.value = str(value)
            self.number = value
        else:
            self.value = value
            if value is None:
                pass
            elif value.lower() in defaultTempoValues.keys():
                self.number = defaultTempoValues[value.lower()]
            elif value in defaultTempoValues.keys():
                self.number = defaultTempoValues[value]
            else:
                pass
                #print 'cannot match value', value
                #environLocal.printDebug(['cannot match', value.decode('utf-8')])    
    
    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.value)



class MetronomeMark(TempoMark):
    '''
    A way of specifying only a particular tempo and referent and (optionally) a text description
    
    >>> from music21 import *
    >>> a = tempo.MetronomeMark(40, note.HalfNote(), "slow")
    >>> a.number
    40
    >>> a.referent
    <music21.duration.Duration 2.0>
    >>> a.referent.type
    'half'
    >>> a.value
    'slow'
    '''
    def __init__(self, number = 60, referent = None, value = None):
        if value is not None:
            TempoMark.__init__(self, value)
        else:
            TempoMark.__init__(self, number)

        self.number = number
        if referent is not None and 'Duration' not in referent.classes:
            self.referent = referent.duration
        else:
            self.referent = referent # should be a music21.duration.Duration object or a Music21Object with a duration or None
    
    def __repr__(self):
        return "<music21.tempo.MetronomeMark %s>" % str(self.number)

def interpolateElements(element1, element2, sourceStream, 
    destinationStream, autoAdd = True):
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
    
    
    Suppose eA, eB, and eC are three quarter notes that lie
    between element1 and element2 in sourceStream
    and destinationStream, as in:
    
    
    >>> eA = note.QuarterNote("D4")
    >>> eB = note.QuarterNote("E4")
    >>> eC = note.QuarterNote("F4")
    >>> sourceStream.insert(11, eA)
    >>> sourceStream.insert(12, eB)
    >>> sourceStream.insert(13, eC)
    >>> destinationStream.append([eA, eB, eC])  # not needed if autoAdd were true
    
    
    
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
        

    def testUnicdoe(self):

        from music21 import tempo
        # test with no arguments
        tm = music21.tempo.TempoMark()

        tm = music21.tempo.TempoMark("adagio")

        self.assertEqual(tm.number, 52)
        tm2 = music21.tempo.TempoMark(u"très vite")

        self.assertEqual(tm2.value, u'très vite')
        self.assertEqual(tm2.number, 144)

        

#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [TempoMark, MetronomeMark, interpolateElements]


if __name__ == "__main__":

    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof


