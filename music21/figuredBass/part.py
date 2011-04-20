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
from music21 import clef

from music21.figuredBass import realizerScale
from music21.figuredBass import realizer

class Part:
    def __init__(self, label, lowestWrittenPitch = realizer.MIN_PITCH, highestWrittenPitch = realizer.MAX_PITCH, soundingTransposition = interval.Interval('P1')):
        '''
        Creates a Part instance, which represents a part or voice in music, a single vocal part or instrument.
         
        A Part is created by providing a lowestPitch and highestPitch for a given part, as represented on a staff, with an associated
        music21 interval which represents the interval between the written pitches and the way they sound in the case of transposing 
        parts. You can access a Part's writtenRange by calling self.writtenRange and soundingRange by calling self.soundingRange.
        
        A Part can store other parameters as well:
        (1) maxSeparation: maximum separation between two consecutive notes/pitches on a staff associated with this part. 
        Default is a perfect octave. Represented as a music21 interval object.
        (2) myClef: default clef to use in staff representation. Default is a Treble Clef. Represented as a music21 clef object.
        
        >>> from music21 import clef  
        >>> from music21.figuredBass import part
        
        >>> bassVoice = part.Part('Bass','E2','E4')
        >>> bassVoice
        <music21.figuredBass.part.Part Bass: E2->E4 (written and sounding)>
        >>> bassVoice.myClef = clef.BassClef()
        >>> bassVoice.maxSeparation
        <music21.interval.Interval P8>
        >>> bassVoice.writtenRange
        <music21.figuredBass.part.WrittenRange E2->E4>
        >>> bassVoice.soundingRange
        <music21.figuredBass.part.SoundingRange E2->E4>
        
        >>> viola = part.Part('Viola','C3','C6')
        >>> viola
        <music21.figuredBass.part.Part Viola: C3->C6 (written and sounding)>
        >>> viola.myClef = clef.AltoClef()
        
        >>> sopranoVoice = part.Part('Soprano','C4','A5')
        >>> sopranoVoice
        <music21.figuredBass.part.Part Soprano: C4->A5 (written and sounding)>
        >>> sopranoVoice.maxSeparation = interval.Interval('M2')
        >>> sopranoVoice.maxSeparation
        <music21.interval.Interval M2>
        
        >>> doubleBass = part.Part('Double Bass','C2','C5', interval.Interval('P-8'))
        >>> doubleBass
        <music21.figuredBass.part.Part Double Bass: C2->C5 (written), C1->C4 (sounding)>
        >>> doubleBass.myClef = clef.BassClef()
        >>> doubleBass.writtenRange
        <music21.figuredBass.part.WrittenRange C2->C5>
        >>> doubleBass.soundingRange
        <music21.figuredBass.part.SoundingRange C1->C4>
        '''
        self.label = label
        self.writtenRange = WrittenRange(lowestWrittenPitch, highestWrittenPitch)
        
        self.soundingTransposition = soundingTransposition
        lowestSoundingPitch = self.writtenRange.lowestPitch.transpose(self.soundingTransposition)
        highestSoundingPitch = self.writtenRange.highestPitch.transpose(self.soundingTransposition)
        self.soundingRange = SoundingRange(lowestSoundingPitch, highestSoundingPitch)
        
        self.maxSeparation = interval.Interval('P8')
        self.myClef = clef.TrebleClef()
        
    def __str__(self):
        if self.writtenRange == self.soundingRange:
            return self.label + ": " + str(self.writtenRange) + " (written and sounding)"
        else:
            return self.label + ": " + str(self.writtenRange) + " (written)" + ", " + str(self.soundingRange) + " (sounding)"
    
    def __repr__(self):
        return "<music21.figuredBass.part.Part " + str(self) + ">"

    def pitchesInSoundingRange(self, pitchList):
        '''
        >>> from music21.figuredBass import part
        >>> from music21.figuredBass import realizerScale
        >>> sc = realizerScale.FiguredBassScale('C')
        >>> pitchesAboveBass = sc.getPitches('C2')
        >>> pitchesAboveBass
        [C2, E2, G2, C3, E3, G3, C4, E4, G4, C5, E5, G5]
        
        >>> bassPart = part.Part('Bass','E2','E4')
        >>> bassPart.pitchesInSoundingRange(pitchesAboveBass)
        [E2, G2, C3, E3, G3, C4, E4]
        >>> doubleBass = part.Part('Double Bass','C2','C5', interval.Interval('P-8'))
        >>> doubleBass.soundingRange
        <music21.figuredBass.part.SoundingRange C1->C4>        
        >>> doubleBass.pitchesInSoundingRange(pitchesAboveBass)
        [C2, E2, G2, C3, E3, G3, C4]
        '''
        return self.soundingRange.pitchesInRange(pitchList)

    def __gt__(self, other):
        '''
        Returns true if Part self is higher than other.
        
        A Part is higher if it's sounding range is higher. 
        
        >>> from music21.figuredBass import part
        >>> soprano1 = part.Part('Soprano1','C4','A5')
        >>> soprano2 = part.Part('Soprano2','C4','A5')
        >>> bass = part.Part('Bass','E2','E4')
        >>> soprano1 > soprano2
        True
        >>> soprano2 > soprano1
        False
        >>> bass > soprano2
        False
        '''
        if self.soundingRange > other.soundingRange:
            return True
        elif self.soundingRange == other.soundingRange:
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
    
    
class PartException(music21.Music21Exception):
    pass

