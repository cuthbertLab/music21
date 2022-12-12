from __future__ import annotations

import copy
import random
import unittest

from music21.abcFormat import testFiles
from music21 import bar
from music21 import converter
from music21 import corpus
from music21 import environment
from music21 import expressions
from music21 import features
from music21 import instrument
from music21 import meter
from music21.musicxml import m21ToXml
from music21.musicxml import testPrimitive
from music21 import note
from music21 import pitch
from music21 import repeat
from music21 import spanner
from music21 import stream

environLocal = environment.Environment('test.test_repeat')


# ------------------------------------------------------------------------------
class Test(unittest.TestCase):
    def testFilterByRepeatMark(self):
        s = stream.Part()
        m1 = stream.Measure()
        m1.leftBarline = bar.Repeat(direction='start')
        m1.rightBarline = bar.Repeat(direction='end', times=2)
        m1.repeatAppend(note.Note('g3', quarterLength=1), 4)

        self.assertEqual(len(m1.getElementsByClass('RepeatMark')), 2)  # leave quotes

        m2 = stream.Measure()
        m2.leftBarline = bar.Repeat(direction='start')
        m2.rightBarline = bar.Repeat(direction='end', times=2)
        m2.repeatAppend(note.Note('d4', quarterLength=1), 4)

        s.append(m1)
        s.append(m2)

        # s.show()

        # now have 4
        self.assertEqual(len(s['RepeatMark']), 4)

        # check coherence
        ex = repeat.Expander(s)
        self.assertTrue(ex.repeatBarsAreCoherent())
        self.assertEqual(ex.findInnermostRepeatIndices(s), [0])

    def testRepeatCoherenceB(self):
        s = stream.Part()
        m1 = stream.Measure()
        m1.leftBarline = bar.Repeat(direction='start')
        m1.rightBarline = bar.Repeat(direction='end', times=2)
        m1.repeatAppend(note.Note('g3', quarterLength=1), 4)

        m2 = stream.Measure()

        m3 = stream.Measure()
        m3.leftBarline = bar.Repeat(direction='start')
        # m3.rightBarline = bar.Repeat(direction='end', times=2)
        m3.repeatAppend(note.Note('d4', quarterLength=1), 4)

        s.append(m1)
        s.append(m2)
        s.append(m3)

        # check coherence: will raise
        ex = repeat.Expander(s)
        self.assertFalse(ex.isExpandable())
        self.assertEqual(ex.findInnermostRepeatIndices(s), [0])

    def testRepeatCoherenceB2(self):
        # a nested repeat; acceptable
        s = stream.Part()
        m1 = stream.Measure()
        m1.leftBarline = bar.Repeat(direction='start')
        # m1.rightBarline = bar.Repeat(direction='end', times=2)
        m1.repeatAppend(note.Note('g3', quarterLength=1), 4)

        m2 = stream.Measure()
        m2.leftBarline = bar.Repeat(direction='start')
        # m2.rightBarline = bar.Repeat(direction='end', times=2)
        m2.repeatAppend(note.Note('b3', quarterLength=1), 4)

        m3 = stream.Measure()
        # m3.leftBarline = bar.Repeat(direction='start')
        m3.rightBarline = bar.Repeat(direction='end', times=2)
        m3.repeatAppend(note.Note('d4', quarterLength=1), 4)

        m4 = stream.Measure()
        # m4.leftBarline = bar.Repeat(direction='start')
        m4.rightBarline = bar.Repeat(direction='end', times=2)
        m4.repeatAppend(note.Note('f4', quarterLength=1), 4)

        s.append(m1)
        s.append(m2)
        s.append(m3)
        s.append(m4)

        # s.show()

        # check coherence
        ex = repeat.Expander(s)
        self.assertTrue(ex.repeatBarsAreCoherent())
        self.assertEqual(ex.findInnermostRepeatIndices(s), [1, 2])

        post = ex.process()
        # post.show()
        self.assertEqual(len(post.getElementsByClass(stream.Measure)), 12)
        self.assertEqual(len(post.recurse().notesAndRests), 48)
        self.assertEqual([m.offset for m in post.getElementsByClass(stream.Measure)],
                         [0.0, 4.0, 8.0, 12.0, 16.0, 20.0, 24.0,
                          28.0, 32.0, 36.0, 40.0, 44.0])

        self.assertEqual([n.nameWithOctave
                          for n in post.flatten().getElementsByClass(note.Note)],
                         ['G3', 'G3', 'G3', 'G3', 'B3', 'B3', 'B3', 'B3',
                          'D4', 'D4', 'D4', 'D4',
                          'B3', 'B3', 'B3', 'B3', 'D4', 'D4', 'D4', 'D4',
                          'F4', 'F4', 'F4', 'F4', 'G3', 'G3', 'G3', 'G3',
                          'B3', 'B3', 'B3', 'B3',
                          'D4', 'D4', 'D4', 'D4', 'B3', 'B3', 'B3', 'B3',
                          'D4', 'D4', 'D4', 'D4', 'F4', 'F4', 'F4', 'F4'])

    def testRepeatCoherenceC(self):
        '''
        Using da capo/dal segno
        '''
        # no repeats
        s = stream.Part()
        m1 = stream.Measure()
        m2 = stream.Measure()
        m3 = stream.Measure()
        s.append([m1, m2, m3])
        ex = repeat.Expander(s)
        self.assertFalse(ex.isExpandable())

        s = stream.Part()
        m1 = stream.Measure()
        m2 = stream.Measure()
        m3 = stream.Measure()
        m3.append(repeat.DaCapo())
        s.append([m1, m2, m3])
        ex = repeat.Expander(s)
        self.assertTrue(ex.isExpandable())

        # missing segno
        s = stream.Part()
        m1 = stream.Measure()
        m2 = stream.Measure()
        m3 = stream.Measure()
        m3.append(repeat.DalSegno())
        s.append([m1, m2, m3])
        ex = repeat.Expander(s)
        self.assertFalse(ex.isExpandable())

        s = stream.Part()
        m1 = stream.Measure()
        m2 = stream.Measure()
        m2.append(repeat.Segno())
        m3 = stream.Measure()
        m3.append(repeat.DalSegno())
        s.append([m1, m2, m3])
        ex = repeat.Expander(s)
        self.assertTrue(ex.isExpandable())

        # dc al fine
        s = stream.Part()
        m1 = stream.Measure()
        m2 = stream.Measure()
        m2.append(repeat.Fine())
        m3 = stream.Measure()
        m3.append(repeat.DaCapoAlFine())
        s.append([m1, m2, m3])
        ex = repeat.Expander(s)
        self.assertTrue(ex.isExpandable())

        # dc al fine but missing fine
        s = stream.Part()
        m1 = stream.Measure()
        m2 = stream.Measure()
        m3 = stream.Measure()
        m3.append(repeat.DaCapoAlFine())
        s.append([m1, m2, m3])
        ex = repeat.Expander(s)
        self.assertFalse(ex.isExpandable())

        # ds al fine
        s = stream.Part()
        m1 = stream.Measure()
        m1.append(repeat.Segno())
        m2 = stream.Measure()
        m2.append(repeat.Fine())
        m3 = stream.Measure()
        m3.append(repeat.DalSegnoAlFine())
        s.append([m1, m2, m3])
        ex = repeat.Expander(s)
        self.assertTrue(ex.isExpandable())

        # "ds al fine" missing "fine"
        s = stream.Part()
        m1 = stream.Measure()
        m1.append(repeat.Segno())
        m2 = stream.Measure()
        m3 = stream.Measure()
        m3.append(repeat.DalSegnoAlFine())
        s.append([m1, m2, m3])
        ex = repeat.Expander(s)
        self.assertFalse(ex.isExpandable())

        # dc al coda
        s = stream.Part()
        m1 = stream.Measure()
        m1.append(repeat.Coda())
        m2 = stream.Measure()
        m3 = stream.Measure()
        m3.append(repeat.Coda())
        m3.append(repeat.DaCapoAlCoda())
        s.append([m1, m2, m3])
        ex = repeat.Expander(s)
        self.assertTrue(ex.isExpandable())

        # dc al coda missing one of two codas
        s = stream.Part()
        m1 = stream.Measure()
        m2 = stream.Measure()
        m3 = stream.Measure()
        m3.append(repeat.Coda())
        m3.append(repeat.DaCapoAlCoda())
        s.append([m1, m2, m3])
        ex = repeat.Expander(s)
        self.assertFalse(ex.isExpandable())

        # ds al coda
        s = stream.Part()
        m1 = stream.Measure()
        m1.append(repeat.Segno())
        m1.append(repeat.Coda())
        m2 = stream.Measure()
        m3 = stream.Measure()
        m3.append(repeat.Coda())
        m3.append(repeat.DaCapoAlCoda())
        s.append([m1, m2, m3])
        ex = repeat.Expander(s)
        self.assertTrue(ex.isExpandable())
        # ex._processRepeatExpression(s, s)

    def testExpandRepeatA(self):





        # two repeat bars in a row
        p = stream.Part()
        m1 = stream.Measure(number=1)
        m1.leftBarline = bar.Repeat(direction='start')
        m1.rightBarline = bar.Repeat(direction='end')
        m1.repeatAppend(note.Note('g3', quarterLength=1), 4)

        m2 = stream.Measure(number=2)
        m2.leftBarline = bar.Repeat(direction='start')
        m2.rightBarline = bar.Repeat(direction='end')
        m2.repeatAppend(note.Note('d4', quarterLength=1), 4)

        p.append(m1)
        p.append(m2)

        ex = repeat.Expander(p)
        post = ex.process()

        self.assertEqual(len(post.getElementsByClass(stream.Measure)), 4)
        self.assertEqual(len(post.recurse().notesAndRests), 16)
        self.assertEqual([m.offset for m in post.getElementsByClass(stream.Measure)],
                         [0.0, 4.0, 8.0, 12.0])

        self.assertEqual([n.nameWithOctave
                          for n in post.flatten().getElementsByClass(note.Note)],
                         ['G3', 'G3', 'G3', 'G3', 'G3', 'G3', 'G3', 'G3',
                          'D4', 'D4', 'D4', 'D4', 'D4', 'D4', 'D4', 'D4'])
        measureNumbersPost = [m.measureNumberWithSuffix()
                              for m in post.getElementsByClass(stream.Measure)]
        self.assertEqual(['1', '1a', '2', '2a'], measureNumbersPost)

        # two repeat bars with another bar in between
        s = stream.Part()
        m1 = stream.Measure()
        m1.leftBarline = bar.Repeat(direction='start')
        m1.rightBarline = bar.Repeat(direction='end')
        m1.repeatAppend(note.Note('g3', quarterLength=1), 4)

        m2 = stream.Measure()
        m2.repeatAppend(note.Note('f3', quarterLength=1), 4)

        m3 = stream.Measure()
        m3.leftBarline = bar.Repeat(direction='start')
        m3.rightBarline = bar.Repeat(direction='end')
        m3.repeatAppend(note.Note('d4', quarterLength=1), 4)

        s.append(m1)
        s.append(m2)
        s.append(m3)
        # s.show('t')

        ex = repeat.Expander(s)
        post = ex.process()

        self.assertEqual(len(post.getElementsByClass(stream.Measure)), 5)
        self.assertEqual(len(post.recurse().notesAndRests), 20)
        self.assertEqual([m.offset for m in post.getElementsByClass(stream.Measure)],
                         [0.0, 4.0, 8.0, 12.0, 16.0])
        self.assertEqual([n.nameWithOctave
                          for n in post.flatten().getElementsByClass(note.Note)],
                         ['G3', 'G3', 'G3', 'G3', 'G3', 'G3', 'G3',
                          'G3', 'F3', 'F3', 'F3', 'F3',
                          'D4', 'D4', 'D4', 'D4', 'D4', 'D4', 'D4', 'D4'])

        # post.show('t')
        # post.show()

    def testExpandRepeatB(self):
        s = converter.parse(testFiles.draughtOfAle)
        # s.show()
        self.assertEqual(len(s.parts[0].getElementsByClass(stream.Measure)), 18)
        self.assertEqual(s.metadata.title, '"A Draught of Ale"    (jig)     0912')
        self.assertEqual(len(s.recurse().notesAndRests), 88)

        # s.show()
        unused_ex = repeat.Expander(s.parts[0])
        # check boundaries here

        post = s.expandRepeats()
        self.assertEqual(len(post.parts[0].getElementsByClass(stream.Measure)), 36)
        # make sure metadata is copied
        self.assertEqual(post.metadata.title, '"A Draught of Ale"    (jig)     0912')
        self.assertEqual(len(post.recurse().notesAndRests), 88 * 2)

        # post.show()

    def testExpandRepeatC(self):
        s = converter.parse(testFiles.kingOfTheFairies)
        self.assertEqual(len(s.parts[0].getElementsByClass(stream.Measure)),
                         26)
        self.assertEqual(s.metadata.title, 'King of the fairies')
        self.assertEqual(len(s.recurse().notesAndRests), 145)

        # s.show()
        ex = repeat.Expander(s.parts[0])
        self.assertEqual(ex.findInnermostRepeatIndices(
            s.parts[0].getElementsByClass(stream.Measure)),
            [0, 1, 2, 3, 4, 5, 6, 7, 8]
        )
        # check boundaries here

        # TODO: this is not yet correct, and is making too many copies
        post = s.expandRepeats()
        self.assertEqual(len(post.parts[0].getElementsByClass(stream.Measure)), 35)
        # make sure metadata is copied
        self.assertEqual(post.metadata.title, 'King of the fairies')
        self.assertEqual(len(post.recurse().notesAndRests), 192)

        # post.show()

    def testExpandRepeatD(self):

        # test one back repeat at end of a measure




        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        m2 = stream.Measure()
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        m2.rightBarline = bar.Repeat(direction='end')
        self.assertEqual(m2.rightBarline.location, 'right')

        m3 = stream.Measure()
        m3.repeatAppend(note.Note('g4', type='half'), 2)
        m4 = stream.Measure()
        m4.repeatAppend(note.Note('b-4', type='half'), 2)

        s = stream.Part()
        s.append([m1, m2, m3, m4])
        self.assertEqual(len(s.recurse().notes), 8)
        post = s.expandRepeats()
        self.assertEqual(len(post.getElementsByClass(stream.Measure)), 6)
        self.assertEqual(len(post.recurse().notes), 12)

    def testExpandRepeatE(self):

        # test one back repeat at end of a measure




        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        m2 = stream.Measure()
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        m2.leftBarline = bar.Repeat(direction='start')
        rb = bar.Repeat(direction='end')
        m2.rightBarline = rb
        m3 = stream.Measure()
        m3.repeatAppend(note.Note('g4', type='half'), 2)

        s = stream.Part()
        s.append([m1, m2, m3])

        self.assertEqual(len(s.recurse().notes), 6)
        self.assertEqual(len(s.getElementsByClass(stream.Measure)), 3)

        # default times is 2, or 1 repeat
        post = s.expandRepeats()
        self.assertEqual(len(post.recurse().notes), 8)
        self.assertEqual(len(post.getElementsByClass(stream.Measure)), 4)

        # can change times
        rb.times = 1  # one is no repeat
        post = s.expandRepeats()
        self.assertEqual(len(post.recurse().notes), 6)
        self.assertEqual(len(post.getElementsByClass(stream.Measure)), 3)

        rb.times = 0  # removes the entire passage
        post = s.expandRepeats()
        self.assertEqual(len(post.recurse().notes), 4)
        self.assertEqual(len(post.getElementsByClass(stream.Measure)), 2)

        rb.times = 4
        post = s.expandRepeats()
        self.assertEqual(len(post.recurse().notes), 12)
        self.assertEqual(len(post.getElementsByClass(stream.Measure)), 6)

    def testExpandRepeatF(self):
        # an algorithmic generation approach
        dur = [0.125, 0.25, 0.5, 0.125]
        durA = dur
        durB = dur[1:] + dur[:1]
        durC = dur[2:] + dur[:2]
        durD = dur[3:] + dur[:3]

        s = stream.Stream()
        repeatHandles = []
        for dur in [durA, durB, durC, durD]:
            m = stream.Measure()
            m.timeSignature = meter.TimeSignature('1/4')
            for d in dur:
                m.append(note.Note(quarterLength=d))
                m.leftBarline = bar.Repeat(direction='start')
                rb = bar.Repeat(direction='end')
                m.rightBarline = rb
                m.makeBeams(inPlace=True)
                repeatHandles.append(rb)
            s.append(m)

        final = stream.Stream()
        # alter all repeatTimes values, expand, and append to final
        for i in range(6):
            for rb in repeatHandles:
                rb.times = random.choice([0, 1, 3])
            expanded = s.expandRepeats()
            for m in expanded:
                final.append(m)
        # final.show()

    # def testExpandRepeatG(self):
    #     unused_s = converter.parse(testFiles.hectorTheHero)
    #     # TODO: this file does not import correctly due to first/second
    #     # ending issues
    #     # s.show()

    def testExpandRepeatH(self):
        # an algorithmic generation approach
        dur = [0.125, 0.25, 0.5, 0.125]
        repeatTimesCycle = [0, 1, 3, 5]
        pitches = [pitch.Pitch(p) for p in ['a2', 'b-3', 'a2', 'a2']]

        s = stream.Stream()
        repeatHandles = []
        for i in range(8):
            m = stream.Measure()
            m.timeSignature = meter.TimeSignature('1/4')
            for j, p in enumerate(pitches):
                m.append(note.Note(p.transpose(i * 3), quarterLength=dur[j]))
            m.leftBarline = bar.Repeat(direction='start')
            rb = bar.Repeat(direction='end')
            rb.times = repeatTimesCycle[i % len(repeatTimesCycle)]
            te = rb.getTextExpression()
            m.rightBarline = rb
            m.append(te)
            m.makeBeams(inPlace=True)
            repeatHandles.append(rb)  # store for annotation
            s.append(m)

        self.assertEqual(len(s), 8)
        self.assertEqual(str(s.flatten().pitches[0]), 'A2')

        self.assertEqual(features.vectorById(s, 'p20'),
                         [3 / 16, 1 / 16, 0.0, 3 / 16, 1 / 16,
                          0.0, 3 / 16, 1 / 16, 0.0, 3 / 16, 1 / 16, 0.0])
        self.assertEqual([x.nameWithOctave for x in s.flatten().pitches],
                         ['A2', 'B-3', 'A2', 'A2', 'C3', 'C#4', 'C3', 'C3', 'E-3',
                          'E4', 'E-3', 'E-3', 'F#3', 'G4', 'F#3', 'F#3', 'A3',
                          'B-4', 'A3', 'A3', 'C4', 'C#5', 'C4', 'C4', 'E-4', 'E5',
                          'E-4', 'E-4', 'F#4', 'G5', 'F#4', 'F#4'])
        # s.show()

        s1 = s.expandRepeats()
        # s1.show()

        self.assertEqual(len(s1), 18)
        # first bar is an A, but repeat is zero, will be removed
        self.assertEqual(str(s1.flatten().pitches[0]), 'C3')

        self.assertEqual(features.vectorById(s1, 'p20'),
                         [15 * (1 / 36), 5 / 36, 0.0, 0.0, 0.0, 0.0,
                          1 / 12, 1 / 36, 0.0, 1 / 4, 1 / 12, 0.0])

        self.assertEqual([x.nameWithOctave for x in s1.flatten().pitches],
                         ['C3', 'C#4', 'C3', 'C3', 'E-3', 'E4', 'E-3',
                          'E-3', 'E-3', 'E4', 'E-3', 'E-3', 'E-3', 'E4',
                          'E-3', 'E-3', 'F#3', 'G4', 'F#3', 'F#3', 'F#3',
                          'G4', 'F#3', 'F#3', 'F#3', 'G4', 'F#3', 'F#3',
                          'F#3', 'G4', 'F#3', 'F#3', 'F#3', 'G4', 'F#3', 'F#3',
                          'C4', 'C#5', 'C4', 'C4', 'E-4', 'E5', 'E-4', 'E-4', 'E-4',
                          'E5', 'E-4', 'E-4', 'E-4', 'E5', 'E-4', 'E-4', 'F#4', 'G5',
                          'F#4', 'F#4', 'F#4', 'G5', 'F#4', 'F#4', 'F#4', 'G5', 'F#4',
                          'F#4', 'F#4', 'G5', 'F#4', 'F#4', 'F#4', 'G5', 'F#4', 'F#4'])

        # s1.show()

    def testRepeatExpressionValidText(self):
        rm = repeat.Coda()
        self.assertTrue(rm.isValidText('coda'))
        self.assertTrue(rm.isValidText('Coda'))
        self.assertTrue(rm.isValidText('TO Coda'))
        self.assertFalse(rm.isValidText('D.C.'))

        rm = repeat.Segno()
        self.assertTrue(rm.isValidText('segno  '))
        self.assertTrue(rm.isValidText('segNO  '))

        rm = repeat.Fine()
        self.assertTrue(rm.isValidText('FINE'))
        self.assertTrue(rm.isValidText('fine'))
        self.assertFalse(rm.isValidText('segno'))

        rm = repeat.DaCapo()
        self.assertTrue(rm.isValidText('DC'))
        self.assertTrue(rm.isValidText('d.c.'))
        self.assertTrue(rm.isValidText('d. c.   '))
        self.assertFalse(rm.isValidText('d. c. al capo'))

        rm = repeat.DaCapoAlFine()
        self.assertTrue(rm.isValidText('d.c. al fine'))
        self.assertTrue(rm.isValidText('da capo al fine'))

        rm = repeat.DaCapoAlCoda()
        self.assertTrue(rm.isValidText('da capo al coda'))

        rm = repeat.DalSegnoAlFine()
        self.assertTrue(rm.isValidText('d.s. al fine'))
        self.assertTrue(rm.isValidText('dal segno al fine'))

        rm = repeat.DalSegnoAlCoda()
        self.assertTrue(rm.isValidText('d.s. al coda'))
        self.assertTrue(rm.isValidText('dal segno al coda'))

    def testRepeatExpressionOnStream(self):
        GEX = m21ToXml.GeneralObjectExporter()

        template = stream.Stream()
        for i in range(5):
            m = stream.Measure()
            template.append(m)
        s = copy.deepcopy(template)
        s[3].insert(0, repeat.DaCapo())
        self.assertEqual(len(s[repeat.DaCapo]), 1)

        raw = GEX.parse(s).decode('utf-8')

        self.assertGreater(raw.find('Da Capo'), 0, raw)

        # can do the same thing starting form a text expression
        s = copy.deepcopy(template)
        s[0].timeSignature = meter.TimeSignature('4/4')
        s[3].insert(0, expressions.TextExpression('da capo'))
        self.assertEqual(len(s[repeat.DaCapo]), 0)

        raw = GEX.parse(s).decode('utf-8')
        self.assertGreater(raw.find('da capo'), 0, raw)

        s2 = converter.parse(raw)
        # now, reconverted from the musicxml, we have a RepeatExpression
        self.assertEqual(len(s2.flatten().getElementsByClass(repeat.DaCapo)), 1)

        # s2.show('t')
        # s2.show()

    def testExpandDaCapoA(self):
        # test one back repeat at end of a measure
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        m2 = stream.Measure()
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        m2.leftBarline = bar.Repeat(direction='start')
        rb = bar.Repeat(direction='end')
        m2.rightBarline = rb
        m3 = stream.Measure()
        m3.repeatAppend(note.Note('g4', type='half'), 2)
        m3.append(repeat.DaCapo())
        m4 = stream.Measure()
        m4.repeatAppend(note.Note('a4', type='half'), 2)

        s = stream.Part()
        s.append([m1, m2, m3, m4])
        ex = repeat.Expander(s)
        self.assertTrue(ex._daCapoIsCoherent())
        self.assertEqual(ex._daCapoOrSegno(), repeat.DaCapo)

        # test incorrect da capo
        sAlt1 = copy.deepcopy(s)
        sAlt1[1].append(repeat.DaCapoAlFine())
        ex = repeat.Expander(sAlt1)
        self.assertFalse(ex._daCapoIsCoherent())
        # rejected here b/c there is more than one
        self.assertEqual(ex._daCapoOrSegno(), None)

        # a da capo with a coda is not valid
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        m2 = stream.Measure()
        m2.append(repeat.Coda())
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        m3 = stream.Measure()
        m3.repeatAppend(note.Note('g4', type='half'), 2)
        m3.append(repeat.DaCapo())
        m4 = stream.Measure()
        m4.repeatAppend(note.Note('a4', type='half'), 2)

        s = stream.Part()
        s.append([m1, m2, m3, m4])
        ex = repeat.Expander(s)
        self.assertFalse(ex._daCapoIsCoherent())
        self.assertEqual(ex._daCapoOrSegno(), repeat.DaCapo)

    def testRemoveRepeatExpressions(self):
        s = stream.Part()
        m1 = stream.Measure()
        m2 = stream.Measure()
        m3 = stream.Measure()
        m3.append(repeat.DaCapo())
        s.append([m1, m2, m3])
        ex = repeat.Expander(s)
        self.assertTrue(ex.isExpandable())
        self.assertEqual(ex.getRepeatExpressionIndex(s, 'DaCapo'), [2])

        ex._stripRepeatExpressions(m3)
        ex = repeat.Expander(s)
        self.assertFalse(ex.isExpandable())

        s = stream.Part()
        m1 = stream.Measure()
        m1.append(repeat.Segno())
        m1.append(repeat.Coda())
        m2 = stream.Measure()
        m3 = stream.Measure()
        m3.append(repeat.Coda())
        m3.append(repeat.DaCapoAlCoda())
        s.append([m1, m2, m3])
        ex = repeat.Expander(s)
        self.assertEqual(ex.getRepeatExpressionIndex(s, repeat.Segno), [0])
        self.assertEqual(ex.getRepeatExpressionIndex(s, 'Segno'), [0])
        self.assertEqual(ex.getRepeatExpressionIndex(s, 'Coda'), [0, 2])
        self.assertEqual(ex.getRepeatExpressionIndex(s, 'DaCapoAlCoda'), [2])

        ex._stripRepeatExpressions(s)  # entire part works too
        ex = repeat.Expander(s)
        self.assertFalse(ex.isExpandable())

        # case where a d.c. statement is placed at the end of bar that is repeated
        m1 = stream.Measure()
        m1.insert(4, repeat.Coda('To Coda'))
        m2 = stream.Measure()
        m3 = stream.Measure()
        m3.leftBarline = bar.Repeat(direction='start')
        m3.rightBarline = bar.Repeat(direction='end')
        m3.insert(4, repeat.DaCapoAlCoda())
        m4 = stream.Measure()
        m5 = stream.Measure()
        m5.append(repeat.Coda('Coda'))
        s = stream.Part()
        s.append([m1, m2, m3, m4, m5])
        ex = repeat.Expander(s)
        self.assertEqual(ex.getRepeatExpressionIndex(s, repeat.Coda), [0, 4])
        self.assertEqual(ex.getRepeatExpressionIndex(s, repeat.DaCapoAlCoda), [2])

        dummy = ex.process()
        # dummy.show()

    def testExpandSimplestPart(self):

        p = stream.Part()
        m = stream.Measure(number=1)
        p.append(m)
        p1 = p.expandRepeats()
        self.assertIsInstance(p1, stream.Part)
        self.assertEqual(len(p1), 1)
        self.assertIsInstance(p1[0], stream.Measure)
        self.assertEqual(p1[0].number, 1)

        s = stream.Score()
        s.insert(0, p)
        s1 = s.expandRepeats()
        self.assertIsInstance(s1, stream.Score)
        self.assertIsInstance(s1[0], stream.Part)

    def testExpandRepeatExpressionA(self):

        # test one back repeat at end of a measure



        # a da capo al fine without a fine is not valid
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        m2 = stream.Measure()
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        m3 = stream.Measure()
        m3.repeatAppend(note.Note('g4', type='half'), 2)
        m3.append(repeat.DaCapoAlFine())
        m4 = stream.Measure()
        m4.repeatAppend(note.Note('a4', type='half'), 2)

        s = stream.Part()
        s.append([m1, m2, m3, m4])
        ex = repeat.Expander(s)
        self.assertFalse(ex._daCapoIsCoherent())
        self.assertEqual(ex._daCapoOrSegno(), repeat.DaCapo)

        # has both da capo and da segno
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        m1.append(repeat.DaCapoAlFine())
        m2 = stream.Measure()
        m1.append(repeat.DalSegnoAlCoda())
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        s = stream.Part()
        s.append([m1, m2])
        ex = repeat.Expander(s)
        self.assertFalse(ex._daCapoIsCoherent())
        self.assertEqual(ex._daCapoOrSegno(), None)

        # segno alone
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        m2 = stream.Measure()
        m1.append(repeat.DalSegnoAlCoda())
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        s = stream.Part()
        s.append([m1, m2])
        ex = repeat.Expander(s)
        self.assertFalse(ex._daCapoIsCoherent())
        self.assertEqual(ex._daCapoOrSegno(), repeat.Segno)
        self.assertFalse(ex._dalSegnoIsCoherent())

        # if nothing, will return None
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        s = stream.Part()
        s.append([m1])
        ex = repeat.Expander(s)
        self.assertEqual(ex._daCapoOrSegno(), None)

    def testExpandRepeatExpressionB(self):

        # test one back repeat at end of a measure



        # simple da capo alone
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        m2 = stream.Measure()
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        m3 = stream.Measure()
        m3.repeatAppend(note.Note('g4', type='half'), 2)
        m3.append(repeat.DaCapo())
        m4 = stream.Measure()
        m4.repeatAppend(note.Note('a4', type='half'), 2)
        s = stream.Part()
        s.append([m1, m2, m3, m4])
        self.assertEqual(len(s.getElementsByClass(stream.Measure)), 4)
        # s.show()
        ex = repeat.Expander(s)
        post = ex.process()
        # three measure repeat
        self.assertEqual(len(post.getElementsByClass(stream.Measure)), 7)
        self.assertEqual([x.nameWithOctave for x in post.flatten().pitches],
                         ['C4', 'C4', 'E4', 'E4', 'G4', 'G4', 'C4', 'C4',
                          'E4', 'E4', 'G4', 'G4', 'A4', 'A4'])

    def testExpandRepeatExpressionC(self):
        # da capo al fine
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        m2 = stream.Measure()
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        m2.append(repeat.Fine())
        m3 = stream.Measure()
        m3.repeatAppend(note.Note('g4', type='half'), 2)
        m3.append(repeat.DaCapoAlFine())
        m4 = stream.Measure()
        m4.repeatAppend(note.Note('a4', type='half'), 2)
        s = stream.Part()
        s.append([m1, m2, m3, m4])
        self.assertEqual(len(s.getElementsByClass(stream.Measure)), 4)
        # s.show()
        ex = repeat.Expander(s)
        post = ex.process()
        # post.show()
        # three measure repeat
        self.assertEqual(len(post.getElementsByClass(stream.Measure)), 5)
        self.assertEqual([x.nameWithOctave for x in post.flatten().pitches],
                         ['C4', 'C4', 'E4', 'E4', 'G4', 'G4', 'C4', 'C4', 'E4', 'E4'])

    def testExpandRepeatExpressionD(self):
        # da capo al coda
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        m2 = stream.Measure()
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        m2.append(repeat.Coda('to coda'))
        m3 = stream.Measure()
        m3.repeatAppend(note.Note('g4', type='half'), 2)
        m3.append(repeat.DaCapoAlCoda())
        m4 = stream.Measure()
        m4.append(repeat.Coda())
        m4.repeatAppend(note.Note('a4', type='half'), 2)
        m5 = stream.Measure()
        m5.repeatAppend(note.Note('b4', type='half'), 2)

        s = stream.Part()
        s.append([m1, m2, m3, m4, m5])
        self.assertEqual(len(s.getElementsByClass(stream.Measure)), 5)
        # s.show()
        ex = repeat.Expander(s)
        post = ex.process()
        # post.show()
        # three measure repeat
        self.assertEqual(len(post.getElementsByClass(stream.Measure)), 7)
        self.assertEqual([x.nameWithOctave for x in post.flatten().pitches],
                         ['C4', 'C4', 'E4', 'E4', 'G4', 'G4', 'C4', 'C4',
                          'E4', 'E4', 'A4', 'A4', 'B4', 'B4'])

    def testExpandRepeatExpressionE(self):
        # dal segno simple
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        m2 = stream.Measure()
        m2.append(repeat.Segno())
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        m3 = stream.Measure()
        m3.repeatAppend(note.Note('g4', type='half'), 2)
        m4 = stream.Measure()
        m4.repeatAppend(note.Note('a4', type='half'), 2)
        m3.append(repeat.DalSegno())

        s = stream.Part()
        s.append([m1, m2, m3, m4])
        # s.show()
        self.assertEqual(len(s.getElementsByClass(stream.Measure)), 4)
        # s.show()
        ex = repeat.Expander(s)
        post = ex.process()
        # post.show()
        # three measure repeat
        self.assertEqual(len(post.getElementsByClass(stream.Measure)), 6)
        self.assertEqual([x.nameWithOctave for x in post.flatten().pitches],
                         ['C4', 'C4', 'E4', 'E4', 'G4', 'G4', 'E4', 'E4',
                          'G4', 'G4', 'A4', 'A4'])

    def testExpandRepeatExpressionF(self):
        # dal segno al fine
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        m2 = stream.Measure()
        m2.append(repeat.Segno())
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        m3 = stream.Measure()
        m3.repeatAppend(note.Note('g4', type='half'), 2)
        m3.append(repeat.Fine())
        m4 = stream.Measure()
        m4.repeatAppend(note.Note('a4', type='half'), 2)
        m4.append(repeat.DalSegnoAlFine())
        m5 = stream.Measure()
        m5.repeatAppend(note.Note('b4', type='half'), 2)

        s = stream.Part()
        s.append([m1, m2, m3, m4, m5])
        # s.show()
        self.assertEqual(len(s.getElementsByClass(stream.Measure)), 5)
        ex = repeat.Expander(s)
        post = ex.process()
        # post.show()
        # three measure repeat
        self.assertEqual(len(post.getElementsByClass(stream.Measure)), 6)
        self.assertEqual([x.nameWithOctave for x in post.flatten().pitches],
                         ['C4', 'C4', 'E4', 'E4', 'G4', 'G4', 'A4', 'A4',
                          'E4', 'E4', 'G4', 'G4'])

    def testExpandRepeatExpressionG(self):
        # dal segno al coda
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)
        m2 = stream.Measure()
        m2.append(repeat.Segno())
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        m2.append(repeat.Coda('to coda'))
        m3 = stream.Measure()
        m3.repeatAppend(note.Note('e4', type='half'), 2)

        m4 = stream.Measure()
        m4.repeatAppend(note.Note('g4', type='half'), 2)
        m4.append(repeat.DalSegnoAlCoda())
        m5 = stream.Measure()
        m5.repeatAppend(note.Note('g4', type='half'), 2)
        m6 = stream.Measure()
        m6.append(repeat.Coda('CODA'))
        m6.repeatAppend(note.Note('a4', type='half'), 2)
        m7 = stream.Measure()
        m7.repeatAppend(note.Note('b4', type='half'), 2)

        s = stream.Part()
        s.append([m1, m2, m3, m4, m5, m6, m7])
        # s.show()
        self.assertEqual(len(s.getElementsByClass(stream.Measure)), 7)
        ex = repeat.Expander(s)
        post = ex.process()
        # post.show()
        # three measure repeat
        self.assertEqual(len(post.getElementsByClass(stream.Measure)), 7)
        self.assertEqual([x.nameWithOctave for x in post.flatten().pitches],
                         ['C4', 'C4', 'E4', 'E4', 'E4', 'E4', 'G4', 'G4',
                          'E4', 'E4', 'A4', 'A4', 'B4', 'B4'])

    def testExpandRepeatExpressionH(self):
        # test one back repeat at end of a measure
        # simple da capo alone
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)

        m2 = stream.Measure()
        m2.repeatAppend(note.Note('e4', type='half'), 2)

        m3 = stream.Measure()
        m3.leftBarline = bar.Repeat(direction='start')
        m3.repeatAppend(note.Note('g4', type='half'), 2)
        m3.rightBarline = bar.Repeat(direction='end')

        m4 = stream.Measure()
        m4.repeatAppend(note.Note('a4', type='half'), 2)
        dcHandle = repeat.DaCapo('D.C.')
        m4.append(dcHandle)

        m5 = stream.Measure()
        m5.repeatAppend(note.Note('b4', type='half'), 2)

        s = stream.Part()
        s.append([m1, m2, m3, m4, m5])
        self.assertEqual(len(s.getElementsByClass(stream.Measure)), 5)
        # s.show()
        ex = repeat.Expander(s)
        post = ex.process()
        # post.show()
        # three measure repeat
        self.assertEqual(len(post.getElementsByClass(stream.Measure)), 10)
        self.assertEqual([x.nameWithOctave for x in post.flatten().pitches],
                         ['C4', 'C4', 'E4', 'E4', 'G4', 'G4', 'G4', 'G4', 'A4',
                          'A4', 'C4', 'C4', 'E4', 'E4', 'G4', 'G4', 'A4', 'A4',
                          'B4', 'B4'])

        # test changing repeat after jump
        dcHandle.repeatAfterJump = True
        ex = repeat.Expander(s)
        post = ex.process()
        # post.show()
        # three measure repeat
        self.assertEqual(len(post.getElementsByClass(stream.Measure)), 11)
        self.assertEqual([x.nameWithOctave for x in post.flatten().pitches],
                         ['C4', 'C4', 'E4', 'E4', 'G4', 'G4', 'G4', 'G4', 'A4',
                          'A4', 'C4', 'C4', 'E4', 'E4', 'G4', 'G4', 'G4', 'G4',
                          'A4', 'A4', 'B4', 'B4'])

    def testExpandRepeatExpressionI(self):
        # test one back repeat at end of a measure
        # simple da capo alone
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4', type='half'), 2)

        m2 = stream.Measure()
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        m2.append(repeat.Coda('to coda'))

        m3 = stream.Measure()
        m3.leftBarline = bar.Repeat(direction='start')
        m3.repeatAppend(note.Note('g4', type='half'), 2)
        dcHandle = repeat.DaCapoAlCoda()
        m3.append(dcHandle)
        m3.rightBarline = bar.Repeat(direction='end')

        m4 = stream.Measure()
        m4.repeatAppend(note.Note('a4', type='half'), 2)

        m5 = stream.Measure()
        m5.append(repeat.Coda())
        m5.repeatAppend(note.Note('b4', type='half'), 2)

        s = stream.Part()
        s.append([m1, m2, m3, m4, m5])
        self.assertEqual(len(s.getElementsByClass(stream.Measure)), 5)
        # s.show()
        # s.expandRepeats().show()
        ex = repeat.Expander(s)
        post = ex.process()
        # post.show()
        self.assertEqual(len(post.getElementsByClass(stream.Measure)), 7)
        self.assertEqual([x.nameWithOctave for x in post.flatten().pitches],
                         ['C4', 'C4', 'E4', 'E4', 'G4', 'G4', 'G4', 'G4',
                          'C4', 'C4', 'E4', 'E4', 'B4', 'B4'])

    def testExpandRepeatExpressionJ(self):
        # test one back repeat at end of a measure
        # simple da capo alone
        m1 = stream.Measure()
        m1.append(repeat.Segno())
        m1.repeatAppend(note.Note('c4', type='half'), 2)

        m2 = stream.Measure()
        m2.repeatAppend(note.Note('e4', type='half'), 2)
        m2.append(repeat.Coda('to coda'))

        m3 = stream.Measure()
        m3.leftBarline = bar.Repeat(direction='start')
        m3.repeatAppend(note.Note('g4', type='half'), 2)
        dsHandle = repeat.DalSegnoAlCoda()
        m3.append(dsHandle)
        m3.rightBarline = bar.Repeat(direction='end')

        m4 = stream.Measure()
        m4.repeatAppend(note.Note('a4', type='half'), 2)

        m5 = stream.Measure()
        m5.append(repeat.Coda())
        m5.repeatAppend(note.Note('b4', type='half'), 2)

        s = stream.Part()
        s.append([m1, m2, m3, m4, m5])
        # add an instrument
        s.insert(0, instrument.Trumpet())
        s.insert(0, spanner.Slur(m1[1], m2[1]))

        self.assertEqual(len(s.getElementsByClass(stream.Measure)), 5)

        # s.show()
        # ex = repeat.Expander(s)
        # post = ex.process()
        post = s.expandRepeats()
        # post.show()
        self.assertEqual(len(post.getElementsByClass(stream.Measure)), 7)
        self.assertEqual([x.nameWithOctave for x in post.flatten().pitches],
                         ['C4', 'C4', 'E4', 'E4', 'G4', 'G4', 'G4', 'G4',
                          'C4', 'C4', 'E4', 'E4', 'B4', 'B4'])

        # instrument is copied in Stream
        self.assertEqual(post.getElementsByClass(instrument.Instrument).first().instrumentName,
                         'Trumpet')

    def testExpandRepeatsImportedA(self):
        '''
        tests expanding repeats in a piece with repeats mid-measure

        Also has grace notes, so it tests our importing of grace notes
        '''
        s = corpus.parse('ryansMammoth/BanjoReel')
        # s.show('text')
        self.assertEqual(len(s.parts), 1)
        self.assertEqual(len(s.parts[0].getElementsByClass(stream.Measure)), 11)
        self.assertEqual(len(s.parts[0].flatten().notes), 58)

        bars = s.parts[0][bar.Barline]
        self.assertEqual(len(bars), 3)

        s2 = s.expandRepeats()
        # s2.show('text')

        self.assertEqual(len(s2.parts[0].getElementsByClass(stream.Measure)), 20)
        self.assertEqual(len(s2.parts[0].recurse().notes), 105)

    def testExpandRepeatsImportedB(self):
        s = corpus.parse('GlobeHornpipe')
        self.assertEqual(len(s.parts), 1)
        self.assertEqual(len(s.parts[0].getElementsByClass(stream.Measure)), 18)
        self.assertEqual(len(s.parts[0].flatten().notes), 125)

        s2 = s.expandRepeats()
        # s2.show()
        self.assertEqual(len(s2.parts[0].getElementsByClass(stream.Measure)), 36)
        self.assertEqual(len(s2.parts[0].flatten().notes), 250)
        # make sure barlines are stripped
        bars = s2.parts[0].flatten().getElementsByClass(bar.Repeat)
        self.assertEqual(len(bars), 0)

        # self.assertEqual(len(s2.parts[0].flatten().notes), 111)

    def testExpandRepeatsImportedC(self):
        s = converter.parse(testPrimitive.repeatExpressionsA)
        self.assertEqual(len(s['RepeatExpression']), 3)

        s = converter.parse(testPrimitive.repeatExpressionsB)
        self.assertEqual(len(s['RepeatExpression']), 3)

        # s.show()

    def testRepeatsEndingsA(self):
        # this has repeat brackets
        # these are stored in bar objects as ending tags,
        # given at start and end
        #         <ending number="2" type="discontinue"/>

        s = converter.parse(testPrimitive.repeatBracketsA)
        GEX = m21ToXml.GeneralObjectExporter()

        raw = GEX.parse(s)

        self.assertGreater(raw.find(b'<repeat direction='), 1)
        self.assertGreater(raw.find(b'<ending number="1" type="start"'), 1)
        self.assertGreater(raw.find(b'<ending number="1" type="stop"'), 1)
        self.assertGreater(raw.find(b'<ending number="2" type="start"'), 1)
        self.assertGreater(raw.find(b'<ending number="2" type="stop"'), 1)

        # TODO: after calling .musicxml, repeat brackets are getting lost
        # s.show()
        raw = GEX.parse(s)

        self.assertGreater(raw.find(b'<repeat direction='), 1)
        self.assertGreater(raw.find(b'<ending number="1" type="start"'), 1)
        self.assertGreater(raw.find(b'<ending number="1" type="stop"'), 1)
        self.assertGreater(raw.find(b'<ending number="2" type="start"'), 1)
        self.assertGreater(raw.find(b'<ending number="2" type="stop"'), 1)

        s1 = copy.deepcopy(s)
        # s.show()

        # s1.show()
        ex = repeat.Expander(s1.parts[0])
        self.assertEqual(len(ex._repeatBrackets), 2)

    def testRepeatEndingsB(self):
        p = stream.Part()
        m1 = stream.Measure()
        m1.append(note.Note('c4', type='whole'))
        m2 = stream.Measure()
        m2.append(note.Note('d4', type='whole'))
        m3 = stream.Measure()
        m3.append(note.Note('e4', type='whole'))
        m4 = stream.Measure()
        m4.append(note.Note('f4', type='whole'))
        m5 = stream.Measure()
        m5.append(note.Note('g4', type='whole'))

        p.append([m1, m2, m3, m4, m5])
        rb1 = spanner.RepeatBracket([m2, m3], number=1)
        m3.rightBarline = bar.Repeat()
        self.assertTrue(rb1.hasSpannedElement(m2))
        self.assertTrue(rb1.hasSpannedElement(m3))
        p.append(rb1)

        rb2 = spanner.RepeatBracket(m4, number=2)
        self.assertTrue(rb2.hasSpannedElement(m4))
        m4.rightBarline = bar.Repeat()
        p.append(rb2)

        ex = repeat.Expander(p)
        self.assertTrue(ex._repeatBracketsAreCoherent())

        # if we change the numbers no longer coherent
        rb2.number = 30
        self.assertFalse(ex._repeatBracketsAreCoherent())
        rb2.number = 2
        self.assertTrue(ex._repeatBracketsAreCoherent())
        rb1.number = 2
        rb2.number = 1
        self.assertFalse(ex._repeatBracketsAreCoherent())

        rb1.number = 1
        rb2.number = 2
        self.assertTrue(ex._repeatBracketsAreCoherent())

        self.assertTrue(ex.repeatBarsAreCoherent())

        # p.show()

    def testRepeatEndingsB2(self):
        p = stream.Part()
        m1 = stream.Measure()
        m1.append(note.Note('c4', type='whole'))
        m2 = stream.Measure()
        m2.append(note.Note('d4', type='whole'))
        m3 = stream.Measure()
        m3.append(note.Note('e4', type='whole'))
        m4 = stream.Measure()
        m4.append(note.Note('f4', type='whole'))
        m5 = stream.Measure()
        m5.append(note.Note('g4', type='whole'))

        p.append([m1, m2, m3, m4, m5])
        rb1 = spanner.RepeatBracket([m2, m3], number=1)
        m3.rightBarline = bar.Repeat()
        self.assertTrue(rb1.hasSpannedElement(m2))
        self.assertTrue(rb1.hasSpannedElement(m3))
        p.append(rb1)

        rb2 = spanner.RepeatBracket(m4, number=2)
        self.assertTrue(rb2.hasSpannedElement(m4))
        m4.rightBarline = bar.Repeat()
        p.append(rb2)

        ex = repeat.Expander(p)
        self.assertTrue(ex._repeatBracketsAreCoherent())

        # if we change the numbers no longer coherent
        rb2.number = 30
        self.assertFalse(ex._repeatBracketsAreCoherent())
        rb2.number = 2
        self.assertTrue(ex._repeatBracketsAreCoherent())
        rb1.number = 2
        rb2.number = 1
        self.assertFalse(ex._repeatBracketsAreCoherent())

        rb1.number = 1
        rb2.number = 2
        self.assertTrue(ex._repeatBracketsAreCoherent())

        self.assertTrue(ex.repeatBarsAreCoherent())

        # p.show()

    def testRepeatEndingsC(self):
        p = stream.Part()
        m1 = stream.Measure()
        m1.append(note.Note('c4', type='whole'))
        m2 = stream.Measure()
        m2.append(note.Note('d4', type='whole'))
        m3 = stream.Measure()
        m3.append(note.Note('e4', type='whole'))
        m4 = stream.Measure()
        m4.append(note.Note('f4', type='whole'))
        m5 = stream.Measure()
        m5.append(note.Note('g4', type='whole'))

        p.append([m1, m2, m3, m4, m5])
        rb1 = spanner.RepeatBracket([m2, m3], number=1)
        p.append(rb1)
        # one repeat bracket w/o a repeat bar; makes no sense, should be
        # rejected
        ex = repeat.Expander(p)
        self.assertFalse(ex._repeatBracketsAreCoherent())

        m3.rightBarline = bar.Repeat()
        # coherent after setting the barline
        ex = repeat.Expander(p)
        self.assertTrue(ex._repeatBracketsAreCoherent())

        # a second repeat bracket need not have a repeat ending
        rb2 = spanner.RepeatBracket(m4, number=2)
        p.append(rb2)
        ex = repeat.Expander(p)
        self.assertTrue(ex._repeatBracketsAreCoherent())

        m4.rightBarline = bar.Repeat()
        ex = repeat.Expander(p)
        self.assertTrue(ex._repeatBracketsAreCoherent())

    def testRepeatEndingsD(self):
        p = stream.Part()
        m1 = stream.Measure(number=1)
        m1.append(note.Note('c4', type='whole'))
        m2 = stream.Measure(number=2)
        m2.append(note.Note('d4', type='whole'))
        m3 = stream.Measure(number=3)
        m3.append(note.Note('e4', type='whole'))
        m4 = stream.Measure(number=4)
        m4.append(note.Note('f4', type='whole'))
        m5 = stream.Measure(number=5)
        m5.append(note.Note('g4', type='whole'))

        p.append([m1, m2, m3, m4, m5])
        rb1 = spanner.RepeatBracket([m2, m3], number=1)
        p.append(rb1)
        m3.rightBarline = bar.Repeat()

        unused_ex = repeat.Expander(p)
        # self.assertTrue(ex._repeatBracketsAreCoherent())
        # overlapping at m3
        rb2 = spanner.RepeatBracket([m3, m4], number=2)
        p.append(rb2)
        m4.rightBarline = bar.Repeat()
        # p.show()
        # even with the right repeat, these are overlapping and should fail
        ex = repeat.Expander(p)
        self.assertFalse(ex._repeatBracketsAreCoherent())
        # can fix overlap even after insertion
        # rb2.replaceSpannedElement(m3, m5)
        # self.assertTrue(ex._repeatBracketsAreCoherent())

    def testRepeatEndingsE(self):
        '''
        Expanding two endings (1, 2, then 3) without a start repeat
        '''
        p = stream.Part()
        m1 = stream.Measure()
        m1.append(note.Note('c4', type='whole'))
        m2 = stream.Measure()
        m2.append(note.Note('d4', type='whole'))
        m3 = stream.Measure()
        m3.append(note.Note('e4', type='whole'))
        m4 = stream.Measure()
        m4.append(note.Note('f4', type='whole'))
        m5 = stream.Measure()
        m5.append(note.Note('g4', type='whole'))

        p.append([m1, m2, m3, m4, m5])
        rb1 = spanner.RepeatBracket([m2, m3], number='1,2')
        m3.rightBarline = bar.Repeat()
        p.append(rb1)
        rb2 = spanner.RepeatBracket(m4, number=3)
        # The second ending might not have a repeat sign.
        p.append(rb2)
        # p.show()

        ex = repeat.Expander(p)
        self.assertTrue(ex._repeatBracketsAreCoherent())
        self.assertTrue(ex.isExpandable())

        self.assertEqual(ex.findInnermostRepeatIndices(p), [0, 1, 2])
        # get groups of brackets; note that this does not get the end
        post = ex._groupRepeatBracketIndices(p)
        self.assertEqual(post[0]['measureIndices'], [1, 2, 3])

    def testRepeatEndingsF(self):
        '''
        Two sets of two endings (1, 2, then 3) without a start repeat
        '''
        p = stream.Part()
        m1 = stream.Measure()
        m1.append(note.Note('c4', type='whole'))
        m2 = stream.Measure()
        m2.append(note.Note('d4', type='whole'))
        m3 = stream.Measure()
        m3.append(note.Note('e4', type='whole'))
        m4 = stream.Measure()
        m4.append(note.Note('f4', type='whole'))
        m5 = stream.Measure()
        m5.append(note.Note('g4', type='whole'))
        m6 = stream.Measure()
        m6.append(note.Note('a4', type='whole'))
        m7 = stream.Measure()
        m7.append(note.Note('b4', type='whole'))
        m8 = stream.Measure()
        m8.append(note.Note('c5', type='whole'))

        p.append([m1, m2, m3, m4, m5, m6, m7, m8])
        rb1 = spanner.RepeatBracket([m2, m3], number='1,2')
        m3.rightBarline = bar.Repeat()
        p.append(rb1)
        rb2 = spanner.RepeatBracket(m4, number=3)
        p.append(rb2)

        # second group
        m5.leftBarline = bar.Repeat()
        m6.rightBarline = bar.Repeat()
        rb3 = spanner.RepeatBracket(m6, number='1-3')
        p.append(rb3)
        m7.rightBarline = bar.Repeat()
        rb4 = spanner.RepeatBracket(m7, number=4)
        p.append(rb4)
        rb5 = spanner.RepeatBracket(m8, number=5)
        p.append(rb5)
        # The second ending might not have a repeat sign.
        # p.show()

        ex = repeat.Expander(p)
        self.assertTrue(ex._repeatBracketsAreCoherent())
        self.assertTrue(ex.isExpandable())

        self.assertEqual(ex.findInnermostRepeatIndices(p[3:]), [1, 2])
