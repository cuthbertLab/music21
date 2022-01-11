# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         segmentByRests.py
# Purpose:      Break up a part into its contiguous melodies.
#
# Authors:      Mark Gotham
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2018 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------

import unittest

from music21 import clef
from music21 import converter
from music21 import exceptions21
from music21 import note
from music21 import interval


from music21 import environment
_MOD = 'analysis.segmentByRests'
environLocal = environment.Environment(_MOD)

# ------------------------------------------------------------------------------

class SegmentationException(exceptions21.Music21Exception):
    pass

class Segmenter:
    '''
    Given a work or part, returns a list of melodic segments or intervals.
    '''
    @classmethod
    def getSegmentsList(cls,
                        workOrPart,
                        removeEmptyLists=True):
        # noinspection PyShadowingNames
        '''
        Segments a part by its rests (and clefs) and returns a returns a list of lists where
        each sublist is one segment of contiguous notes. NB Uses .recurse() internally.

        >>> example = converter.parse("tinyNotation: C4 r D E r r F r G r A B r c")
        >>> segments = analysis.segmentByRests.Segmenter.getSegmentsList(example)
        >>> segments
        [[<music21.note.Note C>],
         [<music21.note.Note D>, <music21.note.Note E>],
         [<music21.note.Note F>],
         [<music21.note.Note G>],
         [<music21.note.Note A>, <music21.note.Note B>],
         [<music21.note.Note C>]]
        '''
        segments = []
        thisSegment = []
        partNotes = workOrPart.recurse().getElementsByClass(['Note', 'Rest', 'Clef'])
        for i in range(len(partNotes)):
            n = partNotes[i]
            if isinstance(n, note.Note):
                thisSegment.append(n)
                # for final segment as workOrPart usually ends with a note not clef or rest
                if i == len(partNotes) - 1:
                    segments.append(thisSegment)
            if isinstance(n, (note.Rest, clef.Clef)):
                segments.append(thisSegment)
                thisSegment = []
                continue

        # Optionally: Remove the empty sublists given by rests
        if removeEmptyLists:
            for segment in segments[::-1]:
                if not segment:
                    segments.remove(segment)
        return segments

    @classmethod
    def getIntervalList(cls, workOrPart):
        '''
        Given a work or part, returns a list of intervals between contiguous notes.
        NB Uses .recurse() internally so
        if called on a work then returns a list of lists with one list per part.

        >>> example = converter.parse("tinyNotation: 4/4 E4 r F G A r g c r c")
        >>> intList = analysis.segmentByRests.Segmenter.getIntervalList(example)
        >>> [x.name for x in intList]
        ['M2', 'M2', 'P5']
        '''
        intervalList = []
        elementList = workOrPart.recurse().getElementsByClass(['Note', 'Rest', 'Clef'])
        for i in range(len(elementList) - 1):
            n1 = elementList[i]
            if isinstance(n1, (note.Rest, clef.Clef)):
                continue
            n2 = elementList[i + 1]
            if isinstance(n2, (note.Rest, clef.Clef)):
                continue
            intervalObj = interval.Interval(n1, n2)
            intervalList.append(intervalObj)
        return intervalList

# ------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def testGetSegmentsList(self):
        ex = converter.parse("tinyNotation: E4 r F G A r g c r c")
        segments = Segmenter.getSegmentsList(ex)

        self.assertIsInstance(segments[0], list)
        self.assertEqual(segments[1][0].name, 'F')

    def testGetIntervalList(self):
        ex = converter.parse("tinyNotation: E4 r F G A r g c r c")
        intervalList = Segmenter.getIntervalList(ex)

        self.assertEqual(intervalList[0].name, 'M2')
        self.assertIsInstance(intervalList, list)


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
