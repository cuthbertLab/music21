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

from music21 import interval

class Rules:
    def __init__(self):
        #Voicing Rules
        self.allowParallelFifths = False
        self.allowParallelOctaves = False
        self.allowVoiceOverlap = False
        self.bottomVoiceLeapIntervalLimit = interval.Interval('P8')
        self.topVoiceLeapIntervalLimit = interval.Interval('P8')

        #Chord rules
        self.allowIncompletePossibilities = False
        self.topVoicesMaxIntervalSeparation = interval.Interval('P8')
        self.filterPitchesByRange = True

        #Chord To Chord Rules
        self.allowHiddenFifths = False
        self.allowHiddenOctaves = False
        
        #AntecedentPossibilityRules
        self.allowVoiceCrossing = False
        
        
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
  