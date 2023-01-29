# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         scale.test_scale_main.py
# Purpose:      Tests for scale/__init__.py
#
# Authors:      Christopher Ariza
#               Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2010-2023 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
from __future__ import annotations

from pprint import pformat
from textwrap import dedent
import unittest

from music21 import common
from music21 import corpus
from music21 import instrument
from music21 import meter
from music21 import note
from music21 import pitch
from music21 import scale
from music21.scale import intervalNetwork
from music21.scale import Terminus, Direction
from music21 import stream

# ------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def pitchOut(self, listIn):
        out = '['
        for p in listIn:
            out += str(p) + ', '
        out = out[0:len(out) - 2]
        out += ']'
        return out

    def testBasicLegacy(self):
        n1 = note.Note()

        cMajor = scale.MajorScale(n1)

        self.assertEqual(cMajor.name, 'C major')
        self.assertEqual(cMajor.getPitches()[6].step, 'B')

        seventh = cMajor.pitchFromDegree(7)
        self.assertEqual(seventh.step, 'B')

        dom = cMajor.getDominant()
        self.assertEqual(dom.step, 'G')

        n2 = note.Note()
        n2.step = 'A'

        aMinor = cMajor.getRelativeMinor()
        self.assertEqual(aMinor.name, 'A minor', 'Got a different name: ' + aMinor.name)

        notes = [note1.name for note1 in aMinor.getPitches()]
        self.assertEqual(notes, ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'A'])

        n3 = note.Note()
        n3.name = 'B-'
        n3.octave = 5

        bFlatMinor = scale.MinorScale(n3)
        self.assertEqual(bFlatMinor.name, 'B- minor', 'Got a different name: ' + bFlatMinor.name)
        notes2 = [note1.name for note1 in bFlatMinor.getPitches()]
        self.assertEqual(notes2, ['B-', 'C', 'D-', 'E-', 'F', 'G-', 'A-', 'B-'])
        self.assertEqual(bFlatMinor.getPitches()[0], n3.pitch)
        self.assertEqual(bFlatMinor.getPitches()[6].octave, 6)

        # harmonic = bFlatMinor.getConcreteHarmonicMinorScale()
        # niceHarmonic = [note1.name for note1 in harmonic]
        # self.assertEqual(niceHarmonic, ['B-', 'C', 'D-', 'E-', 'F', 'G-', 'A', 'B-'])
        #
        # harmonic2 = bFlatMinor.getAbstractHarmonicMinorScale()
        # self.assertEqual([note1.name for note1 in harmonic2], niceHarmonic)
        # for note1 in harmonic2:
        #     self.assertEqual(note1.octave, 0)
        #
        # melodic = bFlatMinor.getConcreteMelodicMinorScale()
        # niceMelodic = [note1.name for note1 in melodic]
        # self.assertEqual(niceMelodic,
        #         ['B-', 'C', 'D-', 'E-', 'F', 'G', 'A', 'B-', 'A-', 'G-',
        #          'F', 'E-', 'D-', 'C', 'B-'])

        # melodic2 = bFlatMinor.getAbstractMelodicMinorScale()
        # self.assertEqual([note1.name for note1 in melodic2], niceMelodic)
        # for note1 in melodic2:
        #     self.assertEqual(note1.octave, 0)

        cNote = bFlatMinor.pitchFromDegree(2)
        self.assertEqual(cNote.name, 'C')
        fNote = bFlatMinor.getDominant()
        self.assertEqual(fNote.name, 'F')

        bFlatMajor = bFlatMinor.getParallelMajor()
        self.assertEqual(bFlatMajor.name, 'B- major')
        # scale = [note1.name for note1 in bFlatMajor.getConcreteMajorScale()]
        # self.assertEqual(scale, ['B-', 'C', 'D', 'E-', 'F', 'G', 'A', 'B-'])

        dFlatMajor = bFlatMinor.getRelativeMajor()
        self.assertEqual(dFlatMajor.name, 'D- major')
        self.assertEqual(dFlatMajor.getTonic().name, 'D-')
        self.assertEqual(dFlatMajor.getDominant().name, 'A-')

    def testBasic(self):
        # deriving a scale from a Stream

        # just get default, c-minor, as derive will check all tonics
        sc2 = scale.MinorScale()

        # we can get a range of pitches
        # noinspection PyTypeChecker
        self.assertEqual(self.pitchOut(sc2.getPitches('c2', 'c5')),
                         '[C2, D2, E-2, F2, G2, A-2, B-2, C3, D3, E-3, F3, G3, A-3, B-3, '
                         + 'C4, D4, E-4, F4, G4, A-4, B-4, C5]')

        # we can transpose the Scale
        sc3 = sc2.transpose('-m3')
        self.assertEqual(self.pitchOut(sc3.getPitches('c2', 'c5')),
                         '[C2, D2, E2, F2, G2, A2, B2, C3, D3, E3, F3, G3, A3, B3, '
                         + 'C4, D4, E4, F4, G4, A4, B4, C5]')

        # getting pitches from scale degrees
        self.assertEqual(str(sc3.pitchFromDegree(3)), 'C4')
        self.assertEqual(str(sc3.pitchFromDegree(7)), 'G4')
        self.assertEqual(self.pitchOut(sc3.pitchesFromScaleDegrees([1, 5, 6])),
                         '[A3, E4, F4, A4]')
        self.assertEqual(
            self.pitchOut(
                sc3.pitchesFromScaleDegrees(
                    [2, 3],
                    minPitch='c6',
                    maxPitch='c9'
                )
            ),
            '[C6, B6, C7, B7, C8, B8, C9]')

        # given a pitch, get the scale degree
        sc4 = scale.MajorScale('A-')
        self.assertEqual(sc4.getScaleDegreeFromPitch('a-'), 1)
        # default is name matching
        self.assertEqual(sc4.getScaleDegreeFromPitch('g#'), None)
        # can set pitchClass comparison attribute
        self.assertEqual(sc4.getScaleDegreeFromPitch('g#',
                                                     comparisonAttribute='pitchClass'), 1)
        self.assertEqual(sc4.getScaleDegreeFromPitch('e-',
                                                     comparisonAttribute='name'), 5)

        # showing scales
        # this assumes that the tonic is not the first scale degree
        sc1 = scale.HypophrygianScale('c4')
        self.assertEqual(str(sc1.pitchFromDegree(1)), 'G3')
        self.assertEqual(str(sc1.pitchFromDegree(4)), 'C4')
        # sc1.show()

        sc1 = scale.MajorScale()
        # deriving a new scale from the pitches found in a collection
        s = corpus.parse('bwv66.6')
        sc3 = sc1.derive(s.parts['#soprano'])
        self.assertEqual(str(sc3), '<music21.scale.MajorScale A major>')

        sc3 = sc1.derive(s.parts['#tenor'])
        self.assertEqual(str(sc3), '<music21.scale.MajorScale A major>')

        sc3 = sc2.derive(s.parts['#bass'])
        self.assertEqual(str(sc3), '<music21.scale.MinorScale F# minor>')

        # composing with a scale
        s = stream.Stream()
        p = 'd#4'
        # sc = scale.PhrygianScale('e')
        sc = scale.MajorScale('E4')
        for d, x in [(Direction.ASCENDING, 1), (Direction.DESCENDING, 2), (Direction.ASCENDING, 3),
                     (Direction.DESCENDING, 4), (Direction.ASCENDING, 3), (Direction.DESCENDING, 2),
                     (Direction.ASCENDING, 1)]:
            # use duration type instead of quarter length
            for y in (1, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25):
                p = sc.nextPitch(p, direction=d, stepSize=x)
                n = note.Note(p)
                n.quarterLength = y
                s.append(n)
        self.assertEqual(self.pitchOut(s.pitches),
                         '[E4, F#4, G#4, A4, B4, C#5, D#5, B4, G#4, E4, C#4, A3, F#3, D#3, '
                         + 'G#3, C#4, F#4, B4, E5, A5, D#6, G#5, C#5, F#4, B3, E3, A2, D#2, G#2, '
                         + 'C#3, F#3, B3, E4, A4, D#5, B4, G#4, E4, C#4, A3, F#3, D#3, E3, F#3, '
                         + 'G#3, A3, B3, C#4, D#4]')
        # s.show()

        # composing with an octatonic scale.
        s1 = stream.Part()
        s2 = stream.Part()
        p1 = 'b4'
        p2 = 'b3'
        sc = scale.OctatonicScale('C4')
        for d, x in [(Direction.ASCENDING, 1), (Direction.DESCENDING, 2), (Direction.ASCENDING, 3),
                     (Direction.DESCENDING, 2), (Direction.ASCENDING, 1)]:
            for y in (1, 0.5, 0.25, 0.25):
                p1 = sc.nextPitch(p1, direction=d, stepSize=x)
                n = note.Note(p1)
                n.quarterLength = y
                s1.append(n)
            if d == Direction.ASCENDING:
                d = Direction.DESCENDING
            elif d == Direction.DESCENDING:
                d = Direction.ASCENDING
            for y in [1, 0.5, 0.25, 0.25]:
                p2 = sc.nextPitch(p2, direction=d, stepSize=x)
                n = note.Note(p2)
                n.quarterLength = y
                s2.append(n)
        s = stream.Score()
        s.insert(0, s1)
        s.insert(0, s2)
        # s.show()

        # compare two different major scales
        sc1 = scale.MajorScale('g')
        sc2 = scale.MajorScale('a')
        sc3 = scale.MinorScale('f#')
        # exact comparisons
        self.assertNotEqual(sc1, sc2)
        self.assertEqual(sc1.abstract, sc2.abstract)
        self.assertNotEqual(sc1, sc3)
        self.assertNotEqual(sc1.abstract, sc3.abstract)
        # getting details on comparison
        self.assertEqual(pformat(sc1.match(sc2)), '''{'matched': [<music21.pitch.Pitch A4>,
             <music21.pitch.Pitch B4>,
             <music21.pitch.Pitch D5>,
             <music21.pitch.Pitch E5>,
             <music21.pitch.Pitch F#5>],
 'notMatched': [<music21.pitch.Pitch C#5>, <music21.pitch.Pitch G#5>]}''', pformat(sc1.match(sc2)))

    def testCyclicalScales(self):
        sc = scale.CyclicalScale('c4', ['m2', 'm2'])

        # we get spelling based on maxAccidental parameter
        # noinspection PyTypeChecker
        self.assertEqual(self.pitchOut(sc.getPitches('g4', 'g6')),
                         '[G4, A-4, A4, B-4, C-5, C5, D-5, D5, E-5, F-5, F5, G-5, '
                         + 'G5, A-5, A5, B-5, C-6, C6, D-6, D6, E-6, F-6, F6, G-6, G6]')

        # these values are different because scale degree 1 has different
        # pitches in different registers, as this is a non-octave repeating
        # scale

        self.assertEqual(sc.abstract.getDegreeMaxUnique(), 2)

        self.assertEqual(str(sc.pitchFromDegree(1)), 'C4')
        self.assertEqual(str(sc.pitchFromDegree(1, 'c2', 'c3')), 'B#1')

        # scale storing parameters
        # How to get a spelling in several ways.
        # ex: octatonic should always compare on pitchClass

        # a very short cyclical scale
        sc = scale.CyclicalScale('c4', ['P5'])  # can give one list
        self.assertEqual(self.pitchOut(sc.pitches), '[C4, G4]')

        # noinspection PyTypeChecker
        self.assertEqual(self.pitchOut(sc.getPitches('g2', 'g6')), '[B-2, F3, C4, G4, D5, A5, E6]')

        # as single interval cycle, all are 1
        # environLocal.printDebug(['calling get scale degree from pitch'])
        self.assertEqual(sc.getScaleDegreeFromPitch('g4'), 1)
        self.assertEqual(sc.getScaleDegreeFromPitch('b-2',
                                                    direction=Direction.ASCENDING), 1)

        # test default args
        sc2 = scale.CyclicalScale()
        self.assertEqual(self.pitchOut(sc2.getPitches()), '[C4, D-4]')

    def testDeriveByDegree(self):
        sc1 = scale.MajorScale()
        self.assertEqual(str(sc1.deriveByDegree(7, 'G#')),
                         '<music21.scale.MajorScale A major>')

        sc1 = scale.HarmonicMinorScale()
        # what scale has g# as its 7th degree
        self.assertEqual(str(sc1.deriveByDegree(7, 'G#')),
                         '<music21.scale.HarmonicMinorScale A harmonic minor>')
        self.assertEqual(str(sc1.deriveByDegree(2, 'E')),
                         '<music21.scale.HarmonicMinorScale D harmonic minor>')

        # TODO(CA): add serial rows as scales

    # # This test does not yet work.
    # def testDeriveByDegreeBiDirectional(self):
    #     sc1 = scale.MelodicMinorScale()
    #     sc1.deriveByDegree(6, 'G')



    def testMelodicMinorA(self):
        mm = scale.MelodicMinorScale('a')
        self.assertEqual(self.pitchOut(mm.pitches), '[A4, B4, C5, D5, E5, F#5, G#5, A5]')

        self.assertEqual(self.pitchOut(mm.getPitches(direction=Direction.ASCENDING)),
                         '[A4, B4, C5, D5, E5, F#5, G#5, A5]')

        # noinspection PyArgumentList
        self.assertEqual(self.pitchOut(mm.getPitches('c1', 'c3', direction=Direction.DESCENDING)),
                         '[C3, B2, A2, G2, F2, E2, D2, C2, B1, A1, G1, F1, E1, D1, C1]')

        # noinspection PyArgumentList
        self.assertEqual(self.pitchOut(mm.getPitches('c1', 'c3', direction=Direction.ASCENDING)),
                         '[C1, D1, E1, F#1, G#1, A1, B1, C2, D2, E2, F#2, G#2, A2, B2, C3]')

        # noinspection PyArgumentList
        self.assertEqual(self.pitchOut(mm.getPitches('c1', 'c3', direction=Direction.DESCENDING)),
                         '[C3, B2, A2, G2, F2, E2, D2, C2, B1, A1, G1, F1, E1, D1, C1]')

        # noinspection PyArgumentList
        self.assertEqual(self.pitchOut(mm.getPitches('a5', 'a6', direction=Direction.ASCENDING)),
                         '[A5, B5, C6, D6, E6, F#6, G#6, A6]')

        # noinspection PyArgumentList
        self.assertEqual(self.pitchOut(mm.getPitches('a5', 'a6', direction=Direction.DESCENDING)),
                         '[A6, G6, F6, E6, D6, C6, B5, A5]')

        self.assertEqual(mm.getScaleDegreeFromPitch('a3'), 1)
        self.assertEqual(mm.getScaleDegreeFromPitch('b3'), 2)

        # ascending, by default, has 7th scale degree as g#
        self.assertEqual(mm.getScaleDegreeFromPitch('g#3'), 7)

        # in descending, G# is not present
        self.assertEqual(mm.getScaleDegreeFromPitch('g#3', direction=Direction.DESCENDING), None)

        # but, g is
        self.assertEqual(mm.getScaleDegreeFromPitch('g3', direction=Direction.DESCENDING), 7)

        # the bidirectional representation has a version of each instance
        # merged
        # noinspection PyArgumentList
        self.assertEqual(self.pitchOut(mm.getPitches('a4', 'a5', direction=Direction.BI)),
                         '[A4, B4, C5, D5, E5, F#5, F5, G#5, G5, A5]')

        # in a bidirectional representation, both g and g# are will return
        # scale degree 7
        self.assertEqual(mm.getScaleDegreeFromPitch('g8', direction=Direction.BI), 7)
        self.assertEqual(mm.getScaleDegreeFromPitch('g#1', direction=Direction.BI), 7)
        self.assertEqual(mm.getScaleDegreeFromPitch('f8', direction=Direction.BI), 6)
        self.assertEqual(mm.getScaleDegreeFromPitch('f#1', direction=Direction.BI), 6)

        self.assertEqual(mm.nextPitch('e5', Direction.ASCENDING).nameWithOctave, 'F#5')
        # self.assertEqual(mm.nextPitch('f#5', Direction.ASCENDING).nameWithOctave, 'F#5')

        self.assertEqual(mm.nextPitch('e5', Direction.DESCENDING).nameWithOctave, 'D5')

        self.assertEqual(mm.nextPitch('g#2', Direction.ASCENDING).nameWithOctave, 'A2')
        # self.assertEqual(mm.nextPitch('g2', Direction.DESCENDING).nameWithOctave, 'f2')

    def testMelodicMinorB(self):
        '''
        Need to test descending form of getting pitches with no defined min and max
        '''
        mm = scale.MelodicMinorScale('a')
        # self.assertEqual(str(mm.getPitches(None, None, direction=Direction.ASCENDING)),
        #    '[A4, B4, C5, D5, E5, F#5, G#5, A5]')

        self.assertEqual(mm.pitchFromDegree(2, direction=Direction.ASCENDING).nameWithOctave, 'B4')

        self.assertEqual(mm.pitchFromDegree(5, direction=Direction.ASCENDING).nameWithOctave, 'E5')

        self.assertEqual(mm.pitchFromDegree(6, direction=Direction.ASCENDING).nameWithOctave, 'F#5')

        self.assertEqual(mm.pitchFromDegree(6, direction=Direction.DESCENDING).nameWithOctave, 'F5')

        # todo: this is ambiguous case
        # self.assertEqual(mm.pitchFromDegree(6, direction==Direction.BI).nameWithOctave, 'F5')

        # noinspection PyArgumentList
        self.assertEqual(self.pitchOut(mm.getPitches(None, None, direction=Direction.DESCENDING)),
                         '[A5, G5, F5, E5, D5, C5, B4, A4]')
        # noinspection PyArgumentList
        self.assertEqual(self.pitchOut(mm.getPitches(None, None, direction=Direction.ASCENDING)),
                         '[A4, B4, C5, D5, E5, F#5, G#5, A5]')

        self.assertEqual(str(mm.nextPitch('a3', Direction.ASCENDING)), 'B3')

        self.assertEqual(str(mm.nextPitch('f#5', Direction.ASCENDING)), 'G#5')
        self.assertEqual(str(mm.nextPitch('G#5', Direction.ASCENDING)), 'A5')

        self.assertEqual(str(mm.nextPitch('f5', Direction.DESCENDING)), 'E5')
        self.assertEqual(str(mm.nextPitch('G5', Direction.DESCENDING)), 'F5')
        self.assertEqual(str(mm.nextPitch('A5', Direction.DESCENDING)), 'G5')

        self.assertEqual(str(mm.nextPitch('f#5', Direction.DESCENDING)), 'F5')
        self.assertEqual(str(mm.nextPitch('f#5', Direction.DESCENDING,
                                          getNeighbor=Direction.DESCENDING)), 'E5')

        self.assertEqual(str(mm.nextPitch('f5', Direction.ASCENDING)), 'F#5')
        self.assertEqual(str(mm.nextPitch('f5', Direction.ASCENDING,
                                          getNeighbor=Direction.DESCENDING)), 'F#5')

        # composing with a scale
        s = stream.Stream()
        p = 'f#3'
        # sc = scale.PhrygianScale('e')
        sc = scale.MelodicMinorScale('g4')
        for direction in range(8):
            if direction % 2 == 0:
                d = Direction.ASCENDING
                qls = [1, 0.5, 0.5, 2, 0.25, 0.25, 0.25, 0.25]
            else:
                d = Direction.DESCENDING
                qls = [1, 0.5, 1, 0.5, 0.5]
            for y in qls:
                p = sc.nextPitch(p, direction=d, stepSize=1)
                n = note.Note(p)
                n.quarterLength = y
                s.append(n)
        s.makeAccidentals(inPlace=True)

        self.assertEqual(
            self.pitchOut(s.pitches),
            '[G3, A3, B-3, C4, D4, E4, F#4, G4, F4, E-4, D4, C4, B-3, C4, D4, E4, F#4, '
            + 'G4, A4, B-4, C5, B-4, A4, G4, F4, E-4, E4, F#4, G4, A4, B-4, C5, D5, E5, '
            + 'E-5, D5, C5, B-4, A4, B-4, C5, D5, E5, F#5, G5, A5, B-5, A5, G5, F5, E-5, D5]')

        # s.show()

    def testPlagalModes(self):
        hs = scale.HypophrygianScale('c4')
        self.assertEqual(self.pitchOut(hs.pitches), '[G3, A-3, B-3, C4, D-4, E-4, F4, G4]')
        self.assertEqual(str(hs.pitchFromDegree(1)), 'G3')

    def testRagAsawari(self):
        sc = scale.RagAsawari('c4')
        self.assertEqual(str(sc.pitchFromDegree(1)), 'C4')

        #
        # ascending should be:  [C2, D2, F2, G2, A-2, C3]

        self.assertEqual(str(sc.nextPitch('c4', Direction.ASCENDING)), 'D4')
        self.assertEqual(self.pitchOut(sc.pitches), '[C4, D4, F4, G4, A-4, C5]')
        # self.assertEqual(str(hs.pitchFromDegree(1)), 'G3')

        # noinspection PyArgumentList
        self.assertEqual(self.pitchOut(sc.getPitches('c2', 'c4', direction=Direction.ASCENDING)),
                         '[C2, D2, F2, G2, A-2, C3, D3, F3, G3, A-3, C4]')

        # noinspection PyArgumentList
        self.assertEqual(self.pitchOut(sc.getPitches('c2', 'c4', direction=Direction.DESCENDING)),
                         '[C4, B-3, A-3, G3, F3, E-3, D3, C3, B-2, A-2, G2, F2, E-2, D2, C2]')

        self.assertEqual(str(sc.nextPitch('c1', Direction.ASCENDING)), 'D1')
        self.assertEqual(str(sc.nextPitch('d1', Direction.ASCENDING)), 'F1')
        self.assertEqual(str(sc.nextPitch('f1', Direction.DESCENDING)), 'E-1')

        self.assertEqual(str(sc.nextPitch('e-1',
                                          Direction.ASCENDING,
                                          getNeighbor=Direction.DESCENDING)),
                         'F1')

        self.assertEqual(str(sc.pitchFromDegree(1)), 'C1')
        # there is no third step in ascending form
        self.assertEqual(str(sc.pitchFromDegree(3)), 'None')
        self.assertEqual(str(sc.pitchFromDegree(3, direction=Direction.DESCENDING)),
                         'E-4')

        self.assertEqual(str(sc.pitchFromDegree(7)), 'None')
        self.assertEqual(str(sc.pitchFromDegree(7, direction=Direction.DESCENDING)), 'B-4')

    def testRagMarwaA(self):
        sc = scale.RagMarwa('c4')
        self.assertEqual(str(sc.pitchFromDegree(1)), 'C4')

        self.assertEqual(str(sc.nextPitch('c4', Direction.ASCENDING)), 'D-4')

        self.assertEqual(self.pitchOut(sc.pitches), '[C4, D-4, E4, F#4, A4, B4, A4, C5, D-5]')

        # noinspection PyArgumentList
        self.assertEqual(self.pitchOut(sc.getPitches('c2', 'c3', direction=Direction.ASCENDING)),
                         '[C2, D-2, E2, F#2, A2, B2, A2, C3]')

        # noinspection PyArgumentList
        self.assertEqual(self.pitchOut(sc.getPitches('c2', 'c4', direction=Direction.ASCENDING)),
                         '[C2, D-2, E2, F#2, A2, B2, A2, C3, D-3, E3, F#3, A3, B3, A3, C4]')

        # noinspection PyArgumentList
        self.assertEqual(self.pitchOut(sc.getPitches('c3', 'd-4', direction=Direction.DESCENDING)),
                         '[D-4, C4, D-4, B3, A3, F#3, E3, D-3, C3]')

        # is this correct: this cuts off the d-4, as it is outside the range
        # noinspection PyArgumentList
        self.assertEqual(self.pitchOut(sc.getPitches('c3', 'c4', direction=Direction.DESCENDING)),
                         '[C4, B3, A3, F#3, E3, D-3, C3]')

        self.assertEqual(str(sc.nextPitch('c1', Direction.ASCENDING)), 'D-1')
        self.assertEqual(str(sc.nextPitch('d-1', Direction.ASCENDING)), 'E1')
        self.assertEqual(str(sc.nextPitch('e1', Direction.ASCENDING)), 'F#1')
        self.assertEqual(str(sc.nextPitch('f#1', Direction.ASCENDING)), 'A1')
        # this is probabilistic
        # self.assertEqual(str(sc.nextPitch('A1', Direction.ASCENDING)), 'B1')
        self.assertEqual(str(sc.nextPitch('B1', Direction.ASCENDING)), 'A1')

        self.assertEqual(str(sc.nextPitch('B2', Direction.DESCENDING)), 'A2')
        self.assertEqual(str(sc.nextPitch('A2', Direction.DESCENDING)), 'F#2')
        self.assertEqual(str(sc.nextPitch('E2', Direction.DESCENDING)), 'D-2')
        # this is correct!
        self.assertEqual(str(sc.nextPitch('C2', Direction.DESCENDING)), 'D-2')
        self.assertEqual(str(sc.nextPitch('D-2', Direction.ASCENDING)), 'E2')

    def testRagMarwaB(self):
        sc = scale.RagMarwa('c4')

        # for rag marwa, and given only the pitch "A", the scale can move to
        # either b or c; this selection is determined by weighted random
        # selection.
        post = []
        for unused_x in range(100):
            post.append(sc.getScaleDegreeFromPitch('A1', Direction.ASCENDING))
        self.assertGreater(post.count(5), 30)
        self.assertGreater(post.count(7), 30)

        # for rag marwa, and given only the pitch d-, the scale can move to
        # either b or c; this selection is determined by weighted random
        # selection; can be 2 or 7
        post = []
        for unused_x in range(100):
            post.append(sc.getScaleDegreeFromPitch('D-3', Direction.DESCENDING))
        self.assertGreater(post.count(2), 30)
        self.assertGreater(post.count(7), 30)

    def testRagMarwaC(self):
        sc = scale.RagMarwa('c4')

        self.assertEqual(sc.abstract._net.realizeTermini('c1', Terminus.LOW),
                         (pitch.Pitch('C1'), pitch.Pitch('C2')))

        self.assertEqual(sc.abstract._net.realizeMinMax('c1', Terminus.LOW),
                         (pitch.Pitch('C1'), pitch.Pitch('D-2')))

        # descending from d-2, we can either go to c2 or b1
        post = []
        for unused_x in range(100):
            post.append(str(sc.nextPitch('D-2', Direction.DESCENDING)))
        self.assertGreater(post.count('C2'), 30)
        self.assertGreater(post.count('B1'), 30)

    def testWeightedHexatonicBluesA(self):
        sc = scale.WeightedHexatonicBlues('c4')

        i = 0
        j = 0
        for dummy in range(50):
            # over 50 iterations, it must be one of these two options
            # noinspection PyTypeChecker
            match = self.pitchOut(sc.getPitches('c3', 'c4'))
            if match == '[C3, E-3, F3, G3, B-3, C4]':
                i += 1
            if match == '[C3, E-3, F3, F#3, G3, B-3, C4]':
                j += 1
            self.assertEqual(match in [
                '[C3, E-3, F3, G3, B-3, C4]',
                '[C3, E-3, F3, F#3, G3, B-3, C4]'],
                True)
        # check that we got at least one; this may fail rarely
        self.assertGreaterEqual(i, 1)
        self.assertGreaterEqual(j, 1)

        # test descending
        i = 0
        j = 0
        for dummy in range(50):
            # over 50 iterations, it must be one of these two options
            # noinspection PyArgumentList
            match = self.pitchOut(sc.getPitches('c3', 'c4', direction=Direction.DESCENDING))
            if match == '[C4, B-3, G3, F3, E-3, C3]':
                i += 1
            if match == '[C4, B-3, G3, F#3, F3, E-3, C3]':
                j += 1
            self.assertEqual(match in [
                '[C4, B-3, G3, F3, E-3, C3]',
                '[C4, B-3, G3, F#3, F3, E-3, C3]'],
                True)
        # check that we got at least one; this may fail rarely
        self.assertGreaterEqual(i, 1)
        self.assertGreaterEqual(j, 1)

        self.assertEqual(str(sc.pitchFromDegree(1)), 'C4')
        self.assertEqual(str(sc.nextPitch('c4', Direction.ASCENDING)), 'E-4')

        # degree 4 is always the blues note in this model
        self.assertEqual(str(sc.pitchFromDegree(4)), 'F#4')

        # This never worked consistently and was not an important enough part of the project tp
        # continue to debug.
        # for unused_trial in range(15):
        #     self.assertTrue(str(sc.nextPitch('f#3', Direction.ASCENDING)) in ['G3', 'F#3'])
        #     # presently this might return the same note, if the
        #     # F# is taken as out of the scale and then found back in the Scale
        #     # in generation
        #     self.assertTrue(str(sc.nextPitch('f#3', Direction.DESCENDING)) in ['F3', 'F#3'])

    def testNextA(self):
        sc = scale.MajorScale('c4')

        # ascending works in pitch space
        self.assertEqual(str(sc.nextPitch('a4', Direction.ASCENDING, 1)), 'B4')
        self.assertEqual(str(sc.nextPitch('b4', Direction.ASCENDING, 1)), 'C5')
        self.assertEqual(str(sc.nextPitch('b5', Direction.ASCENDING, 1)), 'C6')
        self.assertEqual(str(sc.nextPitch('b3', Direction.ASCENDING, 1)), 'C4')

        # descending works in pitch space
        self.assertEqual(str(sc.nextPitch('c3', Direction.DESCENDING, 1)), 'B2')
        self.assertEqual(str(sc.nextPitch('c8', Direction.DESCENDING, 1)), 'B7')

        sc = scale.MajorScale('a4')

        self.assertEqual(str(sc.nextPitch('g#2', Direction.ASCENDING, 1)), 'A2')
        self.assertEqual(str(sc.nextPitch('g#4', Direction.ASCENDING, 1)), 'A4')

    def testIntervalBetweenDegrees(self):
        sc = scale.MajorScale('c4')
        self.assertEqual(str(sc.intervalBetweenDegrees(3, 4)), '<music21.interval.Interval m2>')
        self.assertEqual(str(sc.intervalBetweenDegrees(1, 7)), '<music21.interval.Interval M7>')
        self.assertEqual(str(sc.intervalBetweenDegrees(1, 5)), '<music21.interval.Interval P5>')
        self.assertEqual(str(sc.intervalBetweenDegrees(2, 4)), '<music21.interval.Interval m3>')

        # with a probabilistic non-deterministic scale,
        # an exception may be raised for step that may not exist
        sc = scale.WeightedHexatonicBlues('g3')
        exceptCount = 0
        for dummy in range(10):
            post = None
            try:
                post = sc.intervalBetweenDegrees(3, 4)
            except scale.ScaleException:
                exceptCount += 1
            if post is not None:
                self.assertEqual(str(post), '<music21.interval.Interval A1>')
        self.assertLess(exceptCount, 3)

    def testScalaScaleA(self):
        # noinspection SpellCheckingInspection
        msg = dedent('''! fj-12tet.scl
            !
            Franck Jedrzejewski continued fractions approx. of 12-tet
             12
            !
            89/84
            55/49
            44/37
            63/50
            4/3
            99/70
            442/295
            27/17
            37/22
            98/55
            15/8
            2/1
            ''')
        # provide a raw scala string
        sc = scale.ScalaScale('c4', msg)
        self.assertEqual(str(sc), '<music21.scale.ScalaScale C Scala: fj-12tet.scl>')
        # noinspection PyTypeChecker
        pitchesOut = self.pitchOut(sc.getPitches('c2', 'c4'))
        self.assertTrue(common.whitespaceEqual(pitchesOut,
                                               '''
            [C2, C#2(+0c), D2(-0c), E-2(-0c), E2(+0c), F2(-2c), F#2(+0c),
             G2, G#2(+1c), A2(+0c), B-2(+0c), B2(-12c),
             C3, C#3(+0c), D3(-0c), E-3(-0c), E3(+0c), F3(-2c), F#3(+0c),
             G3, G#3(+1c), A3(+0c), B-3(+0c), B3(-12c),
             C4]'''), pitchesOut)

    def testScalaScaleOutput(self):
        sc = scale.MajorScale('c4')
        ss = sc.getScalaData()
        self.assertEqual(ss.pitchCount, 7)
        msg = '''!
            <music21.scale.MajorScale C major>
            7
            !
            200.0
            400.0
            500.0
            700.0
            900.0
            1100.0
            1200.0
            '''
        self.assertTrue(common.whitespaceEqual(ss.getFileString(), msg), ss.getFileString())

    # noinspection SpellCheckingInspection

    def testScalaScaleB(self):
        # test importing from scala archive
        sc = scale.ScalaScale('e2', 'fj 12tet')
        self.assertEqual(sc._abstract._net.pitchSimplification, 'mostCommon')
        # this is showing that there are slight microtonal adjustments,
        # but they are less than one cent large
        pList = sc.pitches
        self.assertEqual(
            self.pitchOut(pList),
            '[E2, F2(+0c), F#2(-0c), G2(-0c), G#2(+0c), A2(-2c), B-2(+0c), B2(-0c), '
            + 'C3(+1c), C#3(+0c), D3(+0c), E-3(-12c), E3(+0c)]')

        # 7 tone scale
        sc = scale.ScalaScale('c2', 'mbira zimb')
        self.assertEqual(
            self.pitchOut(sc.pitches),
            '[C2, C#2(-2c), D~2(+21c), E~2(+22c), F#~2(-8c), G~2(+21c), A~2(+2c), B~2(-2c)]')

        # 21 tone scale
        sc = scale.ScalaScale('c2', 'mbira_mude')
        self.assertEqual(
            self.pitchOut(sc.pitches),
            '[C2, C#~2(+24c), E-2(-11c), F#2(-25c), F#2(+12c), G~2(+20c), B~2(-4c), B-2(-24c), '
            + 'F3(-22c), D~3(+17c), F#~3(-2c), G#3(-13c), A3(+15c), C#~3(-24c), A3(+17c), '
            + 'B~3(-2c), C#~4(-22c), D~4(-4c), E~4(+10c), F#~4(-18c), G#4(+5c), B`4(+15c)]')
        # sc.show()

        # two octave slendro scale
        sc = scale.ScalaScale('c2', 'slendro_pliat')
        self.assertEqual(self.pitchOut(sc.pitches),
                         '[C2, D~2(-15c), E~2(+4c), G2(+5c), A~2(-23c), C3, D~3(-15c), E~3(+4c), '
                         + 'G3(+5c), A~3(-23c)]')

        # 5 note slendro scale
        sc = scale.ScalaScale('c2', 'slendro_ang2')
        self.assertEqual(self.pitchOut(sc.pitches),
                         '[C2, E-2(-22c), F~2(+19c), G~2(-10c), B`2(-8c), C3]')

        # 5 note slendro scale
        sc = scale.ScalaScale('c2', 'slendroc5.scl')
        self.assertEqual(self.pitchOut(sc.pitches),
                         '[C2, D~2(-14c), E~2(+4c), G2(+5c), A~2(-22c), C3]')

        s = stream.Stream()
        s.append(meter.TimeSignature('6/4'))

        sc1 = scale.ScalaScale('c2', 'slendro_ang2')
        sc2 = scale.ScalaScale('c2', 'slendroc5.scl')
        p1 = stream.Part()
        p1.append([note.Note(p, lyric=p.microtone) for p in sc1.pitches])
        p2 = stream.Part()
        p2.append([note.Note(p, lyric=p.microtone) for p in sc2.pitches])
        s.insert(0, p1)
        s.insert(0, p2)
        # s.show()

    def testConcreteScaleA(self):
        # testing of arbitrary concrete scales
        sc = scale.ConcreteScale(
            pitches=['C#3', 'E-3', 'F3', 'G3', 'B3', 'D~4', 'F#4', 'A4', 'C#5']
        )
        self.assertEqual(str(sc.getTonic()), 'C#3')

        self.assertFalse(sc.abstract.octaveDuplicating)

        self.assertEqual(self.pitchOut(sc.pitches),
                         '[C#3, E-3, F3, G3, B3, D~4, F#4, A4, C#5]')

        # noinspection PyTypeChecker
        self.assertEqual(self.pitchOut(sc.getPitches('C#3', 'C#5')),
                         '[C#3, E-3, F3, G3, B3, D~4, F#4, A4, C#5]')

        # noinspection PyTypeChecker
        self.assertEqual(
            self.pitchOut(sc.getPitches('C#1', 'C#5')),
            '[C#1, E-1, F1, G1, B1, D~2, F#2, A2, C#3, E-3, F3, G3, B3, D~4, F#4, A4, C#5]')

        # a portion of the scale
        # noinspection PyTypeChecker
        self.assertEqual(self.pitchOut(sc.getPitches('C#4', 'C#5')),
                         '[D~4, F#4, A4, C#5]')

        # noinspection PyTypeChecker
        self.assertEqual(self.pitchOut(sc.getPitches('C#7', 'C#5')),
                         '[C#7, A6, F#6, D~6, B5, G5, F5, E-5, C#5]')

        sc = scale.ConcreteScale(pitches=['C#3', 'E-3', 'F3', 'G3', 'B3', 'C#4'])
        self.assertEqual(str(sc.getTonic()), 'C#3')
        self.assertTrue(sc.abstract.octaveDuplicating)

    def testTuneA(self):
        # fokker_12.scl  Fokker's 7-limit 12-tone just scale
        # pyth_12.scl    12  12-tone Pythagorean scale
        s = corpus.parse('bwv66.6')
        p1 = s.parts[0]
        # p1.show('midi')

        self.assertEqual(self.pitchOut(p1.pitches[0:10]),
                         '[C#5, B4, A4, B4, C#5, E5, C#5, B4, A4, C#5]')

        sc = scale.ScalaScale('C4', 'fokker_12.scl')
        self.assertEqual(
            self.pitchOut(sc.pitches),
            '[C4, C#4(+19c), D4(+4c), D~4(+17c), E4(-14c), F4(-2c), F#4(-10c), G4(+2c), '
            + 'G#4(+21c), A4(-16c), A~4(+19c), B4(-12c), C5]')
        sc.tune(s)

        p1 = s.parts[0]
        # problem of not matching enharmonics
        self.assertEqual(
            self.pitchOut(p1.pitches[0:10]),
            '[C#5(+19c), B4(-12c), A4(-16c), B4(-12c), C#5(+19c), E5(-14c), C#5(+19c), '
            + 'B4(-12c), A4(-16c), C#5(+19c)]')
        # p1.show('midi')

    def testTuneB(self):
        # fokker_12.scl  Fokker's 7-limit 12-tone just scale
        # pyth_12.scl    12  12-tone Pythagorean scale
        sc = scale.ScalaScale('C4', 'fokker_12.scl')
        pl = sc.pitches
        self.assertEqual(
            self.pitchOut(pl),
            '[C4, C#4(+19c), D4(+4c), D~4(+17c), E4(-14c), F4(-2c), F#4(-10c), G4(+2c), '
            + 'G#4(+21c), A4(-16c), A~4(+19c), B4(-12c), C5]')

        s = corpus.parse('bwv66.6')
        sc.tune(s)
        # s.show('midi')
        self.assertEqual(
            self.pitchOut(s.parts[0].pitches[0:10]),
            '[C#5(+19c), B4(-12c), A4(-16c), B4(-12c), C#5(+19c), E5(-14c), C#5(+19c), '
            + 'B4(-12c), A4(-16c), C#5(+19c)]')

        self.assertEqual(self.pitchOut(s.parts[1].pitches[0:10]),
                         '[E4(-14c), F#4(-10c), E4(-14c), E4(-14c), E4(-14c), '
                         + 'E4(-14c), A4(-16c), G#4(+21c), E4(-14c), G#4(+21c)]')

    def testTunePythagorean(self):
        '''
        Applies a pythagorean tuning to a section of D. Luca's Gloria
        and then uses Marchetto da Padova's very high sharps and very low
        flats (except B-flat) to inflect the accidentals
        '''
        s = corpus.parse('luca/gloria').measures(70, 79)
        for p in s.parts:
            inst = p[instrument.Instrument].first()
            inst.midiProgram = 52
        sc = scale.ScalaScale('F2', 'pyth_12.scl')
        sc.tune(s)
        for p in s.flatten().pitches:
            if p.accidental is not None:
                if p.accidental.name == 'sharp':
                    p.microtone = p.microtone.cents + 45
                elif p.accidental.name == 'flat' and p.step == 'B':
                    p.microtone = p.microtone.cents - 20
                elif p.accidental.name == 'flat':
                    p.microtone = p.microtone.cents - 45
        # s.show()
        # s = s.transpose('P-4')
        # print(s[0].measure(77).notes[1].microtone)
        # s.show('midi')

    def testChromaticScaleA(self):
        cs = scale.ChromaticScale('c4')
        self.assertEqual(self.pitchOut(cs.pitches),
                         '[C4, C#4, D4, E-4, E4, F4, F#4, G4, A-4, A4, B-4, B4, C5]')

    def testSieveScaleA(self):
        # sc = scale.SieveScale('d4', '3@0')
        # self.assertEqual(str(sc.getPitches('c2', 'c4')), '[D2, E#2, G#2, B2, D3, E#3, G#3, B3]')

        sc = scale.SieveScale('d4', '1@0', eld=2)
        # noinspection PyTypeChecker
        self.assertEqual(self.pitchOut(sc.getPitches('c2', 'c4')),
                         '[C2, D2, F-2, G-2, A-2, B-2, C3, D3, F-3, G-3, A-3, B-3, C4]')

        sc = scale.SieveScale('d4', '1@0', eld=0.5)
        # noinspection PyTypeChecker
        self.assertEqual(
            self.pitchOut(sc.getPitches('c2', 'c4')),
            '[C2, C~2, D-2, D`2, D2, D~2, E-2, E`2, F-2, F`2, F2, F~2, G-2, '
            + 'G`2, G2, G~2, A-2, A`2, A2, A~2, B-2, B`2, C-3, C`3, C3, C~3, D-3, '
            + 'D`3, D3, D~3, E-3, E`3, F-3, F`3, F3, F~3, G-3, G`3, G3, G~3, A-3, '
            + 'A`3, A3, A~3, B-3, B`3, C-4, C`4, C4]'
        )

        sc = scale.SieveScale('d4', '1@0', eld=0.25)
        # noinspection PyTypeChecker
        self.assertEqual(
            self.pitchOut(sc.getPitches('c2', 'c3')),
            '[C2, C2(+25c), C~2, C#2(-25c), D-2, D`2(-25c), D`2, D2(-25c), D2, '
            + 'D2(+25c), D~2, D#2(-25c), E-2, E`2(-25c), E`2, E2(-25c), F-2, F`2(-25c), '
            + 'F`2, F2(-25c), F2, F2(+25c), F~2, F#2(-25c), G-2, G`2(-25c), G`2, G2(-25c), '
            + 'G2, G2(+25c), G~2, G#2(-25c), A-2, A`2(-25c), A`2, A2(-25c), A2, A2(+25c), '
            + 'A~2, A#2(-25c), B-2, B`2(-25c), B`2, B2(-25c), C-3, C`3(-25c), C`3, '
            + 'C3(-25c), C3]'
        )

    def testDerivedScaleNoOctaves(self):
        d = scale.ConcreteScale(pitches=['A', 'B', 'C', 'D', 'E', 'F', 'G#', 'A'])
        e = d.deriveRanked(['C', 'E', 'G'], comparisonAttribute='name')
        self.assertEqual(str(e),
                         ''.join(['[(3, <music21.scale.ConcreteScale F Concrete>), ',
                                   '(3, <music21.scale.ConcreteScale E Concrete>), ',
                                   '(2, <music21.scale.ConcreteScale B Concrete>), ',
                                   '(2, <music21.scale.ConcreteScale A Concrete>)]']),
                         str(e)
                         )

    def testDerivedScaleAbsurdOctaves(self):
        e = scale.ConcreteScale(pitches=['A4', 'B4', 'C4', 'D4', 'E4', 'F4', 'G4', 'A4'])
        with self.assertRaises(intervalNetwork.IntervalNetworkException):
            e.deriveRanked(['C4', 'E4', 'G4'], comparisonAttribute='name')

    def test_getPitches_multiple_times(self):
        '''
        Worth testing because we found cached lists being mutated.
        '''
        c_maj = scale.MajorScale('C')

        for i in range(3):  # catch both even and odd states
            with self.subTest(iterations=i):
                # due to a tight coupling of direction and reverse, this sets reverse=True
                # when calling getRealization()
                post = c_maj.getPitches(direction=Direction.DESCENDING)

                self.assertEqual(post[0].nameWithOctave, 'C5')
                self.assertEqual(post[-1].nameWithOctave, 'C4')


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    # sys.arg test options will be used in mainTest()
    import music21
    music21.mainTest(Test)
