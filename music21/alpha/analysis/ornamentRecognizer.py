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
    Busy notes refer to the expanded ornament notes.
    Simple note(s) refer to the base note of ornament which is often shown
    with the ornament marking on it.
    '''
    def calculateOrnamentNoteQl(self, busyNotes, simpleNotes=None):
        '''
        Finds the quarter length value for each ornament note
        assuming busy notes all are an expanded ornament.

        Expanded ornament total duration is time of all busy notes combined or
        duration of the first note in simpleNotes when provided.
        '''
        numOrnamentNotes = len(busyNotes)
        totalDurationQuarterLength = self.calculateOrnamentTotalQl(busyNotes, simpleNotes)
        return totalDurationQuarterLength / numOrnamentNotes

    def calculateOrnamentTotalQl(self, busyNotes, simpleNotes=None):
        '''
        Returns total length of trill assuming busy notes are all an expanded trill.
        This is either the time of all busy notes combined or
        duration of the first note in simpleNotes when provided.
        '''
        if simpleNotes:
            return simpleNotes[0].duration.quarterLength
        trillQl = 0
        for n in busyNotes:
            trillQl += n.duration.quarterLength
        return trillQl


class TrillRecognizer(OrnamentRecognizer):
    '''
    An object to identify if a stream of ("busy") notes is an expanded trill.

    By default, does not consider Nachschlag trills, but setting checkNachschlag will consider.

    When optional stream of simpleNotes are provided, considers if busyNotes are
    an expansion of a trill which would be denoted on the first note in simpleNotes.
    '''
    def __init__(self, checkNachschlag=False):
        self.checkNachschlag = checkNachschlag
        self.acceptableInterval = 3
        self.minimumLengthForNachschlag = 5

    def recognize(self, busyNotes, simpleNotes=None) -> Union[bool, expressions.Trill]:
        '''
        Tries to identify the busy notes as a trill.

        When simple notes is provided, tries to identify busy notes
        as the trill shortened by simple notes.
        Currently only supports one simple note in simple notes.

        Only when checkNachschlag is true, allows last few notes to break trill rules.

        Trill interval size is interval between busy notes.

        Returns: False if not possible or the Trill Expression
        '''
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
        trill.quarterLength = self.calculateOrnamentNoteQl(busyNotes, simpleNotes)
        if isNachschlag:
            trill.nachschlag = True

        if not simpleNotes:
            trill.size = interval.Interval(noteStart=n1, noteEnd=n2)
            return trill

        # currently ignore other notes in simpleNotes
        simpleNote = simpleNotes[0]

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

class TurnRecognizer(OrnamentRecognizer):
    def __init__(self, ):
        self.acceptableInterval = 3
        self.minimumLengthForNachschlag = 6
        self.acceptableIntervals = [
            interval.Interval('M2'), interval.Interval('M-2'),
            interval.Interval('m2'), interval.Interval('m-2'),
            interval.Interval('A2'), interval.Interval('A-2'),
        ]

    def isAcceptableInterval(self, intervalToCheck) -> bool:
        '''
        :param intervalToCheck: interval
        :return: whether that interval can occur in a turn
        '''
        return intervalToCheck in self.acceptableIntervals

    def recognize(
        self,
        busyNotes,
        simpleNotes=None,
    ) -> Union[bool, expressions.Turn, expressions.InvertedTurn]:
        '''
        Tries to identify the busy notes as a turn or inverted turn.

        When simple notes is provided, tries to identify busy notes
        as the turn shortened by simple notes.
        Currently only supports one simple note in simple notes.

        Turns and inverted turns have four notes separated by m2, M2, A2.

        Turns:
        start above base note
        go down to base note,
        go down again,
        and go back up to base note

        Inverted Turns:
        start below base note
        go up to base note,
        go up again,
        and go back down to base note

        When going up or down, must go to the adjacent note name,
        so A goes down to G, G#, G flat, G##, etc

        Returns: False if not possible or the Turn/Inverted Turn Expression
        '''
        # number of notes/ duration of notes ok
        if len(busyNotes) != 4:
            return False

        if simpleNotes:
            eps = 0.1
            totalBusyNotesDuration = 0
            for n in busyNotes:
                totalBusyNotesDuration += n.duration.quarterLength
            if abs(simpleNotes[0].duration.quarterLength - totalBusyNotesDuration) > eps:
                return False

        # pitches ok
        if busyNotes[1].pitch.midi != busyNotes[3].pitch.midi:
            return False
        if simpleNotes and simpleNotes[0].pitch.midi != busyNotes[1].pitch.midi:
            return False

        # intervals ok
        firstInterval = interval.Interval(noteStart=busyNotes[0], noteEnd=busyNotes[1])
        if not self.isAcceptableInterval(firstInterval):
            return False
        secondInterval = interval.Interval(noteStart=busyNotes[1], noteEnd=busyNotes[2])
        if not self.isAcceptableInterval(secondInterval):
            return False
        thirdInterval = interval.Interval(noteStart=busyNotes[2], noteEnd=busyNotes[3])
        if not self.isAcceptableInterval(thirdInterval):
            return False

        # goes in same direction
        if firstInterval.direction != secondInterval.direction:
            return False
        # and then in opposite direction
        if secondInterval.direction == thirdInterval.direction:
            return False

        # decide direction of turn to return
        if firstInterval.direction == interval.Interval('M-2').direction:  # down
            turn = expressions.Turn()
        else:
            turn = expressions.InvertedTurn()
        turn.quarterLength = self.calculateOrnamentNoteQl(busyNotes, simpleNotes)
        return turn

class _TestCondition:
    def __init__(
        self, name, busyNotes, isOrnament,
        simpleNotes=None, ornamentSize=None, isNachschlag=False, isInverted=False
    ):
        self.name = name
        self.busyNotes = busyNotes
        self.isOrnament = isOrnament
        self.simpleNotes = simpleNotes
        self.ornamentSize = ornamentSize
        self.isNachschlag = isNachschlag
        self.isInverted = isInverted

class Test(unittest.TestCase):
    def testRecognizeTurn(self):
        # set up experiment
        testConditions = []

        n1 = note.Note('F#')
        n1Enharmonic = note.Note('G-')
        noteInTurnNotBase = note.Note('G')
        noteNotInTurn = note.Note('A')

        evenTurn = [note.Note('G'), note.Note('F#'), note.Note('E'), note.Note('F#')]
        for n in evenTurn:
            n.duration.quarterLength = n1.duration.quarterLength / len(evenTurn)

        delayedTurn = [note.Note('G'), note.Note('F#'), note.Note('E'), note.Note('F#')]
        delayedTurn[0].duration.quarterLength = 2 * n1.duration.quarterLength / len(delayedTurn)
        for i in range(1, len(delayedTurn)):
            smallerDuration = n1.duration.quarterLength / (2 * len(delayedTurn))
            delayedTurn[i].duration.quarterLength = smallerDuration

        rubatoTurn = [note.Note('G'), note.Note('F#'), note.Note('E'), note.Note('F#')]
        # durations all different, add up to 1
        rubatoTurn[0].duration.quarterLength = .25
        rubatoTurn[1].duration.quarterLength = .15
        rubatoTurn[2].duration.quarterLength = .2
        rubatoTurn[3].duration.quarterLength = .4

        invertedTurn = [note.Note('E'), note.Note('F#'), note.Note('G'), note.Note('F#')]
        for n in invertedTurn:
            n.duration.quarterLength = n1.duration.quarterLength / len(invertedTurn)

        testConditions.append(
            _TestCondition(
                name='even turn no simple note',
                busyNotes=evenTurn,
                isOrnament=True)
        )
        testConditions.append(
            _TestCondition(
                name='even turn with simple note',
                busyNotes=evenTurn,
                simpleNotes=[n1],
                isOrnament=True)
        )
        testConditions.append(
            _TestCondition(
                name='even turn with enharmonic simple note',
                busyNotes=evenTurn,
                simpleNotes=[n1Enharmonic],
                isOrnament=True)
        )
        testConditions.append(
            _TestCondition(
                name='even turn with wrong simple note still in turn',
                busyNotes=evenTurn,
                simpleNotes=[noteInTurnNotBase],
                isOrnament=False)
        )
        testConditions.append(
            _TestCondition(
                name='even turn with wrong simple note not in turn',
                busyNotes=evenTurn,
                simpleNotes=[noteNotInTurn],
                isOrnament=False)
        )
        testConditions.append(
            _TestCondition(
                name='rubato turn with all notes different length',
                busyNotes=rubatoTurn,
                isOrnament=True)
        )
        testConditions.append(
            _TestCondition(
                name='delayed turn',
                busyNotes=delayedTurn,
                isOrnament=True)
        )
        testConditions.append(
            _TestCondition(
                name='inverted turn',
                busyNotes=invertedTurn,
                isInverted=True,
                isOrnament=True)
        )
        testConditions.append(
            _TestCondition(
                name='one wrong note',
                busyNotes=[note.Note('G'), note.Note('F#'), note.Note('E'), note.Note('D')],
                isOrnament=False)
        )
        testConditions.append(
            _TestCondition(
                name='non-adjacent note jump',
                busyNotes=[note.Note('E'), note.Note('G'), note.Note('A'), note.Note('G')],
                isOrnament=False)
        )
        testConditions.append(
            _TestCondition(
                name='trill is not a turn',
                busyNotes=[note.Note('G'), note.Note('F#'), note.Note('G'), note.Note('F#')],
                isOrnament=False)
        )
        testConditions.append(
            _TestCondition(
                name='too many notes for turn',
                busyNotes=[note.Note('G'), note.Note('F#'), note.Note('E'), note.Note('F#'),
                           note.Note('E')],
                isOrnament=False)
        )
        testConditions.append(
            _TestCondition(
                name='too few notes for turn',
                busyNotes=[note.Note('G'), note.Note('F#'), note.Note('E')],
                isOrnament=False)
        )
        testConditions.append(
            _TestCondition(
                name='total turn notes length longer than simple note',
                busyNotes=[note.Note('G'), note.Note('F#'), note.Note('E'), note.Note('F#')],
                simpleNotes=[n1],
                isOrnament=False)
        )

        # run test
        for cond in testConditions:
            turnRecognizer = TurnRecognizer()
            if cond.simpleNotes:
                turn = turnRecognizer.recognize(cond.busyNotes, simpleNotes=cond.simpleNotes)
            else:
                turn = turnRecognizer.recognize(cond.busyNotes)

            if cond.isOrnament:
                if cond.isInverted:
                    self.assertIsInstance(turn, expressions.InvertedTurn, cond.name)
                else:
                    self.assertIsInstance(turn, expressions.Turn, cond.name)
            else:
                self.assertFalse(turn, cond.name)

    def testRecognizeTrill(self):
        # set up the experiment
        testConditions = []

        n1Duration = duration.Duration('quarter')
        t1NumNotes = 4
        t1UpInterval = interval.Interval('M2')
        t1DownInterval = interval.Interval('M-2')
        n1Lower = note.Note('G')
        n1Lower.duration = n1Duration
        n1Upper = note.Note('A')
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
            _TestCondition(
                name='even whole step trill up without simple note',
                busyNotes=t1Notes,
                isOrnament=True,
                ornamentSize=t1UpInterval)
        )
        testConditions.append(
            _TestCondition(
                name='even whole step trill up from simple note',
                busyNotes=t1Notes,
                simpleNotes=[n1Lower],
                isOrnament=True,
                ornamentSize=t1UpInterval)
        )
        testConditions.append(
            _TestCondition(
                name='even whole step trill up to simple note',
                busyNotes=t1Notes,
                simpleNotes=[n1Upper],
                isOrnament=True,
                ornamentSize=t1DownInterval)
        )
        testConditions.append(
            _TestCondition(
                name='valid trill up to enharmonic simple note',
                busyNotes=t1Notes,
                simpleNotes=[note.Note('G##')],  # A
                isOrnament=True,
                ornamentSize=t1DownInterval)
        )
        testConditions.append(
            _TestCondition(
                name='valid trill but not with simple note',
                busyNotes=t1Notes,
                simpleNotes=[note.Note('E')],
                isOrnament=False)
        )
        testConditions.append(
            _TestCondition(
                name='invalid trill has rest inside',
                busyNotes=t1NotesWithRest,
                isOrnament=False)
        )

        n2Duration = duration.Duration('half')
        t2NumNotes = 5
        t2UpInterval = interval.Interval('m2')
        t2DownInterval = interval.Interval('m-2')
        n2Lower = note.Note('G#')
        n2Lower.duration = n2Duration
        n2Upper = note.Note('A')
        n2Upper.duration = n2Duration
        t2NoteDuration = duration.Duration(calculateTrillNoteDuration(t2NumNotes, n2Duration))
        t2n1 = note.Note('A')  # trill2note1
        t2n1.duration = t2NoteDuration
        t2n2 = note.Note('G#')
        t2n2.duration = t2NoteDuration
        t2Notes = stream.Stream()  # A G# A G# A
        t2Notes.append([t2n1, t2n2, deepcopy(t2n1), deepcopy(t2n2), deepcopy(t2n1)])
        testConditions.append(
            _TestCondition(
                name='odd half step trill down without simple note',
                busyNotes=t2Notes,
                isOrnament=True,
                ornamentSize=t2DownInterval)
        )
        testConditions.append(
            _TestCondition(
                name='odd half step trill down to simple note',
                busyNotes=t2Notes,
                simpleNotes=[n2Lower],
                isOrnament=True,
                ornamentSize=t2UpInterval)
        )
        testConditions.append(
            _TestCondition(
                name='odd trill down from simple note',
                busyNotes=t2Notes,
                simpleNotes=[n2Upper],
                isOrnament=True,
                ornamentSize=t2DownInterval)
        )

        n3Duration = duration.Duration('quarter')
        t3NumNotes = 8
        t3UpInterval = interval.Interval('m2')
        t3DownInterval = interval.Interval('m-2')
        n3 = note.Note('B')
        n3.duration = n3Duration
        t3NoteDuration = duration.Duration(calculateTrillNoteDuration(t3NumNotes, n3Duration))
        t3n1 = note.Note('C5')
        t3n1.duration = t3NoteDuration
        t3n2 = note.Note('B')
        t3n2.duration = t3NoteDuration
        nachschlagN1 = note.Note('D5')
        nachschlagN1.duration = t3NoteDuration
        nachschlagN2 = note.Note('E5')
        nachschlagN2.duration = t3NoteDuration
        nachschlagN3 = note.Note('F5')
        nachschlagN3.duration = t3NoteDuration
        t3Notes = stream.Stream()  # CBCBCDEF
        t3Notes.append(
            [t3n1, t3n2, deepcopy(t3n1), deepcopy(t3n2), deepcopy(t3n1),
            nachschlagN1, nachschlagN2, nachschlagN3]
        )

        testConditions.append(
            _TestCondition(
                name='Nachschlag trill when not checking for nachschlag',
                busyNotes=t3Notes,
                isOrnament=False)
        )
        testConditions.append(
            _TestCondition(
                name='Nachschlag trill when checking for nachschlag',
                busyNotes=t3Notes,
                isNachschlag=True,
                isOrnament=True,
                ornamentSize=t3DownInterval)
        )
        testConditions.append(
            _TestCondition(
                name='Nachschlag trill when checking for nachschlag up to simple note',
                busyNotes=t3Notes,
                simpleNotes=[n3],
                isNachschlag=True,
                isOrnament=True,
                ornamentSize=t3UpInterval)
        )

        t4Duration = duration.Duration('eighth')
        t4n1 = note.Note('A')
        t4n1.duration = t4Duration
        t4n2 = note.Note('G')
        t4n2.duration = t4Duration
        testConditions.append(
            _TestCondition(
                name='One note not a trill',
                busyNotes=[t4n1],
                isOrnament=False)
        )
        testConditions.append(
            _TestCondition(
                name='Two notes not a trill',
                busyNotes=[t4n1, t4n2],
                isOrnament=False)
        )

        t5NoteDuration = duration.Duration('eighth')
        t5n1 = note.Note('A')  # trill2note1
        t5n1.duration = t5NoteDuration
        t5n2 = note.Note('C')
        t5n2.duration = t5NoteDuration
        t5Notes = stream.Stream()  # A C A C
        t5Notes.append([t5n1, t5n2, deepcopy(t5n1), deepcopy(t5n2)])
        testConditions.append(
            _TestCondition(
                name='Too big of oscillating interval to be trill',
                busyNotes=t5Notes,
                isOrnament=False)
        )

        t6NoteDuration = duration.Duration('eighth')
        t6n1 = note.Note('F')  # trill2note1
        t6n1.duration = t6NoteDuration
        t6n2 = note.Note('E')
        t6n2.duration = t6NoteDuration
        t6n3 = note.Note('G')
        t6n3.duration = t2NoteDuration
        t5Notes = stream.Stream()  # F E F G
        t5Notes.append([t6n1, t6n2, deepcopy(t6n1), t6n3])
        testConditions.append(
            _TestCondition(
                name='Right interval but not oscillating between same notes',
                busyNotes=t5Notes,
                isOrnament=False)
        )

        # run test
        for cond in testConditions:
            trillRecognizer = TrillRecognizer()
            if cond.isNachschlag:
                trillRecognizer.checkNachschlag = True

            if cond.simpleNotes:
                trill = trillRecognizer.recognize(cond.busyNotes, simpleNotes=cond.simpleNotes)
            else:
                trill = trillRecognizer.recognize(cond.busyNotes)

            if cond.isOrnament:
                self.assertIsInstance(trill, expressions.Trill, cond.name)
                # ensure trill is correct
                self.assertEqual(trill.nachschlag, cond.isNachschlag, cond.name)
                if cond.ornamentSize:
                    self.assertEqual(trill.size, cond.ornamentSize, cond.name)
            else:
                self.assertFalse(trill, cond.name)


def calculateTrillNoteDuration(numTrillNotes, totalDuration):
    return totalDuration.quarterLength / numTrillNotes


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
