
import unittest, doctest

import music21
from music21.note import Note
from music21 import interval


class VoiceLeadingQuartet(music21.Music21Object):
    '''A quartet of four pitches: v1n1, v1n2, v2n1, v2n2
    where v1n1 moves to v1n2 at the same time as 
    v2n1 moves to v2n2.  
    
    Necessary for classifying types of voice-leading motion
    '''
    
    motionType = None
    unison = interval.generateIntervalFromString("P1")
    fifth = interval.generateIntervalFromString("P5")
    octave = interval.generateIntervalFromString("P8")
        
    def __init__(self, v1n1, v1n2, v2n1, v2n2):
        self.v1n1 = v1n1
        self.v1n2 = v1n2
        self.v2n1 = v2n1
        self.v2n2 = v2n2    
        self.vIntervals = []
        self.hIntervals = []
        self.findIntervals()
    
    def findIntervals(self):
        self.vIntervals.append(interval.generateInterval(self.v1n1, self.v2n1))
        self.vIntervals.append(interval.generateInterval(self.v1n2, self.v2n2))
        self.hIntervals.append(interval.generateInterval(self.v1n1, self.v1n2))
        self.hIntervals.append(interval.generateInterval(self.v2n1, self.v2n2))
    
    def noMotion(self):
        '''Returns true if no voice moves at this "voice-leading" moment'''
        for iV in self.hIntervals:
            if iV.name != "P1": 
                return False
        return True

    def obliqueMotion(self):
        '''Returns true if one voice remains the same and another moves.  I.e., isNoMotion 
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
        if self.noMotion():
            return False
        else:
            if self.hIntervals[0].direction == self.hIntervals[1].direction:
                return True
            else:
                return False
 
    def parallelMotion(self):
        '''returns true if both voices move with the same interval or an octave duplicate of the interval'''
        if not self.similarMotion():
            return False
        else:
            if self.vIntervals[0].directedSimpleName == self.vIntervals[1].directedSimpleName:
                return True
    
    def contraryMotion(self):
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
        if not self.contraryMotion():
            return False
        else:
            if self.vIntervals[0].simpleName == self.vIntervals[1].simpleName:
                return True
            else:
                return False

 
    def parallelInterval(self, thisInterval):
        '''
        parrallelInterval traps both parallelMotion and antiParallelMotion
        '''
        
        if not (self.parallelMotion() or self.antiParallelMotion()):
            return False
        else:
            if self.vIntervals[0].semiSimpleName == thisInterval.semiSimpleName:
                return True
            else:
                return False

    def parallelFifth(self):
        return self.parallelInterval(self.fifth)
    
    def parallelOctave(self):
        return self.parallelInterval(self.octave)
    
    def parallelUnison(self):
        return self.parallelInterval(self.unison)
    
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

###### test routines
class Test(unittest.TestCase):

    def runTest(self):
        pass
    
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
        assert a.parallelInterval(interval.generateIntervalFromString("P5")) == True
        assert a.parallelInterval(interval.generateIntervalFromString("M3")) == False
    
        b = VoiceLeadingQuartet(C4, C4, G4, G4)
        assert b.noMotion() == True
        assert b.parallelMotion() == False
        assert b.antiParallelMotion() == False
        assert b.obliqueMotion() == False
            
        c = VoiceLeadingQuartet(C4, G4, C5, G4)
        assert c.antiParallelMotion() == True
        assert c.hiddenInterval(interval.generateIntervalFromString("P5")) == False
    
        d = VoiceLeadingQuartet(C4, D4, E4, A4)
        assert d.hiddenInterval(interval.generateIntervalFromString("P5")) == True
        assert d.hiddenInterval(interval.generateIntervalFromString("A4")) == False
        assert d.hiddenInterval(interval.generateIntervalFromString("AA4")) == False

if __name__ == "__main__":
    music21.mainTest(Test)