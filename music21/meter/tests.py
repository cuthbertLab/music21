# -----------------------------------------------------------------------------
# Name:         meter.tests.py
# Purpose:      Tests of meter
#
# Authors:      Christopher Ariza
#               Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2009-2026 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
from __future__ import annotations

import copy
import random
import unittest
from unittest import mock

from music21 import common
from music21 import duration
from music21.exceptions21 import MeterException
from music21 import note
from music21 import stream
from music21.meter.base import TimeSignature
from music21.meter.core import (
    MeterSequence, MeterTerminal, getMeterSequence, getMeterTerminal,
)

class TestExternal(unittest.TestCase):
    show = True

    def testSingle(self):
        '''
        Need to test direct meter creation w/o stream
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
                numerator = random.choice(meterStrNumerator)
                denominator = random.choice(meterStrDenominator)
                msg.append(f'{numerator}/{denominator}')
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
    def testMeterSubdivision(self):
        a = MeterSequence('4/4', 4)
        self.assertEqual(str(a), '{1/4+1/4+1/4+1/4}')

        a = a.setIndex(0, a[0].subdivide(2))
        self.assertEqual(str(a), '{{1/8+1/8}+1/4+1/4+1/4}')

        a = a.setIndex(3, a[3].subdivide(4))
        self.assertEqual(str(a), '{{1/8+1/8}+1/4+1/4+{1/16+1/16+1/16+1/16}}')

    def testGetItemNegativeIndex(self):
        # ms[-len(ms)] raised IndexError, so ms[-1] on a single part did too
        ms = MeterSequence('3/8+2/8+1/8')
        self.assertEqual(str(ms[-1]), '1/8')
        self.assertEqual(str(ms[-3]), '3/8')
        self.assertEqual(str(MeterSequence('4/4')[-1]), '4/4')
        for outOfRange in (3, -4):
            with self.assertRaisesRegex(IndexError, str(outOfRange), msg=outOfRange):
                unused_part = ms[outOfRange]

    def testPartitionOptionsAddUpToMeter(self):
        # 18/4 offered 4/4+4/4+4/4+4/4 (only 16/4); 14/8 offered 3/8 four times (only 12/8)
        for meterString in ('18/4', '14/8'):
            ms = MeterSequence(meterString)
            for option in ms.getPartitionOptions():
                self.assertEqual(MeterSequence(list(option)).duration.quarterLength,
                                 ms.duration.quarterLength,
                                 f'{meterString}: {option}')

        # no way left to make four parts of 18/4, so raise or use the default
        with self.assertRaises(MeterException):
            MeterSequence('18/4').partitionedByCount(4, loadDefault=False)
        self.assertEqual(str(MeterSequence('18/4').partitionedByCount(4)),
                         '{' + '+'.join(['3/4'] * 6) + '}')

    def testMeterSequenceDeepcopy(self):
        a = MeterSequence('4/4', 4)
        b = copy.deepcopy(a)
        # a MeterSequence is immutable, so deepcopy returns the same object
        self.assertIs(a, b)
        self.assertEqual(a, b)

    def testTimeSignatureDeepcopy(self):
        c = TimeSignature('4/4')
        d = copy.deepcopy(c)
        self.assertIsNot(c, d)
        self.assertEqual(c, d)

        e = TimeSignature('slow 6/8')
        f = TimeSignature('fast 6/8')
        self.assertNotEqual(e, f)

    def testMeterTerminalCache(self):
        a = getMeterTerminal(1, 4)
        self.assertIs(a, getMeterTerminal(1, 4))
        self.assertEqual(a, getMeterTerminal(numerator=1, denominator=4, weight=1.0))
        b = getMeterTerminal(1, 4, weight=0.5)
        self.assertIsNot(a, b)
        self.assertIs(b, getMeterTerminal(1, 4, weight=0.5))
        # equal however they were made
        self.assertEqual(MeterTerminal('1/4'), getMeterTerminal(1, 4))

    def testMeterTerminalModify(self):
        a = getMeterTerminal(2, 4, weight=0.5)
        # modify changes only what is named; the rest carries over
        b = a.modify(weight=0.25)
        self.assertEqual((b.numerator, b.denominator, b.weight), (2, 4, 0.25))
        c = a.modify(numerator=3)
        self.assertEqual((c.numerator, c.denominator, c.weight), (3, 4, 0.5))
        # the original is unchanged and setting an attribute raises
        self.assertEqual(a.weight, 0.5)
        with self.assertRaises(TypeError):
            a.weight = 0.25
        # asking again gives the same object; __replace__ is the same as modify
        self.assertIs(a.modify(weight=0.25), b)
        self.assertIs(a.__replace__(numerator=3), c)
        # any other keyword raises
        with self.assertRaises(ValueError):
            a.modify(parenthesis=True)

    def testMeterSequenceCache(self):
        from music21.meter.base import _defaultSequenceCache
        ms = getMeterSequence('4/4', 4)
        self.assertIs(getMeterSequence('4/4', 4), ms)
        # TimeSignature.load caches (display, beam, beat, accent) sequences by
        # (value, divisions); a second 4/4 uses the same ones
        a = TimeSignature('4/4')
        display, beam, beat, accent = _defaultSequenceCache[('4/4', None)]
        self.assertIs(a.displaySequence, display)
        self.assertIs(a.beamSequence, beam)
        self.assertIs(a.beatSequence, beat)
        self.assertIs(a.accentSequence, accent)
        b = TimeSignature('4/4')
        for seqName in ('beamSequence', 'beatSequence',
                        'accentSequence', 'displaySequence'):
            self.assertIs(getattr(a, seqName), getattr(b, seqName), seqName)

    def testCachesAreBounded(self):
        from music21.meter import base as meterBase
        cache = meterBase._defaultSequenceCache
        first = TimeSignature('4/4')
        with mock.patch.object(meterBase, '_DEFAULT_SEQUENCE_CACHE_SIZE', 4):
            for numerator in range(1, 9):
                TimeSignature(f'{numerator}/64')
                TimeSignature('4/4')
            self.assertLessEqual(len(cache), 4)
            self.assertIn(('4/4', None), cache)
            self.assertNotIn(('1/64', None), cache)
            self.assertIs(TimeSignature('4/4').beatSequence, first.beatSequence)
            evicted = TimeSignature('1/64')
            self.assertEqual(evicted.beatSequence, MeterSequence('1/64'))

    def testHashIsCached(self):
        import pickle
        a = MeterSequence('6/8', 2)
        b = MeterSequence('6/8', 2)
        self.assertIsNone(a._frozenHash)
        h = hash(a)
        self.assertEqual(a._frozenHash, h)
        self.assertEqual(hash(a), h)
        self.assertIsNone(b._frozenHash)
        self.assertEqual(a, b)
        self.assertEqual(hash(b), h)
        self.assertNotIn('_frozenHash', a._getSlotsRecursive())
        self.assertNotIn('_frozenHash', a.__getstate__())
        self.assertIs(copy.deepcopy(a), a)
        for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
            loaded = pickle.loads(pickle.dumps(a, protocol))
            self.assertIsNone(loaded._frozenHash, protocol)
            self.assertEqual(loaded, a)
            self.assertEqual(hash(loaded), h)
        mt = MeterTerminal('3/8')
        self.assertIsNone(mt._frozenHash)
        self.assertEqual(hash(mt), mt._frozenHash)
        fd = duration.FrozenDuration(1.5)
        self.assertIsNone(fd._frozenHash)
        self.assertEqual(hash(fd), fd._frozenHash)
        self.assertEqual(hash(fd), hash(duration.FrozenDuration(1.5)))

    def testMeterSequenceModify(self):
        a = MeterSequence('4/4', 4)
        self.assertFalse(a.parenthesis)
        b = a.modify(parenthesis=True)
        self.assertTrue(b.parenthesis)
        self.assertFalse(a.parenthesis)  # original unchanged
        # setting an attribute raises
        with self.assertRaises(TypeError):
            a.parenthesis = True
        # two separate sequences modified the same way give the same object
        self.assertIs(b, MeterSequence('4/4', 4).modify(parenthesis=True))
        # numerator, denominator, and weight come from the partition, so they raise
        for kw in ({'numerator': 3}, {'denominator': 8}, {'weight': 1.5}):
            with self.assertRaises(ValueError):
                a.modify(**kw)

    def testBarDurationCannotBeChanged(self):
        # changing the copy that barDuration used to return was silently lost
        ts = TimeSignature('3/4')
        self.assertIsInstance(ts.barDuration, duration.FrozenDuration)
        with self.assertRaises(TypeError):
            ts.barDuration.quarterLength = 7.0
        self.assertEqual(ts.barDuration.quarterLength, 3.0)
        self.assertEqual(ts.barDuration, duration.Duration(3.0))

        # an assigned duration is returned as given
        override = duration.Duration(7.0)
        ts.barDuration = override
        self.assertIs(ts.barDuration, override)

    def testEmptySequenceDuration(self):
        self.assertEqual(MeterSequence().duration.quarterLength, 0.0)

    def testModifyDenominatorMustBePowerOfTwo(self):
        a = MeterTerminal('3/4')
        self.assertEqual(a.modify(denominator=256).denominator, 256)
        for badDenominator in (0, 7, 12):
            with self.assertRaises(MeterException):
                a.modify(denominator=badDenominator)

    def testNoneIsFourFour(self):
        self.assertEqual(TimeSignature(None).ratioString, '4/4')

    def testInPlaceFormsRaise(self):
        ts = TimeSignature('6/8')
        before = ts.beatSequence
        removed = [
            ('partition', (6,), 'partitioned'),
            ('partitionByCount', (6,), 'partitionedByCount'),
            ('partitionByList', ([1, 1, 1, 1, 1, 1],), 'partitionedByList'),
            ('partitionByOtherMeterSequence', (MeterSequence('6/8', 6),),
             'partitionedByOtherMeterSequence'),
            ('subdividePartitionsEqual', (3,), 'subdividedPartitionsEqual'),
            ('subdivideNestedHierarchy', (3,), 'subdividedNestedHierarchy'),
            ('setLevelWeight', ([1, 2],), 'withLevelWeight'),
        ]
        for oldName, arguments, newName in removed:
            with self.assertRaisesRegex(MeterException, newName + '[(][)]', msg=oldName):
                getattr(ts.beatSequence, oldName)(*arguments)
            getattr(ts.beatSequence, newName)(*arguments)
        self.assertIs(ts.beatSequence, before)

        with self.assertRaisesRegex(MeterException, r"MeterSequence\('4/4'\)"):
            MeterSequence().load('4/4')
        with self.assertRaisesRegex(TypeError, r'setIndex\(0, value\)'):
            ts.beatSequence[0] = ts.beatSequence[0].subdivide(3)

        mt = MeterTerminal('3/4')
        for attribute, value in (('numerator', 2), ('denominator', 8), ('weight', 0.5),
                                 ('duration', duration.Duration(2.0))):
            with self.assertRaises(TypeError, msg=attribute):
                setattr(mt, attribute, value)
        for attribute, value in (('weight', 0.5), ('parenthesis', True),
                                 ('summedNumerator', True)):
            with self.assertRaises(TypeError, msg=attribute):
                setattr(ts.beatSequence, attribute, value)
        self.assertIs(ts.beatSequence, before)
        self.assertEqual(str(mt), '3/4')

    def testDefaultBeamsLargeCompoundMeter(self):
        # 24/8 had 8 beats under one unbroken beam; only numerators through 21 grouped in threes
        ts = TimeSignature('24/8')
        self.assertEqual(str(ts.beamSequence), '{' + '+'.join(['3/8'] * 8) + '}')
        self.assertEqual(len(ts.beamSequence), ts.beatCount)
        # not a multiple of 3: beam all together
        self.assertEqual(str(TimeSignature('20/8').beamSequence), '{20/8}')

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
        def recSub(node, remaining):
            # subdivide node by 2, `remaining` levels deep
            if remaining == 0:
                return node
            sub = node.subdivide(2)
            for idx in range(len(sub)):
                sub = sub.setIndex(idx, recSub(sub[idx], remaining - 1))
            return sub

        a = MeterSequence('4/4')
        for h in range(len(a)):
            a = a.setIndex(h, recSub(a[h], 3))

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
        ms = MeterSequence('2/4').subdividedPartitionsEqual(None)
        self.assertEqual(str(ms), '{{1/4+1/4}}')

        ms = MeterSequence('3/4').subdividedPartitionsEqual(None)
        self.assertEqual(str(ms), '{{1/4+1/4+1/4}}')

        ms = MeterSequence('6/8').subdividedPartitionsEqual(None)
        self.assertEqual(str(ms), '{{3/8+3/8}}')

        ms = MeterSequence('6/16').subdividedPartitionsEqual(None)
        self.assertEqual(str(ms), '{{3/16+3/16}}')

        ms = MeterSequence('3/8+3/8').subdividedPartitionsEqual(None)
        self.assertEqual(str(ms), '{{1/8+1/8+1/8}+{1/8+1/8+1/8}}')

        ms = MeterSequence('2/8+3/8').subdividedPartitionsEqual(None)
        self.assertEqual(str(ms), '{{1/8+1/8}+{1/8+1/8+1/8}}')

        ms = MeterSequence('5/8').subdividedPartitionsEqual(None)
        self.assertEqual(str(ms), '{{1/8+1/8+1/8+1/8+1/8}}')

        ms = MeterSequence('3/8+3/4').subdividedPartitionsEqual(None)  # can partition by another
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
        ts.beatSequence = ts.beatSequence.partitioned(6)
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
        for m in faulty.recurse().getElementsByClass(stream.Measure):
            m.timeSignature = m.bestTimeSignature()
        p1 = faulty.parts[1]
        tsReps = []
        for m in p1.getElementsByClass(stream.Measure):
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

    def testEquality(self):
        '''
        Additional tests of TimeSignature object equality.
        Apart from this and the doc tests,
        see also testTimeSignatureDeepcopy for a test of
        time signatures with different structure with same ratioString
        (fast vs slow 6/8).
        '''

        # 5/8: but different internal structure

        oneKindOf5 = TimeSignature('2+3/8')
        sameKindOf5 = TimeSignature('2+3/8')
        self.assertEqual(oneKindOf5.ratioString, '2/8+3/8')
        self.assertEqual(str(oneKindOf5.beatSequence), '{{1/8+1/8}+{1/8+1/8+1/8}}')
        self.assertEqual(sameKindOf5.ratioString, '2/8+3/8')
        self.assertEqual(str(sameKindOf5.beatSequence), '{{1/8+1/8}+{1/8+1/8+1/8}}')
        self.assertEqual(oneKindOf5, sameKindOf5)

        otherKindOf5 = TimeSignature('3+2/8')
        self.assertEqual(otherKindOf5.ratioString, '3/8+2/8')
        self.assertEqual(str(otherKindOf5.beatSequence), '{{1/8+1/8+1/8}+{1/8+1/8}}')
        self.assertNotEqual(oneKindOf5, otherKindOf5)

        # 4/4: same internal structure, different written time signature.

        oneKindOf44 = TimeSignature('4/4')
        sameKindOf44 = TimeSignature()
        self.assertEqual(oneKindOf44, sameKindOf44)

        otherKindOf44 = TimeSignature('Cut')
        self.assertEqual(otherKindOf44.ratioString, '2/2')
        self.assertNotEqual(oneKindOf5, otherKindOf44)
        # Likewise, Different 'symbol'
        self.assertNotEqual(TimeSignature('Cut'), TimeSignature('2/2'))

        # Completely different class (either way round)

        self.assertNotEqual(TimeSignature(), note.Note())
        self.assertNotEqual(note.Note(), TimeSignature())
        # NB: not self.assertRaises(AttributeError). Do we want that instead?


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
