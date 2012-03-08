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
from music21 import note
from music21 import chord
from collections import defaultdict
#from music21 import harmony can't do this either
#from music21 import roman Can't import roman because of circular 
#importing issue with counterpoint.py and figuredbass


#-------------------------------------------------------------------------------
class VoiceLeadingQuartet(music21.Music21Object):
    '''
    An object consisting of four pitches: v1n1, v1n2, v2n1, v2n2
    where v1n1 moves to v1n2 at the same time as 
    v2n1 moves to v2n2.  
    
    Necessary for classifying types of voice-leading motion
    '''
    
    unison = interval.Interval("P1")
    fifth  = interval.Interval("P5")
    octave = interval.Interval("P8")
        
    def __init__(self, v1n1 = None, v1n2 = None, v2n1 = None, v2n2 = None, key=key.Key('C')):
        self._v1n1 = None
        self._v1n2 = None
        self._v2n1 = None
        self._v2n2 = None

        self.v1n1 = v1n1
        self.v1n2 = v1n2
        self.v2n1 = v2n1
        self.v2n2 = v2n2
          
        self.vIntervals = [] #vertical intervals (harmonic)
        self.hIntervals = [] #horizontal intervals (melodic)
        
        self._key = key
        if key is not None:
            self.key = key
        if v1n1 is not None and v1n2 is not None and v2n1 is not None and v2n2 is not None:
            self._findIntervals()
    
    
    def _getKey(self):
        return self._key
        
        
    def _setKey(self, keyValue):
        if common.isStr(keyValue):
            try:
                keyValue = key.Key(key.convertKeyStringToMusic21KeyString(keyValue))
            except: 
                raise VoiceLeadingQuartetException('got a key signature string that is not supported: %s', keyValue)                               
        else:
            try:
                keyValue.isClassOrSubclass('Key')
            except:   
                raise VoiceLeadingQuartetException('got a key signature that is not a string or music21 key signature object: %s', keyValue)
        self._key = keyValue
        
    key = property(_getKey, _setKey)
    
    
    
    def _getv1n1(self):
        return self._v1n1

    def _setv1n1(self, value):
        if value == None:
            self._v1n1 = None
        elif common.isStr(value):
            self._v1n1 = note.Note(value)
        else:
            try:
                if value.isClassOrSubclass([note.Note, pitch.Pitch]):
                    self._v1n1 = value
            except:
                raise VoiceLeadingQuartetException('not a valid note specification: %s' % value)

    v1n1 = property(_getv1n1, _setv1n1, doc = '''
        >>> from music21 import *
        >>> vl = VoiceLeadingQuartet('C', 'D', 'E', 'F')
        >>> vl.v1n1    
        <music21.note.Note C>
        ''')
    
    def _getv1n2(self):
        return self._v1n2

    def _setv1n2(self, value):
        if value == None:
            self._v1n2 = None
        elif common.isStr(value):
            self._v1n2 = note.Note(value)
        else:
            try:
                if value.isClassOrSubclass([note.Note, pitch.Pitch]):
                    self._v1n2 = value
            except:
                raise VoiceLeadingQuartetException('not a valid note specification: %s' % value)

    v1n2 = property(_getv1n2, _setv1n2, doc = '''
        >>> from music21 import *
        >>> vl = VoiceLeadingQuartet('C', 'D', 'E', 'F')
        >>> vl.v1n2
        <music21.note.Note D>
    
        ''')
    
    
    def _getv2n1(self):
        return self._v2n1

    def _setv2n1(self, value):
        if value == None:
            self._v2n1 = None
        elif common.isStr(value):
            self._v2n1 = note.Note(value)
        else:
            try:
                if value.isClassOrSubclass([note.Note, pitch.Pitch]):
                    self._v2n1 = value
            except:
                raise VoiceLeadingQuartetException('not a valid note specification: %s' % value)

    v2n1 = property(_getv2n1, _setv2n1, doc = '''
        >>> from music21 import *
        >>> vl = VoiceLeadingQuartet('C', 'D', 'E', 'F')
        >>> vl.v2n1
        <music21.note.Note E>
        ''')
    
    def _getv2n2(self):
        return self._v2n2

    def _setv2n2(self, value):
        if value == None:
            self._v2n2 = None
        elif common.isStr(value):
            self._v2n2 = note.Note(value)
        else:
            try:
                if value.isClassOrSubclass([note.Note, pitch.Pitch]):
                    self._v2n2 = value
            except:
                raise VoiceLeadingQuartetException('not a valid note specification: %s' % value)

    v2n2 = property(_getv2n2, _setv2n2, doc = '''
        >>> from music21 import *
        >>> vl = VoiceLeadingQuartet('C', 'D', 'E', 'F')
        >>> vl.v2n2
        <music21.note.Note F>
        ''')    
    
    def _findIntervals(self):
        self.vIntervals.append(interval.notesToInterval(self.v1n1, self.v2n1))
        self.vIntervals.append(interval.notesToInterval(self.v1n2, self.v2n2))
        self.hIntervals.append(interval.notesToInterval(self.v1n1, self.v1n2))
        self.hIntervals.append(interval.notesToInterval(self.v2n1, self.v2n2))    
    
    def motionType(self):
        '''
        >>> from music21 import *
        >>> n1 = note.Note('D4')
        >>> n2 = note.Note('E4')
        >>> m1 = note.Note('F4')
        >>> m2 = note.Note('B4')
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.motionType()
        'Similar'
        
        >>> n1 = note.Note('A4')
        >>> n2 = note.Note('C5')
        >>> m1 = note.Note('D4')
        >>> m2 = note.Note('F4')
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.motionType()
        'Parallel'
        '''
        motionType = ''
        if self.obliqueMotion():
            motionType = 'Oblique'
        elif self.parallelMotion():
            motionType = 'Parallel'
        elif self.similarMotion():
            motionType = 'Similar'
        elif self.contraryMotion():
            motionType = 'Contrary'
        elif self.antiParallelMotion():
            motionType = 'Anti-Parallel'
        elif self.noMotion():
            motionType = 'No Motion'
        return motionType
            
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
    
    def improperResolution(self):
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
        >>> vl.improperResolution() #d5
        True
        
        >>> n1 = note.Note('E5')
        >>> n2 = note.Note('F5')
        >>> m1 = note.Note('B-4')
        >>> m2 = note.Note('A4')
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.improperResolution() #A4
        True
        
        >>> n1 = note.Note('B-4')
        >>> n2 = note.Note('A4')
        >>> m1 = note.Note('C4')
        >>> m2 = note.Note('F4')
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.improperResolution() #m7
        True        
        
        >>> n1 = note.Note('C4')
        >>> n2 = note.Note('D4')
        >>> m1 = note.Note('F4')
        >>> m2 = note.Note('G4')
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.improperResolution() #not dissonant, true returned
        False 
        
        >>> vl = VoiceLeadingQuartet('B-4', 'A4', 'C2', 'F2')
        >>> vl.key = key.Key('F')
        >>> vl.improperResolution() #not dissonant, true returned
        False 
        
        '''
        if self.noMotion():
            return False

        scale = self.key.getScale()
    
        if self.vIntervals[0].simpleName == 'd5':
            return not (scale.getScaleDegreeFromPitch(self.v2n1) == 7 and \
            scale.getScaleDegreeFromPitch(self.v2n2) == 1 and \
            self.inwardContraryMotion() and self.vIntervals[1].generic.simpleUndirected == 3)

        elif self.vIntervals[0].simpleName == 'A4':
            return not (scale.getScaleDegreeFromPitch(self.v2n1) == 4 and \
            scale.getScaleDegreeFromPitch(self.v2n2) == 3 and \
            self.outwardContraryMotion() and self.vIntervals[1].generic.simpleUndirected == 6)
            
        elif self.vIntervals[0].simpleName == 'm7':
            return not (scale.getScaleDegreeFromPitch(self.v2n1) == 5 and \
            scale.getScaleDegreeFromPitch(self.v2n2) == 1 and \
            self.inwardContraryMotion() and self.vIntervals[1].generic.simpleUndirected == 3)
        else:
            return False
           
    def leapNotSetWithStep(self):
        '''
        returns true if there is a leap or skip in once voice then the other voice must be a step or unison.
        if neither part skips then False is returned. Returns False if the two voices skip thirds in contrary 
        motion.
        
        >>> from music21 import *
        >>> n1 = note.Note('G4')
        >>> n2 = note.Note('C5')
        >>> m1 = note.Note('B3')
        >>> m2 = note.Note('A3')
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.leapNotSetWithStep()
        False
        
        >>> n1 = note.Note('G4')
        >>> n2 = note.Note('C5')
        >>> m1 = note.Note('B3')
        >>> m2 = note.Note('F3')
        >>> vl = VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.leapNotSetWithStep()
        True
        
        >>> vl = VoiceLeadingQuartet('E', 'G', 'G', 'E')
        >>> vl.leapNotSetWithStep()
        False
        '''
        if self.noMotion():
            return False
    
        if self.hIntervals[0].generic.undirected == 3 and self.hIntervals[1].generic.undirected == 3 and self.contraryMotion():
            return False
        
        if self.hIntervals[0].generic.isSkip:
            return not (self.hIntervals[1].generic.isDiatonicStep or self.hIntervals[1].generic.isUnison)
        elif self.hIntervals[1].generic.isSkip:
            return not (self.hIntervals[0].generic.isDiatonicStep or self.hIntervals[0].generic.isUnison)
        else:
            return False
        
    def opensIncorrectly(self):
        '''Returns true if the opening or second harmonic interval is PU, P8, or P5, to accommodate an anacrusis.
        also checks to see if opening establishes tonic or dominant harmony (uses 
        :meth:`~music21.roman.identifyAsTonicOrDominant`
        
        >>> from music21 import *
        >>> vl = VoiceLeadingQuartet('D','D','D','F#')
        >>> vl.key = 'D'
        >>> vl.opensIncorrectly()
        False
        >>> vl = VoiceLeadingQuartet('B','A','G#','A')
        >>> vl.key = 'A'
        >>> vl.opensIncorrectly()
        False
        >>> vl = VoiceLeadingQuartet('A', 'A', 'F#', 'D')
        >>> vl.key = 'A'
        >>> vl.opensIncorrectly()
        False
        
        >>> vl = VoiceLeadingQuartet('C#', 'C#', 'D', 'E')
        >>> vl.key = 'A'
        >>> vl.opensIncorrectly()
        True
        
        >>> vl = VoiceLeadingQuartet('B', 'B', 'A', 'A')
        >>> vl.key = 'C'
        >>> vl.opensIncorrectly()
        True
        '''

        c1 = chord.Chord([self.vIntervals[0].noteStart, self.vIntervals[0].noteEnd])
        c2 = chord.Chord([self.vIntervals[1].noteStart, self.vIntervals[1].noteEnd])
        r1 = music21.roman.identifyAsTonicOrDominant(c1, self.key)
        r2 = music21.roman.identifyAsTonicOrDominant(c2, self.key)
        openings = ['P1','P5', 'I', 'V']
        return not ( ( self.vIntervals[0].simpleName in openings or self.vIntervals[1].simpleName in openings)  and
                       (r1[0].upper() in openings if r1 is not False else False or r2[0].upper() in openings if r2 is not False else False  ) )

    def closesIncorrectly(self):
        '''
        returns true if closing harmonic interval is a P8 or PU and the interval approaching the close is
        6 - 8, 10 - 8, or 3 - U. Must be in contrary motion, and if in minor key, the leading tone resolves to the tonic.
        
        >>> from music21 import *
        >>> vl = VoiceLeadingQuartet('C#', 'D', 'E', 'D')
        >>> vl.key = key.Key('d')
        >>> vl.closesIncorrectly()
        False
        
        >>> vl = VoiceLeadingQuartet('B3', 'C4', 'G3', 'C2')
        >>> vl.key = key.Key('C')
        >>> vl.closesIncorrectly()
        False       
        
        >>> vl = VoiceLeadingQuartet('F', 'G', 'D', 'G')
        >>> vl.key = key.Key('g')
        >>> vl.closesIncorrectly()
        True
        
        >>> vl = VoiceLeadingQuartet('C#4', 'D4', 'A2', 'D3', key='D')
        >>> vl.closesIncorrectly()
        True
        
        
        OMIT_FROM_DOCS
        TODO: when we write 2 by 3 matrix, check to see if 6 is raised for minor keys
        TODO: check to make sure closing ends with tonic
         
        '''
        raisedMinorCorrectly = False
        if self.key.mode == 'minor':
            if self.key.pitchFromDegree(7).transpose("A1").name == self.v1n1.name:
                raisedMinorCorrectly = self.key.getScaleDegreeFromPitch(self.v1n2) == 1
            elif self.key.pitchFromDegree(7).transpose("A1").name == self.v2n1.name:
                raisedMinorCorrectly = self.key.getScaleDegreeFromPitch(self.v1n2) == 1
        else:
            raisedMinorCorrectly = True
        preclosings = [6,3]
        closingPitches = [self.v1n2.pitch.name, self.v2n2.name]  
        return not ( self.vIntervals[0].generic.simpleUndirected in preclosings and 
            self.vIntervals[1].generic.simpleUndirected == 1 and raisedMinorCorrectly and
             self.key.pitchFromDegree(1).name in closingPitches and
             self.contraryMotion())
           
class VoiceLeadingQuartetException(Exception):
    pass


def getVerticalSliceFromObject(music21Obj, scoreObjectIsFrom, classFilterList=None):
    '''
    >>> from music21 import *
    >>> c = corpus.parse('bach')
    >>> n1 = c.flat.getElementsByClass(note.Note)[0]
    >>> voiceLeading.getVerticalSliceFromObject(n1, c)
    <music21.voiceLeading.VerticalSlice contentDict={0: [<music21.note.Note F>], 1: [<music21.note.Note F>], 2: [<music21.note.Note C>], 3: [<music21.note.Note A>], 4: [<music21.note.Note F>]}  

    '''
    #if scoreObjectIsFrom == None:
    #    scoreObjectIsFrom = music21Obj.getAllContextsByClass(music21.stream.Score) #EXTREMELY UNRELIABLE AND VERY PRONE TO ERROR>>>>GRRRRR

    offsetOfObject =  music21Obj.getOffsetBySite(scoreObjectIsFrom.flat)
    

    contentDict = {}
    for partNum, partObj in enumerate(scoreObjectIsFrom.parts):
        elementStream = partObj.flat.getElementsByOffset(offsetOfObject, mustBeginInSpan=False, classList=classFilterList)
        #USE special python dictionary here!!! (defaultDict)
        for el in elementStream.elements:
            if partNum in contentDict.keys():
                contentDict[partNum].append(el)
            else:
                contentDict[partNum] = el
    return VerticalSlice(contentDict)


class VerticalSlice(music21.Music21Object):
    ''' A vertical slice of music21 objects that occur simultaneously in a score. The vertical slice 
    is instantiated by passing in a dictionary of the form {partNumber : [ music21Objects ] } 
    Typically vertical slices are created by :meth:`~music21.theoryAnalzyer.getVerticalSlices`
    

    >>> from music21 import *
    >>> vs1 = VerticalSlice({0:[note.Note('A4'), harmony.ChordSymbol('Cm')], 1: [note.Note('F2')]})
    >>> vs1.getObjectsByClass(note.Note)
    [<music21.note.Note A>, <music21.note.Note F>]
    >>> vs1.getObjectsByPart(0, note.Note)
    <music21.note.Note A>
    '''

    def __init__(self,contentDict):
        music21.Music21Object.__init__(self)
        for partNum, element in contentDict.items():
            if not isinstance(element, list):
                contentDict[partNum] = [element]
        
        self.contentDict = contentDict
        
        _DOC_ATTR = {
    'contentDict': 'Dictionary representing contents of vertical slices. the keys of the dictionary \
    are the part numbers and the element at each key is a list of music21 objects (allows for multiple voices \
    in a single part'
    }
    #method should be depricated...and will be as soon as we fix the other code that uses this    
#    def noteFromPart(self,partNum):
#        partNoteList = self.getObjectsByPart(partNum, classFilterList=['Note'])
#        if partNoteList:
#            return [0]
    
    def getObjectsByPart(self, partNum, classFilterList=None ):
        '''
        return the list of music21 objects associated with that part number (if more than one). returns
        the single object if only one. Optionally specify which
        type of objects to return with classFilterList
        
        >>> from music21 import *
        >>> vs1 = VerticalSlice({0:[note.Note('A4'), harmony.ChordSymbol('C')], 1: [note.Note('C')]})
        >>> vs1.getObjectsByPart(0, classFilterList=['Harmony'])
        <music21.harmony.ChordSymbol C>

        '''
        if not common.isIterable( classFilterList):
            classFilterList = [classFilterList]
        retList = []
        for el in self.contentDict[partNum]:
    
            if classFilterList is not None:
                if not el.isClassOrSubclass(classFilterList):
                    continue
            retList.append(el)
        if len(retList) > 1:
            return retList
        elif len(retList) == 1:
            return retList[0]
        else:
            return None
#    def _getNoteList(self):
#
#        noteList = []
#        for part, m21object in self.contentDict.items():
#            if m21object == None:
#                continue
#            else:
#                noteList.extend(m21object)
#        return noteList 
#    
#    noteList = property(_getNoteList, doc = '''
#        the a list of only the note objects in the vertical slice 
#    
#    
#    ''')    
    
    def getObjectsByClass(self, classFilterList, partNums=None):
        '''
        >>> from music21 import *
        >>> vs1 = VerticalSlice({0:[note.Note('A4'), harmony.ChordSymbol('C')], 1: [note.Note('C')], 2: [note.Note('B'), note.Note('F#')]})
        >>> vs1.getObjectsByClass('Note')
        [<music21.note.Note A>, <music21.note.Note C>, <music21.note.Note B>, <music21.note.Note F#>]
        >>>
        >>> vs1.getObjectsByClass('Note', [1,2])
        [<music21.note.Note C>, <music21.note.Note B>, <music21.note.Note F#>]

        '''
        if not common.isIterable( classFilterList):
            classFilterList = [classFilterList]
        retList = []
        for part, objList in self.contentDict.items():
            for m21object in objList:
                
                if  m21object == None or not m21object.isClassOrSubclass(classFilterList):
                    continue
                else:
                    if partNums and not part in partNums:
                            continue
                    retList.append(m21object)
        return retList 
    
    def _getObjects(self):
        retList = []
        for part, objList in self.contentDict.items():
            for m21object in objList:
                
                if  m21object == None:
                    continue
                else:
                    retList.append(m21object)
        return retList 
    
    objects = property(_getObjects, doc = '''
        return a list of all the music21 objects in the vertical slice
        
        >>> from music21 import *
        >>> vs1 = VerticalSlice({0:[ harmony.ChordSymbol('C'), note.Note('A4'),], 1: [note.Note('C')]})
        >>> vs1.objects
        [<music21.harmony.ChordSymbol C>, <music21.note.Note A>, <music21.note.Note C>]

        
        ''')
    
    def getStream(self, streamVSCameFrom = None):
        '''
        returns the stream representation of this vertical slice. Optionally pass in
        the full stream that this VS was extracted from, and correct key, meter, and time
        signatures will be included
        
        >>> from music21 import *
        >>> vs1 = VerticalSlice({0:[ harmony.ChordSymbol('C'), note.Note('A4'),], 1: [note.Note('C')]})
        >>> len(vs1.getStream().flat.getElementsByClass(note.Note))
        2
        >>> len(vs1.getStream().flat.getElementsByClass('Harmony'))
        1
        '''
        #scoreFromNote1 = music21Obj.getAllContextsByClass(stream.Score) #EXTREMELY UNRELIABLE AND VERY PRONE TO ERROR>>>>GRRRRR
        retStream = music21.stream.Score()
        for partNum, elementList in self.contentDict.items():
            p = music21.stream.Part()
            if streamVSCameFrom:
                foundObj = elementList[0]
                
                ks = foundObj.getContextByClass(key.KeySignature)
                ts = foundObj.getContextByClass(music21.meter.TimeSignature)
                cl = foundObj.getContextByClass(music21.clef.Clef)
               
                if cl:
                    p.append(cl)
                if ks:
                    p.append(ks)
                if ts:
                    p.append(ts)
                p.append(foundObj)
            if len(elementList) > 1:
                for el in elementList:
                    p.insert(music21.stream.Voice([el])) #probably wrong! Need to fix!!!
            else:
                p.insert(elementList[0])
            retStream.insert(p)
        return retStream

        
    def offset(self,leftAlign=True):
        '''
        returns the overall offset of the vertical slice. Typically, this would just be the
        offset of each object in the vertical slice, and each object would have the same offset.
        However, if the duration of one object in the slice is different than the duration of another,
        and that other starts after the first, but the first is still sounding, then the offsets would be
        different. In this case, specify leftAlign=True to return the lowest valued-offset of all the objects
        in the vertical slice. If you prefer the offset of the right-most starting object, then specify leftAlign=False
        
        >>> from music21 import *
        >>> s = stream.Score()
        >>> n1 = note.Note('A4', quarterLength=1.0)
        >>> s.append(n1)
        >>> n1.offset
        0.0
        >>> n2 = note.Note('F2', quarterLength =0.5)
        >>> s.append(n2)
        >>> n2.offset
        1.0
        >>> vs = VerticalSlice({0:n1, 1: n2})
        >>> vs.getObjectsByClass(note.Note)
        [<music21.note.Note A>, <music21.note.Note F>]

        >>> vs.offset(leftAlign=True)
        0.0
        >>> vs.offset(leftAlign=False)
        1.0
        '''
        if leftAlign:
            return sorted(self.objects, key=lambda m21Obj: m21Obj.offset)[0].offset
        else:
            return sorted(self.objects, key=lambda m21Obj: m21Obj.offset)[-1].offset
    
        
    def _setLyric(self, value):
        newList = sorted(self.objects, key=lambda x: x.offset, reverse=True)
        newList[0].lyric = value
        
    def _getLyric(self):
        newList = sorted(self.objects, key=lambda x: x.offset, reverse=True)
        return newList[0].lyric
        
    lyric = property(_getLyric, _setLyric, doc = '''
        sets each element on the vertical slice to have the passed in lyric
        
        >>> from music21 import *
        >>> h = voiceLeading.VerticalSlice({1:note.Note('C'), 2:harmony.ChordSymbol('C')})
        >>> h.lyric = 'vertical slice 1'
        >>> h.getStream().flat.getElementsByClass(note.Note)[0].lyric
        'vertical slice 1'
        ''')
    
    def __repr__(self):
        return '<music21.voiceLeading.%s contentDict=%s  ' % (self.__class__.__name__, self.contentDict)
                                                              
class VerticalSliceNTuplet(music21.Music21Object):
    '''a collection of n number of vertical slices'''
    def __init__(self, listofVerticalSlices): 
        music21.Music21Object.__init__(self)
              
        self.verticalSlices = listofVerticalSlices
        self.nTupletNum = len(listofVerticalSlices)
        
        self.chordList = []
        if listofVerticalSlices:
            self._calcChords()
        
    def _calcChords(self):
        for vs in self.verticalSlices:
            self.chordList.append(chord.Chord(vs.getObjectsByClass(note.Note)))
    
    def __repr__(self):
        return '<music21.voiceLeading.%s listofVerticalSlices=%s ' % (self.__class__.__name__, self.verticalSlices)
       
class VerticalSliceTriplet(VerticalSliceNTuplet):
    '''a collection of three vertical slices'''
    def __init__(self, listofVerticalSlices):
        VerticalSliceNTuplet.__init__(self, listofVerticalSlices)
        
        self.tnlsDict = {} #defaultdict(int) #Three Note Linear Segments
        self._calcTNLS()
        
    def _calcTNLS(self):
        '''
        calculates the three note linear segments if only three vertical slices provided
        '''
        for partNum in range(0,min(len(self.verticalSlices[0].getObjectsByClass(note.Note)), \
                                   len(self.verticalSlices[1].getObjectsByClass(note.Note)),\
                                    len(self.verticalSlices[2].getObjectsByClass(note.Note)))):
            self.tnlsDict[partNum] = ThreeNoteLinearSegment([self.verticalSlices[0].getObjectsByPart(partNum, note.Note),\
                                                              self.verticalSlices[1].getObjectsByPart(partNum, note.Note), \
                                                              self.verticalSlices[2].getObjectsByPart(partNum, note.Note)])

       
    def hasPassingTone(self, partNumToIdentify, unaccentedOnly=False):  
        '''
        partNum is the part (starting with 0) to identify the passing tone
        for use on 3 vertical slices (3Tuplet)
        
        
        >>> from music21 import *
        >>> vs1 = VerticalSlice({0:note.Note('A4'), 1: note.Note('F2')})
        >>> vs2 = VerticalSlice({0:note.Note('B-4'), 1: note.Note('F2')})
        >>> vs3 = VerticalSlice({0:note.Note('C5'), 1: note.Note('E2')})
        >>> tbtm = VerticalSliceTriplet([vs1, vs2, vs3])
        >>> tbtm.hasPassingTone(0)
        True
        '''  

        ret = self.tnlsDict[partNumToIdentify].couldBePassingTone()
        if unaccentedOnly:
            try:
                ret = ret and (self.tnlsDict[partNumToIdentify].n2.beatStrength < 0.5)
            except:
                pass
        return ret and self.chordList[0].isConsonant() and not self.chordList[1].isConsonant() and self.chordList[2].isConsonant()
        
        #check that the vertical slice containing the passing tone is dissonant        

    def hasNeighborTone(self, partNumToIdentify, unaccentedOnly=False):  
        '''
        partNum is the part (starting with 0) to identify the passing tone
        for use on 3 vertical slices (3tuplet)
        
        >>> from music21 import *
        >>> vs1 = VerticalSlice({0:note.Note('E-4'), 1: note.Note('C3')})
        >>> vs2 = VerticalSlice({0:note.Note('E-4'), 1: note.Note('B2')})
        >>> vs3 = VerticalSlice({0:note.Note('C5'), 1: note.Note('C3')})
        >>> tbtm = VerticalSliceTriplet([vs1, vs2, vs3])
        >>> tbtm.hasNeighborTone(1)
        True
        '''

        
        ret = self.tnlsDict[partNumToIdentify].couldBeNeighborTone()
        if unaccentedOnly:
            try:
                ret = ret and (self.tnlsDict[partNumToIdentify].n2.beatStrength < 0.5)
            except:
                pass
        return ret and not self.chordList[1].isConsonant()


class NChordLinearSegmentException(Exception):
    pass
class NObjectLinearSegment(music21.Music21Object):
    def __init__(self, objectList):
        self.objectList = objectList
    
    def __repr__(self):
        return '<music21.voiceLeading.%s objectList=%s  ' % (self.__class__.__name__, self.objectList)
     
    
class NChordLinearSegment(NObjectLinearSegment):
    def __init__(self, chordList):
        NObjectLinearSegment.__init__(self, chordList)
        self._chordList = []
        for value in chordList:
            if value == None:
                self._chordList.append(None)
            else:
                try:
                    if value.isClassOrSubclass([chord.Chord, music21.harmony.Harmony]):
                        self._chordList.append(value)
                    #else:
                        #raise NChordLinearSegmentException('not a valid chord specification: %s' % value)
                except:
                    raise NChordLinearSegmentException('not a valid chord specification: %s' % value)
                
    def _getChordList(self):
        return self._chordList

    chordList = property(_getChordList, doc = '''
    
        >>> from music21 import *
        >>> n = NChordLinearSegment([harmony.ChordSymbol('Am'), harmony.ChordSymbol('F7'), harmony.ChordSymbol('G9')])
        >>> n.chordList
        [<music21.harmony.ChordSymbol Am>, <music21.harmony.ChordSymbol F7>, <music21.harmony.ChordSymbol G9>]

    
        ''')
    def __repr__(self):
        return '<music21.voiceLeading.%s objectList=%s  ' % (self.__class__.__name__, self.chordList
                                                             )
class TwoChordLinearSegment(NChordLinearSegment):  
    def __init__(self, chordList, chord2=None):
        if isinstance(chordList, (list, tuple)):
            NChordLinearSegment.__init__(self, chordList)
        else:
            NChordLinearSegment.__init__(self, [chordList,chord2])
            
    def rootInterval(self, type='chromatic'):
        '''
        >>> from music21 import *
        >>> h = voiceLeading.TwoChordLinearSegment([harmony.ChordSymbol('C'), harmony.ChordSymbol('G')])
        >>> h.rootInterval()
        <music21.interval.ChromaticInterval 7>
        '''
        if type == 'chromatic':
            return interval.notesToChromatic(self.chordList[0].root(), self.chordList[1].root())
    
    def bassInterval(self, type='chromatic'):
        '''
        >>> from music21 import *
        >>> h = voiceLeading.TwoChordLinearSegment(harmony.ChordSymbol('C/E'), harmony.ChordSymbol('G'))
        >>> h.bassInterval()
        <music21.interval.ChromaticInterval 3>
        '''
        if type == 'chromatic':
            return interval.notesToChromatic(self.chordList[0].bass(), self.chordList[1].bass())
    
    
class NNoteLinearSegment(music21.Music21Object):
    '''a list of n notes strung together in a sequence
    noteList = [note1, note2, note3, ..., note-n ] Once this
    object is created with a noteList, the noteList may not
    be changed
    
    >>> from music21 import *
    >>> n = NNoteLinearSegment(['A', 'C', 'D'])
    >>> n.noteList
    [<music21.note.Note A>, <music21.note.Note C>, <music21.note.Note D>]

    '''
    def __init__(self, noteList):
        self._noteList = []
        for value in noteList:
            if value == None:
                self._noteList.append(None)
            elif common.isStr(value):
                self._noteList.append(note.Note(value))
            else:
                try:
                    if value.isClassOrSubclass([note.Note, pitch.Pitch]):
                        self._noteList.append(value)
                except:
                    raise NNoteLinearSegmentException('not a valid note specification: %s' % value)
                
    def _getNoteList(self):
        return self._noteList

    noteList = property(_getNoteList, doc = '''
    
        >>> from music21 import *
        >>> n = NNoteLinearSegment(['A', 'B5', 'C', 'F#'])
        >>> n.noteList
        [<music21.note.Note A>, <music21.note.Note B>, <music21.note.Note C>, <music21.note.Note F#>]
        
    
        ''')
    
    def _getMelodicIntervals(self):

        tempListOne = self.noteList[:-1]
        tempListTwo = self.noteList[1:]
        melodicIntervalList = []
        for n1, n2 in zip (tempListOne, tempListTwo):
            melodicIntervalList.append(music21.interval.Interval(n1, n2))
        
        return melodicIntervalList
        
    melodicIntervals = property(_getMelodicIntervals, doc = '''
        calculates the melodic intervals and returns them as a list,
        with the interval at 0 being the interval between the first and second note.
        
        >>> from music21 import *
        >>> n = NNoteLinearSegment([note.Note('A'), note.Note('B'), note.Note('C'), note.Note('D')])
        >>> n.melodicIntervals
        [<music21.interval.Interval M2>, <music21.interval.Interval M-7>, <music21.interval.Interval M2>]

        '''
        )

class NNoteLinearSegmentException(Exception):
    pass
    
class ThreeNoteLinearSegmentException(Exception):
    pass

class ThreeNoteLinearSegment(NNoteLinearSegment):
    '''
    An object consisting of three sequential notes
    
    The middle tone in a ThreeNoteLinearSegment can
    be classified using methods enclosed in this class
    to identify it as types of embellishing tones. Further
    methods can be used on the entire stream to identify these
    as non-harmonic.
    
    Accepts a sequence of strings, pitches, or notes.
    
    >>> from music21 import *
    >>> ex = voiceLeading.ThreeNoteLinearSegment('C#4','D4','E-4')
    >>> ex.n1
    <music21.note.Note C#>
    >>> ex.n2
    <music21.note.Note D>
    >>> ex.n3
    <music21.note.Note E->
    
    >>> ex = voiceLeading.ThreeNoteLinearSegment(note.Note('A4'),note.Note('D4'),'F5')
    >>> ex.n1
    <music21.note.Note A>  
    >>> ex.n2
    <music21.note.Note D>
    >>> ex.n3
    <music21.note.Note F>
    >>> ex.iLeftToRight
    <music21.interval.Interval m6>
    
    >>> ex.iLeft
    <music21.interval.Interval P-5>
    >>> ex.iRight
    <music21.interval.Interval m10>
    
    if no octave specified, default octave of 4 is assumed
    
    >>> ex2 = voiceLeading.ThreeNoteLinearSegment('a','b','c')
    >>> ex2.n1
    <music21.note.Note A>
    >>> ex2.n1.pitch.defaultOctave
    4
    
    '''

    def __init__(self, noteListorn1=None, n2 = None, n3 = None):
        if isinstance(noteListorn1, (list, tuple)):
            NNoteLinearSegment.__init__(self, noteListorn1)
        else:
            NNoteLinearSegment.__init__(self, [noteListorn1,n2,n3])
            
    def _getN1(self):
        return self.noteList[0]
    
    def _setN1(self, value):
        self.noteList[0] = self._correctNoteInput(value)
        
    def _getN2(self):
        return self.noteList[1]
    
    def _setN2(self, value):
        self.noteList[1] = self._correctNoteInput(value)
 
    def _getN3(self):
        return self.noteList[2]
    
    def _setN3(self, value):
        self.noteList[2] = self._correctNoteInput(value)
                
    def _correctNoteInput(self, value):
        if value == None:
            return None
        elif common.isStr(value):
            return note.Note(value)
        else:
            try:
                if value.isClassOrSubclass([note.Note, pitch.Pitch]):
                    return value
            except:
                raise ThreeNoteLinearSegmentException('not a valid note specification: %s' % value)
        
    n1 = property(_getN1, _setN1)
    n2 = property(_getN2, _setN2)
    n3 = property(_getN3, _setN3)
    
    def _getiLeftToRight(self):
        return music21.interval.Interval(self.n1, self.n3)
    
    def _getiLeft(self):
        return self.melodicIntervals[0]
    
    def _getiRight(self):
        return self.melodicIntervals[1]
    
    iLeftToRight = property(_getiLeftToRight)
    iLeft = property(_getiLeft)
    iRight = property(_getiRight)
    
    def __repr__(self):
        return '<music21.voiceLeading.%s n1=%s n2=%s n3=%s ' % (self.__class__.__name__, self.n1, self.n2, self.n3)
    
    def color(self, color='red', noteList = [2]):
        '''
        color all the notes in noteList (1,2,3). Default is to color only the second note red
        '''
        if 1 in noteList:
            self.n1.color = color
        if 2 in noteList:
            self.n2.color = color
        if 3 in noteList:
            self.n3.color = color
        
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
        >>> ThreeNoteLinearSegment('C3','D3','C3').couldBeDiatonicNeighborTone()
        True
        >>> ThreeNoteLinearSegment('C3','C#3','C3').couldBeDiatonicNeighborTone()
        False
        >>> ThreeNoteLinearSegment('C3','D-3','C3').couldBeDiatonicNeighborTone()
        False
        '''

        return self.n1.nameWithOctave == self.n3.nameWithOctave and \
            self.iLeft.chromatic.undirected == 2 and self.iRight.chromatic.undirected == 2 and \
            (self.iLeft.direction * self.iRight.direction == -1)

        
    def couldBeChromaticNeighborTone(self):
        '''
        returns true if and only if noteToAnalyze could be a chromatic neighbor tone
        
        >>> from music21 import *
        >>> ThreeNoteLinearSegment('C3','D3','C3').couldBeChromaticNeighborTone()
        False
        >>> ThreeNoteLinearSegment('C3','D-3','C3').couldBeChromaticNeighborTone()
        True
        >>> ThreeNoteLinearSegment('C#3','D3','C#3').couldBeChromaticNeighborTone()
        True
        >>> ThreeNoteLinearSegment('C#3','D3','D-3').couldBeChromaticNeighborTone()
        False
        '''
        return self.n1.nameWithOctave == self.n3.nameWithOctave and \
            self.iLeft.isChromaticStep and self.iRight.isChromaticStep and \
            (self.iLeft.direction * self.iRight.direction ==  -1)       

#class TwoByThreeLinearSegment(music21.Music21Object):
#    '''
#    An object consisting of two ThreeNoteLinearSegments (for now)....later on maybe more than just two
#    '''
#
#    def __init__(self, tnls1, tnls2):
#        self.tnls1 = tnls1
#        self.tnls2 = tnls2
#        
#        self.vIntervals = [] #vertical intervals (harmonic)
#        self.hIntervals = [] #horizontal intervals (melodic)
#        
#        if tnls1 is not None and tnls2 is not None:
#            self._findIntervals()        
#        
#        
#    def _findIntervals(self):
#        self.vIntervals.append(interval.notesToInterval(self.tnls1.n1, self.tnls2.n1))
#        self.vIntervals.append(interval.notesToInterval(self.tnls1.n2, self.tnls2.n2))
#        self.vIntervals.append(interval.notesToInterval(self.tnls1.n3, self.tnls2.n3))
#        
#        #self.hIntervals.append(interval.notesToInterval(self.tnls1.p1, self.tnls2.p1))
#        #self.hIntervals.append(interval.notesToInterval(self.tnls.p2, self.tnls2.p2))    
#        #self.hIntervals.append(interval.notesToInterval(self.tnls1.p3, self.tnls2.p3))  
#        
#    def __repr__(self):
#        return '<music21.voiceLeading.%s tnls1=%s tnls2=%s ' % (self.__class__.__name__, self.tnls1, self.tnls2)
#       
#    def hasUnaccentedPassingTone(self, partNum):  
#        '''
#        partNum is the part (0 or 1) to identify the passing tone
#        
#        >>> from music21 import *
#        >>> n1 = note.Note('A4', quarterLength = 0.5)
#        >>> n2 = note.Note('B-4', quarterLength = 0.5)
#        >>> n3 = note.Note('C5', quarterLength = 1.0)
#        >>> n4 = note.Note('F3', quarterLength = 1.0)
#        >>> n5 = note.Note('E3', quarterLength = 1.0)
#        >>> vl1 = ThreeNoteLinearSegment(n1, n2, n3)
#        >>> vl2 = ThreeNoteLinearSegment(n4, n4, n5)
#        >>> tbtm = TwoByThreeLinearSegment(vl1, vl2)
#        >>> tbtm.hasUnaccentedPassingTone(0)
#        True
#        '''  
#        
#        ret = False
#        if partNum == 0:
#            ret = self.tnls1.couldBePassingTone()
#        elif partNum == 1:
#            ret = self.tnls2.couldBePassingTone()
#        try:
#            ret = ret and (self.tnls1.n2.beatStrength < 0.5)
#        except:
#            pass
#        #print self.tnls1.n2.quarterLength
#        return ret and not self.vIntervals[1].isConsonant()
#        
#        
#        #check that the vertical slice containing the passing tone is dissonant
#   
#        
#
#
#def labelPassingTones(music21Stream, checkForDissonance=True, checkSimultaneous=True, checkForAccent=True, markWithColor=False, color='#FF0000'):
#    '''
#    searches through all voices of all parts in a given music21 stream and
#    identifies passing tones, then assigns a True/False value to the 
#    note's :class:`~music21.editorial.NoteEditorial` object. The information is 
#    stored as a miscellaneous attribute in the note editorial object, called 'isPassingTone'. 
#    Access this data from any note object in the stream after running this method by typing
#
#    for note in labeledStream.flat.getElementsByClass(music21.note.Note):
#    print note.editorial.misc['isPassingTone']
#    
#    Selectivity in labeling is provided by the following optional arguments:
#    checkForDissonance (default = True) --> checks if the chord formed is dissonant, and only
#    labels tone as a passing tone if the chord is dissonant.
#    
#    checkSimultaneous (default = True) --> iterates through every instance where simultaneous notes
#    are labeled (with color) and if their durations are different, labels only the tone that has a shorter duration
#    
#    checkForAccent (default = True) --> only labels passing tones on unaccented beats of the measure
#    
#    markWithColor (default = False) --> optionally label the identified passing tones with a color; default
#    color is red. Change labeling color with color modifier/
#    
#    color (default = '#00FF00') --> color to label notes if markWithColor is True. Colors must be specified
#    in a string HEX. For example, 
#    color = '#FF0000' (red)
#    color = '#00FF00' (green)
#    color = '#0000FF' (blue)
#    color = '#FFFF00' (yellow)
#    color = '#00FFFF' (turquoise)
#    color = '#FF00FF' (magenta)
#    color = '#C0C0C0' (grey)
#    color = '#FFFFFF' (white)
#    
#    '''
#
#    for part in music21Stream.parts:
#        notes = part.flat.getElementsByClass(music21.note.Note)
#        index = 0
#        for note in notes[1:len(notes) - 1]:
#            index = index + 1
#            if ThreeNoteLinearSegment(notes[index - 1], note, notes[index + 1]).couldBePassingTone():
#                listOfTruths = []
#                if checkForDissonance:
#                    listOfTruths.append(not _noteContextIsConsonant(note, music21Stream))
#                if checkForAccent:
#                    listOfTruths.append(_beatIsUnaccented(note))
#                if not (False in listOfTruths):
#                    note.editorial.misc['isPassingTone'] = True
#                    if markWithColor:
#                        note.color = color
#                else:
#                    note.editorial.misc['isPassingTone'] = False
#            else:
#                note.editorial.misc['isPassingTone'] = False
#                    
#        notes[0].editorial.misc['isPassingTone'] = False
#        notes[len(notes)-1].editorial.misc['isPassingTone'] = False
#        
#    if checkSimultaneous:
#        music21Stream = _checkForSimultaneousLabels(music21Stream, markWithColor)
#    return music21Stream
#    
#def labelNeighborTones(music21Stream, checkForDissonance=True, checkSimultaneous=True, checkForAccent=True, markWithColor=False, color='#00FF00'):
#    '''
#    searches through all voices of all parts in a given music21 stream and
#    identifies neighbor tones, then assigns a True/False value to the 
#    note's :class:`~music21.editorial.NoteEditorial` object. The information is 
#    stored as a miscellaneous attribute in the note editorial object, called 'isPassingTone'. 
#    Access this data from any note object in the stream after running this method by typing
#
#    for note in labeledStream.flat.getElementsByClass(music21.note.Note):
#    print note.editorial.misc['isNeighborTone']
#    
#    Selectivity in labeling is provided by the following optional arguments:
#    checkForDissonance (default = True) --> checks if the chord formed is dissonant, and only
#    labels tone as a passing tone if the chord is dissonant.
#    
#    checkSimultaneous (default = True) --> iterates through every instance where simultaneous notes
#    are labeled (with color) and if their durations are different, labels only the tone that has a shorter duration
#    
#    checkForAccent (default = True) --> only labels passing tones on unacented beats of the measure
#    
#    markWithColor (default = False) --> optionally label the identified neighbor tones with a color; default
#    color is green. Change labeling color with color modifier/
#    
#    color (default = '#00FF00') --> color to label notes if markWithColor is True. Colors must be specified
#    in a string HEX. 
#    For example, 
#    color = '#FF0000' (red)
#    color = '#00FF00' (green)
#    color = '#0000FF' (blue)
#    color = '#FFFF00' (yellow)
#    color = '#00FFFF' (turquoise)
#    color = '#FF00FF' (magenta)
#    color = '#C0C0C0' (grey)
#    color = '#FFFFFF' (white)
#    
#    '''
#    for part in music21Stream.parts:
#        notes = part.flat.getElementsByClass(music21.note.Note)
#        index = 0
#        for note in notes[1:len(notes) - 1]:
#            index = index + 1
#            if ThreeNoteLinearSegment(notes[index - 1], note, notes[index + 1]).couldBeNeighborTone():
#                listOfTruths = []
#                if checkForDissonance:
#                    listOfTruths.append(not _noteContextIsConsonant(note, music21Stream))
#                if checkForAccent:
#                    listOfTruths.append(_beatIsUnaccented(note))
#                if not (False in listOfTruths):
#                    note.editorial.misc['isNeighborTone'] = True
#                    if markWithColor:
#                        note.color = color
#                else:
#                    note.editorial.misc['isNeighborTone'] = False
#            else:
#                note.editorial.misc['isNeighborTone'] = False         
#        notes[0].editorial.misc['isNeighborTone'] = False
#        notes[len(notes)-1].editorial.misc['isNeighborTone'] = False
#    if checkSimultaneous:
#        music21Stream = _checkForSimultaneousLabels(music21Stream, markWithColor)
#    return music21Stream
#    
#def _checkForSimultaneousLabels(preLabeledMusic21Stream, checkPT=True, checkNT=True, markWithColor=False, color='#000000'):
#    '''
#    If after running a non-harmonic labeling method (such as labelPassingTones or labelNeighborTones)
#    you find that there are simultaneous pitches labeled when at least one of those pitches must
#    not be labeled, run this method to sort out which has the shorter duration, and this one remains
#    labeled while the other one becomes unlabeled. Optionally label with colors (as in with label passing tones)
#    
#    This method is run after every label non-harmonic tone method (labelPassingTones and labelNeighborTones)
#    
#    if markWithColor = True, then the identified non-harmonic tones that are returned to normal status are 
#    set back to the default color of black.
#    
#    Method steps through each part, and checks that part against each of the other parts. This method
#    should unlabel all simultaneous sounding like-type non-harmonic tones that have the same duration if a shorter
#    duraiton like-type non-harmonic tone is sounding simultaneously. For example, in four voices (SATB)
#    if the soprano and alto both have a passing tone labeled but each is a quarter note, and the tenor 
#    has a neighbor tone labeled but it is an eighth note, the soprano and alto labels are removed 
#    (editorial.misc['isPassingTone'] set to False and their color optionally returned to black. If the bass
#    is labeled as a neighbor tone and is simultaneous, there is no consequence because it is not of the same
#    'type' of non-harmonic tone.
#    
#    '''
#    partNumberBeingSearched = -1
#    while partNumberBeingSearched < len(preLabeledMusic21Stream.parts) - 1:
#        partNumberBeingSearched += 1
#        for note in preLabeledMusic21Stream.parts[partNumberBeingSearched].flat.getElementsByClass(music21.note.Note):
#            try:
#                note.editorial.misc['isPassingTone']
#            except:
#                note.editorial.misc['isPassingTone'] = False
#            try:
#                note.editorial.misc['isNeighborTone']
#            except:
#                note.editorial.misc['isNeighborTone'] = False
#                  
#            if checkPT and note.editorial.misc['isPassingTone'] == True:
#                for part in preLabeledMusic21Stream.parts[partNumberBeingSearched:]:
#                    for simultaneousNote in part.flat.getElementsByOffset(note.offset).flat.getElementsByClass(music21.note.Note):
#                        if simultaneousNote.editorial.misc['isPassingTone'] == True:
#                            if simultaneousNote.duration.quarterLength > note.duration.quarterLength:
#                                simultaneousNote.editorial.misc['isPassingTone'] = False
#                                simultaneousNote.color = color
#                            elif simultaneousNote.duration.quarterLength < note.duration.quarterLength:
#                                note.color = color
#                                note.editorial.misc['isPassingTone'] = False
#                            else:
#                                pass
#            if checkPT and note.editorial.misc['isNeighborTone'] == True:
#                for part in preLabeledMusic21Stream.parts[partNumberBeingSearched:]:
#                    for simultaneousNote in part.flat.getElementsByOffset(note.offset).flat.getElementsByClass(music21.note.Note):
#                        if simultaneousNote.editorial.misc['isNeighborTone'] == True:
#                            if simultaneousNote.duration.quarterLength > note.duration.quarterLength:
#                                simultaneousNote.editorial.misc['isNeighborTone'] = False
#                                simultaneousNote.color = color
#                            elif simultaneousNote.duration.quarterLength < note.duration.quarterLength:
#                                note.color = color
#                                note.editorial.misc['isNeighborTone'] = False
#                            else:
#                                pass
#                                #if the two durations are equal, then how do we know which is the passing tone
#                                #and which is the chordal tone???
#    
#    return preLabeledMusic21Stream
#
##METHOD UNDER REVISION...
##getVerticalSlice() should be able to operate directly on a stream...    
#def _noteContextIsConsonant(note, music21Stream):
#    #WRITE TESTS
#    
#    #music21Score
#    #isClass or subclass
#    #harmonicContext
#    #be able to pass in any object with an offset in a stream
#    #could be a spanner
#    #contextSearch (getContextByClass)
#    
#    '''
#    determines if the given note is a non-harmonic tone due to the context around the note,
#    specifically the pitches sounding simultaneously in all voices while the note sounds.
#    If the chord formed by these simultaneous pitches in consonant, False is returned. 
#    If the chord formed is consonant, true is returned
#    
#    Consonance is determined by making a chord of the simultaneous pitches, 
#    then calling chord's isConsonant() on that chord.
#    
#
#    '''
#    pitches = []
#    #hypothetically (and in actuality if used correctly), note.offset should be equal to offsetOfPitchToIdentify
#    offsetOfPitchToIdentify =  note.getOffsetBySite(music21Stream.flat)
##getContextByClass 
#    for part in music21Stream.parts: #'Rest'
#        value = part.flat.getElementAtOrBefore(offsetOfPitchToIdentify, classList=['Pitch', 'Note', 'Chord', music21.note.Rest])
#        if 'Chord' in value.classes:
#            value = value.pitches
#        if 'Rest' in value.classes:
#            pitches.append(value)
#    cWithPitch = music21.chord.Chord(pitches)
#    return cWithPitch.isConsonant()
#
##contextSearch in stream
#
#def _beatIsUnaccented(note):
#    #only unnacented passing tones are labeled
#    try:
#        return note.beatStrength < 0.5
#    except:
#        return False        
    
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
    

_DOC_ORDER = [VoiceLeadingQuartet, ThreeNoteLinearSegment, VerticalSlice, VerticalSliceNTuplet]

if __name__ == "__main__":
    music21.mainTest(Test)
    music21.mainTest


#------------------------------------------------------------------------------
# eof

