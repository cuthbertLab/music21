# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         transposition.py
# Purpose:      Tools for checking distinct transposition
#
# Authors:      Mark Gotham
#
# Copyright:    Copyright © 2017 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------

import unittest

from music21 import common
from music21 import exceptions21
from music21 import pitch
from music21 import chord

from music21 import environment
_MOD = 'analysis.transposition'
environLocal = environment.Environment(_MOD)


class TranspositionException(exceptions21.Music21Exception):
    pass


class TranspositionChecker:
    '''
    Given a list of pitches, checks for the number of distinct transpositions.

    >>> pList = [pitch.Pitch('C4'), pitch.Pitch('E4'), pitch.Pitch('G#4')]
    >>> tc = analysis.transposition.TranspositionChecker(pList)
    >>> tc.numDistinctTranspositions()
    4
    >>> allNormalOrderPitchTuples = tc.getPitchesOfDistinctTranspositions()
    >>> allNormalOrderPitchTuples
    [(<music21.pitch.Pitch C>, <music21.pitch.Pitch E>,
                                         <music21.pitch.Pitch G#>),
     (<music21.pitch.Pitch C#>, <music21.pitch.Pitch F>,
                                         <music21.pitch.Pitch A>),
     (<music21.pitch.Pitch D>, <music21.pitch.Pitch F#>,
                                         <music21.pitch.Pitch A#>),
     (<music21.pitch.Pitch E->, <music21.pitch.Pitch G>,
                                         <music21.pitch.Pitch B>)]
    >>> myChord = chord.Chord(['C', 'E-', 'F#', 'A'])
    >>> pList = myChord.pitches
    >>> tc = analysis.transposition.TranspositionChecker(pList)
    >>> allNormalOrderChords = tc.getChordsOfDistinctTranspositions()
    >>> allNormalOrderChords
    [<music21.chord.Chord C E- F# A>,
     <music21.chord.Chord C# E G A#>,
     <music21.chord.Chord D F G# B>]
    '''
    def __init__(self, pitches=None):
        if pitches is None:
            raise TranspositionException('Must have some input')
        if not common.isIterable(pitches):
            raise TranspositionException('Must be a list or tuple')
        if not pitches:
            raise TranspositionException(
                'Must have at least one element in list'
            )
        # p0 = pitches[0]
        # if not isinstance(p0, pitch.Pitch):
        #     raise TranspositionException('List must have pitch objects')
        self.pitches = pitches
        self.allTranspositions = None
        self.allNormalOrders = None
        self.distinctNormalOrders = None

    def getTranspositions(self):
        '''
        Gets all 12 transpositions (distinct or otherwise)

        >>> p = [pitch.Pitch('D#')]
        >>> tc = analysis.transposition.TranspositionChecker(p)
        >>> tc.getTranspositions()
        [[<music21.pitch.Pitch E->],
        [<music21.pitch.Pitch E>],
        [<music21.pitch.Pitch F>],
        [<music21.pitch.Pitch F#>],
        [<music21.pitch.Pitch G>],
        [<music21.pitch.Pitch G#>],
        [<music21.pitch.Pitch A>],
        [<music21.pitch.Pitch B->],
        [<music21.pitch.Pitch B>],
        [<music21.pitch.Pitch C>],
        [<music21.pitch.Pitch C#>],
        [<music21.pitch.Pitch D>]]
        '''
        allTranspositions = []
        for i in range(12):
            thisTransposition = []
            for p in self.pitches:
                thisTransposition.append(p.transpose(i))
            allTranspositions.append(thisTransposition)
        self.allTranspositions = allTranspositions
        return allTranspositions

    def listNormalOrders(self):
        '''
        List the normal orders for all 12 transpositions

        >>> pList = [pitch.Pitch('C4'), pitch.Pitch('E4'), pitch.Pitch('G#4')]
        >>> tc = analysis.transposition.TranspositionChecker(pList)
        >>> tc.listNormalOrders()
        [[0, 4, 8], [1, 5, 9], [2, 6, 10], [3, 7, 11],
         [0, 4, 8], [1, 5, 9], [2, 6, 10], [3, 7, 11],
         [0, 4, 8], [1, 5, 9], [2, 6, 10], [3, 7, 11]]
        '''
        if self.allTranspositions is None:
            self.getTranspositions()
        allTranspositions = self.allTranspositions
        allNormalOrders = []
        for thisTransposition in allTranspositions:
            # pass
            c = chord.Chord(thisTransposition)
            thisNormalOrder = c.normalOrder
            allNormalOrders.append(thisNormalOrder)
        self.allNormalOrders = allNormalOrders
        return allNormalOrders

    def listDistinctNormalOrders(self):
        '''
        List the distinct normal orders (without duplication).

        >>> pList = [pitch.Pitch('C4'), pitch.Pitch('E4'), pitch.Pitch('G#4')]
        >>> tc = analysis.transposition.TranspositionChecker(pList)
        >>> tc.listDistinctNormalOrders()
        [[0, 4, 8], [1, 5, 9], [2, 6, 10], [3, 7, 11]]
        '''
        if self.allNormalOrders is None:
            self.listNormalOrders()
        allNormalOrders = self.allNormalOrders
        seen = set()
        distinctNormalOrders = [x for x in allNormalOrders
                                if not (tuple(x) in seen or seen.add(tuple(x)))]
        self.distinctNormalOrders = distinctNormalOrders
        return distinctNormalOrders

    def numDistinctTranspositions(self):
        '''
        Gives the number of distinct transpositions (normal orders).

        >>> pList = [pitch.Pitch('C4'), pitch.Pitch('E4'), pitch.Pitch('G#4')]
        >>> tc = analysis.transposition.TranspositionChecker(pList)
        >>> tc.numDistinctTranspositions()
        4
        '''
        if self.distinctNormalOrders is None:
            self.listDistinctNormalOrders()
        return len(self.distinctNormalOrders)

    def getChordsOfDistinctTranspositions(self):
        '''
        Outputs chords for each distinct transposition (normal order).

        >>> pList = [pitch.Pitch('C4'), pitch.Pitch('E4'), pitch.Pitch('G#4')]
        >>> tc = analysis.transposition.TranspositionChecker(pList)
        >>> tc.getChordsOfDistinctTranspositions()
        [<music21.chord.Chord C E G#>,
         <music21.chord.Chord C# F A>,
         <music21.chord.Chord D F# A#>,
         <music21.chord.Chord E- G B>]
        '''
        if self.distinctNormalOrders is None:
            self.listDistinctNormalOrders()
        distinctNormalOrders = self.distinctNormalOrders
        allNormalOrderChords = []
        for thisNormalOrder in distinctNormalOrders:
            thisNormalOrderChord = chord.Chord(thisNormalOrder)
            allNormalOrderChords.append(thisNormalOrderChord)
        return allNormalOrderChords

    def getPitchesOfDistinctTranspositions(self):
        '''
        Outputs pitch tuples for each distinct transposition (normal order).

        >>> pList = [pitch.Pitch('C4'), pitch.Pitch('E4'), pitch.Pitch('G#4')]
        >>> tc = analysis.transposition.TranspositionChecker(pList)
        >>> tc.getPitchesOfDistinctTranspositions()
        [(<music21.pitch.Pitch C>, <music21.pitch.Pitch E>, <music21.pitch.Pitch G#>),
         (<music21.pitch.Pitch C#>, <music21.pitch.Pitch F>, <music21.pitch.Pitch A>),
         (<music21.pitch.Pitch D>, <music21.pitch.Pitch F#>, <music21.pitch.Pitch A#>),
         (<music21.pitch.Pitch E->, <music21.pitch.Pitch G>, <music21.pitch.Pitch B>)]
        '''
        chords = self.getChordsOfDistinctTranspositions()
        allNormalOrderPitchTuples = [c.pitches for c in chords]
        return allNormalOrderPitchTuples

