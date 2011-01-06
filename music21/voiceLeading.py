#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         voiceLeading.py
# Purpose:      music21 classes for voice leading
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#               Jackie Rogoff
#
# Copyright:    (c) 2009 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import unittest, doctest

import music21

from music21 import interval
from music21 import common

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
    unison = interval.Interval("P1")
    fifth  = interval.Interval("P5")
    octave = interval.Interval("P8")
        
    def __init__(self, v1n1 = None, v1n2 = None, v2n1 = None, v2n2 = None):
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
        '''Returns true if no voice moves at this "voice-leading" moment


        >>> from music21 import *
        >>> n1 = note.Note('G4')
        >>> n2 = note.Note('G4')
        >>> m1 = note.Note('G4')
        >>> m2 = note.Note('G4')
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.noMotion()
        True
        >>> n2.octave = 5
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.noMotion()
        False

        '''
        for iV in self.hIntervals:
            if iV.name != "P1": 
                return False
        return True

    def obliqueMotion(self):
        '''
        Returns true if one voice remains the same and another moves.  I.e.,
        noMotion must be False if obliqueMotion is True.


        >>> from music21 import *
        >>> n1 = note.Note('G4')
        >>> n2 = note.Note('G4')
        >>> m1 = note.Note('G4')
        >>> m2 = note.Note('G4')
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.obliqueMotion()
        False
        >>> n2.octave = 5
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.obliqueMotion()
        True
        >>> m2.octave = 5
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.obliqueMotion()
        False
        
        '''
        if self.noMotion():
            return False
        else:
            iNames = [self.hIntervals[0].name, self.hIntervals[1].name]
            if "P1" not in iNames: 
                return False
            else:
                return True
    
    
    def similarMotion(self):
        '''
        Returns true if the two voices both move in the same direction.
        Parallel Motion will also return true, as it is a special case of
        similar motion. If there is no motion, returns False.


        >>> from music21 import *
        >>> n1 = note.Note('G4')
        >>> n2 = note.Note('G4')
        >>> m1 = note.Note('G4')
        >>> m2 = note.Note('G4')
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.similarMotion()
        False
        >>> n2.octave = 5
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.similarMotion()
        False
        >>> m2.octave = 5
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.similarMotion()
        True
        >>> m2 = note.Note('A5')
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.similarMotion()
        True
        
        '''
        
        if self.noMotion():
            return False
        else:
            if self.hIntervals[0].direction == self.hIntervals[1].direction:
                return True
            else:
                return False
 
    def parallelMotion(self, requiredInterval = None):
        '''returns True if both voices move with the same interval or an
        octave duplicate of the interval.  if requiredInterval is given
        then returns True only if the parallel interval is that simple interval.
        

        >>> from music21 import *
        >>> n1 = note.Note('G4')
        >>> n2 = note.Note('G4')
        >>> m1 = note.Note('G4')
        >>> m2 = note.Note('G4')
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.parallelMotion() #no motion, so oblique motion will give False
        False
        >>> n2.octave = 5
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.parallelMotion()
        False
        >>> m2.octave = 5
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.parallelMotion()
        True
        >>> vl.parallelMotion('P8')
        True
        >>> vl.parallelMotion('M6')
        False
        
        >>> m2 = note.Note('A5')
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.parallelMotion()
        False

        '''
        if not self.similarMotion():
            return False
        elif self.vIntervals[0].directedSimpleName != self.vIntervals[1].directedSimpleName:
            return False
        else:
            if requiredInterval is None:
                return True
            else:
                if common.isStr(requiredInterval):
                    requiredInterval = interval.Interval(requiredInterval)

                if self.vIntervals[0].simpleName == requiredInterval.simpleName:
                    return True
                else:
                    return False                
    
    def contraryMotion(self):
        '''
        returns True if both voices move in opposite directions


        >>> from music21 import *
        >>> n1 = note.Note('G4')
        >>> n2 = note.Note('G4')
        >>> m1 = note.Note('G4')
        >>> m2 = note.Note('G4')
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.contraryMotion() #no motion, so oblique motion will give False
        False
        >>> n2.octave = 5
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.contraryMotion()
        False
        >>> m2.octave = 5
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.contraryMotion()
        False
        >>> m2 = note.Note('A5')
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.contraryMotion()
        False
        >>> m2 = note.Note('C4')
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.contraryMotion()
        True
        
        '''
        
        if self.noMotion():
            return False
        elif self.obliqueMotion():
            return False
        else:
            if self.hIntervals[0].direction == self.hIntervals[1].direction:
                return False
            else:
                return True
 
    def antiParallelMotion(self, simpleName = None):
        '''
        Returns true if the simple interval before is the same as the simple
        interval after and the motion is contrary. if simpleName is
        specified as an Interval object or a string then it only returns
        true if the simpleName of both intervals is the same as simpleName
        (i.e., use to find antiParallel fifths) 

        >>> from music21 import *
        >>> n11 = note.Note("C4")
        >>> n12 = note.Note("D3") # descending 7th
        >>> n21 = note.Note("G4")
        >>> n22 = note.Note("A4") # ascending 2nd
        >>> vlq1 = voiceLeading.VoiceLeadingQuartet(n11, n12, n21, n22)
        >>> vlq1.antiParallelMotion()
        True
        >>> vlq1.antiParallelMotion('M2')
        False
        >>> vlq1.antiParallelMotion('P5')
        True
        
        We can also use interval objects
        >>> p5Obj = interval.Interval("P5")
        >>> p8Obj = interval.Interval('P8')
        >>> vlq1.antiParallelMotion(p5Obj)
        True
        >>> p8Obj = interval.Interval('P8')
        >>> vlq1.antiParallelMotion(p8Obj)
        False

        >>> n1 = note.Note('G4')
        >>> n2 = note.Note('G4')
        >>> m1 = note.Note('G4')
        >>> m2 = note.Note('G3')
        >>> vl2 = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl2.antiParallelMotion()
        False
        '''
        if not self.contraryMotion():
            return False
        else:
            if self.vIntervals[0].simpleName == self.vIntervals[1].simpleName:
                if simpleName is None:
                    return True
                else:
                    if common.isStr(simpleName):
                        if self.vIntervals[0].simpleName == simpleName:
                            return True
                        else:
                            return False
                    else: # assume Interval object
                        if self.vIntervals[0].simpleName == simpleName.simpleName:
                            return True
                        else:
                            return False
            else:
                return False

 
    def parallelInterval(self, thisInterval):
        '''
        Returns true if there is a parallel or antiParallel interval of
        this type (thisInterval should be an Interval object)
        
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
        common practice counterpoint rules. Takes thisInterval,
        an Interval object.


        >>> from music21 import *
        >>> n1 = note.Note('C4')
        >>> n2 = note.Note('G4')
        >>> m1 = note.Note('B4')
        >>> m2 = note.Note('D5')
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.hiddenInterval(Interval('P5'))
        True
        >>> n1 = note.Note('E4')
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.hiddenInterval(Interval('P5'))
        False
        >>> m2.octave = 6
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.hiddenInterval(Interval('P5'))
        False
        
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
    
    def voiceCrossing(self):
        '''
        >>> from music21 import *
        >>> v1n1 = pitch.Pitch('C3')
        >>> v1n2 = pitch.Pitch('F3')
        >>> v2n1 = pitch.Pitch('E3')
        >>> v2n2 = pitch.Pitch('G3')
        >>> vlq = VoiceLeadingQuartet(v1n1, v1n2, v2n1, v2n2)
        >>> vlq.voiceCrossing()
        True
        '''
        isCrossing = False
        if (self.v1n2.ps >= self.v2n1.ps) or (self.v1n1.ps >= self.v2n2.ps):
            isCrossing = True
        return isCrossing

class VoiceLeadingException(Exception):
    pass





#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass
 

    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
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
        assert a.parallelInterval(interval.Interval("P5")) == True
        assert a.parallelInterval(interval.Interval("M3")) == False
    
        b = VoiceLeadingQuartet(C4, C4, G4, G4)
        assert b.noMotion() == True
        assert b.parallelMotion() == False
        assert b.antiParallelMotion() == False
        assert b.obliqueMotion() == False
            
        c = VoiceLeadingQuartet(C4, G4, C5, G4)
        assert c.antiParallelMotion() == True
        assert c.hiddenInterval(interval.Interval("P5")) == False
    
        d = VoiceLeadingQuartet(C4, D4, E4, A4)
        assert d.hiddenInterval(Interval("P5")) == True
        assert d.hiddenInterval(Interval("A4")) == False
        assert d.hiddenInterval(Interval("AA4")) == False

if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof

