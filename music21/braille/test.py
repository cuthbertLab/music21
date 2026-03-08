# ------------------------------------------------------------------------------
# Name:         test.py
# Purpose:      Examples from "Introduction to Braille Music Transcription"
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    Copyright © 2012, 2016 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
from __future__ import annotations

import re
import textwrap
import unittest

from music21 import articulations
from music21.articulations import Fingering
from music21.braille.objects import BrailleSegmentDivision
from music21.braille.translate import partToBraille, measureToBraille, keyboardPartsToBraille
from music21 import bar
from music21 import chord
from music21 import clef
from music21 import converter
from music21 import dynamics
from music21 import expressions
from music21 import key
from music21 import meter
from music21 import note
from music21 import pitch
from music21 import spanner
from music21 import stream
from music21 import tempo

_DOC_IGNORE_MODULE_OR_PACKAGE = True

# called elsewhere:

def example11_2():
    bm = converter.parse('''tinynotation: 4/4 r2. b-4 g e- d e- g2 f4
        e- a- g c'4. c'8 b-2. b-4 e'-4 b- a-4. g8
        g2 f4 c' c' f a-4. d8 e-2. g4 g4. f8 f4 f a-2 g4 b- b- an an c'
        b-2. b-4 e'- b- a- g g2 f4 c' c' r f r a-2. d4 e-2.''').flatten()
    bm.insert(0, key.KeySignature(-3))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    m = bm.getElementsByClass(stream.Measure)
    for sm in m:
        sm.number -= 1
    m[0].padAsAnacrusis(useInitialRests=True)
    bm.measure(8).insert(3.0, BrailleSegmentDivision())
    return bm


# Examples follow the order in:
#   Introduction to Braille Music Transcription, Second Edition (2005)
# Mary Turner De Garmo
# https://www.loc.gov/nls/services-and-resources/music-service-and-materials/
# ------------------------------------------------------------------------------
class Test(unittest.TestCase):
    '''
    A series of tests from the DeGarmo book that run automatically
    when self.b (expected braille) or self.e (expected english) are altered
    '''
    @property
    def s(self, streamIn):
        self.stream = streamIn

    def _neutralizeSpacing(self, sStr):
        sStr = textwrap.dedent(sStr)
        sStr = re.sub(r'^ *\n', '', sStr)  # remove spaces to first line break
        sStr = sStr.rstrip() + '\n'  # (but not before first word.)
        return sStr

    @property
    def b(self, brailleInput):
        '''
        Sets the expected brailleInput and runs assertMultilineEqual
        '''
        self.expectedBraille = self._neutralizeSpacing(brailleInput)
        if self.autoRun:
            self.runB()

    @property
    def e(self, english):
        self.expectedEnglish = self._neutralizeSpacing(english)
        if self.autoRun:
            self.runE()

    def runB(self):
        ns = self._neutralizeSpacing
        if self.stream is None:
            return
        streamBraille = self.method(self.stream, inPlace=True, **self.methodArgs)
        self.assertMultiLineEqual(
            ns(streamBraille),
            self.expectedBraille
        )

    def runE(self):
        ns = self._neutralizeSpacing
        if self.stream is None:
            return
        streamEnglish = self.method(self.stream, inPlace=True, debug=True, **self.methodArgs)
        self.assertMultiLineEqual(
            ns(streamEnglish),
            self.expectedEnglish
        )

    def setUp(self):
        self.maxDiff = None
        self.autoRun = True
        self.stream = None
        self.expectedBraille = ''
        self.expectedEnglish = ''
        self.method = partToBraille
        self.methodArgs = {}

# ------------------------------------------------------------------------------
# PART ONE
# Basic Procedures and Transcribing Single-Staff Music
#
# ------------------------------------------------------------------------------
# Chapter 2: Eighth Notes, the Eighth Rest, and Other Basic Signs

    def test_example02_1(self):
        bm = converter.parse('tinynotation: 3/8         '
                             'g8 r8 e8     f8 r8 a8     g8 r8 f8    e8 r8 r8 '
                             'e8 r8 c8     d8 r8 f8     e8 r8 d8    c8 r8 r8 '
                             'd8 r8 f8     e8 r8 g8     f8 g8 a8    g8 r8 r8 '
                             'a8 r8 f8     g8 r8 e8     f8 e8 d8    c8 r8 r8',
                             makeNotation=False)
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.methodArgs = {'suppressOctaveMarks': True}
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠓⠭⠋⠀⠛⠭⠊⠀⠓⠭⠛⠀⠋⠭⠭⠀⠋⠭⠙⠀⠑⠭⠛⠀⠋⠭⠑⠀⠙⠭⠭⠀⠑⠭⠛
        ⠀⠀⠋⠭⠓⠀⠛⠓⠊⠀⠓⠭⠭⠀⠊⠭⠛⠀⠓⠭⠋⠀⠛⠋⠑⠀⠙⠭⠭⠣⠅
        '''
        self.s = bm.measures(1, 4)
        self.e = '''
          ---begin segment---
          <music21.braille.segment BrailleSegment>
          Measure 1, Signature Grouping 1:
          Time Signature 3/8 ⠼⠉⠦
          ===
          Measure 1, Note Grouping 1:
          <music21.clef.TrebleClef>
          G eighth ⠓
          Rest eighth ⠭
          E eighth ⠋
          ===
          Measure 2, Note Grouping 1:
          F eighth ⠛
          Rest eighth ⠭
          A eighth ⠊
          ===
          Measure 3, Note Grouping 1:
          G eighth ⠓
          Rest eighth ⠭
          F eighth ⠛
          ===
          Measure 4, Note Grouping 1:
          E eighth ⠋
          Rest eighth ⠭
          Rest eighth ⠭
          ===
          ---end segment---
        '''

    def test_example02_2(self):
        self.s = bm = converter.parse(
            'tinynotation: 4/8 r8 r8 r8 d8 d8 c8 B8 d8 c8 B8 A8 c8 B8 A8 G8 B8 A8 A8 D8 r8 '
            'E8 E8 G8 E8 D8 E8 G8 B8 d8 c8 B8 A8 G8 G8 G8 r8')
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[0].padAsAnacrusis(useInitialRests=True)
        for measure in m:
            measure.number -= 1
        self.methodArgs = {'suppressOctaveMarks': True}
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠚⠀⠑⠀⠑⠙⠚⠑⠀⠙⠚⠊⠙⠀⠚⠊⠓⠚⠀⠊⠊⠑⠭⠀⠋⠋⠓⠋⠀⠑⠋⠓⠚⠀⠑⠙⠚⠊
        ⠀⠀⠓⠓⠓⠭⠣⠅
        '''

    def test_example02_3(self):
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse('''
            tinynotation: 2/8 e8 e8 g8 a8 g8 f8 e8 g8 f8 e8 d8 f8 e8 c8 d8
            r8 e8 e8 f8 f8 g8 a8 b8 c'8 a8 f8 e8 d8 c8 B8 c8 r8''')
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠃⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠋⠋⠀⠓⠊⠀⠓⠛⠀⠋⠓⠀⠛⠋⠀⠑⠛⠀⠋⠙⠀⠑⠭⠀⠋⠋⠀⠛⠛⠀⠓⠊⠀⠚⠙
        ⠀⠀⠊⠛⠀⠋⠑⠀⠙⠚⠀⠙⠭⠣⠅
        '''

    def test_example02_4(self):
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse('''
            tinynotation: 3/8 A8 c8 e8 d8 c8 B8 c8 r8 B8 A8 r8 r8 B8 B8
            c8 d8 c8 B8 A8 r8 A8 B8 r8 r8 A8 E8 A8 c8 B8 A8 A8 B8 c8 d8
            r8 r8 e8 d8 c8 B8 E8 B8 A8 r8 A8 A8 r8 r8''')
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[7].rightBarline = bar.Barline('double')
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠊⠙⠋⠀⠑⠙⠚⠀⠙⠭⠚⠀⠊⠭⠭⠀⠚⠚⠙⠀⠑⠙⠚⠀⠊⠭⠊⠀⠚⠭⠭⠣⠅⠄
        ⠀⠀⠊⠋⠊⠀⠙⠚⠊⠀⠊⠚⠙⠀⠑⠭⠭⠀⠋⠑⠙⠀⠚⠋⠚⠀⠊⠭⠊⠀⠊⠭⠭⠣⠅
        '''

    def test_example02_5(self):
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse('''
            tinynotation: 4/8 r8 r8 d'8 e'8 f'8 c'8 a8 c'8 d'8 c'8 a8
            c'8 a8 c'8 a8 g8 e8 g8 f8 r8
            d8 e8 f8 d8 c8 d8 e8 f8 g8 e8 c8 e8 f8 r8''')
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[0].padAsAnacrusis(useInitialRests=True)
        for measure in m:
            measure.number -= 1
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠚⠀⠑⠋⠀⠛⠙⠊⠙⠀⠑⠙⠊⠙⠀⠊⠙⠊⠓⠀⠋⠓⠛⠭⠀⠑⠋⠛⠑⠀⠙⠑⠋⠛⠀⠓⠋⠙⠋
        ⠀⠀⠛⠭⠣⠅
        '''

    def test_example02_6(self):
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse('''
            tinynotation: 6/8 G8 G8 G8 G8 E8 F8 A8 G8 G8 G8 r8
            G8 A8 A8 A8 c8 B8 A8 A8 G8 G8 G8 r8 r8
            G8 F8 F8 F8 r8 r8 F8 E8 E8 E8 r8 r8 D8 E8
            D8 G8 F8 D8 C8 E8 D8 C8 r8 r8''').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠋⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠓⠓⠓⠓⠋⠛⠀⠊⠓⠓⠓⠭⠓⠀⠊⠊⠊⠙⠚⠊⠀⠊⠓⠓⠓⠭⠭⠀⠓⠛⠛⠛⠭⠭
        ⠀⠀⠛⠋⠋⠋⠭⠭⠀⠑⠋⠑⠓⠛⠑⠀⠙⠋⠑⠙⠭⠭⠣⠅
        '''

    def test_example02_7(self):
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse('''
            tinynotation: 6/8 e8 r8 e8 f8 r8 f8 d8 r8 d8 e8
            r8 e8 c8 d8 e8 g8 f8 e8 e8 d8 d8 d8 r8 r8
            c8 r8 c8 e8 r8 e8 f8 r8 f8 a8 r8 a8 g8 r8
            g8 g8 a8 b8 d'8 c'8 c'8 c'8 r8 r8''').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠋⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠋⠭⠋⠛⠭⠛⠀⠑⠭⠑⠋⠭⠋⠀⠙⠑⠋⠓⠛⠋⠀⠋⠑⠑⠑⠭⠭⠀⠙⠭⠙⠋⠭⠋
        ⠀⠀⠛⠭⠛⠊⠭⠊⠀⠓⠭⠓⠓⠊⠚⠀⠑⠙⠙⠙⠭⠭⠣⠅
        '''

# ------------------------------------------------------------------------------
# Chapter 3: Quarter Notes, the Quarter Rest, and the Dot

    def test_example03_1(self):
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse('''
            tinynotation: 4/4 d'4 b4 g4 b4 c'4 b4 a4 r4 b4 g4 e4 g4 d4 B4
            d4 r4 e4 g4 a4 g4 d4 g4 b4 d'4 e'4 d'4 c'4 a4 g4 d4 g4 r4''')
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠱⠺⠳⠺⠀⠹⠺⠪⠧⠀⠺⠳⠫⠳⠀⠱⠺⠱⠧⠀⠫⠳⠪⠳⠀⠱⠳⠺⠱⠀⠫⠱⠹⠪
        ⠀⠀⠳⠱⠳⠧⠣⠅
        '''

    def test_example03_2(self):
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse(
            'tinynotation: 4/4 A4 F4 C4 F4 G4 E4 C4 E4 F4 G4 A4 F4 D4 E4 F4 r4 G4 A4 G4 C4 '
            'F4 A4 c4 d4 c4 A4 G4 C4 D4 E4 F4 r4')
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠪⠻⠹⠻⠀⠳⠫⠹⠫⠀⠻⠳⠪⠻⠀⠱⠫⠻⠧⠀⠳⠪⠳⠹⠀⠻⠪⠹⠱⠀⠹⠪⠳⠹
        ⠀⠀⠱⠫⠻⠧⠣⠅
        '''

    def test_example03_3(self):
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse('''
            tinynotation: 2/4 g4 e4 a4 g4 f4 r4 d4 r4 c4. c8 d4. d8 e4
            r4 c4 r4 g4 g4 a4 b4 c'4 r4 a4 r4 g4. g8 f4 d4 c4 e4 c4 r4''').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠃⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠳⠫⠀⠪⠳⠀⠻⠧⠀⠱⠧⠀⠹⠄⠙⠀⠱⠄⠑⠀⠫⠧⠀⠹⠧⠀⠳⠳⠀⠪⠺⠀⠹⠧⠀⠪⠧
        ⠀⠀⠳⠄⠓⠀⠻⠱⠀⠹⠫⠀⠹⠧⠣⠅
        '''

    def test_example03_4(self):
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse('tinynotation: 4/4 E4 C8 D8 E4 r4 F4 A8 F8 E4 r4 D4 E8 F8 '
                             'G8 E8 C4 D4 D4 G4 r4 F4 E8 D8 E4 r4 G4 F8 E8 F4 r4 A4 G8 '
                             'F8 E8 F8 G4 F4 D4 C4 r4')
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠫⠙⠑⠫⠧⠀⠻⠊⠛⠫⠧⠀⠱⠋⠛⠓⠋⠹⠀⠱⠱⠳⠧⠀⠻⠋⠑⠫⠧⠀⠳⠛⠋⠻⠧
        ⠀⠀⠪⠓⠛⠋⠛⠳⠀⠻⠱⠹⠧⠣⠅
        '''

    def test_example03_5(self):
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse('''
            tinynotation: 4/4 f4. c8 d4 e4 f4. g8 a4 f4
            a4 c'4 d'4 c'4 a4 f4 g4 r4
            g4. e8 c4 e4 f4. c8 f4 a4 g4 g4 f4 e4 f4 a4 f4 r4''')
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[3].rightBarline = bar.Barline('double')
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠻⠄⠙⠱⠫⠀⠻⠄⠓⠪⠻⠀⠪⠹⠱⠹⠀⠪⠻⠳⠧⠣⠅⠄⠀⠳⠄⠋⠹⠫⠀⠻⠄⠙⠻⠪
        ⠀⠀⠳⠳⠻⠫⠀⠻⠪⠻⠧⠣⠅
        '''

    def test_example03_6(self):
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse('''
            tinynotation: 3/4 g4 g8 d4 d8 g4 b8 d'8 b8
            g8 a4 a8 a8 b8 c'8 b4 b8
            g4 r8 a4 a8 d4 d8 g4 b8 a4 c'8 b8 c'8 d'8 c'4 a8
            g4 g8 g4 r8''').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠳⠓⠱⠑⠀⠳⠚⠑⠚⠓⠀⠪⠊⠊⠚⠙⠀⠺⠚⠳⠭⠀⠪⠊⠱⠑⠀⠳⠚⠪⠙⠀⠚⠙⠑⠹⠊
        ⠀⠀⠳⠓⠳⠭⠣⠅
        '''

# ------------------------------------------------------------------------------
# Chapter 4: Half Notes, the Half Rest, and the Tie

    def test_example04_1(self):
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse('''
            tinynotation: 4/4 c2 e2 d2 f2 e2 g2 f2 a2 g2 b2 a2 c'2 b2 d'2 c'2 r2
            ''').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠝⠏⠀⠕⠟⠀⠏⠗⠀⠟⠎⠀⠗⠞⠀⠎⠝⠀⠞⠕⠀⠝⠥⠣⠅
        '''

    def test_example04_2(self):
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse(
            'tinynotation: 4/4 F2 A2 G2 C2 D4 C4 D4 E4 F2 r2 D2 F2 C2 F2 E4 F4 G4 A4 F2 r2'
        ).flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠟⠎⠀⠗⠝⠀⠱⠹⠱⠫⠀⠟⠥⠀⠕⠟⠀⠝⠟⠀⠫⠻⠳⠪⠀⠟⠥⠣⠅
        '''

    def test_example04_3(self):
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse('''
            tinynotation: 3/4 c2 c4 d8 c8 B8 c8 d4 e2 e4 f8 e8 d8
            e8 f4 g2 g4 a8 g8 f8 g8 a4 b8 a8 g8 a8 b8 d'8 c'4 r2 e'2
            e'4 d'8 c'8 b8 c'8 d'4 c'2 c'4 b8 a8 g8 a8 b4 a2 a4 g8 f8 e8 f8 g4
            f8 e8 d8 e8 f8 d8 c4 r2''').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠝⠹⠀⠑⠙⠚⠙⠱⠀⠏⠫⠀⠛⠋⠑⠋⠻⠀⠗⠳⠀⠊⠓⠛⠓⠪⠀⠚⠊⠓⠊⠚⠑⠀⠹⠥
        ⠀⠀⠏⠫⠀⠑⠙⠚⠙⠱⠀⠝⠹⠀⠚⠊⠓⠊⠺⠀⠎⠪⠀⠓⠛⠋⠛⠳⠀⠛⠋⠑⠋⠛⠑⠀⠹⠥⠣⠅
        '''

    def test_example04_4(self):
        self.method = measureToBraille
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse('tinynotation: 4/4 f2~ f4. f8').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[0].pop(1)
        m[-1].rightBarline = None
        self.s = m[0]
        self.b = '''
        ⠟⠈⠉⠻⠄⠛
        '''

    def test_example04_5(self):
        self.method = measureToBraille
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse('tinynotation: 3/4 g4.~ g8 a8 g8').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[0].pop(1)
        m[-1].rightBarline = None
        self.s = m[0]
        self.b = '''
        ⠳⠄⠈⠉⠓⠊⠓
        '''

    def test_example04_6(self):
        self.method = measureToBraille
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse('tinynotation: 3/4 g2 g4~ g2 r4').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[0].pop(0)
        m[-1].rightBarline = None
        self.s = m[0]
        self.b = '''
        ⠼⠉⠲⠀⠗⠳⠈⠉
        '''
        self.s = m[1]
        self.b = '''
        ⠗⠧
        '''

    def test_example04_7(self):
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse('tinynotation: 3/4 g2. e2. c2. e2. c4 d4 e4 g4 f4 e4 d2.~ d2. '
                             'e2 e4 e4 f4 g4 a2 a4 a4 g4 f4 e2 f4 d2 e4 c2.~ c2.').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠗⠄⠀⠏⠄⠀⠝⠄⠀⠏⠄⠀⠹⠱⠫⠀⠳⠻⠫⠀⠕⠄⠈⠉⠀⠕⠄⠀⠏⠫⠀⠫⠻⠳⠀⠎⠪
        ⠀⠀⠪⠳⠻⠀⠏⠻⠀⠕⠫⠀⠝⠄⠈⠉⠀⠝⠄⠣⠅
        '''

# ------------------------------------------------------------------------------
# Chapter 5: Whole and Double Whole Notes and Rests, Measure Rests, and
# Transcriber-Added Signs

    def test_example05_1(self):
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse('''
            tinynotation: 4/4 c'1 a1 f1 a1 c'1 d'1 c'1~ c'1
            d'1 e'1 f'1 d'1 c'1 g'1 f'1~ f'1''').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠽⠀⠮⠀⠿⠀⠮⠀⠽⠀⠵⠀⠽⠈⠉⠀⠽⠀⠵⠀⠯⠀⠿⠀⠵⠀⠽⠀⠷⠀⠿⠈⠉⠀⠿⠣⠅
        '''

    def test_example05_2(self):
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse('tinynotation: 4/4 C1 E1 G1 A1 B1 A1 G1~ G1 A1 c1 A1 '
                             'F1 G1 B1 G1 E1 F1 A1 F1 D1 BB1 D1 C1~ C1').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠽⠀⠯⠀⠷⠀⠮⠀⠾⠀⠮⠀⠷⠈⠉⠀⠷⠀⠮⠀⠽⠀⠮⠀⠿⠀⠷⠀⠾⠀⠷⠀⠯⠀⠿⠀⠮
        ⠀⠀⠿⠀⠵⠀⠾⠀⠵⠀⠽⠈⠉⠀⠽⠣⠅
        '''

    def test_example05_3(self):
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse('tinynotation: 3/2 r1 g2 g2 g2 g2 g4 g4 r1').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠼⠉⠆⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠍⠗⠀⠗⠗⠗⠀⠳⠳⠍⠣⠅
        '''

    def test_example05_4(self):
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse('tinynotation: 4/4 E2 F2 G1 E2 D2 C1 D2 E2 F2 E2 D1 r1 '
                                'C2 D2 E1 F2 G2 A1 G2 F2 E2 D2 C1 r1')
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠏⠟⠀⠷⠀⠏⠕⠀⠽⠀⠕⠏⠀⠟⠏⠀⠵⠀⠍⠀⠝⠕⠀⠯⠀⠟⠗⠀⠮⠀⠗⠟⠀⠏⠕⠀⠽
        ⠀⠀⠍⠣⠅
        '''
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.BassClef>
        E half ⠏
        F half ⠟
        ===
        Measure 2, Note Grouping 1:
        G whole ⠷
        ===
        Measure 3, Note Grouping 1:
        E half ⠏
        D half ⠕
        ===
        Measure 4, Note Grouping 1:
        C whole ⠽
        ===
        Measure 5, Note Grouping 1:
        D half ⠕
        E half ⠏
        ===
        Measure 6, Note Grouping 1:
        F half ⠟
        E half ⠏
        ===
        Measure 7, Note Grouping 1:
        D whole ⠵
        ===
        Measure 8, Note Grouping 1:
        Rest whole ⠍
        ===
        Measure 9, Note Grouping 1:
        C half ⠝
        D half ⠕
        ===
        Measure 10, Note Grouping 1:
        E whole ⠯
        ===
        Measure 11, Note Grouping 1:
        F half ⠟
        G half ⠗
        ===
        Measure 12, Note Grouping 1:
        A whole ⠮
        ===
        Measure 13, Note Grouping 1:
        G half ⠗
        F half ⠟
        ===
        Measure 14, Note Grouping 1:
        E half ⠏
        D half ⠕
        ===
        Measure 15, Note Grouping 1:
        C whole ⠽
        ===
        Measure 16, Note Grouping 1:
        Rest whole ⠍
        Barline final ⠣⠅
        ===
        ---end segment---
        '''

    def test_example05_5(self):
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse('tinynotation: 3/4 F2. r2. A2. r2. F4 G4 A4 c4 A4 F4 G4 r2 r2. '
                             'E2. r2. G2. r2. C4 D4 E4 G4 E4 C4 F4 r2 r2.').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠟⠄⠀⠍⠀⠎⠄⠀⠍⠀⠻⠳⠪⠀⠹⠪⠻⠀⠳⠥⠀⠍⠀⠏⠄⠀⠍⠀⠗⠄⠀⠍⠀⠹⠱⠫
        ⠀⠀⠳⠫⠹⠀⠻⠥⠀⠍⠣⠅
        '''
        self. e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.BassClef>
        F half ⠟
        Dot ⠄
        ===
        Measure 2, Note Grouping 1:
        Rest whole ⠍
        ===
        Measure 3, Note Grouping 1:
        A half ⠎
        Dot ⠄
        ===
        Measure 4, Note Grouping 1:
        Rest whole ⠍
        ===
        Measure 5, Note Grouping 1:
        F quarter ⠻
        G quarter ⠳
        A quarter ⠪
        ===
        Measure 6, Note Grouping 1:
        C quarter ⠹
        A quarter ⠪
        F quarter ⠻
        ===
        Measure 7, Note Grouping 1:
        G quarter ⠳
        Rest half ⠥
        ===
        Measure 8, Note Grouping 1:
        Rest whole ⠍
        ===
        Measure 9, Note Grouping 1:
        E half ⠏
        Dot ⠄
        ===
        Measure 10, Note Grouping 1:
        Rest whole ⠍
        ===
        Measure 11, Note Grouping 1:
        G half ⠗
        Dot ⠄
        ===
        Measure 12, Note Grouping 1:
        Rest whole ⠍
        ===
        Measure 13, Note Grouping 1:
        C quarter ⠹
        D quarter ⠱
        E quarter ⠫
        ===
        Measure 14, Note Grouping 1:
        G quarter ⠳
        E quarter ⠫
        C quarter ⠹
        ===
        Measure 15, Note Grouping 1:
        F quarter ⠻
        Rest half ⠥
        ===
        Measure 16, Note Grouping 1:
        Rest whole ⠍
        Barline final ⠣⠅
        ===
        ---end segment---

        '''

    def test_example05_6(self):
        # NOTE: Breve note and breve rest are transcribed using method (b) on page 24.
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse('''
            tinynotation: a1 c'1 b1 c'2 b2 a1 b2 c'2 b1
            ''', makeNotation=False)
        bm.append(note.Rest(quarterLength=8.0))
        bm2 = converter.parse('tinynotation: g1 b1 a2 g2', makeNotation=False)
        bm2.append(note.Note('A4', quarterLength=8.0))
        bm2.append(note.Rest(quarterLength=4.0))
        bm.append(bm2.flatten())
        bm.insert(0, meter.TimeSignature('6/2'))
        bm = bm.flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠋⠆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠮⠽⠾⠀⠝⠞⠮⠞⠝⠀⠾⠍⠘⠉⠍⠀⠷⠾⠎⠗⠀⠮⠘⠉⠮⠍⠣⠅
        '''

    # The following examples (as well as the rest of the examples in the chapter)
    # don't work correctly yet.
    #
    def xtest_example05_7a(self):
        bm = converter.parse('tinynotation: 4/4 r1 r1 r1 r1 r1').flatten()
        bm.makeNotation(inPlace=True)
        m = bm.getElementsByClass(stream.Measure)
        m[0].pop(0)
        self.methodArgs = {'showHeading': False, 'showFirstMeasureNumber': False}
        self.s = bm

    def xtest_example05_7b(self):
        bm = converter.parse('tinynotation: r1 r1 r1 r1').flatten()
        bm.makeNotation(inPlace=True)
        m = bm.getElementsByClass(stream.Measure)
        m[0].pop(0)
        self.methodArgs = {'showHeading': False, 'showFirstMeasureNumber': False}
        self.s = bm

    def xtest_example05_7c(self):
        bm = converter.parse('tinynotation: r1 r1').flatten()
        bm.makeNotation(inPlace=True)
        m = bm.getElementsByClass(stream.Measure)
        m[0].pop(0)
        self.methodArgs = {'showHeading': False, 'showFirstMeasureNumber': False}
        self.s = bm
        # self.b = ''

# ------------------------------------------------------------------------------
# Chapter 6: Accidentals

    def test_example06_1(self):
        from music21.braille.basic import noteToBraille
        from music21.note import Note
        self.assertEqual(noteToBraille(Note('C#4', quarterLength=2), showOctave=False),
                         '⠩⠝')
        self.assertEqual(noteToBraille(Note('Gn4', quarterLength=2), showOctave=False),
                         '⠡⠗')
        self.assertEqual(noteToBraille(Note('E-4', quarterLength=2), showOctave=False),
                         '⠣⠏')

    def test_example06_2(self):
        self.method = measureToBraille
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse('tinynotation: g#4 f##4 g#2').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[0].pop(1)
        m[-1].rightBarline = None
        self.s = m[0]
        self.b = '⠩⠳⠩⠩⠻⠗'

    def test_example06_3(self):
        self.method = measureToBraille
        self.methodArgs = {'suppressOctaveMarks': True}

        bm = converter.parse("tinynotation: 4/4 c'2 b-2~ b-4 c'4 a4 f4").flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[0].pop(0)
        m[-1].rightBarline = None
        self.s = m[0]
        self.b = '⠼⠙⠲⠀⠝⠣⠞⠈⠉'
        self.s = m[1]
        self.b = '⠺⠹⠪⠻'

    def test_example06_4(self):
        self.method = measureToBraille
        self.methodArgs = {'suppressOctaveMarks': True}

        bm = converter.parse("tinynotation: 3/4 e4 e8 a8 c'8 e'8 f'2.", makeNotation=False)
        bm.notes[0].pitch.accidental = pitch.Accidental()
        bm.notes[0].pitch.accidental.displayStatus = True
        bm.notes[4].pitch.accidental = pitch.Accidental()
        bm.notes[4].pitch.accidental.displayStatus = True
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[-1].rightBarline = None
        self.s = m[0]
        self.b = '''
        ⠼⠉⠲⠀⠡⠫⠋⠊⠙⠡⠋
        '''
        self.s = m[1]
        self.b = '''
        ⠟⠄
        '''

    def test_example06_5(self):
        self.method = measureToBraille
        self.methodArgs = {'suppressOctaveMarks': True}

        bm = converter.parse("tinynotation: 3/4 c'8 b-8 a8 g8 f4 g8 bn8 c'4 d'4").flatten()
        bm.notes[-3].pitch.accidental = pitch.Accidental()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[-1].rightBarline = None
        self.s = m[0]
        self.b = '''
        ⠼⠉⠲⠀⠙⠣⠚⠊⠓⠻
        '''
        self.s = m[1]
        self.b = '''
        ⠓⠡⠚⠹⠱
        '''

    def test_example06_6(self):
        self.methodArgs = {'suppressOctaveMarks': True}

        bm = converter.parse('''
            tinynotation: c4 c#4 d4 d#4 e4 f4 f#4 g4 g#4 a4 b-4 bn4
            c'2 r2 e'2 e'-4 d'4 c'4 d'4 e'4 c'4 b4 b-4 a4 bn4 c'2 r2''')
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠹⠩⠹⠱⠩⠱⠀⠫⠻⠩⠻⠳⠀⠩⠳⠪⠣⠺⠡⠺⠀⠝⠥⠀⠏⠣⠫⠱⠀⠹⠱⠡⠫⠹
        ⠀⠀⠺⠣⠺⠪⠡⠺⠀⠝⠥⠣⠅
        '''

    def test_example06_7(self):
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse('''
            tinynotation: g'4 f'#4 f'4 e'4 e'-4 d'4 d'-4 c'4 b4 b-4 a4 a-4 g4
            f#4 f4 e4 e-4 d4 d-4 c4 B4 c4 d4 e4 c2 r2 c1
            ''', makeNotation=False).getElementsNotOfClass(['TimeSignature']).stream()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[-3][2].pitch.accidental.displayStatus = False
        m[-3][3].pitch.accidental.displayStatus = False
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠳⠩⠻⠡⠻⠫⠀⠣⠫⠱⠣⠱⠹⠀⠺⠣⠺⠪⠣⠪⠀⠳⠩⠻⠡⠻⠫⠀⠣⠫⠱⠣⠱⠹
        ⠀⠀⠺⠹⠱⠫⠀⠝⠥⠀⠽⠣⠅
        '''

    def test_example06_8(self):
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse('''
            tinynotation: 4/4 c'4 c'8 b-8 a-8 c'8 f'8
            a'-8~ a'-8 g'8 f'8 g'8 c'2
            d'-4 f'8 d'-8 c'8 c'8 a-8 f8 g8 g8 c8 c8 f2''')
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠹⠙⠣⠚⠣⠊⠙⠛⠣⠊⠈⠉⠀⠊⠓⠛⠓⠝⠀⠣⠱⠛⠑⠙⠙⠣⠊⠛⠀⠓⠓⠙⠙⠟⠣⠅
        '''

    def test_example06_9(self):
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse('tinynotation: E4 G2 E4 F#4 A2 F#4 G8 A8 B4 G4 E4 D#8 E8 F#4 D#4 G4 '
                             'C4 E2 F#4 G4 B2 c4 B8 A8 G8 B8 A8 G8 F#8 D#8 E1')
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠫⠗⠫⠀⠩⠻⠎⠻⠀⠓⠊⠺⠳⠫⠀⠩⠑⠋⠩⠻⠱⠳⠀⠹⠏⠩⠻⠀⠳⠞⠹
        ⠀⠀⠚⠊⠓⠚⠊⠓⠩⠛⠩⠑⠀⠯⠣⠅
        '''

    def test_example06_10(self):
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse('''
            tinynotation: a4 a2 a4~ a4 r4 b-2 c'4 c'4 r4 c'4~ c'4 r4 d'2
            e'8 e'4 e'8 f'4 r4 e'8 e'4 e'8 d'4 r4 c'8 c'4 c'8 b-8 b-4 b-8 a2. r4''')
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠪⠎⠪⠈⠉⠀⠪⠧⠣⠞⠀⠹⠹⠧⠹⠈⠉⠀⠹⠧⠕⠀⠋⠫⠋⠻⠧⠀⠋⠫⠋⠱⠧
        ⠀⠀⠙⠹⠙⠣⠚⠺⠚⠀⠎⠄⠧⠣⠅
        '''

    def test_example06_11(self):
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse('''
            tinynotation: A4. B8 c4 B4 A8 c8 e8 c8 A8 c8 e4 d4. f8
            a4 f4 d8 f8 a8 f8 d8 f8 a4
            g#4. e8 a2 b4. b8 c'2 d'8 c'8 b8 a8 g#8 e8 f#8 g#8 a2~ a8 g#8 a4''')
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠪⠄⠚⠹⠺⠀⠊⠙⠋⠙⠊⠙⠫⠀⠱⠄⠛⠪⠻⠀⠑⠛⠊⠛⠑⠛⠪⠀⠩⠳⠄⠋⠎
        ⠀⠀⠺⠄⠚⠝⠀⠑⠙⠚⠊⠩⠓⠋⠩⠛⠓⠀⠎⠈⠉⠊⠩⠓⠪⠣⠅
        '''

    def test_example06_12(self):
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse('''
            tinynotation: e'8 e'-8 d'8 d'-8 c'8 a8 a-8 g8 b--8 a-8 g8 g-8
            f8 e8 d8 c8 d8 B8 B-8 Bn8 c8 d8 e8 f8 g8 g#8 a8 b8 c'4 r4''').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        bm.measure(2).notes[5].pitch.accidental.displayStatus = False
        bm.measure(2).notes[6].pitch.accidental.displayStatus = False
        bm.measure(3).notes[1].pitch.accidental.displayStatus = False
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠋⠣⠋⠑⠣⠑⠙⠊⠣⠊⠓⠀⠣⠣⠚⠣⠊⠓⠣⠓⠛⠋⠑⠙⠀⠑⠚⠣⠚⠡⠚⠙⠑⠋⠛
        ⠀⠀⠓⠩⠓⠊⠚⠹⠧⠣⠅
        '''

# ------------------------------------------------------------------------------
# Chapter 7: Octave Marks

    def test_example07_1(self):
        bm = stream.Part()
        bm.append(note.Note('C1', quarterLength=4.0))
        bm.append(note.Note('C2', quarterLength=4.0))
        bm.append(note.Note('C3', quarterLength=4.0))
        bm.append(note.Note('C4', quarterLength=4.0))
        bm.append(note.Note('C5', quarterLength=4.0))
        bm.append(note.Note('C6', quarterLength=4.0))
        bm.append(note.Note('C7', quarterLength=4.0))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[-1].rightBarline = None
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠈⠽⠀⠘⠽⠀⠸⠽⠀⠐⠽⠀⠨⠽⠀⠰⠽⠀⠠⠽
        '''

    def test_example07_2(self):
        bm = stream.Part()
        bm.append(note.Note('A0', quarterLength=4.0))
        bm.append(note.Note('B0', quarterLength=4.0))
        bm.append(note.Note('C8', quarterLength=4.0))
        bm.insert(0, meter.TimeSignature('2/1'))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[0].pop(0)
        m[-1].rightBarline = None
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠼⠃⠂⠀⠀⠀⠀
        ⠼⠁⠀⠈⠈⠮⠾⠀⠠⠠⠽
        '''

    def test_example07_3a(self):
        self.method = measureToBraille
        bm = converter.parse('tinynotation: c4 e4').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[0].pop(1)
        m[-1].rightBarline = None
        self.s = m[0]
        self.b = '⠐⠹⠫'

    def test_example07_3b(self):
        self.method = measureToBraille
        bm = converter.parse("tinynotation: c'2. a4").flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[0].pop(1)
        m[-1].rightBarline = None
        self.s = m[0]
        self.b = '⠨⠝⠄⠪'

    def test_example07_4a(self):
        self.method = measureToBraille
        bm = converter.parse('tinynotation: 4/4 c2 a2').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[0].pop(1)
        m[-1].rightBarline = None
        self.s = m[0]
        self.b = '⠐⠝⠐⠎'

    def test_example07_4b(self):
        self.method = measureToBraille
        bm = converter.parse("tinynotation: 4/4 c'2 e2").flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[0].pop(1)
        m[-1].rightBarline = None
        self.s = m[0]
        self.b = '⠨⠝⠐⠏'

    def test_example07_5a(self):
        self.method = measureToBraille
        bm = converter.parse('tinynotation: C2 F2').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[0].pop(1)
        m[-1].rightBarline = None
        self.s = m[0]
        self.b = '⠸⠝⠟'

    def test_example07_5b(self):
        self.method = measureToBraille
        bm = converter.parse("tinynotation: f2 c'2").flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[0].pop(1)
        m[-1].rightBarline = None
        self.s = m[0]
        self.b = '⠐⠟⠨⠝'

    def test_example07_6(self):
        bm = converter.parse('''
            tinynotation: 4/8 e'-8 e'-8 e'-8 e'-8 d'8 d'8 b-4 c'8
            c'8 c'8 c'8 e-8 c'8 b-4
            f8 f8 c'4 b-8 b-8 f'4 e'-8 d'8 c'8 b-8 e'-4 e-4''').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠣⠨⠋⠋⠋⠋⠀⠑⠑⠣⠺⠀⠙⠙⠙⠙⠀⠣⠐⠋⠨⠙⠣⠺⠀⠛⠛⠨⠹⠀⠣⠚⠚⠨⠻
        ⠀⠀⠣⠨⠋⠑⠙⠣⠚⠀⠣⠨⠫⠣⠐⠫⠣⠅
        '''

        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/8 ⠼⠙⠦
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Accidental flat ⠣
        Octave 5 ⠨
        E eighth ⠋
        E eighth ⠋
        E eighth ⠋
        E eighth ⠋
        ===
        Measure 2, Note Grouping 1:
        D eighth ⠑
        D eighth ⠑
        Accidental flat ⠣
        B quarter ⠺
        ===
        Measure 3, Note Grouping 1:
        C eighth ⠙
        C eighth ⠙
        C eighth ⠙
        C eighth ⠙
        ===
        Measure 4, Note Grouping 1:
        Accidental flat ⠣
        Octave 4 ⠐
        E eighth ⠋
        Octave 5 ⠨
        C eighth ⠙
        Accidental flat ⠣
        B quarter ⠺
        ===
        Measure 5, Note Grouping 1:
        F eighth ⠛
        F eighth ⠛
        Octave 5 ⠨
        C quarter ⠹
        ===
        Measure 6, Note Grouping 1:
        Accidental flat ⠣
        B eighth ⠚
        B eighth ⠚
        Octave 5 ⠨
        F quarter ⠻
        ===
        Measure 7, Note Grouping 1:
        Accidental flat ⠣
        Octave 5 ⠨
        E eighth ⠋
        D eighth ⠑
        C eighth ⠙
        Accidental flat ⠣
        B eighth ⠚
        ===
        Measure 8, Note Grouping 1:
        Accidental flat ⠣
        Octave 5 ⠨
        E quarter ⠫
        Accidental flat ⠣
        Octave 4 ⠐
        E quarter ⠫
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
        self.assertTrue(bm.measure(7).notes[3].pitch.accidental.displayStatus)

    def test_example07_7(self):
        '''
        "Whenever the marking “8va” occurs in print over or under certain notes,
        these notes should be transcribed according to the octaves in which they
        are actually to be played." page 42, Braille Transcription Manual

        TODO: Replace with actual 8va spanner.
        '''
        bm = converter.parse('''
            tinynotation: 4/8 a8 c'8 f'8 c'8 a8 c'8 f'8 c'8 a'8
            f'8 c'8 d'8 a'8 f'8 e'8 c'8 f'2''').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[0].pop(0)
        m[1].transpose('P8', inPlace=True)
        m[2].transpose('P8', inPlace=True)
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠐⠊⠙⠛⠙⠀⠨⠊⠙⠛⠙⠀⠰⠊⠛⠙⠑⠀⠨⠊⠛⠋⠙⠀⠟⠣⠅
        '''

    def test_example07_8(self):
        bm = converter.parse('tinynotation: C2 GG4 E4 D4. C8 C4 C4 A2 G4 E4 D4 G2 G4 '
                             'c4. B8 A4 G4 A4 F4 C4 AA4 GG4 GG4 D4 G4 E4 C2.')
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠸⠝⠘⠳⠸⠫⠀⠱⠄⠙⠹⠹⠀⠸⠎⠳⠫⠀⠱⠗⠳⠀⠐⠹⠄⠚⠪⠳⠀⠪⠻⠹⠪
        ⠀⠀⠘⠳⠳⠸⠱⠳⠀⠫⠝⠄⠣⠅
        '''

    def test_example07_9(self):
        bm = converter.parse('''
            tinynotation: 3/4 e4. a8 c'8 e'8 d'4 d'8 c'8 b4 e4. g#8 b8 e'8 c'4 c'8 b8 a4
            a8 c'#8 e'8 a'8 c'#8 g'8 f'8 d'8 a8 e'8 d'8 f8 c'8 b8 d8 a8 g#8 e8 a2.''')
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠐⠫⠄⠊⠙⠋⠀⠱⠑⠙⠺⠀⠫⠄⠩⠓⠚⠨⠋⠀⠹⠙⠚⠪⠀⠊⠩⠙⠋⠊⠨⠙⠓
        ⠀⠀⠨⠛⠑⠐⠊⠨⠋⠑⠐⠛⠀⠨⠙⠚⠐⠑⠊⠩⠓⠋⠀⠎⠄⠣⠅
        '''

    def test_example07_10(self):
        bm = converter.parse('''
            tinynotation: 4/4 a4 e'4 a'4 e'4 c'#8 f'#8 e'8 a8 b4
            e'4 d'8 a8 f#8 d'8 c'#8 a8 e8 c'#8 b8 f#8 g#8 a8 b4 e4
            a4 a4 f'#4 e'4 d'4 d'4 b'4 a'4
            a'8 c'#8 g'#8 f'#8 e'8 e8 c'#8 b8 a2 r2''')
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠐⠪⠨⠫⠪⠫⠀⠩⠙⠩⠛⠋⠐⠊⠺⠨⠫⠀⠑⠐⠊⠩⠛⠨⠑⠩⠙⠊⠋⠨⠙
        ⠀⠀⠐⠚⠩⠛⠩⠓⠊⠺⠫⠀⠪⠪⠩⠨⠻⠫⠀⠱⠱⠨⠺⠪⠀⠊⠩⠨⠙⠩⠓⠩⠛⠋⠐⠋⠨⠙⠚
        ⠀⠀⠐⠎⠥⠣⠅
        '''
        t = [(2, 0, True), (2, 1, True), (3, 2, True), (3, 4, True), (3, 7, False),
             (4, 1, True), (4, 2, True), (5, 2, True), (7, 1, True), (7, 2, True),
             (7, 3, True), (7, 6, False)]
        for measureNum, noteNum, result in t:
            self.assertEqual(bm.measure(measureNum).notes[noteNum].pitch.accidental.displayStatus,
                             result)

    def test_example07_11(self):
        bm = converter.parse(
            'tinynotation: 6/8 r2 r8 GG8 C4 GG8 C4 E-8 D4 GG8 D4 G8 C4 '
            'G8 c4 B-8 A-4 F8 C4 A-8 '
            'G8 E-8 A-8 G8 C8 F8 E-8 GG8 D8 C8 GG8 EE-8 FF8 D8 C8 BBn8 GG8 GG8 CC4. r4')
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[0].padAsAnacrusis(useInitialRests=True)
        for measure in m:
            measure.number -= 1
        bm.measure(7).notes[3].pitch.accidental = pitch.Accidental()
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠋⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠚⠀⠘⠓⠀⠸⠹⠘⠓⠸⠹⠣⠋⠀⠱⠘⠓⠸⠱⠓⠀⠹⠓⠐⠹⠣⠚⠀⠣⠪⠛⠹⠸⠊
        ⠀⠀⠸⠓⠣⠋⠣⠊⠓⠙⠛⠀⠣⠋⠘⠓⠸⠑⠙⠘⠓⠣⠋⠀⠛⠸⠑⠙⠡⠚⠓⠓⠀⠹⠄⠧⠣⠅
        '''
        t = [(4, 0, True),  # A-3
             (4, 3, False),  # A-3
             (5, 1, True),  # E-3
             (5, 2, True),  # A-3
             (6, 0, True),  # E-3
             (6, 5, True)]  # E-2
        for measureNum, noteNum, result in t:
            self.assertEqual(bm.measure(measureNum).notes[noteNum].pitch.accidental.displayStatus,
                             result)

