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
# Copyright:    Copyright © 2009-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Objects to represent unique elements in a score that contain special analysis routines
to identify certain aspects of music theory. for use especially with theoryAnalyzer, which will
divide a score up into these segments, returning a list of segments to later analyze

The list of objects included here are:

* :class:`~music21.voiceLeading.VoiceLeadingQuartet` : two by two matrix of notes

* :class:`~music21.voiceLeading.Verticality` : vertical context in a score, 
    composed of any music21 objects
* :class:`~music21.voiceLeading.VerticalityNTuplet` : group of three 
    contiguous verticality objects
* :class:`~music21.voiceLeading.VerticalityTriplet` : three vertical slices

* :class:`~music21.voiceLeading.NObjectLinearSegment` : n (any number) of music21 objects
* :class:`~music21.voiceLeading.NNoteLinearSegment` : n (any number) of notes
* :class:`~music21.voiceLeading.ThreeNoteLinearSegment` : three notes in the same part of a score
* :class:`~music21.voiceLeading.NChordLinearSegment` : 
    preliminary implementation of n(any number) chords
* :class:`~music21.voiceLeading.TwoChordLinearSegment` : 2 chord objects

'''
import unittest

from music21 import base
from music21 import exceptions21
from music21 import interval
from music21 import common
from music21 import pitch
from music21 import key
from music21 import note
from music21 import chord
from music21.ext import six

try:
    import enum # @UnresolvedImport
except ImportError:
    from music21.ext import enum # enum34 backport

#from music21 import harmony can't do this either
#from music21 import roman Can't import roman because of circular
#    importing issue with counterpoint.py and figuredbass


# create a module level shared cache for intervals of P1, P5, P8
# to be populated the first time a VLQ object is created
intervalCache = []

class MotionType(str, enum.Enum):
    antiParallel = 'Anti-Parallel'
    contrary = 'Contrary'
    noMotion = 'No Motion'
    oblique = 'Oblique'
    parallel = 'Parallel'
    similar = 'Similar'

#-------------------------------------------------------------------------------
class VoiceLeadingQuartet(base.Music21Object):
    '''
    An object consisting of four pitches: v1n1, v1n2, v2n1, v2n2
    where v1n1 moves to v1n2 at the same time as
    v2n1 moves to v2n2.
    (v1n1: voice 1(top voice), note 1 (left most note) )

    Necessary for classifying types of voice-leading motion
    '''

    _DOC_ATTR = {'vIntervals': '''list of the two harmonic intervals present, 
                     vn1n1 to v2n1 and v1n2 to v2n2''',
                 'hIntervals': '''list of the two melodic intervals present, 
                     v1n1 to v1n2 and v2n1 to v2n2'''}

    def __init__(self, v1n1=None, v1n2=None, v2n1=None, v2n2=None, analyticKey=key.Key('C')):
        base.Music21Object.__init__(self)
        if len(intervalCache) == 0:
            # populate interval cache if not done yet
            # more efficient than doing it as Class level variables
            # if VLQ is never called (likely)
            intervalCache.append(interval.Interval("P1"))
            intervalCache.append(interval.Interval("P5"))
            intervalCache.append(interval.Interval("P8"))
        self.unison = intervalCache[0]
        self.fifth = intervalCache[1]
        self.octave = intervalCache[2]

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

        self._key = None
        if analyticKey is not None:
            self.key = analyticKey
        if v1n1 is not None and v1n2 is not None and v2n1 is not None and v2n2 is not None:
            self._findIntervals()

    def __repr__(self):
        return '<music21.voiceLeading.%s v1n1=%s, v1n2=%s, v2n1=%s, v2n2=%s  >' % (
                    self.__class__.__name__, self.v1n1, self.v1n2, self.v2n1, self.v2n2)


    def _getKey(self):
        return self._key


    def _setKey(self, keyValue):
        if isinstance(keyValue, six.string_types):
            try:
                keyValue = key.Key(key.convertKeyStringToMusic21KeyString(keyValue))
            except:
                raise VoiceLeadingQuartetException(
                    'got a key signature string that is not supported: %s', keyValue)
        else:
            try:
                isKey = True if 'Key' in keyValue.classes else False
                if isKey is False:
                    raise AttributeError
            except AttributeError:
                raise VoiceLeadingQuartetException(
                    'got a key signature that is not a string or music21 Key ' + 
                    'object: %s' % keyValue)
        self._key = keyValue

    key = property(_getKey, _setKey, doc='''
        set the key of this voiceleading quartet, for use in theory analysis routines
        such as closesIncorrectly. The default key is C major

        >>> vlq = voiceLeading.VoiceLeadingQuartet('D','G','B','G')
        >>> vlq.key
        <music21.key.Key of C major>
        >>> vlq.key = 'G'
        >>> vlq.key
        <music21.key.Key of G major>
        ''')

    def _setVoiceNote(self, value, which):
        if value is None:
            setattr(self, which, None)
        elif isinstance(value, six.string_types):
            setattr(self, which, note.Note(value)) 
        else:
            try:
                if 'Note' in value.classes:
                    setattr(self, which, value)
                elif 'Pitch' in value.classes:
                    n = note.Note()
                    n.duration.quarterLength = 0.0
                    n.pitch = value
                    setattr(self, which, n)
            except:
                raise VoiceLeadingQuartetException(
                    'not a valid note specification: %s' % value)

    def _getv1n1(self):
        return self._v1n1

    def _setv1n1(self, value):
        self._setVoiceNote(value, '_v1n1')
        
    v1n1 = property(_getv1n1, _setv1n1, doc='''
        set note1 for voice 1

        >>> vl = voiceLeading.VoiceLeadingQuartet('C', 'D', 'E', 'F')
        >>> vl.v1n1
        <music21.note.Note C>
        ''')

    def _getv1n2(self):
        return self._v1n2

    def _setv1n2(self, value):
        self._setVoiceNote(value, '_v1n2')

    v1n2 = property(_getv1n2, _setv1n2, doc='''
        set note 2 for voice 1

        >>> vl = voiceLeading.VoiceLeadingQuartet('C', 'D', 'E', 'F')
        >>> vl.v1n2
        <music21.note.Note D>

        ''')


    def _getv2n1(self):
        return self._v2n1

    def _setv2n1(self, value):
        self._setVoiceNote(value, '_v2n1')

    v2n1 = property(_getv2n1, _setv2n1, doc='''
        set note 1 for voice 2

        >>> vl = voiceLeading.VoiceLeadingQuartet('C', 'D', 'E', 'F')
        >>> vl.v2n1
        <music21.note.Note E>
        ''')

    def _getv2n2(self):
        return self._v2n2

    def _setv2n2(self, value):
        self._setVoiceNote(value, '_v2n2')

    v2n2 = property(_getv2n2, _setv2n2, doc='''
        set note 2 for voice 2

        >>> vl = voiceLeading.VoiceLeadingQuartet('C', 'D', 'E', 'F')
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
        returns the type of motion from the MotionType Enum object 
        that exists in this voice leading quartet

        >>> for mt in voiceLeading.MotionType:
        ...     print(repr(mt))
        <MotionType.antiParallel: 'Anti-Parallel'>
        <MotionType.contrary: 'Contrary'>
        <MotionType.noMotion: 'No Motion'>
        <MotionType.oblique: 'Oblique'>
        <MotionType.parallel: 'Parallel'>
        <MotionType.similar: 'Similar'>

        >>> n1 = note.Note('D4')
        >>> n2 = note.Note('E4')
        >>> m1 = note.Note('F4')
        >>> m2 = note.Note('B4')
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.motionType()
        <MotionType.similar: 'Similar'>

        >>> n1 = note.Note('A4')
        >>> n2 = note.Note('C5')
        >>> m1 = note.Note('D4')
        >>> m2 = note.Note('F4')
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.motionType()
        <MotionType.parallel: 'Parallel'>
        >>> print(vl.motionType())
        MotionType.parallel
        >>> vl.motionType() == 'Parallel'
        True
        '''
        motionType = ''
        if self.obliqueMotion():
            motionType = MotionType.oblique
        elif self.parallelMotion():
            motionType = MotionType.parallel
        elif self.similarMotion():
            motionType = MotionType.similar
        elif self.contraryMotion():
            motionType = MotionType.contrary
        elif self.antiParallelMotion():
            motionType = MotionType.antiParallel
        elif self.noMotion():
            motionType = MotionType.noMotion
        return motionType

    def noMotion(self):
        '''
        Returns true if no voice moves in this "voice-leading" moment

        >>> n1 = note.Note('G4')
        >>> n2 = note.Note('G4')
        >>> m1 = note.Note('D4')
        >>> m2 = note.Note('D4')
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.noMotion()
        True
        >>> n2.octave = 5
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.noMotion()
        False

        '''
        for iV in self.hIntervals:
            if iV.name != "P1":
                return False
        return True

    def obliqueMotion(self):
        '''
        Returns true if one voice remains the same and another moves.  i.e.,
        noMotion must be False if obliqueMotion is True.


        >>> n1 = note.Note('G4')
        >>> n2 = note.Note('G4')
        >>> m1 = note.Note('D4')
        >>> m2 = note.Note('D4')
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.obliqueMotion()
        False
        >>> n2.octave = 5
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.obliqueMotion()
        True
        >>> m2.octave = 5
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
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


        >>> n1 = note.Note('G4')
        >>> n2 = note.Note('G4')
        >>> m1 = note.Note('G4')
        >>> m2 = note.Note('G4')
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.similarMotion()
        False
        >>> n2.octave = 5
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.similarMotion()
        False
        >>> m2.octave = 5
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.similarMotion()
        True
        >>> m2 = note.Note('A5')
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
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

    def parallelMotion(self, requiredInterval=None):
        '''Returns True if both voices move with the same interval or an
        octave duplicate of the interval.  If requiredInterval is given
        then returns True only if the parallel interval is that simple interval.

        >>> n1 = note.Note('G4')
        >>> n2 = note.Note('G4')
        >>> m1 = note.Note('G4')
        >>> m2 = note.Note('G4')
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.parallelMotion() #no motion, so oblique motion will give False
        False

        >>> n2.octave = 5
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.parallelMotion()
        False

        >>> m2.octave = 5
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.parallelMotion()
        True

        >>> vl.parallelMotion('P8')
        True

        >>> vl.parallelMotion('M6')
        False

        >>> m2 = note.Note('A5')
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.parallelMotion()
        False

        Return boolean.
        '''

        if not self.similarMotion():
            return False
        elif self.vIntervals[0].directedSimpleName != self.vIntervals[1].directedSimpleName:
            return False
        else:
            if requiredInterval is None:
                return True
            else:
                if isinstance(requiredInterval, six.string_types):
                    requiredInterval = interval.Interval(requiredInterval)

                if self.vIntervals[0].simpleName == requiredInterval.simpleName:
                    return True
                else:
                    return False

    def contraryMotion(self):
        '''Returns True if both voices move in opposite directions

        >>> n1 = note.Note('G4')
        >>> n2 = note.Note('G4')
        >>> m1 = note.Note('G4')
        >>> m2 = note.Note('G4')
        
        No motion, so False:
        
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.contraryMotion() 
        False

        Oblique motion, so False:

        >>> n2.octave = 5
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.contraryMotion()
        False

        Parallel motion, so False

        >>> m2.octave = 5
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.contraryMotion()
        False

        Similar motion, so False

        >>> m2 = note.Note('A5')
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.contraryMotion()
        False

        Finally, contrary motion, so True!

        >>> m2 = note.Note('C4')
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.contraryMotion()
        True

        Returns boolean.
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

        >>> n1 = note.Note('D5')
        >>> n2 = note.Note('E5')
        >>> m1 = note.Note('G4')
        >>> m2 = note.Note('F4')
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.outwardContraryMotion()
        True
        >>> vl.inwardContraryMotion()
        False
        '''
        return self.contraryMotion() and self.hIntervals[0].direction == 1

    def inwardContraryMotion(self):
        '''
        Returns true if both voices move inward by contrary motion

        >>> n1 = note.Note('C5')
        >>> n2 = note.Note('B4')
        >>> m1 = note.Note('G4')
        >>> m2 = note.Note('A4')
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.inwardContraryMotion()
        True
        >>> vl.outwardContraryMotion()
        False
        '''
        return self.contraryMotion() and self.hIntervals[0].direction == -1

    def antiParallelMotion(self, simpleName=None):
        '''Returns True if the simple interval before is the same as the simple
        interval after and the motion is contrary. if simpleName is
        specified as an Interval object or a string then it only returns
        true if the simpleName of both intervals is the same as simpleName
        (i.e., use to find antiParallel fifths)

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
        >>> vl2 = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl2.antiParallelMotion()
        False

        Returns boolean.
        '''
        if not self.contraryMotion():
            return False
        else:
            if self.vIntervals[0].simpleName == self.vIntervals[1].simpleName:
                if simpleName is None:
                    return True
                else:
                    if isinstance(simpleName, six.string_types):
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
        '''Returns true if there is a parallel motion or antiParallel motion of
        this type (thisInterval should be an Interval object)

        >>> n11 = note.Note("C4")
        >>> n12a = note.Note("D4") # ascending 2nd
        >>> n12b = note.Note("D3") # descending 7th

        >>> n21 = note.Note("G4")
        >>> n22a = note.Note("A4") # ascending 2nd
        >>> n22b = note.Note("B4") # ascending 3rd
        >>> vlq1 = voiceLeading.VoiceLeadingQuartet(n11, n12a, n21, n22a)
        >>> vlq1.parallelInterval(interval.Interval("P5"))
        True

        >>> vlq1.parallelInterval(interval.Interval("P8"))
        False

        Antiparallel fifths also are true

        >>> vlq2 = voiceLeading.VoiceLeadingQuartet(n11, n12b, n21, n22a)
        >>> vlq2.parallelInterval(interval.Interval("P5"))
        True

        Non-parallel intervals are, of course, False

        >>> vlq3 = voiceLeading.VoiceLeadingQuartet(n11, n12a, n21, n22b)
        >>> vlq3.parallelInterval(interval.Interval("P5"))
        False

        Returns boolean.
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
        Returns true if the motion is a parallel Perfect Fifth 
        (or antiparallel) or Octave duplication

        >>> voiceLeading.VoiceLeadingQuartet(
        ...     note.Note("C4"),
        ...     note.Note("D4"),
        ...     note.Note("G4"),
        ...     note.Note("A4")
        ...     ).parallelFifth()
        True

        >>> voiceLeading.VoiceLeadingQuartet(
        ...     note.Note("C4"),
        ...     note.Note("D4"),
        ...     note.Note("G5"),
        ...     note.Note("A5")
        ...     ).parallelFifth()
        True

        >>> voiceLeading.VoiceLeadingQuartet(note.Note("C4"),
        ...     note.Note("D#4"),
        ...     note.Note("G4"),
        ...     note.Note("A4")
        ...     ).parallelFifth()
        False

        Returns boolean.
        '''
        return self.parallelInterval(self.fifth)

    def parallelOctave(self):
        '''Returns True if the motion is a parallel Perfect Octave...
        a concept so abhorrent we shudder to illustrate it with an example, but alas, we must:

        >>> N = note.Note # to make these examples shorter
        
        >>> vlq = voiceLeading.VoiceLeadingQuartet(N("C4"), N("D4"), N("C5"), N("D5"))
        >>> vlq.parallelOctave()
        True

        >>> vlq = voiceLeading.VoiceLeadingQuartet(N("C4"), N("D4"), N("C6"), N("D6"))
        >>> vlq.parallelOctave()
        True

        Or False if the motion is according to the rules of God's own creation:

        >>> vlq = voiceLeading.VoiceLeadingQuartet(N("C4"), N("D4"), N("C4"), N("D4"))
        >>> vlq.parallelOctave()
        False

        Return boolean.
        '''
        return self.parallelInterval(self.octave)

    def parallelUnison(self):
        '''Returns true if the motion is a parallel Perfect Unison (and not
        Perfect Octave, etc.)

        >>> N = note.Note
        >>> voiceLeading.VoiceLeadingQuartet(N("C4"), N("D4"), N("C4"), N("D4")).parallelUnison()
        True

        >>> voiceLeading.VoiceLeadingQuartet(N("C4"), N("D4"), N("C5"), N("D5")).parallelUnison()
        False

        Return boolean.
        '''
        return self.parallelInterval(self.unison)

    def parallelUnisonOrOctave(self):
        '''Returns true if voice leading quartet is either motion by parallel
        octave or unison

        >>> voiceLeading.VoiceLeadingQuartet(
        ...     note.Note("C4"),
        ...     note.Note("D4"),
        ...     note.Note("C3"),
        ...     note.Note("D3")
        ...     ).parallelUnisonOrOctave()
        True

        >>> voiceLeading.VoiceLeadingQuartet(
        ...     note.Note("C4"),
        ...     note.Note("D4"),
        ...     note.Note("C4"),
        ...     note.Note("D4")
        ...     ).parallelUnisonOrOctave()
        True

        Returns boolean.
        '''

        return self.parallelOctave() or self.parallelUnison()

    def hiddenInterval(self, thisInterval):
        '''N.b. -- this method finds ALL hidden intervals,
        not just those that are forbidden under traditional
        common practice counterpoint rules. Takes thisInterval,
        an Interval object.

        >>> n1 = note.Note('C4')
        >>> n2 = note.Note('G4')
        >>> m1 = note.Note('B4')
        >>> m2 = note.Note('D5')
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.hiddenInterval(interval.Interval('P5'))
        True

        >>> n1 = note.Note('E4')
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.hiddenInterval(interval.Interval('P5'))
        False

        >>> m2.octave = 6
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.hiddenInterval(interval.Interval('P5'))
        False

        Returns boolean.
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
        '''
        Calls :meth:`~music21.voiceLeading.VoiceLeadingQuartet.hiddenInterval` by passing a fifth
        '''
        return self.hiddenInterval(self.fifth)

    def hiddenOctave(self):
        '''
        Calls hiddenInterval by passing an octave
        '''
        return self.hiddenInterval(self.octave)

    def improperResolution(self):
        '''
        Checks whether the voice-leading quartet resolves correctly according to standard
        counterpoint rules. If the first harmony is dissonant (d5, A4, or m7) it checks
        that these are correctly resolved. If the first harmony is consonant, True is returned.

        The key parameter should be specified to check for motion in the bass from specific
        note degrees. Default key is C Major.

        Diminished Fifth: in by contrary motion to a third, with 7 resolving up to 1 in the bass
        Augmented Fourth: out by contrary motion to a sixth, with chordal seventh resolving
        down to a third in the bass.
        Minor Seventh: In to a third with a leap form 5 to 1 in the bass

        >>> n1 = note.Note('B-4')
        >>> n2 = note.Note('A4')
        >>> m1 = note.Note('E4')
        >>> m2 = note.Note('F4')
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.improperResolution() #d5
        True

        >>> n1 = note.Note('E5')
        >>> n2 = note.Note('F5')
        >>> m1 = note.Note('B-4')
        >>> m2 = note.Note('A4')
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.improperResolution() #A4
        True

        >>> n1 = note.Note('B-4')
        >>> n2 = note.Note('A4')
        >>> m1 = note.Note('C4')
        >>> m2 = note.Note('F4')
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.improperResolution() #m7
        True

        >>> n1 = note.Note('C4')
        >>> n2 = note.Note('D4')
        >>> m1 = note.Note('F4')
        >>> m2 = note.Note('G4')
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.improperResolution() #not dissonant, true returned
        False

        >>> vl = voiceLeading.VoiceLeadingQuartet('B-4', 'A4', 'C2', 'F2')
        >>> vl.key = key.Key('F')
        >>> vl.improperResolution() # not dissonant, true returned
        False

        Returns boolean.
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
        returns true if there is a leap or skip in once voice then the other voice must 
        be a step or unison.
        if neither part skips then False is returned. Returns False if the two voices 
        skip thirds in contrary motion.

        >>> n1 = note.Note('G4')
        >>> n2 = note.Note('C5')
        >>> m1 = note.Note('B3')
        >>> m2 = note.Note('A3')
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.leapNotSetWithStep()
        False

        >>> n1 = note.Note('G4')
        >>> n2 = note.Note('C5')
        >>> m1 = note.Note('B3')
        >>> m2 = note.Note('F3')
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.leapNotSetWithStep()
        True

        >>> vl = voiceLeading.VoiceLeadingQuartet('E', 'G', 'G', 'E')
        >>> vl.leapNotSetWithStep()
        False
        '''
        if self.noMotion():
            return False

        if (self.hIntervals[0].generic.undirected == 3 
                and self.hIntervals[1].generic.undirected == 3 
                and self.contraryMotion()):
            return False

        if self.hIntervals[0].generic.isSkip:
            return not (self.hIntervals[1].generic.isDiatonicStep
                        or self.hIntervals[1].generic.isUnison)
        elif self.hIntervals[1].generic.isSkip:
            return not (self.hIntervals[0].generic.isDiatonicStep
                        or self.hIntervals[0].generic.isUnison)
        else:
            return False

    def opensIncorrectly(self):
        '''
        RENAME TODO
        
        In the style of 16th century Counterpoint (not Bach Chorale style)

        Returns true if the opening or second harmonic interval is PU, P8, or P5, 
        to accommodate an anacrusis.
        also checks to see if opening establishes tonic or dominant harmony (uses
        :meth:`~music21.roman.identifyAsTonicOrDominant`

        >>> vl = voiceLeading.VoiceLeadingQuartet('D','D','D','F#')
        >>> vl.key = 'D'
        >>> vl.opensIncorrectly()
        False
        >>> vl = voiceLeading.VoiceLeadingQuartet('B','A','G#','A')
        >>> vl.key = 'A'
        >>> vl.opensIncorrectly()
        False
        >>> vl = voiceLeading.VoiceLeadingQuartet('A', 'A', 'F#', 'D')
        >>> vl.key = 'A'
        >>> vl.opensIncorrectly()
        False

        >>> vl = voiceLeading.VoiceLeadingQuartet('C#', 'C#', 'D', 'E')
        >>> vl.key = 'A'
        >>> vl.opensIncorrectly()
        True

        >>> vl = voiceLeading.VoiceLeadingQuartet('B', 'B', 'A', 'A')
        >>> vl.key = 'C'
        >>> vl.opensIncorrectly()
        True
        '''
        from music21 import roman
        c1 = chord.Chord([self.vIntervals[0].noteStart, self.vIntervals[0].noteEnd])
        c2 = chord.Chord([self.vIntervals[1].noteStart, self.vIntervals[1].noteEnd])
        r1 = roman.identifyAsTonicOrDominant(c1, self.key)
        r2 = roman.identifyAsTonicOrDominant(c2, self.key)
        openings = ['P1','P5', 'I', 'V']
        return not ( (self.vIntervals[0].simpleName in openings
                        or self.vIntervals[1].simpleName in openings)
                      and (r1[0].upper() in openings if r1 is not False else False
                           or r2[0].upper() in openings if r2 is not False else False) )

    def closesIncorrectly(self):
        '''
        In the style of 16th century Counterpoint (not Bach Chorale style)

        returns true if closing harmonic interval is a P8 or PU and the interval 
        approaching the close is
        6 - 8, 10 - 8, or 3 - U. Must be in contrary motion, and if in minor key, 
        the leading tone resolves to the tonic.

        >>> vl = voiceLeading.VoiceLeadingQuartet('C#', 'D', 'E', 'D')
        >>> vl.key = key.Key('d')
        >>> vl.closesIncorrectly()
        False
        >>> vl = voiceLeading.VoiceLeadingQuartet('B3', 'C4', 'G3', 'C2')
        >>> vl.key = key.Key('C')
        >>> vl.closesIncorrectly()
        False
        >>> vl = voiceLeading.VoiceLeadingQuartet('F', 'G', 'D', 'G')
        >>> vl.key = key.Key('g')
        >>> vl.closesIncorrectly()
        True
        >>> vl = voiceLeading.VoiceLeadingQuartet('C#4', 'D4', 'A2', 'D3', analyticKey='D')
        >>> vl.closesIncorrectly()
        True

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
        return not ( self.vIntervals[0].generic.simpleUndirected in preclosings 
                     and self.vIntervals[1].generic.simpleUndirected == 1 
                     and raisedMinorCorrectly 
                     and self.key.pitchFromDegree(1).name in closingPitches 
                     and self.contraryMotion())

class VoiceLeadingQuartetException(exceptions21.Music21Exception):
    pass


def getVerticalityFromObject(music21Obj, scoreObjectIsFrom, classFilterList=None):
    '''
    returns the :class:`~music21.voiceLeading.Verticality` object given a score, 
    and a music21 object within this score
    (under development)

    TODO: How is contentDict not sometimes out of order in Python 3?

    >>> c = corpus.parse('bach/bwv66.6')
    >>> n1 = c.flat.getElementsByClass(note.Note)[0]
    >>> voiceLeading.getVerticalityFromObject(n1, c)
    <music21.voiceLeading.Verticality 
        contentDict={0: [<music21.instrument.Instrument P1: Soprano: Instrument 1>, 
                         <music21.clef.TrebleClef>, 
                         <music21.key.Key of f# minor>, 
                         <music21.meter.TimeSignature 4/4>, 
                         <music21.note.Note C#>], 
              1: [<music21.instrument.Instrument P2: Alto: Instrument 2>, 
                  <music21.clef.TrebleClef>, 
                  <music21.key.Key of f# minor>, 
                  <music21.meter.TimeSignature 4/4>, 
                  <music21.note.Note E>],
              2: [<music21.instrument.Instrument P3: Tenor: Instrument 3>, 
                  <music21.clef.BassClef>, 
                  <music21.key.Key of f# minor>, 
                  <music21.meter.TimeSignature 4/4>, 
                  <music21.note.Note A>], 
              3: [<music21.instrument.Instrument P4: Bass: Instrument 4>, 
                  <music21.clef.BassClef>, 
                  <music21.key.Key of f# minor>, 
                  <music21.meter.TimeSignature 4/4>, 
                  <music21.note.Note A>]}>

    for getting things at the beginning of scores, probably better to use a classFilterList:

    >>> voiceLeading.getVerticalityFromObject(n1, c, 
    ...                      classFilterList=[note.Note, chord.Chord, note.Rest])
    <music21.voiceLeading.Verticality contentDict={0: [<music21.note.Note C#>], 
              1: [<music21.note.Note E>], 
              2: [<music21.note.Note A>], 
              3: [<music21.note.Note A>]}>
    '''
    offsetOfObject =  music21Obj.getOffsetBySite(scoreObjectIsFrom.flat)

    contentDict = {}
    for partNum, partObj in enumerate(scoreObjectIsFrom.parts):
        elementStream = partObj.flat.getElementsByOffset(offsetOfObject, 
                                                         mustBeginInSpan=False, 
                                                         classList=classFilterList)
        for el in elementStream.elements:
            if partNum in contentDict:
                contentDict[partNum].append(el)
            else:
                contentDict[partNum] = [el]
    return Verticality(contentDict)


class Verticality(base.Music21Object):
    '''
    A vertical slice object provides more accessible information about
    vertical moments in a score. A vertical slice is instantiated by passing in a dictionary of
    the form {partNumber : [ music21Objects ] }
    To create vertical slices out of a score, call 
    by :meth:`~music21.theoryAnalzyer.getVerticalities`

    Vertical slices are useful to provide direct and easy access to objects in a part. 
    A list of vertical
    slices, although similar to the list of chords from a chordified score, 
    provides easier access to partnumber
    information and identity of objects in the score. Plus, the objects in a 
    vertical slice points directly
    to the objects in the score, so modifying a vertical slice taken from a 
    score is the same as modyfing the elements
    of the vertical slice in the score directly.


    >>> vs1 = voiceLeading.Verticality({0:[note.Note('A4'), harmony.ChordSymbol('Cm')], 
    ...                                 1: [note.Note('F2')]})
    >>> vs1.getObjectsByClass(note.Note)
    [<music21.note.Note A>, <music21.note.Note F>]
    >>> vs1.getObjectsByPart(0, note.Note)
    <music21.note.Note A>
    '''
    _DOC_ATTR = {
    'contentDict': '''Dictionary representing contents of vertical slices. 
        the keys of the dictionary
        are the part numbers and the element at each key is a list of 
        music21 objects (allows for multiple voices
        in a single part)'''
    }

    def __init__(self, contentDict):
        base.Music21Object.__init__(self)
        for partNum, element in contentDict.items():
            if not isinstance(element, list):
                contentDict[partNum] = [element]

        self.contentDict = contentDict
        self._color = ''

    def isConsonant(self):
        '''
        evaluates whether this vertical slice moment is consonant or dissonant 
        according to the common-practice
        consonance rules. Method generates chord of all simultaneously sounding pitches, then calls
        :meth:`~music21.chord.isConsonant`

        >>> V = voiceLeading.Verticality
        >>> N = note.Note
        >>> V({0:N('A4'), 1:N('B4'), 2:N('A4')}).isConsonant()
        False
        >>> V({0:N('A4'), 1:N('B4'), 2:N('C#4')}).isConsonant()
        False
        >>> V({0:N('C3'), 1:N('G5'), 2:chord.Chord(['C3','E4','G5'])}).isConsonant()
        True
        >>> V({0:N('A3'), 1:N('B3'), 2:N('C4')}).isConsonant()
        False
        >>> V({0:N('C1'), 1:N('C2'), 2:N('C3'), 3:N('G1'), 4:N('G2'), 5:N('G3')}).isConsonant()
        True
        >>> V({0:N('A3'), 1:harmony.ChordSymbol('Am')}).isConsonant()
        True
        '''
        return self.getChord().isConsonant()

    def getChord(self):
        '''
        extracts all simultaneously sounding pitches (from chords, notes, harmony objects, etc.) 
        and returns
        as a chord. Pretty much returns the vertical slice to a chordified output.

        >>> N = note.Note
        >>> vs1 = voiceLeading.Verticality({0:N('A4'), 1:chord.Chord(['B','C','A']), 2:N('A')})
        >>> vs1.getChord()
        <music21.chord.Chord A4 B C A A>
        >>> voiceLeading.Verticality({0:N('A3'), 
        ...                           1:chord.Chord(['F3','D4','A4']), 
        ...                           2:harmony.ChordSymbol('Am')}).getChord()
        <music21.chord.Chord A3 F3 D4 A4 A2 C3 E3>
        '''
        pitches = []
        for el in self.objects:
            if 'Chord' in el.classes:
                for x in el.pitches:
                    pitches.append(x.nameWithOctave)
            elif 'Note' in el.classes:
                pitches.append(el)
        return chord.Chord(pitches)

    def makeAllSmallestDuration(self):
        '''
        locates the smallest duration of all elements in the vertical slice 
        and assigns this duration
        to each element

        >>> n1 =  note.Note('C4')
        >>> n1.quarterLength = 1
        >>> n2 =  note.Note('G4')
        >>> n2.quarterLength = 2
        >>> cs = harmony.ChordSymbol('C')
        >>> cs.quarterLength = 4
        >>> vs1 = voiceLeading.Verticality({0:n1, 1:n2, 2:cs})
        >>> vs1.makeAllSmallestDuration()
        >>> [x.quarterLength for x in vs1.objects]
        [1.0, 1.0, 1.0]
        '''
        self.changeDurationofAllObjects(self.getShortestDuration())

    def makeAllLargestDuration(self):
        '''
        locates the largest duration of all elements in the vertical slice 
        and assigns this duration
        to each element

        >>> n1 =  note.Note('C4')
        >>> n1.quarterLength = 1
        >>> n2 =  note.Note('G4')
        >>> n2.quarterLength = 2
        >>> cs = harmony.ChordSymbol('C')
        >>> cs.quarterLength = 4
        >>> vs1 = voiceLeading.Verticality({0:n1, 1:n2, 2:cs})
        >>> vs1.makeAllLargestDuration()
        >>> [x.quarterLength for x in vs1.objects]
        [4.0, 4.0, 4.0]
        '''
        self.changeDurationofAllObjects(self.getLongestDuration())

    def getShortestDuration(self):
        '''
        returns the smallest quarterLength that exists among all elements

        >>> n1 =  note.Note('C4')
        >>> n1.quarterLength = 1
        >>> n2 =  note.Note('G4')
        >>> n2.quarterLength = 2
        >>> cs = harmony.ChordSymbol('C')
        >>> cs.quarterLength = 4
        >>> vs1 = voiceLeading.Verticality({0:n1, 1:n2, 2:cs})
        >>> vs1.getShortestDuration()
        1.0
        '''
        leastQuarterLength = self.objects[0].quarterLength
        for obj in self.objects:
            if obj.quarterLength < leastQuarterLength:
                leastQuarterLength = obj.quarterLength
        return leastQuarterLength

    def getLongestDuration(self):
        '''
        returns the longest duration that exists among all elements

        >>> n1 =  note.Note('C4')
        >>> n1.quarterLength = 1
        >>> n2 =  note.Note('G4')
        >>> n2.quarterLength = 2
        >>> cs = harmony.ChordSymbol('C')
        >>> cs.quarterLength = 4
        >>> vs1 = voiceLeading.Verticality({0:n1, 1:n2, 2:cs})
        >>> vs1.getLongestDuration()
        4.0
        '''
        longestQuarterLength = self.objects[0].quarterLength
        for obj in self.objects:
            if obj.quarterLength > longestQuarterLength:
                longestQuarterLength = obj.quarterLength
        return longestQuarterLength

    def changeDurationofAllObjects(self, newQuarterLength):
        '''
        changes the duration of all objects in vertical slice

        >>> n1 =  note.Note('C4')
        >>> n1.quarterLength = 1
        >>> n2 =  note.Note('G4')
        >>> n2.quarterLength = 2
        >>> cs = harmony.ChordSymbol('C')
        >>> cs.quarterLength = 4
        >>> vs1 = voiceLeading.Verticality({0:n1, 1:n2, 2:cs})
        >>> vs1.changeDurationofAllObjects(1.5)
        >>> [x.quarterLength for x in vs1.objects]
        [1.5, 1.5, 1.5]
        '''
        for obj in self.objects:
            obj.quarterLength = newQuarterLength

    def getObjectsByPart(self, partNum, classFilterList=None ):
        '''
        returns the list of music21 objects associated with a given part number 
        (if more than one). returns
        the single object if only one. Optionally specify which
        type of objects to return with classFilterList

        >>> vs1 = voiceLeading.Verticality({0:[note.Note('A4'), harmony.ChordSymbol('C')], 
        ...                                 1:[note.Note('C')]})
        >>> vs1.getObjectsByPart(0, classFilterList=['Harmony'])
        <music21.harmony.ChordSymbol C>
        >>> vs1.getObjectsByPart(0)
        [<music21.note.Note A>, <music21.harmony.ChordSymbol C>]
        >>> vs1.getObjectsByPart(1)
        <music21.note.Note C>
        '''
        if not common.isIterable( classFilterList):
            classFilterList = [classFilterList]
        retList = []
        for el in [el for el in self.contentDict[partNum] if el is not None]:
            if classFilterList == [None]:
                retList.append(el)
            else:
                if el.isClassOrSubclass(classFilterList):
                    retList.append(el)
        if len(retList) > 1:
            return retList
        elif len(retList) == 1:
            return retList[0]
        else:
            return None


    def getObjectsByClass(self, classFilterList, partNums=None):
        '''
        returns a list of all objects in the vertical slice of a type contained 
        in the classFilterList. Optionally
        specify partnumbers to only search for matching objects

        >>> N = note.Note
        >>> vs1 = voiceLeading.Verticality({0: [N('A4'), harmony.ChordSymbol('C')], 
        ...                                 1: [N('C')], 
        ...                                 2: [N('B'), N('F#')]})
        >>> vs1.getObjectsByClass('Note')
        [<music21.note.Note A>, <music21.note.Note C>, 
         <music21.note.Note B>, <music21.note.Note F#>]
        >>> vs1.getObjectsByClass('Note', [1,2])
        [<music21.note.Note C>, <music21.note.Note B>, <music21.note.Note F#>]

        '''
        if not common.isIterable( classFilterList):
            classFilterList = [classFilterList]
        retList = []
        for part, objList in self.contentDict.items():
            for m21object in objList:

                if  m21object is None or not m21object.isClassOrSubclass(classFilterList):
                    continue
                else:
                    if partNums and not part in partNums:
                        continue
                    retList.append(m21object)
        return retList

    def _getObjects(self):
        retList = []
        for unused_part, objList in self.contentDict.items():
            for m21object in objList:

                if  m21object is None:
                    continue
                else:
                    retList.append(m21object)
        return retList

    objects = property(_getObjects, doc='''
        return a list of all the music21 objects in the vertical slice

        >>> vs1 = voiceLeading.Verticality({0:[harmony.ChordSymbol('C'), note.Note('A4'),], 
        ...                                 1:[note.Note('C')]})
        >>> vs1.objects
        [<music21.harmony.ChordSymbol C>, <music21.note.Note A>, <music21.note.Note C>]
        ''')

    def getStream(self, streamVSCameFrom = None):
        '''
        returns the stream representation of this vertical slice. Optionally pass in
        the full stream that this verticality was extracted from, and correct key, meter, and time
        signatures will be included
        (under development)

        >>> vs1 = voiceLeading.Verticality({0:[harmony.ChordSymbol('C'), note.Note('A4'),], 
        ...                                 1:[note.Note('C')]})
        >>> len(vs1.getStream().flat.getElementsByClass(note.Note))
        2
        >>> len(vs1.getStream().flat.getElementsByClass('Harmony'))
        1
        '''
        from music21 import stream
        retStream = stream.Score()
        for unused_partNum, elementList in self.contentDict.items():
            p = stream.Part()
            if streamVSCameFrom:
                foundObj = elementList[0]

                ks = foundObj.getContextByClass("KeySignature")
                ts = foundObj.getContextByClass("TimeSignature")
                cl = foundObj.getContextByClass("Clef")

                if cl:
                    p.append(cl)
                if ks:
                    p.append(ks)
                if ts:
                    p.append(ts)
                p.append(foundObj)
            if len(elementList) > 1:
                for el in elementList:
                    p.insert(stream.Voice([el])) #probably wrong! Need to fix!!!
            else:
                p.insert(elementList[0])
            retStream.insert(p)
        return retStream


    def offset(self,leftAlign=True):
        '''
        returns the overall offset of the vertical slice. Typically, this would just be the
        offset of each object in the vertical slice, and each object would have the same offset.
        However, if the duration of one object in the slice is different than the duration 
        of another,
        and that other starts after the first, but the first is still sounding, then the 
        offsets would be
        different. In this case, specify leftAlign=True to return the lowest valued-offset 
        of all the objects
        in the vertical slice. If you prefer the offset of the right-most starting object, 
        then specify leftAlign=False

        >>> s = stream.Score()
        >>> n1 = note.Note('A4', quarterLength=1.0)
        >>> s.append(n1)
        >>> n1.offset
        0.0
        >>> n2 = note.Note('F2', quarterLength =0.5)
        >>> s.append(n2)
        >>> n2.offset
        1.0
        >>> vs = voiceLeading.Verticality({0:n1, 1: n2})
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

    lyric = property(_getLyric, _setLyric, doc='''
        sets each element on the vertical slice to have the passed in lyric

        >>> h = voiceLeading.Verticality({1:note.Note('C'), 2:harmony.ChordSymbol('C')})
        >>> h.lyric = 'vertical slice 1'
        >>> h.getStream().flat.getElementsByClass(note.Note)[0].lyric
        'vertical slice 1'
        ''')

    def __repr__(self):
        return '<music21.voiceLeading.%s contentDict=%s>' % (
                                self.__class__.__name__, self.contentDict)

    def _setColor(self, color):

        for obj in self.objects:
            obj.color = color

    def _getColor(self):
        return self._color

    color = property(_getColor, _setColor, doc='''
        sets the color of each element in the vertical slice

        >>> vs1 = voiceLeading.Verticality({1:note.Note('C'), 2:harmony.ChordSymbol('C')})
        >>> vs1.color = 'blue'
        >>> [x.color for x in vs1.objects]
        ['blue', 'blue']
    ''')


class VerticalityNTuplet(base.Music21Object):
    '''
    a collection of n number of vertical slices. These objects are useful when 
    analyzing counterpoint
    motion and music theory elements such as passing tones'''
    def __init__(self, listofVerticalities):
        base.Music21Object.__init__(self)

        self.verticalities = listofVerticalities
        self.nTupletNum = len(listofVerticalities)

        self.chordList = []
        if listofVerticalities:
            self._calcChords()

    def _calcChords(self):
        for vs in self.verticalities:
            self.chordList.append(chord.Chord(vs.getObjectsByClass(note.Note)))

    def __repr__(self):
        return '<music21.voiceLeading.%s listofVerticalities=%s >' % (
                        self.__class__.__name__, self.verticalities)
    def __str__(self):
        return self.__repr__()

class VerticalityTriplet(VerticalityNTuplet):
    '''a collection of three vertical slices'''
    def __init__(self, listofVerticalities):
        VerticalityNTuplet.__init__(self, listofVerticalities)

        self.tnlsDict = {} #defaultdict(int) #Three Note Linear Segments
        self._calcTNLS()

    def _calcTNLS(self):
        '''
        calculates the three note linear segments if only three vertical slices provided
        '''
        for partNum in range(0, min(len(self.verticalities[0].getObjectsByClass(note.Note)),
                                    len(self.verticalities[1].getObjectsByClass(note.Note)),
                                    len(self.verticalities[2].getObjectsByClass(note.Note)))
                             ):
            self.tnlsDict[partNum] = ThreeNoteLinearSegment([
                                    self.verticalities[0].getObjectsByPart(partNum, note.Note),
                                    self.verticalities[1].getObjectsByPart(partNum, note.Note),
                                    self.verticalities[2].getObjectsByPart(partNum, note.Note)])


    def hasPassingTone(self, partNumToIdentify, unaccentedOnly=False):
        '''
        return true if this vertical slice triplet contains a passing tone
        music21 currently identifies passing tones by analyzing both horizontal motion 
        and vertical motion.
        It first checks to see if the note could be a passing tone based on the notes 
        linearly adjacent to it.
        It then checks to see if the note's vertical context is dissonant, while the 
        vertical slices
        to the left and right are consonant

        partNum is the part (starting with 0) to identify the passing tone

        >>> vs1 = voiceLeading.Verticality({0:note.Note('A4'), 1:note.Note('F2')})
        >>> vs2 = voiceLeading.Verticality({0:note.Note('B-4'), 1:note.Note('F2')})
        >>> vs3 = voiceLeading.Verticality({0:note.Note('C5'), 1:note.Note('E2')})
        >>> tbtm = voiceLeading.VerticalityTriplet([vs1, vs2, vs3])
        >>> tbtm.hasPassingTone(0)
        True
        >>> tbtm.hasPassingTone(1)
        False

        '''
        if partNumToIdentify in self.tnlsDict:
            ret = self.tnlsDict[partNumToIdentify].couldBePassingTone()
        else:
            return False
        if unaccentedOnly:
            try:
                ret = ret and (self.tnlsDict[partNumToIdentify].n2.beatStrength < 0.5)
            except (AttributeError, NameError, base.Music21ObjectException):
                pass
        if (ret
                and self.chordList[0].isConsonant()
                and not self.chordList[1].isConsonant()
                and self.chordList[2].isConsonant()):
            return True
        else:
            return False
        #check that the vertical slice containing the passing tone is dissonant

    def hasNeighborTone(self, partNumToIdentify, unaccentedOnly=False):
        '''
        return true if this vertical slice triplet contains a neighbor tone
        music21 currently identifies neighbor tones by analyzing both horizontal motion 
        and vertical motion.
        It first checks to see if the note could be a neighbor tone based on the notes 
        linearly adjacent to it.
        It then checks to see if the note's vertical context is dissonant, 
        while the vertical slices
        to the left and right are consonant

        partNum is the part (starting with 0) to identify the passing tone
        for use on 3 vertical slices (3tuplet)

        >>> vs1 = voiceLeading.Verticality({0:note.Note('E-4'), 1: note.Note('C3')})
        >>> vs2 = voiceLeading.Verticality({0:note.Note('E-4'), 1: note.Note('B2')})
        >>> vs3 = voiceLeading.Verticality({0:note.Note('C5'), 1: note.Note('C3')})
        >>> tbtm = voiceLeading.VerticalityTriplet([vs1, vs2, vs3])
        >>> tbtm.hasNeighborTone(1)
        True
        '''

        if partNumToIdentify in self.tnlsDict:
            ret = self.tnlsDict[partNumToIdentify].couldBeNeighborTone()
        else:
            return False
        if unaccentedOnly:
            try:
                ret = ret and (self.tnlsDict[partNumToIdentify].n2.beatStrength < 0.5)
            except (AttributeError, NameError, base.Music21ObjectException):
                pass
        return ret and not self.chordList[1].isConsonant()




class NNoteLinearSegment(base.Music21Object):
    '''a list of n notes strung together in a sequence
    noteList = [note1, note2, note3, ..., note-n ] Once this
    object is created with a noteList, the noteList may not
    be changed

    >>> n = voiceLeading.NNoteLinearSegment(['A', 'C', 'D'])
    >>> n.noteList
    [<music21.note.Note A>, <music21.note.Note C>, <music21.note.Note D>]

    '''
    def __init__(self, noteList):
        base.Music21Object.__init__(self)
        self._noteList = []
        for value in noteList:
            if value is None:
                self._noteList.append(None)
            elif isinstance(value, six.string_types):
                self._noteList.append(note.Note(value))
            else:
                try:
                    if value.isClassOrSubclass([note.Note, pitch.Pitch]):
                        self._noteList.append(value)
                except (AttributeError, NameError):
                    self._noteList.append(None)

    def _getNoteList(self):
        return self._noteList

    noteList = property(_getNoteList, doc='''
        >>> n = voiceLeading.NNoteLinearSegment(['A', 'B5', 'C', 'F#'])
        >>> n.noteList
        [<music21.note.Note A>, <music21.note.Note B>, 
         <music21.note.Note C>, <music21.note.Note F#>]
        ''')

    def _getMelodicIntervals(self):

        tempListOne = self.noteList[:-1]
        tempListTwo = self.noteList[1:]
        melodicIntervalList = []
        for n1, n2 in zip (tempListOne, tempListTwo):
            if n1 and n2:
                melodicIntervalList.append(interval.Interval(n1, n2))
            else:
                melodicIntervalList.append(None)
        return melodicIntervalList

    melodicIntervals = property(_getMelodicIntervals, doc='''
        calculates the melodic intervals and returns them as a list,
        with the interval at 0 being the interval between the first and second note.

        >>> n = voiceLeading.NNoteLinearSegment([note.Note('A'), note.Note('B'), 
        ...            note.Note('C'), note.Note('D')])
        >>> n.melodicIntervals
        [<music21.interval.Interval M2>, 
         <music21.interval.Interval M-7>, 
         <music21.interval.Interval M2>]
        '''
        )

class NNoteLinearSegmentException(exceptions21.Music21Exception):
    pass

class ThreeNoteLinearSegmentException(exceptions21.Music21Exception):
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
    _DOC_ORDER = ['couldBePassingTone', 
                  'couldBeDiatonicPassingTone', 
                  'couldBeChromaticPassingTone',
                  'couldBeNeighborTone',
                  'couldBeDiatonicNeighborTone',
                  'couldBeChromaticNeighborTone']
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
        if value is None:
            return None
        elif isinstance(value, six.string_types):
            return note.Note(value)
        else:
            try:
                if value.isClassOrSubclass([note.Note, pitch.Pitch]):
                    return value
            except:
                raise ThreeNoteLinearSegmentException('not a valid note specification: %s' % value)

    n1 = property(_getN1, _setN1, doc='''
        get or set the first note (left-most) in the segment
        ''')
    n2 = property(_getN2, _setN2, doc='''
        get or set the middle note in the segment
        ''')
    n3 = property(_getN3, _setN3, doc='''
        get or set the last note (right-most) in the segment
        ''')

    def _getiLeftToRight(self):
        if self.n1 and self.n3:
            return interval.Interval(self.n1, self.n3)
        else:
            return None
    def _getiLeft(self):
        return self.melodicIntervals[0]

    def _getiRight(self):
        return self.melodicIntervals[1]

    iLeftToRight = property(_getiLeftToRight, doc='''
        get the interval between the left-most note and the right-most note
        (read-only property)

        >>> tnls = voiceLeading.ThreeNoteLinearSegment('C', 'E','G')
        >>> tnls.iLeftToRight
        <music21.interval.Interval P5>
        ''')

    iLeft = property(_getiLeft, doc='''
        get the interval between the left-most note and the middle note
        (read-only property)

        >>> tnls = voiceLeading.ThreeNoteLinearSegment('A','B','G')
        >>> tnls.iLeft
        <music21.interval.Interval M2>
        ''')
    iRight = property(_getiRight, doc='''
        get the interval between the middle note and the right-most note
        (read-only property)

        >>> tnls = voiceLeading.ThreeNoteLinearSegment('A','B','G')
        >>> tnls.iRight
        <music21.interval.Interval M-3>
        ''')

    def __repr__(self):
        return '<music21.voiceLeading.%s n1=%s n2=%s n3=%s >' % (
                        self.__class__.__name__, self.n1, self.n2, self.n3)

    def color(self, color='red', noteList=(2,)):
        '''
        color all the notes in noteList (1,2,3). Default is to color only the second note red
        '''
        if 1 in noteList:
            self.n1.color = color
        if 2 in noteList:
            self.n2.color = color
        if 3 in noteList:
            self.n3.color = color

    def _isComplete(self):
        #if not (self.n1 and self.n2 and self.n3):

        return (self.n1 is not None) and (self.n2 is not None) and (self.n3 is not None) 
        #if any of these are none, it isn't complete

    def couldBePassingTone(self):
        '''
        checks if the two intervals are steps and if these steps
        are moving in the same direction. Returns true if the tone is
        identified as either a chromatic passing tone or a diatonic passing
        tone. Only major and minor diatonic passing tones are recognized (not
        pentatonic or scales beyond twelve-notes). Does NOT check if tone is non harmonic

        Accepts pitch or note objects; method is dependent on octave information

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
        if not self._isComplete():
            return False
        else:
            return self.couldBeDiatonicPassingTone() or self.couldBeChromaticPassingTone()

    def couldBeDiatonicPassingTone(self):
        '''
        A note could be a diatonic passing tone (and therefore a passing tone in general)
        if the generic interval between the previous and the current is 2 or -2;
        same for the next; and both move in the same direction
        (that is, the two intervals multiplied by each other are 4, not -4).

        >>> voiceLeading.ThreeNoteLinearSegment('B3','C4','C#4').couldBeDiatonicPassingTone()
        False
        >>> voiceLeading.ThreeNoteLinearSegment('C3','D3','E3').couldBeDiatonicPassingTone()
        True
        '''
        return self._isComplete() and (self.iLeftToRight.generic.isSkip and \
            self.iLeft.generic.undirected == 2 and self.iRight.generic.undirected == 2 and \
            self.iLeft.generic.undirected * self.iRight.generic.undirected == 4 and \
            (self.iLeft.direction * self.iRight.direction == 1))


    def couldBeChromaticPassingTone(self):
        '''
        A note could a chromatic passing tone (and therefore a passing tone in general)
        if the generic interval between the previous and the current is -2, 1, or 2;
        the generic interval between the current and next is -2, 1, 2; the two generic
        intervals multiply to -2 or 2 (if 4 then it's a diatonic interval; if 1 then
        not a passing tone; i.e, C -> C# -> C## is not a chromatic passing tone);
        AND between each of the notes there is a chromatic interval of 1 or -1 and
        multiplied together it is 1. (i.e.: C -> D-- -> D- is not a chromatic passing tone).

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

        return (self._isComplete() 
            and ((self.iLeft.generic.undirected == 2 or self.iLeft.generic.undirected == 1)
                and (self.iRight.generic.undirected == 2 or self.iRight.generic.undirected == 1)
                and self.iLeft.generic.undirected * self.iRight.generic.undirected == 2
                and self.iLeft.isChromaticStep 
                and self.iRight.isChromaticStep
                and self.iLeft.direction * self.iRight.direction == 1))

    def couldBeNeighborTone(self):
        '''
        checks if noteToAnalyze could be a neighbor tone, either a diatonic neighbor tone
        or a chromatic neighbor tone. Does NOT check if tone is non harmonic

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
        if not self._isComplete():
            return False
        else:
            return self.couldBeDiatonicNeighborTone() or self.couldBeChromaticNeighborTone()


    def couldBeDiatonicNeighborTone(self):
        '''
        returns true if and only if noteToAnalyze could be a diatonic neighbor tone, that is,
        the left and right notes are identical while the middle is a diatonic step up or down

        >>> voiceLeading.ThreeNoteLinearSegment('C3','D3','C3').couldBeDiatonicNeighborTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('C3','C#3','C3').couldBeDiatonicNeighborTone()
        False
        >>> voiceLeading.ThreeNoteLinearSegment('C3','D-3','C3').couldBeDiatonicNeighborTone()
        False
        '''

        return (self._isComplete() 
            and self.n1.nameWithOctave == self.n3.nameWithOctave 
            and self.iLeft.chromatic.undirected == 2 
            and self.iRight.chromatic.undirected == 2 
            and self.iLeft.direction * self.iRight.direction == -1)


    def couldBeChromaticNeighborTone(self):
        '''
        returns true if and only if noteToAnalyze could be a chromatic neighbor tone, that is,
        the left and right notes are identical while the middle is a chromatic step up or down

        >>> voiceLeading.ThreeNoteLinearSegment('C3','D3','C3').couldBeChromaticNeighborTone()
        False
        >>> voiceLeading.ThreeNoteLinearSegment('C3','D-3','C3').couldBeChromaticNeighborTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('C#3','D3','C#3').couldBeChromaticNeighborTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('C#3','D3','D-3').couldBeChromaticNeighborTone()
        False
        '''
        return (self._isComplete() 
            and (self.n1.nameWithOctave == self.n3.nameWithOctave 
                 and self.iLeft.isChromaticStep 
                 and self.iRight.isChromaticStep 
                 and (self.iLeft.direction * self.iRight.direction ==  -1)))

### Below: beginnings of an implementation for any object segments, 
### such as two chord linear segments
### currently only used by theoryAnalyzer

class NChordLinearSegmentException(exceptions21.Music21Exception):
    pass

class NObjectLinearSegment(base.Music21Object):

    def __init__(self, objectList):
        base.Music21Object.__init__(self)
        self.objectList = objectList

    def __repr__(self):
        return '<music21.voiceLeading.%s objectList=%s  >' % (
                self.__class__.__name__, self.objectList)


class NChordLinearSegment(NObjectLinearSegment):
    def __init__(self, chordList):
        NObjectLinearSegment.__init__(self, chordList)
        self._chordList = []
        for value in chordList:
            if value is None:
                self._chordList.append(None)
            else:
                try:
                    if value.isClassOrSubclass(["Chord", "Harmony"]):
                        self._chordList.append(value)
                    #else:
                        #raise NChordLinearSegmentException(
                        #     'not a valid chord specification: %s' % value)
                except:
                    raise NChordLinearSegmentException(
                            'not a valid chord specification: %s' % value)

    def _getChordList(self):
        return self._chordList

    chordList = property(_getChordList, doc='''
        returns a list of all chord symbols in this linear segment

        >>> n = voiceLeading.NChordLinearSegment([harmony.ChordSymbol('Am'), 
        ...                                       harmony.ChordSymbol('F7'), 
        ...                                       harmony.ChordSymbol('G9')])
        >>> n.chordList
        [<music21.harmony.ChordSymbol Am>, 
         <music21.harmony.ChordSymbol F7>, 
         <music21.harmony.ChordSymbol G9>]


        ''')
    def __repr__(self):
        return '<music21.voiceLeading.%s objectList=%s  >' % (
                                                self.__class__.__name__, self.chordList
                                                             )
class TwoChordLinearSegment(NChordLinearSegment):
    def __init__(self, chordList, chord2=None):
        if isinstance(chordList, (list, tuple)):
            NChordLinearSegment.__init__(self, chordList)
        else:
            NChordLinearSegment.__init__(self, [chordList,chord2])

    def rootInterval(self):
        '''
        returns the chromatic interval between the roots of the two chord symbols

        >>> h = voiceLeading.TwoChordLinearSegment([harmony.ChordSymbol('C'), 
        ...                                         harmony.ChordSymbol('G')])
        >>> h.rootInterval()
        <music21.interval.ChromaticInterval 7>
        '''
        return interval.notesToChromatic(self.chordList[0].root(), self.chordList[1].root())

    def bassInterval(self):
        '''
        returns the chromatic interval between the basses of the two chord symbols

        >>> h = voiceLeading.TwoChordLinearSegment(harmony.ChordSymbol('C/E'), 
        ...                                        harmony.ChordSymbol('G'))
        >>> h.bassInterval()
        <music21.interval.ChromaticInterval 3>
        '''
        return interval.notesToChromatic(self.chordList[0].bass(), self.chordList[1].bass())


#-------------------------------------------------------------------------------

class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testInstantiateEmptyObject(self):
        '''
        test instantiating an empty VoiceLeadingQuartet
        '''
        unused_vlq = VoiceLeadingQuartet()

    def testCopyAndDeepcopy(self):
        #Test copying all objects defined in this module
        import copy
        import sys
        import types
        for part in sys.modules[self.__module__].__dict__:
            match = False
            for skip in ['_', '__', 'Test', 'Exception', 'MotionType']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            obj = getattr(sys.modules[self.__module__], part)
            if callable(obj) and not isinstance(obj, types.FunctionType):
                unused_a = copy.copy(obj)
                unused_b = copy.deepcopy(obj)

    def test_unifiedTest(self):
        C4 = note.Note()
        C4.name = "C"
        D4 = note.Note()
        D4.name = "D"
        E4 = note.Note()
        E4.name = "E"
        F4 = note.Note()
        F4.name = "F"
        G4 = note.Note()
        G4.name = "G"
        A4 = note.Note()
        A4.name = "A"
        B4 = note.Note()
        B4.name = "B"
        C5 = note.Note()
        C5.name = "C"
        C5.octave = 5
        D5 = note.Note()
        D5.name = "D"
        D5.octave = 5

        a = VoiceLeadingQuartet(C4, D4, G4, A4)
        assert a.similarMotion() is True
        assert a.parallelMotion() is True
        assert a.antiParallelMotion() is False
        assert a.obliqueMotion() is False
        assert a.parallelInterval(interval.Interval("P5")) is True
        assert a.parallelInterval(interval.Interval("M3")) is False

        b = VoiceLeadingQuartet(C4, C4, G4, G4)
        assert b.noMotion() is True
        assert b.parallelMotion() is False
        assert b.antiParallelMotion() is False
        assert b.obliqueMotion() is False

        c = VoiceLeadingQuartet(C4, G4, C5, G4)
        assert c.antiParallelMotion() is True
        assert c.hiddenInterval(interval.Interval("P5")) is False

        d = VoiceLeadingQuartet(C4, D4, E4, A4)
        assert d.hiddenInterval(interval.Interval("P5")) is True
        assert d.hiddenInterval(interval.Interval("A4")) is False
        assert d.hiddenInterval(interval.Interval("AA4")) is False


class TestExternal(unittest.TestCase):
    def runTest(self):
        pass


#------------------------------------------------------------------------------

_DOC_ORDER = [VoiceLeadingQuartet, ThreeNoteLinearSegment, Verticality, VerticalityNTuplet]

if __name__ == "__main__":
    import music21
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof
