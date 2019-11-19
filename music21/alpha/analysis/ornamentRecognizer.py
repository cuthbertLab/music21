# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         alpha/analysis/ornamentRecognizer.py
# Purpose:      Identifies expanded ornaments
#
# Authors:      Janelle Sands
#
# Copyright:    Copyright © 2016 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
# ------------------------------------------------------------------------------
import unittest
from copy import deepcopy
from typing import Union

from music21 import duration
from music21 import expressions
from music21 import interval
from music21 import note
from music21 import stream


class OrnamentRecognizer:
    '''
    An object to identify if a stream of notes is an expanded ornament.
    '''
    def __init__(self, busyNotes, simpleNotes=None):
        self.simpleNotes = simpleNotes
        self.busyNotes = busyNotes


class TrillRecognizer(OrnamentRecognizer):
    '''
    An object to identify if a stream of ("busy") notes is an expanded trill.

    By default, does not consider Nachschlag trills, but setting checkNachschlag will consider.

    When optional stream of simpleNotes are provided, considers if busyNotes are
    an expansion of a trill which would be denoted on the first note in simpleNotes.
    '''
    def __init__(self, busyNotes, simpleNotes=None, checkNachschlag=False):
        super().__init__(busyNotes, simpleNotes)
        self.checkNachschlag = checkNachschlag
        self.acceptableInterval = 3
        self.minimumLengthForNachschlag = 5

    def calculateTrillNoteQuarterLength(self):
        '''
        Finds the quarter length value for each trill note
        assuming busy notes all are an expanded trill.

        Expanded trill total duration is time of all busy notes combined or
        duration of the first note in simpleNotes when provided.
        '''
        numTrillNotes = len(self.busyNotes)
        totalDurationQuarterLength = self.calculateTrillNoteTotalQuarterLength()
        return totalDurationQuarterLength / numTrillNotes

    def calculateTrillNoteTotalQuarterLength(self):
        '''
        Returns total length of trill assuming busy notes are all an expanded trill.
        This is either the time of all busy notes combined or
        duration of the first note in simpleNotes when provided.
        '''
        if self.simpleNotes:
            return self.simpleNotes[0].duration.quarterLength
        trillQl = 0
        for n in self.busyNotes:
            trillQl += n.duration.quarterLength
        return trillQl

    def recognize(self) -> Union[bool, expressions.Trill]:
        '''
        Tries to identify the busy notes as a trill.

        When simple notes is provided, tries to identify busy notes
        as the trill shortened by simple notes.
        Currently only supports one simple note in simple notes.

        Only when checkNachschlag is true, allows last few notes to break trill rules.

        Trill interval size is interval between busy notes.

        Returns: False if not possible or the Trill Expression
        '''
        busyNotes = self.busyNotes

        # Enough notes to trill
        if len(busyNotes) <= 2:
            return False

        # Oscillation pitches
        n1 = busyNotes[0]
        n2 = busyNotes[1]

        if not n1.isNote or not n2.isNote:
            return False

        if abs(n1.pitch.midi - n2.pitch.midi) > self.acceptableInterval:
            return False

        twoNoteOscillation = True
        i = 0
        for i in range(len(busyNotes)):
            noteConsidering = busyNotes[i]
            if not noteConsidering.isNote:
                return False
            if i % 2 == 0 and noteConsidering.pitch != n1.pitch:
                twoNoteOscillation = False
                break
            elif i % 2 != 0 and noteConsidering.pitch != n2.pitch:
                twoNoteOscillation = False
                break

        isNachschlag = False
        if twoNoteOscillation:
            pass
        elif not self.checkNachschlag:
            return False
        else:
            lengthOk = len(busyNotes) >= self.minimumLengthForNachschlag
            notTooMuchNachschlag = i >= len(busyNotes) / 2
            if lengthOk and notTooMuchNachschlag:
                isNachschlag = True
            else:
                return False

        # set up trill
        trill = expressions.Trill()
        trill.quarterLength = self.calculateTrillNoteQuarterLength()
        if isNachschlag:
            trill.nachschlag = True

        if not self.simpleNotes:
            trill.size = interval.Interval(noteStart=n1, noteEnd=n2)
            return trill

        # currently ignore other notes in simpleNotes
        simpleNote = self.simpleNotes[0]

        # enharmonic invariant checker
        if not(simpleNote.pitch.midi == n1.pitch.midi or simpleNote.pitch.midi == n2.pitch.midi):
            return False

        endNote = n2
        startNote = n1
        if simpleNote.pitch.midi == n2.pitch.midi:
            endNote = n1
            startNote = n2
        distance = interval.Interval(noteStart=startNote, noteEnd=endNote)
        trill.size = distance
        return trill

