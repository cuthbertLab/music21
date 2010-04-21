#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         voiceLeading.py
# Purpose:      music21 classes for voice leading
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import unittest, doctest

import music21
from music21 import interval

from music21.note import Note
from music21.interval import Interval

#-------------------------------------------------------------------------------
class VoiceLeadingQuartet(music21.Music21Object):
    '''An object consisting of four pitches: v1n1, v1n2, v2n1, v2n2
    where v1n1 moves to v1n2 at the same time as 
    v2n1 moves to v2n2.  
    
    Necessary for classifying types of voice-leading motion
    '''
    
    motionType = None
    unison = interval.stringToInterval("P1")
    fifth  = interval.stringToInterval("P5")
    octave = interval.stringToInterval("P8")
        
    def __init__(self, v1n1, v1n2, v2n1, v2n2):
        self.v1n1 = v1n1
        self.v1n2 = v1n2
        self.v2n1 = v2n1
        self.v2n2 = v2n2    
        self.vIntervals = []
        self.hIntervals = []
        self._findIntervals()
    
    def _findIntervals(self):
        self.vIntervals.append(interval.notesToInterval(self.v1n1, self.v2n1))
        self.vIntervals.append(interval.notesToInterval(self.v1n2, self.v2n2))
        self.hIntervals.append(interval.notesToInterval(self.v1n1, self.v1n2))
        self.hIntervals.append(interval.notesToInterval(self.v2n1, self.v2n2))
    
    def noMotion(self):
        '''Returns true if no voice moves at this "voice-leading" moment'''
        for iV in self.hIntervals:
            if iV.name != "P1": 
                return False
        return True

    def obliqueMotion(self):
        '''
        Returns true if one voice remains the same and another moves.  I.e., isNoMotion 
        must also be false
        '''
        if self.noMotion():
            return False
        else:
            for iV in self.hIntervals:
                if iV.name != "P1": 
                    return False
            else:
                return True
    
    
    def similarMotion(self):
        '''
        Returns true if the two voices both move in the same direction.
        Parallel Motion will also return true, as it is a special case of similar motion
        '''
        
        if self.noMotion():
            return False
        else:
            if self.hIntervals[0].direction == self.hIntervals[1].direction:
                return True
            else:
                return False
 
    def parallelMotion(self):
        '''returns True if both voices move with the same interval or an octave duplicate of the interval'''
        if not self.similarMotion():
            return False
        else:
            if self.vIntervals[0].directedSimpleName == self.vIntervals[1].directedSimpleName:
                return True
    
    def contraryMotion(self):
        '''
        returns True if both voices move in opposite directions
        '''
        
        if self.noMotion():
            return False
        elif self.parallelMotion():
            return False
        else:
            if self.hIntervals[0].direction == self.hIntervals[1].direction:
                return False
            else:
                return True
 
    def antiParallelMotion(self):
        '''
        Returns true if the simple interval before is the same as the simple interval after
        and the motion is contrary

        >>> n11 = Note("C4")
        >>> n12 = Note("D3") # descending 7th
        >>> n21 = Note("G4")
        >>> n22 = Note("A4") # ascending 2nd
        >>> vlq1 = VoiceLeadingQuartet(n11, n12, n21, n22)
        >>> vlq1.antiParallelMotion()
        True

        '''
        if not self.contraryMotion():
            return False
        else:
            if self.vIntervals[0].simpleName == self.vIntervals[1].simpleName:
                return True
            else:
                return False

 
    def parallelInterval(self, thisInterval):
        '''
        Returns true if there is a parallel or antiParallel interval of this type
        
        >>> n11 = Note("C4")
        >>> n12a = Note("D4") # ascending 2nd
        >>> n12b = Note("D3") # descending 7th

        >>> n21 = Note("G4")
        >>> n22a = Note("A4") # ascending 2nd
        >>> n22b = Note("B4") # ascending 3rd
        >>> vlq1 = VoiceLeadingQuartet(n11, n12a, n21, n22a)
        >>> vlq1.parallelInterval(Interval("P5"))
        True
        >>> vlq1.parallelInterval(Interval("P8"))
        False
        
        Antiparallel fifths also are true
        >>> vlq2 = VoiceLeadingQuartet(n11, n12b, n21, n22a)
        >>> vlq2.parallelInterval(Interval("P5"))
        True
        
        Non-parallel intervals are, of course, False
        >>> vlq3 = VoiceLeadingQuartet(n11, n12a, n21, n22b)
        >>> vlq3.parallelInterval(Interval("P5"))
        False
        '''
        
        if not (self.parallelMotion() or self.antiParallelMotion()):
            return False
        else:
            if self.vIntervals[0].semiSimpleName == thisInterval.semiSimpleName:
                return True
            else:
                return False

    def parallelFifth(self):
        '''
        Returns true if the motion is a parallel Perfect Fifth (or antiparallel) or Octave duplication
        >>> VoiceLeadingQuartet(Note("C4"), Note("D4"), Note("G4"), Note("A4")).parallelFifth()
        True
        >>> VoiceLeadingQuartet(Note("C4"), Note("D4"), Note("G5"), Note("A5")).parallelFifth()
        True
        >>> VoiceLeadingQuartet(Note("C4"), Note("D#4"), Note("G4"), Note("A4")).parallelFifth()
        False
        '''
        return self.parallelInterval(self.fifth)
    
    def parallelOctave(self):
        '''
        Returns true if the motion is a parallel Perfect Octave
        
        [ a concept so abhorrent we shudder to illustrate it with an example, but alas, we must ]

        >>> VoiceLeadingQuartet(Note("C4"), Note("D4"), Note("C5"), Note("D5")).parallelOctave()
        True
        >>> VoiceLeadingQuartet(Note("C4"), Note("D4"), Note("C6"), Note("D6")).parallelOctave()
        True
        >>> VoiceLeadingQuartet(Note("C4"), Note("D4"), Note("C4"), Note("D4")).parallelOctave()
        False
        '''
        return self.parallelInterval(self.octave)
    
    def parallelUnison(self):
        '''
        Returns true if the motion is a parallel Perfect Unison (and not Perfect Octave, etc.)

        >>> VoiceLeadingQuartet(Note("C4"), Note("D4"), Note("C4"), Note("D4")).parallelUnison()
        True
        >>> VoiceLeadingQuartet(Note("C4"), Note("D4"), Note("C5"), Note("D5")).parallelUnison()
        False
        '''
        return self.parallelInterval(self.unison)

    def parallelUnisonOrOctave(self):
        '''
        >>> VoiceLeadingQuartet(Note("C4"), Note("D4"), Note("C3"), Note("D3")).parallelUnisonOrOctave()
        True
        >>> VoiceLeadingQuartet(Note("C4"), Note("D4"), Note("C4"), Note("D4")).parallelUnisonOrOctave()
        True
        '''
    
        return (self.parallelOctave() | self.parallelUnison() )
    
    
    def hiddenInterval(self, thisInterval):
        '''
        n.b. -- this method finds ALL hidden intervals,
        not just those that are forbidden under traditional
        common practice counterpoint rules
        '''
        
        if self.parallelMotion():
            return False
        elif not self.similarMotion():
            return False
        else:
            if self.vIntervals[1].simpleName == thisInterval.simpleName:
                return True
            else:
                return False
 
    def hiddenFifth(self):
        return self.hiddenInterval(self.fifth)
    
    def hiddenOctave(self):
        return self.hiddenInterval(self.octave)