# ------------------------------------------------------------------------------
# Chapter 8: The Music Heading: Signatures, Tempo, and Mood

    def test_example08_1a(self):
        from music21.braille.basic import keySigToBraille
        results = ['⠣', '⠣⠣', '⠣⠣⠣', '⠼⠙⠣', '⠼⠑⠣', '⠼⠋⠣', '⠼⠛⠣']
        for i, r in enumerate(results):
            flats = -1 * (i + 1)
            self.assertEqual(keySigToBraille(key.KeySignature(flats)), r)

    def test_example08_1b(self):
        from music21.braille.basic import keySigToBraille
        results = ['⠩', '⠩⠩', '⠩⠩⠩', '⠼⠙⠩', '⠼⠑⠩', '⠼⠋⠩', '⠼⠛⠩']
        for i, r in enumerate(results):
            sharps = (i + 1)
            self.assertEqual(keySigToBraille(key.KeySignature(sharps)), r)

    def test_example08_2(self):
        from music21.braille.basic import timeSigToBraille
        for ts, r in [('6/8', '⠼⠋⠦'),
                      ('2/4', '⠼⠃⠲'),
                      ('12/8', '⠼⠁⠃⠦'),
                      ('2/2', '⠼⠃⠆'),
                      ]:
            self.assertEqual(timeSigToBraille(meter.TimeSignature(ts)), r)

    def xtest_example08_3(self):
        '''
        Time signatures with one number. Not currently supported.
        '''
        pass

    def xtest_example08_4(self):
        '''
        Combined time signatures. Not currently supported.
        '''
        pass

    def test_example08_5(self):
        '''
        Common/cut time signatures
        '''
        from music21.braille.basic import timeSigToBraille
        for ts, r in [('common', '⠨⠉'),
                      ('cut', '⠸⠉'),
                      ]:
            self.assertEqual(timeSigToBraille(meter.TimeSignature(ts)), r)

    def test_example08_6(self):
        from music21.braille.basic import transcribeSignatures
        for ks, ts, r in [(1, '2/4', '⠩⠼⠃⠲'),
                          (-3, '3/4', '⠣⠣⠣⠼⠉⠲'),
                          (4, '3/8', '⠼⠙⠩⠼⠉⠦'),
                          (3, '3/8', '⠩⠩⠩⠼⠉⠦'),
                          # The following two cases are identical, having no key signature
                          # is equivalent to having a key signature with no sharps or flats.
                          (None, '4/4', '⠼⠙⠲'),
                          (0, '4/4', '⠼⠙⠲'),

                          (-1, '3/4', '⠣⠼⠉⠲'),
                          (0, '6/8', '⠼⠋⠦')
                          ]:
            if ks is not None:
                ks = key.KeySignature(ks)
            ts = meter.TimeSignature(ts)
            self.assertEqual(transcribeSignatures(ks, ts), r)

    def test_example08_7a(self):
        from music21.braille.basic import transcribeHeading
        results = [
            (-4, '4/4', 'Andante', '⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠁⠝⠙⠁⠝⠞⠑⠲⠀⠼⠙⠣⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀'),
            (3, '3/8', 'Con moto', '⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠉⠕⠝⠀⠍⠕⠞⠕⠲⠀⠩⠩⠩⠼⠉⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀'),
            (None, '4/4', 'Andante cantabile',
                                   '⠀⠀⠀⠀⠀⠀⠀⠀⠠⠁⠝⠙⠁⠝⠞⠑⠀⠉⠁⠝⠞⠁⠃⠊⠇⠑⠲⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀'),
            (2, '7/8', 'Very brightly',
                                   '⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠧⠑⠗⠽⠀⠃⠗⠊⠛⠓⠞⠇⠽⠲⠀⠩⠩⠼⠛⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀')
        ]
        for ks, ts, tt, r in results:
            if ks is not None:
                ks = key.KeySignature(ks)
            ts = meter.TimeSignature(ts)
            tt = tempo.TempoText(tt)
            self.assertEqual(transcribeHeading(ks, ts, tt), r)

    def test_example08_8(self):
        from music21.braille import basic
        self.assertEqual(basic.metronomeMarkToBraille(
            tempo.MetronomeMark(number=80,
                                                referent=note.Note(type='half'))), '⠝⠶⠼⠓⠚')

    def test_example08_9(self):
        from music21.braille.basic import transcribeHeading
        ks = key.KeySignature(-3)
        ts = meter.TimeSignature('12/8')
        tt = tempo.TempoText('Andante')
        mm = tempo.MetronomeMark(number=132, referent=note.Note(type='eighth'))
        self.assertEqual(transcribeHeading(ks, ts, tt, mm),
                         '⠀⠀⠀⠀⠀⠀⠀⠀⠠⠁⠝⠙⠁⠝⠞⠑⠲⠀⠙⠶⠼⠁⠉⠃⠀⠣⠣⠣⠼⠁⠃⠦⠀⠀⠀⠀⠀⠀⠀⠀')

    def test_example08_10(self):
        '''
        Actual look is:

    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠇⠑⠝⠞⠕⠀⠁⠎⠎⠁⠊⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠁⠝⠞⠁⠝⠞⠑⠀⠑⠀⠞⠗⠁⠝⠟⠥⠊⠇⠇⠕⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠹⠄⠶⠼⠑⠃⠀⠼⠑⠣⠼⠋⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        '''
        from music21.braille.basic import transcribeHeading
        ks = key.KeySignature(-5)
        ts = meter.TimeSignature('6/8')
        # noinspection SpellCheckingInspection
        tt = tempo.TempoText('Lento assai, cantante e tranquillo')
        mm = tempo.MetronomeMark(number=52, referent=note.Note(quarterLength=1.5))
        self.assertMultiLineEqual(transcribeHeading(ks, ts, tt, mm),
                                  '''⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠇⠑⠝⠞⠕⠀⠁⠎⠎⠁⠊⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠁⠝⠞⠁⠝⠞⠑⠀⠑⠀⠞⠗⠁⠝⠟⠥⠊⠇⠇⠕⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠹⠄⠶⠼⠑⠃⠀⠼⠑⠣⠼⠋⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀''')

    def test_drill08_1(self):
        bm = converter.parse('''
            tinynotation: 4/4 a2 g8 f8 e4 d4 e4 f8 g8 a4 g4 c'8 b8 a4 g4 f4. e8 d2
            c4 e4 a4 e'4 e'4 d'4 c'8 b8 a4 a'4 g'8 f'8 e'4 d'4 c'4 a8 b8 c'2''',
            makeNotation=False)
        bm.replace(bm.getElementsByClass(meter.TimeSignature).first(), meter.TimeSignature('c'))
        bm.insert(0, tempo.TempoText('Andante maestoso'))
        bm.insert(0, tempo.MetronomeMark(number=92, referent=note.Note(type='quarter')))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠠⠁⠝⠙⠁⠝⠞⠑⠀⠍⠁⠑⠎⠞⠕⠎⠕⠲⠀⠹⠶⠼⠊⠃⠀⠨⠉⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠐⠎⠓⠛⠫⠀⠱⠫⠛⠓⠪⠀⠳⠨⠙⠚⠪⠳⠀⠻⠄⠋⠕⠀⠹⠫⠪⠨⠫⠀⠫⠱⠙⠚⠪
        ⠀⠀⠨⠪⠓⠛⠫⠱⠀⠹⠊⠚⠝⠣⠅
        '''

    def test_drill08_2(self):
        bm = converter.parse(
            'tinynotation: 3/4 E-8 r8 BB-8 r8 E-8 r8 En4 F4 F#4 G8 r8 D8 r8 G8 r8 A-4 G4 F4 '
            'E-8 r8 C8 r8 AA-8 r8 AAn4 BB-4 BBn4 C8 D8 r8 E-8 r8 BB-8 E-8 En8 r8 F8 r8 F#8 '
            'G8 D8 r8 G8 r8 A-8 A-8 G8 r8 F8 r8 E-8 D8 C8 BB-4 BB-4 EE-2.').flatten()
        bm.insert(0, key.KeySignature(-3))
        bm.insert(0, tempo.TempoText('In strict time'))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[-2].notes[-1].transpose('P-8', inPlace=True)
        bm.measure(7).notes[-1].pitch.accidental.displayStatus = False
        bm.measure(11).notes[-1].pitch.accidental.displayStatus = False
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠠⠊⠝⠀⠎⠞⠗⠊⠉⠞⠀⠞⠊⠍⠑⠲⠀⠣⠣⠣⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠸⠋⠭⠘⠚⠭⠸⠋⠭⠀⠡⠫⠻⠩⠻⠀⠓⠭⠑⠭⠓⠭⠀⠪⠳⠻⠀⠋⠭⠙⠭⠊⠭
        ⠀⠀⠡⠘⠪⠺⠡⠺⠀⠙⠑⠭⠋⠭⠘⠚⠀⠸⠋⠡⠋⠭⠛⠭⠩⠛⠀⠓⠑⠭⠓⠭⠊⠀⠊⠓⠭⠛⠭⠋
        ⠀⠀⠸⠑⠙⠺⠈⠺⠀⠘⠏⠄⠣⠅
        '''

    def test_drill08_3(self):
        bm = converter.parse('''
            tinynotation: 6/8 r2 d'#8 c'#8 b4.~ b8 d'#8 g'#8 g'#4. f'#4 r8
             e'4.~ e'8 d'#8 g#8 d'#4 c'#8 d'#4 r8 a#8 g#8 a#8 b8 a#8 b8
             c'#8 d'#8 e'8 f'#8 g'#8 a'#8 b'8 f'#8 d'#8 g'#8 e'8 b8 f'#4 d'#8
             e'8 d'#8 c'#8 b8 f#8 d'#8 b4 f#8 d#8 f#8 b8 c'#4 a#8 b2.~ b4. r8
             ''').flatten()
        bm.insert(0, key.KeySignature(5))
        bm.insert(0, tempo.TempoText('Con delicatezza'))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[0].padAsAnacrusis(useInitialRests=True)
        for measure in m:
            measure.number -= 1
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠠⠉⠕⠝⠀⠙⠑⠇⠊⠉⠁⠞⠑⠵⠵⠁⠲⠀⠼⠑⠩⠼⠋⠦⠀⠀⠀⠀⠀⠀⠀
        ⠼⠚⠀⠨⠑⠙⠀⠺⠄⠈⠉⠚⠑⠓⠀⠳⠄⠻⠭⠀⠫⠄⠈⠉⠋⠑⠐⠓⠀⠨⠱⠙⠱⠭
        ⠀⠀⠐⠊⠓⠊⠚⠊⠚⠀⠙⠑⠋⠛⠓⠊⠀⠚⠛⠑⠓⠋⠐⠚⠀⠨⠻⠑⠋⠑⠙⠀⠚⠛⠨⠑⠺⠛
        ⠀⠀⠐⠑⠛⠚⠹⠊⠀⠞⠄⠈⠉⠀⠺⠄⠭⠣⠅
        '''

    def test_drill08_4(self):
        bm = converter.parse(
            'tinynotation: 4/4 A2.. G8 F2 E4 D4 E4. F8 G4 E4 C#2 D4 r4 '
            'AA2.. BBn8 C#4. D8 E4 G4 F4 G4 A4 F4 D2.. r8').flatten()
        bm.insert(0, key.KeySignature(-1))
        bm.insert(0, tempo.TempoText('Grazioso'))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠛⠗⠁⠵⠊⠕⠎⠕⠲⠀⠣⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠸⠎⠄⠄⠓⠀⠟⠫⠱⠀⠫⠄⠛⠳⠫⠀⠩⠝⠱⠧⠀⠘⠎⠄⠄⠡⠚⠀⠩⠹⠄⠑⠫⠳
        ⠀⠀⠸⠻⠳⠪⠻⠀⠕⠄⠄⠭⠣⠅
        '''

    def test_drill08_5(self):
        bm = converter.parse('''
            tinynotation: 2/2 r2 f'4 e'-4 d'2 b-4 g4 e'-2 c'4
            f4 f'2 e'-4 d'4 c'2 f4 f4 g2 f4 g4
            a2 d'4 c'4 b-4 a4 b-4 c'4 d'2 e'-4 f'4
            g'2 e'-4 c'4 f'2 d'4 b-4 e'-2 c'4 f4 d'2 b-4 b-4 c'2
            b-4 c'4 d'4 b-4 c'4 d'4 b-4 c'4 b-4 a4 b-2''', makeNotation=False)
        bm.replace(bm.getElementsByClass(meter.TimeSignature).first(), meter.TimeSignature('cut'))
        bm.insert(0, key.KeySignature(-2))
        bm.insert(0, tempo.TempoText('Ben marcato'))
        bm.insert(0, tempo.MetronomeMark(number=112, referent=note.Note(type='half')))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[0].padAsAnacrusis(useInitialRests=True)
        for measure in m:
            measure.number -= 1
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠠⠃⠑⠝⠀⠍⠁⠗⠉⠁⠞⠕⠲⠀⠝⠶⠼⠁⠁⠃⠀⠣⠣⠸⠉⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠚⠀⠨⠻⠫⠀⠕⠺⠳⠀⠨⠏⠹⠐⠻⠀⠨⠟⠫⠱⠀⠝⠐⠻⠻⠀⠗⠻⠳⠀⠎⠨⠱⠹⠀⠺⠪⠺⠹
        ⠀⠀⠨⠕⠫⠻⠀⠗⠫⠹⠀⠟⠱⠺⠀⠨⠏⠹⠐⠻⠀⠨⠕⠺⠺⠀⠝⠺⠹⠀⠱⠺⠹⠱⠀⠺⠹⠺⠪
        ⠀⠀⠐⠞⠣⠅
        '''

# ------------------------------------------------------------------------------
# Chapter 9: Fingering

    def test_example09_1(self):
        self.methodArgs = {'showFirstMeasureNumber': False}
        bm = converter.parse('tinynotation: 2/4 a4 g f4. c8').flatten()
        bm.insert(0, key.KeySignature(-1))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[-1].rightBarline = None
        m[0].notes[0].articulations.append(Fingering('4'))
        m[0].notes[1].articulations.append(Fingering('3'))
        m[1].notes[0].articulations.append(Fingering('2'))
        m[1].notes[1].articulations.append(Fingering('1'))
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠣⠼⠃⠲⠀⠀⠀
        ⠐⠪⠂⠳⠇⠀⠻⠄⠃⠙⠁
        '''
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 1 flat(s) ⠣
        Time Signature 2/4 ⠼⠃⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        A quarter ⠪
        G quarter ⠳
        ===
        Measure 2, Note Grouping 1:
        F quarter ⠻
        Dot ⠄
        C eighth ⠙
        ===
        ---end segment---
        '''

    def test_example09_2(self):
        self.methodArgs = {'showFirstMeasureNumber': False}
        bm = converter.parse("tinynotation: 3/4 f'4 e'-8 d' c' b-~ b-4 r8 a c' b-").flatten()
        bm.insert(0, key.KeySignature(-2))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[-1].rightBarline = None
        m[0].notes[0].articulations.append(Fingering('4'))
        m[0].notes[1].articulations.append(Fingering('3'))
        m[0].notes[2].articulations.append(Fingering('2'))
        m[0].notes[3].articulations.append(Fingering('1'))
        m[0].notes[4].articulations.append(Fingering('2'))
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠣⠣⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀
        ⠨⠻⠂⠋⠇⠑⠃⠙⠁⠚⠃⠈⠉⠀⠺⠭⠊⠙⠚
        '''

    def test_example09_3(self):
        self.methodArgs = {'showFirstMeasureNumber': False}
        bm = converter.parse('tinynotation: 6/8 c2.~ c4. f4 g8').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[-1].rightBarline = None
        m[0].notes[0].articulations.append(Fingering('1'))
        m[1].notes[1].articulations.append(Fingering('2'))
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠼⠋⠦⠀⠀⠀⠀⠀
        ⠐⠝⠄⠁⠈⠉⠀⠹⠄⠻⠃⠓
        '''

    def test_example09_4a(self):
        self.methodArgs = {'showFirstMeasureNumber': False}
        bm = converter.parse('tinynotation: 3/4 d2 F#4').flatten()
        bm.insert(0, key.KeySignature(2))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[-1].rightBarline = None
        m[0].notes[0].articulations.append(Fingering('2-1'))
        self.s = bm
        self.b = '''
        ⠀⠩⠩⠼⠉⠲⠀
        ⠐⠕⠃⠉⠁⠸⠻
        '''

    def test_example09_4b(self):
        self.methodArgs = {'showFirstMeasureNumber': False}
        bm = converter.parse('tinynotation: 3/4 c2 g4').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[-1].rightBarline = None
        m[0].notes[0].articulations.append(Fingering('3-1'))
        self.s = bm
        self.b = '''
        ⠀⠼⠉⠲⠀⠀
        ⠐⠝⠇⠉⠁⠳
        '''

    def test_example09_5a(self):
        self.methodArgs = {'showFirstMeasureNumber': False}
        bm = converter.parse("tinynotation: 2/4 c8 e g c'").flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[-1].rightBarline = None
        m[0].notes[3].articulations.append(Fingering('5|4'))
        self.s = bm
        self.b = '''
        ⠀⠀⠼⠃⠲⠀⠀⠀
        ⠐⠙⠋⠓⠨⠙⠅⠂
        '''

    def test_example09_5b(self):
        self.methodArgs = {'showFirstMeasureNumber': False,
                           'upperFirstInNoteFingering': False}
        bm = converter.parse('tinynotation: 6/8 d8 c d e4.').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[-1].rightBarline = None
        m[0].notes[0].articulations.append(Fingering('3|2'))
        m[0].notes[1].articulations.append(Fingering('2|1'))
        m[0].notes[2].articulations.append(Fingering('3|2'))
        m[0].notes[3].articulations.append(Fingering('4|3'))
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠼⠋⠦⠀⠀⠀⠀⠀⠀
        ⠐⠑⠃⠇⠙⠁⠃⠑⠃⠇⠫⠄⠇⠂
        '''

    def test_example09_6(self):
        self.methodArgs = {'showFirstMeasureNumber': False,
                           'upperFirstInNoteFingering': True}
        bm = converter.parse("tinynotation: 2/4 f#4 a d' f'# f'# e'").flatten()
        bm.insert(0, key.KeySignature(2))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)

        m[-1].rightBarline = None
        m[0].notes[0].articulations.append(Fingering('2,1'))
        m[0].notes[1].articulations.append(Fingering('1,2'))
        m[1].notes[0].articulations.append(Fingering('x,4'))
        m[1].notes[1].articulations.append(Fingering('4,5'))
        m[2].notes[0].articulations.append(Fingering('4,3'))
        m[2].notes[1].articulations.append(Fingering('3,2'))
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠩⠩⠼⠃⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠐⠻⠃⠁⠪⠁⠃⠀⠨⠱⠠⠂⠻⠂⠅⠀⠻⠂⠇⠫⠇⠃
        '''
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 2 sharp(s) ⠩⠩
        Time Signature 2/4 ⠼⠃⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        F quarter ⠻
        A quarter ⠪
        ===
        Measure 2, Note Grouping 1:
        Octave 5 ⠨
        D quarter ⠱
        F quarter ⠻
        ===
        Measure 3, Note Grouping 1:
        F quarter ⠻
        E quarter ⠫
        ===
        ---end segment---
        '''
        self.methodArgs = {'showFirstMeasureNumber': False,
                           'upperFirstInNoteFingering': False}
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠩⠩⠼⠃⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠐⠻⠁⠃⠪⠃⠁⠀⠨⠱⠂⠄⠻⠅⠂⠀⠻⠇⠂⠫⠃⠇
        '''

    def test_drill09_1(self):
        bm = converter.parse('''
            tinynotation: 6/8 r2 g8 a- b-4.~ b-8 g b- d'4.~ d'8 c'
            b- a-4 g8 e-4 f8 g4. r8 a- b-
            c'4.~ c'8 a- c' e'-4.~ e'-8 d' f' e'- d' c' b- a- f e-4.~ e-8
            ''').flatten()
        bm.insert(0.0, tempo.TempoText('Allegretto'))
        bm.insert(0.0, key.KeySignature(-3))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        bmSave = bm
        bm = bmSave.getElementsByClass(stream.Measure)

        bm[0].padAsAnacrusis(useInitialRests=True)
        for m in bm:
            m.number -= 1
        bm[0].notes[0].articulations.append(Fingering('2'))
        bm[1].notes[2].articulations.append(Fingering('1'))
        bm[2].notes[0].articulations.append(Fingering('5'))
        bm[3].notes[2].articulations.append(Fingering('2'))
        bm[3].notes[3].articulations.append(Fingering('1'))
        bm[4].notes[0].articulations.append(Fingering('2'))
        bm[5].notes[2].articulations.append(Fingering('1'))
        bm[5].notes[3].articulations.append(Fingering('2'))
        bm[6].notes[0].articulations.append(Fingering('3'))
        bm[6].notes[2].articulations.append(Fingering('2'))
        bm[6].notes[3].articulations.append(Fingering('4'))
        bm[7].notes[3].articulations.append(Fingering('4'))
        bm[7].notes[5].articulations.append(Fingering('2|1'))
        bm[8].notes[0].articulations.append(Fingering('1|2'))
        self.s = bmSave
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠁⠇⠇⠑⠛⠗⠑⠞⠞⠕⠲⠀⠣⠣⠣⠼⠋⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠚⠀⠐⠓⠃⠊⠀⠺⠄⠈⠉⠚⠓⠁⠚⠀⠱⠄⠅⠈⠉⠑⠙⠚⠀⠪⠓⠫⠃⠛⠁⠀⠳⠄⠃⠭⠊⠚
        ⠀⠀⠨⠹⠄⠈⠉⠙⠊⠁⠙⠃⠀⠫⠄⠇⠈⠉⠋⠑⠃⠛⠂⠀⠋⠑⠙⠚⠂⠊⠛⠃⠁
        ⠀⠀⠐⠫⠄⠁⠃⠈⠉⠋⠣⠅
        '''

    def test_drill09_2(self):
        bm = converter.parse('''
            tinynotation: 4/4 a2~ a8 g a d' c' b e' d' c' f'
            e'4~ e'8 f' e' b c' d' a b c' g a2~ a8 f
            g c' b a d' c' b e' d'2~ d'8 g' f' c' d' e' b c' d'4 a8 g a2.~ a8 r
            ''', makeNotation=False)
        bm.replace(bm.getElementsByClass(meter.TimeSignature).first(), meter.TimeSignature('c'))

        bm.insert(0, tempo.TempoText('Adagio e molto legato'))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        bmSave = bm
        bm = bmSave.getElementsByClass(stream.Measure)

        bm[0].notes[0].articulations.append(Fingering('2'))
        bm[0].notes[4].articulations.append(Fingering('5|4'))
        bm[1].notes[0].articulations.append(Fingering('4|3'))
        bm[1].notes[1].articulations.append(Fingering('3|1'))
        bm[1].notes[2].articulations.append(Fingering('5|4'))
        bm[1].notes[3].articulations.append(Fingering('4|3'))
        bm[1].notes[4].articulations.append(Fingering('3|2'))
        bm[1].notes[5].articulations.append(Fingering('5'))
        bm[1].notes[6].articulations.append(Fingering('4'))
        bm[2].notes[3].articulations.append(Fingering('1'))
        bm[2].notes[4].articulations.append(Fingering('2'))
        bm[2].notes[5].articulations.append(Fingering('3'))
        bm[2].notes[6].articulations.append(Fingering('1'))
        bm[3].notes[1].articulations.append(Fingering('1'))
        bm[3].notes[2].articulations.append(Fingering('2-3'))
        bm[3].notes[4].articulations.append(Fingering('1'))
        bm[4].notes[1].articulations.append(Fingering('4'))
        bm[4].notes[2].articulations.append(Fingering('3'))
        bm[4].notes[3].articulations.append(Fingering('2'))
        bm[4].notes[4].articulations.append(Fingering('4'))
        bm[4].notes[5].articulations.append(Fingering('3'))
        bm[4].notes[6].articulations.append(Fingering('2'))
        bm[4].notes[7].articulations.append(Fingering('4'))
        bm[5].notes[0].articulations.append(Fingering('3'))
        bm[5].notes[2].articulations.append(Fingering('5'))
        bm[6].notes[2].articulations.append(Fingering('1'))
        bm[6].notes[3].articulations.append(Fingering('2'))
        bm[6].notes[4].articulations.append(Fingering('3'))
        bm[6].notes[5].articulations.append(Fingering('1'))
        bm[6].notes[6].articulations.append(Fingering('2'))
        bm[7].notes[0].articulations.append(Fingering('1'))
        self.s = bmSave
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠠⠁⠙⠁⠛⠊⠕⠀⠑⠀⠍⠕⠇⠞⠕⠀⠇⠑⠛⠁⠞⠕⠲⠀⠨⠉⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠐⠎⠃⠈⠉⠊⠓⠊⠨⠑⠅⠂⠀⠙⠂⠇⠚⠇⠁⠨⠋⠅⠂⠑⠂⠇⠙⠇⠃⠛⠅⠫⠂⠈⠉
        ⠀⠀⠨⠋⠛⠋⠐⠚⠁⠙⠃⠑⠇⠐⠊⠁⠚⠀⠙⠐⠓⠁⠎⠃⠉⠇⠈⠉⠊⠛⠁
        ⠀⠀⠐⠓⠨⠙⠂⠚⠇⠊⠃⠨⠑⠂⠙⠇⠚⠃⠨⠋⠂⠀⠕⠇⠈⠉⠑⠓⠅⠛⠙
        ⠀⠀⠨⠑⠋⠐⠚⠁⠙⠃⠱⠇⠐⠊⠁⠓⠃⠀⠎⠄⠁⠈⠉⠊⠭⠣⠅
        '''

    def test_drill09_3(self):
        bm = converter.parse('tinynotation: 2/4 BB4 C#8 D E F# G A B4 c#8 d e f# g f# e4 d8 c# '
                             'B A G F# E4 D8 C# D C# BB AA# BB2').flatten()
        bm.insert(0, key.KeySignature(2))
        bm.insert(0, tempo.TempoText('Moderato'))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        bmSave = bm
        bm = bmSave.getElementsByClass(stream.Measure)

        bm[2].insert(0, clef.TrebleClef())
        bm[5].insert(0, clef.BassClef())
        # measure 1 fingerings
        bm[0].notes[0].articulations.append(Fingering('3,4'))
        bm[0].notes[1].articulations.append(Fingering('2,3'))
        bm[0].notes[2].articulations.append(Fingering('1,2'))
        # measure 2 fingerings
        bm[1].notes[0].articulations.append(Fingering('4,1'))
        bm[1].notes[1].articulations.append(Fingering('x,3'))
        bm[1].notes[2].articulations.append(Fingering('x,1'))
        bm[1].notes[3].articulations.append(Fingering('1,2'))
        # measure 3 fingerings
        bm[2].notes[0].articulations.append(Fingering('3,1'))
        bm[2].notes[1].articulations.append(Fingering('x,3'))
        bm[2].notes[2].articulations.append(Fingering('1,2'))
        # measure 4 fingerings
        bm[3].notes[0].articulations.append(Fingering('3,1'))
        bm[3].notes[1].articulations.append(Fingering('x,2'))
        bm[3].notes[2].articulations.append(Fingering('1,1'))
        bm[3].notes[3].articulations.append(Fingering('2,2'))
        # measure 5 fingerings
        bm[4].notes[0].articulations.append(Fingering('3,1'))
        bm[4].notes[1].articulations.append(Fingering('1,2'))
        bm[4].notes[2].articulations.append(Fingering('x,3'))
        # measure 6 fingerings
        bm[5].notes[0].articulations.append(Fingering('x,1'))
        bm[5].notes[1].articulations.append(Fingering('1,2'))
        bm[5].notes[2].articulations.append(Fingering('x,3'))
        bm[5].notes[3].articulations.append(Fingering('x,4'))
        # measure 7 fingerings
        bm[6].notes[0].articulations.append(Fingering('4,1'))
        bm[6].notes[1].articulations.append(Fingering('1,x'))
        bm[6].notes[2].articulations.append(Fingering('2,x'))
        # measure 8 fingerings
        bm[7].notes[0].articulations.append(Fingering('1,1'))
        bm[7].notes[1].articulations.append(Fingering('2,2'))
        bm[7].notes[2].articulations.append(Fingering('1,3'))
        bm[7].notes[3].articulations.append(Fingering('2,4'))
        # measure 9 fingerings
        bm[8].notes[0].articulations.append(Fingering('1,3'))
        self.s = bmSave
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠍⠕⠙⠑⠗⠁⠞⠕⠲⠀⠩⠩⠼⠃⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠘⠺⠇⠂⠙⠃⠇⠑⠁⠃⠀⠋⠂⠁⠛⠠⠇⠓⠠⠁⠊⠁⠃⠀⠺⠇⠁⠙⠠⠇⠑⠁⠃
        ⠀⠀⠐⠋⠇⠁⠛⠠⠃⠓⠁⠁⠛⠃⠃⠀⠫⠇⠁⠑⠁⠃⠙⠠⠇⠀⠚⠠⠁⠊⠁⠃⠓⠠⠇⠛⠠⠂
        ⠀⠀⠸⠫⠂⠁⠑⠁⠄⠙⠃⠄⠀⠑⠁⠁⠙⠃⠃⠚⠁⠇⠩⠊⠃⠂⠀⠞⠁⠇⠣⠅
        '''

    def test_drill09_4(self):
        bm = converter.parse('tinynotation: 5/8 E8 D# E F# D# BB4 E G8 G F# G A B '
                             'B4 BB BB8 DD GG BB GG BB E4 G F#8 '
                             'E BB G E BB E4 EE EE8 EE4 r8 EE8 EE DD '
                             'EE EE EE EE EE EE EE4 EE8 EE4~ EE8 r8 r').flatten()
        bm.insert(0, key.KeySignature(1))
        bm.insert(0, tempo.MetronomeMark(number=100, referent=note.Note(type='quarter')))
        bm.insert(0, tempo.TempoText('Not too fast'))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        bmSave = bm
        bm = bmSave.getElementsByClass(stream.Measure)
        # measure 1 fingerings
        bm[0].notes[1].articulations.append(Fingering('2'))
        bm[0].notes[3].articulations.append(Fingering('2'))
        # measure 2 fingerings
        bm[1].notes[1].articulations.append(Fingering('3'))
        # measure 3 fingerings
        bm[2].notes[0].articulations.append(Fingering('2'))
        bm[2].notes[1].articulations.append(Fingering('3'))
        bm[2].notes[4].articulations.append(Fingering('2'))
        # measure 4 fingerings
        bm[3].notes[0].articulations.append(Fingering('1'))
        bm[3].notes[1].articulations.append(Fingering('5'))
        bm[3].notes[2].articulations.append(Fingering('1'))
        # measure 5 fingerings
        bm[4].notes[2].articulations.append(Fingering('1'))
        bm[4].notes[3].articulations.append(Fingering('5'))
        bm[4].notes[4].articulations.append(Fingering('4'))
        # measure 6 fingerings
        bm[5].notes[0].articulations.append(Fingering('2'))
        bm[5].notes[1].articulations.append(Fingering('1'))
        # measure 8 fingerings
        bm[7].notes[0].articulations.append(Fingering('1'))
        bm[7].notes[1].articulations.append(Fingering('5'))
        bm[7].notes[2].articulations.append(Fingering('4'))
        # measure 9 fingerings
        bm[8].notes[0].articulations.append(Fingering('3'))
        bm[8].notes[1].articulations.append(Fingering('2'))
        bm[8].notes[2].articulations.append(Fingering('1'))
        # measure 10 fingerings
        bm[9].notes[0].articulations.append(Fingering('3'))
        bm[9].notes[1].articulations.append(Fingering('2'))
        bm[9].notes[2].articulations.append(Fingering('3'))
        bm[9].notes[3].articulations.append(Fingering('2'))
        bm[9].notes[4].articulations.append(Fingering('1'))
        # measure 11 fingerings
        bm[10].notes[0].articulations.append(Fingering('3'))
        bm[10].notes[1].articulations.append(Fingering('2'))
        bm[10].notes[2].articulations.append(Fingering('3'))
        bm[10].notes[3].articulations.append(Fingering('2'))
        # measure 12 fingerings
        bm[11].notes[0].articulations.append(Fingering('1'))
        self.s = bmSave
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠠⠝⠕⠞⠀⠞⠕⠕⠀⠋⠁⠎⠞⠲⠀⠹⠶⠼⠁⠚⠚⠀⠩⠼⠑⠦⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠸⠋⠩⠑⠃⠋⠛⠃⠑⠀⠺⠸⠫⠇⠓⠀⠓⠃⠛⠇⠓⠊⠚⠃⠀⠺⠁⠘⠺⠅⠚⠁
        ⠀⠀⠘⠑⠓⠚⠁⠓⠅⠚⠂⠀⠸⠫⠃⠳⠁⠛⠀⠋⠘⠚⠸⠓⠋⠘⠚⠀⠸⠫⠁⠘⠫⠅⠋⠂
        ⠀⠀⠘⠫⠇⠭⠋⠃⠋⠁⠀⠑⠇⠋⠃⠋⠇⠋⠃⠋⠁⠀⠋⠇⠋⠃⠫⠇⠋⠃⠀⠫⠁⠈⠉⠋⠭⠭⠣⠅
        '''

    def xtest_drill09_5(self):
        '''
        No longer working -- because of some changes in accidentals -- needs to
        be looked at.
        '''
        bm = converter.parse('''
            tinynotation: 3/4 f8 A G# A c A g B- A B- d B- g c Bn c a c b- c Bn c B- c
            A c a c Bn d c a g# a c' a c b- a b- c' b- a d' c' a g c f2.''').flatten()
        bm.insert(0, key.KeySignature(-1))
        bm.insert(0, tempo.TempoText('Lightly, almost in one'))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        bmSave = bm
        bm = bmSave.getElementsByClass(stream.Measure)
        gm2 = bm[1].notes[0].pitch.accidental
        if gm2:
            gm2.displayStatus = False
        # measure 1 fingerings
        bm[0].notes[0].articulations.append(Fingering('5'))
        bm[0].notes[1].articulations.append(Fingering('1'))
        bm[0].notes[2].articulations.append(Fingering('2'))
        bm[0].notes[3].articulations.append(Fingering('1'))
        # measure 2 fingerings
        bm[1].notes[1].articulations.append(Fingering('2'))
        bm[1].notes[2].articulations.append(Fingering('1'))
        bm[1].notes[3].articulations.append(Fingering('2'))
        bm[1].notes[4].articulations.append(Fingering('3'))
        bm[1].notes[5].articulations.append(Fingering('2'))
        # measure 3 fingerings
        bm[2].notes[5].articulations.append(Fingering('1'))
        # measure 4 fingerings
        bm[3].notes[1].articulations.append(Fingering('1'))
        bm[3].notes[2].articulations.append(Fingering('2'))
        bm[3].notes[3].articulations.append(Fingering('3'))
        bm[3].notes[4].articulations.append(Fingering('2'))
        bm[3].notes[5].articulations.append(Fingering('3'))
        # measure 5 fingerings
        bm[4].notes[0].articulations.append(Fingering('1'))
        bm[4].notes[1].articulations.append(Fingering('2'))
        bm[4].notes[2].articulations.append(Fingering('5'))
        bm[4].notes[3].articulations.append(Fingering('1'))
        bm[4].notes[4].articulations.append(Fingering('2'))
        bm[4].notes[5].articulations.append(Fingering('3'))
        # measure 6 fingerings
        bm[5].notes[0].articulations.append(Fingering('1'))
        bm[5].notes[1].articulations.append(Fingering('4'))
        bm[5].notes[2].articulations.append(Fingering('3'))
        bm[5].notes[3].articulations.append(Fingering('4'))
        # measure 7 fingerings
        bm[6].notes[1].articulations.append(Fingering('4'))
        bm[6].notes[2].articulations.append(Fingering('3'))
        # measure 8 fingerings
        bm[7].notes[1].articulations.append(Fingering('5'))
        bm[7].notes[2].articulations.append(Fingering('4'))
        bm[7].notes[3].articulations.append(Fingering('3'))
        bm[7].notes[4].articulations.append(Fingering('2'))
        bm[7].notes[5].articulations.append(Fingering('1'))
        # measure 12 fingerings
        bm[8].notes[0].articulations.append(Fingering('2'))
        self.s = bmSave
        self.b = '''
        ⠀⠠⠇⠊⠛⠓⠞⠇⠽⠂⠀⠁⠇⠍⠕⠎⠞⠀⠊⠝⠀⠕⠝⠑⠲⠀⠣⠼⠉⠲⠀
        ⠼⠁⠀⠐⠛⠅⠸⠊⠁⠩⠓⠃⠊⠁⠙⠊⠀⠐⠓⠸⠚⠃⠊⠁⠚⠃⠑⠇⠚⠃
        ⠀⠀⠐⠓⠙⠡⠚⠙⠐⠊⠐⠙⠁⠀⠣⠐⠚⠐⠙⠁⠡⠚⠃⠙⠇⠣⠚⠃⠙⠇
        ⠀⠀⠸⠊⠁⠙⠃⠐⠊⠅⠐⠙⠁⠡⠚⠃⠑⠇⠀⠙⠁⠐⠊⠂⠩⠓⠇⠊⠂⠙⠊
        ⠀⠀⠐⠙⠐⠚⠂⠊⠇⠚⠙⠚⠀⠊⠨⠑⠅⠙⠂⠊⠇⠓⠃⠙⠁⠀⠟⠄⠃⠣⠅
        '''

