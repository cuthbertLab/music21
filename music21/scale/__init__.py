# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         scale.py
# Purpose:      music21 classes for representing scales
#
# Authors:      Christopher Ariza
#               Michael Scott Asato Cuthbert
#               Jose Cabal-Ugaz
#
# Copyright:    Copyright © 2009-2011 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
The various Scale objects provide a bidirectional object representation
of octave repeating and non-octave repeating scales built by network
of :class:`~music21.interval.Interval` objects as modeled
in :class:`~music21.intervalNetwork.IntervalNetwork`.

The main public interface to these resources are subclasses
of :class:`~music21.scale.ConcreteScale`, such
as :class:`~music21.scale.MajorScale`, :class:`~music21.scale.MinorScale`,
and :class:`~music21.scale.MelodicMinorScale`.

More unusual scales are also available, such
as :class:`~music21.scale.OctatonicScale`, :class:`~music21.scale.SieveScale`,
and :class:`~music21.scale.RagMarwa`.

All :class:`~music21.scale.ConcreteScale` subclasses provide the ability
to get a pitches across any range, get a pitch for scale step, get a
scale step for pitch, and, for any given pitch ascend or descend to the
next pitch. In all cases :class:`~music21.pitch.Pitch` objects are returned.

>>> sc1 = scale.MajorScale('a')
>>> [str(p) for p in sc1.getPitches('g2', 'g4')]
['G#2', 'A2', 'B2', 'C#3', 'D3', 'E3', 'F#3', 'G#3', 'A3', 'B3', 'C#4', 'D4', 'E4', 'F#4']

>>> sc2 = scale.MelodicMinorScale('a')
>>> [str(p) for p in sc2.getPitches('g2', 'g4', direction=scale.Direction.DESCENDING)]
['G4', 'F4', 'E4', 'D4', 'C4', 'B3', 'A3', 'G3', 'F3', 'E3', 'D3', 'C3', 'B2', 'A2', 'G2']

