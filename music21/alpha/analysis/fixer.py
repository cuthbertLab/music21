# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         alpha/analysis/fixer.py
# Purpose:      Fixes two streams given a list of changes between them
#
# Authors:      Emily Zhang
#
# Copyright:    Copyright © 2016 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
import unittest
from copy import deepcopy
from typing import Optional, TypeVar

from music21.alpha.analysis import aligner
from music21.alpha.analysis import ornamentRecognizer

from music21 import duration
from music21 import expressions
from music21 import interval
from music21 import note
from music21 import pitch
from music21 import stream

# noinspection PyShadowingBuiltins
_T = TypeVar('_T')


class OMRMidiFixer:
    '''
    Base class for future fixers
    changes is a list of changes associated with the midiStream and omrStream,
    not a list of lists
    '''
    def __init__(self, changes, midiStream, omrStream):
        self.changes = changes
        self.midiStream = midiStream
        self.omrStream = omrStream

    def fix(self):
        pass

    def checkIfNoteInstance(self, midiRef, omrRef):
        if isinstance(midiRef, note.Note) and isinstance(omrRef, note.Note):
            return True
        return False

class DeleteFixer(OMRMidiFixer):
    '''
    The DeleteFixer was designed to fit the specifications of the OpenScore project.
    The goal of the OpenScore project is to open-source music with open source software
    (like music21!). OpenScore will use a combination of computer and human power
    to digitize classical music scores and put them in the public domain. One idea is
    that software can identify wrong recognized notes in a scanned score and mark or
    delete the entire measure that that note is in and pass it off to a human corrector to
    re-transcribe the entire measure. The DeleteFixer could be the computer power in
    this method of score correction that OpenScore is using.

    CAUTION: this does really weird things still.
    '''
    def fix(self):
        super().fix()
        for (midiRef, omrRef, op) in self.changes:
            if self.checkIfNoteInstance(midiRef, omrRef) is False:
                continue
            # if the are the same, don't bother to try changing it
            # 3 is the number of noChange Ops
            if isinstance(op, aligner.ChangeOps) and op == aligner.ChangeOps.NoChange:
                continue

            m = omrRef.getContextByClass(stream.Measure)
            self.omrStream.remove(m)

