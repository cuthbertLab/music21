# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         voiceLeading.py
# Purpose:      music21 classes for voice leading
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#               Jackie Rogoff
#               Beth Hadley
#
# Copyright:    Copyright © 2009-2012 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
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
* :class:`~music21.voiceLeading.VerticalityTriplet` : three verticality objects --
    has special features
* :class:`~music21.voiceLeading.NObjectLinearSegment` : n (any number) of music21 objects
* :class:`~music21.voiceLeading.NNoteLinearSegment` : n (any number) of notes
* :class:`~music21.voiceLeading.ThreeNoteLinearSegment` : three notes in the same part of a score
* :class:`~music21.voiceLeading.NChordLinearSegment` :
    preliminary implementation of n(any number) chords
* :class:`~music21.voiceLeading.TwoChordLinearSegment` : 2 chord objects

'''
import enum
import unittest
from typing import List

from music21 import base
from music21 import exceptions21
from music21 import interval
from music21 import common
from music21 import pitch
from music21 import key
from music21 import note
from music21 import chord
from music21 import scale


# from music21 import harmony can't do this either
# from music21 import roman Can't import roman because of circular
#    importing issue with counterpoint.py and figuredbass

# create a module level shared cache for intervals of P1, P5, P8
# to be populated the first time a VLQ object is created
intervalCache = []  # type: List[interval.Interval]


class MotionType(str, enum.Enum):
    antiParallel = 'Anti-Parallel'
    contrary = 'Contrary'
    noMotion = 'No Motion'
    oblique = 'Oblique'
    parallel = 'Parallel'
    similar = 'Similar'


# ------------------------------------------------------------------------------
class VoiceLeadingQuartet(base.Music21Object):
    '''
    An object consisting of four pitches: v1n1, v1n2, v2n1, v2n2
    where v1n1 moves to v1n2 at the same time as
    v2n1 moves to v2n2.
    (v1n1: voice 1(top voice), note 1 (left most note) )

    Necessary for classifying types of voice-leading motion.

    In general, v1 should be the "higher" voice and v2 the "lower" voice
    in order for methods such as `.voiceCrossing` and `isProperResolution`
    to make sense.  Most routines will work the other way still though.
    '''

    _DOC_ATTR = {'vIntervals': '''list of the two harmonic intervals present,
                     vn1n1 to v2n1 and v1n2 to v2n2''',
                 'hIntervals': '''list of the two melodic intervals present,
                     v1n1 to v1n2 and v2n1 to v2n2'''}

    def __init__(self, v1n1=None, v1n2=None, v2n1=None, v2n2=None, analyticKey=None):
        super().__init__()
        if not intervalCache:
            # populate interval cache if not done yet
            # more efficient than doing it as Class level variables
            # if VLQ is never called (likely)
            intervalCache.append(interval.Interval('P1'))
            intervalCache.append(interval.Interval('P5'))
            intervalCache.append(interval.Interval('P8'))
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

        self.vIntervals = []  # vertical intervals (harmonic)
        self.hIntervals = []  # horizontal intervals (melodic)

        self._key = None
        if analyticKey is not None:
            self.key = analyticKey
        if v1n1 is not None and v1n2 is not None and v2n1 is not None and v2n2 is not None:
            self._findIntervals()

    def _reprInternal(self):
        nameV1n1 = None
        nameV1n2 = None
        nameV2n1 = None
        nameV2n2 = None
        try:
            nameV1n1 = self.v1n1.nameWithOctave
        except AttributeError:
            pass

        try:
            nameV1n2 = self.v1n2.nameWithOctave
        except AttributeError:
            pass

        try:
            nameV2n1 = self.v2n1.nameWithOctave
        except AttributeError:
            pass

        try:
            nameV2n2 = self.v2n2.nameWithOctave
        except AttributeError:
            pass

        return f'v1n1={nameV1n1}, v1n2={nameV1n2}, v2n1={nameV2n1}, v2n2={nameV2n2}'

    @property
    def key(self):
        '''
        get or set the key of this VoiceLeadingQuartet, for use in theory analysis routines
        such as closesIncorrectly. Can be None

        >>> vlq = voiceLeading.VoiceLeadingQuartet('D', 'G', 'B', 'G')
        >>> vlq.key is None
        True
        >>> vlq.key = key.Key('G')
        >>> vlq.key
        <music21.key.Key of G major>

        Key can also be given as a string:

        >>> vlq.key = 'd'
        >>> vlq.key
        <music21.key.Key of d minor>

        Incorrect keys raise VoiceLeadingQuartetExceptions
        '''
        return self._key

    @key.setter
    def key(self, keyValue):
        if isinstance(keyValue, str):
            try:
                keyValue = key.Key(key.convertKeyStringToMusic21KeyString(keyValue))
            except Exception as e:  # pragma: no cover  # pylint: disable=broad-except
                raise VoiceLeadingQuartetException(
                    f'got a key signature string that is not supported: {keyValue}'
                ) from e
        else:
            try:
                isKey = ('Key' in keyValue.classes)
                if isKey is False:
                    raise AttributeError
            except AttributeError:  # pragma: no cover  # pylint: disable=raise-missing-from
                raise VoiceLeadingQuartetException(
                    'got a key signature that is not a string or music21 Key '
                    + f'object: {keyValue}'
                )
        self._key = keyValue

    def _setVoiceNote(self, value, which):
        if value is None:
            setattr(self, which, None)
        elif isinstance(value, str):
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
            except Exception as e:  # pragma: no cover  # pylint: disable=broad-except
                raise VoiceLeadingQuartetException(
                    f'not a valid note specification: {value!r}'
                ) from e

    def _getV1n1(self):
        return self._v1n1

    def _setV1n1(self, value):
        self._setVoiceNote(value, '_v1n1')

    v1n1 = property(_getV1n1, _setV1n1, doc='''
        set note1 for voice 1

        >>> vl = voiceLeading.VoiceLeadingQuartet('C', 'D', 'E', 'F')
        >>> vl.v1n1
        <music21.note.Note C>
        ''')

    def _getV1n2(self):
        return self._v1n2

    def _setV1n2(self, value):
        self._setVoiceNote(value, '_v1n2')

    v1n2 = property(_getV1n2, _setV1n2, doc='''
        set note 2 for voice 1

        >>> vl = voiceLeading.VoiceLeadingQuartet('C', 'D', 'E', 'F')
        >>> vl.v1n2
        <music21.note.Note D>
        ''')


    def _getV2n1(self):
        return self._v2n1

    def _setV2n1(self, value):
        self._setVoiceNote(value, '_v2n1')

    v2n1 = property(_getV2n1, _setV2n1, doc='''
        set note 1 for voice 2

        >>> vl = voiceLeading.VoiceLeadingQuartet('C', 'D', 'E', 'F')
        >>> vl.v2n1
        <music21.note.Note E>
        ''')

    def _getV2n2(self):
        return self._v2n2

    def _setV2n2(self, value):
        self._setVoiceNote(value, '_v2n2')

    v2n2 = property(_getV2n2, _setV2n2, doc='''
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

    def motionType(self, *, allowAntiParallel=False):
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

        >>> n1_d4 = note.Note('D4')
        >>> n2_e4 = note.Note('E4')
        >>> m1_f4 = note.Note('F4')
        >>> m2_b4 = note.Note('B4')
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1_d4, n2_e4, m1_f4, m2_b4)
        >>> vl.motionType()
        <MotionType.similar: 'Similar'>

        >>> n1_a4 = note.Note('A4')
        >>> n2_c5 = note.Note('C5')
        >>> m1_d4 = note.Note('D4')
        >>> m2_f4 = note.Note('F4')
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1_a4, n2_c5, m1_d4, m2_f4)
        >>> vl.motionType()
        <MotionType.parallel: 'Parallel'>
        >>> print(vl.motionType())
        MotionType.parallel
        >>> vl.motionType() == 'Parallel'
        True

        Demonstrations of other motion types.

        Contrary:

        >>> n1_d5 = note.Note('D5')   # D5, C5 against D4, F4
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1_d5, n2_c5, m1_d4, m2_f4)
        >>> vl.motionType()
        <MotionType.contrary: 'Contrary'>

        Oblique:

        >>> n1_c5 = note.Note('C5')   # C5, C5 against D4, F4
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1_c5, n2_c5, m1_d4, m2_f4)
        >>> vl.motionType()
        <MotionType.oblique: 'Oblique'>

        No motion (if I had a dollar for every time I forgot to teach
        that this is not a form of oblique motion...):

        >>> m1_f4 = note.Note('F4')   # C5, C5 against F4, F4
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1_c5, n2_c5, m1_f4, m2_f4)
        >>> vl.motionType()
        <MotionType.noMotion: 'No Motion'>


        Anti-parallel motion has to be explicitly enabled to appear:

        >>> n1_a5 = note.Note('A5')
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1_a5, n2_c5, m1_d4, m2_f4)
        >>> vl.motionType()  # anti-parallel fifths
        <MotionType.contrary: 'Contrary'>
        >>> vl.motionType(allowAntiParallel=True)
        <MotionType.antiParallel: 'Anti-Parallel'>

        Changed in v.6 -- anti-parallel motion was supposed to be
        able to be returned in previous versions, but a bug prevented it.
        To preserve backwards compatibility, it must be explicitly enabled.
        '''
        motionType = ''
        if self.obliqueMotion():
            motionType = MotionType.oblique
        elif self.parallelMotion():
            motionType = MotionType.parallel
        elif self.similarMotion():
            motionType = MotionType.similar
        elif allowAntiParallel and self.antiParallelMotion():
            motionType = MotionType.antiParallel
        elif self.contraryMotion():
            motionType = MotionType.contrary
        elif self.noMotion():
            motionType = MotionType.noMotion

        return motionType

    def noMotion(self) -> bool:
        '''
        Returns True if no voice moves in this "voice-leading" moment

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
            if iV.name != 'P1':
                return False
        return True

    def obliqueMotion(self) -> bool:
        '''
        Returns True if one voice remains the same and another moves.  i.e.,
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
            if 'P1' not in iNames:
                return False
            else:
                return True

    def similarMotion(self) -> bool:
        '''
        Returns True if the two voices both move in the same direction.
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

    def parallelMotion(
        self,
        requiredInterval=None,
        allowOctaveDisplacement=False
    ) -> bool:
        '''
        Returns True if both the first and second intervals are the same sized
        generic interval.

        If requiredInterval is set, returns True only if both intervals are that
        generic or specific interval.

        allowOctaveDisplacement treats motion as parallel even if any of the intervals
        are displaced by octaves, except in the case of unisons and octaves, which
        are always treated as distinct.

        We will make the examples shorter with this abbreviation:
        >>> N = note.Note

        >>> vl = voiceLeading.VoiceLeadingQuartet(N('G4'), N('G4'), N('G3'), N('G3'))
        >>> vl.parallelMotion()  # not even similar motion
        False

        >>> vl = voiceLeading.VoiceLeadingQuartet(N('G4'), N('B4'), N('G3'), N('A3'))
        >>> vl.parallelMotion()  # similar motion, but no kind of parallel
        False

        >>> vl = voiceLeading.VoiceLeadingQuartet(N('G4'), N('G5'), N('G4'), N('G5'))
        >>> vl.parallelMotion()  # parallel unisons
        True

        >>> vl.parallelMotion('P1')
        True

        octaves never equivalent to unisons

        >>> vl.parallelMotion('P8', allowOctaveDisplacement=True)
        False

        >>> vl = voiceLeading.VoiceLeadingQuartet(N('A4'), N('B4'), N('D3'), N('E3'))
        >>> vl.parallelMotion()  # parallel fifths
        True

        >>> vl = voiceLeading.VoiceLeadingQuartet(N('A4'), N('B5'), N('D3'), N('E3'))
        >>> vl.parallelMotion()  # 5th to a 12th
        False
        >>> vl.parallelMotion(allowOctaveDisplacement=True)
        True

        >>> vl = voiceLeading.VoiceLeadingQuartet(N('A4'), N('Bb4'), N('F4'), N('G4'))
        >>> vl.parallelMotion(3)  # parallel thirds ...
        True
        >>> vl.parallelMotion('M3')  # ... but not parallel MAJOR thirds
        False

        >>> vl = voiceLeading.VoiceLeadingQuartet(N('D4'), N('E4'), N('F3'), N('G3'))
        >>> gi = interval.GenericInterval(6)
        >>> vl.parallelMotion(gi)  # these are parallel sixths ...
        True

        These are also parallel major sixths

        >>> i = interval.Interval('M6')
        >>> di = interval.DiatonicInterval('major', 6)
        >>> vl.parallelMotion(i) and vl.parallelMotion(di)
        True

        >>> vl = voiceLeading.VoiceLeadingQuartet(N('D5'), N('E6'), N('F3'), N('G3'))
        >>> vl.parallelMotion(gi)  # octave displacement
        False
        >>> vl.parallelMotion(gi, allowOctaveDisplacement=True)
        True
        '''

        if not self.similarMotion():
            return False

        elif (self.vIntervals[0].generic.directed != self.vIntervals[1].generic.directed
              and not allowOctaveDisplacement):
            return False

        elif (self.vIntervals[0].generic.semiSimpleUndirected
                != self.vIntervals[1].generic.semiSimpleUndirected):
            return False

        elif requiredInterval is None:
            return True

        else:
            intervalsAreValid = False

            if isinstance(requiredInterval, interval.GenericInterval):
                intervalsAreValid = (self.vIntervals[0].generic.semiSimpleUndirected
                                     == requiredInterval.semiSimpleUndirected)

            if isinstance(requiredInterval, int):
                # assume the user wants a parallel generic interval
                requiredInterval = interval.GenericInterval(requiredInterval)
                intervalsAreValid = (self.vIntervals[0].generic.semiSimpleUndirected
                                     == requiredInterval.semiSimpleUndirected)

            if isinstance(requiredInterval, str):
                requiredInterval = interval.Interval(requiredInterval)
                intervalsAreValid = (self.vIntervals[0].semiSimpleName
                                        == requiredInterval.semiSimpleName
                                     and self.vIntervals[1].semiSimpleName
                                        == requiredInterval.semiSimpleName)

            elif isinstance(requiredInterval, (interval.Interval, interval.DiatonicInterval)):
                intervalsAreValid = (self.vIntervals[0].semiSimpleName
                                        == requiredInterval.semiSimpleName
                                     and self.vIntervals[1].semiSimpleName
                                        == requiredInterval.semiSimpleName)

            return intervalsAreValid



    def contraryMotion(self) -> bool:
        '''
        Returns True if both voices move in opposite directions

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

    def outwardContraryMotion(self) -> bool:
        '''
        Returns True if both voices move outward by contrary motion

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
        return (self.contraryMotion()
                and self.hIntervals[0].direction == interval.Direction.ASCENDING)

    def inwardContraryMotion(self) -> bool:
        '''
        Returns True if both voices move inward by contrary motion

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
        return (self.contraryMotion()
                and self.hIntervals[0].direction == interval.Direction.DESCENDING)

    def antiParallelMotion(self, simpleName=None) -> bool:
        '''Returns True if the simple interval before is the same as the simple
        interval after and the motion is contrary. if simpleName is
        specified as an Interval object or a string then it only returns
        true if the simpleName of both intervals is the same as simpleName
        (i.e., use to find antiParallel fifths)

        >>> n11 = note.Note('C4')
        >>> n12 = note.Note('D3')  # descending 7th
        >>> n21 = note.Note('G4')
        >>> n22 = note.Note('A4')  # ascending 2nd
        >>> vlq1 = voiceLeading.VoiceLeadingQuartet(n11, n12, n21, n22)
        >>> vlq1.antiParallelMotion()
        True

        >>> vlq1.antiParallelMotion('M2')
        False

        >>> vlq1.antiParallelMotion('P5')
        True

        We can also use interval objects

        >>> p5Obj = interval.Interval('P5')
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
        '''
        if not self.contraryMotion():
            return False
        else:
            if self.vIntervals[0].simpleName == self.vIntervals[1].simpleName:
                if simpleName is None:
                    return True
                else:
                    if isinstance(simpleName, str):
                        if self.vIntervals[0].simpleName == simpleName:
                            return True
                        else:
                            return False
                    else:  # assume Interval object
                        if self.vIntervals[0].simpleName == simpleName.simpleName:
                            return True
                        else:
                            return False
            else:
                return False

    def parallelInterval(self, thisInterval) -> bool:
        '''
        Returns True if there is a parallel motion or antiParallel motion of
        this type (thisInterval should be an Interval object)

        >>> n11 = note.Note('G4')
        >>> n12a = note.Note('A4')  # ascending 2nd

        >>> n21 = note.Note('C4')
        >>> n22a = note.Note('D4')  # ascending 2nd

        >>> vlq1 = voiceLeading.VoiceLeadingQuartet(n11, n12a, n21, n22a)
        >>> vlq1.parallelInterval(interval.Interval('P5'))
        True

        >>> vlq1.parallelInterval(interval.Interval('P8'))
        False

        Antiparallel fifths also are True

        >>> n22b = note.Note('D3')  # descending 7th
        >>> vlq2 = voiceLeading.VoiceLeadingQuartet(n11, n12a, n21, n22b)
        >>> vlq2.parallelInterval(interval.Interval('P5'))
        True

        But Antiparallel other interval are not:

        >>> N = note.Note
        >>> vlq2a = voiceLeading.VoiceLeadingQuartet(N('C5'), N('C6'), N('C4'), N('C3'))
        >>> vlq2a.parallelInterval(interval.Interval('P5'))
        False
        >>> vlq2a.parallelInterval(interval.Interval('P8'))
        True


        Non-parallel intervals are, of course, False

        >>> n12b = note.Note('B4')  # ascending 3rd
        >>> vlq3 = voiceLeading.VoiceLeadingQuartet(n11, n12b, n21, n22b)
        >>> vlq3.parallelInterval(interval.Interval('P5'))
        False
        '''

        return (
            self.parallelMotion(
                requiredInterval=thisInterval,
                allowOctaveDisplacement=True
            )
            or self.antiParallelMotion(thisInterval)
        )


    def parallelFifth(self) -> bool:
        '''
        Returns True if the motion is a parallel or antiparallel Perfect Fifth,
        allowing displacement by an octave (e.g., 5th to a 12th).

        We will make the examples shorter with this abbreviation:

        >>> N = note.Note

        Parallel fifths

        >>> vlq = voiceLeading.VoiceLeadingQuartet(N('G4'), N('A4'), N('C4'), N('D4'))
        >>> vlq.parallelFifth()
        True

        5th -> 12th in similar motion

        >>> vlq = voiceLeading.VoiceLeadingQuartet(N('G4'), N('A5'), N('C4'), N('D4'))
        >>> vlq.parallelFifth()
        True

        5th -> 12th in antiparallel motion

        >>> vlq = voiceLeading.VoiceLeadingQuartet(N('G4'), N('A4'), N('C4'), N('D3'))
        >>> vlq.parallelFifth()
        True

        Note that diminished fifth moving to perfect fifth is not a parallelFifth

        >>> vlq = voiceLeading.VoiceLeadingQuartet(N('G4'), N('A4'), N('C#4'), N('D4'))
        >>> vlq.parallelFifth()
        False

        Nor is P5 moving to d5.

        >>> vlq = voiceLeading.VoiceLeadingQuartet(N('G4'), N('Ab4'), N('C4'), N('D4'))
        >>> vlq.parallelFifth()
        False
        '''
        return self.parallelInterval(self.fifth)

    def parallelOctave(self) -> bool:
        '''
        Returns True if the motion is a parallel Perfect Octave...
        a concept so abhorrent we shudder to illustrate it with an example, but alas, we must:

        We will make the examples shorter with this abbreviation:
        >>> N = note.Note

        >>> vlq = voiceLeading.VoiceLeadingQuartet(N('C5'), N('D5'), N('C4'), N('D4'))
        >>> vlq.parallelOctave()
        True

        >>> vlq = voiceLeading.VoiceLeadingQuartet(N('C6'), N('D6'), N('C4'), N('D4'))
        >>> vlq.parallelOctave()
        True

        Or False if the motion is according to the rules of God's own creation:

        >>> vlq = voiceLeading.VoiceLeadingQuartet(N('C4'), N('D4'), N('C4'), N('D4'))
        >>> vlq.parallelOctave()
        False
        '''
        return self.parallelInterval(self.octave)

    def parallelUnison(self) -> bool:
        '''
        Returns True if the motion is a parallel Perfect Unison (and not
        Perfect Octave, etc.)

        We will make the examples shorter with this abbreviation:

        >>> N = note.Note
        >>> vlq = voiceLeading.VoiceLeadingQuartet(N('C4'), N('D4'), N('C4'), N('D4'))
        >>> vlq.parallelUnison()
        True

        >>> vlq  = voiceLeading.VoiceLeadingQuartet(N('C5'), N('D5'), N('C4'), N('D4'))
        >>> vlq.parallelUnison()
        False
        '''
        return self.parallelInterval(self.unison)

    def parallelUnisonOrOctave(self) -> bool:
        '''
        Returns True if the VoiceLeadingQuartet has motion by parallel
        octave or parallel unison

        >>> voiceLeading.VoiceLeadingQuartet(
        ...     note.Note('C4'),
        ...     note.Note('D4'),
        ...     note.Note('C3'),
        ...     note.Note('D3')
        ...     ).parallelUnisonOrOctave()
        True

        >>> voiceLeading.VoiceLeadingQuartet(
        ...     note.Note('C4'),
        ...     note.Note('D4'),
        ...     note.Note('C4'),
        ...     note.Note('D4')
        ...     ).parallelUnisonOrOctave()
        True
        '''

        return self.parallelUnison() or self.parallelOctave()

    def hiddenInterval(self, thisInterval) -> bool:
        '''
        Returns True if there is a hidden interval that matches
        thisInterval.

        N.B. -- this method finds ALL hidden intervals,
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
        >>> n2 = note.Note('G4')
        >>> m1 = note.Note('B4')
        >>> m2 = note.Note('D5')
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.hiddenInterval(interval.Interval('P5'))
        False

        >>> n1 = note.Note('E4')
        >>> n2 = note.Note('G4')
        >>> m1 = note.Note('B4')
        >>> m2 = note.Note('D6')
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.hiddenInterval(interval.Interval('P5'))
        False
        '''
        if self.parallelMotion(allowOctaveDisplacement=True):
            return False
        elif not self.similarMotion():
            return False
        else:
            if isinstance(thisInterval, str):
                thisInterval = interval.Interval(thisInterval)

            if self.vIntervals[1].simpleName == thisInterval.simpleName:
                return True
            else:
                return False

    def hiddenFifth(self) -> bool:
        '''
        Calls :meth:`~music21.voiceLeading.VoiceLeadingQuartet.hiddenInterval`
        by passing a fifth
        '''
        return self.hiddenInterval(self.fifth)

    def hiddenOctave(self) -> bool:
        '''
        Calls hiddenInterval by passing an octave
        '''
        return self.hiddenInterval(self.octave)

    def voiceOverlap(self) -> bool:
        '''
        Returns True if the second note in V1 is lower than the first in V2, or
        if the second note in V2 is higher than the first note in V1.

        We will make the examples shorter with this abbreviation:
        >>> N = note.Note

        >>> vl = voiceLeading.VoiceLeadingQuartet(N('A4'), N('B4'), N('F4'), N('G4'))
        >>> vl.voiceOverlap()  # no overlap
        False

        >>> vl = voiceLeading.VoiceLeadingQuartet(N('A4'), N('B4'), N('F4'), N('A4'))
        >>> vl.voiceOverlap()  # Motion to the SAME note is not considered overlap
        False

        >>> vl = voiceLeading.VoiceLeadingQuartet(N('A4'), N('C4'), N('F4'), N('Bb4'))
        >>> vl.voiceOverlap()  # V2 overlaps V1
        True

        >>> vl = voiceLeading.VoiceLeadingQuartet(N('A4'), N('E4'), N('F4'), N('D4'))
        >>> vl.voiceOverlap()  # V1 overlaps V2
        True
        '''
        if self.v1n2.pitch < self.v2n1.pitch or self.v2n2.pitch > self.v1n1.pitch:
            return True
        else:
            return False

    def voiceCrossing(self) -> bool:
        '''
        Returns True if either note in V1 is lower than the simultaneous note in V2.

        We will make the examples shorter with this abbreviation:

        >>> N = note.Note

        >>> vl = voiceLeading.VoiceLeadingQuartet(N('A4'), N('A4'), N('G4'), N('G4'))
        >>> vl.voiceCrossing()  # nothing crossed
        False

        >>> vl = voiceLeading.VoiceLeadingQuartet(N('A4'), N('F4'), N('G4'), N('G4'))
        >>> vl.voiceCrossing()  # second interval is crossed
        True

        >>> vl = voiceLeading.VoiceLeadingQuartet(N('F4'), N('A4'), N('G4'), N('G4'))
        >>> vl.voiceCrossing()  # first interval crossed
        True

        >>> vl = voiceLeading.VoiceLeadingQuartet(N('F4'), N('F4'), N('G4'), N('G4'))
        >>> vl.voiceCrossing()  # both crossed
        True
        '''
        if self.v1n1.pitch < self.v2n1.pitch or self.v1n2.pitch < self.v2n2.pitch:
            return True
        else:
            return False

    def isProperResolution(self) -> bool:
        '''
        Checks whether the voice-leading quartet resolves correctly according to standard
        counterpoint rules. If the first harmony is dissonant (P4, d5, A4, or m7) it checks
        that these are correctly resolved. If the first harmony is consonant, True is returned.

        The key parameter should be specified to check for motion in the bass from specific
        note degrees. If it is not set, then no checking for scale degrees takes place.

        Currently implements the following resolutions:

            P4:     Top voice must resolve downward.

            A4:     out by contrary motion to a sixth, with chordal seventh resolving
                    down to a third in the bass.

            d5:     in by contrary motion to a third, with 7 resolving up to 1 in the bass

            m7:     Resolves to a third with a leap from 5 to 1 in the bass


        We will make the examples shorter with this abbreviation:
        >>> N = note.Note

        >>> n1 = note.Note('B-4')
        >>> n2 = note.Note('A4')
        >>> m1 = note.Note('E4')
        >>> m2 = note.Note('F4')
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.isProperResolution()  # d5 resolves inward
        True
        >>> m2.pitch.name = 'D'
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.isProperResolution()  # d5 resolves outward
        False
        >>> vl.key = 'B-'
        >>> vl.isProperResolution()  # not on scale degrees that need resolution
        True

        >>> n1 = note.Note('D4')
        >>> n2 = note.Note('C4')
        >>> m1 = note.Note('G#3')
        >>> m2 = note.Note('A3')
        >>> k = key.Key('a')
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2, k)
        >>> vl.isProperResolution()  # d5 with #7 in minor handled correctly
        True

        >>> n1 = note.Note('E5')
        >>> n2 = note.Note('F5')
        >>> m1 = note.Note('B-4')
        >>> m2 = note.Note('A4')
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.isProperResolution()  # A4 resolves outward
        True
        >>> m2.pitch.nameWithOctave = 'D5'
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.isProperResolution()  # A4 resolves inward
        False
        >>> vl.key = 'B-'
        >>> vl.isProperResolution()  # A4 not on scale degrees that need resolution
        True
        >>> vl.key = 'F'
        >>> vl.isProperResolution()  # A4 on scale degrees that need resolution
        False

        >>> n1 = note.Note('B-4')
        >>> n2 = note.Note('A4')
        >>> m1 = note.Note('C4')
        >>> m2 = note.Note('F4')
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.isProperResolution()  # m7
        True
        >>> m2.pitch.nameWithOctave = 'F3'
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.isProperResolution()  # m7 with similar motion
        True
        >>> vl.key = 'B-'
        >>> vl.isProperResolution()  # m7 not on scale degrees that need resolution
        True
        >>> vl.key = 'F'
        >>> vl.isProperResolution()  # m7 on scale degrees that need resolution
        True

        P4 on the initial harmony must move down.

        >>> n1 = note.Note('F5')
        >>> n2 = note.Note('G5')
        >>> m1 = note.Note('C4')
        >>> m2 = note.Note('C4')
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.isProperResolution()  # P4 must move down or remain static
        False
        >>> n2.step = 'E'
        >>> vl = voiceLeading.VoiceLeadingQuartet(n1, n2, m1, m2)
        >>> vl.isProperResolution()  # P4 can move down by step or leap
        True

        >>> vl = voiceLeading.VoiceLeadingQuartet('B-4', 'A4', 'C2', 'F2')
        >>> vl.key = key.Key('F')
        >>> vl.isProperResolution()  # not dissonant, True returned
        True
        '''
        if self.noMotion():
            return True

        if self.key:
            keyScale = self.key.getScale(self.key.mode)
            n1degree = keyScale.getScaleDegreeFromPitch(self.v2n1)
            n2degree = keyScale.getScaleDegreeFromPitch(self.v2n2)

            # catches case of #7 in minor
            if self.key.mode == 'minor' and n1degree is None:
                minorScale = scale.MelodicMinorScale(self.key.tonic)
                n1degree = minorScale.getScaleDegreeFromPitch(
                    self.v2n1,
                    direction=scale.DIRECTION_ASCENDING)

        else:
            keyScale = None
            n1degree = None
            n2degree = None

        firstHarmony = self.vIntervals[0].simpleName
        secondHarmony = self.vIntervals[1].generic.simpleUndirected

        if firstHarmony == 'P4':
            if self.v1n1 >= self.v1n2:
                return True
            else:
                return False

        elif firstHarmony == 'A4':
            if keyScale and n1degree != 4:
                return True
            if keyScale and n2degree != 3:
                return False
            return (self.outwardContraryMotion()
                        and secondHarmony == 6)

        elif firstHarmony == 'd5':
            if keyScale and n1degree != 7:
                return True
            if keyScale and n2degree != 1:
                return False
            return (self.inwardContraryMotion()
                        and secondHarmony == 3)

        elif firstHarmony == 'm7':
            if keyScale and n1degree != 5:
                return True
            if keyScale and n2degree != 1:
                return False
            return secondHarmony == 3

        else:
            return True

    def leapNotSetWithStep(self) -> bool:
        '''
        Returns True if there is a leap or skip in once voice then the other voice must
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

    def opensIncorrectly(self) -> bool:
        '''
        TODO(msc): will be renamed to be less dogmatic

        Returns True if the VLQ would be an incorrect opening in
        the style of 16th century Counterpoint (not Bach Chorale style)

        Returns True if the opening or second harmonic interval is PU, P8, or P5,
        to accommodate an anacrusis.
        also checks to see if opening establishes tonic or dominant harmony (uses
        :meth:`~music21.roman.identifyAsTonicOrDominant`

        >>> vl = voiceLeading.VoiceLeadingQuartet('D', 'D', 'D', 'F#')
        >>> vl.key = 'D'
        >>> vl.opensIncorrectly()
        False
        >>> vl = voiceLeading.VoiceLeadingQuartet('B', 'A', 'G#', 'A')
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
        openings = ['P1', 'P5', 'I', 'V']
        return not ((self.vIntervals[0].simpleName in openings
                        or self.vIntervals[1].simpleName in openings)
                      and (r1[0].upper() in openings if r1 is not False else False
                           or r2[0].upper() in openings if r2 is not False else False))

    def closesIncorrectly(self) -> bool:
        '''
        TODO(msc): will be renamed to be less dogmatic

        Returns True if the VLQ would be an incorrect closing in
        the style of 16th century Counterpoint (not Bach Chorale style)

        Returns True if closing harmonic interval is a P8 or PU and the interval
        approaching the close is
        6 - 8, 10 - 8, or 3 - U. Must be in contrary motion, and if in minor key,
        has a leading tone resolves to the tonic.

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
            if self.key.pitchFromDegree(7).transpose('A1').name == self.v1n1.name:
                raisedMinorCorrectly = self.key.getScaleDegreeFromPitch(self.v1n2) == 1
            elif self.key.pitchFromDegree(7).transpose('A1').name == self.v2n1.name:
                raisedMinorCorrectly = self.key.getScaleDegreeFromPitch(self.v1n2) == 1
        else:
            raisedMinorCorrectly = True
        preClosings = (6, 3)
        closingPitches = [self.v1n2.pitch.name, self.v2n2.name]
        return not (self.vIntervals[0].generic.simpleUndirected in preClosings
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

    >>> c = corpus.parse('bach/bwv66.6')
    >>> n1 = c.flat.getElementsByClass(note.Note)[0]
    >>> voiceLeading.getVerticalityFromObject(n1, c)
    <music21.voiceLeading.Verticality
        contentDict={0: [<music21.instrument.Instrument 'P1: Soprano: Instrument 1'>,
                         <music21.clef.TrebleClef>,
                         <music21.key.Key of f# minor>,
                         <music21.meter.TimeSignature 4/4>,
                         <music21.note.Note C#>],
              1: [<music21.instrument.Instrument 'P2: Alto: Instrument 2'>,
                  <music21.clef.TrebleClef>,
                  <music21.key.Key of f# minor>,
                  <music21.meter.TimeSignature 4/4>,
                  <music21.note.Note E>],
              2: [<music21.instrument.Instrument 'P3: Tenor: Instrument 3'>,
                  <music21.clef.BassClef>,
                  <music21.key.Key of f# minor>,
                  <music21.meter.TimeSignature 4/4>,
                  <music21.note.Note A>],
              3: [<music21.instrument.Instrument 'P4: Bass: Instrument 4'>,
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
    offsetOfObject = music21Obj.getOffsetBySite(scoreObjectIsFrom.flat)

    contentDict = {}
    for partNum, partObj in enumerate(scoreObjectIsFrom.parts):
        elementSelection = partObj.flat.getElementsByOffset(offsetOfObject,
                                                         mustBeginInSpan=False,
                                                         classList=classFilterList)
        for el in elementSelection:
            if partNum in contentDict:
                contentDict[partNum].append(el)
            else:
                contentDict[partNum] = [el]
    return Verticality(contentDict)


class Verticality(base.Music21Object):
    '''
    A Verticality (previously called "vertical slice")
    object provides more accessible information about
    vertical moments in a score. A Verticality is
    instantiated by passing in a dictionary of
    the form {partNumber : [ music21Objects ] }

    Verticalities are useful to provide direct and easy access to objects in a part.
    A list of Verticalities, although similar to the list of chords from a chordified score,
    provides easier access to part number
    information and identity of objects in the score. Plus, the objects in a
    Verticality point directly
    to the objects in the score, so modifying a Verticality taken from a
    score is the same as modifying the elements
    of the Verticality in the score directly.

    >>> vs1 = voiceLeading.Verticality({0:[note.Note('A4'), harmony.ChordSymbol('Cm')],
    ...                                 1: [note.Note('F2')]})
    >>> vs1.getObjectsByClass(note.Note)
    [<music21.note.Note A>, <music21.note.Note F>]
    >>> vs1.getObjectsByPart(0, note.Note)
    <music21.note.Note A>
    '''
    #  obsolete:     To create Verticalities out of a score, call
    #                by :meth:`~music21.theoryAnalyzer.getVerticalities`

    _DOC_ATTR = {
        'contentDict': '''Dictionary representing contents of Verticalities.
            the keys of the dictionary
            are the part numbers and the element at each key is a list of
            music21 objects (allows for multiple voices
            in a single part)''',
    }

    def __init__(self, contentDict: dict):
        super().__init__()
        for partNum, element in contentDict.items():
            if not isinstance(element, list):
                contentDict[partNum] = [element]

        self.contentDict = contentDict

    def isConsonant(self):
        '''
        evaluates whether this Verticality moment is consonant or dissonant
        according to the common-practice
        consonance rules. Method generates chord of all simultaneously sounding pitches, then calls
        :meth:`~music21.chord.isConsonant`

        >>> V = voiceLeading.Verticality
        >>> N = note.Note
        >>> V({0:N('A4'), 1:N('B4'), 2:N('A4')}).isConsonant()
        False
        >>> V({0:N('A4'), 1:N('B4'), 2:N('C#4')}).isConsonant()
        False
        >>> V({0:N('C3'), 1:N('G5'), 2:chord.Chord(['C3', 'E4', 'G5'])}).isConsonant()
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
        as a chord. Pretty much returns the Verticality to a chordified output.

        >>> N = note.Note
        >>> vs1 = voiceLeading.Verticality({0:N('A4'), 1:chord.Chord(['B', 'C', 'A']), 2:N('A')})
        >>> vs1.getChord()
        <music21.chord.Chord A4 B C A A>
        >>> voiceLeading.Verticality({0:N('A3'),
        ...                           1:chord.Chord(['F3', 'D4', 'A4']),
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
        ch = chord.Chord(pitches)
        ch.style = self.style
        return ch

    def makeAllSmallestDuration(self):
        '''
        locates the smallest duration of all elements in the Verticality
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
        self.changeDurationOfAllObjects(self.getShortestDuration())

    def makeAllLargestDuration(self):
        '''
        locates the largest duration of all elements in the Verticality
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
        self.changeDurationOfAllObjects(self.getLongestDuration())

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

    def changeDurationOfAllObjects(self, newQuarterLength):
        '''
        changes the duration of all objects in Verticality

        >>> n1 =  note.Note('C4')
        >>> n1.quarterLength = 1
        >>> n2 =  note.Note('G4')
        >>> n2.quarterLength = 2
        >>> cs = harmony.ChordSymbol('C')
        >>> cs.quarterLength = 4
        >>> vs1 = voiceLeading.Verticality({0:n1, 1:n2, 2:cs})
        >>> vs1.changeDurationOfAllObjects(1.5)
        >>> [x.quarterLength for x in vs1.objects]
        [1.5, 1.5, 1.5]

        Note: capitalization of function changed in v5.7
        '''
        for obj in self.objects:
            obj.quarterLength = newQuarterLength

    def getObjectsByPart(self, partNum, classFilterList=None):
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
        if not common.isIterable(classFilterList):
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
        returns a list of all objects in the Verticality of a type contained
        in the classFilterList. Optionally
        specify part numbers to only search for matching objects

        >>> N = note.Note
        >>> vs1 = voiceLeading.Verticality({0: [N('A4'), harmony.ChordSymbol('C')],
        ...                                 1: [N('C')],
        ...                                 2: [N('B'), N('F#')]})
        >>> vs1.getObjectsByClass('Note')
        [<music21.note.Note A>, <music21.note.Note C>,
         <music21.note.Note B>, <music21.note.Note F#>]
        >>> vs1.getObjectsByClass('Note', [1, 2])
        [<music21.note.Note C>, <music21.note.Note B>, <music21.note.Note F#>]

        '''
        if not common.isIterable(classFilterList):
            classFilterList = [classFilterList]
        retList = []
        for part, objList in self.contentDict.items():
            for m21object in objList:

                if m21object is None or not m21object.isClassOrSubclass(classFilterList):
                    continue
                else:
                    if partNums and part not in partNums:
                        continue
                    retList.append(m21object)
        return retList

    @property
    def objects(self):
        '''
        return a list of all the music21 objects in the Verticality

        >>> vs1 = voiceLeading.Verticality({0:[harmony.ChordSymbol('C'), note.Note('A4'),],
        ...                                 1:[note.Note('C')]})
        >>> vs1.objects
        [<music21.harmony.ChordSymbol C>, <music21.note.Note A>, <music21.note.Note C>]
        '''
        retList = []
        for unused_part, objList in self.contentDict.items():
            for m21object in objList:
                if m21object is not None:
                    retList.append(m21object)
        return retList

    def getStream(self, streamVSCameFrom=None):
        '''
        returns the stream representation of this Verticality. Optionally pass in
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

                ks = foundObj.getContextByClass('KeySignature')
                ts = foundObj.getContextByClass('TimeSignature')
                cl = foundObj.getContextByClass('Clef')

                if cl:
                    p.append(cl)
                if ks:
                    p.append(ks)
                if ts:
                    p.append(ts)
                p.append(foundObj)
            if len(elementList) > 1:
                for el in elementList:
                    p.insert(stream.Voice([el]))  # probably wrong! Need to fix!!!
            else:
                p.insert(elementList[0])
            retStream.insert(p)
        return retStream


    def offset(self, leftAlign=True):
        '''
        returns the overall offset of the Verticality. Typically, this would just be the
        offset of each object in the Verticality,
        and each object would have the same offset.
        However, if the duration of one object in the slice is different than the duration
        of another,
        and that other starts after the first, but the first is still sounding, then the
        offsets would be
        different. In this case, specify leftAlign=True to return the lowest valued-offset
        of all the objects
        in the Verticality. If you prefer the offset of the right-most starting object,
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
        sets each element on the Verticality to have the passed in lyric

        >>> h = voiceLeading.Verticality({1:note.Note('C'), 2:harmony.ChordSymbol('C')})
        >>> h.lyric = 'Verticality 1'
        >>> h.getStream().flat.getElementsByClass(note.Note)[0].lyric
        'Verticality 1'
        ''')

    def _reprInternal(self):
        return f'contentDict={self.contentDict}'

    def _setColor(self, color):
        self.style.color = color
        for obj in self.objects:
            obj.style.color = color

    def _getColor(self):
        return self.style.color

    color = property(_getColor, _setColor, doc='''
        sets the color of each element in the Verticality

        >>> vs1 = voiceLeading.Verticality({1:note.Note('C'), 2:harmony.ChordSymbol('D')})
        >>> vs1.color = 'blue'
        >>> [(x, x.style.color) for x in vs1.objects]
        [(<music21.note.Note C>, 'blue'), (<music21.harmony.ChordSymbol D>, 'blue')]
    ''')


class VerticalityNTuplet(base.Music21Object):
    '''
    a collection of n number of Verticalities. These objects are useful when
    analyzing counterpoint
    motion and music theory elements such as passing tones
    '''

    def __init__(self, listOfVerticalities):
        super().__init__()

        self.verticalities = listOfVerticalities
        self.nTupletNum = len(listOfVerticalities)

        self.chordList = []
        if listOfVerticalities:
            self._calcChords()

    def _calcChords(self):
        for vs in self.verticalities:
            self.chordList.append(chord.Chord(vs.getObjectsByClass(note.Note)))

    def _reprInternal(self):
        return f'listOfVerticalities={self.verticalities}'



class VerticalityTriplet(VerticalityNTuplet):
    '''a collection of three Verticalities'''

    def __init__(self, listOfVerticalities):
        super().__init__(listOfVerticalities)

        self.tnlsDict = {}  # defaultdict(int)  # Three Note Linear Segments
        self._calcTNLS()

    def _calcTNLS(self):
        '''
        calculates the three note linear segments if only three Verticalities provided
        '''
        for partNum in range(min(len(self.verticalities[0].getObjectsByClass(note.Note)),
                                    len(self.verticalities[1].getObjectsByClass(note.Note)),
                                    len(self.verticalities[2].getObjectsByClass(note.Note)))
                             ):
            self.tnlsDict[partNum] = ThreeNoteLinearSegment(
                [
                    self.verticalities[0].getObjectsByPart(partNum, note.Note),
                    self.verticalities[1].getObjectsByPart(partNum, note.Note),
                    self.verticalities[2].getObjectsByPart(partNum, note.Note)
                ]
            )


    def hasPassingTone(self, partNumToIdentify, unaccentedOnly=False):
        '''
        return true if this Verticality triplet contains a passing tone
        music21 currently identifies passing tones by analyzing both horizontal motion
        and vertical motion.
        It first checks to see if the note could be a passing tone based on the notes
        linearly adjacent to it.
        It then checks to see if the note's vertical context is dissonant, while the
        Verticalities
        to the left and right are consonant

        partNum is the part (starting with 0) to identify the passing tone

        >>> vs1 = voiceLeading.Verticality({0:note.Note('A4'), 1:note.Note('F2')})
        >>> vs2 = voiceLeading.Verticality({0:note.Note('B-4'), 1:note.Note('F2')})
        >>> vs3 = voiceLeading.Verticality({0:note.Note('C5'), 1:note.Note('E2')})
        >>> vt = voiceLeading.VerticalityTriplet([vs1, vs2, vs3])
        >>> vt.hasPassingTone(0)
        True
        >>> vt.hasPassingTone(1)
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
        # check that the Verticality containing the passing tone is dissonant

    def hasNeighborTone(self, partNumToIdentify, unaccentedOnly=False):
        '''
        return true if this Verticality triplet contains a neighbor tone
        music21 currently identifies neighbor tones by analyzing both horizontal motion
        and vertical motion.
        It first checks to see if the note could be a neighbor tone based on the notes
        linearly adjacent to it.
        It then checks to see if the note's vertical context is dissonant,
        while the Verticalities
        to the left and right are consonant

        partNum is the part (starting with 0) to identify the passing tone
        for use on 3 Verticalities (3-tuplet)

        >>> vs1 = voiceLeading.Verticality({0:note.Note('E-4'), 1: note.Note('C3')})
        >>> vs2 = voiceLeading.Verticality({0:note.Note('E-4'), 1: note.Note('B2')})
        >>> vs3 = voiceLeading.Verticality({0:note.Note('C5'), 1: note.Note('C3')})
        >>> vt = voiceLeading.VerticalityTriplet([vs1, vs2, vs3])
        >>> vt.hasNeighborTone(1)
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
        super().__init__()
        self._noteList = []
        for value in noteList:
            if value is None:
                self._noteList.append(None)
            elif isinstance(value, str):
                self._noteList.append(note.Note(value))
            else:
                try:
                    if value.isClassOrSubclass([note.Note, pitch.Pitch]):
                        self._noteList.append(value)
                except (AttributeError, NameError):
                    self._noteList.append(None)

    @property
    def noteList(self):
        '''
        Read-only property -- returns a copy of the list of notes in the
        linear segment.

        >>> n = voiceLeading.NNoteLinearSegment(['A', 'B5', 'C', 'F#'])
        >>> n.noteList
        [<music21.note.Note A>, <music21.note.Note B>,
         <music21.note.Note C>, <music21.note.Note F#>]
        '''
        return self._noteList[:]


    def _getMelodicIntervals(self):
        tempListOne = self.noteList[:-1]
        tempListTwo = self.noteList[1:]
        melodicIntervalList = []
        for n1, n2 in zip(tempListOne, tempListTwo):
            if n1 and n2:
                melodicIntervalList.append(interval.Interval(n1, n2))
            else:
                melodicIntervalList.append(None)
        return melodicIntervalList

    melodicIntervals = property(_getMelodicIntervals, doc='''
        calculates the melodic intervals and returns them as a list,
        with the interval at 0 being the interval between the first and second note.

        >>> linSeg = voiceLeading.NNoteLinearSegment([note.Note('A'), note.Note('B'),
        ...            note.Note('C'), note.Note('D')])
        >>> linSeg.melodicIntervals
        [<music21.interval.Interval M2>,
         <music21.interval.Interval M-7>,
         <music21.interval.Interval M2>]
        ''')


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

    >>> ex = voiceLeading.ThreeNoteLinearSegment('C#4', 'D4', 'E-4')
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

    >>> ex2 = voiceLeading.ThreeNoteLinearSegment('a', 'b', 'c')
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

    def __init__(self, noteListOrN1=None, n2=None, n3=None):
        if common.isIterable(noteListOrN1):
            super().__init__(noteListOrN1)
        else:
            super().__init__([noteListOrN1, n2, n3])

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
        elif isinstance(value, str):
            return note.Note(value)
        else:
            try:
                if value.isClassOrSubclass([note.Note, pitch.Pitch]):
                    return value
                else:
                    return None
            except AttributeError as e:  # pragma: no cover
                raise ThreeNoteLinearSegmentException(
                    f'not a valid note specification: {value!r}'
                ) from e


    n1 = property(_getN1, _setN1, doc='''
        get or set the first note (left-most) in the segment
        ''')
    n2 = property(_getN2, _setN2, doc='''
        get or set the middle note in the segment
        ''')
    n3 = property(_getN3, _setN3, doc='''
        get or set the last note (right-most) in the segment
        ''')

    def _getILeftToRight(self):
        if self.n1 and self.n3:
            return interval.Interval(self.n1, self.n3)
        else:
            return None

    def _getILeft(self):
        return self.melodicIntervals[0]

    def _getIRight(self):
        return self.melodicIntervals[1]

    iLeftToRight = property(_getILeftToRight, doc='''
        get the interval between the left-most note and the right-most note
        (read-only property)

        >>> tnls = voiceLeading.ThreeNoteLinearSegment('C', 'E', 'G')
        >>> tnls.iLeftToRight
        <music21.interval.Interval P5>
        ''')

    iLeft = property(_getILeft, doc='''
        get the interval between the left-most note and the middle note
        (read-only property)

        >>> tnls = voiceLeading.ThreeNoteLinearSegment('A', 'B', 'G')
        >>> tnls.iLeft
        <music21.interval.Interval M2>
        ''')
    iRight = property(_getIRight, doc='''
        get the interval between the middle note and the right-most note
        (read-only property)

        >>> tnls = voiceLeading.ThreeNoteLinearSegment('A', 'B', 'G')
        >>> tnls.iRight
        <music21.interval.Interval M-3>
        ''')

    def _reprInternal(self):
        return f'n1={self.n1} n2={self.n2} n3={self.n3}'

    def color(self, color='red', noteList=(2,)):
        '''
        color all the notes in noteList (1, 2, 3). Default is to color
        only the second note red

        DEPRECATED.
        '''
        if 1 in noteList:
            self.n1.style.color = color
        if 2 in noteList:
            self.n2.style.color = color
        if 3 in noteList:
            self.n3.style.color = color

    def _isComplete(self) -> bool:
        return (self.n1 is not None) and (self.n2 is not None) and (self.n3 is not None)
        # if any of these are None, it isn't complete

    def couldBePassingTone(self) -> bool:
        '''
        checks if the two intervals are steps and if these steps
        are moving in the same direction. Returns True if the tone is
        identified as either a chromatic passing tone or a diatonic passing
        tone. Only major and minor diatonic passing tones are recognized (not
        pentatonic or scales beyond twelve-notes). Does NOT check if tone is non harmonic

        Accepts pitch or note objects; method is dependent on octave information

        >>> voiceLeading.ThreeNoteLinearSegment('C#4', 'D4', 'E-4').couldBePassingTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('C3', 'D3', 'E3').couldBePassingTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('E-3', 'F3', 'G-3').couldBePassingTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('C3', 'C3', 'C3').couldBePassingTone()
        False
        >>> voiceLeading.ThreeNoteLinearSegment('A3', 'C3', 'D3').couldBePassingTone()
        False

        Directionality must be maintained

        >>> voiceLeading.ThreeNoteLinearSegment('B##3', 'C4', 'D--4').couldBePassingTone()
        False

        If no octave is given then ._defaultOctave is used.  This is generally octave 4

        >>> voiceLeading.ThreeNoteLinearSegment('C', 'D', 'E').couldBePassingTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('C4', 'D', 'E').couldBePassingTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('C5', 'D', 'E').couldBePassingTone()
        False

        Method returns True if either a chromatic passing tone or a diatonic passing
        tone is identified. Spelling of the pitch does matter!

        >>> voiceLeading.ThreeNoteLinearSegment('B3', 'C4', 'B##3').couldBePassingTone()
        False
        >>> voiceLeading.ThreeNoteLinearSegment('A##3', 'C4', 'E---4').couldBePassingTone()
        False
        >>> voiceLeading.ThreeNoteLinearSegment('B3', 'C4', 'D-4').couldBePassingTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('B3', 'C4', 'C#4').couldBePassingTone()
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

        >>> tls = voiceLeading.ThreeNoteLinearSegment('B3', 'C4', 'C#4')
        >>> tls.couldBeDiatonicPassingTone()
        False

        >>> tls = voiceLeading.ThreeNoteLinearSegment('C3', 'D3', 'E3')
        >>> tls.couldBeDiatonicPassingTone()
        True
        '''
        return (self._isComplete()
                and self.iLeftToRight.generic.isSkip
                and self.iLeft.generic.undirected == 2
                and self.iRight.generic.undirected == 2
                and self.iLeft.generic.undirected * self.iRight.generic.undirected == 4
                and self.iLeft.direction * self.iRight.direction == 1)


    def couldBeChromaticPassingTone(self):
        '''
        A note could a chromatic passing tone (and therefore a passing tone in general)
        if the generic interval between the previous and the current is -2, 1, or 2;
        the generic interval between the current and next is -2, 1, 2; the two generic
        intervals multiply to -2 or 2 (if 4 then it's a diatonic interval; if 1 then
        not a passing tone; i.e, C -> C# -> C## is not a chromatic passing tone);
        AND between each of the notes there is a chromatic interval of 1 or -1 and
        multiplied together it is 1. (i.e.: C -> D-- -> D- is not a chromatic passing tone).

        >>> voiceLeading.ThreeNoteLinearSegment('B3', 'C4', 'C#4').couldBeChromaticPassingTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('B3', 'C4', 'C#4').couldBeChromaticPassingTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('B3', 'B#3', 'C#4').couldBeChromaticPassingTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('B3', 'D-4', 'C#4').couldBeChromaticPassingTone()
        False
        >>> voiceLeading.ThreeNoteLinearSegment('B3', 'C##4', 'C#4').couldBeChromaticPassingTone()
        False
        >>> voiceLeading.ThreeNoteLinearSegment('C#4', 'C4', 'C##4').couldBeChromaticPassingTone()
        False
        >>> voiceLeading.ThreeNoteLinearSegment('D--4', 'C4', 'D-4').couldBeChromaticPassingTone()
        False
        '''

        return (self._isComplete()
                and ((self.iLeft.generic.undirected == 2
                            or self.iLeft.generic.undirected == 1)
                     and (self.iRight.generic.undirected == 2
                            or self.iRight.generic.undirected == 1)
                     and self.iLeft.generic.undirected * self.iRight.generic.undirected == 2
                     and self.iLeft.isChromaticStep
                     and self.iRight.isChromaticStep
                     and self.iLeft.direction * self.iRight.direction == 1))

    def couldBeNeighborTone(self):
        '''
        checks if noteToAnalyze could be a neighbor tone, either a diatonic neighbor tone
        or a chromatic neighbor tone. Does NOT check if tone is non harmonic

        >>> voiceLeading.ThreeNoteLinearSegment('E3', 'F3', 'E3').couldBeNeighborTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('B-4', 'C5', 'B-4').couldBeNeighborTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('B4', 'C5', 'B4').couldBeNeighborTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('G4', 'F#4', 'G4').couldBeNeighborTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('E-3', 'F3', 'E-4').couldBeNeighborTone()
        False
        >>> voiceLeading.ThreeNoteLinearSegment('C3', 'D3', 'E3').couldBeNeighborTone()
        False
        >>> voiceLeading.ThreeNoteLinearSegment('A3', 'C3', 'D3').couldBeNeighborTone()
        False
        '''
        if not self._isComplete():
            return False
        else:
            return self.couldBeDiatonicNeighborTone() or self.couldBeChromaticNeighborTone()


    def couldBeDiatonicNeighborTone(self) -> bool:
        '''
        Returns True if and only if noteToAnalyze could be a diatonic neighbor tone, that is,
        the left and right notes are identical while the middle is a diatonic step up or down

        >>> voiceLeading.ThreeNoteLinearSegment('C3', 'D3', 'C3').couldBeDiatonicNeighborTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('C3', 'C#3', 'C3').couldBeDiatonicNeighborTone()
        False
        >>> voiceLeading.ThreeNoteLinearSegment('C3', 'D-3', 'C3').couldBeDiatonicNeighborTone()
        False
        '''

        return (self._isComplete()
            and self.n1.nameWithOctave == self.n3.nameWithOctave
            and self.iLeft.chromatic.undirected == 2
            and self.iRight.chromatic.undirected == 2
            and self.iLeft.direction * self.iRight.direction == -1)


    def couldBeChromaticNeighborTone(self) -> bool:
        '''
        returns True if and only if noteToAnalyze could be a chromatic neighbor tone, that is,
        the left and right notes are identical while the middle is a chromatic step up or down

        >>> voiceLeading.ThreeNoteLinearSegment('C3', 'D3', 'C3').couldBeChromaticNeighborTone()
        False
        >>> voiceLeading.ThreeNoteLinearSegment('C3', 'D-3', 'C3').couldBeChromaticNeighborTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('C#3', 'D3', 'C#3').couldBeChromaticNeighborTone()
        True
        >>> voiceLeading.ThreeNoteLinearSegment('C#3', 'D3', 'D-3').couldBeChromaticNeighborTone()
        False
        '''
        return (self._isComplete()
            and (self.n1.nameWithOctave == self.n3.nameWithOctave
                 and self.iLeft.isChromaticStep
                 and self.iRight.isChromaticStep
                 and (self.iLeft.direction * self.iRight.direction == -1)))


# Below: beginnings of an implementation for any object segments,
# such as two chord linear segments
# currently only used by theoryAnalyzer
class NChordLinearSegmentException(exceptions21.Music21Exception):
    pass


class NObjectLinearSegment(base.Music21Object):
    def __init__(self, objectList):
        super().__init__()
        self.objectList = objectList

    def _reprInternal(self):
        return f'objectList={self.objectList}'


class NChordLinearSegment(NObjectLinearSegment):
    def __init__(self, chordList):
        super().__init__(chordList)
        self._chordList = []
        for value in chordList:
            if value is None:
                self._chordList.append(None)
            else:
                try:
                    if value.isClassOrSubclass(['Chord', 'Harmony']):
                        self._chordList.append(value)
                    # else:
                        # raise NChordLinearSegmentException(
                        #     'not a valid chord specification: %s' % value)
                except AttributeError as e:  # pragma: no cover
                    raise NChordLinearSegmentException(
                        f'not a valid chord specification: {value!r}'
                    ) from e

    @property
    def chordList(self):
        '''
        Returns a list of all chord symbols in this linear segment.
        Modifying the list does not change the linear segment.

        >>> n = voiceLeading.NChordLinearSegment([harmony.ChordSymbol('Am'),
        ...                                       harmony.ChordSymbol('F7'),
        ...                                       harmony.ChordSymbol('G9')])
        >>> n.chordList
        [<music21.harmony.ChordSymbol Am>,
         <music21.harmony.ChordSymbol F7>,
         <music21.harmony.ChordSymbol G9>]
        '''
        return self._chordList[:]


    def _reprInternal(self):
        return f'chordList={self.chordList}'

class TwoChordLinearSegment(NChordLinearSegment):
    def __init__(self, chordList, chord2=None):
        if isinstance(chordList, (list, tuple)):
            if len(chordList) != 2:  # pragma: no cover
                raise ValueError(
                    f'First argument must be a list of length 2, not {chordList!r}'
                )
            super().__init__(chordList)
        else:
            super().__init__([chordList, chord2])

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


# ------------------------------------------------------------------------------

class Test(unittest.TestCase):

    def testInstantiateEmptyObject(self):
        '''
        test instantiating an empty VoiceLeadingQuartet
        '''
        VoiceLeadingQuartet()

    def testCopyAndDeepcopy(self):
        # Test copying all objects defined in this module
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
            # noinspection PyTypeChecker
            if callable(obj) and not isinstance(obj, types.FunctionType):
                copy.copy(obj)
                copy.deepcopy(obj)

    def test_unifiedTest(self):
        c4 = note.Note('C4')
        d4 = note.Note('D4')
        e4 = note.Note('E4')
        # f4 = note.Note('F4')
        g4 = note.Note('G4')
        a4 = note.Note('A4')
        # b4 = note.Note('B4')
        c5 = note.Note('C5')
        # d5 = note.Note('D5')

        a = VoiceLeadingQuartet(c4, d4, g4, a4)
        assert a.similarMotion() is True
        assert a.parallelMotion() is True
        assert a.antiParallelMotion() is False
        assert a.obliqueMotion() is False
        assert a.parallelInterval(interval.Interval('P5')) is True
        assert a.parallelInterval(interval.Interval('M3')) is False

        b = VoiceLeadingQuartet(c4, c4, g4, g4)
        assert b.noMotion() is True
        assert b.parallelMotion() is False
        assert b.antiParallelMotion() is False
        assert b.obliqueMotion() is False

        c = VoiceLeadingQuartet(c4, g4, c5, g4)
        assert c.antiParallelMotion() is True
        assert c.hiddenInterval(interval.Interval('P5')) is False

        d = VoiceLeadingQuartet(c4, d4, e4, a4)
        assert d.hiddenInterval(interval.Interval('P5')) is True
        assert d.hiddenInterval(interval.Interval('A4')) is False
        assert d.hiddenInterval(interval.Interval('AA4')) is False


class TestExternal(unittest.TestCase):  # pragma: no cover
    pass


# -----------------------------------------------------------------------------

_DOC_ORDER = [VoiceLeadingQuartet, ThreeNoteLinearSegment, Verticality, VerticalityNTuplet]

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)