>>> [str(p) for p in sc2.getPitches('g2', 'g4', direction=scale.Direction.ASCENDING)]
['G#2', 'A2', 'B2', 'C3', 'D3', 'E3', 'F#3', 'G#3', 'A3', 'B3', 'C4', 'D4', 'E4', 'F#4']
'''
from __future__ import annotations

__all__ = [
    'intervalNetwork', 'scala',
    'Direction', 'Terminus',
    'ScaleException', 'Scale',
    'AbstractScale', 'AbstractDiatonicScale', 'AbstractOctatonicScale',
    'AbstractHarmonicMinorScale', 'AbstractMelodicMinorScale',
    'AbstractCyclicalScale', 'AbstractOctaveRepeatingScale',
    'AbstractRagAsawari', 'AbstractRagMarwa', 'AbstractWeightedHexatonicBlues',
    'ConcreteScale', 'DiatonicScale', 'MajorScale',
    'MinorScale', 'DorianScale', 'PhrygianScale', 'LydianScale', 'MixolydianScale',
    'HypodorianScale', 'HypophrygianScale', 'HypolydianScale', 'HypomixolydianScale',
    'LocrianScale', 'HypolocrianScale', 'HypoaeolianScale',
    'HarmonicMinorScale', 'MelodicMinorScale',
    'OctatonicScale', 'OctaveRepeatingScale', 'CyclicalScale', 'ChromaticScale',
    'WholeToneScale', 'SieveScale', 'ScalaScale', 'RagAsawari',
    'RagMarwa', 'WeightedHexatonicBlues',
]
import copy
import typing as t

from music21.scale import intervalNetwork
from music21.scale import scala
# -------------------------
from music21 import base
from music21 import common
from music21.common.decorators import deprecated
from music21 import defaults
from music21 import environment
from music21 import exceptions21
from music21 import note
from music21 import pitch
from music21 import interval
from music21 import sieve

environLocal = environment.Environment('scale')

Direction = intervalNetwork.Direction
Terminus = intervalNetwork.Terminus

_PitchDegreeCacheKey = tuple[
    type,  # scale class
    str,  # scale type
    str,  # tonic name with octave
    int,  # degree
    Direction,  # direction
    bool  # equating termini
]

# a dictionary mapping an abstract scale class, tonic.nameWithOctave,
# and degree to a pitchNameWithOctave.
_pitchDegreeCache: dict[_PitchDegreeCacheKey, str] = {}


# ------------------------------------------------------------------------------
class ScaleException(exceptions21.Music21Exception):
    pass


class Scale(base.Music21Object):
    '''
    Generic base class for all scales, both abstract and concrete.

    >>> s = scale.Scale()
    >>> s.type
    'Scale'
    >>> s.name  # default same as type.
    'Scale'
    >>> s.isConcrete
    False

    Not a useful class on its own.  See its subclasses.
    '''
    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.type = 'Scale'  # could be mode, could be other indicator

    @property
    def name(self):
        '''
        Return or construct the name of this scale
        '''
        return self.type

    @property
    def isConcrete(self):
        '''
        To be concrete, a Scale must have a defined tonic.
        An abstract Scale is not Concrete, nor is a Concrete scale
        without a defined tonic.  Thus, is always false.
        '''
        return False

    @staticmethod
    def extractPitchList(other, comparisonAttribute='nameWithOctave', removeDuplicates=True):
        # noinspection PyShadowingNames
        '''
        Utility function and staticmethod

        Given a data format as "other" (a ConcreteScale, Chord, Stream, List of Pitches,
        or single Pitch),
        extract all unique Pitches using comparisonAttribute to test for them.

        >>> pStrList = ['A4', 'D4', 'E4', 'F-4', 'D4', 'D5', 'A', 'D#4']
        >>> pList = [pitch.Pitch(p) for p in pStrList]
        >>> nList = [note.Note(p) for p in pStrList]
        >>> s = stream.Stream()
        >>> for n in nList:
        ...     s.append(n)

        Here we only remove the second 'D4' because the default comparison is `nameWithOctave`

        >>> [str(p) for p in scale.Scale.extractPitchList(pList)]
        ['A4', 'D4', 'E4', 'F-4', 'D5', 'A4', 'D#4']

        Note that octaveless notes like the 'A' get a default octave.  In general,
        it is better to work with octave-possessing pitches.

        Now we remove the F-4, D5, and A also because we are working with
        `comparisonAttribute=pitchClass`.
        Note that we're using a Stream as `other` now...

        >>> [str(p) for p in scale.Scale.extractPitchList(s, comparisonAttribute='pitchClass')]
        ['A4', 'D4', 'E4', 'D#4']

        Now let's get rid of all but one diatonic `D`
        by using :meth:`~music21.pitch.Pitch.step` as our
        `comparisonAttribute`.  Note that we can just give a list of
        strings as well, and they become :class:`~music21.pitch.Pitch` objects. Oh, we will also
        show that `extractPitchList` works on any scale:

        >>> sc = scale.Scale()
        >>> [str(p) for p in sc.extractPitchList(pStrList, comparisonAttribute='step')]
        ['A4', 'D4', 'E4', 'F-4']
        '''
        pre = []
        # if a ConcreteScale, Chord or Stream
        if hasattr(other, 'pitches'):
            pre = list(other.pitches)
        # if a list
        elif common.isIterable(other):
            # assume a list of pitches; possible permit conversions?
            pre = []
            for p in other:
                if hasattr(p, 'pitch'):
                    pre.append(p.pitch)
                elif isinstance(p, pitch.Pitch):
                    pre.append(p)
                else:
                    pre.append(pitch.Pitch(p))
        elif hasattr(other, 'pitch'):
            pre = [other.pitch]  # get pitch attribute

        if removeDuplicates is False:
            return pre

        uniquePitches = {}

        post = []

        for p in pre:
            hashValue = getattr(p, comparisonAttribute)
            if hashValue not in uniquePitches:
                uniquePitches[hashValue] = True
                post.append(p)
        for p in post:
            if p.octave is None:
                p.octave = defaults.pitchOctave

        return post

# ------------------------------------------------------------------------------


class AbstractScale(Scale):
    '''
    An abstract scale is specific scale formation, but does not have a
    defined pitch collection or pitch reference. For example, all Major
    scales can be represented by an AbstractScale; a ConcreteScale,
    however, is a specific Major Scale, such as G Major.

    These classes provide an interface to, and create and manipulate,
    the stored :class:`~music21.intervalNetwork.IntervalNetwork`
    object. Thus, they are rarely created or manipulated directly by
    most users.

    The AbstractScale additionally stores an `_alteredDegrees` dictionary.
    Subclasses can define altered nodes in AbstractScale that are passed
    to the :class:`~music21.intervalNetwork.IntervalNetwork`.

    Equality
    --------
    Two abstract scales are the same if they have the same class and the
    same tonicDegree and octaveDuplicating attributes and the same intervalNetwork,
    and it satisfies all other music21 superclass attributes.

    >>> as1 = scale.AbstractOctatonicScale()
    >>> as2 = scale.AbstractOctatonicScale()
    >>> as1 == as2
    True
    >>> as2.tonicDegree = 5
    >>> as1 == as2
    False

    >>> as1 == scale.AbstractDiatonicScale()
    False
    '''
    # TODO: make a subclass of IntervalNetwork and remove the ._net aspect.
    equalityAttributes = ('tonicDegree', '_net', 'octaveDuplicating')

    def __init__(self, **keywords):
        super().__init__(**keywords)
        # store interval network within abstract scale
        self._net = None
        # in most cases tonic/final of scale is step one, but not always
        self.tonicDegree = 1  # step of tonic

        # declare if this scale is octave duplicating
        # can be used as to optimize pitch gathering
        self.octaveDuplicating = True

        # passed to interval network
        self.deterministic = True
        # store parameter for interval network-based node modifications
        # entries are in the form:
        # step: {'direction':Direction.BI, 'interval':Interval}
        self._alteredDegrees = {}

    def buildNetwork(self):
        '''
        Calling the buildNetwork, with or without parameters,
        is main job of the AbstractScale class.  This needs to be subclassed by a derived class
        '''
        raise NotImplementedError

    def buildNetworkFromPitches(self, pitchList):
        '''
        Builds the network (list of motions) for an abstract scale
        from a list of pitch.Pitch objects.  If
        the concluding note (usually the "octave") is not given,
        then it'll be created automatically.

        Here we treat the augmented triad as a scale:

        >>> p1 = pitch.Pitch('C4')
        >>> p2 = pitch.Pitch('E4')
        >>> p3 = pitch.Pitch('G#4')
        >>> abstractScale = scale.AbstractScale()
        >>> abstractScale.buildNetworkFromPitches([p1, p2, p3])
        >>> abstractScale.octaveDuplicating
        True
        >>> abstractScale._net
        <music21.scale.intervalNetwork.IntervalNetwork object at 0x...>

        Now see it return a new "scale" of the augmentedTriad on D5

        >>> abstractScale._net.realizePitch('D5')
        [<music21.pitch.Pitch D5>, <music21.pitch.Pitch F#5>,
         <music21.pitch.Pitch A#5>, <music21.pitch.Pitch D6>]

        It is also possible to use implicit octaves:

        >>> abstract_scale = scale.AbstractScale()
        >>> abstract_scale.buildNetworkFromPitches(['C', 'F'])
        >>> abstract_scale.octaveDuplicating
        True
        >>> abstract_scale._net.realizePitch('G')
        [<music21.pitch.Pitch G4>, <music21.pitch.Pitch C5>, <music21.pitch.Pitch G5>]
        '''
        pitchListReal = []
        for p in pitchList:
            if isinstance(p, str):
                pitchListReal.append(pitch.Pitch(p))
            elif isinstance(p, note.Note):
                pitchListReal.append(p.pitch)
            else:  # assume this is a pitch object
                pitchListReal.append(p)
        pitchList = pitchListReal

        self.fixDefaultOctaveForPitchList(pitchList)

        if not common.isListLike(pitchList) or not pitchList:
            raise ScaleException(f'Cannot build a network from this pitch list: {pitchList}')
        intervalList = []
        for i in range(len(pitchList) - 1):
            intervalList.append(interval.Interval(pitchList[i], pitchList[i + 1]))
        if pitchList[-1].name == pitchList[0].name:  # the completion of the scale has been given.
            # print('hi %s ' % pitchList)
            # this scale is only octave duplicating if the top note is exactly
            # 1 octave above the bottom; if it spans more than one octave,
            # all notes must be identical in each octave
            # if abs(pitchList[-1].ps - pitchList[0].ps) == 12:
            span = interval.Interval(pitchList[0], pitchList[-1])
            # environLocal.printDebug(['got span', span, span.name])
            if span.name == 'P8':
                self.octaveDuplicating = True
            else:
                self.octaveDuplicating = False
        else:
            p = copy.deepcopy(pitchList[0])
            if p.octave is None:
                p.octave = p.implicitOctave
            if pitchList[-1] > pitchList[0]:  # ascending
                while p.ps < pitchList[-1].ps:
                    p.octave += 1
            else:
                while p.ps > pitchList[-1].ps:
                    p.octave += -1

            intervalList.append(interval.Interval(pitchList[-1], p))
            span = interval.Interval(pitchList[0], p)
            # environLocal.printDebug(['got span', span, span.name])
            if span.name == 'P8':
                self.octaveDuplicating = True
            else:
                self.octaveDuplicating = False

            # if abs(p.ps - pitchList[0].ps) == 12:
            #     self.octaveDuplicating == True
            # else:
            #     self.octaveDuplicating == False

        # environLocal.printDebug(['intervalList', intervalList,
        #                        'self.octaveDuplicating', self.octaveDuplicating])
        self._net = intervalNetwork.IntervalNetwork(intervalList,
                                                    octaveDuplicating=self.octaveDuplicating)

    @staticmethod
    def fixDefaultOctaveForPitchList(pitchList):
        # noinspection PyShadowingNames
        '''
        Suppose you have a set of octaveless Pitches that you use to make a scale.

        Something like:

        >>> pitchListStrs = 'a b c d e f g a'.split()
        >>> pitchList = [pitch.Pitch(p) for p in pitchListStrs]

        Here's the problem, between `pitchList[1]` and `pitchList[2]` the `.implicitOctave`
        stays the same, so the `.ps` drops:

        >>> (pitchList[1].implicitOctave, pitchList[2].implicitOctave)
        (4, 4)
        >>> (pitchList[1].ps, pitchList[2].ps)
        (71.0, 60.0)

        Hence this helper staticmethod that makes it so that for octaveless pitches ONLY, each
        one has a .ps above the previous:

        >>> pl2 = scale.AbstractScale.fixDefaultOctaveForPitchList(pitchList)
        >>> (pl2[1].implicitOctave, pl2[2].implicitOctave, pl2[3].implicitOctave)
        (4, 5, 5)
        >>> (pl2[1].ps, pl2[2].ps)
        (71.0, 72.0)

        Note that the list is modified inPlace:

        >>> pitchList is pl2
        True
        >>> pitchList[2] is pl2[2]
        True
        '''
        # fix defaultOctave for pitchList
        lastPs = 0
        lastOctave = pitchList[0].implicitOctave
        for p in pitchList:
            if p.octave is None:
                if lastPs > p.ps:
                    p.octave = lastOctave
                while lastPs > p.ps:
                    lastOctave += 1
                    p.octave = lastOctave

            lastPs = p.ps
            lastOctave = p.implicitOctave

        return pitchList

    def getDegreeMaxUnique(self):
        '''
        Return the maximum number of scale steps, or the number to use as a
        modulus.
        '''
        # access from property
        return self._net.degreeMaxUnique

    # def reverse(self):
    #     '''
    #     Reverse all intervals in this scale.
    #     '''
    #     pass

    # expose interface from network. these methods must be called (and not
    # ._net directly because they can pass the alteredDegrees dictionary

    def getRealization(self,
                       pitchObj,
                       stepOfPitch,
                       minPitch=None,
                       maxPitch=None,
                       direction=Direction.ASCENDING,
                       reverse=False):
        '''
        Realize the abstract scale as a list of pitch objects,
        given a pitch object, the step of that pitch object,
        and a min and max pitch.
        '''
        if self._net is None:
            raise ScaleException('no IntervalNetwork is defined by this "scale".')

        post = self._net.realizePitch(pitchObj,
                                      stepOfPitch,
                                      minPitch=minPitch,
                                      maxPitch=maxPitch,
                                      alteredDegrees=self._alteredDegrees,
                                      direction=direction,
                                      reverse=reverse)
        # here, we copy the list of pitches so as not to allow editing of
        # cached pitch values later
        return copy.deepcopy(post)

    def getIntervals(self,
                     stepOfPitch=None,
                     minPitch=None,
                     maxPitch=None,
                     direction=Direction.ASCENDING,
                     reverse=False):
        '''
        Realize the abstract scale as a list of pitch
        objects, given a pitch object, the step of
        that pitch object, and a min and max pitch.
        '''
        if self._net is None:
            raise ScaleException('no network is defined.')

        post = self._net.realizeIntervals(stepOfPitch,
                                          minPitch=minPitch,
                                          maxPitch=maxPitch,
                                          alteredDegrees=self._alteredDegrees,
                                          direction=direction,
                                          reverse=reverse)
        # here, we copy the list of pitches so as not to allow editing of
        # cached pitch values later
        return post

    def getPitchFromNodeDegree(self,
                               pitchReference,
                               nodeName,
                               nodeDegreeTarget,
                               direction=Direction.ASCENDING,
                               minPitch=None,
                               maxPitch=None,
                               equateTermini=True):
        '''
        Get a pitch for desired scale degree.
        '''
        post = self._net.getPitchFromNodeDegree(
            pitchReference=pitchReference,  # pitch defined here
            nodeName=nodeName,  # defined in abstract class
            nodeDegreeTarget=nodeDegreeTarget,  # target looking for
            direction=direction,
            minPitch=minPitch,
            maxPitch=maxPitch,
            alteredDegrees=self._alteredDegrees,
            equateTermini=equateTermini
        )
        return copy.deepcopy(post)

    def realizePitchByDegree(self,
                             pitchReference,
                             nodeId,
                             nodeDegreeTargets,
                             direction=Direction.ASCENDING,
                             minPitch=None,
                             maxPitch=None):
        '''
        Given one or more scale degrees, return a list of
        all matches over the entire range.

        See :meth:`~music21.intervalNetwork.IntervalNetwork.realizePitchByDegree`.
        in `intervalNetwork.IntervalNetwork`.

        Create an abstract pentatonic scale:

        >>> pitchList = ['C#4', 'D#4', 'F#4', 'G#4', 'A#4']
        >>> abstractScale = scale.AbstractScale()
        >>> abstractScale.buildNetworkFromPitches([pitch.Pitch(p) for p in pitchList])
        '''
        # TODO: rely here on intervalNetwork for caching
        post = self._net.realizePitchByDegree(
            pitchReference=pitchReference,  # pitch defined here
            nodeId=nodeId,  # defined in abstract class
            nodeDegreeTargets=nodeDegreeTargets,  # target looking for
            direction=direction,
            minPitch=minPitch,
            maxPitch=maxPitch,
            alteredDegrees=self._alteredDegrees)
        return copy.deepcopy(post)

    def getRelativeNodeDegree(self,
                              pitchReference,
                              nodeName,
                              pitchTarget,
                              comparisonAttribute='pitchClass',
                              direction=Direction.ASCENDING):
        '''
        Expose functionality from
        :class:`~music21.intervalNetwork.IntervalNetwork`, passing on the
        stored alteredDegrees dictionary.
        '''
        post = self._net.getRelativeNodeDegree(
            pitchReference=pitchReference,
            nodeId=nodeName,
            pitchTarget=pitchTarget,
            comparisonAttribute=comparisonAttribute,
            direction=direction,
            alteredDegrees=self._alteredDegrees
        )
        return copy.deepcopy(post)

    def nextPitch(self,
                  pitchReference,
                  nodeName,
                  pitchOrigin,
                  direction: Direction = Direction.ASCENDING,
                  stepSize=1,
                  getNeighbor: Direction | bool = True):
        '''
        Expose functionality from :class:`~music21.intervalNetwork.IntervalNetwork`,
        passing on the stored alteredDegrees dictionary.
        '''
        post = self._net.nextPitch(pitchReference=pitchReference,
                                   nodeName=nodeName,
                                   pitchOrigin=pitchOrigin,
                                   direction=direction,
                                   stepSize=stepSize,
                                   alteredDegrees=self._alteredDegrees,
                                   getNeighbor=getNeighbor
                                   )
        return copy.deepcopy(post)

    def getNewTonicPitch(self,
                         pitchReference,
                         nodeName,
                         direction=Direction.ASCENDING,
                         minPitch=None,
                         maxPitch=None):
        '''
        Define a pitch target and a node.
        '''
        post = self._net.getPitchFromNodeDegree(
            pitchReference=pitchReference,
            nodeName=nodeName,
            nodeDegreeTarget=1,  # get the pitch of the tonic
            direction=direction,
            minPitch=minPitch,
            maxPitch=maxPitch,
            alteredDegrees=self._alteredDegrees
        )
        return copy.deepcopy(post)

    # --------------------------------------------------------------------------

    def getScalaData(self, direction=Direction.ASCENDING):
        '''
        Get the interval sequence as a :class:~music21.scala.ScalaData object
        for a particular scale:
        '''
        # get one octave of intervals
        intervals = self.getIntervals(direction=direction)
        ss = scala.ScalaData()
        ss.setIntervalSequence(intervals)
        ss.description = repr(self)
        return ss

    def write(self, fmt=None, fp=None, direction=Direction.ASCENDING, **keywords):
        '''
        Write the scale in a format. Here, prepare scala format if requested.
        '''
        if fmt is not None:
            fileFormat, ext = common.findFormat(fmt)
            if fp is None:
                fpLocal = environLocal.getTempFile(ext)
            else:
                fpLocal = fp

            if fileFormat == 'scala':
                ss = self.getScalaData(direction=direction)
                sf = scala.ScalaFile(ss)  # pass storage to the file
                sf.open(fpLocal, 'w')
                sf.write()
                sf.close()
                return fpLocal
        return Scale.write(self, fmt=fmt, fp=fp, **keywords)

    def show(self, fmt=None, app=None, direction=Direction.ASCENDING, **keywords):
        '''
        Show the scale in a format. Here, prepare scala format if requested.
        '''
        from music21.converter.subConverters import SubConverter
        if fmt is not None:
            fileFormat, unused_ext = common.findFormat(fmt)
            if fileFormat == 'scala':
                returnedFilePath = self.write(fileFormat, direction=direction)
                SubConverter().launch(returnedFilePath, fmt=fileFormat, app=app)
                return
        Scale.show(self, fmt=fmt, app=app, **keywords)

# ------------------------------------------------------------------------------
# abstract subclasses


class AbstractDiatonicScale(AbstractScale):
    '''
    An abstract representation of a Diatonic scale w/ or without mode.

    >>> as1 = scale.AbstractDiatonicScale('major')
    >>> as1.type
    'Abstract diatonic'
    >>> as1.mode
    'major'
    >>> as1.octaveDuplicating
    True

    Equality
    --------
    AbstractDiatonicScales must satisfy all the characteristics of a
    general AbstractScale but also need to have equal dominantDegrees.

    >>> as1 = scale.AbstractDiatonicScale('major')
    >>> as2 = scale.AbstractDiatonicScale('lydian')
    >>> as1 == as2
    False

    Note that their modes do not need to be the same.
    For instance for the case of major and Ionian which have
    the same networks:

    >>> as3 = scale.AbstractDiatonicScale('ionian')
    >>> (as1.mode, as3.mode)
    ('major', 'ionian')
    >>> as1 == as3
    True
    '''
    def __init__(self, mode: str | None = None, **keywords):
        super().__init__(**keywords)
        self.mode = mode
        self.type = 'Abstract diatonic'
        self.tonicDegree = None  # step of tonic
        self.dominantDegree = None  # step of dominant
        # all diatonic scales are octave duplicating
        self.octaveDuplicating = True
        self.relativeMinorDegree: int = -1
        self.relativeMajorDegree: int = -1
        self.buildNetwork(mode=mode)

    def buildNetwork(self, mode=None):
        '''
        Given subclass dependent parameters, build and assign the IntervalNetwork.

        >>> sc = scale.AbstractDiatonicScale()
        >>> sc.buildNetwork('Lydian')  # N.B. case-insensitive name
        >>> [str(p) for p in sc.getRealization('f4', 1, 'f2', 'f6')]
        ['F2', 'G2', 'A2', 'B2', 'C3', 'D3', 'E3',
         'F3', 'G3', 'A3', 'B3', 'C4', 'D4', 'E4',
         'F4', 'G4', 'A4', 'B4', 'C5', 'D5', 'E5',
         'F5', 'G5', 'A5', 'B5', 'C6', 'D6', 'E6', 'F6']

        Unknown modes raise an exception:

        >>> sc.buildNetwork('blues-like')
        Traceback (most recent call last):
        music21.scale.ScaleException: Cannot create a
            scale of the following mode: 'blues-like'

        * Changed in v6: case-insensitive modes
        '''
        # reference: http://cnx.org/content/m11633/latest/
        # most diatonic scales will start with this collection
        srcList = ('M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2')
        self.tonicDegree = 1
        self.dominantDegree = 5

        if isinstance(mode, str):
            mode = mode.lower()

        if mode in (None, 'major', 'ionian'):  # c to C
            intervalList = srcList
            self.relativeMajorDegree = 1
            self.relativeMinorDegree = 6
        elif mode == 'dorian':
            intervalList = srcList[1:] + srcList[:1]  # d to d
            self.relativeMajorDegree = 7
            self.relativeMinorDegree = 5
        elif mode == 'phrygian':
            intervalList = srcList[2:] + srcList[:2]  # e to e
            self.relativeMajorDegree = 6
            self.relativeMinorDegree = 4
        elif mode == 'lydian':
            intervalList = srcList[3:] + srcList[:3]  # f to f
            self.relativeMajorDegree = 5
            self.relativeMinorDegree = 3
        elif mode == 'mixolydian':
            intervalList = srcList[4:] + srcList[:4]  # g to g
            self.relativeMajorDegree = 4
            self.relativeMinorDegree = 2
        elif mode in ('aeolian', 'minor'):
            intervalList = srcList[5:] + srcList[:5]  # a to A
            self.relativeMajorDegree = 3
            self.relativeMinorDegree = 1
        elif mode == 'locrian':
            intervalList = srcList[6:] + srcList[:6]  # b to B
            self.relativeMajorDegree = 2
            self.relativeMinorDegree = 7
        elif mode == 'hypodorian':
            intervalList = srcList[5:] + srcList[:5]  # a to a
            self.tonicDegree = 4
            self.dominantDegree = 6
            self.relativeMajorDegree = 3
            self.relativeMinorDegree = 1
        elif mode == 'hypophrygian':
            intervalList = srcList[6:] + srcList[:6]  # b to b
            self.tonicDegree = 4
            self.dominantDegree = 7
            self.relativeMajorDegree = 2
            self.relativeMinorDegree = 7
        elif mode == 'hypolydian':  # c to c
            intervalList = srcList
            self.tonicDegree = 4
            self.dominantDegree = 6
            self.relativeMajorDegree = 1
            self.relativeMinorDegree = 6
        elif mode == 'hypomixolydian':
            intervalList = srcList[1:] + srcList[:1]  # d to d
            self.tonicDegree = 4
            self.dominantDegree = 7
            self.relativeMajorDegree = 7
            self.relativeMinorDegree = 5
        elif mode == 'hypoaeolian':
            intervalList = srcList[2:] + srcList[:2]  # e to e
            self.tonicDegree = 4
            self.dominantDegree = 6
            self.relativeMajorDegree = 6
            self.relativeMinorDegree = 4
        elif mode == 'hypolocrian':
            intervalList = srcList[3:] + srcList[:3]  # f to f
            self.tonicDegree = 4
            self.dominantDegree = 6
            self.relativeMajorDegree = 5
            self.relativeMinorDegree = 3
        else:
            raise ScaleException(f'Cannot create a scale of the following mode: {mode!r}')

        self._net = intervalNetwork.IntervalNetwork(
            intervalList,
            octaveDuplicating=self.octaveDuplicating,
            pitchSimplification=None)


class AbstractOctatonicScale(AbstractScale):
    '''
    Abstract scale representing the two octatonic scales.
    '''

    def __init__(self, mode=None, **keywords):
        super().__init__(**keywords)
        self.type = 'Abstract Octatonic'
        # all octatonic scales are octave duplicating
        self.octaveDuplicating = True
        # here, accept None
        self.buildNetwork(mode=mode)

    def buildNetwork(self, mode=None):
        '''
        Given subclass dependent parameters, build and assign the IntervalNetwork.

        >>> sc = scale.AbstractDiatonicScale()
        >>> sc.buildNetwork('lydian')
        >>> [str(p) for p in sc.getRealization('f4', 1, 'f2', 'f6')]
        ['F2', 'G2', 'A2', 'B2', 'C3', 'D3', 'E3',
         'F3', 'G3', 'A3', 'B3', 'C4', 'D4', 'E4',
         'F4', 'G4', 'A4', 'B4', 'C5', 'D5', 'E5',
         'F5', 'G5', 'A5', 'B5', 'C6', 'D6', 'E6', 'F6']
       '''
        srcList = ('M2', 'm2', 'M2', 'm2', 'M2', 'm2', 'M2', 'm2')
        if mode in (None, 2, 'M2'):
            intervalList = srcList  # start with M2
            self.tonicDegree = 1
        elif mode in (1, 'm2'):
            intervalList = srcList[1:] + srcList[:1]  # start with m2
            self.tonicDegree = 1
        else:
            raise ScaleException(f'cannot create a scale of the following mode: {mode}')
        self._net = intervalNetwork.IntervalNetwork(intervalList,
                                                    octaveDuplicating=self.octaveDuplicating,
                                                    pitchSimplification='maxAccidental')
        # might also set weights for tonic and dominant here


class AbstractHarmonicMinorScale(AbstractScale):
    '''
    A true bidirectional scale that with the augmented
    second to a leading tone.

    This is the only scale to use the "_alteredDegrees" property.

    mode is not used
    '''
    def __init__(self, mode: str | None = None, **keywords) -> None:
        super().__init__(**keywords)
        self.type = 'Abstract Harmonic Minor'
        self.octaveDuplicating = True
        self.dominantDegree: int = -1
        self.buildNetwork()

    def buildNetwork(self):
        intervalList = ['M2', 'm2', 'M2', 'M2', 'm2', 'M2', 'M2']  # a to A
        self.tonicDegree = 1
        self.dominantDegree = 5
        self._net = intervalNetwork.IntervalNetwork(intervalList,
                                                    octaveDuplicating=self.octaveDuplicating,
                                                    pitchSimplification=None)

        # raise the seventh in all directions
        # 7 here is scale step/degree, not node id
        self._alteredDegrees[7] = {
            'direction': intervalNetwork.Direction.BI,
            'interval': interval.Interval('a1')
        }


class AbstractMelodicMinorScale(AbstractScale):
    '''
    A directional scale.

    mode is not used.
    '''
    def __init__(self, mode: str | None = None, **keywords) -> None:
        super().__init__(**keywords)
        self.type = 'Abstract Melodic Minor'
        self.octaveDuplicating = True
        self.dominantDegree: int = -1
        self.buildNetwork()

    def buildNetwork(self):
        self.tonicDegree = 1
        self.dominantDegree = 5
        self._net = intervalNetwork.IntervalNetwork(
            octaveDuplicating=self.octaveDuplicating,
            pitchSimplification=None)
        self._net.fillMelodicMinor()


class AbstractCyclicalScale(AbstractScale):
    '''
    A scale of any size built with an interval list of any form.
    The resulting scale may be non octave repeating.
    '''

    def __init__(self, mode=None, **keywords):
        super().__init__(**keywords)
        self.type = 'Abstract Cyclical'
        self.octaveDuplicating = False
        self.buildNetwork(mode=mode)
        # cannot assume that abstract cyclical scales are octave duplicating
        # until we have the intervals in use

    def buildNetwork(self, mode):
        '''
        Here, mode is the list of intervals.
        '''
        if not isinstance(mode, (list, tuple)):
            modeList = [mode]  # place in list
        else:
            modeList = mode
        self.tonicDegree = 1
        self._net = intervalNetwork.IntervalNetwork(modeList,
                                                    octaveDuplicating=self.octaveDuplicating)


class AbstractOctaveRepeatingScale(AbstractScale):
    '''
    A scale of any size built with an interval list
    that assumes octave completion. An additional
    interval to complete the octave will be added
    to the provided intervals. This does not guarantee
    that the octave will be repeated in one octave,
    only the next octave above the last interval will
    be provided.
    '''

    def __init__(self, mode=None, **keywords):
        super().__init__(**keywords)
        self.type = 'Abstract Octave Repeating'

        if mode is None:
            # supply a default
            mode = ['P8']
        self.buildNetwork(mode=mode)

        # by definition, these are forced to be octave duplicating
        # though, do to some intervals, duplication may not happen every oct
        self.octaveDuplicating = True

    def buildNetwork(self, mode):
        '''
        Here, mode is the list of intervals.
        '''
        if not common.isListLike(mode):
            mode = [mode]  # place in list
        # get the interval to complete the octave

        intervalSum = interval.add(mode)
        iComplement = intervalSum.complement
        if iComplement is not None:
            mode.append(iComplement)

        self.tonicDegree = 1
        self._net = intervalNetwork.IntervalNetwork(mode,
                                                    octaveDuplicating=self.octaveDuplicating)


class AbstractRagAsawari(AbstractScale):
    '''
    A pseudo raga-scale.
    '''
    def __init__(self, **keywords) -> None:
        super().__init__(**keywords)
        self.type = 'Abstract Rag Asawari'
        self.octaveDuplicating = True
        self.dominantDegree: int = -1
        self.buildNetwork()

    def buildNetwork(self):
        self.tonicDegree = 1
        self.dominantDegree = 5
        nodes = ({'id': Terminus.LOW, 'degree': 1},  # c
                 {'id': 0, 'degree': 2},  # d
                 {'id': 1, 'degree': 4},  # f
                 {'id': 2, 'degree': 5},  # g
                 {'id': 3, 'degree': 6},  # a-
                 {'id': Terminus.HIGH, 'degree': 8},  # c

                 {'id': 4, 'degree': 7},  # b-
                 {'id': 5, 'degree': 6},  # a-
                 {'id': 6, 'degree': 5},  # g
                 {'id': 7, 'degree': 4},  # f
                 {'id': 8, 'degree': 3},  # e-
                 {'id': 9, 'degree': 2},  # d
                 )
        edges = (
            # ascending
            {'interval': 'M2',
                 'connections': (
                     [Terminus.LOW, 0, Direction.ASCENDING],  # c to d
                 )},
            {'interval': 'm3',
                 'connections': (
                     [0, 1, Direction.ASCENDING],  # d to f
                 )},
            {'interval': 'M2',
                 'connections': (
                     [1, 2, Direction.ASCENDING],  # f to g
                 )},
            {'interval': 'm2',
                 'connections': (
                     [2, 3, Direction.ASCENDING],  # g to a-
                 )},
            {'interval': 'M3',
                 'connections': (
                     [3, Terminus.HIGH, Direction.ASCENDING],  # a- to c
                 )},
            # descending
            {'interval': 'M2',
                 'connections': (
                     [Terminus.HIGH, 4, Direction.DESCENDING],  # c to b-
                 )},
            {'interval': 'M2',
                 'connections': (
                     [4, 5, Direction.DESCENDING],  # b- to a-
                 )},
            {'interval': 'm2',
                 'connections': (
                     [5, 6, Direction.DESCENDING],  # a- to g
                 )},
            {'interval': 'M2',
                 'connections': (
                     [6, 7, Direction.DESCENDING],  # g to f
                 )},
            {'interval': 'M2',
                 'connections': (
                     [7, 8, Direction.DESCENDING],  # f to e-
                 )},
            {'interval': 'm2',
                 'connections': (
                     [8, 9, Direction.DESCENDING],  # e- to d
                 )},
            {'interval': 'M2',
                 'connections': (
                     [9, Terminus.LOW, Direction.DESCENDING],  # d to c
                 )},
        )

        self._net = intervalNetwork.IntervalNetwork(
            octaveDuplicating=self.octaveDuplicating,
            pitchSimplification='mostCommon')
        # using representation stored in interval network
        self._net.fillArbitrary(nodes, edges)


class AbstractRagMarwa(AbstractScale):
    '''
    A pseudo raga-scale.
    '''
    def __init__(self, **keywords) -> None:
        super().__init__(**keywords)
        self.type = 'Abstract Rag Marwa'
        self.octaveDuplicating = True
        self.dominantDegree: int = -1
        self.buildNetwork()

    def buildNetwork(self):
        self.tonicDegree = 1
        self.dominantDegree = 5
        nodes = ({'id': Terminus.LOW, 'degree': 1},  # c
                 {'id': 0, 'degree': 2},  # d-
                 {'id': 1, 'degree': 3},  # e
                 {'id': 2, 'degree': 4},  # f#
                 {'id': 3, 'degree': 5},  # a
                 {'id': 4, 'degree': 6},  # b
                 {'id': 5, 'degree': 7},  # a (could use id 3 again?)
                 {'id': Terminus.HIGH, 'degree': 8},  # c

                 {'id': 6, 'degree': 7},  # d- (above terminus)
                 {'id': 7, 'degree': 6},  # b
                 {'id': 8, 'degree': 5},  # a
                 {'id': 9, 'degree': 4},  # f#
                 {'id': 10, 'degree': 3},  # e
                 {'id': 11, 'degree': 2},  # d-
                 )
        edges = (
            # ascending
            {'interval': 'm2',
             'connections': ([Terminus.LOW, 0, Direction.ASCENDING],)  # c to d-
             },
            {'interval': 'A2',
             'connections': ([0, 1, Direction.ASCENDING],)  # d- to e
             },
            {'interval': 'M2',
             'connections': ([1, 2, Direction.ASCENDING],)  # e to f#
             },
            {'interval': 'm3',
             'connections': ([2, 3, Direction.ASCENDING],)  # f# to a
             },
            {'interval': 'M2',
             'connections': ([3, 4, Direction.ASCENDING],)  # a to b
             },
            {'interval': '-M2',
             'connections': ([4, 5, Direction.ASCENDING],)  # b to a (downward)
             },
            {'interval': 'm3',
             'connections': ([5, Terminus.HIGH, Direction.ASCENDING],)  # a to c
             },

            # descending
            {'interval': '-m2',
             'connections': ([Terminus.HIGH, 6, Direction.DESCENDING],)  # c to d- (up)
             },
            {'interval': 'd3',
             'connections': ([6, 7, Direction.DESCENDING],)  # d- to b
             },
            {'interval': 'M2',
             'connections': ([7, 8, Direction.DESCENDING],)  # b to a
             },
            {'interval': 'm3',
             'connections': ([8, 9, Direction.DESCENDING],)  # a to f#
             },
            {'interval': 'M2',
             'connections': ([9, 10, Direction.DESCENDING],)  # f# to e
             },
            {'interval': 'A2',
             'connections': ([10, 11, Direction.DESCENDING],)  # e to d-
             },
            {'interval': 'm2',
             'connections': ([11, Terminus.LOW, Direction.DESCENDING],)  # d- to c
             },
        )

        self._net = intervalNetwork.IntervalNetwork(
            octaveDuplicating=self.octaveDuplicating,
        )
        # using representation stored in interval network
        self._net.fillArbitrary(nodes, edges)


class AbstractWeightedHexatonicBlues(AbstractScale):
    '''
    A dynamic, probabilistic mixture of minor pentatonic and a hexatonic blues scale
    '''

    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.type = 'Abstract Weighted Hexatonic Blues'
        # probably not, as all may not have some pitches in each octave
        self.octaveDuplicating = True
        self.deterministic = False
        self.dominantDegree = 5
        self.buildNetwork()

    def buildNetwork(self):
        self.tonicDegree = 1
        self.dominantDegree = 5
        nodes = ({'id': Terminus.LOW, 'degree': 1},  # c
                 {'id': 0, 'degree': 2},  # e-
                 {'id': 1, 'degree': 3},  # f
                 {'id': 2, 'degree': 4},  # f#
                 {'id': 3, 'degree': 5},  # g
                 {'id': 4, 'degree': 6},  # b-
                 {'id': Terminus.HIGH, 'degree': 7},  # c
                 )
        edges = (
            # all bidirectional
            {'interval': 'm3',
                 'connections': (
                     [Terminus.LOW, 0, Direction.BI],  # c to e-
                 )},
            {'interval': 'M2',
                 'connections': (
                     [0, 1, Direction.BI],  # e- to f
                 )},
            {'interval': 'M2',
                 'connections': (
                     [1, 3, Direction.BI],  # f to g
                 )},
            {'interval': 'a1',
                 'connections': (
                     [1, 2, Direction.BI],  # f to f#
                 )},
            {'interval': 'm2',
                 'connections': (
                     [2, 3, Direction.BI],  # f# to g
                 )},
            {'interval': 'm3',
                 'connections': (
                     [3, 4, Direction.BI],  # g to b-
                 )},
            {'interval': 'M2',
                 'connections': (
                     [4, Terminus.HIGH, Direction.BI],  # b- to c
                 )},
        )

        self._net = intervalNetwork.IntervalNetwork(
            octaveDuplicating=self.octaveDuplicating,
            deterministic=self.deterministic,)
        # using representation stored in interval network
        self._net.fillArbitrary(nodes, edges)


# ------------------------------------------------------------------------------
class ConcreteScale(Scale):
    '''
    A concrete scale is specific scale formation with
    a defined pitch collection (a `tonic` Pitch) that
    may or may not be bound by specific range. For
    example, a specific Major Scale, such as G
    Major, from G2 to G4.

    This class is can either be used directly or more
    commonly as a base class for all concrete scales.

    Here we treat a diminished triad as a scale:

    >>> myScale = scale.ConcreteScale(pitches=['C4', 'E-4', 'G-4', 'A4'])
    >>> myScale.getTonic()
    <music21.pitch.Pitch C4>
    >>> myScale.nextPitch('G-2')
    <music21.pitch.Pitch A2>
    >>> [str(p) for p in myScale.getPitches('E-5', 'G-7')]
    ['E-5', 'G-5', 'A5', 'C6', 'E-6', 'G-6', 'A6', 'C7', 'E-7', 'G-7']


    A scale that lasts two octaves and uses quarter tones (D~)

    >>> complexScale = scale.ConcreteScale(
    ...     pitches=['C#3', 'E-3', 'F3', 'G3', 'B3', 'D~4', 'F#4', 'A4', 'C#5']
    ... )
    >>> complexScale.getTonic()
    <music21.pitch.Pitch C#3>
    >>> complexScale.nextPitch('G3', direction=scale.Direction.DESCENDING)
    <music21.pitch.Pitch F3>

    >>> [str(p) for p in complexScale.getPitches('C3', 'C7')]
    ['C#3', 'E-3', 'F3', 'G3', 'B3', 'D~4', 'F#4',
     'A4', 'C#5', 'E-5', 'F5', 'G5', 'B5', 'D~6', 'F#6', 'A6']

    Descending form:

    >>> [str(p) for p in complexScale.getPitches('C7', 'C5')]
    ['A6', 'F#6', 'D~6', 'B5', 'G5', 'F5', 'E-5', 'C#5']

    Equality
    --------
    Two ConcreteScales are the same if they satisfy all general Music21Object
    equality methods and their Abstract scales, their tonics, and their
    boundRanges are the same:



    OMIT_FROM_DOCS

    >>> scale.ConcreteScale(tonic=4)
    Traceback (most recent call last):
    ValueError: Tonic must be a Pitch, Note, or str, not <class 'int'>

    This is in OMIT
    '''
    usePitchDegreeCache = False

    def __init__(self,
                 tonic: str | pitch.Pitch | note.Note | None = None,
                 pitches: list[pitch.Pitch | str] | None = None,
                 **keywords):
        super().__init__(**keywords)

        self.type = 'Concrete'
        # store an instance of an abstract scale
        # subclasses might use multiple abstract scales?
        self._abstract: AbstractScale | None = None

        # determine whether this is a limited range
        self.boundRange = False

        if (tonic is None
                and pitches is not None
                and common.isListLike(pitches)
                and pitches):
            tonic = pitches[0]

        # here, tonic is a pitch
        # the abstract scale defines what step the tonic is expected to be
        # found on
        # no default tonic is defined; as such, it is mostly an abstract scale, and
        # can't be used concretely until it is created.
        self.tonic: pitch.Pitch | None
        if tonic is None:
            self.tonic = None  # pitch.Pitch()
        elif isinstance(tonic, str):
            self.tonic = pitch.Pitch(tonic)
        elif isinstance(tonic, note.Note):
            self.tonic = tonic.pitch
        elif isinstance(tonic, pitch.Pitch):  # assume this is a pitch object
            self.tonic = tonic
        else:
            raise ValueError(f'Tonic must be a Pitch, Note, or str, not {type(tonic)}')

        if (pitches is not None
                and common.isListLike(pitches)
                and pitches):
            self._abstract = AbstractScale()
            self._abstract.buildNetworkFromPitches(pitches)
            if self.tonic in pitches:
                self._abstract.tonicDegree = pitches.index(self.tonic) + 1

    @property
    def isConcrete(self):
        '''
        Return True if the scale is Concrete, that is, it has a defined Tonic.

        >>> sc1 = scale.MajorScale('c')
        >>> sc1.isConcrete
        True
        >>> sc2 = scale.MajorScale()
        >>> sc2.isConcrete
        False

        To be concrete, a Scale must have a
        defined tonic. An abstract Scale is not Concrete
        '''
        if self.tonic is None:
            return False
        else:
            return True

    def __eq__(self, other):
        '''
        For concrete equality, the stored abstract objects must evaluate as equal,
        as well as local attributes.

        >>> sc1 = scale.MajorScale('c')
        >>> sc2 = scale.MajorScale('c')
        >>> sc3 = scale.MinorScale('c')
        >>> sc4 = scale.MajorScale('g')
        >>> sc5 = scale.MajorScale()  # an abstract scale, as no tonic defined

        >>> sc1 == sc2
        True
        >>> sc1 == sc3
        False
        >>> sc1 == sc4
        False
        >>> sc1.abstract == sc4.abstract  # can compare abstract forms
        True
        >>> sc4 == sc5  # implicit abstract comparison
        True
        >>> sc5 == sc2  # implicit abstract comparison
        True
        >>> sc5 == sc3  # implicit abstract comparison
        False
        '''
        if not super().__eq__(other):
            return False

        if not self.isConcrete or not other.isConcrete:
            # if tonic is none, then we automatically do an abstract comparison
            return self._abstract == other._abstract
        else:
            if (isinstance(other, self.__class__)
                    and isinstance(self, other.__class__)
                    and self._abstract == other._abstract
                    and self.boundRange == other.boundRange
                    and self.tonic == other.tonic):
                return True
            else:
                return False

    def __hash__(self):
        return id(self) >> 4

    @property
    def name(self):
        '''
        Return or construct the name of this scale

        >>> sc = scale.DiatonicScale()  # abstract, as no defined tonic
        >>> sc.name
        'Abstract diatonic'
        '''
        if self.tonic is None:
            return ' '.join(['Abstract', self.type])
        else:
            return ' '.join([self.tonic.name, self.type])

    def _reprInternal(self):
        return self.name

    # --------------------------------------------------------------------------

    def getTonic(self):
        '''
        Return the tonic.

        >>> sc = scale.ConcreteScale(tonic='e-4')
        >>> sc.getTonic()
        <music21.pitch.Pitch E-4>
        '''
        return self.tonic

    @property
    def abstract(self):
        '''
        Return the AbstractScale instance governing this ConcreteScale.

        >>> sc1 = scale.MajorScale('d')
        >>> sc2 = scale.MajorScale('b-')
        >>> sc1 == sc2
        False
        >>> sc1.abstract == sc2.abstract
        True

        Abstract scales can also be set afterwards:

        >>> scVague = scale.ConcreteScale()
        >>> scVague.abstract = scale.AbstractDiatonicScale('major')
        >>> scVague.tonic = pitch.Pitch('D')
        >>> [p.name for p in scVague.getPitches()]
        ['D', 'E', 'F#', 'G', 'A', 'B', 'C#', 'D']

        >>> scVague.abstract = scale.AbstractOctatonicScale()
        >>> [p.name for p in scVague.getPitches()]
        ['D', 'E', 'F', 'G', 'A-', 'B-', 'C-', 'D-', 'D']

        * Changed in v6: changing `.abstract` is now allowed.
        '''
        # copy before returning? (No... too slow)
        return self._abstract

    @abstract.setter
    def abstract(self, newAbstract: AbstractScale):
        if not isinstance(newAbstract, AbstractScale):
            raise TypeError(f'abstract must be an AbstractScale, not {type(newAbstract)}')
        self._abstract = newAbstract


    def getDegreeMaxUnique(self):
        '''
        Convenience routine to get this from the AbstractScale.
        '''
        return self._abstract.getDegreeMaxUnique()

    def transpose(self, value, *, inPlace=False):
        '''
        Transpose this Scale by the given interval

        Note: It does not make sense to transpose an abstract scale, since
        it is merely a collection of intervals.  Thus,
        only concrete scales can be transposed.

        >>> sc1 = scale.MajorScale('C')
        >>> sc2 = sc1.transpose('p5')
        >>> sc2
        <music21.scale.MajorScale G major>
        >>> sc3 = sc2.transpose('p5')
        >>> sc3
        <music21.scale.MajorScale D major>

        >>> sc3.transpose('p5', inPlace=True)
        >>> sc3
        <music21.scale.MajorScale A major>
        '''
        if inPlace:
            post = self
        else:
            post = copy.deepcopy(self)
        if self.tonic is None:
            # could raise an error; just assume a 'c'
            post.tonic = pitch.Pitch('C4')
            post.tonic.transpose(value, inPlace=True)
        else:
            post.tonic.transpose(value, inPlace=True)
        # may need to clear cache here
        if not inPlace:
            return post

    def tune(
        self,
        streamObj,
        minPitch=None,
        maxPitch=None,
        direction=None
    ) -> None:
        '''
        Given a Stream object containing Pitches, match all pitch names
        and or pitch space values and replace the target pitch with
        copies of pitches stored in this scale.

        This is always applied recursively to all sub-Streams.
        '''
        from music21 import chord

        # we may use a directed or subset of the scale to tune
        # in the future, we might even match contour or direction

        # bug in PyCharm
        # noinspection PyArgumentList
        pitchColl = self.getPitches(minPitch=minPitch,
                                    maxPitch=maxPitch,
                                    direction=direction
                                    )
        pitchCollNames = [p.name for p in pitchColl]

        def tuneOnePitch(p, dst: list[pitch.Pitch]):
            # some pitches might be quarter / 3/4 tones; need to convert
            # these to microtonal representations so that we can directly
            # compare pitch names
            pAlt = p.convertQuarterTonesToMicrotones(inPlace=False)
            # need to permit enharmonic comparisons: G# and A- should
            # in most cases match
            testEnharmonics = pAlt.getAllCommonEnharmonics(alterLimit=2)
            testEnharmonics.append(pAlt)
            for pEnh in testEnharmonics:
                if pEnh.name not in pitchCollNames:
                    continue
                # get the index from the names and extract the pitch by
                # index
                pDst = pitchColl[pitchCollNames.index(pEnh.name)]
                # get a deep copy for each note
                pDstNew = copy.deepcopy(pDst)
                pDstNew.octave = pEnh.octave  # copy octave
                # need to adjust enharmonic
                pDstNewEnh = pDstNew.getAllCommonEnharmonics(alterLimit=2)
                match: pitch.Pitch | None = None
                for x in pDstNewEnh:
                    # try to match enharmonic with original alt
                    if x.name == pAlt.name:
                        match = x
                if match is None:  # get original
                    dst.append(pDstNew)
                else:
                    dst.append(match)

        # for p in streamObj.pitches:  # this is always recursive
        for e in streamObj.recurse().notes:  # get notes and chords
            if e.isChord:
                elementPitches = e.pitches
            else:  # simulate a lost
                elementPitches = [e.pitch]

            # store a list of reset chord pitches
            outerDestination: list[pitch.Pitch] = []

            for p in elementPitches:
                tuneOnePitch(p, outerDestination)
            # reassign the changed pitch
            if outerDestination:
                if isinstance(e, chord.Chord):
                    # note: we may not have matched all pitches
                    e.pitches = tuple(outerDestination)
                else:  # only one
                    e.pitch = outerDestination[0]

    def romanNumeral(self, degree):
        '''
        Return a RomanNumeral object built on the specified scale degree.

        >>> sc1 = scale.MajorScale('a-4')
        >>> h1 = sc1.romanNumeral(1)
        >>> h1.root()
        <music21.pitch.Pitch A-4>

        >>> h5 = sc1.romanNumeral(5)
        >>> h5.root()
        <music21.pitch.Pitch E-5>
        >>> h5
        <music21.roman.RomanNumeral V in A- major>
        '''
        from music21 import roman
        return roman.RomanNumeral(degree, self)

    def getPitches(
        self,
        minPitch: str | pitch.Pitch | None = None,
        maxPitch: str | pitch.Pitch | None = None,
        direction: Direction | None = None
    ) -> list[pitch.Pitch]:
        '''
        Return a list of Pitch objects, using a
        deepcopy of a cached version if available.
        '''
        # get from interval network of abstract scale

        if self._abstract is None:
            return []

        # TODO: get and store in cache; return a copy
        # or generate from network stored in abstract
        if self.tonic is None:
            # note: could raise an error here, but instead will
            # use a pseudo-tonic
            pitchObj = pitch.Pitch('C4')
        else:
            pitchObj = self.tonic
        stepOfPitch = self._abstract.tonicDegree

        minPitchObj: pitch.Pitch | None
        if isinstance(minPitch, str):
            minPitchObj = pitch.Pitch(minPitch)
        else:
            minPitchObj = minPitch

        maxPitchObj: pitch.Pitch | None
        if isinstance(maxPitch, str):
            maxPitchObj = pitch.Pitch(maxPitch)
        else:
            maxPitchObj = maxPitch

        if (minPitchObj is not None
                and maxPitchObj is not None
                and minPitchObj > maxPitchObj
                and direction is None):
            reverse = True
            (minPitchObj, maxPitchObj) = (maxPitchObj, minPitchObj)
        elif direction == Direction.DESCENDING:
            reverse = True  # reverse presentation so pitches go high to low
        else:
            reverse = False

        if direction is None:
            direction = Direction.ASCENDING

        # this creates new pitches on each call
        return self._abstract.getRealization(pitchObj,
                                             stepOfPitch,
                                             minPitch=minPitchObj,
                                             maxPitch=maxPitchObj,
                                             direction=direction,
                                             reverse=reverse)
        # raise ScaleException('Cannot generate a scale from a DiatonicScale class')

    # this needs to stay separate from getPitches; both are needed
    pitches = property(getPitches,
                       doc='''
                           Get a default pitch list from this scale.
                           ''')

    def getChord(
        self,
        minPitch=None,
        maxPitch=None,
        direction=Direction.ASCENDING,
        **keywords
    ) -> 'music21.chord.Chord':
        '''
        Return a realized chord containing all the
        pitches in this scale within a particular
        inclusive range defined by two pitches.

        All keyword arguments are passed on to the
        Chord, permitting specification of
        `quarterLength` and similar parameters.
        '''
        from music21 import chord

        # bug in PyCharm
        # noinspection PyArgumentList
        myPitches = self.getPitches(minPitch=minPitch,
                                    maxPitch=maxPitch,
                                    direction=direction)
        return chord.Chord(myPitches, **keywords)

    # this needs to stay separate from getChord
    chord = property(getChord,
                     doc='''
        Return a Chord object from this harmony over a default range.
        Use the `getChord()` method if you need greater control over the
        parameters of the chord.
        ''')

    def pitchFromDegree(
            self,
            degree: int,
            minPitch=None,
            maxPitch=None,
            direction: Direction = Direction.ASCENDING,
            equateTermini: bool = True):
        '''
        Given a scale degree, return a deepcopy of the appropriate pitch.

        >>> sc = scale.MajorScale('e-')
        >>> sc.pitchFromDegree(2)
        <music21.pitch.Pitch F4>
        >>> sc.pitchFromDegree(7)
        <music21.pitch.Pitch D5>

        OMIT_FROM_DOCS

        Test deepcopy

        >>> d = sc.pitchFromDegree(7)
        >>> d.accidental = pitch.Accidental('sharp')
        >>> d
        <music21.pitch.Pitch D#5>
        >>> sc.pitchFromDegree(7)
        <music21.pitch.Pitch D5>
        '''
        if self._abstract is None:  # pragma: no cover
            raise ScaleException('Abstract scale underpinning this scale is not defined.')

        cacheKey: _PitchDegreeCacheKey | None = None
        if (self.usePitchDegreeCache and self.tonic
                and not minPitch and not maxPitch and getattr(self, 'type', None)):
            tonicCacheKey = self.tonic.nameWithOctave
            cacheKey = (
                self.__class__,
                self.type,
                tonicCacheKey,
                degree,
                direction,
                equateTermini
            )
            if cacheKey in _pitchDegreeCache:
                return pitch.Pitch(_pitchDegreeCache[cacheKey])

        post = self._abstract.getPitchFromNodeDegree(
            pitchReference=self.tonic,  # pitch defined here
            nodeName=self._abstract.tonicDegree,  # defined in abstract class
            nodeDegreeTarget=degree,  # target looking for
            direction=direction,
            minPitch=minPitch,
            maxPitch=maxPitch,
            equateTermini=equateTermini)

        if cacheKey:
            _pitchDegreeCache[cacheKey] = post.nameWithOctave

        return post

        # if 0 < degree <= self._abstract.getDegreeMaxUnique():
        #     return self.getPitches()[degree - 1]
        # else:
        #     raise('Scale degree is out of bounds: must be between 1 and %s.' % (
        #        self._abstract.getDegreeMaxUnique()))

    def pitchesFromScaleDegrees(
            self,
            degreeTargets,
            minPitch=None,
            maxPitch=None,
            direction=Direction.ASCENDING):
        '''
        Given one or more scale degrees, return a list
        of all matches over the entire range.

        >>> sc = scale.MajorScale('e-')
        >>> sc.pitchesFromScaleDegrees([3, 7])
        [<music21.pitch.Pitch G4>, <music21.pitch.Pitch D5>]
        >>> [str(p) for p in sc.pitchesFromScaleDegrees([3, 7], 'c2', 'c6')]
        ['D2', 'G2', 'D3', 'G3', 'D4', 'G4', 'D5', 'G5']

        >>> sc = scale.HarmonicMinorScale('a')
        >>> [str(p) for p in sc.pitchesFromScaleDegrees([3, 7], 'c2', 'c6')]
        ['C2', 'G#2', 'C3', 'G#3', 'C4', 'G#4', 'C5', 'G#5', 'C6']
        '''
        # TODO: rely here on intervalNetwork for caching
        post = self._abstract.realizePitchByDegree(
            pitchReference=self.tonic,  # pitch defined here
            nodeId=self._abstract.tonicDegree,  # defined in abstract class
            nodeDegreeTargets=degreeTargets,  # target looking for
            direction=direction,
            minPitch=minPitch,
            maxPitch=maxPitch)
        return post

    def intervalBetweenDegrees(
            self,
            degreeStart,
            degreeEnd,
            direction=Direction.ASCENDING,
            equateTermini=True):
        '''
        Given two degrees, provide the interval as an interval.Interval object.

        >>> sc = scale.MajorScale('e-')
        >>> sc.intervalBetweenDegrees(3, 7)
        <music21.interval.Interval P5>
        '''
        # get pitches for each degree
        pStart = self.pitchFromDegree(degreeStart, direction=direction,
                                      equateTermini=equateTermini)
        pEnd = self.pitchFromDegree(degreeEnd, direction=direction,
                                    equateTermini=equateTermini)
        if pStart is None:
            raise ScaleException(f'cannot get a pitch for scale degree: {pStart}')
        if pEnd is None:
            raise ScaleException(f'cannot get a pitch for scale degree: {pEnd}')
        return interval.Interval(pStart, pEnd)

    def getScaleDegreeFromPitch(self,
                                pitchTarget,
                                direction=Direction.ASCENDING,
                                comparisonAttribute='name'):
        '''
        For a given pitch, return the appropriate scale degree.
        If no scale degree is available, None is returned.

        Note: by default it will use a find algorithm that is based on the note's
        `.name` not on `.pitchClass` because this is used so commonly by tonal functions.
        So if it's important that D# and E- are the same, set the
        comparisonAttribute to `pitchClass`

        >>> sc = scale.MajorScale('e-')
        >>> sc.getScaleDegreeFromPitch('e-2')
        1
        >>> sc.getScaleDegreeFromPitch('d')
        7
        >>> sc.getScaleDegreeFromPitch('d#', comparisonAttribute='name') is None
        True
        >>> sc.getScaleDegreeFromPitch('d#', comparisonAttribute='pitchClass')
        1
        >>> sc.getScaleDegreeFromPitch('e') is None
        True
        >>> sc.getScaleDegreeFromPitch('e', comparisonAttribute='step')
        1

        >>> sc = scale.HarmonicMinorScale('a')
        >>> sc.getScaleDegreeFromPitch('c')
        3
        >>> sc.getScaleDegreeFromPitch('g#')
        7
        >>> sc.getScaleDegreeFromPitch('g') is None
        True

        >>> cMaj = key.Key('C')
        >>> cMaj.getScaleDegreeFromPitch(pitch.Pitch('E-'),
        ...                              direction=scale.Direction.ASCENDING,
        ...                              comparisonAttribute='step')
        3
        '''
        post = self._abstract.getRelativeNodeDegree(pitchReference=self.tonic,
                                                    nodeName=self._abstract.tonicDegree,
                                                    pitchTarget=pitchTarget,
                                                    comparisonAttribute=comparisonAttribute,
                                                    direction=direction)
        return post

    def getScaleDegreeAndAccidentalFromPitch(self,
                                             pitchTarget,
                                             direction=Direction.ASCENDING,
                                             comparisonAttribute='name'):
        '''
        Given a scale (or :class:`~music21.key.Key` object) and a pitch, return a two-element
        tuple of the degree of the scale and an accidental (or None) needed to get this
        pitch.

        >>> cMaj = key.Key('C')
        >>> cMaj.getScaleDegreeAndAccidentalFromPitch(pitch.Pitch('E'))
        (3, None)
        >>> cMaj.getScaleDegreeAndAccidentalFromPitch(pitch.Pitch('E-'))
        (3, <music21.pitch.Accidental flat>)


        The Direction of a melodic minor scale is significant

        >>> aMin = scale.MelodicMinorScale('a')
        >>> aMin.getScaleDegreeAndAccidentalFromPitch(pitch.Pitch('G'),
        ...                                           direction=scale.Direction.DESCENDING)
        (7, None)
        >>> aMin.getScaleDegreeAndAccidentalFromPitch(pitch.Pitch('G'),
        ...                                           direction=scale.Direction.ASCENDING)
        (7, <music21.pitch.Accidental flat>)
        >>> aMin.getScaleDegreeAndAccidentalFromPitch(pitch.Pitch('G-'),
        ...                                           direction=scale.Direction.ASCENDING)
        (7, <music21.pitch.Accidental double-flat>)

        Returns (None, None) if for some reason this scale does not have this step
        (a whole-tone scale, for instance)
        '''
        scaleStep = self.getScaleDegreeFromPitch(pitchTarget, direction, comparisonAttribute)
        if scaleStep is not None:
            return (scaleStep, None)
        else:
            scaleStepNormal = self.getScaleDegreeFromPitch(pitchTarget,
                                                           direction,
                                                           comparisonAttribute='step')
            if scaleStepNormal is None:
                raise ScaleException(
                    'Cannot get any scale degree from getScaleDegreeFromPitch for pitchTarget '
                    + f"{pitchTarget}, direction {direction}, comparisonAttribute='step'")
            pitchesFound = self.pitchesFromScaleDegrees([scaleStepNormal])

            if not pitchesFound:
                return (None, None)
            else:
                foundPitch = pitchesFound[0]
            if foundPitch.accidental is None:
                foundAlter = 0
            else:
                foundAlter = foundPitch.accidental.alter

            if pitchTarget.accidental is None:
                pitchAlter = 0
            else:
                pitchAlter = pitchTarget.accidental.alter

            alterDiff = pitchAlter - foundAlter

            if alterDiff == 0:
                # should not happen...
                return (scaleStepNormal, None)
            else:
                alterAccidental = pitch.Accidental(alterDiff)
                return (scaleStepNormal, alterAccidental)

    # uses "traditional" chromatic solfeg and mostly Shearer Hullah (if needed)
    # noinspection SpellCheckingInspection
    _solfegSyllables = {1: {-2: 'def',
                            -1: 'de',
                             0: 'do',
                             1: 'di',
                             2: 'dis',
                            },
                        2: {-2: 'raf',
                            -1: 'ra',
                             0: 're',
                             1: 'ri',
                             2: 'ris',
                            },
                        3: {-2: 'mef',
                            -1: 'me',
                             0: 'mi',
                             1: 'mis',
                             2: 'mish',
                            },
                        4: {-2: 'fef',
                            -1: 'fe',
                             0: 'fa',
                             1: 'fi',
                             2: 'fis',
                            },
                        5: {-2: 'sef',
                            -1: 'se',
                             0: 'sol',
                             1: 'si',
                             2: 'sis',
                            },
                        6: {-2: 'lef',
                            -1: 'le',
                             0: 'la',
                             1: 'li',
                             2: 'lis',
                            },
                        7: {-2: 'tef',
                            -1: 'te',
                             0: 'ti',
                             1: 'tis',
                             2: 'tish',
                            },
                        }
    # TOO SLOW!
    # _humdrumSolfegSyllables = copy.deepcopy(_solfegSyllables)
    # _humdrumSolfegSyllables[3][1] = 'my'
    # _humdrumSolfegSyllables[5] = {-2: 'sef', -1: 'se', 0: 'so', 1:'si', 2:'sis'}
    # _humdrumSolfegSyllables[7][1] = 'ty'
    # noinspection SpellCheckingInspection
    _humdrumSolfegSyllables = {
        1: {-2: 'def',
            -1: 'de',
             0: 'do',
             1: 'di',
             2: 'dis',
            },
        2: {-2: 'raf',
            -1: 'ra',
             0: 're',
             1: 'ri',
             2: 'ris',
            },
        3: {-2: 'mef',
            -1: 'me',
             0: 'mi',
             1: 'my',
             2: 'mish',
            },
        4: {-2: 'fef',
            -1: 'fe',
             0: 'fa',
             1: 'fi',
             2: 'fis',
            },
        5: {-2: 'sef',
            -1: 'se',
             0: 'so',
             1: 'si',
             2: 'sis',
            },
        6: {-2: 'lef',
            -1: 'le',
             0: 'la',
             1: 'li',
             2: 'lis',
            },
        7: {-2: 'tef',
            -1: 'te',
             0: 'ti',
             1: 'ty',
             2: 'tish',
            },
    }

    def solfeg(self,
               pitchTarget=None,
               direction=Direction.ASCENDING,
               variant='music21',
               chromatic=True):
        '''
        Returns the chromatic solfeg (or diatonic if chromatic is False)
        for a given pitch in a given scale.

        The `variant` method lets one specify either the default `music21`
        or `humdrum` solfeg representation
        for altered notes.

        >>> eflatMaj = key.Key('E-')
        >>> eflatMaj.solfeg(pitch.Pitch('G'))
        'mi'
        >>> eflatMaj.solfeg('A')
        'fi'
        >>> eflatMaj.solfeg('A', chromatic=False)
        'fa'
        >>> eflatMaj.solfeg(pitch.Pitch('G#'), variant='music21')  # default
        'mis'
        >>> eflatMaj.solfeg(pitch.Pitch('G#'), variant='humdrum')
        'my'
        '''
        if isinstance(pitchTarget, str):
            pitchTarget = pitch.Pitch(pitchTarget)
        (scaleDeg, accidental) = self.getScaleDegreeAndAccidentalFromPitch(pitchTarget, direction)
        if variant == 'music21':
            syllableDict = self._solfegSyllables
        elif variant == 'humdrum':
            syllableDict = self._humdrumSolfegSyllables
        else:
            raise ScaleException(f'Unknown solfeg variant {variant}')

        if scaleDeg > 7:
            raise ScaleException('Cannot call solfeg on non-7-degree scales')
        if scaleDeg is None:
            raise ScaleException('Unknown scale degree for this pitch')

        if chromatic is True:
            if accidental is None:
                return syllableDict[scaleDeg][0]
            else:
                return syllableDict[scaleDeg][accidental.alter]
        else:
            return syllableDict[scaleDeg][0]

    # no type checking as a deprecated call that shadows superclass.
    @t.no_type_check
    @deprecated('v9', 'v10', 'use nextPitch instead')
    def next(
        self,
        pitchOrigin=None,
        direction: Direction | int = Direction.ASCENDING,
        stepSize=1,
        getNeighbor: Direction | bool = True,
    ):  # pragma: no cover
        '''
        See :meth:`~music21.scale.ConcreteScale.nextPitch`.  This function
        is a deprecated alias for that method.

        This routine was named and created before music21 aspired to have
        full subclass substitution.  Thus, is shadows the `.next()` function of
        Music21Object without performing similar functionality.

        The routine is formally deprecated in v9 and will be removed in v10.
        '''
        return self.nextPitch(
            pitchOrigin=pitchOrigin,
            direction=direction,
            stepSize=stepSize,
            getNeighbor=getNeighbor
        )

    def nextPitch(
        self,
        pitchOrigin=None,
        direction: Direction | int = Direction.ASCENDING,
        stepSize=1,
        getNeighbor: Direction | bool = True,
    ):
        '''
        Get the next pitch above (or below if direction is Direction.DESCENDING)
        a `pitchOrigin` or None. If the `pitchOrigin` is None, the tonic pitch is
        returned. This is useful when starting a chain of iterative calls.

        The `direction` attribute may be either ascending or descending.
        Default is `ascending`. Optionally, positive or negative integers
        may be provided as directional stepSize scalars.

        An optional `stepSize` argument can be used to set the number
        of scale steps that are stepped through.  Thus, .nextPitch(stepSize=2)
        will give not the next pitch in the scale, but the next after this one.

        The `getNeighbor` will return a pitch from the scale
        if `pitchOrigin` is not in the scale. This value can be
        True, Direction.ASCENDING, or Direction.DESCENDING.

        >>> sc = scale.MajorScale('e-')
        >>> print(sc.nextPitch('e-5'))
        F5
        >>> print(sc.nextPitch('e-5', stepSize=2))
        G5
        >>> print(sc.nextPitch('e-6', stepSize=3))
        A-6

        This uses the getNeighbor attribute to
        find the next note above f#5 in the E-flat
        major scale:

        >>> sc.nextPitch('f#5')
        <music21.pitch.Pitch G5>

        >>> sc = scale.HarmonicMinorScale('g')
        >>> sc.nextPitch('g4', scale.Direction.DESCENDING)
        <music21.pitch.Pitch F#4>
        >>> sc.nextPitch('F#4', scale.Direction.DESCENDING)
        <music21.pitch.Pitch E-4>
        >>> sc.nextPitch('E-4', scale.Direction.DESCENDING)
        <music21.pitch.Pitch D4>
        >>> sc.nextPitch('E-4', scale.Direction.ASCENDING, 1)
        <music21.pitch.Pitch F#4>
        >>> sc.nextPitch('E-4', scale.Direction.ASCENDING, 2)
        <music21.pitch.Pitch G4>
        '''
        if pitchOrigin is None:
            return self.tonic

        if self._abstract is None:  # pragma: no cover
            raise ScaleException('Abstract scale underpinning this scale is not defined.')

        directionEnum: Direction

        # allow numerical directions
        if isinstance(direction, int):
            if direction != 0:
                # treat as a positive or negative step scalar
                if direction > 0:
                    stepScalar = direction
                    directionEnum = Direction.ASCENDING
                else:  # negative non-zero
                    stepScalar = abs(direction)
                    directionEnum = Direction.DESCENDING
            else:
                raise ScaleException('direction cannot be zero')
        else:  # when direction is a string, use scalar of 1
            stepScalar = 1  # stepSize is still used...
            directionEnum = direction

        # pick reverse direction for neighbor
        if getNeighbor is True:
            if directionEnum == Direction.ASCENDING:
                getNeighbor = Direction.DESCENDING
            elif directionEnum == Direction.DESCENDING:
                getNeighbor = Direction.ASCENDING

        post = self._abstract.nextPitch(
            pitchReference=self.tonic,
            nodeName=self._abstract.tonicDegree,
            pitchOrigin=pitchOrigin,
            direction=directionEnum,
            stepSize=stepSize * stepScalar,  # multiplied
            getNeighbor=getNeighbor
        )
        return post

    def isNext(self,
               other,
               pitchOrigin,
               direction: Direction = Direction.ASCENDING,
               stepSize=1,
               getNeighbor: Direction | bool = True,
               comparisonAttribute='name'):
        '''
        Given another pitch, as well as an origin and a direction,
        determine if this other pitch is in the next in the scale.

        >>> sc1 = scale.MajorScale('g')
        >>> sc1.isNext('d4', 'c4', scale.Direction.ASCENDING)
        True
        '''
        if isinstance(other, str):  # convert to pitch
            other = pitch.Pitch(other)
        elif hasattr(other, 'pitch'):  # possibly a note
            other = other.pitch  # just get pitch component
        elif not isinstance(other, pitch.Pitch):
            return False  # cannot compare to non-pitch

        nPitch = self.nextPitch(pitchOrigin,
                                direction=direction,
                                stepSize=stepSize,
                                getNeighbor=getNeighbor)
        if nPitch is None:
            return None

        if (getattr(nPitch, comparisonAttribute)
                == getattr(other, comparisonAttribute)):
            return True
        else:
            return False

    # --------------------------------------------------------------------------
    # comparison and evaluation

    def match(self, other, comparisonAttribute='name'):
        '''
        Given another object of the forms that `extractPitchList` can take,
        (e.g., a :class:`~music21.stream.Stream`, a :class:`~music21.scale.ConcreteScale`,
        a list of :class:`~music21.pitch.Pitch` objects),
        return a named dictionary of pitch lists with keys 'matched' and 'notMatched'.

        >>> sc1 = scale.MajorScale('g')
        >>> sc2 = scale.MajorScale('d')
        >>> sc3 = scale.MajorScale('a')
        >>> sc4 = scale.MajorScale('e')

        >>> from pprint import pprint as pp
        >>> pp(sc1.match(sc2))
        {'matched': [<music21.pitch.Pitch D4>, <music21.pitch.Pitch E4>,
                     <music21.pitch.Pitch F#4>, <music21.pitch.Pitch G4>,
                     <music21.pitch.Pitch A4>, <music21.pitch.Pitch B4>],
        'notMatched': [<music21.pitch.Pitch C#5>]}

        >>> pp(sc2.match(sc3))
        {'matched': [<music21.pitch.Pitch A4>, <music21.pitch.Pitch B4>,
                     <music21.pitch.Pitch C#5>, <music21.pitch.Pitch D5>,
                     <music21.pitch.Pitch E5>, <music21.pitch.Pitch F#5>],
        'notMatched': [<music21.pitch.Pitch G#5>]}

        >>> pp(sc1.match(sc4))
        {'matched': [<music21.pitch.Pitch E4>, <music21.pitch.Pitch F#4>,
                     <music21.pitch.Pitch A4>, <music21.pitch.Pitch B4>],
         'notMatched': [<music21.pitch.Pitch G#4>,
                        <music21.pitch.Pitch C#5>,
                        <music21.pitch.Pitch D#5>]}
        '''
        # strip out unique pitches in a list
        otherPitches = self.extractPitchList(other,
                                             comparisonAttribute=comparisonAttribute)

        # need to deal with direction here? or get an aggregate scale
        matched, notMatched = self._abstract._net.match(
            pitchReference=self.tonic,
            nodeId=self._abstract.tonicDegree,
            pitchTarget=otherPitches,  # can supply a list here
            comparisonAttribute=comparisonAttribute)

        post = {
            'matched': matched,
            'notMatched': notMatched,
        }
        return post

    def findMissing(self,
                    other,
                    comparisonAttribute='pitchClass',
                    minPitch=None,
                    maxPitch=None,
                    direction=Direction.ASCENDING,
                    alteredDegrees=None):
        '''
        Given another object of the forms that `extractPitches` takes
        (e.g., a :class:`~music21.stream.Stream`,
        a :class:`~music21.scale.ConcreteScale`,
        a list of :class:`~music21.pitch.Pitch` objects),
        return a list of pitches that are found in this Scale but are not
        found in the provided object.

        >>> sc1 = scale.MajorScale('g4')
        >>> [str(p) for p in sc1.findMissing(['d'])]
        ['G4', 'A4', 'B4', 'C5', 'E5', 'F#5', 'G5']
        '''
        # strip out unique pitches in a list
        otherPitches = self.extractPitchList(other,
                                             comparisonAttribute=comparisonAttribute)
        post = self._abstract._net.findMissing(
            pitchReference=self.tonic,
            nodeId=self._abstract.tonicDegree,
            pitchTarget=otherPitches,  # can supply a list here
            comparisonAttribute=comparisonAttribute,
            minPitch=minPitch,
            maxPitch=maxPitch,
            direction=direction,
            alteredDegrees=alteredDegrees,
        )
        return post

    def deriveRanked(self,
                     other,
                     resultsReturned=4,
                     comparisonAttribute='pitchClass',
                     removeDuplicates=False):
        # noinspection PyShadowingNames
        '''
        Return a list of closest-matching :class:`~music21.scale.ConcreteScale` objects
        based on this :class:`~music21.scale.AbstractScale`,
        provided as a :class:`~music21.stream.Stream`, a :class:`~music21.scale.ConcreteScale`,
        or a list of :class:`~music21.pitch.Pitch` objects.
        Returned integer values represent the number of matches.

        If you are working with Diatonic Scales, you will probably
        want to change the `comparisonAttribute` to `name`.

        >>> sc1 = scale.MajorScale()
        >>> sc1.deriveRanked(['C', 'E', 'B'])
        [(3, <music21.scale.MajorScale G major>),
         (3, <music21.scale.MajorScale C major>),
         (2, <music21.scale.MajorScale B major>),
         (2, <music21.scale.MajorScale A major>)]

        With the default of comparing by pitchClass, D- is fine for B major
        because C# is in the B major scale.

        >>> sc1.deriveRanked(['D-', 'E', 'B'])
        [(3, <music21.scale.MajorScale B major>),
         (3, <music21.scale.MajorScale A major>),
         (3, <music21.scale.MajorScale E major>),
         (3, <music21.scale.MajorScale D major>)]

        Comparing based on enharmonic-sensitive spelling, has fewer hits
        for all of these scales:

        >>> sc1.deriveRanked(['D-', 'E', 'B'], comparisonAttribute='name')
        [(2, <music21.scale.MajorScale B major>),
         (2, <music21.scale.MajorScale A major>),
         (2, <music21.scale.MajorScale G major>),
         (2, <music21.scale.MajorScale E major>)]

        Notice that we check how many of the pitches are in the scale
        and do not de-duplicate pitches.

        >>> sc1.deriveRanked(['C', 'E', 'E', 'E', 'B'])
        [(5, <music21.scale.MajorScale G major>),
         (5, <music21.scale.MajorScale C major>),
         (4, <music21.scale.MajorScale B major>),
         (4, <music21.scale.MajorScale A major>)]

        If removeDuplicates is given, the E's will get less weight:

        >>> sc1.deriveRanked(['C', 'E', 'E', 'E', 'B'], removeDuplicates=True)
        [(3, <music21.scale.MajorScale G major>),
         (3, <music21.scale.MajorScale C major>),
         (2, <music21.scale.MajorScale B major>),
         (2, <music21.scale.MajorScale A major>)]

        >>> sc1.deriveRanked(['C#', 'E', 'G#'])
        [(3, <music21.scale.MajorScale B major>),
         (3, <music21.scale.MajorScale A major>),
         (3, <music21.scale.MajorScale E major>),
         (3, <music21.scale.MajorScale C- major>)]

        A Concrete Scale created from pitches still has similar
        characteristics to the original.

        Here we create a scale like a Harmonic minor but with flat 2 and sharp 4.

        >>> e = scale.ConcreteScale(pitches=['A4', 'B-4', 'C5', 'D#5', 'E5', 'F5', 'G#5', 'A5'])

        Notice the G# is allowed to be chosen even though we are specifically looking for
        scales with a G natural in them.  Once no scale matched all three pitches,
        which scale that matches two pitches is arbitrary.

        >>> bestScales = e.deriveRanked(['C', 'E', 'G'], resultsReturned=6)
        >>> bestScales
        [(3, <music21.scale.ConcreteScale E Concrete>),
         (3, <music21.scale.ConcreteScale D- Concrete>),
         (3, <music21.scale.ConcreteScale C# Concrete>),
         (2, <music21.scale.ConcreteScale B Concrete>),
         (2, <music21.scale.ConcreteScale A Concrete>),
         (2, <music21.scale.ConcreteScale G# Concrete>)]


        >>> eConcrete = bestScales[0][1]
        >>> ' '.join([str(p) for p in eConcrete.pitches])
        'E4 F4 G4 A#4 B4 C5 D#5 E5'
        '''
        # possibly return dictionary with named parameters
        # default return all scales that match all provided pitches
        # instead of results returned, define how many matched pitches necessary
        otherPitches = self.extractPitchList(other,
                                             comparisonAttribute=comparisonAttribute,
                                             removeDuplicates=removeDuplicates)

        pairs = self._abstract._net.find(pitchTarget=otherPitches,
                                         resultsReturned=resultsReturned,
                                         comparisonAttribute=comparisonAttribute,
                                         alteredDegrees=self._abstract._alteredDegrees)
        post = []
        for weight, p in pairs:
            sc = self.__class__(tonic=p)
            if sc.abstract is None:
                sc.abstract = copy.deepcopy(self._abstract)

            post.append((weight, sc))
        return post

    def derive(self, other, comparisonAttribute='pitchClass'):
        '''
        Return the closest-matching :class:`~music21.scale.ConcreteScale`
        based on the pitch collection provided as a
        :class:`~music21.stream.Stream`, a :class:`~music21.scale.ConcreteScale`,
        or a list of :class:`~music21.pitch.Pitch` objects.

        How the "closest-matching" scale is defined still needs to be
        refined and has changed in the past and will probably change in the future.

        >>> sc1 = scale.MajorScale()
        >>> sc1.derive(['C#', 'E', 'G#'])
        <music21.scale.MajorScale B major>

        >>> sc1.derive(['E-', 'B-', 'D'], comparisonAttribute='name')
        <music21.scale.MajorScale B- major>
        '''
        otherPitches = self.extractPitchList(other,
                                             comparisonAttribute=comparisonAttribute)

        # weight target membership
        pairs = self._abstract._net.find(pitchTarget=otherPitches,
                                         comparisonAttribute=comparisonAttribute)

        newScale = self.__class__(tonic=pairs[0][1])
        if newScale.abstract is None:
            newScale.abstract = copy.deepcopy(self._abstract)
        return newScale

    def deriveAll(self, other, comparisonAttribute='pitchClass'):
        # noinspection PyShadowingNames
        '''
        Return a list of all Scales of the same class as `self`
        where all the pitches in `other` are contained.

        Similar to "deriveRanked" but only returns those scales
        no matter how many which contain all the pitches.

        Just returns a list in order.

        If you are working with Diatonic Scales, you will
        probably want to change the `comparisonAttribute` to `name`.

        >>> sc1 = scale.MajorScale()
        >>> sc1.deriveAll(['C', 'E', 'B'])
        [<music21.scale.MajorScale G major>, <music21.scale.MajorScale C major>]

        >>> [sc.name for sc in sc1.deriveAll(['D-', 'E', 'B'])]
        ['B major', 'A major', 'E major', 'D major', 'C- major']

        >>> sc1.deriveAll(['D-', 'E', 'B'], comparisonAttribute='name')
        []

        Find all instances of this pentatonic scale in major scales:

        >>> scList = sc1.deriveAll(['C#', 'D#', 'F#', 'G#', 'A#'], comparisonAttribute='name')
        >>> [sc.name for sc in scList]
        ['B major', 'F# major', 'C# major']
        '''
        # possibly return dictionary with named parameters
        # default return all scales that match all provided pitches
        # instead of results returned, define how many matched pitches necessary
        otherPitches = self.extractPitchList(other,
                                             comparisonAttribute=comparisonAttribute)

        pairs = self._abstract._net.find(pitchTarget=otherPitches,
                                         resultsReturned=None,
                                         comparisonAttribute=comparisonAttribute,
                                         alteredDegrees=self._abstract._alteredDegrees)
        post = []
        numPitches = len(otherPitches)

        for weight, p in pairs:
            if weight == numPitches:  # only want matches where all notes match
                sc = self.__class__(tonic=p)
                if sc.abstract is None:
                    sc.abstract = copy.deepcopy(self._abstract)
                post.append(sc)
        return post

    def deriveByDegree(self, degree, pitchRef):
        '''
        Given a scale degree and a pitch, return a
        new :class:`~music21.scale.ConcreteScale` that satisfies
        that condition.

        Find a major scale with C as the 7th degree:

        >>> sc1 = scale.MajorScale()
        >>> sc1.deriveByDegree(7, 'c')
        <music21.scale.MajorScale D- major>

        TODO: Does not yet work for directional scales
        '''
        p = self._abstract.getNewTonicPitch(
            pitchReference=pitchRef,
            nodeName=degree,
        )
        # except intervalNetwork.IntervalNetworkException:
        #     p = self._abstract.getNewTonicPitch(
        #         pitchReference=pitchRef,
        #         nodeName=degree,
        #         direction=Direction.DESCENDING,
        #     )

        if p is None:
            raise ScaleException('cannot derive new tonic')

        newScale = self.__class__(tonic=p)
        if newScale.abstract is None:
            newScale.abstract = copy.deepcopy(self._abstract)
        return newScale

    # --------------------------------------------------------------------------
    # alternative outputs

    def getScalaData(self):
        '''
        Return a configured :class:`~music21.scala.ScalaData`
        Object for this scale.  It can be used to find interval
        distances in cents between degrees.
        '''
        ss = self.abstract.getScalaData()
        # customize with more specific representation
        ss.description = repr(self)
        return ss

    def write(self, fmt=None, fp=None, direction=Direction.ASCENDING):
        '''
        Write the scale in a format.
        Here, prepare scala format if requested.
        '''
        if fmt is not None:
            fileFormat, unused_ext = common.findFormat(fmt)
            if fileFormat == 'scala':
                return self.abstract.write(fmt=fmt, fp=fp, direction=direction)
        return Scale.write(self, fmt=fmt, fp=fp)

    def show(self, fmt=None, app=None, direction=Direction.ASCENDING):
        '''
        Show the scale in a format. Here, prepare scala format
        if requested.
        '''
        if fmt is not None:
            fileFormat, unused_ext = common.findFormat(fmt)
            if fileFormat == 'scala':
                self.abstract.show(fmt=fmt, app=app, direction=direction)
                return
        Scale.show(self, fmt=fmt, app=app)

# ------------------------------------------------------------------------------
# concrete scales and subclasses


class DiatonicScale(ConcreteScale):
    '''
    A concrete diatonic scale. Each DiatonicScale
    has one instance of a :class:`~music21.scale.AbstractDiatonicScale`.
    '''
    usePitchDegreeCache = True

    def __init__(self, tonic: str | pitch.Pitch | note.Note | None = None, **keywords):
        super().__init__(tonic=tonic, **keywords)
        self._abstract: AbstractDiatonicScale = AbstractDiatonicScale(**keywords)
        self.type = 'diatonic'

    def getTonic(self):
        '''
        Return the tonic of the diatonic scale.

        >>> sc = scale.MajorScale('e-')
        >>> sc.getTonic()
        <music21.pitch.Pitch E-4>
        >>> sc = scale.MajorScale('F#')
        >>> sc.getTonic()
        <music21.pitch.Pitch F#4>

        If no tonic has been defined, it will return an Exception.
        (same is true for `getDominant`, `getLeadingTone`, etc.)

        >>> sc = scale.DiatonicScale()
        >>> sc.getTonic()
        Traceback (most recent call last):
        music21.scale.intervalNetwork.IntervalNetworkException: pitchReference cannot be None
        '''
        # NOTE: override method on ConcreteScale that simply returns _tonic
        return self.pitchFromDegree(self._abstract.tonicDegree)

    def getDominant(self):
        '''
        Return the dominant.

        >>> sc = scale.MajorScale('e-')
        >>> sc.getDominant()
        <music21.pitch.Pitch B-4>
        >>> sc = scale.MajorScale('F#')
        >>> sc.getDominant()
        <music21.pitch.Pitch C#5>
        '''
        return self.pitchFromDegree(self._abstract.dominantDegree)

    def getLeadingTone(self):
        '''
        Return the leading tone.

        >>> sc = scale.MinorScale('c')
        >>> sc.getLeadingTone()
        <music21.pitch.Pitch B4>

        Note that the leading tone isn't necessarily
        the same as the 7th scale degree in minor:

        >>> sc.pitchFromDegree(7)
        <music21.pitch.Pitch B-4>
        '''
        # NOTE: must adjust for modes that do not have a proper leading tone
        seventhDegree = self.pitchFromDegree(7)
        distanceInSemitones = seventhDegree.midi - self.tonic.midi
        if distanceInSemitones != 11:
            # if not a major seventh, raise/lower the seventh degree
            alterationInSemitones = 11 - distanceInSemitones
            seventhDegree.accidental = pitch.Accidental(
                seventhDegree.alter + alterationInSemitones
            )
        return seventhDegree

    def getParallelMinor(self):
        '''
        Return a parallel minor scale based on this
        concrete scale.

        >>> sc1 = scale.MajorScale(pitch.Pitch('a'))
        >>> [str(p) for p in sc1.pitches]
        ['A4', 'B4', 'C#5', 'D5', 'E5', 'F#5', 'G#5', 'A5']
        >>> sc2 = sc1.getParallelMinor()
        >>> [str(p) for p in sc2.pitches]
        ['A4', 'B4', 'C5', 'D5', 'E5', 'F5', 'G5', 'A5']

        Running getParallelMinor() again doesn't change anything

        >>> sc3 = sc2.getParallelMinor()
        >>> [str(p) for p in sc3.pitches]
        ['A4', 'B4', 'C5', 'D5', 'E5', 'F5', 'G5', 'A5']
        '''
        return MinorScale(self.tonic)

    def getParallelMajor(self):
        '''
        Return a concrete relative major scale

        >>> sc1 = scale.MinorScale(pitch.Pitch('g'))
        >>> [str(p) for p in sc1.pitches]
        ['G4', 'A4', 'B-4', 'C5', 'D5', 'E-5', 'F5', 'G5']

        >>> sc2 = sc1.getParallelMajor()
        >>> [str(p) for p in sc2.pitches]
        ['G4', 'A4', 'B4', 'C5', 'D5', 'E5', 'F#5', 'G5']
        '''
        return MajorScale(self.tonic)

    def getRelativeMinor(self):
        '''
        Return a relative minor scale based on this concrete scale.

        >>> sc1 = scale.MajorScale(pitch.Pitch('a'))
        >>> [str(p) for p in sc1.pitches]
        ['A4', 'B4', 'C#5', 'D5', 'E5', 'F#5', 'G#5', 'A5']
        >>> sc2 = sc1.getRelativeMinor()
        >>> [str(p) for p in sc2.pitches]
        ['F#5', 'G#5', 'A5', 'B5', 'C#6', 'D6', 'E6', 'F#6']
        '''
        return MinorScale(self.pitchFromDegree(self.abstract.relativeMinorDegree))

    def getRelativeMajor(self):
        '''
        Return a concrete relative major scale

        >>> sc1 = scale.MinorScale(pitch.Pitch('g'))
        >>> [str(p) for p in sc1.pitches]
        ['G4', 'A4', 'B-4', 'C5', 'D5', 'E-5', 'F5', 'G5']

        >>> sc2 = sc1.getRelativeMajor()
        >>> [str(p) for p in sc2.pitches]
        ['B-4', 'C5', 'D5', 'E-5', 'F5', 'G5', 'A5', 'B-5']

        Though it's unlikely you would want to do it,
        `getRelativeMajor` works on other diatonic scales than
        just Major and Minor.

        >>> sc2 = scale.DorianScale('d')
        >>> [str(p) for p in sc2.pitches]
        ['D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5', 'D5']

        >>> [str(p) for p in sc2.getRelativeMajor().pitches]
        ['C5', 'D5', 'E5', 'F5', 'G5', 'A5', 'B5', 'C6']
        '''
        return MajorScale(self.pitchFromDegree(self.abstract.relativeMajorDegree))


# ------------------------------------------------------------------------------
# diatonic scales and modes
class MajorScale(DiatonicScale):
    '''
    A Major Scale

    >>> sc = scale.MajorScale(pitch.Pitch('d'))
    >>> sc.pitchFromDegree(7).name
    'C#'
    '''

    def __init__(self, tonic=None, **keywords):
        super().__init__(tonic=tonic, **keywords)
        self.type = 'major'
        # build the network for the appropriate scale
        self._abstract.buildNetwork(self.type)

        # N.B. do not subclass methods, since generally RomanNumerals use Keys
        # and Key is a subclass of DiatonicScale not MajorScale or MinorScale


class MinorScale(DiatonicScale):
    '''
    A natural minor scale, or the Aeolian mode.

    >>> sc = scale.MinorScale(pitch.Pitch('g'))
    >>> [str(p) for p in sc.pitches]
    ['G4', 'A4', 'B-4', 'C5', 'D5', 'E-5', 'F5', 'G5']
    '''

    def __init__(self, tonic=None, **keywords):
        super().__init__(tonic=tonic, **keywords)
        self.type = 'minor'
        self._abstract.buildNetwork(self.type)


class DorianScale(DiatonicScale):
    '''
    A scale built on the Dorian (D-D white-key) mode.

    >>> sc = scale.DorianScale(pitch.Pitch('d'))
    >>> [str(p) for p in sc.pitches]
    ['D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5', 'D5']
    '''

    def __init__(self, tonic=None, **keywords):
        super().__init__(tonic=tonic, **keywords)
        self.type = 'dorian'
        self._abstract.buildNetwork(self.type)


class PhrygianScale(DiatonicScale):
    '''
    A Phrygian scale (E-E white key)

    >>> sc = scale.PhrygianScale(pitch.Pitch('e'))
    >>> [str(p) for p in sc.pitches]
    ['E4', 'F4', 'G4', 'A4', 'B4', 'C5', 'D5', 'E5']
    '''

    def __init__(self, tonic=None, **keywords):
        super().__init__(tonic=tonic, **keywords)
        self.type = 'phrygian'
        self._abstract.buildNetwork(self.type)


class LydianScale(DiatonicScale):
    '''
    A Lydian scale (that is, the F-F white-key scale; does not have the
    probability of B- emerging as in a historical Lydian collection).

    >>> sc = scale.LydianScale(pitch.Pitch('f'))
    >>> [str(p) for p in sc.pitches]
    ['F4', 'G4', 'A4', 'B4', 'C5', 'D5', 'E5', 'F5']

    >>> sc = scale.LydianScale(pitch.Pitch('c'))
    >>> [str(p) for p in sc.pitches]
    ['C4', 'D4', 'E4', 'F#4', 'G4', 'A4', 'B4', 'C5']
    '''

    def __init__(self, tonic=None, **keywords):
        super().__init__(tonic=tonic, **keywords)
        self.type = 'lydian'
        self._abstract.buildNetwork(self.type)


class MixolydianScale(DiatonicScale):
    '''
    A mixolydian scale

    >>> sc = scale.MixolydianScale(pitch.Pitch('g'))
    >>> [str(p) for p in sc.pitches]
    ['G4', 'A4', 'B4', 'C5', 'D5', 'E5', 'F5', 'G5']

    >>> sc = scale.MixolydianScale(pitch.Pitch('c'))
    >>> [str(p) for p in sc.pitches]
    ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B-4', 'C5']
    '''

    def __init__(self, tonic=None, **keywords):
        super().__init__(tonic=tonic, **keywords)
        self.type = 'mixolydian'
        self._abstract.buildNetwork(self.type)


class HypodorianScale(DiatonicScale):
    '''
    A hypodorian scale: a dorian scale where the given pitch is scale degree 4.

    >>> sc = scale.HypodorianScale(pitch.Pitch('d'))
    >>> [str(p) for p in sc.pitches]
    ['A3', 'B3', 'C4', 'D4', 'E4', 'F4', 'G4', 'A4']
    >>> sc = scale.HypodorianScale(pitch.Pitch('c'))
    >>> [str(p) for p in sc.pitches]
    ['G3', 'A3', 'B-3', 'C4', 'D4', 'E-4', 'F4', 'G4']
    '''

    def __init__(self, tonic=None, **keywords):
        super().__init__(tonic=tonic, **keywords)
        self.type = 'hypodorian'
        self._abstract.buildNetwork(self.type)


class HypophrygianScale(DiatonicScale):
    '''
    A hypophrygian scale

    >>> sc = scale.HypophrygianScale(pitch.Pitch('e'))
    >>> sc.abstract.octaveDuplicating
    True
    >>> [str(p) for p in sc.pitches]
    ['B3', 'C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4']
    >>> sc.getTonic()
    <music21.pitch.Pitch E4>
    >>> sc.getDominant()
    <music21.pitch.Pitch A4>
    >>> sc.pitchFromDegree(1)  # scale degree 1 is treated as lowest
    <music21.pitch.Pitch B3>
    '''
    def __init__(self, tonic=None, **keywords):
        super().__init__(tonic=tonic, **keywords)
        self.type = 'hypophrygian'
        self._abstract.buildNetwork(self.type)


class HypolydianScale(DiatonicScale):
    '''
    A hypolydian scale

    >>> sc = scale.HypolydianScale(pitch.Pitch('f'))
    >>> [str(p) for p in sc.pitches]
    ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5']
    >>> sc = scale.HypolydianScale(pitch.Pitch('c'))
    >>> [str(p) for p in sc.pitches]
    ['G3', 'A3', 'B3', 'C4', 'D4', 'E4', 'F#4', 'G4']
    '''
    def __init__(self, tonic=None, **keywords):
        super().__init__(tonic=tonic, **keywords)
        self.type = 'hypolydian'
        self._abstract.buildNetwork(self.type)


class HypomixolydianScale(DiatonicScale):
    '''
    A hypomixolydian scale

    >>> sc = scale.HypomixolydianScale(pitch.Pitch('g'))
    >>> [str(p) for p in sc.pitches]
    ['D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5', 'D5']
    >>> sc = scale.HypomixolydianScale(pitch.Pitch('c'))
    >>> [str(p) for p in sc.pitches]
    ['G3', 'A3', 'B-3', 'C4', 'D4', 'E4', 'F4', 'G4']
    '''
    def __init__(self, tonic=None, **keywords):
        super().__init__(tonic=tonic, **keywords)
        self.type = 'hypomixolydian'
        self._abstract.buildNetwork(self.type)


class LocrianScale(DiatonicScale):
    '''
    A so-called "locrian" scale

    >>> sc = scale.LocrianScale(pitch.Pitch('b'))
    >>> [str(p) for p in sc.pitches]
    ['B4', 'C5', 'D5', 'E5', 'F5', 'G5', 'A5', 'B5']

    >>> sc = scale.LocrianScale(pitch.Pitch('c'))
    >>> [str(p) for p in sc.pitches]
    ['C4', 'D-4', 'E-4', 'F4', 'G-4', 'A-4', 'B-4', 'C5']
    '''

    def __init__(self, tonic=None, **keywords):
        super().__init__(tonic=tonic, **keywords)
        self.type = 'locrian'
        self._abstract.buildNetwork(self.type)


class HypolocrianScale(DiatonicScale):
    '''
    A hypolocrian scale

    >>> sc = scale.HypolocrianScale(pitch.Pitch('b'))
    >>> [str(p) for p in sc.pitches]
    ['F4', 'G4', 'A4', 'B4', 'C5', 'D5', 'E5', 'F5']

    >>> sc = scale.HypolocrianScale(pitch.Pitch('c'))
    >>> [str(p) for p in sc.pitches]
    ['G-3', 'A-3', 'B-3', 'C4', 'D-4', 'E-4', 'F4', 'G-4']
    '''

    def __init__(self, tonic=None, **keywords):
        super().__init__(tonic=tonic, **keywords)
        self.type = 'hypolocrian'
        self._abstract.buildNetwork(self.type)


class HypoaeolianScale(DiatonicScale):
    '''
    A hypoaeolian scale

    >>> sc = scale.HypoaeolianScale(pitch.Pitch('a'))
    >>> [str(p) for p in sc.pitches]
    ['E4', 'F4', 'G4', 'A4', 'B4', 'C5', 'D5', 'E5']

    >>> sc = scale.HypoaeolianScale(pitch.Pitch('c'))
    >>> [str(p) for p in sc.pitches]
    ['G3', 'A-3', 'B-3', 'C4', 'D4', 'E-4', 'F4', 'G4']
    '''
    def __init__(self, tonic=None, **keywords):
        super().__init__(tonic=tonic, **keywords)
        self.type = 'hypoaeolian'
        self._abstract.buildNetwork(self.type)


# ------------------------------------------------------------------------------
# other diatonic scales
class HarmonicMinorScale(DiatonicScale):
    '''
    The harmonic minor collection, realized as a scale.

    (The usage of this collection as a scale, is quite ahistorical for
    Western European classical music, but it is common in other parts of the
    world, but where the term "HarmonicMinor" would not be appropriate).

    >>> sc = scale.HarmonicMinorScale('e4')
    >>> [str(p) for p in sc.pitches]
    ['E4', 'F#4', 'G4', 'A4', 'B4', 'C5', 'D#5', 'E5']
    >>> sc.getTonic()
    <music21.pitch.Pitch E4>
    >>> sc.getDominant()
    <music21.pitch.Pitch B4>
    >>> sc.pitchFromDegree(1)  # scale degree 1 is treated as lowest
    <music21.pitch.Pitch E4>

    >>> sc = scale.HarmonicMinorScale()
    >>> sc
    <music21.scale.HarmonicMinorScale Abstract harmonic minor>
    >>> sc.deriveRanked(['C', 'E', 'G'], comparisonAttribute='name')
    [(3, <music21.scale.HarmonicMinorScale F harmonic minor>),
     (3, <music21.scale.HarmonicMinorScale E harmonic minor>),
     (2, <music21.scale.HarmonicMinorScale B harmonic minor>),
     (2, <music21.scale.HarmonicMinorScale A harmonic minor>)]

    Note that G and D are also equally good as B and A, but the system arbitrarily
    chooses among ties.
    '''

    def __init__(self, tonic=None, **keywords):
        super().__init__(tonic=tonic, **keywords)
        self.type = 'harmonic minor'

        # note: this changes the previously assigned AbstractDiatonicScale
        # from the DiatonicScale base class

        self._abstract = AbstractHarmonicMinorScale()
        # network building happens on object creation
        # self._abstract.buildNetwork()


class MelodicMinorScale(DiatonicScale):
    '''
    A melodic minor scale, which is not the same ascending or descending

    >>> sc = scale.MelodicMinorScale('e4')
    '''

    def __init__(self, tonic=None, **keywords):
        super().__init__(tonic=tonic, **keywords)
        self.type = 'melodic minor'

        # note: this changes the previously assigned AbstractDiatonicScale
        # from the DiatonicScale base class
        self._abstract = AbstractMelodicMinorScale()


# ------------------------------------------------------------------------------
# other scales

class OctatonicScale(ConcreteScale):
    '''
    A concrete Octatonic scale in one of two modes
    '''
    usePitchDegreeCache = True

    def __init__(self, tonic=None, mode=None, **keywords):
        super().__init__(tonic=tonic, **keywords)
        self._abstract = AbstractOctatonicScale(mode=mode)
        self.type = 'Octatonic'


class OctaveRepeatingScale(ConcreteScale):
    '''
    A concrete cyclical scale, based on a cycle of intervals.


    >>> sc = scale.OctaveRepeatingScale('c4', ['m3', 'M3'])
    >>> sc.pitches
    [<music21.pitch.Pitch C4>, <music21.pitch.Pitch E-4>,
     <music21.pitch.Pitch G4>, <music21.pitch.Pitch C5>]
    >>> [str(p) for p in sc.getPitches('g2', 'g6')]
    ['G2', 'C3', 'E-3', 'G3', 'C4', 'E-4', 'G4', 'C5', 'E-5', 'G5', 'C6', 'E-6', 'G6']
    >>> sc.getScaleDegreeFromPitch('c4')
    1
    >>> sc.getScaleDegreeFromPitch('e-')
    2

    No `intervalList` defaults to a single minor second:

    >>> sc2 = scale.OctaveRepeatingScale()
    >>> sc2.pitches
    [<music21.pitch.Pitch C4>, <music21.pitch.Pitch D-4>, <music21.pitch.Pitch C5>]
    '''

    def __init__(self, tonic=None, intervalList: list | None = None, **keywords):
        super().__init__(tonic=tonic, **keywords)
        mode = intervalList if intervalList else ['m2']
        self._abstract = AbstractOctaveRepeatingScale(mode=mode)
        self.type = 'Octave Repeating'


class CyclicalScale(ConcreteScale):
    '''
    A concrete cyclical scale, based on a cycle of intervals.

    >>> sc = scale.CyclicalScale('c4', ['P5'])  # can give one list
    >>> sc.pitches
    [<music21.pitch.Pitch C4>, <music21.pitch.Pitch G4>]
    >>> [str(p) for p in sc.getPitches('g2', 'g6')]
    ['B-2', 'F3', 'C4', 'G4', 'D5', 'A5', 'E6']
    >>> sc.getScaleDegreeFromPitch('g4')  # as single interval cycle, all are 1
    1
    >>> sc.getScaleDegreeFromPitch('b-2', direction=scale.Direction.BI)
    1

    No `intervalList` defaults to a single minor second:

    >>> sc2 = scale.CyclicalScale()
    >>> sc2.pitches
    [<music21.pitch.Pitch C4>, <music21.pitch.Pitch D-4>]
    '''

    def __init__(self,
                 tonic: str | pitch.Pitch | note.Note | None = None,
                 intervalList: list | None = None,
                 **keywords):
        super().__init__(tonic=tonic, **keywords)
        mode = intervalList if intervalList else ['m2']
        self._abstract = AbstractCyclicalScale(mode=mode)
        self.type = 'Cyclical'


class ChromaticScale(ConcreteScale):
    '''
    A concrete cyclical scale, based on a cycle of half steps.


    >>> sc = scale.ChromaticScale('g2')
    >>> [str(p) for p in sc.pitches]
    ['G2', 'A-2', 'A2', 'B-2', 'B2', 'C3', 'C#3', 'D3', 'E-3', 'E3', 'F3', 'F#3', 'G3']
    >>> [str(p) for p in sc.getPitches('g2', 'g6')]
    ['G2', 'A-2', ..., 'F#3', 'G3', 'A-3', ..., 'F#4', 'G4', 'A-4', ..., 'G5', ..., 'F#6', 'G6']
    >>> sc.abstract.getDegreeMaxUnique()
    12
    >>> sc.pitchFromDegree(1)
    <music21.pitch.Pitch G2>
    >>> sc.pitchFromDegree(2)
    <music21.pitch.Pitch A-2>
    >>> sc.pitchFromDegree(3)
    <music21.pitch.Pitch A2>
    >>> sc.pitchFromDegree(8)
    <music21.pitch.Pitch D3>
    >>> sc.pitchFromDegree(12)
    <music21.pitch.Pitch F#3>
    >>> sc.getScaleDegreeFromPitch('g2', comparisonAttribute='pitchClass')
    1
    >>> sc.getScaleDegreeFromPitch('F#6', comparisonAttribute='pitchClass')
    12
    '''
    usePitchDegreeCache = True

    def __init__(self, tonic=None, **keywords):
        super().__init__(tonic=tonic, **keywords)
        self._abstract = AbstractCyclicalScale(mode=[
            'm2', 'm2', 'm2',
            'm2', 'm2', 'm2', 'm2', 'm2', 'm2', 'm2', 'm2', 'm2'])
        self._abstract._net.pitchSimplification = 'mostCommon'
        self.type = 'Chromatic'


class WholeToneScale(ConcreteScale):
    '''
    A concrete whole-tone scale.

    >>> sc = scale.WholeToneScale('g2')
    >>> [str(p) for p in sc.pitches]
    ['G2', 'A2', 'B2', 'C#3', 'D#3', 'E#3', 'G3']
    >>> [str(p) for p in sc.getPitches('g2', 'g5')]
    ['G2', 'A2', 'B2', 'C#3', 'D#3', 'E#3', 'G3', 'A3', 'B3', 'C#4',
     'D#4', 'E#4', 'G4', 'A4', 'B4', 'C#5', 'D#5', 'E#5', 'G5']
    >>> sc.abstract.getDegreeMaxUnique()
    6
    >>> sc.pitchFromDegree(1)
    <music21.pitch.Pitch G2>
    >>> sc.pitchFromDegree(2)
    <music21.pitch.Pitch A2>
    >>> sc.pitchFromDegree(6)
    <music21.pitch.Pitch E#3>
    >>> sc.getScaleDegreeFromPitch('g2', comparisonAttribute='pitchClass')
    1
    >>> sc.getScaleDegreeFromPitch('F6', comparisonAttribute='pitchClass')
    6
    '''
    usePitchDegreeCache = True

    def __init__(self, tonic=None, **keywords):
        super().__init__(tonic=tonic, **keywords)
        self._abstract = AbstractCyclicalScale(mode=['M2', 'M2', 'M2', 'M2', 'M2', 'M2'])
        self.type = 'Whole tone'


class SieveScale(ConcreteScale):
    '''
    A scale created from a Xenakis sieve logical string, based on the
    :class:`~music21.sieve.Sieve` object definition. The complete period of the
    sieve is realized as intervals and used to create a scale.


    >>> sc = scale.SieveScale('c4', '3@0')
    >>> sc.pitches
    [<music21.pitch.Pitch C4>, <music21.pitch.Pitch E-4>]
    >>> sc = scale.SieveScale('d4', '3@0')
    >>> sc.pitches
    [<music21.pitch.Pitch D4>, <music21.pitch.Pitch F4>]
    >>> sc = scale.SieveScale('c2', '(-3@2 & 4) | (-3@1 & 4@1) | (3@2 & 4@2) | (-3 & 4@3)')
    >>> [str(p) for p in sc.pitches]
    ['C2', 'D2', 'E2', 'F2', 'G2', 'A2', 'B2', 'C3']


    OMIT_FROM_DOCS

    Test that an empty SieveScale can be created...

    >>> sc = scale.SieveScale()
    '''

    def __init__(self,
                 tonic=None,
                 sieveString='2@0',
                 eld: int | float = 1,
                 **keywords):
        super().__init__(tonic=tonic, **keywords)

        # self.tonic is a Pitch
        if self.tonic is not None:
            tonic = self.tonic
        else:
            tonic = pitch.Pitch('C4')
        self._pitchSieve = sieve.PitchSieve(sieveString,
                                            pitchLower=str(tonic),
                                            pitchUpper=str(tonic.transpose(48)), eld=eld)
        # four octave default

        # environLocal.printDebug([self._pitchSieve.sieveObject.represent(),
        #      self._pitchSieve.getIntervalSequence()])
        # mode here is a list of intervals
        intervalSequence = self._pitchSieve.getIntervalSequence()
        self._abstract = AbstractCyclicalScale(mode=intervalSequence)
        self.type = 'Sieve'


class ScalaScale(ConcreteScale):
    '''
    A scale created from a Scala scale .scl file. Any file
    in the Scala archive can be given by name. Additionally, a file
    path to a Scala .scl file, or a raw string representation, can be used.

    >>> sc = scale.ScalaScale('g4', 'mbira banda')
    >>> [str(p) for p in sc.pitches]
    ['G4', 'A4(-15c)', 'B4(-11c)', 'C#5(-7c)', 'D~5(+6c)', 'E5(+14c)', 'F~5(+1c)', 'G#5(+2c)']

    If only a single string is given, and it's too long to be a tonic,
    or it ends in .scl, assume it's the name of a scala scale and
    set the tonic to C4

    >>> sc = scale.ScalaScale('pelog_9')
    >>> [str(p) for p in sc.pitches]
    ['C4', 'C#~4(-17c)', 'D~4(+17c)', 'F~4(-17c)',
     'F#~4(+17c)', 'G#4(-0c)', 'A~4(-17c)', 'C5(-0c)']

    If no scale with that name can be found then it raises an exception:

    >>> sc = scale.ScalaScale('badFileName.scl')
    Traceback (most recent call last):
    music21.scale.ScaleException: Could not find a file named badFileName.scl in the scala database
    '''

    def __init__(self, tonic=None, scalaString=None, **keywords):
        if (tonic is not None
            and scalaString is None
            and isinstance(tonic, str)
            and (len(tonic) >= 4
                 or tonic.endswith('scl'))):
            # just a scale was wanted
            scalaString = tonic
            tonic = 'C4'

        super().__init__(tonic=tonic, **keywords)

        self._scalaData = None
        self.description = None

        # this might be a raw scala file list
        if scalaString is not None and scalaString.count('\n') > 3:
            # if no match, this might be a complete Scala string
            self._scalaData = scala.ScalaData(scalaString)
            self._scalaData.parse()
        elif scalaString is not None:
            # try to load a named scale from a file path or stored
            # on the scala archive
            # returns None or a scala storage object
            readFile = scala.parse(scalaString)
            if readFile is None:
                raise ScaleException(
                    f'Could not find a file named {scalaString} in the scala database')
            self._scalaData = readFile
        else:  # grab a default
            self._scalaData = scala.parse('fj-12tet.scl')

        intervalSequence = self._scalaData.getIntervalSequence()
        self._abstract = AbstractCyclicalScale(mode=intervalSequence)
        self._abstract._net.pitchSimplification = 'mostCommon'
        self.type = f'Scala: {self._scalaData.fileName}'
        self.description = self._scalaData.description


class RagAsawari(ConcreteScale):
    '''
    A concrete pseudo-raga scale.

    >>> sc = scale.RagAsawari('c2')
    >>> [str(p) for p in sc.pitches]
    ['C2', 'D2', 'F2', 'G2', 'A-2', 'C3']
    >>> [str(p) for p in sc.getPitches(direction=scale.Direction.DESCENDING)]
    ['C3', 'B-2', 'A-2', 'G2', 'F2', 'E-2', 'D2', 'C2']
    '''

    def __init__(self, tonic=None, **keywords):
        super().__init__(tonic=tonic, **keywords)
        self._abstract = AbstractRagAsawari()
        self.type = 'Rag Asawari'


class RagMarwa(ConcreteScale):
    '''
    A concrete pseudo-raga scale.

    >>> sc = scale.RagMarwa('c2')

    this gets a pitch beyond the terminus b/c of descending form max

    >>> [str(p) for p in sc.pitches]
    ['C2', 'D-2', 'E2', 'F#2', 'A2', 'B2', 'A2', 'C3', 'D-3']
    '''

    def __init__(self, tonic=None, **keywords):
        super().__init__(tonic=tonic, **keywords)
        self._abstract = AbstractRagMarwa()
        self.type = 'Rag Marwa'
        # >>> sc.getPitches(direction=Direction.DESCENDING)
        # [C2, D2, E2, G2, A2, C3]


class WeightedHexatonicBlues(ConcreteScale):
    '''
    A concrete scale based on a dynamic mixture of a minor pentatonic
    and the hexatonic blues scale.
    '''

    def __init__(self, tonic=None, **keywords):
        super().__init__(tonic=tonic, **keywords)
        self._abstract = AbstractWeightedHexatonicBlues()
        self.type = 'Weighted Hexatonic Blues'


# TODO: decide whether to store implicit tonic.
#     if not set, then comparisons fall to abstract

# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [ConcreteScale, AbstractScale]


if __name__ == '__main__':
    import music21
    music21.mainTest()
