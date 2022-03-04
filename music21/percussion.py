# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         percussion.py
# Purpose:      music21 classes for representing unpitched events
#
# Authors:      Jacob Tyler Walls
#               Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2006-2019 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------

import unittest

from music21 import common
from music21 import chord
from music21 import note


class PercussionChord(chord.ChordBase):
    '''
    :class:`~music21.chord.ChordBase` and `:class:`~music21.note.NotRest` subclass that is NOT
    a :class:`~music21.chord.Chord` because one or more notes is an :class:`~music21.note.Unpitched`
    object.

    >>> pChord = percussion.PercussionChord([note.Unpitched('D4'), note.Note('E5')])
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

    OMIT_FROM_DOCS

    See the repr of an empty percussion chord:

    >>> percussion.PercussionChord()
    <music21.percussion.PercussionChord object at 0x...>
    '''

    isChord = False


    @property
    def notes(self) -> tuple:
        return tuple(self._notes)

    @notes.setter
    def notes(self, newNotes):
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
            if hasattr(thisNote, 'nameWithOctave'):
                allNotes.append(thisNote.nameWithOctave)
            elif thisNote.storedInstrument:
                allNotes.append(str(thisNote.storedInstrument.instrumentName))
            else:
                allNotes.append(f'unpitched[{thisNote.displayName}]')

        return '[' + ' '.join(allNotes) + ']'


class Test(unittest.TestCase):
    pass


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