class EnharmonicFixer(OMRMidiFixer):
    '''
    Fixes incorrectly spelled enharmonics
    initialized with self.changes -- a list of tuples in this form:
    (MIDIReference, OMRReference, op)
    MIDIReference and OMRReference are actual note/rest/chord object in some stream
    op is a ChangeOp that relates the two references

    TEST 1, no changes in OMR stream

    >>> omrStream1 = stream.Stream()
    >>> midiStream1 = stream.Stream()

    >>> omrNote1 = note.Note('A#4')
    >>> omrNote2 = note.Note('A#4')
    >>> midiNote1 = note.Note('B-4')
    >>> midiNote2 = note.Note('B-4')

    >>> omrStream1.append([omrNote1, omrNote2])
    >>> midiStream1.append([midiNote1, midiNote2])
    >>> subOp = alpha.analysis.aligner.ChangeOps.Substitution

    >>> ct1 = (midiNote1, omrNote1, subOp)
    >>> ct2 = (midiNote2, omrNote2, subOp)
    >>> changes1 = [ct1, ct2]

    >>> fixer1 = alpha.analysis.fixer.EnharmonicFixer(changes1, None, None)
    >>> fixer1.fix()
    >>> omrStream1[0]
    <music21.note.Note A#>
    >>> omrStream1[1]
    <music21.note.Note A#>


    TEST 2, no changes in OMR stream

    >>> omrStream2 = stream.Stream()
    >>> midiStream2 = stream.Stream()

    >>> omr2Note1 = note.Note('A#4')
    >>> omr2Note2 = note.Note('A#4')
    >>> midi2Note1 = note.Note('A#4')
    >>> midi2Note2 = note.Note('A#4')

    >>> omrStream2.append([omr2Note1, omr2Note2])
    >>> midiStream2.append([midi2Note1, midi2Note2])
    >>> ncOp = alpha.analysis.aligner.ChangeOps.NoChange

    >>> ct2_1 = (midi2Note1, omr2Note1, ncOp)
    >>> ct2_2 = (midi2Note2, omr2Note2, ncOp)
    >>> changes2 = [ct2_1, ct2_2]

    >>> fixer2 = alpha.analysis.fixer.EnharmonicFixer(changes2, None, None)
    >>> fixer2.fix()
    >>> omrStream2[0]
    <music21.note.Note A#>
    >>> omrStream1[1]
    <music21.note.Note A#>


    TEST 3 (case 1)

    >>> midiNote3 = note.Note('A4')
    >>> omrNote3 = note.Note('An4')

    >>> subOp = alpha.analysis.aligner.ChangeOps.Substitution

    >>> ct3 = (midiNote3, omrNote3, subOp)
    >>> changes3 = [ct3]
    >>> omrNote3.pitch.accidental
    <accidental natural>
    >>> fixer3 = alpha.analysis.fixer.EnharmonicFixer(changes3, None, None)
    >>> fixer3.fix()
    >>> omrNote3.pitch.accidental


    TEST 4 (case 2-1) e.g MIDI = g#, ground truth = a-, OMR = an

    >>> midiNote4 = note.Note('G#4')
    >>> omrNote4 = note.Note('An4')

    >>> subOp = alpha.analysis.aligner.ChangeOps.Substitution

    >>> ct4 = (midiNote4, omrNote4, subOp)
    >>> changes4 = [ct4]
    >>> omrNote4.pitch.accidental
    <accidental natural>
    >>> fixer4 = alpha.analysis.fixer.EnharmonicFixer(changes4, None, None)
    >>> fixer4.fix()
    >>> omrNote4.pitch.accidental
    <accidental flat>


    TEST 5 (case 2-2) e.g midi = g-, gt = f#, omr = fn

    >>> midiNote5 = note.Note('G-4')
    >>> omrNote5 = note.Note('Fn4')

    >>> subOp = alpha.analysis.aligner.ChangeOps.Substitution

    >>> ct5 = (midiNote5, omrNote5, subOp)
    >>> changes5 = [ct5]
    >>> omrNote5.pitch.accidental
    <accidental natural>
    >>> fixer5 = alpha.analysis.fixer.EnharmonicFixer(changes5, None, None)
    >>> fixer5.fix()
    >>> omrNote5.pitch.accidental
    <accidental sharp>


    TEST 6.1 (case 3) e.g. midi = g#, gt = g#, omr = gn or omr = g-

    >>> midiNote6_1 = note.Note('G#4')
    >>> midiNote6_2 = note.Note('G#4')
    >>> omrNote6_1 = note.Note('Gn4')
    >>> omrNote6_2 = note.Note('G-4')

    >>> subOp6_1 = alpha.analysis.aligner.ChangeOps.Substitution
    >>> subOp6_2 = alpha.analysis.aligner.ChangeOps.Substitution
    >>> ct6_1 = (midiNote6_1, omrNote6_1, subOp6_1)
    >>> ct6_2 = (midiNote6_2, omrNote6_2, subOp6_2)
    >>> changes6 = [ct6_1, ct6_2]

    >>> omrNote6_1.pitch.accidental
    <accidental natural>
    >>> omrNote6_2.pitch.accidental
    <accidental flat>
    >>> fixer6 = alpha.analysis.fixer.EnharmonicFixer(changes6, None, None)
    >>> fixer6.fix()
    >>> omrNote6_1.pitch.accidental
    <accidental sharp>
    >>> omrNote6_2.pitch.accidental
    <accidental sharp>


    TEST 7 (case 4-1, 4-2) notes are on different step, off by an interval of 2:
    * 4-1: e.g. midi = g#, gt = a-, omr = a#
    * 4-2: e.g. midi = a-, gt = g#, omr = g-

    >>> midiNote7_1 = note.Note('G#4')
    >>> omrNote7_1 = note.Note('A#4')

    >>> midiNote7_2 = note.Note('A-4')
    >>> omrNote7_2 = note.Note('G-4')

    >>> subOp7_1 = alpha.analysis.aligner.ChangeOps.Substitution
    >>> subOp7_2 = alpha.analysis.aligner.ChangeOps.Substitution
    >>> ct7_1 = (midiNote7_1, omrNote7_1, subOp7_1)
    >>> ct7_2 = (midiNote7_2, omrNote7_2, subOp7_2)
    >>> changes7 = [ct7_1, ct7_2]

    >>> omrNote7_1.pitch.accidental
    <accidental sharp>
    >>> omrNote7_2.pitch.accidental
    <accidental flat>
    >>> fixer7 = alpha.analysis.fixer.EnharmonicFixer(changes7, None, None)
    >>> fixer7.fix()

    >>> omrNote7_1.pitch.step
    'A'
    >>> omrNote7_1.pitch.accidental
    <accidental flat>

    >>> omrNote7_2.pitch.step
    'G'
    >>> omrNote7_2.pitch.accidental
    <accidental sharp>
    '''
    def fix(self):
        super().fix()
        for (midiRef, omrRef, op) in self.changes:
            omrRef.style.color = 'black'
            # if they're not notes, don't bother with rest
            if self.checkIfNoteInstance(midiRef, omrRef) is False:
                continue
            # if the are the same, don't bother to try changing it
            # 3 is the number of noChange Ops
            if isinstance(op, aligner.ChangeOps) and op == aligner.ChangeOps.NoChange:
                continue

            # don't bother with notes with too big of an interval between them
            if self.intervalTooBig(midiRef, omrRef, setInt=5):
                continue
            # case 1: omr has extraneous natural sign in front of it, get rid of it
            if self.hasNatAcc(omrRef):
                if self.isEnharmonic(midiRef, omrRef):
                    omrRef.pitch.accidental = None
                else:
                    # case 2-1: midi note is sharp, omr note is one step higher and natural,
                    # should be a flat instead. e.g midi = g#, gt = a-, omr = an
                    # omr note has higher ps than midi-- on a higher
                    # line or space than midi note
                    if omrRef.pitch > midiRef.pitch:
                        if omrRef.pitch.transpose(interval.Interval(-1)
                                                  ).isEnharmonic(midiRef.pitch):
                            omrRef.pitch.accidental = pitch.Accidental('flat')
                    # case 2-2: midi note is flat, omr note is one step lower and natural,
                    # should be a flat instead. e.g midi = g-, gt = f#, omr = fn
                    # omr note has lower ps than midi-- on a higher line
                    # or space than midi note
                    elif omrRef.pitch < midiRef.pitch:
                        if omrRef.pitch.transpose(interval.Interval(1)
                                                  ).isEnharmonic(midiRef.pitch):
                            omrRef.pitch.accidental = pitch.Accidental('sharp')
            # case 3: notes are on same step, but omr got read wrong.
            # e.g. midi = g#, gt = g#, omr = gn or omr = g-
            elif self.hasSharpFlatAcc(omrRef) and self.stepEq(midiRef, omrRef):
                if self.hasAcc(omrRef):
                    omrRef.pitch.accidental = midiRef.pitch.accidental
                else:
                    omrRef.pitch.accidental = None

            elif self.hasSharpFlatAcc(omrRef) and self.stepNotEq(midiRef, omrRef):
                # case 4-1: notes are on different step, off by an interval of 2,
                # omr note is higher and sharp
                # e.g. midi = g#, gt = a-, omr = a#
                if omrRef.pitch > midiRef.pitch:
                    if omrRef.pitch.accidental == pitch.Accidental('sharp'):
                        if omrRef.pitch.transpose(interval.Interval(-2)
                                                  ).isEnharmonic(midiRef.pitch):
                            omrRef.pitch.accidental = pitch.Accidental('flat')
                # case 4-2: notes are on different step, off by an interval of 2,
                # omr note is lower and flat
                # e.g. midi = a-, gt = g#, omr = g-
                elif omrRef.pitch < midiRef.pitch:
                    if omrRef.pitch.accidental == pitch.Accidental('flat'):
                        if omrRef.pitch.transpose(interval.Interval(2)
                                                  ).isEnharmonic(midiRef.pitch):
                            omrRef.pitch.accidental = pitch.Accidental('sharp')
            # case 5: same step, MIDI has accidental,
            # omr was read wrong (e.g. key signature not parsed)
            # e.g. midi = b-, gt = b-, omr=
            elif (omrRef.pitch != midiRef.pitch
                    and self.hasSharpFlatAcc(midiRef)
                    and self.stepEq(midiRef, omrRef)):
                omrRef.pitch = midiRef.pitch


    def isEnharmonic(self, midiRef, omrRef):
        return midiRef.pitch.isEnharmonic(omrRef.pitch)

    def hasAcc(self, omrRef):
        return omrRef.pitch.accidental is not None

    def hasNatAcc(self, omrRef):
        return self.hasAcc(omrRef) and omrRef.pitch.accidental.name == 'natural'

    def hasSharpFlatAcc(self, omrRef):
        return self.hasAcc(omrRef) and omrRef.pitch.accidental.name != 'natural'

    def stepEq(self, midiRef, omrRef):
        return midiRef.step == omrRef.step

    def stepNotEq(self, midiRef, omrRef):
        return midiRef.step != omrRef.step

    def intervalTooBig(self, midiRef, omrRef, setInt=5):
        if interval.notesToChromatic(midiRef, omrRef).intervalClass > setInt:
            return True
        return False

