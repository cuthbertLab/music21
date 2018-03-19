# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         segmentByRests.py
# Purpose:      Break up a part into its contiguous melodies.
#
# Authors:      Mark Gotham
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2017 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

import unittest

from music21 import common
from music21 import exceptions21
from music21 import pitch
from music21 import interval
from music21 import stream
from music21 import converter

from music21 import environment
_MOD = 'analysis.segmentByRests'
environLocal = environment.Environment(_MOD)

#-------------------------------------------------------------------------------

class SegmentationException(exceptions21.Music21Exception):
    pass

class Segmenter:
    '''
    Given a work or part, returns a list of melodic segments or intervals.
    '''
    def __init__(self, inputStream):
        self.inputStream = inputStream

    def getSegmentsList(workOrPart):
        '''
        Segments a part by its rests (and clefs) and returns a returns a list of lists where
        each sublist is one segment of contiguous notes.

        >>> testStream = converter.parse("tinyNotation: E4 r F G A r g c r c")
        >>> segments = analysis.segmentByRests.Segmenter.getSegmentsList(testStream)
        >>> segments
        [[], [<music21.note.Note E>],
        [<music21.note.Note F>, <music21.note.Note G>, <music21.note.Note A>],
        [<music21.note.Note G>, <music21.note.Note C>]]
        '''
        segments = []
        thisSegment = []
        elementList = workOrPart.recurse().getElementsByClass(['Note', 'Rest', 'Clef'])
        for i in range(len(elementList)-1):
            n = elementList[i]
            if 'Note' in n.classes:
                thisSegment.append(n)
            elif 'Rest' in n.classes or 'Clef' in n.classes:
                segments.append(thisSegment)
                thisSegment = []
                continue
        return segments

    def getIntervalList(workOrPart, printUnusual=False):
        '''
        Given a work or part, returns a list of intervals between contiguous notes.

        >>> testStream = converter.parse("tinyNotation: 4/4 E4 r F G A r g c r c")
        >>> intList = analysis.segmentByRests.Segmenter.getIntervalList(testStream)
        >>> [x.name for x in intList]
        ['M2', 'M2', 'P5']
        '''
        intervalList = []
        elementList = workOrPart.recurse().getElementsByClass(['Note', 'Rest', 'Clef'])
        for i in range(len(elementList)-1):
            n1 = elementList[i]
            if 'Rest' in n1.classes or 'Clef' in n1.classes:
                continue
            n2 = elementList[i + 1]
            if 'Rest' in n2.classes or 'Clef' in n2.classes:
                continue
            intervalObj = interval.Interval(n1, n2)
            semis = intervalObj.semitones
            if printUnusual and (abs(semis) > 12 or
                                 abs(semis) == 6 or
                                 abs(semis) == 10 or
                                 abs(semis) == 11):
                 print('************************')
                 print('Interval (semitones):', semis)
                 print('Note 1:', n1)
                 print('Measure Number:', n1.measureNumber)
                 print('Part:', n1.getContextByClass('Part'))
                 print('File Path:', list(n1.contextSites())[-1].site.filePath)
            intervalList.append(intervalObj)
        return intervalList

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def testGetSegmentsList(self):
        testStream = converter.parse("tinyNotation: E4 r F G A r g c r c")
        segments = Segmenter.getSegmentsList(testStream)

        self.assertIsInstance(segments[0], list)
        self.assertEqual(segments[1][0].name, 'E')

    def testGetIntervalList(self):
        testStream = converter.parse("tinyNotation: E4 r F G A r g c r c")
        intervalList = Segmenter.getIntervalList(testStream)

        self.assertEqual(intervalList[0].name,'M2')
        self.assertIsInstance(intervalList, list)

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import music21
    music21.mainTest(Test)
