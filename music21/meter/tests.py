# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         meter.tests.py
# Purpose:      Tests of meter
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009-2012, 2015, 2021 Michael Scott Cuthbert
#               and the music21 Project
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
import copy
import random
import unittest

from music21 import common
from music21 import duration
from music21 import note
from music21 import stream
from music21.meter.base import TimeSignature
from music21.meter.core import MeterSequence, MeterTerminal

class TestExternal(unittest.TestCase):
    show = True

    def testSingle(self):
        '''Need to test direct meter creation w/o stream
        '''
        a = TimeSignature('3/16')
        if self.show:
            a.show()

    def testBasic(self):
        a = stream.Stream()
        for meterStrDenominator in [1, 2, 4, 8, 16, 32]:
            for meterStrNumerator in [2, 3, 4, 5, 6, 7, 9, 11, 12, 13]:
                ts = TimeSignature(f'{meterStrNumerator}/{meterStrDenominator}')
                m = stream.Measure()
                m.timeSignature = ts
                a.insert(m.timeSignature.barDuration.quarterLength, m)
        if self.show:
            a.show()

    def testCompound(self):
        a = stream.Stream()
        meterStrDenominator = [1, 2, 4, 8, 16, 32]
        meterStrNumerator = [2, 3, 4, 5, 6, 7, 9, 11, 12, 13]

        for i in range(8):
            msg = []
            for j in range(1, random.choice([2, 4])):
                msg.append('%s/%s' % (random.choice(meterStrNumerator),
                                      random.choice(meterStrDenominator)))
            ts = TimeSignature('+'.join(msg))
            m = stream.Measure()
            m.timeSignature = ts
            a.insert(m.timeSignature.barDuration.quarterLength, m)
        if self.show:
            a.show()

    def testMeterBeam(self):
        ts = TimeSignature('6/8', 2)
        b = [duration.Duration('16th')] * 12
        s = stream.Stream()
        s.insert(0, ts)
        for x in b:
            n = note.Note()
            n.duration = x
            s.append(n)
        if self.show:
            s.show()