class OrnamentFixer(OMRMidiFixer):
    '''
    Fixes missed ornaments in OMR using expanded ornaments in MIDI
    initialized with self.changes -- a list of tuples in this form:
    (MIDIReference, OMRReference, op)
    MIDIReference and OMRReference are actual note/rest/chord object in some stream
    op is a ChangeOp that relates the two references

    recognizers can be a single recognizer or list of recognizers,
    but self.recognizers is always a list.
    recognizers take in stream of busy notes and optional stream of simple note(s)
    and return False or an instance of the ornament recognized
    '''
    def __init__(self, changes, midiStream, omrStream, recognizers, markChangeColor='blue'):
        super().__init__(changes, midiStream, omrStream)
        if not isinstance(recognizers, list):
            self.recognizers = [recognizers]
        else:
            self.recognizers = recognizers
        self.markChangeColor = markChangeColor

    def findOrnament(self, busyNotes, simpleNotes) -> Optional[expressions.Ornament]:
        '''
        Finds an ornament in busyNotes based from simpleNote
        using provided recognizers.

        :param busyNotes: stream of notes
        :param simpleNotes: stream of notes

        Tries the recognizers in order, returning the result of the first
        one to successfully recognize an ornament.
        '''
        for r in self.recognizers:
            ornament = r.recognize(busyNotes, simpleNotes=simpleNotes)
            if ornament:
                return ornament
        return None

    def addOrnament(self,
                    selectedNote: 'music21.note.Note',
                    ornament: 'music21.expressions.Ornament',
                    *,
                    show=False) -> bool:
        '''
        Adds the ornament to the selectedNote when selectedNote has no ornaments already.

        * selectedNote: Note.note to add ornament to
        * ornament: Expressions.ornament to add to note
        * show: True when note should be colored blue

        Returns True if added successfully, or False if there was already an
        ornament on the note and it wasn't added.
        '''
        if not any(isinstance(e, expressions.Ornament) for e in selectedNote.expressions):
            selectedNote.expressions.append(ornament)
            if show:
                selectedNote.style.color = self.markChangeColor
            return True
        return False

    def fix(self: _T, *, show=False, inPlace=True) -> Optional[_T]:
        '''
        Corrects missed ornaments in omr stream according to mid stream
        :param show: Whether to show results
        :param inPlace: Whether to make changes to own omr stream or
        return a new OrnamentFixer with changes
        '''
        changes = self.changes
        sa = None
        omrNotesLabeledOrnament = []
        midiNotesAlreadyFixedForOrnament = []

        if not inPlace:
            omrStreamCopy = deepcopy(self.omrStream)
            midiStreamCopy = deepcopy(self.midiStream)
            sa = aligner.StreamAligner(sourceStream=omrStreamCopy, targetStream=midiStreamCopy)
            sa.align()
            changes = sa.changes

        for midiNoteRef, omrNoteRef, change in changes:
            # reasonable changes
            if change is aligner.ChangeOps.NoChange or change is aligner.ChangeOps.Deletion:
                continue

            # get relevant notes
            if omrNoteRef in omrNotesLabeledOrnament:
                continue
            busyNotes = getNotesWithinDuration(midiNoteRef, omrNoteRef.duration)
            busyNoteAlreadyUsed = False
            for busyNote in busyNotes:
                if busyNote in midiNotesAlreadyFixedForOrnament:
                    busyNoteAlreadyUsed = True
                    break
            if busyNoteAlreadyUsed:
                continue

            # try to recognize ornament
            ornamentFound = self.findOrnament(busyNotes, [deepcopy(omrNoteRef)])

            # mark ornament
            if ornamentFound:
                midiNotesAlreadyFixedForOrnament += busyNotes
                omrNotesLabeledOrnament.append(omrNoteRef)
                self.addOrnament(omrNoteRef, ornamentFound, show=show)

        if show:
            self.omrStream.show()
            self.midiStream.show()

        if not inPlace:
            return TrillFixer(sa.changes, sa.targetStream, sa.sourceStream)

