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

    def _s(self, streamIn):
        self.stream = streamIn

    s = property(fset=_s)

    def _neutralizeSpacing(self, sStr):
        sStr = textwrap.dedent(sStr)
        sStr = re.sub(r'^ *\n', '', sStr)  # remove spaces to first line break
        sStr = '\n'.join(line.rstrip() for line in sStr.split('\n'))
        sStr = sStr.rstrip() + '\n'  # (but not before first word.)
        return sStr

    def _b(self, brailleInput):
        '''
        Sets the expected brailleInput and runs assertMultilineEqual
        '''
        self.expectedBraille = self._neutralizeSpacing(brailleInput)
        if self.autoRun:
            self.runB()

    b = property(fset=_b)

    def _e(self, english):
        self.expectedEnglish = self._neutralizeSpacing(english)
        if self.autoRun:
            self.runE()

    e = property(fset=_e)

    def runB(self):
        ns = self._neutralizeSpacing
        if self.stream is None:
            return
        streamBraille = self.method(self.stream, inPlace=True, **self.methodArgs)
        self.assertMultiLineEqual(ns(streamBraille), self.expectedBraille)

    def runE(self):
        import copy
        ns = self._neutralizeSpacing
        if self.stream is None:
            return
        stream_copy = copy.deepcopy(self.stream)
        streamEnglish = self.method(stream_copy, inPlace=True, debug=True, **self.methodArgs)
        self.assertMultiLineEqual(ns(streamEnglish), self.expectedEnglish)

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
        Measure 5, Note Grouping 1:
        E eighth ⠋
        Rest eighth ⠭
        C eighth ⠙
        ===
        Measure 6, Note Grouping 1:
        D eighth ⠑
        Rest eighth ⠭
        F eighth ⠛
        ===
        Measure 7, Note Grouping 1:
        E eighth ⠋
        Rest eighth ⠭
        D eighth ⠑
        ===
        Measure 8, Note Grouping 1:
        C eighth ⠙
        Rest eighth ⠭
        Rest eighth ⠭
        ===
        Measure 9, Note Grouping 1:
        D eighth ⠑
        Rest eighth ⠭
        F eighth ⠛
        ===
        Measure 10, Note Grouping 1:
        E eighth ⠋
        Rest eighth ⠭
        G eighth ⠓
        ===
        Measure 11, Note Grouping 1:
        F eighth ⠛
        G eighth ⠓
        A eighth ⠊
        ===
        Measure 12, Note Grouping 1:
        G eighth ⠓
        Rest eighth ⠭
        Rest eighth ⠭
        ===
        Measure 13, Note Grouping 1:
        A eighth ⠊
        Rest eighth ⠭
        F eighth ⠛
        ===
        Measure 14, Note Grouping 1:
        G eighth ⠓
        Rest eighth ⠭
        E eighth ⠋
        ===
        Measure 15, Note Grouping 1:
        F eighth ⠛
        E eighth ⠋
        D eighth ⠑
        ===
        Measure 16, Note Grouping 1:
        C eighth ⠙
        Rest eighth ⠭
        Rest eighth ⠭
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠓⠭⠋⠀⠛⠭⠊⠀⠓⠭⠛⠀⠋⠭⠭⠀⠋⠭⠙⠀⠑⠭⠛⠀⠋⠭⠑⠀⠙⠭⠭⠀⠑⠭⠛
        ⠀⠀⠋⠭⠓⠀⠛⠓⠊⠀⠓⠭⠭⠀⠊⠭⠛⠀⠓⠭⠋⠀⠛⠋⠑⠀⠙⠭⠭⠣⠅
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 0, Signature Grouping 1:
        Time Signature 4/8 ⠼⠙⠦
        ===
        Measure 0, Note Grouping 1:
        <music21.clef.BassClef>
        D eighth ⠑
        ===
        Measure 1, Note Grouping 1:
        D eighth ⠑
        C eighth ⠙
        B eighth ⠚
        D eighth ⠑
        ===
        Measure 2, Note Grouping 1:
        C eighth ⠙
        B eighth ⠚
        A eighth ⠊
        C eighth ⠙
        ===
        Measure 3, Note Grouping 1:
        B eighth ⠚
        A eighth ⠊
        G eighth ⠓
        B eighth ⠚
        ===
        Measure 4, Note Grouping 1:
        A eighth ⠊
        A eighth ⠊
        D eighth ⠑
        Rest eighth ⠭
        ===
        Measure 5, Note Grouping 1:
        E eighth ⠋
        E eighth ⠋
        G eighth ⠓
        E eighth ⠋
        ===
        Measure 6, Note Grouping 1:
        D eighth ⠑
        E eighth ⠋
        G eighth ⠓
        B eighth ⠚
        ===
        Measure 7, Note Grouping 1:
        D eighth ⠑
        C eighth ⠙
        B eighth ⠚
        A eighth ⠊
        ===
        Measure 8, Note Grouping 1:
        G eighth ⠓
        G eighth ⠓
        G eighth ⠓
        Rest eighth ⠭
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 2/8 ⠼⠃⠦
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        E eighth ⠋
        E eighth ⠋
        ===
        Measure 2, Note Grouping 1:
        G eighth ⠓
        A eighth ⠊
        ===
        Measure 3, Note Grouping 1:
        G eighth ⠓
        F eighth ⠛
        ===
        Measure 4, Note Grouping 1:
        E eighth ⠋
        G eighth ⠓
        ===
        Measure 5, Note Grouping 1:
        F eighth ⠛
        E eighth ⠋
        ===
        Measure 6, Note Grouping 1:
        D eighth ⠑
        F eighth ⠛
        ===
        Measure 7, Note Grouping 1:
        E eighth ⠋
        C eighth ⠙
        ===
        Measure 8, Note Grouping 1:
        D eighth ⠑
        Rest eighth ⠭
        ===
        Measure 9, Note Grouping 1:
        E eighth ⠋
        E eighth ⠋
        ===
        Measure 10, Note Grouping 1:
        F eighth ⠛
        F eighth ⠛
        ===
        Measure 11, Note Grouping 1:
        G eighth ⠓
        A eighth ⠊
        ===
        Measure 12, Note Grouping 1:
        B eighth ⠚
        C eighth ⠙
        ===
        Measure 13, Note Grouping 1:
        A eighth ⠊
        F eighth ⠛
        ===
        Measure 14, Note Grouping 1:
        E eighth ⠋
        D eighth ⠑
        ===
        Measure 15, Note Grouping 1:
        C eighth ⠙
        B eighth ⠚
        ===
        Measure 16, Note Grouping 1:
        C eighth ⠙
        Rest eighth ⠭
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 3/8 ⠼⠉⠦
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        A eighth ⠊
        C eighth ⠙
        E eighth ⠋
        ===
        Measure 2, Note Grouping 1:
        D eighth ⠑
        C eighth ⠙
        B eighth ⠚
        ===
        Measure 3, Note Grouping 1:
        C eighth ⠙
        Rest eighth ⠭
        B eighth ⠚
        ===
        Measure 4, Note Grouping 1:
        A eighth ⠊
        Rest eighth ⠭
        Rest eighth ⠭
        ===
        Measure 5, Note Grouping 1:
        B eighth ⠚
        B eighth ⠚
        C eighth ⠙
        ===
        Measure 6, Note Grouping 1:
        D eighth ⠑
        C eighth ⠙
        B eighth ⠚
        ===
        Measure 7, Note Grouping 1:
        A eighth ⠊
        Rest eighth ⠭
        A eighth ⠊
        ===
        Measure 8, Note Grouping 1:
        B eighth ⠚
        Rest eighth ⠭
        Rest eighth ⠭
        Barline double ⠣⠅⠄
        ===
        Measure 9, Note Grouping 1:
        A eighth ⠊
        E eighth ⠋
        A eighth ⠊
        ===
        Measure 10, Note Grouping 1:
        C eighth ⠙
        B eighth ⠚
        A eighth ⠊
        ===
        Measure 11, Note Grouping 1:
        A eighth ⠊
        B eighth ⠚
        C eighth ⠙
        ===
        Measure 12, Note Grouping 1:
        D eighth ⠑
        Rest eighth ⠭
        Rest eighth ⠭
        ===
        Measure 13, Note Grouping 1:
        E eighth ⠋
        D eighth ⠑
        C eighth ⠙
        ===
        Measure 14, Note Grouping 1:
        B eighth ⠚
        E eighth ⠋
        B eighth ⠚
        ===
        Measure 15, Note Grouping 1:
        A eighth ⠊
        Rest eighth ⠭
        A eighth ⠊
        ===
        Measure 16, Note Grouping 1:
        A eighth ⠊
        Rest eighth ⠭
        Rest eighth ⠭
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 0, Signature Grouping 1:
        Time Signature 4/8 ⠼⠙⠦
        ===
        Measure 0, Note Grouping 1:
        <music21.clef.TrebleClef>
        D eighth ⠑
        E eighth ⠋
        ===
        Measure 1, Note Grouping 1:
        F eighth ⠛
        C eighth ⠙
        A eighth ⠊
        C eighth ⠙
        ===
        Measure 2, Note Grouping 1:
        D eighth ⠑
        C eighth ⠙
        A eighth ⠊
        C eighth ⠙
        ===
        Measure 3, Note Grouping 1:
        A eighth ⠊
        C eighth ⠙
        A eighth ⠊
        G eighth ⠓
        ===
        Measure 4, Note Grouping 1:
        E eighth ⠋
        G eighth ⠓
        F eighth ⠛
        Rest eighth ⠭
        ===
        Measure 5, Note Grouping 1:
        D eighth ⠑
        E eighth ⠋
        F eighth ⠛
        D eighth ⠑
        ===
        Measure 6, Note Grouping 1:
        C eighth ⠙
        D eighth ⠑
        E eighth ⠋
        F eighth ⠛
        ===
        Measure 7, Note Grouping 1:
        G eighth ⠓
        E eighth ⠋
        C eighth ⠙
        E eighth ⠋
        ===
        Measure 8, Note Grouping 1:
        F eighth ⠛
        Rest eighth ⠭
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 6/8 ⠼⠋⠦
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.BassClef>
        G eighth ⠓
        G eighth ⠓
        G eighth ⠓
        G eighth ⠓
        E eighth ⠋
        F eighth ⠛
        ===
        Measure 2, Note Grouping 1:
        A eighth ⠊
        G eighth ⠓
        G eighth ⠓
        G eighth ⠓
        Rest eighth ⠭
        G eighth ⠓
        ===
        Measure 3, Note Grouping 1:
        A eighth ⠊
        A eighth ⠊
        A eighth ⠊
        C eighth ⠙
        B eighth ⠚
        A eighth ⠊
        ===
        Measure 4, Note Grouping 1:
        A eighth ⠊
        G eighth ⠓
        G eighth ⠓
        G eighth ⠓
        Rest eighth ⠭
        Rest eighth ⠭
        ===
        Measure 5, Note Grouping 1:
        G eighth ⠓
        F eighth ⠛
        F eighth ⠛
        F eighth ⠛
        Rest eighth ⠭
        Rest eighth ⠭
        ===
        Measure 6, Note Grouping 1:
        F eighth ⠛
        E eighth ⠋
        E eighth ⠋
        E eighth ⠋
        Rest eighth ⠭
        Rest eighth ⠭
        ===
        Measure 7, Note Grouping 1:
        D eighth ⠑
        E eighth ⠋
        D eighth ⠑
        G eighth ⠓
        F eighth ⠛
        D eighth ⠑
        ===
        Measure 8, Note Grouping 1:
        C eighth ⠙
        E eighth ⠋
        D eighth ⠑
        C eighth ⠙
        Rest eighth ⠭
        Rest eighth ⠭
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 6/8 ⠼⠋⠦
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        E eighth ⠋
        Rest eighth ⠭
        E eighth ⠋
        F eighth ⠛
        Rest eighth ⠭
        F eighth ⠛
        ===
        Measure 2, Note Grouping 1:
        D eighth ⠑
        Rest eighth ⠭
        D eighth ⠑
        E eighth ⠋
        Rest eighth ⠭
        E eighth ⠋
        ===
        Measure 3, Note Grouping 1:
        C eighth ⠙
        D eighth ⠑
        E eighth ⠋
        G eighth ⠓
        F eighth ⠛
        E eighth ⠋
        ===
        Measure 4, Note Grouping 1:
        E eighth ⠋
        D eighth ⠑
        D eighth ⠑
        D eighth ⠑
        Rest eighth ⠭
        Rest eighth ⠭
        ===
        Measure 5, Note Grouping 1:
        C eighth ⠙
        Rest eighth ⠭
        C eighth ⠙
        E eighth ⠋
        Rest eighth ⠭
        E eighth ⠋
        ===
        Measure 6, Note Grouping 1:
        F eighth ⠛
        Rest eighth ⠭
        F eighth ⠛
        A eighth ⠊
        Rest eighth ⠭
        A eighth ⠊
        ===
        Measure 7, Note Grouping 1:
        G eighth ⠓
        Rest eighth ⠭
        G eighth ⠓
        G eighth ⠓
        A eighth ⠊
        B eighth ⠚
        ===
        Measure 8, Note Grouping 1:
        D eighth ⠑
        C eighth ⠙
        C eighth ⠙
        C eighth ⠙
        Rest eighth ⠭
        Rest eighth ⠭
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        D quarter ⠱
        B quarter ⠺
        G quarter ⠳
        B quarter ⠺
        ===
        Measure 2, Note Grouping 1:
        C quarter ⠹
        B quarter ⠺
        A quarter ⠪
        Rest quarter ⠧
        ===
        Measure 3, Note Grouping 1:
        B quarter ⠺
        G quarter ⠳
        E quarter ⠫
        G quarter ⠳
        ===
        Measure 4, Note Grouping 1:
        D quarter ⠱
        B quarter ⠺
        D quarter ⠱
        Rest quarter ⠧
        ===
        Measure 5, Note Grouping 1:
        E quarter ⠫
        G quarter ⠳
        A quarter ⠪
        G quarter ⠳
        ===
        Measure 6, Note Grouping 1:
        D quarter ⠱
        G quarter ⠳
        B quarter ⠺
        D quarter ⠱
        ===
        Measure 7, Note Grouping 1:
        E quarter ⠫
        D quarter ⠱
        C quarter ⠹
        A quarter ⠪
        ===
        Measure 8, Note Grouping 1:
        G quarter ⠳
        D quarter ⠱
        G quarter ⠳
        Rest quarter ⠧
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.BassClef>
        A quarter ⠪
        F quarter ⠻
        C quarter ⠹
        F quarter ⠻
        ===
        Measure 2, Note Grouping 1:
        G quarter ⠳
        E quarter ⠫
        C quarter ⠹
        E quarter ⠫
        ===
        Measure 3, Note Grouping 1:
        F quarter ⠻
        G quarter ⠳
        A quarter ⠪
        F quarter ⠻
        ===
        Measure 4, Note Grouping 1:
        D quarter ⠱
        E quarter ⠫
        F quarter ⠻
        Rest quarter ⠧
        ===
        Measure 5, Note Grouping 1:
        G quarter ⠳
        A quarter ⠪
        G quarter ⠳
        C quarter ⠹
        ===
        Measure 6, Note Grouping 1:
        F quarter ⠻
        A quarter ⠪
        C quarter ⠹
        D quarter ⠱
        ===
        Measure 7, Note Grouping 1:
        C quarter ⠹
        A quarter ⠪
        G quarter ⠳
        C quarter ⠹
        ===
        Measure 8, Note Grouping 1:
        D quarter ⠱
        E quarter ⠫
        F quarter ⠻
        Rest quarter ⠧
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 2/4 ⠼⠃⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        G quarter ⠳
        E quarter ⠫
        ===
        Measure 2, Note Grouping 1:
        A quarter ⠪
        G quarter ⠳
        ===
        Measure 3, Note Grouping 1:
        F quarter ⠻
        Rest quarter ⠧
        ===
        Measure 4, Note Grouping 1:
        D quarter ⠱
        Rest quarter ⠧
        ===
        Measure 5, Note Grouping 1:
        C quarter ⠹
        Dot ⠄
        C eighth ⠙
        ===
        Measure 6, Note Grouping 1:
        D quarter ⠱
        Dot ⠄
        D eighth ⠑
        ===
        Measure 7, Note Grouping 1:
        E quarter ⠫
        Rest quarter ⠧
        ===
        Measure 8, Note Grouping 1:
        C quarter ⠹
        Rest quarter ⠧
        ===
        Measure 9, Note Grouping 1:
        G quarter ⠳
        G quarter ⠳
        ===
        Measure 10, Note Grouping 1:
        A quarter ⠪
        B quarter ⠺
        ===
        Measure 11, Note Grouping 1:
        C quarter ⠹
        Rest quarter ⠧
        ===
        Measure 12, Note Grouping 1:
        A quarter ⠪
        Rest quarter ⠧
        ===
        Measure 13, Note Grouping 1:
        G quarter ⠳
        Dot ⠄
        G eighth ⠓
        ===
        Measure 14, Note Grouping 1:
        F quarter ⠻
        D quarter ⠱
        ===
        Measure 15, Note Grouping 1:
        C quarter ⠹
        E quarter ⠫
        ===
        Measure 16, Note Grouping 1:
        C quarter ⠹
        Rest quarter ⠧
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.BassClef>
        E quarter ⠫
        C eighth ⠙
        D eighth ⠑
        E quarter ⠫
        Rest quarter ⠧
        ===
        Measure 2, Note Grouping 1:
        F quarter ⠻
        A eighth ⠊
        F eighth ⠛
        E quarter ⠫
        Rest quarter ⠧
        ===
        Measure 3, Note Grouping 1:
        D quarter ⠱
        E eighth ⠋
        F eighth ⠛
        G eighth ⠓
        E eighth ⠋
        C quarter ⠹
        ===
        Measure 4, Note Grouping 1:
        D quarter ⠱
        D quarter ⠱
        G quarter ⠳
        Rest quarter ⠧
        ===
        Measure 5, Note Grouping 1:
        F quarter ⠻
        E eighth ⠋
        D eighth ⠑
        E quarter ⠫
        Rest quarter ⠧
        ===
        Measure 6, Note Grouping 1:
        G quarter ⠳
        F eighth ⠛
        E eighth ⠋
        F quarter ⠻
        Rest quarter ⠧
        ===
        Measure 7, Note Grouping 1:
        A quarter ⠪
        G eighth ⠓
        F eighth ⠛
        E eighth ⠋
        F eighth ⠛
        G quarter ⠳
        ===
        Measure 8, Note Grouping 1:
        F quarter ⠻
        D quarter ⠱
        C quarter ⠹
        Rest quarter ⠧
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        F quarter ⠻
        Dot ⠄
        C eighth ⠙
        D quarter ⠱
        E quarter ⠫
        ===
        Measure 2, Note Grouping 1:
        F quarter ⠻
        Dot ⠄
        G eighth ⠓
        A quarter ⠪
        F quarter ⠻
        ===
        Measure 3, Note Grouping 1:
        A quarter ⠪
        C quarter ⠹
        D quarter ⠱
        C quarter ⠹
        ===
        Measure 4, Note Grouping 1:
        A quarter ⠪
        F quarter ⠻
        G quarter ⠳
        Rest quarter ⠧
        Barline double ⠣⠅⠄
        ===
        Measure 5, Note Grouping 1:
        G quarter ⠳
        Dot ⠄
        E eighth ⠋
        C quarter ⠹
        E quarter ⠫
        ===
        Measure 6, Note Grouping 1:
        F quarter ⠻
        Dot ⠄
        C eighth ⠙
        F quarter ⠻
        A quarter ⠪
        ===
        Measure 7, Note Grouping 1:
        G quarter ⠳
        G quarter ⠳
        F quarter ⠻
        E quarter ⠫
        ===
        Measure 8, Note Grouping 1:
        F quarter ⠻
        A quarter ⠪
        F quarter ⠻
        Rest quarter ⠧
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        G quarter ⠳
        G eighth ⠓
        D quarter ⠱
        D eighth ⠑
        ===
        Measure 2, Note Grouping 1:
        G quarter ⠳
        B eighth ⠚
        D eighth ⠑
        B eighth ⠚
        G eighth ⠓
        ===
        Measure 3, Note Grouping 1:
        A quarter ⠪
        A eighth ⠊
        A eighth ⠊
        B eighth ⠚
        C eighth ⠙
        ===
        Measure 4, Note Grouping 1:
        B quarter ⠺
        B eighth ⠚
        G quarter ⠳
        Rest eighth ⠭
        ===
        Measure 5, Note Grouping 1:
        A quarter ⠪
        A eighth ⠊
        D quarter ⠱
        D eighth ⠑
        ===
        Measure 6, Note Grouping 1:
        G quarter ⠳
        B eighth ⠚
        A quarter ⠪
        C eighth ⠙
        ===
        Measure 7, Note Grouping 1:
        B eighth ⠚
        C eighth ⠙
        D eighth ⠑
        C quarter ⠹
        A eighth ⠊
        ===
        Measure 8, Note Grouping 1:
        G quarter ⠳
        G eighth ⠓
        G quarter ⠳
        Rest eighth ⠭
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        C half ⠝
        E half ⠏
        ===
        Measure 2, Note Grouping 1:
        D half ⠕
        F half ⠟
        ===
        Measure 3, Note Grouping 1:
        E half ⠏
        G half ⠗
        ===
        Measure 4, Note Grouping 1:
        F half ⠟
        A half ⠎
        ===
        Measure 5, Note Grouping 1:
        G half ⠗
        B half ⠞
        ===
        Measure 6, Note Grouping 1:
        A half ⠎
        C half ⠝
        ===
        Measure 7, Note Grouping 1:
        B half ⠞
        D half ⠕
        ===
        Measure 8, Note Grouping 1:
        C half ⠝
        Rest half ⠥
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.BassClef>
        F half ⠟
        A half ⠎
        ===
        Measure 2, Note Grouping 1:
        G half ⠗
        C half ⠝
        ===
        Measure 3, Note Grouping 1:
        D quarter ⠱
        C quarter ⠹
        D quarter ⠱
        E quarter ⠫
        ===
        Measure 4, Note Grouping 1:
        F half ⠟
        Rest half ⠥
        ===
        Measure 5, Note Grouping 1:
        D half ⠕
        F half ⠟
        ===
        Measure 6, Note Grouping 1:
        C half ⠝
        F half ⠟
        ===
        Measure 7, Note Grouping 1:
        E quarter ⠫
        F quarter ⠻
        G quarter ⠳
        A quarter ⠪
        ===
        Measure 8, Note Grouping 1:
        F half ⠟
        Rest half ⠥
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        C half ⠝
        C quarter ⠹
        ===
        Measure 2, Note Grouping 1:
        D eighth ⠑
        C eighth ⠙
        B eighth ⠚
        C eighth ⠙
        D quarter ⠱
        ===
        Measure 3, Note Grouping 1:
        E half ⠏
        E quarter ⠫
        ===
        Measure 4, Note Grouping 1:
        F eighth ⠛
        E eighth ⠋
        D eighth ⠑
        E eighth ⠋
        F quarter ⠻
        ===
        Measure 5, Note Grouping 1:
        G half ⠗
        G quarter ⠳
        ===
        Measure 6, Note Grouping 1:
        A eighth ⠊
        G eighth ⠓
        F eighth ⠛
        G eighth ⠓
        A quarter ⠪
        ===
        Measure 7, Note Grouping 1:
        B eighth ⠚
        A eighth ⠊
        G eighth ⠓
        A eighth ⠊
        B eighth ⠚
        D eighth ⠑
        ===
        Measure 8, Note Grouping 1:
        C quarter ⠹
        Rest half ⠥
        ===
        Measure 9, Note Grouping 1:
        E half ⠏
        E quarter ⠫
        ===
        Measure 10, Note Grouping 1:
        D eighth ⠑
        C eighth ⠙
        B eighth ⠚
        C eighth ⠙
        D quarter ⠱
        ===
        Measure 11, Note Grouping 1:
        C half ⠝
        C quarter ⠹
        ===
        Measure 12, Note Grouping 1:
        B eighth ⠚
        A eighth ⠊
        G eighth ⠓
        A eighth ⠊
        B quarter ⠺
        ===
        Measure 13, Note Grouping 1:
        A half ⠎
        A quarter ⠪
        ===
        Measure 14, Note Grouping 1:
        G eighth ⠓
        F eighth ⠛
        E eighth ⠋
        F eighth ⠛
        G quarter ⠳
        ===
        Measure 15, Note Grouping 1:
        F eighth ⠛
        E eighth ⠋
        D eighth ⠑
        E eighth ⠋
        F eighth ⠛
        D eighth ⠑
        ===
        Measure 16, Note Grouping 1:
        C quarter ⠹
        Rest half ⠥
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        F half ⠟
        Tie ⠈⠉
        F quarter ⠻
        Dot ⠄
        F eighth ⠛
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        G quarter ⠳
        Dot ⠄
        Tie ⠈⠉
        G eighth ⠓
        A eighth ⠊
        G eighth ⠓
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        G half ⠗
        G quarter ⠳
        Tie ⠈⠉
        ===
        ---end segment---
        '''
        self.b = '''
        ⠼⠉⠲⠀⠗⠳⠈⠉
        '''
        self.s = m[1]
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 2, Note Grouping 1:
        G half ⠗
        Rest quarter ⠧
        ===
        ---end segment---
        '''
        self.b = '''
        ⠗⠧
        '''

    def test_example04_7(self):
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse('tinynotation: 3/4 g2. e2. c2. e2. c4 d4 e4 g4 f4 e4 d2.~ d2. '
                             'e2 e4 e4 f4 g4 a2 a4 a4 g4 f4 e2 f4 d2 e4 c2.~ c2.').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        G half ⠗
        Dot ⠄
        ===
        Measure 2, Note Grouping 1:
        E half ⠏
        Dot ⠄
        ===
        Measure 3, Note Grouping 1:
        C half ⠝
        Dot ⠄
        ===
        Measure 4, Note Grouping 1:
        E half ⠏
        Dot ⠄
        ===
        Measure 5, Note Grouping 1:
        C quarter ⠹
        D quarter ⠱
        E quarter ⠫
        ===
        Measure 6, Note Grouping 1:
        G quarter ⠳
        F quarter ⠻
        E quarter ⠫
        ===
        Measure 7, Note Grouping 1:
        D half ⠕
        Dot ⠄
        Tie ⠈⠉
        ===
        Measure 8, Note Grouping 1:
        D half ⠕
        Dot ⠄
        ===
        Measure 9, Note Grouping 1:
        E half ⠏
        E quarter ⠫
        ===
        Measure 10, Note Grouping 1:
        E quarter ⠫
        F quarter ⠻
        G quarter ⠳
        ===
        Measure 11, Note Grouping 1:
        A half ⠎
        A quarter ⠪
        ===
        Measure 12, Note Grouping 1:
        A quarter ⠪
        G quarter ⠳
        F quarter ⠻
        ===
        Measure 13, Note Grouping 1:
        E half ⠏
        F quarter ⠻
        ===
        Measure 14, Note Grouping 1:
        D half ⠕
        E quarter ⠫
        ===
        Measure 15, Note Grouping 1:
        C half ⠝
        Dot ⠄
        Tie ⠈⠉
        ===
        Measure 16, Note Grouping 1:
        C half ⠝
        Dot ⠄
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        C whole ⠽
        ===
        Measure 2, Note Grouping 1:
        A whole ⠮
        ===
        Measure 3, Note Grouping 1:
        F whole ⠿
        ===
        Measure 4, Note Grouping 1:
        A whole ⠮
        ===
        Measure 5, Note Grouping 1:
        C whole ⠽
        ===
        Measure 6, Note Grouping 1:
        D whole ⠵
        ===
        Measure 7, Note Grouping 1:
        C whole ⠽
        Tie ⠈⠉
        ===
        Measure 8, Note Grouping 1:
        C whole ⠽
        ===
        Measure 9, Note Grouping 1:
        D whole ⠵
        ===
        Measure 10, Note Grouping 1:
        E whole ⠯
        ===
        Measure 11, Note Grouping 1:
        F whole ⠿
        ===
        Measure 12, Note Grouping 1:
        D whole ⠵
        ===
        Measure 13, Note Grouping 1:
        C whole ⠽
        ===
        Measure 14, Note Grouping 1:
        G whole ⠷
        ===
        Measure 15, Note Grouping 1:
        F whole ⠿
        Tie ⠈⠉
        ===
        Measure 16, Note Grouping 1:
        F whole ⠿
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.BassClef>
        C whole ⠽
        ===
        Measure 2, Note Grouping 1:
        E whole ⠯
        ===
        Measure 3, Note Grouping 1:
        G whole ⠷
        ===
        Measure 4, Note Grouping 1:
        A whole ⠮
        ===
        Measure 5, Note Grouping 1:
        B whole ⠾
        ===
        Measure 6, Note Grouping 1:
        A whole ⠮
        ===
        Measure 7, Note Grouping 1:
        G whole ⠷
        Tie ⠈⠉
        ===
        Measure 8, Note Grouping 1:
        G whole ⠷
        ===
        Measure 9, Note Grouping 1:
        A whole ⠮
        ===
        Measure 10, Note Grouping 1:
        C whole ⠽
        ===
        Measure 11, Note Grouping 1:
        A whole ⠮
        ===
        Measure 12, Note Grouping 1:
        F whole ⠿
        ===
        Measure 13, Note Grouping 1:
        G whole ⠷
        ===
        Measure 14, Note Grouping 1:
        B whole ⠾
        ===
        Measure 15, Note Grouping 1:
        G whole ⠷
        ===
        Measure 16, Note Grouping 1:
        E whole ⠯
        ===
        Measure 17, Note Grouping 1:
        F whole ⠿
        ===
        Measure 18, Note Grouping 1:
        A whole ⠮
        ===
        Measure 19, Note Grouping 1:
        F whole ⠿
        ===
        Measure 20, Note Grouping 1:
        D whole ⠵
        ===
        Measure 21, Note Grouping 1:
        B whole ⠾
        ===
        Measure 22, Note Grouping 1:
        D whole ⠵
        ===
        Measure 23, Note Grouping 1:
        C whole ⠽
        Tie ⠈⠉
        ===
        Measure 24, Note Grouping 1:
        C whole ⠽
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 3/2 ⠼⠉⠆
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Rest whole ⠍
        G half ⠗
        ===
        Measure 2, Note Grouping 1:
        G half ⠗
        G half ⠗
        G half ⠗
        ===
        Measure 3, Note Grouping 1:
        G quarter ⠳
        G quarter ⠳
        Rest whole ⠍
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠏⠟⠀⠷⠀⠏⠕⠀⠽⠀⠕⠏⠀⠟⠏⠀⠵⠀⠍⠀⠝⠕⠀⠯⠀⠟⠗⠀⠮⠀⠗⠟⠀⠏⠕⠀⠽
        ⠀⠀⠍⠣⠅
        '''

    def test_example05_5(self):
        self.methodArgs = {'suppressOctaveMarks': True}
        bm = converter.parse('tinynotation: 3/4 F2. r2. A2. r2. F4 G4 A4 c4 A4 F4 G4 r2 r2. '
                             'E2. r2. G2. r2. C4 D4 E4 G4 E4 C4 F4 r2 r2.').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
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
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠟⠄⠀⠍⠀⠎⠄⠀⠍⠀⠻⠳⠪⠀⠹⠪⠻⠀⠳⠥⠀⠍⠀⠏⠄⠀⠍⠀⠗⠄⠀⠍⠀⠹⠱⠫
        ⠀⠀⠳⠫⠹⠀⠻⠥⠀⠍⠣⠅
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 6/2 ⠼⠋⠆
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        A whole ⠮
        C whole ⠽
        B whole ⠾
        ===
        Measure 2, Note Grouping 1:
        C half ⠝
        B half ⠞
        A whole ⠮
        B half ⠞
        C half ⠝
        ===
        Measure 3, Note Grouping 1:
        B whole ⠾
        Rest breve ⠍⠘⠉⠍
        ===
        Measure 4, Note Grouping 1:
        G whole ⠷
        B whole ⠾
        A half ⠎
        G half ⠗
        ===
        Measure 5, Note Grouping 1:
        A breve ⠮⠘⠉⠮
        Rest whole ⠍
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Accidental sharp ⠩
        G quarter ⠳
        Accidental double-sharp ⠩⠩
        F quarter ⠻
        G half ⠗
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        C half ⠝
        Accidental flat ⠣
        B half ⠞
        Tie ⠈⠉
        ===
        ---end segment---
        '''
        self.b = '⠼⠙⠲⠀⠝⠣⠞⠈⠉'
        self.s = m[1]
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 2, Note Grouping 1:
        B quarter ⠺
        C quarter ⠹
        A quarter ⠪
        F quarter ⠻
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Accidental natural ⠡
        E quarter ⠫
        E eighth ⠋
        A eighth ⠊
        C eighth ⠙
        Accidental natural ⠡
        E eighth ⠋
        ===
        ---end segment---
        '''
        self.b = '''
        ⠼⠉⠲⠀⠡⠫⠋⠊⠙⠡⠋
        '''
        self.s = m[1]
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 2, Note Grouping 1:
        F half ⠟
        Dot ⠄
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        C eighth ⠙
        Accidental flat ⠣
        B eighth ⠚
        A eighth ⠊
        G eighth ⠓
        F quarter ⠻
        ===
        ---end segment---
        '''
        self.b = '''
        ⠼⠉⠲⠀⠙⠣⠚⠊⠓⠻
        '''
        self.s = m[1]
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 2, Note Grouping 1:
        G eighth ⠓
        Accidental natural ⠡
        B eighth ⠚
        C quarter ⠹
        D quarter ⠱
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        C quarter ⠹
        Accidental sharp ⠩
        C quarter ⠹
        D quarter ⠱
        Accidental sharp ⠩
        D quarter ⠱
        ===
        Measure 2, Note Grouping 1:
        E quarter ⠫
        F quarter ⠻
        Accidental sharp ⠩
        F quarter ⠻
        G quarter ⠳
        ===
        Measure 3, Note Grouping 1:
        Accidental sharp ⠩
        G quarter ⠳
        A quarter ⠪
        Accidental flat ⠣
        B quarter ⠺
        Accidental natural ⠡
        B quarter ⠺
        ===
        Measure 4, Note Grouping 1:
        C half ⠝
        Rest half ⠥
        ===
        Measure 5, Note Grouping 1:
        E half ⠏
        Accidental flat ⠣
        E quarter ⠫
        D quarter ⠱
        ===
        Measure 6, Note Grouping 1:
        C quarter ⠹
        D quarter ⠱
        Accidental natural ⠡
        E quarter ⠫
        C quarter ⠹
        ===
        Measure 7, Note Grouping 1:
        B quarter ⠺
        Accidental flat ⠣
        B quarter ⠺
        A quarter ⠪
        Accidental natural ⠡
        B quarter ⠺
        ===
        Measure 8, Note Grouping 1:
        C half ⠝
        Rest half ⠥
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        G quarter ⠳
        Accidental sharp ⠩
        F quarter ⠻
        Accidental natural ⠡
        F quarter ⠻
        E quarter ⠫
        ===
        Measure 2, Note Grouping 1:
        Accidental flat ⠣
        E quarter ⠫
        D quarter ⠱
        Accidental flat ⠣
        D quarter ⠱
        C quarter ⠹
        ===
        Measure 3, Note Grouping 1:
        B quarter ⠺
        Accidental flat ⠣
        B quarter ⠺
        A quarter ⠪
        Accidental flat ⠣
        A quarter ⠪
        ===
        Measure 4, Note Grouping 1:
        G quarter ⠳
        Accidental sharp ⠩
        F quarter ⠻
        Accidental natural ⠡
        F quarter ⠻
        E quarter ⠫
        ===
        Measure 5, Note Grouping 1:
        Accidental flat ⠣
        E quarter ⠫
        D quarter ⠱
        Accidental flat ⠣
        D quarter ⠱
        C quarter ⠹
        ===
        Measure 6, Note Grouping 1:
        B quarter ⠺
        C quarter ⠹
        D quarter ⠱
        E quarter ⠫
        ===
        Measure 7, Note Grouping 1:
        C half ⠝
        Rest half ⠥
        ===
        Measure 8, Note Grouping 1:
        C whole ⠽
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        C quarter ⠹
        C eighth ⠙
        Accidental flat ⠣
        B eighth ⠚
        Accidental flat ⠣
        A eighth ⠊
        C eighth ⠙
        F eighth ⠛
        Accidental flat ⠣
        A eighth ⠊
        Tie ⠈⠉
        ===
        Measure 2, Note Grouping 1:
        A eighth ⠊
        G eighth ⠓
        F eighth ⠛
        G eighth ⠓
        C half ⠝
        ===
        Measure 3, Note Grouping 1:
        Accidental flat ⠣
        D quarter ⠱
        F eighth ⠛
        D eighth ⠑
        C eighth ⠙
        C eighth ⠙
        Accidental flat ⠣
        A eighth ⠊
        F eighth ⠛
        ===
        Measure 4, Note Grouping 1:
        G eighth ⠓
        G eighth ⠓
        C eighth ⠙
        C eighth ⠙
        F half ⠟
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.BassClef>
        E quarter ⠫
        G half ⠗
        E quarter ⠫
        ===
        Measure 2, Note Grouping 1:
        Accidental sharp ⠩
        F quarter ⠻
        A half ⠎
        F quarter ⠻
        ===
        Measure 3, Note Grouping 1:
        G eighth ⠓
        A eighth ⠊
        B quarter ⠺
        G quarter ⠳
        E quarter ⠫
        ===
        Measure 4, Note Grouping 1:
        Accidental sharp ⠩
        D eighth ⠑
        E eighth ⠋
        Accidental sharp ⠩
        F quarter ⠻
        D quarter ⠱
        G quarter ⠳
        ===
        Measure 5, Note Grouping 1:
        C quarter ⠹
        E half ⠏
        Accidental sharp ⠩
        F quarter ⠻
        ===
        Measure 6, Note Grouping 1:
        G quarter ⠳
        B half ⠞
        C quarter ⠹
        ===
        Measure 7, Note Grouping 1:
        B eighth ⠚
        A eighth ⠊
        G eighth ⠓
        B eighth ⠚
        A eighth ⠊
        G eighth ⠓
        Accidental sharp ⠩
        F eighth ⠛
        Accidental sharp ⠩
        D eighth ⠑
        ===
        Measure 8, Note Grouping 1:
        E whole ⠯
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        A quarter ⠪
        A half ⠎
        A quarter ⠪
        Tie ⠈⠉
        ===
        Measure 2, Note Grouping 1:
        A quarter ⠪
        Rest quarter ⠧
        Accidental flat ⠣
        B half ⠞
        ===
        Measure 3, Note Grouping 1:
        C quarter ⠹
        C quarter ⠹
        Rest quarter ⠧
        C quarter ⠹
        Tie ⠈⠉
        ===
        Measure 4, Note Grouping 1:
        C quarter ⠹
        Rest quarter ⠧
        D half ⠕
        ===
        Measure 5, Note Grouping 1:
        E eighth ⠋
        E quarter ⠫
        E eighth ⠋
        F quarter ⠻
        Rest quarter ⠧
        ===
        Measure 6, Note Grouping 1:
        E eighth ⠋
        E quarter ⠫
        E eighth ⠋
        D quarter ⠱
        Rest quarter ⠧
        ===
        Measure 7, Note Grouping 1:
        C eighth ⠙
        C quarter ⠹
        C eighth ⠙
        Accidental flat ⠣
        B eighth ⠚
        B quarter ⠺
        B eighth ⠚
        ===
        Measure 8, Note Grouping 1:
        A half ⠎
        Dot ⠄
        Rest quarter ⠧
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        A quarter ⠪
        Dot ⠄
        B eighth ⠚
        C quarter ⠹
        B quarter ⠺
        ===
        Measure 2, Note Grouping 1:
        A eighth ⠊
        C eighth ⠙
        E eighth ⠋
        C eighth ⠙
        A eighth ⠊
        C eighth ⠙
        E quarter ⠫
        ===
        Measure 3, Note Grouping 1:
        D quarter ⠱
        Dot ⠄
        F eighth ⠛
        A quarter ⠪
        F quarter ⠻
        ===
        Measure 4, Note Grouping 1:
        D eighth ⠑
        F eighth ⠛
        A eighth ⠊
        F eighth ⠛
        D eighth ⠑
        F eighth ⠛
        A quarter ⠪
        ===
        Measure 5, Note Grouping 1:
        Accidental sharp ⠩
        G quarter ⠳
        Dot ⠄
        E eighth ⠋
        A half ⠎
        ===
        Measure 6, Note Grouping 1:
        B quarter ⠺
        Dot ⠄
        B eighth ⠚
        C half ⠝
        ===
        Measure 7, Note Grouping 1:
        D eighth ⠑
        C eighth ⠙
        B eighth ⠚
        A eighth ⠊
        Accidental sharp ⠩
        G eighth ⠓
        E eighth ⠋
        Accidental sharp ⠩
        F eighth ⠛
        G eighth ⠓
        ===
        Measure 8, Note Grouping 1:
        A half ⠎
        Tie ⠈⠉
        A eighth ⠊
        Accidental sharp ⠩
        G eighth ⠓
        A quarter ⠪
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        E eighth ⠋
        Accidental flat ⠣
        E eighth ⠋
        D eighth ⠑
        Accidental flat ⠣
        D eighth ⠑
        C eighth ⠙
        A eighth ⠊
        Accidental flat ⠣
        A eighth ⠊
        G eighth ⠓
        ===
        Measure 2, Note Grouping 1:
        Accidental double-flat ⠣⠣
        B eighth ⠚
        Accidental flat ⠣
        A eighth ⠊
        G eighth ⠓
        Accidental flat ⠣
        G eighth ⠓
        F eighth ⠛
        E eighth ⠋
        D eighth ⠑
        C eighth ⠙
        ===
        Measure 3, Note Grouping 1:
        D eighth ⠑
        B eighth ⠚
        Accidental flat ⠣
        B eighth ⠚
        Accidental natural ⠡
        B eighth ⠚
        C eighth ⠙
        D eighth ⠑
        E eighth ⠋
        F eighth ⠛
        ===
        Measure 4, Note Grouping 1:
        G eighth ⠓
        Accidental sharp ⠩
        G eighth ⠓
        A eighth ⠊
        B eighth ⠚
        C quarter ⠹
        Rest quarter ⠧
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 1 ⠈
        C whole ⠽
        ===
        Measure 2, Note Grouping 1:
        Octave 2 ⠘
        C whole ⠽
        ===
        Measure 3, Note Grouping 1:
        Octave 3 ⠸
        C whole ⠽
        ===
        Measure 4, Note Grouping 1:
        Octave 4 ⠐
        C whole ⠽
        ===
        Measure 5, Note Grouping 1:
        Octave 5 ⠨
        C whole ⠽
        ===
        Measure 6, Note Grouping 1:
        Octave 6 ⠰
        C whole ⠽
        ===
        Measure 7, Note Grouping 1:
        Octave 7 ⠠
        C whole ⠽
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 2/1 ⠼⠃⠂
        ===
        Measure 1, Note Grouping 1:
        Octave 0 ⠈⠈
        A whole ⠮
        B whole ⠾
        ===
        Measure 2, Note Grouping 1:
        Octave 8 ⠠⠠
        C whole ⠽
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        C quarter ⠹
        E quarter ⠫
        ===
        ---end segment---
        '''
        self.b = '⠐⠹⠫'

    def test_example07_3b(self):
        self.method = measureToBraille
        bm = converter.parse("tinynotation: c'2. a4").flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[0].pop(1)
        m[-1].rightBarline = None
        self.s = m[0]
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 5 ⠨
        C half ⠝
        Dot ⠄
        A quarter ⠪
        ===
        ---end segment---
        '''
        self.b = '⠨⠝⠄⠪'

    def test_example07_4a(self):
        self.method = measureToBraille
        bm = converter.parse('tinynotation: 4/4 c2 a2').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[0].pop(1)
        m[-1].rightBarline = None
        self.s = m[0]
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        C half ⠝
        Octave 4 ⠐
        A half ⠎
        ===
        ---end segment---
        '''
        self.b = '⠐⠝⠐⠎'

    def test_example07_4b(self):
        self.method = measureToBraille
        bm = converter.parse("tinynotation: 4/4 c'2 e2").flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[0].pop(1)
        m[-1].rightBarline = None
        self.s = m[0]
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 5 ⠨
        C half ⠝
        Octave 4 ⠐
        E half ⠏
        ===
        ---end segment---
        '''
        self.b = '⠨⠝⠐⠏'

    def test_example07_5a(self):
        self.method = measureToBraille
        bm = converter.parse('tinynotation: C2 F2').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[0].pop(1)
        m[-1].rightBarline = None
        self.s = m[0]
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Note Grouping 1:
        <music21.clef.BassClef>
        Octave 3 ⠸
        C half ⠝
        F half ⠟
        ===
        ---end segment---
        '''
        self.b = '⠸⠝⠟'

    def test_example07_5b(self):
        self.method = measureToBraille
        bm = converter.parse("tinynotation: f2 c'2").flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        m = bm.getElementsByClass(stream.Measure)
        m[0].pop(1)
        m[-1].rightBarline = None
        self.s = m[0]
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        F half ⠟
        Octave 5 ⠨
        C half ⠝
        ===
        ---end segment---
        '''
        self.b = '⠐⠟⠨⠝'

    def test_example07_6(self):
        bm = converter.parse('''
            tinynotation: 4/8 e'-8 e'-8 e'-8 e'-8 d'8 d'8 b-4 c'8
            c'8 c'8 c'8 e-8 c'8 b-4
            f8 f8 c'4 b-8 b-8 f'4 e'-8 d'8 c'8 b-8 e'-4 e-4''').flatten()
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
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
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠣⠨⠋⠋⠋⠋⠀⠑⠑⠣⠺⠀⠙⠙⠙⠙⠀⠣⠐⠋⠨⠙⠣⠺⠀⠛⠛⠨⠹⠀⠣⠚⠚⠨⠻
        ⠀⠀⠣⠨⠋⠑⠙⠣⠚⠀⠣⠨⠫⠣⠐⠫⠣⠅
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/8 ⠼⠙⠦
        ===
        Measure 1, Note Grouping 1:
        Octave 4 ⠐
        A eighth ⠊
        C eighth ⠙
        F eighth ⠛
        C eighth ⠙
        ===
        Measure 2, Note Grouping 1:
        Octave 5 ⠨
        A eighth ⠊
        C eighth ⠙
        F eighth ⠛
        C eighth ⠙
        ===
        Measure 3, Note Grouping 1:
        Octave 6 ⠰
        A eighth ⠊
        F eighth ⠛
        C eighth ⠙
        D eighth ⠑
        ===
        Measure 4, Note Grouping 1:
        Octave 5 ⠨
        A eighth ⠊
        F eighth ⠛
        E eighth ⠋
        C eighth ⠙
        ===
        Measure 5, Note Grouping 1:
        F half ⠟
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠐⠊⠙⠛⠙⠀⠨⠊⠙⠛⠙⠀⠰⠊⠛⠙⠑⠀⠨⠊⠛⠋⠙⠀⠟⠣⠅
        '''

    def test_example07_8(self):
        bm = converter.parse('tinynotation: C2 GG4 E4 D4. C8 C4 C4 A2 G4 E4 D4 G2 G4 '
                             'c4. B8 A4 G4 A4 F4 C4 AA4 GG4 GG4 D4 G4 E4 C2.')
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        self.s = bm
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.BassClef>
        Octave 3 ⠸
        C half ⠝
        Octave 2 ⠘
        G quarter ⠳
        Octave 3 ⠸
        E quarter ⠫
        ===
        Measure 2, Note Grouping 1:
        D quarter ⠱
        Dot ⠄
        C eighth ⠙
        C quarter ⠹
        C quarter ⠹
        ===
        Measure 3, Note Grouping 1:
        Octave 3 ⠸
        A half ⠎
        G quarter ⠳
        E quarter ⠫
        ===
        Measure 4, Note Grouping 1:
        D quarter ⠱
        G half ⠗
        G quarter ⠳
        ===
        Measure 5, Note Grouping 1:
        Octave 4 ⠐
        C quarter ⠹
        Dot ⠄
        B eighth ⠚
        A quarter ⠪
        G quarter ⠳
        ===
        Measure 6, Note Grouping 1:
        A quarter ⠪
        F quarter ⠻
        C quarter ⠹
        A quarter ⠪
        ===
        Measure 7, Note Grouping 1:
        Octave 2 ⠘
        G quarter ⠳
        G quarter ⠳
        Octave 3 ⠸
        D quarter ⠱
        G quarter ⠳
        ===
        Measure 8, Note Grouping 1:
        E quarter ⠫
        C half ⠝
        Dot ⠄
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        E quarter ⠫
        Dot ⠄
        A eighth ⠊
        C eighth ⠙
        E eighth ⠋
        ===
        Measure 2, Note Grouping 1:
        D quarter ⠱
        D eighth ⠑
        C eighth ⠙
        B quarter ⠺
        ===
        Measure 3, Note Grouping 1:
        E quarter ⠫
        Dot ⠄
        Accidental sharp ⠩
        G eighth ⠓
        B eighth ⠚
        Octave 5 ⠨
        E eighth ⠋
        ===
        Measure 4, Note Grouping 1:
        C quarter ⠹
        C eighth ⠙
        B eighth ⠚
        A quarter ⠪
        ===
        Measure 5, Note Grouping 1:
        A eighth ⠊
        Accidental sharp ⠩
        C eighth ⠙
        E eighth ⠋
        A eighth ⠊
        Octave 5 ⠨
        C eighth ⠙
        G eighth ⠓
        ===
        Measure 6, Note Grouping 1:
        Octave 5 ⠨
        F eighth ⠛
        D eighth ⠑
        Octave 4 ⠐
        A eighth ⠊
        Octave 5 ⠨
        E eighth ⠋
        D eighth ⠑
        Octave 4 ⠐
        F eighth ⠛
        ===
        Measure 7, Note Grouping 1:
        Octave 5 ⠨
        C eighth ⠙
        B eighth ⠚
        Octave 4 ⠐
        D eighth ⠑
        A eighth ⠊
        Accidental sharp ⠩
        G eighth ⠓
        E eighth ⠋
        ===
        Measure 8, Note Grouping 1:
        A half ⠎
        Dot ⠄
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        A quarter ⠪
        Octave 5 ⠨
        E quarter ⠫
        A quarter ⠪
        E quarter ⠫
        ===
        Measure 2, Note Grouping 1:
        Accidental sharp ⠩
        C eighth ⠙
        Accidental sharp ⠩
        F eighth ⠛
        E eighth ⠋
        Octave 4 ⠐
        A eighth ⠊
        B quarter ⠺
        Octave 5 ⠨
        E quarter ⠫
        ===
        Measure 3, Note Grouping 1:
        D eighth ⠑
        Octave 4 ⠐
        A eighth ⠊
        Accidental sharp ⠩
        F eighth ⠛
        Octave 5 ⠨
        D eighth ⠑
        Accidental sharp ⠩
        C eighth ⠙
        A eighth ⠊
        E eighth ⠋
        Octave 5 ⠨
        C eighth ⠙
        ===
        Measure 4, Note Grouping 1:
        Octave 4 ⠐
        B eighth ⠚
        Accidental sharp ⠩
        F eighth ⠛
        Accidental sharp ⠩
        G eighth ⠓
        A eighth ⠊
        B quarter ⠺
        E quarter ⠫
        ===
        Measure 5, Note Grouping 1:
        A quarter ⠪
        A quarter ⠪
        Accidental sharp ⠩
        Octave 5 ⠨
        F quarter ⠻
        E quarter ⠫
        ===
        Measure 6, Note Grouping 1:
        D quarter ⠱
        D quarter ⠱
        Octave 5 ⠨
        B quarter ⠺
        A quarter ⠪
        ===
        Measure 7, Note Grouping 1:
        A eighth ⠊
        Accidental sharp ⠩
        Octave 5 ⠨
        C eighth ⠙
        Accidental sharp ⠩
        G eighth ⠓
        Accidental sharp ⠩
        F eighth ⠛
        E eighth ⠋
        Octave 4 ⠐
        E eighth ⠋
        Octave 5 ⠨
        C eighth ⠙
        B eighth ⠚
        ===
        Measure 8, Note Grouping 1:
        Octave 4 ⠐
        A half ⠎
        Rest half ⠥
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 0, Signature Grouping 1:
        Time Signature 6/8 ⠼⠋⠦
        ===
        Measure 0, Note Grouping 1:
        <music21.clef.BassClef>
        Octave 2 ⠘
        G eighth ⠓
        ===
        Measure 1, Note Grouping 1:
        Octave 3 ⠸
        C quarter ⠹
        Octave 2 ⠘
        G eighth ⠓
        Octave 3 ⠸
        C quarter ⠹
        Accidental flat ⠣
        E eighth ⠋
        ===
        Measure 2, Note Grouping 1:
        D quarter ⠱
        Octave 2 ⠘
        G eighth ⠓
        Octave 3 ⠸
        D quarter ⠱
        G eighth ⠓
        ===
        Measure 3, Note Grouping 1:
        C quarter ⠹
        G eighth ⠓
        Octave 4 ⠐
        C quarter ⠹
        Accidental flat ⠣
        B eighth ⠚
        ===
        Measure 4, Note Grouping 1:
        Accidental flat ⠣
        A quarter ⠪
        F eighth ⠛
        C quarter ⠹
        Octave 3 ⠸
        A eighth ⠊
        ===
        Measure 5, Note Grouping 1:
        Octave 3 ⠸
        G eighth ⠓
        Accidental flat ⠣
        E eighth ⠋
        Accidental flat ⠣
        A eighth ⠊
        G eighth ⠓
        C eighth ⠙
        F eighth ⠛
        ===
        Measure 6, Note Grouping 1:
        Accidental flat ⠣
        E eighth ⠋
        Octave 2 ⠘
        G eighth ⠓
        Octave 3 ⠸
        D eighth ⠑
        C eighth ⠙
        Octave 2 ⠘
        G eighth ⠓
        Accidental flat ⠣
        E eighth ⠋
        ===
        Measure 7, Note Grouping 1:
        F eighth ⠛
        Octave 3 ⠸
        D eighth ⠑
        C eighth ⠙
        Accidental natural ⠡
        B eighth ⠚
        G eighth ⠓
        G eighth ⠓
        ===
        Measure 8, Note Grouping 1:
        C quarter ⠹
        Dot ⠄
        Rest quarter ⠧
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature common ⠨⠉
        ===
        Measure 1, Tempo Text Grouping 1:
        Tempo Text Andante maestoso ⠠⠁⠝⠙⠁⠝⠞⠑⠀⠍⠁⠑⠎⠞⠕⠎⠕⠲
        ===
        Measure 1, Metronome Mark Grouping 1:
        Metronome Note C quarter ⠹
        Metronome symbol ⠶
        Metronome number 92 ⠼⠊⠃
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        A half ⠎
        G eighth ⠓
        F eighth ⠛
        E quarter ⠫
        ===
        Measure 2, Note Grouping 1:
        D quarter ⠱
        E quarter ⠫
        F eighth ⠛
        G eighth ⠓
        A quarter ⠪
        ===
        Measure 3, Note Grouping 1:
        G quarter ⠳
        Octave 5 ⠨
        C eighth ⠙
        B eighth ⠚
        A quarter ⠪
        G quarter ⠳
        ===
        Measure 4, Note Grouping 1:
        F quarter ⠻
        Dot ⠄
        E eighth ⠋
        D half ⠕
        ===
        Measure 5, Note Grouping 1:
        C quarter ⠹
        E quarter ⠫
        A quarter ⠪
        Octave 5 ⠨
        E quarter ⠫
        ===
        Measure 6, Note Grouping 1:
        E quarter ⠫
        D quarter ⠱
        C eighth ⠙
        B eighth ⠚
        A quarter ⠪
        ===
        Measure 7, Note Grouping 1:
        Octave 5 ⠨
        A quarter ⠪
        G eighth ⠓
        F eighth ⠛
        E quarter ⠫
        D quarter ⠱
        ===
        Measure 8, Note Grouping 1:
        C quarter ⠹
        A eighth ⠊
        B eighth ⠚
        C half ⠝
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 3 flat(s) ⠣⠣⠣
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Tempo Text Grouping 1:
        Tempo Text In strict time ⠠⠊⠝⠀⠎⠞⠗⠊⠉⠞⠀⠞⠊⠍⠑⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.BassClef>
        Octave 3 ⠸
        E eighth ⠋
        Rest eighth ⠭
        Octave 2 ⠘
        B eighth ⠚
        Rest eighth ⠭
        Octave 3 ⠸
        E eighth ⠋
        Rest eighth ⠭
        ===
        Measure 2, Note Grouping 1:
        Accidental natural ⠡
        E quarter ⠫
        F quarter ⠻
        Accidental sharp ⠩
        F quarter ⠻
        ===
        Measure 3, Note Grouping 1:
        G eighth ⠓
        Rest eighth ⠭
        D eighth ⠑
        Rest eighth ⠭
        G eighth ⠓
        Rest eighth ⠭
        ===
        Measure 4, Note Grouping 1:
        A quarter ⠪
        G quarter ⠳
        F quarter ⠻
        ===
        Measure 5, Note Grouping 1:
        E eighth ⠋
        Rest eighth ⠭
        C eighth ⠙
        Rest eighth ⠭
        A eighth ⠊
        Rest eighth ⠭
        ===
        Measure 6, Note Grouping 1:
        Accidental natural ⠡
        Octave 2 ⠘
        A quarter ⠪
        B quarter ⠺
        Accidental natural ⠡
        B quarter ⠺
        ===
        Measure 7, Note Grouping 1:
        C eighth ⠙
        D eighth ⠑
        Rest eighth ⠭
        E eighth ⠋
        Rest eighth ⠭
        Octave 2 ⠘
        B eighth ⠚
        ===
        Measure 8, Note Grouping 1:
        Octave 3 ⠸
        E eighth ⠋
        Accidental natural ⠡
        E eighth ⠋
        Rest eighth ⠭
        F eighth ⠛
        Rest eighth ⠭
        Accidental sharp ⠩
        F eighth ⠛
        ===
        Measure 9, Note Grouping 1:
        G eighth ⠓
        D eighth ⠑
        Rest eighth ⠭
        G eighth ⠓
        Rest eighth ⠭
        A eighth ⠊
        ===
        Measure 10, Note Grouping 1:
        A eighth ⠊
        G eighth ⠓
        Rest eighth ⠭
        F eighth ⠛
        Rest eighth ⠭
        E eighth ⠋
        ===
        Measure 11, Note Grouping 1:
        Octave 3 ⠸
        D eighth ⠑
        C eighth ⠙
        B quarter ⠺
        Octave 1 ⠈
        B quarter ⠺
        ===
        Measure 12, Note Grouping 1:
        Octave 2 ⠘
        E half ⠏
        Dot ⠄
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 0, Signature Grouping 1:
        Key Signature 5 sharp(s) ⠼⠑⠩
        Time Signature 6/8 ⠼⠋⠦
        ===
        Measure 0, Tempo Text Grouping 1:
        Tempo Text Con delicatezza ⠠⠉⠕⠝⠀⠙⠑⠇⠊⠉⠁⠞⠑⠵⠵⠁⠲
        ===
        Measure 0, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 5 ⠨
        D eighth ⠑
        C eighth ⠙
        ===
        Measure 1, Note Grouping 1:
        B quarter ⠺
        Dot ⠄
        Tie ⠈⠉
        B eighth ⠚
        D eighth ⠑
        G eighth ⠓
        ===
        Measure 2, Note Grouping 1:
        G quarter ⠳
        Dot ⠄
        F quarter ⠻
        Rest eighth ⠭
        ===
        Measure 3, Note Grouping 1:
        E quarter ⠫
        Dot ⠄
        Tie ⠈⠉
        E eighth ⠋
        D eighth ⠑
        Octave 4 ⠐
        G eighth ⠓
        ===
        Measure 4, Note Grouping 1:
        Octave 5 ⠨
        D quarter ⠱
        C eighth ⠙
        D quarter ⠱
        Rest eighth ⠭
        ===
        Measure 5, Note Grouping 1:
        Octave 4 ⠐
        A eighth ⠊
        G eighth ⠓
        A eighth ⠊
        B eighth ⠚
        A eighth ⠊
        B eighth ⠚
        ===
        Measure 6, Note Grouping 1:
        C eighth ⠙
        D eighth ⠑
        E eighth ⠋
        F eighth ⠛
        G eighth ⠓
        A eighth ⠊
        ===
        Measure 7, Note Grouping 1:
        B eighth ⠚
        F eighth ⠛
        D eighth ⠑
        G eighth ⠓
        E eighth ⠋
        Octave 4 ⠐
        B eighth ⠚
        ===
        Measure 8, Note Grouping 1:
        Octave 5 ⠨
        F quarter ⠻
        D eighth ⠑
        E eighth ⠋
        D eighth ⠑
        C eighth ⠙
        ===
        Measure 9, Note Grouping 1:
        B eighth ⠚
        F eighth ⠛
        Octave 5 ⠨
        D eighth ⠑
        B quarter ⠺
        F eighth ⠛
        ===
        Measure 10, Note Grouping 1:
        Octave 4 ⠐
        D eighth ⠑
        F eighth ⠛
        B eighth ⠚
        C quarter ⠹
        A eighth ⠊
        ===
        Measure 11, Note Grouping 1:
        B half ⠞
        Dot ⠄
        Tie ⠈⠉
        ===
        Measure 12, Note Grouping 1:
        B quarter ⠺
        Dot ⠄
        Rest eighth ⠭
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 1 flat(s) ⠣
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Tempo Text Grouping 1:
        Tempo Text Grazioso ⠠⠛⠗⠁⠵⠊⠕⠎⠕⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.BassClef>
        Octave 3 ⠸
        A half ⠎
        Dot ⠄
        Dot ⠄
        G eighth ⠓
        ===
        Measure 2, Note Grouping 1:
        F half ⠟
        E quarter ⠫
        D quarter ⠱
        ===
        Measure 3, Note Grouping 1:
        E quarter ⠫
        Dot ⠄
        F eighth ⠛
        G quarter ⠳
        E quarter ⠫
        ===
        Measure 4, Note Grouping 1:
        Accidental sharp ⠩
        C half ⠝
        D quarter ⠱
        Rest quarter ⠧
        ===
        Measure 5, Note Grouping 1:
        Octave 2 ⠘
        A half ⠎
        Dot ⠄
        Dot ⠄
        Accidental natural ⠡
        B eighth ⠚
        ===
        Measure 6, Note Grouping 1:
        Accidental sharp ⠩
        C quarter ⠹
        Dot ⠄
        D eighth ⠑
        E quarter ⠫
        G quarter ⠳
        ===
        Measure 7, Note Grouping 1:
        Octave 3 ⠸
        F quarter ⠻
        G quarter ⠳
        A quarter ⠪
        F quarter ⠻
        ===
        Measure 8, Note Grouping 1:
        D half ⠕
        Dot ⠄
        Dot ⠄
        Rest eighth ⠭
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 0, Signature Grouping 1:
        Key Signature 2 flat(s) ⠣⠣
        Time Signature cut ⠸⠉
        ===
        Measure 0, Tempo Text Grouping 1:
        Tempo Text Ben marcato ⠠⠃⠑⠝⠀⠍⠁⠗⠉⠁⠞⠕⠲
        ===
        Measure 0, Metronome Mark Grouping 1:
        Metronome Note C half ⠝
        Metronome symbol ⠶
        Metronome number 112 ⠼⠁⠁⠃
        ===
        Measure 0, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 5 ⠨
        F quarter ⠻
        E quarter ⠫
        ===
        Measure 1, Note Grouping 1:
        D half ⠕
        B quarter ⠺
        G quarter ⠳
        ===
        Measure 2, Note Grouping 1:
        Octave 5 ⠨
        E half ⠏
        C quarter ⠹
        Octave 4 ⠐
        F quarter ⠻
        ===
        Measure 3, Note Grouping 1:
        Octave 5 ⠨
        F half ⠟
        E quarter ⠫
        D quarter ⠱
        ===
        Measure 4, Note Grouping 1:
        C half ⠝
        Octave 4 ⠐
        F quarter ⠻
        F quarter ⠻
        ===
        Measure 5, Note Grouping 1:
        G half ⠗
        F quarter ⠻
        G quarter ⠳
        ===
        Measure 6, Note Grouping 1:
        A half ⠎
        Octave 5 ⠨
        D quarter ⠱
        C quarter ⠹
        ===
        Measure 7, Note Grouping 1:
        B quarter ⠺
        A quarter ⠪
        B quarter ⠺
        C quarter ⠹
        ===
        Measure 8, Note Grouping 1:
        Octave 5 ⠨
        D half ⠕
        E quarter ⠫
        F quarter ⠻
        ===
        Measure 9, Note Grouping 1:
        G half ⠗
        E quarter ⠫
        C quarter ⠹
        ===
        Measure 10, Note Grouping 1:
        F half ⠟
        D quarter ⠱
        B quarter ⠺
        ===
        Measure 11, Note Grouping 1:
        Octave 5 ⠨
        E half ⠏
        C quarter ⠹
        Octave 4 ⠐
        F quarter ⠻
        ===
        Measure 12, Note Grouping 1:
        Octave 5 ⠨
        D half ⠕
        B quarter ⠺
        B quarter ⠺
        ===
        Measure 13, Note Grouping 1:
        C half ⠝
        B quarter ⠺
        C quarter ⠹
        ===
        Measure 14, Note Grouping 1:
        D quarter ⠱
        B quarter ⠺
        C quarter ⠹
        D quarter ⠱
        ===
        Measure 15, Note Grouping 1:
        B quarter ⠺
        C quarter ⠹
        B quarter ⠺
        A quarter ⠪
        ===
        Measure 16, Note Grouping 1:
        Octave 4 ⠐
        B half ⠞
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.b = '''
        ⠀⠀⠀⠀⠣⠼⠃⠲⠀⠀⠀
        ⠐⠪⠂⠳⠇⠀⠻⠄⠃⠙⠁
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 2 flat(s) ⠣⠣
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 5 ⠨
        F quarter ⠻
        E eighth ⠋
        D eighth ⠑
        C eighth ⠙
        B eighth ⠚
        Tie ⠈⠉
        ===
        Measure 2, Note Grouping 1:
        B quarter ⠺
        Rest eighth ⠭
        A eighth ⠊
        C eighth ⠙
        B eighth ⠚
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 6/8 ⠼⠋⠦
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        C half ⠝
        Dot ⠄
        Tie ⠈⠉
        ===
        Measure 2, Note Grouping 1:
        C quarter ⠹
        Dot ⠄
        F quarter ⠻
        G eighth ⠓
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 2 sharp(s) ⠩⠩
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.BassClef>
        Octave 4 ⠐
        D half ⠕
        Octave 3 ⠸
        F quarter ⠻
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        C half ⠝
        G quarter ⠳
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 2/4 ⠼⠃⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        C eighth ⠙
        E eighth ⠋
        G eighth ⠓
        Octave 5 ⠨
        C eighth ⠙
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 6/8 ⠼⠋⠦
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        D eighth ⠑
        C eighth ⠙
        D eighth ⠑
        E quarter ⠫
        Dot ⠄
        ===
        ---end segment---
        '''
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
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠩⠩⠼⠃⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠐⠻⠃⠁⠪⠁⠃⠀⠨⠱⠠⠂⠻⠂⠅⠀⠻⠂⠇⠫⠇⠃
        '''
        self.methodArgs = {'showFirstMeasureNumber': False,
                           'upperFirstInNoteFingering': False}
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 0, Signature Grouping 1:
        Key Signature 3 flat(s) ⠣⠣⠣
        Time Signature 6/8 ⠼⠋⠦
        ===
        Measure 0, Tempo Text Grouping 1:
        Tempo Text Allegretto ⠠⠁⠇⠇⠑⠛⠗⠑⠞⠞⠕⠲
        ===
        Measure 0, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        G eighth ⠓
        A eighth ⠊
        ===
        Measure 1, Note Grouping 1:
        B quarter ⠺
        Dot ⠄
        Tie ⠈⠉
        B eighth ⠚
        G eighth ⠓
        B eighth ⠚
        ===
        Measure 2, Note Grouping 1:
        D quarter ⠱
        Dot ⠄
        Tie ⠈⠉
        D eighth ⠑
        C eighth ⠙
        B eighth ⠚
        ===
        Measure 3, Note Grouping 1:
        A quarter ⠪
        G eighth ⠓
        E quarter ⠫
        F eighth ⠛
        ===
        Measure 4, Note Grouping 1:
        G quarter ⠳
        Dot ⠄
        Rest eighth ⠭
        A eighth ⠊
        B eighth ⠚
        ===
        Measure 5, Note Grouping 1:
        Octave 5 ⠨
        C quarter ⠹
        Dot ⠄
        Tie ⠈⠉
        C eighth ⠙
        A eighth ⠊
        C eighth ⠙
        ===
        Measure 6, Note Grouping 1:
        E quarter ⠫
        Dot ⠄
        Tie ⠈⠉
        E eighth ⠋
        D eighth ⠑
        F eighth ⠛
        ===
        Measure 7, Note Grouping 1:
        E eighth ⠋
        D eighth ⠑
        C eighth ⠙
        B eighth ⠚
        A eighth ⠊
        F eighth ⠛
        ===
        Measure 8, Note Grouping 1:
        Octave 4 ⠐
        E quarter ⠫
        Dot ⠄
        Tie ⠈⠉
        E eighth ⠋
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature common ⠨⠉
        ===
        Measure 1, Tempo Text Grouping 1:
        Tempo Text Adagio e molto legato ⠠⠁⠙⠁⠛⠊⠕⠀⠑⠀⠍⠕⠇⠞⠕⠀⠇⠑⠛⠁⠞⠕⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        A half ⠎
        Tie ⠈⠉
        A eighth ⠊
        G eighth ⠓
        A eighth ⠊
        Octave 5 ⠨
        D eighth ⠑
        ===
        Measure 2, Note Grouping 1:
        C eighth ⠙
        B eighth ⠚
        Octave 5 ⠨
        E eighth ⠋
        D eighth ⠑
        C eighth ⠙
        F eighth ⠛
        E quarter ⠫
        Tie ⠈⠉
        ===
        Measure 3, Note Grouping 1:
        Octave 5 ⠨
        E eighth ⠋
        F eighth ⠛
        E eighth ⠋
        Octave 4 ⠐
        B eighth ⠚
        C eighth ⠙
        D eighth ⠑
        Octave 4 ⠐
        A eighth ⠊
        B eighth ⠚
        ===
        Measure 4, Note Grouping 1:
        C eighth ⠙
        Octave 4 ⠐
        G eighth ⠓
        A half ⠎
        Tie ⠈⠉
        A eighth ⠊
        F eighth ⠛
        ===
        Measure 5, Note Grouping 1:
        Octave 4 ⠐
        G eighth ⠓
        Octave 5 ⠨
        C eighth ⠙
        B eighth ⠚
        A eighth ⠊
        Octave 5 ⠨
        D eighth ⠑
        C eighth ⠙
        B eighth ⠚
        Octave 5 ⠨
        E eighth ⠋
        ===
        Measure 6, Note Grouping 1:
        D half ⠕
        Tie ⠈⠉
        D eighth ⠑
        G eighth ⠓
        F eighth ⠛
        C eighth ⠙
        ===
        Measure 7, Note Grouping 1:
        Octave 5 ⠨
        D eighth ⠑
        E eighth ⠋
        Octave 4 ⠐
        B eighth ⠚
        C eighth ⠙
        D quarter ⠱
        Octave 4 ⠐
        A eighth ⠊
        G eighth ⠓
        ===
        Measure 8, Note Grouping 1:
        A half ⠎
        Dot ⠄
        Tie ⠈⠉
        A eighth ⠊
        Rest eighth ⠭
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 2 sharp(s) ⠩⠩
        Time Signature 2/4 ⠼⠃⠲
        ===
        Measure 1, Tempo Text Grouping 1:
        Tempo Text Moderato ⠠⠍⠕⠙⠑⠗⠁⠞⠕⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.BassClef>
        Octave 2 ⠘
        B quarter ⠺
        C eighth ⠙
        D eighth ⠑
        ===
        Measure 2, Note Grouping 1:
        E eighth ⠋
        F eighth ⠛
        G eighth ⠓
        A eighth ⠊
        ===
        Measure 3, Note Grouping 1:
        <music21.clef.TrebleClef>
        B quarter ⠺
        C eighth ⠙
        D eighth ⠑
        ===
        Measure 4, Note Grouping 1:
        Octave 4 ⠐
        E eighth ⠋
        F eighth ⠛
        G eighth ⠓
        F eighth ⠛
        ===
        Measure 5, Note Grouping 1:
        E quarter ⠫
        D eighth ⠑
        C eighth ⠙
        ===
        Measure 6, Note Grouping 1:
        <music21.clef.BassClef>
        B eighth ⠚
        A eighth ⠊
        G eighth ⠓
        F eighth ⠛
        ===
        Measure 7, Note Grouping 1:
        Octave 3 ⠸
        E quarter ⠫
        D eighth ⠑
        C eighth ⠙
        ===
        Measure 8, Note Grouping 1:
        D eighth ⠑
        C eighth ⠙
        B eighth ⠚
        Accidental sharp ⠩
        A eighth ⠊
        ===
        Measure 9, Note Grouping 1:
        B half ⠞
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 1 sharp(s) ⠩
        Time Signature 5/8 ⠼⠑⠦
        ===
        Measure 1, Tempo Text Grouping 1:
        Tempo Text Not too fast ⠠⠝⠕⠞⠀⠞⠕⠕⠀⠋⠁⠎⠞⠲
        ===
        Measure 1, Metronome Mark Grouping 1:
        Metronome Note C quarter ⠹
        Metronome symbol ⠶
        Metronome number 100 ⠼⠁⠚⠚
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.BassClef>
        Octave 3 ⠸
        E eighth ⠋
        Accidental sharp ⠩
        D eighth ⠑
        E eighth ⠋
        F eighth ⠛
        D eighth ⠑
        ===
        Measure 2, Note Grouping 1:
        B quarter ⠺
        Octave 3 ⠸
        E quarter ⠫
        G eighth ⠓
        ===
        Measure 3, Note Grouping 1:
        G eighth ⠓
        F eighth ⠛
        G eighth ⠓
        A eighth ⠊
        B eighth ⠚
        ===
        Measure 4, Note Grouping 1:
        B quarter ⠺
        Octave 2 ⠘
        B quarter ⠺
        B eighth ⠚
        ===
        Measure 5, Note Grouping 1:
        Octave 2 ⠘
        D eighth ⠑
        G eighth ⠓
        B eighth ⠚
        G eighth ⠓
        B eighth ⠚
        ===
        Measure 6, Note Grouping 1:
        Octave 3 ⠸
        E quarter ⠫
        G quarter ⠳
        F eighth ⠛
        ===
        Measure 7, Note Grouping 1:
        E eighth ⠋
        Octave 2 ⠘
        B eighth ⠚
        Octave 3 ⠸
        G eighth ⠓
        E eighth ⠋
        Octave 2 ⠘
        B eighth ⠚
        ===
        Measure 8, Note Grouping 1:
        Octave 3 ⠸
        E quarter ⠫
        Octave 2 ⠘
        E quarter ⠫
        E eighth ⠋
        ===
        Measure 9, Note Grouping 1:
        Octave 2 ⠘
        E quarter ⠫
        Rest eighth ⠭
        E eighth ⠋
        E eighth ⠋
        ===
        Measure 10, Note Grouping 1:
        D eighth ⠑
        E eighth ⠋
        E eighth ⠋
        E eighth ⠋
        E eighth ⠋
        ===
        Measure 11, Note Grouping 1:
        E eighth ⠋
        E eighth ⠋
        E quarter ⠫
        E eighth ⠋
        ===
        Measure 12, Note Grouping 1:
        E quarter ⠫
        Tie ⠈⠉
        E eighth ⠋
        Rest eighth ⠭
        Rest eighth ⠭
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 4 flat(s) ⠼⠙⠣
        Time Signature 6/8 ⠼⠋⠦
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        F quarter ⠻
        Octave 5 ⠨
        C eighth ⠙
        D eighth ⠑
        C eighth ⠙
        B eighth ⠚
        ===
        Measure 2, Signature Grouping 1:
        Time Signature 2/4 ⠼⠃⠲
        ===
        Measure 2, Note Grouping 1:
        Octave 4 ⠐
        A quarter ⠪
        G quarter ⠳
        Barline double ⠣⠅⠄
        ===
        Measure 3, Signature Grouping 1:
        Key Signature -4 naturals ⠡
        Key Signature 3 flat(s) ⠣⠣⠣
        Time Signature 6/8 ⠼⠋⠦
        ===
        Measure 3, Note Grouping 1:
        Octave 4 ⠐
        E eighth ⠋
        Octave 5 ⠨
        E eighth ⠋
        D eighth ⠑
        E quarter ⠫
        Octave 4 ⠐
        G eighth ⠓
        ===
        Measure 4, Signature Grouping 1:
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 4, Note Grouping 1:
        Octave 4 ⠐
        A quarter ⠪
        G quarter ⠳
        F quarter ⠻
        Barline double ⠣⠅⠄
        ===
        Measure 5, Signature Grouping 1:
        Key Signature -3 naturals ⠡⠡⠡
        Key Signature 0 flat(s)
        ===
        Measure 5, Note Grouping 1:
        Octave 4 ⠐
        G eighth ⠓
        F eighth ⠛
        E eighth ⠋
        D eighth ⠑
        C eighth ⠙
        B eighth ⠚
        ===
        Measure 6, Note Grouping 1:
        C half ⠝
        Dot ⠄
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 1 flat(s) ⠣
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Split Note Grouping A 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        E eighth ⠋
        Accidental sharp ⠩
        F eighth ⠛
        Accidental sharp ⠩
        G eighth ⠓
        A eighth ⠊
        music hyphen ⠐
        ===
        Measure 1, Split Note Grouping B 1:
        Octave 4 ⠐
        B eighth ⠚
        Accidental natural ⠡
        G eighth ⠓
        E eighth ⠋
        C eighth ⠙
        ===
        Measure 2, Note Grouping 1:
        F eighth ⠛
        A eighth ⠊
        G eighth ⠓
        C eighth ⠙
        Octave 4 ⠐
        A half ⠎
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 1 flat(s) ⠣
        Time Signature 6/8 ⠼⠋⠦
        ===
        Measure 1, Split Note Grouping A 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        E eighth ⠋
        Accidental sharp ⠩
        F eighth ⠛
        Accidental sharp ⠩
        G eighth ⠓
        music hyphen ⠐
        ===
        Measure 1, Split Note Grouping B 1:
        Octave 4 ⠐
        A eighth ⠊
        B eighth ⠚
        Accidental natural ⠡
        G eighth ⠓
        ===
        Measure 2, Note Grouping 1:
        E eighth ⠋
        C eighth ⠙
        F eighth ⠛
        A eighth ⠊
        G eighth ⠓
        C eighth ⠙
        ===
        Measure 3, Note Grouping 1:
        Octave 4 ⠐
        A half ⠎
        Dot ⠄
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 1 flat(s) ⠣
        Time Signature 12/8 ⠼⠁⠃⠦
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        E half ⠏
        Dot ⠄
        Tie ⠈⠉
        E eighth ⠋
        Accidental sharp ⠩
        F eighth ⠛
        Accidental sharp ⠩
        G eighth ⠓
        A eighth ⠊
        B eighth ⠚
        Accidental natural ⠡
        G eighth ⠓
        ===
        Measure 2, Split Note Grouping A 1:
        C eighth ⠙
        D eighth ⠑
        E eighth ⠋
        F quarter ⠻
        Dot ⠄
        Tie ⠈⠉
        F eighth ⠛
        music hyphen ⠐
        ===
        Measure 2, Split Note Grouping B 1:
        Octave 4 ⠐
        E eighth ⠋
        F eighth ⠛
        G eighth ⠓
        F eighth ⠛
        E eighth ⠋
        ===
        Measure 3, Note Grouping 1:
        F half ⠟
        Dot ⠄
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 3 flat(s) ⠣⠣⠣
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        G quarter ⠳
        Dot ⠄
        F eighth ⠛
        E quarter ⠫
        ===
        Measure 2, Note Grouping 1:
        Octave 3 ⠸
        B quarter ⠺
        Octave 4 ⠐
        B quarter ⠺
        G quarter ⠳
        ===
        Measure 3, Note Grouping 1:
        F half ⠟
        Barline double ⠣⠅⠄
        music hyphen ⠐
        ===
        Measure 3, Note Grouping 2:
        Octave 4 ⠐
        G quarter ⠳
        ===
        Measure 4, Note Grouping 1:
        Octave 5 ⠨
        E quarter ⠫
        Dot ⠄
        D eighth ⠑
        C quarter ⠹
        ===
        Measure 5, Note Grouping 1:
        D quarter ⠱
        Octave 4 ⠐
        G quarter ⠳
        Accidental natural ⠡
        B quarter ⠺
        ===
        Measure 6, Note Grouping 1:
        Octave 5 ⠨
        D quarter ⠱
        C quarter ⠹
        Barline double ⠣⠅⠄
        music hyphen ⠐
        ===
        Measure 6, Signature Grouping 2:
        Key Signature 4 flat(s) ⠼⠙⠣
        music hyphen ⠐
        ===
        Measure 6, Note Grouping 2:
        Octave 5 ⠨
        C quarter ⠹
        ===
        Measure 7, Note Grouping 1:
        A quarter ⠪
        Dot ⠄
        G eighth ⠓
        F quarter ⠻
        ===
        Measure 8, Note Grouping 1:
        C quarter ⠹
        Octave 5 ⠨
        C quarter ⠹
        Accidental natural ⠡
        Octave 4 ⠐
        E quarter ⠫
        ===
        Measure 9, Note Grouping 1:
        F half ⠟
        Dot ⠄
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 3 sharp(s) ⠩⠩⠩
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        A quarter ⠪
        Octave 5 ⠨
        A quarter ⠪
        Tie ⠈⠉
        A eighth ⠊
        G eighth ⠓
        F eighth ⠛
        E eighth ⠋
        ===
        Measure 2, Note Grouping 1:
        F quarter ⠻
        E quarter ⠫
        Tie ⠈⠉
        E eighth ⠋
        D eighth ⠑
        C eighth ⠙
        B eighth ⠚
        ===
        Measure 3, Note Grouping 1:
        D quarter ⠱
        C quarter ⠹
        Tie ⠈⠉
        C eighth ⠙
        B eighth ⠚
        A eighth ⠊
        B eighth ⠚
        ===
        Measure 4, Note Grouping 1:
        C half ⠝
        Barline double ⠣⠅⠄
        music hyphen ⠐
        ===
        Measure 4, Note Grouping 2:
        Rest eighth ⠭
        Octave 5 ⠨
        A eighth ⠊
        G eighth ⠓
        F eighth ⠛
        ===
        Measure 5, Note Grouping 1:
        E eighth ⠋
        D eighth ⠑
        C eighth ⠙
        B eighth ⠚
        A eighth ⠊
        B eighth ⠚
        C eighth ⠙
        B eighth ⠚
        ===
        Measure 6, Note Grouping 1:
        A half ⠎
        Dot ⠄
        Rest quarter ⠧
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 2 flat(s) ⠣⠣
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.BassClef>
        Octave 2 ⠘
        B quarter ⠺
        Octave 3 ⠸
        F quarter ⠻
        B quarter ⠺
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        F quarter ⠻
        ===
        Measure 2, Note Grouping 1:
        B quarter ⠺
        D quarter ⠱
        C quarter ⠹
        A quarter ⠪
        ===
        Measure 3, Note Grouping 1:
        B whole ⠾
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠣⠣⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠘⠺⠸⠻⠺⠐⠻⠀⠺⠱⠹⠪⠀⠾⠣⠅
        '''
        self.methodArgs = {'showClefSigns': True}
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 2 flat(s) ⠣⠣
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        Bass Clef ⠜⠼
        Octave 2 ⠘
        B quarter ⠺
        Octave 3 ⠸
        F quarter ⠻
        B quarter ⠺
        Treble Clef ⠜⠌
        Octave 4 ⠐
        F quarter ⠻
        ===
        Measure 2, Note Grouping 1:
        B quarter ⠺
        D quarter ⠱
        C quarter ⠹
        A quarter ⠪
        ===
        Measure 3, Note Grouping 1:
        B whole ⠾
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 3 sharp(s) ⠩⠩⠩
        Time Signature 6/8 ⠼⠋⠦
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.AltoClef>
        Octave 4 ⠐
        A eighth ⠊
        E eighth ⠋
        A eighth ⠊
        B eighth ⠚
        C eighth ⠙
        D eighth ⠑
        ===
        Measure 2, Note Grouping 1:
        <music21.clef.TrebleClef>
        E eighth ⠋
        F eighth ⠛
        G eighth ⠓
        A quarter ⠪
        Dot ⠄
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠩⠩⠩⠼⠋⠦⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠐⠊⠋⠊⠚⠙⠑⠀⠋⠛⠓⠪⠄⠣⠅
        '''
        self.methodArgs = {'showClefSigns': True}
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 3 sharp(s) ⠩⠩⠩
        Time Signature 6/8 ⠼⠋⠦
        ===
        Measure 1, Note Grouping 1:
        Alto Clef ⠜⠬
        Octave 4 ⠐
        A eighth ⠊
        E eighth ⠋
        A eighth ⠊
        B eighth ⠚
        C eighth ⠙
        D eighth ⠑
        ===
        Measure 2, Note Grouping 1:
        Treble Clef ⠜⠌
        Octave 5 ⠨
        E eighth ⠋
        F eighth ⠛
        G eighth ⠓
        A quarter ⠪
        Dot ⠄
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠩⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠐⠱⠻⠪⠻⠀⠑⠋⠛⠓⠎⠣⠅⠄⠀⠣⠣⠣⠀⠐⠫⠳⠺⠳⠀⠋⠛⠓⠊⠞⠣⠅⠄⠀⠼⠙⠩
        ⠀⠀⠐⠫⠳⠺⠳⠀⠋⠛⠓⠊⠞⠣⠅⠄⠀⠣⠀⠐⠻⠪⠹⠪⠀⠛⠓⠊⠚⠝⠣⠅⠄⠀⠼⠋⠣
        ⠀⠀⠐⠳⠺⠱⠺⠀⠓⠊⠚⠙⠕⠣⠅⠄
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠁⠀⠨⠱⠺⠳⠺⠀⠑⠙⠚⠊⠗⠣⠅⠄
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
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠉⠕⠝⠀⠃⠗⠊⠕⠲⠀⠣⠨⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠚⠀⠜⠼⠇⠘⠪⠀⠱⠧⠐⠕⠈⠉⠀⠑⠛⠋⠑⠩⠹⠪⠀⠞⠈⠉⠚⠑⠠⠄⠡⠠⠄⠙⠚
        ⠀⠀⠸⠪⠻⠱⠫⠀⠻⠓⠊⠺⠩⠙⠡⠚⠀⠩⠙⠑⠜⠌⠇⠐⠑⠋⠛⠊⠪⠀⠓⠋⠩⠙⠓⠐
        ⠀⠀⠐⠛⠑⠡⠚⠐⠛⠀⠜⠼⠇⠐⠋⠩⠙⠊⠐⠋⠑⠡⠙⠚⠑⠀⠹⠚⠊⠳⠛⠋⠀⠱⠘⠪⠱⠣⠅
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 2 sharp(s) ⠩⠩
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.BassClef>
        Octave 3 ⠸
        D quarter ⠱
        E eighth ⠋
        F eighth ⠛
        G eighth ⠓
        A eighth ⠊
        ===
        Measure 2, Note Grouping 1:
        B quarter ⠺
        A quarter ⠪
        G eighth ⠓
        F eighth ⠛
        ===
        Measure 3, Note Grouping 1:
        E eighth ⠋
        D eighth ⠑
        C eighth ⠙
        D eighth ⠑
        E eighth ⠋
        F eighth ⠛
        ===
        Measure 4, Note Grouping 1:
        G quarter ⠳
        A quarter ⠪
        Rest quarter ⠧
        ===
        Measure 5, Note Grouping 1:
        B quarter ⠺
        C eighth ⠙
        D eighth ⠑
        E eighth ⠋
        F eighth ⠛
        ===
        Measure 6, Note Grouping 1:
        E quarter ⠫
        D quarter ⠱
        C eighth ⠙
        B eighth ⠚
        ===
        Measure 7, Note Grouping 1:
        Octave 4 ⠐
        C eighth ⠙
        E eighth ⠋
        D eighth ⠑
        C eighth ⠙
        B eighth ⠚
        Accidental sharp ⠩
        A eighth ⠊
        ===
        Measure 8, Note Grouping 1:
        B half ⠞
        Rest quarter ⠧
        ===
        ---end segment---
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 9, Note Grouping 1:
        Octave 4 ⠐
        F quarter ⠻
        D eighth ⠑
        C eighth ⠙
        B quarter ⠺
        ===
        Measure 10, Note Grouping 1:
        Octave 4 ⠐
        E quarter ⠫
        C eighth ⠙
        B eighth ⠚
        Accidental sharp ⠩
        A quarter ⠪
        ===
        Measure 11, Note Grouping 1:
        Octave 4 ⠐
        D quarter ⠱
        B eighth ⠚
        Accidental natural ⠡
        A eighth ⠊
        Accidental sharp ⠩
        G quarter ⠳
        ===
        Measure 12, Note Grouping 1:
        A half ⠎
        Rest quarter ⠧
        ===
        Measure 13, Note Grouping 1:
        A quarter ⠪
        G eighth ⠓
        F eighth ⠛
        E eighth ⠋
        D eighth ⠑
        ===
        Measure 14, Note Grouping 1:
        C quarter ⠹
        D quarter ⠱
        E eighth ⠋
        F eighth ⠛
        ===
        Measure 15, Note Grouping 1:
        Octave 3 ⠸
        G eighth ⠓
        A eighth ⠊
        B eighth ⠚
        A eighth ⠊
        G eighth ⠓
        F eighth ⠛
        ===
        Measure 16, Note Grouping 1:
        E quarter ⠫
        D quarter ⠱
        Rest quarter ⠧
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠣⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠚⠀⠐⠺⠀⠳⠫⠱⠫⠀⠗⠻⠫⠀⠪⠳⠨⠹⠄⠙⠀⠞⠄⠺⠀⠨⠫⠐⠺⠪⠄⠓⠀⠗⠻⠨⠹
        ⠀⠀⠨⠹⠐⠻⠪⠄⠑⠀⠏⠄⠐
        ⠼⠓⠄⠀⠐⠳⠀⠳⠄⠛⠻⠻⠀⠎⠳⠺⠀⠺⠡⠪⠪⠹⠀⠞⠄⠺⠀⠨⠫⠐⠺⠪⠳⠀⠗⠻⠨⠹
        ⠀⠀⠨⠹⠧⠐⠻⠧⠀⠎⠄⠱⠀⠏⠄⠣⠅
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        G quarter ⠳
        Dot ⠄
        Opening single slur ⠉
        F eighth ⠛
        E quarter ⠫
        Opening single slur ⠉
        D quarter ⠱
        ===
        Measure 2, Note Grouping 1:
        G quarter ⠳
        Opening single slur ⠉
        F quarter ⠻
        Opening single slur ⠉
        E quarter ⠫
        Rest quarter ⠧
        ===
        Measure 3, Note Grouping 1:
        F quarter ⠻
        Opening single slur ⠉
        G quarter ⠳
        Opening single slur ⠉
        A quarter ⠪
        Opening single slur ⠉
        B quarter ⠺
        ===
        Measure 4, Note Grouping 1:
        C quarter ⠹
        Opening single slur ⠉
        D quarter ⠱
        Opening single slur ⠉
        C quarter ⠹
        Rest quarter ⠧
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        G quarter ⠳
        Dot ⠄
        Opening double slur ⠉⠉
        F eighth ⠛
        E quarter ⠫
        D quarter ⠱
        ===
        Measure 2, Note Grouping 1:
        G quarter ⠳
        F quarter ⠻
        Closing bracket slur ⠉
        E quarter ⠫
        Rest quarter ⠧
        ===
        Measure 3, Note Grouping 1:
        F quarter ⠻
        Opening double slur ⠉⠉
        G quarter ⠳
        A quarter ⠪
        B quarter ⠺
        ===
        Measure 4, Note Grouping 1:
        C quarter ⠹
        D quarter ⠱
        Closing bracket slur ⠉
        C quarter ⠹
        Rest quarter ⠧
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Opening bracket slur ⠰⠃
        Accidental flat ⠣
        Octave 4 ⠐
        E quarter ⠫
        Dot ⠄
        F eighth ⠛
        G quarter ⠳
        E quarter ⠫
        ===
        Measure 2, Note Grouping 1:
        F quarter ⠻
        G quarter ⠳
        Accidental flat ⠣
        A quarter ⠪
        Closing bracket slur ⠘⠆
        Rest quarter ⠧
        ===
        Measure 3, Note Grouping 1:
        Opening bracket slur ⠰⠃
        G quarter ⠳
        G quarter ⠳
        Accidental flat ⠣
        Octave 5 ⠨
        E quarter ⠫
        D quarter ⠱
        ===
        Measure 4, Note Grouping 1:
        C half ⠝
        Dot ⠄
        Closing bracket slur ⠘⠆
        Rest quarter ⠧
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 12/8 ⠼⠁⠃⠦
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Opening bracket slur ⠰⠃
        Octave 5 ⠨
        E quarter ⠫
        Dot ⠄
        Opening single slur ⠉
        C quarter ⠹
        Opening single slur ⠉
        G eighth ⠓
        G quarter ⠳
        Dot ⠄
        Opening single slur ⠉
        F quarter ⠻
        Opening single slur ⠉
        E eighth ⠋
        Closing bracket slur ⠘⠆
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 2 sharp(s) ⠩⠩
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Opening bracket slur ⠰⠃
        Octave 4 ⠐
        A half ⠎
        B quarter ⠺
        ===
        Measure 2, Note Grouping 1:
        A eighth ⠊
        Octave 5 ⠨
        F eighth ⠛
        E eighth ⠋
        D eighth ⠑
        C eighth ⠙
        B eighth ⠚
        ===
        Measure 3, Note Grouping 1:
        Opening bracket slur ⠰⠃
        Closing bracket slur ⠘⠆
        A quarter ⠪
        B eighth ⠚
        C eighth ⠙
        D eighth ⠑
        E eighth ⠋
        ===
        Measure 4, Note Grouping 1:
        F half ⠟
        Dot ⠄
        Closing bracket slur ⠘⠆
        ===
        ---end segment---
        '''
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠩⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠰⠃⠐⠎⠺⠀⠊⠨⠛⠋⠑⠙⠚⠀⠰⠃⠘⠆⠪⠚⠙⠑⠋⠀⠟⠄⠘⠆
        '''
        self.methodArgs = {'showFirstMeasureNumber': False, 'slurLongPhraseWithBrackets': False}
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 2 sharp(s) ⠩⠩
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        A half ⠎
        Opening double slur ⠉⠉
        B quarter ⠺
        ===
        Measure 2, Note Grouping 1:
        A eighth ⠊
        Octave 5 ⠨
        F eighth ⠛
        E eighth ⠋
        D eighth ⠑
        C eighth ⠙
        B eighth ⠚
        Closing bracket slur ⠉
        ===
        Measure 3, Note Grouping 1:
        A quarter ⠪
        Opening double slur ⠉⠉
        B eighth ⠚
        C eighth ⠙
        D eighth ⠑
        E eighth ⠋
        Closing bracket slur ⠉
        ===
        Measure 4, Note Grouping 1:
        F half ⠟
        Dot ⠄
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 5 ⠨
        C half ⠝
        Tie ⠈⠉
        C eighth ⠙
        Opening single slur ⠉
        D eighth ⠑
        ===
        Measure 2, Note Grouping 1:
        D half ⠕
        Tie ⠈⠉
        D eighth ⠑
        Opening single slur ⠉
        E eighth ⠋
        ===
        ---end segment---
        '''
        self.b = '''
        ⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀
        ⠨⠝⠈⠉⠙⠉⠑⠀⠕⠈⠉⠑⠉⠋
        '''
        self.methodArgs = {'showFirstMeasureNumber': False, 'showShortSlursAndTiesTogether': True}
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 5 ⠨
        C half ⠝
        Opening single slur ⠉
        Tie ⠈⠉
        C eighth ⠙
        Opening single slur ⠉
        D eighth ⠑
        ===
        Measure 2, Note Grouping 1:
        D half ⠕
        Opening single slur ⠉
        Tie ⠈⠉
        D eighth ⠑
        Opening single slur ⠉
        E eighth ⠋
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 1 flat(s) ⠣
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Opening bracket slur ⠰⠃
        Octave 5 ⠨
        F half ⠟
        Dot ⠄
        Tie ⠈⠉
        ===
        Measure 2, Note Grouping 1:
        F eighth ⠛
        C eighth ⠙
        D eighth ⠑
        C eighth ⠙
        B eighth ⠚
        A eighth ⠊
        Closing bracket slur ⠘⠆
        ===
        ---end segment---
        '''
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠣⠼⠉⠲⠀⠀⠀⠀⠀⠀
        ⠰⠃⠨⠟⠄⠈⠉⠀⠛⠙⠑⠙⠚⠊⠘⠆
        '''
        self.methodArgs = {'showFirstMeasureNumber': False, 'slurLongPhraseWithBrackets': False}
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 1 flat(s) ⠣
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 5 ⠨
        F half ⠟
        Dot ⠄
        Tie ⠈⠉
        ===
        Measure 2, Note Grouping 1:
        F eighth ⠛
        Opening double slur ⠉⠉
        C eighth ⠙
        D eighth ⠑
        C eighth ⠙
        B eighth ⠚
        Closing bracket slur ⠉
        A eighth ⠊
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 1 flat(s) ⠣
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 5 ⠨
        F half ⠟
        Dot ⠄
        Tie ⠈⠉
        ===
        Measure 2, Note Grouping 1:
        Opening bracket slur ⠰⠃
        F eighth ⠛
        C eighth ⠙
        D eighth ⠑
        C eighth ⠙
        B eighth ⠚
        A eighth ⠊
        Closing bracket slur ⠘⠆
        ===
        ---end segment---
        '''
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠣⠼⠉⠲⠀⠀⠀⠀⠀⠀
        ⠨⠟⠄⠈⠉⠀⠰⠃⠛⠙⠑⠙⠚⠊⠘⠆
        '''
        self.methodArgs = {'showFirstMeasureNumber': False, 'slurLongPhraseWithBrackets': False}
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 1 flat(s) ⠣
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 5 ⠨
        F half ⠟
        Dot ⠄
        Tie ⠈⠉
        ===
        Measure 2, Note Grouping 1:
        F eighth ⠛
        Opening double slur ⠉⠉
        C eighth ⠙
        D eighth ⠑
        C eighth ⠙
        B eighth ⠚
        Closing bracket slur ⠉
        A eighth ⠊
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Opening bracket slur ⠰⠃
        Octave 5 ⠨
        E eighth ⠋
        F eighth ⠛
        G eighth ⠓
        F eighth ⠛
        E eighth ⠋
        D eighth ⠑
        ===
        Measure 2, Note Grouping 1:
        C half ⠝
        Dot ⠄
        Tie ⠈⠉
        ===
        Measure 3, Note Grouping 1:
        C quarter ⠹
        Closing bracket slur ⠘⠆
        Rest quarter ⠧
        Rest quarter ⠧
        ===
        ---end segment---
        '''
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠰⠃⠨⠋⠛⠓⠛⠋⠑⠀⠝⠄⠈⠉⠀⠹⠘⠆⠧⠧
        '''
        self.methodArgs = {'showFirstMeasureNumber': False, 'slurLongPhraseWithBrackets': False}
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 5 ⠨
        E eighth ⠋
        Opening double slur ⠉⠉
        F eighth ⠛
        G eighth ⠓
        F eighth ⠛
        E eighth ⠋
        D eighth ⠑
        Closing bracket slur ⠉
        ===
        Measure 2, Note Grouping 1:
        C half ⠝
        Dot ⠄
        Tie ⠈⠉
        ===
        Measure 3, Note Grouping 1:
        C quarter ⠹
        Rest quarter ⠧
        Rest quarter ⠧
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        C quarter ⠹
        Opening single slur ⠉
        C quarter ⠹
        Opening single slur ⠉
        C quarter ⠹
        Opening single slur ⠉
        C quarter ⠹
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 1 flat(s) ⠣
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Word ⠜
        Text Expression dolce ⠙⠕⠇⠉⠑
        Octave 4 ⠐
        F half ⠟
        E quarter ⠫
        ===
        Measure 2, Note Grouping 1:
        E quarter ⠫
        D quarter ⠱
        Word: ⠜
        Dynamic p ⠏
        Octave 4 ⠐
        C quarter ⠹
        ===
        Measure 3, Note Grouping 1:
        Octave 4 ⠐
        A quarter ⠪
        Dot ⠄
        B eighth ⠚
        A quarter ⠪
        ===
        Measure 4, Note Grouping 1:
        G quarter ⠳
        Word: ⠜
        Dynamic mf ⠍⠋
        Octave 4 ⠐
        C eighth ⠙
        D eighth ⠑
        E eighth ⠋
        F eighth ⠛
        ===
        Measure 5, Note Grouping 1:
        Octave 4 ⠐
        G quarter ⠳
        Word ⠜
        Text Expression rit. ⠗⠊⠞⠄
        Octave 4 ⠐
        F quarter ⠻
        E quarter ⠫
        ===
        Measure 6, Note Grouping 1:
        F half ⠟
        Dot ⠄
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 1 sharp(s) ⠩
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Word: ⠜
        Dynamic f ⠋
        Dot 3 ⠄
        Accidental sharp ⠩
        Octave 5 ⠨
        D quarter ⠱
        Opening single slur ⠉
        E eighth ⠋
        Rest eighth ⠭
        Word: ⠜
        Dynamic p ⠏
        Opening bracket slur ⠰⠃
        Octave 4 ⠐
        B quarter ⠺
        G quarter ⠳
        ===
        Measure 2, Note Grouping 1:
        A quarter ⠪
        F quarter ⠻
        G quarter ⠳
        Closing bracket slur ⠘⠆
        Word ⠜
        Text Expression rit. ⠗⠊⠞⠄
        Accidental natural ⠡
        Octave 4 ⠐
        F eighth ⠛
        Opening single slur ⠉
        E eighth ⠋
        ===
        Measure 3, Note Grouping 1:
        Octave 4 ⠐
        D eighth ⠑
        Opening single slur ⠉
        E eighth ⠋
        Opening single slur ⠉
        Accidental natural ⠡
        F eighth ⠛
        Opening single slur ⠉
        E eighth ⠋
        Word ⠜
        Text Expression morendo ⠍⠕⠗⠑⠝⠙⠕
        Dot 3 ⠄
        Accidental sharp ⠩
        Octave 4 ⠐
        F eighth ⠛
        Opening single slur ⠉
        G eighth ⠓
        F eighth ⠛
        Opening single slur ⠉
        Accidental sharp ⠩
        G eighth ⠓
        ===
        Measure 4, Note Grouping 1:
        Accidental sharp ⠩
        A whole ⠮
        Word: ⠜
        Dynamic ppp ⠏⠏⠏
        Dot 3 ⠄
        Barline final ⠣⠅
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Word ⠜
        Text Expression rush! ⠗⠥⠎⠓⠖
        Word: ⠜
        Dynamic f ⠋
        Octave 4 ⠐
        G eighth ⠓
        A eighth ⠊
        B eighth ⠚
        C eighth ⠙
        D eighth ⠑
        E eighth ⠋
        F eighth ⠛
        G eighth ⠓
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Word ⠜
        Text Expression (marc.) ⠶⠍⠁⠗⠉⠄⠶
        Word: ⠜
        Dynamic f ⠋
        Octave 4 ⠐
        C quarter ⠹
        C quarter ⠹
        E quarter ⠫
        C quarter ⠹
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 2 sharp(s) ⠩⠩
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 5 ⠨
        E quarter ⠫
        E quarter ⠫
        F quarter ⠻
        ===
        Measure 2, Note Grouping 1:
        G half ⠗
        Dot ⠄
        ===
        Measure 3, Long Text Expression Grouping 1:
        Word ⠜
        Text Expression dim. e rall. ⠙⠊⠍⠄⠀⠑⠀⠗⠁⠇⠇⠄
        Word ⠜
        ===
        Measure 3, Note Grouping 1:
        Octave 5 ⠨
        F eighth ⠛
        D eighth ⠑
        Octave 4 ⠐
        A eighth ⠊
        Octave 5 ⠨
        D eighth ⠑
        E eighth ⠋
        C eighth ⠙
        ===
        Measure 4, Note Grouping 1:
        D half ⠕
        Dot ⠄
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 2 flat(s) ⠣⠣
        Time Signature 2/4 ⠼⠃⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 5 ⠨
        D eighth ⠑
        C eighth ⠙
        B eighth ⠚
        A eighth ⠊
        ===
        Measure 2, Note Grouping 1:
        G half ⠗
        ===
        Measure 3, Long Text Expression Grouping 1:
        Word ⠜
        Text Expression calm, serene ⠉⠁⠇⠍⠂⠀⠎⠑⠗⠑⠝⠑
        Word ⠜
        ===
        Measure 3, Note Grouping 1:
        Octave 4 ⠐
        B quarter ⠺
        Dot ⠄
        A eighth ⠊
        ===
        Measure 4, Note Grouping 1:
        G quarter ⠳
        Dot ⠄
        B eighth ⠚
        ===
        Measure 5, Note Grouping 1:
        A quarter ⠪
        Dot ⠄
        G eighth ⠓
        ===
        Measure 6, Note Grouping 1:
        F half ⠟
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 2 flat(s) ⠣⠣
        Time Signature 2/4 ⠼⠃⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 5 ⠨
        D eighth ⠑
        C eighth ⠙
        B eighth ⠚
        A eighth ⠊
        ===
        Measure 2, Note Grouping 1:
        G half ⠗
        ===
        Measure 3, Long Text Expression Grouping 1:
        Word ⠜
        Text Expression Sehr ruhig ⠎⠑⠓⠗⠀⠗⠥⠓⠊⠛
        Word ⠜
        ===
        Measure 3, Note Grouping 1:
        Octave 4 ⠐
        B quarter ⠺
        Dot ⠄
        A eighth ⠊
        ===
        Measure 4, Note Grouping 1:
        G quarter ⠳
        Dot ⠄
        B eighth ⠚
        ===
        Measure 5, Note Grouping 1:
        A quarter ⠪
        Dot ⠄
        G eighth ⠓
        ===
        Measure 6, Note Grouping 1:
        F half ⠟
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        G quarter ⠳
        Rest quarter ⠧
        music hyphen ⠐
        ===
        Measure 1, Long Text Expression Grouping 2:
        Word ⠜
        Text Expression rit. e dim. ⠗⠊⠞⠄⠀⠑⠀⠙⠊⠍⠄
        Word ⠜
        music hyphen ⠐
        ===
        Measure 1, Note Grouping 2:
        Opening bracket slur ⠰⠃
        Octave 5 ⠨
        G quarter ⠳
        ===
        Measure 2, Note Grouping 1:
        G quarter ⠳
        E quarter ⠫
        C quarter ⠹
        ===
        Measure 3, Note Grouping 1:
        F quarter ⠻
        D quarter ⠱
        B quarter ⠺
        ===
        Measure 4, Note Grouping 1:
        C half ⠝
        Dot ⠄
        Closing bracket slur ⠘⠆
        ===
        ---end segment---
        '''
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
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠼⠁⠀⠘⠻⠐⠀⠜⠎⠏⠑⠑⠙⠊⠝⠛⠀⠥⠏⠜⠀⠘⠓⠊⠚⠙⠀⠱⠚⠙⠐
        ⠀⠀⠜⠎⠇⠕⠺⠊⠝⠛⠸⠑⠋⠀⠻⠋⠑⠹
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 45, Signature Grouping 1:
        Key Signature 2 sharp(s) ⠩⠩
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 45, Note Grouping 1:
        <music21.clef.TrebleClef>
        Opening bracket slur ⠰⠃
        Octave 4 ⠐
        E half ⠏
        F quarter ⠻
        G quarter ⠳
        ===
        Measure 46, Note Grouping 1:
        A half ⠎
        Word ⠜
        Text Expression rall. ⠗⠁⠇⠇⠄
        Octave 4 ⠐
        B quarter ⠺
        A quarter ⠪
        ===
        Measure 47, Note Grouping 1:
        G half ⠗
        F quarter ⠻
        E quarter ⠫
        ===
        Measure 48, Note Grouping 1:
        D half ⠕
        Dot ⠄
        Closing bracket slur ⠘⠆
        Rest quarter ⠧
        Barline double ⠣⠅⠄
        ===
        Measure 49, Signature Grouping 1:
        Key Signature 2 flat(s) ⠣⠣
        ===
        Measure 49, Tempo Text Grouping 1:
        Tempo Text Presto ⠠⠏⠗⠑⠎⠞⠕⠲
        ===
        Measure 49, Note Grouping 1:
        Word ⠜
        Text Expression ff ⠋⠋
        Octave 4 ⠐
        B quarter ⠺
        D eighth ⠑
        F eighth ⠛
        B quarter ⠺
        F eighth ⠛
        D eighth ⠑
        ===
        Measure 50, Note Grouping 1:
        B quarter ⠺
        Octave 5 ⠨
        E eighth ⠋
        G eighth ⠓
        B quarter ⠺
        G eighth ⠓
        E eighth ⠋
        ===
        Measure 51, Note Grouping 1:
        Octave 4 ⠐
        B quarter ⠺
        Octave 5 ⠨
        E eighth ⠋
        F eighth ⠛
        A quarter ⠪
        F eighth ⠛
        E eighth ⠋
        ===
        Measure 52, Note Grouping 1:
        Octave 4 ⠐
        B quarter ⠺
        D eighth ⠑
        F eighth ⠛
        B quarter ⠺
        Rest quarter ⠧
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 1 flat(s) ⠣
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Articulation accent ⠨⠦
        Octave 4 ⠐
        F eighth ⠛
        A eighth ⠊
        Articulation accent ⠨⠦
        C eighth ⠙
        A eighth ⠊
        Articulation accent ⠨⠦
        G eighth ⠓
        Octave 5 ⠨
        C eighth ⠙
        Articulation accent ⠨⠦
        Octave 4 ⠐
        E eighth ⠋
        G eighth ⠓
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Opening bracket slur ⠰⠃
        Octave 5 ⠨
        E half ⠏
        Dot ⠄
        ===
        Measure 2, Note Grouping 1:
        D quarter ⠱
        F quarter ⠻
        Octave 4 ⠐
        B quarter ⠺
        ===
        Measure 3, Note Grouping 1:
        C quarter ⠹
        Closing bracket slur ⠘⠆
        Articulation tenuto ⠸⠦
        Articulation tenuto ⠸⠦
        Octave 4 ⠐
        E quarter ⠫
        G quarter ⠳
        ===
        Measure 4, Note Grouping 1:
        Octave 5 ⠨
        C quarter ⠹
        D quarter ⠱
        Articulation tenuto ⠸⠦
        Accidental sharp ⠩
        D quarter ⠱
        ===
        Measure 5, Note Grouping 1:
        Articulation accent ⠨⠦
        E half ⠏
        Dot ⠄
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 3 flat(s) ⠣⠣⠣
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Opening bracket slur ⠰⠃
        Articulation accent ⠨⠦
        Octave 5 ⠨
        D eighth ⠑
        E eighth ⠋
        C eighth ⠙
        D eighth ⠑
        B eighth ⠚
        A eighth ⠊
        G eighth ⠓
        F eighth ⠛
        Closing bracket slur ⠘⠆
        ===
        Measure 2, Note Grouping 1:
        Articulation staccato ⠦
        G quarter ⠳
        Articulation staccato ⠦
        E quarter ⠫
        Articulation tenuto ⠸⠦
        E half ⠏
        ===
        Measure 3, Note Grouping 1:
        E quarter ⠫
        Opening single slur ⠉
        Articulation staccato ⠦
        E eighth ⠋
        Rest eighth ⠭
        G quarter ⠳
        Opening single slur ⠉
        Articulation staccato ⠦
        G eighth ⠓
        Rest eighth ⠭
        ===
        Measure 4, Note Grouping 1:
        Articulation tenuto ⠸⠦
        Octave 4 ⠐
        F quarter ⠻
        Opening single slur ⠉
        Articulation tenuto ⠸⠦
        F quarter ⠻
        E quarter ⠫
        Tie ⠈⠉
        E eighth ⠋
        Rest eighth ⠭
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 1 flat(s) ⠣
        Time Signature cut ⠸⠉
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.BassClef>
        Articulation staccato ⠦
        Articulation staccato ⠦
        Octave 3 ⠸
        D eighth ⠑
        Rest eighth ⠭
        F eighth ⠛
        Rest eighth ⠭
        A eighth ⠊
        Rest eighth ⠭
        Articulation staccato ⠦
        Octave 4 ⠐
        D eighth ⠑
        Rest eighth ⠭
        ===
        Measure 2, Note Grouping 1:
        Articulation accent ⠨⠦
        B half ⠞
        A quarter ⠪
        Rest quarter ⠧
        ===
        ---end segment---
        '''
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
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⠸⠻⠦⠦⠑⠛⠙⠋⠀⠨⠦⠨⠦⠘⠚⠊⠚⠙⠨⠦⠱⠀⠑⠦⠋⠸⠦⠻⠧
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.BassClef>
        Articulation staccato ⠦
        Articulation accent ⠨⠦
        Octave 3 ⠸
        C quarter ⠹
        Articulation staccato ⠦
        Articulation accent ⠨⠦
        E quarter ⠫
        Articulation staccato ⠦
        Articulation accent ⠨⠦
        F quarter ⠻
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.BassClef>
        Articulation accent ⠨⠦
        Articulation tenuto ⠸⠦
        Octave 3 ⠸
        G quarter ⠳
        Articulation accent ⠨⠦
        Articulation tenuto ⠸⠦
        B quarter ⠺
        Articulation accent ⠨⠦
        Articulation tenuto ⠸⠦
        C quarter ⠹
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.BassClef>
        Octave 3 ⠸
        G quarter ⠳
        Note-fermata: Shape normal: ⠣⠇
        Tie ⠈⠉
        G eighth ⠓
        F eighth ⠛
        D eighth ⠑
        B eighth ⠚
        ===
        Measure 2, Note Grouping 1:
        C half ⠝
        Dot ⠄
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 1 flat(s) ⠣
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 5 ⠨
        D eighth ⠑
        F eighth ⠛
        F quarter ⠻
        E eighth ⠋
        C eighth ⠙
        Rest quarter ⠧
        Note-fermata: Shape normal: ⠣⠇
        ===
        Measure 2, Note Grouping 1:
        D half ⠕
        Rest quarter ⠧
        Note-fermata: Shape normal: ⠣⠇
        Opening bracket slur ⠰⠃
        D eighth ⠑
        F eighth ⠛
        ===
        Measure 3, Note Grouping 1:
        E eighth ⠋
        C eighth ⠙
        D half ⠕
        Closing bracket slur ⠘⠆
        Rest quarter ⠧
        Note-fermata: Shape normal: ⠣⠇
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 0, Signature Grouping 1:
        Key Signature 1 sharp(s) ⠩
        Time Signature 2/4 ⠼⠃⠲
        ===
        Measure 0, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        D eighth ⠑
        ===
        Measure 1, Note Grouping 1:
        G eighth ⠓
        Dot ⠄
        F 16th ⠿
        G eighth ⠓
        B eighth ⠚
        ===
        Measure 2, Note Grouping 1:
        A eighth ⠊
        Dot ⠄
        G 16th ⠷
        A eighth ⠊
        B eighth ⠚
        ===
        Measure 3, Note Grouping 1:
        G eighth ⠓
        Dot ⠄
        G 16th ⠷
        B eighth ⠚
        D eighth ⠑
        ===
        Measure 4, Note Grouping 1:
        E quarter ⠫
        Dot ⠄
        E eighth ⠋
        ===
        Measure 5, Note Grouping 1:
        D eighth ⠑
        Dot ⠄
        B 16th ⠾
        B eighth ⠚
        G eighth ⠓
        ===
        Measure 6, Note Grouping 1:
        A eighth ⠊
        Dot ⠄
        G 16th ⠷
        A eighth ⠊
        B eighth ⠚
        ===
        Measure 7, Note Grouping 1:
        Octave 4 ⠐
        G eighth ⠓
        Dot ⠄
        E 16th ⠯
        E eighth ⠋
        D eighth ⠑
        ===
        Measure 8, Note Grouping 1:
        G quarter ⠳
        Dot ⠄
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 1 sharp(s) ⠩
        Time Signature 2/4 ⠼⠃⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 5 ⠨
        D eighth ⠑
        Rest 16th ⠍
        E 16th ⠯
        D eighth ⠑
        Rest 16th ⠍
        Accidental sharp ⠩
        C 16th ⠽
        ===
        Measure 2, Note Grouping 1:
        D quarter ⠱
        B eighth ⠚
        Rest eighth ⠭
        ===
        Measure 3, Note Grouping 1:
        B eighth ⠚
        Rest 16th ⠍
        C 16th ⠽
        B eighth ⠚
        Rest 16th ⠍
        Accidental sharp ⠩
        A 16th ⠮
        ===
        Measure 4, Note Grouping 1:
        B quarter ⠺
        G eighth ⠓
        Rest eighth ⠭
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 6/8 ⠼⠋⠦
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        E eighth ⠋
        Dot ⠄
        F 16th ⠿
        E eighth ⠋
        G quarter ⠳
        G eighth ⠓
        ===
        Measure 2, Note Grouping 1:
        D eighth ⠑
        Dot ⠄
        E 16th ⠯
        D eighth ⠑
        F quarter ⠻
        F eighth ⠛
        ===
        Measure 3, Note Grouping 1:
        C quarter ⠹
        D eighth ⠑
        E quarter ⠫
        F eighth ⠛
        ===
        Measure 4, Note Grouping 1:
        E quarter ⠫
        D eighth ⠑
        D quarter ⠱
        E eighth ⠋
        ===
        Measure 5, Note Grouping 1:
        E quarter ⠫
        F eighth ⠛
        G quarter ⠳
        A 16th ⠮
        B 32nd ⠞
        C 32nd ⠝
        ===
        Measure 6, Note Grouping 1:
        Octave 4 ⠐
        C quarter ⠹
        E 16th ⠯
        D 16th ⠵
        C quarter ⠹
        Rest 16th ⠍
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 5 ⠨
        E quarter ⠫
        Tie ⠈⠉
        E eighth ⠋
        Dot ⠄
        F 16th ⠿
        D eighth ⠑
        Dot ⠄
        E 16th ⠯
        ===
        Measure 2, Note Grouping 1:
        C quarter ⠹
        Octave 6 ⠰
        C quarter ⠹
        C quarter ⠹
        ===
        Measure 3, Note Grouping 1:
        Accidental sharp ⠩
        Octave 5 ⠨
        G 16th ⠷
        A 16th ⠮
        Rest eighth ⠭
        E 16th ⠯
        F 16th ⠿
        Rest eighth ⠭
        D 16th ⠵
        B 16th ⠾
        Rest eighth ⠭
        ===
        Measure 4, Note Grouping 1:
        C quarter ⠹
        Rest quarter ⠧
        Rest quarter ⠧
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 0, Signature Grouping 1:
        Key Signature 3 sharp(s) ⠩⠩⠩
        Time Signature 3/8 ⠼⠉⠦
        ===
        Measure 0, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        E 16th ⠯
        Dot ⠄
        B 32nd ⠞
        ===
        Measure 1, Note Grouping 1:
        B eighth ⠚
        A eighth ⠊
        B eighth ⠚
        ===
        Measure 2, Note Grouping 1:
        Accidental sharp ⠩
        B eighth ⠚
        C 16th ⠽
        Rest 16th ⠍
        Octave 4 ⠐
        E 16th ⠯
        Dot ⠄
        Octave 5 ⠨
        C 32nd ⠝
        ===
        Measure 3, Note Grouping 1:
        C eighth ⠙
        B eighth ⠚
        C eighth ⠙
        ===
        Measure 4, Note Grouping 1:
        C eighth ⠙
        D 16th ⠵
        Rest 16th ⠍
        D eighth ⠑
        ===
        Measure 5, Note Grouping 1:
        D quarter ⠱
        E 16th ⠯
        F 16th ⠿
        ===
        Measure 6, Note Grouping 1:
        F 16th ⠿
        Octave 4 ⠐
        B eighth ⠚
        Dot ⠄
        C eighth ⠙
        ===
        Measure 7, Note Grouping 1:
        Octave 5 ⠨
        E eighth ⠋
        Dot ⠄
        D 16th ⠵
        C 16th ⠽
        B 16th ⠾
        ===
        Measure 8, Note Grouping 1:
        A quarter ⠪
        Barline double ⠣⠅⠄
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        C 16th ⠽
        B beam ⠚
        C beam ⠙
        D beam ⠑
        E 16th ⠯
        D beam ⠑
        E beam ⠋
        F beam ⠛
        G 16th ⠷
        G beam ⠓
        A beam ⠊
        B beam ⠚
        C 16th ⠽
        D beam ⠑
        E beam ⠋
        E beam ⠋
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        C 16th ⠽
        B 16th ⠾
        C 16th ⠽
        D 16th ⠵
        E 16th ⠯
        D 16th ⠵
        E 16th ⠯
        F 16th ⠿
        G 16th ⠷
        G 16th ⠷
        A 16th ⠮
        B 16th ⠾
        C 16th ⠽
        D 16th ⠵
        E 16th ⠯
        E 16th ⠯
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 2/4 ⠼⠃⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        G 16th ⠷
        Octave 5 ⠨
        D beam ⠑
        C beam ⠙
        B beam ⠚
        C quarter ⠹
        ===
        Measure 2, Note Grouping 1:
        Octave 4 ⠐
        G 16th ⠷
        Dot ⠄
        F 32nd ⠟
        E 16th ⠯
        D 16th ⠵
        E quarter ⠫
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 2/4 ⠼⠃⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.BassClef>
        Octave 3 ⠸
        G 16th ⠷
        E beam ⠋
        F beam ⠛
        E beam ⠋
        G 16th ⠷
        F 16th ⠿
        Rest eighth ⠭
        ===
        Measure 2, Note Grouping 1:
        F 16th ⠿
        D beam ⠑
        E beam ⠋
        D beam ⠑
        F 16th ⠿
        E 16th ⠯
        Rest eighth ⠭
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 1 sharp(s) ⠩
        Time Signature 2/4 ⠼⠃⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Rest 16th ⠍
        Octave 5 ⠨
        D beam ⠑
        C beam ⠙
        B beam ⠚
        C 16th ⠽
        D beam ⠑
        E beam ⠋
        C beam ⠙
        ===
        Measure 2, Note Grouping 1:
        B 16th ⠾
        C beam ⠙
        B beam ⠚
        A beam ⠊
        G 16th ⠷
        F 16th ⠿
        G 16th ⠷
        Rest 16th ⠍
        ===
        Measure 3, Note Grouping 1:
        Octave 5 ⠨
        G 16th ⠷
        F beam ⠛
        E beam ⠋
        D beam ⠑
        C 16th ⠽
        Rest 16th ⠍
        B 16th ⠾
        A 16th ⠮
        ===
        Measure 4, Note Grouping 1:
        G half ⠗
        ===
        ---end segment---
        '''
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
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        lastMeasure = bm.getElementsByClass(stream.Measure).last()
        lastMeasure.rightBarline = None
        for m in bm.getElementsByClass(stream.Measure):
            m.number -= 1
        m0 = bm.getElementsByClass(stream.Measure).first()
        for i in range(3):
            m0.pop(2)
        lastMeasure.notes[7].pitch.accidental = pitch.Accidental('natural')
        lastMeasure.notes[11].pitch.accidental = pitch.Accidental('natural')
        self.s = bm
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 0, Signature Grouping 1:
        Time Signature 12/8 ⠼⠁⠃⠦
        ===
        Measure 0, Note Grouping 1:
        <music21.clef.TrebleClef>
        Accidental flat ⠣
        Octave 4 ⠐
        B eighth ⠚
        ===
        Measure 1, Split Note Grouping A 1:
        Accidental flat ⠣
        E 16th ⠯
        Accidental flat ⠣
        Octave 5 ⠨
        E beam ⠋
        Accidental flat ⠣
        Octave 4 ⠐
        G beam ⠓
        Accidental flat ⠣
        Octave 5 ⠨
        G beam ⠓
        Accidental flat ⠣
        Octave 4 ⠐
        B beam ⠚
        Accidental flat ⠣
        Octave 5 ⠨
        B beam ⠚
        Accidental natural ⠡
        Octave 4 ⠐
        B 16th ⠾
        Accidental natural ⠡
        Octave 5 ⠨
        B 16th ⠾
        Accidental flat ⠣
        Octave 4 ⠐
        B 16th ⠾
        Accidental flat ⠣
        Octave 5 ⠨
        B 16th ⠾
        music hyphen ⠐
        ===
        Measure 1, Split Note Grouping B 1:
        Accidental natural ⠡
        Octave 4 ⠐
        B 16th ⠾
        Accidental natural ⠡
        Octave 5 ⠨
        B 16th ⠾
        Accidental flat ⠣
        Octave 4 ⠐
        B 16th ⠾
        Accidental flat ⠣
        Octave 5 ⠨
        B beam ⠚
        Accidental flat ⠣
        A beam ⠊
        F beam ⠛
        D beam ⠑
        B beam ⠚
        Octave 5 ⠨
        E quarter ⠫
        Dot ⠄
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 2/4 ⠼⠃⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Triplet ⠆
        Articulation accent ⠨⠦
        Octave 4 ⠐
        C eighth ⠙
        E eighth ⠋
        A eighth ⠊
        G quarter ⠳
        ===
        Measure 2, Note Grouping 1:
        Triplet ⠆
        Articulation accent ⠨⠦
        Octave 3 ⠸
        B eighth ⠚
        D eighth ⠑
        A eighth ⠊
        G quarter ⠳
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 2 flat(s) ⠣⠣
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        B quarter ⠺
        Tie ⠈⠉
        Triplet ⠆
        B eighth ⠚
        C eighth ⠙
        Octave 4 ⠐
        F eighth ⠛
        Triplet ⠆
        B eighth ⠚
        D eighth ⠑
        Octave 4 ⠐
        F eighth ⠛
        ===
        Measure 2, Note Grouping 1:
        B quarter ⠺
        Tie ⠈⠉
        Triplet ⠆
        B eighth ⠚
        C eighth ⠙
        D eighth ⠑
        Triplet ⠆
        D eighth ⠑
        C eighth ⠙
        B eighth ⠚
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 4 flat(s) ⠼⠙⠣
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Word ⠜
        Text Expression legato ⠇⠑⠛⠁⠞⠕
        Word: ⠜
        Dynamic p ⠏
        Opening bracket slur ⠰⠃
        Triplet ⠆
        Octave 5 ⠨
        C eighth ⠙
        B eighth ⠚
        A eighth ⠊
        Triplet ⠆
        A eighth ⠊
        B eighth ⠚
        C eighth ⠙
        Triplet ⠆
        B eighth ⠚
        C eighth ⠙
        B eighth ⠚
        E quarter ⠫
        Closing bracket slur ⠘⠆
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Key Signature 2 sharp(s) ⠩⠩
        Time Signature 6/8 ⠼⠋⠦
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        F quarter ⠻
        A eighth ⠊
        Octave 5 ⠨
        D eighth ⠑
        C eighth ⠙
        B eighth ⠚
        ===
        Measure 2, Note Grouping 1:
        Tuplet of 4/3rds ⠸⠲⠄
        A eighth ⠊
        G eighth ⠓
        F eighth ⠛
        A eighth ⠊
        Tuplet of 4/3rds ⠸⠲⠄
        G eighth ⠓
        F eighth ⠛
        E eighth ⠋
        G eighth ⠓
        ===
        Measure 3, Note Grouping 1:
        F eighth ⠛
        G eighth ⠓
        B eighth ⠚
        A eighth ⠊
        F eighth ⠛
        E eighth ⠋
        ===
        Measure 4, Note Grouping 1:
        D half ⠕
        Dot ⠄
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        C quarter ⠹
        E quarter ⠫
        A quarter ⠪
        G quarter ⠳
        ** Grouping x 2 **
        ===
        Measure 3, Note Grouping 1:
        Octave 3 ⠸
        B quarter ⠺
        D quarter ⠱
        A quarter ⠪
        G quarter ⠳
        ===
        Measure 4, Note Grouping 1:
        G whole ⠷
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Articulation staccato ⠦
        Octave 4 ⠐
        G quarter ⠳
        Articulation staccato ⠦
        Accidental sharp ⠩
        F quarter ⠻
        Articulation accent ⠨⠦
        Accidental natural ⠡
        F half ⠟
        ** Grouping x 2 **
        ===
        Measure 3, Note Grouping 1:
        E half ⠏
        G half ⠗
        ===
        Measure 4, Note Grouping 1:
        E whole ⠯
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        C quarter ⠹
        E quarter ⠫
        G quarter ⠳
        ** Grouping x 3 **
        ===
        Measure 4, Note Grouping 1:
        Octave 5 ⠨
        C half ⠝
        Dot ⠄
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        C quarter ⠹
        E quarter ⠫
        G quarter ⠳
        ** Grouping x 3 **
        ===
        Measure 4, Note Grouping 1:
        A half ⠎
        Dot ⠄
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 3/4 ⠼⠉⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 4 ⠐
        G quarter ⠳
        G eighth ⠓
        G eighth ⠓
        G quarter ⠳
        ** Grouping x 6 **
        ===
        Measure 7, Note Grouping 1:
        Octave 4 ⠐
        C eighth ⠙
        E eighth ⠋
        G eighth ⠓
        Octave 5 ⠨
        C eighth ⠙
        E quarter ⠫
        ** Grouping x 2 **
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 4/4 ⠼⠙⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.TrebleClef>
        Word: ⠜
        Dynamic f ⠋
        Octave 4 ⠐
        C half ⠝
        E half ⠏
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 1, Signature Grouping 1:
        Time Signature 2/4 ⠼⠃⠲
        ===
        Measure 1, Note Grouping 1:
        <music21.clef.BassClef>
        Octave 3 ⠸
        C eighth ⠙
        Rest eighth ⠭
        E eighth ⠋
        Rest eighth ⠭
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin grand segment---
        <music21.braille.segment BrailleGrandSegment>
        ===
        Measure 1 Right, Signature Grouping 1:
        Time Signature 2/4 ⠼⠃⠲

        Measure 1 Left, Signature Grouping 1:
        <music21.meter.TimeSignature 2/4>
        ====
        Measure 1 Right, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 5 ⠨
        C eighth ⠙
        Octave 4 ⠐
        G eighth ⠓
        E eighth ⠋
        G eighth ⠓

        Measure 1 Left, Note Grouping 1:
        <music21.clef.BassClef>
        Octave 3 ⠸
        C eighth ⠙
        G eighth ⠓
        Octave 4 ⠐
        C eighth ⠙
        B eighth ⠚
        ====
        Measure 2 Right, Note Grouping 1:
        Octave 4 ⠐
        F eighth ⠛
        G eighth ⠓
        E eighth ⠋
        A eighth ⠊

        Measure 2 Left, Note Grouping 1:
        Octave 3 ⠸
        A eighth ⠊
        B eighth ⠚
        C eighth ⠙
        C eighth ⠙
        ====
        Measure 3 Right, Note Grouping 1:
        Octave 4 ⠐
        G eighth ⠓
        F eighth ⠛
        E eighth ⠋
        D eighth ⠑

        Measure 3 Left, Note Grouping 1:
        Octave 3 ⠸
        B eighth ⠚
        A eighth ⠊
        G eighth ⠓
        B eighth ⠚
        ====
        Measure 4 Right, Note Grouping 1:
        Octave 4 ⠐
        E eighth ⠋
        E eighth ⠋
        D eighth ⠑
        Rest eighth ⠭

        Measure 4 Left, Note Grouping 1:
        Octave 4 ⠐
        C eighth ⠙
        C eighth ⠙
        B eighth ⠚
        G eighth ⠓
        ====
        Measure 5 Right, Note Grouping 1:
        Octave 4 ⠐
        E eighth ⠋
        D eighth ⠑
        E eighth ⠋
        G eighth ⠓

        Measure 5 Left, Note Grouping 1:
        Octave 4 ⠐
        C eighth ⠙
        Rest eighth ⠭
        Accidental flat ⠣
        B quarter ⠺
        ====
        Measure 6 Right, Note Grouping 1:
        Octave 4 ⠐
        F eighth ⠛
        G eighth ⠓
        A eighth ⠊
        F eighth ⠛

        Measure 6 Left, Note Grouping 1:
        Octave 3 ⠸
        A eighth ⠊
        Rest eighth ⠭
        C eighth ⠙
        Rest eighth ⠭
        ====
        Measure 7 Right, Note Grouping 1:
        Octave 4 ⠐
        E eighth ⠋
        G eighth ⠓
        G eighth ⠓
        F eighth ⠛

        Measure 7 Left, Note Grouping 1:
        Octave 4 ⠐
        C eighth ⠙
        Rest eighth ⠭
        B eighth ⠚
        G eighth ⠓
        ====
        Measure 8 Right, Note Grouping 1:
        Octave 4 ⠐
        E half ⠏
        Barline final ⠣⠅

        Measure 8 Left, Note Grouping 1:
        Octave 4 ⠐
        C half ⠝
        Barline final ⠣⠅
        ====

        ---end grand segment---
        '''
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
        self.e = '''
        ---begin grand segment---
        <music21.braille.segment BrailleGrandSegment>
        ===
        Measure 0 Right, Signature Grouping 1:
        Key Signature 2 flat(s) ⠣⠣
        Time Signature 3/4 ⠼⠉⠲

        Measure 0 Left, Signature Grouping 1:
        <music21.key.KeySignature of 2 flats>
        <music21.meter.TimeSignature 3/4>
        ====
        Measure 0 Right, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 5 ⠨
        D quarter ⠱

        Measure 0 Left, Note Grouping 1:
        <music21.clef.BassClef>
        Octave 3 ⠸
        B eighth ⠚
        A eighth ⠊
        ====
        Measure 1 Right, Note Grouping 1:
        Octave 5 ⠨
        D eighth ⠑
        E eighth ⠋
        D eighth ⠑
        C eighth ⠙
        B eighth ⠚
        A eighth ⠊

        Measure 1 Left, Note Grouping 1:
        Octave 3 ⠸
        G eighth ⠓
        Rest eighth ⠭
        B eighth ⠚
        Rest eighth ⠭
        D eighth ⠑
        Rest eighth ⠭
        ====
        Measure 2 Right, Note Grouping 1:
        Octave 4 ⠐
        G half ⠗
        Opening single slur ⠉
        B quarter ⠺

        Measure 2 Left, Note Grouping 1:
        Octave 3 ⠸
        G eighth ⠓
        A eighth ⠊
        B eighth ⠚
        C eighth ⠙
        D quarter ⠱
        ====

        ---end grand segment---
        '''
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
        self.e = '''
        ---begin grand segment---
        <music21.braille.segment BrailleGrandSegment>
        ===
        Measure 9 Right, Signature Grouping 1:
        Key Signature 2 sharp(s) ⠩⠩
        Time Signature 4/4 ⠼⠙⠲

        Measure 9 Left, Signature Grouping 1:
        <music21.key.KeySignature of 2 sharps>
        <music21.meter.TimeSignature 4/4>
        ====
        Measure 9 Right, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 6 ⠰
        D 16th ⠵
        B beam ⠚
        A beam ⠊
        F beam ⠛
        E quarter ⠫
        Tie ⠈⠉
        E 16th ⠯
        D beam ⠑
        Octave 4 ⠐
        A beam ⠊
        Octave 5 ⠨
        D beam ⠑
        E quarter ⠫

        Measure 9 Left, Note Grouping 1:
        <music21.clef.TrebleClef>
        Octave 5 ⠨
        D quarter ⠱
        Tie ⠈⠉
        D 16th ⠵
        C beam ⠙
        B beam ⠚
        G beam ⠓
        F quarter ⠻
        Tie ⠈⠉
        F 16th ⠿
        G beam ⠓
        B beam ⠚
        G beam ⠓
        ====
        Measure 10 Right, Note Grouping 1:
        Octave 5 ⠨
        C 16th ⠽
        B beam ⠚
        C beam ⠙
        D beam ⠑
        E 16th ⠯
        G beam ⠓
        F beam ⠛
        E beam ⠋
        F 16th ⠿
        E beam ⠋
        F beam ⠛
        G beam ⠓
        A 16th ⠮
        B beam ⠚
        C beam ⠙
        D beam ⠑

        Measure 10 Left, Note Grouping 1:
        Octave 4 ⠐
        A quarter ⠪
        C quarter ⠹
        D eighth ⠑
        D 16th ⠵
        E 16th ⠯
        F 16th ⠿
        G beam ⠓
        E beam ⠋
        F beam ⠛
        ====
        Measure 11 Right, Note Grouping 1:
        Octave 6 ⠰
        E 16th ⠯
        D beam ⠑
        C beam ⠙
        B beam ⠚
        A 16th ⠮
        G beam ⠓
        F beam ⠛
        E beam ⠋
        D half ⠕
        Barline final ⠣⠅

        Measure 11 Left, Note Grouping 1:
        Octave 5 ⠨
        G quarter ⠳
        C quarter ⠹
        Rest 16th ⠍
        A beam ⠊
        F beam ⠛
        E beam ⠋
        D quarter ⠱
        Barline final ⠣⠅
        ====

        ---end grand segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 0, Note Grouping 1:
        Descending Chord:
        Octave 5 ⠨
        G whole ⠷
        Interval 4 ⠼
        Interval 6 ⠴
        Interval 8 ⠤
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 0, Note Grouping 1:
        Ascending Chord:
        Octave 2 ⠘
        G whole ⠷
        Interval 3 ⠬
        Interval 5 ⠔
        Interval 8 ⠤
        ===
        ---end segment---
        '''
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
        self.e = '''
        ---begin grand segment---
        <music21.braille.segment BrailleGrandSegment>
        ===
        Measure 1 Right, Signature Grouping 1:
        Time Signature common ⠨⠉

        Measure 1 Left, Signature Grouping 1:
        <music21.meter.TimeSignature 4/4>
        ====
        Measure 1 Right, Note Grouping 1:
        <music21.clef.TrebleClef>
        Descending Chord:
        Octave 5 ⠨
        G whole ⠷
        Interval 6 ⠴
        Interval 4 ⠼

        Measure 1 Left, Note Grouping 1:
        <music21.clef.BassClef>
        Ascending Chord:
        Octave 2 ⠘
        G whole ⠷
        Interval 5 ⠔
        Interval 3 ⠬
        ====

        ---end grand segment---
        '''
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
        self.e = '''
        ---begin grand segment---
        <music21.braille.segment BrailleGrandSegment>
        ===
        Measure 1 Right, Signature Grouping 1:
        Time Signature common ⠨⠉

        Measure 1 Left, Signature Grouping 1:
        <music21.meter.TimeSignature 4/4>
        ====
        Measure 1 Right, Note Grouping 1:
        <music21.clef.TrebleClef>
        Descending Chord:
        Octave 5 ⠨
        E whole ⠯
        Octave 4 ⠐
        Interval 3 ⠬

        Measure 1 Left, Note Grouping 1:
        <music21.clef.BassClef>
        Ascending Chord:
        Octave 2 ⠘
        C whole ⠽
        Octave 3 ⠸
        Interval 3 ⠬
        ====

        ---end grand segment---
        '''
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
        self.e = '''
        ---begin grand segment---
        <music21.braille.segment BrailleGrandSegment>
        ===
        Measure 1 Right, Signature Grouping 1:
        Time Signature common ⠨⠉

        Measure 1 Left, Signature Grouping 1:
        <music21.meter.TimeSignature 4/4>
        ====
        Measure 1 Right, Note Grouping 1:
        <music21.clef.TrebleClef>
        Descending Chord:
        Octave 6 ⠰
        C whole ⠽
        Interval 6 ⠴
        Interval 2 ⠌

        Measure 1 Left, Note Grouping 1:
        <music21.clef.BassClef>
        Ascending Chord:
        Octave 2 ⠘
        G whole ⠷
        Interval 6 ⠴
        Octave 4 ⠐
        Interval 6 ⠴
        ====

        ---end grand segment---
        '''
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
        self.e = '''
        ---begin grand segment---
        <music21.braille.segment BrailleGrandSegment>
        ===
        Measure 1 Right, Signature Grouping 1:
        Key Signature 1 sharp(s) ⠩
        Time Signature 4/4 ⠼⠙⠲

        Measure 1 Left, Signature Grouping 1:
        <music21.key.KeySignature of 1 sharp>
        <music21.meter.TimeSignature 4/4>
        ====
        Measure 1 Right, Note Grouping 1:
        <music21.clef.TrebleClef>
        Descending Chord:
        Octave 4 ⠐
        B eighth ⠚
        Interval 3 ⠬
        C eighth ⠙
        Descending Chord:
        D eighth ⠑
        Interval 3 ⠬
        Octave 4 ⠐
        G eighth ⠓
        Descending Chord:
        Octave 5 ⠨
        E eighth ⠋
        Interval 3 ⠬
        F eighth ⠛
        Descending Chord:
        G eighth ⠓
        Interval 6 ⠴
        Octave 4 ⠐
        G eighth ⠓

        Measure 1 Left, Note Grouping 1:
        <music21.clef.BassClef>
        Ascending Chord:
        Octave 2 ⠘
        G eighth ⠓
        Interval 5 ⠔
        Octave 3 ⠸
        E eighth ⠋
        Ascending Chord:
        Octave 2 ⠘
        G eighth ⠓
        Interval 5 ⠔
        Octave 3 ⠸
        B eighth ⠚
        Ascending Chord:
        Octave 3 ⠸
        C eighth ⠙
        Interval 5 ⠔
        A eighth ⠊
        Ascending Chord:
        G eighth ⠓
        Interval 5 ⠔
        Octave 3 ⠸
        B eighth ⠚
        ====

        ---end grand segment---
        '''
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
        self.e = '''
        ---begin grand segment---
        <music21.braille.segment BrailleGrandSegment>
        ===
        Measure 1 Right, Signature Grouping 1:
        Time Signature 2/4 ⠼⠃⠲

        Measure 1 Left, Signature Grouping 1:
        <music21.meter.TimeSignature 2/4>
        ====
        Measure 1 Right, Note Grouping 1:
        <music21.clef.TrebleClef>
        Descending Chord:
        Octave 5 ⠨
        E quarter ⠫
        Interval 3 ⠬
        Descending Chord:
        D quarter ⠱
        Interval 3 ⠬

        Measure 1 Left, Note Grouping 1:
        <music21.clef.BassClef>
        Ascending Chord:
        Octave 3 ⠸
        E quarter ⠫
        Interval 3 ⠬
        Ascending Chord:
        G quarter ⠳
        Octave 3 ⠸
        Interval 8 ⠤
        ====
        Measure 2 Right, Note Grouping 1:
        Descending Chord:
        Octave 5 ⠨
        C half ⠝
        Octave 5 ⠨
        Interval 8 ⠤

        Measure 2 Left, Note Grouping 1:
        Ascending Chord:
        Octave 3 ⠸
        C half ⠝
        Interval 8 ⠤
        ====

        ---end grand segment---
        '''
        self.b = '''
        ⠀⠀⠀⠀⠀⠀⠼⠃⠲⠀⠀⠀⠀⠀⠀
        ⠁⠀⠨⠜⠨⠫⠬⠱⠬⠀⠀⠨⠝⠨⠤
        ⠀⠀⠸⠜⠸⠫⠬⠳⠸⠤⠀⠸⠝⠤⠀
        '''
# ------------------------------------------------------------------------------


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)  # , runTest='test_example10_4')