class VoiceLeadingException(Exception):
    pass





#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass
 

    def testCopyAndDeepcopy(self):
        '''Test copyinng all objects defined in this module
        '''
        import sys, types, copy
        for part in sys.modules[self.__module__].__dict__.keys():
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            obj = getattr(sys.modules[self.__module__], part)
            if callable(obj) and not isinstance(obj, types.FunctionType):
                a = copy.copy(obj)
                b = copy.deepcopy(obj)

   
    def unifiedTest(self):
        C4 = Note(); C4.name = "C"
        D4 = Note(); D4.name = "D"
        E4 = Note(); E4.name = "E"
        F4 = Note(); F4.name = "F"
        G4 = Note(); G4.name = "G"
        A4 = Note(); A4.name = "A"
        B4 = Note(); B4.name = "B"
        C5 = Note(); C5.name = "C"; C5.octave = 5
        D5 = Note(); D5.name = "D"; D5.octave = 5
        
        a = VoiceLeadingQuartet(C4, D4, G4, A4)
        assert a.similarMotion() == True
        assert a.parallelMotion() == True
        assert a.antiParallelMotion() == False
        assert a.obliqueMotion() == False
        assert a.parallelInterval(interval.stringToInterval("P5")) == True
        assert a.parallelInterval(interval.stringToInterval("M3")) == False
    
        b = VoiceLeadingQuartet(C4, C4, G4, G4)
        assert b.noMotion() == True
        assert b.parallelMotion() == False
        assert b.antiParallelMotion() == False
        assert b.obliqueMotion() == False
            
        c = VoiceLeadingQuartet(C4, G4, C5, G4)
        assert c.antiParallelMotion() == True
        assert c.hiddenInterval(interval.stringToInterval("P5")) == False
    
        d = VoiceLeadingQuartet(C4, D4, E4, A4)
        assert d.hiddenInterval(Interval("P5")) == True
        assert d.hiddenInterval(Interval("A4")) == False
        assert d.hiddenInterval(Interval("AA4")) == False

if __name__ == "__main__":
    music21.mainTest(Test)