# ------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def testConstructTranspositionChecker(self):
        p = [pitch.Pitch('D#')]
        tc = TranspositionChecker(p)

        self.assertEqual(tc.pitches, p)
        numberOfPitchesInTc = len(tc.pitches)
        self.assertEqual(numberOfPitchesInTc, len(p))

    def testTranspositions(self):
        p = [pitch.Pitch('D#')]
        tc = TranspositionChecker(p)
        allTranspositions = tc.getTranspositions()

        self.assertEqual(len(allTranspositions), 12)
        self.assertIsInstance(allTranspositions[0][0], pitch.Pitch)
        self.assertEqual(allTranspositions[0][0].midi, p[0].midi)
        self.assertEqual(allTranspositions[1][0].midi, p[0].midi + 1)

        p = [pitch.Pitch('D#'), pitch.Pitch('F')]
        tc = TranspositionChecker(p)
        allTranspositions = tc.getTranspositions()

        self.assertEqual(len(allTranspositions), 12)
        self.assertIsInstance(allTranspositions[0][0], pitch.Pitch)
        self.assertEqual(allTranspositions[0][0].midi, p[0].midi)
        self.assertEqual(allTranspositions[0][1].midi, p[1].midi)

    def testNormalOrders(self):
        pList = [pitch.Pitch('C4'), pitch.Pitch('E4'), pitch.Pitch('G#4')]
        tc = TranspositionChecker(pList)
        normalOrders = tc.listNormalOrders()

        self.assertEqual(len(normalOrders), 12)
        self.assertLess(normalOrders[0][0], 13)

    def testDistinctNormalOrders(self):
        pList = [pitch.Pitch('C4'), pitch.Pitch('E4'), pitch.Pitch('G#4')]
        tc = TranspositionChecker(pList)
        allDistinctNormalOrders = tc.listDistinctNormalOrders()

        lengthDistinctNormalOrders = tc.numDistinctTranspositions()

        self.assertEqual(len(allDistinctNormalOrders), 4)
        self.assertEqual(lengthDistinctNormalOrders, 4)
        self.assertIsInstance(allDistinctNormalOrders, list)
        self.assertEqual(allDistinctNormalOrders[0], [0, 4, 8])

    def testNormalOrderChords(self):
        pList = [pitch.Pitch('C4'), pitch.Pitch('E4'), pitch.Pitch('G#4')]
        tc = TranspositionChecker(pList)

        allNormalOrderChords = tc.getChordsOfDistinctTranspositions()

        self.assertEqual(len(allNormalOrderChords), 4)
        # self.assertEqual(lengthDistinctNormalOrders, 4)
        self.assertIsInstance(allNormalOrderChords[0], chord.Chord)
        self.assertIsInstance(allNormalOrderChords[0].pitches[0], pitch.Pitch)
        # self.assertEqual(allDistinctNormalOrders[0], [0,4,8])

    def testNormalOrdersPitches(self):
        pList = [pitch.Pitch('C4'), pitch.Pitch('E4'), pitch.Pitch('G#4')]
        tc = TranspositionChecker(pList)

        allNormalOrderPitchTuples = tc.getPitchesOfDistinctTranspositions()

        self.assertEqual(len(allNormalOrderPitchTuples), 4)
        # self.assertEqual(lengthDistinctNormalOrders, 4)
        self.assertIsInstance(allNormalOrderPitchTuples[0], tuple)
        self.assertIsInstance(allNormalOrderPitchTuples[0][0], pitch.Pitch)
        # self.assertEqual(allDistinctNormalOrders[0], [0,4,8])


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
