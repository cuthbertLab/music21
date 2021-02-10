# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         enharmonics.py
# Purpose:      Tools for returning best enharmonics
#
# Authors:      Mark Gotham
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2017 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------

import itertools
from math import inf
import unittest


from music21 import exceptions21
from music21 import pitch
from music21 import musedata

from music21 import environment
_MOD = 'analysis.enharmonics'
environLocal = environment.Environment(_MOD)


class EnharmonicsException(exceptions21.Music21Exception):
    pass

class EnharmonicScoreRules:
    def __init__(self):
        self.sameStaffLine = False
        self.alterationPenalty = 4
        self.augDimPenalty = 2
        self.mixSharpsFlatsPenalty = False

class ChordEnharmonicScoreRules(EnharmonicScoreRules):
    def __init__(self):
        super().__init__()
        self.mixSharpsFlatsPenalty = 2

class EnharmonicSimplifier:
    '''
    Takes any pitch list input and returns the best enharmonic respelling according to the input
    criteria and rule weightings.
    Those criteria and rule weightings are currently fixed, but in future the user should be able
    to select their own combination and weighting of rules according to preferences,
    with predefined defaults for melodic and harmonic norms.
    Note: EnharmonicSimplifier itself returns nothing.
    '''
    def __init__(self, pitchList, ruleClass=EnharmonicScoreRules):
        if isinstance(pitchList[0], str):
            pitchList = [pitch.Pitch(p) for p in pitchList]

        self.pitchList = pitchList
        self.ruleObject = ruleClass()
        self.allPossibleSpellings = None
        self.allSpellings = []
        self.getRepresentations()

    def getRepresentations(self):
        '''
        Takes a list of pitches or pitch names and retrieves all enharmonic spellings.
        Note: getRepresentations itself returns nothing.
        '''
        allSpellings = []
        for p in self.pitchList:
            spellings = [p] + p.getAllCommonEnharmonics(1)
            allSpellings.append(spellings)
        self.allSpellings = allSpellings

    def getProduct(self):
        self.allPossibleSpellings = list(itertools.product(*self.allSpellings))
        return self.allPossibleSpellings

    def bestPitches(self):
        '''
        Returns a list of pitches in the best enharmonic
        spelling according to the input criteria.

        >>> pList1 = [pitch.Pitch('C'), pitch.Pitch('D'), pitch.Pitch('E')]
        >>> es = analysis.enharmonics.EnharmonicSimplifier(pList1)
        >>> es.bestPitches()
        (<music21.pitch.Pitch C>, <music21.pitch.Pitch D>, <music21.pitch.Pitch E>)
        >>> pList2 = ['D--', 'E', 'F##']
        >>> es = analysis.enharmonics.EnharmonicSimplifier(pList2)
        >>> es.bestPitches()
        (<music21.pitch.Pitch C>, <music21.pitch.Pitch E>, <music21.pitch.Pitch G>)
        '''
        self.getProduct()
        bestPitches = []
        minScore = inf
        for possibility in self.allPossibleSpellings:
            thisAugDimScore = self.getAugDimScore(possibility)
            thisAlterationScore = self.getAlterationScore(possibility)
            thisMixSharpsFlatScore = self.getMixSharpFlatsScore(possibility)
            thisScore = thisAugDimScore + thisAlterationScore + thisMixSharpsFlatScore
            if thisScore < minScore:
                minScore = thisScore
                bestPitches = possibility
        return bestPitches

    def getAlterationScore(self, possibility):
        '''
        Returns a score according to the number of sharps and flats in a possible spelling.
        The score is the sum of the flats and sharps + 1, multiplied by the alterationPenalty.
        '''
        if self.ruleObject.alterationPenalty is False:
            return 1

        joinedPossibility = ''.join([p.name for p in possibility])
        flatCount = joinedPossibility.count('-')
        sharpCount = joinedPossibility.count('#')
        score = (flatCount + sharpCount + 1) * self.ruleObject.alterationPenalty
        return score

    def getMixSharpFlatsScore(self, possibility):
        '''
        Returns a score based on the mixture of sharps and flats in a possible spelling:
        the score is given by the number of the lesser used accidental (sharps or flats)
        multiplied by the mixSharpsFlatsPenalty.
        '''
        if self.ruleObject.mixSharpsFlatsPenalty is False:
            return 1

        joinedPossibility = ''.join([p.name for p in possibility])
        flatCount = joinedPossibility.count('-')
        sharpCount = joinedPossibility.count('#')
        score = min([flatCount, sharpCount]) * self.ruleObject.mixSharpsFlatsPenalty
        return score

    def getAugDimScore(self, possibility):
        '''
        Returns a score based on the number of augmented and diminished intervals between
        successive pitches in the given spelling.
        '''
        if self.ruleObject.augDimPenalty is False:
            return 1

        intervalStr = ''
        for i in range(len(possibility) - 1):
            p0 = musedata.base40.base40Representation[possibility[i].name]
            p1 = musedata.base40.base40Representation[possibility[i + 1].name]
            base40diff = (p1 - p0) % 40
            intervalStr += musedata.base40.base40IntervalTable.get(base40diff, 'ddd')
        dimCount = intervalStr.count('A')
        augCount = intervalStr.count('d')
        score = (dimCount + augCount + 1) * self.ruleObject.augDimPenalty
        return score

# ------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def testBestPitches(self):
        pList = [pitch.Pitch('C'), pitch.Pitch('D'), pitch.Pitch('E')]
        es = EnharmonicSimplifier(pList)
        bestPitchList = es.bestPitches()

        self.assertEqual(len(pList), 3)
        self.assertEqual(len(bestPitchList), 3)
        self.assertIsInstance(bestPitchList[0], pitch.Pitch)

    def testGetAlterationScore(self):
        pList = [pitch.Pitch('C'), pitch.Pitch('D'), pitch.Pitch('E')]
        es = EnharmonicSimplifier(pList)
        poss = [pitch.Pitch('C'), pitch.Pitch('D'), pitch.Pitch('E')]
        testAltScore = es.getAlterationScore(poss)

        self.assertEqual(len(pList), 3)
        self.assertIsInstance(testAltScore, int)

    def testGetMixSharpFlatsScore(self):
        pList = [pitch.Pitch('C'), pitch.Pitch('D'), pitch.Pitch('E')]
        es = EnharmonicSimplifier(pList)
        poss = [pitch.Pitch('C'), pitch.Pitch('D'), pitch.Pitch('E')]
        testMixScore = es.getMixSharpFlatsScore(poss)

        self.assertEqual(len(pList), 3)
        self.assertIsInstance(testMixScore, int)

    def testGetAugDimScore(self):
        pList = [pitch.Pitch('C'), pitch.Pitch('D'), pitch.Pitch('E')]
        es = EnharmonicSimplifier(pList)
        poss = [pitch.Pitch('C'), pitch.Pitch('D'), pitch.Pitch('E')]
        testAugDimScore = es.getAugDimScore(poss)

        self.assertEqual(len(pList), 3)
        self.assertIsInstance(testAugDimScore, int)


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
