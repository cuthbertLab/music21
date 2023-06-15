# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         chord.py
# Purpose:      Chord representation and utilities
#
# Authors:      Michael Scott Asato Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2023 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
This module defines the Chord object, a subclass of :class:`~music21.note.GeneralNote`
as well as other methods, functions, and objects related to chords.
'''
from __future__ import annotations

__all__ = ['tools', 'tables', 'Chord', 'ChordException', 'fromIntervalVector', 'fromForteClass']

from collections.abc import Iterable, Sequence
import copy
import typing as t
from typing import overload  # pycharm bug
import unittest

from music21 import beam
from music21 import common
from music21.common.decorators import cacheMethod
from music21 import derivation
from music21.duration import Duration
from music21 import environment
from music21 import exceptions21
from music21 import interval
from music21 import note
from music21 import pitch
from music21 import tie
from music21 import volume

from music21.chord import tables
from music21.chord import tools


if t.TYPE_CHECKING:
    from music21 import stream


environLocal = environment.Environment('chord')

_ChordBaseType = t.TypeVar('_ChordBaseType', bound='music21.chord.ChordBase')
_ChordType = t.TypeVar('_ChordType', bound='music21.chord.Chord')

# ------------------------------------------------------------------------------
class ChordException(exceptions21.Music21Exception):
    pass


# ------------------------------------------------------------------------------
class ChordBase(note.NotRest):
    '''
    A base class for NotRest objects that have multiple underlying structures
    like notes or unpitched percussion.

    As of Version 7, ChordBase lies between Chord and NotRest in the music21
    hierarchy, so that features can be shared with PercussionChord.

    >>> cb = chord.ChordBase('C4 E4 G4')
    >>> cb.notes
    (<music21.note.Note C>, <music21.note.Note E>, <music21.note.Note G>)


    **Equality**

    Equality on ChordBase is strange, but necessary to help Chord and PercussionChord
    do meaningful equality checks themselves.

    Two ChordBase objects are equal if they pass all `super()`
    equality tests and the **number** of stored Notes are the same.

    >>> cb1 = chord.ChordBase('C4 E4 G4')
    >>> cb2 = chord.ChordBase('C4 E4')
    >>> cb1 == cb2
    False

    This is surprising, but it's necessary to make checking equality
    of Chord objects and PercussionChord objects themselves easier.

    >>> cb3 = chord.ChordBase('A#4 A#4 A#4')
    >>> cb1 == cb3
    True
    '''
    isNote = False
    isRest = False

    _DOC_ATTR: dict[str, str] = {
        'isNote': '''
            Boolean read-only value describing if this
            GeneralNote object is a Note. Is False''',
        'isRest': r'''
            Boolean read-only value describing if this
            GeneralNote object is a Rest. Is False

            >>> c = chord.Chord()
            >>> c.isRest
            False
            ''',
        'beams': 'A :class:`music21.beam.Beams` object.',
    }

    # update inherited _DOC_ATTR dictionary
    _DOC_ATTR.update(note.NotRest._DOC_ATTR)

    def __init__(self,
                 notes: t.Union[None,
                                str,
                                Sequence[str],
                                Sequence[pitch.Pitch],
                                Sequence[ChordBase],
                                Sequence[note.NotRest],
                                Sequence[int]] = None,
                 **keywords):

        if notes is None:
            notes = []

        if isinstance(notes, str):
            if ' ' in notes:
                notes = notes.split()
            else:
                notes = [notes]

        # the list of pitch objects is managed by a property; this permits
        # only updating the _chordTablesAddress when ".pitches" has changed

        self._overrides: dict[str, t.Any] = {}

        self._notes: list[note.NotRest] = []
        # here, pitch and duration data is extracted from notes
        # if provided.

        super().__init__(**keywords)

        # inherit Duration object from GeneralNote
        # keep it here in case we have no notes
        durationKeyword = None
        if 'duration' in keywords:
            durationKeyword = keywords['duration']

        durationKeyword = self._add_core_or_init(notes, useDuration=durationKeyword)

        if durationKeyword is not None:
            self.duration = durationKeyword
        elif 'type' in keywords or 'quarterLength' in keywords:  # dots dont cut it
            self.duration = Duration(**keywords)


    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        if not len(self.notes) == len(other.notes):
            return False
        return True

    def __hash__(self):
        return super().__hash__()

    def __deepcopy__(self: _ChordBaseType, memo=None) -> _ChordBaseType:
        '''
        As Chord objects have one or more Volume, objects, and Volume
        objects store weak refs to the client object, need to specialize
        deepcopy handling depending on if the chord has its own volume object.
        '''
        # environLocal.printDebug(['calling NotRest.__deepcopy__', self])
        # as this inherits from NotRest, can use that __deepcopy__ as basis
        # that looks only to _volume to see if it is not None; with a
        # Chord, _volume will always be None
        new = super().__deepcopy__(memo=memo)
        # after copying, if a Volume exists, it is linked to the old object
        # look at _volume so as not to create object if not already there
        # noinspection PyProtectedMember
        for n in new._notes:  # pylint: disable=no-member
            n._chordAttached = new
            # if .volume is called, a new Volume obj will be created
            if n.hasVolumeInformation():
                n.volume.client = new  # update with new instance
        return new

    # TODO: __getitem__

    def __iter__(self):
        return iter(self._notes)

    def __len__(self):
        '''
        Return the length of components in the chord.

        >>> c = chord.Chord(['c', 'e', 'g'])
        >>> len(c)
        3
        '''
        return len(self._notes)

    def _add_core_or_init(self,
                          notes,
                          *,
                          useDuration: None | t.Literal[False] | Duration = None):
        '''
        This is the private append method called by .add and called by __init__.

        It differs from the public method in that a duration object can
        be passed in which is used for the first note of the chord or as many pitches
        as can use it -- it's all an optimization step to create as few duration objects
        as is necessary.

        Does not clear any caches.

        Also requires that notes be iterable.

        Changed in v9: incorrect arguments raise TypeError
        '''
        # quickDuration specifies whether the duration object for the chord
        # should be taken from the first note of the list.
        quickDuration = False
        if useDuration is None:
            useDuration = self.duration
            quickDuration = True

        newNote: note.NotRest
        for n in notes:
            if isinstance(n, pitch.Pitch):
                # assign pitch to a new Note
                if useDuration:  # not False or None
                    newNote = note.Note(n, duration=useDuration)
                else:
                    newNote = note.Note(n)
                self._notes.append(newNote)
                # self._notes.append({'pitch':n})
            elif isinstance(n, ChordBase):
                for newNote in n._notes:
                    self._notes.append(copy.deepcopy(newNote))
                if quickDuration is True:
                    self.duration = n.duration
                    useDuration = None
                    quickDuration = False
            elif isinstance(n, note.NotRest):
                self._notes.append(n)
                if quickDuration is True:
                    self.duration = n.duration
                    useDuration = None
                    quickDuration = False
            elif isinstance(n, (str, int)):
                if useDuration:
                    self._notes.append(note.Note(n, duration=useDuration))
                else:
                    self._notes.append(note.Note(n))
                # self._notes.append({'pitch':music21.pitch.Pitch(n)})
            else:
                raise TypeError(f'Could not process input argument {n}')

        for n in self._notes:
            # noinspection PyProtectedMember
            n._chordAttached = self

        return useDuration

    def add(
        self,
        notes,
    ) -> None:
        '''
        Add a Note, Pitch, the `.notes` of another chord,
        or string representing a Pitch,
        or a list of any-of-the-above types to a Chord or PercussionChord.

        Does no sorting.  That is on the Chord object.

        >>> c = chord.Chord('C4 E4 G4')
        >>> c.add('B3')
        >>> c
        <music21.chord.Chord B3 C4 E4 G4>
        >>> c.duration
        <music21.duration.Duration 1.0>

        >>> c.add('A2', runSort=False)
        >>> c
        <music21.chord.Chord B3 C4 E4 G4 A2>

        >>> c.add(['B5', 'C6'])
        >>> c
        <music21.chord.Chord A2 B3 C4 E4 G4 B5 C6>

        >>> c.add(pitch.Pitch('D6'))
        >>> c
        <music21.chord.Chord A2 B3 C4 E4 G4 B5 C6 D6>

        >>> n = note.Note('E6')
        >>> n.duration.type = 'half'
        >>> c.add(n)
        >>> c
        <music21.chord.Chord A2 B3 C4 E4 G4 B5 C6 D6 E6>
        >>> c.duration
        <music21.duration.Duration 1.0>
        >>> c[-1]
        <music21.note.Note E>
        >>> c[-1].duration
        <music21.duration.Duration 2.0>
        '''
        if not common.isIterable(notes):
            notes = [notes]
        self._add_core_or_init(notes, useDuration=False)
        self.clearCache()

    def remove(self, removeItem):
        '''
        Removes a note or pitch from the chord.  Must be a pitch
        equal to a pitch in the chord or a string specifying the pitch
        name with octave or a note from a chord.  If not found,
        raises a ValueError

        >>> c = chord.Chord('C4 E4 G4')
        >>> c.remove('E4')
        >>> c
        <music21.chord.Chord C4 G4>
        >>> c.remove('D5')
        Traceback (most recent call last):
        ValueError: Chord.remove(x), x not in chord

        >>> c = chord.Chord('C4 E4 G4')
        >>> c.remove(pitch.Pitch('E4'))
        >>> c
        <music21.chord.Chord C4 G4>
        >>> c.remove(pitch.Pitch('F#5'))
        Traceback (most recent call last):
        ValueError: Chord.remove(x), x not in chord


        The Note also does not need to be the exact note of the
        chord, just matches on equality

        >>> c = chord.Chord('C4 E4 G4')
        >>> c.remove(note.Note('E4'))
        >>> c
        <music21.chord.Chord C4 G4>

        >>> c.remove(c[1])
        >>> c
        <music21.chord.Chord C4>

        >>> c.remove(note.Note('B-2'))
        Traceback (most recent call last):
        ValueError: Chord.remove(x), x not in chord

        >>> c.remove(4)
        Traceback (most recent call last):
        ValueError: Cannot remove 4 from a chord; try a Pitch or Note object

        Like Python's list object does not work on lists...

        >>> c = chord.Chord('C4 E4 G4')
        >>> c.remove(['C4', 'E4'])
        Traceback (most recent call last):
        ValueError: Cannot remove ['C4', 'E4'] from a chord; try a Pitch or Note object
        '''
        if isinstance(removeItem, str):
            for n in self._notes:
                if not hasattr(n, 'pitch'):
                    continue
                if n.pitch.nameWithOctave == removeItem:
                    self._notes.remove(n)
                    self.clearCache()
                    return
            raise ValueError('Chord.remove(x), x not in chord')

        if isinstance(removeItem, pitch.Pitch):
            for n in self._notes:
                if hasattr(n, 'pitch') and n.pitch == removeItem:
                    self._notes.remove(n)
                    self.clearCache()
                    return
            raise ValueError('Chord.remove(x), x not in chord')

        if not isinstance(removeItem, note.NotRest):
            raise ValueError(
                f'Cannot remove {removeItem} from a chord; try a Pitch or Note object'
            )
        try:
            self._notes.remove(removeItem)
            self.clearCache()
        except ValueError:
            raise ValueError('Chord.remove(x), x not in chord')

    @property
    def notes(self) -> tuple[note.NotRest, ...]:
        return tuple(self._notes)

    @property
    def tie(self) -> tie.Tie | None:
        '''
        Get or set a single tie based on all the ties in this Chord.

        This overloads the behavior of the tie attribute found in all
        NotRest classes.

        If setting a tie, tie is applied to all pitches.

        >>> c1 = chord.Chord(['c4', 'g4'])
        >>> tie1 = tie.Tie('start')
        >>> c1.tie = tie1
        >>> c1.tie
        <music21.tie.Tie start>

        >>> c1.getTie(c1.pitches[1])
        <music21.tie.Tie start>
        '''
        for d in self._notes:
            if d.tie is not None:
                return d.tie
        return None

    @tie.setter
    def tie(self, value: tie.Tie | None):
        for d in self._notes:
            d.tie = value
            # set the same instance for each pitch
            # d['tie'] = value

    @property
    def volume(self) -> 'music21.volume.Volume':  # do NOT change to volume.Volume
        '''
        Get or set the :class:`~music21.volume.Volume` object for this
        Chord.

        When setting the .volume property, all pitches are treated as
        having the same Volume object.

        >>> c = chord.Chord(['g#', 'd-'])
        >>> c.volume
        <music21.volume.Volume realized=0.71>

        >>> c.volume = volume.Volume(velocity=64)
        >>> c.volume.velocityIsRelative = False
        >>> c.volume
        <music21.volume.Volume realized=0.5>

        * Changed in v8: setting volume to a list of volumes is no longer supported.
          See :meth:`~music21.chord.ChordBase.setVolumes` instead

        OMIT_FROM_DOCS

        Make sure that empty chords have a volume:

        >>> chord.Chord().volume
        <music21.volume.Volume realized=0.71>
        '''
        if isinstance(self._volume, volume.Volume):
            # if we already have a Volume, use that
            return self._volume

        if not self.hasComponentVolumes():
            # create a single new Volume object for the chord
            self._volume = note.NotRest._getVolume(self, forceClient=self)
            return self._volume

        # if we have components and _volume is None, create a volume from
        # components
        velocities = []
        for d in self._notes:
            velocities.append(d.volume.velocity)
        # create new local object
        self._volume = volume.Volume(client=self)
        if velocities:  # avoid division by zero error
            self._volume.velocity = int(round(sum(velocities) / len(velocities)))

        if t.TYPE_CHECKING:
            assert self._volume is not None
        return self._volume


    @volume.setter
    def volume(self, expr: None | 'music21.volume.Volume' | int | float):
        # Do NOT change typing to volume.Volume because it will take the property as
        # its name
        if isinstance(expr, volume.Volume):
            expr.client = self
            # remove any component volumes
            for c in self._notes:
                c._volume = None
            note.NotRest._setVolume(self, expr, setClient=False)
        elif common.isNum(expr):
            vol = self._getVolume()
            if t.TYPE_CHECKING:
                assert isinstance(expr, (int, float))

            if expr < 1:  # assume a scalar
                vol.velocityScalar = expr
            else:  # assume velocity
                vol.velocity = expr
        else:
            raise ChordException(f'unhandled setting expr: {expr}')

    def hasComponentVolumes(self) -> bool:
        '''
        Utility method to determine if this object has component
        :class:`~music21.volume.Volume` objects assigned to each
        note-component.

        >>> c1 = chord.Chord(['c4', 'd-1', 'g6'])
        >>> c1.setVolumes([60, 20, 120])
        >>> [n.volume.velocity for n in c1]
        [60, 20, 120]

        >>> c1.hasComponentVolumes()
        True

        >>> c2 = chord.Chord(['c4', 'd-1', 'g6'])
        >>> c2.volume.velocity = 23
        >>> c2.hasComponentVolumes()
        False

        >>> c3 = chord.Chord(['c4', 'd-1', 'g6'])
        >>> c3.setVolumes([0.2, 0.5, 0.8])
        >>> [n.volume.velocity for n in c3]
        [25, 64, 102]

        >>> c4 = chord.Chord(['c4', 'd-1', 'g6'])
        >>> c4.volume = 89
        >>> c4.volume.velocity
        89

        >>> c4.hasComponentVolumes()
        False

        '''
        count = 0
        for c in self._notes:
            # access private attribute, as property will create otherwise
            if c.hasVolumeInformation():
                count += 1
        if count == len(self._notes):
            # environLocal.printDebug(['hasComponentVolumes:', True])
            return True
        else:
            # environLocal.printDebug(['hasComponentVolumes:', False])
            return False

    # --------------------------------------------------------------------------
    # volume per pitch ??
    # --------------------------------------------------------------------------
    def setVolumes(self, volumes: Sequence['music21.volume.Volume' | int | float]):
        # do not change typing to volume.Volume -- will get the property of same name.
        # noinspection PyShadowingNames
        '''
        Set as many individual volumes as appear in volumes.  If there are not
        enough volumes, then cycles through the list of volumes here:

        >>> c = chord.Chord(['g#', 'd-'])
        >>> c.setVolumes([volume.Volume(velocity=96), volume.Volume(velocity=96)])
        >>> c.hasComponentVolumes()
        True

        Note that this means that the chord itself does not have a volume at this moment!

        >>> c.hasVolumeInformation()
        False

        >>> c.volume.velocity
        96

        But after having called the volume, now it does:

        >>> c.hasVolumeInformation()
        True

        >>> c.volume.velocityIsRelative = False
        >>> c.volume
        <music21.volume.Volume realized=0.76>

        * New in v8: replaces setting .volume to a list
        '''
        # if setting components, remove single velocity
        self._volume = None
        for i, c in enumerate(self._notes):
            v_entry = volumes[i % len(volumes)]
            v: volume.Volume
            if isinstance(v_entry, volume.Volume):
                v = v_entry
            else:  # create a new Volume
                if v_entry < 1:  # assume a scalar
                    v = volume.Volume(velocityScalar=v_entry)
                else:  # assume velocity
                    v = volume.Volume(velocity=v_entry)
            v.client = self
            c._setVolume(v, setClient=False)


# ------------------------------------------------------------------------------
class Chord(ChordBase):
    '''
    Class representing Chords.

    A Chord functions like a Note object but has multiple pitches.

    Create chords by passing a list of strings of pitch names:

    >>> dMaj = chord.Chord(['D', 'F#', 'A'])
    >>> dMaj
    <music21.chord.Chord D F# A>

    Pitch names can also include octaves:

    >>> dMaj = chord.Chord(['D3', 'F#4', 'A5'])
    >>> dMaj
    <music21.chord.Chord D3 F#4 A5>

    A single string with note names separated by spaces also works:

    >>> myChord = chord.Chord('A4 C#5 E5')
    >>> myChord
    <music21.chord.Chord A4 C#5 E5>


    Or you can combine already created Notes or Pitches:

    >>> cNote = note.Note('C')
    >>> eNote = note.Note('E')
    >>> gNote = note.Note('G')

    And then create a chord with note objects:

    >>> cmaj = chord.Chord([cNote, eNote, gNote])
    >>> cmaj  # default octave of 4 is used for these notes, since octave was not specified
    <music21.chord.Chord C E G>

    Or with pitches:

    >>> cmaj2 = chord.Chord([pitch.Pitch('C'), pitch.Pitch('E'), pitch.Pitch('G')])
    >>> cmaj2
    <music21.chord.Chord C E G>

    Chord has the ability to determine the root of a chord, as well as the bass note of a chord.
    In addition, Chord is capable of determining what type of chord a particular chord is, whether
    it is a triad or a seventh, major or minor, etc., as well as what inversion the chord is in.

    A chord can also be created from pitch class numbers:

    >>> c = chord.Chord([0, 2, 3, 5])
    >>> c.pitches
    (<music21.pitch.Pitch C>,
     <music21.pitch.Pitch D>,
     <music21.pitch.Pitch E->,
     <music21.pitch.Pitch F>)

    Or from MIDI numbers:

    >>> c = chord.Chord([72, 76, 79])
    >>> c.pitches
    (<music21.pitch.Pitch C5>, <music21.pitch.Pitch E5>, <music21.pitch.Pitch G5>)

    (If the number is < 12, it is assumed to be an octaveless pitch-class number, if above
    12, then a MIDI number.  To create chords below MIDI 12, create a Pitch object with that
    MIDI number instead and then pass that to the Chord creator).


    Duration or quarterLength also works:

    >>> d = duration.Duration(2.0)
    >>> myChord = chord.Chord('A4 C#5 E5', duration=d)
    >>> myChord
    <music21.chord.Chord A4 C#5 E5>
    >>> myChord.duration
    <music21.duration.Duration 2.0>
    >>> myChord.duration is d
    True

    >>> myChord = chord.Chord('A4 C#5 E5', quarterLength=3.75)
    >>> myChord.duration.type
    'half'
    >>> myChord.duration.dots
    3


    OMIT_FROM_DOCS

    Test that durations are being created efficiently:

    >>> dMaj.duration
    <music21.duration.Duration 1.0>

    >>> cmaj.pitches[0] is cNote.pitch
    True

    >>> cNote.duration
    <music21.duration.Duration 1.0>

    >>> cmaj.duration
    <music21.duration.Duration 1.0>

    >>> cmaj.duration is cNote.duration
    True

    Create a chord from two chords (or a chord + notes):

    >>> eFlatSixFive = chord.Chord('G3 B-3 D-4 E-4')
    >>> fFlat = chord.Chord('F-2 A-2 C-3 F-3')
    >>> riteOfSpring = chord.Chord([fFlat, eFlatSixFive])
    >>> riteOfSpring
    <music21.chord.Chord F-2 A-2 C-3 F-3 G3 B-3 D-4 E-4>

    Incorrect entries raise a TypeError:

    >>> chord.Chord([base])
    Traceback (most recent call last):
    TypeError: Could not process input argument <module 'music21.base' from '...base...'>

    **Equality**

    Two chords are equal if the Chord passes all `super()`
    equality tests and all their pitches are equal
    (possibly in a different order)

    >>> c1 = chord.Chord('C4 E4 G4')
    >>> c2 = chord.Chord('E4 C4 G4')
    >>> c1 == c2
    True
    >>> c3 = chord.Chord('E4 C#4 G4')
    >>> c2 == c3
    False
    >>> n1 = note.Note('C4')
    >>> c1 == n1
    False
    >>> c2.duration.quarterLength = 2.0
    >>> c1 == c2
    False
    >>> c1 != c2
    True
    '''
    # CLASS VARIABLES #
    isChord = True

    # define order of presenting names in documentation; use strings
    _DOC_ORDER = ['pitches']
    # documentation for all attributes (not properties or methods)
    _DOC_ATTR: dict[str, str] = {
        'isChord': '''
            Boolean read-only value describing if this
            GeneralNote object is a Chord. Is True''',
    }
    # update inherited _DOC_ATTR dictionary
    _DOC_ATTR.update(ChordBase._DOC_ATTR)


    # INITIALIZER #
    def __init__(self,
                 notes: t.Union[None,
                                Sequence[pitch.Pitch],
                                Sequence[note.Note],
                                Sequence[Chord],
                                Sequence[str],
                                str,
                                Sequence[int]] = None,
                 **keywords):
        if notes is not None and any(isinstance(n, note.GeneralNote)
                                     and not isinstance(n, (note.Note, Chord))
                                     for n in notes):
            raise TypeError(f'Use a PercussionChord to contain Unpitched objects; got {notes}')
        super().__init__(notes=notes, **keywords)

        # if there were a covariant list, we would use that instead.
        self._notes: list[note.Note]  # type: ignore

        if notes is not None and all(isinstance(n, int) for n in notes):
            self.simplifyEnharmonics(inPlace=True)


    # SPECIAL METHODS #

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        if set(self.pitches) != set(other.pitches):
            return False
        return True

    def __hash__(self):
        return super().__hash__()

    def __getitem__(self, key: int | str | note.Note | pitch.Pitch):
        '''
        Get item makes accessing pitch components for the Chord easier

        >>> c = chord.Chord('C#4 D-4')
        >>> cSharp = c[0]
        >>> cSharp
        <music21.note.Note C#>

        >>> c['0.step']
        'C'
        >>> c['3.accidental']
        Traceback (most recent call last):
        KeyError: "Cannot access component with: '3.accidental'"

        >>> c[5]
        Traceback (most recent call last):
        KeyError: 'Cannot access component with: 5'

        >>> c['D-4']
        <music21.note.Note D->

        >>> c['D-4.style.color'] is None
        True

        Getting by note does not do very much...

        >>> c[cSharp]
        <music21.note.Note C#>

        But we can get from another note

        >>> cSharp2 = note.Note('C#4')
        >>> cSharp2.duration.quarterLength = 3.0
        >>> c[cSharp2] is cSharp
        True
        >>> c[cSharp2] is cSharp2
        False

        KeyError is raised if not in chord.

        >>> notInChord = note.Note('G')
        >>> c[notInChord]
        Traceback (most recent call last):
        KeyError: 'Cannot access component with: <music21.note.Note G>'

        >>> c[None]
        Traceback (most recent call last):
        KeyError: 'Cannot access component with: None'
        '''
        foundNote: note.Note
        attributes: tuple[str, ...]

        keyErrorStr = f'Cannot access component with: {key!r}'
        if isinstance(key, str):
            if key.count('.'):
                key, attrStr = key.split('.', 1)
                if not attrStr.count('.'):
                    attributes = (attrStr,)
                else:
                    attributes = tuple(attrStr.split('.'))
            else:
                attributes = ()

            try:
                key = int(key)
            except ValueError:
                pass

        else:
            attributes = ()

        if isinstance(key, int):
            try:
                foundNote = self._notes[key]  # must be a number
            except (KeyError, IndexError):
                raise KeyError(keyErrorStr)

        elif isinstance(key, str):
            key = key.upper()
            for n in self._notes:
                if n.pitch.nameWithOctave == key:
                    foundNote = n
                    break
            else:
                raise KeyError(keyErrorStr)
        elif isinstance(key, note.Note):
            for n in self._notes:
                if n is key:
                    foundNote = n
                    break
            else:
                for n in self._notes:
                    if n.pitch == key.pitch:
                        foundNote = n
                        break
                else:
                    raise KeyError(keyErrorStr)
        elif isinstance(key, pitch.Pitch):
            for n in self._notes:
                if n.pitch is key:
                    foundNote = n
                    break
            else:
                for n in self._notes:
                    if n.pitch == key:
                        foundNote = n
                        break
                else:
                    raise KeyError(keyErrorStr)
        else:
            raise KeyError(keyErrorStr)

        if not attributes:
            return foundNote

        currentValue: t.Any = foundNote

        for attr in attributes:
            if attr == 'volume':  # special handling
                # noinspection PyArgumentList
                currentValue = currentValue._getVolume(forceClient=self)
            else:
                currentValue = getattr(currentValue, attr)

        return currentValue

    def __setitem__(self, key, value):
        '''
        Change either a note in the chord components, or set an attribute on a
        component

        >>> c = chord.Chord('C4 E4 G4')
        >>> c[0] = note.Note('C#4')
        >>> c
        <music21.chord.Chord C#4 E4 G4>
        >>> c['0.octave'] = 3
        >>> c
        <music21.chord.Chord C#3 E4 G4>
        >>> c['E4'] = 'F4'
        >>> c
        <music21.chord.Chord C#3 F4 G4>
        >>> c['G4.style.color'] = 'red'
        >>> c['G4.style.color']
        'red'
        >>> c[-1].style.color
        'red'

        >>> c[0] = None
        Traceback (most recent call last):
        ValueError: Chord index must be set to a valid note object
        '''
        if isinstance(key, str) and key.count('.'):
            keySplit = key.split('.')
            keyFind = '.'.join(keySplit[0:-1])
            attr = keySplit[-1]
            keyObj = self[keyFind]
            setattr(keyObj, attr, value)
            return

        keyObj = self[key]
        keyIndex = self._notes.index(keyObj)

        if isinstance(value, str):
            value = note.Note(value)
        elif isinstance(value, pitch.Pitch):
            value = note.Note(pitch=value)
        elif not isinstance(value, note.Note):
            raise ValueError('Chord index must be set to a valid note object')

        self._notes[keyIndex] = value

    def _reprInternal(self) -> str:
        if not self.pitches:
            return super()._reprInternal()

        allPitches = []
        for thisPitch in self.pitches:
            allPitches.append(thisPitch.nameWithOctave)

        return ' '.join(allPitches)

    # STATIC METHOD #

    @staticmethod
    def formatVectorString(vectorList) -> str:
        '''
        Return a string representation of a vector or set

        Static method.  Works on the class:

        >>> chord.Chord.formatVectorString([0, 11])
        '<0B>'

        or an existing chord:

        >>> c1 = chord.Chord(['D4', 'A4', 'F#5', 'D6'])
        >>> c1.formatVectorString(c1.normalOrder)
        '<269>'

        or on a list that has nothing to do with the chord

        >>> c1.formatVectorString([10, 11, 3, 5])
        '<AB35>'

        '''
        msg = ['<']
        for e in vectorList:  # should be numbers
            eStr = pitch.convertPitchClassToStr(e)
            msg.append(eStr)
        msg.append('>')
        return ''.join(msg)

    # PRIVATE METHODS #
    def _findBass(self) -> pitch.Pitch | None:
        '''
        Returns the lowest Pitch in the chord.

        The only time findBass should be called is by bass() when it is
        figuring out what the bass note of the chord is.

        Generally call bass() instead:

        >>> cmaj = chord.Chord(['C4', 'E3', 'G4'])
        >>> cmaj._findBass()
        <music21.pitch.Pitch E3>
        '''
        lowest = None
        for thisPitch in self.pitches:
            if lowest is None:
                lowest = thisPitch
            else:
                lowest = interval.getWrittenLowerNote(lowest, thisPitch)
        return lowest

    def _removePitchByRedundantAttribute(
        self: _ChordType,
        attribute: str,
        *,
        inPlace=False
    ) -> _ChordType | list[pitch.Pitch]:
        '''
        Common method for stripping pitches based on redundancy of one pitch
        attribute. The `attribute` is provided by a string.
        '''
        if not inPlace:  # make a copy
            returnObj = copy.deepcopy(self)
        else:
            returnObj = self

        uniquePitches = []
        deleteComponents = []
        for comp in returnObj._notes:
            if getattr(comp.pitch, attribute) not in uniquePitches:
                uniquePitches.append(getattr(comp.pitch, attribute))
            else:
                deleteComponents.append(comp)

        # environLocal.printDebug(['unique, delete', self, unique, delete])
        altered = returnObj._notes
        alteredId = [id(n) for n in altered]
        for n in deleteComponents:
            nIndex = alteredId.index(id(n))
            altered.pop(nIndex)
            alteredId.pop(nIndex)

        returnObj._notes = altered
        if deleteComponents:
            returnObj.clearCache()

        if not inPlace:
            return returnObj
        else:
            return [n.pitch for n in deleteComponents]


    # PUBLIC METHODS #

    def add(
        self,
        notes,
        *,
        runSort=True
    ) -> None:
        '''
        Add a Note, Pitch, the `.notes` of another chord,
        or string representing a pitch,
        or a list of any-of-the-above types to a Chord.

        If `runSort` is True (default=True) then after appending, the
        chord will be sorted.

        >>> c = chord.Chord('C4 E4 G4')
        >>> c.add('B3')
        >>> c
        <music21.chord.Chord B3 C4 E4 G4>
        >>> c.duration
        <music21.duration.Duration 1.0>

        >>> c.add('A2', runSort=False)
        >>> c
        <music21.chord.Chord B3 C4 E4 G4 A2>

        >>> c.add(['B5', 'C6'])
        >>> c
        <music21.chord.Chord A2 B3 C4 E4 G4 B5 C6>

        >>> c.add(pitch.Pitch('D6'))
        >>> c
        <music21.chord.Chord A2 B3 C4 E4 G4 B5 C6 D6>

        >>> n = note.Note('E6')
        >>> n.duration.type = 'half'
        >>> c.add(n)
        >>> c
        <music21.chord.Chord A2 B3 C4 E4 G4 B5 C6 D6 E6>
        >>> c.duration
        <music21.duration.Duration 1.0>
        >>> c[-1]
        <music21.note.Note E>
        >>> c[-1].duration
        <music21.duration.Duration 2.0>

        Overrides `ChordBase.add()` to permit sorting with `runSort`.
        '''
        if not common.isIterable(notes):
            notes = [notes]
        if any(isinstance(n, note.Unpitched) for n in notes):
            raise TypeError(f'Use a PercussionChord to contain Unpitched objects; got {notes}')
        super().add(notes)
        if runSort:
            self.sortAscending(inPlace=True)

    @overload
    def annotateIntervals(
        self: _ChordType,
        *,
        inPlace: bool = False,
        stripSpecifiers: bool = True,
        sortPitches: bool = True,
        returnList: t.Literal[True]
    ) -> list[str]:
        pass

    @overload
    def annotateIntervals(
        self: _ChordType,
        *,
        inPlace: t.Literal[True],
        stripSpecifiers: bool = True,
        sortPitches: bool = True,
        returnList: t.Literal[False] = False
    ) -> None:
        pass

    @overload
    def annotateIntervals(
        self: _ChordType,
        *,
        inPlace: t.Literal[False] = False,
        stripSpecifiers: bool = True,
        sortPitches: bool = True,
        returnList: t.Literal[False] = False
    ) -> _ChordType:
        pass

    def annotateIntervals(
        self: _ChordType,
        *,
        inPlace: bool = False,
        stripSpecifiers: bool = True,
        sortPitches: bool = True,
        returnList: bool = False
    ) -> _ChordType | None | list[str]:
        # noinspection PyShadowingNames
        '''
        Add lyrics to the chord that show the distance of each note from
        the bass.  If returnList is True, a list of the intervals is returned instead.

        By default, we show only the generic interval:

        >>> c1 = chord.Chord(['C2', 'E2', 'G2', 'C3'])
        >>> c2 = c1.annotateIntervals(inPlace=False)
        >>> c2.lyrics
        [<music21.note.Lyric number=1 syllabic=single text='8'>,
         <music21.note.Lyric number=2 syllabic=single text='5'>,
         <music21.note.Lyric number=3 syllabic=single text='3'>]

        >>> [ly.text for ly in c2.lyrics]
        ['8', '5', '3']

        The `stripSpecifiers` parameter can be used to show only the intervals size (3, 5, etc.)
        or the complete interval specification (m3, P5, etc.)

        >>> c3 = c1.annotateIntervals(inPlace=False, stripSpecifiers=False)
        >>> c3.lyrics
        [<music21.note.Lyric number=1 syllabic=single text='P8'>,
         <music21.note.Lyric number=2 syllabic=single text='P5'>,
         <music21.note.Lyric number=3 syllabic=single text='M3'>]

        >>> [ly.text for ly in c3.lyrics]
        ['P8', 'P5', 'M3']

        This chord was giving us problems:

        >>> c4 = chord.Chord(['G4', 'E4', 'B3', 'E3'])
        >>> c4.annotateIntervals(inPlace=True, stripSpecifiers=False)
        >>> [ly.text for ly in c4.lyrics]
        ['m3', 'P8', 'P5']
        >>> c4.annotateIntervals(inPlace=True, stripSpecifiers=False, returnList=True)
        ['m3', 'P8', 'P5']

        If sortPitches is false it still gives problems...

        >>> c4 = chord.Chord(['G4', 'E4', 'B3', 'E3'])
        >>> c4.annotateIntervals(inPlace=True, stripSpecifiers=False, sortPitches=False)
        >>> [ly.text for ly in c4.lyrics]
        ['m3', 'm6', 'm3']

        >>> c = chord.Chord(['c4', 'd-4', 'g4'])
        >>> c.annotateIntervals(inPlace=True)
        >>> [ly.text for ly in c.lyrics]
        ['5', '2']

        >>> c = chord.Chord(['c4', 'd-4', 'g4'])
        >>> c.annotateIntervals(inPlace=True, stripSpecifiers=False)
        >>> [ly.text for ly in c.lyrics]
        ['P5', 'm2']

        >>> c = chord.Chord(['c4', 'd---4', 'g4'])
        >>> c.annotateIntervals(inPlace=True, stripSpecifiers=False)
        >>> [ly.text for ly in c.lyrics]
        ['P5', 'dd2']

        >>> c = chord.Chord(['c4', 'g5', 'e6'])
        >>> c.annotateIntervals(inPlace=True)
        >>> [ly.text for ly in c.lyrics]
        ['5', '3']
        '''
        # make a copy of self for reducing pitches, but attach to self
        c = copy.deepcopy(self)
        # this could be an option
        c.removeRedundantPitches(inPlace=True)

        if sortPitches:
            c = c.sortAscending()
        # environLocal.printDebug(['annotateIntervals()', c.pitches])
        lyricsList = []

        for j in range(len(c.pitches) - 1, 0, -1):  # only go to one; zero never used
            p = c.pitches[j]
            i = interval.Interval(c.pitches[0], p)
            if stripSpecifiers is False:
                notation = i.semiSimpleName
            else:
                notation = str(i.diatonic.generic.semiSimpleUndirected)
            lyricsList.append(notation)

        if stripSpecifiers and sortPitches:
            lyricsList.sort(reverse=True)

        if returnList:
            return lyricsList

        for notation in lyricsList:
            if inPlace:
                self.addLyric(notation)
            else:
                c.addLyric(notation)

        if not inPlace:
            return c

    def areZRelations(self: _ChordType, other: _ChordType) -> bool:
        '''
        Check if another Chord is a z-relation to this Chord.

        >>> c1 = chord.Chord(['C', 'c#', 'e', 'f#'])
        >>> c2 = chord.Chord(['C', 'c#', 'e-', 'g'])
        >>> c3 = chord.Chord(['C', 'c#', 'f#', 'g'])
        >>> c1.areZRelations(c2)
        True

        >>> c1.areZRelations(c3)
        False

        If there is no z-relation for the first chord, obviously return False:

        >>> c4 = chord.Chord('C E G')
        >>> c4.areZRelations(c3)
        False
        '''
        zRelationAddress = tables.addressToZAddress(self.chordTablesAddress)
        if zRelationAddress is None:
            return False
        if other.chordTablesAddress[0:3] == zRelationAddress[0:3]:
            return True
        return False

    @overload
    def bass(self,
             newbass: None = None,
             *,
             find: bool | None = None,
             allow_add: bool = False,
             ) -> pitch.Pitch:
        return self.pitches[0]  # dummy until Astroid 1015 is fixed.

    @overload
    def bass(self,
             newbass: str | pitch.Pitch | note.Note,
             *,
             find: bool | None = None,
             allow_add: bool = False,
             ) -> None:
        return None

    def bass(self,
             newbass: None | str | pitch.Pitch | note.Note = None,
             *,
             find: bool | None = None,
             allow_add: bool = False,
             ) -> pitch.Pitch | None:
        '''
        Generally used to find and return the bass Pitch:

        >>> cmaj1stInv = chord.Chord(['C4', 'E3', 'G5'])
        >>> cmaj1stInv.bass()
        <music21.pitch.Pitch E3>

        Subclasses of Chord often have basses that are harder to determine.

        >>> cmaj = harmony.ChordSymbol('CM')
        >>> cmaj.bass()
        <music21.pitch.Pitch C3>

        >>> cmin_inv = harmony.ChordSymbol('Cm/E-')
        >>> cmin_inv.bass()
        <music21.pitch.Pitch E-3>

        Can also be used in rare occasions to set the bass note to a new Pitch,
        so long as that note is found in the chord:

        >>> strange_chord = chord.Chord('E##4 F-4 C5')
        >>> strange_chord.bass()
        <music21.pitch.Pitch E##4>
        >>> strange_chord.bass('F-4')
        >>> strange_chord.bass()
        <music21.pitch.Pitch F-4>

        If the note assigned to the bass is not found, it will default to raising a
        ChordException:

        >>> strange_chord.bass('G--4')
        Traceback (most recent call last):
        music21.chord.ChordException: Pitch G--4 not found in chord

        For the purposes of initializing from a ChordSymbol and in other cases,
        a new bass can be added to the chord by setting `allow_add = True`:

        >>> strange_chord.bass('G--4', allow_add=True)
        >>> strange_chord.bass()
        <music21.pitch.Pitch G--4>


        By default, if nothing has been overridden, this method uses a
        quick algorithm to find the bass among the
        chord's pitches, if no bass has been previously specified. If this is
        not intended, set find to False when calling this method, and 'None'
        will be returned if no bass is specified

        >>> em = chord.Chord(['E3', 'G3', 'B4'])
        >>> print(em.bass(find=False))
        None

        * Changed in v8: raise an exception if setting a new bass
          to a pitch not in the chord, unless new keyword `allow_add` is `True`.

        OMIT_FROM_DOCS

        Test to make sure that cached basses still work by calling twice:

        >>> a = chord.Chord(['C4'])
        >>> a.bass()
        <music21.pitch.Pitch C4>
        >>> a.bass()
        <music21.pitch.Pitch C4>

        # After changing behavior uncomment these lines.

        # Setting a new bass note might be helpful to move it to a different
        # octave.  Otherwise, it is likely just to lead to confusion and
        # hard to diagnose errors.
        #
        # >>> cmin_inv.bass('E-2')
        # >>> cmin_inv.bass()
        # <music21.pitch.Pitch E-2>
        #
        # To find the bass again from the pitches in the chord, set find=True
        #
        # >>> cmin_inv.bass(find=True)
        # <music21.pitch.Pitch E-3>
        #
        # Subsequent calls after an overridden bass has been cleared by find=True
        # will continue to return the algorithmically determined bass.
        #
        # >>> cmin_inv.bass()
        # <music21.pitch.Pitch E-3>

        '''
        if newbass:
            newbassPitch: pitch.Pitch
            if isinstance(newbass, str):
                newbass = common.cleanedFlatNotation(newbass)
                newbassPitch = pitch.Pitch(newbass)
            elif isinstance(newbass, pitch.Pitch):
                newbassPitch = newbass
            elif isinstance(newbass, note.Note):
                newbassPitch = newbass.pitch
            else:
                raise ChordException(f'newbass should be a Pitch, not {type(newbass)}')

            # try to set newbass to be a pitch in the chord if possible
            foundBassInChord: bool = False
            for p in self.pitches:  # first by identity
                if newbassPitch is p:
                    foundBassInChord = True
                    break

            if not foundBassInChord:
                for p in self.pitches:  # then by name with octave
                    if p.nameWithOctave == newbassPitch.nameWithOctave:
                        newbassPitch = p
                        foundBassInChord = True
                        break

            if not foundBassInChord:  # finally by name
                for p in self.pitches:
                    if p.name == newbassPitch.name:
                        foundBassInChord = True
                        newbassPitch = p
                        break

            if not foundBassInChord:  # it's not there, needs to be added
                if not allow_add:
                    raise ChordException(f'Pitch {newbass} not found in chord')

                self.pitches = (newbassPitch, *(p for p in self.pitches))

            self._overrides['bass'] = newbassPitch
            self._cache['bass'] = newbassPitch
            if 'inversion' in self._cache:
                del self._cache['inversion']
            # reset inversion if bass changes
            return None

        if 'bass' in self._overrides and find is not True:
            return self._overrides['bass']

        if find is False:
            return None

        if 'bass' in self._overrides:
            del self._overrides['bass']

        if find is not True and 'bass' in self._cache:
            return self._cache['bass']
        else:
            self._cache['bass'] = self._findBass()
            return self._cache['bass']

    def canBeDominantV(self) -> bool:
        '''
        Returns True if the chord is a Major Triad or a Dominant Seventh:

        >>> gSeven = chord.Chord(['g', 'b', 'd', 'f'])
        >>> gSeven.canBeDominantV()
        True

        >>> gDim = chord.Chord(['g', 'b-', 'd-'])
        >>> gDim.canBeDominantV()
        False
        '''
        if self.isMajorTriad() or self.isDominantSeventh():
            return True
        else:
            return False

    def canBeTonic(self) -> bool:
        '''
        Returns True if the chord is a major or minor triad:

        >>> a = chord.Chord(['g', 'b', 'd', 'f'])
        >>> a.canBeTonic()
        False

        >>> a = chord.Chord(['g', 'b', 'd'])
        >>> a.canBeTonic()
        True

        '''
        if self.isMajorTriad() or self.isMinorTriad():
            return True
        else:
            return False

    @overload
    def closedPosition(
        self: _ChordType,
        *,
        forceOctave: int | None,
        inPlace: t.Literal[True],
        leaveRedundantPitches=False
    ) -> None:
        # astroid 1003
        return None

    @overload
    def closedPosition(
        self: _ChordType,
        *,
        forceOctave: int | None = None,
        inPlace: t.Literal[False] = False,
        leaveRedundantPitches: bool = False
    ) -> _ChordType:
        # astroid 1003
        return self

    def closedPosition(
        self: _ChordType,
        *,
        forceOctave: int | None = None,
        inPlace: bool = False,
        leaveRedundantPitches: bool = False
    ) -> _ChordType | None:
        '''
        Returns a new Chord object with the same pitch classes,
        but now in closed position.

        If `forcedOctave` is provided, the bass of the chord will
        be shifted to that provided octave.

        If inPlace is True then the original chord is returned with new pitches.

        >>> chord1 = chord.Chord(['C#4', 'G5', 'E6'])
        >>> chord2 = chord1.closedPosition()
        >>> chord2
        <music21.chord.Chord C#4 E4 G4>

        Force octave changes the octave of the bass note (and all notes above it...)

        >>> c2 = chord.Chord(['C#4', 'G5', 'E6'])
        >>> c2.closedPosition(forceOctave=2)
        <music21.chord.Chord C#2 E2 G2>

        >>> c3 = chord.Chord(['C#4', 'G5', 'E6'])
        >>> c3.closedPosition(forceOctave=6)
        <music21.chord.Chord C#6 E6 G6>

        Redundant pitches are removed by default, but can be retained...

        >>> c4 = chord.Chord(['C#4', 'C5', 'F7', 'F8'])
        >>> c5 = c4.closedPosition(forceOctave=4, inPlace=False)
        >>> c5
        <music21.chord.Chord C#4 F4 C5>

        >>> c6 = c4.closedPosition(forceOctave=4, inPlace=False, leaveRedundantPitches=True)
        >>> c6
        <music21.chord.Chord C#4 F4 F4 C5>

        Implicit octaves work fine...

        >>> c7 = chord.Chord(['A4', 'B4', 'A'])
        >>> c7.closedPosition(forceOctave=4, inPlace=True)
        >>> c7
        <music21.chord.Chord A4 B4>

        OMIT_FROM_DOCS
        Very specialized fears...

        Duplicate octaves were not working

        >>> c7b = chord.Chord(['A4', 'B4', 'A5'])
        >>> c7b.closedPosition(inPlace=True)
        >>> c7b
        <music21.chord.Chord A4 B4>

        but the bass must remain A4:

        >>> c7c = chord.Chord(['A4', 'B4', 'A5', 'G##6'])
        >>> c7c.closedPosition(inPlace=True)
        >>> c7c
        <music21.chord.Chord A4 B4 G##5>

        >>> str(c7c.bass())
        'A4'

        complex chord for semiclosed-position testing...

        >>> c8 = chord.Chord(['C3', 'E5', 'C#6', 'E-7', 'G8', 'C9', 'E#9'])
        >>> c8.closedPosition(inPlace=True)
        >>> c8
        <music21.chord.Chord C3 C#3 E-3 E3 E#3 G3>

        Implicit octave + forceOctave

        >>> c9 = chord.Chord('C G E')
        >>> c9.closedPosition(forceOctave=6)
        <music21.chord.Chord C6 E6 G6>
        '''
        # environLocal.printDebug(['calling closedPosition()', inPlace])
        if inPlace:
            returnObj = self
        else:
            returnObj = copy.deepcopy(self)
            returnObj.derivation = derivation.Derivation(returnObj)
            returnObj.derivation.origin = self
            returnObj.derivation.method = 'closedPosition'
        # tempChordNotes = returnObj.pitches

        pBass = returnObj.bass()  # returns a reference, not a copy
        if forceOctave is not None:
            pBassOctave = pBass.octave
            if pBassOctave is None:
                pBassOctave = pBass.implicitOctave

            if pBassOctave > forceOctave:
                dif = -1
            elif pBassOctave < forceOctave:
                dif = 1
            else:  # equal
                dif = None
            if dif is not None:
                while pBass.octave != forceOctave:
                    # shift octave of all pitches
                    for p in returnObj.pitches:
                        if p.octave is None:
                            p.octave = p.implicitOctave
                        p.octave += dif

        # can change these pitches in place
        for p in returnObj.pitches:
            # bring each pitch down octaves until pitch space is
            # within an octave
            if p.octave is None:
                p.octave = p.implicitOctave
            while p.ps >= pBass.ps + 12:
                p.octave -= 1
            # check for a bass of C4 and the note B#7 added to it, should be B#4 not B#3...
            if p.diatonicNoteNum < pBass.diatonicNoteNum:
                p.octave += 1

        if leaveRedundantPitches is not True:
            returnObj.removeRedundantPitches(inPlace=True)  # here we can always be in place...

        # if not inPlace, creates a second new chord object!
        returnObj.sortAscending(inPlace=True)

        if not inPlace:
            return returnObj

    def containsSeventh(self) -> bool:
        '''
        Returns True if the chord contains at least one of each of Third, Fifth, and Seventh.
        raises an exception if the Root can't be determined

        A ninth chord contains a seventh:

        >>> c9 = chord.Chord(['C4', 'E4', 'G4', 'B4', 'D5'])
        >>> c9.containsSeventh()
        True

        As does a cluster:

        >>> cluster = chord.Chord('C D E F G A B')
        >>> cluster.containsSeventh()
        True

        But a major triad does not:

        >>> dMaj = chord.Chord([pitch.Pitch('D4'), pitch.Pitch('F#4'), pitch.Pitch('A5')])
        >>> dMaj.containsSeventh()
        False

        Note that a seventh chord itself contains a seventh.

        >>> cChord = chord.Chord(['C', 'E', 'G', 'B'])
        >>> cChord.containsSeventh()
        True


        Empty chord returns False

        >>> chord.Chord().containsSeventh()
        False
        '''
        if not self.containsTriad():
            return False
        # no need to cache, since third, fifth, and seventh are cached
        if self.seventh is None:
            return False

        return True

    def containsTriad(self) -> bool:
        '''
        Returns True or False if there is no triad above the root.
        "Contains vs. Is": A dominant-seventh chord contains a triad.

        >>> cChord = chord.Chord(['C', 'E', 'G'])
        >>> other = chord.Chord(['C', 'D', 'E', 'F', 'G'])
        >>> cChord.containsTriad()
        True

        >>> other.containsTriad()
        True

        >>> scale = chord.Chord(['C', 'D-', 'E', 'F#', 'G', 'A#', 'B'])
        >>> scale.containsTriad()
        True

        >>> c = chord.Chord('C4 D4')
        >>> c.containsTriad()
        False

        >>> chord.Chord().containsTriad()
        False
        '''
        # no need to cache, since third and fifth are cached
        if self.third is None:
            return False

        if self.fifth is None:
            return False

        return True

    def _findRoot(self) -> pitch.Pitch:
        '''
        Looks for the root usually by finding the note with the most 3rds above
        it.

        Generally use root() instead, since if a chord doesn't know its root,
        root() will run ._findRoot() automatically.
        '''
        def rootnessFunction(rootThirdList):
            '''
            Returns a value for how likely this pitch is to be a root given the
            number of thirds and fifths above it.

            Takes a list of True's and False's where each value represents
            whether a note has a 3rd, 5th, 7th, 9th, 11th, and 13th above it
            and calculates a value based on that.  The highest score on
            rootnessFunction is the root.

            This formula might be tweaked if wrong notes are found.

            Rootness function might be divided by the inversion number
            in case that's a problem.
            '''
            score = 0
            for root_index, val in enumerate(rootThirdList):
                if val is True:
                    score += 1 / (root_index + 6)
            return score

        # FIND ROOT FAST -- for cases where one note has perfectly stacked
        # thirds, like E C G; but not C E B-
        # if one pitch has perfectlyStackedThirds, return it always.

        # we use the music21 unique function since it preserves the order
        nonDuplicatingPitches = common.misc.unique((n.pitch for n in self._notes),
                                                   key=lambda pp: pp.step)
        lenPitches = len(nonDuplicatingPitches)
        if not lenPitches:
            raise ChordException(f'no pitches in chord {self!r}')

        if lenPitches == 1:
            return self.pitches[0]
        elif lenPitches == 7:  # 13th chord
            return self.bass()

        stepNumsToPitches: dict[int, pitch.Pitch] = {pitch.STEP_TO_DNN_OFFSET[p.step]: p
                                                     for p in nonDuplicatingPitches}

        # TODO: duplicate the steps array [1,0,1,0,1,0,0] so it's [1,0,1,0,1,0,0,1,0,1,0,1,0,0]
        #    and then for each cardinality, use a template like [1, 0, 1, 0, 1] to slide along
        #    and see if it fits -- this will allow this routine to work for any number of
        #    steps from 3-6.
        stepNums = sorted(stepNumsToPitches)
        for startIndex in range(lenPitches):
            all_are_thirds = True
            this_step_num = stepNums[startIndex]
            last_step_num = this_step_num
            for endIndex in range(startIndex + 1, startIndex + lenPitches):
                endIndexMod = endIndex % lenPitches
                endStepNum = stepNums[endIndexMod]
                if endStepNum - last_step_num not in (2, -5):
                    all_are_thirds = False
                    break
                last_step_num = endStepNum
            if all_are_thirds:
                return stepNumsToPitches[this_step_num]

        # FIND ROOT SLOW
        # no notes (or more than one...) have perfectlyStackedThirds above them.  Return
        # the highest scoring note...
        # this is the slowest...

        rootnessFunctionScores = []
        orderedChordSteps = (3, 5, 7, 2, 4, 6)

        for p in nonDuplicatingPitches:
            currentListOfThirds = []
            this_step_num = pitch.STEP_TO_DNN_OFFSET[p.step]
            for chordStepTest in orderedChordSteps:
                if (this_step_num + chordStepTest - 1) % 7 in stepNumsToPitches:
                    currentListOfThirds.append(True)
                else:
                    currentListOfThirds.append(False)

            rootnessScore = rootnessFunction(currentListOfThirds)
            rootnessFunctionScores.append(rootnessScore)

        mostRootyIndex = rootnessFunctionScores.index(max(rootnessFunctionScores))
        return nonDuplicatingPitches[mostRootyIndex]

    def geometricNormalForm(self) -> list[int]:
        '''
        Geometric Normal Form, as first defined by Dmitri Tymoczko, orders pitch classes
        such that the spacing is prioritized with the smallest spacing between the first and
        second pitch class first, then the smallest spacing between second and third pitch class,
        and so on. This form has unique properties that make it useful.  It also transposes
        to PC0

        `geometricNormalForm` returns a list of pitch class integers in
        geometric normal form.

        Example 1: A major triad has geometricNormalForm of 038 not 047.

        >>> c1 = chord.Chord('E4 C5 G6 C7')
        >>> pcList = c1.geometricNormalForm()
        >>> pcList
        [0, 3, 8]

        >>> c2 = chord.Chord(pcList)
        >>> c2.orderedPitchClassesString
        '<038>'

        Compare this to the usual normalOrder transposed to PC0:

        >>> normalOrder = c1.normalOrder
        >>> normalOrderFirst = normalOrder[0]
        >>> [(pc - normalOrderFirst) % 12 for pc in normalOrder]
        [0, 4, 7]
        '''
        # no need to cache, since only DT uses it...
        # Order pitches
        pitchClassList = []
        for i in range(len(self.pitches)):
            pitchClassList.append(self.pitches[i].pitchClass)
        sortedPitchClassList = sorted(pitchClassList)
        # Remove duplicates
        uniquePitchClassList = [sortedPitchClassList[0]]
        for i in range(1, len(sortedPitchClassList)):
            if sortedPitchClassList[i] != sortedPitchClassList[i - 1]:
                uniquePitchClassList.append(sortedPitchClassList[i])
        intervalList = []
        for i in range(1, len(uniquePitchClassList)):
            lPC = (uniquePitchClassList[i] - uniquePitchClassList[i - 1]) % 12
            intervalList.append(lPC)
        intervalList.append((uniquePitchClassList[0] - uniquePitchClassList[-1]) % 12)
        # make list of rotations
        rotationList = []
        for i in range(0, len(intervalList)):
            b = intervalList.pop(0)
            intervalList.append(b)
            intervalTuple = tuple(intervalList)
            rotationList.append(intervalTuple)
        # Sort list of rotations.
        # First entry will be the geometric normal form arranged intervals
        newRotationList = sorted(rotationList)
        # Take that first entry and assign it as the PCIs that we will want for our chord
        geomNormChord = newRotationList[0]
        # Create final form of Geometric Normal Chord by starting at pc 0 and
        # assigning the notes based on the intervals we just discovered.
        geomNormChordPitches = []
        intervalSum = 0
        for i in range(0, len(geomNormChord)):
            geomNormChordPitches.append(intervalSum)
            intervalSum += geomNormChord[i]
        return geomNormChordPitches

    def getChordStep(
        self,
        chordStep: int,
        *,
        testRoot: note.Note | pitch.Pitch | None = None
    ) -> pitch.Pitch | None:
        '''
        Returns the (first) pitch at the provided scaleDegree (Thus, it's
        exactly like semitonesFromChordStep, except it instead of the number of
        semitones.)

        Returns None if none can be found.

        >>> cmaj = chord.Chord(['C', 'E', 'G'])
        >>> cmaj.getChordStep(3)  # will return the third of the chord
        <music21.pitch.Pitch E>

        >>> g = cmaj.getChordStep(5)  # will return the fifth of the chord
        >>> g.name
        'G'

        >>> cmaj.getChordStep(6) is None
        True

        Ninths can be specified with either 9 or 2.  Similarly for elevenths
        and thirteenths.

        >>> c9 = chord.Chord('C4 E4 G4 B4 D5')
        >>> c9.getChordStep(9)
        <music21.pitch.Pitch D5>
        >>> c9.getChordStep(2)
        <music21.pitch.Pitch D5>

        OMIT_FROM_DOCS

        If `root` has been explicitly overridden as `None`, calling this raises `ChordException`:

        >>> cmaj._overrides['root'] = None
        >>> cmaj.getChordStep(6)
        Traceback (most recent call last):
        music21.chord.ChordException: Cannot run getChordStep without a root

        (This is in OMIT...)
        '''
        if chordStep >= 8:
            chordStep -= 7

        testRootPitch: pitch.Pitch
        if testRoot is None:
            testRootPitch = self.root()  # raises ChordException if no pitches
            if testRootPitch is None:  # if root was overridden to be None
                raise ChordException('Cannot run getChordStep without a root')
        elif isinstance(testRoot, note.Note):
            testRootPitch = testRoot.pitch
        elif isinstance(testRoot, pitch.Pitch):
            testRootPitch = testRoot
        else:
            raise ChordException(f'testRoot should be a Pitch, not {type(testRoot)}')

        rootDNN = testRootPitch.diatonicNoteNum
        for thisPitch in self.pitches:
            diatonicDistance = ((thisPitch.diatonicNoteNum - rootDNN) % 7) + 1
            if diatonicDistance == chordStep:
                return thisPitch
        return None

    def getColor(
        self,
        pitchTarget
    ):
        # noinspection PyShadowingNames
        '''
        For a pitch in this Chord, return the color stored in self.editorial,
        or, if set for each component, return the color assigned to this
        component.

        First checks for "is" then "equals"

        >>> p = pitch.Pitch('C4')
        >>> n = note.Note(p)
        >>> n.style.color = 'red'
        >>> c = chord.Chord([n, 'E4'])
        >>> c.getColor(p)
        'red'
        >>> c.getColor('C4')
        'red'
        >>> c.getColor('E4') is None
        True

        The color of any pitch (even a non-existing one) is the color of the chord if
        the color of that pitch is not defined.

        >>> c.style.color = 'pink'
        >>> c.getColor('E4')
        'pink'
        >>> c.getColor('D#7')
        'pink'
        '''
        if isinstance(pitchTarget, str):
            pitchTarget = pitch.Pitch(pitchTarget)
        for n in self._notes:
            if n.pitch is pitchTarget:
                if n.hasStyleInformation and n.style.color is not None:
                    return n.style.color
        for n in self._notes:
            if n.pitch == pitchTarget:
                if n.hasStyleInformation and n.style.color is not None:
                    return n.style.color
        if self.hasStyleInformation:
            return self.style.color  # may be None
        else:
            return None

    def getNotehead(self, p):
        '''
        Given a pitch in this Chord, return an associated notehead
        attribute, or return 'normal' if not defined for that Pitch.

        If the pitch is not found, None will be returned.

        >>> n1 = note.Note('D4')
        >>> n2 = note.Note('G4')
        >>> n2.notehead = 'diamond'
        >>> c1 = chord.Chord([n1, n2])
        >>> c1.getNotehead(c1.pitches[1])
        'diamond'

        >>> c1.getNotehead(c1.pitches[0])
        'normal'

        >>> c1.getNotehead(pitch.Pitch('A#6')) is None
        True

        Will work if the two notes are equal in pitch

        >>> c1.getNotehead(note.Note('G4'))
        'diamond'
        '''
        if hasattr(p, 'pitch'):
            p = p.pitch

        for d in self._notes:
            if d.pitch is p:
                return d.notehead
        for d in self._notes:
            if d.pitch == p:
                return d.notehead
        return None

    def getNoteheadFill(self, p):
        '''
        Given a pitch in this Chord, return an associated noteheadFill
        attribute, or return None if not defined for that Pitch.

        If the pitch is not found, None will also be returned.

        >>> n1 = note.Note('D4')
        >>> n2 = note.Note('G4')
        >>> n2.noteheadFill = True
        >>> c1 = chord.Chord([n1, n2])
        >>> c1.getNoteheadFill(c1.pitches[1])
        True

        >>> print(c1.getNoteheadFill(c1.pitches[0]))
        None

        >>> c1.getNoteheadFill(pitch.Pitch('A#6')) is None
        True

        Will work if the two notes are equal in pitch

        >>> c1.getNoteheadFill(note.Note('G4'))
        True

        Returns None if the pitch is not in the Chord:

        '''
        if hasattr(p, 'pitch'):
            p = p.pitch

        for d in self._notes:
            if d.pitch is p:
                return d.noteheadFill
        for d in self._notes:
            if d.pitch == p:
                return d.noteheadFill
        return None

    def getStemDirection(self, p):
        '''
        Given a pitch in this Chord, return an associated stem attribute, or
        return 'unspecified' if not defined for that Pitch or None.

        If the pitch is not found, None will be returned.

        >>> n1 = note.Note('D4')
        >>> n2 = note.Note('G4')
        >>> n2.stemDirection = 'double'
        >>> c1 = chord.Chord([n1, n2])
        >>> c1.getStemDirection(c1.pitches[1])
        'double'

        >>> c1.getStemDirection(c1.pitches[0])
        'unspecified'

        Will work if the two pitches are equal in pitch

        >>> c1.getStemDirection(note.Note('G4'))
        'double'

        Returns None if a Note or Pitch is not in the Chord

        >>> c1.getStemDirection(pitch.Pitch('A#4')) is None
        True

        '''
        if hasattr(p, 'pitch'):
            p = p.pitch

        for d in self._notes:
            if d.pitch is p:  # compare by obj id first
                return d.stemDirection

        for d in self._notes:
            if d.pitch == p:
                return d.stemDirection
        return None

    def getTie(self, p):
        '''
        Given a pitch in this Chord, return an associated Tie object, or return
        None if not defined for that Pitch.

        >>> c1 = chord.Chord(['d', 'e-', 'b-'])
        >>> t1 = tie.Tie('start')
        >>> c1.setTie(t1, c1.pitches[2])  # just to b-
        >>> c1.getTie(c1.pitches[2]) == t1
        True

        >>> c1.getTie(c1.pitches[0]) is None
        True

        All notes not in chord return None

        >>> c1.getTie(pitch.Pitch('F#2')) is None
        True

        >>> c1.getTie('B-')
        <music21.tie.Tie start>
        '''
        try:
            return self[p].tie
        except KeyError:
            return None

    def getVolume(self, p):
        '''
        For a given Pitch in this Chord, return the
        :class:`~music21.volume.Volume` object.

        Raises an exception if the pitch isn't in the chord
        (TODO: consider changing to be like notehead, etc.)

        >>> c = chord.Chord('C4 F4')
        >>> c[0].volume = 2
        >>> c.getVolume('C4')
        <music21.volume.Volume realized=0.02>

        >>> c.getVolume('F4')  # default
        <music21.volume.Volume realized=0.71>

        >>> c.getVolume('G4')
        Traceback (most recent call last):
        music21.chord.ChordException: the given pitch is not in the Chord: G4
        '''
        try:
            n = self[p]
            # noinspection PyArgumentList
            return n._getVolume(forceClient=self)
        except KeyError:
            raise ChordException(f'the given pitch is not in the Chord: {p}')

    def getZRelation(self) -> Chord | None:
        '''
        Return a Z relation if it exists, otherwise return None.

        >>> chord.fromIntervalVector((1, 1, 1, 1, 1, 1))
        <music21.chord.Chord C C# E F#>

        >>> chord.fromIntervalVector((1, 1, 1, 1, 1, 1)).getZRelation()
        <music21.chord.Chord C D- E- G>

        Z relation will always be zero indexed:

        >>> c = chord.Chord('D D# F# G#')
        >>> c.getZRelation()
        <music21.chord.Chord C D- E- G>

        >>> chord.Chord('C E G').getZRelation() is None
        True
        '''
        if self.hasZRelation:
            chordTablesAddress = self.chordTablesAddress
            v = tables.addressToIntervalVector(chordTablesAddress)
            addresses = tables.intervalVectorToAddress(v)
            # environLocal.printDebug(['addresses', addresses,
            #    'chordTablesAddress', chordTablesAddress])
            # addresses returned here are 2 elements lists
            other = None
            for thisAddress in addresses:
                if thisAddress.forteClass != chordTablesAddress.forteClass:
                    other = thisAddress
            # other should always be defined to not None
            prime = tables.addressToTransposedNormalForm(other)
            return Chord(prime)
        return None
        # c2.getZRelation()  # returns a list in non-ET12 space...
        # <music21.chord.ForteSet at 0x234892>

    def hasAnyEnharmonicSpelledPitches(self) -> bool:
        '''
        Returns True if for any given pitchClass there is at most one spelling of the note
        (in any octave).

        >>> cChord = chord.Chord('C4 E4 G4 C5')
        >>> cChord.hasAnyEnharmonicSpelledPitches()
        False

        Notice that having a C in two different octaves is no problem.  However, this is False:

        >>> cChord = chord.Chord('C4 E4 G4 B#4')
        >>> cChord.hasAnyEnharmonicSpelledPitches()
        True
        '''
        if len(self._unorderedPitchClasses()) != len(set(p.name for p in self.pitches)):
            return True
        else:
            return False

    def hasAnyRepeatedDiatonicNote(self) -> bool:
        '''
        Returns True if for any diatonic note (e.g., C or C# = C) there are two or more
        different notes (such as E and E-) in the chord. If there are no repeated
        scale degrees, return False.

        >>> cChord = chord.Chord(['C', 'E', 'E-', 'G'])
        >>> cChord.hasAnyRepeatedDiatonicNote()
        True

        This routine is helpful for anything that works with Generic intervals and chord
        steps such as `.third` which makes sure that checking for root, second, third,
        ..., seventh will actually find all the different notes.

        This following example returns False because chromatically identical notes of
        different scale degrees do not count as a repeated diatonic note.
        (See :meth:`~music21.chord.Chord.hasAnyEnharmonicSpelledPitches` for that method)

        >>> other = chord.Chord(['C', 'E', 'F-', 'G'])
        >>> other.hasAnyRepeatedDiatonicNote()
        False
        '''
        if len(set(p.step for p in self.pitches)) != len(set(p.name for p in self.pitches)):
            return True
        else:
            return False

    def hasRepeatedChordStep(self, chordStep, *, testRoot=None):
        '''
        Returns True if chordStep above testRoot (or self.root()) has two
        or more different notes (such as E and E-) in it.  Otherwise
        returns False.

        >>> cChord = chord.Chord(['G2', 'E4', 'E-5', 'C6'])
        >>> cChord.hasRepeatedChordStep(3)
        True

        >>> cChord.hasRepeatedChordStep(5)
        False

        '''
        if testRoot is None:
            testRoot = self.root()
            if testRoot is None:
                raise ChordException('Cannot run hasRepeatedChordStep without a root')

        first = self.intervalFromChordStep(chordStep)
        for thisPitch in self.pitches:
            thisInterval = interval.Interval(testRoot, thisPitch)
            if thisInterval.diatonic.generic.mod7 == chordStep:
                if thisInterval.chromatic.mod12 - first.chromatic.mod12 != 0:
                    return True

        return False

    def intervalFromChordStep(self, chordStep, *, testRoot=None):
        '''
        Exactly like semitonesFromChordStep, except it returns the interval
        itself instead of the number of semitones:

        >>> cmaj = chord.Chord(['C', 'E', 'G'])
        >>> cmaj.intervalFromChordStep(3)  # will return the interval between C and E
        <music21.interval.Interval M3>

        >>> cmaj.intervalFromChordStep(5)  # will return the interval between C and G
        <music21.interval.Interval P5>

        >>> print(cmaj.intervalFromChordStep(6))
        None

        '''
        if testRoot is None:
            try:
                testRoot = self.root()
            except ChordException:
                raise ChordException('Cannot run intervalFromChordStep without a root')
            if testRoot is None:
                raise ChordException('Cannot run intervalFromChordStep without a root')
        for thisPitch in self.pitches:
            thisInterval = interval.Interval(testRoot, thisPitch)
            if thisInterval.diatonic.generic.mod7 == chordStep:
                return thisInterval
        return None

    @overload
    def inversion(
        self,
        newInversion: int,
        *,
        find: bool = True,
        testRoot: pitch.Pitch | None = None,
        transposeOnSet: bool = True
    ) -> None:
        return None  # dummy until Astroid 1015 is fixed

    @overload
    def inversion(
        self,
        newInversion: None = None,
        *,
        find: bool = True,
        testRoot: pitch.Pitch | None = None,
        transposeOnSet: bool = True
    ) -> int:
        return -1  # dummy until Astroid 1015 is fixed

    def inversion(
        self,
        newInversion: int | None = None,
        *,
        find: bool = True,
        testRoot: pitch.Pitch | None = None,
        transposeOnSet: bool = True
    ) -> int | None:
        '''
        Find the chord's inversion or (if called with a number) set the chord to
        the new inversion.

        When called without a number argument, returns an integer (or None)
        representing which inversion (if any)
        the chord is in. The Chord does not have to be complete, in which case
        this function determines the inversion by looking at the relationship
        of the bass note to the root.

        Returns a maximum value of 5 for the fifth inversion of a thirteenth chord.
        Returns 0 if the bass to root interval is a unison
        or if interval is not a common inversion (1st-5th).
        The octave of the bass and root are irrelevant to this calculation of inversion.
        Returns None if the Chord has no pitches.

        >>> g7 = chord.Chord(['g4', 'b4', 'd5', 'f5'])
        >>> g7.inversion()
        0
        >>> g7.inversion(1)
        >>> g7
        <music21.chord.Chord B4 D5 F5 G5>

        With implicit octaves, D becomes the bass (since octaves start on C):

        >>> g7_implicit = chord.Chord(['g', 'b', 'd', 'f'])
        >>> g7_implicit.inversion()
        2

        Note that in inverting a chord with implicit octaves, some
        pitches will gain octave designations, but not necessarily all of them
        (this behavior might change in the future):

        >>> g7_implicit.inversion(1)
        >>> g7_implicit
        <music21.chord.Chord B D5 F5 G5>

        Examples of each inversion:

        >>> cTriad1stInversion = chord.Chord(['E1', 'G1', 'C2'])
        >>> cTriad1stInversion.inversion()
        1

        >>> cTriad2ndInversion = chord.Chord(['G1', 'E2', 'C2'])
        >>> cTriad2ndInversion.inversion()
        2

        >>> dSeventh3rdInversion = chord.Chord(['C4', 'B4'])
        >>> dSeventh3rdInversion.bass(pitch.Pitch('B4'))
        >>> dSeventh3rdInversion.inversion()
        3

        >>> gNinth4thInversion = chord.Chord(['G4', 'B4', 'D5', 'F5', 'A4'])
        >>> gNinth4thInversion.bass(pitch.Pitch('A4'))
        >>> gNinth4thInversion.inversion()
        4

        >>> bbEleventh5thInversion = chord.Chord(['B-', 'D', 'F', 'A', 'C', 'E-'])
        >>> bbEleventh5thInversion.bass(pitch.Pitch('E-4'))
        >>> bbEleventh5thInversion.inversion()
        5

        Repeated notes do not affect the inversion:

        >>> gMajRepeats = chord.Chord(['G4', 'B5', 'G6', 'B6', 'D7'])
        >>> gMajRepeats.inversion(2)
        >>> gMajRepeats
        <music21.chord.Chord D7 G7 B7 G8 B8>

        >>> gMajRepeats.inversion(3)
        Traceback (most recent call last):
        music21.chord.ChordException: Could not invert chord...inversion may not exist


        If testRoot is True then that temporary root is used instead of self.root().

        Get the inversion for a seventh chord showing different roots

        >>> dim7 = chord.Chord('B4 D5 F5 A-5 C6 E6 G6')
        >>> dim7.inversion()
        0
        >>> dim7.inversion(testRoot=pitch.Pitch('D5'))
        6
        >>> dim7.inversion('six-four')
        Traceback (most recent call last):
        music21.chord.ChordException: Inversion must be an integer, got: <class 'str'>

        Chords without pitches or otherwise impossible chords return -1, indicating
        no normal inversion.

        >>> chord.Chord().inversion(testRoot=pitch.Pitch('C5'))
        -1

        For Harmony subclasses, this method does not check to see if
        the inversion is reasonable according to the figure provided.
        see :meth:`~music21.harmony.ChordSymbol.inversionIsValid`
        for checker method on ChordSymbolObjects.

        If only two pitches given, an inversion is still returned, often as
        if it were a triad:

        >>> chord.Chord('C4 G4').inversion()
        0
        >>> chord.Chord('G4 C5').inversion()
        2

        If transposeOnSet is False then setting the inversion simply
        sets the value to be returned later, which might be useful for
        cases where the chords are poorly spelled, or there is an added note.

        * Changed in v8: chords without pitches
        '''
        if not self.pitches:
            return -1

        if testRoot is not None:
            rootPitch = testRoot
        else:
            rootPitch = self.root()

        if newInversion is not None:
            try:
                int_newInversion = int(newInversion)
            except (ValueError, TypeError):
                raise ChordException(f'Inversion must be an integer, got: {type(newInversion)}')
            self._setInversion(int_newInversion, rootPitch, transposeOnSet)
            return None
        elif ('inversion' not in self._overrides and find) or testRoot is not None:
            try:
                if rootPitch is None or self.bass() is None:
                    return -1
            except ChordException:
                raise ChordException('Not a normal inversion')  # can this be run?

            return self._findInversion(rootPitch)
        elif 'inversion' in self._overrides:
            return self._overrides['inversion']
        else:
            return -1

    def _setInversion(self,
                      newInversion: int,
                      rootPitch: pitch.Pitch,
                      transposeOnSet: bool
                      ) -> None:
        '''
        Helper function for inversion(int)
        '''
        if transposeOnSet is False:
            self._overrides['inversion'] = newInversion
            return
        # could have set bass or root externally
        numberOfRunsBeforeCrashing = len(self.pitches) + 2
        soughtInversion = newInversion

        if 'inversion' in self._overrides:
            del self._overrides['inversion']
        if 'bass' in self._overrides:
            # bass might have been overridden for a different octave
            del self._overrides['bass']
        currentInversion = self.inversion(find=True)
        while currentInversion != soughtInversion and numberOfRunsBeforeCrashing > 0:
            currentMaxMidi = max(self.pitches).ps
            tempBassPitch = self.bass()
            while tempBassPitch.ps < currentMaxMidi:
                if tempBassPitch.octave is not None:
                    tempBassPitch.octave += 1
                else:
                    tempBassPitch.octave = tempBassPitch.implicitOctave + 1

            # housekeeping for next loop tests
            self.clearCache()
            currentInversion = self.inversion(find=True)
            numberOfRunsBeforeCrashing -= 1

        if numberOfRunsBeforeCrashing == 0:
            raise ChordException('Could not invert chord...inversion may not exist')

        self.sortAscending(inPlace=True)

    def _findInversion(self, rootPitch: pitch.Pitch) -> int:
        '''
        Helper function for .inversion()
        '''
        # bassNote = self.bass()
        # do all interval calculations with bassNote being one octave below root note
        tempBassPitch = copy.deepcopy(self.bass())
        tempBassPitch.octave = 1
        tempRootPitch = copy.deepcopy(rootPitch)
        tempRootPitch.octave = 2

        bassToRoot = interval.notesToGeneric(tempBassPitch,
                                             tempRootPitch).simpleDirected
        # print('bassToRoot', bassToRoot)
        if bassToRoot == 1:
            inv = 0
        elif bassToRoot == 6:  # triads
            inv = 1
        elif bassToRoot == 4:  # triads
            inv = 2
        elif bassToRoot == 2:  # sevenths
            inv = 3
        elif bassToRoot == 7:  # ninths
            inv = 4
        elif bassToRoot == 5:  # eleventh
            inv = 5
        elif bassToRoot == 3:  # thirteenth
            inv = 6
        else:
            inv = -1  # no longer raise an exception if not normal inversion

        # is this cache worth it? or more trouble than it's worth...
        self._cache['inversion'] = inv
        return inv

    def inversionName(self) -> int | None:
        '''
        Returns an integer representing the common abbreviation for the
        inversion the chord is in. If chord is not in a common inversion,
        returns None.

        Third inversion sevenths return 42 not 2.

        >>> a = chord.Chord(['G3', 'B3', 'F3', 'D3'])
        >>> a.inversionName()
        43
        '''
        inv: int  # pylint requires this outside of the "try" to avoid "invalid-sequence-index"

        try:
            inv = self.inversion()
        except ChordException:
            return None

        if inv == -1:
            return None

        seventhMapping = [7, 65, 43, 42]
        triadMapping = [53, 6, 64]

        if self.isSeventh() or self.seventh is not None:
            if 0 <= inv <= 3:
                return seventhMapping[inv]
            else:
                raise ChordException(f'Not a normal inversion for a seventh: {inv!r}')
        elif self.isTriad():
            if 0 <= inv <= 2:
                return triadMapping[inv]
            else:
                raise ChordException(f'Not a normal inversion for a triad: {inv!r}')
        else:
            raise ChordException('Not a triad or Seventh, cannot determine inversion.')

    def inversionText(self) -> str:
        '''
        A helper method to return a readable inversion text (with capitalization) for a chord:

        >>> chord.Chord('C4 E4 G4').inversionText()
        'Root Position'
        >>> chord.Chord('E4 G4 C5').inversionText()
        'First Inversion'

        >>> chord.Chord('B-3 C4 E4 G4').inversionText()
        'Third Inversion'

        >>> chord.Chord().inversionText()
        'Unknown Position'
        '''
        UNKNOWN = 'Unknown Position'
        inv: int  # pylint requires this outside of the "try" to avoid "invalid-sequence-index"

        try:
            inv = self.inversion()
        except ChordException:
            return UNKNOWN

        if inv == -1:
            return UNKNOWN

        if inv == 0:
            return 'Root Position'

        return common.numberTools.ordinals[inv] + ' Inversion'



    def isAugmentedSixth(self, *, permitAnyInversion=False):
        '''
        returns True if the chord is an Augmented 6th chord in normal inversion.
        (that is, in first inversion for Italian and German and second for French and Swiss)

        >>> c = chord.Chord(['A-3', 'C4', 'E-4', 'F#4'])
        >>> c.isAugmentedSixth()
        True

        Spelling matters

        >>> c.pitches[3].getEnharmonic(inPlace=True)
        >>> c
        <music21.chord.Chord A-3 C4 E-4 G-4>
        >>> c.isAugmentedSixth()
        False

        Italian...

        >>> c = chord.Chord(['A-3', 'C4', 'F#4'])
        >>> c.isAugmentedSixth()
        True

        If `permitAnyInversion` is True then any inversion is allowed.

        '''
        # cardinality is just used to speed up the call to avoid checking multiple augmented
        # 6ths on a triad, etc.  The fact that Ab C F# Gb will have cardinality of 3
        # but fail isItalianAugmentedSixth is not a problem.
        cardinality = self.pitchClassCardinality
        if cardinality == 3 and self.isItalianAugmentedSixth(permitAnyInversion=permitAnyInversion):
            return True
        if cardinality == 4:
            if self.isFrenchAugmentedSixth(permitAnyInversion=permitAnyInversion):
                return True
            elif self.isGermanAugmentedSixth(permitAnyInversion=permitAnyInversion):
                return True
            elif self.isSwissAugmentedSixth(permitAnyInversion=permitAnyInversion):
                return True

        return False

    @cacheMethod
    def isAugmentedTriad(self):
        '''
        Returns True if chord is an Augmented Triad, that is,
        if it contains only notes that are
        either in unison with the root, a major third above the root,
        or an augmented fifth above the
        root. Additionally, the Chord must contain at least one of each third and
        fifth above the root.

        The chord might not seem to need to be spelled correctly
        since incorrectly spelled Augmented Triads are
        usually augmented triads in some other inversion
        (e.g. C-E-Ab is a second-inversion augmented triad; C-Fb-Ab
        is in first inversion).  However, B#-Fb-Ab does return False as it is not a
        stack of two major thirds in any inversion.

        Returns False if is not an augmented triad.

        >>> c = chord.Chord(['C4', 'E4', 'G#4'])
        >>> c.isAugmentedTriad()
        True
        >>> c = chord.Chord(['C4', 'E4', 'G4'])
        >>> c.isAugmentedTriad()
        False

        Other spellings will give other roots!

        >>> c = chord.Chord(['C4', 'E4', 'A-4'])
        >>> c.isAugmentedTriad()
        True
        >>> c.root()
        <music21.pitch.Pitch A-4>

        >>> c = chord.Chord(['C4', 'F-4', 'A-4'])
        >>> c.isAugmentedTriad()
        True
        >>> c = chord.Chord(['B#4', 'F-4', 'A-4'])
        >>> c.isAugmentedTriad()
        False

        >>> chord.Chord().isAugmentedTriad()
        False
        '''
        return self._checkTriadType((3, 12, 0), 4, 8)

    @cacheMethod
    def isConsonant(self):
        # noinspection PyShadowingNames
        '''
        Returns True if the chord is:

        * one pitch (always consonant)

        * two pitches: uses :meth:`~music21.interval.Interval.isConsonant()` , which
             checks if the interval is a major or minor third or sixth or perfect fifth.

        * three pitches: if chord is a major or minor triad not in second inversion.

        These rules define all common-practice consonances
        (and earlier back to about 1300 all imperfect consonances)

        >>> c1 = chord.Chord(['C3', 'E4', 'G5'])
        >>> c1.isConsonant()
        True

        >>> c2 = chord.Chord(['G3', 'E-4', 'C5'])
        >>> c2.isConsonant()
        False

        >>> c3 = chord.Chord(['F2', 'A2', 'C3', 'E-3'])
        >>> c3.isConsonant()
        False

        >>> c4 = chord.Chord(['C1', 'G1', 'C2', 'G2', 'C3', 'G3'])
        >>> c4.isConsonant()
        True

        >>> c5 = chord.Chord(['G1', 'C2', 'G2', 'C3', 'G3'])
        >>> c5.isConsonant()
        False

        >>> c6 = chord.Chord(['F#'])
        >>> c6.isConsonant()
        True

        >>> c7 = chord.Chord(['C1', 'C#1', 'D-1'])
        >>> c7.isConsonant()
        False

        Spelling does matter:

        >>> c8 = chord.Chord(['D-4', 'G#4'])
        >>> c8.isConsonant()
        False

        >>> c9 = chord.Chord(['D3', 'A2', 'D2', 'D2', 'A4'])
        >>> c9.isConsonant()
        True

        >>> c10 = chord.Chord(['D3', 'A2', 'D2', 'D2', 'A1'])
        >>> c10.isConsonant()
        False

        >>> c11 = chord.Chord(['F3', 'D4', 'A4'])
        >>> c11.isConsonant()
        True

        >>> c12 = chord.Chord(['F3', 'D4', 'A4', 'E#4'])
        >>> c12.isConsonant()
        False

        OMIT_FROM_DOCS

        Weird things used to happen when some notes have octaves and some don't:

        >>> c13 = chord.Chord(['A4', 'B4', 'A'])
        >>> c14 = c13.removeRedundantPitchNames(inPlace=False)
        >>> c14
        <music21.chord.Chord A4 B4>

        >>> i14 = interval.Interval(c14.pitches[0], c14.pitches[1])
        >>> i14
        <music21.interval.Interval M2>

        >>> i14.isConsonant()
        False

        >>> c13.isConsonant()
        False

        '''
        c2 = self.removeRedundantPitchNames(inPlace=False)
        if len(c2.pitches) == 1:
            return True
        elif len(c2.pitches) == 2:
            c3 = self.closedPosition()
            # to get from lowest to highest for P4 protection
            c4 = c3.removeRedundantPitches(inPlace=False)
            i = interval.Interval(c4.pitches[0], c4.pitches[1])
            return i.isConsonant()
        elif len(c2.pitches) == 3:
            if ((self.isMajorTriad() is True or self.isMinorTriad() is True)
                    and (self.inversion() != 2)):
                return True
            else:
                return False
        else:
            return False

    @cacheMethod
    def isDiminishedSeventh(self):
        '''
        Returns True if chord is a Diminished Seventh, that is,
        if it contains only notes that are
        either in unison with the root, a minor third above the root,
        a diminished fifth, or a minor seventh
        above the root. Additionally, must contain at least one of
        each third and fifth above the root.
        Chord must be spelled correctly. Otherwise returns false.

        >>> a = chord.Chord(['c', 'e-', 'g-', 'b--'])
        >>> a.isDiminishedSeventh()
        True

        >>> chord.Chord().isDiminishedSeventh()
        False
        '''
        return self.isSeventhOfType((0, 3, 6, 9))

    def isSeventhOfType(self, intervalArray):
        '''
        Returns True if chord is a seventh chord of a particular type
        as specified by intervalArray.  For instance `.isDiminishedSeventh()`
        is just a thin wrapper around `.isSeventhOfType([0, 3, 6, 9])`
        and `isDominantSeventh()` has intervalArray([0, 4, 7, 10])

        intervalArray can be any iterable.

        Though it checks on intervalArray, it does make sure that it is a
        seventh chord, not D--, D##, G, B-

        >>> chord.Chord('C E G B-').isSeventhOfType((0, 4, 7, 10))
        True
        >>> chord.Chord('C E G B-').isSeventhOfType((0, 3, 7, 10))
        False
        >>> chord.Chord('D-- D## G B-').isSeventhOfType((0, 4, 7, 10))
        False
        '''
        if not self.isSeventh():
            return False

        root = self.root()

        for thisPitch in self.pitches:
            thisInterval = interval.Interval(root, thisPitch)
            if thisInterval.chromatic.mod12 not in intervalArray:
                return False
        return True

    @cacheMethod
    def isDiminishedTriad(self) -> bool:
        '''
        Returns True if chord is a Diminished Triad, that is,
        if it contains only notes that are
        either in unison with the root, a minor third above the
        root, or a diminished fifth above the
        root. Additionally, must contain at least one of each
        third and fifth above the root.
        Chord must be spelled correctly. Otherwise returns false.

        >>> cChord = chord.Chord(['C', 'E-', 'G-'])
        >>> cChord.isDiminishedTriad()
        True
        >>> other = chord.Chord(['C', 'E-', 'F#'])
        >>> other.isDiminishedTriad()
        False

        OMIT_FROM_DOCS

        >>> chord.Chord().isDiminishedTriad()
        False
        >>> other = chord.Chord(['C', 'E-', 'F#', 'G-'])
        >>> other.isDiminishedTriad()
        False

        This is in an OMIT section
        '''
        return self._checkTriadType((3, 10, 0), 3, 6)

    @cacheMethod
    def isDominantSeventh(self) -> bool:
        '''
        Returns True if chord is a Dominant Seventh, that is,
        if it contains only notes that are
        either in unison with the root, a major third above the root,
        a perfect fifth, or a major seventh
        above the root. Additionally, must contain at least one of
        each third and fifth above the root.
        Chord must be spelled correctly. Otherwise returns false.

        >>> a = chord.Chord(['b', 'g', 'd', 'f'])
        >>> a.isDominantSeventh()
        True

        >>> chord.Chord().isDominantSeventh()
        False

        >>> c2 = chord.Chord('C4 E4 G4 A#4')
        >>> c2.isDominantSeventh()
        False
        '''
        return self.isSeventhOfType((0, 4, 7, 10))

    @cacheMethod
    def isFalseDiminishedSeventh(self) -> bool:
        '''
        Returns True if chord is a Diminished Seventh, that is,
        if it contains only notes that are
        either in unison with the root, a minor third above the root,
        a diminished fifth, or a diminished seventh
        above the root. Additionally, must contain at least one of
        each third and fifth above the root.
        Chord MAY BE SPELLED INCORRECTLY. Otherwise returns False.


        >>> c = chord.Chord('C D# G- A')
        >>> c.isFalseDiminishedSeventh()
        True

        >>> chord.Chord().isFalseDiminishedSeventh()
        False

        >>> chord.Chord('C4 E4 G4').isFalseDiminishedSeventh()
        False

        Correctly spelled diminished seventh chords are also false diminished sevenths.

        >>> chord.Chord('C4 E-4 G-4 B--4').isFalseDiminishedSeventh()
        True
        '''
        return self.chordTablesAddress[:3] == (4, 28, 0)

    def isFrenchAugmentedSixth(self, *, permitAnyInversion=False) -> bool:
        '''
        Returns True if the chord is a French augmented sixth chord
        (flat 6th scale degree in bass, tonic, second scale degree, and raised 4th).

        N.B. The root() method of music21.chord.Chord determines
        the root based on the note with
        the most thirds above it. However, under this definition, a
        1st-inversion french augmented sixth chord
        resembles a second inversion chord, not the first inversion
        subdominant chord it is based
        upon. We fix this by adjusting the root. First, however, we
        check to see if the chord is
        in second inversion to begin with, otherwise it is not
        a Fr+6 chord. This is to avoid ChordException errors.

        >>> fr6a = chord.Chord(['A-3', 'C4', 'D4', 'F#4'])
        >>> fr6a.isFrenchAugmentedSixth()
        True

        Spelling matters:

        >>> fr6b = chord.Chord(['A-3', 'C4', 'D4', 'G-4'])
        >>> fr6b.isFrenchAugmentedSixth()
        False

        >>> fr6b = chord.Chord(['A-3', 'C4', 'E--4', 'F#4'])
        >>> fr6b.isFrenchAugmentedSixth()
        False

        Inversion matters...

        >>> fr6c = chord.Chord(['C4', 'D4', 'F#4', 'A-4'])
        >>> fr6c.isFrenchAugmentedSixth()
        False

        Unless `permitAnyInversion` is True

        >>> fr6c.isFrenchAugmentedSixth(permitAnyInversion=True)
        True

        * Changed in v7: `permitAnyInversion` added

        OMIT_FROM_DOCS

        >>> chord.Chord().isFrenchAugmentedSixth()
        False

        >>> fr6d = chord.Chord(['A-3', 'C-4', 'D4', 'F#4'])
        >>> fr6d.isFrenchAugmentedSixth()
        False
        '''
        return self._isAugmentedSixthHelper(
            (4, 25, 0),
            2,
            permitAnyInversion,
            [('M3', 'm-6'), ('d5', 'A-4'), ('m7', 'M-2')]
        )

    def isGermanAugmentedSixth(self, *, permitAnyInversion=False) -> bool:
        '''
        Returns True if the chord is a German augmented sixth chord
        (flat 6th scale degree in bass, tonic, flat third scale degree, and raised 4th).


        >>> gr6a = chord.Chord(['A-3', 'C4', 'E-4', 'F#4'])
        >>> gr6a.isGermanAugmentedSixth()
        True

        Spelling matters (see isSwissAugmentedSixth)

        >>> gr6b = chord.Chord(['A-3', 'C4', 'D#4', 'F#4'])
        >>> gr6b.isGermanAugmentedSixth()
        False

        Inversion matters...

        >>> gr6c = chord.Chord(['C4', 'E-4', 'F#4', 'A-4'])
        >>> gr6c.isGermanAugmentedSixth()
        False

        unless `permitAnyInversion` is True

        >>> gr6c.isGermanAugmentedSixth(permitAnyInversion=True)
        True

        * Changed in v7: `permitAnyInversion` added

        OMIT_FROM_DOCS

        >>> chord.Chord().isGermanAugmentedSixth()
        False

        >>> gr6d = chord.Chord(['A-3', 'C-4', 'E-4', 'F#4'])
        >>> gr6d.isGermanAugmentedSixth()
        False

        '''
        return self._isAugmentedSixthHelper(
            (4, 27, -1),
            1,
            permitAnyInversion,
            [('d3', 'A-6'), ('d5', 'A-4'), ('d7', 'A-2')]
        )

    @cacheMethod
    def isHalfDiminishedSeventh(self) -> bool:
        '''
        Returns True if chord is a Half Diminished Seventh, that is,
        if it contains only notes that are
        either in unison with the root, a minor third above the root, a
        diminished fifth, or a major seventh
        above the root. Additionally, must contain at least one of each third,
        fifth, and seventh above the root.
        Chord must be spelled correctly. Otherwise returns false.


        >>> c1 = chord.Chord(['C4', 'E-4', 'G-4', 'B-4'])
        >>> c1.isHalfDiminishedSeventh()
        True

        Incorrectly spelled chords are not considered half-diminished sevenths
        >>> c2 = chord.Chord(['C4', 'E-4', 'G-4', 'A#4'])
        >>> c2.isHalfDiminishedSeventh()
        False

        Nor are incomplete chords
        >>> c3 = chord.Chord(['C4', 'G-4', 'B-4'])
        >>> c3.isHalfDiminishedSeventh()
        False

        >>> chord.Chord().isHalfDiminishedSeventh()
        False
        '''
        return self.isSeventhOfType((0, 3, 6, 10))

    @cacheMethod
    def isIncompleteMajorTriad(self) -> bool:
        '''
        Returns True if the chord is an incomplete Major triad, or, essentially,
        a dyad of root and major third


        >>> c1 = chord.Chord(['C4', 'E3'])
        >>> c1.isMajorTriad()
        False
        >>> c1.isIncompleteMajorTriad()
        True

        Note that complete major triads return False:

        >>> c2 = chord.Chord(['C4', 'E3', 'G5'])
        >>> c2.isIncompleteMajorTriad()
        False

        Remember, MAJOR Triad...

        >>> c3 = chord.Chord(['C4', 'E-3'])
        >>> c3.isIncompleteMajorTriad()
        False

        Must be spelled properly

        >>> c1 = chord.Chord(['C4', 'F-4'])
        >>> c1.isIncompleteMajorTriad()
        False

        Empty Chords return False

        >>> chord.Chord().isIncompleteMajorTriad()
        False

        OMIT_FROM_DOCS

        Swap the two notes:

        >>> c1 = chord.Chord(['C####4', 'E----4'])
        >>> c1.isIncompleteMajorTriad()
        False
        '''
        if self.chordTablesAddress[:2] != (2, 4):
            return False

        third = self.third
        if third is None:
            return False

        for thisPitch in self.pitches:
            thisInterval = interval.Interval(self.root(), thisPitch)
            if thisInterval.chromatic.mod12 not in (0, 4):
                return False

        return True

    @cacheMethod
    def isIncompleteMinorTriad(self) -> bool:
        '''
        returns True if the chord is an incomplete Minor triad, or, essentially,
        a dyad of root and minor third

        >>> c1 = chord.Chord(['C4', 'E-3'])
        >>> c1.isMinorTriad()
        False
        >>> c1.isIncompleteMinorTriad()
        True
        >>> c2 = chord.Chord(['C4', 'E-3', 'G5'])
        >>> c2.isIncompleteMinorTriad()
        False

        OMIT_FROM_DOCS

        >>> c3 = chord.Chord(['C4', 'E4'])
        >>> c3.isIncompleteMinorTriad()
        False

        >>> c3 = chord.Chord(['C4', 'D#4'])
        >>> c3.isIncompleteMinorTriad()
        False

        >>> c3 = chord.Chord(['C###4', 'E---4'])
        >>> c3.isIncompleteMinorTriad()
        False

        >>> chord.Chord().isIncompleteMinorTriad()
        False
        '''
        if self.chordTablesAddress[:2] != (2, 3):
            return False

        third = self.third
        if third is None:
            return False

        for thisPitch in self.pitches:
            thisInterval = interval.Interval(self.root(), thisPitch)
            if thisInterval.chromatic.mod12 not in (0, 3):
                return False

        return True

    def isItalianAugmentedSixth(self, *, restrictDoublings=False, permitAnyInversion=False) -> bool:
        '''
        Returns True if the chord is a properly spelled Italian augmented sixth chord in
        first inversion.  Otherwise returns False.

        If restrictDoublings is set to True then only the tonic may be doubled.

        >>> c1 = chord.Chord(['A-4', 'C5', 'F#6'])
        >>> c1.isItalianAugmentedSixth()
        True

        Spelling matters:

        >>> c2 = chord.Chord(['A-4', 'C5', 'G-6'])
        >>> c2.isItalianAugmentedSixth()
        False

        So does inversion:

        >>> c3 = chord.Chord(['F#4', 'C5', 'A-6'])
        >>> c3.isItalianAugmentedSixth()
        False
        >>> c4 = chord.Chord(['C5', 'A-5', 'F#6'])
        >>> c4.isItalianAugmentedSixth()
        False

        If inversions don't matter to you, add `permitAnyInversion=True`:

        >>> c3.isItalianAugmentedSixth(permitAnyInversion=True)
        True
        >>> c4.isItalianAugmentedSixth(permitAnyInversion=True)
        True

        If doubling rules are turned on then only the tonic can be doubled:

        >>> c4 = chord.Chord(['A-4', 'C5', 'F#6', 'C6', 'C7'])
        >>> c4.isItalianAugmentedSixth(restrictDoublings=True)
        True
        >>> c5 = chord.Chord(['A-4', 'C5', 'F#6', 'C5', 'F#7'])
        >>> c5.isItalianAugmentedSixth(restrictDoublings=True)
        False
        >>> c5.isItalianAugmentedSixth(restrictDoublings=False)
        True

        * Changed in v7: `restrictDoublings` is keyword only.  Added `permitAnyInversion`.
        '''
        aug6check = self._isAugmentedSixthHelper(
            (3, 8, 1),
            1,
            permitAnyInversion,
            [('d3', 'A-6'), ('d5', 'A-4')]
        )
        if not aug6check:
            return False

        if restrictDoublings:
            root = self.root()
            third = self.third
            fifth = self.fifth

            # only the tonic (that is, fifth) can be doubled...
            for p in self.pitches:
                if p.name == fifth.name:
                    continue
                if p is not third and p is not root:
                    return False
        return True

    def _isAugmentedSixthHelper(
        self,
        chordTableAddress: tuple[int, int, int],
        requiredInversion: int,
        permitAnyInversion: bool,
        intervalsCheck: list[tuple[str, str]],
    ) -> bool:
        '''
        Helper method for simplifying checking Italian, German, etc. Augmented
        Sixth chords
        '''
        if self.chordTablesAddress[:3] != chordTableAddress:
            return False

        if self.hasAnyEnharmonicSpelledPitches():
            return False

        # Chord must be in first inversion.
        try:
            if not permitAnyInversion and self.inversion() != requiredInversion:
                return False
        except ChordException:
            return False

        root = self.root()
        third = self.third
        if third is None:
            return False
        thirdInterval = interval.Interval(root, third)
        if thirdInterval.directedSimpleName not in intervalsCheck[0]:
            return False

        fifth = self.fifth
        if fifth is None:
            return False
        fifthInterval = interval.Interval(root, fifth)
        if fifthInterval.directedSimpleName not in intervalsCheck[1]:
            return False

        if len(intervalsCheck) < 3:
            return True

        seventh = self.seventh
        if seventh is None:
            return False
        seventhInterval = interval.Interval(root, seventh)
        if seventhInterval.directedSimpleName not in intervalsCheck[2]:
            return False

        return True

    def _checkTriadType(self, chordAddress, thirdSemitones, fifthSemitones):
        '''
        Helper method for `isMajorTriad`, `isMinorTriad`, `isDiminishedTriad`, and
        `isAugmentedTriad` that checks the chordAddress first, then the number
        of semitones the third should be and fifth.  Deals with strange corner
        cases like C, E###, G--- not being a major triad, as quickly as possible.
        '''
        # chordTablesAddress takes only 39 microseconds compared to 220 for
        # rest of routine, so might as well short-circuit for false
        if self.chordTablesAddress[:3] != chordAddress:
            return False

        if not self.isTriad():
            return False

        if self.hasAnyEnharmonicSpelledPitches():
            return False

        # these are cached, and guaranteed to be non-None by isTriad()
        third = self.third
        fifth = self.fifth

        root = self.root()
        rootPitchClass = root.pitchClass
        thirdInterval = (third.pitchClass - rootPitchClass) % 12
        if thirdInterval != thirdSemitones:
            return False
        fifthInterval = (fifth.pitchClass - rootPitchClass) % 12
        if fifthInterval != fifthSemitones:
            return False

        return True

    @cacheMethod
    def isMajorTriad(self):
        '''
        Returns True if chord is a Major Triad, that is, if it contains only notes that are
        either in unison with the root, a major third above the root, or a perfect fifth above the
        root. Additionally, must contain at least one of each third and fifth above the root.
        Chord must be spelled correctly. Otherwise returns false.

        Example:

        >>> cChord = chord.Chord(['C', 'E', 'G'])
        >>> other = chord.Chord(['C', 'G'])
        >>> cChord.isMajorTriad()
        True
        >>> other.isMajorTriad()
        False

        Notice that the proper spelling of notes is crucial

        >>> chord.Chord(['B-', 'D', 'F']).isMajorTriad()
        True
        >>> chord.Chord(['A#', 'D', 'F']).isMajorTriad()
        False

        (See: :meth:`~music21.chord.Chord.forteClassTn` to catch this case; major triads
        in the forte system are 3-11B no matter how they are spelled.)

        >>> chord.Chord(['A#', 'D', 'F']).forteClassTn == '3-11B'
        True


        OMIT_FROM_DOCS

        Strange chords like [C,E###,G---] used to return True.  E### = G
        and G--- = E, so the chord is found to be a major triad, even though it should
        not be.  This bug is now fixed.

        >>> chord.Chord(['C', 'E###', 'G---']).isMajorTriad()
        False
        >>> chord.Chord(['C', 'E', 'G', 'E###', 'G---']).isMajorTriad()
        False


        >>> chord.Chord().isMajorTriad()
        False
        '''
        return self._checkTriadType((3, 11, -1), 4, 7)

    @cacheMethod
    def isMinorTriad(self):
        '''
        Returns True if chord is a Minor Triad, that is, if it contains only notes that are
        either in unison with the root, a minor third above the root, or a perfect fifth above the
        root. Additionally, must contain at least one of each third and fifth above the root.
        Chord must be spelled correctly. Otherwise returns false.

        Example:

        >>> cChord = chord.Chord(['C', 'E-', 'G'])
        >>> cChord.isMinorTriad()
        True
        >>> other = chord.Chord(['C', 'E', 'G'])
        >>> other.isMinorTriad()
        False

        OMIT_FROM_DOCS

        >>> chord.Chord().isMinorTriad()
        False
        '''
        return self._checkTriadType((3, 11, 1), 3, 7)

    def isTranspositionallySymmetrical(self, *, requireIntervallicEvenness=False) -> bool:
        '''
        Returns True if the Chord is symmetrical under transposition
        and False otherwise.  A pitch-class-based way of looking at this, is
        can all the pitch classes be transposed up some number of semitones 1-11
        and end up with the same pitch-classes.  Like the dyad F-B can have each
        note transposed up 6 semitones and get another B-F = F-B dyad.

        A tonally-focused way of looking at this would be to ask, "Are we unable
        to distinguish root position vs. some inversion of the basic chord by ear alone?"
        For instance, we can see (visually) that C-Eb-Gb-Bbb is a diminished-seventh
        chord in root position, while
        Eb-Gb-Bbb-C is a diminished-seventh in first inversion.
        But if the chord were heard in isolation
        it would not be possible to tell the inversion at all, since diminished-sevenths
        are transpositionally symmetrical.

        With either way of looking at it,
        there are fourteen set classes of 2-10 pitch classes have this property,
        including the augmented triad:

        >>> chord.Chord('C E G#').isTranspositionallySymmetrical()
        True

        ...but not the major triad:

        >>> chord.Chord('C E G').isTranspositionallySymmetrical()
        False

        The whole-tone scale and the Petrushka chord are both transpositionally symmetrical:

        >>> wholeToneAsChord = chord.Chord('C D E F# G# B- C')
        >>> wholeToneAsChord.isTranspositionallySymmetrical()
        True

        >>> petrushka = chord.Chord([0, 1, 3, 6, 7, 9])
        >>> petrushka.isTranspositionallySymmetrical()
        True

        If `requireIntervallicEvenness` is True then only chords that also have
        even spacing / evenly divide the octave are considered transpositionally
        symmetrical.  The normal cases are the F-B (06) dyad, the augmented triad,
        the diminished-seventh chord, and the whole-tone scale collection:

        >>> wholeToneAsChord.isTranspositionallySymmetrical(requireIntervallicEvenness=True)
        True

        >>> petrushka.isTranspositionallySymmetrical(requireIntervallicEvenness=True)
        False

        Note that complements of these chords (except the whole-tone collection) are
        not transpositionally symmetrical if `requireIntervallicEvenness` is required:

        >>> chord.Chord([0, 4, 8]).isTranspositionallySymmetrical(requireIntervallicEvenness=True)
        True

        >>> chord.Chord([1, 2, 3, 5, 6, 7, 9, 10, 11]).isTranspositionallySymmetrical(
        ...       requireIntervallicEvenness=True)
        False

        Empty chords and the total aggregate cannot have their inversion determined by ear alone.
        So they are `True` with or without `requireIntervallicEvenness`.

        >>> chord.Chord().isTranspositionallySymmetrical()
        True

        >>> chord.Chord(list(range(12))).isTranspositionallySymmetrical()
        True

        Monads (single-note "chords") cannot be transposed 1-11 semitones to recreate themselves,
        so they return `False` by default:

        >>> chord.Chord('C').isTranspositionallySymmetrical()
        False

        But they are the only case where `requireIntervallicEvenness` actually switches from
        `False` to `True`, because they do evenly divide the octave.

        >>> chord.Chord('C').isTranspositionallySymmetrical(requireIntervallicEvenness=True)
        True

        11-note chords return `False` in either case:

        >>> chord.Chord(list(range(11))).isTranspositionallySymmetrical()
        False
        '''
        if not self._notes:
            return True

        address = self.chordTablesAddress
        if address.cardinality == 1:
            return requireIntervallicEvenness

        lookup = (address.cardinality, address.forteClass)
        if lookup in (
            (2,  6),  # 06 -- omitted by Straus  # noqa: E241
            (3, 12),  # augmented triad
            (4, 28),  # diminished seventh chord
            (6, 35),  # whole-tone scale
            (12, 1),  # total aggregate.
        ):
            return True

        if not requireIntervallicEvenness and lookup in (
            (4,  9),  # 0167  # noqa: E241
            (4, 25),  # 0268
            (6,  7),  # 012678  # noqa: E241
            (6, 20),  # "Hexatonic scale" 014589
            (6, 30),  # Petrushka chord 013679
            (8,  9),  # 01236789  # noqa: E241
            (8, 25),  # 0124678T
            (8, 28),  # octatonic scale
            (9, 12),  # complement to augmented triad
            (10, 6),  # complement to 06
        ):
            return True
        else:
            return False

    @cacheMethod
    def isSeventh(self):
        '''
        Returns True if chord contains at least one of each of Third, Fifth, and Seventh,
        and every note in the chord is a Third, Fifth, or Seventh, such that there are no
        repeated scale degrees (ex: E and E-). Else return false.

        Example:

        >>> cChord = chord.Chord(['C', 'E', 'G', 'B'])
        >>> cChord.isSeventh()
        True
        >>> other = chord.Chord(['C', 'D', 'E', 'F', 'G', 'B'])
        >>> other.isSeventh()
        False

        OMIT_FROM_DOCS

        >>> chord.Chord().isSeventh()
        False
        '''
        uniquePitchNames = set(self.pitchNames)
        if len(uniquePitchNames) != 4:
            return False

        if self.third is None:
            return False

        if self.fifth is None:
            return False

        if self.seventh is None:
            return False

        return True

    @cacheMethod
    def isNinth(self):
        '''
        Returns True if chord contains at least one of each of Third, Fifth, Seventh, and Ninth
        and every note in the chord is a Third, Fifth, Seventh, or Ninth, such that there are no
        repeated scale degrees (ex: E and E-). Else return false.

        Example:

        >>> cChord = chord.Chord(['C', 'E', 'G', 'B', 'D'])
        >>> cChord.isNinth()
        True
        >>> other = chord.Chord(['C', 'E', 'F', 'G', 'B'])
        >>> other.isNinth()
        False

        OMIT_FROM_DOCS

        >>> chord.Chord().isNinth()
        False

        >>> chord.Chord('C C# C## C### C###').isNinth()
        False

        >>> chord.Chord('C C# E B D').isNinth()
        False

        >>> chord.Chord('C E G C- D').isNinth()
        False
        '''
        uniquePitchNames = set(self.pitchNames)
        if len(uniquePitchNames) != 5:
            return False

        if self.third is None:
            return False

        if self.fifth is None:
            return False

        if self.seventh is None:
            return False

        try:
            return bool(self.getChordStep(2))
        except ChordException:  # pragma: no cover
            # probably not reachable, since self.third would have caught the same
            # exception and returned False...
            return False

    def isSwissAugmentedSixth(self, *, permitAnyInversion=False):
        '''
        Returns true if it is a respelled German augmented 6th chord with
        sharp 2 instead of flat 3.  This chord has many names,
        Swiss Augmented Sixth, Alsatian Chord, English A6, Norwegian, etc.
        as well as doubly-augmented sixth, which is a bit of a misnomer since
        it is the 4th that is doubly augmented, not the sixth.

        >>> chord.Chord('A-4 C5 D#5 F#6').isSwissAugmentedSixth()
        True

        Respelled as a German Augmented Sixth does not count:

        >>> chord.Chord('A-4 C5 E-5 F#6').isSwissAugmentedSixth()
        False

        Inversions matter:

        >>> ch3 = chord.Chord('F#4 D#5 C6 A-6')
        >>> ch3.isSwissAugmentedSixth()
        False

        unless `permitAnyInversion` is given:

        >>> ch3.isSwissAugmentedSixth(permitAnyInversion=True)
        True

        * Changed in v7: `permitAnyInversion` added
        '''
        return self._isAugmentedSixthHelper(
            (4, 27, -1),
            2,
            permitAnyInversion,
            [('m3', 'M-6'), ('dd5', 'AA-4'), ('d7', 'A-2')]
        )


    @cacheMethod
    def isTriad(self) -> bool:
        '''
        Returns True if this Chord is a triad of some sort.  It could even be a rather
        exotic triad so long as the chord contains at least one Third and one Fifth and
        all notes have the same name as one of the three notes.

        Note: only returns True if triad is spelled correctly.

        Note the difference of "containsTriad" vs. "isTriad":
        A dominant-seventh chord is NOT a triad, but it contains two triads.

        >>> cChord = chord.Chord(['C4', 'E4', 'A4'])
        >>> cChord.isTriad()
        True

        >>> other = chord.Chord(['C', 'D', 'E', 'F', 'G'])
        >>> other.isTriad()
        False

        >>> incorrectlySpelled = chord.Chord(['C', 'D#', 'G'])
        >>> incorrectlySpelled.isTriad()
        False

        >>> incorrectlySpelled.pitches[1].getEnharmonic(inPlace=True)
        >>> incorrectlySpelled
        <music21.chord.Chord C E- G>
        >>> incorrectlySpelled.isTriad()
        True

        OMIT_FROM_DOCS

        >>> chord.Chord().isTriad()
        False
        >>> chord.Chord('C4 E4 G4 B#4').isTriad()
        False
        '''
        uniquePitchNames = set(self.pitchNames)
        if len(uniquePitchNames) == 3 and self.third and self.fifth:
            return True
        return False

    def removeRedundantPitches(self, *, inPlace=False):
        '''
        Remove all but one instance of a pitch that appears twice.

        It removes based on the name of the note and the octave, so the same
        note name in two different octaves is retained.

        If `inPlace` is True, a copy is not made and a list of deleted pitches is returned;
        otherwise a copy is made and that copy is returned.

        >>> c1 = chord.Chord(['c2', 'e3', 'g4', 'e3'])
        >>> c1
        <music21.chord.Chord C2 E3 G4 E3>

        >>> removedList = c1.removeRedundantPitches(inPlace=True)
        >>> c1
        <music21.chord.Chord C2 E3 G4>
        >>> removedList
        [<music21.pitch.Pitch E3>]

        >>> c1.forteClass
        '3-11B'

        >>> c2 = chord.Chord(['c2', 'e3', 'g4', 'c5'])
        >>> c2c = c2.removeRedundantPitches(inPlace=False)
        >>> c2c
        <music21.chord.Chord C2 E3 G4 C5>

        It is a known bug that because pitch.nameWithOctave gives
        the same value for B-flat in octave 1 as B-natural in octave
        negative 1, negative octaves can screw up this method.
        With all the things left to do for music21, it doesn't seem
        a bug worth squashing at this moment, but FYI:

        >>> p1 = pitch.Pitch('B-')
        >>> p1.octave = 1
        >>> p2 = pitch.Pitch('B')
        >>> p2.octave = -1
        >>> c3 = chord.Chord([p1, p2])
        >>> removedPitches = c3.removeRedundantPitches(inPlace=True)
        >>> c3.pitches
        (<music21.pitch.Pitch B-1>,)

        >>> c3.pitches[0].name
        'B-'
        >>> c3.pitches[0].octave
        1
        >>> removedPitches
        [<music21.pitch.Pitch B-1>]
        >>> removedPitches[0].name
        'B'
        >>> removedPitches[0].octave
        -1

        The first pitch survives:

        >>> c3.pitches[0] is p1
        True

        >>> c3.pitches[0] is p2
        False

        * Changed in v6: inPlace defaults to False.
        '''
        return self._removePitchByRedundantAttribute('nameWithOctave',
                                                     inPlace=inPlace)

    def removeRedundantPitchClasses(self, *, inPlace=False):
        '''
        Remove all but the FIRST instance of a pitch class with more than one
        instance of that pitch class.

        If `inPlace` is True, a copy is not made and a list of deleted pitches is returned;
        otherwise a copy is made and that copy is returned.

        >>> c1 = chord.Chord(['c2', 'e3', 'g4', 'e3'])
        >>> removed = c1.removeRedundantPitchClasses(inPlace=True)
        >>> c1.pitches
        (<music21.pitch.Pitch C2>, <music21.pitch.Pitch E3>, <music21.pitch.Pitch G4>)

        >>> c2 = chord.Chord(['c5', 'e3', 'g4', 'c2', 'e3', 'f-4'])
        >>> removed = c2.removeRedundantPitchClasses(inPlace=True)
        >>> c2.pitches
        (<music21.pitch.Pitch C5>, <music21.pitch.Pitch E3>, <music21.pitch.Pitch G4>)

        * Changed in v6: inPlace defaults to False.
        '''
        return self._removePitchByRedundantAttribute('pitchClass',
                                                     inPlace=inPlace)

    def removeRedundantPitchNames(self, *, inPlace=False):
        '''
        Remove all but the FIRST instance of a pitch class with more than one
        instance of that pitch name regardless of octave (but note that
        spelling matters, so that in the example, the F-flat stays even
        though there is already an E.)

        If `inPlace` is True, a copy is not made and a list of deleted pitches is returned;
        otherwise a copy is made and that copy is returned.

        >>> c2 = chord.Chord(['c5', 'e3', 'g4', 'c2', 'e3', 'f-4'])
        >>> c2
        <music21.chord.Chord C5 E3 G4 C2 E3 F-4>

        >>> rem = c2.removeRedundantPitchNames(inPlace=True)
        >>> c2
        <music21.chord.Chord C5 E3 G4 F-4>
        >>> rem
        [<music21.pitch.Pitch C2>, <music21.pitch.Pitch E3>]

        * Changed in v6: inPlace defaults to False.
        '''
        return self._removePitchByRedundantAttribute('name',
                                                     inPlace=inPlace)

    @overload
    def root(self,
             newroot: None = None,
             *,
             find: bool | None = None
             ) -> pitch.Pitch:
        return self.pitches[0]  # dummy until Astroid 1015 is fixed.

    @overload
    def root(self,
             newroot: str | pitch.Pitch | note.Note,
             *,
             find: bool | None = None
             ) -> None:
        return None  # dummy until Astroid 1015 is fixed.

    def root(self,
             newroot: None | str | pitch.Pitch | note.Note = None,
             *,
             find: bool | None = None
             ) -> pitch.Pitch | None:
        # noinspection PyShadowingNames
        '''
        Returns the root of the chord.  Or if given a Pitch as the
        newroot will override the algorithm and always return that Pitch.

        >>> cmaj = chord.Chord(['E3', 'C4', 'G5'])
        >>> cmaj.root()
        <music21.pitch.Pitch C4>

        Examples:

        >>> cmaj = chord.Chord(['E', 'G', 'C'])
        >>> cmaj.root()
        <music21.pitch.Pitch C>

        For some chords we make an exception.  For instance, this chord in
        B-flat minor:

        >>> aDim7no3rd = chord.Chord(['A3', 'E-4', 'G4'])

        ...could be considered a type of E-flat 11 chord with a 3rd, but no 5th,
        7th, or 9th, in 5th inversion.  That doesn't make sense, so we should
        call it an A dim 7th chord
        with no 3rd.

        >>> aDim7no3rd.root()
        <music21.pitch.Pitch A3>

        >>> aDim7no3rdInv = chord.Chord(['E-3', 'A4', 'G4'])
        >>> aDim7no3rdInv.root()
        <music21.pitch.Pitch A4>

        The root of a 13th chord (which could be any chord in any inversion) is
        designed to be the bass:

        >>> chord.Chord('F3 A3 C4 E-4 G-4 B4 D5').root()
        <music21.pitch.Pitch F3>

        Multiple pitches in different octaves do not interfere with root.

        >>> lotsOfNotes = chord.Chord(['E3', 'C4', 'G4', 'B-4', 'E5', 'G5'])
        >>> r = lotsOfNotes.root()
        >>> r
        <music21.pitch.Pitch C4>

        >>> r is lotsOfNotes.pitches[1]
        True

        Setting of a root may happen for a number of reasons, such as
        in the case where music21's idea of a root differs from the interpreter's.

        To specify the root directly, pass the pitch to the root function:

        >>> cSus4 = chord.Chord('C4 F4 G4')
        >>> cSus4.root()  # considered by music21 to be an F9 chord in 2nd inversion
        <music21.pitch.Pitch F4>

        Change it to be a Csus4:

        >>> cSus4.root('C4')
        >>> cSus4.root()
        <music21.pitch.Pitch C4>

        Note that if passing in a string as the root,
        the root is set to a pitch in the chord if possible.

        >>> cSus4.root() is cSus4.pitches[0]
        True


        You might also want to supply an "implied root." For instance, some people
        call a diminished seventh chord (generally viio7)
        a dominant chord with an omitted root (Vo9) -- here we will specify the root
        to be a note not in the chord:

        >>> vo9 = chord.Chord(['B3', 'D4', 'F4', 'A-4'])
        >>> vo9.root()
        <music21.pitch.Pitch B3>

        >>> vo9.root(pitch.Pitch('G3'))
        >>> vo9.root()
        <music21.pitch.Pitch G3>

        When setting a root, the pitches of the chord are left untouched:

        >>> [p.nameWithOctave for p in vo9.pitches]
        ['B3', 'D4', 'F4', 'A-4']

        By default, this method uses an algorithm to find the root among the
        chord's pitches, if no root has been previously specified.  If a root
        has been explicitly specified, as in the Csus4 chord above, it can be
        returned to the original root() by setting find explicitly to True:

        >>> cSus4.root(find=True)
        <music21.pitch.Pitch F4>

        Subsequent calls without find=True have also removed the overridden root:

        >>> cSus4.root()
        <music21.pitch.Pitch F4>

        If for some reason you do not want the root-finding algorithm to be
        run (for instance, checking to see if an overridden root has been
        specified) set find=False.  "None" will be returned if no root has been specified.

        >>> c = chord.Chord(['E3', 'G3', 'B4'])
        >>> print(c.root(find=False))
        None

        Chord symbols, for instance, have their root already specified on construction:

        >>> d = harmony.ChordSymbol('CM/E')
        >>> d.root(find=False)
        <music21.pitch.Pitch C4>

        There is no need to set find=False in this case, however, the
        algorithm will skip the slow part of finding the root if it
        has been specified (or already found and no pitches have changed).


        A chord with no pitches has no root and raises a ChordException.

        >>> chord.Chord().root()
        Traceback (most recent call last):
        music21.chord.ChordException: no pitches in chord <music21.chord.Chord ...>

        * Changed in v5.2: `find` is a keyword-only parameter,
          `newroot` finds `Pitch` in `Chord`
        '''
        # None value for find indicates: return override if overridden, cache if cached
        # or find new value if neither is the case.
        if newroot:
            newroot_pitch: pitch.Pitch
            if isinstance(newroot, str):
                newroot = common.cleanedFlatNotation(newroot)
                newroot_pitch = pitch.Pitch(newroot)
            elif isinstance(newroot, note.Note):
                newroot_pitch = newroot.pitch
            elif isinstance(newroot, pitch.Pitch):
                newroot_pitch = newroot
            else:
                raise ValueError(f'Cannot find a Pitch in {newroot!r}')

            # try to set newroot to be a pitch in the chord if possible
            foundRootInChord = False
            for p in self.pitches:  # first by identity
                if newroot_pitch is p:
                    foundRootInChord = True
                    break

            if not foundRootInChord:
                for p in self.pitches:  # then by name with octave
                    if p.nameWithOctave == newroot_pitch.nameWithOctave:
                        newroot_pitch = p
                        foundRootInChord = True
                        break

            if not foundRootInChord:  # finally by name
                for p in self.pitches:
                    if p.name == newroot_pitch.name:
                        newroot_pitch = p
                        break

            self._overrides['root'] = newroot_pitch
            self._cache['root'] = newroot_pitch

            if 'inversion' in self._cache:
                del self._cache['inversion']
                # reset inversion if root changes
            return None

        elif find is True:
            if 'root' in self._overrides:
                del self._overrides['root']
            if 'inversion' in self._cache:
                del self._cache['inversion']
            self._cache['root'] = self._findRoot()
            return self._cache['root']
        elif ('root' not in self._overrides) and find is not False:
            if 'root' in self._cache:
                return self._cache['root']
            else:
                self._cache['root'] = self._findRoot()
                return self._cache['root']
        elif 'root' in self._overrides:
            return self._overrides['root']
        else:
            return None

    @overload
    def semiClosedPosition(
        self: _ChordType,
        *,
        forceOctave,
        inPlace: t.Literal[True],
        leaveRedundantPitches=False
    ) -> None:
        return None

    @overload
    def semiClosedPosition(
        self: _ChordType,
        *,
        forceOctave=None,
        inPlace: t.Literal[False] = False,
        leaveRedundantPitches=False
    ) -> _ChordType:
        return self

    def semiClosedPosition(
        self: _ChordType,
        *,
        forceOctave: int | None = None,
        inPlace: t.Literal[True] | t.Literal[False] = False,
        leaveRedundantPitches: bool = False
    ) -> None | _ChordType:
        # noinspection PyShadowingNames
        '''
        Similar to :meth:`~music21.chord.Chord.ClosedPosition` in that it
        moves everything within an octave EXCEPT if there's already
        a pitch at that step, then it puts it up an octave.  It's a
        very useful display standard for dense post-tonal chords.

        >>> c1 = chord.Chord(['C3', 'E5', 'C#6', 'E-7', 'G8', 'C9', 'E#9'])
        >>> c2 = c1.semiClosedPosition(inPlace=False)
        >>> c2
        <music21.chord.Chord C3 E-3 G3 C#4 E4 E#5>

        `leaveRedundantPitches` still works, and gives them a new octave!

        >>> c3 = c1.semiClosedPosition(
        ...     inPlace=False,
        ...     leaveRedundantPitches=True,
        ...     )
        >>> c3
        <music21.chord.Chord C3 E-3 G3 C4 E4 C#5 E#5>

        of course `forceOctave` still works, as does `inPlace=True`.

        >>> c1.semiClosedPosition(
        ...     forceOctave=2,
        ...     inPlace=True,
        ...     leaveRedundantPitches=True,
        ...     )
        >>> c1
        <music21.chord.Chord C2 E-2 G2 C3 E3 C#4 E#4>

        '''
        c2 = self.closedPosition(forceOctave=forceOctave,
                                 inPlace=inPlace,
                                 leaveRedundantPitches=leaveRedundantPitches)
        if inPlace is True:
            c2 = self

        if t.TYPE_CHECKING:
            from music21.stream import Stream
            assert isinstance(c2, Stream)
        # startOctave = c2.bass().octave
        remainingPitches = copy.copy(c2.pitches)  # no deepcopy needed

        while remainingPitches:
            usedSteps = []
            newRemainingPitches = []
            for i, p in enumerate(remainingPitches):
                if p.step not in usedSteps:
                    usedSteps.append(p.step)
                else:
                    p.octave += 1
                    newRemainingPitches.append(p)
            remainingPitches = newRemainingPitches

        c2.clearCache()
        c2.sortAscending(inPlace=True)

        if inPlace is False:
            return c2

    def semitonesFromChordStep(self, chordStep, testRoot=None):
        '''
        Returns the number of semitones (mod12) above the root that the
        chordStep lies (i.e., 3 = third of the chord; 5 = fifth, etc.) if one
        exists.  Or None if it does not exist.

        You can optionally specify a note.Note object to try as the root.  It
        does not change the Chord.root object.  We use these methods to figure
        out what the root of the triad is.

        Currently, there is a bug that in the case of a triply diminished third
        (e.g., "c" => "e----"), this function will incorrectly claim no third
        exists.  Perhaps this should be construed as a feature.

        In the case of chords such as C, E-, E, semitonesFromChordStep(3)
        will return the number for the first third, in this case 3.  It
        will not return 4, nor a list object (3, 4).  You probably do not
        want to be using tonal chord manipulation functions on chords such
        as these anyway.  Check for such cases with
        chord.hasAnyRepeatedDiatonicNote first.

        Tools with the expression "chordStep" in them refer to the diatonic
        third, fifth, etc., of the chord.  They have little to do with
        the scale degree of the scale or key that the chord is embedded
        within.  See "chord.scaleDegrees" for this functionality.

        >>> cChord = chord.Chord(['E3', 'C4', 'G5'])
        >>> cChord.semitonesFromChordStep(3)  # distance from C to E
        4

        >>> cChord.semitonesFromChordStep(5)  # C to G
        7

        Omitted chordSteps return None

        >>> print(cChord.semitonesFromChordStep(6))
        None

        Note that the routine returns the semitones to the FIRST third.
        This chord has two thirds, C and C#

        >>> aChord = chord.Chord(['a2', 'c4', 'c#5', 'e#7'])
        >>> aChord.semitonesFromChordStep(3)
        3

        >>> aChord.semitonesFromChordStep(5)
        8
        >>> print(aChord.semitonesFromChordStep(2))
        None


        Test whether this strange chord gets the B# as 0 semitones:

        >>> c = chord.Chord(['C4', 'E4', 'G4', 'B#4'])
        >>> c.semitonesFromChordStep(7)
        0

        If testRoot is set to a Pitch object then that note is used as the root of the chord
        regardless of anything else that might be considered.

        A-minor: 1st inversion.

        >>> aMin = chord.Chord(['C4', 'E4', 'A4'])
        >>> aMin.semitonesFromChordStep(3)
        3
        >>> aMin.semitonesFromChordStep(5)
        7

        C6 chord, jazz like, root position:

        >>> cPitch = pitch.Pitch('C4')
        >>> c6 = aMin  # renaming for clarity
        >>> c6.semitonesFromChordStep(3, testRoot = cPitch)
        4
        >>> c6.semitonesFromChordStep(5, testRoot = cPitch) is None
        True
        >>> c6.semitonesFromChordStep(6, testRoot = cPitch)
        9
        '''
        tempInt = self.intervalFromChordStep(chordStep, testRoot=testRoot)
        if tempInt is None:
            return None
        else:
            return tempInt.chromatic.mod12

    def setColor(self, value, pitchTarget=None):
        '''
        Set color for specific pitch.

        >>> c = chord.Chord('C4 E4 G4')
        >>> c.setColor('red', 'C4')
        >>> c['0.style.color']
        'red'
        >>> c.setColor('blue')  # set for whole chord...
        >>> c.style.color
        'blue'
        >>> c['E4.style.color']
        'blue'

        >>> c.setColor('red', 'C9')
        Traceback (most recent call last):
        music21.chord.ChordException: the given pitch is not in the Chord: C9
        '''
        # assign to base
        if pitchTarget is None and self._notes:
            self.style.color = value
            for n in self._notes:
                n.style.color = value

            return
        elif isinstance(pitchTarget, str):
            pitchTarget = pitch.Pitch(pitchTarget)

        match = False
        for d in self._notes:
            if d.pitch is pitchTarget:
                d.style.color = value
                match = True
                break
        if not match:  # look at equality of value
            for d in self._notes:
                if d.pitch == pitchTarget:
                    d.style.color = value
                    match = True
                    break
        if not match:
            raise ChordException(
                f'the given pitch is not in the Chord: {pitchTarget}')

    def setNotehead(self, nh, pitchTarget):
        '''
        Given a notehead attribute as a string and a pitch object in this
        Chord, set the notehead attribute of that pitch to the value of that
        notehead. Valid notehead type names are found in note.noteheadTypeNames
        (see below):

        >>> for noteheadType in note.noteheadTypeNames:
        ...    noteheadType
        ...
        'arrow down'
        'arrow up'
        'back slashed'
        'circle dot'
        'circle-x'
        'circled'
        'cluster'
        'cross'
        'diamond'
        'do'
        'fa'
        'inverted triangle'
        'la'
        'left triangle'
        'mi'
        'none'
        'normal'
        'other'
        're'
        'rectangle'
        'slash'
        'slashed'
        'so'
        'square'
        'ti'
        'triangle'
        'x'

        >>> n1 = note.Note('D4')
        >>> n2 = note.Note('G4')
        >>> c1 = chord.Chord([n1, n2])
        >>> c1.setNotehead('diamond', c1.pitches[1])  # just to g
        >>> c1.getNotehead(c1.pitches[1])
        'diamond'

        >>> c1.getNotehead(c1.pitches[0])
        'normal'

        If a chord has two of the same pitch, but each associated with a different notehead, then
        object equality must be used to distinguish between the two.

        >>> c2 = chord.Chord(['D4', 'D4'])
        >>> secondD4 = c2.pitches[1]
        >>> c2.setNotehead('diamond', secondD4)
        >>> for i in [0, 1]:
        ...     c2.getNotehead(c2.pitches[i])
        ...
        'normal'
        'diamond'

        By default, assigns to first pitch:

        >>> c3 = chord.Chord('C3 F4')
        >>> c3.setNotehead('slash', None)
        >>> c3['0.notehead']
        'slash'

        Less safe to match by string, but possible:

        >>> c3.setNotehead('so', 'F4')
        >>> c3['1.notehead']
        'so'

        Error:

        >>> c3.setNotehead('so', 'G4')
        Traceback (most recent call last):
        music21.chord.ChordException: the given pitch is not in the Chord: G4

        '''
        # assign to first pitch by default
        if pitchTarget is None and self._notes:
            pitchTarget = self._notes[0].pitch
        elif isinstance(pitchTarget, str):
            pitchTarget = pitch.Pitch(pitchTarget)
        match = False
        for d in self._notes:
            if d.pitch is pitchTarget:
                d.notehead = nh
                match = True
                break
        if not match:
            for d in self._notes:
                if d.pitch == pitchTarget:
                    d.notehead = nh
                    match = True
                    break
        if not match:
            raise ChordException(f'the given pitch is not in the Chord: {pitchTarget}')

    def setNoteheadFill(self, nh, pitchTarget):
        '''
        Given a noteheadFill attribute as a string (or False) and a pitch object in this
        Chord, set the noteheadFill attribute of that pitch to the value of that
        notehead. Valid noteheadFill names are True, False, None (default)

        >>> n1 = note.Note('D4')
        >>> n2 = note.Note('G4')
        >>> c1 = chord.Chord([n1, n2])
        >>> c1.setNoteheadFill(False, c1.pitches[1])  # just to g
        >>> c1.getNoteheadFill(c1.pitches[1])
        False

        >>> c1.getNoteheadFill(c1.pitches[0]) is None
        True

        If a chord has two of the same pitch, but each associated with a different notehead, then
        object equality must be used to distinguish between the two.

        >>> c2 = chord.Chord(['D4', 'D4'])
        >>> secondD4 = c2.pitches[1]
        >>> c2.setNoteheadFill(False, secondD4)
        >>> for i in [0, 1]:
        ...     print(c2.getNoteheadFill(c2.pitches[i]))
        ...
        None
        False

        By default assigns to first pitch:

        >>> c3 = chord.Chord('C3 F4')
        >>> c3.setNoteheadFill(False, None)
        >>> c3['0.noteheadFill']
        False

        Less safe to match by string, but possible:

        >>> c3.setNoteheadFill(True, 'F4')
        >>> c3['1.noteheadFill']
        True

        Error:
        >>> c3.setNoteheadFill(True, 'G4')
        Traceback (most recent call last):
        music21.chord.ChordException: the given pitch is not in the Chord: G4

        '''
        # assign to first pitch by default
        if pitchTarget is None and self._notes:
            pitchTarget = self._notes[0].pitch
        elif isinstance(pitchTarget, str):
            pitchTarget = pitch.Pitch(pitchTarget)
        match = False
        for d in self._notes:
            if d.pitch is pitchTarget:
                d.noteheadFill = nh
                match = True
                break
        if not match:
            for d in self._notes:
                if d.pitch == pitchTarget:
                    d.noteheadFill = nh
                    match = True
                    break
        if not match:
            raise ChordException(f'the given pitch is not in the Chord: {pitchTarget}')

    def setStemDirection(self, stem, pitchTarget):
        '''
        Given a stem attribute as a string and a pitch object in this Chord,
        set the stem attribute of that pitch to the value of that stem. Valid
        stem directions are found note.stemDirectionNames (see below).

        >>> for name in note.stemDirectionNames:
        ...     name
        ...
        'double'
        'down'
        'noStem'
        'none'
        'unspecified'
        'up'

        >>> n1 = note.Note('D4')
        >>> n2 = note.Note('G4')
        >>> c1 = chord.Chord([n1, n2])
        >>> c1.setStemDirection('double', c1.pitches[1])  # just to g
        >>> c1.getStemDirection(c1.pitches[1])
        'double'

        >>> c1.getStemDirection(c1.pitches[0])
        'unspecified'

        If a chord has two of the same pitch, but each associated with a
        different stem, then object equality must be used to distinguish
        between the two.

        >>> c2 = chord.Chord(['D4', 'D4'])
        >>> secondD4 = c2.pitches[1]
        >>> c2.setStemDirection('double', secondD4)
        >>> for i in [0, 1]:
        ...    print(c2.getStemDirection(c2.pitches[i]))
        ...
        unspecified
        double

        By default, assigns to first pitch:

        >>> c3 = chord.Chord('C3 F4')
        >>> c3.setStemDirection('down', None)
        >>> c3['0.stemDirection']
        'down'

        Less safe to match by string, but possible:

        >>> c3.setStemDirection('down', 'F4')
        >>> c3['1.stemDirection']
        'down'

        Error:
        >>> c3.setStemDirection('up', 'G4')
        Traceback (most recent call last):
        music21.chord.ChordException: the given pitch is not in the Chord: G4

        '''
        if pitchTarget is None and self._notes:
            pitchTarget = self._notes[0].pitch  # first is default
        elif isinstance(pitchTarget, str):
            pitchTarget = pitch.Pitch(pitchTarget)
        match = False
        for d in self._notes:
            if d.pitch is pitchTarget:
                d.stemDirection = stem
                match = True
                break
        if not match:
            for d in self._notes:
                if d.pitch == pitchTarget:
                    d.stemDirection = stem
                    match = True
                    break
        if not match:
            raise ChordException(
                f'the given pitch is not in the Chord: {pitchTarget}')

    def setTie(self, tieObjOrStr: tie.Tie | str, pitchTarget):
        '''
        Given a tie object (or a tie type string) and a pitch or Note in this Chord,
        set the pitch's tie attribute in this chord to that tie type.

        >>> c1 = chord.Chord(['d3', 'e-4', 'b-4'])
        >>> t1 = tie.Tie('start')
        >>> c1.setTie(t1, 'b-4')  # or it can be done with a pitch.Pitch object
        >>> c1.getTie(c1.pitches[2]) is t1
        True

        Setting a tie with a chord with the same pitch twice requires
        getting the exact pitch object out to be sure which one...

        >>> c2 = chord.Chord(['D4', 'D4'])
        >>> secondD4 = c2.pitches[1]
        >>> c2.setTie('start', secondD4)
        >>> for i in [0, 1]:
        ...    print(c2.getTie(c2.pitches[i]))
        ...
        None
        <music21.tie.Tie start>

        >>> c3 = chord.Chord('C3 F4')
        >>> c3.setTie('start', None)
        >>> c3.getTie(c3.pitches[0])
        <music21.tie.Tie start>

        Less safe to match by string, because there might be multiple
        pitches with the same name in the chord, but possible:

        >>> c4 = chord.Chord('D4 F#4')
        >>> c4.setTie('start', 'F#4')
        >>> c4.getTie('F#4')
        <music21.tie.Tie start>

        Setting a tie on a note not in the chord is an error:

        >>> c3.setTie('stop', 'G4')
        Traceback (most recent call last):
        music21.chord.ChordException: the given pitch is not in the Chord: G4
        '''
        if pitchTarget is None and self._notes:  # if no pitch
            pitchTarget = self._notes[0].pitch
        elif isinstance(pitchTarget, str):
            pitchTarget = pitch.Pitch(pitchTarget)

        tieObj: tie.Tie
        if isinstance(tieObjOrStr, str):
            tieObj = tie.Tie(tieObjOrStr)
        else:
            tieObj = tieObjOrStr

        match = False
        for d in self._notes:
            if d.pitch is pitchTarget or d is pitchTarget:  # compare by obj id first
                d.tie = tieObj
                match = True
                break
        if not match:  # more loose comparison: by ==
            for d in self._notes:
                if pitchTarget in (d, d.pitch):
                    d.tie = tieObj
                    match = True
                    break
        if not match:
            raise ChordException(
                f'the given pitch is not in the Chord: {pitchTarget}')

    def setVolume(self,
                  vol: volume.Volume,
                  target: str | note.Note | pitch.Pitch):
        '''
        Set the :class:`~music21.volume.Volume` object of a specific Pitch.

        * Changed in v8: after appearing in ChordBase in v7, it has been properly
            moved back to Chord itself.  The ability to change just the first note's
            volume has been removed.  Use `Chord().volume = vol` to change the
            volume for a whole chord.
        '''
        # assign to first pitch by default
        if isinstance(target, str):
            pitchTarget = pitch.Pitch(target)
        elif isinstance(target, note.Note):
            pitchTarget = target.pitch
        elif isinstance(target, pitch.Pitch):
            pitchTarget = target
        else:
            raise ValueError(f'Cannot setVolume on target {target!r}')

        match = False
        for d in self._notes:
            if d.pitch is pitchTarget or d.pitch == pitchTarget:
                vol.client = self
                # noinspection PyArgumentList
                d._setVolume(vol, setClient=False)
                match = True
                break
        if not match:
            raise ChordException(f'the given pitch is not in the Chord: {pitchTarget}')

    def simplifyEnharmonics(self, *, inPlace=False, keyContext=None):
        '''
        Calls `pitch.simplifyMultipleEnharmonics` on the pitches of the chord.

        Simplifies the enharmonics in the sense of making a more logical chord.  Note below
        that E# is added there because C# major is simpler than C# F G#.

        >>> c = chord.Chord('C# F G#')
        >>> c.pitches
        (<music21.pitch.Pitch C#>, <music21.pitch.Pitch F>, <music21.pitch.Pitch G#>)

        >>> c.simplifyEnharmonics(inPlace=True)
        >>> c.pitches
        (<music21.pitch.Pitch C#>, <music21.pitch.Pitch E#>, <music21.pitch.Pitch G#>)

        If `keyContext` is provided the enharmonics are simplified based on the supplied
        Key or KeySignature.

        >>> c.simplifyEnharmonics(inPlace=True, keyContext=key.Key('A-'))
        >>> c.pitches
        (<music21.pitch.Pitch D->, <music21.pitch.Pitch F>, <music21.pitch.Pitch A->)
        '''
        if inPlace:
            returnObj = self
        else:
            returnObj = copy.deepcopy(self)

        pitches = pitch.simplifyMultipleEnharmonics(self.pitches, keyContext=keyContext)
        for i in range(len(pitches)):
            returnObj._notes[i].pitch = pitches[i]

        if inPlace is False:
            return returnObj

    def sortAscending(self, *, inPlace=False):
        return self.sortDiatonicAscending(inPlace=inPlace)

    def sortChromaticAscending(self):
        '''
        Same as sortAscending but notes are sorted by midi number, so F## sorts above G-.
        '''
        newChord = copy.deepcopy(self)
        # tempChordNotes = newChord.pitches
        newChord._notes.sort(key=lambda x: x.pitch.ps)
        return newChord

    def sortDiatonicAscending(self, *, inPlace=False):
        '''
        The notes are sorted by :attr:`~music21.pitch.Pitch.diatonicNoteNum`
        or vertical position on a grand staff (so F## sorts below G-).
        Notes that are the identical diatonicNoteNum are further sorted by
        :attr:`~music21.pitch.Pitch.ps` (midi numbers that accommodate floats).

        We return a new Chord object with the notes arranged from lowest to highest
        (unless inPlace=True)

        >>> cMajUnsorted = chord.Chord(['E4', 'C4', 'G4'])
        >>> cMajSorted = cMajUnsorted.sortDiatonicAscending()
        >>> cMajSorted.pitches[0].name
        'C'

        >>> c2 = chord.Chord(['E4', 'C4', 'G4'])
        >>> c2.sortDiatonicAscending(inPlace=True)
        >>> c2
        <music21.chord.Chord C4 E4 G4>

        >>> sameDNN = chord.Chord(['F#4', 'F4'])
        >>> sameDNN.sortDiatonicAscending()
        <music21.chord.Chord F4 F#4>

        * Changed in v6: if inPlace is True do not return anything.
        '''
        if inPlace:
            if self._cache.get('isSortedAscendingDiatonic', False):
                return None
            returnObj = self
            self.clearCache()
        else:
            # cache is not copied to the new item.
            returnObj = copy.deepcopy(self)
        returnObj._notes.sort(key=lambda x: (x.pitch.diatonicNoteNum, x.pitch.ps))
        returnObj._cache['isSortedAscendingDiatonic'] = True

        if not inPlace:
            return returnObj

    def sortFrequencyAscending(self):
        '''
        Same as above, but uses a note's frequency to determine height; so that
        C# would be below D- in 1/4-comma meantone, equal in equal temperament,
        but below it in (most) just intonation types.
        '''
        newChord = copy.deepcopy(self)
        newChord._notes.sort(key=lambda x: x.pitch.frequency)
        return newChord

    def transpose(self, value, *, inPlace=False):
        '''
        Transpose the Chord by the user-provided value. If the value
        is an integer, the transposition is treated in half steps and
        enharmonics might be simplified (not done yet). If the value is a
        string, any Interval string specification can be provided.

        If inPlace is set to True (default = False) then the original
        chord is changed.  Otherwise a new Chord is returned.

        We take a three-note chord (G, A, C#) and transpose it up a minor
        third, getting the chord B-flat, C, E.

        >>> a = chord.Chord(['g4', 'a3', 'c#6'])
        >>> b = a.transpose('m3')
        >>> b
        <music21.chord.Chord B-4 C4 E6>

        Here we create the interval object first (rather than giving
        a string) and specify transposing down six semitones, instead
        of saying A-4.

        >>> aInterval = interval.Interval(-6)
        >>> b = a.transpose(aInterval)
        >>> b
        <music21.chord.Chord C#4 E-3 G5>

        If `inPlace` is True then rather than returning a new chord, the
        chord itself is changed.

        >>> a.transpose(aInterval, inPlace=True)
        >>> a
        <music21.chord.Chord C#4 E-3 G5>

        '''
        if hasattr(value, 'diatonic'):  # it is an Interval class
            intervalObj = value
        else:  # try to process
            intervalObj = interval.Interval(value)
        if not inPlace:
            post = copy.deepcopy(self)
        else:
            post = self
        # call transpose on component Notes
        for n in post._notes:
            n.transpose(intervalObj, inPlace=True)
        # for p in post.pitches:
        #     # we are either operating on self or a copy; always use inPlace
        #     p.transpose(intervalObj, inPlace=True)
        #     # pitches.append(intervalObj.transposePitch(p))
        if not inPlace:
            return post
        else:
            return None

    # PUBLIC PROPERTIES #

    # see https://github.com/python/mypy/issues/1362
    @property  # type: ignore
    @cacheMethod
    def chordTablesAddress(self):
        '''
        Return a four-element ChordTableAddress that represents that raw data location for
        information on the set class interpretation of this Chord as well as the original
        pitchClass

        The data format is a Forte set class cardinality, index number, and
        inversion status (where 0 is invariant, and -1 and 1 represent
        inverted or not, respectively).

        >>> c = chord.Chord(['D4', 'F#4', 'B-4'])
        >>> c.chordTablesAddress
        ChordTableAddress(cardinality=3, forteClass=12, inversion=0, pcOriginal=2)

        >>> c = chord.Chord('G#2 A2 D3 G3')
        >>> c.chordTablesAddress
        ChordTableAddress(cardinality=4, forteClass=6, inversion=0, pcOriginal=2)

        This method caches the result so that it does not need to be looked up again.

        One change from chord.tables.seekChordTablesAddress: the empty chord returns
        a special address instead of raising an exception:

        >>> chord.Chord().chordTablesAddress
        ChordTableAddress(cardinality=0, forteClass=0, inversion=0, pcOriginal=0)
        '''
        try:
            return tables.seekChordTablesAddress(self)
        except tables.ChordTablesException:
            return tables.ChordTableAddress(0, 0, 0, 0)


    @property    # type: ignore
    @cacheMethod
    def commonName(self) -> str:
        '''
        Return the most common name associated with this Chord as a string.
        Checks some common enharmonic equivalents.

        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.commonName
        'minor triad'

        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.commonName
        'major triad'

        >>> c2b = chord.Chord(['c', 'f-', 'g'])
        >>> c2b.commonName
        'enharmonic equivalent to major triad'

        >>> c3 = chord.Chord(['c', 'd-', 'e', 'f#'])
        >>> c3.commonName
        'all-interval tetrachord'

        Chords with no common names just return the Forte Class

        >>> c3 = chord.Chord([0, 1, 2, 3, 4, 9])
        >>> c3.commonName
        'forte class 6-36B'

        Dominant seventh and German/Swiss sixths are distinguished

        >>> c4a = chord.Chord(['c', 'e', 'g', 'b-'])
        >>> c4a.commonName
        'dominant seventh chord'

        >>> c4b = chord.Chord(['c', 'e', 'g', 'a#'])
        >>> c4b.commonName
        'German augmented sixth chord'

        >>> c4c = chord.Chord(['c', 'e', 'f##', 'a#'])
        >>> c4c.commonName  # some call it Alsacian or English
        'Swiss augmented sixth chord'

        When in an unusual inversion, augmented sixth chords have their inversion added:

        >>> c4b = chord.Chord('A#3 C4 E4 G4')
        >>> c4b.commonName
        'German augmented sixth chord in root position'


        Dyads are called by actual name:

        >>> dyad1 = chord.Chord('C E')
        >>> dyad1.commonName
        'Major Third'
        >>> dyad2 = chord.Chord('C F-')
        >>> dyad2.commonName
        'Diminished Fourth'

        Compound intervals are given in full if there are only two distinct pitches:

        >>> dyad1 = chord.Chord('C4 E5')
        >>> dyad1.commonName
        'Major Tenth'

        But if there are more pitches, then the interval is given in a simpler form:

        >>> dyad1 = chord.Chord('C4 C5 E5 C6')
        >>> dyad1.commonName
        'Major Third with octave doublings'


        If there are multiple enharmonics present just the simple
        number of semitones is returned.

        >>> dyad1 = chord.Chord('C4 E5 F-5 B#7')
        >>> dyad1.commonName
        '4 semitones'



        Special handling of one- and two-pitchClass chords:

        >>> gAlone = chord.Chord(['G4'])
        >>> gAlone.commonName
        'note'
        >>> gAlone = chord.Chord('G4 G4')
        >>> gAlone.commonName
        'unison'
        >>> gAlone = chord.Chord('G4 G5')
        >>> gAlone.commonName
        'Perfect Octave'
        >>> gAlone = chord.Chord('G4 G6')
        >>> gAlone.commonName
        'Perfect Double-octave'
        >>> gAlone = chord.Chord('G4 G5 G6')
        >>> gAlone.commonName
        'multiple octaves'
        >>> gAlone = chord.Chord('F#4 G-4')
        >>> gAlone.commonName
        'enharmonic unison'

        >>> chord.Chord().commonName
        'empty chord'

        Microtonal chords all have the same commonName:

        >>> chord.Chord('C`4 D~4').commonName
        'microtonal chord'

        Enharmonic equivalents to common sevenths and ninths are clarified:

        >>> chord.Chord('C4 E4 G4 A##4').commonName
        'enharmonic equivalent to major seventh chord'

        >>> chord.Chord('C4 E-4 G4 A#4 D4').commonName
        'enharmonic equivalent to minor-ninth chord'

        * Changed in v5.5: special cases for checking enharmonics in some cases
        * Changed in v6.5: better handling of 0-, 1-, and 2-pitchClass and microtonal chords.
        * Changed in v7: Inversions of augmented sixth-chords are specified.
        * Changed in v7.3: Enharmonic equivalents to common seventh and ninth chords are specified.

        OMIT_FROM_DOCS

        >>> chord.Chord('C E G C-').commonName
        'enharmonic equivalent to major seventh chord'
        '''
        if any(not p.isTwelveTone() for p in self.pitches):
            return 'microtonal chord'

        cta = self.chordTablesAddress
        if cta.cardinality == 0:
            return 'empty chord'

        if cta.cardinality == 1:
            if len(self.pitches) == 1:
                return 'note'
            pitchNames = {p.name for p in self.pitches}
            pitchPSes = {p.ps for p in self.pitches}
            if len(pitchNames) == 1:
                if len(pitchPSes) == 1:
                    return 'unison'
                if len(pitchPSes) == 2:
                    return interval.Interval(self.pitches[0], self.pitches[1]).niceName
                else:
                    return 'multiple octaves'
            if len(pitchPSes) == 1:
                return 'enharmonic unison'
            else:
                return 'enharmonic octaves'

        ctn = tables.addressToCommonNames(cta)
        if cta.cardinality == 2:
            pitchNames = {p.name for p in self.pitches}
            pitchPSes = {p.ps for p in self.pitches}

            # find two different pitchClasses
            p0 = self.pitches[0]
            p0pitchClass = p0.pitchClass
            p1: pitch.Pitch
            for p in self.pitches[1:]:
                if p.pitchClass != p0pitchClass:
                    p1 = p
                    break
            else:  # pragma: no cover
                raise ChordException('Will never happen, just for typing.')

            relevantInterval = interval.Interval(p0, p1)

            if len(pitchNames) > 2:
                # C4 E4 B#4, etc.
                simpleUn = relevantInterval.chromatic.simpleUndirected
                plural = 's' if simpleUn != 1 else ''
                return f'{simpleUn} semitone{plural}'

            if len(pitchPSes) > 2:
                return relevantInterval.semiSimpleNiceName + ' with octave doublings'

            return interval.Interval(self.pitches[0], self.pitches[1]).niceName

        forteClass = self.forteClass
        # forteClassTn = self.forteClassTn

        def _isSeventhWithPerfectFifthAboveRoot(c: Chord) -> bool:
            '''
            For testing minor-minor sevenths and major-major sevenths
            '''
            if not c.isSeventh():
                return False
            hypothetical_fifth = c.root().transpose('P5')
            return hypothetical_fifth.name in c.pitchNames

        enharmonicTests = {
            '3-11A': self.isMinorTriad,
            '3-11B': self.isMajorTriad,
            '3-10': self.isDiminishedTriad,
            '3-12': self.isAugmentedTriad,
            '4-27A': self.isHalfDiminishedSeventh,
            '4-28': self.isDiminishedSeventh,
            '5-27A': self.isNinth,  # major-ninth
            '5-27B': self.isNinth,  # minor-ninth
            '5-34': self.isNinth,  # dominant-ninth
        }

        # special cases
        if forteClass == '4-27B':
            # dominant seventh OR German Aug 6
            if self.isDominantSeventh():
                return ctn[0]
            elif self.isGermanAugmentedSixth():
                return ctn[2]
            elif self.isGermanAugmentedSixth(permitAnyInversion=True):
                return ctn[2] + ' in ' + self.inversionText().lower()
            elif self.isSwissAugmentedSixth():
                return ctn[3]
            elif self.isSwissAugmentedSixth(permitAnyInversion=True):
                return ctn[3] + ' in ' + self.inversionText().lower()
            else:
                return 'enharmonic to ' + ctn[0]
        elif forteClass == '4-25':
            if self.isFrenchAugmentedSixth():
                return ctn[1]
            elif self.isFrenchAugmentedSixth(permitAnyInversion=True):
                return ctn[1] + ' in ' + self.inversionText().lower()
            else:
                return ctn[0]
        elif forteClass == '3-8A':
            if self.isItalianAugmentedSixth():
                return ctn[1]
            elif self.isItalianAugmentedSixth(permitAnyInversion=True):
                return ctn[1] + ' in ' + self.inversionText().lower()
            else:
                return ctn[0]
        elif forteClass in ('4-20', '4-26'):
            # minor seventh or major seventh chords,
            # but cannot just test isSeventh, as
            # that would permit C E G A## (A## as root)
            if _isSeventhWithPerfectFifthAboveRoot(self):
                return ctn[0]
            else:
                return 'enharmonic equivalent to ' + ctn[0]

        elif forteClass in enharmonicTests:
            out = ctn[0]
            test = enharmonicTests[forteClass]
            if not test():
                out = 'enharmonic equivalent to ' + out
            return out

        if not ctn:
            return 'forte class ' + forteClass
        else:
            return ctn[0]


    @property
    def duration(self) -> Duration:
        # noinspection PyShadowingNames
        '''
        Get or set the duration of this Chord as a Duration object.

        >>> c = chord.Chord(['a', 'c', 'e'])
        >>> c.duration
        <music21.duration.Duration 1.0>

        Durations can be overridden after the fact:

        >>> d = duration.Duration()
        >>> d.quarterLength = 2
        >>> c.duration = d
        >>> c.duration
        <music21.duration.Duration 2.0>

        >>> c.duration == d
        True

        >>> c.duration is d
        True
        '''
        d = t.cast(Duration | None, self._duration)  # type: ignore
        if d is None and self._notes:
            # pitchZeroDuration = self._notes[0]['pitch'].duration
            pitchZeroDuration = self._notes[0].duration
            self._duration = pitchZeroDuration

        d_out = self._duration
        if t.TYPE_CHECKING:
            assert isinstance(d_out, Duration)
        return d_out

    @duration.setter
    def duration(self, durationObj: Duration):
        '''
        Set a Duration object.
        '''
        if isinstance(durationObj, Duration):
            self._duration = durationObj
        else:
            # need to permit Duration object assignment here
            raise ChordException(f'this must be a Duration object, not {durationObj}')

    @property  # type: ignore
    @cacheMethod
    def fifth(self) -> pitch.Pitch | None:
        '''
        Shortcut for getChordStep(5), but caches it and does not raise exceptions

        >>> cMaj1stInv = chord.Chord(['E3', 'C4', 'G5'])
        >>> cMaj1stInv.fifth
        <music21.pitch.Pitch G5>

        >>> cMaj1stInv.fifth.midi
        79

        >>> chord.Chord('C4 D4').fifth is None
        True

        OMIT_FROM_DOCS

        >>> chord.Chord().fifth
        '''
        try:
            return self.getChordStep(5)
        except ChordException:
            return None

    @property
    def forteClass(self):
        '''
        Return the Forte set class name as a string. This assumes a Tn
        formation, where inversion distinctions are represented.

        (synonym: forteClassTn)

        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.forteClass
        '3-11A'

        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.forteClass
        '3-11B'

        Empty chords return 'N/A'

        >>> chord.Chord().forteClass
        'N/A'

        Non-twelve-tone chords return as if all microtones and non-twelve-tone
        accidentals are removed:

        >>> chord.Chord('c~4 d`4').forteClass
        '2-2'
        '''
        try:
            return tables.addressToForteName(self.chordTablesAddress, 'tn')
        except tables.ChordTablesException:
            return 'N/A'

    @property
    def forteClassNumber(self):
        '''
        Return the number of the Forte set class within the defined set group.
        That is, if the set is 3-11, this method returns 11.

        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.forteClassNumber
        11

        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.forteClassNumber
        11
        '''
        return self.chordTablesAddress.forteClass

    @property
    def forteClassTn(self):
        '''
        A synonym for "forteClass"

        Return the Forte Tn set class name, where inversion distinctions are
        represented:

        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.forteClass
        '3-11A'

        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.forteClassTn
        '3-11B'
        '''
        return self.forteClass

    @property
    def forteClassTnI(self):
        '''
        Return the Forte TnI class name, where inversion distinctions are not
        represented.

        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.forteClassTnI
        '3-11'

        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.forteClassTnI
        '3-11'

        Empty chords return 'N/A'

        >>> chord.Chord().forteClassTnI
        'N/A'

        Non-twelve-tone chords return as if all microtones and non-twelve-tone
        accidentals are removed:

        >>> chord.Chord('c~4 d`4').forteClassTnI
        '2-2'
        '''
        try:
            return tables.addressToForteName(self.chordTablesAddress, 'tni')
        except tables.ChordTablesException:
            return 'N/A'

    @property
    def fullName(self):
        '''
        Return the most complete representation of this Note, providing
        duration and pitch information.

        >>> c = chord.Chord(['D', 'F#', 'A'])
        >>> c.fullName
        'Chord {D | F-sharp | A} Quarter'

        >>> chord.Chord(['d1', 'e4-', 'b3-'], quarterLength=2/3).fullName
        'Chord {D in octave 1 | E-flat in octave 4 | B-flat in octave 3} Quarter Triplet (2/3 QL)'

        '''
        msg = []
        sub = []
        for p in self.pitches:
            sub.append(f'{p.fullName}')
        msg.append('Chord')
        msg.append(' {' + (' | '.join(sub)) + '} ')
        msg.append(self.duration.fullName)
        return ''.join(msg)

    @property
    def hasZRelation(self):
        '''
        Return True or False if the Chord has a Z-relation.

        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.hasZRelation
        False

        >>> c2 = chord.Chord(['c', 'c#', 'e', 'f#'])
        >>> c2.hasZRelation  # it is c, c#, e-, g
        True

        OMIT_FROM_DOCS

        >>> chord.Chord().hasZRelation
        False
        '''
        try:
            post = tables.addressToZAddress(self.chordTablesAddress)
        except tables.ChordTablesException:
            return False  # empty chords have no z-relations

        # environLocal.printDebug(['got post', post])
        if post is not None:
            return True
        return False

    @property
    def intervalVector(self):
        '''
        Return the interval vector for this Chord as a list of integers.

        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.intervalVector
        [0, 0, 1, 1, 1, 0]

        >>> c2 = chord.Chord(['c', 'c#', 'e', 'f#'])
        >>> c2.intervalVector
        [1, 1, 1, 1, 1, 1]

        >>> c3 = chord.Chord(['c', 'c#', 'e-', 'g'])
        >>> c3.intervalVector
        [1, 1, 1, 1, 1, 1]

        OMIT_FROM_DOCS

        >>> chord.Chord().intervalVector
        [0, 0, 0, 0, 0, 0]
        '''
        try:
            return list(tables.addressToIntervalVector(self.chordTablesAddress))
        except tables.ChordTablesException:
            return [0, 0, 0, 0, 0, 0]

    @property
    def intervalVectorString(self):
        '''
        Return the interval vector as a string representation.

        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.intervalVectorString
        '<001110>'
        '''
        return Chord.formatVectorString(self.intervalVector)

    @property
    def isPrimeFormInversion(self):
        '''
        Return True or False if the Chord represents a set class inversion.

        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.isPrimeFormInversion
        False

        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.isPrimeFormInversion
        True
        '''
        if self.chordTablesAddress.inversion == -1:
            return True
        else:
            return False

    @property
    def multisetCardinality(self):
        '''
        Return an integer representing the cardinality of the multiset, or the
        number of pitch values.

        >>> c1 = chord.Chord(['D4', 'A4', 'F#5', 'D6'])
        >>> c1.multisetCardinality
        4
        '''
        return len(self.pitchClasses)

    @property
    def notes(self) -> tuple[note.Note, ...]:
        '''
        Return a tuple (immutable) of the notes contained in the chord.

        Generally using .pitches or iterating over the chord is the best way to work with
        the components of a chord, but in unusual cases, a chord may, for instance, consist
        of notes with independent durations, volumes, or colors, or, more often, different tie
        statuses.  `Chord` includes methods such as `.setTie()` for most of these features,
        but from time to time accessing all the `Note` objects as a tuple can be valuable.

        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.duration.type = 'quarter'
        >>> c1Notes = c1.notes
        >>> c1Notes
        (<music21.note.Note C>, <music21.note.Note E->, <music21.note.Note G>)

        Note that to set duration independently, a new Duration object needs to
        be created.  Internal notes for Chords created from strings or pitches
        all share a Duration object.

        >>> c1.duration is c1Notes[0].duration
        True
        >>> c1Notes[1].duration is c1Notes[2].duration
        True

        >>> c1Notes[2].duration = duration.Duration('half')
        >>> c1.duration.type
        'quarter'
        >>> c1[2].duration.type
        'half'

        The property can also set the notes for a chord, but it must be
        set to an iterable of literal Note objects.

        >>> c1.notes = [note.Note('D#4'), note.Note('C#4')]
        >>> c1
        <music21.chord.Chord D#4 C#4>

        Notice that the notes set this way are not sorted -- this is a property for
        power users who want complete control.

        Any incorrect assignment raises a TypeError:

        >>> c1.notes = 'C E G'
        Traceback (most recent call last):
        TypeError: notes must be set with an iterable

        >>> c1.notes = [pitch.Pitch('C'), pitch.Pitch('E')]
        Traceback (most recent call last):
        TypeError: every element of notes must be a note.Note object

        In case of an error, the previous notes are not changed (for this reason,
        `.notes` cannot take a generator expression).

        >>> c1
        <music21.chord.Chord D#4 C#4>

        * New in v5.7
        '''
        return tuple(self._notes)

    @notes.setter
    def notes(self, newNotes: Iterable[note.Note]) -> None:
        '''
        sets notes to an iterable of Note objects
        '''
        if not common.isIterable(newNotes):
            raise TypeError('notes must be set with an iterable')
        if not all(isinstance(n, note.Note) for n in newNotes):
            raise TypeError('every element of notes must be a note.Note object')
        self._notes.clear()
        self.add(newNotes, runSort=False)

    @property  # type: ignore
    @cacheMethod
    def normalOrder(self):
        '''
        Return the normal order/normal form of the Chord represented as a list of integers:

        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.normalOrder
        [0, 3, 7]

        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.normalOrder
        [0, 4, 7]

        >>> c3 = chord.Chord(['d', 'f#', 'a'])
        >>> c3.normalOrder
        [2, 6, 9]

        >>> c3 = chord.Chord(['B-4', 'D5', 'F5'])
        >>> c3.normalOrder
        [10, 2, 5]

        To get normalOrder transposed to PC 0, do this:

        >>> c3 = chord.Chord(['B-4', 'D5', 'F5'])
        >>> normalOrder = c3.normalOrder
        >>> firstPitch = normalOrder[0]
        >>> [(pc - firstPitch) % 12 for pc in normalOrder]
        [0, 4, 7]

        To get normalOrder formatted as a vectorString run .formatVectorString on it:

        >>> c3.normalOrder
        [10, 2, 5]

        >>> chord.Chord.formatVectorString(c3.normalOrder)
        '<A25>'

        (this is equivalent...)

        >>> c3.formatVectorString(c3.normalOrder)
        '<A25>'

        OMIT_FROM_DOCS

        These were giving problems before:

        >>> chord.Chord('G#2 A2 D3 G3').normalOrder
        [7, 8, 9, 2]

        >>> chord.Chord('G3 D4 A-4 A4 C5 E5').normalOrder
        [7, 8, 9, 0, 2, 4]

        >>> chord.Chord('E#3 A3 C#4').normalOrder
        [1, 5, 9]

        >>> chord.Chord().normalOrder
        []
        '''
        cta = self.chordTablesAddress
        try:
            transposedNormalForm = tables.addressToTransposedNormalForm(cta)
        except tables.ChordTablesException:
            return []

        orderedPCs = self.orderedPitchClasses
        mustBePresentPCs = set(orderedPCs)
        for transposeAmount in orderedPCs:
            possibleNormalOrder = [(pc + transposeAmount) % 12 for pc in transposedNormalForm]
            if set(possibleNormalOrder) == mustBePresentPCs:
                return possibleNormalOrder
        raise ChordException('Could not find a normalOrder for chord: '
                             + str(self.orderedPitchClassesString))

    @property
    def normalOrderString(self):
        '''
        Return the normal order/normal form of the Chord as a string representation.

        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.normalOrder
        [0, 3, 7]

        >>> c1.normalOrderString
        '<037>'
        '''
        return Chord.formatVectorString(self.normalOrder)

    def _unorderedPitchClasses(self) -> set[int]:
        '''
        helper function for orderedPitchClasses but also routines
        like pitchClassCardinality which do not need sorting.

        Returns a set of ints
        '''
        pcGroup = set()
        for p in self.pitches:
            pcGroup.add(p.pitchClass)
        return pcGroup

    @property
    def orderedPitchClasses(self) -> list[int]:
        '''
        Return a list of pitch class integers, ordered form lowest to highest.

        >>> c1 = chord.Chord(['D4', 'A4', 'F#5', 'D6'])
        >>> c1.orderedPitchClasses
        [2, 6, 9]
        '''
        return list(sorted(self._unorderedPitchClasses()))

    @property
    def orderedPitchClassesString(self) -> str:
        '''
        Return a string representation of the pitch class values.

        >>> c1 = chord.Chord(['f#', 'e-', 'g'])
        >>> c1.orderedPitchClassesString
        '<367>'

        Redundancies are removed

        >>> c1 = chord.Chord(['f#', 'e-', 'e-', 'g'])
        >>> c1.orderedPitchClassesString
        '<367>'
        '''
        return Chord.formatVectorString(self.orderedPitchClasses)

    @property
    def pitchClassCardinality(self) -> int:
        '''
        Return the cardinality of pitch classes, or the number of unique
        pitch classes, in the Chord:

        >>> c1 = chord.Chord(['D4', 'A4', 'F#5', 'D6'])
        >>> c1.pitchClassCardinality
        3
        '''
        return len(self._unorderedPitchClasses())

    @property
    def pitchClasses(self) -> list[int]:
        '''
        Return a list of all pitch classes in the chord as integers. Not sorted

        >>> c1 = chord.Chord(['D4', 'A4', 'F#5', 'D6'])
        >>> c1.pitchClasses
        [2, 9, 6, 2]
        '''
        pcGroup = []
        for p in self.pitches:
            pcGroup.append(p.pitchClass)
        return pcGroup

    @property
    def pitchNames(self) -> list[str]:
        '''
        Return a list of Pitch names from each
        :class:`~music21.pitch.Pitch` object's
        :attr:`~music21.pitch.Pitch.name` attribute.

        >>> c = chord.Chord(['g#', 'd-'])
        >>> c.pitchNames
        ['G#', 'D-']

        >>> c = chord.Chord('C4 E4 G4 C4')
        >>> c.pitchNames
        ['C', 'E', 'G', 'C']

        >>> c.pitchNames = ['c2', 'g2']
        >>> c.pitchNames
        ['C', 'G']
        '''
        return [d.pitch.name for d in self._notes]

    @pitchNames.setter
    def pitchNames(self, value):
        if common.isListLike(value):
            if isinstance(value[0], str):  # only checking first
                self._notes = []  # clear
                for name in value:
                    self._notes.append(note.Note(name))
            else:
                raise ChordException(
                    f'must provide a list containing a Pitch, not: {value}')
        else:
            raise ChordException(f'cannot set pitch name with provided object: {value}')
        self.clearCache()

    @property
    def pitchedCommonName(self) -> str:
        '''
        Return a common name of this Chord including a pitch identifier, if possible:

        Most common chords will use the root as the pitch name and have it at the beginning:

        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.pitchedCommonName
        'C-minor triad'

        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.pitchedCommonName
        'C-major triad'

        Because the hyphen is confusing w/ music21 flat notation, flats are displayed
        as "b":

        >>> c2a = chord.Chord('C-2 E-2 G-2')
        >>> c2a.pitchedCommonName
        'Cb-major triad'

        Other forms might have the pitch elsewhere.  Thus, this is a method for display,
        not for extracting information:

        >>> c3 = chord.Chord('A#2 D3 F3')
        >>> c3.pitchedCommonName
        'enharmonic equivalent to major triad above A#'

        Note that in this case, the bass, not the root is used to determine the pitch name:

        >>> c4 = chord.Chord('D3 F3 A#3')
        >>> c4.pitchedCommonName
        'enharmonic equivalent to major triad above D'

        >>> c5 = chord.Chord([1, 2, 3, 4, 5, 10])
        >>> c5.pitchedCommonName
        'forte class 6-36B above C#'

        >>> c4 = chord.Chord('D3 F3 A#3')
        >>> c4.pitchedCommonName
        'enharmonic equivalent to major triad above D'


        A single pitch just returns that pitch name:

        >>> chord.Chord(['D3']).pitchedCommonName
        'D'

        Unless there is more than one octave:

        >>> chord.Chord('D3 D4').pitchedCommonName
        'Perfect Octave above D'
        >>> chord.Chord('D3 D4 D5').pitchedCommonName
        'multiple octaves above D'


        Two different pitches give interval names:

        >>> chord.Chord('F3 C4').pitchedCommonName
        'Perfect Fifth above F'

        Compound intervals are used unless there are multiple octaves:

        >>> chord.Chord('E-3 C5').pitchedCommonName
        'Major Thirteenth above Eb'
        >>> chord.Chord('E-3 C5 C6').pitchedCommonName
        'Major Sixth with octave doublings above Eb'


        These one-pitch-class and two-pitch-class chords with multiple enharmonics are unusual:

        >>> chord.Chord('D#3 E-3').pitchedCommonName
        'enharmonic unison above D#'
        >>> chord.Chord('D#3 E-3 D#4').pitchedCommonName
        'enharmonic octaves above D#'
        >>> chord.Chord('D#3 E-3 E3').pitchedCommonName
        '1 semitone above D#'
        >>> chord.Chord('D#3 E-3 F3 G--4').pitchedCommonName
        '2 semitones above D#'

        >>> chord.Chord().pitchedCommonName
        'empty chord'

        * Changed in v5.5: octaves never included, flats are converted,
          special tools for enharmonics.
        * Changed in v6.5: special names for 0-, 1-, and 2-pitchClass chords.
        '''
        nameStr = self.commonName
        if nameStr == 'empty chord':
            return nameStr

        if nameStr in ('note', 'unison'):
            return self.pitches[0].name


        if self.pitchClassCardinality <= 2 or (
                'enharmonic' in nameStr
                or 'forte class' in nameStr
                or ' semitone' in nameStr):
            # root detection gives weird results for pitchedCommonName
            bass = self.bass()
            bassName = bass.name.replace('-', 'b')
            return f'{nameStr} above {bassName}'
        else:
            try:
                root = self.root()
            except ChordException:  # if a root cannot be found
                root = self.pitches[0]
            rootName = root.name.replace('-', 'b')
            return f'{rootName}-{nameStr}'

    @property
    def pitches(self) -> tuple[pitch.Pitch, ...]:
        '''
        Get or set a list or tuple of all Pitch objects in this Chord.

        >>> c = chord.Chord(['C4', 'E4', 'G#4'])
        >>> c.pitches
        (<music21.pitch.Pitch C4>, <music21.pitch.Pitch E4>, <music21.pitch.Pitch G#4>)

        >>> [p.midi for p in c.pitches]
        [60, 64, 68]

        >>> d = chord.Chord()
        >>> d.pitches = c.pitches
        >>> d.pitches
        (<music21.pitch.Pitch C4>, <music21.pitch.Pitch E4>, <music21.pitch.Pitch G#4>)

        >>> c = chord.Chord(['C4', 'A4', 'E5'])
        >>> c.bass()
        <music21.pitch.Pitch C4>

        >>> c.root()
        <music21.pitch.Pitch A4>


        Note here that the list will be converted to a tuple:

        >>> c.pitches = ['C#4', 'A#4', 'E#5']
        >>> c.pitches
        (<music21.pitch.Pitch C#4>, <music21.pitch.Pitch A#4>, <music21.pitch.Pitch E#5>)

        Bass and root information is also changed.

        >>> c.bass()
        <music21.pitch.Pitch C#4>

        >>> c.root()
        <music21.pitch.Pitch A#4>
        '''
        # noinspection PyTypeChecker
        pitches: tuple[pitch.Pitch, ...] = tuple(component.pitch for component in self._notes)
        return pitches

    @pitches.setter
    def pitches(self, value: Sequence[str | pitch.Pitch | int]):
        self._notes = []
        self.clearCache()
        # TODO: individual ties are not being retained here
        for p in value:
            # assumes value is an iterable of pitches or something to pass to Note __init__
            self._notes.append(note.Note(p))

    @property
    def primeForm(self) -> list[int]:
        '''
        Return a representation of the Chord as a prime-form list of pitch
        class integers:

        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.primeForm
        [0, 3, 7]

        >>> c2 = chord.Chord(['c', 'e', 'g'])
        >>> c2.primeForm
        [0, 3, 7]

        OMIT_FROM_DOCS

        >>> chord.Chord().primeForm
        []
        '''
        try:
            return list(tables.addressToPrimeForm(self.chordTablesAddress))
        except tables.ChordTablesException:
            return []

    @property
    def primeFormString(self) -> str:
        '''
        Return a representation of the Chord as a prime-form set class string.

        >>> c1 = chord.Chord(['c', 'e-', 'g'])
        >>> c1.primeFormString
        '<037>'

        >>> c1 = chord.Chord(['c', 'e', 'g'])
        >>> c1.primeFormString
        '<037>'
        '''
        return Chord.formatVectorString(self.primeForm)


    @property  # type: ignore
    @cacheMethod
    def quality(self):
        '''
        Returns the quality of the underlying triad of a triad or
        seventh, either major, minor, diminished, augmented, or other:

        >>> a = chord.Chord(['a', 'c', 'e'])
        >>> a.quality
        'minor'

        Inversions don't matter, nor do added tones so long as a root can be
        found:

        >>> a = chord.Chord(['f', 'b', 'd', 'g'])
        >>> a.quality
        'major'

        >>> a = chord.Chord(['c', 'a-', 'e'])
        >>> a.quality
        'augmented'

        >>> a = chord.Chord(['c', 'c#', 'd'])
        >>> a.quality
        'other'

        Incomplete triads are returned as major or minor:

        >>> a = chord.Chord(['c', 'e-'])
        >>> a.quality
        'minor'

        >>> a = chord.Chord(['e-', 'g'])
        >>> a.quality
        'major'

        Chords that contain more than one triad return 'other'

        >>> chord.Chord('C C# E G').quality
        'other'
        >>> chord.Chord('C E- E G').quality
        'other'
        >>> chord.Chord('C E G- G').quality
        'other'

        Note these two edge cases:

        >>> chord.Chord('C D E').quality  # NB! Major 9th....
        'major'
        >>> chord.Chord('C E--').quality
        'other'

        Empty chords are definitely 'other':

        >>> chord.Chord().quality
        'other'
        '''
        try:
            third = self.semitonesFromChordStep(3)
            fifth = self.semitonesFromChordStep(5)
        except ChordException:
            return 'other'

        # environLocal.printDebug(['third, fifth', third, fifth])
        if third is None:
            return 'other'
        elif self.hasRepeatedChordStep(1):
            return 'other'
        elif self.hasRepeatedChordStep(3):
            return 'other'
        elif fifth is None:
            if third == 4:
                return 'major'
            elif third == 3:
                return 'minor'
            else:
                return 'other'
        elif self.hasRepeatedChordStep(5):
            return 'other'
        elif fifth == 7 and third == 4:
            return 'major'
        elif fifth == 7 and third == 3:
            return 'minor'
        elif fifth == 8 and third == 4:
            return 'augmented'
        elif fifth == 6 and third == 3:
            return 'diminished'
        else:
            return 'other'


    @property
    def scaleDegrees(self):
        '''
        Returns a list of two-element tuples for each pitch in the chord where
        the first element of the tuple is the scale degree as an int and the
        second is an Accidental object that specifies the alteration from the
        scale degree (could be None if the note is not part of the scale).

        It is easiest to see the utility of this method using a chord subclass,
        :class:`music21.roman.RomanNumeral`, but it is also callable from this
        Chord object if the Chord has a Key or Scale context set for it.

        >>> k = key.Key('f#')  # 3-sharps minor
        >>> rn = roman.RomanNumeral('V', k)
        >>> rn.key
        <music21.key.Key of f# minor>

        >>> rn.pitches
        (<music21.pitch.Pitch C#5>, <music21.pitch.Pitch E#5>, <music21.pitch.Pitch G#5>)

        >>> rn.scaleDegrees
        [(5, None), (7, <music21.pitch.Accidental sharp>), (2, None)]

        >>> rn2 = roman.RomanNumeral('N6', k)
        >>> rn2.pitches
        (<music21.pitch.Pitch B4>, <music21.pitch.Pitch D5>, <music21.pitch.Pitch G5>)

        >>> rn2.scaleDegrees  # N.B. -- natural form used for minor!
        [(4, None), (6, None), (2, <music21.pitch.Accidental flat>)]

        As mentioned above, the property can also get its scale from context if
        the chord is embedded in a Stream.  Let's create the same V in f#-minor
        again, but give it a context of c-sharp minor, and then c-minor instead:

        >>> chord1 = chord.Chord(['C#5', 'E#5', 'G#5'])
        >>> st1 = stream.Stream()
        >>> st1.append(key.Key('c#'))  # c-sharp minor
        >>> st1.append(chord1)
        >>> chord1.scaleDegrees
        [(1, None), (3, <music21.pitch.Accidental sharp>), (5, None)]

        >>> st2 = stream.Stream()
        >>> chord2 = chord.Chord(['C#5', 'E#5', 'G#5'])
        >>> st2.append(key.Key('c'))  # c minor
        >>> st2.append(chord2)        # same pitches as before gives different scaleDegrees
        >>> chord2.scaleDegrees
        [(1, <music21.pitch.Accidental sharp>),
         (3, <music21.pitch.Accidental double-sharp>),
         (5, <music21.pitch.Accidental sharp>)]

        >>> st3 = stream.Stream()
        >>> st3.append(key.Key('C'))  # C major
        >>> chord2 = chord.Chord(['C4', 'C#4', 'D4', 'E-4', 'E4', 'F4'])  # 1st 1/2 of chromatic
        >>> st3.append(chord2)
        >>> chord2.scaleDegrees
        [(1, None), (1, <music21.pitch.Accidental sharp>), (2, None),
         (3, <music21.pitch.Accidental flat>), (3, None), (4, None)]

        If no context can be found, return `None`:

        >>> chord.Chord('C4 E4 G4').scaleDegrees is None
        True

        * Changed in v6.5: will return `None` if no context can be found:
        '''
        from music21 import scale
        # roman numerals have this built in as the key attribute
        if hasattr(self, 'key') and self.key is not None:  # pylint: disable=no-member
            # Key is a subclass of scale.DiatonicScale
            sc = self.key  # pylint: disable=no-member
        else:
            sc = self.getContextByClass(scale.Scale, sortByCreationTime=True)
            if sc is None:
                return None
        degrees = []
        for thisPitch in self.pitches:
            degree = sc.getScaleDegreeFromPitch(
                thisPitch,
                comparisonAttribute='step',
                direction=scale.Direction.DESCENDING,
            )
            if degree is None:
                degrees.append((None, None))
            else:
                actualPitch = sc.pitchFromDegree(
                    degree,
                    direction=scale.Direction.DESCENDING
                )
                if actualPitch.name == thisPitch.name:
                    degrees.append((degree, None))
                else:
                    actualPitch.octave = thisPitch.octave
                    tupleKey = (degree,
                                pitch.Accidental(int(thisPitch.ps - actualPitch.ps)))
                    degrees.append(tupleKey)
        return degrees

    @property  # type: ignore
    @cacheMethod
    def seventh(self):
        '''
        Shortcut for getChordStep(7), but caches the value

        >>> bDim7_2ndInv = chord.Chord(['F2', 'A-3', 'B4', 'D5'])
        >>> bDim7_2ndInv.seventh
        <music21.pitch.Pitch A-3>

        Test whether this strange chord gets the B# not the C or something else:

        >>> c = chord.Chord(['C4', 'E4', 'G4', 'B#4'])
        >>> c.seventh
        <music21.pitch.Pitch B#4>

        * Changed in v6.5: return None on empty chords/errors

        OMIT_FROM_DOCS

        >>> chord.Chord().seventh
        '''
        try:
            return self.getChordStep(7)
        except ChordException:
            return None

    @property  # type: ignore
    @cacheMethod
    def third(self) -> pitch.Pitch | None:
        '''
        Shortcut for getChordStep(3), but caches the value, and returns
        None on errors.

        >>> cMaj1stInv = chord.Chord(['E3', 'C4', 'G5'])
        >>> cMaj1stInv.third
        <music21.pitch.Pitch E3>

        >>> cMaj1stInv.third.octave
        3

        * Changed in v6.5: return `None` on empty chords/errors

        OMIT_FROM_DOCS

        >>> chord.Chord().third
        '''
        try:
            return self.getChordStep(3)
        except ChordException:
            return None



def fromForteClass(notation: str | Sequence[int]) -> Chord:
    '''
    Return a Chord given a Forte-class notation. The Forte class can be
    specified as string (e.g., 3-11) or as a list of cardinality and number
    (e.g., [8, 1]).

    If no match is available, None is returned.

    >>> chord.fromForteClass('3-11')
    <music21.chord.Chord C E- G>

    >>> chord.fromForteClass('3-11b')
    <music21.chord.Chord C E G>

    >>> chord.fromForteClass('3-11a')
    <music21.chord.Chord C E- G>

    >>> chord.fromForteClass((11, 1))
    <music21.chord.Chord C D- D E- E F G- G A- A B->

    '''
    card = None
    num = 1
    inv = None
    if isinstance(notation, str):
        if '-' in notation:
            notationParts = notation.split('-')
            card = int(notationParts[0])
            str_num, chars = common.getNumFromStr(notationParts[1])
            num = int(str_num)
            if 'a' in chars.lower():
                inv = 1
            elif 'b' in chars.lower():
                inv = -1
        else:
            raise ChordException(
                f'cannot extract set-class representation from string: {notation}')
    elif common.isListLike(notation):
        if len(notation) <= 3:
            # assume it's a set-class representation
            if notation:
                card = notation[0]
            if len(notation) > 1:
                num = notation[1]
            if len(notation) > 2:
                inv = notation[2]
        else:
            raise ChordException(f'cannot handle specified notation: {notation}')
    else:
        raise ChordException(f'cannot handle specified notation: {notation}')

    prime = tables.addressToTransposedNormalForm([card, num, inv])
    return Chord(prime)


def fromIntervalVector(notation, getZRelation=False):
    '''
    Return one or more Chords given an interval vector.

    >>> chord.fromIntervalVector([0, 0, 0, 0, 0, 1])
    <music21.chord.Chord C F#>

    >>> chord.fromIntervalVector((5, 5, 5, 5, 5, 5)) is None
    True

    >>> chord.fromIntervalVector((1, 1, 1, 1, 1, 1))
    <music21.chord.Chord C C# E F#>

    >>> chord.fromIntervalVector((1, 1, 1, 1, 1, 1), getZRelation=True)
    <music21.chord.Chord C D- E- G>

    >>> chord.fromIntervalVector((1, 1, 1, 1, 1, 1)).getZRelation()
    <music21.chord.Chord C D- E- G>

    '''
    addressList = None
    if common.isListLike(notation):
        if len(notation) == 6:  # assume it's an interval vector
            addressList = tables.intervalVectorToAddress(notation)
    if addressList is None:
        raise ChordException(f'cannot handle specified notation: {notation}')

    post = []
    for address in addressList:
        post.append(Chord(tables.addressToTransposedNormalForm(address)))
    # for now, return the first chord
    # z-related chords will have more than one
    if len(post) == 1:
        return post[0]
    elif len(post) == 2 and not getZRelation:
        return post[0]
    elif len(post) == 2 and getZRelation:
        return post[1]
    else:
        return None



# ------------------------------------------------------------------------------
class Test(unittest.TestCase):
    '''
    Most tests now in test/test_chord
    '''
    def testCopyAndDeepcopy(self):
        from music21.test.commonTest import testCopyAll
        testCopyAll(self, globals())



_DOC_ORDER = [Chord]


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)  # , runTest='testInvertingSimple')