# ------------------------------------------------------------------------------
# Chapter 10: Changes of Signature; the Braille Music Hyphen, Asterisk, and
# Parenthesis; Clef Signs

    def test_example10_1(self):
        bm = stream.Part()

        m1 = stream.Measure(number=1)
        m1.append(clef.TrebleClef())
        m1.append(key.KeySignature(-4))
        m1.append(meter.TimeSignature('6/8'))
        m1.append(note.Note('F4'))
        m1.append(note.Note('C5', quarterLength=0.5))
        m1.append(note.Note('D-5', quarterLength=0.5))
        m1.append(note.Note('C5', quarterLength=0.5))
        m1.append(note.Note('B-4', quarterLength=0.5))
        bm.append(m1)

        m2 = stream.Measure(number=2)
        m2.append(meter.TimeSignature('2/4'))
        m2.append(note.Note('A-4'))
        m2.append(note.Note('G4'))
        m2.rightBarline = bar.Barline('double')
        bm.append(m2)

        m3 = stream.Measure(number=3)
        m3.append(key.KeySignature(-3))
        m3.append(meter.TimeSignature('6/8'))
        m3.append(note.Note('E-4', quarterLength=0.5))
        m3.append(note.Note('E-5', quarterLength=0.5))
        m3.append(note.Note('D5', quarterLength=0.5))
        m3.append(note.Note('E-5'))
        m3.append(note.Note('G4', quarterLength=0.5))
        bm.append(m3)

        m4 = stream.Measure(number=4)
        m4.append(meter.TimeSignature('3/4'))
        m4.append(note.Note('A-4'))
        m4.append(note.Note('G4'))
        m4.append(note.Note('F4'))
        m4.rightBarline = bar.Barline('double')
        bm.append(m4)

        m5 = stream.Measure(number=5)
        m5.append(key.KeySignature(0))
        m5.append(note.Note('G4', quarterLength=0.5))
        m5.append(note.Note('F4', quarterLength=0.5))
        m5.append(note.Note('E4', quarterLength=0.5))
        m5.append(note.Note('D4', quarterLength=0.5))
        m5.append(note.Note('C4', quarterLength=0.5))
        m5.append(note.Note('B3', quarterLength=0.5))
        bm.append(m5)

        m6 = stream.Measure(number=6)
        m6.append(note.Note('C4', quarterLength=3.0))
        m6.rightBarline = bar.Barline('final')
        bm.append(m6)

        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠣⠼⠋⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠐⠻⠨⠙⠑⠙⠚⠀⠼⠃⠲⠀⠐⠪⠳⠣⠅⠄⠀⠡⠣⠣⠣⠼⠋⠦⠀⠐⠋⠨⠋⠑⠫⠐⠓
        ⠀⠀⠼⠉⠲⠀⠐⠪⠳⠻⠣⠅⠄⠀⠡⠡⠡⠀⠐⠓⠛⠋⠑⠙⠚⠀⠝⠄⠣⠅
        '''

    def test_example10_2(self):
        self.methodArgs = {'dummyRestLength': 5, 'maxLineLength': 20}
        bm = converter.parse('tinynotation: 4/4 e8 f# g# a b- gn e c f a g c a2').flatten()
        bm.insert(0, key.KeySignature(-1))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        gm2 = m[1].notes[0].pitch.accidental
        if gm2:
            gm2.displayStatus = False
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠣⠼⠙⠲⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠄⠄⠄⠄⠄⠀⠐⠋⠩⠛⠩⠓⠊⠐
        ⠀⠀⠐⠚⠡⠓⠋⠙⠀⠛⠊⠓⠙⠐⠎⠣⠅
        '''

    def test_example10_3(self):
        self.methodArgs = {'dummyRestLength': 10, 'maxLineLength': 21}
        bm = converter.parse('tinynotation: 6/8 e8 f# g# a b- g e c f a g c a2.').flatten()
        bm.insert(0, key.KeySignature(-1))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        gm2 = m[1].notes[2].pitch.accidental
        if gm2:
            gm2.displayStatus = False

        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠼⠋⠦⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠀⠐⠋⠩⠛⠩⠓⠐
        ⠀⠀⠐⠊⠚⠡⠓⠀⠋⠙⠛⠊⠓⠙⠀⠐⠎⠄⠣⠅
        '''

    def test_example10_4(self):
        self.methodArgs = {'dummyRestLength': 10}
        bm = converter.parse(
            'tinynotation: 12/8 e2.~ e8 f# g# a b- gn c d e f4.~ f8 e f g f e f2.').flatten()
        bm.insert(0, key.KeySignature(-1))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[1].notesAndRests[3].pitch.accidental.displayStatus = False
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠼⠁⠃⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠀⠐⠏⠄⠈⠉⠋⠩⠛⠩⠓⠊⠚⠡⠓⠀⠙⠑⠋⠻⠄⠈⠉⠛⠐
        ⠀⠀⠐⠋⠛⠓⠛⠋⠀⠟⠄⠣⠅
        '''

    def test_example10_5(self):
        bm = converter.parse('''
            tinynotation: 3/4 g4. f8 e-4 B-4 b-4 g4 f2 g4
            e'-4. d'8 c'4 d'4 g4 bn4
            d'4 c'4 c'4 a-4. g8 f4 c4 c'4 en4 f2.''').flatten()
        bm.insert(0, key.KeySignature(-3))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[2].insert(1, bar.Barline('double'))
        m[5].insert(2, key.KeySignature(-4))
        m[5].insert(2, bar.Barline('double'))
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠣⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠐⠳⠄⠛⠫⠀⠸⠺⠐⠺⠳⠀⠟⠣⠅⠄⠐⠀⠐⠳⠀⠨⠫⠄⠑⠹⠀⠱⠐⠳⠡⠺
        ⠀⠀⠨⠱⠹⠣⠅⠄⠐⠀⠼⠙⠣⠀⠨⠹⠀⠪⠄⠓⠻⠀⠹⠨⠹⠡⠐⠫⠀⠟⠄⠣⠅
        '''

    def test_example10_6(self):
        bm = converter.parse('''
            tinynotation: 4/4 a4 a'~ a'8 g'# f'# e' f'#4
            e'~ e'8 d' c'# b d'4 c'#~ c'#8 b a b
            c'#2 r8 a'8 g'# f'# e' d' c'# b a b c'# b a2. r4''', makeNotation=False)
        bm.insert(0, key.KeySignature(3))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[3].insert(2.0, bar.Barline('double'))
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠩⠩⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠐⠪⠨⠪⠈⠉⠊⠓⠛⠋⠀⠻⠫⠈⠉⠋⠑⠙⠚⠀⠱⠹⠈⠉⠙⠚⠊⠚⠀⠝⠣⠅⠄
        ⠀⠀⠭⠨⠊⠓⠛⠀⠋⠑⠙⠚⠊⠚⠙⠚⠀⠎⠄⠧⠣⠅
        '''

    def test_example10_9(self):
        self.methodArgs = {'showClefSigns': False}
        bm = converter.parse("tinynotation: 4/4 BB-4 F B- f b- d' c' a b-1", makeNotation=False)
        bm.insert(0, key.KeySignature(-2))
        bm.insert(0, clef.BassClef())
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[0].insert(3.0, clef.TrebleClef())
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠣⠣⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠘⠺⠸⠻⠺⠐⠻⠀⠺⠱⠹⠪⠀⠾⠣⠅
        '''
        self.methodArgs = {'showClefSigns': True}
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠜⠼⠇⠘⠺⠸⠻⠺⠜⠌⠇⠐⠻⠀⠺⠱⠹⠪⠀⠾⠣⠅
        '''

    def test_example10_10(self):
        self.methodArgs = {'showClefSigns': False}
        bm = converter.parse("tinynotation: 6/8 a8 e a b c'# d' e' f'# g'# a'4.",
                             makeNotation=False)
        bm.insert(0, key.KeySignature(3))
        bm.insert(0, clef.AltoClef())
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[1].insert(0.0, clef.TrebleClef())
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠩⠩⠩⠼⠋⠦⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠐⠊⠋⠊⠚⠙⠑⠀⠋⠛⠓⠪⠄⠣⠅
        '''
        self.methodArgs = {'showClefSigns': True}
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠩⠩⠼⠋⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠜⠬⠇⠐⠊⠋⠊⠚⠙⠑⠀⠜⠌⠇⠨⠋⠛⠓⠪⠄⠣⠅
        '''

    def test_drill10_2(self):
        self.methodArgs = {'cancelOutgoingKeySig': False}
        bm = converter.parse('''tinynotation: 4/4 d4 f# a f# d8 e f# g a2
            e-4 g b- g e-8 f g a- b-2
            e4 g# b g# e8 f# g# a b2 f4 a c' a f8 g a b- c'2
            g-4 b- d'- b- g-8 a- b- c'- d'-2 d'4 b g b d'8 c' b a g2''', makeNotation=False)
        bm.insert(0.0, key.KeySignature(2))
        bm.insert(8.0, key.KeySignature(-3))
        bm.insert(16.0, key.KeySignature(4))
        bm.insert(24.0, key.KeySignature(-1))
        bm.insert(32.0, key.KeySignature(-6))
        bm.insert(40.0, key.KeySignature(0))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[1].rightBarline = bar.Barline('double')
        m[3].rightBarline = bar.Barline('double')
        m[5].rightBarline = bar.Barline('double')
        m[7].rightBarline = bar.Barline('double')
        m[9].rightBarline = bar.Barline('double')
        m[11].rightBarline = bar.Barline('double')
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠩⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠐⠱⠻⠪⠻⠀⠑⠋⠛⠓⠎⠣⠅⠄⠀⠣⠣⠣⠀⠐⠫⠳⠺⠳⠀⠋⠛⠓⠊⠞⠣⠅⠄⠀⠼⠙⠩
        ⠀⠀⠐⠫⠳⠺⠳⠀⠋⠛⠓⠊⠞⠣⠅⠄⠀⠣⠀⠐⠻⠪⠹⠪⠀⠛⠓⠊⠚⠝⠣⠅⠄⠀⠼⠋⠣
        ⠀⠀⠐⠳⠺⠱⠺⠀⠓⠊⠚⠙⠕⠣⠅⠄
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠁⠀⠨⠱⠺⠳⠺⠀⠑⠙⠚⠊⠗⠣⠅⠄
        '''
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 2 sharp(s) ⠩⠩
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        D quarter ⠱
        F quarter ⠻
        A quarter ⠪
        F quarter ⠻
        ===
        Measure 2, Note Grouping 1:
        D eighth ⠑
        E eighth ⠋
        F eighth ⠛
        G eighth ⠓
        A half ⠎
        Barline double ⠣⠅⠄
        ===
        Measure 3, Signature Grouping 1:
        Key Signature 3 flat(s) ⠣⠣⠣
        ===
        Measure 3, Note Grouping 1:
        Octave 4 ⠐
        E quarter ⠫
        G quarter ⠳
        B quarter ⠺
        G quarter ⠳
        ===
        Measure 4, Note Grouping 1:
        E eighth ⠋
        F eighth ⠛
        G eighth ⠓
        A eighth ⠊
        B half ⠞
        Barline double ⠣⠅⠄
        ===
        Measure 5, Signature Grouping 1:
        Key Signature 4 sharp(s) ⠼⠙⠩
        ===
        Measure 5, Note Grouping 1:
        Octave 4 ⠐
        E quarter ⠫
        G quarter ⠳
        B quarter ⠺
        G quarter ⠳
        ===
        Measure 6, Note Grouping 1:
        E eighth ⠋
        F eighth ⠛
        G eighth ⠓
        A eighth ⠊
        B half ⠞
        Barline double ⠣⠅⠄
        ===
        Measure 7, Signature Grouping 1:
        Key Signature 1 flat(s) ⠣
        ===
        Measure 7, Note Grouping 1:
        Octave 4 ⠐
        F quarter ⠻
        A quarter ⠪
        C quarter ⠹
        A quarter ⠪
        ===
        Measure 8, Note Grouping 1:
        F eighth ⠛
        G eighth ⠓
        A eighth ⠊
        B eighth ⠚
        C half ⠝
        Barline double ⠣⠅⠄
        ===
        Measure 9, Signature Grouping 1:
        Key Signature 6 flat(s) ⠼⠋⠣
        ===
        Measure 9, Note Grouping 1:
        Octave 4 ⠐
        G quarter ⠳
        B quarter ⠺
        D quarter ⠱
        B quarter ⠺
        ===
        Measure 10, Note Grouping 1:
        G eighth ⠓
        A eighth ⠊
        B eighth ⠚
        C eighth ⠙
        D half ⠕
        Barline double ⠣⠅⠄
        ===
        ---end segment---
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 11, Signature Grouping 1:
        <music21.key.KeySignature of no sharps or flats>
        ===
        Measure 11, Note Grouping 1:
        Octave 5 ⠨
        D quarter ⠱
        B quarter ⠺
        G quarter ⠳
        B quarter ⠺
        ===
        Measure 12, Note Grouping 1:
        D eighth ⠑
        C eighth ⠙
        B eighth ⠚
        A eighth ⠊
        G half ⠗
        Barline double ⠣⠅⠄
        ===
        ---end segment---
        '''
    # test_drill10_3 -- requires alternate time signature symbols

    def test_drill10_4(self):
        # TODO: 4/4 as c symbol.
        bm = converter.parse('''tinynotation: 4/4 r2. AA4 DD r d2~ d8 f e d c#4
            A B-2~ B-8 d cn B- A4 F D E
            F G8 A B-4 c#8 Bn c# d d e f a a4 g8 e c# g f d Bn f e c# A e d cn B- d
            c4 B-8 A G4 F8 E D4 AA DD''').flatten()
        bm.insert(0, key.KeySignature(-1))
        bm.insert(0, tempo.TempoText('Con brio'))
        bm.insert(25.0, clef.TrebleClef())
        bm.insert(32.0, clef.BassClef())
        bm[meter.TimeSignature].first().symbol = 'common'
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[0].padAsAnacrusis(useInitialRests=True)
        m[3].notes[3].pitch.accidental.displayStyle = 'parentheses'
        m[8].notes[6].pitch.accidental.displayStatus = False
        for sm in m:
            sm.number -= 1
        self.methodArgs = {'showClefSigns': True}
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠉⠕⠝⠀⠃⠗⠊⠕⠲⠀⠣⠨⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠚⠀⠜⠼⠇⠘⠪⠀⠱⠧⠐⠕⠈⠉⠀⠑⠛⠋⠑⠩⠹⠪⠀⠞⠈⠉⠚⠑⠠⠄⠡⠠⠄⠙⠚
        ⠀⠀⠸⠪⠻⠱⠫⠀⠻⠓⠊⠺⠩⠙⠡⠚⠀⠩⠙⠑⠜⠌⠇⠐⠑⠋⠛⠊⠪⠀⠓⠋⠩⠙⠓⠐
        ⠀⠀⠐⠛⠑⠡⠚⠐⠛⠀⠜⠼⠇⠐⠋⠩⠙⠊⠐⠋⠑⠡⠙⠚⠑⠀⠹⠚⠊⠳⠛⠋⠀⠱⠘⠪⠱⠣⠅
        '''
        self.e = '''
---begin segment---
<music21.braille.segment BrailleSegment>
Measure 0, Signature Grouping 1:
Key Signature 1 flat(s) ⠣
Time Signature common ⠨⠉
===
Measure 0, Tempo Text Grouping 1:
Tempo Text Con brio ⠠⠉⠕⠝⠀⠃⠗⠊⠕⠲
===
Measure 0, Note Grouping 1:
Bass Clef ⠜⠼
Octave 2 ⠘
A quarter ⠪
===
Measure 1, Note Grouping 1:
D quarter ⠱
Rest quarter ⠧
Octave 4 ⠐
D half ⠕
Tie ⠈⠉
===
Measure 2, Note Grouping 1:
D eighth ⠑
F eighth ⠛
E eighth ⠋
D eighth ⠑
Accidental sharp ⠩
C quarter ⠹
A quarter ⠪
===
Measure 3, Note Grouping 1:
B half ⠞
Tie ⠈⠉
B eighth ⠚
D eighth ⠑
Parenthesis ⠠⠄
Accidental natural ⠡
Parenthesis ⠠⠄
C eighth ⠙
B eighth ⠚
===
Measure 4, Note Grouping 1:
Octave 3 ⠸
A quarter ⠪
F quarter ⠻
D quarter ⠱
E quarter ⠫
===
Measure 5, Note Grouping 1:
F quarter ⠻
G eighth ⠓
A eighth ⠊
B quarter ⠺
Accidental sharp ⠩
C eighth ⠙
Accidental natural ⠡
B eighth ⠚
===
Measure 6, Note Grouping 1:
Accidental sharp ⠩
C eighth ⠙
D eighth ⠑
Treble Clef ⠜⠌
Octave 4 ⠐
D eighth ⠑
E eighth ⠋
F eighth ⠛
A eighth ⠊
A quarter ⠪
===
Measure 7, Split Note Grouping A 1:
G eighth ⠓
E eighth ⠋
Accidental sharp ⠩
C eighth ⠙
G eighth ⠓
music hyphen ⠐
===
Measure 7, Split Note Grouping B 1:
Octave 4 ⠐
F eighth ⠛
D eighth ⠑
Accidental natural ⠡
B eighth ⠚
Octave 4 ⠐
F eighth ⠛
===
Measure 8, Note Grouping 1:
Bass Clef ⠜⠼
Octave 4 ⠐
E eighth ⠋
Accidental sharp ⠩
C eighth ⠙
A eighth ⠊
Octave 4 ⠐
E eighth ⠋
D eighth ⠑
Accidental natural ⠡
C eighth ⠙
B eighth ⠚
D eighth ⠑
===
Measure 9, Note Grouping 1:
C quarter ⠹
B eighth ⠚
A eighth ⠊
G quarter ⠳
F eighth ⠛
E eighth ⠋
===
Measure 10, Note Grouping 1:
D quarter ⠱
Octave 2 ⠘
A quarter ⠪
D quarter ⠱
Barline final ⠣⠅
===
---end segment---
        '''

