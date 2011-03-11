#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         voice.py
# Purpose:      music21 class which represents the concept of a voice and its range.
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import music21
import unittest
import copy

from music21 import interval

from music21.figuredBass import realizerScale

class Voice:
    def __init__(self, label, range = None, maxIntervalLeap = interval.Interval('P8')):
        '''
        >>> from music21 import *
        >>> sc = realizerScale.FiguredBassScale('C')
        >>> pitchesAboveBass = sc.getPitches('C2')
        >>> pitchesAboveBass
        [C2, E2, G2, C3, E3, G3, C4, E4, G4, C5, E5, G5]
        
        >>> bassRange = Range('E2','E4')
        >>> bassVoice = Voice('Bass', bassRange)
        >>> bassVoice
        Bass: E2->E4
        '''
        self.label = label
        self.range = range
        self.maxIntervalLeap = maxIntervalLeap
        # A voice also has these associations:
        # Clef -> Treble/Bass (or less commonly alto, tenor, soprano) 
        # These last two are more properties of the bar than anything:
        # Key Signature
        # Time Signature
        
    def pitchesInRange(self, pitchList):
        '''
        >>> from music21 import *
        >>> sc = realizerScale.FiguredBassScale('C')
        >>> pitchesAboveBass = sc.getPitches('C2')
        >>> pitchesAboveBass
        [C2, E2, G2, C3, E3, G3, C4, E4, G4, C5, E5, G5]
        
        >>> bassRange = Range('E2','E4')
        >>> bassVoice = Voice('Bass', bassRange)
        >>> bassVoice.pitchesInRange(pitchesAboveBass)
        [E2, G2, C3, E3, G3, C4, E4]
        '''
        if self.range is None:
            return copy.copy(pitchList)
        else:
            return self.range.pitchesInRange(pitchList)

    def __str__(self):
        return self.label + ": " + str(self.range)
        
    def __repr__(self):
        return str(self)

    def __gt__(self, other):
        if self.range > other.range:
            return True
        elif self.range == other.range and self.label < other.label:
            return True
        else:
            return False
    
    def __ge__(self, other):
        if self > other or self == other:
            return True
        else:
            return False
    
    def __lt__(self, other):
        if self.range < other.range:
            return True
        elif self.range == other.range and self.label > other.label:
            return True
        else:
            return False
    
    def __le__(self, other):
        if self < other or self == other:
            return True
        else:
            return False
    
    def __eq__(self, other):    
        if self.range == other.range and self.label == other.label:
            return True
        else:
            return False
    
    def __ne__(self, other):
        if not (self.range == other.range):
            return True
        else:
            return False
    
    
class VoiceException(music21.Music21Exception):
    pass

#-------------------------------------------------------------------------------  
class Range:
    def __init__(self, lowestPitch, highestPitch):
        '''
        Conveniently stores the lower and upper ranges of vocals or instruments.
        
        >>> from music21 import *
        >>> r0 = Range('E2','E4')
        >>> r1 = Range('C3','A4')
        >>> r2 = Range('F3','G5')
        >>> r3 = Range('C4','A5')
        >>> r4 = Range('C4','A5')

        >>> r2 > r3
        False
        >>> r3 < r0
        False
        >>> r3 == r3
        True
        >>> r3 > r1
        True
        >>> r3 > r4
        False
        
        >>> ranges = [r3, r0, r1, r2, r4]
        >>> ranges
        [C4->A5, E2->E4, C3->A4, F3->G5, C4->A5]
        >>> ranges.sort()
        >>> ranges # from lowest to highest 
        [E2->E4, C3->A4, F3->G5, C4->A5, C4->A5]
        >>> ranges.reverse()
        >>> ranges # from highest to lowest
        [C4->A5, C4->A5, F3->G5, C3->A4, E2->E4]
        '''
        pitchA = realizerScale.convertToPitch(lowestPitch)
        pitchB = realizerScale.convertToPitch(highestPitch)
        if pitchA > pitchB:
            raise RangeException("Invalid range provided.")
        self.lowestPitch = pitchA
        self.highestPitch = pitchB
    
    def __str__(self):
        return str(self.lowestPitch) + "->" + str(self.highestPitch)
    
    def __repr__(self):
        return str(self)
        
    def __gt__(self, other):
        if self.lowestPitch > other.lowestPitch:
            return True
        elif self.lowestPitch == other.lowestPitch:
            if self.highestPitch > other.highestPitch:
                return True
            else:
                return False
        else:
            return False
    
    def __ge__(self, other):
        if self > other or self == other:
            return True
        else:
            return False

    def __lt__(self, other):
        if self.lowestPitch < other.lowestPitch:
            return True
        elif self.lowestPitch == other.lowestPitch:
            if self.highestPitch < other.highestPitch:
                return True
            else:
                return False
        else:
            return False

    def __le__(self, other):
        if self < other or self == other:
            return True
        else:
            return False
    
    def __eq__(self, other):
        if self.lowestPitch == other.lowestPitch and self.highestPitch == other.highestPitch:
            return True
        else:
            return False
        
    def __ne__(self, other):
        if not self == other:
            return True
        else:
            return False
    
    def pitchesInRange(self, pitchList):
        '''
        Given a list of pitches, returns a list of those which fall within this range, inclusive.
        The original list is not modified, but the new list contains the same pitches, not copies.
    
        >>> from music21 import *
        >>> sc = realizerScale.FiguredBassScale('C')
        >>> pitchesAboveBass = sc.getPitches('C2')
        >>> pitchesAboveBass
        [C2, E2, G2, C3, E3, G3, C4, E4, G4, C5, E5, G5]
        
        >>> r0 = Range('E2', 'E4')
        >>> r0.pitchesInRange(pitchesAboveBass)
        [E2, G2, C3, E3, G3, C4, E4]
        
        >>> r1 = Range('C3', 'A4')
        >>> r1.pitchesInRange(pitchesAboveBass)
        [C3, E3, G3, C4, E4, G4]
        
        >>> r2 = Range('F3', 'G5')
        >>> r2.pitchesInRange(pitchesAboveBass)
        [G3, C4, E4, G4, C5, E5, G5]
        
        >>> r3 = Range('C4', 'A5')
        >>> r3.pitchesInRange(pitchesAboveBass)
        [C4, E4, G4, C5, E5, G5]
        '''
        validPitches = []
        for possiblePitch in pitchList:
            if not (self.lowestPitch > possiblePitch) and not (possiblePitch > self.highestPitch):
                    validPitches.append(possiblePitch)
                
        if len(validPitches) == 0:
            raise RangeException("None of the pitches in pitch list fall within " + str(self))
        
        return validPitches

class RangeException(music21.Music21Exception):
    pass

#-------------------------------------------------------------------------------  
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof
    