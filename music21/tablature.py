# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         tablature.py
# Purpose:      Object for storing music21 information in the form of musical tablature.
#
# Authors:      Luke Poeppel
#
# Copyright:    Copyright © 2006-2016 Michael Scott Cuthbert and the music21 Project
# Licence:      BSD, see licence.txt
# ------------------------------------------------------------------------------
'''
Music21 representation of FretNote and FretBoard objects.

TODO:
Chord from Figure
Chord from FretBoard Object with tuning.
'''
import unittest
from typing import List, Optional

from music21 import common
from music21 import exceptions21
from music21 import harmony
from music21 import pitch
from music21 import prebase


class TablatureException(exceptions21.Music21Exception):
    pass


class FretNote(prebase.ProtoM21Object):
    '''
    A FretNote represents a note on a Fretboard, where each string should
    be fingered (or not).

    >>> fn = tablature.FretNote(3, 4, 1)
    >>> fn
    <music21.tablature.FretNote 3rd string, 4th fret, 1st finger>

    >>> fn.string
    3
    >>> fn.fret
    4
    >>> fn.fingering
    1
    >>> fn.displayFingerNumber
    True

    >>> fnStupid = tablature.FretNote()
    >>> fnStupid.string is None
    True
    '''
    def __init__(self, string=None, fret=None, fingering=None):
        self.string = string
        self.fret = fret
        self.fingering = fingering
        self.displayFingerNumber = True

    def _reprInternal(self):
        '''
        Defines the representation of a FretNote object under music21 standards.

        >>> fn = tablature.FretNote(4, 2, 1)
        >>> fn
        <music21.tablature.FretNote 4th string, 2nd fret, 1st finger>

        >>> fn2 = tablature.FretNote(3, 2)
        >>> fn2
        <music21.tablature.FretNote 3rd string, 2nd fret>

        >>> fn3 = tablature.FretNote(fret=2, fingering=3)
        >>> fn3
        <music21.tablature.FretNote 2nd fret, 3rd finger>

        >>> emptyNote = tablature.FretNote()
        >>> emptyNote
        <music21.tablature.FretNote>
        '''
        def abbr(x):
            return f'{x}{common.ordinalAbbreviation(x)}'

        if self.string is not None:
            stringRepr = f'{abbr(self.string)} string'
        else:
            stringRepr = ''

        if self.fret is not None:
            fretRepr = f'{abbr(self.fret)} fret'
        else:
            fretRepr = ''

        if self.fingering is not None:
            fingeringRepr = f'{abbr(self.fingering)} finger'
        else:
            fingeringRepr = ''

        nonEmptyRepr = []
        for thisRepr in stringRepr, fretRepr, fingeringRepr:
            if thisRepr != '':
                nonEmptyRepr.append(thisRepr)

        fullRepr = ', '.join(nonEmptyRepr)
        return fullRepr