# ------------------------------------------------------------------------------
# Chapter 11: Segments for Single-Line Instrumental Music, Format for the
# Beginning of a Composition or Movement

    def test_example11_1(self):
        bm = converter.parse('''tinynotation: 3/4 D4 E8 F#8 G8 A8 B4 A4 G8 F#8
            E8 D8 C#8 D8 E8 F#8 G4 A4 r4 B4 c#8 d8 e8 f#8 e4 d4 c#8 B8
            c#8 e8 d8 c#8 B8 A#8 B2 r4 f#4 d8 c#8 B4 e4 c#8 B8 A#4 d4 B8 An8 G#4 A2 r4
            A4 G8 F#8 E8 D8 C#4 D4 E8 F#8 G8 A8 B8 A8 G8 F#8 E4 D4 r4''').flatten()
        bm.insert(0, key.KeySignature(2))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        bm.measure(9).insert(0, BrailleSegmentDivision())
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠩⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠸⠱⠋⠛⠓⠊⠀⠺⠪⠓⠛⠀⠋⠑⠙⠑⠋⠛⠀⠳⠪⠧⠀⠺⠙⠑⠋⠛⠀⠫⠱⠙⠚
        ⠀⠀⠐⠙⠋⠑⠙⠚⠩⠊⠀⠞⠧
        ⠼⠊⠀⠐⠻⠑⠙⠺⠀⠐⠫⠙⠚⠩⠪⠀⠐⠱⠚⠡⠊⠩⠳⠀⠎⠧⠀⠪⠓⠛⠋⠑⠀⠹⠱⠋⠛
        ⠀⠀⠸⠓⠊⠚⠊⠓⠛⠀⠫⠱⠧⠣⠅
        '''

    def test_example11_2(self):
        # this example was used elsewhere, so needed to be retained.
        bm = example11_2()
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠣⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠚⠀⠐⠺⠀⠳⠫⠱⠫⠀⠗⠻⠫⠀⠪⠳⠨⠹⠄⠙⠀⠞⠄⠺⠀⠨⠫⠐⠺⠪⠄⠓⠀⠗⠻⠨⠹
        ⠀⠀⠨⠹⠐⠻⠪⠄⠑⠀⠏⠄⠐
        ⠼⠓⠄⠀⠐⠳⠀⠳⠄⠛⠻⠻⠀⠎⠳⠺⠀⠺⠡⠪⠪⠹⠀⠞⠄⠺⠀⠨⠫⠐⠺⠪⠳⠀⠗⠻⠨⠹
        ⠀⠀⠨⠹⠧⠐⠻⠧⠀⠎⠄⠱⠀⠏⠄⠣⠅
        '''
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 0, Signature Grouping 1:
        Key Signature 3 flat(s) ⠣⠣⠣
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 0, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        B quarter ⠺
        ===
        Measure 1, Note Grouping 1:
        G quarter ⠳
        E quarter ⠫
        D quarter ⠱
        E quarter ⠫
        ===
        Measure 2, Note Grouping 1:
        G half ⠗
        F quarter ⠻
        E quarter ⠫
        ===
        Measure 3, Note Grouping 1:
        A quarter ⠪
        G quarter ⠳
        Octave 5 ⠨
        C quarter ⠹
        Dot ⠄
        C eighth ⠙
        ===
        Measure 4, Note Grouping 1:
        B half ⠞
        Dot ⠄
        B quarter ⠺
        ===
        Measure 5, Note Grouping 1:
        Octave 5 ⠨
        E quarter ⠫
        Octave 4 ⠐
        B quarter ⠺
        A quarter ⠪
        Dot ⠄
        G eighth ⠓
        ===
        Measure 6, Note Grouping 1:
        G half ⠗
        F quarter ⠻
        Octave 5 ⠨
        C quarter ⠹
        ===
        Measure 7, Note Grouping 1:
        Octave 5 ⠨
        C quarter ⠹
        Octave 4 ⠐
        F quarter ⠻
        A quarter ⠪
        Dot ⠄
        D eighth ⠑
        ===
        Measure 8, Note Grouping 1:
        E half ⠏
        Dot ⠄
        music hyphen ⠐
        ===
        ---end segment---
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 8, Note Grouping 2:
        Octave 4 ⠐
        G quarter ⠳
        ===
        Measure 9, Note Grouping 1:
        G quarter ⠳
        Dot ⠄
        F eighth ⠛
        F quarter ⠻
        F quarter ⠻
        ===
        Measure 10, Note Grouping 1:
        A half ⠎
        G quarter ⠳
        B quarter ⠺
        ===
        Measure 11, Note Grouping 1:
        B quarter ⠺
        Accidental natural ⠡
        A quarter ⠪
        A quarter ⠪
        C quarter ⠹
        ===
        Measure 12, Note Grouping 1:
        B half ⠞
        Dot ⠄
        B quarter ⠺
        ===
        Measure 13, Note Grouping 1:
        Octave 5 ⠨
        E quarter ⠫
        Octave 4 ⠐
        B quarter ⠺
        A quarter ⠪
        G quarter ⠳
        ===
        Measure 14, Note Grouping 1:
        G half ⠗
        F quarter ⠻
        Octave 5 ⠨
        C quarter ⠹
        ===
        Measure 15, Note Grouping 1:
        Octave 5 ⠨
        C quarter ⠹
        Rest quarter ⠧
        Octave 4 ⠐
        F quarter ⠻
        Rest quarter ⠧
        ===
        Measure 16, Note Grouping 1:
        A half ⠎
        Dot ⠄
        D quarter ⠱
        ===
        Measure 17, Note Grouping 1:
        E half ⠏
        Dot ⠄
        Barline final ⠣⠅
        ===
        ---end segment---
        '''

# ------------------------------------------------------------------------------
# Chapter 12: Slurs (Phrasing)

    def test_example12_1(self):
        bm = converter.parse(
            "tinynotation: 4/4 g4. f8 e4 d4 g4 f4 e4 r4 f4 g4 a4 b4 c'4 d'4 c'4 r4").flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[0].notes[0].articulations.append(Fingering('5'))
        m[2].notes[0].articulations.append(Fingering('2'))
        m[2].notes[1].articulations.append(Fingering('1'))
        m[0].append(spanner.Slur(m[0].notes[0], m[0].notes[1]))
        m[0].append(spanner.Slur(m[0].notes[2], m[0].notes[3]))
        m[1].append(spanner.Slur(m[1].notes[0], m[1].notes[2]))
        m[2].append(spanner.Slur(m[2].notes[0], m[2].notes[3]))
        m[3].append(spanner.Slur(m[3].notes[0], m[3].notes[2]))
        m[3].rightBarline = None
        self.s = bm
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠐⠳⠄⠅⠉⠛⠫⠉⠱⠀⠳⠉⠻⠉⠫⠧⠀⠻⠃⠉⠳⠁⠉⠪⠉⠺⠀⠹⠉⠱⠉⠹⠧
        '''

    def test_example12_2(self):
        bm = converter.parse("tinynotation: 4/4 g4. f8 e4 d g f e r f g a b c' d' c' r").flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[1].append(spanner.Slur(m[0].notes[0], m[1].notes[2]))
        m[3].append(spanner.Slur(m[2].notes[0], m[3].notes[2]))
        m[0].notes[0].articulations.append(Fingering('5'))
        m[2].notes[0].articulations.append(Fingering('1'))
        m[3].notes[0].articulations.append(Fingering('1'))
        m[3].rightBarline = None
        self.s = bm
        self.methodArgs = {'showFirstMeasureNumber': False,
                           'slurLongPhraseWithBrackets': False}
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠐⠳⠄⠅⠉⠉⠛⠫⠱⠀⠳⠻⠉⠫⠧⠀⠻⠁⠉⠉⠳⠪⠺⠀⠹⠁⠱⠉⠹⠧
        '''

    def test_example12_3(self):
        bm = converter.parse(
            "tinynotation: 4/4 e-4. f8 g4 e- f g a- r g g e'- d' c'2. r4").flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[1].append(spanner.Slur(m[0].notes[0], m[1].notes[2]))
        m[3].append(spanner.Slur(m[2].notes[0], m[3].notes[0]))
        m[0].notes[0].articulations.append(Fingering('1'))
        m[2].notes[0].articulations.append(Fingering('1'))
        m[2].notes[2].articulations.append(Fingering('4'))
        m[3].rightBarline = None
        self.s = bm
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠰⠃⠣⠐⠫⠄⠁⠛⠳⠫⠀⠻⠳⠣⠪⠘⠆⠧⠀⠰⠃⠳⠁⠳⠣⠨⠫⠂⠱⠀⠝⠄⠘⠆⠧
        '''

    def test_example12_4(self):
        bm = converter.parse("tinynotation: 12/8 e'4. c'4 g'8 g'4. f'4 e'8").flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[0].append(spanner.Slur(m[0].notes[0], m[0].notes[2]))
        m[0].append(spanner.Slur(m[0].notes[3], m[0].notes[5]))
        m[0].append(spanner.Slur(m[0].notes[0], m[0].notes[5]))
        m[0].rightBarline = None
        self.s = bm
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠼⠁⠃⠦⠀⠀⠀⠀⠀⠀
        ⠰⠃⠨⠫⠄⠉⠹⠉⠓⠳⠄⠉⠻⠉⠋⠘⠆
        '''

    def test_example12_5(self):
        bm = converter.parse("tinynotation: 3/4 a2 b4 a8 f'# e' d' c'# b a4 b8 c'# d' e' f'#2."
                             ).flatten()
        bm.insert(0, key.KeySignature(2))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[2].append(spanner.Slur(m[0].notes[0], m[2].notes[0]))
        m[3].append(spanner.Slur(m[2].notes[0], m[3].notes[0]))
        m[3].rightBarline = None
        self.s = bm
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠩⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠰⠃⠐⠎⠺⠀⠊⠨⠛⠋⠑⠙⠚⠀⠰⠃⠘⠆⠪⠚⠙⠑⠋⠀⠟⠄⠘⠆
        '''
        self.methodArgs = {'showFirstMeasureNumber': False, 'slurLongPhraseWithBrackets': False}
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠩⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠐⠎⠉⠉⠺⠀⠊⠨⠛⠋⠑⠙⠚⠉⠀⠪⠉⠉⠚⠙⠑⠋⠉⠀⠟⠄
        '''

    def test_example12_6(self):
        bm = converter.parse("tinynotation: 3/4 c'2~ c'8 d' d'2~ d'8 e'").flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[0].append(spanner.Slur(m[0].notes[0], m[0].notes[2]))
        m[1].append(spanner.Slur(m[1].notes[0], m[1].notes[2]))
        m[1].rightBarline = None
        self.s = bm
        self.methodArgs = {'showFirstMeasureNumber': False, 'showShortSlursAndTiesTogether': False}
        self.b = '''
        ⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀
        ⠨⠝⠈⠉⠙⠉⠑⠀⠕⠈⠉⠑⠉⠋
        '''
        self.methodArgs = {'showFirstMeasureNumber': False, 'showShortSlursAndTiesTogether': True}
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀
        ⠨⠝⠉⠈⠉⠙⠉⠑⠀⠕⠉⠈⠉⠑⠉⠋
        '''

    def test_example12_7(self):
        bm = converter.parse("tinynotation: 3/4 f'2.~ f'8 c' d' c' b- a").flatten()
        bm.insert(0, key.KeySignature(-1))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[-1].append(spanner.Slur(m[0].notes[0], m[-1].notes[-1]))
        m[-1].rightBarline = None
        self.s = bm
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠣⠼⠉⠲⠀⠀⠀⠀⠀⠀
        ⠰⠃⠨⠟⠄⠈⠉⠀⠛⠙⠑⠙⠚⠊⠘⠆
        '''
        self.methodArgs = {'showFirstMeasureNumber': False, 'slurLongPhraseWithBrackets': False}
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠣⠼⠉⠲⠀⠀⠀⠀⠀
        ⠨⠟⠄⠈⠉⠀⠛⠉⠉⠙⠑⠙⠚⠉⠊
        '''

    def test_example12_8(self):
        bm = converter.parse("tinynotation: 3/4 f'2.~ f'8 c' d' c' b- a").flatten()
        bm.insert(0, key.KeySignature(-1))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        ml = bm.getElementsByClass(stream.Measure).last()
        ml.append(spanner.Slur(ml.notes.first(), ml.notes.last()))
        ml.rightBarline = None
        self.s = bm
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠣⠼⠉⠲⠀⠀⠀⠀⠀⠀
        ⠨⠟⠄⠈⠉⠀⠰⠃⠛⠙⠑⠙⠚⠊⠘⠆
        '''
        self.methodArgs = {'showFirstMeasureNumber': False, 'slurLongPhraseWithBrackets': False}
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠣⠼⠉⠲⠀⠀⠀⠀⠀
        ⠨⠟⠄⠈⠉⠀⠛⠉⠉⠙⠑⠙⠚⠉⠊
        '''

    def test_example12_9(self):
        bm = converter.parse("tinynotation: 3/4 e'8 f' g' f' e' d' c'2.~ c'4 r r").flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[-1].append(spanner.Slur(m[0].notes[0], m[-1].notes[-1]))
        m[-1].rightBarline = None
        self.s = bm
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠰⠃⠨⠋⠛⠓⠛⠋⠑⠀⠝⠄⠈⠉⠀⠹⠘⠆⠧⠧
        '''
        self.methodArgs = {'showFirstMeasureNumber': False, 'slurLongPhraseWithBrackets': False}
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀
        ⠨⠋⠉⠉⠛⠓⠛⠋⠑⠉⠀⠝⠄⠈⠉⠀⠹⠧⠧
        '''

    def test_example12_10(self):
        bm = converter.parse("tinynotation: 3/4 e'8 f' g' f' e' d' c'2.~ c'4 r r").flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[1].append(spanner.Slur(m[0].notes[0], m[1].notes[0]))
        m[-1].rightBarline = None
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠰⠃⠨⠋⠛⠓⠛⠋⠑⠀⠝⠄⠘⠆⠈⠉⠀⠹⠧⠧
        '''
        self.methodArgs = {'showFirstMeasureNumber': False, 'slurLongPhraseWithBrackets': False}
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀
        ⠨⠋⠉⠉⠛⠓⠛⠋⠑⠉⠀⠝⠄⠈⠉⠀⠹⠧⠧
        '''

    def test_example12_11(self):
        bm = converter.parse('tinynotation: 4/4 c4 c c c').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[0].append(spanner.Slur(m[0].notes[0], m[0].notes[1]))
        m[0].append(spanner.Slur(m[0].notes[1], m[0].notes[2]))
        m[0].append(spanner.Slur(m[0].notes[2], m[0].notes[3]))
        m[0].notes[0].articulations.append(Fingering('3'))
        m[0].notes[1].articulations.append(Fingering('2'))
        m[0].notes[2].articulations.append(Fingering('1'))
        m[0].notes[3].articulations.append(Fingering('3'))
        m[-1].rightBarline = None
        self.s = bm
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.b = '''
        ⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀
        ⠐⠹⠇⠉⠹⠃⠉⠹⠁⠉⠹⠇
        '''