#-------------------------------------------------------------------------------  
class Range:
    def __init__(self, lowestPitch, highestPitch):
        '''
        '''
        pitchA = realizerScale.convertToPitch(lowestPitch)
        pitchB = realizerScale.convertToPitch(highestPitch)
        if pitchA > pitchB:
            self.lowestPitch = pitchB
            self.highestPitch = pitchA
        else:
            self.lowestPitch = pitchA
            self.highestPitch = pitchB

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
        >>> sopranoWritten = part.WrittenRange('C4','A5')
        >>> sopranoSounding = part.SoundingRange('C4','A5')
        >>> bassWritten = part.WrittenRange('E2','E4')
        >>> sopranoWritten == sopranoSounding
        True
        >>> sopranoWritten == bassWritten
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
        >>> sopranoWritten = part.WrittenRange('C4','A5')
        >>> sopranoSounding = part.SoundingRange('C4','A5')
        >>> bassWritten = part.WrittenRange('E2','E4')
        >>> sopranoWritten != sopranoSounding
        False
        >>> sopranoWritten != bassWritten
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
        
        SamplePitch can be either a music21 pitch or a pitch string.
        
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
            if not (self.lowestPitch > possiblePitch) and not (possiblePitch > self.highestPitch):
                    validPitches.append(possiblePitch)
                
        if len(validPitches) == 0:
            raise RangeException("None of these pitches fall within the range " + str(self) + ": " +  str(pitchList))
        
        return validPitches

class WrittenRange(Range):
    '''
    '''
    def __repr__(self):
        '''
        Returns the WrittenRange as a string with a "music21.figuredBass.part WrittenRange" designation.
        
        >>> from music21 import interval       
        >>> from music21.figuredBass import part
        >>> bassVoice = part.WrittenRange('E2','E4')
        >>> doubleBass = part.WrittenRange('C2','C5')
        >>> bassVoice
        <music21.figuredBass.part.WrittenRange E2->E4>
        >>> doubleBass
        <music21.figuredBass.part.WrittenRange C2->C5>       
        '''
        return "<music21.figuredBass.part.WrittenRange " + str(self) + ">"

class SoundingRange(Range):
    '''
    '''
    def __repr__(self):
        '''
        Returns the SoundingRange as a string with a "music21.figuredBass.part SoundingRange" designation.
        
        >>> from music21 import interval       
        >>> from music21.figuredBass import part
        >>> bassVoice = part.SoundingRange('E2','E4')
        >>> doubleBass = part.SoundingRange('C1','C4')
        >>> bassVoice
        <music21.figuredBass.part.SoundingRange E2->E4>
        >>> doubleBass
        <music21.figuredBass.part.SoundingRange C1->C4>       
        '''
        return "<music21.figuredBass.part.SoundingRange " + str(self) + ">"

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
    