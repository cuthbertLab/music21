import music21
import unittest

from music21.figuredBass import realizerScale

class Range:
    def __init__(self, designation, lowestPitch = None, highestPitch = None):
        '''
        >>> from music21 import *
        >>> r0 = Range('Bass', 'E2', 'E4')
        >>> r1 = Range('Tenor', 'C3', 'A4')
        >>> r2 = Range('Alto', 'F3', 'G5')
        >>> r3 = Range('Soprano1', 'C4', 'A5')
        >>> r4 = Range('Soprano2', 'C4', 'A5')

        >>> r2 > r3
        False
        >>> r3 < r0
        False
        >>> r3 == r3
        True
        >>> r3 > r1
        True
        >>> r3 < r4 # When low/high pitches are equal, distinguished in reverse alphabetical order
        False
        
        >>> ranges = [r3, r0, r1, r2, r4]
        >>> ranges
        [<Soprano1: C4->A5>, <Bass: E2->E4>, <Tenor: C3->A4>, <Alto: F3->G5>, <Soprano2: C4->A5>]
        >>> ranges.sort()
        >>> ranges # from lowest to highest 
        [<Bass: E2->E4>, <Tenor: C3->A4>, <Alto: F3->G5>, <Soprano2: C4->A5>, <Soprano1: C4->A5>]
        >>> ranges.reverse()
        >>> ranges # from highest to lowest
        [<Soprano1: C4->A5>, <Soprano2: C4->A5>, <Alto: F3->G5>, <Tenor: C3->A4>, <Bass: E2->E4>]
        '''
        self.designation = designation
        self.lowestPitch = realizerScale.convertToPitch(lowestPitch)
        self.highestPitch = realizerScale.convertToPitch(highestPitch)
    
    def __str__(self):
        return str(self.designation) + ': ' + str(self.lowestPitch) + "->" + str(self.highestPitch)
    
    def __repr__(self):
        return "<" + str(self) + ">"
        
    def __gt__(self, other):
        # Works with vocal music, don't know how it'll stack up against instrumental music
        if self.lowestPitch > other.lowestPitch:
            return True
        elif self.lowestPitch == other.lowestPitch:
            if self.highestPitch > other.highestPitch:
                return True
            elif self.highestPitch == other.highestPitch:
                if self.designation < other.designation:
                    return True
                else:
                    return False
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
        # Works with vocal music, don't know how it'll stack up against instrumental music
        if self.lowestPitch < other.lowestPitch:
            return True
        elif self.lowestPitch == other.lowestPitch:
            if self.highestPitch < other.highestPitch:
                return True
            elif self.highestPitch == other.highestPitch:
                if self.designation > other.designation:
                    return True
                else:
                    return False
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
        if self.lowestPitch == other.lowestPitch and self.highestPitch == other.highestPitch and self.designation == other.designation:
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
        >>> pitchesAboveBass = sc.getPitches('C3')
        >>> pitchesAboveBass
        [C3, E3, G3, C4, E4, G4, C5, E5, G5]
        
        >>> r0 = Range('Bass', 'E2', 'E4')
        >>> r0.pitchesInRange(pitchesAboveBass)
        [C3, E3, G3, C4, E4]
        
        >>> r1 = Range('Tenor', 'C3', 'A4')
        >>> r1.pitchesInRange(pitchesAboveBass)
        [C3, E3, G3, C4, E4, G4]
        
        >>> r2 = Range('Alto', 'F3', 'G5')
        >>> r2.pitchesInRange(pitchesAboveBass)
        [G3, C4, E4, G4, C5, E5, G5]
        
        >>> r3 = Range('Soprano', 'C4', 'A5')
        >>> r3.pitchesInRange(pitchesAboveBass)
        [C4, E4, G4, C5, E5, G5]
        '''
        validPitches = []
        for possiblePitch in pitchList:
            if not (self.lowestPitch > possiblePitch):
                if not (possiblePitch > self.highestPitch):
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
    