class FretBoard(prebase.ProtoM21Object):
    '''
    A FretBoard represents a displayed fretboard (i.e. used in chord symbols).
    To be displayed, a fretboard requires a tuning system, defined by the fretted instrument
    classes defined.

    >>> fn1 = tablature.FretNote(string=3, fret=2, fingering=1)
    >>> fn2 = tablature.FretNote(string=2, fret=3, fingering=3)
    >>> fn3 = tablature.FretNote(string=1, fret=2, fingering=2)
    >>> fb = tablature.FretBoard(6, fretNotes=[fn1, fn2, fn3], displayFrets=5)
    >>> fb.numStrings
    6
    >>> fb
    <music21.tablature.FretBoard 6 strings, 3 notes, 5 frets>
    >>> len(fb.fretNotes)
    3
    >>> fb.fretNotes[0]
    <music21.tablature.FretNote 3rd string, 2nd fret, 1st finger>

    >>> fb.getFretNoteByString(2)
    <music21.tablature.FretNote 2nd string, 3rd fret, 3rd finger>
    '''

    def __init__(self, numStrings=6, fretNotes=None, displayFrets=4):
        if fretNotes is None:
            fretNotes = []

        self.numStrings = numStrings
        self.fretNotes = fretNotes
        self.displayFrets = displayFrets

        self.tuning = []

    def _reprInternal(self):
        '''
        >>> fn3 = tablature.FretNote(string=6, fret=1, fingering=1)
        >>> fn2 = tablature.FretNote(string=4, fret=2, fingering=2)
        >>> fn1 = tablature.FretNote(string=2, fret=4, fingering=4)
        >>> fb = tablature.FretBoard(6, fretNotes=[fn3, fn2, fn1], displayFrets=4)
        >>> fb
        <music21.tablature.FretBoard 6 strings, 3 notes, 4 frets>
        '''
        return f'{self.numStrings} strings, {len(self.fretNotes)} notes, {self.displayFrets} frets'

    def fretNotesLowestFirst(self):
        # noinspection PyShadowingNames
        '''
        Returns a list of FretNotes in lowest to highest string order.

        >>> firstNote = tablature.FretNote(string=2, fret=3, fingering=4)
        >>> secondNote = tablature.FretNote(string=3, fret=3, fingering=3)
        >>> thirdNote = tablature.FretNote(string=1, fret=3, fingering=3)
        >>> myFretBoard = tablature.FretBoard(6, fretNotes=[firstNote, secondNote, thirdNote])
        >>> for thisFretNote in myFretBoard.fretNotesLowestFirst():
        ...    print(thisFretNote)
        <music21.tablature.FretNote 3rd string, 3rd fret, 3rd finger>
        <music21.tablature.FretNote 2nd string, 3rd fret, 4th finger>
        <music21.tablature.FretNote 1st string, 3rd fret, 3rd finger>
        '''
        allFretNotes = []

        for stringNumber in range(self.numStrings, 0, -1):
            thisFretNote = self.getFretNoteByString(stringNumber)
            if thisFretNote is None:
                continue

            allFretNotes.append(thisFretNote)

        return allFretNotes

    def getFretNoteByString(self, requestedString):
        '''
        Returns FretNote object on a given string or None if there are none.

        >>> firstNote = tablature.FretNote(string=6, fret=3, fingering=4)
        >>> secondNote = tablature.FretNote(string=2, fret=3, fingering=3)
        >>> myFretBoard = tablature.FretBoard(6, fretNotes=[firstNote, secondNote])
        >>> myFretBoard.getFretNoteByString(6)
        <music21.tablature.FretNote 6th string, 3rd fret, 4th finger>

        >>> myFretBoard.getFretNoteByString(2)
        <music21.tablature.FretNote 2nd string, 3rd fret, 3rd finger>

        >>> myFretBoard.getFretNoteByString(9) is None
        True
        '''
        for thisFretNote in self.fretNotes:
            if requestedString == thisFretNote.string:
                return thisFretNote

        return None

    def getPitches(self):
        '''
        Returns a list of all the pitches (or None for each) given the FretNote information. This
        requires a tuning to be set.

        >>> firstNote = tablature.FretNote(string=4, fret=3, fingering=3)
        >>> secondNote = tablature.FretNote(string=2, fret=1, fingering=1)
        >>> gfb = tablature.GuitarFretBoard(fretNotes=[firstNote, secondNote])
        >>> gfb.getPitches()
        [None, None, <music21.pitch.Pitch F3>, None, <music21.pitch.Pitch C4>, None]

        What if the User provides an empty FretBoard?
        >>> gfb2 = tablature.GuitarFretBoard(fretNotes=[])
        >>> gfb2.getPitches()
        [None, None, None, None, None, None]

        Works for other stringed instruments, as long as the tuning is included (see below).

        >>> tablature.UkeleleFretBoard().numStrings
        4
        >>> uke = tablature.UkeleleFretBoard(fretNotes=[firstNote, secondNote])
        >>> uke.getPitches()
        [<music21.pitch.Pitch B-4>, None, <music21.pitch.Pitch F4>, None]
        '''
        if len(self.tuning) != self.numStrings:
            raise TablatureException(
                'Tuning must be set first, tuned for {0} notes, on a {1} string instrument'.format(
                    len(self.tuning),
                    self.numStrings
                ))

        pitchList: List[Optional['music21.pitch.Pitch']] = [None] * self.numStrings

        if not self.fretNotes:
            return pitchList

        for thisFretNote in self.fretNotes:
            pitchListPosition = (thisFretNote.string * -1)

            tuningPitch = self.tuning[pitchListPosition]
            tuningPitchAsPs = tuningPitch.ps
            actualPitch = tuningPitchAsPs + thisFretNote.fret
            displayPitch = pitch.Pitch(actualPitch)

            pitchList[pitchListPosition] = displayPitch

        return pitchList