#         # get groups of brackets
        # returns a list of dictionaries
        post = ex._groupRepeatBracketIndices(p)
        self.assertEqual(post[0]['measureIndices'], [1, 2, 3])
        self.assertEqual(post[1]['measureIndices'], [5, 6, 7])

    def testRepeatEndingsG(self):
        '''
        Two sets of two endings (1, 2, then 3) without a start repeat
        '''
        p = stream.Part()
        m1 = stream.Measure()
        m1.append(note.Note('c4', type='whole'))
        m2 = stream.Measure()
        m2.append(note.Note('d4', type='whole'))
        m3 = stream.Measure()
        m3.append(note.Note('e4', type='whole'))
        m4 = stream.Measure()
        m4.append(note.Note('f4', type='whole'))
        m5 = stream.Measure()
        m5.append(note.Note('g4', type='whole'))
        m6 = stream.Measure()
        m6.append(note.Note('a4', type='whole'))
        m7 = stream.Measure()
        m7.append(note.Note('b4', type='whole'))
        m8 = stream.Measure()
        m8.append(note.Note('c5', type='whole'))

        p.append([m1, m2, m3, m4, m5])
        # p.append([m1, m2, m3, m4, m5, m6, m7, m8])
        rb1 = spanner.RepeatBracket([m2, m3], number='1,2')
        m3.rightBarline = bar.Repeat()
        p.append(rb1)
        rb2 = spanner.RepeatBracket(m4, number=3)
        p.append(rb2)
        # p.show()

        ex = repeat.Expander(p)
        self.assertTrue(ex.isExpandable())
        post = ex.process()
        # post.show()
        self.assertEqual(len(post), 9)
        self.assertEqual([n.name for n in post.flatten().notes],
                         ['C', 'D', 'E', 'C', 'D', 'E', 'C', 'F', 'G'])
        # post.show()

    def testRepeatEndingsH(self):
        '''
        Two sets of two endings (1, 2, then 3) without a start repeat
        '''
        p = stream.Part()
        m1 = stream.Measure(number=1)
        m1.append(note.Note('c4', type='whole'))
        m2 = stream.Measure(number=2)
        m2.append(note.Note('d4', type='whole'))
        m3 = stream.Measure(number=3)
        m3.append(note.Note('e4', type='whole'))
        m4 = stream.Measure(number=4)
        m4.append(note.Note('f4', type='whole'))
        m5 = stream.Measure(number=5)
        m5.append(note.Note('g4', type='whole'))
        m6 = stream.Measure(number=6)
        m6.append(note.Note('a4', type='whole'))
        m7 = stream.Measure(number=7)
        m7.append(note.Note('b4', type='whole'))
        m8 = stream.Measure(number=8)
        m8.append(note.Note('c5', type='whole'))

        p.append([m1, m2, m3, m4, m5, m6, m7, m8])
        rb1 = spanner.RepeatBracket([m2, m3], number='1,2')
        m3.rightBarline = bar.Repeat()
        p.append(rb1)

        rb2 = spanner.RepeatBracket(m4, number=3)
        p.append(rb2)
        m4.rightBarline = bar.Repeat()

        rb3 = spanner.RepeatBracket(m5, number=4)
        p.append(rb3)

        # p.show()
        ex = repeat.Expander(p)
        self.assertTrue(ex.isExpandable())
        post = ex.process()
        environLocal.printDebug(['post process', [n.name for n in post.flatten().notes]])
        # post.show()
        self.assertEqual(len(post), 13)
        self.assertEqual([n.name for n in post.flatten().notes],
                         ['C', 'D', 'E', 'C', 'D', 'E', 'C', 'F', 'C', 'G', 'A', 'B', 'C'])

    def testRepeatEndingsI(self):
        '''
        Two sets of two endings (1, 2, then 3) without a start repeat
        '''
        p = stream.Part()
        m1 = stream.Measure(number=1)
        m1.append(note.Note('c4', type='whole'))
        m2 = stream.Measure(number=2)
        m2.append(note.Note('d4', type='whole'))
        m3 = stream.Measure(number=3)
        m3.append(note.Note('e4', type='whole'))
        m4 = stream.Measure(number=4)
        m4.append(note.Note('f4', type='whole'))
        m5 = stream.Measure(number=5)
        m5.append(note.Note('g4', type='whole'))
        m6 = stream.Measure(number=6)
        m6.append(note.Note('a4', type='whole'))
        m7 = stream.Measure(number=7)
        m7.append(note.Note('b4', type='whole'))
        m8 = stream.Measure(number=8)
        m8.append(note.Note('c5', type='whole'))

        p.append([m1, m2, m3, m4, m5, m6, m7, m8])
        rb1 = spanner.RepeatBracket([m2, m3], number='1,2')
        m3.rightBarline = bar.Repeat()
        p.append(rb1)

        rb2 = spanner.RepeatBracket(m4, number=3)
        p.append(rb2)
        m4.rightBarline = bar.Repeat()

        # second group
        m5.leftBarline = bar.Repeat()
        m6.rightBarline = bar.Repeat()
        rb3 = spanner.RepeatBracket(m6, number='1-3')
        p.append(rb3)
        m7.rightBarline = bar.Repeat()
        rb4 = spanner.RepeatBracket(m7, number=4)
        p.append(rb4)
        rb5 = spanner.RepeatBracket(m8, number=5)
        p.append(rb5)
        # The second ending might not have a repeat sign.
        # p.show()

        # p.show()
        ex = repeat.Expander(p)
        self.assertTrue(ex.isExpandable())
        post = ex.process()
        # post.show()
