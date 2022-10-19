# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         harmony.py
# Purpose:      music21 classes for representing harmonies and chord symbols
#
# Authors:      Michael Scott Asato Cuthbert
#               Beth Hadley
#               Jacob Tyler Walls
#               Christopher Ariza
#
# Copyright:    Copyright © 2011-2022, Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
An object representation of harmony, a subclass of chord, as encountered as chord symbols or
roman numerals, or other chord representations with a defined root.
'''
from __future__ import annotations

import collections
import copy
import re
import unittest

import typing as t

from music21 import base
from music21 import chord
from music21 import common
from music21 import duration
from music21 import environment
from music21 import exceptions21
from music21.figuredBass import realizerScale
from music21 import interval
from music21 import key
from music21 import pitch
from music21 import prebase
from music21 import style

environLocal = environment.Environment('harmony')

T = t.TypeVar('T', bound='ChordSymbol')
NCT = t.TypeVar('NCT', bound='NoChord')

# --------------------------------------------------------------------------


# Y indicates this chord_type is an official XML chord type
# N indicates XML does not support this chord type
# Y : 'some string' indicates XML supports the chord type, but
#      uses a name different from what I use in this dictionary
#      I mostly used XML's nomenclature, but for a few of the sevenths
#      I just couldn't stand to adopt their names because they aren't consistent
# sorry, you can't use '-' for minor, cause that's a flat in music21


# noinspection SpellCheckingInspection
CHORD_TYPES = collections.OrderedDict([
    ('major', ['1,3,5', ['', 'M', 'maj']]),  # Y
    ('minor', ['1,-3,5', ['m', 'min']]),  # Y
    ('augmented', ['1,3,#5', ['+', 'aug']]),  # Y
    ('diminished', ['1,-3,-5', ['dim', 'o']]),  # Y
    # sevenths
    ('dominant-seventh', ['1,3,5,-7', ['7', 'dom7', ]]),  # Y: 'dominant'
    ('major-seventh', ['1,3,5,7', ['maj7', 'M7']]),  # Y
    ('minor-major-seventh', ['1,-3,5,7', ['mM7', 'm#7', 'minmaj7']]),  # Y: 'major-minor'
    ('minor-seventh', ['1,-3,5,-7', ['m7', 'min7']]),  # Y
    ('augmented-major-seventh', ['1,3,#5,7', ['+M7', 'augmaj7']]),  # N
    ('augmented-seventh', ['1,3,#5,-7', ['7+', '+7', 'aug7']]),  # Y
    ('half-diminished-seventh', ['1,-3,-5,-7', ['ø7', 'm7b5']]),  # Y: 'half-diminished'
    ('diminished-seventh', ['1,-3,-5,--7', ['o7', 'dim7']]),  # Y
    ('seventh-flat-five', ['1,3,-5,-7', ['dom7dim5']]),  # N

    # sixths
    ('major-sixth', ['1,3,5,6', ['6']]),  # Y
    ('minor-sixth', ['1,-3,5,6', ['m6', 'min6']]),  # Y

    # ninths
    ('major-ninth', ['1,3,5,7,9', ['M9', 'Maj9']]),  # Y
    ('dominant-ninth', ['1,3,5,-7,9', ['9', 'dom9']]),  # Y
    ('minor-major-ninth', ['1,-3,5,7,9', ['mM9', 'minmaj9']]),  # N
    ('minor-ninth', ['1,-3,5,-7,9', ['m9', 'min9']]),  # N
    ('augmented-major-ninth', ['1,3,#5,7,9', ['+M9', 'augmaj9']]),  # Y
    ('augmented-dominant-ninth', ['1,3,#5,-7,9', ['9#5', '+9', 'aug9']]),  # N
    ('half-diminished-ninth', ['1,-3,-5,-7,9', ['ø9']]),  # N
    ('half-diminished-minor-ninth', ['1,-3,-5,-7,-9', ['øb9']]),  # N
    ('diminished-ninth', ['1,-3,-5,--7,9', ['o9', 'dim9']]),  # N
    ('diminished-minor-ninth', ['1,-3,-5,--7,-9', ['ob9', 'dimb9']]),  # N

    # elevenths
    ('dominant-11th', ['1,3,5,-7,9,11', ['11', 'dom11']]),  # Y
    ('major-11th', ['1,3,5,7,9,11', ['M11', 'Maj11']]),  # Y
    ('minor-major-11th', ['1,-3,5,7,9,11', ['mM11', 'minmaj11']]),  # N
    ('minor-11th', ['1,-3,5,-7,9,11', ['m11', 'min11']]),  # Y
    ('augmented-major-11th', ['1,3,#5,7,9,11', ['+M11', 'augmaj11']]),  # N
    ('augmented-11th', ['1,3,#5,-7,9,11', ['+11', 'aug11']]),  # N
    ('half-diminished-11th', ['1,-3,-5,-7,-9,11', ['ø11']]),  # N
    ('diminished-11th', ['1,-3,-5,--7,-9,-11', ['o11', 'dim11']]),  # N

    # thirteenths
    ('major-13th', ['1,3,5,7,9,11,13', ['M13', 'Maj13']]),  # Y
    ('dominant-13th', ['1,3,5,-7,9,11,13', ['13', 'dom13']]),  # Y
    ('minor-major-13th', ['1,-3,5,7,9,11,13', ['mM13', 'minmaj13']]),  # N
    ('minor-13th', ['1,-3,5,-7,9,11,13', ['m13', 'min13']]),  # Y
    ('augmented-major-13th', ['1,3,#5,7,9,11,13', ['+M13', 'augmaj13']]),  # N
    ('augmented-dominant-13th', ['1,3,#5,-7,9,11,13', ['+13', 'aug13']]),  # N
    ('half-diminished-13th', ['1,-3,-5,-7,9,11,13', ['ø13']]),  # N

    # other
    ('suspended-second', ['1,2,5', ['sus2']]),  # Y
    ('suspended-fourth', ['1,4,5', ['sus', 'sus4']]),  # Y
    ('suspended-fourth-seventh', ['1,4,5,-7', ['7sus', '7sus4']]),  # Y
    ('Neapolitan', ['1,2-,3,5-', ['N6']]),  # Y
    ('Italian', ['1,#4,-6', ['It+6', 'It']]),  # Y
    ('French', ['1,2,#4,-6', ['Fr+6', 'Fr']]),  # Y
    ('German', ['1,-3,#4,-6', ['Gr+6', 'Ger']]),  # Y
    ('pedal', ['1', ['pedal']]),  # Y
    ('power', ['1,5', ['power']]),  # Y
    ('Tristan', ['1,#4,#6,#9', ['tristan']]),  # Y
])

# these are different names used by MusicXML and others,
# and the authoritative name that they resolve to
CHORD_ALIASES = {'dominant': 'dominant-seventh',
                 'major-minor': 'minor-major-seventh',
                 'half-diminished': 'half-diminished-seventh',
                 }


# ------------------------------------------------------------------------------
class HarmonyException(exceptions21.Music21Exception):
    pass


# ------------------------------------------------------------------------------
class Harmony(chord.Chord):
    '''
    Harmony objects in music21 are a special type of chord - they retain all
    the same functionality as a chord (and inherit from chord directly),
    although they have special representations symbolically. They contain a
    figure representation, a shorthand, for the actual pitches they contain.
    This shorthand is commonly used on musical scores rather than writing out
    the chord pitches. Thus, each harmony object has an attribute,
    self.writeAsChord that dictates whether the object will be written to a
    score as a chord (with pitches realized) or with just the
    figure (as in Chord Symbols).

    Most users should start with the ChordSymbol class or the RomanNumeral
    class.  The Harmony object is primarily a base object for defining other
    sorts of objects:

    >>> c6 = harmony.ChordSymbol('C/E')
    >>> c6
    <music21.harmony.ChordSymbol C/E>

    By default, Harmony objects just float above the score and are a sort of
    analytical object.  To make them also count as pitches in a score, use
    `writeAsChord=True`

    >>> c6.writeAsChord = True
    >>> c6
    <music21.harmony.ChordSymbol C/E: E G C>

    Or individual components can be specified:

    >>> c6_again = harmony.ChordSymbol(root='C', bass='E', kind='major')
    >>> c6_again
    <music21.harmony.ChordSymbol C/E>

    It is also possible to instantiate an empty Harmony object and
    then set components later, but this is an advanced and delicate operation:

    >>> h = harmony.ChordSymbol()
    >>> h.root('B-3')
    >>> h.bass('D', allow_add=True)
    >>> h.inversion(1, transposeOnSet=False)
    >>> h.addChordStepModification(harmony.ChordStepModification('add', 4))
    >>> h
    <music21.harmony.ChordSymbol B-/D add 4>

    >>> h = harmony.ChordSymbol('C7/E')
    >>> h.root()
    <music21.pitch.Pitch C4>

    >>> h.bass()
    <music21.pitch.Pitch E3>

    >>> h.inversion()
    1

    >>> h.isSeventh()
    True

    >>> [str(p) for p in h.pitches]
    ['E3', 'G3', 'B-3', 'C4']

    >>> sus = harmony.ChordSymbol('Dsus4')
    >>> sus.root()
    <music21.pitch.Pitch D3>

    Accepts a keyword 'updatePitches'. By default, it
    is `True`, but can be set to `False` to initialize faster if pitches are not needed.
    '''
    # sort harmony just before notes and chords and other default objects
    classSortOrder = base.Music21Object.classSortOrder - 1
    _styleClass = style.TextStyle

    # INITIALIZER #

    def __init__(self,
                 figure: str | None = None,
                 root: str | pitch.Pitch | None = None,
                 bass: str | pitch.Pitch | None = None,
                 inversion: int | None = None,
                 updatePitches: bool = True,
                 **keywords
                 ):
        super().__init__(**keywords)
        self._writeAsChord = False
        # TODO: Deal with the roman numeral property of harmonies.
        #       MusicXML documentation is ambiguous:
        #       A root is a pitch name like C, D, E, where a function is an
        #       indication like I, II, III. It is an either/or choice to avoid
        #       data inconsistency.

        # a romanNumeral numeral object, musicxml stores this within a node
        # called <function> which might conflict with the Harmony...
        self._roman = None
        # specify an array of degree alteration objects
        self.chordStepModifications: list[ChordStepModification] = []
        self._degreesList: list[str] = []
        self._key = None
        # senseless to parse inversion until chord members are populated
        self._updateFromParameters(root=root, bass=bass)
        # figure is the string representation of a Harmony object
        # for example, for Chord Symbols the figure might be 'Cm7'
        # for roman numerals, the figure might be 'I7'
        self._figure = figure
        if self._figure:
            self._parseFigure()
        # if the bass is not specified, but the root is,
        # assume the bass and root are identical and
        # assign the values accordingly
        if 'bass' not in self._overrides and 'root' in self._overrides:
            self.bass(self._overrides['root'], allow_add=True)

        if (updatePitches
                and self._figure  # == '' or is not None
                or 'root' in self._overrides
                or 'bass' in self._overrides):
            self._updatePitches()
        self._updateFromParameters(root=root, bass=bass, inversion=inversion)

    # SPECIAL METHODS #

    def _reprInternal(self):
        summary = self.figure
        if self.writeAsChord:
            summary += ': '
            summary += ' '.join([p.name for p in self.pitches])
        return summary

    # PRIVATE METHODS #
    def _parseFigure(self):
        '''
        subclass this in extensions (SO WHY IS IT PRIVATE???)
        '''
        return

    def _updatePitches(self):
        '''
        subclass this in extensions (SO WHY IS IT PRIVATE???)
        '''
        return

    def _updateFromParameters(self, root, bass, inversion: int | None = None):
        '''
        This method must be called twice, once before the pitches
        are rendered, and once after. This is because after the pitches
        are rendered, the root() and bass() becomes reset by the chord class,
        but we want the objects to retain their initial root, bass, and inversion.
        '''
        if root and isinstance(root, str):
            root = common.cleanedFlatNotation(root)
            self.root(pitch.Pitch(root, octave=3))
        elif root is not None:
            self.root(root)
        if bass and isinstance(bass, str):
            bass = common.cleanedFlatNotation(bass)
            self.bass(pitch.Pitch(bass, octave=3), allow_add=True)
        elif bass is not None:
            self.bass(bass, allow_add=True)
        if inversion is not None:
            self.inversion(inversion, transposeOnSet=True)

    # PUBLIC PROPERTIES #

    @property
    def figure(self):
        '''
        Get or set the figure of the harmony object. The figure is the
        character (string) representation of the object. For example, 'I',
        'CM', '3#'.

        When you instantiate a harmony object, if you pass in a figure it
        is stored internally and returned when you access the figure
        property. If you don't instantiate the object with a figure, this
        property calls :meth:`music21.harmony.Harmony.findFigure` method which
        deduces the figure provided other information about the object,
        especially the chord.

        If the pitches of the harmony object have been modified after being
        instantiated, call :meth:`music21.harmony.Harmony.findFigure` to deduce the
        new figure.

        >>> h = harmony.ChordSymbol('CM')
        >>> h.figure
        'CM'

        >>> harmony.ChordSymbol(root='C', bass='A', kind='minor').figure
        'Cm/A'

        >>> h.bass(note.Note('E'))
        >>> h.figure
        'CM'
        '''
        if self._figure is None:
            return self.findFigure()
        else:
            return self._figure

    @figure.setter
    def figure(self, value):
        self._figure = value
        if self._figure:
            self._parseFigure()
            self._updatePitches()

    @property
    def key(self):
        '''
        Gets or sets the current Key (or Scale object) associated with this
        Harmony object.

        For a given RomanNumeral object. Each sub-classed harmony object
        may treat this property differently, for example Roman Numeral
        objects update the pitches when the key is changed, but chord
        symbol objects do not and the key provides more information about
        the musical context from where the harmony object was extracted.

        >>> r1 = roman.RomanNumeral('V')
        >>> r1.pitches
        (<music21.pitch.Pitch G4>, <music21.pitch.Pitch B4>, <music21.pitch.Pitch D5>)

        >>> r1.key = key.Key('A')
        >>> r1.pitches
        (<music21.pitch.Pitch E5>, <music21.pitch.Pitch G#5>, <music21.pitch.Pitch B5>)

        Changing the key for a ChordSymbol object does nothing to its pitches, since it's
        not dependent on key:

        >>> h1 = harmony.ChordSymbol('D-m11')
        >>> [str(p) for p in h1.pitches]
        ['D-2', 'F-2', 'A-2', 'C-3', 'E-3', 'G-3']

        >>> h1.key = 'CM'  # = C-Major
        >>> [str(p) for p in h1.pitches]
        ['D-2', 'F-2', 'A-2', 'C-3', 'E-3', 'G-3']


        But it should change the .romanNumeral object:

        >>> y = harmony.ChordSymbol('F')
        >>> y.key is None
        True
        >>> y.romanNumeral
        <music21.roman.RomanNumeral I in F major>
        >>> y.key = key.Key('C')
        >>> y.romanNumeral
        <music21.roman.RomanNumeral IV in C major>
        '''
        return self._key

    @key.setter
    def key(self, keyOrScale):
        if isinstance(keyOrScale, str):
            self._key = key.Key(keyOrScale)
        else:
            self._key = keyOrScale
            self._roman = None

    @property
    def romanNumeral(self):
        # noinspection SpellCheckingInspection
        '''
        Get or set the romanNumeral numeral function of the Harmony as a
        :class:`~music21.romanNumeral.RomanNumeral` object. String
        representations accepted by RomanNumeral are also accepted.

        >>> h = harmony.ChordSymbol('Dmaj7')
        >>> h.romanNumeral
        <music21.roman.RomanNumeral I7 in D major>

        >>> h.romanNumeral = 'III7'
        >>> h.romanNumeral
        <music21.roman.RomanNumeral III7>

        >>> h.romanNumeral.key = key.Key('B')
        >>> h.romanNumeral
        <music21.roman.RomanNumeral III7 in B major>

        >>> h.romanNumeral = roman.RomanNumeral('IV7', 'A')
        >>> h.romanNumeral
        <music21.roman.RomanNumeral IV7 in A major>

        >>> h = harmony.ChordSymbol('B-/D')
        >>> h.romanNumeral
        <music21.roman.RomanNumeral I6 in B- major>

        OMIT_FROM_DOCS

        Empty ChordSymbol = empty RomanNumeral:

        >>> harmony.ChordSymbol().romanNumeral
        <music21.roman.RomanNumeral>
        '''
        if self._roman is None:
            from music21 import roman
            if not self.pitches:
                return roman.RomanNumeral()

            # what is manipulating this so that write as chord matters?
            storedWriteAsChord = self._writeAsChord
            self.writeAsChord = True
            if self.key is None:
                self._roman = roman.romanNumeralFromChord(self, key.Key(self.root()))
            else:
                self._roman = roman.romanNumeralFromChord(self, self.key)
            self._writeAsChord = storedWriteAsChord
        return self._roman

    @romanNumeral.setter
    def romanNumeral(self, value):
        if hasattr(value, 'classes') and 'RomanNumeral' in value.classes:
            self._roman = value
            return
        from music21 import roman
        try:  # try to create
            self._roman = roman.RomanNumeral(value)
            return
        except exceptions21.Music21Exception:
            pass
        raise HarmonyException(f'not a valid pitch specification: {value}')

    @property
    def writeAsChord(self):
        '''
        Boolean attribute of all harmony objects that specifies how this
        object will be written to the rendered output (such as musicxml). If `True`
        (default for romanNumerals), the chord with pitches is written. If
        False (default for ChordSymbols) the harmony symbol is written.
        For `NoChord` objects, writeAsChord means to write as a rest.
        '''
        return self._writeAsChord

    @writeAsChord.setter
    def writeAsChord(self, val):
        self._writeAsChord = val
        # try:
        #     self._updatePitches()
        # except exceptions21.Music21Exception:
        #     pass
        if val and self.duration.quarterLength == 0:
            self.duration = duration.Duration(1)

    # PUBLIC METHODS #

    def addChordStepModification(self, degree, *, updatePitches=True):
        '''
        Add a harmony degree specification to this Harmony as a
        :class:`~music21.harmony.ChordStepModification` object.

        >>> hd = harmony.ChordStepModification('add', 4)
        >>> h = harmony.ChordSymbol()
        >>> h.addChordStepModification(hd)
        >>> h.addChordStepModification('juicy')
        Traceback (most recent call last):
        music21.harmony.HarmonyException: cannot add this object as a degree: juicy

        Alteration will also impact the pitches,
        if the keyword argument updatePitches is given as True

        >>> h = harmony.ChordSymbol('C')
        >>> mod = harmony.ChordStepModification('alter', 5, -1)
        >>> h.addChordStepModification(mod, updatePitches=True)
        >>> h.pitches
        (<music21.pitch.Pitch C3>, <music21.pitch.Pitch E3>, <music21.pitch.Pitch G-3>)

        * Changed in v7: updatePitches is True by default
        '''
        if not isinstance(degree, ChordStepModification):
            # TODO: possibly create ChordStepModification objects from other
            # specifications
            raise HarmonyException(
                f'cannot add this object as a degree: {degree}')

        self.chordStepModifications.append(degree)
        if updatePitches:
            self._updatePitches()

    def findFigure(self):
        return 'No Figure Representation'

    def getChordStepModifications(self):
        '''
        Return all harmony degrees as a list.
        '''
        return self.chordStepModifications


# ------------------------------------------------------------------------------


class ChordStepModificationException(exceptions21.Music21Exception):
    pass

# ------------------------------------------------------------------------------


class ChordStepModification(prebase.ProtoM21Object):
    '''
    ChordStepModification objects define the specification of harmony degree
    alterations, subtractions, or additions, used in
    :class:`~music21.harmony.Harmony` objects, which includes
    harmony.ChordSymbol objects (and will include harmony.RomanNumeral
    objects).

    - degree-value element: indicates degree in chord, positive integers only
    - degree-alter: indicates semitone alteration of degree, positive and
      negative integers only
    - degree-type: add, alter, or subtract
        - if `add`: degree-alter is relative to a dominant chord (major and
          perfect intervals except for a minor seventh)
        - if `alter` or `subtract`: degree-alter is relative to degree already in
          the chord based on its kind element

    >>> hd = harmony.ChordStepModification('add', 4)
    >>> hd
    <music21.harmony.ChordStepModification modType=add degree=4 interval=None>

    >>> hd = harmony.ChordStepModification('alter', 3, 1)
    >>> hd
    <music21.harmony.ChordStepModification modType=alter
        degree=3 interval=<music21.interval.Interval A1>>
    '''
    # FROM MUSIC XML DOCUMENTATION - FOR DEVELOPER'S REFERENCE
    # The degree element is used to add, alter, or subtract
    # individual notes in the chord. The degree-value element
    # is a number indicating the degree of the chord (1 for
    # the root, 3 for third, etc). The degree-alter element
    # is like the alter element in notes: 1 for sharp, -1 for
    # flat, etc. The degree-type element can be `add`, `alter`, or
    # `subtract`. If the degree-type is alter or subtract, the
    # degree-alter is relative to the degree already in the
    # chord based on its kind element. If the degree-type is
    # `add`, the degree-alter is relative to a dominant chord
    # (major and perfect intervals except for a minor
    # seventh). The print-object attribute can be used to
    # keep the degree from printing separately when it has
    # already taken into account in the text attribute of
    # the kind element. The plus-minus attribute is used to
    # indicate if plus and minus symbols should be used
    # instead of sharp and flat symbols to display the degree
    # alteration; it is `no` by default. The degree-value and
    # degree-type text attributes specify how the value and
    # type of the degree should be displayed.
    #
    # A harmony of kind "other" can be spelled explicitly by
    # using a series of degree elements together with a root.

    # INITIALIZER #

    def __init__(self, modType=None, degree=None, intervalObj=None):
        self._modType = None  # add, alter, subtract
        self._interval = None  # alteration of degree, alter ints in mxl
        self._degree = None  # the degree number, where 3 is the third
        # use properties if defined
        if modType is not None:
            self.modType = modType
        if degree is not None:
            self.degree = degree
        if intervalObj is not None:
            self.interval = intervalObj

    # SPECIAL METHODS #

    def _reprInternal(self):
        return f'modType={self.modType} degree={self.degree} interval={self.interval}'

    # PUBLIC PROPERTIES #

    @property
    def degree(self):
        '''
        Returns or sets an integer specifying the scale degree
        that this ChordStepModification alters.

        >>> hd = harmony.ChordStepModification()
        >>> hd.degree = 3
        >>> hd.degree
        3

        >>> hd.degree = 'juicy'
        Traceback (most recent call last):
        music21.harmony.ChordStepModificationException: not a valid degree: juicy
        '''
        return self._degree

    @degree.setter
    def degree(self, expr):
        if expr is not None and common.isNum(expr):
            self._degree = int(expr)  # should always be an integer
            return
        raise ChordStepModificationException(
            f'not a valid degree: {expr}')

    @property
    def interval(self):
        '''
        Get or set the alteration of this degree as a
        :class:`~music21.interval.Interval` object, generally
        as a type of ascending or descending augmented unison.

        >>> hd = harmony.ChordStepModification()
        >>> hd.interval = 1
        >>> hd.interval
        <music21.interval.Interval A1>

        >>> hd.interval = -2
        >>> hd.interval
        <music21.interval.Interval AA-1>

        >>> hd.interval = 0
        >>> hd.interval
        <music21.interval.Interval P1>

        >>> hd.interval = interval.Interval('m3')
        >>> hd.interval
        <music21.interval.Interval m3>

        More than 3 half step alteration gets
        an interval that isn't a prime.

        >>> hd.interval = -4
        >>> hd.interval
        <music21.interval.Interval M-3>
        '''
        return self._interval

    @interval.setter
    def interval(self, value):
        if value in (None,):
            self._interval = None
        elif isinstance(value, interval.Interval):
            # an interval object: set directly
            self._interval = value
        else:
            # accept numbers to permit loading from mxl alter specs
            numAs = abs(value)
            if numAs <= 3:
                if numAs == 0:
                    aStr = 'P'
                else:
                    aStr = 'a' * numAs
                aStr += '1'
                if value < 0:
                    aStr += '-'
                self._interval = interval.Interval(aStr)
            else:  # try to create interval object
                self._interval = interval.Interval(value)

    @property
    def modType(self):
        '''
        Get or set the ChordStepModification modification type, where
        permitted types are the strings add, subtract, or alter.

        >>> hd = harmony.ChordStepModification()
        >>> hd.modType = 'add'
        >>> hd.modType
        'add'

        >>> hd.modType = 'juicy'
        Traceback (most recent call last):
        music21.harmony.ChordStepModificationException: not a valid degree modification type: juicy
        '''
        return self._modType

    @modType.setter
    def modType(self, expr):
        if expr is not None and isinstance(expr, str):
            if expr.lower() in ['add', 'subtract', 'alter']:
                self._modType = expr.lower()
                return
        raise ChordStepModificationException(
            f'not a valid degree modification type: {expr}')


# ------------------------------------------------------------------------------


def addNewChordSymbol(chordTypeName, fbNotationString, AbbreviationList):
    # noinspection SpellCheckingInspection
    '''
    Add a new chord symbol:

    >>> harmony.addNewChordSymbol('BethChord', '1,3,-6,#9', ['MH', 'beth'])
    >>> [str(p) for p in harmony.ChordSymbol('BMH').pitches]
    ['B2', 'C##3', 'D#3', 'G3']

    >>> harmony.ChordSymbol('Cbeth').pitches
    (<music21.pitch.Pitch C3>, <music21.pitch.Pitch D#3>,
     <music21.pitch.Pitch E3>, <music21.pitch.Pitch A-3>)

    >>> harmony.ChordSymbol('C-beth').pitches
    (<music21.pitch.Pitch C-3>, <music21.pitch.Pitch D3>,
     <music21.pitch.Pitch E-3>, <music21.pitch.Pitch A--3>)

    OMIT_FROM_DOCS

    >>> harmony.ChordSymbol(root='Cb', kind='BethChord').pitches
    (<music21.pitch.Pitch C-3>, <music21.pitch.Pitch D3>,
     <music21.pitch.Pitch E-3>, <music21.pitch.Pitch A--3>)

    >>> harmony.ChordSymbol(root='C-', kind='BethChord').pitches
    (<music21.pitch.Pitch C-3>, <music21.pitch.Pitch D3>,
     <music21.pitch.Pitch E-3>, <music21.pitch.Pitch A--3>)

    >>> harmony.removeChordSymbols('BethChord')
    '''
    CHORD_TYPES[chordTypeName] = [fbNotationString, AbbreviationList]


def changeAbbreviationFor(chordType, changeTo):
    '''
    Change the current Abbreviation used for a certain
    :class:`music21.harmony.ChordSymbol` chord type

    >>> harmony.getCurrentAbbreviationFor('minor')
    'm'

    >>> harmony.changeAbbreviationFor('minor', 'min')
    >>> harmony.getCurrentAbbreviationFor('minor')
    'min'

    OMIT_FROM_DOCS

    >>> harmony.changeAbbreviationFor('minor', 'm')  # must change it back for the rest of doctests
    '''
    CHORD_TYPES[chordType][1].insert(0, changeTo)


def chordSymbolFigureFromChord(inChord: chord.Chord, includeChordType=False):
    # noinspection SpellCheckingInspection
    '''
    Analyze the given chord, and attempt to describe its pitches using a
    standard chord symbol figure.

    The pitches of the chord are analyzed based on intervals, and compared to
    standard triads, sevenths, ninths, elevenths, and thirteenth chords. The
    type of chord therefore is determined if it matches (given certain
    guidelines documented below) and the figure is returned. There is no
    standard "chord symbol" notation, so a typical notation is used that can be
    easily modified if desired by changing a dictionary in the source code.

    Set includeChordType to true (default is False) to return a tuple, the
    first element being the figure and the second element the identified chord
    type.

    >>> harmony.chordSymbolFigureFromChord(chord.Chord(['C3', 'E3', 'G3']))
    'C'

    THIRDS

    >>> c = chord.Chord(['C3', 'E3', 'G3'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('C', 'major')

    >>> c = chord.Chord(['B-3', 'D-4', 'F4'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('B-m', 'minor')

    >>> c = chord.Chord(['F#3', 'A#3', 'C##4'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('F#+', 'augmented')

    >>> c = chord.Chord(['C3', 'E-3', 'G-3'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('Cdim', 'diminished')

    SEVENTHS

    >>> c = chord.Chord(['E-3', 'G3', 'B-3', 'D-4'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('E-7', 'dominant-seventh')

    >>> c = chord.Chord(['C3', 'E3', 'G3', 'B3'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('Cmaj7', 'major-seventh')

    >>> c = chord.Chord(['F#3', 'A3', 'C#4', 'E#4'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('F#mM7', 'minor-major-seventh')

    >>> c = chord.Chord(['F3', 'A-3', 'C4', 'E-4'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('Fm7', 'minor-seventh')

    >>> c = chord.Chord(['F3', 'A3', 'C#4', 'E4'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('F+M7', 'augmented-major-seventh')

    >>> c = chord.Chord(['C3', 'E3', 'G#3', 'B-3'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('C7+', 'augmented-seventh')

    >>> c = chord.Chord(['G3', 'B-3', 'D-4', 'F4'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('Gø7', 'half-diminished-seventh')

    >>> c = chord.Chord(['C3', 'E-3', 'G-3', 'B--3'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('Co7', 'diminished-seventh')

    >>> c = chord.Chord(['B-3', 'D4', 'F-4', 'A-4'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('B-dom7dim5', 'seventh-flat-five')

    NINTHS

    >>> c = chord.Chord(['C3', 'E3', 'G3', 'B3', 'D3'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('CM9', 'major-ninth')

    >>> c = chord.Chord(['B-3', 'D4', 'F4', 'A-4', 'C4'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('B-9', 'dominant-ninth')

    >>> c = chord.Chord(['E-3', 'G-3', 'B-3', 'D4', 'F3'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('E-mM9', 'minor-major-ninth')

    >>> c = chord.Chord(['C3', 'E-3', 'G3', 'B-3', 'D3'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('Cm9', 'minor-ninth')

    >>> c = chord.Chord(['F#3', 'A#3', 'C##4', 'E#4', 'G#3'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('F#+M9', 'augmented-major-ninth')

    >>> c = chord.Chord(['G3', 'B3', 'D#4', 'F4', 'A3'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('G9#5', 'augmented-dominant-ninth')

    >>> c = chord.Chord(['C3', 'E-3', 'G-3', 'B-3', 'D3'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('Cø9', 'half-diminished-ninth')

    >>> c = chord.Chord(['B-3', 'D-4', 'F-4', 'A-4', 'C-4'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('B-øb9', 'half-diminished-minor-ninth')

    >>> c = chord.Chord(['C3', 'E-3', 'G-3', 'B--3', 'D3'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('Co9', 'diminished-ninth')

    >>> c = chord.Chord(['F3', 'A-3', 'C-4', 'E--4', 'G-3'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('Fob9', 'diminished-minor-ninth')

    This harmony can either be CmaddD or Csus2addE-. music21 prefers the former.
    Change the ordering of harmony.CHORD_TYPES to switch the preference. From Bach BWV380

    >>> c = chord.Chord(['C3', 'D4', 'G4', 'E-5'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('CmaddD', 'minor')


    ELEVENTHS

    >>> c = chord.Chord(['E-3', 'G3', 'B-3', 'D-4', 'F3', 'A-3'] )
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('E-11', 'dominant-11th')

    >>> c = chord.Chord(['G3', 'B3', 'D4', 'F#4', 'A3', 'C4'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('GM11', 'major-11th')

    >>> c = chord.Chord(['C3', 'E-3', 'G3', 'B3', 'D3', 'F3'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('CmM11', 'minor-major-11th')

    >>> c = chord.Chord(['F#3', 'A3', 'C#4', 'E4', 'G#3', 'B3'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('F#m11', 'minor-11th')

    >>> c = chord.Chord(['B-3', 'D4', 'F#4', 'A4', 'C4', 'E-4'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('B-+M11', 'augmented-major-11th')

    >>> c = chord.Chord(['F3', 'A3', 'C#4', 'E-4', 'G3', 'B-3'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('F+11', 'augmented-11th')

    >>> c = chord.Chord(['G3', 'B-3', 'D-4', 'F4', 'A-3', 'C4'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('Gø11', 'half-diminished-11th')

    >>> c = chord.Chord(['E-3', 'G-3', 'B--3', 'D--4', 'F-3', 'A--3'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('E-o11', 'diminished-11th')

    THIRTEENTHS
    these are so tricky...music21 needs to be told what the root is in these cases
    all tests here are 'C' chords, but any root will work:

    >>> c = chord.Chord(['C3', 'E3', 'G3', 'B3', 'D4', 'F4', 'A4'])
    >>> c.root('C3')
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('CM13', 'major-13th')

    >>> c = chord.Chord(['C3', 'E3', 'G3', 'B-3', 'D4', 'F4', 'A4'])
    >>> c.root('C3')
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('C13', 'dominant-13th')

    >>> c = chord.Chord(['C3', 'E-3', 'G3', 'B3', 'D4', 'F4', 'A4'])
    >>> c.root('C3')
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('CmM13', 'minor-major-13th')

    >>> c = chord.Chord(['C3', 'E-3', 'G3', 'B-3', 'D4', 'F4', 'A4'])
    >>> c.root('C3')
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('Cm13', 'minor-13th')

    >>> c = chord.Chord(['C3', 'E3', 'G#3', 'B3', 'D4', 'F4', 'A4'])
    >>> c.root('C3')
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('C+M13', 'augmented-major-13th')

    >>> c = chord.Chord(['C3', 'E3', 'G#3', 'B-3', 'D4', 'F4', 'A4'])
    >>> c.root('C3')
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('C+13', 'augmented-dominant-13th')

    >>> c = chord.Chord(['C3', 'E-3', 'G-3', 'B-3', 'D4', 'F4', 'A4'])
    >>> c.root('C3')
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('Cø13', 'half-diminished-13th')

    Pop chords are typically not always "strictly" spelled and often certain degrees
    are omitted. Therefore, the following common chord omissions are permitted
    and the chord will still be identified correctly:

    * triads: none
    * seventh chords: none
    * ninth chords: fifth
    * eleventh chords: third and/or fifth
    * thirteenth chords: fifth, eleventh, ninth


    This Chord could be minor 7th with a C4, but because this 5th isn't present, not identified

    >>> c = chord.Chord(['F3', 'A-3', 'E-4'])
    >>> harmony.chordSymbolFigureFromChord(c)
    'Chord Symbol Cannot Be Identified'

    Removing the fifth G3  (fifth of chord)

    >>> c = chord.Chord(['C3', 'E3',  'B3', 'D3'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('CM9', 'major-ninth')

    Chord with G3 and B-3 removed (3rd & 5th of chord)

    >>> c = chord.Chord(['E-3', 'D-4', 'F3', 'A-3'] )

    Without a 3rd and 5th, root() algorithm can't locate the root,
    so we must tell it the root (or write an algorithm that assumes the root is the
    lowest note if the root can't be found)

    >>> c.root('E-3')
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('E-11', 'dominant-11th')

    Inversions are supported, and indicated with a '/' between the root, type-string, and bass

    >>> c = chord.Chord([ 'G#3', 'B-3', 'C4', 'E4',])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('C7+/G#', 'augmented-seventh')

    >>> c = chord.Chord(['G#2', 'B2', 'F#3', 'A3', 'C#4', 'E4'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('F#m11/G#', 'minor-11th')

    if the algorithm matches the chord, but omissions or subtractions are present,
    the chord symbol attempts to indicate this (although there is no standard way of doing
    this so the notation might be different from what you're familiar with).

    An example of using this algorithm for identifying chords "in the wild":

    >>> score = corpus.parse('bach/bwv380')
    >>> excerpt = score.measures(2, 3)
    >>> chfy = excerpt.chordify()
    >>> for c in chfy.flatten().getElementsByClass(chord.Chord):
    ...   print(harmony.chordSymbolFigureFromChord(c))
    B-7
    E-maj7/B-
    B-7
    Chord Symbol Cannot Be Identified
    B-7
    E-
    B-
    Chord Symbol Cannot Be Identified
    B-/D
    B-7
    CmaddD
    Cm/D
    E-+M7/D
    Cm/E-
    F7

    Notice, however, that this excerpt contains many embellishment and non-harmonic tones,
    so an algorithm to truly identify the chord symbols must be as complex as any harmonic
    analysis algorithm, which this is not, so innately this method is flawed.

    And for the sake of completeness, unique chords supported by musicxml that
    this method can still successfully identify. Notice that the root must
    often be specified for this method to work.

    >>> c = chord.Chord(['C3', 'D3', 'G3'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('Csus2', 'suspended-second')
    >>> c.root()
    <music21.pitch.Pitch C3>
    >>> c.bass()
    <music21.pitch.Pitch C3>


    >>> c = chord.Chord(['C3', 'F3', 'G3'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('Csus', 'suspended-fourth')
    >>> c.root()
    <music21.pitch.Pitch C3>
    >>> c.inversion()
    0

    >>> c = chord.Chord(['C3', 'D-3', 'E3', 'G-3'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('CN6', 'Neapolitan')

    >>> c = chord.Chord(['C3', 'F#3', 'A-3'])
    >>> c.root('C3')
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('CIt+6', 'Italian')

    >>> c = chord.Chord(['C3', 'D3', 'F#3', 'A-3'])
    >>> c.root('C3')
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('CFr+6', 'French')

    >>> c = chord.Chord(['C3', 'E-3', 'F#3', 'A-3'])
    >>> c.root('C3')
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('CGr+6', 'German')

    >>> c = chord.Chord(['C3'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('Cpedal', 'pedal')

    >>> c = chord.Chord(['C3', 'G3'])
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('Cpower', 'power')

    >>> c = chord.Chord(['F3', 'G#3', 'B3', 'D#4'] )
    >>> c.root('F3')
    >>> harmony.chordSymbolFigureFromChord(c, True)
    ('Ftristan', 'Tristan')

    This algorithm works as follows:

    1. chord is analyzed for root (using chord's root() )
       if the root cannot be determined, error is raised
       be aware that the root() method determines the root based on which note has
       the most thirds above it
       this is not a consistent way to determine the root of 13th chords, for example
    2. a chord vector is extracted from the chord
        using  :meth:`music21.chord.Chord.semitonesFromChordStep`
        this vector extracts the following degrees: (2, 3, 4, 5, 6, 7, 9, 11, and 13)
    3. this vector is converted to fbNotationString (in the form of chord step,
        and a '-' or '#' to indicate semitone distance)
    4. the fbNotationString is matched against the CHORD_TYPES dictionary in this harmony module,
        although certain subtractions are permitted for example a 9th chord will
        still be identified correctly even if it is missing the 5th
    5. the type with the most identical matches is used, and if no type matches,
        "Chord Type Cannot Be Identified" is returned
    6. the output format for the chord symbol figure is the chord's root (with 'b' instead of '-'),
        the chord type's Abbreviation (saved in CHORD_TYPES dictionary),
        a '/' if the chord is in an inversion, and the chord's bass

    The chord symbol nomenclature is not entirely standardized. There are several
    ways to write each abbreviation.

    For example, an augmented triad might be symbolized with '+' or 'aug'.
    Thus, by default the returned symbol is the first (element 0) in the CHORD_TYPES list.
    For example (Eb minor eleventh chord, second inversion):

        root + chord-type-str + '/' + bass = 'Ebmin11/Bb'

    Users who wish to change these defaults can simply change that
    entry in the CHORD_TYPES dictionary.

    >>> harmony.chordSymbolFigureFromChord(chord.Chord(['C2', 'E2', 'G2']))
    'C'

    >>> harmony.changeAbbreviationFor('major', 'maj')
    >>> harmony.chordSymbolFigureFromChord(chord.Chord(['C2', 'E2', 'G2']))
    'Cmaj'

    OMIT_FROM_DOCS

    >>> harmony.changeAbbreviationFor('major', '')

    '''
    if not inChord.pitches:
        return ''

    try:
        inChord.root()
    except Exception as e:
        raise HarmonyException(str(e)) from e

    if len(inChord.pitches) == 1:
        if includeChordType:
            return (inChord.root().name.replace('-', 'b') + 'pedal', 'pedal')
        else:
            return inChord.root().name.replace('-', 'b') + 'pedal'

    d3 = inChord.semitonesFromChordStep(3)  # 4  triad
    d5 = inChord.semitonesFromChordStep(5)  # 7  triad
    d7 = inChord.semitonesFromChordStep(7)  # 11 seventh
    d9 = inChord.semitonesFromChordStep(2)  # 2  ninth
    d11 = inChord.semitonesFromChordStep(4)  # 5  eleventh
    d13 = inChord.semitonesFromChordStep(6)  # 9  thirteenth

    d2 = d9
    d4 = d11
    d6 = d13

    def compare(inChordNums, givenChordNums, permittedOmissions=()):
        '''
        inChord is the chord the user submits to analyze,
        givenChordNum is the chord type that the method is currently looking at
        to determine if it could be a match for inChord

        the corresponding semitones are compared, and if they do not match it is determined
        whether this is a permitted omission, etc.

        '''
        m = len(givenChordNums)
        if m > len(inChordNums):
            return False
        if m >= 1 and inChordNums[0] != givenChordNums[0]:
            if (not (3 in permittedOmissions and givenChordNums[0] == 4)
                    or inChordNums[0] is not None):
                return False
        if m >= 2 and inChordNums[1] != givenChordNums[1]:
            if (not (5 in permittedOmissions and givenChordNums[1] == 7)
                    or inChordNums[1] is not None):
                return False
        if m >= 3 and inChordNums[2] != givenChordNums[2]:
            if (not (7 in permittedOmissions and givenChordNums[2] == 11)
                    or inChordNums[2] is not None):
                return False
        if m >= 4 and inChordNums[3] != givenChordNums[3]:
            if (not (9 in permittedOmissions and givenChordNums[3] == 2)
                    or inChordNums[3] is not None):
                return False
        if m >= 5 and inChordNums[4] != givenChordNums[4]:
            if (not (11 in permittedOmissions and givenChordNums[4] == 5)
                    or inChordNums[4] is not None):
                return False
        if m >= 6 and inChordNums[5] != givenChordNums[5]:
            if (not (13 in permittedOmissions and givenChordNums[5] == 9)
                    or inChordNums[5] is not None):
                return False

        return True

    kindStr = kind = ''
    isTriad = inChord.isTriad()
    isSeventh = inChord.isSeventh()

    def convertFBNotationStringToDegrees(innerKind, fbNotation):
        # convert the fb-notation string provided in CHORD_TYPES to chordDegrees notation
        types = {
            3: 4,
            5: 7,
            7: 11,
            9: 2,
            11: 5,
            13: 9,
            2: 2,
            4: 5,
            6: 9,
        }
        inner_chordDegrees = []
        if innerKind in CHORD_ALIASES:
            innerKind = CHORD_ALIASES[innerKind]

        if innerKind in CHORD_TYPES:
            for char in fbNotation.split(','):
                if char == '1':
                    continue
                if '-' in char:
                    alt = char.count('-') * -1
                else:
                    alt = char.count('#')
                degree = int(char.replace('-', '').replace('#', ''))
                inner_chordDegrees.append(types[degree] + alt)
        return inner_chordDegrees

    for chordKind in CHORD_TYPES:
        chordKindStr = getAbbreviationListGivenChordType(chordKind)
        fbNotationString = getNotationStringGivenChordType(chordKind)
        chordDegrees = convertFBNotationStringToDegrees(chordKind, fbNotationString)
        if not common.isListLike(chordKindStr):
            chordKindStr = [chordKindStr]

        if common.isListLike(chordDegrees):
            if len(chordDegrees) == 2 and isTriad:
                if compare((d3, d5), chordDegrees) and isTriad:
                    kind = chordKind
                    kindStr = chordKindStr[0]
            elif len(chordDegrees) == 3 and isSeventh:
                if compare((d3, d5, d7), chordDegrees):
                    kind = chordKind
                    kindStr = chordKindStr[0]
            elif len(chordDegrees) == 4 and d9 and not d11 and not d13:
                if compare((d3, d5, d7, d9), chordDegrees, permittedOmissions=(5,)):
                    kind = chordKind
                    kindStr = chordKindStr[0]
            elif len(chordDegrees) == 5 and d11 and not d13:
                if compare((d3, d5, d7, d9, d11), chordDegrees, permittedOmissions=(3, 5)):
                    kind = chordKind
                    kindStr = chordKindStr[0]
            elif len(chordDegrees) == 6 and d13:
                if compare((d3, d5, d7, d9, d11, d13), chordDegrees, permittedOmissions=(5, 11, 9)):
                    kind = chordKind
                    kindStr = chordKindStr[0]

    if not kind:  # if, after all that, no chord has been found, try to match by degree instead
        numberOfMatchedDegrees = 0
        for chordKind in CHORD_TYPES:
            chordKindStr = getAbbreviationListGivenChordType(chordKind)
            fbNotationString = getNotationStringGivenChordType(chordKind)
            chordDegrees = convertFBNotationStringToDegrees(chordKind, fbNotationString)
            if not common.isListLike(chordKindStr):
                chordKindStr = [chordKindStr]

            if common.isListLike(chordDegrees):
                s = fbNotationString.replace('-', '').replace('#', '')
                degrees = s.split(',')
                degrees = [int(x) for x in degrees]
                degrees.sort()

                data = {2: d2, 3: d3, 4: d4, 5: d5, 6: d6, 7: d7, 9: d9, 11: d11, 13: d13}
                toCompare = []
                for x in degrees:
                    if x != 1:
                        toCompare.append(data[x])

                if compare(toCompare, chordDegrees):
                    if numberOfMatchedDegrees < len(chordDegrees):
                        # a better match has been found! update!
                        numberOfMatchedDegrees = len(chordDegrees)
                        kind = chordKind
                        kindStr = chordKindStr[0]

    if kind:
        # new algorithm makes sus chord be a sus2 in inversion:
        if inChord.inversion():
            if kindStr == 'sus2':
                inChord.root(inChord.bass())
                kindStr = 'sus'
                kind = 'suspended-fourth'
                cs = inChord.root().name + kindStr
            else:
                cs = inChord.root().name + kindStr + '/' + inChord.bass().name
        else:
            cs = inChord.root().name + kindStr
        perfect = {p.name for p in ChordSymbol(cs).pitches}
        inPitches = {p.name for p in inChord.pitches}

        if not perfect.issuperset(inPitches):  # must be subtraction or deletion....
            additions = inPitches.difference(perfect)
            subtractions = perfect.difference(inPitches)
            if additions:
                cs += 'add'
                for a in additions:
                    cs += (a + ',')
            if subtractions:
                cs += 'omit'
                for s in subtractions:
                    cs += (s + ',')
            cs = cs[:-1]
    else:
        cs = 'Chord Symbol Cannot Be Identified'
    if includeChordType:
        return (cs, kind)
    else:
        return cs


def chordSymbolFromChord(inChord: chord.Chord) -> ChordSymbol:
    '''
    Get the :class:`~music21.harmony.chordSymbol` object from the chord, using
    :meth:`music21.harmony.Harmony.chordSymbolFigureFromChord`

    >>> c = chord.Chord(['D3', 'F3', 'A4', 'B-5'])
    >>> symbol = harmony.chordSymbolFromChord(c)
    >>> symbol
    <music21.harmony.ChordSymbol B-maj7/D>
    >>> c.pitches == symbol.pitches
    True
    '''
    cs = ChordSymbol(chordSymbolFigureFromChord(inChord))
    cs.pitches = inChord.pitches
    return cs


def getAbbreviationListGivenChordType(chordType):
    '''
    Get the Abbreviation list (all allowed Abbreviations that map to this
    :class:`music21.harmony.ChordSymbol` object):

    >>> harmony.getAbbreviationListGivenChordType('minor-major-13th')
    ['mM13', 'minmaj13']

    '''
    return CHORD_TYPES[chordType][1]


def getCurrentAbbreviationFor(chordType):
    '''
    Return the current Abbreviation for a given
    :class:`music21.harmony.ChordSymbol` chordType:

    >>> harmony.getCurrentAbbreviationFor('dominant-seventh')
    '7'

    '''
    return getAbbreviationListGivenChordType(chordType)[0]


def getNotationStringGivenChordType(chordType):
    '''
    Get the notation string (fb-notation style) associated with this
    :class:`music21.harmony.ChordSymbol` chordType

    >>> harmony.getNotationStringGivenChordType('German')
    '1,-3,#4,-6'

    '''
    return CHORD_TYPES[chordType][0]


def removeChordSymbols(chordType):
    '''
    Remove the given chord type from the CHORD_TYPES dictionary, so it
    can no longer be identified or parsed by harmony methods.
    '''
    del CHORD_TYPES[chordType]


# --------------------------------------------------------------------------
realizerScaleCache: dict[tuple[str, str], realizerScale.FiguredBassScale] = {}

# --------------------------------------------------------------------------


class ChordSymbol(Harmony):
    # noinspection SpellCheckingInspection
    '''
    Class representing the Chord Symbols commonly found on lead sheets.
    Chord Symbol objects can be instantiated one of two main ways:

    1. when music xml is parsed by the music21 converter, xml Chord Symbol tags
       are interpreted as Chord Symbol objects with a root and kind attribute.
       If bass is not specified, the bass is assumed to be the root

    2. by creating a chord symbol object with music21 by passing in the
       expression commonly found on leadsheets. Due to the relative diversity
       of lead sheet chord syntax, not all expressions are supported. Consult
       the examples for the supported syntax, or email us for help.

    All :class:`~music21.harmony.ChordSymbol` inherit from
    :class:`~music21.chord.Chord` so you can consider these objects as chords,
    although they have a unique representation in a score. ChordSymbols, unlike
    chords, by default appear as chord symbols in a score and have duration of
    0.

    To obtain the chord representation of the `ChordSymbol` in the score, change
    :attr:`~music21.harmony.Harmony.writeAsChord` to True. Unless otherwise
    specified, the duration of this chord object will become 1.0. If you have a
    leadsheet, run :func:`music21.harmony.realizeChordSymbolDurations` on the
    stream to assign the correct (according to offsets) duration to each
    harmony object.)

    The music xml-based approach to instantiating Chord Symbol objects:

    >>> cs = harmony.ChordSymbol(kind='minor', kindStr='m', root='C', bass='E-')
    >>> cs
    <music21.harmony.ChordSymbol Cm/E->

    >>> cs.chordKind
    'minor'

    >>> cs.root()
    <music21.pitch.Pitch C4>

    >>> cs.bass()
    <music21.pitch.Pitch E-3>

    The second approach to creating a Chord Symbol object, by
    passing a regular expression (this list is not exhaustive):

    >>> symbols = ['', 'm', '+', 'dim', '7',
    ...            'M7', 'm7', 'dim7', '7+', 'm7b5',  # half-diminished
    ...            'mM7', '6', 'm6', '9', 'Maj9', 'm9',
    ...            '11', 'Maj11', 'm11', '13',
    ...            'Maj13', 'm13', 'sus2', 'sus4',
    ...            'N6', 'It+6', 'Fr+6', 'Gr+6', 'pedal',
    ...            'power', 'tristan', '/E', 'm7/E-', 'add2',
    ...            '7omit3',]
    >>> for s in symbols:
    ...     chordSymbolName = 'C' + s
    ...     h = harmony.ChordSymbol(chordSymbolName)
    ...     pitchNames = [str(p) for p in h.pitches]
    ...     print('%-10s%s' % (chordSymbolName, '[' + (', '.join(pitchNames)) + ']'))
    C         [C3, E3, G3]
    Cm        [C3, E-3, G3]
    C+        [C3, E3, G#3]
    Cdim      [C3, E-3, G-3]
    C7        [C3, E3, G3, B-3]
    CM7       [C3, E3, G3, B3]
    Cm7       [C3, E-3, G3, B-3]
    Cdim7     [C3, E-3, G-3, B--3]
    C7+       [C3, E3, G#3, B-3]
    Cm7b5     [C3, E-3, G-3, B-3]
    CmM7      [C3, E-3, G3, B3]
    C6        [C3, E3, G3, A3]
    Cm6       [C3, E-3, G3, A3]
    C9        [C3, E3, G3, B-3, D4]
    CMaj9     [C3, E3, G3, B3, D4]
    Cm9       [C3, E-3, G3, B-3, D4]
    C11       [C2, E2, G2, B-2, D3, F3]
    CMaj11    [C2, E2, G2, B2, D3, F3]
    Cm11      [C2, E-2, G2, B-2, D3, F3]
    C13       [C2, E2, G2, B-2, D3, F3, A3]
    CMaj13    [C2, E2, G2, B2, D3, F3, A3]
    Cm13      [C2, E-2, G2, B-2, D3, F3, A3]
    Csus2     [C3, D3, G3]
    Csus4     [C3, F3, G3]
    CN6       [C3, D-3, E3, G-3]
    CIt+6     [C3, F#3, A-3]
    CFr+6     [C3, D3, F#3, A-3]
    CGr+6     [C3, E-3, F#3, A-3]
    Cpedal    [C3]
    Cpower    [C3, G3]
    Ctristan  [C3, D#3, F#3, A#3]
    C/E       [E3, G3, C4]
    Cm7/E-    [E-3, G3, B-3, C4]
    Cadd2     [C3, D3, E3, G3]
    C7omit3   [C3, G3, B-3]

    You can also create a Chord Symbol by writing out each degree,
    and any alterations to that degree:
    You must explicitly indicate EACH degree (a triad is NOT necessarily implied)

    >>> [str(p) for p in harmony.ChordSymbol('C35b7b9#11b13').pitches]
    ['C2', 'E2', 'G2', 'D-3', 'F#3', 'A-3', 'B-3']

    >>> [str(p) for p in harmony.ChordSymbol('C35911').pitches]
    ['C2', 'E2', 'G2', 'D3', 'F3']

    to prevent ambiguity in notation...

    ...and in accordance with the rest of music21, if a root or bass is flat,
    the '-' must be used, and NOT 'b'. However, alterations and chord
    abbreviations are specified normally with the 'b' and '#' signs.

    >>> dFlat = harmony.ChordSymbol('D-35')
    >>> [str(p) for p in dFlat.pitches]
    ['D-3', 'F3', 'A-3']

    >>> [str(p) for p in harmony.ChordSymbol('Db35').pitches]
    ['D3', 'F3', 'A3']

    >>> [str(p) for p in harmony.ChordSymbol('D,35b7b9#11b13').pitches]
    ['D2', 'F#2', 'A2', 'E-3', 'G#3', 'B-3', 'C4']

    >>> harmony.ChordSymbol('Am').pitches
    (<music21.pitch.Pitch A2>, <music21.pitch.Pitch C3>, <music21.pitch.Pitch E3>)

    >>> harmony.ChordSymbol('A-m').pitches
    (<music21.pitch.Pitch A-2>, <music21.pitch.Pitch C-3>, <music21.pitch.Pitch E-3>)

    >>> harmony.ChordSymbol('A-m').pitches
    (<music21.pitch.Pitch A-2>, <music21.pitch.Pitch C-3>, <music21.pitch.Pitch E-3>)

    >>> harmony.ChordSymbol('F-dim7').pitches
    (<music21.pitch.Pitch F-2>, <music21.pitch.Pitch A--2>,
     <music21.pitch.Pitch C--3>, <music21.pitch.Pitch E---3>)

    Thanks to David Bolton for catching the bugs tested below:

    >>> [str(p) for p in harmony.ChordSymbol('C3579').pitches]
    ['C2', 'E2', 'G2', 'D3', 'B3']

    >>> [str(p) for p in harmony.ChordSymbol('C35b79').pitches]
    ['C2', 'E2', 'G2', 'D3', 'B-3']

    >>> [str(p) for p in harmony.ChordSymbol('C357b9').pitches]
    ['C2', 'E2', 'G2', 'D-3', 'B3']

    When bass is not in chord:

    >>> cs = harmony.ChordSymbol(root='E', bass='C', kind='diminished-seventh')

    >>> [str(p) for p in cs.pitches]
    ['C2', 'E3', 'G3', 'B-3', 'D-4']

    >>> cs.figure
    'Eo7/C'

    And now, and example of parsing in the wild:

    >>> s = corpus.parse('leadsheet/fosterBrownHair')
    >>> initialSymbols = s.flatten().getElementsByClass(harmony.ChordSymbol)[0:5]
    >>> [[str(c.name) for c in c.pitches] for c in initialSymbols]
    [['F', 'A', 'C'], ['B-', 'D', 'F'], ['F', 'A', 'C'], ['C', 'E', 'G'], ['F', 'A', 'C']]


    Test creating an empty chordSymbol:

    >>> cs = harmony.ChordSymbol()
    >>> cs
    <music21.harmony.ChordSymbol>
    >>> cs.root('E-')
    >>> cs.bass('B-', allow_add=True)

    important: we are not asking for transposition, merely specifying the inversion that
    the chord should be read in (transposeOnSet = False)

    >>> cs.inversion(2, transposeOnSet=False)

    >>> cs.romanNumeral = 'I64'
    >>> cs.chordKind = 'major'
    >>> cs.chordKindStr = 'M'
    >>> cs
    <music21.harmony.ChordSymbol E-/B->
    '''

    # INITIALIZER #

    def __init__(self,
                 figure=None,
                 root: pitch.Pitch | str | None = None,
                 bass: pitch.Pitch | str | None = None,
                 inversion: int | None = None,
                 kind='',
                 kindStr='',
                 **keywords
                 ):
        self.chordKind = kind  # a string from defined list of chord symbol harmonies
        self.chordKindStr = kindStr  # the presentation of the kind or label of symbol

        super().__init__(figure, root=root, bass=bass, inversion=inversion, **keywords)
        if 'duration' not in keywords and 'quarterLength' not in keywords:
            self.duration = duration.Duration(0)
        if self.chordKind or self.chordKindStr:
            self._updatePitches()

    # PRIVATE METHODS #

    def _adjustOctaves(self, pitches):
        if not isinstance(pitches, list):
            pitches = list(pitches)

        # do this for all ninth, thirteenth, and eleventh chords...
        # this must be done to get octave spacing right
        # possibly rewrite figured bass function with this integrated?
        ninths = ['dominant-ninth', 'major-ninth', 'minor-ninth']
        elevenths = ['dominant-11th', 'major-11th', 'minor-11th']
        thirteenths = ['dominant-13th', 'major-13th', 'minor-13th']

        if self.chordKind in ninths:
            pitches[1] = pitch.Pitch(pitches[1].name + str(pitches[1].octave + 1))
        elif self.chordKind in elevenths:
            pitches[1] = pitch.Pitch(pitches[1].name + str(pitches[1].octave + 1))
            pitches[3] = pitch.Pitch(pitches[3].name + str(pitches[3].octave + 1))

        elif self.chordKind in thirteenths:
            pitches[1] = pitch.Pitch(pitches[1].name + str(pitches[1].octave + 1))
            pitches[3] = pitch.Pitch(pitches[3].name + str(pitches[3].octave + 1))
            pitches[5] = pitch.Pitch(pitches[5].name + str(pitches[5].octave + 1))
        else:
            return pitches

        c = chord.Chord(pitches)
        c = c.sortDiatonicAscending()

        return list(c.pitches)

    def _adjustPitchesForChordStepModifications(self, pitches):
        '''
        degree-value element: indicates degree in chord, positive integers only

        degree-alter: indicates semitone alteration of degree, positive and negative integers only

        degree-type: `add`, `alter`, or `subtract`:
            if `add`:
                degree-alter is relative to a dominant chord (major and perfect
                intervals except for a minor seventh)
            if `alter` or `subtract`:
                degree-alter is relative to degree already in the chord based on its kind element


        FROM XML DOCUMENTATION

        The degree element is used to add, alter, or subtract
        individual notes in the chord. The degree-value element
        is a number indicating the degree of the chord (1 for
        the root, 3 for third, etc). The degree-alter element
        is like the alter element in notes: 1 for sharp, -1 for
        flat, etc. The degree-type element can be `add`, `alter`, or
        `subtract`. If the degree-type is `alter` or `subtract`, the
        degree-alter is relative to the degree already in the
        chord based on its kind element. If the degree-type is
        `add`, the degree-alter is relative to a dominant chord
        (major and perfect intervals except for a minor
        seventh). The print-object attribute can be used to
        keep the degree from printing separately when it has
        already taken into account in the text attribute of
        the kind element. The plus-minus attribute is used to
        indicate if plus and minus symbols should be used
        instead of sharp and flat symbols to display the degree
        alteration; it is `no` by default. The degree-value and
        degree-type text attributes specify how the value and
        type of the degree should be displayed.

        A harmony of kind "other" can be spelled explicitly by
        using a series of degree elements together with a root.
        '''
        from music21 import scale

        pitches = list(pitches)
        chordStepModifications = self.chordStepModifications
        if chordStepModifications is None:
            return pitches

        rootPitch = self.root()
        sc = scale.MajorScale(rootPitch)

        def typeAdd(hD):
            '''
            change the pitches list based on this chordStepModification, adding
            a pitch
            '''
            pitchToAppend = sc.pitchFromDegree(hD.degree, rootPitch)
            if hD.interval and hD.interval.semitones != 0:
                # added degrees are relative to dominant chords, which have all major degrees
                # except for the seventh which is minor, thus the transposition down one half step
                if hD.degree == 7 and self.chordKind is not None and self.chordKind != '':
                    pitchToAppend = pitchToAppend.transpose(-1)
                pitchToAppend = pitchToAppend.transpose(hD.interval)
            if hD.degree >= 7:
                pitchToAppend.octave = pitchToAppend.octave + 1

            degrees = self._degreesList

            if str(hD.degree) in degrees:
                for p in pitches:
                    if sc.getScaleDegreeFromPitch(p) == hD.degree:
                        pitches.remove(p)
                        pitches.append(pitchToAppend)
            else:
                pitches.append(pitchToAppend)
                # # for now I won't worry about the octave of the added note
                # # if self.bass() is not None:
                # #     p = sc.pitchFromDegree(hD.degree, self.bass())
                # # else:
                # #     p = sc.pitchFromDegree(hD.degree, self.root())
                # if hD.degree == 7 and self.chordKind is not None and self.chordKind != '':
                #     # don't know why anyone would want
                #     # to add a seventh to a dominant chord already
                #     # ...but according to documentation
                #     # added degrees are relative to dominant chords, which have all major degrees
                #     # except for the seventh which is minor, thus the transposition down
                #     # one half step
                #     p = p.transpose(-1)
                #     self._degreesList.append('-7')
                #     # degreeForList = '-7'
                # else:
                #     self._degreesList.append(hD.degree)
                #     # degreeForList = str(hD.degree)
                # # adjust the added pitch by degree-alter interval
                # if hD.interval:
                #     p = p.transpose(hD.interval)
                #     if hD.degree >= 7:
                #         p.octave = p.octave + 1
                # pitches.append(p)

        def typeSubtract(hD):
            '''
            change the pitches list based on this chordStepModification, removing a pitch
            '''
            degrees = self._degreesList
            if not degrees:
                return

            pitchFound = False
            for p, degree in zip(pitches, degrees):
                degree = degree.replace('-', '')
                degree = degree.replace('#', '')
                degree = degree.replace('A', '')  # A is for 'Altered'
                if hD.degree == int(degree):
                    pitches.remove(p)
                    pitchFound = True

                    for degreeString in self._degreesList:
                        if str(hD.degree) in degreeString:
                            self._degreesList.remove(degreeString)
                            break
                    # if hD.degree not in string,
                    # should we throw an exception???? for now yes, but maybe later we
                    # will be more lenient.
            if not pitchFound:
                raise ChordStepModificationException(
                    f'Degree not in specified chord: {hD.degree}')

        def typeAlter(hD):
            '''
            alter
            '''
            pitchFound = False
            degrees = self._degreesList

            for p, degree in zip(pitches, degrees):
                degree = degree.replace('-', '')
                degree = degree.replace('#', '')
                degree = degree.replace('A', '')  # A is for 'Altered'
                if hD.degree == int(degree):
                    # transpose by semitones (positive for up, negative for down)
                    p = p.transpose(hD.interval, inPlace=True)
                    pitchFound = True

                    # for degreeString in self._degreesList:
                    #     if str(hD.degree) in degreeString:
                    #         self._degreesList = self._degreesList.replace(
                    #                    degreeString, ('A' + str(hD.degree)))
                    #         # the 'A' stands for altered...
                    #         break
                    # # if hD.degree not in string:
                    # # should we throw an exception???? for now yes, but maybe later we should.
            if not pitchFound:
                raise ChordStepModificationException(
                    f'Degree not in specified chord: {hD.degree}')

        # main routines...
        for chordStepModification in chordStepModifications:
            if chordStepModification.modType == 'add':
                typeAdd(chordStepModification)
            elif chordStepModification.modType == 'subtract':
                typeSubtract(chordStepModification)
            elif chordStepModification.modType == 'alter':
                typeAlter(chordStepModification)

        return tuple(pitches)

    def _parseAddAlterSubtract(self, remaining: str, modType: str) -> str:
        '''
        Removes and parses the first instance of a given `modType` such as
        'add', 'alter', 'omit', or 'subtract'. Returns the unparsed remainder.

        >>> cs = harmony.ChordSymbol()
        >>> cs._parseAddAlterSubtract('add#9omit5', 'add')
        'omit5'
        >>> cs.chordStepModifications
        [<music21.harmony.ChordStepModification
            modType=add degree=9 interval=<music21.interval.Interval A1>>]
        '''
        degree: str = ''
        alter: int = 0
        startIndex: int = remaining.index(modType) + len(modType)

        # Remove modType
        remaining = remaining[startIndex:]

        if remaining[:1] == 'b':
            alter = -1
            remaining = remaining[1:]
        elif remaining[:1] == '#':
            alter = 1
            remaining = remaining[1:]
        # 11, 13, etc.
        if remaining[:2].isnumeric():
            degree = remaining[:2]
            remaining = remaining[2:]
        # 9, 6, 4, etc.
        elif remaining[0].isnumeric():
            degree = remaining[0]
            remaining = remaining[1:]
        if degree:
            if modType == 'omit':
                modType = 'subtract'
            self.addChordStepModification(
                ChordStepModification(modType, int(degree), alter), updatePitches=False)
        return remaining

    def _getKindFromShortHand(self, sH):
        originalsH = sH
        if 'add' in sH:
            sH = sH[0:sH.index('add')]
        if 'alter' in sH:
            sH = sH[0:sH.index('alter')]
        if 'omit' in sH:
            sH = sH[0:sH.index('omit')]
        if 'subtract' in sH:
            sH = sH[0:sH.index('subtract')]
        if '#' in sH and sH[sH.index('#') + 1].isdigit():
            sH = sH[0:sH.index('#')]
        if ('b' in sH and sH.index('b') < len(sH) - 1
                and sH[sH.index('b') + 1].isdigit()
                and 'ob9' not in sH and 'øb9' not in sH):
            sH = sH[0:sH.index('b')]
        for chordKind in CHORD_TYPES:
            for charString in getAbbreviationListGivenChordType(chordKind):
                if sH == charString:
                    self.chordKind = chordKind
                    return originalsH.replace(charString, '')
        return originalsH

    def _hasPitchAboveC4(self, pitches):
        for p in pitches:
            if p.diatonicNoteNum > 30:  # if there are pitches above middle C, bump the octave down
                return True
        return False

    def _hasPitchBelowA1(self, pitches):
        for p in pitches:
            if p.diatonicNoteNum < 13:  # anything below this is just obnoxious
                return True
        return False

    def _notationString(self):
        '''
        returns NotationString of ChordSymbolObject which dictates which scale
        degrees and how those scale degrees are altered in this chord.

        >>> h = harmony.ChordSymbol('F-dim7')
        >>> h._notationString()
        '1,-3,-5,--7'
        '''
        notationString = ''

        kind = self.chordKind
        if kind in CHORD_ALIASES:
            kind = CHORD_ALIASES[kind]

        if kind in CHORD_TYPES:
            notationString = getNotationStringGivenChordType(kind)
        else:
            notationString = ''

        degrees = notationString.replace(',', ' ')
        self._degreesList = degrees.split()

        return notationString

    def _parseFigure(self):
        '''
        Translate the figure string (regular expression) into a meaningful
        Harmony object by identifying the root, bass, inversion, kind, and
        kindStr.
        '''
        if self.figure == 'Chord Symbol Cannot Be Identified':
            return self.figure
        # remove spaces from prelim Figure...
        prelimFigure = self.figure
        prelimFigure = re.sub(r'\s', '', prelimFigure)
        # Get Root:
        if ',' in prelimFigure:
            root = prelimFigure[0:prelimFigure.index(',')]
            st = prelimFigure.replace(',', '')
            st = st.replace(root, '')
            prelimFigure = prelimFigure.replace(',', '')
        else:
            m1 = re.match(r'[A-Ga-g][#-]*', prelimFigure)  # match not case-sensitive,
            if m1:
                root = m1.group()
                # remove the root and bass from the string and any additions/omissions/alterations/
                st = prelimFigure.replace(m1.group(), '', 1)
            else:
                raise ValueError(f'Chord {prelimFigure} does not begin '
                                 + 'with a valid root note.')

        if root:
            self.root(pitch.Pitch(root))

        # Get optional Bass:
        m2 = re.search(r'/[A-Ga-g][#-]*', prelimFigure)  # match not case-sensitive
        remaining = st
        if m2:
            bass = m2.group()
            bass = bass.replace('/', '')
            self.bass(bass, allow_add=True)
            # remove the root and bass from the string
            remaining = st.replace(m2.group(), '')

        st = self._getKindFromShortHand(remaining)

        ALTER_TYPES = ('add', 'alter', 'omit', 'subtract')
        searchStart: int = 1000  # not -1 for the sake of min(), below
        for alterType in ALTER_TYPES:
            try:
                searchStart = min(remaining.index(alterType), searchStart)
            except ValueError:
                pass

        searchStringForAlterTypes: str = remaining[searchStart:]
        substring: str = ''
        i = 0
        while searchStringForAlterTypes and i < len(searchStringForAlterTypes):
            for char in searchStringForAlterTypes:
                i += 1
                if char.isalpha():
                    substring += char
                if substring in ALTER_TYPES:
                    searchStringForAlterTypes = self._parseAddAlterSubtract(
                        searchStringForAlterTypes, substring)
                    substring = ''
                    i = 0
                    break

        st = st.replace(',', '')
        # Unsafe to proceed until every alterType and anything following
        # is stripped from 'st'
        for alterType in ALTER_TYPES:
            if alterType in st:
                st = st[:st.index(alterType)]

        if 'b' in st or '#' in st:
            splitter = re.compile('([b#]+[^b#]+)')
            alterations = splitter.split(st)
        else:
            alterations = [st]
        indexes = []
        altCopy = []
        for itemString in alterations:
            if not itemString:
                continue
            justInts = itemString.replace('b', '')
            justInts = justInts.replace('#', '')
            try:
                justInts = int(justInts)
            except ValueError as ve:
                raise ValueError(
                    f'Invalid chord abbreviation {st!r}; see '
                    + 'music21.harmony.CHORD_TYPES for valid '
                    + 'abbreviations or specify all alterations.'
                ) from ve
            if justInts > 20:   # MSC: what is this doing?
                skipNext = False
                i = 0
                charString = ''
                for char in itemString:
                    if not skipNext:
                        if char == '1':
                            indexes.append(itemString[i] + itemString[i + 1])
                            skipNext = True
                        elif char in ('b', '#'):
                            charString = charString + char
                        else:
                            charString = charString + char
                            indexes.append(charString)
                            charString = ''
                    else:
                        skipNext = False
                    i = i + 1
            else:
                altCopy.append(itemString)
        for item in indexes:
            altCopy.append(item)
        alterations = altCopy
        degrees = []
        for alteration in alterations:
            if alteration != '':
                if 'b' in alteration:
                    semiToneAlter = -1 * alteration.count('b')
                else:
                    semiToneAlter = alteration.count('#')
                m3 = re.search(r'[1-9]+', alteration)
                if m3:
                    degrees.append([int(m3.group()), semiToneAlter])

        for degree, alterBy in degrees:
            self.addChordStepModification(
                ChordStepModification('add', degree, alterBy), updatePitches=False)

    def _updatePitches(self):
        '''
        TODO: EXTREMELY SLOW!

        Calculate the pitches in the chord symbol and update all associated
        variables, including bass, root, inversion and chord:

        >>> CS = harmony.ChordSymbol

        >>> [str(pi) for pi in CS(root='C', bass='E', kind='major').pitches]
        ['E3', 'G3', 'C4']

        >>> [str(pi) for pi in CS(root='C', bass='G', kind='major').pitches]
        ['G2', 'C3', 'E3']

        >>> [str(pi) for pi in CS(root='C', kind='minor').pitches]
        ['C3', 'E-3', 'G3']

        >>> [str(pi) for pi in CS(root='C', bass='B', kind='major-ninth').pitches]
        ['B2', 'C3', 'D3', 'E3', 'G3']

        >>> [str(pi) for pi in CS(root='D', bass='F', kind='minor-seventh').pitches]
        ['F3', 'A3', 'C4', 'D4']

        Note that this ChordSymbol creates what looks like a B- minor-seventh
        chord in first inversion, but is considered to be a D- chord in root
        position:

        >>> dFlatMaj6 = CS('D-6')
        >>> [str(pi) for pi in dFlatMaj6.pitches]
        ['D-3', 'F3', 'A-3', 'B-3']

        >>> dFlatMaj6.root()
        <music21.pitch.Pitch D-3>

        >>> dFlatMaj6.inversion()
        0

        OMIT_FROM_DOCS

        >>> CS('E7omit3').root().nameWithOctave
        'E3'
        >>> CS('E7omit5/G#').bass().nameWithOctave
        'G#2'
        >>> CS('E9omit5/G#').root().nameWithOctave
        'E3'
        >>> CS('E11omit3').root().nameWithOctave
        'E2'
        '''
        if 'root' not in self._overrides or 'bass' not in self._overrides or self.chordKind is None:
            return

        # create figured bass scale with root as scale
        scaleInitTuple = (self._overrides['root'].name, 'major')
        if scaleInitTuple in realizerScaleCache:
            fbScale = realizerScaleCache[scaleInitTuple]
        else:
            fbScale = realizerScale.FiguredBassScale(self._overrides['root'], 'major')
            realizerScaleCache[scaleInitTuple] = fbScale

        # render in the 3rd octave by default
        self._overrides['root'].octave = 3
        self._overrides['bass'].octave = 3

        if self._notationString():
            pitches = fbScale.getSamplePitches(self._overrides['root'], self._notationString())
            # remove duplicated bass note due to figured bass method.
            pitches.pop(0)
        else:
            pitches = []
            pitches.append(self._overrides['root'])
            if self._overrides['bass'] not in pitches:
                pitches.append(self._overrides['bass'])

        pitches = self._adjustOctaves(pitches)

        if self._overrides['root'].name != self._overrides['bass'].name:

            inversionNum = self.inversion()

            if not self.inversionIsValid(inversionNum):
                # there is a bass, yet no normal inversion was found: must be added note

                inversionNum = None
                # arbitrary octave, must be below root,
                # which was arbitrarily chosen as 3 above
                self._overrides['bass'].octave = 2
                pitches.append(self._overrides['bass'])
        else:
            self.inversion(None, transposeOnSet=False)
            inversionNum = None

        pitches = list(self._adjustPitchesForChordStepModifications(pitches))

        if inversionNum not in (0, None):
            for p in pitches[0:inversionNum]:
                p.octave = p.octave + 1
                # Repeat if 9th/11th/13th chord in 4th inversion or greater
                if inversionNum > 3:
                    p.octave = p.octave + 1

            # if after bumping up the octaves, there are still pitches below bass pitch
            # bump up their octaves
            # bassPitch = pitches[inversionNum]

            # self.bass(bassPitch)
            for p in pitches:
                if p.diatonicNoteNum < self._overrides['bass'].diatonicNoteNum:
                    p.octave = p.octave + 1

        while self._hasPitchAboveC4(pitches):
            for thisPitch in pitches:
                thisPitch.octave -= 1

        # but if this has created pitches below lowest note (the A 3 octaves below middle C)
        # on a standard piano, we're going to have to bump all the octaves back up
        while self._hasPitchBelowA1(pitches):
            for thisPitch in pitches:
                thisPitch.octave += 1

        self.pitches = tuple(pitches)
        self.sortDiatonicAscending(inPlace=True)

        # set overrides to be pitches in the harmony
        # self._overrides = {}  # JTW: was wiping legit overrides such as root=C from 'C6'
        self.bass(self.bass(), allow_add=True)
        self.root(self.root())

    # PUBLIC METHODS #

    def findFigure(self):
        '''
        Return the chord symbol figure associated with this chord.

        This method tries to deduce what information it can from the provided
        pitches.

        >>> h = harmony.ChordSymbol(root='F', bass='D-', kind='Neapolitan')
        >>> h.figure
        'FN6/D-'

        Thanks to Norman Schmidt for code sample and helping fix a bug

        >>> foster = corpus.parse('leadsheet/fosterBrownHair.xml')
        >>> foster = foster.parts[0].getElementsByClass(stream.Measure)
        >>> for m in foster[12:17]:
        ...   c = m.getElementsByClass(harmony.ChordSymbol)
        ...   if c:
        ...     ch = c[0].figure
        ...     print(ch.replace('-', 'b'))
        ...   else:
        ...     print('n.c.')
        F
        G7
        C
        C
        C

        Thanks to David Bolton for catching the bugs tested below:

        >>> h1 = harmony.ChordSymbol('C7 b9')
        >>> for x in h1.pitches:
        ...     x
        ...
        <music21.pitch.Pitch C3>
        <music21.pitch.Pitch E3>
        <music21.pitch.Pitch G3>
        <music21.pitch.Pitch B-3>
        <music21.pitch.Pitch D-4>

        >>> h2 = harmony.ChordSymbol('C/B- add 2')
        >>> for x in h2.pitches:
        ...     x
        ...
        <music21.pitch.Pitch B-2>
        <music21.pitch.Pitch C3>
        <music21.pitch.Pitch D3>
        <music21.pitch.Pitch E3>
        <music21.pitch.Pitch G3>

        OMIT_FROM_DOCS

        >>> from xml.etree.ElementTree import fromstring as EL
        >>> MP = musicxml.xmlToM21.MeasureParser()

        >>> elStr = (r'<harmony><root><root-step>C</root-step></root><kind>dominant</kind>' +
        ...           '<degree><degree-value>9</degree-value><degree-alter>-1</degree-alter>' +
        ...           '        <degree-type>add</degree-type></degree></harmony>')
        >>> mxHarmony = EL(elStr)

        >>> cs = MP.xmlToChordSymbol(mxHarmony)
        >>> print(cs.figure)
        C7 add b9

        >>> cs.pitches
        (<music21.pitch.Pitch C3>,
         <music21.pitch.Pitch E3>,
         <music21.pitch.Pitch G3>,
         <music21.pitch.Pitch B-3>,
         <music21.pitch.Pitch D-4>)

        >>> elStr = (r'<harmony><root><root-step>C</root-step></root><kind>major</kind>' +
        ...           '<bass><bass-step>B</bass-step><bass-alter>-1</bass-alter></bass>' +
        ...           '<degree><degree-value>2</degree-value><degree-alter>0</degree-alter>' +
        ...           '        <degree-type>add</degree-type></degree></harmony>')
        >>> mxHarmony = EL(elStr)

        >>> cs = MP.xmlToChordSymbol(mxHarmony)
        >>> print(cs.figure)
        C/B- add 2

        >>> cs.pitches
        (<music21.pitch.Pitch B-2>,
         <music21.pitch.Pitch C3>,
         <music21.pitch.Pitch D3>,
         <music21.pitch.Pitch E3>,
         <music21.pitch.Pitch G3>)
        '''
        if self.chordStepModifications or self.chordKind:
            # there is no hope to determine the chord from pitches
            # if it's been modified, so we'll just have to try this route:

            if self.root() is None:
                raise HarmonyException('Cannot find figure. No root to the chord found', self)

            figure = self.root().name
            kind = self.chordKind
            if kind in CHORD_ALIASES:
                kind = CHORD_ALIASES[kind]

            if kind in CHORD_TYPES:
                figure += getAbbreviationListGivenChordType(kind)[0]
            if self.bass() is not None:
                if self.root().name != self.bass().name:
                    figure += '/' + self.bass().name

            for csMod in self.chordStepModifications:
                if csMod.interval is not None:
                    numAlter = csMod.interval.semitones
                    if numAlter > 0:
                        s = '#'
                    else:
                        s = 'b'
                    prefix = s * abs(numAlter)

                    figure += ' ' + csMod.modType + ' ' + prefix + str(csMod.degree)
                else:
                    figure += ' ' + csMod.modType + ' ' + str(csMod.degree)

            return figure
        else:
            # if neither chordKind nor chordStepModifications, best bet is probably to
            # try to deduce the figure from the chord
            return chordSymbolFigureFromChord(self)

    def inversionIsValid(self, inversion):
        '''
        Returns true if the provided inversion exists for the given pitches of
        the chord. If not, it returns false and the getPitches method then
        appends the bass pitch to the chord.
        '''
        sevenths = (
            'French',
            'German',
            'Italian',
            'Neapolitan',
            'Tristan',
            'augmented-seventh',
            'diminished-seventh',
            'dominant-seventh',
            'half-diminished',
            'major-minor',
            'major-seventh',
            'minor-seventh',
        )
        ninths = (
            'dominant-ninth',
            'major-ninth',
            'minor-ninth',
        )
        elevenths = (
            'dominant-11th',
            'major-11th',
            'minor-11th',
        )
        thirteenths = (
            'dominant-13th',
            'major-13th',
            'minor-13th',
        )
        if inversion == 5 and (
            self.chordKind in thirteenths
            or self.chordKind in elevenths
        ):
            return True
        elif inversion == 4 and (
            self.chordKind in elevenths
            or self.chordKind in thirteenths
            or self.chordKind in ninths
        ):
            return True
        elif inversion == 3 and (
            self.chordKind in sevenths
            or self.chordKind in ninths
            or self.chordKind in elevenths
            or self.chordKind in thirteenths
        ):
            return True
        elif (inversion in (2, 1)
                and self.chordKind != 'pedal'):
            return True
        elif inversion is None:
            return False
        else:
            return False

    def transpose(self: T, value, *, inPlace=False) -> T | None:
        '''
        Overrides :meth:`~music21.chord.Chord.transpose` so that this ChordSymbol's
        `figure` is appropriately cleared afterward.

        >>> cs = harmony.ChordSymbol('Am')
        >>> cs.figure
        'Am'
        >>> cs.transpose(1)
        <music21.harmony.ChordSymbol B-m>
        >>> cs.transpose(5, inPlace=True)
        >>> cs
        <music21.harmony.ChordSymbol Dm>
        >>> cs.figure
        'Dm'
        '''
        post = super().transpose(value, inPlace=inPlace)
        if not inPlace:
            post.figure = None
            return post
        else:
            self.figure = None
            return None


class NoChord(ChordSymbol):
    '''
    Class representing a special 'no chord' ChordSymbol used to explicitly
    encode absence of chords. This is especially useful to stop a chord
    without playing another.

    >>> from music21.harmony import ChordSymbol, NoChord
    >>> s = stream.Score()
    >>> s.repeatAppend(note.Note('C'), 4)
    >>> s.append(ChordSymbol('C'))
    >>> s.repeatAppend(note.Note('C'), 4)
    >>> s.append(NoChord())
    >>> s.repeatAppend(note.Note('C'), 4)
    >>> s = s.makeMeasures()

    See how the chordSymbol of C stops at offset 8 rather
    than continuing, thanks to the NoChord object.

    >>> s = harmony.realizeChordSymbolDurations(s)
    >>> s.show('text', addEndTimes=True)
    {0.0 - 0.0} <music21.clef.BassClef>
    {0.0 - 0.0} <music21.meter.TimeSignature 4/4>
    {0.0 - 1.0} <music21.note.Note C>
    {1.0 - 2.0} <music21.note.Note C>
    {2.0 - 3.0} <music21.note.Note C>
    {3.0 - 4.0} <music21.note.Note C>
    {4.0 - 8.0} <music21.harmony.ChordSymbol C>
    {4.0 - 5.0} <music21.note.Note C>
    {5.0 - 6.0} <music21.note.Note C>
    {6.0 - 7.0} <music21.note.Note C>
    {7.0 - 8.0} <music21.note.Note C>
    {8.0 - 12.0} <music21.harmony.NoChord N.C.>
    {8.0 - 9.0} <music21.note.Note C>
    {9.0 - 10.0} <music21.note.Note C>
    {10.0 - 11.0} <music21.note.Note C>
    {11.0 - 12.0} <music21.note.Note C>
    {12.0 - 12.0} <music21.bar.Barline type=final>

    >>> c_major = s.getElementsByClass(ChordSymbol).first()
    >>> c_major.duration
    <music21.duration.Duration 4.0>
    >>> c_major.offset
    4.0

    Other text than the default of 'N.C.' can be given:

    >>> nc2 = NoChord('NC')
    >>> nc2
    <music21.harmony.NoChord NC>
    >>> nc2.pitches
    ()

    Note that even if the text is a valid chord abbreviation, no
    pitches are generated.  This feature may be useful for adding
    the appearance of ChordSymbols in a piece without having them
    be realized.

    >>> nc2 = NoChord('C7')
    >>> nc2
    <music21.harmony.NoChord C7>
    >>> nc2.pitches
    ()
    '''
    def __init__(self, figure=None, kind='none', kindStr=None, **keywords):
        super().__init__(figure, kind=kind, kindStr=kindStr or figure or 'N.C.', **keywords)

        if self._figure is None:
            self._figure = self.chordKindStr

    def root(self, newroot=None, *, find=None):
        # Ignore newroot, and set find to "False" to always return None
        return None

    def bass(self, newbass=None, *, find=None, allow_add=False):
        # Ignore newbass, and set find to "False" to always return None
        return None

    def _parseFigure(self):
        # do nothing, everything is already set.
        return

    def transpose(self: NCT, _value, *, inPlace=False) -> NCT | None:
        '''
        Overrides :meth:`~music21.chord.Chord.transpose` to do nothing.

        >>> nc = harmony.NoChord()
        >>> nc.figure
        'N.C.'
        >>> nc.transpose(8, inPlace=True)
        >>> nc.figure
        'N.C.'
        '''
        if not inPlace:
            return copy.deepcopy(self)
        else:
            return None


# ------------------------------------------------------------------------------


def realizeChordSymbolDurations(piece):
    '''
    Returns music21 stream with duration attribute of chord symbols correctly
    set. Duration of chord symbols is based on the surrounding chord symbols;
    The chord symbol continues duration until another chord symbol is located
    or the piece ends.

    >>> s = stream.Score()
    >>> s.append(harmony.ChordSymbol('C'))
    >>> s.repeatAppend(note.Note('C'), 4)
    >>> s.append(harmony.ChordSymbol('C'))
    >>> s.repeatAppend(note.Note('C'), 4)
    >>> s = s.makeMeasures()

    >>> harmony.realizeChordSymbolDurations(s).show('text')
    {0.0} <music21.clef.BassClef>
    {0.0} <music21.meter.TimeSignature 4/4>
    {0.0} <music21.harmony.ChordSymbol C>
    {0.0} <music21.note.Note C>
    {1.0} <music21.note.Note C>
    {2.0} <music21.note.Note C>
    {3.0} <music21.note.Note C>
    {4.0} <music21.harmony.ChordSymbol C>
    {4.0} <music21.note.Note C>
    {5.0} <music21.note.Note C>
    {6.0} <music21.note.Note C>
    {7.0} <music21.note.Note C>
    {8.0} <music21.bar.Barline type=final>

    If only one chord symbol object is present:

    >>> s = stream.Score()
    >>> s.append(harmony.ChordSymbol('C'))
    >>> s.repeatAppend(note.Note('C'), 4)
    >>> s = s.makeMeasures()
    >>> harmony.realizeChordSymbolDurations(s).show('text')
    {0.0} <music21.clef.BassClef>
    {0.0} <music21.meter.TimeSignature 4/4>
    {0.0} <music21.harmony.ChordSymbol C>
    {0.0} <music21.note.Note C>
    {1.0} <music21.note.Note C>
    {2.0} <music21.note.Note C>
    {3.0} <music21.note.Note C>
    {4.0} <music21.bar.Barline type=final>

    If a ChordSymbol object exists followed by many notes, duration represents
    all those notes (how else can the computer know to end the chord? if
    there's no chord following it other than end the chord at the end of the
    piece?).

    >>> s = stream.Score()
    >>> s.repeatAppend(note.Note('C'), 4)
    >>> s.append(harmony.ChordSymbol('C'))
    >>> s.repeatAppend(note.Note('C'), 8)
    >>> s = s.makeMeasures()
    >>> harmony.realizeChordSymbolDurations(s).show('text')
    {0.0} <music21.clef.BassClef>
    {0.0} <music21.meter.TimeSignature 4/4>
    {0.0} <music21.note.Note C>
    {1.0} <music21.note.Note C>
    {2.0} <music21.note.Note C>
    {3.0} <music21.note.Note C>
    {4.0} <music21.harmony.ChordSymbol C>
    {4.0} <music21.note.Note C>
    {5.0} <music21.note.Note C>
    {6.0} <music21.note.Note C>
    {7.0} <music21.note.Note C>
    {8.0} <music21.note.Note C>
    {9.0} <music21.note.Note C>
    {10.0} <music21.note.Note C>
    {11.0} <music21.note.Note C>
    {12.0} <music21.bar.Barline type=final>
    '''
    pf = piece.flatten()
    onlyChords = pf.getElementsByClass(ChordSymbol).stream()
    first = True
    lastChord = None

    if len(onlyChords) > 1:
        for cs in onlyChords:
            if first:
                first = False
                lastChord = cs
                continue
            else:
                qlDiff = pf.elementOffset(cs) - pf.elementOffset(lastChord)
                lastChord.duration.quarterLength = qlDiff

                if onlyChords.index(cs) == (len(onlyChords) - 1):
                    cs.duration.quarterLength = pf.highestTime - pf.elementOffset(cs)
                lastChord = cs
        return pf
    elif len(onlyChords) == 1:
        onlyChords[0].duration.quarterLength = pf.highestTime - pf.elementOffset(onlyChords[0])
        return pf
    else:
        return piece


# ------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def testChordAttributes(self):
        from music21 import harmony
        cs = harmony.ChordSymbol('Cm')
        self.assertEqual(str(cs), '<music21.harmony.ChordSymbol Cm>')
        self.assertEqual(
            str(cs.pitches),
            '(<music21.pitch.Pitch C3>, <music21.pitch.Pitch E-3>, <music21.pitch.Pitch G3>)')
        self.assertEqual(str(cs.bass()), 'C3')
        self.assertTrue(cs.isConsonant())

    def testBasic(self):
        from music21 import harmony
        h = harmony.Harmony()
        hd = harmony.ChordStepModification('add', 4)
        h.addChordStepModification(hd)
        self.assertEqual(len(h.chordStepModifications), 1)

    def testChordKindSetting(self):
        from music21 import harmony
        cs = harmony.ChordSymbol()
        cs.root('E-')
        cs.bass('B-', allow_add=True)
        cs.inversion(2, transposeOnSet=False)
        cs.romanNumeral = 'I64'
        cs.chordKind = 'major'
        cs.chordKindStr = 'M'
        self.assertEqual(repr(cs), '<music21.harmony.ChordSymbol E-/B->')

    def testDoubleSharpsEtc(self):
        # noinspection SpellCheckingInspection
        cisisdim = chord.Chord(('c##5', 'e#5', 'g#5'))
        fig = chordSymbolFigureFromChord(cisisdim)
        self.assertEqual(fig, 'C##dim')

    def testChordSymbolSetsBassOctave(self):
        d = ChordSymbol('Cm/E-')
        root = d.root()
        self.assertEqual(root.nameWithOctave, 'C4')
        b = d.bass()
        self.assertEqual(b.nameWithOctave, 'E-3')

    def testClassSortOrderHarmony(self):
        '''
        This tests a former bug in getContextByClass
        because ChordSymbol used to have the same `.classSortOrder`
        as Note.
        '''
        from music21 import note
        from music21 import stream

        cs = ChordSymbol('C')
        n = note.Note('C')
        m = stream.Measure(1)

        m.insert(0, n)
        m.insert(0, cs)
        self.assertIs(n.getContextByClass('ChordSymbol'), cs)

        # check that it works also with append
        cs = ChordSymbol('C')
        n = note.Note('C')
        n.duration.quarterLength = 0
        m = stream.Measure(1)
        m.append(n)
        m.append(cs)
        self.assertIs(n.getContextByClass('ChordSymbol'), cs)

    def testNoChord(self):
        from music21 import harmony
        nc = harmony.NoChord()
        self.assertEqual('none', nc.chordKind)
        self.assertEqual('N.C.', nc.chordKindStr)
        self.assertEqual('N.C.', nc.figure)

        nc = harmony.NoChord('NC')
        self.assertEqual('none', nc.chordKind)
        self.assertEqual('NC', nc.chordKindStr)
        self.assertEqual('NC', nc.figure)

        nc = harmony.NoChord('None')
        self.assertEqual('none', nc.chordKind)
        self.assertEqual('None', nc.chordKindStr)
        self.assertEqual('None', nc.figure)

        nc = harmony.NoChord(kind='none')
        self.assertEqual('none', nc.chordKind)
        self.assertEqual('N.C.', nc.chordKindStr)
        self.assertEqual('N.C.', nc.figure)

        nc = harmony.NoChord(kindStr='No Chord')
        self.assertEqual('none', nc.chordKind)
        self.assertEqual('No Chord', nc.chordKindStr)
        self.assertEqual('No Chord', nc.figure)

        nc = harmony.NoChord('NC', kindStr='No Chord')
        self.assertEqual('none', nc.chordKind)
        self.assertEqual('No Chord', nc.chordKindStr)
        self.assertEqual('NC', nc.figure)

        nc = harmony.NoChord(root='C', bass='E', kind='none')
        self.assertEqual('N.C.', nc.chordKindStr)
        self.assertEqual('N.C.', nc.figure)

        self.assertEqual(str(nc), '<music21.harmony.NoChord N.C.>')
        self.assertEqual(0, len(nc.pitches))
        self.assertIsNone(nc.root())
        self.assertIsNone(nc.bass())

        nc._updatePitches()
        self.assertEqual(0, len(nc.pitches))

    def testInvalidRoots(self):
        from music21 import harmony
        with self.assertRaises(ValueError) as context:
            harmony.ChordSymbol('H-7')

        self.assertEqual(
            str(context.exception),
            'Chord H-7 does not begin with a valid root note.'
        )

        with self.assertRaises(ValueError) as context:
            # noinspection SpellCheckingInspection
            harmony.ChordSymbol('Garg7')

        self.assertEqual(
            str(context.exception),
            "Invalid chord abbreviation 'arg7'; see "
            + 'music21.harmony.CHORD_TYPES for valid '
            + 'abbreviations or specify all alterations.'
        )

    def testInvalidSymbol(self):
        from music21 import harmony
        c = chord.Chord(('A#', 'C', 'E'))
        cs = harmony.chordSymbolFromChord(c)
        self.assertEqual(cs.figure, 'Chord Symbol Cannot Be Identified')

    def testRegexEdgeCases(self):
        cs = ChordSymbol('FFr+6')
        self.assertEqual([p.name for p in cs.pitches], ['F', 'G', 'B', 'D-'])
        cs = ChordSymbol('dadd6')
        self.assertEqual([p.name for p in cs.pitches], ['D', 'F#', 'A', 'B'])
        cs = ChordSymbol('atristan')
        self.assertEqual([p.name for p in cs.pitches], ['A', 'B#', 'D#', 'F##'])


    def runTestOnChord(self, xmlString, figure, pitches):
        '''
        Run a series of tests on the given chord.

        xmlString: an XML harmony object

        figure: the equivalent figure representation

        pitches: the list of pitches of the chord
        '''
        from xml.etree.ElementTree import fromstring as EL
        from music21 import musicxml

        pitches = tuple(pitch.Pitch(p) for p in pitches)

        MP = musicxml.xmlToM21.MeasureParser()
        mxHarmony = EL(xmlString)

        cs1 = MP.xmlToChordSymbol(mxHarmony)
        cs2 = ChordSymbol(cs1.figure)
        cs3 = ChordSymbol(figure)

        self.assertEqual(pitches, cs1.pitches)
        self.assertEqual(pitches, cs2.pitches)
        self.assertEqual(pitches, cs3.pitches)

        kind1 = cs1.chordKind
        kind2 = cs2.chordKind
        kind3 = cs3.chordKind
        if kind1 in CHORD_ALIASES:
            kind1 = CHORD_ALIASES[kind1]
        if kind2 in CHORD_ALIASES:
            kind2 = CHORD_ALIASES[kind2]
        if kind3 in CHORD_ALIASES:
            kind3 = CHORD_ALIASES[kind3]
        self.assertEqual(kind1, kind2)
        self.assertEqual(kind1, kind3)

        self.assertEqual(cs1.root(), cs2.root())
        self.assertEqual(cs1.root(), cs3.root())

        self.assertEqual(cs1.bass(), cs2.bass())
        self.assertEqual(cs1.bass(), cs3.bass())

    def testChordWithBass(self):

        xmlString = '''
          <harmony>
            <root>
              <root-step>A</root-step>
            </root>
            <kind text="7">dominant</kind>
            <inversion>3</inversion>
            <bass>
              <bass-step>G</bass-step>
            </bass>
          </harmony>
          '''
        figure = 'A7/G'
        pitches = ('G2', 'A2', 'C#3', 'E3')

        self.runTestOnChord(xmlString, figure, pitches)

    def testChordFlatSharpInFigure(self):
        # Octave placement of this A2 neither great nor intolerable
        pitches = ('G2', 'A2', 'B2', 'D#3', 'F3')
        figure = 'G+9'
        cs = ChordSymbol(figure)
        self.assertEqual(cs.pitches, tuple(pitch.Pitch(p) for p in pitches))

        pitches = ('G2', 'B2', 'D#3', 'F3', 'A3')
        figure = 'G9#5'
        cs = ChordSymbol(figure)
        self.assertEqual(cs.pitches, tuple(pitch.Pitch(p) for p in pitches))

        pitches = ('A2', 'C3', 'E3', 'G#3')
        pitches = tuple(pitch.Pitch(p) for p in pitches)
        self.assertEqual(pitches, ChordSymbol('AmM7').pitches)
        self.assertEqual(pitches, ChordSymbol('Aminmaj7').pitches)
        pitches = ('A1', 'C2', 'E2', 'G#3')
        pitches = tuple(pitch.Pitch(p) for p in pitches)
        self.assertEqual(pitches, ChordSymbol('Am#7').pitches)

    def testRootBassParsing(self):
        '''
        This tests a bug where the root and bass were wrongly parsed,
        since the matched root and bass were globally removed from figure,
        and not only where matched.
        '''

        xmlString = '''
          <harmony>
            <root>
              <root-step>E</root-step>
            </root>
            <kind text="7">dominant</kind>
            <bass>
              <bass-step>E</bass-step>
              <bass-alter>-1</bass-alter>
            </bass>
          </harmony>
        '''
        figure = 'E7/E-'
        pitches = ('E-2', 'E3', 'G#3', 'B3', 'D4')
        self.runTestOnChord(xmlString, figure, pitches)


    def testChordStepBass(self):
        '''
        This tests a bug where the chord modification (add 2) was placed at a
        wrong octave, resulting in a D bass instead of the proper E.
        '''

        xmlString = '''
          <harmony>
            <root>
              <root-step>C</root-step>
            </root>
            <kind>major</kind>
            <bass>
              <bass-step>E</bass-step>
            </bass>
            <degree>
              <degree-value>2</degree-value>
              <degree-alter>0</degree-alter>
              <degree-type text="add">add</degree-type>
            </degree>
          </harmony>
           '''
        figure = 'C/E add 2'
        pitches = ('E3', 'G3', 'C4', 'D4')

        self.runTestOnChord(xmlString, figure, pitches)

    def testSusBass(self):
        '''
        This tests a bug where the bass addition was considered as the fifth
        inversion in suspended chords. Now, this is considered as a non-valid
        inversion, and the bass is simply added before the root.
        '''
        from xml.etree.ElementTree import fromstring as EL
        from music21 import musicxml

        pitches = ('G2', 'D3', 'G3', 'A3')
        pitches = tuple(pitch.Pitch(p) for p in pitches)

        xmlString = '''
          <harmony>
            <root>
              <root-step>D</root-step>
            </root>
            <kind text="sus">suspended-fourth</kind>
            <bass>
              <bass-step>G</bass-step>
            </bass>
          </harmony>
         '''

        MP = musicxml.xmlToM21.MeasureParser()
        mxHarmony = EL(xmlString)

        cs1 = MP.xmlToChordSymbol(mxHarmony)
        cs2 = ChordSymbol(cs1.figure)
        cs3 = ChordSymbol('Dsus/G')

        self.assertEqual(pitches, cs1.pitches)
        self.assertEqual(pitches, cs2.pitches)
        self.assertEqual(pitches, cs3.pitches)

    def testBassNotInChord(self):
        from xml.etree.ElementTree import fromstring as EL
        from music21 import musicxml

        pitches = ('E-3', 'E3', 'G3', 'C4')
        pitches = tuple(pitch.Pitch(p) for p in pitches)

        xmlString = '''
          <harmony>
            <root>
              <root-step>C</root-step>
            </root>
            <kind text="">major</kind>
            <bass>
              <bass-step>E-</bass-step>
            </bass>
          </harmony>
         '''

        MP = musicxml.xmlToM21.MeasureParser()
        mxHarmony = EL(xmlString)

        cs1 = MP.xmlToChordSymbol(mxHarmony)
        cs2 = ChordSymbol(cs1.figure)
        cs3 = ChordSymbol('C/E-')

        self.assertEqual(pitches, cs1.pitches)
        self.assertEqual(pitches, cs2.pitches)
        self.assertEqual(pitches, cs3.pitches)

        # There was a bug where the bass was E3, because E-3 was assumed to be
        # in the chord.
        self.assertEqual('E-3', cs1.bass().nameWithOctave)

    def testSus2Bass(self):
        from xml.etree.ElementTree import fromstring as EL
        from music21 import musicxml

        pitches = ('E3', 'G3', 'C4', 'D4')
        pitches = tuple(pitch.Pitch(p) for p in pitches)

        xmlString = '''
          <harmony>
            <root>
              <root-step>C</root-step>
            </root>
            <kind text="sus2">suspended-second</kind>
            <bass>
              <bass-step>E</bass-step>
            </bass>
          </harmony>
       '''

        MP = musicxml.xmlToM21.MeasureParser()
        mxHarmony = EL(xmlString)

        cs1 = MP.xmlToChordSymbol(mxHarmony)
        cs2 = ChordSymbol(cs1.figure)
        cs3 = ChordSymbol('Csus2/E')

        self.assertEqual('E3', cs1.bass().nameWithOctave)

        self.assertEqual(pitches, cs1.pitches)
        self.assertEqual(pitches, cs2.pitches)
        self.assertEqual(pitches, cs3.pitches)

    def testNinth(self):
        '''
        This tests a bug in _adjustOctaves.
        '''

        xmlString = '''
        <harmony >
            <root>
              <root-step>D</root-step>
            </root>
            <kind text="min9">minor-ninth</kind>
        </harmony>
           '''
        pitches = ('D2', 'F2', 'A2', 'C3', 'E3')
        figure = 'Dm9'

        self.runTestOnChord(xmlString, figure, pitches)

    def testInversion(self):
        from xml.etree.ElementTree import fromstring as EL
        from music21 import musicxml

        xmlString = '''
        <harmony>
          <root>
            <root-step>C</root-step>
          </root>
          <kind>major</kind>
          <inversion>1</inversion>
        </harmony>
        '''

        pitches = ('E2', 'G2', 'C3')
        pitches = tuple(pitch.Pitch(p) for p in pitches)

        MP = musicxml.xmlToM21.MeasureParser()
        mxHarmony = EL(xmlString)

        cs1 = MP.xmlToChordSymbol(mxHarmony)
        cs2 = ChordSymbol('C/E')

        self.assertEqual(1, cs1.inversion())
        self.assertEqual(1, cs2.inversion())

        pitches = ('E3', 'G3', 'C4')
        pitches = tuple(pitch.Pitch(p) for p in pitches)
        self.assertEqual(cs1.pitches, pitches)
        self.assertEqual(cs2.pitches, pitches)

        self.assertEqual(cs1.root(), cs2.root())
        self.assertEqual(cs1.bass(), cs2.bass())

    def testChordWithoutKind(self):
        cs = ChordSymbol(root='C', bass='E')

        self.assertEqual(1, cs.inversion())
        self.assertEqual('C4', str(cs.root()))
        self.assertEqual('E3', str(cs.bass()))


    def testChordStepFromFigure(self):
        xmlString = '''
          <harmony>
            <root>
              <root-step>G</root-step>
            </root>
            <kind text="7alt">dominant</kind>
            <degree>
              <degree-value>5</degree-value>
              <degree-alter>0</degree-alter>
              <degree-type>subtract</degree-type>
            </degree>
            <degree>
              <degree-value>9</degree-value>
              <degree-alter>-1</degree-alter>
              <degree-type>add</degree-type>
            </degree>
            <degree>
              <degree-value>9</degree-value>
              <degree-alter>1</degree-alter>
              <degree-type>add</degree-type>
            </degree>
            <degree>
              <degree-value>11</degree-value>
              <degree-alter>1</degree-alter>
              <degree-type>add</degree-type>
            </degree>
            <degree>
              <degree-value>13</degree-value>
              <degree-alter>-1</degree-alter>
              <degree-type>add</degree-type>
            </degree>
          </harmony>
        '''
        figure = 'G7 subtract 5 add b9 add #9 add #11 add b13'
        pitches = ('G2', 'B2', 'F3', 'A-3', 'A#3', 'C#4', 'E-4')
        self.runTestOnChord(xmlString, figure, pitches)

        figure = 'G7 subtract5 addb9 add#9 add#11 addb13'
        self.runTestOnChord(xmlString, figure, pitches)

        figure = 'G7subtract5addb9add#9add#11addb13'
        self.runTestOnChord(xmlString, figure, pitches)

        #########

        xmlString = '''
            <harmony>
            <root>
              <root-step>C</root-step>
            </root>
            <kind text="7b9">dominant</kind>
            <degree>
              <degree-value>9</degree-value>
              <degree-alter>-1</degree-alter>
              <degree-type>add</degree-type>
            </degree>
          </harmony>
        '''
        figure = 'C7 b9'
        pitches = ('C3', 'E3', 'G3', 'B-3', 'D-4')

        self.runTestOnChord(xmlString, figure, pitches)

        figure = 'C7 add b9'
        self.runTestOnChord(xmlString, figure, pitches)

        # Test alter
        cs = ChordSymbol('A7 alter #5')
        self.assertEqual('(<music21.pitch.Pitch A2>, <music21.pitch.Pitch '
                         'C#3>, <music21.pitch.Pitch E#3>, '
                         '<music21.pitch.Pitch G3>)', str(cs.pitches))

        #########

        xmlString = '''
          <harmony>
            <root>
              <root-step>A</root-step>
              </root>
            <kind>dominant</kind>
            <degree>
              <degree-value>5</degree-value>
              <degree-alter>1</degree-alter>
              <degree-type>alter</degree-type>
              </degree>
            <degree>
              <degree-value>9</degree-value>
              <degree-alter>1</degree-alter>
              <degree-type>add</degree-type>
              </degree>
            <degree>
              <degree-value>11</degree-value>
              <degree-alter>1</degree-alter>
              <degree-type>add</degree-type>
              </degree>
            </harmony>
        '''
        figure = 'A7 alter #5 add #9 add #11'
        pitches = ('A2', 'C#3', 'E#3', 'G3', 'B#3', 'D#4')

        self.runTestOnChord(xmlString, figure, pitches)

    def testExpressSusUsingAlterations(self):
        ch1 = ChordSymbol('F7 add 4 subtract 3')
        ch2 = ChordSymbol('F7sus4')

        self.assertEqual(ch1.pitches, ch2.pitches)

    def x_testPower(self):
        '''
        power chords should not have inversions
        '''
        pitches = ('E2', 'A2', 'E3')
        pitches = tuple(pitch.Pitch(p) for p in pitches)

        xmlString = '''
          <harmony>
            <root>
              <root-step>A</root-step>
            </root>
            <kind text="5">power</kind>
            <bass>
              <bass-step>E</bass-step>
            </bass>
          </harmony>
        '''
        figure = 'Apower/E'

        self.runTestOnChord(xmlString, figure, pitches)

    def testSingleChordSymbol(self):
        '''
        Test an edge case where a Stream contains only one ChordSymbol
        at the highest offset: should still have a nonzero duration
        if there is a subsequent highest time.
        '''
        from music21 import note
        from music21 import stream

        m = stream.Measure()  # NB: no barline!
        cs = ChordSymbol('A7')
        m.insert(0, note.Note(type='whole'))
        m.insert(1.0, cs)
        realizeChordSymbolDurations(m)
        self.assertEqual(cs.quarterLength, 3.0)


class TestExternal(unittest.TestCase):

    def testReadInXML(self):
        from music21 import harmony
        from music21 import corpus
        from music21 import stream
        testFile = corpus.parse('leadSheet/fosterBrownHair.xml')

        # testFile.show('text')
        testFile = harmony.realizeChordSymbolDurations(testFile)
        # testFile.show()
        chordSymbols = testFile.flatten().getElementsByClass(harmony.ChordSymbol)
        s = stream.Stream()

        for cS in chordSymbols:
            cS.writeAsChord = False
            s.append(cS)

        # csChords = s.flatten().getElementsByClass(chord.Chord)
        # s.show()
        # self.assertEqual(len(csChords), 40)

    def testChordRealization(self):
        from music21 import harmony
        from music21 import corpus
        from music21 import note
        from music21 import stream
        # There is a test file under demos called ComprehensiveChordSymbolsTestFile.xml
        # that should contain a complete iteration of tests of chord symbol objects
        # this test makes sure that no error exists, and checks that 57 chords were
        # created out of that file....feel free to add to file if you find missing
        # tests, and adjust 57 accordingly
        testFile = corpus.parse('demos/ComprehensiveChordSymbolsTestFile.xml')

        testFile = harmony.realizeChordSymbolDurations(testFile)
        chords = testFile.flatten().getElementsByClass(harmony.ChordSymbol)
        # testFile.show()
        s = stream.Stream()
        # i = 0
        for x in chords:
            # print(x.pitches)
            x.quarterLength = 0
            s.insert(x.offset, x)
            # i += 4
            #
            # x.show()

        s.makeRests(fillGaps=True, inPlace=True)
        s.append(note.Rest(quarterLength=4))
        unused_csChords = s.flatten().getElementsByClass(chord.Chord)
        # self.assertEqual(len(csChords), 57)
        # s.show()
        # s.show('text')

    def testALLChordKinds(self):
        notes = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
        mod = ['', '-', '#']
        for n in notes:
            for m in mod:
                for unused_key, val in CHORD_TYPES.items():
                    # example val = ['1,-3,5,6', ['m6', 'min6']]
                    for harmony_type in val[1]:
                        symbol = n + m + harmony_type
                        ChordSymbol(symbol)

    # def labelChordSymbols(self):
    #     '''
    #     A very rough sketch of code to label the chord symbols in a bach
    #     chorale (in response to a post to the music21 list asking if this is
    #     possible).
    #     '''
    #     from music21.alpha.theoryAnalysis import theoryAnalyzer
    #     from music21 import harmony, corpus
    #
    #     score = corpus.parse('bach/bwv380')
    #     excerpt = score.measures(2, 3)
    #
    #     # remove passing and/or neighbor tones?
    #     analyzer = theoryAnalyzer.Analyzer()
    #     analyzer.removePassingTones(excerpt)
    #     analyzer.removeNeighborTones(excerpt)
    #
    #     slices = analyzer.getVerticalities(excerpt)
    #     for vs in slices:
    #         x = harmony.chordSymbolFigureFromChord(vs.getChord())
    #         if x  != 'Chord Symbol Cannot Be Identified':
    #             vs.lyric = x.replace('-', 'b')
    #         print(x.replace('-', 'b'))


# ------------------------------------------------------------------------------


_DOC_ORDER = [Harmony, chordSymbolFigureFromChord, ChordSymbol, ChordStepModification]


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)  # , runTest='testChordStepBass')

