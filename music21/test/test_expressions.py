
from __future__ import annotations

import unittest

from music21 import chord
from music21 import clef
from music21 import expressions
from music21 import key
from music21 import meter
from music21.musicxml import m21ToXml
from music21 import note
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

        # because turn0.quarterLength defaults to 0.25 (16th-note), each of the four turn
        # notes is ql=0.25 instead of 0.375 (realize doesn't stretch to fill).
        self.assertEqual(realized2[0].quarterLength, 0.25)
        self.assertEqual(realized2[1].quarterLength, 0.25)
        self.assertEqual(realized2[2].quarterLength, 0.25)
        self.assertEqual(realized2[3].quarterLength, 0.25)

        # Here, delay is still a quarter-note (delay=1.0), and each of the four turn notes
        # is ql=0.125 (because turn0.quarterLength has been set to 0.125, and realize
        # doesn't stretch to fit).
        turn0.quarterLength = 0.125
        realized1b = expressions.realizeOrnaments(n1)
        self.assertEqual(realized1b[0].quarterLength, 1.0)
        self.assertEqual(realized1b[1].quarterLength, 0.125)
        self.assertEqual(realized1b[2].quarterLength, 0.125)
        self.assertEqual(realized1b[3].quarterLength, 0.125)
        self.assertEqual(realized1b[4].quarterLength, 0.125)


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

    def testUnpitchedUnsupported(self):
        unp = note.Unpitched()
        mord = expressions.Mordent()
        with self.assertRaises(TypeError):
            mord.realize(unp)  # type: ignore


# class TestExternal(unittest.TestCase):
#     def testCPEBachRealizeOrnaments(self):
#         from music21 import corpus
#         cpe = corpus.parse('cpebach/h186').parts[0].measures(1, 4)
#         cpe2 = cpe.realizeOrnaments()
#         cpe2.show()


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
