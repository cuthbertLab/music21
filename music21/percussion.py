# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         percussion.py
# Purpose:      music21 classes for representing unpitched events
#
# Authors:      Jacob Tyler Walls
#               Michael Scott Asato Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2006-2019 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
from __future__ import annotations

from collections.abc import Iterable
import typing as t
import unittest

from music21 import common
from music21 import chord
from music21 import note


if t.TYPE_CHECKING:
    from music21 import pitch


class PercussionChord(chord.ChordBase):
    '''
    :class:`~music21.chord.ChordBase` and `:class:`~music21.note.NotRest` subclass that is NOT
    a :class:`~music21.chord.Chord` because one or more notes is an :class:`~music21.note.Unpitched`
    object.

    >>> pChord = percussion.PercussionChord([note.Unpitched(displayName='D4'), note.Note('E5')])
    >>> pChord.isChord
    False

    Has notes, just like any ChordBase:

    >>> pChord.notes
    (<music21.note.Unpitched object at 0x...>, <music21.note.Note E>)

    Assign them to another PercussionChord:

    >>> pChord2 = percussion.PercussionChord()
    >>> pChord2.notes = pChord.notes
    >>> pChord2.notes
    (<music21.note.Unpitched object at 0x...>, <music21.note.Note E>)

    Don't attempt setting anything but Note or Unpitched objects as notes:

    >>> pChord2.notes = [note.Rest()]
    Traceback (most recent call last):
    TypeError: every element of notes must be a note.Note or note.Unpitched object

    **Equality**

    Two PercussionChord objects are equal if their notes are equal *and in the same
    order* (this is different from Chord, but necessary because we cannot compare
    based just on pitch equality)

    >>> pChord == pChord2
    True
    >>> pChord3 = percussion.PercussionChord([note.Unpitched('D4')])
    >>> pChord == pChord3
    False

    OMIT_FROM_DOCS

    See the repr of an empty percussion chord:

    >>> percussion.PercussionChord()
    <music21.percussion.PercussionChord object at 0x...>

    This is in OMIT
    '''
    isChord = False

    def __deepcopy__(self, memo=None):
        new = super().__deepcopy__(memo=memo)
        for n in new._notes:
            n._chordAttached = new
        return new

    def __eq__(self, other):
        '''
        Returns True if all the notes are equal and in the same order.
        '''
        if not super().__eq__(other):
            return False
        # super ensures that both have same number of notes.
        for my_n, other_n in zip(self.notes, other.notes):
            if my_n != other_n:
                return False
        return True

    def __hash__(self):
        return id(self) >> 4

    @property
    def notes(self) -> tuple[note.NotRest, ...]:
        return tuple(self._notes)

    @notes.setter
    def notes(self, newNotes: Iterable[note.Unpitched | note.Note]) -> None:
        '''
        Sets notes to an iterable of Note or Unpitched objects
        '''
        if not common.isIterable(newNotes):
            raise TypeError('notes must be set with an iterable')
        if not all(isinstance(n, (note.Unpitched, note.Note)) for n in newNotes):
            raise TypeError('every element of notes must be a note.Note or note.Unpitched object')
        self._notes.clear()
        self.add(newNotes)

    def _reprInternal(self) -> str:
        if not self.notes:
            return super()._reprInternal()

        allNotes = []
        for thisNote in self.notes:
            if isinstance(thisNote, note.Note):
                allNotes.append(thisNote.nameWithOctave)
            elif isinstance(thisNote, note.Unpitched):
                if thisNote.storedInstrument:
                    allNotes.append(str(thisNote.storedInstrument.instrumentName))
                else:
                    allNotes.append(f'unpitched[{thisNote.displayName}]')

        return '[' + ' '.join(allNotes) + ']'


    @property
    def pitches(self) -> tuple[pitch.Pitch, ...]:
        '''
        Get or set a list or tuple of all Pitch objects in this PercussionChord.

        Unpitched members (that at most have only display pitches) are ignored.

        >>> pChord = percussion.PercussionChord([note.Unpitched(displayName='D4'), note.Note('E5')])
        >>> pChord.pitches
        (<music21.pitch.Pitch E5>,)

        >>> pChord.pitches = [60]
        >>> pChord.pitches
        (<music21.pitch.Pitch C4>,)

        Notice that setting pitches has now just cleared any existing notes, pitched or unpitched:
        >>> pChord.notes
        (<music21.note.Note C>,)
        '''
        pitches: tuple[pitch.Pitch, ...] = tuple(
            component.pitch for component in self._notes if isinstance(component, note.Note))
        return pitches

    @pitches.setter
    def pitches(self, value: t.Sequence[str | pitch.Pitch | int]):
        self._notes = []
        # TODO: individual ties are not being retained here
        for p in value:
            # assumes value is an iterable of pitches or something to pass to Note __init__
            self._notes.append(note.Note(p))


class Test(unittest.TestCase):
    pass


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