def getNotesWithinDuration(startingGeneralNote, totalDuration, referenceStream=None):
    '''
    Returns maximal stream of deepcopies of notes, rests, and chords following
    (and including) startingNote which occupy no more than totalDuration combined.

    * startingGeneralNote is a GeneralNote (could be a note, rest, or chord)
    * totalDuration is a duration
    * referenceStream is optionally a stream which the startingGeneralNote's
        active site should be set to when provided
    '''
    if referenceStream:
        startingGeneralNote.activeSite = referenceStream

    notes = stream.Stream()

    # even startingNote is too long
    if startingGeneralNote.duration.quarterLength > totalDuration.quarterLength:
        return notes

    durationQlLeft = totalDuration.quarterLength - startingGeneralNote.duration.quarterLength
    nextGeneralNote = startingGeneralNote.next('GeneralNote', activeSiteOnly=True)
    notes.append(deepcopy(startingGeneralNote))

    while nextGeneralNote and durationQlLeft >= nextGeneralNote.duration.quarterLength:
        currentGeneralNote = nextGeneralNote
        nextGeneralNote = currentGeneralNote.next('GeneralNote', activeSiteOnly=True)

        durationQlLeft -= currentGeneralNote.duration.quarterLength
        notes.append(deepcopy(currentGeneralNote))

    return notes

