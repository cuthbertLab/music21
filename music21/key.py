# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         key.py
# Purpose:      Classes for keys
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009, 2010, 2012 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
This module defines objects for representing key signatures as well as key
areas. The :class:`~music21.key.KeySignature` is used in
:class:`~music21.stream.Measure` objects for defining notated key signatures.

The :class:`~music21.key.Key` object is a fuller representation not just of
a key signature but also of the key of a region.
'''
import copy
import re
import unittest
from typing import Union, Optional

from music21 import base
from music21 import exceptions21
from music21 import interval
from music21 import note
from music21 import pitch
from music21 import scale
from music21 import style

from music21.common.decorators import cacheMethod
from music21 import environment
_MOD = 'key'
environLocal = environment.Environment(_MOD)


# ------------------------------------------------------------------------------
# store a cache of already-found values
_sharpsToPitchCache = {}


def convertKeyStringToMusic21KeyString(textString):
    '''
    Utility function to change strings in the form of "Eb" to
    "E-" (for E-flat major) and leaves alone proper music21 strings
    (like "E-" or "f#").  A little bit complex because of parsing
    bb as B-flat minor and Bb as B-flat major.

    >>> key.convertKeyStringToMusic21KeyString('Eb')
    'E-'
    >>> key.convertKeyStringToMusic21KeyString('f#')
    'f#'
    >>> key.convertKeyStringToMusic21KeyString('bb')
    'b-'
    >>> key.convertKeyStringToMusic21KeyString('Bb')
    'B-'
    >>> key.convertKeyStringToMusic21KeyString('b#')
    'b#'
    >>> key.convertKeyStringToMusic21KeyString('c')
    'c'
    '''
    if textString == 'bb':
        textString = 'b-'
    elif textString == 'Bb':
        textString = 'B-'
    elif textString.endswith('b') and not textString.startswith('b'):
        textString = textString.rstrip('b') + '-'
    return textString


def sharpsToPitch(sharpCount):
    '''
    Given a number a positive/negative number of sharps, return a Pitch
    object set to the appropriate major key value.

    >>> key.sharpsToPitch(1)
    <music21.pitch.Pitch G>
    >>> key.sharpsToPitch(2)
    <music21.pitch.Pitch D>
    >>> key.sharpsToPitch(-2)
    <music21.pitch.Pitch B->
    >>> key.sharpsToPitch(-6)
    <music21.pitch.Pitch G->

    Note that these are :class:`music21.pitch.Pitch` objects not just names:

    >>> k1 = key.sharpsToPitch(6)
    >>> k1
    <music21.pitch.Pitch F#>
    >>> k1.step
    'F'
    >>> k1.accidental
    <accidental sharp>

    OMIT_FROM_DOCS

    The second time we do something it should be in the cache, so let's make sure it still works:

    >>> key.sharpsToPitch(1)
    <music21.pitch.Pitch G>
    >>> key.sharpsToPitch(1)
    <music21.pitch.Pitch G>
    >>> 1 in key._sharpsToPitchCache
    True
    >>> key._sharpsToPitchCache[1]
    <music21.pitch.Pitch G>
    '''
    if sharpCount is None:
        sharpCount = 0  # fix for C major

    if sharpCount in _sharpsToPitchCache:
        # return a deepcopy of the pitch
        return copy.deepcopy(_sharpsToPitchCache[sharpCount])

    pitchInit = pitch.Pitch('C')
    pitchInit.octave = None
    # keyPc = (self.sharps * 7) % 12
    if sharpCount > 0:
        intervalStr = 'P5'
    elif sharpCount < 0:
        intervalStr = 'P-5'
    else:
        return pitchInit  # C

    intervalObj = interval.Interval(intervalStr)
    for i in range(abs(sharpCount)):
        pitchInit = intervalObj.transposePitch(pitchInit)
    pitchInit.octave = None

    _sharpsToPitchCache[sharpCount] = pitchInit
    return pitchInit


# store a cache of already-found values
# _pitchToSharpsCache = {}

fifthsOrder = ['F', 'C', 'G', 'D', 'A', 'E', 'B']
modeSharpsAlter = {'major': 0,
                   'ionian': 0,
                   'minor': -3,
                   'aeolian': -3,
                   'dorian': -2,
                   'phrygian': -4,
                   'lydian': 1,
                   'mixolydian': -1,
                   'locrian': -5,
                   }


def pitchToSharps(value, mode=None):
    '''
    Given a pitch or :class:`music21.pitch.Pitch` object,
    return the number of sharps found in that mode.

    The `mode` parameter can be 'major', 'minor', or most
    of the common church/jazz modes ('dorian', 'mixolydian', etc.)
    including Locrian.

    If `mode` is omitted or not found, the default mode is major.

    (extra points to anyone who can find the earliest reference to
    the Locrian mode in print.  David Cohen and I (MSC) have been
    looking for this for years).

    >>> key.pitchToSharps('c')
    0
    >>> key.pitchToSharps('c', 'minor')
    -3
    >>> key.pitchToSharps('a', 'minor')
    0
    >>> key.pitchToSharps('d')
    2
    >>> key.pitchToSharps('e-')
    -3
    >>> key.pitchToSharps('a')
    3
    >>> key.pitchToSharps('e', 'minor')
    1
    >>> key.pitchToSharps('f#', 'major')
    6
    >>> key.pitchToSharps('g-', 'major')
    -6
    >>> key.pitchToSharps('c#')
    7
    >>> key.pitchToSharps('g#')
    8
    >>> key.pitchToSharps('e', 'dorian')
    2
    >>> key.pitchToSharps('d', 'dorian')
    0
    >>> key.pitchToSharps('g', 'mixolydian')
    0
    >>> key.pitchToSharps('e-', 'lydian')
    -2
    >>> key.pitchToSharps('e-', 'lydian')
    -2
    >>> key.pitchToSharps('a', 'phrygian')
    -1
    >>> key.pitchToSharps('e', 'phrygian')
    0
    >>> key.pitchToSharps('f#')
    6
    >>> key.pitchToSharps('f-')
    -8
    >>> key.pitchToSharps('f--')
    -15
    >>> key.pitchToSharps('f--', 'locrian')
    -20
    >>> key.pitchToSharps('a', 'ionian')
    3
    >>> key.pitchToSharps('a', 'aeolian')
    0


    But quarter tones don't work:

    >>> key.pitchToSharps('C~')
    Traceback (most recent call last):
    music21.key.KeyException: Cannot determine sharps for quarter-tone keys! silly!
    '''
    if isinstance(value, str):
        value = pitch.Pitch(value)
    elif 'Pitch' in value.classes:
        pass
    elif 'Note' in value.classes:
        value = value.pitch
    else:
        raise KeyException('Cannot get a sharp number from value')

    # the -1 is because we begin with F not C.
    sharps = fifthsOrder.index(value.step) - 1
    if value.accidental is not None:
        if value.accidental.isTwelveTone() is False:
            raise KeyException('Cannot determine sharps for quarter-tone keys! silly!')
        vaa = int(value.accidental.alter)
        sharps = sharps + 7 * vaa

    if mode is not None and mode in modeSharpsAlter:
        sharps += modeSharpsAlter[mode]

    return sharps


class KeySignatureException(exceptions21.Music21Exception):
    pass


class KeyException(exceptions21.Music21Exception):
    pass


# ------------------------------------------------------------------------------
class KeySignature(base.Music21Object):
    '''
    A KeySignature object specifies the signature to be used for a piece; it takes
    in zero or one arguments.  The only argument is an int giving the number of sharps,
    or if negative the number of flats.

    If you are starting with the name of a key, see the :class:`~music21.key.Key` object.

    >>> A = key.KeySignature(3)
    >>> A
    <music21.key.KeySignature of 3 sharps>

    >>> Eflat = key.KeySignature(-3)
    >>> Eflat
    <music21.key.KeySignature of 3 flats>

    If you want to get a real Key, then use the :class:`~music21.key.Key` object instead:

    >>> illegal = key.KeySignature('c#')
    Traceback (most recent call last):
    music21.key.KeySignatureException: Cannot get a KeySignature from this
        "number" of sharps: 'c#'; did you mean to use a key.Key() object instead?

    >>> legal = key.Key('c#')
    >>> legal.sharps
    4
    >>> legal
    <music21.key.Key of c# minor>

    To set a non-traditional Key Signature, create a KeySignature object and then
    set the alteredPitches list:

    >>> unusual = key.KeySignature()
    >>> unusual.alteredPitches = ['E-', 'G#']
    >>> unusual
    <music21.key.KeySignature of pitches: [E-, G#]>
    >>> unusual.isNonTraditional
    True

    To set a pitch as displayed in a particular octave, create a non-traditional
    KeySignature and then set pitches with octaves:

    >>> unusual = key.KeySignature()
    >>> unusual.alteredPitches = ['F#4']
    >>> unusual
    <music21.key.KeySignature of pitches: [F#4]>

    If the accidental applies to all octaves but is being displayed differently
    then you are done, but if you want them to apply only to the octave displayed
    in then set `.accidentalsApplyOnlyToOctave` to `True`:

    >>> unusual.accidentalsApplyOnlyToOctave
    False
    >>> unusual.accidentalsApplyOnlyToOctave = True
    '''
    _styleClass = style.TextStyle

    # note that musicxml permits non-traditional keys by specifying
    # one or more altered tones; these are given as pairs of
    # step names and semitone alterations

    classSortOrder = 2

    def __init__(self, sharps=None):
        super().__init__()
        # position on the circle of fifths, where 1 is one sharp, -1 is one flat

        try:
            if sharps is not None and (sharps != int(sharps)):
                raise KeySignatureException(
                    f'Cannot get a KeySignature from this "number" of sharps: {sharps!r}; '
                    + 'did you mean to use a key.Key() object instead?')
        except ValueError as ve:
            raise KeySignatureException(
                f'Cannot get a KeySignature from this "number" of sharps: {sharps!r}; '
                + 'did you mean to use a key.Key() object instead?'
            ) from ve

        self._sharps = sharps
        # need to store a list of pitch objects, used for creating a
        # non traditional key
        self._alteredPitches = None

        # cache altered pitches
        self._alteredPitchesCached = []
        self.accidentalsApplyOnlyToOctave = False

    def __hash__(self):
        hashTuple = (self._sharps, tuple(self._alteredPitches), self.accidentalsApplyOnlyToOctave)
        return hash(hashTuple)

    # --------------------------------------------------------------------------

    def _strDescription(self):
        output = ''
        ns = self.sharps
        if ns is None:
            output = 'pitches: [' + ', '.join([str(p) for p in self.alteredPitches]) + ']'
        elif ns > 1:
            output = f'{ns} sharps'
        elif ns == 1:
            output = '1 sharp'
        elif ns == 0:
            output = 'no sharps or flats'
        elif ns == -1:
            output = '1 flat'
        else:
            output = f'{abs(ns)} flats'
        return output

    def __eq__(self, other):
        '''
        two KeySignatures are equal if their sharps are equal.
        '''
        try:
            if self.sharps == other.sharps:
                return True
            else:
                return False
        except AttributeError:
            return False

    def _reprInternal(self):
        return 'of ' + self._strDescription()

    def asKey(self, mode='major'):
        '''
        return a `key.Key` object representing this KeySignature object as a key in the
        given mode (default = major)
        '''
        mode = mode.lower()
        if mode not in modeSharpsAlter:
            raise KeyException(f'Mode {mode} is unknown')
        sharpAlterationFromMajor = modeSharpsAlter[mode]
        pitchObj = sharpsToPitch(self.sharps - sharpAlterationFromMajor)
        return Key(pitchObj.name, mode)

    @property
    @cacheMethod
    def alteredPitches(self):
        # noinspection PyShadowingNames
        '''
        Return or set a list of music21.pitch.Pitch objects that are altered by this
        KeySignature. That is, all Pitch objects that will receive an accidental.

        >>> a = key.KeySignature(3)
        >>> a.alteredPitches
        [<music21.pitch.Pitch F#>, <music21.pitch.Pitch C#>, <music21.pitch.Pitch G#>]
        >>> b = key.KeySignature(1)
        >>> b.alteredPitches
        [<music21.pitch.Pitch F#>]

        >>> c = key.KeySignature(9)
        >>> [str(p) for p in c.alteredPitches]
        ['F#', 'C#', 'G#', 'D#', 'A#', 'E#', 'B#', 'F##', 'C##']

        >>> d = key.KeySignature(-3)
        >>> d.alteredPitches
        [<music21.pitch.Pitch B->, <music21.pitch.Pitch E->, <music21.pitch.Pitch A->]

        >>> e = key.KeySignature(-1)
        >>> e.alteredPitches
        [<music21.pitch.Pitch B->]

        >>> f = key.KeySignature(-6)
        >>> [str(p) for p in f.alteredPitches]
        ['B-', 'E-', 'A-', 'D-', 'G-', 'C-']

        >>> g = key.KeySignature(-8)
        >>> [str(p) for p in g.alteredPitches]
        ['B-', 'E-', 'A-', 'D-', 'G-', 'C-', 'F-', 'B--']


        Non-standard, non-traditional key signatures can set their own
        altered pitches cache.

        >>> nonTrad = key.KeySignature()
        >>> nonTrad.alteredPitches = ['B-', 'F#', 'E-', 'G#']
        >>> nonTrad.alteredPitches
        [<music21.pitch.Pitch B->,
         <music21.pitch.Pitch F#>,
         <music21.pitch.Pitch E->,
         <music21.pitch.Pitch G#>]
        '''
        if self._alteredPitches is not None:
            return self._alteredPitches

        post = []
        if self.sharps > 0:
            pKeep = pitch.Pitch('B')
            if self.sharps > 8:
                pass
            for i in range(self.sharps):
                pKeep.transpose('P5', inPlace=True)
                p = copy.deepcopy(pKeep)
                p.octave = None
                post.append(p)

        elif self.sharps < 0:
            pKeep = pitch.Pitch('F')
            for i in range(abs(self.sharps)):
                pKeep.transpose('P4', inPlace=True)
                p = copy.deepcopy(pKeep)
                p.octave = None
                post.append(p)

        return post

    @alteredPitches.setter
    def alteredPitches(self, newAlteredPitches):
        self.clearCache()
        newList = []
        for p in newAlteredPitches:
            if not hasattr(p, 'classes'):
                newList.append(pitch.Pitch(p))
            elif 'Pitch' in p.classes:
                newList.append(p)
            elif 'Note' in p.classes:
                newList.append(copy.deepcopy(p.pitch))
        self._alteredPitches = newList

    @property
    def isNonTraditional(self):
        '''
        Returns bool if this is a non-traditional KeySignature:

        >>> g = key.KeySignature(3)
        >>> g.isNonTraditional
        False

        >>> g = key.KeySignature()
        >>> g.alteredPitches = [pitch.Pitch('E`')]
        >>> g.isNonTraditional
        True

        >>> g
        <music21.key.KeySignature of pitches: [E`]>

        >>> g.accidentalByStep('E')
        <accidental half-flat>
        '''
        if self.sharps is None and self.alteredPitches:
            return True
        else:
            return False

    def accidentalByStep(self, step):
        '''
        Given a step (C, D, E, F, etc.) return the accidental
        for that note in this key (using the natural minor for minor)
        or None if there is none.

        >>> g = key.KeySignature(1)
        >>> g.accidentalByStep('F')
        <accidental sharp>
        >>> g.accidentalByStep('G')

        >>> f = key.KeySignature(-1)
        >>> bbNote = note.Note('B-5')
        >>> f.accidentalByStep(bbNote.step)
        <accidental flat>

        Fix a wrong note in F-major:

        >>> wrongBNote = note.Note('B#4')
        >>> if f.accidentalByStep(wrongBNote.step) != wrongBNote.pitch.accidental:
        ...    wrongBNote.pitch.accidental = f.accidentalByStep(wrongBNote.step)
        >>> wrongBNote
        <music21.note.Note B->

        Set all notes to the correct notes for a key using the
        note's Key Context.  Before:

        >>> s1 = stream.Stream()
        >>> s1.append(key.KeySignature(4))  # E-major or C-sharp-minor
        >>> s1.append(note.Note('C', type='half'))
        >>> s1.append(note.Note('E-', type='half'))
        >>> s1.append(key.KeySignature(-4))  # A-flat-major or F-minor
        >>> s1.append(note.Note('A', type='whole'))
        >>> s1.append(note.Note('F#', type='whole'))
        >>> #_DOCS_SHOW s1.show()

        .. image:: images/keyAccidentalByStep_Before.*
            :width: 400

        After:

        >>> for n in s1.notes:
        ...    n.pitch.accidental = n.getContextByClass(key.KeySignature).accidentalByStep(n.step)
        >>> #_DOCS_SHOW s1.show()

        .. image:: images/keyAccidentalByStep.*
            :width: 400

        OMIT_FROM_DOCS
        >>> s1.show('text')
        {0.0} <music21.key.KeySignature of 4 sharps>
        {0.0} <music21.note.Note C#>
        {2.0} <music21.note.Note E>
        {4.0} <music21.key.KeySignature of 4 flats>
        {4.0} <music21.note.Note A->
        {8.0} <music21.note.Note F>

        Test to make sure there are not linked accidentals (fixed bug 22 Nov. 2010)

        >>> nB1 = note.Note('B', type='whole')
        >>> nB2 = note.Note('B', type='whole')
        >>> s1.append(nB1)
        >>> s1.append(nB2)
        >>> for n in s1.notes:
        ...    n.pitch.accidental = n.getContextByClass(key.KeySignature).accidentalByStep(n.step)
        >>> (nB1.pitch.accidental, nB2.pitch.accidental)
        (<accidental flat>, <accidental flat>)
        >>> nB1.pitch.accidental.name = 'sharp'
        >>> (nB1.pitch.accidental, nB2.pitch.accidental)
        (<accidental sharp>, <accidental flat>)
        '''
        # temp measure to fix dbl flats, etc.
        for thisAlteration in reversed(self.alteredPitches):
            if thisAlteration.step.lower() == step.lower():
                return copy.deepcopy(thisAlteration.accidental)
            # get a new one each time otherwise we have linked accidentals, YUK!

        return None

    # --------------------------------------------------------------------------
    # methods

    def transpose(self, value, *, inPlace=False):
        '''
        Transpose the KeySignature by the user-provided value.
        If the value is an integer, the transposition is treated
        in half steps. If the value is a string, any Interval string
        specification can be provided. Alternatively, a
        :class:`music21.interval.Interval` object can be supplied.

        >>> a = key.KeySignature(2)
        >>> a
        <music21.key.KeySignature of 2 sharps>
        >>> a.asKey('major')
        <music21.key.Key of D major>

        >>> b = a.transpose('p5')
        >>> b
        <music21.key.KeySignature of 3 sharps>
        >>> b.asKey('major')
        <music21.key.Key of A major>
        >>> b.sharps
        3

        >>> c = b.transpose('-m2')
        >>> c.asKey('major')
        <music21.key.Key of G# major>
        >>> c.sharps
        8

        >>> d = c.transpose('-a3')
        >>> d.asKey('major')
        <music21.key.Key of E- major>
        >>> d.sharps
        -3

        Transposition by semitone (or other chromatic interval)

        >>> c = key.KeySignature(0)
        >>> dFlat = c.transpose(1)
        >>> dFlat
        <music21.key.KeySignature of 5 flats>
        >>> d = dFlat.transpose(1)
        >>> d
        <music21.key.KeySignature of 2 sharps>
        >>> eFlat = d.transpose(1)
        >>> eFlat
        <music21.key.KeySignature of 3 flats>
        '''
        if hasattr(value, 'diatonic'):  # its an Interval class
            intervalObj = value
        elif hasattr(value, 'classes') and 'GenericInterval' in value.classes:
            intervalObj = value
        else:  # try to process
            intervalObj = interval.Interval(value)

        if not inPlace:
            post = copy.deepcopy(self)
        else:
            post = self

        k1 = post.asKey('major')
        p1 = k1.tonic
        p2 = intervalObj.transposePitch(p1)
        if isinstance(value, int) and abs(pitchToSharps(p2)) > 6:
            p2 = p2.getEnharmonic()

        post.sharps = pitchToSharps(p2)
        post.clearCache()

        # mode is already set
        if not inPlace:
            return post
        else:
            return None

    def transposePitchFromC(self, p: pitch.Pitch, *, inPlace=False) -> Optional[pitch.Pitch]:
        '''
        Takes a pitch in C major and transposes it so that it has
        the same step position in the current key signature.

        Example: B is the leading tone in C major, so given
        a key signature of 3 flats, get the leading tone in E-flat major:

        >>> ks = key.KeySignature(-3)
        >>> p1 = pitch.Pitch('B')
        >>> p2 = ks.transposePitchFromC(p1)
        >>> p2.name
        'D'

        Original pitch is unchanged:

        >>> p1.name
        'B'

        >>> ks2 = key.KeySignature(2)
        >>> p2 = ks2.transposePitchFromC(p1)
        >>> p2.name
        'C#'

        For out of scale pitches the relationship still works; note also that
        original octave is preserved.

        >>> p3 = pitch.Pitch('G-4')
        >>> p4 = ks.transposePitchFromC(p3)
        >>> p4.nameWithOctave
        'B--4'

        If inPlace is True then nothing is returned and the original pitch is
        modified.

        >>> p5 = pitch.Pitch('C5')
        >>> ks.transposePitchFromC(p5, inPlace=True)
        >>> p5.nameWithOctave
        'E-5'

        New method in v6.
        '''
        transInterval = None
        transTimes = 0

        originalOctave = p.octave
        if not inPlace:
            p = copy.deepcopy(p)

        if self.sharps == 0:
            if inPlace:
                return
            else:
                return p
        elif self.sharps < 0:
            transTimes = abs(self.sharps)
            transInterval = interval.Interval('P4')
        else:
            transTimes = self.sharps
            transInterval = interval.Interval('P5')

        for i in range(transTimes):
            transInterval.transposePitch(p, inPlace=True)

        if originalOctave is not None:
            p.octave = originalOctave

        if not inPlace:
            return p

    def getScale(self, mode='major'):
        '''
        Return a :class:`music21.scale.Scale` object (or, actually, a subclass such as
        :class:`~music21.scale.MajorScale` or :class:`~music21.scale.MinorScale`) that is
        representative of this key signature and mode.

        Raises KeySignatureException if mode is not in [None, 'major', 'minor'].

        >>> ks = key.KeySignature(3)
        >>> ks
        <music21.key.KeySignature of 3 sharps>
        >>> ks.getScale('major')
        <music21.scale.MajorScale A major>
        >>> ks.getScale('minor')
        <music21.scale.MinorScale F# minor>
        '''
        pitchObj = self.asKey(mode).tonic
        if mode in (None, 'major'):
            return scale.MajorScale(pitchObj)
        elif mode == 'minor':
            return scale.MinorScale(pitchObj)
        else:
            raise KeySignatureException(f'No mapping to a scale exists for this mode yet: {mode}')

    # --------------------------------------------------------------------------
    # properties

    def _getSharps(self):
        return self._sharps

    def _setSharps(self, value):
        if value != self._sharps:
            self._sharps = value
            self.clearCache()

    sharps = property(_getSharps, _setSharps,
                      doc='''
        Get or set the number of sharps.  If the number is negative
        then it sets the number of flats.  Equivalent to musicxml's 'fifths'
        attribute.

        >>> ks1 = key.KeySignature(2)
        >>> ks1.sharps
        2
        >>> ks1.sharps = -4
        >>> ks1
        <music21.key.KeySignature of 4 flats>
        ''')


class Key(KeySignature, scale.DiatonicScale):
    '''
    Note that a key is a sort of hypothetical/conceptual object.
    It probably has a scale (or scales) associated with it and a :class:`~music21.key.KeySignature`,
    but not necessarily.

    A Key object has all the attributes of a KeySignature and all the attributes of a
    :class:`~music21.scale.DiatonicScale`.

    >>> cm = key.Key('c')  # lowercase = c minor.
    >>> cm
    <music21.key.Key of c minor>
    >>> cm.mode
    'minor'
    >>> cm.tonic
    <music21.pitch.Pitch C>

    >>> cm.sharps
    -3
    >>> cm.pitchFromDegree(3)
    <music21.pitch.Pitch E-4>
    >>> cm.pitchFromDegree(7)
    <music21.pitch.Pitch B-4>

    >>> cSharpMaj = key.Key('C#')  # uppercase = C# major
    >>> cSharpMaj
    <music21.key.Key of C# major>
    >>> cSharpMaj.sharps
    7

    >>> fFlatMaj = key.Key('F-')
    >>> fFlatMaj
    <music21.key.Key of F- major>
    >>> fFlatMaj.sharps
    -8
    >>> fFlatMaj.accidentalByStep('B')
    <accidental double-flat>


    >>> eDor = key.Key('E', 'dorian')
    >>> eDor
    <music21.key.Key of E dorian>
    >>> eDor.sharps
    2
    >>> eDor.pitches
    [<music21.pitch.Pitch E4>,
     <music21.pitch.Pitch F#4>,
     <music21.pitch.Pitch G4>,
     <music21.pitch.Pitch A4>,
     <music21.pitch.Pitch B4>,
     <music21.pitch.Pitch C#5>,
     <music21.pitch.Pitch D5>,
     <music21.pitch.Pitch E5>]

    '''
    _sharps = 0
    _mode = None

    def __init__(self,
                 tonic: Union[str, pitch.Pitch, note.Note] = 'C',
                 mode=None):
        if hasattr(tonic, 'classes') and ('Music21Object' in tonic.classes
                                          or 'Pitch' in tonic.classes):
            if hasattr(tonic, 'name'):
                tonic = tonic.name
            elif hasattr(tonic, 'pitches') and tonic.pitches:  # chord w/ >= 1 pitch
                if mode is None:
                    if tonic.isMinorTriad() is True:
                        mode = 'minor'
                    else:
                        mode = 'major'
                tonic = tonic.root().name

        if mode is None:
            if 'm' in tonic:
                mode = 'minor'
                tonic = re.sub('m', '', tonic)
            elif 'M' in tonic:
                mode = 'major'
                tonic = re.sub('M', '', tonic)
            elif tonic.lower() == tonic:
                mode = 'minor'
            else:
                mode = 'major'
        else:
            mode = mode.lower()
        sharps = pitchToSharps(tonic, mode)

        KeySignature.__init__(self, sharps)
        scale.DiatonicScale.__init__(self, tonic=tonic)

        if hasattr(tonic, 'classes') and 'Pitch' in tonic.classes:
            self.tonic = tonic
        else:
            self.tonic = pitch.Pitch(tonic)

        self.type = mode
        self.mode = mode

        # build the network for the appropriate scale
        self._abstract.buildNetwork(self.type)

        # optionally filled attributes
        # store a floating point value between 0 and 1 regarding
        # correlation coefficient between the detected key and the algorithm for detecting the key
        self.correlationCoefficient = None

        # store an ordered list of alternative Key objects
        self.alternateInterpretations = []

    def __hash__(self):
        hashTuple = (self.tonic, self.mode)
        return hash(hashTuple)

    def _reprInternal(self):
        return 'of ' + str(self)

    def __str__(self):
        # string representation needs to be complete, as is used
        # for metadata comparisons
        tonic = self.tonicPitchNameWithCase
        return f'{tonic} {self.mode}'

    def __eq__(self, other):
        '''
        two Keys are equal if their tonics are equal and their modes are equal
        '''
        try:
            if self.tonic == other.tonic and self.mode == other.mode:
                return True
            else:
                return False
        except AttributeError:
            return False

    @property
    def relative(self):
        '''
        if the Key is major or minor, return the relative minor or major.

        Otherwise, just returns self -- this is the best way to not have random crashes
        in the middle of large datasets.

        Note that this uses .sharps as a speedup, so if that has been changed, there
        will be a problem...

        >>> k = key.Key('E-')
        >>> k
        <music21.key.Key of E- major>
        >>> k.relative
        <music21.key.Key of c minor>
        >>> k.relative.relative
        <music21.key.Key of E- major>

        >>> key.Key('D', 'dorian').relative
        <music21.key.Key of D dorian>
        '''
        if self.mode not in ('minor', 'major'):
            return self

        if self.mode == 'major':
            return KeySignature(self.sharps).asKey('minor')
        else:  # minor
            return KeySignature(self.sharps).asKey('major')

    @property
    def parallel(self):
        '''
        if the Key is major or minor, return the parallel minor or major.

        Otherwise, just returns self -- this is the best way to not have random crashes
        in the middle of large datasets.

        >>> k = key.Key('D')
        >>> k
        <music21.key.Key of D major>
        >>> k.parallel
        <music21.key.Key of d minor>
        >>> k.parallel.parallel
        <music21.key.Key of D major>

        >>> key.Key('D', 'dorian').parallel
        <music21.key.Key of D dorian>
        '''
        if self.mode not in ('minor', 'major'):
            return self

        if self.mode == 'major':
            return Key(self.tonic, 'minor')
        else:  # minor
            return Key(self.tonic, 'major')

    @property
    def tonicPitchNameWithCase(self):
        '''
        Return the pitch name as a string with the proper case (upper = major; lower = minor)

        Useful, but simple:

        >>> k = key.Key('c#')
        >>> k.tonicPitchNameWithCase
        'c#'
        >>> k = key.Key('B')
        >>> k.tonicPitchNameWithCase
        'B'
        >>> k.mode = 'minor'
        >>> k.tonicPitchNameWithCase
        'b'

        Anything else will return the default (capital)

        >>> k.mode = 'dorian'
        >>> k.tonicPitchNameWithCase
        'B'
        '''
        tonic = self.tonic.name
        if self.mode == 'major':
            tonic = tonic.upper()
        elif self.mode == 'minor':
            tonic = tonic.lower()
        return tonic

    def deriveByDegree(self, degree, pitchRef):
        '''
        Given a degree and pitchReference derive a new
        Key object that has the same mode but a different tonic

        Example: What minor key has scale degree 3 as B-flat?

        >>> minorKey = key.Key(mode='minor')
        >>> newMinor = minorKey.deriveByDegree(3, 'B-')
        >>> newMinor
        <music21.key.Key of g minor>

        Note that in minor, the natural form is used:

        >>> minorKey.deriveByDegree(7, 'E')
        <music21.key.Key of f# minor>
        >>> minorKey.deriveByDegree(6, 'G')
        <music21.key.Key of b minor>

        To use the harmonic form, change `.abstract` on the key to
        another abstract scale:

        >>> minorKey.abstract = scale.AbstractHarmonicMinorScale()
        >>> minorKey.deriveByDegree(7, 'E')
        <music21.key.Key of f minor>
        >>> minorKey.deriveByDegree(6, 'G')
        <music21.key.Key of b minor>

        Currently because of a limitation in bidirectional scale
        searching, melodic minor scales cannot be used as abstracts
        for deriving by degree.

        New in v.6 -- preserve mode in key.Key.deriveByDegree
        '''
        ret = super().deriveByDegree(degree, pitchRef)
        ret.mode = self.mode

        # clear these since they no longer apply.
        ret.correlationCoefficient = None
        ret.alternateInterpretations = []

        return ret


    def _tonalCertaintyCorrelationCoefficient(self, *args, **keywords):
        # possible measures:
        if not self.alternateInterpretations:
            raise KeySignatureException(
                'cannot process ambiguity without a list of .alternateInterpretations')
        focus = []
        focus.append(self.correlationCoefficient)
        for subKey in self.alternateInterpretations:
            cc = subKey.correlationCoefficient
            if cc > 0:
                focus.append(cc)
        if len(focus) < 2:
            if self.correlationCoefficient <= 0:
                return 0.0
            else:
                return self.correlationCoefficient
        # take abs magnitude as one factor; assume between 0 and 1
        # greater certainty often has a larger number
        absMagnitude = focus[0]

        # take distance from first to second; greater certainty
        # seems to have a greater span
        leaderSpan = focus[0] - focus[1]

        # combine factors with a weighting for each
        # estimate range as 2, normalize between zero and 1
        return (absMagnitude * 1) + (leaderSpan * 2)

    def tonalCertainty(self,
                       method='correlationCoefficient',
                       *args,
                       **keywords):
        '''
        Provide a measure of tonal ambiguity for Key
        determined with one of many methods.

        The `correlationCoefficient` assumes that the
        alternateInterpretations list has
        been filled from the use of a KeyWeightKeyAnalysis subclass.

        >>> littlePiece = converter.parse('tinyNotation: 4/4 c4 d e f g a b cc ee gg ee cc')
        >>> k = littlePiece.analyze('key')
        >>> k
        <music21.key.Key of C major>
        >>> k.tonalCertainty()
        1.1648...

        Three most likely alternateInterpretations:

        >>> k.alternateInterpretations[0:3]
        [<music21.key.Key of a minor>, <music21.key.Key of F major>, <music21.key.Key of d minor>]
        >>> k.correlationCoefficient
        0.9068...
        >>> k.alternateInterpretations[0].correlationCoefficient
        0.7778...

        least likely interpretation:

        >>> k.alternateInterpretations[-1]
        <music21.key.Key of F# major>


        Note that this method only exists if the key has come from an analysis method. Otherwise
        it raises a KeySignatureException

        >>> k2 = key.Key('b-')
        >>> k2.tonalCertainty()
        Traceback (most recent call last):
        music21.key.KeySignatureException: cannot process ambiguity without a
            list of .alternateInterpretations

        >>> k2.alternateInterpretations
        []
        '''
        if method == 'correlationCoefficient':
            return self._tonalCertaintyCorrelationCoefficient(
                args, keywords)

    def transpose(self, value, *, inPlace=False):
        '''
        Transpose the Key by the user-provided value.
        If the value is an integer, the transposition is treated
        in half steps. If the value is a string, any Interval string
        specification can be provided. Alternatively, a
        :class:`music21.interval.Interval` object can be supplied.

        >>> dMajor = key.Key('D')
        >>> dMajor
        <music21.key.Key of D major>

        >>> aMaj = dMajor.transpose('p5')
        >>> aMaj
        <music21.key.Key of A major>
        >>> aMaj.sharps
        3
        >>> aMaj.tonic
        <music21.pitch.Pitch A>
        >>> aMaj.mode
        'major'

        inPlace works here

        >>> changingKey = key.Key('g')
        >>> changingKey
        <music21.key.Key of g minor>
        >>> changingKey.sharps
        -2
        >>> changingKey.transpose('m-3', inPlace=True)
        >>> changingKey
        <music21.key.Key of e minor>
        >>> changingKey.sharps
        1

        >>> changingKey.transpose(1, inPlace=True)
        >>> changingKey
        <music21.key.Key of f minor>
        >>> changingKey.sharps
        -4
        >>> changingKey.transpose(1, inPlace=True)
        >>> changingKey
        <music21.key.Key of f# minor>
        >>> changingKey.transpose(1, inPlace=True)
        >>> changingKey
        <music21.key.Key of g minor>
        >>> changingKey.transpose(1, inPlace=True)
        >>> changingKey
        <music21.key.Key of g# minor>

        '''
        if inPlace is True:
            super().transpose(value, inPlace=inPlace)
            post = self
        else:
            post = super().transpose(value, inPlace=inPlace)

        postKey = post.asKey(self.mode)
        post.tonic = postKey.tonic
        post.clearCache()

        # mode is already set
        if not inPlace:
            return post


# ------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def testCopyAndDeepcopy(self):
        '''
        Test copying all objects defined in this module
        '''
        import sys
        import types
        for part in sys.modules[self.__module__].__dict__:
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            name = getattr(sys.modules[self.__module__], part)
            # noinspection PyTypeChecker
            if callable(name) and not isinstance(name, types.FunctionType):
                try:  # see if obj can be made w/ args
                    obj = name()
                except TypeError:
                    continue
                i = copy.copy(obj)
                j = copy.deepcopy(obj)

    def testBasic(self):
        a = KeySignature()
        self.assertEqual(a.sharps, None)

    def testTonalAmbiguityA(self):
        from music21 import corpus, stream
        # s = corpus.parse('bwv64.2')
        # k = s.analyze('KrumhanslSchmuckler')
        # k.tonalCertainty(method='correlationCoefficient')

        s = corpus.parse('bwv66.6')
        k = s.analyze('KrumhanslSchmuckler')
        ta = k.tonalCertainty(method='correlationCoefficient')
        self.assertTrue(2 > ta > 0.1)

        s = corpus.parse('schoenberg/opus19', 6)
        k = s.analyze('KrumhanslSchmuckler')
        ta = k.tonalCertainty(method='correlationCoefficient')
        self.assertTrue(2 > ta > 0.1)

        sc1 = scale.MajorScale('g')
        sc2 = scale.MajorScale('d')
        sc3 = scale.MajorScale('a')
        sc5 = scale.MajorScale('f#')

        s = stream.Stream()
        for p in sc1.pitches:
            s.append(note.Note(p))
        k = s.analyze('KrumhanslSchmuckler')
        ta = k.tonalCertainty(method='correlationCoefficient')
        self.assertTrue(2 > ta > 0.1)

        s = stream.Stream()
        for p in sc1.pitches + sc2.pitches + sc2.pitches + sc3.pitches:
            s.append(note.Note(p))
        k = s.analyze('KrumhanslSchmuckler')
        ta = k.tonalCertainty(method='correlationCoefficient')
        self.assertTrue(2 > ta > 0.1)

        s = stream.Stream()
        for p in sc1.pitches + sc5.pitches:
            s.append(note.Note(p))
        k = s.analyze('KrumhanslSchmuckler')
        ta = k.tonalCertainty(method='correlationCoefficient')
        self.assertTrue(2 > ta > 0.1)

        s = stream.Stream()
        for p in ('c', 'g', 'c', 'c', 'e'):
            s.append(note.Note(p))
        k = s.analyze('KrumhanslSchmuckler')
        ta = k.tonalCertainty(method='correlationCoefficient')
        self.assertTrue(2 > ta > 0.1)

        # s = corpus.parse('bwv66.2')
        # k = s.analyze('KrumhanslSchmuckler')
        # k.tonalCertainty(method='correlationCoefficient')
        # s = corpus.parse('bwv48.3')


# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [KeySignature, Key]


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)


