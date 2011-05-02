#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         part.py
# Purpose:      music21 class which represents the concept of a part and its range.
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import music21
import unittest
import copy

from music21.interval import Interval
from music21.pitch import Pitch

from music21.figuredBass import realizerScale

class Part(object):
    def __init__(self, label, maxSeparation = 12, lowestPitch = 'A0', highestPitch = 'C8'):
        '''
        Creates a Part instance, which represents information for a line of music.
        
        A Part is created by providing the following parameters:
        (1) A label, which names the part. 
        (2) A lowestPitch and highestPitch, which is stored as a Range instance.
        (3) A maxSeparation integer which represents, in semitones, the maximum separation 
        allowed between two consecutive notes/pitches on an associated staff.
        
        The default lowestPitch is A0, and the default highestPitch is C8, the typical range for a piano.
        The default maxSeparation is 12 semitones, enharmonically equivalent to a perfect octave (P8).
        
        A Part is immmutable once it is created, to allow it to be hashable and act as a key for a Possibility.
        
        >>> from music21.figuredBass import part
        >>> upperLine1 = part.Part(1)
        >>> upperLine1
        <music21.figuredBass.part Part 1: A0->C8>
        >>> upperLine1.label
        1
        >>> upperLine1.maxSeparation
        12
        >>> upperLine1.range.lowestPitch
        A0
        >>> upperLine1.range.highestPitch
        C8
         
        >>> upperLine2 = part.Part(2, 2)
        >>> upperLine2.maxSeparation # Major second, part limited to stepwise motion
        2
        
        >>> bassLine = part.Part('Bass', 16, 'E2', 'E4')
        >>> bassLine
        <music21.figuredBass.part Part Bass: E2->E4>
        >>> bassLine.label
        'Bass'
        >>> bassLine.maxSeparation # Major tenth
        16
        >>> bassLine.range.lowestPitch
        E2
        >>> bassLine.range.highestPitch
        E4
        '''
        super(Part, self).__setattr__('label', label)
        super(Part, self).__setattr__('range', Range(lowestPitch, highestPitch))
        super(Part, self).__setattr__('maxSeparation', maxSeparation)

    def __setattr__(self, *args):
        raise TypeError("Can't modify Part: It is an immutable instance.")
    
    __delattr__ = __setattr__
    
    def __hash__(self):
        tup = (self.label, self.maxSeparation, str(self.range.lowestPitch), str(self.range.highestPitch))
        return hash(tup)
        
    def __str__(self):
        return str(self.label) + ": " + str(self.range)

    def __repr__(self):
        return "<music21.figuredBass.part Part " + str(self) + ">"

    def __gt__(self, other):
        '''
        Returns true if Part self is higher than other.
        A Part is higher if its range is higher. 
        '''
        if self.range > other.range:
            return True
        elif self.range == other.range:
            if self.label < other.label:
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
    
def convertToInterval(intervalString):
    '''
    Converts an interval string to a music21 Interval, only if necessary.
    A PartException is raised if (1) an invalid interval string is provided or
    (2) what is provided is not a string or Interval.
    
    >>> from music21 import *
    >>> convertToInterval('P8')
    <music21.interval.Interval P8>
    >>> convertToInterval(interval.Interval('P8')) #does nothing
    <music21.interval.Interval P8>
    >>> convertToInterval('C3') #Invalid string interval
    Traceback (most recent call last):
    PartException: Could not convert the string C3 to a music21 Interval.
    >>> convertToInterval(note.Note('D3')) #Not an interval string or Interval
    Traceback (most recent call last):
    PartException: Could not convert <music21.note.Note D> to a music21 Interval.
    '''    
    if isinstance(intervalString, Interval):
        return intervalString
    
    if isinstance(intervalString, str):
        try:
            return Interval(intervalString)
        except:
            raise PartException("Could not convert the string " + str(intervalString) + " to a music21 Interval.")

    raise PartException("Could not convert " + str(intervalString) + " to a music21 Interval.")