# ------------------------------------------------------------------------------
# Chapter 13: Words, Abbreviations, Letters, and Phrases of Expression

    def test_example13_1(self):
        bm = converter.parse(
            'tinynotation: 3/4 f2 e4 e4 d4 c4 a4. b-8 a4 g4 c8 d8 e8 f8 g4 f4 e4 f2.').flatten()
        bm.insert(0, key.KeySignature(-1))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[0].insert(0.0, expressions.TextExpression('dolce'))
        m[1].insert(2.0, dynamics.Dynamic('p'))
        m[3].insert(1.0, dynamics.Dynamic('mf'))
        m[4].insert(1.0, expressions.TextExpression('rit.'))
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠜⠙⠕⠇⠉⠑⠐⠟⠫⠀⠫⠱⠜⠏⠐⠹⠀⠐⠪⠄⠚⠪⠀⠳⠜⠍⠋⠐⠙⠑⠋⠛
        ⠀⠀⠐⠳⠜⠗⠊⠞⠄⠐⠻⠫⠀⠟⠄⠣⠅
        '''

    def test_example13_2(self):
        bm = converter.parse('''
            tinynotation: 4/4 d'#4 e'8 r b4 g a f# g fn8 e d e fn e f# g f# g# a#1
            ''').flatten()
        bm.insert(0, key.KeySignature(1))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        ml = bm.getElementsByClass(stream.Measure)
        ml[0].append(spanner.Slur(bm[0].notes[0], bm[0].notes[1]))
        ml[1].append(spanner.Slur(bm[0].notes[2], bm[1].notes[2]))
        ml[1].append(spanner.Slur(bm[1].notes[3], bm[1].notes[4]))
        ml[2].append(spanner.Slur(bm[2].notes[0], bm[2].notes[3]))
        ml[2].append(spanner.Slur(bm[2].notes[4], bm[2].notes[5]))
        ml[2].append(spanner.Slur(bm[2].notes[6], bm[2].notes[7]))
        ml[0].insert(0.0, dynamics.Dynamic('f'))
        ml[0].insert(2.0, dynamics.Dynamic('p'))
        ml[1].insert(3.0, expressions.TextExpression('rit.'))
        ml[2].insert(2.0, expressions.TextExpression('morendo'))
        ml[3].insert(4.0, dynamics.Dynamic('ppp'))
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠜⠋⠄⠩⠨⠱⠉⠋⠭⠜⠏⠰⠃⠐⠺⠳⠀⠪⠻⠳⠘⠆⠜⠗⠊⠞⠄⠡⠐⠛⠉⠋
        ⠀⠀⠐⠑⠉⠋⠉⠡⠛⠉⠋⠜⠍⠕⠗⠑⠝⠙⠕⠄⠩⠐⠛⠉⠓⠛⠉⠩⠓⠀⠩⠮⠜⠏⠏⠏⠄⠣⠅
        '''

    def xtest_example13_3(self):
        # Problem: How to plug in wedges into music21?
        bm = converter.parse('tinynotation: 4/4 a1 a1 a1 a1').flatten()
        commonTime = bm[meter.TimeSignature].first()
        if commonTime is not None:  # it is not None, but for typing
            commonTime.symbol = 'common'
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        ml = bm.getElementsByClass(stream.Measure)
        ml[-1].rightBarline = None
        e0 = expressions.TextExpression('cresc.')
        e1 = expressions.TextExpression('decresc.')
        ml[0].insert(0.0, e0)
        ml[1].insert(0.0, e1)
        # w1 = dynamics.Wedge(type='crescendo')
        self.s = bm
        # self.b = '''
        # '''

    def test_example13_9(self):
        bm = converter.parse("tinynotation: 4/4 g8 a b c' d' e' f' g'").flatten()
        bm.insert(0.0, dynamics.Dynamic('f'))
        bm.insert(0.0, expressions.TextExpression('rush!'))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        ml = bm.getElementsByClass(stream.Measure)
        ml[-1].rightBarline = None
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀
        ⠜⠗⠥⠎⠓⠖⠜⠋⠐⠓⠊⠚⠙⠑⠋⠛⠓
        '''

    def test_example13_10(self):
        bm = converter.parse('tinynotation: 4/4 c4 c e c').flatten()
        bm.insert(0.0, dynamics.Dynamic('f'))
        bm.insert(0.0, expressions.TextExpression('(marc.)'))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        ml = bm.getElementsByClass(stream.Measure)
        ml[-1].rightBarline = None
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀
        ⠜⠶⠍⠁⠗⠉⠄⠶⠜⠋⠐⠹⠹⠫⠹
        '''

    def xtest_example13_11(self):
        # Problem: How to braille the pp properly?
        bm = converter.parse('tinynotation: 4/4 b-2 r f e- d1 r B-').flatten()
        bm.insert(0.0, key.KeySignature(-2))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        ml = bm.getElementsByClass(stream.Measure)
        ml[0].insert(0.0, dynamics.Dynamic('f'))
        ml[0].insert(2.0, dynamics.Dynamic('pp'))
        ml[1].append(spanner.Slur(ml[1].notes[0], ml[1].notes[1]))
        ml[3].insert(0.0, expressions.TextExpression('rit.'))
        self.s = bm
        # self.b = '''
        # '''

    def test_example13_14(self):
        bm = converter.parse("tinynotation: 3/4 e'4 e' f'# g'2. f'#8 d' a d' e' c'# d'2.").flatten()
        bm.insert(0.0, key.KeySignature(2))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        ml = bm.getElementsByClass(stream.Measure)
        ml[2].insert(0.0, expressions.TextExpression('dim. e rall.'))
        ml[-1].rightBarline = None
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠩⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠨⠫⠫⠻⠀⠗⠄⠀⠜⠙⠊⠍⠄⠀⠑⠀⠗⠁⠇⠇⠄⠜⠀⠨⠛⠑⠐⠊⠨⠑⠋⠙⠀⠕⠄
        '''

    def test_example13_15(self):
        bm = converter.parse("tinynotation: 2/4 d'8 c' b- a g2 b-4. a8 g4. b-8 a4. g8 f2").flatten()
        bm.insert(0.0, key.KeySignature(-2))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        ml = bm.getElementsByClass(stream.Measure)
        ml[2].insert(0.0, expressions.TextExpression('calm, serene'))
        ml[-1].rightBarline = None
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠼⠃⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠨⠑⠙⠚⠊⠀⠗⠀⠜⠉⠁⠇⠍⠂⠀⠎⠑⠗⠑⠝⠑⠜⠀⠐⠺⠄⠊⠀⠳⠄⠚⠀⠪⠄⠓⠀⠟
        '''

    def test_example13_16(self):
        bm = converter.parse("tinynotation: 2/4 d'8 c' b- a g2 b-4. a8 g4. b-8 a4. g8 f2").flatten()
        bm.insert(0.0, key.KeySignature(-2))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        ml = bm.getElementsByClass(stream.Measure)
        # noinspection SpellCheckingInspection
        ml[2].insert(0.0, expressions.TextExpression('Sehr ruhig'))
        ml[-1].rightBarline = None
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠼⠃⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠨⠑⠙⠚⠊⠀⠗⠀⠜⠎⠑⠓⠗⠀⠗⠥⠓⠊⠛⠜⠀⠐⠺⠄⠊⠀⠳⠄⠚⠀⠪⠄⠓⠀⠟
        '''

    def test_example13_17(self):
        bm = converter.parse("tinynotation: 3/4 g4 r g' g' e' c' f' d' b c'2.").flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        ml = bm.getElementsByClass(stream.Measure)
        ml[0].insert(2.0, expressions.TextExpression('rit. e dim.'))
        ml[-1].append(spanner.Slur(bm[0].notes[1], bm[-1].notes[0]))
        ml[-1].rightBarline = None
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠐⠳⠧⠐⠀⠜⠗⠊⠞⠄⠀⠑⠀⠙⠊⠍⠄⠜⠀⠰⠃⠨⠳⠀⠳⠫⠹⠀⠻⠱⠺⠀⠝⠄⠘⠆
        '''

    def test_example13_18(self):
        bm = converter.parse('tinynotation: 3/4 FF4 GG8 AA BB- C    '
                             'D4 BB-8 C D E    F4 E8 D C4').flatten()
        bm.insert(0.0, key.KeySignature(-1))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        ml = bm.getElementsByClass(stream.Measure)
        ml[0].insert(1.0, expressions.TextExpression('speeding up'))
        ml[1].insert(2.0, expressions.TextExpression('slowing'))
        ml[-1].rightBarline = None
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠘⠻⠐⠀⠜⠎⠏⠑⠑⠙⠊⠝⠛⠀⠥⠏⠜⠀⠘⠓⠊⠚⠙⠀⠱⠚⠙⠐
        ⠀⠀⠜⠎⠇⠕⠺⠊⠝⠛⠸⠑⠋⠀⠻⠋⠑⠹
        '''
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 1 flat(s) ⠣
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.BassClef>
        Octave 2 ⠘
        F quarter ⠻
        music hyphen ⠐
        ===
        Measure 1, Long Text Expression Grouping 2:
        Word ⠜
        Text Expression speeding up ⠎⠏⠑⠑⠙⠊⠝⠛⠀⠥⠏
        Word ⠜
        music hyphen ⠐
        ===
        Measure 1, Note Grouping 2:
        Octave 2 ⠘
        G eighth ⠓
        A eighth ⠊
        B eighth ⠚
        C eighth ⠙
        ===
        Measure 2, Split Note Grouping A 1:
        D quarter ⠱
        B eighth ⠚
        C eighth ⠙
        music hyphen ⠐
        ===
        Measure 2, Split Note Grouping B 1:
        Word ⠜
        Text Expression slowing ⠎⠇⠕⠺⠊⠝⠛
        Octave 3 ⠸
        D eighth ⠑
        E eighth ⠋
        ===
        Measure 3, Note Grouping 1:
        F quarter ⠻
        E eighth ⠋
        D eighth ⠑
        C quarter ⠹
        ===
        ---end segment---
        '''

    def xtest_example13_19(self):
        bm = converter.parse("tinynotation: 3/4 c'8 d' c' b- a g a2.").flatten()
        bm.insert(0.0, key.KeySignature(-1))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        ml = bm.getElementsByClass(stream.Measure)
        ml[0].insert(0.0, dynamics.Dynamic('pp'))
        ml[0].insert(0.0, expressions.TextExpression('very sweetly'))
        ml[-1].rightBarline = None
        self.s = bm
        # self.b = '''
        # '''

    def test_example13_26(self):
        bm = converter.parse('''
            tinynotation: 4/4 e2 f#4 g a2 b4 a g2 f#4 e d2. r4
             b-4 d'8 f' b'-4 f'8 d'8
             b-4 e'-8 g' b'-4 g'8 e'-8 b-4 e'-8 f' a'4 f'8 e'-
             b-4 d'8 f' b'-4 r''', makeNotation=False)
        bm.insert(0.0, key.KeySignature(2))
        bm.insert(16.0, key.KeySignature(-2))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        ml = bm.getElementsByClass(stream.Measure)
        for m in ml:
            m.number += 44
        ml[4].append(spanner.Slur(ml[0].notes[0], ml[3].notes[0]))
        ml[1].insert(2.0, expressions.TextExpression('rall.'))
        ml[3].rightBarline = bar.Barline('double')
        ml[4].insert(0.0, expressions.TextExpression('ff'))
        ml[4].insert(0.0, tempo.TempoText('Presto'))
        ml[-1].rightBarline = None
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠩⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠙⠑⠀⠰⠃⠐⠏⠻⠳⠀⠎⠜⠗⠁⠇⠇⠄⠐⠺⠪⠀⠗⠻⠫⠀⠕⠄⠘⠆⠧⠣⠅⠄⠀⠡⠡⠣⠣
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠏⠗⠑⠎⠞⠕⠲⠀⠣⠣⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠙⠊⠀⠜⠋⠋⠐⠺⠑⠛⠺⠛⠑⠀⠺⠨⠋⠓⠺⠓⠋⠀⠐⠺⠨⠋⠛⠪⠛⠋⠀⠐⠺⠑⠛⠺⠧
        '''

# ------------------------------------------------------------------------------
# Chapter 14: Symbols of Expression and Execution

    def test_example14_1(self):
        bm = converter.parse("tinynotation: 4/4 f8 a c' a g c' e g").flatten()
        bm.notes[0].articulations.append(articulations.Accent())
        bm.notes[2].articulations.append(articulations.Accent())
        bm.notes[4].articulations.append(articulations.Accent())
        bm.notes[6].articulations.append(articulations.Accent())
        bm.insert(0, key.KeySignature(-1))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        bm.getElementsByClass(stream.Measure)[-1].rightBarline = None
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠣⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀
        ⠨⠦⠐⠛⠊⠨⠦⠙⠊⠨⠦⠓⠨⠙⠨⠦⠐⠋⠓
        '''

    def test_example14_2(self):
        '''
        Doubling of Tenuto marking is demonstrated. Accent is used in place of
        Reversed Accent because music21
        doesn't support the latter.
        '''
        bm = converter.parse("tinynotation: 3/4 e'2. d'4 f' b c' e g c' d' d'# e'2.").flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        ml = bm.getElementsByClass(stream.Measure)
        ml[2].append(spanner.Slur(bm[0].notes[0], bm[2].notes[0]))
        ml[2].notes[1].articulations.append(articulations.Tenuto())
        ml[2].notes[2].articulations.append(articulations.Tenuto())
        ml[3].notes[0].articulations.append(articulations.Tenuto())
        ml[3].notes[1].articulations.append(articulations.Tenuto())
        ml[3].notes[2].articulations.append(articulations.Tenuto())
        ml[4].notes[0].articulations.append(articulations.Accent())
        ml[-1].rightBarline = None
        self.methodArgs = {'showFirstMeasureNumber': False, 'slurLongPhraseWithBrackets': True}
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠰⠃⠨⠏⠄⠀⠱⠻⠐⠺⠀⠹⠘⠆⠸⠦⠸⠦⠐⠫⠳⠀⠨⠹⠱⠸⠦⠩⠱⠀⠨⠦⠏⠄
        '''

    def test_example14_3(self):
        bm = converter.parse('''
            tinynotation: 4/4 d'8 e'- c' d' b- a- g f g4 e- e-2
            e-4~ e-8 r g4~ g8 r f4~ f e-~ e-8 r''').flatten()
        bm.insert(0, key.KeySignature(-3))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m0 = bm.getElementsByClass(stream.Measure)[0]
        m1 = bm.getElementsByClass(stream.Measure)[1]
        m2 = bm.getElementsByClass(stream.Measure)[2]
        m3 = bm.getElementsByClass(stream.Measure)[3]
        mLast = bm.getElementsByClass(stream.Measure).last()

        m0.append(spanner.Slur(m0.notes.first(), m0.notes.last()))
        m0.notes[0].articulations.append(articulations.Accent())
        m1.notes[0].articulations.append(articulations.Staccato())
        m1.notes[1].articulations.append(articulations.Staccato())
        m1.notes[2].articulations.append(articulations.Tenuto())
        m2.notes[1].articulations.append(articulations.Staccato())
        m2.notes[3].articulations.append(articulations.Staccato())
        m3.notes[0].articulations.append(articulations.Tenuto())
        m3.notes[1].articulations.append(articulations.Tenuto())
        mLast.rightBarline = None
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠣⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠰⠃⠨⠦⠨⠑⠋⠙⠑⠚⠊⠓⠛⠘⠆⠀⠦⠳⠦⠫⠸⠦⠏⠀⠫⠉⠦⠋⠭⠳⠉⠦⠓⠭
        ⠀⠀⠸⠦⠐⠻⠉⠸⠦⠻⠫⠈⠉⠋⠭
        '''

    def test_example14_5(self):
        bm = converter.parse('tinynotation: 2/2 D8 r F r A r d r B-2 A4 r', makeNotation=False)
        bm.getElementsByClass(meter.TimeSignature).first().symbol = 'cut'
        bm.insert(0, key.KeySignature(-1))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m0 = bm.getElementsByClass(stream.Measure).first()
        m0.notes[0].articulations.append(articulations.Staccato())
        m0.notes[1].articulations.append(articulations.Staccato())
        m0.notes[2].articulations.append(articulations.Staccato())
        m0.notes[3].articulations.append(articulations.Staccato())
        bm.getElementsByClass(stream.Measure)[1].notes.first().articulations.append(
            articulations.Accent()
        )
        bm.getElementsByClass(stream.Measure)[-1].rightBarline = None
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠣⠸⠉⠀⠀⠀⠀⠀⠀⠀⠀
        ⠦⠦⠸⠑⠭⠛⠭⠊⠭⠦⠐⠑⠭⠀⠨⠦⠞⠪⠧
        '''

    def test_example14_6(self):
        bm = converter.parse('tinynotation: 3/4 F4 D8 F C E BB AA BB C D4 D8 E F4 r').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        for n in bm.flatten().notes[1:-1]:
            n.articulations.append(articulations.Staccato())
        for n in bm[1].notes:
            n.articulations.append(articulations.Accent())
        bm.getElementsByClass(stream.Measure)[2].notes[-1].articulations.append(
            articulations.Tenuto())
        bm.getElementsByClass(stream.Measure)[-1].rightBarline = None
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠸⠻⠦⠦⠑⠛⠙⠋⠀⠨⠦⠨⠦⠘⠚⠊⠚⠙⠨⠦⠱⠀⠑⠦⠋⠸⠦⠻⠧
        '''
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.BassClef>
        Octave 3 ⠸
        F quarter ⠻
        Articulation staccato ⠦
        Articulation staccato ⠦
        D eighth ⠑
        F eighth ⠛
        C eighth ⠙
        E eighth ⠋
        ===
        Measure 2, Note Grouping 1:
        Articulation accent ⠨⠦
        Articulation accent ⠨⠦
        Octave 2 ⠘
        B eighth ⠚
        A eighth ⠊
        B eighth ⠚
        C eighth ⠙
        Articulation accent ⠨⠦
        D quarter ⠱
        ===
        Measure 3, Note Grouping 1:
        D eighth ⠑
        Articulation staccato ⠦
        E eighth ⠋
        Articulation tenuto ⠸⠦
        F quarter ⠻
        Rest quarter ⠧
        ===
        ---end segment---
        '''

    def test_example14_7(self):
        bm = converter.parse('tinynotation: 3/4 C4 E F').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        for n in bm.getElementsByClass(stream.Measure).first().notes:
            n.articulations.append(articulations.Accent())
            n.articulations.append(articulations.Staccato())
        bm.getElementsByClass(stream.Measure).first().rightBarline = None
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀
        ⠦⠨⠦⠸⠹⠦⠨⠦⠫⠦⠨⠦⠻
        '''

    def test_example14_8(self):
        bm = converter.parse('tinynotation: 3/4 G4 B c').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        for n in bm.getElementsByClass(stream.Measure).first().notes:
            # pass
            n.articulations.append(articulations.Tenuto())
            n.articulations.append(articulations.Accent())
        bm.getElementsByClass(stream.Measure).first().rightBarline = None
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀
        ⠨⠦⠸⠦⠸⠳⠨⠦⠸⠦⠺⠨⠦⠸⠦⠹
        '''

    def test_example_14_14(self):
        bm = converter.parse('tinynotation: 3/4 G4~ G8 F D BB C2.').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        bm.measure(1).notes[0].articulations.append(articulations.Fingering(2))
        bm.measure(1).notes[2].articulations.append(articulations.Fingering(1))
        bm.measure(1).notes[0].expressions.append(expressions.Fermata())
        bm.measure(2).rightBarline = None
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀
        ⠸⠳⠃⠣⠇⠈⠉⠓⠛⠁⠑⠚⠀⠝⠄
        '''

    def test_example_14_15(self):
        bm = converter.parse('''
            tinynotation: 4/4 d'8 f' f'4 e'8 c' r4
            d'2 r4 d'8 f'     e' c' d'2 r4''').flatten()
        bm.insert(0, key.KeySignature(-1))
        sl = spanner.Slur(bm.notes[-5], bm.notes[-1])
        bm.insert(0, sl)
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        bm.measure(1).notesAndRests[-1].expressions.append(expressions.Fermata())
        bm.measure(2).notesAndRests[1].expressions.append(expressions.Fermata())
        bm.measure(3).notesAndRests[-1].expressions.append(expressions.Fermata())
        bm.measure(3).rightBarline = None
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠨⠑⠛⠻⠋⠙⠧⠣⠇⠀⠕⠧⠣⠇⠰⠃⠑⠛⠀⠋⠙⠕⠘⠆⠧⠣⠇
        '''

    # ------------------------------------------------------------------------------
    # Chapter 15: Smaller Values and Regular Note-Grouping, the Music Comma

    def test_example15_1(self):
        bm = converter.parse('''
            tinynotation: 2/4 r4. d8 g8. f#16 g8 b8 a8. g16 a8 b8 g8.
            g16 b8 d'8 e'4. e'8 d'8. b16 b8 g8 a8. g16
            a8 b8 g8. e16 e8 d8 g4.''', makeNotation=False)
        bm.insert(0, key.KeySignature(1))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        bm.getElementsByClass(stream.Measure).first().padAsAnacrusis(useInitialRests=True)
        for m in bm.getElementsByClass(stream.Measure):
            m.number -= 1
        bm.getElementsByClass(stream.Measure).last().rightBarline = None
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠼⠃⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠚⠀⠐⠑⠀⠓⠄⠿⠓⠚⠀⠊⠄⠷⠊⠚⠀⠓⠄⠷⠚⠑⠀⠫⠄⠋⠀⠑⠄⠾⠚⠓⠀⠊⠄⠷⠊⠚
        ⠀⠀⠐⠓⠄⠯⠋⠑⠀⠳⠄
        '''

    def test_example15_2(self):
        bm = converter.parse('''
            tinynotation: 2/4 d'8 r16 e'16 d'8 r16 c'#16
            d'4 b8 r8 b8 r16 c'16 b8 r16 a#16 b4 g8 r8''').flatten()
        bm.insert(0, key.KeySignature(1))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        bm.getElementsByClass(stream.Measure)[-1].rightBarline = None
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠼⠃⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠨⠑⠍⠯⠑⠍⠩⠽⠀⠱⠚⠭⠀⠚⠍⠽⠚⠍⠩⠮⠀⠺⠓⠭
        '''

    def test_example15_3(self):
        bm = converter.parse('''
            tinynotation: 6/8 e8. f16 e8 g4 g8 d8. e16 d8 f4 f8 c4 d8 e4 f8
            e4 d8 d4 e8 e4 f8 g4 a16 b32 c'32 c4 e16 d16 c4 r16''')
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        bm.getElementsByClass(stream.Measure)[-1].rightBarline = None
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠋⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠐⠋⠄⠿⠋⠳⠓⠀⠑⠄⠯⠑⠻⠛⠀⠹⠑⠫⠛⠀⠫⠑⠱⠋⠀⠫⠛⠳⠮⠞⠝
        ⠀⠀⠐⠹⠯⠵⠹⠍
        '''

    def test_example15_4(self):
        bm = converter.parse('''
            tinynotation: 3/4 e'4~ e'8. f'16 d'8. e'16 c'4 c''4 c''4
            g'#16 a'16 r8 e'16 f'16 r8 d'16 b16 r8 c'4 r4 r4''').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        bm.getElementsByClass(stream.Measure)[-1].rightBarline = None
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠨⠫⠈⠉⠋⠄⠿⠑⠄⠯⠀⠹⠰⠹⠹⠀⠩⠨⠷⠮⠭⠯⠿⠭⠵⠾⠭⠀⠹⠧⠧
        '''

    def test_example15_5(self):
        bm = converter.parse('''
            tinynotation: 3/8 r4 e16. b32 b8 a8 b8 b#8 c'#16 r16 e16.
            c'#32 c'#8 b8 c'#8 c'#8 d'16 r16 d'8 d'4 e'16 f'#16 f'#16
            b8. c'#8 e'8. d'16 c'#16 b16 a4''').flatten()
        bm.insert(0, key.KeySignature(3))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        bm.getElementsByClass(stream.Measure).first().padAsAnacrusis(useInitialRests=True)
        bm.getElementsByClass(stream.Measure)[3][1].pitch.accidental.displayStatus = False
        # remove cautionary accidental display
        for m in bm:
            m.number -= 1
        bm.getElementsByClass(stream.Measure).last().rightBarline = bar.Barline('double')
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠩⠩⠼⠉⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠚⠀⠐⠯⠄⠞⠀⠚⠊⠚⠀⠩⠚⠽⠍⠐⠯⠄⠨⠝⠀⠙⠚⠙⠀⠙⠵⠍⠑⠀⠱⠯⠿⠀⠿⠐⠚⠄⠙
        ⠀⠀⠨⠋⠄⠵⠽⠾⠀⠪⠣⠅⠄
        '''

    def test_example15_6a(self):
        # beamed 16th notes
        bm = converter.parse("tinynotation: 4/4 c16 B c d e d e f g g a b c' d' e' e'").flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        bm.getElementsByClass(stream.Measure)[-1].rightBarline = None
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀
        ⠐⠽⠚⠙⠑⠯⠑⠋⠛⠷⠓⠊⠚⠽⠑⠋⠋
        '''

    def test_example15_6b(self):
        # unbeamed 16th notes
        bm = converter.parse("tinynotation: 4/4 c16 B c d e d e f g g a b c' d' e' e'").flatten()
        # not calling makeNotation because it calls makeBeams
        bm.makeMeasures(inPlace=True)
        bm.makeAccidentals(cautionaryNotImmediateRepeat=False, inPlace=True)
        bm.getElementsByClass(stream.Measure)[-1].rightBarline = None
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀
        ⠐⠽⠾⠽⠵⠯⠵⠯⠿⠷⠷⠮⠾⠽⠵⠯⠯
        '''

    def test_example15_7(self):
        bm = converter.parse("tinynotation: 2/4 g16 d' c' b c'4 g16. f32 e16 d e4").flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        bm.getElementsByClass(stream.Measure)[-1].rightBarline = None
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠼⠃⠲⠀⠀⠀⠀⠀⠀
        ⠐⠷⠨⠑⠙⠚⠹⠀⠐⠷⠄⠟⠯⠵⠫
        '''

    def test_example15_8(self):
        bm = converter.parse('tinynotation: 2/4 G16 E F E G F r8 F16 D E D F E r8').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        bm.getElementsByClass(stream.Measure)[-1].rightBarline = None
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠼⠃⠲⠀⠀⠀⠀⠀⠀⠀
        ⠸⠷⠋⠛⠋⠷⠿⠭⠀⠿⠑⠋⠑⠿⠯⠭
        '''

    def test_example15_9(self):
        bm = converter.parse('''
            tinynotation: 2/4 r16 d' c' b c' d' e' c' b c' b a g
            f# g r g' f'# e' d' c' r b a g2''').flatten()
        bm.insert(0, key.KeySignature(1))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        bm.getElementsByClass(stream.Measure)[-1].rightBarline = None
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠼⠃⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠍⠨⠑⠙⠚⠽⠑⠋⠙⠀⠾⠙⠚⠊⠷⠿⠷⠍⠀⠨⠷⠛⠋⠑⠽⠍⠾⠮⠀⠗
        '''

    def xtest_example15_10(self):
        # print(translate.partToBraille(test.test_example15_10(),
        #       inPlace=True, dummyRestLength = 24))
        # Division of measure at end of line of "4/4" bar occurs
        #  in middle of measure, when in reality
        # it could occur 3/4 into the bar. Hypothetical example that might not be worth attacking.
        bm = converter.parse('tinynotation: 4/4 g16 a g f e8 c d16 e f d e8 c').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        bm.getElementsByClass(stream.Measure)[-1].rightBarline = None
        self.s = bm
        # self.b = '''
        # '''

    def test_example15_11(self):
        bm = converter.parse('''
            tinynotation: 12/8 r1 r4 r8 b-8 e-16 e'- g- g'- b- b'- bn b'n
            b- b'- bn b'n b- b'- a'- f' d' b- e'-4.''').flatten()
        bm2 = bm.makeNotation(cautionaryNotImmediateRepeat=False)
        lastMeasure = bm2.getElementsByClass(stream.Measure).last()
        lastMeasure.rightBarline = None
        for m in bm2.getElementsByClass(stream.Measure):
            m.number -= 1
        m0 = bm2.getElementsByClass(stream.Measure).first()
        for i in range(3):
            m0.pop(2)
        lastMeasure.notes[7].pitch.accidental = pitch.Accidental('natural')
        lastMeasure.notes[11].pitch.accidental = pitch.Accidental('natural')
        self.s = bm2
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠁⠃⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠚⠀⠣⠐⠚⠀⠣⠯⠣⠨⠋⠣⠐⠓⠣⠨⠓⠣⠐⠚⠣⠨⠚⠡⠐⠾⠡⠨⠾⠣⠐⠾⠣⠨⠾⠐
        ⠀⠀⠡⠐⠾⠡⠨⠾⠣⠐⠾⠣⠨⠚⠣⠊⠛⠑⠚⠨⠫⠄
        '''

# ------------------------------------------------------------------------------
# Chapter 16: Irregular Note-Grouping

# Triplets
# --------
    def test_example16_1(self):
        bm = converter.parse('tinynotation: 2/4 trip{c8 e a} g4 trip{B8 d a} g4').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        bm.getElementsByClass(stream.Measure)[-1].rightBarline = None
        for i in (0, 1):
            m = bm.getElementsByClass(stream.Measure)[i]
            m.notes.first().articulations.append(articulations.Accent())
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠼⠃⠲⠀⠀⠀⠀⠀⠀⠀
        ⠆⠨⠦⠐⠙⠋⠊⠳⠀⠆⠨⠦⠸⠚⠑⠊⠳
        '''

    def test_example16_2(self):
        bm = converter.parse('''
            tinynotation: 3/4 b-4~ trip{b-8 c' f} trip{b- d' f}
            b-4~ trip{b-8 c' d'} trip{d' c' b-}''').flatten()
        bm.insert(0, key.KeySignature(-2))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        bm.getElementsByClass(stream.Measure)[-1].rightBarline = None
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠐⠺⠈⠉⠆⠚⠙⠐⠛⠆⠚⠑⠐⠛⠀⠺⠈⠉⠆⠚⠙⠑⠆⠑⠙⠚
        '''

    def test_example16_4(self):
        bm = converter.parse('''
            tinynotation: 4/4 trip{c'8 b- a-} trip{a- b- c'}
            trip{b- c' b-} e-4''').flatten()
        bm.insert(0, key.KeySignature(-4))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m0 = bm.getElementsByClass(stream.Measure).first()
        m0.insert(0.0, dynamics.Dynamic('p'))
        m0.insert(0.0, expressions.TextExpression('legato'))
        m0.append(spanner.Slur(m0.notes.first(), m0.notes.last()))
        bm.getElementsByClass(stream.Measure)[-1].rightBarline = None
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠣⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠜⠇⠑⠛⠁⠞⠕⠜⠏⠰⠃⠆⠨⠙⠚⠊⠆⠊⠚⠙⠆⠚⠙⠚⠫⠘⠆
        '''

    def xtest_example16_6(self):
        bm = converter.parse('''
            tinynotation: 2/4 trip{b'-8 f' d'} trip{b- d' e'-}
            trip{f' d' b-} trip{f b- d'}''').flatten()
        bm.insert(0, key.KeySignature(-2))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        bm.getElementsByClass(stream.Measure)[-1].rightBarline = None
        self.s = bm
        # self.b = '''
        # '''

    def test_example16_15(self):
        bm = converter.parse('''
            tinynotation: 6/8 f#4 a8 d' c'# b quad{a g f# a} quad{g f# e g}
            f# g b a f# e d2.''').flatten()
        bm.insert(0, key.KeySignature(2))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        bm.getElementsByClass(stream.Measure)[-1].rightBarline = None
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠩⠼⠋⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠐⠻⠊⠨⠑⠙⠚⠀⠸⠲⠄⠊⠓⠛⠊⠸⠲⠄⠓⠛⠋⠓⠀⠛⠓⠚⠊⠛⠋⠀⠕⠄
        '''

    # ------------------------------------------------------------------------------
    # Chapter 17: Measure Repeats, Full-Measure In-Accords

    def test_example17_1(self):
        bm = converter.parse('tinynotation: 4/4 c4 e a g c e a g B d a g g1').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        bm.getElementsByClass(stream.Measure)[-1].rightBarline = None
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀
        ⠐⠹⠫⠪⠳⠀⠶⠀⠸⠺⠱⠪⠳⠀⠷
        '''

    def test_example17_2(self):
        bm = converter.parse('tinynotation: 4/4 g4 f# fn2 g4 f# fn2 e2 g2 e1').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        bm.getElementsByClass(stream.Measure)[-1].rightBarline = None
        m0 = bm.getElementsByClass(stream.Measure)[0]
        m0.notes[0].articulations.append(articulations.Staccato())
        m0.notes[1].articulations.append(articulations.Staccato())
        m0.notes[2].articulations.append(articulations.Accent())
        m1 = bm.getElementsByClass(stream.Measure)[1]
        m1.notes[0].articulations.append(articulations.Staccato())
        m1.notes[1].articulations.append(articulations.Staccato())
        m1.notes[2].articulations.append(articulations.Accent())
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀
        ⠦⠐⠳⠦⠩⠻⠨⠦⠡⠟⠀⠶⠀⠏⠗⠀⠯
        '''

    def test_example17_3(self):
        bm = converter.parse("tinynotation: 3/4 c4 e g c e g c e g c'2.").flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        bm.getElementsByClass(stream.Measure)[-1].rightBarline = None
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀
        ⠐⠹⠫⠳⠀⠶⠀⠶⠀⠨⠝⠄
        '''

    def test_example17_4(self):
        bm = converter.parse('tinynotation: 3/4 c4 e g c e g c e g a2.').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        bm.getElementsByClass(stream.Measure)[-1].rightBarline = None
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀
        ⠐⠹⠫⠳⠀⠶⠀⠶⠀⠎⠄
        '''

    def test_example17_5(self):
        bm = converter.parse('''
            tinynotation: 3/4 g4 g8 g g4
            g4 g8 g g4
            g4 g8 g g4
            g4 g8 g g4
            g4 g8 g g4
            g4 g8 g g4
            c8 e g c' e'4
            c8 e g c' e'4 ''')
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        bm.getElementsByClass(stream.Measure)[-1].rightBarline = None
        self.methodArgs = {'showFirstMeasureNumber': False}
        self.s = bm
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀
        ⠐⠳⠓⠓⠳⠀⠶⠼⠑⠀⠐⠙⠋⠓⠨⠙⠫⠀⠶
        '''

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# PART TWO
# Transcribing Two- and Three-Staff Music
#
# ------------------------------------------------------------------------------
# Chapter 24: Bar-over-Bar Format

    def test_example24_1a(self):
        self.method = measureToBraille
        rightHand = converter.parse('tinynotation: 4/4 c2 e2').flatten()
        rightHand.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = rightHand.getElementsByClass(stream.Measure).first()
        m.rightBarline = None
        m.insert(0.0, dynamics.Dynamic('f'))
        self.methodArgs = {'showHand': 'right', 'showHeading': True}
        self.s = m
        self.b = '''
        ⠀⠀⠼⠙⠲⠀⠀⠀
        ⠨⠜⠄⠜⠋⠐⠝⠏
        '''

    def test_example24_1b(self):
        self.method = measureToBraille
        leftHand = converter.parse('tinynotation: 2/4 C8 r8 E8 r8').flatten()
        leftHand.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)

        m = leftHand.getElementsByClass(stream.Measure).first()
        m.rightBarline = None
        self.methodArgs = {'showHand': 'left', 'showHeading': True}
        self.s = m
        self.b = '''
        ⠀⠀⠼⠃⠲⠀⠀
        ⠸⠜⠸⠙⠭⠋⠭
        '''

    def test_example24_2(self):
        self.method = keyboardPartsToBraille
        rightHand = converter.parse('''
            tinynotation: 2/4 c'8 g e g f g e a g
            f e d e e d r e d e g f g a f e g g f e2''').flatten()
        leftHand = converter.parse('''
            tinynotation: 2/4 C8 G c B A B c c B A G B
            c c B G c r B-4 A8 r c r c r B G c2''').flatten()
        rightHand.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        leftHand.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        keyboardPart = stream.Score()
        keyboardPart.append(rightHand)
        keyboardPart.append(leftHand)
        self.s = keyboardPart
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠃⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠁⠀⠨⠜⠨⠙⠐⠓⠋⠓⠀⠐⠛⠓⠋⠊⠀⠐⠓⠛⠋⠑⠀⠐⠋⠋⠑⠭⠀⠐⠋⠑⠋⠓⠀⠐⠛⠓⠊⠛
        ⠀⠀⠸⠜⠸⠙⠓⠐⠙⠚⠀⠸⠊⠚⠙⠙⠀⠸⠚⠊⠓⠚⠀⠐⠙⠙⠚⠓⠀⠐⠙⠭⠣⠺⠀⠸⠊⠭⠙⠭
        ⠛⠀⠨⠜⠐⠋⠓⠓⠛⠀⠐⠏⠣⠅
        ⠀⠀⠸⠜⠐⠙⠭⠚⠓⠀⠐⠝⠣⠅
        '''

    def test_example24_3(self):
        self.method = keyboardPartsToBraille
        rightHand = converter.parse(
            "tinynotation: 3/4 r2 d'4 d'8 e'-8 d'8 c'8 b-8 a8 g2 b-4").flatten()
        leftHand = converter.parse('''
            tinynotation: 3/4 r2 B-8 A G r B- r d
            r G A B- c d4''').flatten()
        rightHand.insert(0, key.KeySignature(-2))
        leftHand.insert(0, key.KeySignature(-2))
        rightHand.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        leftHand.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        rhm = rightHand.getElementsByClass(stream.Measure)
        lastRH = rhm[-1]
        lastRH.append(spanner.Slur(lastRH.notes[0], lastRH.notes[1]))
        rhm[0].notes[0].articulations.append(Fingering('3'))
        lastRH.notes[0].articulations.append(Fingering('1'))
        lastRH.notes[1].articulations.append(Fingering('3'))
        rhm[0].padAsAnacrusis(useInitialRests=True)

        lhm = leftHand.getElementsByClass(stream.Measure)
        lhm[0].padAsAnacrusis(useInitialRests=True)
        for m in rhm:
            m.number -= 1
        for m in lhm:
            m.number -= 1
        lastRH.rightBarline = None
        lhm[-1].rightBarline = None
        keyboardPart = stream.Score()
        keyboardPart.append(rightHand)
        keyboardPart.append(leftHand)
        self.s = keyboardPart
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠚⠀⠨⠜⠨⠱⠇⠀⠨⠑⠋⠑⠙⠚⠊⠀⠐⠗⠁⠉⠺⠇
        ⠀⠀⠸⠜⠸⠚⠊⠀⠸⠓⠭⠚⠭⠑⠭⠀⠸⠓⠊⠚⠙⠱
        '''

    def test_example24_4(self):
        self.method = keyboardPartsToBraille
        rightHand = converter.parse('''
            tinynotation: 4/4 d'16 b16 a16 f#16 e4~ e16 d16 A16 d16 e4
            c#16 B16 c#16 d16 e16 g16 f#16 e16 f#16 e16 f#16 g16 a16
            b16 c'#16 d'16 e'16 d'16 c'#16 b16 a16 g16 f#16 e16 d2''').flatten()
        leftHand = converter.parse('''
            tinynotation: 4/4 d'4~ d'16 c'#16 b16 g16 f#4~ f#16 g16
            b16 g16 a4 c'#4 d'8 d'16 e'16 f'#16 g'16 e'16 f'#16 g'4
            c'#4 r16 a16 f#16 e16 d4''').flatten()
        rightHand.transpose('P8', inPlace=True)
        rightHand.insert(0, key.KeySignature(2))
        leftHand.insert(0, key.KeySignature(2))
        rightHand.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        leftHand.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        for m in rightHand.getElementsByClass(stream.Measure):
            m.number += 8
        for m in leftHand.getElementsByClass(stream.Measure):
            m.number += 8
        keyboardPart = stream.Part()  # test that this works on a Part also,
        keyboardPart.append(rightHand)
        keyboardPart.append(leftHand)
        self.s = keyboardPart
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠩⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠀⠊⠀⠨⠜⠰⠵⠚⠊⠛⠫⠈⠉⠯⠑⠐⠊⠨⠑⠫⠀⠨⠽⠚⠙⠑⠯⠓⠛⠋⠿⠋⠛⠓⠮⠚⠙⠑
        ⠀⠀⠀⠸⠜⠨⠱⠈⠉⠵⠙⠚⠓⠻⠈⠉⠿⠓⠚⠓⠀⠐⠪⠹⠑⠵⠯⠿⠓⠋⠛⠀⠀⠀⠀⠀⠀⠀
        ⠁⠁⠀⠨⠜⠰⠯⠑⠙⠚⠮⠓⠛⠋⠕⠣⠅
        ⠀⠀⠀⠸⠜⠨⠳⠹⠍⠊⠛⠋⠱⠣⠅⠀⠀
        '''

    def xtest_example24_5(self):
        rightHand = converter.parse('''
            tinynotation: 2/4 trip{d'-8 c' b-} trip{f8 b- d'-}
            trip{c'8 an f} trip{c'8 d'- e'-} d'-4
            ''').flatten()
        leftHand = converter.parse('tinynotation: 2/4 B-4 B- An F B-2').flatten()
        rightHand.insert(0, key.KeySignature(-5))
        leftHand.insert(0, key.KeySignature(-5))
        rightHand.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        leftHand.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        rhm = rightHand.getElementsByClass(stream.Measure)
        lhm = leftHand.getElementsByClass(stream.Measure)
        for m in rhm:
            m.number += 9
        for m in lhm:
            m.number += 9
        rhm[0].notes[0].articulations.append(Fingering('4'))
        rhm[0].notes[1].articulations.append(Fingering('3'))
        rhm[0].notes[2].articulations.append(Fingering('2'))
        rhm[0].notes[3].articulations.append(Fingering('1'))
        rhm[0].notes[4].articulations.append(Fingering('2'))
        rhm[0].notes[5].articulations.append(Fingering('4'))
        rhm[1].notes[0].articulations.append(Fingering('3'))
        rhm[1].notes[3].articulations.append(Fingering('2'))
        keyboardPart = stream.Part()
        keyboardPart.append(rightHand)
        keyboardPart.append(leftHand)
        return keyboardPart

    # ------------------------------------------------------------------------------
    # Chapter 26: Interval Signs and Chords

    def test_example26_1a(self):
        self.method = measureToBraille
        c1 = chord.Chord(['G4', 'B4', 'D5', 'G5'], quarterLength=4.0)
        m1 = stream.Measure()
        m1.append(c1)
        self.methodArgs = {'showHand': 'right', 'descendingChords': True}
        self.s = m1
        self.b = '''
        ⠨⠜⠨⠷⠼⠴⠤
        '''

    def test_example26_1b(self):
        self.method = measureToBraille
        c1 = chord.Chord(['G2', 'B2', 'D3', 'G3'], quarterLength=4.0)
        m1 = stream.Measure()
        m1.append(c1)
        self.methodArgs = {'showHand': 'left', 'descendingChords': False}
        self.s = m1
        self.b = '''
        ⠸⠜⠘⠷⠬⠔⠤
        '''

    def test_example26_2(self):
        self.method = keyboardPartsToBraille
        chord_right = chord.Chord(['D4', 'B4', 'G5'], quarterLength=4.0)
        chord_left = chord.Chord(['G2', 'D3', 'B3'], quarterLength=4.0)
        part_right = stream.Part()
        part_right.append(meter.TimeSignature('c'))
        part_right.append(chord_right)
        part_left = stream.Part()
        part_left.append(meter.TimeSignature('c'))
        part_left.append(chord_left)
        part_right.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        part_left.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        part_right.getElementsByClass(stream.Measure)[-1].rightBarline = None
        part_left.getElementsByClass(stream.Measure)[-1].rightBarline = None
        keyboardPart = stream.Part()
        keyboardPart.append(part_right)
        keyboardPart.append(part_left)
        self.s = keyboardPart
        self.b = '''
        ⠀⠀⠀⠨⠉⠀⠀⠀
        ⠁⠀⠨⠜⠨⠷⠴⠼
        ⠀⠀⠸⠜⠘⠷⠔⠬
        '''

    def test_example26_3(self):
        self.method = keyboardPartsToBraille
        chord_right = chord.Chord(['C4', 'E5'], quarterLength=4.0)
        chord_left = chord.Chord(['C2', 'E3'], quarterLength=4.0)
        part_right = stream.Part()
        part_right.append(meter.TimeSignature('c'))
        part_right.append(chord_right)
        part_left = stream.Part()
        part_left.append(meter.TimeSignature('c'))
        part_left.append(chord_left)
        part_right.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        part_left.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        part_right.getElementsByClass(stream.Measure)[-1].rightBarline = None
        part_left.getElementsByClass(stream.Measure)[-1].rightBarline = None
        keyboardPart = stream.Part()
        keyboardPart.append(part_right)
        keyboardPart.append(part_left)
        self.s = keyboardPart
        self.b = '''
        ⠀⠀⠀⠨⠉⠀⠀⠀
        ⠁⠀⠨⠜⠨⠯⠐⠬
        ⠀⠀⠸⠜⠘⠽⠸⠬
        '''

    def test_example26_4(self):
        self.method = keyboardPartsToBraille
        chord_right = chord.Chord(['B4', 'E5', 'C6'], quarterLength=4.0)
        chord_left = chord.Chord(['G2', 'E3', 'E4'], quarterLength=4.0)
        part_right = stream.Part()
        part_right.append(meter.TimeSignature('c'))
        part_right.append(chord_right)
        part_left = stream.Part()
        part_left.append(meter.TimeSignature('c'))
        part_left.append(chord_left)
        part_right.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        part_left.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        part_right.getElementsByClass(stream.Measure)[-1].rightBarline = None
        part_left.getElementsByClass(stream.Measure)[-1].rightBarline = None
        keyboardPart = stream.Part()
        keyboardPart.append(part_right)
        keyboardPart.append(part_left)
        self.s = keyboardPart
        self.b = '''
        ⠀⠀⠀⠀⠨⠉⠀⠀⠀
        ⠁⠀⠨⠜⠰⠽⠴⠌⠀
        ⠀⠀⠸⠜⠘⠷⠴⠐⠴
        '''

    def test_example26_5(self):
        self.method = keyboardPartsToBraille
        C = chord.Chord
        N = note.Note
        all_right = [C(['G4', 'B4'], quarterLength=0.5), N('C5', quarterLength=0.5),
                     C(['B4', 'D5'], quarterLength=0.5), N('G4', quarterLength=0.5),
                     C(['C5', 'E5'], quarterLength=0.5), N('F#5', quarterLength=0.5),
                     C(['B4', 'G5'], quarterLength=0.5), N('G4', quarterLength=0.5)]
        part_right = stream.Part()
        part_right.append(key.KeySignature(1))
        part_right.append(meter.TimeSignature('4/4'))
        part_right.append(all_right)

        all_left = [C(['G2', 'D3'], quarterLength=0.5), N('E3', quarterLength=0.5),
                    C(['G2', 'D3'], quarterLength=0.5), N('B3', quarterLength=0.5),
                    C(['C3', 'G3'], quarterLength=0.5), N('A2', quarterLength=0.5),
                    C(['G2', 'D3'], quarterLength=0.5), N('B3', quarterLength=0.5)]
        part_left = stream.Part()
        part_left.append(key.KeySignature(1))
        part_left.append(meter.TimeSignature('4/4'))
        part_left.append(all_left)

        part_right.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        part_left.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        part_right.getElementsByClass(stream.Measure)[-1].rightBarline = None
        part_left.getElementsByClass(stream.Measure)[-1].rightBarline = None
        keyboardPart = stream.Part()
        keyboardPart.append(part_right)
        keyboardPart.append(part_left)
        self.s = keyboardPart
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠁⠀⠨⠜⠐⠚⠬⠙⠑⠬⠐⠓⠨⠋⠬⠛⠓⠴⠐⠓⠀⠀
        ⠀⠀⠸⠜⠘⠓⠔⠸⠋⠘⠓⠔⠸⠚⠸⠙⠔⠊⠓⠔⠸⠚
        '''

    def test_example26_6(self):
        self.method = keyboardPartsToBraille
        part_right = stream.Part()
        part_right.append(meter.TimeSignature('2/4'))
        part_right.append(chord.Chord(['C5', 'E5'], quarterLength=1.0))
        part_right.append(chord.Chord(['B4', 'D5'], quarterLength=1.0))
        part_right.append(chord.Chord(['C5', 'C5'], quarterLength=2.0))
        part_left = stream.Part()
        part_left.append(meter.TimeSignature('2/4'))
        part_left.append(chord.Chord(['E3', 'G3'], quarterLength=1.0))
        part_left.append(chord.Chord(['G3', 'G3'], quarterLength=1.0))
        part_left.append(chord.Chord(['C3', 'C4'], quarterLength=2.0))
        part_right.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        part_left.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        part_right.getElementsByClass(stream.Measure)[-1].rightBarline = None
        part_left.getElementsByClass(stream.Measure)[-1].rightBarline = None
        keyboardPart = stream.Part()
        keyboardPart.append(part_right)
        keyboardPart.append(part_left)
        self.s = keyboardPart
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠼⠃⠲⠀⠀⠀⠀⠀⠀
        ⠁⠀⠨⠜⠨⠫⠬⠱⠬⠀⠀⠨⠝⠨⠤
        ⠀⠀⠸⠜⠸⠫⠬⠳⠸⠤⠀⠸⠝⠤⠀
        '''
# ------------------------------------------------------------------------------


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)  # , runTest='test_example10_4')

