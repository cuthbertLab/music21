
from __future__ import annotations

import unittest

from music21 import chord
from music21 import clef
from music21 import expressions
from music21 import interval
from music21 import key
from music21 import meter
from music21.musicxml import m21ToXml
from music21 import note
from music21 import pitch
from music21 import stream


class Test(unittest.TestCase):

    def testRealize(self):
        n1 = note.Note('D4')
        n1.quarterLength = 4
        n1.expressions.append(expressions.WholeStepMordent())
        expList = expressions.realizeOrnaments(n1)
        st1 = stream.Stream()
        st1.append(expList)
        st1n = st1.notes
        self.assertEqual(st1n[0].name, 'D')
        self.assertEqual(st1n[0].quarterLength, 0.125)
        self.assertEqual(st1n[1].name, 'C')
        self.assertEqual(st1n[1].quarterLength, 0.125)
        self.assertEqual(st1n[2].name, 'D')
        self.assertEqual(st1n[2].quarterLength, 3.75)

    def testGetRepeatExpression(self):
        te = expressions.TextExpression('lightly')
        # no repeat expression is possible
        self.assertEqual(te.getRepeatExpression(), None)

        te = expressions.TextExpression('d.c.')
        self.assertEqual(str(te.getRepeatExpression()),
                         "<music21.repeat.DaCapo 'd.c.'>")
        re = te.getRepeatExpression()
        self.assertEqual(re.getTextExpression().content, 'd.c.')

        te = expressions.TextExpression('DC al coda')
        self.assertEqual(str(te.getRepeatExpression()),
                         "<music21.repeat.DaCapoAlCoda 'DC al coda'>")
        re = te.getRepeatExpression()
        self.assertEqual(re.getTextExpression().content, 'DC al coda')

        te = expressions.TextExpression('DC al fine')
        self.assertEqual(str(te.getRepeatExpression()),
                         "<music21.repeat.DaCapoAlFine 'DC al fine'>")
        re = te.getRepeatExpression()
        self.assertEqual(re.getTextExpression().content, 'DC al fine')

        te = expressions.TextExpression('ds al coda')
        self.assertEqual(str(te.getRepeatExpression()),
                         "<music21.repeat.DalSegnoAlCoda 'ds al coda'>")
        re = te.getRepeatExpression()
        self.assertEqual(re.getTextExpression().content, 'ds al coda')

        te = expressions.TextExpression('d.s. al fine')
        self.assertEqual(str(te.getRepeatExpression()),
                         "<music21.repeat.DalSegnoAlFine 'd.s. al fine'>")
        re = te.getRepeatExpression()
        self.assertEqual(re.getTextExpression().content, 'd.s. al fine')

    def testExpandTurns(self):
        # n1 is a half-note with a delayed turn
        # n1 is a dotted-quarter-note with a non-delayed inverted turn
        p1 = stream.Part()
        m1 = stream.Measure()
        m2 = stream.Measure()
        p1.append(clef.TrebleClef())
        p1.append(key.Key('F', 'major'))
        p1.append(meter.TimeSignature('2/4'))
        n1 = note.Note('C5', type='half')
        turn0 = expressions.Turn(delay=1.)  # delay is a quarter-note
        n1.expressions.append(turn0)
        n2 = note.Note('B4', type='quarter')
        n2.duration.dots = 1

        n2.expressions.append(expressions.InvertedTurn())
        m1.append(n1)
        m2.append(key.KeySignature(5))
        m2.append(n2)
        m2.append(note.Rest('eighth'))
        p1.append(m1)
        p1.append(m2)
        realized1 = expressions.realizeOrnaments(n1)
        realized2 = expressions.realizeOrnaments(n2)
        self.assertEqual('C5 D5 C5 B-4 C5', ' '.join(n.pitch.nameWithOctave for n in realized1))
        self.assertEqual('A#4 B4 C#5 B4', ' '.join(n.pitch.nameWithOctave for n in realized2))

        # total length of realized1 is half-note (ql=2.0): quarter note (half the original note)
        # followed by 4 turn notes that together add up to the other quarter note.
        self.assertEqual(realized1[0].quarterLength, 1.0)
        self.assertEqual(realized1[1].quarterLength, 0.25)
        self.assertEqual(realized1[2].quarterLength, 0.25)
        self.assertEqual(realized1[3].quarterLength, 0.25)
        self.assertEqual(realized1[4].quarterLength, 0.25)

        # Because turn0.quarterLength defaults to 0.25 (16th-note), the first three turn
        # notes are ql=0.25, and the fourth turn note has the remaining duration (0.75)
        self.assertEqual(realized2[0].quarterLength, 0.25)
        self.assertEqual(realized2[1].quarterLength, 0.25)
        self.assertEqual(realized2[2].quarterLength, 0.25)
        self.assertEqual(realized2[3].quarterLength, 0.75)

        # Here, delay is still a quarter-note (delay=1.0), the first three turn notes
        # are ql=0.125 (because turn0.quarterLength has been set to 0.125), and the
        # fourth turn note has the remaining duration (0.625)
        turn0.quarterLength = 0.125
        realized1b = expressions.realizeOrnaments(n1)
        self.assertEqual(realized1b[0].quarterLength, 1.0)
        self.assertEqual(realized1b[1].quarterLength, 0.125)
        self.assertEqual(realized1b[2].quarterLength, 0.125)
        self.assertEqual(realized1b[3].quarterLength, 0.125)
        self.assertEqual(realized1b[4].quarterLength, 0.625)


    def testExpandTrills(self):
        p1 = stream.Part()
        m1 = stream.Measure()
        p1.append(clef.TrebleClef())
        p1.append(key.Key('D', 'major'))
        p1.append(meter.TimeSignature('1/4'))
        n1 = note.Note('E4', type='eighth')
        n1.expressions.append(expressions.Trill())
        m1.append(n1)
        p1.append(m1)
        realized = expressions.realizeOrnaments(n1)
        self.assertIsInstance(realized, list)
        self.assertEqual(len(realized), 4)
        self.assertIsInstance(realized[0], note.Note)
        self.assertEqual(realized[0].quarterLength, 0.125)
        self.assertEqual('E4 F#4 E4 F#4', ' '.join(n.pitch.nameWithOctave for n in realized))


    def testTrillExtensionA(self):
        '''
        Test basic wave line creation and output, as well as passing
        objects through make measure calls.
        '''
        s = stream.Stream()
        s.repeatAppend(note.Note(), 12)
        n1 = s.notes[0]
        n2 = s.notes[-1]
        sp1 = expressions.TrillExtension(n1, n2)
        s.append(sp1)
        raw = m21ToXml.GeneralObjectExporter().parse(s)
        self.assertEqual(raw.count(b'wavy-line'), 2)

        s = stream.Stream()
        s.repeatAppend(chord.Chord(['c-3', 'g4']), 12)
        n1 = s.notes[0]
        n2 = s.notes[-1]
        sp1 = expressions.TrillExtension(n1, n2)
        s.append(sp1)
        raw = m21ToXml.GeneralObjectExporter().parse(s)
        # s.show()
        self.assertEqual(raw.count(b'wavy-line'), 2)

    def testFixedSizeOrnamentAccidental(self):
        # Check that accidental works as expected (i.e. not at all) on all the
        # old-style fixed-size Trill/Mordent types.

        # init with accidental raises ExpressionException
        flatAccid = pitch.Accidental('flat')
        with self.assertRaises(expressions.ExpressionException):
            trill = expressions.HalfStepTrill(accidental=flatAccid)
        with self.assertRaises(expressions.ExpressionException):
            trill = expressions.WholeStepTrill(accidental=flatAccid)
        with self.assertRaises(expressions.ExpressionException):
            mord = expressions.HalfStepMordent(accidental=flatAccid)
        with self.assertRaises(expressions.ExpressionException):
            mord = expressions.WholeStepMordent(accidental=flatAccid)
        with self.assertRaises(expressions.ExpressionException):
            mord = expressions.HalfStepInvertedMordent(accidental=flatAccid)
        with self.assertRaises(expressions.ExpressionException):
            mord = expressions.WholeStepInvertedMordent(accidental=flatAccid)

        # get accidental returns None, set accidental raises ExpressionException
        sharpAccid = pitch.Accidental('sharp')
        trill = expressions.HalfStepTrill()
        self.assertIsNone(trill.accidental)
        with self.assertRaises(expressions.ExpressionException):
            trill.accidental = sharpAccid
        trill = expressions.WholeStepTrill()
        self.assertIsNone(trill.accidental)
        with self.assertRaises(expressions.ExpressionException):
            trill.accidental = sharpAccid
        mord = expressions.HalfStepMordent()
        self.assertIsNone(mord.accidental)
        with self.assertRaises(expressions.ExpressionException):
            mord.accidental = sharpAccid
        mord = expressions.WholeStepMordent()
        self.assertIsNone(mord.accidental)
        with self.assertRaises(expressions.ExpressionException):
            mord.accidental = sharpAccid
        mord = expressions.HalfStepInvertedMordent()
        self.assertIsNone(mord.accidental)
        with self.assertRaises(expressions.ExpressionException):
            mord.accidental = sharpAccid
        mord = expressions.WholeStepInvertedMordent()
        self.assertIsNone(mord.accidental)
        with self.assertRaises(expressions.ExpressionException):
            mord.accidental = sharpAccid

    def testResolveOrnamentalPitches(self):
        # with no accidental, no key, explicit octave
        trill = expressions.Trill()
        itrill = expressions.InvertedTrill()

        noteWithExplicitOctave = note.Note('C4')
        trill.resolveOrnamentalPitches(noteWithExplicitOctave)
        self.assertEqual(trill.ornamentalPitches, (pitch.Pitch('D4'),))
        self.assertIsNone(trill.ornamentalPitches[0].accidental)
        itrill.resolveOrnamentalPitches(noteWithExplicitOctave)
        self.assertEqual(itrill.ornamentalPitches, (pitch.Pitch('B3'),))
        self.assertIsNone(itrill.ornamentalPitches[0].accidental)

        # with no accidental, no key, implicit octave
        noteWithImplicitOctave = note.Note('C')
        trill.resolveOrnamentalPitches(noteWithImplicitOctave)
        self.assertEqual(trill.ornamentalPitches, (pitch.Pitch('D4'),))
        self.assertIsNone(trill.ornamentalPitches[0].accidental)
        itrill.resolveOrnamentalPitches(noteWithImplicitOctave)
        self.assertEqual(itrill.ornamentalPitches, (pitch.Pitch('B3'),))
        self.assertIsNone(itrill.ornamentalPitches[0].accidental)

        # with accidental=naturalAccid, no key, explicit octave
        naturalAccid = pitch.Accidental(0)
        naturalAccid.displayStatus = True
        trill.accidental = naturalAccid
        itrill.accidental = naturalAccid
        trill.resolveOrnamentalPitches(noteWithExplicitOctave)
        expectedPitch = pitch.Pitch('D4')
        expectedPitch.accidental = pitch.Accidental('natural')
        self.assertEqual(trill.ornamentalPitches, (expectedPitch,))
        self.assertEqual(
            trill.ornamentalPitches[0].accidental.name,
            'natural'
        )
        self.assertEqual(
            trill.ornamentalPitches[0].accidental.displayStatus,
            True
        )
        itrill.resolveOrnamentalPitches(noteWithImplicitOctave)
        expectedPitch = pitch.Pitch('B3')
        expectedPitch.accidental = pitch.Accidental('natural')
        self.assertEqual(itrill.ornamentalPitches, (expectedPitch,))
        self.assertEqual(
            itrill.ornamentalPitches[0].accidental.name,
            'natural'
        )
        self.assertEqual(
            itrill.ornamentalPitches[0].accidental.displayStatus,
            True
        )

        # with accidental=doubleSharpAccid, no key, explicit octave
        doubleSharpAccid = pitch.Accidental('##')
        doubleSharpAccid.displayStatus = True
        trill.accidental = doubleSharpAccid
        itrill.accidental = doubleSharpAccid
        trill.resolveOrnamentalPitches(noteWithExplicitOctave)
        expectedPitch = pitch.Pitch('D4')
        expectedPitch.accidental = pitch.Accidental('double-sharp')
        expectedPitch.displayStatus = True
        self.assertEqual(trill.ornamentalPitches, (expectedPitch,))
        self.assertEqual(
            trill.ornamentalPitches[0].accidental.name,
            'double-sharp'
        )
        self.assertEqual(
            trill.ornamentalPitches[0].accidental.displayStatus,
            True
        )
        itrill.resolveOrnamentalPitches(noteWithImplicitOctave)
        expectedPitch = pitch.Pitch('B3')
        expectedPitch.accidental = pitch.Accidental('double-sharp')
        expectedPitch.displayStatus = True
        self.assertEqual(itrill.ornamentalPitches, (expectedPitch,))
        self.assertEqual(
            itrill.ornamentalPitches[0].accidental.name,
            'double-sharp'
        )
        self.assertEqual(
            itrill.ornamentalPitches[0].accidental.displayStatus,
            True
        )

    def testUpdateAccidentalDisplay(self):
        # Trill is already tested in header doc, test Mordent and Turn here
        noSharpsOrFlats = key.KeySignature(0)
        mord1 = expressions.InvertedMordent()
        mord1.resolveOrnamentalPitches(note.Note('G4'), keySig=noSharpsOrFlats)
        self.assertEqual(mord1.ornamentalPitch, pitch.Pitch('A4'))
        self.assertIsNone(mord1.ornamentalPitch.accidental, None)
        past = [pitch.Pitch('A#4'), pitch.Pitch('C#4'), pitch.Pitch('C4')]
        mord1.updateAccidentalDisplay(pitchPast=past, cautionaryAll=True)
        self.assertEqual(mord1.ornamentalPitch.accidental, pitch.Accidental('natural'))
        self.assertTrue(mord1.ornamentalPitch.accidental.displayStatus)

        mord2 = expressions.InvertedMordent()
        mord2.resolveOrnamentalPitches(note.Note('G4'), keySig=noSharpsOrFlats)
        self.assertEqual(mord2.ornamentalPitch, pitch.Pitch('A4'))
        self.assertIsNone(mord2.ornamentalPitch.accidental, None)
        past = [pitch.Pitch('A#4'), pitch.Pitch('C#4'), pitch.Pitch('C4')]
        mord2.updateAccidentalDisplay(pitchPast=past)  # should add a natural
        self.assertEqual(mord2.ornamentalPitch.accidental, pitch.Accidental('natural'))
        self.assertTrue(mord2.ornamentalPitch.accidental.displayStatus)

        mord3 = expressions.InvertedMordent()
        mord3.resolveOrnamentalPitches(note.Note('G4'), keySig=noSharpsOrFlats)
        self.assertEqual(mord3.ornamentalPitch, pitch.Pitch('A4'))
        self.assertIsNone(mord3.ornamentalPitch.accidental, None)
        past = [pitch.Pitch('A#3'), pitch.Pitch('C#'), pitch.Pitch('C')]
        mord3.updateAccidentalDisplay(pitchPast=past, cautionaryPitchClass=False)
        self.assertIsNone(mord3.ornamentalPitch.accidental)

        turn1 = expressions.Turn()
        turn1.resolveOrnamentalPitches(note.Note('G4'), keySig=noSharpsOrFlats)
        self.assertEqual(turn1.upperOrnamentalPitch, pitch.Pitch('A4'))
        self.assertIsNone(turn1.upperOrnamentalPitch.accidental, None)
        self.assertEqual(turn1.lowerOrnamentalPitch, pitch.Pitch('F4'))
        self.assertIsNone(turn1.lowerOrnamentalPitch.accidental, None)
        past = [pitch.Pitch('A#4'), pitch.Pitch('C#4'), pitch.Pitch('C4')]
        turn1.updateAccidentalDisplay(pitchPast=past, cautionaryAll=True)  # should add naturals
        self.assertEqual(turn1.upperOrnamentalPitch.accidental, pitch.Accidental('natural'))
        self.assertTrue(turn1.upperOrnamentalPitch.accidental.displayStatus)
        self.assertEqual(turn1.lowerOrnamentalPitch.accidental, pitch.Accidental('natural'))
        self.assertTrue(turn1.lowerOrnamentalPitch.accidental.displayStatus)

        turn2 = expressions.Turn()
        turn2.resolveOrnamentalPitches(note.Note('G4'), keySig=noSharpsOrFlats)
        self.assertEqual(turn2.upperOrnamentalPitch, pitch.Pitch('A4'))
        self.assertIsNone(turn2.upperOrnamentalPitch.accidental, None)
        self.assertEqual(turn2.lowerOrnamentalPitch, pitch.Pitch('F4'))
        self.assertIsNone(turn2.lowerOrnamentalPitch.accidental, None)
        past = [pitch.Pitch('A#4'), pitch.Pitch('C#4'), pitch.Pitch('C4')]
        turn2.updateAccidentalDisplay(pitchPast=past)  # should add upper natural
        self.assertEqual(turn2.upperOrnamentalPitch.accidental, pitch.Accidental('natural'))
        self.assertTrue(turn2.upperOrnamentalPitch.accidental.displayStatus)
        self.assertIsNone(turn2.lowerOrnamentalPitch.accidental)

        turn3 = expressions.Turn()
        turn3.resolveOrnamentalPitches(note.Note('G4'), keySig=noSharpsOrFlats)
        self.assertEqual(turn3.upperOrnamentalPitch, pitch.Pitch('A4'))
        self.assertIsNone(turn3.upperOrnamentalPitch.accidental, None)
        self.assertEqual(turn3.lowerOrnamentalPitch, pitch.Pitch('F4'))
        self.assertIsNone(turn3.lowerOrnamentalPitch.accidental, None)
        past = [pitch.Pitch('A#3'), pitch.Pitch('C#'), pitch.Pitch('C')]
        turn3.updateAccidentalDisplay(pitchPast=past, cautionaryPitchClass=False)  # no naturals
        self.assertIsNone(turn3.upperOrnamentalPitch.accidental)
        self.assertIsNone(turn3.lowerOrnamentalPitch.accidental)

    def testUpdateAccidentalDisplayWithAccidentNameSet(self):
        # Trill is already tested in header doc, test Mordent and Turn here
        naturalAccid = pitch.Accidental(0)
        naturalAccid.displayStatus = True
        noSharpsOrFlats = key.KeySignature(0)
        mord = expressions.InvertedMordent()
        mord.accidental = naturalAccid
        mord.resolveOrnamentalPitches(note.Note('G4'), keySig=noSharpsOrFlats)
        expectedOrnamentalPitch = pitch.Pitch('A4')
        expectedOrnamentalPitch.accidental = pitch.Accidental('natural')
        expectedOrnamentalPitch.accidental.displayStatus = True
        self.assertEqual(mord.ornamentalPitch, expectedOrnamentalPitch)
        self.assertEqual(mord.ornamentalPitch.accidental, pitch.Accidental('natural'))
        self.assertTrue(mord.ornamentalPitch.accidental.displayStatus)
        past = [pitch.Pitch('a#3'), pitch.Pitch('c#'), pitch.Pitch('c')]
        mord.updateAccidentalDisplay(pitchPast=past, cautionaryPitchClass=False)
        self.assertEqual(mord.ornamentalPitch, expectedOrnamentalPitch)
        self.assertEqual(mord.ornamentalPitch.accidental, pitch.Accidental('natural'))
        self.assertTrue(mord.ornamentalPitch.accidental.displayStatus)

        turn = expressions.Turn()
        turn.upperAccidental = naturalAccid
        turn.lowerAccidental = naturalAccid
        turn.resolveOrnamentalPitches(note.Note('G4'), keySig=noSharpsOrFlats)
        expectedOrnamentalPitches = (pitch.Pitch('A4'), pitch.Pitch('F4'))
        expectedOrnamentalPitches[0].accidental = pitch.Accidental('natural')
        expectedOrnamentalPitches[0].accidental.displayStatus = True
        expectedOrnamentalPitches[1].accidental = pitch.Accidental('natural')
        expectedOrnamentalPitches[1].accidental.displayStatus = True
        self.assertEqual(turn.ornamentalPitches[0], expectedOrnamentalPitches[0])
        self.assertEqual(turn.ornamentalPitches[0].accidental, pitch.Accidental('natural'))
        self.assertTrue(turn.ornamentalPitches[0].accidental.displayStatus)
        self.assertEqual(turn.ornamentalPitches[1], expectedOrnamentalPitches[1])
        self.assertEqual(turn.ornamentalPitches[1].accidental, pitch.Accidental('natural'))
        self.assertTrue(turn.ornamentalPitches[1].accidental.displayStatus)
        past = [pitch.Pitch('a#3'), pitch.Pitch('c#'), pitch.Pitch('c')]
        turn.updateAccidentalDisplay(pitchPast=past, cautionaryPitchClass=False)
        self.assertEqual(turn.ornamentalPitches[0], expectedOrnamentalPitches[0])
        self.assertEqual(turn.ornamentalPitches[0].accidental, pitch.Accidental('natural'))
        self.assertTrue(turn.ornamentalPitches[0].accidental.displayStatus)
        self.assertEqual(turn.ornamentalPitches[1], expectedOrnamentalPitches[1])
        self.assertEqual(turn.ornamentalPitches[1].accidental, pitch.Accidental('natural'))
        self.assertTrue(turn.ornamentalPitches[1].accidental.displayStatus)

    def testEdgeCases(self):
        # Make sure you can call resolveOrnamentalPitches() on non-Trill/Mordent/Turn Ornaments
        # without raising an exception (or actually doing anything interesting).
        orn = expressions.Ornament()
        orn.resolveOrnamentalPitches(note.Note('C4'))
        self.assertEqual(orn.ornamentalPitches, tuple())

        # Make sure you can call realize() on non-Trill/Mordent/Turn ornaments and
        # just get an identical note back, with empty before and after lists.
        n = note.Note('C4')
        realized = orn.realize(n, inPlace=False)
        self.assertEqual(realized, ([], n, []))
        self.assertIsNot(realized[1], n)
        realized = orn.realize(n, inPlace=True)
        self.assertEqual(realized, ([], n, []))
        self.assertIs(realized[1], n)

        # Make sure that fillListOfRealizedNotes raises if srcObj is Unpitched, but
        # transposeInterval is not unison.
        filledList = []
        with self.assertRaises(TypeError):
            orn.fillListOfRealizedNotes(
                note.Unpitched(),
                fillObjects=filledList,
                transposeInterval=interval.Interval('M2')
            )
        self.assertEqual(filledList, [])

        # Make sure various Ornaments have correct direction
        self.assertEqual(expressions.Trill().direction, 'up')
        self.assertEqual(expressions.InvertedTrill().direction, 'down')
        self.assertEqual(expressions.Mordent().direction, 'down')
        self.assertEqual(expressions.InvertedMordent().direction, 'up')

        # Make sure Turn.getSize raises on bad which value (must be 'upper' or 'lower')
        with self.assertRaises(expressions.ExpressionException):
            expressions.Turn().getSize(note.Note('C4'), which='bad: not upper or lower')

    def testUnpitchedOrnaments(self):
        unp = note.Unpitched()

        mord = expressions.Mordent()
        realized = mord.realize(unp)
        self.assertEqual(len(realized), 3)
        self.assertEqual(len(realized[0]), 2)
        self.assertIsInstance(realized[0][0], note.Unpitched)
        self.assertIsInstance(realized[0][1], note.Unpitched)
        self.assertIsInstance(realized[1], note.Unpitched)
        self.assertEqual(len(realized[2]), 0)
        self.assertEqual(mord.getSize(unp), interval.Interval('P1'))
        mord.resolveOrnamentalPitches(unp)
        self.assertEqual(mord.ornamentalPitches, tuple())

        mord = expressions.InvertedMordent()
        realized = mord.realize(unp)
        self.assertEqual(len(realized), 3)
        self.assertEqual(len(realized[0]), 2)
        self.assertIsInstance(realized[0][0], note.Unpitched)
        self.assertIsInstance(realized[0][1], note.Unpitched)
        self.assertIsInstance(realized[1], note.Unpitched)
        self.assertEqual(len(realized[2]), 0)
        self.assertEqual(mord.getSize(unp), interval.Interval('P1'))
        mord.resolveOrnamentalPitches(unp)
        self.assertEqual(mord.ornamentalPitches, tuple())

        turn = expressions.Turn()
        realized = turn.realize(unp)
        self.assertEqual(len(realized), 3)
        self.assertEqual(len(realized[0]), 0)
        self.assertIsNone(realized[1])
        self.assertEqual(len(realized[2]), 4)
        self.assertIsInstance(realized[2][0], note.Unpitched)
        self.assertIsInstance(realized[2][1], note.Unpitched)
        self.assertIsInstance(realized[2][2], note.Unpitched)
        self.assertIsInstance(realized[2][3], note.Unpitched)
        self.assertEqual(turn.getSize(unp, which='upper'), interval.Interval('P1'))
        self.assertEqual(turn.getSize(unp, which='lower'), interval.Interval('P1'))
        turn.resolveOrnamentalPitches(unp)
        self.assertEqual(turn.ornamentalPitches, tuple())

        turn = expressions.InvertedTurn()
        realized = turn.realize(unp)
        self.assertEqual(len(realized), 3)
        self.assertEqual(len(realized[0]), 0)
        self.assertIsNone(realized[1])
        self.assertEqual(len(realized[2]), 4)
        self.assertIsInstance(realized[2][0], note.Unpitched)
        self.assertIsInstance(realized[2][1], note.Unpitched)
        self.assertIsInstance(realized[2][2], note.Unpitched)
        self.assertIsInstance(realized[2][3], note.Unpitched)
        self.assertEqual(turn.getSize(unp, which='upper'), interval.Interval('P1'))
        self.assertEqual(turn.getSize(unp, which='lower'), interval.Interval('P1'))
        turn.resolveOrnamentalPitches(unp)
        self.assertEqual(turn.ornamentalPitches, tuple())

        trill = expressions.Trill()
        realized = trill.realize(unp)
        self.assertEqual(len(realized), 3)
        self.assertEqual(len(realized[0]), 8)
        self.assertIsInstance(realized[0][0], note.Unpitched)
        self.assertIsInstance(realized[0][1], note.Unpitched)
        self.assertIsInstance(realized[0][2], note.Unpitched)
        self.assertIsInstance(realized[0][3], note.Unpitched)
        self.assertIsInstance(realized[0][4], note.Unpitched)
        self.assertIsInstance(realized[0][5], note.Unpitched)
        self.assertIsInstance(realized[0][6], note.Unpitched)
        self.assertIsInstance(realized[0][7], note.Unpitched)
        self.assertIsNone(realized[1])
        self.assertEqual(len(realized[2]), 0)
        self.assertEqual(trill.getSize(unp), interval.Interval('P1'))
        trill.resolveOrnamentalPitches(unp)
        self.assertEqual(turn.ornamentalPitches, tuple())

        trill = expressions.InvertedTrill()
        realized = trill.realize(unp)
        self.assertEqual(len(realized), 3)
        self.assertEqual(len(realized[0]), 8)
        self.assertIsInstance(realized[0][0], note.Unpitched)
        self.assertIsInstance(realized[0][1], note.Unpitched)
        self.assertIsInstance(realized[0][2], note.Unpitched)
        self.assertIsInstance(realized[0][3], note.Unpitched)
        self.assertIsInstance(realized[0][4], note.Unpitched)
        self.assertIsInstance(realized[0][5], note.Unpitched)
        self.assertIsInstance(realized[0][6], note.Unpitched)
        self.assertIsInstance(realized[0][7], note.Unpitched)
        self.assertIsNone(realized[1])
        self.assertEqual(len(realized[2]), 0)
        self.assertEqual(trill.getSize(unp), interval.Interval('P1'))
        trill.resolveOrnamentalPitches(unp)
        self.assertEqual(turn.ornamentalPitches, tuple())


# class TestExternal(unittest.TestCase):
#     def testCPEBachRealizeOrnaments(self):
#         from music21 import corpus
#         cpe = corpus.parse('cpebach/h186').parts[0].measures(1, 4)
#         cpe2 = cpe.realizeOrnaments()
#         cpe2.show()


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
