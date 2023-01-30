from __future__ import annotations

import unittest

from music21 import corpus
from music21 import interval
from music21 import note
from music21 import pitch


class Test(unittest.TestCase):

    def testConstructorPitches(self):
        p1 = pitch.Pitch('A4')
        p2 = pitch.Pitch('E5')
        intv = interval.Interval(p1, p2)
        self.assertEqual(intv.name, 'P5')
        self.assertIs(intv.pitchStart, p1)
        self.assertIs(intv.pitchEnd, p2)

        # same with keywords, but reversed
        intv = interval.Interval(pitchStart=p2, pitchEnd=p1)
        self.assertEqual(intv.name, 'P5')
        self.assertEqual(intv.directedName, 'P-5')
        self.assertIs(intv.pitchStart, p2)
        self.assertIs(intv.pitchEnd, p1)

    def testFirst(self):
        n1 = note.Note()
        n2 = note.Note()

        n1.step = 'C'
        n1.octave = 4

        n2.step = 'B'
        n2.octave = 5
        n2.pitch.accidental = pitch.Accidental('-')

        int0 = interval.Interval(noteStart=n1, noteEnd=n2)
        dInt0 = int0.diatonic
        gInt0 = dInt0.generic

        self.assertFalse(gInt0.isDiatonicStep)
        self.assertTrue(gInt0.isSkip)

        n1.pitch.accidental = pitch.Accidental('#')
        int1 = interval.Interval(noteStart=n1, noteEnd=n2)

        # returns music21.interval.ChromaticInterval object
        cInt1 = interval.notesToChromatic(n1, n2)
        self.assertIsInstance(cInt1, interval.ChromaticInterval)
        cInt2 = int1.chromatic  # returns same as cInt1 -- a different way of thinking of things
        self.assertEqual(cInt1.semitones, cInt2.semitones)

        self.assertEqual(int1.simpleNiceName, 'Diminished Seventh')

        self.assertEqual(int1.directedSimpleNiceName, 'Ascending Diminished Seventh')
        self.assertEqual(int1.name, 'd14')
        self.assertEqual(int1.specifier, interval.Specifier.DIMINISHED)

        # returns same as gInt1 -- just a different way of thinking of things
        dInt1 = int1.diatonic
        gInt1 = dInt1.generic

        self.assertEqual(gInt1.directed, 14)
        self.assertEqual(gInt1.undirected, 14)
        self.assertEqual(gInt1.simpleDirected, 7)
        self.assertEqual(gInt1.simpleUndirected, 7)

        self.assertEqual(cInt1.semitones, 21)
        self.assertEqual(cInt1.undirected, 21)
        self.assertEqual(cInt1.mod12, 9)
        self.assertEqual(cInt1.intervalClass, 3)

        n4 = note.Note()
        n4.step = 'D'
        n4.octave = 3
        n4.pitch.accidental = '-'

        # n3 = interval.transposePitch(n4, 'AA8')
        # if n3.pitch.accidental is not None:
        #    print(n3.step, n3.pitch.accidental.name, n3.octave)
        # else:
        #    print(n3.step, n3.octave)
        # print(n3.name)
        # print()

        cI = interval.ChromaticInterval(-14)
        self.assertEqual(cI.semitones, -14)
        self.assertEqual(cI.cents, -1400)
        self.assertEqual(cI.undirected, 14)
        self.assertEqual(cI.mod12, 10)
        self.assertEqual(cI.intervalClass, 2)

        lowB = note.Note()
        lowB.name = 'B'
        highBb = note.Note()
        highBb.name = 'B-'
        highBb.octave = 5
        dimOct = interval.Interval(lowB, highBb)
        self.assertEqual(dimOct.niceName, 'Diminished Octave')

        noteA1 = note.Note()
        noteA1.name = 'E-'
        noteA1.octave = 4
        noteA2 = note.Note()
        noteA2.name = 'F#'
        noteA2.octave = 5
        intervalA1 = interval.Interval(noteA1, noteA2)

        noteA3 = note.Note()
        noteA3.name = 'D'
        noteA3.octave = 1

        noteA4 = interval.transposeNote(noteA3, intervalA1)
        self.assertEqual(noteA4.name, 'E#')
        self.assertEqual(noteA4.octave, 2)

        interval1 = interval.Interval('-P5')

        n5 = interval.transposeNote(n4, interval1)
        n6 = interval.transposeNote(n4, 'P-5')
        self.assertEqual(n5.name, 'G-')
        self.assertEqual(n6.name, n5.name)

        # same thing using newer syntax:

        interval1 = interval.Interval('P-5')

        n5 = interval.transposeNote(n4, interval1)
        self.assertEqual(n5.name, 'G-')
        n7 = note.Note()
        n8 = interval.transposeNote(n7, 'P8')
        self.assertEqual(n8.name, 'C')
        self.assertEqual(n8.octave, 5)

        n9 = interval.transposeNote(n7, 'm7')  # should be B-
        self.assertEqual(n9.name, 'B-')
        self.assertEqual(n9.octave, 4)
        n10 = interval.transposeNote(n7, 'dd-2')  # should be B##
        self.assertEqual(n10.name, 'B##')
        self.assertEqual(n10.octave, 3)

        # test getWrittenHigherNote functions
        nE = note.Note('E')
        nESharp = note.Note('E#')
        nFFlat = note.Note('F-')
        nF1 = note.Note('F')
        nF2 = note.Note('F')

        higher1 = interval.getWrittenHigherNote(nE, nESharp)
        higher2 = interval.getWrittenHigherNote(nESharp, nFFlat)
        higher3 = interval.getWrittenHigherNote(nF1, nF2)

        self.assertEqual(higher1, nESharp)
        self.assertEqual(higher2, nFFlat)
        self.assertEqual(higher3, nF1)  # in case of ties, first is returned

        higher4 = interval.getAbsoluteHigherNote(nE, nESharp)
        higher5 = interval.getAbsoluteHigherNote(nESharp, nFFlat)
        higher6 = interval.getAbsoluteHigherNote(nESharp, nF1)
        higher7 = interval.getAbsoluteHigherNote(nF1, nESharp)

        self.assertEqual(higher4, nESharp)
        self.assertEqual(higher5, nESharp)
        self.assertEqual(higher6, nESharp)
        self.assertEqual(higher7, nF1)

        lower1 = interval.getWrittenLowerNote(nESharp, nE)
        lower2 = interval.getWrittenLowerNote(nFFlat, nESharp)
        lower3 = interval.getWrittenLowerNote(nF1, nF2)

        self.assertEqual(lower1, nE)
        self.assertEqual(lower2, nESharp)
        self.assertEqual(lower3, nF1)  # still returns first.

        lower4 = interval.getAbsoluteLowerNote(nESharp, nE)
        lower5 = interval.getAbsoluteLowerNote(nFFlat, nESharp)
        lower6 = interval.getAbsoluteLowerNote(nESharp, nF1)

        self.assertEqual(lower4, nE)
        self.assertEqual(lower5, nFFlat)
        self.assertEqual(lower6, nESharp)

        middleC = note.Note()
        lowerC = note.Note()
        lowerC.octave = 3
        descendingOctave = interval.Interval(middleC, lowerC)
        self.assertEqual(descendingOctave.generic.simpleDirected, 1)
        # no descending unisons ever
        self.assertEqual(descendingOctave.generic.semiSimpleDirected, -8)
        # no descending unisons ever
        self.assertEqual(descendingOctave.directedName, 'P-8')
        self.assertEqual(descendingOctave.directedSimpleName, 'P1')

        lowerG = note.Note()
        lowerG.name = 'G'
        lowerG.octave = 3
        descendingFourth = interval.Interval(middleC, lowerG)
        self.assertEqual(descendingFourth.diatonic.directedNiceName,
                         'Descending Perfect Fourth')
        self.assertEqual(descendingFourth.diatonic.directedSimpleName, 'P-4')
        self.assertEqual(descendingFourth.diatonic.simpleName, 'P4')
        self.assertEqual(descendingFourth.diatonic.mod7, 'P5')

        perfectFifth = descendingFourth.complement
        self.assertEqual(perfectFifth.niceName, 'Perfect Fifth')
        self.assertEqual(perfectFifth.diatonic.simpleName, 'P5')
        self.assertEqual(perfectFifth.diatonic.mod7, 'P5')
        self.assertEqual(perfectFifth.complement.niceName, 'Perfect Fourth')

    def testCreateIntervalFromPitch(self):
        p1 = pitch.Pitch('c')
        p2 = pitch.Pitch('g')
        i = interval.Interval(p1, p2)
        self.assertEqual(i.intervalClass, 5)

    def testTransposeImported(self):
        def collectAccidentalDisplayStatus(s_inner):
            post = []
            for e in s_inner.flatten().notes:
                if e.pitch.accidental is not None:
                    post.append(e.pitch.accidental.displayStatus)
                else:  # mark as not having an accidental
                    post.append('x')
            return post

        s = corpus.parse('bach/bwv66.6')
        # this has accidentals in measures 2 and 6
        sSub = s.parts[3].measures(2, 6)

        self.assertEqual(collectAccidentalDisplayStatus(sSub),
                         ['x', False, 'x', 'x', True, False, 'x', False, False, False,
                          False, False, False, 'x', 'x', 'x', False, False, False,
                          'x', 'x', 'x', 'x', True, False])

        sTransposed = sSub.flatten().transpose('p5')
        # sTransposed.show()

        self.assertEqual(collectAccidentalDisplayStatus(sTransposed),
                         ['x', None, 'x', 'x', None, None, None, None, None,
                          None, None, None, None, 'x', None, None, None, None,
                          None, 'x', 'x', 'x', None, None, None])

    def testIntervalMicrotonesA(self):
        i = interval.Interval('m3')
        self.assertEqual(i.chromatic.cents, 300)
        self.assertEqual(i.cents, 300.0)

        i = interval.Interval('p5')
        self.assertEqual(i.chromatic.cents, 700)
        self.assertEqual(i.cents, 700.0)

        i = interval.Interval(8)
        self.assertEqual(i.chromatic.cents, 800)
        self.assertEqual(i.cents, 800.0)

        i = interval.Interval(8.5)
        self.assertEqual(i.chromatic.cents, 850.0)
        self.assertEqual(i.cents, 850.0)

        i = interval.Interval(5.25)  # a sharp p4
        self.assertEqual(i.cents, 525.0)
        # we can subtract the two to get an offset
        self.assertEqual(i.cents, 525.0)
        self.assertEqual(str(i), '<music21.interval.Interval P4 (+25c)>')
        self.assertEqual(i._diatonicIntervalCentShift(), 25)

        i = interval.Interval(4.75)  # a flat p4
        self.assertEqual(str(i), '<music21.interval.Interval P4 (-25c)>')
        self.assertEqual(i._diatonicIntervalCentShift(), -25)

        i = interval.Interval(4.48)  # a sharp M3
        self.assertEqual(str(i), '<music21.interval.Interval M3 (+48c)>')
        self.assertAlmostEqual(i._diatonicIntervalCentShift(), 48.0)

        i = interval.Interval(4.5)  # a sharp M3
        self.assertEqual(str(i), '<music21.interval.Interval M3 (+50c)>')
        self.assertAlmostEqual(i._diatonicIntervalCentShift(), 50.0)

        i = interval.Interval(5.25)  # a sharp p4
        p1 = pitch.Pitch('c4')
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'F4(+25c)')

        i = interval.Interval(5.80)  # a sharp p4
        p1 = pitch.Pitch('c4')
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'F#4(-20c)')

        i = interval.Interval(6.00)  # an exact Tritone
        p1 = pitch.Pitch('c4')
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'F#4')

        i = interval.Interval(5)  # a chromatic p4
        p1 = pitch.Pitch('c4')
        p1.microtone = 10  # c+20
        self.assertEqual(str(p1), 'C4(+10c)')
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'F4(+10c)')

        i = interval.Interval(7.20)  # a sharp P5
        p1 = pitch.Pitch('c4')
        p1.microtone = -20  # c+20
        self.assertEqual(str(p1), 'C4(-20c)')
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'G4')

        i = interval.Interval(7.20)  # a sharp P5
        p1 = pitch.Pitch('c4')
        p1.microtone = 80  # c+20
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'G#4')

        i = interval.Interval(0.20)  # a sharp unison
        p1 = pitch.Pitch('e4')
        p1.microtone = 10
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'E~4(-20c)')

        i = interval.Interval(0.05)  # a tiny bit sharp unison
        p1 = pitch.Pitch('e4')
        p1.microtone = 5
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'E4(+10c)')

        i = interval.Interval(12.05)  # a tiny bit sharp octave
        p1 = pitch.Pitch('e4')
        p1.microtone = 5
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'E5(+10c)')

        i = interval.Interval(11.85)  # a flat octave
        p1 = pitch.Pitch('e4')
        p1.microtone = 5
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'E5(-10c)')

        i = interval.Interval(11.85)  # a flat octave
        p1 = pitch.Pitch('e4')
        p1.microtone = -20
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'E`5(+15c)')

    def testIntervalMicrotonesB(self):
        i = interval.Interval(note.Note('c4'), note.Note('c#4'))
        self.assertEqual(str(i), '<music21.interval.Interval A1>')

        i = interval.Interval(note.Note('c4'), note.Note('c~4'))
        self.assertEqual(str(i), '<music21.interval.Interval A1 (-50c)>')

    def testDescendingAugmentedUnison(self):
        ns = note.Note('C4')
        ne = note.Note('C-4')
        i = interval.Interval(noteStart=ns, noteEnd=ne)
        directedNiceName = i.directedNiceName
        self.assertEqual(directedNiceName, 'Descending Diminished Unison')

    def testTransposeWithChromaticInterval(self):
        ns = note.Note('C4')
        i = interval.ChromaticInterval(5)
        n2 = ns.transpose(i)
        self.assertEqual(n2.nameWithOctave, 'F4')

        ns = note.Note('B#3')
        i = interval.ChromaticInterval(5)
        n2 = ns.transpose(i)
        self.assertEqual(n2.nameWithOctave, 'F4')

    def testTransposeImplicit(self):
        p = pitch.Pitch('D#4')
        i = interval.Interval(0)
        self.assertTrue(i.implicitDiatonic)
        p2 = i.transposePitch(p)
        self.assertEqual(p.ps, p2.ps)
        self.assertNotEqual(p.name, p2.name)

    def testRepeatedTransposePitch(self):
        p = pitch.Pitch('C1')
        intv = interval.Interval('P5')
        out = []
        for _ in range(33):
            out.append(p.nameWithOctave)
            intv.transposePitch(p, maxAccidental=None, inPlace=True)
        self.assertEqual(
            out,
            ['C1', 'G1', 'D2', 'A2', 'E3', 'B3', 'F#4',
             'C#5', 'G#5', 'D#6', 'A#6', 'E#7', 'B#7', 'F##8',
             'C##9', 'G##9', 'D##10', 'A##10', 'E##11', 'B##11', 'F###12',
             'C###13', 'G###13', 'D###14', 'A###14', 'E###15', 'B###15', 'F####16',
             'C####17', 'G####17', 'D####18', 'A####18', 'E####19',
             ]
        )
        with self.assertRaisesRegex(pitch.AccidentalException,
                                    '5 is not a supported accidental type'):
            intv.transposePitch(p, maxAccidental=None)
        p2 = intv.transposePitch(p)
        self.assertEqual(p2.nameWithOctave, 'B-20')


    def testIntervalWithOneNoteGiven(self):
        noteC = note.Note('C4')
        with self.assertRaises(ValueError):
            i = interval.Interval(name='P4', noteStart=noteC)
        i = interval.Interval(name='P4')
        i.noteStart = noteC
        self.assertEqual(i.noteEnd.nameWithOctave, 'F4')
        noteF = i.noteEnd

        # giving noteStart and noteEnd and a name where the name does not match
        # the notes is an exception.
        with self.assertRaises(ValueError):
            interval.Interval(name='d5', noteStart=noteC, noteEnd=noteF)

        # same with chromatic only intervals
        with self.assertRaises(ValueError):
            interval.Interval(chromatic=interval.ChromaticInterval(6),
                              noteStart=noteC,
                              noteEnd=noteF)

        # but these should work
        i2 = interval.Interval(name='P4', noteStart=noteC, noteEnd=noteF)
        self.assertIs(i2.noteStart, noteC)
        self.assertIs(i2.noteEnd, noteF)
        self.assertEqual(i2.name, 'P4')
        self.assertEqual(i2.semitones, 5)

        i3 = interval.Interval(chromatic=interval.ChromaticInterval(5),
                               noteStart=noteC,
                               noteEnd=noteF)
        self.assertIs(i3.noteStart, noteC)
        self.assertIs(i3.noteEnd, noteF)
        self.assertEqual(i3.name, 'P4')
        self.assertEqual(i3.semitones, 5)


    def testEmptyIntervalProperties(self):
        '''
        As of v8, an empty Interval is equal to P1
        '''
        empty = interval.DiatonicInterval()
        self.assertEqual(empty.cents, 0.0)

        empty = interval.Interval()
        self.assertEqual(empty.cents, 0.0)
        self.assertEqual(empty.intervalClass, 0)
        self.assertEqual(empty.name, 'P1')


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