class Test(unittest.TestCase):
    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
        '''
        import sys
        import types
        for part in sys.modules[self.__module__].__dict__:
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            name = getattr(sys.modules[self.__module__], part)
            # noinspection PyTypeChecker
            if callable(name) and not isinstance(name, types.FunctionType):
                try:  # see if obj can be made w/ args
                    obj = name()
                except TypeError:
                    continue
                i = copy.copy(obj)
                j = copy.deepcopy(obj)

    def testMeterSubdivision(self):
        a = MeterSequence()
        a.load('4/4', 4)
        self.assertEqual(str(a), '{1/4+1/4+1/4+1/4}')

        a[0] = a[0].subdivide(2)
        self.assertEqual(str(a), '{{1/8+1/8}+1/4+1/4+1/4}')

        a[3] = a[3].subdivide(4)
        self.assertEqual(str(a), '{{1/8+1/8}+1/4+1/4+{1/16+1/16+1/16+1/16}}')

    def testMeterDeepcopy(self):
        a = MeterSequence()
        a.load('4/4', 4)
        b = copy.deepcopy(a)
        self.assertNotEqual(a, b)

        c = TimeSignature('4/4')
        d = copy.deepcopy(c)
        self.assertNotEqual(c, d)

    def testGetBeams(self):
        ts = TimeSignature('6/8')
        durList = [16, 16, 16, 16, 8, 16, 16, 16, 16, 8]

        notesList = [note.Note(quarterLength=4 / d) for d in durList]
        beams = ts.getBeams(notesList)
        match = '''[<music21.beam.Beams <music21.beam.Beam 1/start>/<music21.beam.Beam 2/start>>,
        <music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/continue>>,
        <music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/continue>>,
        <music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/stop>>,
        <music21.beam.Beams <music21.beam.Beam 1/stop>>,
        <music21.beam.Beams <music21.beam.Beam 1/start>/<music21.beam.Beam 2/start>>,
        <music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/continue>>,
        <music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/continue>>,
        <music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/stop>>,
        <music21.beam.Beams <music21.beam.Beam 1/stop>>]'''

        self.assertTrue(common.whitespaceEqual(str(beams), match))

    def test_getBeams_offset(self):
        '''
        Test getting Beams from a Measure that has an anacrusis that makes the
        first note not beamed.
        '''
        m = stream.Measure()
        m.repeatAppend(note.Note(type='eighth'), 5)
        ts = TimeSignature('2/2')

        beams = ts.getBeams(m, measureStartOffset=1.5)
        self.assertIsNone(beams[0])
        for b in beams[1:]:
            self.assertIsNotNone(b)
        match = '''[None,
        <music21.beam.Beams <music21.beam.Beam 1/start>>,
        <music21.beam.Beams <music21.beam.Beam 1/continue>>,
        <music21.beam.Beams <music21.beam.Beam 1/continue>>,
        <music21.beam.Beams <music21.beam.Beam 1/stop>>]'''
        self.assertTrue(common.whitespaceEqual(str(beams), match))

        m.append(note.Note(type='eighth'))
        beams = ts.getBeams(m, measureStartOffset=1.0)
        match = '''[<music21.beam.Beams <music21.beam.Beam 1/start>>,
        <music21.beam.Beams <music21.beam.Beam 1/stop>>,
        <music21.beam.Beams <music21.beam.Beam 1/start>>,
        <music21.beam.Beams <music21.beam.Beam 1/continue>>,
        <music21.beam.Beams <music21.beam.Beam 1/continue>>,
        <music21.beam.Beams <music21.beam.Beam 1/stop>>]'''
        self.assertTrue(common.whitespaceEqual(str(beams), match), str(beams))

        m = stream.Measure()
        m.repeatAppend(note.Note(type='eighth'), 5)
        ts = TimeSignature('3/2')

        beams = ts.getBeams(m, measureStartOffset=3.5)
        match = '''[None,
        <music21.beam.Beams <music21.beam.Beam 1/start>>,
        <music21.beam.Beams <music21.beam.Beam 1/continue>>,
        <music21.beam.Beams <music21.beam.Beam 1/continue>>,
        <music21.beam.Beams <music21.beam.Beam 1/stop>>]'''
        self.assertTrue(common.whitespaceEqual(str(beams), match))


        m = stream.Measure()
        m.repeatAppend(note.Note(type='eighth'), 4)
        ts = TimeSignature('6/8')
        beams = ts.getBeams(m, measureStartOffset=1.0)
        match = '''[None,
        <music21.beam.Beams <music21.beam.Beam 1/start>>,
        <music21.beam.Beams <music21.beam.Beam 1/continue>>,
        <music21.beam.Beams <music21.beam.Beam 1/stop>>]'''
        self.assertTrue(common.whitespaceEqual(str(beams), match))

        m.append(note.Note(type='eighth'))
        beams = ts.getBeams(m, measureStartOffset=0.5)
        match = '''[<music21.beam.Beams <music21.beam.Beam 1/start>>,
        <music21.beam.Beams <music21.beam.Beam 1/stop>>,
        <music21.beam.Beams <music21.beam.Beam 1/start>>,
        <music21.beam.Beams <music21.beam.Beam 1/continue>>,
        <music21.beam.Beams <music21.beam.Beam 1/stop>>]'''
        self.assertTrue(common.whitespaceEqual(str(beams), match), str(beams))


    def testOffsetToDepth(self):
        # get a maximally divided 4/4 to the level of 1/8
        a = MeterSequence('4/4')
        for h in range(len(a)):
            a[h] = a[h].subdivide(2)
            for i in range(len(a[h])):
                a[h][i] = a[h][i].subdivide(2)
                for j in range(len(a[h][i])):
                    a[h][i][j] = a[h][i][j].subdivide(2)

        # matching with starts result in a Lerdahl-Jackendoff style depth
        match = [4, 1, 2, 1, 3, 1, 2, 1]
        for x in range(8):
            pos = x * 0.5
            test = a.offsetToDepth(pos, align='start')
            self.assertEqual(test, match[x])

        match = [1, 2, 1, 3, 1, 2, 1]
        for x in range(7):
            pos = (x * 0.5) + 0.5
            test = a.offsetToDepth(pos, align='end')
            # environLocal.printDebug(['here', test])
            self.assertEqual(test, match[x])

        # can quantize by lowest value
        match = [4, 1, 2, 1, 3, 1, 2, 1]
        for x in range(8):
            pos = (x * 0.5) + 0.25
            test = a.offsetToDepth(pos, align='quantize')
            self.assertEqual(test, match[x])

    def testDefaultBeatPartitions(self):
        src = ['2/2', '2/4', '2/8', '6/4', '6/8', '6/16']
        for tsStr in src:
            ts = TimeSignature(tsStr)
            self.assertEqual(len(ts.beatSequence), 2)
            self.assertEqual(ts.beatCountName, 'Duple')
            if ts.numerator == 2:
                for ms in ts.beatSequence:  # should be divided in two
                    self.assertEqual(len(ms), 2)
            elif ts.numerator == 6:
                for ms in ts.beatSequence:  # should be divided in three
                    self.assertEqual(len(ms), 3)

        src = ['3/2', '3/4', '9/4', '9/8', '9/16']
        for tsStr in src:
            ts = TimeSignature(tsStr)
            self.assertEqual(len(ts.beatSequence), 3)
            self.assertEqual(ts.beatCountName, 'Triple')
            if ts.numerator == 3:
                for ms in ts.beatSequence:  # should be divided in two
                    self.assertEqual(len(ms), 2)
            elif ts.numerator == 9:
                for ms in ts.beatSequence:  # should be divided in three
                    self.assertEqual(len(ms), 3)

        src = ['3/8', '3/16', '3/32']
        for tsStr in src:
            ts = TimeSignature(tsStr)
            self.assertEqual(len(ts.beatSequence), 1)
            self.assertEqual(ts.beatCountName, 'Single')
            for ms in ts.beatSequence:  # should not be divided
                self.assertIsInstance(ms, MeterTerminal)

        src = ['4/2', '4/4', '4/8', '12/4', '12/8', '12/16']
        for tsStr in src:
            ts = TimeSignature(tsStr)
            self.assertEqual(len(ts.beatSequence), 4)
            self.assertEqual(ts.beatCountName, 'Quadruple')
            if ts.numerator == 4:
                for ms in ts.beatSequence:  # should be divided in two
                    self.assertEqual(len(ms), 2)
            elif ts.numerator == 12:
                for ms in ts.beatSequence:  # should be divided in three
                    self.assertEqual(len(ms), 3)

        src = ['5/2', '5/4', '5/8', '15/4', '15/8', '15/16']
        for tsStr in src:
            ts = TimeSignature(tsStr)
            self.assertEqual(len(ts.beatSequence), 5)
            self.assertEqual(ts.beatCountName, 'Quintuple')
            if ts.numerator == 5:
                for ms in ts.beatSequence:  # should be divided in two
                    self.assertEqual(len(ms), 2)
            elif ts.numerator == 15:
                for ms in ts.beatSequence:  # should be divided in three
                    self.assertEqual(len(ms), 3)

        src = ['18/4', '18/8', '18/16']
        for tsStr in src:
            ts = TimeSignature(tsStr)
            self.assertEqual(len(ts.beatSequence), 6)
            self.assertEqual(ts.beatCountName, 'Sextuple')
            if ts.numerator == 18:
                for ms in ts.beatSequence:  # should be divided in three
                    self.assertEqual(len(ms), 3)

        # odd or unusual partitions
        src = ['13/4', '19/8', '17/16']
        for tsStr in src:
            firstPart, unused = tsStr.split('/')
            ts = TimeSignature(tsStr)
            # self.assertEqual(len(ts.beatSequence), 6)
            self.assertEqual(ts.beatCountName, firstPart + '-uple')  # "13-uple" etc.

    def testBeatProportionFromTimeSignature(self):
        # given meter, ql, beat proportion, and beat ql
        data = [
            ['2/4', (0, 0.5, 1, 1.5), (1, 1.5, 2, 2.5), (1, 1, 1, 1)],
            ['3/4', (0, 0.5, 1, 1.5), (1, 1.5, 2, 2.5), (1, 1, 1, 1)],
            ['4/4', (0, 0.5, 1, 1.5), (1, 1.5, 2, 2.5), (1, 1, 1, 1)],

            ['6/8', (0, 0.5, 1, 1.5, 2), (1, 4 / 3, 5 / 3, 2.0, 7 / 3), (1.5, 1.5, 1.5, 1.5, 1.5)],
            ['9/8', (0, 0.5, 1, 1.5, 2), (1, 4 / 3, 5 / 3, 2.0, 7 / 3), (1.5, 1.5, 1.5, 1.5, 1.5)],
            ['12/8', (0, 0.5, 1, 1.5, 2), (1, 4 / 3, 5 / 3, 2.0, 7 / 3), (1.5, 1.5, 1.5, 1.5, 1.5)],

            ['2/8+3/8', (0, 0.5, 1, 1.5), (1, 1.5, 2, 7 / 3), (1, 1, 1.5, 1.5, 1.5)],
        ]

        for tsStr, src, dst, beatDur in data:
            ts = TimeSignature(tsStr)
            for i in range(len(src)):
                ql = src[i]
                self.assertAlmostEqual(ts.getBeatProportion(ql), dst[i], 4)
                self.assertEqual(ts.getBeatDuration(ql).quarterLength,
                                 beatDur[i])

    def testSubdividePartitionsEqual(self):
        ms = MeterSequence('2/4')
        ms.subdividePartitionsEqual(None)
        self.assertEqual(str(ms), '{{1/4+1/4}}')

        ms = MeterSequence('3/4')
        ms.subdividePartitionsEqual(None)
        self.assertEqual(str(ms), '{{1/4+1/4+1/4}}')

        ms = MeterSequence('6/8')
        ms.subdividePartitionsEqual(None)
        self.assertEqual(str(ms), '{{3/8+3/8}}')

        ms = MeterSequence('6/16')
        ms.subdividePartitionsEqual(None)
        self.assertEqual(str(ms), '{{3/16+3/16}}')

        ms = MeterSequence('3/8+3/8')
        ms.subdividePartitionsEqual(None)
        self.assertEqual(str(ms), '{{1/8+1/8+1/8}+{1/8+1/8+1/8}}')

        ms = MeterSequence('2/8+3/8')
        ms.subdividePartitionsEqual(None)
        self.assertEqual(str(ms), '{{1/8+1/8}+{1/8+1/8+1/8}}')

        ms = MeterSequence('5/8')
        ms.subdividePartitionsEqual(None)
        self.assertEqual(str(ms), '{{1/8+1/8+1/8+1/8+1/8}}')

        ms = MeterSequence('3/8+3/4')
        ms.subdividePartitionsEqual(None)  # can partition by another
        self.assertEqual(str(ms), '{{1/8+1/8+1/8}+{1/4+1/4+1/4}}')

    def testSetDefaultAccentWeights(self):
        # these tests take the level to 3. in some cases, a level of 2
        # is not sufficient to normalize all denominators
        pairs = [
            ('4/4', [1.0, 0.125, 0.25, 0.125, 0.5, 0.125, 0.25, 0.125]),

            ('3/4', [1.0, 0.125, 0.25, 0.125, 0.5, 0.125, 0.25, 0.125, 0.5, 0.125, 0.25, 0.125]),

            ('2/4', [1.0, 0.125, 0.25, 0.125, 0.5, 0.125, 0.25, 0.125]),

            # divided at 4th 8th
            ('6/8', [1.0, 0.125, 0.25, 0.125, 0.25, 0.125,
                     0.5, 0.125, 0.25, 0.125, 0.25, 0.125]),

            # all beats are even b/c this is un-partitioned
            ('5/4',
             [1.0, 0.125, 0.25, 0.125, 0.5, 0.125, 0.25, 0.125,
              0.5, 0.125, 0.25, 0.125, 0.5, 0.125, 0.25, 0.125, 0.5, 0.125, 0.25, 0.125]),

            ('9/4', [1.0, 0.125, 0.25, 0.125, 0.25, 0.125,
                     0.5, 0.125, 0.25, 0.125, 0.25, 0.125,
                     0.5, 0.125, 0.25, 0.125, 0.25, 0.125]),

            ('18/4', [1.0, 0.125, 0.25, 0.125, 0.25, 0.125,
                      0.5, 0.125, 0.25, 0.125, 0.25, 0.125,
                      0.5, 0.125, 0.25, 0.125, 0.25, 0.125,
                      0.5, 0.125, 0.25, 0.125, 0.25, 0.125,
                      0.5, 0.125, 0.25, 0.125, 0.25, 0.125,
                      0.5, 0.125, 0.25, 0.125, 0.25, 0.125]),

            ('3/8', [1.0, 0.125, 0.25, 0.125, 0.5, 0.125,
                     0.25, 0.125, 0.5, 0.125, 0.25, 0.125]),

            ('11/8',
             [1.0, 0.125, 0.25, 0.125,
              0.5, 0.125, 0.25, 0.125,
              0.5, 0.125, 0.25, 0.125,
              0.5, 0.125, 0.25, 0.125,
              0.5, 0.125, 0.25, 0.125,
              0.5, 0.125, 0.25, 0.125,
              0.5, 0.125, 0.25, 0.125,
              0.5, 0.125, 0.25, 0.125,
              0.5, 0.125, 0.25, 0.125,
              0.5, 0.125, 0.25, 0.125,
              0.5, 0.125, 0.25, 0.125]),


            ('2/8+3/8',
             [1.0, 0.125, 0.25, 0.125,
              0.5, 0.125, 0.25, 0.125, 0.25, 0.125]),

            ('3/8+2/8+3/4',
             [1.0, 0.0625, 0.125, 0.0625, 0.25, 0.0625, 0.125, 0.0625,
              0.25, 0.0625, 0.125, 0.0625,
              0.5, 0.0625, 0.125, 0.0625, 0.25, 0.0625, 0.125, 0.0625,

              0.5, 0.03125, 0.0625, 0.03125, 0.125, 0.03125, 0.0625, 0.03125,
              0.25, 0.03125, 0.0625, 0.03125, 0.125, 0.03125, 0.0625, 0.03125,
              0.25, 0.03125, 0.0625, 0.03125, 0.125, 0.03125, 0.0625, 0.03125
              ]),


            ('1/2+2/16',
             [1.0, 0.015625, 0.03125, 0.015625, 0.0625, 0.015625, 0.03125, 0.015625,
              0.125, 0.015625, 0.03125, 0.015625, 0.0625, 0.015625, 0.03125, 0.015625,
              0.25, 0.015625, 0.03125, 0.015625, 0.0625, 0.015625, 0.03125, 0.015625,
              0.125, 0.015625, 0.03125, 0.015625, 0.0625, 0.015625, 0.03125, 0.015625,

              0.5, 0.0625, 0.125, 0.0625, 0.25, 0.0625, 0.125, 0.0625]),


        ]

        for tsStr, match in pairs:
            # environLocal.printDebug([tsStr])
            ts1 = TimeSignature(tsStr)
            ts1._setDefaultAccentWeights(3)  # going to a lower level here
            self.assertEqual([mt.weight for mt in ts1.accentSequence], match)

    def testMusicxmlDirectOut(self):
        # test rendering musicxml directly from meter
        from music21.musicxml import m21ToXml

        ts = TimeSignature('3/8')
        xmlOut = m21ToXml.GeneralObjectExporter().parse(ts).decode('utf-8')

        match = '<time><beats>3</beats><beat-type>8</beat-type></time>'
        xmlOut = xmlOut.replace(' ', '')
        xmlOut = xmlOut.replace('\n', '')
        self.assertNotEqual(xmlOut.find(match), -1)

    def testSlowSixEight(self):
        from music21 import meter
        # create a meter with 6 beats but beams in 2 groups
        ts = meter.TimeSignature('6/8')
        ts.beatSequence.partition(6)
        self.assertEqual(str(ts.beatSequence), '{1/8+1/8+1/8+1/8+1/8+1/8}')
        self.assertEqual(str(ts.beamSequence), '{3/8+3/8}')

        # check that beats are calculated properly
        m = stream.Measure()
        m.timeSignature = ts
        n = note.Note(quarterLength=0.5)
        m.repeatAppend(n, 6)
        match = [n.beatStr for n in m.notes]
        self.assertEqual(match, ['1', '2', '3', '4', '5', '6'])
        m.makeBeams(inPlace=True)
        # m.show()
        # try with extra creation args
        ts = meter.TimeSignature('slow 6/8')
        self.assertEqual(ts.beatDivisionCountName, 'Simple')
        self.assertEqual(
            str(ts.beatSequence),
            '{{1/16+1/16}+{1/16+1/16}+{1/16+1/16}+{1/16+1/16}+{1/16+1/16}+{1/16+1/16}}'
        )

        ts = meter.TimeSignature('6/8')
        self.assertEqual(ts.beatDivisionCountName, 'Compound')
        self.assertEqual(str(ts.beatSequence), '{{1/8+1/8+1/8}+{1/8+1/8+1/8}}')

        ts = meter.TimeSignature('6/8 fast')
        self.assertEqual(ts.beatDivisionCountName, 'Compound')
        self.assertEqual(str(ts.beatSequence), '{{1/8+1/8+1/8}+{1/8+1/8+1/8}}')

    def testMixedDurationsBeams(self):
        fourFour = TimeSignature('4/4')
        n = note.Note
        dList = [n(type='eighth'), n(type='quarter'), n(type='eighth'),
                 n(type='eighth'), n(type='quarter'), n(type='eighth')]
        beamList = fourFour.getBeams(dList)
        self.assertEqual(beamList, [None] * 6)

        dList = [n(type='eighth'), n(type='quarter'), n(type='eighth'),
                 n(type='eighth'), n(type='eighth'), n(type='quarter')]
        beamList = fourFour.getBeams(dList)
        self.assertEqual([repr(b) for b in beamList],
                         ['None', 'None', 'None',
                          '<music21.beam.Beams <music21.beam.Beam 1/start>>',
                          '<music21.beam.Beams <music21.beam.Beam 1/stop>>',
                          'None'])

    def testMixedDurationBeams2(self):
        from music21 import converter
        bm = converter.parse('tinyNotation: 3/8 b8 c16 r e. d32').flatten()
        bm2 = bm.makeNotation()
        beamList = [n.beams for n in bm2.recurse().notes]
        self.assertEqual(
            [repr(b) for b in beamList],
            ['<music21.beam.Beams <music21.beam.Beam 1/start>>',
             '<music21.beam.Beams <music21.beam.Beam 1/stop>/<music21.beam.Beam 2/partial/left>>',
             '<music21.beam.Beams <music21.beam.Beam 1/start>/<music21.beam.Beam 2/start>>',
             '<music21.beam.Beams <music21.beam.Beam 1/stop>/<music21.beam.Beam 2/stop>/'
             + '<music21.beam.Beam 3/partial/left>>', ]
        )

        bm = converter.parse("tinyNotation: 2/4 b16 c' b a g f# g r")
        bm2 = bm.makeNotation()
        beamList = [n.beams for n in bm2.recurse().notes]
        beamListRepr = [str(i) + ' ' + repr(beamList[i]) for i in range(len(beamList))]
        self.maxDiff = 2000
        self.assertEqual(beamListRepr, [
            '0 <music21.beam.Beams <music21.beam.Beam 1/start>/<music21.beam.Beam 2/start>>',
            '1 <music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/stop>>',
            '2 <music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/start>>',
            '3 <music21.beam.Beams <music21.beam.Beam 1/stop>/<music21.beam.Beam 2/stop>>',
            '4 <music21.beam.Beams <music21.beam.Beam 1/start>/<music21.beam.Beam 2/start>>',
            '5 <music21.beam.Beams <music21.beam.Beam 1/continue>/<music21.beam.Beam 2/continue>>',
            '6 <music21.beam.Beams <music21.beam.Beam 1/stop>/<music21.beam.Beam 2/stop>>',
        ])

    def testBestTimeSignature(self):
        from music21 import converter
        from music21 import meter
        s6 = converter.parse('C4 D16.', format='tinyNotation').flatten().notes
        m6 = stream.Measure()
        for el in s6:
            m6.insert(el.offset, el)
        ts6 = meter.bestTimeSignature(m6)
        self.assertEqual(repr(ts6), '<music21.meter.TimeSignature 11/32>')

    def testBestTimeSignatureB(self):
        '''
        Correct the TimeSignatures (4/4 in m. 1; no others) in a 4-measure score
        of 12, 11.5, 12, 13 quarters, where one of the parts is a PartStaff with
        multiple voices.
        '''
        from music21 import corpus
        faulty = corpus.parse('demos/incorrect_time_signature_pv')
        for m in faulty.recurse().getElementsByClass('Measure'):
            m.timeSignature = m.bestTimeSignature()
        p1 = faulty.parts[1]
        tsReps = []
        for m in p1.getElementsByClass('Measure'):
            tsReps.append(repr(m.timeSignature))
        self.assertEqual(tsReps, ['<music21.meter.TimeSignature 12/4>',
                                  '<music21.meter.TimeSignature 23/8>',
                                  '<music21.meter.TimeSignature 12/4>',
                                  '<music21.meter.TimeSignature 13/4>'])

    def testBestTimeSignatureDoubleDotted(self):
        from music21 import converter
        from music21 import meter

        s6 = converter.parse('C4.', format='tinyNotation').flatten().notes
        m6 = stream.Measure()
        for el in s6:
            m6.insert(el.offset, el)
        ts6 = meter.bestTimeSignature(m6)
        self.assertEqual(repr(ts6), '<music21.meter.TimeSignature 3/8>')

        s6 = converter.parse('C2..', format='tinyNotation').flatten().notes
        m6 = stream.Measure()
        for el in s6:
            m6.insert(el.offset, el)
        ts6 = meter.bestTimeSignature(m6)
        self.assertEqual(repr(ts6), '<music21.meter.TimeSignature 7/8>')

        s6 = converter.parse('C2...', format='tinyNotation').flatten().notes
        m6 = stream.Measure()
        for el in s6:
            m6.insert(el.offset, el)
        ts6 = meter.bestTimeSignature(m6)
        self.assertEqual(repr(ts6), '<music21.meter.TimeSignature 15/16>')

    def testBestTimeSignatureDoubleDottedB(self):
        '''
        These add up the same as testBestTimeSignatureDoubleDotted, but
        use multiple notes.
        '''
        from music21 import converter
        from music21 import meter
        s6 = converter.parse('C2 D4 E8', format='tinyNotation').flatten().notes
        m6 = stream.Measure()
        for el in s6:
            m6.insert(el.offset, el)
        ts6 = meter.bestTimeSignature(m6)
        self.assertEqual(repr(ts6), '<music21.meter.TimeSignature 7/8>')

        s6 = converter.parse('C2 D4 E8 F16', format='tinyNotation').flatten().notes
        m6 = stream.Measure()
        for el in s6:
            m6.insert(el.offset, el)
        ts6 = meter.bestTimeSignature(m6)
        self.assertEqual(repr(ts6), '<music21.meter.TimeSignature 15/16>')

    def testBestTimeSignatureDoubleDottedC(self):
        '''
        These add up the same as testBestTimeSignatureDoubleDotted, but
        use multiple notes which are dotted divisions of the original
        '''
        from music21 import converter
        from music21 import meter

        s6 = converter.parse('C4.. D4..', format='tinyNotation').flatten().notes
        m6 = stream.Measure()
        for el in s6:
            m6.insert(el.offset, el)
        ts6 = meter.bestTimeSignature(m6)
        self.assertEqual(repr(ts6), '<music21.meter.TimeSignature 7/8>')

        s6 = converter.parse('C4... D4...', format='tinyNotation').flatten().notes
        m6 = stream.Measure()
        for el in s6:
            m6.insert(el.offset, el)
        ts6 = meter.bestTimeSignature(m6)
        self.assertEqual(repr(ts6), '<music21.meter.TimeSignature 15/16>')

    def testCompoundSameDenominator(self):
        ts328 = TimeSignature('3+2/8')
        beatSeq = ts328.beamSequence
        self.assertEqual(str(beatSeq), '{3/8+2/8}')



if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
