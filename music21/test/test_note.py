from __future__ import annotations

import copy
import unittest

from music21 import articulations
from music21 import corpus
from music21.duration import DurationTuple
from music21 import expressions
from music21.lily.translate import LilypondConverter
from music21 import meter
from music21 import note
from music21 import stream
from music21 import tie
from music21 import volume

class Test(unittest.TestCase):
    def testLyricRepr(self):
        ly = note.Lyric()
        self.assertEqual(repr(ly), '<music21.note.Lyric number=1>')
        ly.text = 'hi'
        self.assertEqual(repr(ly), "<music21.note.Lyric number=1 text='hi'>")
        ly.identifier = 'verse'
        self.assertEqual(repr(ly), "<music21.note.Lyric number=1 identifier='verse' text='hi'>")
        ly.text = None
        self.assertEqual(repr(ly), "<music21.note.Lyric number=1 identifier='verse'>")

    def testComplex(self):
        note1 = note.Note()
        note1.duration.clear()
        d1 = DurationTuple('whole', 0, 4.0)
        d2 = DurationTuple('quarter', 0, 1.0)
        note1.duration.addDurationTuple(d1)
        note1.duration.addDurationTuple(d2)
        self.assertEqual(note1.duration.quarterLength, 5.0)
        self.assertEqual(note1.duration.componentIndexAtQtrPosition(2), 0)
        self.assertEqual(note1.duration.componentIndexAtQtrPosition(4), 1)
        self.assertEqual(note1.duration.componentIndexAtQtrPosition(4.5), 1)
        note1.duration.sliceComponentAtPosition(1.0)

        matchStr = "c'4~\nc'2.~\nc'4"
        conv = LilypondConverter()
        conv.appendM21ObjectToContext(note1)
        outStr = str(conv.context).replace(' ', '').strip()
        # print(outStr)
        self.assertEqual(matchStr, outStr)
        i = 0
        for thisNote in note1.splitAtDurations():
            matchSub = matchStr.split('\n')[i]  # pylint: disable=use-maxsplit-arg
            conv = LilypondConverter()
            conv.appendM21ObjectToContext(thisNote)
            outStr = str(conv.context).replace(' ', '').strip()
            self.assertEqual(matchSub, outStr)
            i += 1

    def testNote(self):
        note2 = note.Rest()
        self.assertTrue(note2.isRest)
        note3 = note.Note()
        note3.pitch.name = 'B-'
        # not sure how to test not None
        # self.assertFalse (note3.pitch.accidental, None)
        self.assertEqual(note3.pitch.accidental.name, 'flat')
        self.assertEqual(note3.pitch.pitchClass, 10)

        a5 = note.Note()
        a5.name = 'A'
        a5.octave = 5
        self.assertAlmostEqual(a5.pitch.frequency, 880.0)
        self.assertEqual(a5.pitch.pitchClass, 9)

    def testCopyNote(self):
        a = note.Note()
        a.quarterLength = 3.5
        a.name = 'D'
        b = copy.deepcopy(a)
        self.assertEqual(b.name, a.name)

    def testMusicXMLFermata(self):
        a = corpus.parse('bach/bwv5.7')
        found = []
        for n in a.flatten().notesAndRests:
            for obj in n.expressions:
                if isinstance(obj, expressions.Fermata):
                    found.append(obj)
        self.assertEqual(len(found), 24)

    def testNoteBeatProperty(self):
        data = [
            ['3/4', 0.5, 6, [1.0, 1.5, 2.0, 2.5, 3.0, 3.5],
             [1.0] * 6, ],
            ['3/4', 0.25, 8, [1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75],
             [1.0] * 8],
            ['3/2', 0.5, 8, [1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75],
             [2.0] * 8],

            ['6/8', 0.5, 6, [1.0, 1.3333, 1.66666, 2.0, 2.3333, 2.666666],
             [1.5] * 6],
            ['9/8', 0.5, 6, [1.0, 1.3333, 1.66666, 2.0, 2.3333, 2.666666],
             [1.5] * 6],
            ['12/8', 0.5, 6, [1.0, 1.3333, 1.66666, 2.0, 2.3333, 2.666666],
             [1.5] * 6],

            ['6/16', 0.25, 6, [1.0, 1.3333, 1.66666, 2.0, 2.3333, 2.666666],
             [0.75] * 6],

            ['5/4', 1, 5, [1.0, 2.0, 3.0, 4.0, 5.0],
             [1.] * 5],

            ['2/8+3/8+2/8', 0.5, 6, [1.0, 1.5, 2.0, 2.33333, 2.66666, 3.0],
             [1., 1., 1.5, 1.5, 1.5, 1.]],

        ]

        # one measure case
        for tsStr, nQL, nCount, matchBeat, matchBeatDur in data:
            n = note.Note()  # need fully qualified name
            n.quarterLength = nQL
            m = stream.Measure()
            m.timeSignature = meter.TimeSignature(tsStr)
            m.repeatAppend(n, nCount)

            self.assertEqual(len(m), nCount + 1)

            # test matching beat proportion value
            post = [m.notesAndRests[i].beat for i in range(nCount)]
            for i in range(len(matchBeat)):
                self.assertAlmostEqual(post[i], matchBeat[i], 4)

            # test getting beat duration
            post = [m.notesAndRests[i].beatDuration.quarterLength for i in range(nCount)]

            for i in range(len(matchBeat)):
                self.assertAlmostEqual(post[i], matchBeatDur[i], 4)

        # two measure case
        for tsStr, nQL, nCount, matchBeat, matchBeatDur in data:
            p = stream.Part()
            n = note.Note()
            n.quarterLength = nQL

            # m1 has time signature
            m1 = stream.Measure()
            m1.timeSignature = meter.TimeSignature(tsStr)
            p.append(m1)

            # m2 does not have time signature
            m2 = stream.Measure()
            m2.repeatAppend(n, nCount)
            self.assertEqual(len(m2), nCount)
            self.assertEqual(len(m2.notesAndRests), nCount)

            p.append(m2)

            # test matching beat proportion value
            post = [m2.notesAndRests[i].beat for i in range(nCount)]
            for i in range(len(matchBeat)):
                self.assertAlmostEqual(post[i], matchBeat[i], 4)
            # test getting beat duration
            post = [m2.notesAndRests[i].beatDuration.quarterLength for i in range(nCount)]
            for i in range(len(matchBeat)):
                self.assertAlmostEqual(post[i], matchBeatDur[i], 4)

    def testNoteBeatPropertyCorpus(self):
        data = [['bach/bwv255', [4.0, 1.0, 2.5, 3.0, 4.0, 4.5, 1.0, 1.5]],
                ['bach/bwv153.9', [1.0, 2.0, 3.0, 1.0, 2.0, 3.0, 1.0, 3.0, 1.0]]
                ]

        for work, match in data:
            s = corpus.parse(work)
            # always use tenor line
            found = []
            for n in s.parts[2].flatten().notesAndRests:
                n.lyric = n.beatStr
                found.append(n.beat)

            for i in range(len(match)):
                self.assertEqual(match[i], found[i])

            # s.show()

    def testNoteEquality(self):
        n1 = note.Note('A#')
        n2 = note.Note('G')
        n3 = note.Note('A-')
        n4 = note.Note('A#')

        self.assertNotEqual(n1, n2)
        self.assertNotEqual(n1, n3)
        self.assertEqual(n1, n4)

        # test durations with the same pitch
        for x, y, match in [
            (1, 1, True),
            (1, 0.5, False),
            (1, 2, False),
            (1, 1.5, False)
        ]:
            n1.quarterLength = x
            n4.quarterLength = y
            self.assertEqual(n1 == n4, match)  # sub1

        # test durations with different pitch
        for x, y, match in [(1, 1, False), (1, 0.5, False),
                            (1, 2, False), (1, 1.5, False)]:
            n1.quarterLength = x
            n2.quarterLength = y
            self.assertEqual(n1 == n2, match)  # sub2

        # same pitches different octaves
        n1.quarterLength = 1.0
        n4.quarterLength = 1.0
        for x, y, match in [(4, 4, True), (3, 4, False), (2, 4, False)]:
            n1.pitch.octave = x
            n4.pitch.octave = y
            self.assertEqual(n1 == n4, match)  # sub4

        # with and without ties
        n1.pitch.octave = 4
        n4.pitch.octave = 4
        t1 = tie.Tie()
        t2 = tie.Tie()
        for x, y, match in [(t1, None, False), (t1, t2, True)]:
            n1.tie = x
            n4.tie = y
            self.assertEqual(n1 == n4, match)  # sub4

        # with ties but different pitches
        for n in [n1, n2, n3, n4]:
            n.quarterLength = 1.0
        t1 = tie.Tie()
        t2 = tie.Tie()
        for a, b, match in [(n1, n2, False), (n1, n3, False),
                            (n2, n3, False), (n1, n4, True)]:
            a.tie = t1
            b.tie = t2
            self.assertEqual(a == b, match)  # sub5

        # articulation groups
        a1 = [articulations.Accent()]
        a2 = [articulations.Accent(), articulations.StrongAccent()]
        a3 = [articulations.StrongAccent(), articulations.Accent()]
        a4 = [articulations.StrongAccent(), articulations.Accent(),
              articulations.Tenuto()]
        a5 = [articulations.Accent(), articulations.Tenuto(),
              articulations.StrongAccent()]

        for a, b, c, d, match in [(n1, n4, a1, a1, True),
                                      (n1, n2, a1, a1, False), (n1, n3, a1, a1, False),
                                  # same pitch different orderings
                                  (n1, n4, a2, a3, True), (n1, n4, a4, a5, True),
                                  # different pitch same orderings
                                  (n1, n2, a2, a3, False), (n1, n3, a4, a5, False),
                                  ]:
            a.articulations = c
            b.articulations = d
            self.assertEqual(a == b, match)  # sub6

    def testMetricalAccent(self):
        data = [
            ('4/4', 8, 0.5, [1.0, 0.125, 0.25, 0.125, 0.5, 0.125, 0.25, 0.125]),
            ('3/4', 6, 0.5, [1.0, 0.25, 0.5, 0.25, 0.5, 0.25]),
            ('6/8', 6, 0.5, [1.0, 0.25, 0.25, 0.5, 0.25, 0.25]),

            ('12/32', 12, 0.125, [1.0, 0.125, 0.125, 0.25, 0.125, 0.125,
                                  0.5, 0.125, 0.125, 0.25, 0.125, 0.125]),

            ('5/8', 10, 0.25, [1.0, 0.25, 0.5, 0.25, 0.5, 0.25, 0.5, 0.25, 0.5, 0.25]),

            # test notes that do not have defined accents
            ('4/4', 16, 0.25, [1.0, 0.0625, 0.125, 0.0625, 0.25, 0.0625, 0.125, 0.0625,
                               0.5, 0.0625, 0.125, 0.0625, 0.25, 0.0625, 0.125, 0.0625]),
            ('4/4', 32, 0.125, [1.0, 0.0625, 0.0625, 0.0625, 0.125, 0.0625, 0.0625, 0.0625,
                                0.25, 0.0625, 0.0625, 0.0625, 0.125, 0.0625, 0.0625, 0.0625,
                                0.5, 0.0625, 0.0625, 0.0625, 0.125, 0.0625, 0.0625, 0.0625,
                                0.25, 0.0625, 0.0625, 0.0625, 0.125, 0.0625, 0.0625, 0.0625]),
        ]

        for tsStr, nCount, dur, match in data:
            m = stream.Measure()
            m.timeSignature = meter.TimeSignature(tsStr)
            n = note.Note()
            n.quarterLength = dur
            m.repeatAppend(n, nCount)

            self.assertEqual([n.beatStrength for n in m.notesAndRests], match)

    def testTieContinue(self):
        n1 = note.Note()
        n1.tie = tie.Tie()
        n1.tie.type = 'start'

        n2 = note.Note()
        n2.tie = tie.Tie()
        n2.tie.type = 'continue'

        n3 = note.Note()
        n3.tie = tie.Tie()
        n3.tie.type = 'stop'

        s = stream.Stream()
        s.append([n1, n2, n3])

        # need to test that this gets us a "continue" tie, but hard to test
        # post musicxml processing
        # s.show()

    def testVolumeA(self):
        v1 = volume.Volume()

        n1 = note.Note()
        n2 = note.Note()

        n1.volume = v1  # can set as v1 has no client
        self.assertEqual(n1.volume, v1)
        self.assertEqual(n1.volume.client, n1)

        # object is created on demand
        self.assertIsNot(n2.volume, v1)
        self.assertIsNotNone(n2.volume)

    def testVolumeB(self):
        # manage deepcopying properly
        n1 = note.Note()

        n1.volume.velocity = 100
        self.assertEqual(n1.volume.velocity, 100)
        self.assertEqual(n1.volume.client, n1)

        n1Copy = copy.deepcopy(n1)
        self.assertEqual(n1Copy.volume.velocity, 100)
        self.assertEqual(n1Copy.volume.client, n1Copy)


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