class TrillFixer(OrnamentFixer):
    '''
    Fixes missed trills in OMR using expanded ornaments in MIDI.
    initialized with self.changes -- a list of tuples in this form:
    (MIDIReference, OMRReference, op)
    MIDIReference and OMRReference are actual note/rest/chord object in some stream
    op is a ChangeOp that relates the two references
    '''
    def __init__(self, changes, midiStream, omrStream):
        defaultOrnamentRecognizer = ornamentRecognizer.TrillRecognizer()
        nachschlagOrnamentRecognizer = ornamentRecognizer.TrillRecognizer()
        nachschlagOrnamentRecognizer.checkNachschlag = True
        recognizers = [defaultOrnamentRecognizer, nachschlagOrnamentRecognizer]
        super().__init__(changes, midiStream, omrStream, recognizers)

class TurnFixer(OrnamentFixer):
    '''
    Fixes missed turns/inverted turns in OMR using expanded ornaments in MIDI.
    initialized with self.changes -- a list of tuples in this form:
    (MIDIReference, OMRReference, op)
    MIDIReference and OMRReference are actual note/rest/chord object in some stream
    op is a ChangeOp that relates the two references
    '''
    def __init__(self, changes, midiStream, omrStream):
        recognizer = ornamentRecognizer.TurnRecognizer()
        super().__init__(changes, midiStream, omrStream, recognizer)