class FirstFret:
    '''
    FirstFretInfo returns the information regarding the first fret utilized in a
    given chord position.
    '''

    def __init__(self, fretNum, location="right"):
        self.fretNum = fretNum
        self.location = location

# class that combines a ChordSymbol and a FretBoard


class ChordWithFretBoard(harmony.ChordSymbol, FretBoard):
    '''
    Music21Object subclass that combines a ChordSymbol with a FretBoard.
    Tuning must be set!

    >>> fn4 = tablature.FretNote(string=4, fret=0)
    >>> fn3 = tablature.FretNote(string=3, fret=2, fingering=2)
    >>> fn2 = tablature.FretNote(string=2, fret=3, fingering=3)
    >>> fn1 = tablature.FretNote(string=1, fret=2, fingering=4)
    >>> cwf = tablature.ChordWithFretBoard('Dm', fretNotes=[fn1, fn2, fn3, fn4])
    '''

    def __init__(self, figure=None, numStrings=6, fretNotes=None, displayFrets=4, **keywords):
        harmony.ChordSymbol.__init__(self, figure=figure, **keywords)
        # uncomment when self.getFretNotesFromFigure() works...
        # if fretNotes is None:
        #     fretNotes = self.getFretNotesFromFigure()

        FretBoard.__init__(self,
                           numStrings=numStrings,
                           fretNotes=fretNotes,
                           displayFrets=displayFrets)

    def getFretNotesFromFigure(self):
        '''
        TODO:
        Given a chord with fret Figure, getFretNotesFromFigure returns each FretNote object
        within it.
        '''
        # figure = self.figure
        return None

# -------------------------------------------------------------------------------
#
# The following classes are some basic fretted instruments that are commonly used in
# Tablature notation.
#


class GuitarFretBoard(FretBoard):
    '''
    A six-string fretboard tuned to E A D G B E.
    '''

    def __init__(self, fretNotes=None, displayFrets=4):
        numStrings = 6
        super().__init__(numStrings, fretNotes, displayFrets)

        self.tuning = [pitch.Pitch('E2'), pitch.Pitch('A2'), pitch.Pitch('D3'),
                       pitch.Pitch('G3'), pitch.Pitch('B3'), pitch.Pitch('E4')]


class UkeleleFretBoard(FretBoard):
    '''
    A four-string fretboard tuned to G C E A
    '''

    def __init__(self, fretNotes=None, displayFrets=4):
        numStrings = 4
        super().__init__(numStrings, fretNotes, displayFrets)

        self.tuning = [pitch.Pitch('G4'), pitch.Pitch('C4'), pitch.Pitch('E4'), pitch.Pitch('A4')]


class BassGuitarFretBoard(FretBoard):
    '''
    A four-string fretboard tuned to E A D G
    '''

    def __init__(self, fretNotes=None, displayFrets=4):
        numStrings = 4
        super().__init__(numStrings, fretNotes, displayFrets)

        self.tuning = [pitch.Pitch('E1'), pitch.Pitch('A1'), pitch.Pitch('D2'), pitch.Pitch('G2')]


class MandolinFretBoard(FretBoard):
    '''
    A four-string fretboard tuned to G D A E
    '''

    def __init__(self, fretNotes=None, displayFrets=4):
        numStrings = 4
        super().__init__(numStrings, fretNotes, displayFrets)

        self.tuning = [pitch.Pitch('G3'), pitch.Pitch('D4'), pitch.Pitch('A4'), pitch.Pitch('E5')]
# ------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def testFretNoteString(self):
        f = FretNote(4, 1, 2)

        stringAndFretInfo = [f.string, f.fret]

        self.assertEqual(stringAndFretInfo, [4, 1])

    def testStupidFretNote(self):
        self.assertEqual(FretNote().string, None)

    def testFretNoteWeirdRepr(self):
        from music21 import tablature
        weirdFretNote = tablature.FretNote(6, 133)

        expectedRepr = '<music21.tablature.FretNote 6th string, 133rd fret>'

        self.assertEqual(repr(weirdFretNote), expectedRepr)

    def testFretBoardLowestFirst(self):
        fretNote1 = FretNote(1, 2, 2)
        fretNote2 = FretNote(2, 1, 1)

        myFretBoard = FretBoard(6, fretNotes=[fretNote1, fretNote2])

        stringList = []

        for thisNote in myFretBoard.fretNotesLowestFirst():
            stringList.append(thisNote.string)

        self.assertEqual(stringList, [2, 1])


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
