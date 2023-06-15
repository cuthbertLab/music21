# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         test.test_pitch.py
# Purpose:      music21 tests for pitches
#
# Authors:      Michael Scott Asato Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2008-2023 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
from __future__ import annotations

import copy
import unittest

from music21 import common
from music21 import converter
from music21 import corpus
from music21 import key
from music21 import note
from music21 import pitch
from music21 import scale
from music21 import stream
from music21.musicxml import m21ToXml
from music21.pitch import Pitch, Accidental


class Test(unittest.TestCase):

    def testCopyManually(self):
        p1 = Pitch('C#3')
        p2 = copy.deepcopy(p1)
        self.assertIsNot(p1, p2)
        self.assertIsNot(p1.accidental, p2.accidental)

    def testRepr(self):
        p = pitch.Pitch('B#3')
        self.assertEqual(repr(p), '<music21.pitch.Pitch B#3>')

    def testOctave(self):
        b = Pitch('B#3')
        self.assertEqual(b.octave, 3)

    def testAccidentalImport(self):
        '''
        Test that we are getting the properly set accidentals
        '''
        s = corpus.parse('bwv438.xml')
        tenorMeasures = s.parts[2].getElementsByClass(stream.Measure)
        pAltered = tenorMeasures[0].pitches[1]
        self.assertEqual(pAltered.accidental.name, 'flat')
        self.assertEqual(pAltered.accidental.displayType, 'normal')
        # in key signature, so should not be shown
        self.assertFalse(pAltered.accidental.displayStatus)

        altoM6 = s.parts[1].measure(6)
        pAltered = altoM6.pitches[2]
        self.assertEqual(pAltered.accidental.name, 'sharp')
        self.assertTrue(pAltered.accidental.displayStatus)

    def testUpdateAccidentalDisplaySimple(self):
        '''
        Test updating accidental display.
        '''
        past = [Pitch('A#3'), Pitch('C#'), Pitch('C')]

        a = Pitch('c')
        a.accidental = Accidental('natural')
        a.accidental.displayStatus = True
        self.assertEqual(a.name, 'C')
        self.assertTrue(a.accidental.displayStatus)

        a.updateAccidentalDisplay(pitchPast=past, overrideStatus=True)
        self.assertFalse(a.accidental.displayStatus)

        b = copy.deepcopy(a)
        self.assertFalse(b.accidental.displayStatus)
        self.assertEqual(b.accidental.name, 'natural')

    def testUpdateAccidentalDisplaySeries(self):
        '''
        Test updating accidental display.
        '''
        def proc(_pList, past):
            for p in _pList:
                p.updateAccidentalDisplay(pitchPast=past)
                past.append(p)

        def compare(past, _result):
            # environLocal.printDebug(['accidental compare'])
            for i in range(len(_result)):
                p = past[i]
                if p.accidental is None:
                    pName = None
                    pDisplayStatus = None
                else:
                    pName = p.accidental.name
                    pDisplayStatus = p.accidental.displayStatus

                targetName = _result[i][0]
                targetDisplayStatus = _result[i][1]

                self.assertEqual(pName, targetName,
                                 f'name error for {i}: {pName} instead of desired {targetName}')
                self.assertEqual(
                    pDisplayStatus,
                    targetDisplayStatus,
                    f'{i}: {p} display: {pDisplayStatus}, target {targetDisplayStatus}'
                )

        # alternating, in a sequence, same pitch space
        pList = [Pitch('a#3'), Pitch('a3'), Pitch('a#3'),
                 Pitch('a3'), Pitch('a#3')]
        result = [('sharp', True), ('natural', True), ('sharp', True),
                  ('natural', True), ('sharp', True)]
        proc(pList, [])
        compare(pList, result)

        # alternating, in a sequence, different pitch space
        pList = [Pitch('a#2'), Pitch('a6'), Pitch('a#1'),
                 Pitch('a5'), Pitch('a#3')]
        result = [('sharp', True), ('natural', True), ('sharp', True),
                  ('natural', True), ('sharp', True)]
        proc(pList, [])
        compare(pList, result)

        # alternating, after gaps
        pList = [Pitch('a-2'), Pitch('g3'), Pitch('a5'),
                 Pitch('a#5'), Pitch('g-3'), Pitch('a3')]
        result = [('flat', True), (None, None), ('natural', True),
                  ('sharp', True), ('flat', True), ('natural', True)]
        proc(pList, [])
        compare(pList, result)

        # repeats of the same: show at different registers
        pList = [Pitch('a-2'), Pitch('a-2'), Pitch('a-5'),
                 Pitch('a#5'), Pitch('a#3'), Pitch('a3'), Pitch('a2')]
        result = [('flat', True), ('flat', False), ('flat', True),
                  ('sharp', True), ('sharp', True), ('natural', True), ('natural', True)]
        proc(pList, [])
        compare(pList, result)

        # the always- 'unless-repeated' setting
        # first, with no modification, repeated accidentals are not shown
        pList = [Pitch('a-2'), Pitch('a#3'), Pitch('a#5')]
        result = [('flat', True), ('sharp', True), ('sharp', True)]
        proc(pList, [])
        compare(pList, result)

        # second, with status set to always
        pList = [Pitch('a-2'), Pitch('a#3'), Pitch('a#3')]
        pList[2].accidental.displayType = 'always'
        result = [('flat', True), ('sharp', True), ('sharp', True)]
        proc(pList, [])
        compare(pList, result)

        # status set to always
        pList = [Pitch('a2'), Pitch('a3'), Pitch('a5')]
        pList[2].accidental = Accidental('natural')
        pList[2].accidental.displayType = 'always'
        result = [(None, None), (None, None), ('natural', True)]
        proc(pList, [])
        compare(pList, result)

        # first use after other pitches in different register
        # note: this will force the display of the accidental
        pList = [Pitch('a-2'), Pitch('g3'), Pitch('a-5')]
        result = [('flat', True), (None, None), ('flat', True)]
        proc(pList, [])
        compare(pList, result)

        # first use after other pitches in different register
        # note: this will force the display of the accidental
        pList = [Pitch('a-2'), Pitch('g3'), Pitch('a-2')]
        # pairs of accidental, displayStatus
        result = [('flat', True), (None, None), ('flat', True)]
        proc(pList, [])
        compare(pList, result)

        # accidentals, first usage, not first pitch
        pList = [Pitch('a2'), Pitch('g#3'), Pitch('d-2')]
        result = [(None, None), ('sharp', True), ('flat', True)]
        proc(pList, [])
        compare(pList, result)

    def testUpdateAccidentalDisplaySeriesKeySignature(self):
        '''
        Test updating accidental display against a KeySignature
        '''
        def proc(_pList, past, alteredPitches):
            for p in _pList:
                p.updateAccidentalDisplay(pitchPast=past, alteredPitches=alteredPitches)
                past.append(p)

        def compare(past, _result):
            # environLocal.printDebug(['accidental compare'])
            for i in range(len(_result)):
                p = past[i]
                if p.accidental is None:
                    pName = None
                    pDisplayStatus = None
                else:
                    pName = p.accidental.name
                    pDisplayStatus = p.accidental.displayStatus

                targetName = _result[i][0]
                targetDisplayStatus = _result[i][1]

                # environLocal.printDebug(['accidental test:', p, pName,
                #         pDisplayStatus, 'target:', targetName, targetDisplayStatus])
                self.assertEqual(pName, targetName)
                self.assertEqual(
                    pDisplayStatus,
                    targetDisplayStatus,
                    f'{i}: {p} display: {pDisplayStatus}, target {targetDisplayStatus}'
                )

        # chromatic alteration of key
        pList = [Pitch('f#3'), Pitch('f#2'), Pitch('f3'),
                 Pitch('f#3'), Pitch('f#3'), Pitch('g3'), Pitch('f#3')]
        result = [('sharp', False), ('sharp', False), ('natural', True),
                  ('sharp', True), ('sharp', False), (None, None), ('sharp', False)]
        ks = key.KeySignature(1)  # f3
        proc(pList, [], ks.alteredPitches)
        compare(pList, result)

        # non initial scale tones
        pList = [Pitch('a3'), Pitch('b2'), Pitch('c#3'),
                 Pitch('f#3'), Pitch('g#3'), Pitch('f#3'), Pitch('a4')]
        result = [(None, None), (None, None), ('sharp', False),
                  ('sharp', False), ('sharp', False), ('sharp', False), (None, None)]
        ks = key.KeySignature(3)
        proc(pList, [], ks.alteredPitches)
        compare(pList, result)

        # non-initial scale tones with chromatic alteration
        pList = [Pitch('a3'), Pitch('c#3'), Pitch('g#3'),
                 Pitch('g3'), Pitch('c#4'), Pitch('g#4')]
        result = [(None, None), ('sharp', False), ('sharp', False),
                  ('natural', True), ('sharp', False), ('sharp', True)]
        ks = key.KeySignature(3)
        proc(pList, [], ks.alteredPitches)
        compare(pList, result)

        # non-initial scale tones with chromatic alteration
        pList = [Pitch('a3'), Pitch('c#3'), Pitch('g#3'),
                 Pitch('g3'), Pitch('c#4'), Pitch('g#4')]
        result = [(None, None), ('sharp', False), ('sharp', False),
                  ('natural', True), ('sharp', False), ('sharp', True)]
        ks = key.KeySignature(3)
        proc(pList, [], ks.alteredPitches)
        compare(pList, result)

        # initial scale tones with chromatic alteration, repeated tones
        pList = [Pitch('f#3'), Pitch('f3'), Pitch('f#3'),
                 Pitch('g3'), Pitch('f#4'), Pitch('f#4')]
        result = [('sharp', False), ('natural', True), ('sharp', True),
                   (None, None), ('sharp', True), ('sharp', False)]
        # no 4 is a dicey affair; could go either way
        ks = key.KeySignature(1)
        proc(pList, [], ks.alteredPitches)
        compare(pList, result)

        # initial scale tones with chromatic alteration, repeated tones
        pList = [Pitch('d3'), Pitch('e3'), Pitch('f#3'),
                 Pitch('g3'), Pitch('f4'), Pitch('g#4'),
                 Pitch('c#3'), Pitch('f#4'), Pitch('c#4')]
        result = [(None, None), (None, None), ('sharp', False),
                  (None, None), ('natural', True), ('sharp', True),
                  ('sharp', False), ('sharp', True), ('sharp', False)]
        ks = key.KeySignature(2)
        proc(pList, [], ks.alteredPitches)
        compare(pList, result)

        # altered tones outside of key
        pList = [Pitch('b3'), Pitch('a3'), Pitch('e3'),
                 Pitch('b-3'), Pitch('a-3'), Pitch('e-3'),
                 Pitch('b-3'), Pitch('a-3'), Pitch('e-3'),
                 Pitch('b-3'), Pitch('a-3'), Pitch('e-3')]
        result = [
            ('natural', True), ('natural', True), ('natural', True),
            ('flat', True), ('flat', True), ('flat', True),
            ('flat', False), ('flat', False), ('flat', False),
            ('flat', False), ('flat', False), ('flat', False),
        ]
        ks = key.KeySignature(-3)  # b-, e-, a-
        proc(pList, [], ks.alteredPitches)
        compare(pList, result)

        # naturals against the key signature are required for each and every use
        pList = [Pitch('b3'), Pitch('a3'), Pitch('e3'),
                 Pitch('b4'), Pitch('a-3'), Pitch('e-3'),
                 Pitch('b3'), Pitch('a3'), Pitch('e3')]
        result = [('natural', True), ('natural', True), ('natural', True),
                  ('natural', True), ('flat', True), ('flat', True),
                  ('natural', True), ('natural', True), ('natural', True)]
        ks = key.KeySignature(-3)  # b-, e-, a-
        proc(pList, [], ks.alteredPitches)
        compare(pList, result)

    def testUpdateAccidentalDisplayOctaves(self):
        '''
        test if octave display is working
        '''
        def proc1(_pList, _past):
            for p in _pList:
                p.updateAccidentalDisplay(pitchPast=_past, cautionaryPitchClass=True,
                                          cautionaryNotImmediateRepeat=False)
                _past.append(p)

        def proc2(_pList, _past):
            for p in _pList:
                p.updateAccidentalDisplay(pitchPast=_past, cautionaryPitchClass=False,
                                          cautionaryNotImmediateRepeat=False)
                _past.append(p)

        def compare(_past, _result):
            # environLocal.printDebug(['accidental compare'])
            for i in range(len(_result)):
                p = _past[i]
                if p.accidental is None:
                    pName = None
                    pDisplayStatus = None
                else:
                    pName = p.accidental.name
                    pDisplayStatus = p.accidental.displayStatus

                targetName = _result[i][0]
                targetDisplayStatus = _result[i][1]

                self.assertEqual(pName, targetName)
                self.assertEqual(
                    pDisplayStatus,
                    targetDisplayStatus,
                    f'{i}: {p} display: {pDisplayStatus}, target {targetDisplayStatus}'
                )

        pList = [Pitch('c#3'), Pitch('c#4'), Pitch('c#3'),
                 Pitch('c#4')]
        result = [('sharp', True), ('sharp', True), ('sharp', False),
                  ('sharp', False)]
        proc1(pList, [])
        compare(pList, result)
        pList = [Pitch('c#3'), Pitch('c#4'), Pitch('c#3'),
                 Pitch('c#4')]
        proc2(pList, [])
        compare(pList, result)

        a4 = Pitch('a4')
        past = [Pitch('a#3'), Pitch('c#'), Pitch('c')]
        # will not add a natural because match is pitchSpace
        a4.updateAccidentalDisplay(pitchPast=past, cautionaryPitchClass=False)
        self.assertEqual(a4.accidental, None)

    def testAccidentalsCautionary(self):
        '''
        a nasty test provided by Jose Cabal-Ugaz about octave leaps,
        cautionaryNotImmediateRepeat=False
        and key signature conflicts.
        '''
        bm = converter.parse("tinynotation: 4/4 fn1 fn1 e-8 e'-8 fn4 en4 e'n4").flatten()
        bm.insert(0, key.KeySignature(1))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        notes = bm[note.Note]
        self.assertEqual(notes[0].pitch.accidental.name, 'natural')     # Fn
        self.assertEqual(notes[0].pitch.accidental.displayStatus, True)
        self.assertEqual(notes[1].pitch.accidental.name, 'natural')     # Fn
        self.assertEqual(notes[1].pitch.accidental.displayStatus, True)
        self.assertEqual(notes[2].pitch.accidental.name, 'flat')        # E-4
        self.assertEqual(notes[2].pitch.accidental.displayStatus, True)
        self.assertEqual(notes[3].pitch.accidental.name, 'flat')        # E-5
        self.assertEqual(notes[3].pitch.accidental.displayStatus, True)
        self.assertEqual(notes[4].pitch.accidental.name, 'natural')     # En4
        self.assertEqual(notes[4].pitch.accidental.displayStatus, True)
        self.assertEqual(notes[5].pitch.accidental.name, 'natural')     # En4
        self.assertEqual(notes[5].pitch.accidental.displayStatus, True)

        self.assertIsNotNone(notes[6].pitch.accidental)  # En5
        self.assertEqual(notes[6].pitch.accidental.name, 'natural')
        self.assertEqual(notes[6].pitch.accidental.displayStatus, True)

    def testOverrideDisplayStatus(self):
        n = note.Note('Cn')
        n.pitch.accidental.displayStatus = True
        k = key.Key('C')
        n.pitch.updateAccidentalDisplay(overrideStatus=True, alteredPitches=k.alteredPitches)
        self.assertIs(n.pitch.accidental.displayStatus, False)

    def testImplicitToExplicitNatural(self):
        p = converter.parse('tinyNotation: 2/4 f4 fn4')
        last_note = p.recurse().notes.last()
        p.makeAccidentals(inPlace=True)
        self.assertIs(last_note.pitch.accidental.displayStatus, False)

        last_note.pitch.accidental.displayStatus = None
        p['Measure'].first().insert(0, key.Key('C-'))
        p.makeAccidentals(inPlace=True)
        self.assertIs(last_note.pitch.accidental.displayStatus, False)

    def testIfAbsolutelyNecessary(self):
        '''
        Beginning of test cases for if-absolutely-necessary.
        '''
        p = converter.parse('tinyNotation: 2/4 f#2 f2')
        last_note = p.recurse().notes.last()
        last_note.pitch.accidental = Accidental('natural')
        last_note.pitch.accidental.displayType = 'if-absolutely-necessary'
        p.makeAccidentals(inPlace=True)
        self.assertIs(last_note.pitch.accidental.displayStatus, False)

        p[stream.Measure].first().insert(0, key.KeySignature(-7))  # F-flat!
        p.makeAccidentals(inPlace=True, overrideStatus=True)
        self.assertIs(last_note.pitch.accidental.displayStatus, True)

        p[key.KeySignature].first().sharps = -5  # No effect on us.
        p.makeAccidentals(inPlace=True, overrideStatus=True)
        self.assertIs(last_note.pitch.accidental.displayStatus, False)

        p = converter.parse('tinyNotation: 2/4 F#4 f4')
        last_note = p.recurse().notes.last()
        last_note.pitch.accidental = Accidental('natural')
        last_note.pitch.accidental.displayType = 'if-absolutely-necessary'
        p.makeAccidentals(inPlace=True)
        self.assertIs(last_note.pitch.accidental.displayStatus, False)

        # F# in different octaves -- need one.
        last_note.pitch.accidental.set('sharp')
        p.makeAccidentals(inPlace=True, overrideStatus=True)
        self.assertIs(last_note.pitch.accidental.displayStatus, True)

    def testNaturalOutsideAlteredPitches(self):
        p = converter.parse('tinyNotation: 2/4 f4 dn4')
        p.makeAccidentals(inPlace=True)
        last_note = p[note.Note].last()
        self.assertIs(last_note.pitch.accidental.displayStatus, False)

        # Rerun test with C-flat major
        last_note.pitch.accidental.displayStatus = None
        p['Measure'].first().insert(0, key.Key('C-'))
        p.makeAccidentals(inPlace=True)
        self.assertIs(last_note.pitch.accidental.displayStatus, True)

    def testInterveningNoteBetweenIdenticalChromaticPitches(self):
        p = converter.parse('tinyNotation: f#4 e f#')
        p.measure(1).insert(0, key.Key('G'))
        p.recurse().notes.last().pitch.accidental.displayStatus = False
        p.makeAccidentals(inPlace=True, overrideStatus=True)
        self.assertIs(p.measure(1).notes.first().pitch.accidental.displayStatus, False)
        self.assertIs(p.measure(1).notes.last().pitch.accidental.displayStatus, False)

    def testPitchEquality(self):
        '''
        Test updating accidental display.
        '''
        data = [
            ('a', 'b', False), ('a', 'a', True), ('a#', 'a', False),
            ('a#', 'b-', False), ('a#', 'a-', False), ('a##', 'a#', False),
            ('a#4', 'a#4', True), ('a-3', 'a-4', False), ('a#3', 'a#4', False),
        ]
        for x, y, match in data:
            p1 = Pitch(x)
            p2 = Pitch(y)
            self.assertEqual(p1 == p2, match)
        # specific case of changing octave
        p1 = Pitch('a#')
        p2 = Pitch('a#')
        self.assertEqual(p1, p2)

        p1.octave = 4
        p2.octave = 3
        self.assertNotEqual(p1, p2)
        p1.octave = 4
        p2.octave = 4
        self.assertEqual(p1, p2)

    def testLowNotes(self):
        dPitch = Pitch('D2')
        lowC = dPitch.transpose('M-23')
        self.assertEqual(lowC.name, 'C')
        self.assertEqual(lowC.octave, -1)

    def testQuarterToneA(self):
        p1 = Pitch('D#~')
        # environLocal.printDebug([p1, p1.accidental])
        self.assertEqual(str(p1), 'D#~')
        # test generation of raw musicxml output
        xmlOut = m21ToXml.GeneralObjectExporter().parse(p1).decode('utf-8')

        match = '<step>D</step><alter>1.5</alter><octave>4</octave>'
        xmlOut = xmlOut.replace(' ', '')
        xmlOut = xmlOut.replace('\n', '')
        self.assertNotEqual(xmlOut.find(match), -1)

        s = stream.Stream()
        for pStr in ['A~', 'A#~', 'A`', 'A-`']:
            p = Pitch(pStr)
            self.assertEqual(str(p), pStr)
            n = note.Note()
            n.pitch = p
            s.append(n)
        self.assertEqual(len(s), 4)
        match = [e.pitch.ps for e in s]
        self.assertEqual(match, [69.5, 70.5, 68.5, 67.5])

        s = stream.Stream()
        alterList = [None, 0.5, 1.5, -1.5, -0.5,
                     'half-sharp', 'one-and-a-half-sharp', 'half-flat', 'one-and-a-half-flat',
                     '~']
        sc = scale.MajorScale('c4')
        for x in range(1, 10):
            n = note.Note(sc.pitchFromDegree(x % sc.getDegreeMaxUnique()))
            n.quarterLength = 0.5
            n.pitch.accidental = Accidental(alterList[x])
            s.append(n)

        match = [str(n.pitch) for n in s.notes]
        self.assertEqual(match,
                         ['C~4', 'D#~4', 'E-`4', 'F`4', 'G~4', 'A#~4', 'B`4', 'C-`4', 'D~4'])

        match = [e.pitch.ps for e in s]
        self.assertEqual(match, [60.5, 63.5, 62.5, 64.5, 67.5, 70.5, 70.5, 58.5, 62.5])

    def testMicrotoneA(self):
        p = pitch.Pitch('a4')
        p.microtone = 25

        self.assertEqual(str(p), 'A4(+25c)')
        self.assertEqual(p.ps, 69.25)

        p.microtone = '-10'
        self.assertEqual(str(p), 'A4(-10c)')
        self.assertEqual(p.ps, 68.90)

        self.assertEqual(p.pitchClass, 9)

        p = p.transpose(12)
        self.assertEqual(str(p), 'A5(-10c)')
        self.assertEqual(p.ps, 80.90)

    def testMicrotoneB(self):
        self.assertEqual(str(pitch.Pitch('c4').getHarmonic(1)), 'C4')

        p = pitch.Pitch('c4')
        p.microtone = 20
        self.assertEqual(str(p), 'C4(+20c)')
        self.assertEqual(str(p.getHarmonic(1)), 'C4(+20c)')

        self.assertEqual(str(pitch.Pitch('c4').getHarmonic(2)), 'C5')
        self.assertEqual(str(pitch.Pitch('c4').getHarmonic(3)), 'G5(+2c)')
        self.assertEqual(str(pitch.Pitch('c4').getHarmonic(4)), 'C6')
        self.assertEqual(str(pitch.Pitch('c4').getHarmonic(5)), 'E6(-14c)')
        self.assertEqual(str(pitch.Pitch('c4').getHarmonic(6)), 'G6(+2c)')
        self.assertEqual(str(pitch.Pitch('c4').getHarmonic(7)), 'A~6(+19c)')

        self.assertEqual(pitch.Pitch('g4').harmonicString('c3'), '3rdH(-2c)/C3')

        self.assertEqual(str(pitch.Pitch('c4').getHarmonic(1)), 'C4')
        self.assertEqual(str(pitch.Pitch('c3').getHarmonic(2)), 'C4')
        self.assertEqual(str(pitch.Pitch('c2').getHarmonic(2)), 'C3')

        self.assertEqual(pitch.Pitch('c4').harmonicString('c3'), '2ndH/C3')

        f = pitch.Pitch('c3')
        f.microtone = -10
        self.assertEqual(str(f.getHarmonic(2)), 'C4(-10c)')

        p = pitch.Pitch('c4')
        f = pitch.Pitch('c3')
        f.microtone = -20
        # the third harmonic of c3 -20 is closer than the
        self.assertEqual(p.harmonicString(f), '2ndH(+20c)/C3(-20c)')

        f.microtone = +20
        self.assertEqual(p.harmonicString(f), '2ndH(-20c)/C3(+20c)')

        p1 = pitch.Pitch('c1')
        self.assertEqual(str(p1.getHarmonic(13)), 'G#~4(-9c)')

        p2 = pitch.Pitch('a1')
        self.assertEqual(str(p2.getHarmonic(13)), 'F~5(-9c)')

        self.assertEqual(str(p1.transpose('M6')), 'A1')
        # not sure if this is correct:
        # self.assertEqual(str(p1.getHarmonic(13).transpose('M6')), 'E##5(-9c)')

    def testMicrotoneC(self):
        match = []
        p = pitch.Pitch('C4')
        p.microtone = 5
        for i in range(11):
            match.append(str(p))
            p.microtone = p.microtone.cents - 1
        self.assertEqual(str(match),
                         "['C4(+5c)', 'C4(+4c)', 'C4(+3c)', 'C4(+2c)', 'C4(+1c)', "
                         + "'C4', 'C4(-1c)', 'C4(-2c)', 'C4(-3c)', 'C4(-4c)', 'C4(-5c)']")

    def testMicrotoneD(self):
        # the microtonal scale used by padberg
        f = [440, 458 + 1 / 3, 476 + 2 / 3, 495, 513 + 1 / 3,
             531 + 2 / 3, 550, 568 + 1 / 3,
             586 + 2 / 3, 605, 623 + 1 / 3, 641 + 2 / 3,
             660, 678 + 1 / 3, 696 + 2 / 3, 715,
             733 + 1 / 3, 751 + 2 / 3, 770, 788 + 1 / 3,
             806 + 2 / 3, 825, 843 + 1 / 3, 861 + 2 / 3]
        self.assertEqual(len(f), 24)
        pList = []
        for fq in f:
            p = pitch.Pitch()
            p.frequency = fq
            pList.append(str(p))
        self.assertTrue(
            common.whitespaceEqual(
                str(pList),
                '''
                ['A4', 'A~4(+21c)', 'B`4(-11c)', 'B4(+4c)', 'B~4(+17c)', 'C~5(-22c)',
                 'C#5(-14c)', 'C#~5(-7c)', 'D5(-2c)', 'D~5(+1c)', 'E-5(+3c)', 'E`5(+3c)',
                 'E5(+2c)', 'E~5(-1c)', 'F5(-4c)', 'F~5(-9c)', 'F#5(-16c)', 'F#~5(-23c)',
                 'F#~5(+19c)', 'G5(+10c)', 'G~5(-1c)', 'G#5(-12c)', 'G#~5(-24c)', 'G#~5(+14c)']''',
            ),
            str(pList)
        )


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