class Test(unittest.TestCase):
    def measuresEqual(self, m1, m2):
        '''
        Returns a tuple of (True/False, reason)

        Reason is '' if True
        '''
        if len(m1) != len(m2):
            msg = 'not equal length'
            return False, msg
        for i in range(len(m1)):
            if len(m1[i].expressions) != len(m2[i].expressions):
                msg = f'Expressions {i} unequal ({m1[i].expressions} != {m2[i].expressions})'
                return False, msg
            if m1[i] != m2[i]:
                msg = f'Elements {i} are unequal ({m1[i]} != {m2[i]})'
                return False, msg
        return True, ''

    def checkFixerHelper(self, testCase, testFixer):
        '''
        testCase is a dictionary with the following keys

        returnDict = {
            'name': string,
            'midi': measure stream,
            'omr': measure stream,
            'expected': fixed measure stream,
        }

        testFixer is an OMRMidiFixer
        '''
        omr = testCase['omr']
        midi = testCase['midi']
        expectedOmr = testCase['expected']
        testingName = testCase['name']

        # set up aligner
        sa = aligner.StreamAligner(sourceStream=omr, targetStream=midi)
        sa.align()
        omrCopy = deepcopy(omr)
        assertionCheck = 'Expect no changes from creating and aligning aligner.'
        self.assertTrue(self.measuresEqual(omrCopy, sa.sourceStream)[0], assertionCheck)

        # set up fixer
        fixer = testFixer(sa.changes, sa.targetStream, sa.sourceStream)
        assertionCheck = 'Expect no changes from creating fixer.'
        self.assertTrue(self.measuresEqual(omrCopy, sa.sourceStream)[0], assertionCheck)

        # test fixing not in place
        notInPlaceResult = fixer.fix(inPlace=False)

        assertionCheck = '. Expect no changes to aligner source stream, but unequal because '
        isEqual, reason = self.measuresEqual(omrCopy, sa.sourceStream)
        self.assertTrue(isEqual, testingName + assertionCheck + reason)

        assertionCheck = '. Expect no changes to fixer omr stream, but unequal because '
        isEqual, reason = self.measuresEqual(omrCopy, fixer.omrStream)
        self.assertTrue(isEqual, testingName + assertionCheck + reason)

        assertionCheck = '. Appropriate changes in new fixer, but unequal because '
        isEqual, reason = self.measuresEqual(notInPlaceResult.omrStream, expectedOmr)
        self.assertTrue(isEqual, testingName + assertionCheck + reason)

        # test fixing in place
        fixerInPlaceResult = fixer.fix(inPlace=True)
        self.assertIsNone(fixerInPlaceResult, testingName)

        assertionCheck = ". Expect changes in fixer's omr stream, but unequal because "
        isEqual, reason = self.measuresEqual(expectedOmr, fixer.omrStream)
        self.assertTrue(isEqual, testingName + assertionCheck + reason)

        assertionCheck = '. Expect changes in original omr stream, but unequal because '
        isEqual, reason = self.measuresEqual(expectedOmr, omr)
        self.assertTrue(isEqual, testingName + assertionCheck + reason)

    def testGetNotesWithinDuration(self):
        n1 = note.Note('C')
        n1.duration = duration.Duration('quarter')
        m1 = stream.Stream()
        m1.append(n1)

        result = getNotesWithinDuration(n1, duration.Duration('quarter'))
        self.assertIsInstance(result, stream.Stream)
        self.assertListEqual([n1], list(result.notes), 'starting note occupies full duration')

        result = getNotesWithinDuration(n1, duration.Duration('half'))
        self.assertListEqual([n1], list(result.notes), 'starting note occupies partial duration')

        result = getNotesWithinDuration(n1, duration.Duration('eighth'))
        self.assertListEqual([], list(result.notes), 'starting note too long')

        m2 = stream.Measure()
        n2 = note.Note('D')
        n2.duration = duration.Duration('eighth')
        n3 = note.Note('E')
        n3.duration = duration.Duration('eighth')
        m2.append([n1, n2, n3])

        result = getNotesWithinDuration(n1, duration.Duration('quarter'))
        self.assertListEqual([n1], list(result.notes), 'starting note occupies full duration')

        result = getNotesWithinDuration(n1, duration.Duration('half'))
        self.assertListEqual([n1, n2, n3], list(result.notes), 'all notes fill up full duration')

        result = getNotesWithinDuration(n1, duration.Duration('whole'))
        self.assertListEqual([n1, n2, n3], list(result.notes), 'all notes fill up partial duration')

        result = getNotesWithinDuration(n1, duration.Duration(1.5))
        self.assertListEqual([n1, n2], list(result.notes), 'some notes fill up full duration')

        result = getNotesWithinDuration(n1, duration.Duration(1.75))
        self.assertListEqual([n1, n2], list(result.notes), 'some notes fill up partial duration')

        # set active site from m2 to m1 (which runs out of notes to fill up)
        result = getNotesWithinDuration(n1, duration.Duration('half'), referenceStream=m1)
        self.assertListEqual([n1], list(result.notes), 'partial fill up from reference stream m1')

        m3 = stream.Measure()
        m3.id = 'm3'
        r1 = note.Rest()
        r1.duration = duration.Duration('quarter')
        m3.append([n1, r1])  # n1 active site now with m2
        result = getNotesWithinDuration(n1, duration.Duration('half'))
        msg = 'note and rest fill up full duration'
        self.assertListEqual([n1, r1], list(result.notesAndRests), msg)

        # set active site from m3 to m2
        result = getNotesWithinDuration(n1, duration.Duration('half'), referenceStream=m2)
        self.assertListEqual([n1, n2, n3], list(result.notes), 'fill up from reference stream m2')

    def testTrillFixer(self):
        def createDoubleTrillMeasure():
            '''
            Returns a dictionary with the following keys

            returnDict = {
                'name': string,
                'midi': measure stream,
                'omr': measure stream,
                'expected': measure stream,
            }
            '''
            noteDuration = duration.Duration('quarter')

            # GAGA Trill
            trill1NoteDuration = duration.Duration(.25)
            n0 = note.Note('G')
            n0.duration = noteDuration
            n1 = note.Note('G')
            n1.duration = trill1NoteDuration
            n2 = note.Note('A')
            n2.duration = trill1NoteDuration
            trill1 = [n1, n2, deepcopy(n1), deepcopy(n2)]  # G A G A

            # C B C B Trill
            trill2NoteDuration = duration.Duration(.0625)
            n3 = note.Note('B3')  # omr
            n3.duration = noteDuration
            n4 = note.Note('B3')
            n4.duration = trill2NoteDuration
            n5 = note.Note('C')
            n5.duration = trill2NoteDuration
            trill2 = [n5, n4, deepcopy(n5), deepcopy(n4),
                      deepcopy(n5), deepcopy(n4), deepcopy(n5), deepcopy(n4)]

            midiMeasure = stream.Measure()
            midiMeasure.append(trill1)
            midiMeasure.append(trill2)

            omrMeasure = stream.Measure()
            omrMeasure.append([n0, n3])

            expectedFixedOmrMeasure = stream.Measure()
            n0WithTrill = deepcopy(n0)
            n0Trill = expressions.Trill()
            n0Trill.size = interval.Interval('m-2')
            n0Trill.quarterLength = trill1NoteDuration.quarterLength
            n0WithTrill.expressions.append(n0Trill)
            n1WithTrill = deepcopy(n3)
            n1Trill = expressions.Trill()
            n1Trill.size = interval.Interval('M2')
            n1Trill.quarterLength = trill2NoteDuration.quarterLength
            n1WithTrill.expressions.append(n0Trill)
            expectedFixedOmrMeasure.append([n0WithTrill, n1WithTrill])

            returnDict = {
                'name': 'Double Trill Measure',
                'midi': midiMeasure,
                'omr': omrMeasure,
                'expected': expectedFixedOmrMeasure,
            }
            return returnDict

        def createWrongTrillMeasure():
            '''
            Returns a dictionary with the following keys

            returnDict = {
                'name': string,
                'midi': measure stream,
                'omr': measure stream,
                'expected': measure stream,
            }
            '''
            noteDuration = duration.Duration('quarter')

            n0 = note.Note('C')  # omr
            n0.duration = noteDuration
            n1 = note.Note('C')
            n1.duration = duration.Duration(.25)
            n2 = note.Note('A')
            n2.duration = duration.Duration(.25)

            nonTrill = [n1, n2, deepcopy(n1), deepcopy(n2)]

            midiMeasure = stream.Measure()
            midiMeasure.append(nonTrill)
            omrMeasure = stream.Measure()
            omrMeasure.append(n0)

            returnDict = {
                'name': 'Non-Trill Measure Wrong Oscillate Interval',
                'midi': midiMeasure,
                'omr': omrMeasure,
                'expected': deepcopy(omrMeasure),
            }
            return returnDict

        def createNonTrillMeasure():
            '''
            Returns a dictionary with the following keys

            returnDict = {
                'name': string,
                'midi': measure stream,
                'omr': measure stream,
                'expected': measure stream,
            }
            '''
            noteDuration = duration.Duration('quarter')

            n0 = note.Note('A')  # omr
            n0.duration = noteDuration
            n1 = note.Note('C')
            n1.duration = duration.Duration(.25)
            n2 = note.Note('D')
            n2.duration = duration.Duration(.25)

            nonTrill = [n1, n2, deepcopy(n1), deepcopy(n2)]

            midiMeasure = stream.Measure()
            midiMeasure.append(nonTrill)
            omrMeasure = stream.Measure()
            omrMeasure.append(n0)

            returnDict = {
                'name': 'Non-Trill Measure Wrong Notes',
                'midi': midiMeasure,
                'omr': omrMeasure,
                'expected': deepcopy(omrMeasure),
            }

            return returnDict

        def createNachschlagTrillMeasure():
            '''
            Returns a dictionary with the following keys

            returnDict = {
                'name': string,
                'midi': measure stream,
                'omr': measure stream,
                'expected': measure stream,
            }
            '''
            noteDuration = duration.Duration('quarter')
            trillDuration = duration.Duration(.125)

            n0 = note.Note('E')
            n0.duration = noteDuration

            tn1 = note.Note('E')
            tn1.duration = trillDuration
            tn2 = note.Note('F')
            tn2.duration = trillDuration
            tn3 = note.Note('D')
            tn3.duration = trillDuration
            firstHalfTrill = [tn1, tn2, deepcopy(tn1), deepcopy(tn2)]
            secondHalfTrill = [deepcopy(tn1), deepcopy(tn2), deepcopy(tn1), tn3]
            expandedTrill = firstHalfTrill + secondHalfTrill

            midiMeasure = stream.Measure()
            midiMeasure.append(expandedTrill)
            omrMeasure = stream.Measure()
            omrMeasure.append(n0)

            nachschlagTrill = expressions.Trill()
            nachschlagTrill.nachschlag = True
            nachschlagTrill.quarterLength = trillDuration.quarterLength
            expectedFixedOmrMeasure = stream.Measure()
            noteWithTrill = deepcopy(n0)
            noteWithTrill.expressions.append(deepcopy(nachschlagTrill))
            expectedFixedOmrMeasure.append(noteWithTrill)

            returnDict = {
                'name': 'Nachschlag Trill',
                'midi': midiMeasure,
                'omr': omrMeasure,
                'expected': expectedFixedOmrMeasure,
            }

            return returnDict

        def createMeasureWithTrillAlready():
            '''
            Returns a dictionary with the following keys

            returnDict = {
                'name': string,
                'midi': measure stream,
                'omr': measure stream,
                'expected': measure stream,
            }
            '''
            noteDuration = duration.Duration('quarter')
            trillDuration = duration.Duration(.125)

            noteWithTrill = note.Note('F')
            noteWithTrill.duration = noteDuration
            trill = expressions.Trill()
            trill.quarterLength = trillDuration.quarterLength
            noteWithTrill.expressions.append(trill)

            tn1 = note.Note('F')
            tn1.duration = trillDuration
            tn2 = note.Note('G')
            tn2.duration = trillDuration
            expandedTrill = [tn1, tn2, deepcopy(tn1), deepcopy(tn2)]

            midiMeasure = stream.Measure()
            midiMeasure.append(expandedTrill)
            omrMeasure = stream.Measure()
            omrMeasure.append(noteWithTrill)

            returnDict = {
                'name': 'OMR with Trill Notation',
                'midi': midiMeasure,
                'omr': omrMeasure,
                'expected': deepcopy(omrMeasure),
            }
            return returnDict

        testConditions = [
            createDoubleTrillMeasure(),
            createWrongTrillMeasure(),
            createNonTrillMeasure(),
            createNachschlagTrillMeasure(),
            createMeasureWithTrillAlready(),
        ]

        for testCase in testConditions:
            self.checkFixerHelper(testCase, TrillFixer)

    def testTurnFixer(self):
        def createSingleTurnMeasure():
            '''
            Returns a dictionary with the following keys

            returnDict = {
                'name': string,
                'midi': measure stream,
                'omr': measure stream,
                'expected': measure stream,
            }
            '''
            omrMeasure = stream.Measure()
            omrNote = note.Note('F')
            omrNote.duration = duration.Duration('whole')
            omrMeasure.append(omrNote)

            expectedFixedOmrMeasure = stream.Stream()
            expectedOmrNote = deepcopy(omrNote)
            expectedOmrNote.expressions.append(expressions.Turn())
            expectedFixedOmrMeasure.append(expectedOmrNote)

            midiMeasure = stream.Measure()
            turn = [note.Note('G'), note.Note('F'), note.Note('E'), note.Note('F')]
            midiMeasure.append(turn)

            returnDict = {
                'name': 'Single Turn Measure',
                'midi': midiMeasure,
                'omr': omrMeasure,
                'expected': expectedFixedOmrMeasure,
            }
            return returnDict

        def createDoubleInvertedTurnMeasure():
            '''
            Returns a dictionary with the following keys

            returnDict = {
                'name': string,
                'midi': measure stream,
                'omr': measure stream,
                'expected': measure stream,
            }
            '''
            omrMeasure = stream.Measure()
            omrNote1 = note.Note('B-')
            middleNote = note.Note('G')
            omrNote2 = note.Note('B-')  # enharmonic to trill
            omrMeasure.append([omrNote1, middleNote, omrNote2])


            expectedFixedOmrMeasure = stream.Stream()
            expectOmrNote1 = deepcopy(omrNote1)
            expectOmrNote1.expressions.append(expressions.InvertedTurn())
            expectOmrNote2 = deepcopy(omrNote2)
            expectOmrNote2.expressions.append(expressions.InvertedTurn())
            expectedFixedOmrMeasure.append([expectOmrNote1, deepcopy(middleNote), expectOmrNote2])

            midiMeasure = stream.Measure()
            turn1 = [note.Note('A'), note.Note('B-'), note.Note('C5'), note.Note('B-')]
            turn2 = [note.Note('G#'), note.Note('A#'), note.Note('B'), note.Note('A#')]
            for n in turn1:
                n.duration = duration.Duration(.25)
            for n in turn2:
                n.duration = duration.Duration(.25)
            midiMeasure.append([*turn1, deepcopy(middleNote), *turn2])

            returnDict = {
                'name': 'Inverted turns with accidentals separated By non-ornament Note',
                'midi': midiMeasure,
                'omr': omrMeasure,
                'expected': expectedFixedOmrMeasure,
            }
            return returnDict

        def createNonTurnMeasure():
            '''
            Returns a dictionary with the following keys

            returnDict = {
                'name': string,
                'midi': measure stream,
                'omr': measure stream,
                'expected': measure stream,
            }
            '''
            omrMeasure = stream.Measure()
            omrNote = note.Note('A')
            omrNote.duration = duration.Duration('whole')
            omrMeasure.append(omrNote)

            midiMeasure = stream.Measure()
            turn = [note.Note('B'), note.Note('A'), note.Note('G'), note.Note('F')]
            midiMeasure.append(turn)

            returnDict = {
                'name': 'Non-Turn Measure',
                'midi': midiMeasure,
                'omr': omrMeasure,
                'expected': deepcopy(omrMeasure),
            }
            return returnDict

        testConditions = [createSingleTurnMeasure(),
                          createDoubleInvertedTurnMeasure(),
                          createNonTurnMeasure()]

        for testCase in testConditions:
            self.checkFixerHelper(testCase, TurnFixer)


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
