# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         voiceLeading.py
# Purpose:      music21 classes for voice leading
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#               Jackie Rogoff
#               Beth Hadley
#
# Copyright:    (c) 2009 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import unittest, doctest

import music21

from music21 import interval
from music21 import common
from music21 import pitch
from music21.note import Note
from music21.interval import Interval
from music21 import key

#TODO: rename VoiceLeadingQuartet -> Pairwise
#TODO: add chordwise -- add parsimonious (all move by step or not at all)

#-------------------------------------------------------------------------------
class VoiceLeadingQuartet(music21.Music21Object):
    '''
    An object consisting of four pitches: v1n1, v1n2, v2n1, v2n2
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
        self.vIntervals = [] #vertical intervals (harmonic)
        self.hIntervals = [] #horizontal intervals (melodic)
        if v1n1 is not None and v1n2 is not None and v2n1 is not None and v2n2 is not None:
            self._findIntervals()
    
    def _findIntervals(self):
        self.vIntervals.append(interval.notesToInterval(self.v1n1, self.v2n1))
        self.vIntervals.append(interval.notesToInterval(self.v1n2, self.v2n2))
        self.hIntervals.append(interval.notesToInterval(self.v1n1, self.v1n2))
        self.hIntervals.append(interval.notesToInterval(self.v2n1, self.v2n2))
    
    def noMotion(self):
        '''
        Returns true if no voice moves at this "voice-leading" moment


        >>> from music21 import *
        >>> n1 = note.Note('G4')
        >>> n2 = note.Note('G4')
        >>> m1 = note.Note('D4')
        >>> m2 = note.Note('D4')
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
        >>> m1 = note.Note('D4')
        >>> m2 = note.Note('D4')
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
        '''
        returns True if both voices move with the same interval or an
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
 
    def outwardContraryMotion(self):
        '''
        Returns true if both voices move outward by contrary motion
        
        >>> from music21 import *
        >>> n1 = note.Note('D5')
        >>> n2 = note.Note('E5')
        >>> m1 = note.Note('G4')
        >>> m2 = note.Note('F4')
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.outwardContraryMotion()
        True
        >>> vl.inwardContraryMotion()
        False
        '''
        return self.contraryMotion() and self.hIntervals[0].direction == 1
 
    def inwardContraryMotion(self):
        '''
        Returns true if both voices move inward by contrary motion
        
        >>> from music21 import *
        >>> n1 = note.Note('C5')
        >>> n2 = note.Note('B4')
        >>> m1 = note.Note('G4')
        >>> m2 = note.Note('A4')
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.inwardContraryMotion()
        True
        >>> vl.outwardContraryMotion()
        False
        '''
        return self.contraryMotion() and self.hIntervals[0].direction == -1
 
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
        Returns true if there is a parallel motion or antiParallel motion of
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
    
    def resolvesCorrectly(self, music21KeyObj=key.KeySignature('C')):
        '''
        checks whether the voice-leading quartet resolves correctly according to standard
        counterpoint rules. If the first harmony is dissonant (d5, A4, or m7) it checks
        that these are correctly resolved. If the first harmony is consonant, True is returned.
        
        The key parameter should be specified to check for motion in the bass from specific
        note degrees. Default key is C Major.
        
        Diminished Fifth: in by contrary motion to a third, with 7 resolving up to 1 in the bass
        Augmented Fourth: out by contrary motion to a sixth, with chordal seventh resolving 
        down to a third in the bass.
        Minor Seventh: In to a third with a leap form 5 to 1 in the bass
        
        >>> from music21 import *
        >>> n1 = note.Note('B-4')
        >>> n2 = note.Note('A4')
        >>> m1 = note.Note('E4')
        >>> m2 = note.Note('F4')
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.resolvesCorrectly(key.Key('F')) #d5
        True
        
        >>> n1 = note.Note('E5')
        >>> n2 = note.Note('F5')
        >>> m1 = note.Note('B-4')
        >>> m2 = note.Note('A4')
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.resolvesCorrectly(key.Key('F')) #A4
        True
        
        >>> n1 = note.Note('B-4')
        >>> n2 = note.Note('A4')
        >>> m1 = note.Note('C4')
        >>> m2 = note.Note('F4')
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.resolvesCorrectly(key.Key('F')) #m7
        True        
        
        >>> n1 = note.Note('C4')
        >>> n2 = note.Note('D4')
        >>> m1 = note.Note('F4')
        >>> m2 = note.Note('G4')
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.resolvesCorrectly(key.Key('C')) #not dissonant, true returned
        True 
        '''
        scale = music21KeyObj.getScale()
         
        if self.vIntervals[0].simpleName == 'd5':
            return scale.getScaleDegreeFromPitch(self.v2n1) == 7 and \
            scale.getScaleDegreeFromPitch(self.v2n2) == 1 and \
            self.inwardContraryMotion() and self.vIntervals[1].generic.undirected == 3

        elif self.vIntervals[0].simpleName == 'A4':
            return scale.getScaleDegreeFromPitch(self.v2n1) == 4 and \
            scale.getScaleDegreeFromPitch(self.v2n2) == 3 and \
            self.outwardContraryMotion() and self.vIntervals[1].generic.undirected == 6
            
        elif self.vIntervals[0].simpleName == 'm7':
            return scale.getScaleDegreeFromPitch(self.v2n1) == 5 and \
            scale.getScaleDegreeFromPitch(self.v2n2) == 1 and \
            self.inwardContraryMotion() and self.vIntervals[1].generic.undirected == 3
        else:
            return True
           
class VoiceLeadingException(Exception):
    pass

class ThreeNoteLinearSegmentException(music21.Music21Exception):
    pass

class ThreeNoteLinearSegment(music21.Music21Object):
    '''
    An object consisting of three sequential pitches,
    leftPitch --> pitchToAnalyze --> rightPitch
    
    The middle tone in a ThreeNoteLinearSegment can
    be classified using methods enclosed in this class
    to identify it as types of embellishing tones. Further
    methods can be used on the entire stream to identify these
    as non-harmonic.
    
    Accepts a sequence of strings, pitches, or notes.
    
    >>> from music21 import *
    >>> ex = voiceLeading.ThreeNoteLinearSegment('C#4','D4','E-4')
    >>> ex.leftPitch
    C#4
    >>> ex.pitchToAnalyze
    D4
    >>> ex.rightPitch
    E-4
    
    >>> ex = voiceLeading.ThreeNoteLinearSegment(pitch.Pitch('A4'),note.Note('D4'),'F5')
    >>> ex.leftPitch
    A4
    >>> ex.pitchToAnalyze
    D4
    >>> ex.rightPitch
    F5
    
    if no octave specified, default octave of 4 is assumed
    
    >>> ex = voiceLeading.ThreeNoteLinearSegment('a','b','c')
    >>> ex.leftPitch
    A
    >>> ex.leftPitch.defaultOctave
    4
    
    OMIT_FROM_DOCS
    
    >>> ex.pitchToAnalyze.defaultOctave
    4
    >>> ex.rightPitch.defaultOctave
    4

    >>> ex = voiceLeading.ThreeNoteLinearSegment(note.Note('D4'),note.Note('E4'),note.Note('F4'))
    >>> ex.leftPitch
    D4
    >>> ex.pitchToAnalyze
    E4
    >>> ex.rightPitch
    F4
    
    >>> ex = voiceLeading.ThreeNoteLinearSegment(pitch.Pitch('A4'),pitch.Pitch('B4'),pitch.Pitch('C5'))
    >>> ex.leftPitch
    A4
    >>> ex.pitchToAnalyze
    B4
    >>> ex.rightPitch
    C5
    
    '''

    def __init__(self, leftPitch=None, pitchToAnalyze=None, rightPitch=None):
        self._leftPitch = None
        self._pitchToAnalyze = None
        self._rightPitch = None
        
        #storage location for the intervals between the pitches
        self.iLeftToRight = None #interval between the left pitch and right pitch
        self.iLeft = None #interval between the left pitch and the pitchToAnalyze
        self.iRight = None #interval between the pitch to Analyze and the right pitch
        
        if leftPitch != None:
            self.leftPitch = leftPitch

        if pitchToAnalyze != None:
            self.pitchToAnalyze = pitchToAnalyze

        if rightPitch != None:
            self.rightPitch = rightPitch

    def _calcIntervals(self):
        #updated every time the leftPitch, pitchToAnalyze, or rightPitch is set (or reset)
        if self.leftPitch != None and self.rightPitch != None:
            self.iLeftToRight = music21.interval.Interval(self.leftPitch, self.rightPitch)
        if self.leftPitch != None and self.pitchToAnalyze != None:
            self.iLeft = music21.interval.Interval(self.leftPitch, self.pitchToAnalyze)
        if self.pitchToAnalyze != None and self.rightPitch != None:
            self.iRight = music21.interval.Interval(self.pitchToAnalyze, self.rightPitch)
    
    def _setleftPitch(self, value):
        if hasattr(value, 'classes') and 'Pitch' in value.classes:
            self._leftPitch = value
            self._calcIntervals()
            return
        elif hasattr(value, 'classes') and 'Note' in value.classes:
            self._leftPitch = value.pitch
            self._calcIntervals()
            return
        try: # try to create a Pitch object
            self._leftPitch = pitch.Pitch(value)
            self._calcIntervals()
            return
        except music21.Music21Exception: 
            pass
        raise ThreeNoteLinearSegmentException('not a valid pitch specification: %s' % value)

    def _getleftPitch(self):
        return self._leftPitch

    leftPitch = property(_getleftPitch, _setleftPitch, doc = '''
        >>> from music21 import *
        >>> h = voiceLeading.ThreeNoteLinearSegment()
        >>> h.leftPitch = 'a3'
        >>> h.leftPitch
        A3
        >>> h.leftPitch = note.Note('A3')
        >>> h.leftPitch
        A3
        >>> h.leftPitch = pitch.Pitch('A')
        >>> h.leftPitch
        A
    
        ''')
    
    
    def _setpitchToAnalyze(self, value):
        if hasattr(value, 'classes') and 'Pitch' in value.classes:
            self._pitchToAnalyze = value
            self._calcIntervals()
            return
        elif hasattr(value, 'classes') and 'Note' in value.classes:
            self._pitchToAnalyze = value.pitch
            self._calcIntervals()
            return
        try: # try to create a Pitch object
            self._pitchToAnalyze = pitch.Pitch(value)
            self._calcIntervals()
            return
        except music21.Music21Exception: 
            pass
        raise ThreeNoteLinearSegmentException('not a valid pitch specification: %s' % value)

    def _getpitchToAnalyze(self):
        return self._pitchToAnalyze

    pitchToAnalyze = property(_getpitchToAnalyze, _setpitchToAnalyze, doc = '''
        >>> from music21 import *
        >>> h = voiceLeading.ThreeNoteLinearSegment()
        >>> h.pitchToAnalyze = 'b3'
        >>> h.pitchToAnalyze
        B3
        >>> h.pitchToAnalyze = note.Note('b3')
        >>> h.pitchToAnalyze
        B3
        >>> h.pitchToAnalyze = pitch.Pitch('b')
        >>> h.pitchToAnalyze
        B
    
        ''')
    
    def _setrightPitch(self, value):
        if hasattr(value, 'classes') and 'Pitch' in value.classes:
            self._rightPitch = value
            self._calcIntervals()
            return
        elif hasattr(value, 'classes') and 'Note' in value.classes:
            self._rightPitch = value.pitch
            self._calcIntervals()
            return
        try: # try to create a Pitch object
            self._rightPitch = pitch.Pitch(value)
            self._calcIntervals()
            return
        except music21.Music21Exception: 
            pass
        raise ThreeNoteLinearSegmentException('not a valid pitch specification: %s' % value)

    def _getrightPitch(self):
        return self._rightPitch

    rightPitch = property(_getrightPitch, _setrightPitch, doc = '''
        >>> from music21 import *
        >>> h = voiceLeading.ThreeNoteLinearSegment()
        >>> h.rightPitch = 'C4'
        >>> h.rightPitch
        C4
        >>> h.rightPitch = note.Note('c4')
        >>> h.rightPitch
        C4
        >>> h.rightPitch = pitch.Pitch('C')
        >>> h.rightPitch
        C
        >>> h.rightPitch.defaultOctave
        4
    
        ''')
    
    def couldBePassingTone(self):
        '''
        checks if the two intervals are steps and if these steps
        are moving in the same direction. Returns true if the tone is
        identified as either a chromatic passing tone or a diatonic passing
        tone. Only major and minor diatonic passing tones are recognized (not 
        pentatonic or scales beyond twelve-notes). Does NOT check if tone is non harmonic
        
        Accepts pitch or note objects; method is dependent on octave information
        
        >>> from music21 import *
        >>> voiceLeading.ThreeNoteLinearSegment('C#4','D4','E-4').couldBePassingTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('C3','D3','E3').couldBePassingTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('E-3','F3','G-3').couldBePassingTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('C3','C3','C3').couldBePassingTone()
        False
        >>> voiceLeading.ThreeNoteLinearSegment('A3','C3','D3').couldBePassingTone()
        False
        
        Directionality must be maintained
        
        >>> voiceLeading.ThreeNoteLinearSegment('B##3','C4','D--4').couldBePassingTone()
        False
       
        If no octave is given then ._defaultOctave is used.  This is generally octave 4
        
        >>> voiceLeading.ThreeNoteLinearSegment('C','D','E').couldBePassingTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('C4','D','E').couldBePassingTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('C5','D','E').couldBePassingTone()
        False
        
        Method returns true if either a chromatic passing tone or a diatonic passing
        tone is identified. Spelling of the pitch does matter!
        
        >>> voiceLeading.ThreeNoteLinearSegment('B3','C4','B##3').couldBePassingTone()
        False
        >>> voiceLeading.ThreeNoteLinearSegment('A##3','C4','E---4').couldBePassingTone()
        False
        >>> voiceLeading.ThreeNoteLinearSegment('B3','C4','D-4').couldBePassingTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('B3','C4','C#4').couldBePassingTone()
        True
        '''
    
        return self.couldBeDiatonicPassingTone() or self.couldBeChromaticPassingTone()
    
    def couldBeDiatonicPassingTone(self):
        '''
        A note could be a diatonic passing tone (and therefore a passing tone in general) 
        if the generic interval between the previous and the current is 2 or -2; 
        same for the next; and both move in the same direction 
        (that is, the two intervals multiplied by each other are 4, not -4).
        
        >>> from music21 import *
        >>> voiceLeading.ThreeNoteLinearSegment('B3','C4','C#4').couldBeDiatonicPassingTone()
        False
        >>> voiceLeading.ThreeNoteLinearSegment('C3','D3','E3').couldBeDiatonicPassingTone()
        True
        '''
        return self.iLeftToRight.generic.isSkip and \
            self.iLeft.generic.undirected == 2 and self.iRight.generic.undirected == 2 and \
            self.iLeft.generic.undirected * self.iRight.generic.undirected == 4 and \
            (self.iLeft.direction * self.iRight.direction == 1)
        
        
    def couldBeChromaticPassingTone(self):
        '''
        A note could a chromatic passing tone (and therefore a passing tone in general) 
        if the generic interval between the previous and the current is -2, 1, or 2; 
        the generic interval between the current and next is -2, 1, 2; the two generic 
        intervals multiply to -2 or 2 (if 4 then it's a diatonic interval; if 1 then 
        not a passing tone; i.e, C -> C# -> C## is not a chromatic passing tone); 
        AND between each of the notes there is a chromatic interval of 1 or -1 and 
        multiplied together it is 1. (i.e.: C -> D-- -> D- is not a chromatic passing tone).
        
        >>> from music21 import *
        >>> voiceLeading.ThreeNoteLinearSegment('B3','C4','C#4').couldBeChromaticPassingTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('B3','C4','C#4').couldBeChromaticPassingTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('B3','B#3','C#4').couldBeChromaticPassingTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('B3','D-4','C#4').couldBeChromaticPassingTone()
        False
        >>> voiceLeading.ThreeNoteLinearSegment('B3','C##4','C#4').couldBeChromaticPassingTone()
        False
        >>> voiceLeading.ThreeNoteLinearSegment('C#4','C4','C##4').couldBeChromaticPassingTone()
        False
        >>> voiceLeading.ThreeNoteLinearSegment('D--4','C4','D-4').couldBeChromaticPassingTone()
        False
        '''
        
        return (self.iLeft.generic.undirected == 2 or self.iLeft.generic.undirected == 1) and \
            (self.iRight.generic.undirected == 2 or self.iRight.generic.undirected == 1) and \
            self.iLeft.generic.undirected * self.iRight.generic.undirected == 2 and \
            self.iLeft.isChromaticStep and self.iRight.isChromaticStep and \
            self.iLeft.direction * self.iRight.direction == 1
    
    def couldBeNeighborTone(self):
        '''
        checks if noteToAnalyze could be a neighbor tone, either a diatonic neighbor tone
        or a chromatic neighbor tone. Does NOT check if tone is non harmonic
        
        >>> from music21 import *
        >>> voiceLeading.ThreeNoteLinearSegment('E3','F3','E3').couldBeNeighborTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('B-4','C5','B-4').couldBeNeighborTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('B4','C5','B4').couldBeNeighborTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('G4','F#4','G4').couldBeNeighborTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('E-3','F3','E-4').couldBeNeighborTone()
        False
        >>> voiceLeading.ThreeNoteLinearSegment('C3','D3','E3').couldBeNeighborTone()
        False
        >>> voiceLeading.ThreeNoteLinearSegment('A3','C3','D3').couldBeNeighborTone()
        False
        '''
        
        return self.couldBeDiatonicNeighborTone() or self.couldBeChromaticNeighborTone()
        

    def couldBeDiatonicNeighborTone(self):
        '''
        returns true if and only if noteToAnalyze could be a diatonic neighbor tone
        
        >>> from music21 import *
        >>> voiceLeading.ThreeNoteLinearSegment('C3','D3','C3').couldBeDiatonicNeighborTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('C3','C#3','C3').couldBeDiatonicNeighborTone()
        False
        >>> voiceLeading.ThreeNoteLinearSegment('C3','D-3','C3').couldBeDiatonicNeighborTone()
        False
        '''
        return self.leftPitch.nameWithOctave == self.rightPitch.nameWithOctave and \
            self.iLeft.chromatic.undirected == 2 and self.iRight.chromatic.undirected == 2 and \
            (self.iLeft.direction * self.iRight.direction == -1)
        
    def couldBeChromaticNeighborTone(self):
        '''
        returns true if and only if noteToAnalyze could be a chromatic neighbor tone
        
        >>> from music21 import *
        >>> voiceLeading.ThreeNoteLinearSegment('C3','D3','C3').couldBeChromaticNeighborTone()
        False
        >>> voiceLeading.ThreeNoteLinearSegment('C3','D-3','C3').couldBeChromaticNeighborTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('C#3','D3','C#3').couldBeChromaticNeighborTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('C#3','D3','D-3').couldBeChromaticNeighborTone()
        False
        '''
        return self.leftPitch.nameWithOctave == self.rightPitch.nameWithOctave and \
            self.iLeft.isChromaticStep and self.iRight.isChromaticStep and \
            (self.iLeft.direction * self.iRight.direction == -1)

def labelPassingTones(music21Stream, checkForDissonance=True, checkSimultaneous=True, checkForAccent=True, markWithColor=False, color='#FF0000'):
    '''
    searches through all voices of all parts in a given music21 stream and
    identifies passing tones, then assigns a True/False value to the 
    note's :class:`~music21.editorial.NoteEditorial` object. The information is 
    stored as a miscellaneous attribute in the note editorial object, called 'isPassingTone'. 
    Access this data from any note object in the stream after running this method by typing

    for note in labeledStream.flat.getElementsByClass(music21.note.Note):
    print note.editorial.misc['isPassingTone']
    
    Selectivity in labeling is provided by the following optional arguments:
    checkForDissonance (default = True) --> checks if the chord formed is dissonant, and only
    labels tone as a passing tone if the chord is dissonant.
    
    checkSimultaneous (default = True) --> iterates through every instance where simultaneous notes
    are labeled (with color) and if their durations are different, labels only the tone that has a shorter duration
    
    checkForAccent (default = True) --> only labels passing tones on unaccented beats of the measure
    
    markWithColor (default = False) --> optionally label the identified passing tones with a color; default
    color is red. Change labeling color with color modifier/
    
    color (default = '#00FF00') --> color to label notes if markWithColor is True. Colors must be specified
    in a string HEX. For example, 
    color = '#FF0000' (red)
    color = '#00FF00' (green)
    color = '#0000FF' (blue)
    color = '#FFFF00' (yellow)
    color = '#00FFFF' (turquoise)
    color = '#FF00FF' (magenta)
    color = '#C0C0C0' (grey)
    color = '#FFFFFF' (white)
    
    '''

    for part in music21Stream.parts:
        notes = part.flat.getElementsByClass(music21.note.Note)
        index = 0
        for note in notes[1:len(notes) - 1]:
            index = index + 1
            if ThreeNoteLinearSegment(notes[index - 1], note, notes[index + 1]).couldBePassingTone():
                listOfTruths = []
                if checkForDissonance:
                    listOfTruths.append(not _noteContextIsConsonant(note, music21Stream))
                if checkForAccent:
                    listOfTruths.append(_beatIsUnaccented(note))
                if not (False in listOfTruths):
                    note.editorial.misc['isPassingTone'] = True
                    if markWithColor:
                        note.color = color
                else:
                    note.editorial.misc['isPassingTone'] = False
            else:
                note.editorial.misc['isPassingTone'] = False
                    
        notes[0].editorial.misc['isPassingTone'] = False
        notes[len(notes)-1].editorial.misc['isPassingTone'] = False
        
    if checkSimultaneous:
        music21Stream = _checkForSimultaneousLabels(music21Stream, markWithColor)
    return music21Stream
    
def labelNeighborTones(music21Stream, checkForDissonance=True, checkSimultaneous=True, checkForAccent=True, markWithColor=False, color='#00FF00'):
    '''
    searches through all voices of all parts in a given music21 stream and
    identifies neighbor tones, then assigns a True/False value to the 
    note's :class:`~music21.editorial.NoteEditorial` object. The information is 
    stored as a miscellaneous attribute in the note editorial object, called 'isPassingTone'. 
    Access this data from any note object in the stream after running this method by typing

    for note in labeledStream.flat.getElementsByClass(music21.note.Note):
    print note.editorial.misc['isNeighborTone']
    
    Selectivity in labeling is provided by the following optional arguments:
    checkForDissonance (default = True) --> checks if the chord formed is dissonant, and only
    labels tone as a passing tone if the chord is dissonant.
    
    checkSimultaneous (default = True) --> iterates through every instance where simultaneous notes
    are labeled (with color) and if their durations are different, labels only the tone that has a shorter duration
    
    checkForAccent (default = True) --> only labels passing tones on unacented beats of the measure
    
    markWithColor (default = False) --> optionally label the identified neighbor tones with a color; default
    color is green. Change labeling color with color modifier/
    
    color (default = '#00FF00') --> color to label notes if markWithColor is True. Colors must be specified
    in a string HEX. 
    For example, 
    color = '#FF0000' (red)
    color = '#00FF00' (green)
    color = '#0000FF' (blue)
    color = '#FFFF00' (yellow)
    color = '#00FFFF' (turquoise)
    color = '#FF00FF' (magenta)
    color = '#C0C0C0' (grey)
    color = '#FFFFFF' (white)
    
    '''
    for part in music21Stream.parts:
        notes = part.flat.getElementsByClass(music21.note.Note)
        index = 0
        for note in notes[1:len(notes) - 1]:
            index = index + 1
            if ThreeNoteLinearSegment(notes[index - 1], note, notes[index + 1]).couldBeNeighborTone():
                listOfTruths = []
                if checkForDissonance:
                    listOfTruths.append(not _noteContextIsConsonant(note, music21Stream))
                if checkForAccent:
                    listOfTruths.append(_beatIsUnaccented(note))
                if not (False in listOfTruths):
                    note.editorial.misc['isNeighborTone'] = True
                    if markWithColor:
                        note.color = color
                else:
                    note.editorial.misc['isNeighborTone'] = False
            else:
                note.editorial.misc['isNeighborTone'] = False         
        notes[0].editorial.misc['isNeighborTone'] = False
        notes[len(notes)-1].editorial.misc['isNeighborTone'] = False
    if checkSimultaneous:
        music21Stream = _checkForSimultaneousLabels(music21Stream, markWithColor)
    return music21Stream
    
def _checkForSimultaneousLabels(preLabeledMusic21Stream, checkPT=True, checkNT=True, markWithColor=False, color='#000000'):
    '''
    If after running a non-harmonic labeling method (such as labelPassingTones or labelNeighborTones)
    you find that there are simultaneous pitches labeled when at least one of those pitches must
    not be labeled, run this method to sort out which has the shorter duration, and this one remains
    labeled while the other one becomes unlabeled. Optionally label with colors (as in with label passing tones)
    
    This method is run after every label non-harmonic tone method (labelPassingTones and labelNeighborTones)
    
    if markWithColor = True, then the identified non-harmonic tones that are returned to normal status are 
    set back to the default color of black.
    
    Method steps through each part, and checks that part against each of the other parts. This method
    should unlabel all simultaneous sounding like-type non-harmonic tones that have the same duration if a shorter
    duraiton like-type non-harmonic tone is sounding simultaneously. For example, in four voices (SATB)
    if the soprano and alto both have a passing tone labeled but each is a quarter note, and the tenor 
    has a neighbor tone labeled but it is an eighth note, the soprano and alto labels are removed 
    (editorial.misc['isPassingTone'] set to False and their color optionally returned to black. If the bass
    is labeled as a neighbor tone and is simultaneous, there is no consequence because it is not of the same
    'type' of non-harmonic tone.
    
    '''
    partNumberBeingSearched = -1
    while partNumberBeingSearched < len(preLabeledMusic21Stream.parts) - 1:
        partNumberBeingSearched += 1
        for note in preLabeledMusic21Stream.parts[partNumberBeingSearched].flat.getElementsByClass(music21.note.Note):
            try:
                note.editorial.misc['isPassingTone']
            except:
                note.editorial.misc['isPassingTone'] = False
            try:
                note.editorial.misc['isNeighborTone']
            except:
                note.editorial.misc['isNeighborTone'] = False
                  
            if checkPT and note.editorial.misc['isPassingTone'] == True:
                for part in preLabeledMusic21Stream.parts[partNumberBeingSearched:]:
                    for simultaneousNote in part.flat.getElementsByOffset(note.offset).flat.getElementsByClass(music21.note.Note):
                        if simultaneousNote.editorial.misc['isPassingTone'] == True:
                            if simultaneousNote.duration.quarterLength > note.duration.quarterLength:
                                simultaneousNote.editorial.misc['isPassingTone'] = False
                                simultaneousNote.color = color
                            elif simultaneousNote.duration.quarterLength < note.duration.quarterLength:
                                note.color = color
                                note.editorial.misc['isPassingTone'] = False
                            else:
                                pass
            if checkPT and note.editorial.misc['isNeighborTone'] == True:
                for part in preLabeledMusic21Stream.parts[partNumberBeingSearched:]:
                    for simultaneousNote in part.flat.getElementsByOffset(note.offset).flat.getElementsByClass(music21.note.Note):
                        if simultaneousNote.editorial.misc['isNeighborTone'] == True:
                            if simultaneousNote.duration.quarterLength > note.duration.quarterLength:
                                simultaneousNote.editorial.misc['isNeighborTone'] = False
                                simultaneousNote.color = color
                            elif simultaneousNote.duration.quarterLength < note.duration.quarterLength:
                                note.color = color
                                note.editorial.misc['isNeighborTone'] = False
                            else:
                                pass
                                #if the two durations are equal, then how do we know which is the passing tone
                                #and which is the chordal tone???
    
    return preLabeledMusic21Stream

#METHOD UNDER REVISION...
#getVerticalSlice() should be able to operate directly on a stream...    
def _noteContextIsConsonant(note, music21Stream):
    #WRITE TESTS
    
    #music21Score
    #isClass or subclass
    #harmonicContext
    #be able to pass in any object with an offset in a stream
    #could be a spanner
    #contextSearch (getContextByClass)
    
    '''
    determines if the given note is a non-harmonic tone due to the context around the note,
    specifically the pitches sounding simultaneously in all voices while the note sounds.
    If the chord formed by these simultaneous pitches in consonant, False is returned. 
    If the chord formed is consonant, true is returned
    
    Consonance is determined by making a chord of the simultaneous pitches, 
    then calling chord's isConsonant() on that chord.
    

    '''
    pitches = []
    #hypothetically (and in actuality if used correctly), note.offset should be equal to offsetOfPitchToIdentify
    offsetOfPitchToIdentify =  note.getOffsetBySite(music21Stream.flat)
#getContextByClass 
    for part in music21Stream.parts: #'Rest'
        value = part.flat.getElementAtOrBefore(offsetOfPitchToIdentify, classList=['Pitch', 'Note', 'Chord', music21.note.Rest])
        if 'Chord' in value.classes:
            value = value.pitches
        if 'Rest' in value.classes:
            pitches.append(value)
    cWithPitch = music21.chord.Chord(pitches)
    return cWithPitch.isConsonant()

#contextSearch in stream

def _beatIsUnaccented(note):
    #only unnacented passing tones are labeled
    try:
        return note.beatStrength < 0.5
    except:
        return False        
    
#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass
 
    def testInstantiateEmptyObject(self):
        '''
        test instantiating an empty VoiceLeadingQuartet
        '''
        vlq = VoiceLeadingQuartet()

    def testCopyAndDeepcopy(self):
        #Test copying all objects defined in this module
        
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

class TestExternal(unittest.TestCase):
    def runTest(self):
        pass
    
    def testThreeNoteLinearSegment(self):
        #s = music21.converter.parse('''\
#C:/Users/bhadley/Dropbox/Music21Theory/WWNortonWorksheets/WWNortonXMLFiles/\
#XML11_worksheets/S11_6_IB.xml''')
        from music21 import corpus
        from music21 import voiceLeading
        from music21 import editorial
        s = corpus.parse('bach/bwv66.6.xml')
        
        s = voiceLeading.labelPassingTones(s, markWithColor=True)
        s = voiceLeading.labelNeighborTones(s, markWithColor=True)
        #s.show()
        #MOST rigorous test below...probably not necessary so commented out for now
        #listOfPassingToneNotes = editorial.getObjectsWithEditorial(s.flat.getElementsByClass(music21.note.Note), "isPassingTone", listOfValues = [True])
        #listOfNeighborToneNotes = editorial.getObjectsWithEditorial(s.flat.getElementsByClass(music21.note.Note), "isNeighborTone", listOfValues = [True])
        #assert len(listOfNeighborToneNotes) == 15
        #assert len(listOfPassingToneNotes) == 45

_DOC_ORDER = [VoiceLeadingQuartet, ThreeNoteLinearSegment, labelPassingTones, labelNeighborTones]

if __name__ == "__main__":
    music21.mainTest(Test)
    


#------------------------------------------------------------------------------
# eof

