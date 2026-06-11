# -----------------------------------------------------------------------------
# Name:         test_makeAccidentals_old.py
# Purpose:      differential tests pinning the deque-based makeAccidentals
#               to the pre-v10.5 list-walking implementation
#
# Authors:      Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2026 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
Differential tests that verify the per-step-deque
:class:`~music21.stream.makeNotation.AccidentalDisplayTracker` (v10.5)
against an oracle replicating the pre-v10.5 Stream.makeAccidentals loop,
which decided every pitch by calling
:meth:`~music21.pitch.Pitch.updateAccidentalDisplay` on ever-growing lists
of past pitches.

These tests exist to build trust in the rewrite; once the deque
implementation is fully trusted, this module can be deleted.  The
long-term behavioral tests for makeAccidentals live in
music21.stream.tests.

This module is entirely AI-assisted (Claude).
'''
from __future__ import annotations

import copy
import random
import unittest

from music21 import chord
from music21 import key
from music21 import note
from music21 import pitch
from music21 import tie
from music21.stream import Measure, Stream


class Test(unittest.TestCase):

    @staticmethod
    def oracleMakeAccidentals(
        s,
        *,
        pitchPast=None,
        pitchPastMeasure=None,
        alteredPitches=None,
        cautionaryPitchClass=True,
        cautionaryAll=False,
        overrideStatus=False,
        cautionaryNotImmediateRepeat=True,
        tiePitchSet=None,
        minimumPastMeasurePitches=4,
    ):
        '''
        A replica of the pre-v10.5 Stream.makeAccidentals loop, deciding
        every pitch with pitch.Pitch.updateAccidentalDisplay against
        explicit, ever-growing lists (with the v10.5 whole-measure context
        retention applied to those lists).  Used as an oracle to verify that
        the per-step-deque AccidentalDisplayTracker reaches identical
        decisions.
        '''
        if pitchPast is None:
            pitchPast = []
        if alteredPitches is None:
            alteredPitches = []
        if tiePitchSet is None:
            tiePitchSet = set()
        pastChunks = []
        if pitchPastMeasure:
            pastChunks.append(list(pitchPastMeasure))

        def flattenedPastChunks():
            flat = []
            for chunk in pastChunks:
                flat.extend(chunk)
            return flat

        pitchPastMeasureList = flattenedPastChunks()
        last_measure = None
        for e in s.recurse().notesAndRests:
            if e.activeSite is not None and e.activeSite.isMeasure:
                if last_measure is not None and e.activeSite is not last_measure:
                    pastChunks.append(pitchPast)
                    while (len(pastChunks) > 1
                            and sum(len(c) for c in pastChunks[1:])
                                >= minimumPastMeasurePitches):
                        pastChunks.pop(0)
                    pitchPastMeasureList = flattenedPastChunks()
                    pitchPast = []
                last_measure = e.activeSite
            if isinstance(e, note.Note):
                lastNoteWasTied = e.pitch.nameWithOctave in tiePitchSet
                e.pitch.updateAccidentalDisplay(
                    pitchPast=pitchPast,
                    pitchPastMeasure=pitchPastMeasureList,
                    alteredPitches=alteredPitches,
                    cautionaryPitchClass=cautionaryPitchClass,
                    cautionaryAll=cautionaryAll,
                    overrideStatus=overrideStatus,
                    cautionaryNotImmediateRepeat=cautionaryNotImmediateRepeat,
                    lastNoteWasTied=lastNoteWasTied)
                pitchPast.append(e.pitch)
                tiePitchSet.clear()
                if e.tie is not None and e.tie.type != 'stop':
                    tiePitchSet.add(e.pitch.nameWithOctave)
            elif isinstance(e, chord.Chord):
                seenPitchNames = set()
                for innerNote in list(e):
                    p = innerNote.pitch
                    lastNoteWasTied = p.nameWithOctave in tiePitchSet
                    p.updateAccidentalDisplay(
                        pitchPast=pitchPast,
                        pitchPastMeasure=pitchPastMeasureList,
                        otherSimultaneousPitches=[
                            other for other in e.pitches if other is not p],
                        alteredPitches=alteredPitches,
                        cautionaryPitchClass=cautionaryPitchClass,
                        cautionaryAll=cautionaryAll,
                        overrideStatus=overrideStatus,
                        cautionaryNotImmediateRepeat=cautionaryNotImmediateRepeat,
                        lastNoteWasTied=lastNoteWasTied)
                    if innerNote.tie is not None and innerNote.tie.type != 'stop':
                        seenPitchNames.add(p.nameWithOctave)
                tiePitchSet.clear()
                for pName in seenPitchNames:
                    tiePitchSet.add(pName)
                pitchPast += e.pitches
            else:
                tiePitchSet.clear()

    @staticmethod
    def randomAccidentalPitch(rng):
        '''
        A random pitch on a deliberately small gamut, so that step and
        octave collisions (the interesting cases) are frequent.
        '''
        p = pitch.Pitch(rng.choice(['C', 'D', 'E']))
        p.octave = rng.choice([3, 4, 4, 4, 5, None])
        accidentalName = rng.choice(
            [None, None, 'natural', 'sharp', 'flat', 'double-sharp'])
        if accidentalName is not None:
            acc = pitch.Accidental(accidentalName)
            displayType = rng.choice(
                [None, None, None, 'normal', 'always', 'never',
                 'unless-repeated', 'even-tied', 'if-absolutely-necessary'])
            if displayType is not None:
                acc.displayType = displayType
            acc.displayStatus = rng.choice(
                [None, None, None, None, None, None, True, False])
            p.accidental = acc
        return p

    def buildRandomAccidentalStream(self, rng):
        '''
        A Stream of Measures of random notes, rests, chords, and ties for
        differential testing of makeAccidentals.
        '''
        s = Stream()
        for _ in range(rng.randint(2, 5)):
            m = Measure()
            for _ in range(rng.randint(1, 12)):
                roll = rng.random()
                if roll < 0.1:
                    m.append(note.Rest())
                elif roll < 0.25:
                    c = chord.Chord(
                        [self.randomAccidentalPitch(rng)
                         for _ in range(rng.randint(2, 3))])
                    if rng.random() < 0.2:
                        c.tie = tie.Tie('start')
                    m.append(c)
                else:
                    n = note.Note()
                    n.pitch = self.randomAccidentalPitch(rng)
                    if rng.random() < 0.2:
                        n.tie = tie.Tie('start')
                    m.append(n)
            s.append(m)
        return s

    def testMakeAccidentalsDequeDifferential(self):
        '''
        makeAccidentals (deque-based since v10.5) must reach decisions
        identical to the historical loop over full pitch lists, which is
        replicated in oracleMakeAccidentals on top of the unchanged
        single-pitch API pitch.Pitch.updateAccidentalDisplay.
        '''
        rng = random.Random(20260609)
        for trial in range(150):
            sOrig = self.buildRandomAccidentalStream(rng)
            kwargs = {
                'cautionaryPitchClass': rng.random() < 0.7,
                'cautionaryAll': rng.random() < 0.15,
                'overrideStatus': rng.random() < 0.3,
                'cautionaryNotImmediateRepeat': rng.random() < 0.7,
                'minimumPastMeasurePitches': rng.choice([0, 2, 4, 9]),
            }
            if rng.random() < 0.5:
                alteredPitches = key.KeySignature(rng.randint(-3, 3)).alteredPitches
            else:
                alteredPitches = []
            if rng.random() < 0.3:
                initialPast = [self.randomAccidentalPitch(rng)
                               for _ in range(rng.randint(1, 4))]
                initialPastMeasure = [self.randomAccidentalPitch(rng)
                                      for _ in range(rng.randint(1, 4))]
            else:
                initialPast = None
                initialPastMeasure = None

            sNew = copy.deepcopy(sOrig)
            sOld = copy.deepcopy(sOrig)
            sNew.makeAccidentals(
                inPlace=True,
                useKeySignature=False,
                alteredPitches=alteredPitches[:],
                pitchPast=copy.deepcopy(initialPast),
                pitchPastMeasure=copy.deepcopy(initialPastMeasure),
                **kwargs)
            self.oracleMakeAccidentals(
                sOld,
                alteredPitches=alteredPitches[:],
                pitchPast=copy.deepcopy(initialPast),
                pitchPastMeasure=copy.deepcopy(initialPastMeasure),
                **kwargs)

            newPitches = [p for n in sNew.recurse().notes for p in n.pitches]
            oldPitches = [p for n in sOld.recurse().notes for p in n.pitches]
            self.assertEqual(len(newPitches), len(oldPitches))
            for idx, (pNew, pOld) in enumerate(zip(newPitches, oldPitches)):
                accNew = pNew.accidental
                accOld = pOld.accidental
                self.assertEqual(
                    (accNew.name if accNew else None,
                     accNew.displayStatus if accNew else None),
                    (accOld.name if accOld else None,
                     accOld.displayStatus if accOld else None),
                    f'trial={trial} idx={idx} pitch={pNew.nameWithOctave} '
                    + f'kwargs={kwargs} alteredPitches={alteredPitches}'
                )

    def testMakeAccidentalsDequeRepeatedNotes(self):
        '''
        Long runs of repeated notes exercise the tracker's run-collapsing;
        decisions must still match the historical loop.
        '''
        rng = random.Random(42)
        s = Stream()
        for _unused_m in range(2):
            m = Measure()
            for _unused_n in range(80):
                n = note.Note()
                if rng.random() < 0.85:
                    n.pitch = pitch.Pitch('C#4')
                else:
                    n.pitch = self.randomAccidentalPitch(rng)
                if rng.random() < 0.25:
                    n.tie = tie.Tie('start')
                m.append(n)
            s.append(m)
        sNew = copy.deepcopy(s)
        sOld = copy.deepcopy(s)
        sNew.makeAccidentals(inPlace=True, useKeySignature=False)
        self.oracleMakeAccidentals(sOld)
        for pNew, pOld in zip(
            [p for n in sNew.recurse().notes for p in n.pitches],
            [p for n in sOld.recurse().notes for p in n.pitches],
        ):
            accNew = pNew.accidental
            accOld = pOld.accidental
            self.assertEqual(
                (accNew.name if accNew else None,
                 accNew.displayStatus if accNew else None),
                (accOld.name if accOld else None,
                 accOld.displayStatus if accOld else None),
            )


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