class TestCondition:
    def __init__(
        self, name, busyNotes, isTrill,
        simpleNotes=None, trillSize=None, isNachschlag=False
    ):
        self.name = name
        self.busyNotes = busyNotes
        self.isTrill = isTrill
        self.simpleNotes = simpleNotes
        self.trillSize = trillSize
        self.isNachschlag = isNachschlag

class Test(unittest.TestCase):
    def testRecognizeTrill(self):

        # set up experiment
        testConditions = []

        n1Duration = duration.Duration('quarter')
        t1NumNotes = 4
        t1UpInterval = interval.Interval('M2')
        t1DownInterval = interval.Interval('M-2')
        n1Lower = note.Note("G")
        n1Lower.duration = n1Duration
        n1Upper = note.Note("A")
        n1Upper.duration = n1Duration
        t1 = expressions.Trill()
        t1NoteDuration = calculateTrillNoteDuration(t1NumNotes, n1Duration)
        t1.quarterLength = t1NoteDuration
        t1Notes = t1.realize(n1Lower)[0]  # GAGA
        t1NotesWithRest = deepcopy(t1Notes)  # GA_A
        r1 = note.Rest()
        r1.duration = duration.Duration(t1NoteDuration)
        t1NotesWithRest[2] = r1
        testConditions.append(
            TestCondition(
                name="even whole step trill up without simple note",
                busyNotes=t1Notes,
                isTrill=True,
                trillSize=t1UpInterval)
        )
        testConditions.append(
            TestCondition(
                name="even whole step trill up from simple note",
                busyNotes=t1Notes,
                simpleNotes=[n1Lower],
                isTrill=True,
                trillSize=t1UpInterval)
        )
        testConditions.append(
            TestCondition(
                name="even whole step trill up to simple note",
                busyNotes=t1Notes,
                simpleNotes=[n1Upper],
                isTrill=True,
                trillSize=t1DownInterval)
        )
        testConditions.append(
            TestCondition(
                name="valid trill up to enharmonic simple note",
                busyNotes=t1Notes,
                simpleNotes=[note.Note("G##")],  # A
                isTrill=True,
                trillSize=t1DownInterval)
        )
        testConditions.append(
            TestCondition(
                name="valid trill but not with simple note",
                busyNotes=t1Notes,
                simpleNotes=[note.Note("E")],
                isTrill=False)
        )
        testConditions.append(
            TestCondition(
                name="invalid trill has rest inside",
                busyNotes=t1NotesWithRest,
                isTrill=False)
        )

        n2Duration = duration.Duration('half')
        t2NumNotes = 5
        t2UpInterval = interval.Interval('m2')
        t2DownInterval = interval.Interval('m-2')
        n2Lower = note.Note("G#")
        n2Lower.duration = n2Duration
        n2Upper = note.Note("A")
        n2Upper.duration = n2Duration
        t2NoteDuration = duration.Duration(calculateTrillNoteDuration(t2NumNotes, n2Duration))
        t2n1 = note.Note("A")  # trill2note1
        t2n1.duration = t2NoteDuration
        t2n2 = note.Note("G#")
        t2n2.duration = t2NoteDuration
        t2Notes = stream.Stream()  # A G# A G# A
        t2Notes.append([t2n1, t2n2, deepcopy(t2n1), deepcopy(t2n2), deepcopy(t2n1)])
        testConditions.append(
            TestCondition(
                name="odd half step trill down without simple note",
                busyNotes=t2Notes,
                isTrill=True,
                trillSize=t2DownInterval)
        )
        testConditions.append(
            TestCondition(
                name="odd half step trill down to simple note",
                busyNotes=t2Notes,
                simpleNotes=[n2Lower],
                isTrill=True,
                trillSize=t2UpInterval)
        )
        testConditions.append(
            TestCondition(
                name="odd trill down from simple note",
                busyNotes=t2Notes,
                simpleNotes=[n2Upper],
                isTrill=True,
                trillSize=t2DownInterval)
        )

        n3Duration = duration.Duration('quarter')
        t3NumNotes = 8
        t3UpInterval = interval.Interval('m2')
        t3DownInterval = interval.Interval('m-2')
        n3 = note.Note("B")
        n3.duration = n3Duration
        t3NoteDuration = duration.Duration(calculateTrillNoteDuration(t3NumNotes, n3Duration))
        t3n1 = note.Note("C5")
        t3n1.duration = t3NoteDuration
        t3n2 = note.Note("B")
        t3n2.duration = t3NoteDuration
        nachschlagN1 = note.Note("D5")
        nachschlagN1.duration = t3NoteDuration
        nachschlagN2 = note.Note("E5")
        nachschlagN2.duration = t3NoteDuration
        nachschlagN3 = note.Note("F5")
        nachschlagN3.duration = t3NoteDuration
        t3Notes = stream.Stream()  # CBCBCDEF
        t3Notes.append(
            [t3n1, t3n2, deepcopy(t3n1), deepcopy(t3n2), deepcopy(t3n1),
            nachschlagN1, nachschlagN2, nachschlagN3]
        )

        testConditions.append(
            TestCondition(
                name="Nachschlag trill when not checking for nachschlag",
                busyNotes=t3Notes,
                isTrill=False)
        )
        testConditions.append(
            TestCondition(
                name="Nachschlag trill when checking for nachschlag",
                busyNotes=t3Notes,
                isNachschlag=True,
                isTrill=True,
                trillSize=t3DownInterval)
        )
        testConditions.append(
            TestCondition(
                name="Nachschlag trill when checking for nachschlag up to simple note",
                busyNotes=t3Notes,
                simpleNotes=[n3],
                isNachschlag=True,
                isTrill=True,
                trillSize=t3UpInterval)
        )

        t4Duration = duration.Duration('eighth')
        t4n1 = note.Note("A")
        t4n1.duration = t4Duration
        t4n2 = note.Note("G")
        t4n2.duration = t4Duration
        testConditions.append(
            TestCondition(
                name="One note not a trill",
                busyNotes=[t4n1],
                isTrill=False)
        )
        testConditions.append(
            TestCondition(
                name="Two notes not a trill",
                busyNotes=[t4n1, t4n2],
                isTrill=False)
        )

        t5NoteDuration = duration.Duration("eighth")
        t5n1 = note.Note("A")  # trill2note1
        t5n1.duration = t5NoteDuration
        t5n2 = note.Note("C")
        t5n2.duration = t5NoteDuration
        t5Notes = stream.Stream()  # A C A C
        t5Notes.append([t5n1, t5n2, deepcopy(t5n1), deepcopy(t5n2)])
        testConditions.append(
            TestCondition(
                name="Too big of oscillating interval to be trill",
                busyNotes=t5Notes,
                isTrill=False)
        )

        t6NoteDuration = duration.Duration("eighth")
        t6n1 = note.Note("F")  # trill2note1
        t6n1.duration = t6NoteDuration
        t6n2 = note.Note("E")
        t6n2.duration = t6NoteDuration
        t6n3 = note.Note("G")
        t6n3.duration = t2NoteDuration
        t5Notes = stream.Stream()  # F E F G
        t5Notes.append([t6n1, t6n2, deepcopy(t6n1), t6n3])
        testConditions.append(
            TestCondition(
                name="Right interval but not oscillating between same notes",
                busyNotes=t5Notes,
                isTrill=False)
        )

        # run test
        for cond in testConditions:
            trillRecognizer = TrillRecognizer(cond.busyNotes)
            if cond.simpleNotes:
                trillRecognizer.simpleNotes = cond.simpleNotes
            if cond.isNachschlag:
                trillRecognizer.checkNachschlag = True

            trill = trillRecognizer.recognize()
            if cond.isTrill:
                self.assertIsInstance(trill, expressions.Trill, cond.name)
                # ensure trill is correct
                self.assertEqual(trill.nachschlag, cond.isNachschlag, cond.name)
                if cond.trillSize:
                    self.assertEqual(trill.size, cond.trillSize, cond.name)
            else:
                self.assertFalse(trill, cond.name)


def calculateTrillNoteDuration(numTrillNotes, totalDuration):
    return totalDuration.quarterLength / numTrillNotes


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
