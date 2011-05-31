#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         rules.py
# Purpose:      music21 class to define rules used in composition
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2010 The music21 Project    
# License:      LGPL
#-------------------------------------------------------------------------------

import music21
import unittest

from music21 import pitch

class Rules(object):
    def __init__(self):
        '''
        >>> from music21.figuredBass import rules
        >>> fbRules = rules.Rules()
        >>> fbRules.forbidParallelFifths = False
        '''
        self.maxPitch = pitch.Pitch('B5')
        self.numParts = 4
                
        #Single Possibility rules
        self.forbidIncompletePossibilities = True
        self.upperPartsMaxSemitoneSeparation = 12
        self.forbidVoiceCrossing = True
        
        #Consecutive Possibility rules
        self.forbidParallelFifths = True
        self.forbidParallelOctaves = True
        self.forbidHiddenFifths = True
        self.forbidHiddenOctaves = True
        self.forbidVoiceOverlap = True
        self.partMovementLimits = []

        #Special resolution rules
        self.resolveDominantSeventhProperly = True
        self.resolveDiminishedSeventhProperly = True
        self.resolveAugmentedSixthProperly = True
        self.doubledRootInDim7 = False
        
        self._upperPartsRemainSame = False


class FiguredBassRulesException(music21.Music21Exception):
    pass

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    music21.mainTest(Test)  

#------------------------------------------------------------------------------
# eof
  