class PartException(music21.Music21Exception):
    pass

#-------------------------------------------------------------------------------  
class Range(object):
    def __init__(self, lowestPitch, highestPitch):
        '''
        '''
        try:
            pitchA = realizerScale.convertToPitch(lowestPitch)
        except:
            pitchA = realizerScale.convertToPitch(lowestPitch) 
            raise RangeException("Cannot convert " + pitchA + " to a music21 Pitch.")
        
        try:
            pitchB = realizerScale.convertToPitch(highestPitch)
        except:
            raise RangeException("Cannot convert " + pitchB + " to a music21 Pitch.")

        if pitchA > pitchB:
            super(Range, self).__setattr__('lowestPitch', pitchB)
            super(Range, self).__setattr__('highestPitch', pitchA)
        else:
            super(Range, self).__setattr__('lowestPitch', pitchA)
            super(Range, self).__setattr__('highestPitch', pitchB)        

    def __setattr__(self, *args):
        raise TypeError("Can't modify Range: It is an immutable instance.")
    
    __delattr__ = __setattr__

    def __str__(self):
        '''
        Returns the Range as a string.

        >>> from music21.figuredBass import part
        >>> r0 = part.Range('E2','E4')
        >>> r1 = part.Range('C2','C5')
        >>> str(r0)
        'E2->E4'
        >>> str(r1)
        'C2->C5'
        '''
        range = str(self.lowestPitch) + "->" + str(self.highestPitch)
        return range

    def __repr__(self):
        return "<music21.figuredBass.part Range " + str(self) + ">"

    def __eq__(self, other):
        '''
        Returns True if both the lowestPitch and highestPitch of self match those of other. Otherwise, returns False.

        >>> from music21.figuredBass import part
        >>> upperPart1 = part.Range('A0','C8')
        >>> upperPart2 = part.Range('A0','C8')
        >>> upperPart3 = part.Range('A0','E4')
        >>> upperPart1 == upperPart2
        True
        >>> upperPart1 == upperPart3
        False
        '''
        if self.lowestPitch == other.lowestPitch and self.highestPitch == other.highestPitch:
            return True
        else:
            return False

    def __ne__(self, other):
        '''
        Returns False if both the lowestPitch and highestPitch of self match those of other. Otherwise, returns True.
        
        >>> from music21.figuredBass import part
        >>> upperPart1 = part.Range('A0','C8')
        >>> upperPart2 = part.Range('A0','C8')
        >>> upperPart3 = part.Range('A0','E4')
        >>> upperPart1 != upperPart2
        False
        >>> upperPart1 != upperPart3
        True
        '''
        if self.lowestPitch == other.lowestPitch and self.highestPitch == other.highestPitch:
            return False
        else:
            return True

    def __gt__(self, other):
        '''
        Returns True if self's Range is higher than other's.
        
        The higher Range is determined based first on the higher lowestPitch, and if they
        are equal, then it is based on the higher highestPitch. Returns False if both the
        lowestPitch and highestPitch of self match those of other.
        
        >>> from music21 import interval       
        >>> from music21.figuredBass import part
        >>> r0 = part.Range('F#3','D6')
        >>> r1 = part.Range('B3','G6')
        >>> r2 = part.Range('B3','G7')
        >>> r0 > r1
        False
        >>> r2 > r1
        True
        >>> r1 > r1
        False
        '''
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
        '''
        Returns True if self's Range is higher than or equal to other's.
        
        The higher Range is determined based first on the higher lowestPitch, and if they
        are equal, then it is based on the higher highestPitch. Returns True if both the
        lowestPitch and highestPitch of self match those of other.

        >>> from music21 import interval       
        >>> from music21.figuredBass import part
        >>> r0 = part.Range('F#3','D6')
        >>> r1 = part.Range('B3','G6')
        >>> r2 = part.Range('B3','G7')
        >>> r0 >= r1
        False
        >>> r2 >= r1
        True
        >>> r1 >= r1
        True
        '''
        if self > other or self == other:
            return True
        else:
            return False

    def __lt__(self, other):
        '''
        Returns True if self's Range is lower than other's.
        
        The lower Range is determined based first on the lower lowestPitch, and if they
        are equal, then it is based on the lower highestPitch. Returns False if both the
        lowestPitch and highestPitch of self match those of other.
        
        >>> from music21 import interval       
        >>> from music21.figuredBass import part
        >>> r0 = part.Range('F#3','D6')
        >>> r1 = part.Range('B3','G6')
        >>> r2 = part.Range('B3','G7')
        >>> r0 < r1
        True
        >>> r2 < r1
        False
        >>> r1 < r1
        False
        '''
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
        '''
        Returns True if self's Range is lower than or equal to other's.
        
        The lower Range is determined based first on the lower lowestPitch, and if they
        are equal, then it is based on the lower highestPitch. Returns True if both the
        lowestPitch and highestPitch of self match those of other.

        >>> from music21 import interval       
        >>> from music21.figuredBass import part
        >>> r0 = part.Range('F#3','D6')
        >>> r1 = part.Range('B3','G6')
        >>> r2 = part.Range('B3','G7')
        >>> r0 <= r1
        True
        >>> r2 <= r1
        False
        >>> r1 <= r1
        True
        '''
    
        if self < other or self == other:
            return True
        else:
            return False

    def pitchInRange(self, samplePitch):
        '''
        Returns True if samplePitch is found between the Range's lowestPitch and highestPitch, inclusive.
        Otherwise, returns False.
        
        samplePitch can be either a music21 pitch or a pitch string.
        
        >>> from music21 import pitch
        >>> from music21.figuredBass import part      
        >>> r0 = part.Range('F#3','D6')      
        >>> r0.pitchInRange(pitch.Pitch('G3'))
        True
        >>> r0.pitchInRange('D6')
        True
        >>> r0.pitchInRange('D7')
        False
        '''
        samplePitch = realizerScale.convertToPitch(samplePitch)
        if not (self.lowestPitch > samplePitch) and not (samplePitch > self.highestPitch):
            return True
        else:
            return False
    
    def pitchesInRange(self, pitchList):
        '''
        Given a list of music21 pitches or pitch strings, returns a second list of pitches which are found
        between the Range's lowestPitch and highestPitch, inclusive. 
        
        The original list is not modified, but the second list either contains references to pitches in
        pitchList or new pitches in the event that pitch strings are provided in pitchList.
    
        >>> from music21.figuredBass import realizerScale
        >>> sc = realizerScale.FiguredBassScale('C')
        >>> pitchesAboveBass = sc.getPitches('C2')
        >>> pitchesAboveBass
        [C2, E2, G2, C3, E3, G3, C4, E4, G4, C5, E5, G5]
        >>> pitchStringsAboveBass = ['C2', 'E2', 'G2', 'C3', 'E3', 'G3','C4', 'E4', 'G4', 'C5', 'E5', 'G5']

        >>> r0 = Range('E2', 'E4')
        >>> r0.pitchesInRange(pitchesAboveBass)
        [E2, G2, C3, E3, G3, C4, E4]
        >>> r0.pitchesInRange(pitchStringsAboveBass)
        [E2, G2, C3, E3, G3, C4, E4]

        >>> r1 = Range('C3', 'A4')
        >>> r1.pitchesInRange(pitchesAboveBass)
        [C3, E3, G3, C4, E4, G4]
        >>> r1.pitchesInRange(pitchStringsAboveBass)
        [C3, E3, G3, C4, E4, G4]
        '''
        validPitches = []
        for possiblePitch in pitchList:
            possiblePitch = realizerScale.convertToPitch(possiblePitch)
            if self.pitchInRange(possiblePitch):
                validPitches.append(possiblePitch)
                
        if len(validPitches) == 0:
            raise RangeException("None of these pitches fall within the range " + str(self) + ": " +  str(pitchList))
        
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
    