#
        self.assertEqual(len(post), 18)
        self.assertEqual([n.name for n in post.flatten().notes],
                         ['C', 'D', 'E', 'C', 'D', 'E', 'C', 'F', 'G', 'A',
                          'G', 'A', 'G', 'A', 'G', 'B', 'G', 'C'])

    def testRepeatEndingsJ(self):
        '''
        Two sets of two endings (1, 2, then 3) without a start repeat
        '''
        p = stream.Part()
        m1 = stream.Measure(number=1)
        m1.append(note.Note('c4', type='whole'))
        m2 = stream.Measure(number=2)
        m2.append(note.Note('d4', type='whole'))
        m3 = stream.Measure(number=3)
        m3.append(note.Note('e4', type='whole'))
        m4 = stream.Measure(number=4)
        m4.append(note.Note('f4', type='whole'))
        m5 = stream.Measure(number=5)
        m5.append(note.Note('g4', type='whole'))
        m6 = stream.Measure(number=6)
        n1 = note.Note('a4', type='half')
        n2 = note.Note('a4', type='half')
        m6.append([n1, n2])
        m7 = stream.Measure(number=7)
        m7.append(note.Note('b4', type='whole'))
        m8 = stream.Measure(number=8)
        m8.append(note.Note('c5', type='whole'))

        m9 = stream.Measure(number=9)
        m9.append(note.Note('d5', type='whole'))
        m10 = stream.Measure(number=10)
        m10.append(note.Note('e5', type='whole'))
        m11 = stream.Measure(number=11)
        m11.append(note.Note('f5', type='whole'))
        m12 = stream.Measure(number=12)
        m12.append(note.Note('g5', type='whole'))

        p.append([m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11, m12])

        rb1 = spanner.RepeatBracket([m2, m3], number='1,2')
        p.append(rb1)
        m3.rightBarline = bar.Repeat()

        rb2 = spanner.RepeatBracket(m4, number=3)
        p.append(rb2)

        # second group
        m5.leftBarline = bar.Repeat()
        m6.leftBarline = bar.Repeat()  # nested repeat
        m6.rightBarline = bar.Repeat()

        rb3 = spanner.RepeatBracket(m7, number='1-3')
        p.append(rb3)
        m7.rightBarline = bar.Repeat()

        rb4 = spanner.RepeatBracket([m8, m10], number='4,5')
        p.append(rb4)
        m10.rightBarline = bar.Repeat()

        rb5 = spanner.RepeatBracket([m11], number='6')
        p.append(rb5)  # not a repeat per se

        # p.show()

        # ex = repeat.Expander(p)
        # self.assertTrue(ex.isExpandable())
        # post = ex.process()
        # post.show()

        post = p.expandRepeats()
        self.assertEqual(len(post), 37)
        # post.show()
        # self.assertEqual(len(post), 18)
        # self.assertEqual([n.name for n in post.flatten().notes],
        #     ['C', 'D', 'E', 'C', 'D', 'E', 'C', 'F', 'G', 'A', 'G', 'A', 'G',
        #      'A', 'G', 'B', 'G', 'C'])

    def testRepeatEndingsImportedA(self):
        s = corpus.parse('ryansMammoth/BanjoReel')
        # s.show()
        firstNotesList = list(s.flatten().notes)
        # [0:16][16:22][0:16][22:27][27:58][27:58]
        expandedByHandList = (firstNotesList[0:16] + firstNotesList[16:22]
                              + firstNotesList[0:16] + firstNotesList[22:27]
                              + firstNotesList[27:58] + firstNotesList[27:58])
        expandedByHandNoteNames = [n.nameWithOctave for n in expandedByHandList]
        ex = repeat.Expander(s.parts[0])
        post = ex.process()
        # post.show()
        # print([n.nameWithOctave for n in post.flatten().notes])
        # post.show()
        secondNotesList = list(post.flatten().notes)
        secondNotesNoteNames = [n.nameWithOctave for n in secondNotesList]
        self.assertEqual(expandedByHandNoteNames, secondNotesNoteNames)

    def testRepeatEndingsImportedB(self):
        # last alternate endings in last bars
        # need to add import from abc
        s = corpus.parse('ryansMammoth/SmugglersReel')
        # s.parts[0].show()
        ex = repeat.Expander(s.parts[0])
        # this is a Stream resulting form getElements
        self.assertEqual(len(ex._repeatBrackets), 2)
        # s.show()
        unused_post = ex.process()
        # post.show()

    def testRepeatEndingsImportedC(self):
        s = converter.parse(testFiles.mysteryReel)
        # s.show()
        post = s.expandRepeats()
        # post.show()
        self.assertEqual(len(post.parts[0]), 32)

        # s = converter.parse(testFiles.hectorTheHero)
        # s.show()
        # post = s.expandRepeats()

    def test_expand_repeats_preserves_name(self):
        # Test case provided by Jacob Tyler Walls on issue #1165
        # https://github.com/cuthbertLab/music21/issues/1165#issuecomment-967293691
        p = converter.parse('tinyNotation: c1 d e f')
        p.measure(2).storeAtEnd(bar.Repeat(direction='end', times=1))
        p.partName = 'my_part_name'
        p.partAbbreviation = 'my_part_abbreviation'
        exp = p.expandRepeats()
        self.assertEqual(exp.partName, 'my_part_name')
        self.assertEqual(exp.partAbbreviation, 'my_part_abbreviation')


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)  # , runTest='testExpandSimplestPart')

