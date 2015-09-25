# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         test.py
# Purpose:      Examples from "Introduction to Braille Music Transcription"
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    Copyright © 2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

_DOC_IGNORE_MODULE_OR_PACKAGE = True


from music21 import articulations, bar, chord, clef, dynamics, \
    expressions, key, meter, note, pitch, spanner, stream, tempo, converter
import unittest



# Introduction to Braille Music Transcription, Second Edition
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# PART ONE
# Basic Procedures and Transcribing Single-Staff Music
#
#-------------------------------------------------------------------------------
# Chapter 2: Eighth Notes, the Eighth Rest, and Other Basic Signs

def example2_1():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example2_1(), inPlace=True, suppressOctaveMarks=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠓⠭⠋⠀⠛⠭⠊⠀⠓⠭⠛⠀⠋⠭⠭⠀⠋⠭⠙⠀⠑⠭⠛⠀⠋⠭⠑⠀⠙⠭⠭⠀⠑⠭⠛
    ⠀⠀⠋⠭⠓⠀⠛⠓⠊⠀⠓⠭⠭⠀⠊⠭⠛⠀⠓⠭⠋⠀⠛⠋⠑⠀⠙⠭⠭⠣⠅
    """
    bm = converter.parse("tinynotation: 3/8 g8 r8 e8 f8 r8 a8 g8 r8 f8 e8 r8 r8 e8 r8 c8 d8 r8 f8 e8 r8 d8 c8 r8 r8 \
    d8 r8 f8 e8 r8 g8 f8 g8 a8 g8 r8 r8 a8 r8 f8 g8 r8 e8 f8 e8 d8 c8 r8 r8", makeNotation=False)
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return bm

def example2_2():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example2_2(), inPlace=True, suppressOctaveMarks=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠚⠀⠑⠀⠑⠙⠚⠑⠀⠙⠚⠊⠙⠀⠚⠊⠓⠚⠀⠊⠊⠑⠭⠀⠋⠋⠓⠋⠀⠑⠋⠓⠚⠀⠑⠙⠚⠊
    ⠀⠀⠓⠓⠓⠭⠣⠅
    """
    bm = converter.parse("tinynotation: 4/8 r8 r8 r8 d8 d8 c8 B8 d8 c8 B8 A8 c8 B8 A8 G8 B8 A8 A8 D8 r8 E8 E8 G8 E8 \
    D8 E8 G8 B8 d8 c8 B8 A8 G8 G8 G8 r8")
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    for unused_numRest in range(3):
        bm[0].pop(2)
    bm[0].padAsAnacrusis()
    for measure in bm:
        measure.number -= 1
    return bm

def example2_3():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example2_3(), inPlace=True, suppressOctaveMarks=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠃⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠋⠋⠀⠓⠊⠀⠓⠛⠀⠋⠓⠀⠛⠋⠀⠑⠛⠀⠋⠙⠀⠑⠭⠀⠋⠋⠀⠛⠛⠀⠓⠊⠀⠚⠙
    ⠀⠀⠊⠛⠀⠋⠑⠀⠙⠚⠀⠙⠭⠣⠅
    """
    bm = converter.parse("tinynotation: 2/8 e8 e8 g8 a8 g8 f8 e8 g8 f8 e8 d8 f8 e8 c8 d8 r8 e8 e8 f8 f8 g8 a8 b8 c'8 \
    a8 f8 e8 d8 c8 B8 c8 r8")
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return bm

def example2_4():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example2_4(), inPlace=True, suppressOctaveMarks=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠊⠙⠋⠀⠑⠙⠚⠀⠙⠭⠚⠀⠊⠭⠭⠀⠚⠚⠙⠀⠑⠙⠚⠀⠊⠭⠊⠀⠚⠭⠭⠣⠅⠄
    ⠀⠀⠊⠋⠊⠀⠙⠚⠊⠀⠊⠚⠙⠀⠑⠭⠭⠀⠋⠑⠙⠀⠚⠋⠚⠀⠊⠭⠊⠀⠊⠭⠭⠣⠅
    """
    bm = converter.parse("tinynotation: 3/8 A8 c8 e8 d8 c8 B8 c8 r8 B8 A8 r8 r8 B8 B8 c8 d8 c8 B8 A8 r8 A8 B8 r8 r8 \
    A8 E8 A8 c8 B8 A8 A8 B8 c8 d8 r8 r8 e8 d8 c8 B8 E8 B8 A8 r8 A8 A8 r8 r8")
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[7].rightBarline = bar.Barline('double')
    return bm

def example2_5():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example2_5(), inPlace=True, suppressOctaveMarks=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠚⠀⠑⠋⠀⠛⠙⠊⠙⠀⠑⠙⠊⠙⠀⠊⠙⠊⠓⠀⠋⠓⠛⠭⠀⠑⠋⠛⠑⠀⠙⠑⠋⠛⠀⠓⠋⠙⠋
    ⠀⠀⠛⠭⠣⠅
    """
    bm = converter.parse("tinynotation: 4/8 r8 r8 d'8 e'8 f'8 c'8 a8 c'8 d'8 c'8 a8 c'8 a8 c'8 a8 g8 e8 g8 f8 r8 \
    d8 e8 f8 d8 c8 d8 e8 f8 g8 e8 c8 e8 f8 r8")
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    for unused_numRest in range(2):
        bm[0].pop(2)
    bm[0].padAsAnacrusis()
    for measure in bm:
        measure.number -= 1
    return bm

def example2_6():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example2_6(), inPlace=True, suppressOctaveMarks=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠋⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠓⠓⠓⠓⠋⠛⠀⠊⠓⠓⠓⠭⠓⠀⠊⠊⠊⠙⠚⠊⠀⠊⠓⠓⠓⠭⠭⠀⠓⠛⠛⠛⠭⠭
    ⠀⠀⠛⠋⠋⠋⠭⠭⠀⠑⠋⠑⠓⠛⠑⠀⠙⠋⠑⠙⠭⠭⠣⠅
    """
    bm = converter.parse("tinynotation: 6/8 G8 G8 G8 G8 E8 F8 A8 G8 G8 G8 r8 G8 A8 A8 A8 c8 B8 A8 A8 G8 G8 G8 r8 r8 \
    G8 F8 F8 F8 r8 r8 F8 E8 E8 E8 r8 r8 D8 E8 D8 G8 F8 D8 C8 E8 D8 C8 r8 r8").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return bm

def example2_7():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example2_7(), inPlace=True, suppressOctaveMarks=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠋⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠋⠭⠋⠛⠭⠛⠀⠑⠭⠑⠋⠭⠋⠀⠙⠑⠋⠓⠛⠋⠀⠋⠑⠑⠑⠭⠭⠀⠙⠭⠙⠋⠭⠋
    ⠀⠀⠛⠭⠛⠊⠭⠊⠀⠓⠭⠓⠓⠊⠚⠀⠑⠙⠙⠙⠭⠭⠣⠅
    """
    bm = converter.parse("tinynotation: 6/8 e8 r8 e8 f8 r8 f8 d8 r8 d8 e8 r8 e8 c8 d8 e8 g8 f8 e8 e8 d8 d8 d8 r8 r8 \
    c8 r8 c8 e8 r8 e8 f8 r8 f8 a8 r8 a8 g8 r8 g8 g8 a8 b8 d'8 c'8 c'8 c'8 r8 r8").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return bm

#-------------------------------------------------------------------------------
# Chapter 3: Quarter Notes, the Quarter Rest, and the Dot

def example3_1():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example3_1(), inPlace=True, suppressOctaveMarks=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠱⠺⠳⠺⠀⠹⠺⠪⠧⠀⠺⠳⠫⠳⠀⠱⠺⠱⠧⠀⠫⠳⠪⠳⠀⠱⠳⠺⠱⠀⠫⠱⠹⠪
    ⠀⠀⠳⠱⠳⠧⠣⠅
    """
    bm = converter.parse("tinynotation: 4/4 d'4 b4 g4 b4 c'4 b4 a4 r4 b4 g4 e4 g4 d4 B4 d4 r4 e4 g4 a4 g4 d4 g4 b4 \
    d'4 e'4 d'4 c'4 a4 g4 d4 g4 r4")
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return bm

def example3_2():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example3_2(), inPlace=True, suppressOctaveMarks=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠪⠻⠹⠻⠀⠳⠫⠹⠫⠀⠻⠳⠪⠻⠀⠱⠫⠻⠧⠀⠳⠪⠳⠹⠀⠻⠪⠹⠱⠀⠹⠪⠳⠹
    ⠀⠀⠱⠫⠻⠧⠣⠅
    """
    bm = converter.parse("tinynotation: 4/4 A4 F4 C4 F4 G4 E4 C4 E4 F4 G4 A4 F4 D4 E4 F4 r4 G4 A4 G4 C4 F4 A4 c4 d4 \
    c4 A4 G4 C4 D4 E4 F4 r4")
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return bm

def example3_3():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example3_3(), inPlace=True, suppressOctaveMarks=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠃⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠳⠫⠀⠪⠳⠀⠻⠧⠀⠱⠧⠀⠹⠄⠙⠀⠱⠄⠑⠀⠫⠧⠀⠹⠧⠀⠳⠳⠀⠪⠺⠀⠹⠧⠀⠪⠧
    ⠀⠀⠳⠄⠓⠀⠻⠱⠀⠹⠫⠀⠹⠧⠣⠅
    """
    bm = converter.parse("tinynotation: 2/4 g4 e4 a4 g4 f4 r4 d4 r4 c4. c8 d4. d8 e4 r4 c4 r4 g4 g4 a4 b4 c'4 r4 a4 r4 \
    g4. g8 f4 d4 c4 e4 c4 r4").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return bm

def example3_4():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example3_4(), inPlace=True, suppressOctaveMarks=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠫⠙⠑⠫⠧⠀⠻⠊⠛⠫⠧⠀⠱⠋⠛⠓⠋⠹⠀⠱⠱⠳⠧⠀⠻⠋⠑⠫⠧⠀⠳⠛⠋⠻⠧
    ⠀⠀⠪⠓⠛⠋⠛⠳⠀⠻⠱⠹⠧⠣⠅
    """
    bm = converter.parse("tinynotation: 4/4 E4 C8 D8 E4 r4 F4 A8 F8 E4 r4 D4 E8 F8 G8 E8 C4 D4 D4 G4 r4 \
    F4 E8 D8 E4 r4 G4 F8 E8 F4 r4 A4 G8 F8 E8 F8 G4 F4 D4 C4 r4")
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return bm

def example3_5():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example3_5(), inPlace=True, suppressOctaveMarks=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠻⠄⠙⠱⠫⠀⠻⠄⠓⠪⠻⠀⠪⠹⠱⠹⠀⠪⠻⠳⠧⠣⠅⠄⠀⠳⠄⠋⠹⠫⠀⠻⠄⠙⠻⠪
    ⠀⠀⠳⠳⠻⠫⠀⠻⠪⠻⠧⠣⠅
    """
    bm = converter.parse("tinynotation: 4/4 f4. c8 d4 e4 f4. g8 a4 f4 a4 c'4 d'4 c'4 a4 f4 g4 r4 \
    g4. e8 c4 e4 f4. c8 f4 a4 g4 g4 f4 e4 f4 a4 f4 r4")
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[3].rightBarline = bar.Barline('double')
    return bm

def example3_6():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example3_6(), inPlace=True, suppressOctaveMarks=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠳⠓⠱⠑⠀⠳⠚⠑⠚⠓⠀⠪⠊⠊⠚⠙⠀⠺⠚⠳⠭⠀⠪⠊⠱⠑⠀⠳⠚⠪⠙⠀⠚⠙⠑⠹⠊
    ⠀⠀⠳⠓⠳⠭⠣⠅
    """
    bm = converter.parse("tinynotation: 3/4 g4 g8 d4 d8 g4 b8 d'8 b8 g8 a4 a8 a8 b8 c'8 b4 b8 g4 r8 a4 a8 d4 d8 g4 b8 a4 c'8\
    b8 c'8 d'8 c'4 a8 g4 g8 g4 r8").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return bm

#-------------------------------------------------------------------------------
# Chapter 4: Half Notes, the Half Rest, and the Tie

def example4_1():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example4_1(), inPlace=True, suppressOctaveMarks=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠝⠏⠀⠕⠟⠀⠏⠗⠀⠟⠎⠀⠗⠞⠀⠎⠝⠀⠞⠕⠀⠝⠥⠣⠅
    """
    bm = converter.parse("tinynotation: 4/4 c2 e2 d2 f2 e2 g2 f2 a2 g2 b2 a2 c'2 b2 d'2 c'2 r2").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return bm

def example4_2():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example4_2(), inPlace=True, suppressOctaveMarks=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠟⠎⠀⠗⠝⠀⠱⠹⠱⠫⠀⠟⠥⠀⠕⠟⠀⠝⠟⠀⠫⠻⠳⠪⠀⠟⠥⠣⠅
    """
    bm = converter.parse("tinynotation: 4/4 F2 A2 G2 C2 D4 C4 D4 E4 F2 r2 D2 F2 C2 F2 E4 F4 G4 A4 F2 r2").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return bm    

def example4_3():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example4_3(), inPlace=True, suppressOctaveMarks=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠝⠹⠀⠑⠙⠚⠙⠱⠀⠏⠫⠀⠛⠋⠑⠋⠻⠀⠗⠳⠀⠊⠓⠛⠓⠪⠀⠚⠊⠓⠊⠚⠑⠀⠹⠥
    ⠀⠀⠏⠫⠀⠑⠙⠚⠙⠱⠀⠝⠹⠀⠚⠊⠓⠊⠺⠀⠎⠪⠀⠓⠛⠋⠛⠳⠀⠛⠋⠑⠋⠛⠑⠀⠹⠥⠣⠅
    """
    bm = converter.parse("tinynotation: 3/4 c2 c4 d8 c8 B8 c8 d4 e2 e4 f8 e8 d8 e8 f4 g2 g4 a8 g8 f8 g8 a4 \
    b8 a8 g8 a8 b8 d'8 c'4 r2 e'2 e'4 d'8 c'8 b8 c'8 d'4 c'2 c'4 b8 a8 g8 a8 b4 a2 a4 g8 f8 e8 f8 g4 \
    f8 e8 d8 e8 f8 d8 c4 r2").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return bm

def example4_4():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> measure1 = test.example4_4()[0]
    >>> print(translate.measureToBraille(measure1, inPlace=True, suppressOctaveMarks=True))
    ⠟⠈⠉⠻⠄⠛
    """
    bm = converter.parse("tinynotation: 4/4 f2~ f4. f8").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].pop(1)
    bm[-1].rightBarline = None
    return bm

def example4_5():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> measure1 = test.example4_5()[0]
    >>> print(translate.measureToBraille(measure1, inPlace=True, suppressOctaveMarks=True))
    ⠳⠄⠈⠉⠓⠊⠓
    """
    bm = converter.parse("tinynotation: 3/4 g4.~ g8 a8 g8").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].pop(1)
    bm[-1].rightBarline = None
    return bm

def example4_6():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> bm = test.example4_6()
    >>> measure1 = bm[0]
    >>> measure2 = bm[1]
    >>> print(translate.measureToBraille(measure1, inPlace=True, suppressOctaveMarks=True))
    ⠼⠉⠲⠀⠗⠳⠈⠉
    >>> print(translate.measureToBraille(measure2, inPlace=True, suppressOctaveMarks=True))
    ⠗⠧
    """
    bm = converter.parse("tinynotation: 3/4 g2 g4~ g2 r4").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].pop(0)
    bm[-1].rightBarline = None
    return bm

def example4_7():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example4_7(), inPlace=True, suppressOctaveMarks=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠗⠄⠀⠏⠄⠀⠝⠄⠀⠏⠄⠀⠹⠱⠫⠀⠳⠻⠫⠀⠕⠄⠈⠉⠀⠕⠄⠀⠏⠫⠀⠫⠻⠳⠀⠎⠪
    ⠀⠀⠪⠳⠻⠀⠏⠻⠀⠕⠫⠀⠝⠄⠈⠉⠀⠝⠄⠣⠅
    """
    bm = converter.parse("tinynotation: 3/4 g2. e2. c2. e2. c4 d4 e4 g4 f4 e4 d2.~ d2.\
    e2 e4 e4 f4 g4 a2 a4 a4 g4 f4 e2 f4 d2 e4 c2.~ c2.").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return bm

#-------------------------------------------------------------------------------
# Chapter 5: Whole and Double Whole Notes and Rests, Measure Rests, and
# Transcriber-Added Signs

def example5_1():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example5_1(), inPlace=True, suppressOctaveMarks=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠽⠀⠮⠀⠿⠀⠮⠀⠽⠀⠵⠀⠽⠈⠉⠀⠽⠀⠵⠀⠯⠀⠿⠀⠵⠀⠽⠀⠷⠀⠿⠈⠉⠀⠿⠣⠅
    """
    bm = converter.parse("tinynotation: 4/4 c'1 a1 f1 a1 c'1 d'1 c'1~ c'1 d'1 e'1 f'1 d'1 c'1 g'1 f'1~ f'1").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return bm

def example5_2():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example5_2(), inPlace=True, suppressOctaveMarks=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠽⠀⠯⠀⠷⠀⠮⠀⠾⠀⠮⠀⠷⠈⠉⠀⠷⠀⠮⠀⠽⠀⠮⠀⠿⠀⠷⠀⠾⠀⠷⠀⠯⠀⠿⠀⠮
    ⠀⠀⠿⠀⠵⠀⠾⠀⠵⠀⠽⠈⠉⠀⠽⠣⠅
    """
    bm = converter.parse("tinynotation: 4/4 C1 E1 G1 A1 B1 A1 G1~ G1 A1 c1 A1 F1 G1 B1 G1 E1 F1 A1 F1 D1 BB1 D1 C1~ C1").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return bm

def example5_3():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example5_3(), inPlace=True, suppressOctaveMarks=True))
    ⠀⠀⠀⠀⠀⠀⠼⠉⠆⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠍⠗⠀⠗⠗⠗⠀⠳⠳⠍⠣⠅
    """
    bm = converter.parse("tinynotation: 3/2 r1 g2 g2 g2 g2 g4 g4 r1").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return bm

def example5_4():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example5_4(), inPlace=True, suppressOctaveMarks=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠏⠟⠀⠷⠀⠏⠕⠀⠽⠀⠕⠏⠀⠟⠏⠀⠵⠀⠍⠀⠝⠕⠀⠯⠀⠟⠗⠀⠮⠀⠗⠟⠀⠏⠕⠀⠽
    ⠀⠀⠍⠣⠅

    """
    bm = converter.parse("tinynotation: 4/4 E2 F2 G1 E2 D2 C1 D2 E2 F2 E2 D1 r1 \
    C2 D2 E1 F2 G2 A1 G2 F2 E2 D2 C1 r1")
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return bm

def example5_5():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example5_5(), inPlace=True, suppressOctaveMarks=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠟⠄⠀⠍⠀⠎⠄⠀⠍⠀⠻⠳⠪⠀⠹⠪⠻⠀⠳⠥⠀⠍⠀⠏⠄⠀⠍⠀⠗⠄⠀⠍⠀⠹⠱⠫
    ⠀⠀⠳⠫⠹⠀⠻⠥⠀⠍⠣⠅
    """
    bm = converter.parse("tinynotation: 3/4 F2. r2. A2. r2. F4 G4 A4 c4 A4 F4 G4 r2 r2. \
    E2. r2. G2. r2. C4 D4 E4 G4 E4 C4 F4 r2 r2.").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return bm

def example5_6():
    u"""
    NOTE: Breve note and breve rest are transcribed using method (b) on page 24.

    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example5_6(), inPlace=True, suppressOctaveMarks=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠋⠆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠮⠽⠾⠀⠝⠞⠮⠞⠝⠀⠾⠍⠘⠉⠍⠀⠷⠾⠎⠗⠀⠮⠘⠉⠮⠍⠣⠅
    """
    bm = converter.parse("tinynotation: a1 c'1 b1 c'2 b2 a1 b2 c'2 b1", makeNotation=False)
    bm.append(note.Rest(quarterLength=8.0))
    bm2 = converter.parse("tinynotation: g1 b1 a2 g2", makeNotation=False)
    bm2.append(note.Note('A4', quarterLength=8.0))
    bm2.append(note.Rest(quarterLength=4.0))
    bm.append(bm2.flat)
    bm.insert(0, meter.TimeSignature("6/2"))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return bm

# The following examples (as well as the rest of the examples in the chapter) don't work correctly yet.
#
def example5_7a():
    bm = converter.parse("tinynotation: 4/4 r1 r1 r1 r1 r1").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].pop(0)
    return bm

def example5_7b():
    bm = converter.parse("tinynotation: r1 r1 r1 r1").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].pop(0)
    return bm

def example5_7c():
    bm = converter.parse("tinynotation: r1 r1").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].pop(0)
    return bm

#-------------------------------------------------------------------------------
# Chapter 6: Accidentals

def example6_1():
    u"""
    >>> from music21.braille import basic
    >>> print(basic.noteToBraille(note.Note('C#4', quarterLength=2.0), showOctave=False))
    ⠩⠝
    >>> print(basic.noteToBraille(note.Note('Gn4', quarterLength=2.0), showOctave=False))
    ⠡⠗
    >>> print(basic.noteToBraille(note.Note('E-4', quarterLength=2.0), showOctave=False))
    ⠣⠏
    """
    pass

def example6_2():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.measureToBraille(test.example6_2()[0], inPlace=True, suppressOctaveMarks=True))
    ⠩⠳⠩⠩⠻⠗
    """
    bm = converter.parse("tinynotation: g#4 f##4 g#2").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].pop(1)
    bm[-1].rightBarline = None
    return bm

def example6_3():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.measureToBraille(test.example6_3()[0], inPlace=True, suppressOctaveMarks=True))
    ⠼⠙⠲⠀⠝⠣⠞⠈⠉
    >>> print(translate.measureToBraille(test.example6_3()[1], inPlace=True, suppressOctaveMarks=True))
    ⠺⠹⠪⠻
    """
    bm = converter.parse("tinynotation: 4/4 c'2 b-2~ b-4 c'4 a4 f4").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].pop(0)
    bm[-1].rightBarline = None
    return bm

def example6_4():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.measureToBraille(test.example6_4()[0], inPlace=True, suppressOctaveMarks=True))
    ⠼⠉⠲⠀⠡⠫⠋⠊⠙⠡⠋
    >>> print(translate.measureToBraille(test.example6_4()[1], inPlace=True, suppressOctaveMarks=True))
    ⠟⠄
    """
    bm = converter.parse("tinynotation: 3/4 e4 e8 a8 c'8 e'8 f'2.", makeNotation=False)
    bm.notes[0].pitch.accidental = pitch.Accidental()
    bm.notes[4].pitch.accidental = pitch.Accidental()
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None
    return bm

def example6_5():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.measureToBraille(test.example6_5()[0], inPlace=True, suppressOctaveMarks=True))
    ⠼⠉⠲⠀⠙⠣⠚⠊⠓⠻
    >>> print(translate.measureToBraille(test.example6_5()[1], inPlace=True, suppressOctaveMarks=True))
    ⠓⠡⠚⠹⠱
    """
    bm = converter.parse("tinynotation: 3/4 c'8 b-8 a8 g8 f4 g8 bn8 c'4 d'4").flat
    bm.notes[-3].pitch.accidental = pitch.Accidental()
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None
    return bm

def example6_6():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example6_6(), inPlace=True, suppressOctaveMarks=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠹⠩⠹⠱⠩⠱⠀⠫⠻⠩⠻⠳⠀⠩⠳⠪⠣⠺⠡⠺⠀⠝⠥⠀⠏⠣⠫⠱⠀⠹⠱⠡⠫⠹
    ⠀⠀⠺⠣⠺⠪⠡⠺⠀⠝⠥⠣⠅
    """
    bm = converter.parse("tinynotation: c4 c#4 d4 d#4 e4 f4 f#4 g4 g#4 a4 b-4 bn4 c'2 r2\
    e'2 e'-4 d'4 c'4 d'4 e'4 c'4 b4 b-4 a4 bn4 c'2 r2")
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return bm

def example6_7():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example6_7(), inPlace=True, suppressOctaveMarks=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠳⠩⠻⠡⠻⠫⠀⠣⠫⠱⠣⠱⠹⠀⠺⠣⠺⠪⠣⠪⠀⠳⠩⠻⠡⠻⠫⠀⠣⠫⠱⠣⠱⠹
    ⠀⠀⠺⠹⠱⠫⠀⠝⠥⠀⠽⠣⠅
    """
    bm = converter.parse("tinynotation: g'4 f'#4 f'4 e'4 e'-4 d'4 d'-4 c'4 b4 b-4 a4 a-4 g4 f#4 f4 e4 e-4 d4 d-4 c4 B4 c4 d4 e4 c2 r2 c1", makeNotation=False).getElementsNotOfClass(['TimeSignature'])
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-3][2].pitch.accidental.displayStatus = False
    bm[-3][3].pitch.accidental.displayStatus = False
    return bm

def example6_8():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example6_8(), inPlace=True, suppressOctaveMarks=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠹⠙⠣⠚⠣⠊⠙⠛⠣⠊⠈⠉⠀⠊⠓⠛⠓⠝⠀⠣⠱⠛⠑⠙⠙⠣⠊⠛⠀⠓⠓⠙⠙⠟⠣⠅
    """
    bm = converter.parse("tinynotation: 4/4 c'4 c'8 b-8 a-8 c'8 f'8 a'-8~ a'-8 g'8 f'8 g'8 c'2\
    d'-4 f'8 d'-8 c'8 c'8 a-8 f8 g8 g8 c8 c8 f2")
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return bm

def example6_9():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example6_9(), inPlace=True, suppressOctaveMarks=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠫⠗⠫⠀⠩⠻⠎⠻⠀⠓⠊⠺⠳⠫⠀⠩⠑⠋⠩⠻⠱⠳⠀⠹⠏⠩⠻⠀⠳⠞⠹
    ⠀⠀⠚⠊⠓⠚⠊⠓⠩⠛⠩⠑⠀⠯⠣⠅
    """
    bm = converter.parse("tinynotation: E4 G2 E4 F#4 A2 F#4 G8 A8 B4 G4 E4 D#8 E8 F#4 D#4 G4\
    C4 E2 F#4 G4 B2 c4 B8 A8 G8 B8 A8 G8 F#8 D#8 E1")
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return bm

def example6_10():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example6_10(), inPlace=True, suppressOctaveMarks=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠪⠎⠪⠈⠉⠀⠪⠧⠣⠞⠀⠹⠹⠧⠹⠈⠉⠀⠹⠧⠕⠀⠋⠫⠋⠻⠧⠀⠋⠫⠋⠱⠧
    ⠀⠀⠙⠹⠙⠣⠚⠺⠚⠀⠎⠄⠧⠣⠅
    """
    bm = converter.parse("tinynotation: a4 a2 a4~ a4 r4 b-2 c'4 c'4 r4 c'4~ c'4 r4 d'2\
    e'8 e'4 e'8 f'4 r4 e'8 e'4 e'8 d'4 r4 c'8 c'4 c'8 b-8 b-4 b-8 a2. r4")
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return bm

def example6_11():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example6_11(), inPlace=True, suppressOctaveMarks=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠪⠄⠚⠹⠺⠀⠊⠙⠋⠙⠊⠙⠫⠀⠱⠄⠛⠪⠻⠀⠑⠛⠊⠛⠑⠛⠪⠀⠩⠳⠄⠋⠎
    ⠀⠀⠺⠄⠚⠝⠀⠑⠙⠚⠊⠩⠓⠋⠩⠛⠓⠀⠎⠈⠉⠊⠩⠓⠪⠣⠅
    """
    bm = converter.parse("tinynotation: A4. B8 c4 B4 A8 c8 e8 c8 A8 c8 e4 d4. f8 a4 f4 d8 f8 a8 f8 d8 f8 a4\
    g#4. e8 a2 b4. b8 c'2 d'8 c'8 b8 a8 g#8 e8 f#8 g#8 a2~ a8 g#8 a4")
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return bm

def example6_12():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example6_12(), inPlace=True, suppressOctaveMarks=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠋⠣⠋⠑⠣⠑⠙⠊⠣⠊⠓⠀⠣⠣⠚⠣⠊⠓⠣⠓⠛⠋⠑⠙⠀⠑⠚⠣⠚⠡⠚⠙⠑⠋⠛
    ⠀⠀⠓⠩⠓⠊⠚⠹⠧⠣⠅
    """
    bm = converter.parse("tinynotation: e'8 e'-8 d'8 d'-8 c'8 a8 a-8 g8 b--8 a-8 g8 g-8 f8 e8 d8 c8 d8 B8 B-8 Bn8 c8 d8 e8 f8 g8 g#8 a8 b8 c'4 r4").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm.measure(2).notes[5].pitch.accidental.displayStatus = False
    bm.measure(2).notes[6].pitch.accidental.displayStatus = False
    bm.measure(3).notes[1].pitch.accidental.displayStatus = False
    return bm

#-------------------------------------------------------------------------------
# Chapter 7: Octave Marks

def example7_1():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example7_1(), inPlace=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠈⠽⠀⠘⠽⠀⠸⠽⠀⠐⠽⠀⠨⠽⠀⠰⠽⠀⠠⠽
    """
    bm = stream.Part()
    bm.append(note.Note('C1', quarterLength=4.0))
    bm.append(note.Note('C2', quarterLength=4.0))
    bm.append(note.Note('C3', quarterLength=4.0))
    bm.append(note.Note('C4', quarterLength=4.0))
    bm.append(note.Note('C5', quarterLength=4.0))
    bm.append(note.Note('C6', quarterLength=4.0))
    bm.append(note.Note('C7', quarterLength=4.0))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None
    return bm

def example7_2():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example7_2(), inPlace=True))
    ⠀⠀⠀⠀⠀⠜⠦⠀⠀⠀⠀
    ⠼⠁⠀⠈⠈⠮⠾⠀⠠⠠⠽
    """
    bm = stream.Part()
    bm.append(note.Note('A0', quarterLength=4.0))
    bm.append(note.Note('B0', quarterLength=4.0))
    bm.append(note.Note('C8', quarterLength=4.0))
    bm.insert(0, meter.TimeSignature('2/1'))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].pop(0)
    bm[-1].rightBarline = None
    return bm
    
def example7_3a():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.measureToBraille(test.example7_3a()[0], inPlace=True))
    ⠐⠹⠫
    """
    bm = converter.parse("tinynotation: c4 e4").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].pop(1)
    bm[-1].rightBarline = None
    return bm

def example7_3b():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.measureToBraille(test.example7_3b()[0], inPlace=True))
    ⠨⠝⠄⠪
    """
    bm = converter.parse("tinynotation: c'2. a4").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].pop(1)
    bm[-1].rightBarline = None
    return bm

def example7_4a():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.measureToBraille(test.example7_4a()[0], inPlace=True))
    ⠐⠝⠐⠎
    """
    bm = converter.parse("tinynotation: 4/4 c2 a2").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].pop(1)
    bm[-1].rightBarline = None
    return bm

def example7_4b():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.measureToBraille(test.example7_4b()[0], inPlace=True))
    ⠨⠝⠐⠏
    """
    bm = converter.parse("tinynotation: 4/4 c'2 e2").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].pop(1)
    bm[-1].rightBarline = None
    return bm

def example7_5a():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.measureToBraille(test.example7_5a()[0], inPlace=True))
    ⠸⠝⠟
    """
    bm = converter.parse("tinynotation: C2 F2").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].pop(1)
    bm[-1].rightBarline = None
    return bm

def example7_5b():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.measureToBraille(test.example7_5b()[0], inPlace=True))
    ⠐⠟⠨⠝
    """
    bm = converter.parse("tinynotation: f2 c'2").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].pop(1)
    bm[-1].rightBarline = None
    return bm

def example7_6():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> inPart = test.example7_6()
    >>> print(translate.partToBraille(inPart, inPlace=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠣⠨⠋⠋⠋⠋⠀⠑⠑⠣⠺⠀⠙⠙⠙⠙⠀⠣⠐⠋⠨⠙⠣⠺⠀⠛⠛⠨⠹⠀⠣⠚⠚⠨⠻
    ⠀⠀⠣⠨⠋⠑⠙⠣⠚⠀⠣⠨⠫⠣⠐⠫⠣⠅
    >>> inPart.measure(7).notes[3].pitch.accidental
    <accidental flat>
    >>> inPart.measure(7).notes[3].pitch.accidental.displayStatus == True
    True
    """
    bm = converter.parse("tinynotation: 4/8 e'-8 e'-8 e'-8 e'-8 d'8 d'8 b-4 c'8 c'8 c'8 c'8 e-8 c'8 b-4\
    f8 f8 c'4 b-8 b-8 f'4 e'-8 d'8 c'8 b-8 e'-4 e-4").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return bm

def example7_7():
    u"""
    "Whenever the marking “8va” occurs in print over or under certain notes,
    these notes should be transcribed according to the octaves in which they
    are actually to be played." page 42, Braille Transcription Manual

    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example7_7(), inPlace=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠐⠊⠙⠛⠙⠀⠨⠊⠙⠛⠙⠀⠰⠊⠛⠙⠑⠀⠨⠊⠛⠋⠙⠀⠟⠣⠅
    """
    bm = converter.parse("tinynotation: 4/8 a8 c'8 f'8 c'8 a8 c'8 f'8 c'8 a'8 f'8 c'8 d'8 a'8 f'8 e'8 c'8 f'2").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].pop(0)
    bm[1].transpose(value='P8', inPlace=True)
    bm[2].transpose(value='P8', inPlace=True)
    return bm

def example7_8():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example7_8(), inPlace=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠸⠝⠘⠳⠸⠫⠀⠱⠄⠙⠹⠹⠀⠸⠎⠳⠫⠀⠱⠗⠳⠀⠐⠹⠄⠚⠪⠳⠀⠪⠻⠹⠪
    ⠀⠀⠘⠳⠳⠸⠱⠳⠀⠫⠝⠄⠣⠅
    """
    bm = converter.parse("tinynotation: C2 GG4 E4 D4. C8 C4 C4 A2 G4 E4 D4 G2 G4\
    c4. B8 A4 G4 A4 F4 C4 AA4 GG4 GG4 D4 G4 E4 C2.")
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return bm

def example7_9():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example7_9(), inPlace=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠐⠫⠄⠊⠙⠋⠀⠱⠑⠙⠺⠀⠫⠄⠩⠓⠚⠨⠋⠀⠹⠙⠚⠪⠀⠊⠩⠙⠋⠊⠨⠙⠓
    ⠀⠀⠨⠛⠑⠐⠊⠨⠋⠑⠐⠛⠀⠨⠙⠚⠐⠑⠊⠩⠓⠋⠀⠎⠄⠣⠅
    """
    bm = converter.parse("tinynotation: 3/4 e4. a8 c'8 e'8 d'4 d'8 c'8 b4 e4. g#8 b8 e'8 c'4 c'8 b8 a4\
    a8 c'#8 e'8 a'8 c'#8 g'8 f'8 d'8 a8 e'8 d'8 f8 c'8 b8 d8 a8 g#8 e8 a2.")
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return bm
    
def example7_10():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> inPart = test.example7_10()
    >>> inPart.measure(2).notes[0].pitch.accidental.displayStatus == True
    True
    >>> inPart.measure(2).notes[1].pitch.accidental.displayStatus == True
    True
    >>> inPart.measure(3).notes[2].pitch.accidental.displayStatus == True
    True
    >>> inPart.measure(3).notes[4].pitch.accidental.displayStatus == True
    True
    >>> inPart.measure(3).notes[7].pitch.accidental.displayStatus == False
    True
    >>> inPart.measure(4).notes[1].pitch.accidental.displayStatus == True
    True
    >>> inPart.measure(4).notes[2].pitch.accidental.displayStatus == True
    True
    >>> inPart.measure(5).notes[2].pitch.accidental.displayStatus == True
    True
    >>> inPart.measure(7).notes[1].pitch.accidental.displayStatus == True
    True
    >>> inPart.measure(7).notes[2].pitch.accidental.displayStatus == True
    True
    >>> inPart.measure(7).notes[3].pitch.accidental.displayStatus == True
    True
    >>> inPart.measure(7).notes[6].pitch.accidental.displayStatus == False
    True


    >>> print(translate.partToBraille(inPart, inPlace=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠐⠪⠨⠫⠪⠫⠀⠩⠙⠩⠛⠋⠐⠊⠺⠨⠫⠀⠑⠐⠊⠩⠛⠨⠑⠩⠙⠊⠋⠨⠙
    ⠀⠀⠐⠚⠩⠛⠩⠓⠊⠺⠫⠀⠪⠪⠩⠨⠻⠫⠀⠱⠱⠨⠺⠪⠀⠊⠩⠨⠙⠩⠓⠩⠛⠋⠐⠋⠨⠙⠚
    ⠀⠀⠐⠎⠥⠣⠅
    """
    bm = converter.parse("tinynotation: 4/4 a4 e'4 a'4 e'4 c'#8 f'#8 e'8 a8 b4 e'4 d'8 a8 f#8 d'8 c'#8 a8 e8 c'#8 b8 f#8 g#8 a8 b4 e4\
    a4 a4 f'#4 e'4 d'4 d'4 b'4 a'4 a'8 c'#8 g'#8 f'#8 e'8 e8 c'#8 b8 a2 r2")
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return bm

def example7_11():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> inPart = test.example7_11()
    >>> inPart.measure(4).notes[0].pitch.accidental.displayStatus == True # A-3
    True
    >>> inPart.measure(4).notes[3].pitch.accidental.displayStatus == False # A-3
    True
    >>> inPart.measure(5).notes[1].pitch.accidental.displayStatus == True # E-3
    True
    >>> inPart.measure(5).notes[2].pitch.accidental.displayStatus == True # A-3
    True
    >>> inPart.measure(6).notes[0].pitch.accidental.displayStatus == True # E-3
    True
    >>> inPart.measure(6).notes[5].pitch.accidental.displayStatus == True # E-2
    True

    >>> print(translate.partToBraille(inPart, inPlace=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠋⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠚⠀⠘⠓⠀⠸⠹⠘⠓⠸⠹⠣⠋⠀⠱⠘⠓⠸⠱⠓⠀⠹⠓⠐⠹⠣⠚⠀⠣⠪⠛⠹⠸⠊
    ⠀⠀⠸⠓⠣⠋⠣⠊⠓⠙⠛⠀⠣⠋⠘⠓⠸⠑⠙⠘⠓⠣⠋⠀⠛⠸⠑⠙⠡⠚⠓⠓⠀⠹⠄⠧⠣⠅
    """
    bm = converter.parse("tinynotation: 6/8 r2 r8 GG8 C4 GG8 C4 E-8 D4 GG8 D4 G8 C4 G8 c4 B-8 A-4 F8 C4 A-8\
    G8 E-8 A-8 G8 C8 F8 E-8 GG8 D8 C8 GG8 EE-8 FF8 D8 C8 BBn8 GG8 GG8 CC4. r4")
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    for unused_numRest in range(2):
        bm[0].pop(2)
    bm[0].padAsAnacrusis()
    for measure in bm:
        measure.number -= 1
    bm.measure(7).notes[3].pitch.accidental = pitch.Accidental()
    return bm

#-------------------------------------------------------------------------------
# Chapter 8: The Music Heading: Signatures, Tempo, and Mood

def example8_1a():
    u"""
    Flats.

    >>> from music21.braille import basic
    >>> print(basic.keySigToBraille(key.KeySignature(-1)))
    ⠣
    >>> print(basic.keySigToBraille(key.KeySignature(-2)))
    ⠣⠣
    >>> print(basic.keySigToBraille(key.KeySignature(-3)))
    ⠣⠣⠣
    >>> print(basic.keySigToBraille(key.KeySignature(-4)))
    ⠼⠙⠣
    >>> print(basic.keySigToBraille(key.KeySignature(-5)))
    ⠼⠑⠣
    >>> print(basic.keySigToBraille(key.KeySignature(-6)))
    ⠼⠋⠣
    >>> print(basic.keySigToBraille(key.KeySignature(-7)))
    ⠼⠛⠣
    """
    pass
    
def example8_1b():
    u"""
    Sharps.

    >>> from music21.braille import basic
    >>> print(basic.keySigToBraille(key.KeySignature(1)))
    ⠩
    >>> print(basic.keySigToBraille(key.KeySignature(2)))
    ⠩⠩
    >>> print(basic.keySigToBraille(key.KeySignature(3)))
    ⠩⠩⠩
    >>> print(basic.keySigToBraille(key.KeySignature(4)))
    ⠼⠙⠩
    >>> print(basic.keySigToBraille(key.KeySignature(5)))
    ⠼⠑⠩
    >>> print(basic.keySigToBraille(key.KeySignature(6)))
    ⠼⠋⠩
    >>> print(basic.keySigToBraille(key.KeySignature(7)))
    ⠼⠛⠩
    """
    pass
    
def example8_2():
    u"""
    Time signatures with two numbers.

    >>> from music21.braille import basic
    >>> print(basic.timeSigToBraille(meter.TimeSignature('6/8')))
    ⠼⠋⠦
    >>> print(basic.timeSigToBraille(meter.TimeSignature('2/4')))
    ⠼⠃⠲
    >>> print(basic.timeSigToBraille(meter.TimeSignature('12/8')))
    ⠼⠁⠃⠦
    >>> print(basic.timeSigToBraille(meter.TimeSignature('2/2')))
    ⠼⠃⠆
    """
    pass

def example8_3():
    u"""
    Time signatures with one number. Not currently supported.
    """
    pass

def example8_4():
    u"""
    Combined time signatures. Not currently supported.
    """
    pass

def example8_5():
    u"""
    Common/cut time signatures.

    >>> from music21.braille import basic
    >>> print(basic.timeSigToBraille(meter.TimeSignature('common')))
    ⠨⠉
    >>> print(basic.timeSigToBraille(meter.TimeSignature('cut')))
    ⠸⠉
    """
    pass

def example8_6():
    u"""
    Combined key and time signatures.

    >>> from music21.braille import basic
    >>> print(basic.transcribeSignatures(key.KeySignature(1), meter.TimeSignature('2/4')))
    ⠩⠼⠃⠲
    >>> print(basic.transcribeSignatures(key.KeySignature(-3), meter.TimeSignature('3/4')))
    ⠣⠣⠣⠼⠉⠲
    >>> print(basic.transcribeSignatures(key.KeySignature(4), meter.TimeSignature('3/8')))
    ⠼⠙⠩⠼⠉⠦
    >>> print(basic.transcribeSignatures(key.KeySignature(3), meter.TimeSignature('3/8')))
    ⠩⠩⠩⠼⠉⠦


    The following two cases are identical, having no key signature is equivalent to having a key signature with no sharps or flats.


    >>> print(basic.transcribeSignatures(None, meter.TimeSignature('4/4')))
    ⠼⠙⠲
    >>> print(basic.transcribeSignatures(key.KeySignature(0), meter.TimeSignature('4/4')))
    ⠼⠙⠲


    >>> print(basic.transcribeSignatures(key.KeySignature(-1), meter.TimeSignature('3/4')))
    ⠣⠼⠉⠲
    >>> print(basic.transcribeSignatures(key.KeySignature(0), meter.TimeSignature('6/8')))
    ⠼⠋⠦
    """
    pass

def example8_7a():
    u"""
    >>> from music21.braille import basic
    >>> print(basic.transcribeHeading(key.KeySignature(-4), meter.TimeSignature("4/4"), tempo.TempoText("Andante"), None))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠁⠝⠙⠁⠝⠞⠑⠲⠀⠼⠙⠣⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    >>> print(basic.transcribeHeading(key.KeySignature(3), meter.TimeSignature("3/8"), tempo.TempoText("Con moto"), None))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠉⠕⠝⠀⠍⠕⠞⠕⠲⠀⠩⠩⠩⠼⠉⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    >>> print(basic.transcribeHeading(None, meter.TimeSignature("4/4"), tempo.TempoText("Andante cantabile"), None))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠠⠁⠝⠙⠁⠝⠞⠑⠀⠉⠁⠝⠞⠁⠃⠊⠇⠑⠲⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀
    >>> print(basic.transcribeHeading(key.KeySignature(2), meter.TimeSignature("7/8"), tempo.TempoText("Very brightly"), None))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠧⠑⠗⠽⠀⠃⠗⠊⠛⠓⠞⠇⠽⠲⠀⠩⠩⠼⠛⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    """
    pass
    
def example8_8():
    u"""
    Metronome Markings

    >>> from music21.braille import basic
    >>> print(basic.metronomeMarkToBraille(tempo.MetronomeMark(number = 80, referent = note.Note(type='half'))))
    ⠝⠶⠼⠓⠚
    """
    pass

def example8_9():
    u"""
    >>> from music21.braille import basic
    >>> print(basic.transcribeHeading(key.KeySignature(-3), meter.TimeSignature("12/8"), tempo.TempoText("Andante"),
    ...   tempo.MetronomeMark(number=132, referent=note.Note(type='eighth'))))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠠⠁⠝⠙⠁⠝⠞⠑⠲⠀⠙⠶⠼⠁⠉⠃⠀⠣⠣⠣⠼⠁⠃⠦⠀⠀⠀⠀⠀⠀⠀⠀
    """
    pass
    
def example8_10():
    u"""
    >>> from music21.braille import basic
    >>> print(basic.transcribeHeading(key.KeySignature(-5), meter.TimeSignature("6/8"),
    ... tempo.TempoText("Lento assai, cantante e tranquillo"),
    ... tempo.MetronomeMark(number=52, referent=note.Note(quarterLength=1.5))))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠇⠑⠝⠞⠕⠀⠁⠎⠎⠁⠊⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠁⠝⠞⠁⠝⠞⠑⠀⠑⠀⠞⠗⠁⠝⠟⠥⠊⠇⠇⠕⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠹⠄⠶⠼⠑⠃⠀⠼⠑⠣⠼⠋⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    """
    pass

def drill8_1():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.drill8_1(), inPlace=True))
    ⠀⠀⠀⠀⠀⠠⠁⠝⠙⠁⠝⠞⠑⠀⠍⠁⠑⠎⠞⠕⠎⠕⠲⠀⠹⠶⠼⠊⠃⠀⠨⠉⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠐⠎⠓⠛⠫⠀⠱⠫⠛⠓⠪⠀⠳⠨⠙⠚⠪⠳⠀⠻⠄⠋⠕⠀⠹⠫⠪⠨⠫⠀⠫⠱⠙⠚⠪
    ⠀⠀⠨⠪⠓⠛⠫⠱⠀⠹⠊⠚⠝⠣⠅
    """
    bm = converter.parse("tinynotation: 4/4 a2 g8 f8 e4 d4 e4 f8 g8 a4 g4 c'8 b8 a4 g4 f4. e8 d2\
    c4 e4 a4 e'4 e'4 d'4 c'8 b8 a4 a'4 g'8 f'8 e'4 d'4 c'4 a8 b8 c'2", makeNotation=False)
    bm.replace(bm.getElementsByClass('TimeSignature')[0], meter.TimeSignature('c'))
    bm.insert(0, tempo.TempoText("Andante maestoso"))
    bm.insert(0, tempo.MetronomeMark(number=92, referent=note.Note(type='quarter')))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return bm

def drill8_2():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.drill8_2(), inPlace=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠠⠊⠝⠀⠎⠞⠗⠊⠉⠞⠀⠞⠊⠍⠑⠲⠀⠣⠣⠣⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠸⠋⠭⠘⠚⠭⠸⠋⠭⠀⠡⠫⠻⠩⠻⠀⠓⠭⠑⠭⠓⠭⠀⠪⠳⠻⠀⠋⠭⠙⠭⠊⠭
    ⠀⠀⠡⠘⠪⠺⠡⠺⠀⠙⠑⠭⠋⠭⠘⠚⠀⠸⠋⠡⠋⠭⠛⠭⠩⠛⠀⠓⠑⠭⠓⠭⠊⠀⠊⠓⠭⠛⠭⠋
    ⠀⠀⠸⠑⠙⠺⠈⠺⠀⠘⠏⠄⠣⠅
    """
    bm = converter.parse("tinynotation: 3/4 E-8 r8 BB-8 r8 E-8 r8 En4 F4 F#4 G8 r8 D8 r8 G8 r8 A-4 G4 F4\
    E-8 r8 C8 r8 AA-8 r8 AAn4 BB-4 BBn4 C8 D8 r8 E-8 r8 BB-8 E-8 En8 r8 F8 r8 F#8\
    G8 D8 r8 G8 r8 A-8 A-8 G8 r8 F8 r8 E-8 D8 C8 BB-4 BB-4 EE-2.").flat
    bm.insert(0, key.KeySignature(-3))
    bm.insert(0, tempo.TempoText("In strict time"))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-2].notes[-1].transpose('P-8', inPlace=True)
    bm.measure(7).notes[-1].pitch.accidental.displayStatus = False # flat not strictly necessary
    bm.measure(11).notes[-1].pitch.accidental.displayStatus = False # flat not necessary (never?)
    return bm

def drill8_3():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.drill8_3(), inPlace=True))
    ⠀⠀⠀⠀⠀⠀⠀⠠⠉⠕⠝⠀⠙⠑⠇⠊⠉⠁⠞⠑⠵⠵⠁⠲⠀⠼⠑⠩⠼⠋⠦⠀⠀⠀⠀⠀⠀⠀
    ⠼⠚⠀⠨⠑⠙⠀⠺⠄⠈⠉⠚⠑⠓⠀⠳⠄⠻⠭⠀⠫⠄⠈⠉⠋⠑⠐⠓⠀⠨⠱⠙⠱⠭
    ⠀⠀⠐⠊⠓⠊⠚⠊⠚⠀⠙⠑⠋⠛⠓⠊⠀⠚⠛⠑⠓⠋⠐⠚⠀⠨⠻⠑⠋⠑⠙⠀⠚⠛⠨⠑⠺⠛
    ⠀⠀⠐⠑⠛⠚⠹⠊⠀⠞⠄⠈⠉⠀⠺⠄⠭⠣⠅
    """
    bm = converter.parse("tinynotation: 6/8 r2 d'#8 c'#8 b4.~ b8 d'#8 g'#8 g'#4. f'#4 r8 e'4.~ e'8 d'#8 g#8 d'#4 c'#8 d'#4 r8 a#8 g#8 a#8 b8 a#8 b8\
    c'#8 d'#8 e'8 f'#8 g'#8 a'#8 b'8 f'#8 d'#8 g'#8 e'8 b8 f'#4 d'#8 e'8 d'#8 c'#8 b8 f#8 d'#8 b4 f#8 d#8 f#8 b8 c'#4 a#8 b2.~ b4. r8").flat
    bm.insert(0, key.KeySignature(5))
    bm.insert(0, tempo.TempoText("Con delicatezza"))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].pop(4)
    bm[0].padAsAnacrusis()
    for measure in bm:
        measure.number -= 1
    return bm

def drill8_4():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.drill8_4(), inPlace=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠛⠗⠁⠵⠊⠕⠎⠕⠲⠀⠣⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠸⠎⠄⠄⠓⠀⠟⠫⠱⠀⠫⠄⠛⠳⠫⠀⠩⠝⠱⠧⠀⠘⠎⠄⠄⠡⠚⠀⠩⠹⠄⠑⠫⠳
    ⠀⠀⠸⠻⠳⠪⠻⠀⠕⠄⠄⠭⠣⠅
    """
    bm = converter.parse(
            "tinynotation: 4/4 A2.. G8 F2 E4 D4 E4. F8 G4 E4 C#2 D4 r4 " + 
            "AA2.. BBn8 C#4. D8 E4 G4 F4 G4 A4 F4 D2.. r8").flat
    bm.insert(0, key.KeySignature(-1))
    bm.insert(0, tempo.TempoText("Grazioso"))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return bm

def drill8_5():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.drill8_5(), inPlace=True))
    ⠀⠀⠀⠀⠀⠀⠀⠠⠃⠑⠝⠀⠍⠁⠗⠉⠁⠞⠕⠲⠀⠝⠶⠼⠁⠁⠃⠀⠣⠣⠸⠉⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠚⠀⠨⠻⠫⠀⠕⠺⠳⠀⠨⠏⠹⠐⠻⠀⠨⠟⠫⠱⠀⠝⠐⠻⠻⠀⠗⠻⠳⠀⠎⠨⠱⠹⠀⠺⠪⠺⠹
    ⠀⠀⠨⠕⠫⠻⠀⠗⠫⠹⠀⠟⠱⠺⠀⠨⠏⠹⠐⠻⠀⠨⠕⠺⠺⠀⠝⠺⠹⠀⠱⠺⠹⠱⠀⠺⠹⠺⠪
    ⠀⠀⠐⠞⠣⠅
    """
    bm = converter.parse("tinynotation: 2/2 r2 f'4 e'-4 d'2 b-4 g4 e'-2 c'4 " + 
                         "f4 f'2 e'-4 d'4 c'2 f4 f4 g2 f4 g4 " +
                         "a2 d'4 c'4 b-4 a4 b-4 c'4 d'2 e'-4 f'4 " + 
                         "g'2 e'-4 c'4 f'2 d'4 b-4 e'-2 c'4 f4 d'2 b-4 b-4 c'2 " + 
                         "b-4 c'4 d'4 b-4 c'4 d'4 b-4 c'4 b-4 a4 b-2", makeNotation=False)
    bm.replace(bm.getElementsByClass('TimeSignature')[0], meter.TimeSignature('cut'))
    bm.insert(0, key.KeySignature(-2))
    bm.insert(0, tempo.TempoText("Ben marcato"))
    bm.insert(0, tempo.MetronomeMark(number=112, referent=note.Note(type='half')))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].pop(5)
    bm[0].padAsAnacrusis()
    for measure in bm:
        measure.number -= 1
    return bm

#-------------------------------------------------------------------------------
# Chapter 9: Fingering

def example9_1():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example9_1(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠣⠼⠃⠲⠀⠀⠀
    ⠐⠪⠂⠳⠇⠀⠻⠄⠃⠙⠁
    >>> print(translate.partToBraille(test.example9_1(), inPlace=True, showFirstMeasureNumber=False, debug=True))
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
    """
    bm = converter.parse("tinynotation: 2/4 a4 g f4. c8").flat
    bm.insert(0, key.KeySignature(-1))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None
    bm[0].notes[0].fingering = '4'
    bm[0].notes[1].fingering = '3'
    bm[1].notes[0].fingering = '2'
    bm[1].notes[1].fingering = '1'
    return bm

def example9_2():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example9_2(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠀⠀⠣⠣⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀
    ⠨⠻⠂⠋⠇⠑⠃⠙⠁⠚⠃⠈⠉⠀⠺⠭⠊⠙⠚
    """
    bm = converter.parse("tinynotation: 3/4 f'4 e'-8 d' c' b-~ b-4 r8 a c' b-").flat
    bm.insert(0, key.KeySignature(-2))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None 
    bm[0].notes[0].fingering = '4'
    bm[0].notes[1].fingering = '3'
    bm[0].notes[2].fingering = '2'
    bm[0].notes[3].fingering = '1'
    bm[0].notes[4].fingering = '2'
    return bm
    
def example9_3():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example9_3(), showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠼⠋⠦⠀⠀⠀⠀⠀
    ⠐⠝⠄⠁⠈⠉⠀⠹⠄⠻⠃⠓
    """
    bm = converter.parse("tinynotation: 6/8 c2.~ c4. f4 g8").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None 
    bm[0].notes[0].fingering = '1'
    bm[1].notes[1].fingering = '2'
    return bm

def example9_4a():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example9_4a(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠩⠩⠼⠉⠲⠀
    ⠐⠕⠃⠉⠁⠸⠻
    """
    bm = converter.parse("tinynotation: 3/4 d2 F#4").flat
    bm.insert(0, key.KeySignature(2))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None 
    bm[0].notes[0].fingering = '2-1'
    return bm

def example9_4b():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example9_4b(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠼⠉⠲⠀⠀
    ⠐⠝⠇⠉⠁⠳
    """
    bm = converter.parse("tinynotation: 3/4 c2 g4").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None 
    bm[0].notes[0].fingering = '3-1'
    return bm

def example9_5a():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example9_5a(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠼⠃⠲⠀⠀⠀
    ⠐⠙⠋⠓⠨⠙⠅⠂
    """
    bm = converter.parse("tinynotation: 2/4 c8 e g c'").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None 
    bm[0].notes[3].fingering = '5|4'
    return bm

def example9_5b():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example9_5b(), inPlace=True, showFirstMeasureNumber=False, upperFirstInNoteFingering=False))
    ⠀⠀⠀⠀⠀⠼⠋⠦⠀⠀⠀⠀⠀⠀
    ⠐⠑⠃⠇⠙⠁⠃⠑⠃⠇⠫⠄⠇⠂
    """
    bm = converter.parse("tinynotation: 6/8 d8 c d e4.").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None 
    bm[0].notes[0].fingering = '3|2'
    bm[0].notes[1].fingering = '2|1'
    bm[0].notes[2].fingering = '3|2'
    bm[0].notes[3].fingering = '4|3'
    return bm
  
def example9_6():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example9_6(), inPlace=True, showFirstMeasureNumber=False, upperFirstInNoteFingering=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠩⠩⠼⠃⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠐⠻⠃⠁⠪⠁⠃⠀⠨⠱⠠⠂⠻⠂⠅⠀⠻⠂⠇⠫⠇⠃
    >>> print(translate.partToBraille(test.example9_6(), inPlace=True, showFirstMeasureNumber=False, upperFirstInNoteFingering=False))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠩⠩⠼⠃⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠐⠻⠁⠃⠪⠃⠁⠀⠨⠱⠂⠠⠻⠅⠂⠀⠻⠇⠂⠫⠃⠇
    """
    bm = converter.parse("tinynotation: 2/4 f#4 a d' f'# f'# e'").flat
    bm.insert(0, key.KeySignature(2))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None 
    bm[0].notes[0].fingering = '2,1'
    bm[0].notes[1].fingering = '1,2'
    bm[1].notes[0].fingering = 'x,4'
    bm[1].notes[1].fingering = '4,5'
    bm[2].notes[0].fingering = '4,3'
    bm[2].notes[1].fingering = '3,2'
    return bm

def drill9_1():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.drill9_1(), inPlace=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠁⠇⠇⠑⠛⠗⠑⠞⠞⠕⠲⠀⠣⠣⠣⠼⠋⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠚⠀⠐⠓⠃⠊⠀⠺⠄⠈⠉⠚⠓⠁⠚⠀⠱⠄⠅⠈⠉⠑⠙⠚⠀⠪⠓⠫⠃⠛⠁⠀⠳⠄⠃⠭⠊⠚
    ⠀⠀⠨⠹⠄⠈⠉⠙⠊⠁⠙⠃⠀⠫⠄⠇⠈⠉⠋⠑⠃⠛⠂⠀⠋⠑⠙⠚⠂⠊⠛⠃⠁
    ⠀⠀⠐⠫⠄⠁⠃⠈⠉⠋⠣⠅
    """
    bm = converter.parse("tinynotation: 6/8 r2 g8 a- b-4.~ b-8 g b- d'4.~ d'8 c' " + 
                         "b- a-4 g8 e-4 f8 g4. r8 a- b- " +
                         "c'4.~ c'8 a- c' e'-4.~ e'-8 d' f' e'- d' c' b- a- f e-4.~ e-8").flat
    bm.insert(0, tempo.TempoText("Allegretto"))
    bm.insert(0, key.KeySignature(-3))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].pop(4)
    bm[0].padAsAnacrusis()
    for m in bm:
        m.number -= 1
    bm[0].notes[0].fingering = '2'
    bm[1].notes[2].fingering = '1'
    bm[2].notes[0].fingering = '5'
    bm[3].notes[2].fingering = '2'
    bm[3].notes[3].fingering = '1'
    bm[4].notes[0].fingering = '2'
    bm[5].notes[2].fingering = '1'
    bm[5].notes[3].fingering = '2'
    bm[6].notes[0].fingering = '3'
    bm[6].notes[2].fingering = '2'
    bm[6].notes[3].fingering = '4'
    bm[7].notes[3].fingering = '4'
    bm[7].notes[5].fingering = '2|1'
    bm[8].notes[0].fingering = '1|2'
    return bm

def drill9_2():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.drill9_2(), inPlace=True))
    ⠀⠀⠀⠀⠀⠀⠠⠁⠙⠁⠛⠊⠕⠀⠑⠀⠍⠕⠇⠞⠕⠀⠇⠑⠛⠁⠞⠕⠲⠀⠨⠉⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠐⠎⠃⠈⠉⠊⠓⠊⠨⠑⠅⠂⠀⠙⠂⠇⠚⠇⠁⠨⠋⠅⠂⠑⠂⠇⠙⠇⠃⠛⠅⠫⠂⠈⠉
    ⠀⠀⠨⠋⠛⠋⠐⠚⠁⠙⠃⠑⠇⠐⠊⠁⠚⠀⠙⠐⠓⠁⠎⠃⠉⠇⠈⠉⠊⠛⠁
    ⠀⠀⠐⠓⠨⠙⠂⠚⠇⠊⠃⠨⠑⠂⠙⠇⠚⠃⠨⠋⠂⠀⠕⠇⠈⠉⠑⠓⠅⠛⠙
    ⠀⠀⠨⠑⠋⠐⠚⠁⠙⠃⠱⠇⠐⠊⠁⠓⠃⠀⠎⠄⠁⠈⠉⠊⠭⠣⠅
    """
    bm = converter.parse("tinynotation: 4/4 a2~ a8 g a d' c' b e' d' c' f' " + 
                         "e'4~ e'8 f' e' b c' d' a b c' g a2~ a8 f " +
                         "g c' b a d' c' b e' d'2~ d'8 g' f' c' d' e' b c' d'4 a8 g a2.~ a8 r", 
                         makeNotation=False)
    bm.replace(bm.getElementsByClass('TimeSignature')[0], meter.TimeSignature('c'))

    bm.insert(0, tempo.TempoText("Adagio e molto legato"))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].notes[0].fingering = '2'
    bm[0].notes[4].fingering = '5|4'
    bm[1].notes[0].fingering = '4|3'
    bm[1].notes[1].fingering = '3|1'
    bm[1].notes[2].fingering = '5|4'
    bm[1].notes[3].fingering = '4|3'
    bm[1].notes[4].fingering = '3|2'
    bm[1].notes[5].fingering = '5'
    bm[1].notes[6].fingering = '4'
    bm[2].notes[3].fingering = '1'
    bm[2].notes[4].fingering = '2'
    bm[2].notes[5].fingering = '3'
    bm[2].notes[6].fingering = '1'
    bm[3].notes[1].fingering = '1'
    bm[3].notes[2].fingering = '2-3'
    bm[3].notes[4].fingering = '1'
    bm[4].notes[1].fingering = '4'
    bm[4].notes[2].fingering = '3'
    bm[4].notes[3].fingering = '2'
    bm[4].notes[4].fingering = '4'
    bm[4].notes[5].fingering = '3'
    bm[4].notes[6].fingering = '2'
    bm[4].notes[7].fingering = '4'
    bm[5].notes[0].fingering = '3'
    bm[5].notes[2].fingering = '5'
    bm[6].notes[2].fingering = '1'
    bm[6].notes[3].fingering = '2'
    bm[6].notes[4].fingering = '3'
    bm[6].notes[5].fingering = '1'
    bm[6].notes[6].fingering = '2'
    bm[7].notes[0].fingering = '1'
    return bm

def drill9_3():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.drill9_3(), inPlace=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠍⠕⠙⠑⠗⠁⠞⠕⠲⠀⠩⠩⠼⠃⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠘⠺⠇⠂⠙⠃⠇⠑⠁⠃⠀⠋⠂⠁⠛⠠⠇⠓⠠⠁⠊⠁⠃⠀⠺⠇⠁⠙⠠⠇⠑⠁⠃
    ⠀⠀⠐⠋⠇⠁⠛⠠⠃⠓⠁⠁⠛⠃⠃⠀⠫⠇⠁⠑⠁⠃⠙⠠⠇⠀⠚⠠⠁⠊⠁⠃⠓⠠⠇⠛⠠⠂
    ⠀⠀⠸⠫⠂⠁⠑⠁⠄⠙⠃⠄⠀⠑⠁⠁⠙⠃⠃⠚⠁⠇⠩⠊⠃⠂⠀⠞⠁⠇⠣⠅
    """
    bm = converter.parse("tinynotation: 2/4 BB4 C#8 D E F# G A B4 c#8 d e f# g f# e4 d8 c# " +
                         "B A G F# E4 D8 C# D C# BB AA# BB2").flat
    bm.insert(0, key.KeySignature(2))
    bm.insert(0, tempo.TempoText("Moderato"))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[2].insert(0, clef.TrebleClef())
    bm[5].insert(0, clef.BassClef())
    # measure 1 fingerings
    bm[0].notes[0].fingering = '3,4'
    bm[0].notes[1].fingering = '2,3'
    bm[0].notes[2].fingering = '1,2'
    # measure 2 fingerings
    bm[1].notes[0].fingering = '4,1'
    bm[1].notes[1].fingering = 'x,3'
    bm[1].notes[2].fingering = 'x,1'
    bm[1].notes[3].fingering = '1,2'
    # measure 3 fingerings
    bm[2].notes[0].fingering = '3,1'
    bm[2].notes[1].fingering = 'x,3'
    bm[2].notes[2].fingering = '1,2'
    # measure 4 fingerings    
    bm[3].notes[0].fingering = '3,1'
    bm[3].notes[1].fingering = 'x,2'
    bm[3].notes[2].fingering = '1,1'
    bm[3].notes[3].fingering = '2,2'
    # measure 5 fingerings
    bm[4].notes[0].fingering = '3,1'
    bm[4].notes[1].fingering = '1,2'
    bm[4].notes[2].fingering = 'x,3'
    # measure 6 fingerings
    bm[5].notes[0].fingering = 'x,1'
    bm[5].notes[1].fingering = '1,2'
    bm[5].notes[2].fingering = 'x,3'
    bm[5].notes[3].fingering = 'x,4'
    # measure 7 fingerings
    bm[6].notes[0].fingering = '4,1'
    bm[6].notes[1].fingering = '1,x'
    bm[6].notes[2].fingering = '2,x'
    # measure 8 fingerings
    bm[7].notes[0].fingering = '1,1'
    bm[7].notes[1].fingering = '2,2'
    bm[7].notes[2].fingering = '1,3'
    bm[7].notes[3].fingering = '2,4'
    # measure 9 fingerings
    bm[8].notes[0].fingering = '1,3'
    return bm
    
def drill9_4():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.drill9_4(), inPlace=True))
    ⠀⠀⠀⠀⠀⠀⠀⠠⠝⠕⠞⠀⠞⠕⠕⠀⠋⠁⠎⠞⠲⠀⠹⠶⠼⠁⠚⠚⠀⠩⠼⠑⠦⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠸⠋⠩⠑⠃⠋⠛⠃⠑⠀⠺⠸⠫⠇⠓⠀⠓⠃⠛⠇⠓⠊⠚⠃⠀⠺⠁⠘⠺⠅⠚⠁
    ⠀⠀⠘⠑⠓⠚⠁⠓⠅⠚⠂⠀⠸⠫⠃⠳⠁⠛⠀⠋⠘⠚⠸⠓⠋⠘⠚⠀⠸⠫⠁⠘⠫⠅⠋⠂
    ⠀⠀⠘⠫⠇⠭⠋⠃⠋⠁⠀⠑⠇⠋⠃⠋⠇⠋⠃⠋⠁⠀⠋⠇⠋⠃⠫⠇⠋⠃⠀⠫⠁⠈⠉⠋⠭⠭⠣⠅
    """
    bm = converter.parse("tinynotation: 5/8 E8 D# E F# D# BB4 E G8 G F# G A B " + 
                         "B4 BB BB8 DD GG BB GG BB E4 G F#8 " +
                         "E BB G E BB E4 EE EE8 EE4 r8 EE8 EE DD " + 
                         "EE EE EE EE EE EE EE4 EE8 EE4~ EE8 r8 r").flat
    bm.insert(0, key.KeySignature(1))
    bm.insert(0, tempo.MetronomeMark(number = 100, referent = note.Note(type='quarter')))
    bm.insert(0, tempo.TempoText("Not too fast"))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    # measure 1 fingerings
    bm[0].notes[1].fingering = '2'
    bm[0].notes[3].fingering = '2'
    # measure 2 fingerings
    bm[1].notes[1].fingering = '3'
    # measure 3 fingerings
    bm[2].notes[0].fingering = '2'
    bm[2].notes[1].fingering = '3'
    bm[2].notes[4].fingering = '2'
    # measure 4 fingerings    
    bm[3].notes[0].fingering = '1'
    bm[3].notes[1].fingering = '5'
    bm[3].notes[2].fingering = '1'
    # measure 5 fingerings
    bm[4].notes[2].fingering = '1'
    bm[4].notes[3].fingering = '5'
    bm[4].notes[4].fingering = '4'
    # measure 6 fingerings
    bm[5].notes[0].fingering = '2'
    bm[5].notes[1].fingering = '1'
    # measure 8 fingerings
    bm[7].notes[0].fingering = '1'
    bm[7].notes[1].fingering = '5'
    bm[7].notes[2].fingering = '4'
    # measure 9 fingerings
    bm[8].notes[0].fingering = '3'
    bm[8].notes[1].fingering = '2'
    bm[8].notes[2].fingering = '1'
    # measure 10 fingerings
    bm[9].notes[0].fingering = '3'
    bm[9].notes[1].fingering = '2'
    bm[9].notes[2].fingering = '3'
    bm[9].notes[3].fingering = '2'
    bm[9].notes[4].fingering = '1'
    # measure 11 fingerings
    bm[10].notes[0].fingering = '3'
    bm[10].notes[1].fingering = '2'
    bm[10].notes[2].fingering = '3'
    bm[10].notes[3].fingering = '2'
    # measure 12 fingerings
    bm[11].notes[0].fingering = '1'
    return bm

def drill9_5():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.drill9_5(), inPlace=True))
    ⠀⠠⠇⠊⠛⠓⠞⠇⠽⠂⠀⠁⠇⠍⠕⠎⠞⠀⠊⠝⠀⠕⠝⠑⠲⠀⠣⠼⠉⠲⠀
    ⠼⠁⠀⠐⠛⠅⠸⠊⠁⠩⠓⠃⠊⠁⠙⠊⠀⠐⠓⠸⠚⠃⠊⠁⠚⠃⠑⠇⠚⠃
    ⠀⠀⠐⠓⠙⠡⠚⠙⠐⠊⠐⠙⠁⠀⠣⠐⠚⠐⠙⠁⠡⠚⠃⠙⠇⠣⠚⠃⠙⠇
    ⠀⠀⠸⠊⠁⠙⠃⠐⠊⠅⠐⠙⠁⠡⠚⠃⠑⠇⠀⠙⠁⠐⠊⠂⠩⠓⠇⠊⠂⠙⠊
    ⠀⠀⠐⠙⠐⠚⠂⠊⠇⠚⠙⠚⠀⠊⠨⠑⠅⠙⠂⠊⠇⠓⠃⠙⠁⠀⠟⠄⠃⠣⠅
    """
    bm = converter.parse(
            "tinynotation: 3/4 f8 A G# A c A g B- A B- d B- g c Bn c a c b- c Bn c B- c " + 
            "A c a c Bn d c a g# a c' a c b- a b- c' b- a d' c' a g c f2.").flat
    bm.insert(0, key.KeySignature(-1))
    bm.insert(0, tempo.TempoText("Lightly, almost in one"))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[1].notes[0].pitch.accidental.displayStatus = False
    # measure 1 fingerings
    bm[0].notes[0].fingering = '5'
    bm[0].notes[1].fingering = '1'
    bm[0].notes[2].fingering = '2'
    bm[0].notes[3].fingering = '1'
    # measure 2 fingerings
    bm[1].notes[1].fingering = '2'
    bm[1].notes[2].fingering = '1'
    bm[1].notes[3].fingering = '2'
    bm[1].notes[4].fingering = '3'
    bm[1].notes[5].fingering = '2'
    # measure 3 fingerings
    bm[2].notes[5].fingering = '1'
    # measure 4 fingerings    
    bm[3].notes[1].fingering = '1'
    bm[3].notes[2].fingering = '2'
    bm[3].notes[3].fingering = '3'
    bm[3].notes[4].fingering = '2'
    bm[3].notes[5].fingering = '3'
    # measure 5 fingerings
    bm[4].notes[0].fingering = '1'
    bm[4].notes[1].fingering = '2'
    bm[4].notes[2].fingering = '5'
    bm[4].notes[3].fingering = '1'
    bm[4].notes[4].fingering = '2'
    bm[4].notes[5].fingering = '3'
    # measure 6 fingerings
    bm[5].notes[0].fingering = '1'
    bm[5].notes[1].fingering = '4'
    bm[5].notes[2].fingering = '3'
    bm[5].notes[3].fingering = '4'
    # measure 7 fingerings
    bm[6].notes[1].fingering = '4'
    bm[6].notes[2].fingering = '3'
    # measure 8 fingerings
    bm[7].notes[1].fingering = '5'
    bm[7].notes[2].fingering = '4'
    bm[7].notes[3].fingering = '3'
    bm[7].notes[4].fingering = '2'
    bm[7].notes[5].fingering = '1'
    # measure 12 fingerings
    bm[8].notes[0].fingering = '2'
    return bm

#-------------------------------------------------------------------------------
# Chapter 10: Changes of Signature; the Braille Music Hyphen, Asterisk, and 
# Parenthesis; Clef Signs

def example10_1():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example10_1(), inPlace=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠣⠼⠋⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠐⠻⠨⠙⠑⠙⠚⠀⠼⠃⠲⠀⠐⠪⠳⠣⠅⠄⠀⠡⠣⠣⠣⠼⠋⠦⠀⠐⠋⠨⠋⠑⠫⠐⠓
    ⠀⠀⠼⠉⠲⠀⠐⠪⠳⠻⠣⠅⠄⠀⠡⠡⠡⠀⠐⠓⠛⠋⠑⠙⠚⠀⠝⠄⠣⠅
    """
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
    return bm

def example10_2():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example10_2(), inPlace=True, dummyRestLength = 5, maxLineLength = 20))
    ⠀⠀⠀⠀⠀⠀⠀⠣⠼⠙⠲⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠄⠄⠄⠄⠄⠀⠐⠋⠩⠛⠩⠓⠊⠐
    ⠀⠀⠐⠚⠡⠓⠋⠙⠀⠛⠊⠓⠙⠐⠎⠣⠅
    """
    bm = converter.parse("tinynotation: 4/4 e8 f# g# a b- gn e c f a g c a2").flat
    bm.insert(0, key.KeySignature(-1))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[1].notesAndRests[0].pitch.accidental.displayStatus = False
    return bm

def example10_3():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example10_3(), inPlace=True, dummyRestLength = 10, maxLineLength = 21))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠼⠋⠦⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠀⠐⠋⠩⠛⠩⠓⠐
    ⠀⠀⠐⠊⠚⠡⠓⠀⠋⠙⠛⠊⠓⠙⠀⠐⠎⠄⠣⠅
    """
    bm = converter.parse("tinynotation: 6/8 e8 f# g# a b- g e c f a g c a2.").flat
    bm.insert(0, key.KeySignature(-1))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[1].notesAndRests[2].pitch.accidental.displayStatus = False
    return bm

def example10_4():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example10_4(), inPlace=True, dummyRestLength = 10))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠼⠁⠃⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠀⠐⠏⠄⠈⠉⠋⠩⠛⠩⠓⠊⠚⠡⠓⠀⠙⠑⠋⠻⠄⠈⠉⠛⠐
    ⠀⠀⠐⠋⠛⠓⠛⠋⠀⠟⠄⠣⠅
    """
    bm = converter.parse("tinynotation: 12/8 e2.~ e8 f# g# a b- gn c d e f4.~ f8 e f g f e f2.").flat
    bm.insert(0, key.KeySignature(-1))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[1].notesAndRests[3].pitch.accidental.displayStatus = False
    return bm
    
def example10_5():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example10_5(), inPlace=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠣⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠐⠳⠄⠛⠫⠀⠸⠺⠐⠺⠳⠀⠟⠣⠅⠄⠐⠀⠐⠳⠀⠨⠫⠄⠑⠹⠀⠱⠐⠳⠡⠺
    ⠀⠀⠨⠱⠹⠣⠅⠄⠐⠀⠼⠙⠣⠀⠨⠹⠀⠪⠄⠓⠻⠀⠹⠨⠹⠡⠐⠫⠀⠟⠄⠣⠅
    """
    bm = converter.parse("tinynotation: 3/4 g4. f8 e-4 B-4 b-4 g4 f2 g4 e'-4. d'8 c'4 d'4 g4 bn4 " +
                         "d'4 c'4 c'4 a-4. g8 f4 c4 c'4 en4 f2.").flat
    bm.insert(0, key.KeySignature(-3))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[2].insert(1, bar.Barline('double'))
    bm[5].insert(2, key.KeySignature(-4))
    bm[5].insert(2, bar.Barline('double'))
    return bm

def example10_6():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example10_6(), inPlace=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠩⠩⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠐⠪⠨⠪⠈⠉⠊⠓⠛⠋⠀⠻⠫⠈⠉⠋⠑⠙⠚⠀⠱⠹⠈⠉⠙⠚⠊⠚⠀⠝⠣⠅⠄
    ⠀⠀⠭⠨⠊⠓⠛⠀⠋⠑⠙⠚⠊⠚⠙⠚⠀⠎⠄⠧⠣⠅
    """
    bm = converter.parse("tinynotation: 4/4 a4 a'~ a'8 g'# f'# e' f'#4 " + 
                         "e'~ e'8 d' c'# b d'4 c'#~ c'#8 b a b " +
                         "c'#2 r8 a'8 g'# f'# e' d' c'# b a b c'# b a2. r4", makeNotation=False)
    bm.insert(0, key.KeySignature(3))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[3].insert(2.0, bar.Barline('double'))
    return bm

def example10_9():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example10_9(), inPlace=True, showClefSigns=False))
    ⠀⠀⠀⠀⠀⠀⠀⠣⠣⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠘⠺⠸⠻⠺⠐⠻⠀⠺⠱⠹⠪⠀⠾⠣⠅
    >>> print(translate.partToBraille(test.example10_9(), inPlace=True, showClefSigns=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠜⠼⠇⠘⠺⠸⠻⠺⠜⠌⠇⠐⠻⠀⠺⠱⠹⠪⠀⠾⠣⠅
    """
    bm = converter.parse("tinynotation: 4/4 BB-4 F B- f b- d' c' a b-1", makeNotation=False)
    bm.insert(0, key.KeySignature(-2))
    bm.insert(0, clef.BassClef())
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].insert(3.0, clef.TrebleClef())
    return bm

def example10_10():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example10_10(), inPlace=True, showClefSigns=False))
    ⠀⠀⠀⠀⠀⠀⠩⠩⠩⠼⠋⠦⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠐⠊⠋⠊⠚⠙⠑⠀⠋⠛⠓⠪⠄⠣⠅
    >>> print(translate.partToBraille(test.example10_10(), inPlace=True, showClefSigns=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠩⠩⠼⠋⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠜⠬⠇⠐⠊⠋⠊⠚⠙⠑⠀⠜⠌⠇⠨⠋⠛⠓⠪⠄⠣⠅
    """
    bm = converter.parse("tinynotation: 6/8 a8 e a b c'# d' e' f'# g'# a'4.", makeNotation=False)
    bm.insert(0, key.KeySignature(3))
    bm.insert(0, clef.AltoClef())
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[1].insert(0.0, clef.TrebleClef())
    return bm

def drill10_2():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.drill10_2(), inPlace=True, cancelOutgoingKeySig=False))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠩⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠐⠱⠻⠪⠻⠀⠑⠋⠛⠓⠎⠣⠅⠄⠀⠣⠣⠣⠀⠐⠫⠳⠺⠳⠀⠋⠛⠓⠊⠞⠣⠅⠄⠀⠼⠙⠩
    ⠀⠀⠐⠫⠳⠺⠳⠀⠋⠛⠓⠊⠞⠣⠅⠄⠀⠣⠀⠐⠻⠪⠹⠪⠀⠛⠓⠊⠚⠝⠣⠅⠄⠀⠼⠋⠣
    ⠀⠀⠐⠳⠺⠱⠺⠀⠓⠊⠚⠙⠕⠣⠅⠄⠀⠨⠱⠺⠳⠺⠀⠑⠙⠚⠊⠗⠣⠅⠄
    """
    bm = converter.parse("""tinynotation: 4/4 d4 f# a f# d8 e f# g a2 e-4 g b- g e-8 f g a- b-2
        e4 g# b g# e8 f# g# a b2 f4 a c' a f8 g a b- c'2
        g-4 b- d'- b- g-8 a- b- c'- d'-2 d'4 b g b d'8 c' b a g2""", makeNotation=False)
    bm.insert(0.0, key.KeySignature(2))
    bm.insert(8.0, key.KeySignature(-3))
    bm.insert(16.0, key.KeySignature(4))
    bm.insert(24.0, key.KeySignature(-1))
    bm.insert(32.0, key.KeySignature(-6))
    bm.insert(40.0, key.KeySignature(0))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[1].rightBarline = bar.Barline('double')
    bm[3].rightBarline = bar.Barline('double')
    bm[5].rightBarline = bar.Barline('double')
    bm[7].rightBarline = bar.Barline('double')
    bm[9].rightBarline = bar.Barline('double')
    bm[11].rightBarline = bar.Barline('double')
    return bm

def drill10_4():
    # TODO: 4/4 as c symbol.
    bm = converter.parse("""tinynotation: 4/4 r2. AA4 DD r d2~ d8 f e d c#4 
        A B-2~ B-8 d cn B- A4 F D E 
        F G8 A B-4 c#8 Bn c# d d e f a a4 g8 e c# g f d Bn f e c# A e d cn B- d 
        c4 B-8 A G4 F8 E D4 AA DD""")
    bm.insert(0, key.KeySignature(-1))
    bm.insert(0, clef.BassClef())
    bm.insert(0, tempo.TempoText("Con brio"))
    bm.insert(25.0, clef.TrebleClef())
    bm.insert(32.0, clef.BassClef())
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].pop(4)
    bm[0].padAsAnacrusis()
    for m in bm:
        m.number -= 1
    return bm

#-------------------------------------------------------------------------------
# Chapter 11: Segments for Single-Line Instrumental Music, Format for the 
# Beginning of a Composition or Movement

def example11_1():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example11_1(), inPlace=True, segmentBreaks = [(9, 0.0)]))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠩⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠸⠱⠋⠛⠓⠊⠀⠺⠪⠓⠛⠀⠋⠑⠙⠑⠋⠛⠀⠳⠪⠧⠀⠺⠙⠑⠋⠛⠀⠫⠱⠙⠚
    ⠀⠀⠐⠙⠋⠑⠙⠚⠩⠊⠀⠞⠧
    ⠼⠊⠀⠐⠻⠑⠙⠺⠀⠐⠫⠙⠚⠩⠪⠀⠐⠱⠚⠡⠊⠩⠳⠀⠎⠧⠀⠪⠓⠛⠋⠑⠀⠹⠱⠋⠛
    ⠀⠀⠸⠓⠊⠚⠊⠓⠛⠀⠫⠱⠧⠣⠅
    """
    bm = converter.parse("""tinynotation: 3/4 D4 E8 F#8 G8 A8 B4 A4 G8 F#8 
        E8 D8 C#8 D8 E8 F#8 G4 A4 r4 B4 c#8 d8 e8 f#8 e4 d4 c#8 B8 
        c#8 e8 d8 c#8 B8 A#8 B2 r4 f#4 d8 c#8 B4 e4 c#8 B8 A#4 d4 B8 An8 G#4 A2 r4 
        A4 G8 F#8 E8 D8 C#4 D4 E8 F#8 G8 A8 B8 A8 G8 F#8 E4 D4 r4""").flat
    bm.insert(0, key.KeySignature(2))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return bm

def example11_2():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example11_2(), inPlace=True, segmentBreaks = [(8, 3.0)]))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠣⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠚⠀⠐⠺⠀⠳⠫⠱⠫⠀⠗⠻⠫⠀⠪⠳⠨⠹⠄⠙⠀⠞⠄⠺⠀⠨⠫⠐⠺⠪⠄⠓⠀⠗⠻⠨⠹
    ⠀⠀⠨⠹⠐⠻⠪⠄⠑⠀⠏⠄⠐
    ⠼⠓⠄⠀⠐⠳⠀⠳⠄⠛⠻⠻⠀⠎⠳⠺⠀⠺⠡⠪⠪⠹⠀⠞⠄⠺⠀⠨⠫⠐⠺⠪⠳⠀⠗⠻⠨⠹
    ⠀⠀⠨⠹⠧⠐⠻⠧⠀⠎⠄⠱⠀⠏⠄⠣⠅
    """
    bm = converter.parse("""tinynotation: 4/4 r2. b-4 g e- d e- g2 f4 
        e- a- g c'4. c'8 b-2. b-4 e'-4 b- a-4. g8 
        g2 f4 c' c' f a-4. d8 e-2. g4 g4. f8 f4 f a-2 g4 b- b- an an c' 
        b-2. b-4 e'- b- a- g g2 f4 c' c' r f r a-2. d4 e-2.""").flat
    bm.insert(0, key.KeySignature(-3))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    for m in bm:
        m.number -= 1
    bm[0].pop(3)
    bm[0].padAsAnacrusis()
    return bm

#-------------------------------------------------------------------------------
# Chapter 12: Slurs (Phrasing)

def example12_1():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example12_1(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠐⠳⠄⠅⠉⠛⠫⠉⠱⠀⠳⠉⠻⠉⠫⠧⠀⠻⠃⠉⠳⠁⠉⠪⠉⠺⠀⠹⠉⠱⠉⠹⠧
    """
    bm = converter.parse(
            "tinynotation: 4/4 g4. f8 e4 d4 g4 f4 e4 r4 f4 g4 a4 b4 c'4 d'4 c'4 r4").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].notes[0].fingering = '5'
    bm[2].notes[0].fingering = '2'
    bm[2].notes[1].fingering = '1'
    bm[0].append(spanner.Slur(bm[0].notes[0], bm[0].notes[1]))
    bm[0].append(spanner.Slur(bm[0].notes[2], bm[0].notes[3]))
    bm[1].append(spanner.Slur(bm[1].notes[0], bm[1].notes[2]))
    bm[2].append(spanner.Slur(bm[2].notes[0], bm[2].notes[3]))
    bm[3].append(spanner.Slur(bm[3].notes[0], bm[3].notes[2]))
    bm[3].rightBarline = None
    return bm

def example12_2():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example12_2(), inPlace=True, showFirstMeasureNumber=False, slurLongPhraseWithBrackets=False))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠐⠳⠄⠅⠉⠉⠛⠫⠱⠀⠳⠻⠉⠫⠧⠀⠻⠁⠉⠉⠳⠪⠺⠀⠹⠁⠱⠉⠹⠧
    """
    bm = converter.parse("tinynotation: 4/4 g4. f8 e4 d g f e r f g a b c' d' c' r").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[1].append(spanner.Slur(bm[0].notes[0], bm[1].notes[2]))
    bm[3].append(spanner.Slur(bm[2].notes[0], bm[3].notes[2]))
    bm[0].notes[0].fingering = '5'
    bm[2].notes[0].fingering = '1'
    bm[3].notes[0].fingering = '1'
    bm[3].rightBarline = None
    return bm
  
def example12_3():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example12_3(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠰⠃⠣⠐⠫⠄⠁⠛⠳⠫⠀⠻⠳⠣⠪⠘⠆⠧⠀⠰⠃⠳⠁⠳⠣⠨⠫⠂⠱⠀⠝⠄⠘⠆⠧
    """
    bm = converter.parse("tinynotation: 4/4 e-4. f8 g4 e- f g a- r g g e'- d' c'2. r4").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[1].append(spanner.Slur(bm[0].notes[0], bm[1].notes[2]))
    bm[3].append(spanner.Slur(bm[2].notes[0], bm[3].notes[0]))
    bm[0].notes[0].fingering = '1'
    bm[2].notes[0].fingering = '1'
    bm[2].notes[2].fingering = '4'
    bm[3].rightBarline = None
    return bm

def example12_4():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example12_4(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠀⠀⠼⠁⠃⠦⠀⠀⠀⠀⠀⠀
    ⠰⠃⠨⠫⠄⠉⠹⠉⠓⠳⠄⠉⠻⠉⠋⠘⠆
    """
    bm = converter.parse("tinynotation: 12/8 e'4. c'4 g'8 g'4. f'4 e'8").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].append(spanner.Slur(bm[0].notes[0], bm[0].notes[2]))
    bm[0].append(spanner.Slur(bm[0].notes[3], bm[0].notes[5]))
    bm[0].append(spanner.Slur(bm[0].notes[0], bm[0].notes[5]))
    bm[0].rightBarline = None
    return bm

def example12_5():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example12_5(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠩⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠰⠃⠐⠎⠺⠀⠊⠨⠛⠋⠑⠙⠚⠀⠰⠃⠘⠆⠪⠚⠙⠑⠋⠀⠟⠄⠘⠆
    >>> print(translate.partToBraille(test.example12_5(), inPlace=True, showFirstMeasureNumber=False, slurLongPhraseWithBrackets=False))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠩⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠐⠎⠉⠉⠺⠀⠊⠨⠛⠋⠑⠙⠚⠉⠀⠪⠉⠉⠚⠙⠑⠋⠉⠀⠟⠄
    """
    bm = converter.parse("tinynotation: 3/4 a2 b4 a8 f'# e' d' c'# b a4 b8 c'# d' e' f'#2.").flat
    bm.insert(0, key.KeySignature(2))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[2].append(spanner.Slur(bm[0].notes[0], bm[2].notes[0]))
    bm[3].append(spanner.Slur(bm[2].notes[0], bm[3].notes[0])) 
    bm[3].rightBarline = None
    return bm

def example12_6():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example12_6(), inPlace=True, showFirstMeasureNumber=False, showShortSlursAndTiesTogether=False))
    ⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀
    ⠨⠝⠈⠉⠙⠉⠑⠀⠕⠈⠉⠑⠉⠋
    >>> print(translate.partToBraille(test.example12_6(), inPlace=True, showFirstMeasureNumber=False, showShortSlursAndTiesTogether=True))
    ⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀
    ⠨⠝⠉⠈⠉⠙⠉⠑⠀⠕⠉⠈⠉⠑⠉⠋
    """
    bm = converter.parse("tinynotation: 3/4 c'2~ c'8 d' d'2~ d'8 e'").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].append(spanner.Slur(bm[0].notes[0], bm[0].notes[2]))
    bm[1].append(spanner.Slur(bm[1].notes[0], bm[1].notes[2])) 
    bm[1].rightBarline = None
    return bm
  
def example12_7():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example12_7(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠀⠣⠼⠉⠲⠀⠀⠀⠀⠀⠀
    ⠰⠃⠨⠟⠄⠈⠉⠀⠛⠙⠑⠙⠚⠊⠘⠆
    >>> print(translate.partToBraille(test.example12_7(), inPlace=True, showFirstMeasureNumber=False, slurLongPhraseWithBrackets=False))
    ⠀⠀⠀⠀⠀⠀⠣⠼⠉⠲⠀⠀⠀⠀⠀
    ⠨⠟⠄⠈⠉⠀⠛⠉⠉⠙⠑⠙⠚⠉⠊
    """
    bm = converter.parse("tinynotation: 3/4 f'2.~ f'8 c' d' c' b- a").flat
    bm.insert(0, key.KeySignature(-1))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].append(spanner.Slur(bm[0].notes[0], bm[-1].notes[-1]))
    bm[-1].rightBarline = None
    return bm

def example12_8():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example12_8(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠀⠣⠼⠉⠲⠀⠀⠀⠀⠀⠀
    ⠨⠟⠄⠈⠉⠀⠰⠃⠛⠙⠑⠙⠚⠊⠘⠆
    >>> print(translate.partToBraille(test.example12_8(), inPlace=True, showFirstMeasureNumber=False, slurLongPhraseWithBrackets=False))
    ⠀⠀⠀⠀⠀⠀⠣⠼⠉⠲⠀⠀⠀⠀⠀
    ⠨⠟⠄⠈⠉⠀⠛⠉⠉⠙⠑⠙⠚⠉⠊
    """
    bm = converter.parse("tinynotation: 3/4 f'2.~ f'8 c' d' c' b- a").flat
    bm.insert(0, key.KeySignature(-1))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].append(spanner.Slur(bm[-1].notes[0], bm[-1].notes[-1]))
    bm[-1].rightBarline = None
    return bm

def example12_9():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example12_9(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠰⠃⠨⠋⠛⠓⠛⠋⠑⠀⠝⠄⠈⠉⠀⠹⠘⠆⠧⠧
    >>> print(translate.partToBraille(test.example12_9(), inPlace=True, showFirstMeasureNumber=False, slurLongPhraseWithBrackets=False))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀
    ⠨⠋⠉⠉⠛⠓⠛⠋⠑⠉⠀⠝⠄⠈⠉⠀⠹⠧⠧
    """
    bm = converter.parse("tinynotation: 3/4 e'8 f' g' f' e' d' c'2.~ c'4 r r").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].append(spanner.Slur(bm[0].notes[0], bm[-1].notes[-1]))
    bm[-1].rightBarline = None
    return bm

def example12_10():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example12_10(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠰⠃⠨⠋⠛⠓⠛⠋⠑⠀⠝⠄⠘⠆⠈⠉⠀⠹⠧⠧
    >>> print(translate.partToBraille(test.example12_10(), inPlace=True, showFirstMeasureNumber=False, slurLongPhraseWithBrackets=False))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀
    ⠨⠋⠉⠉⠛⠓⠛⠋⠑⠉⠀⠝⠄⠈⠉⠀⠹⠧⠧
    """
    bm = converter.parse("tinynotation: 3/4 e'8 f' g' f' e' d' c'2.~ c'4 r r").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[1].append(spanner.Slur(bm[0].notes[0], bm[1].notes[0]))
    bm[-1].rightBarline = None
    return bm

def example12_11():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example12_11(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀
    ⠐⠹⠇⠉⠹⠃⠉⠹⠁⠉⠹⠇
    """
    bm = converter.parse("tinynotation: 4/4 c4 c c c").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].append(spanner.Slur(bm[0].notes[0], bm[0].notes[1]))
    bm[0].append(spanner.Slur(bm[0].notes[1], bm[0].notes[2]))
    bm[0].append(spanner.Slur(bm[0].notes[2], bm[0].notes[3]))
    bm[0].notes[0].fingering = '3'
    bm[0].notes[1].fingering = '2'
    bm[0].notes[2].fingering = '1'
    bm[0].notes[3].fingering = '3'
    bm[-1].rightBarline = None
    return bm

#-------------------------------------------------------------------------------
# Chapter 13: Words, Abbreviations, Letters, and Phrases of Expression

def example13_1():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example13_1(), inPlace=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠜⠙⠕⠇⠉⠑⠐⠟⠫⠀⠫⠱⠜⠏⠐⠹⠀⠐⠪⠄⠚⠪⠀⠳⠜⠍⠋⠐⠙⠑⠋⠛
    ⠀⠀⠐⠳⠜⠗⠊⠞⠄⠐⠻⠫⠀⠟⠄⠣⠅
    """
    bm = converter.parse(
            "tinynotation: 3/4 f2 e4 e4 d4 c4 a4. b-8 a4 g4 c8 d8 e8 f8 g4 f4 e4 f2.").flat
    bm.insert(0, key.KeySignature(-1))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].insert(0.0, expressions.TextExpression("dolce"))
    bm[1].insert(2.0, dynamics.Dynamic('p'))
    bm[3].insert(1.0, dynamics.Dynamic('mf'))
    bm[4].insert(1.0, expressions.TextExpression("rit."))
    return bm

def example13_2():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example13_2(), inPlace=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠜⠋⠄⠩⠨⠱⠉⠋⠭⠜⠏⠰⠃⠐⠺⠳⠀⠪⠻⠳⠘⠆⠜⠗⠊⠞⠄⠡⠐⠛⠉⠋
    ⠀⠀⠐⠑⠉⠋⠉⠡⠛⠉⠋⠜⠍⠕⠗⠑⠝⠙⠕⠄⠩⠐⠛⠉⠓⠛⠉⠩⠓⠀⠩⠮⠜⠏⠏⠏⠄⠣⠅
    """
    bm = converter.parse(
            "tinynotation: 4/4 d'#4 e'8 r b4 g a f# g fn8 e d e fn e f# g f# g# a#1").flat
    bm.insert(0, key.KeySignature(1))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].append(spanner.Slur(bm[0].notes[0], bm[0].notes[1]))
    bm[1].append(spanner.Slur(bm[0].notes[2], bm[1].notes[2]))
    bm[1].append(spanner.Slur(bm[1].notes[3], bm[1].notes[4]))
    bm[2].append(spanner.Slur(bm[2].notes[0], bm[2].notes[3]))
    bm[2].append(spanner.Slur(bm[2].notes[4], bm[2].notes[5]))
    bm[2].append(spanner.Slur(bm[2].notes[6], bm[2].notes[7]))
    bm[0].insert(0.0, dynamics.Dynamic('f'))
    bm[0].insert(2.0, dynamics.Dynamic('p'))
    bm[1].insert(3.0, expressions.TextExpression("rit."))
    bm[2].insert(2.0, expressions.TextExpression("morendo"))
    bm[3].insert(4.0, dynamics.Dynamic('ppp'))
    return bm
    
def example13_3():
    # Problem: How to plug in wedges into music21?
    bm = converter.parse("tinynotation: a1 a1 a1 a1", "c").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None
    e0 = expressions.TextExpression('cresc.')
    e1 = expressions.TextExpression('decresc.')
    bm[0].insert(0.0, e0)
    bm[1].insert(0.0, e1)
    #w1 = dynamics.Wedge(type = 'crescendo')
    return bm

def example13_9():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example13_9(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀
    ⠜⠗⠥⠎⠓⠖⠜⠋⠐⠓⠊⠚⠙⠑⠋⠛⠓
    """
    bm = converter.parse("tinynotation: 4/4 g8 a b c' d' e' f' g'").flat
    bm.insert(0.0, dynamics.Dynamic('f'))
    bm.insert(0.0, expressions.TextExpression('rush!'))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None
    return bm

def example13_10():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example13_10(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀
    ⠜⠶⠍⠁⠗⠉⠄⠶⠜⠋⠐⠹⠹⠫⠹
    """
    bm = converter.parse("tinynotation: 4/4 c4 c e c").flat
    bm.insert(0.0, dynamics.Dynamic('f'))
    bm.insert(0.0, expressions.TextExpression('(marc.)'))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None
    return bm

def example13_11():
    # Problem: How to braille the pp properly?
    bm = converter.parse("tinynotation: 4/4 b-2 r f e- d1 r B-").flat
    bm.insert(0.0, key.KeySignature(-2))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].insert(0.0, dynamics.Dynamic('f'))
    bm[0].insert(2.0, dynamics.Dynamic('pp'))
    bm[1].append(spanner.Slur(bm[1].notes[0], bm[1].notes[1]))
    bm[3].insert(0.0, expressions.TextExpression('rit.'))
    return bm

def example13_14():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example13_14(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠩⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠨⠫⠫⠻⠀⠗⠄⠀⠜⠙⠊⠍⠄⠀⠑⠀⠗⠁⠇⠇⠄⠜⠀⠨⠛⠑⠐⠊⠨⠑⠋⠙⠀⠕⠄
    """
    bm = converter.parse("tinynotation: 3/4 e'4 e' f'# g'2. f'#8 d' a d' e' c'# d'2.").flat
    bm.insert(0.0, key.KeySignature(2))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[2].insert(0.0, expressions.TextExpression('dim. e rall.'))
    bm[-1].rightBarline = None
    return bm

def example13_15():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example13_15(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠼⠃⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠨⠑⠙⠚⠊⠀⠗⠀⠜⠉⠁⠇⠍⠂⠀⠎⠑⠗⠑⠝⠑⠜⠀⠐⠺⠄⠊⠀⠳⠄⠚⠀⠪⠄⠓⠀⠟
    """
    bm = converter.parse("tinynotation: 2/4 d'8 c' b- a g2 b-4. a8 g4. b-8 a4. g8 f2").flat
    bm.insert(0.0, key.KeySignature(-2))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[2].insert(0.0, expressions.TextExpression('calm, serene'))
    bm[-1].rightBarline = None
    return bm

def example13_16():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example13_16(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠼⠃⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠨⠑⠙⠚⠊⠀⠗⠀⠜⠎⠑⠓⠗⠀⠗⠥⠓⠊⠛⠜⠀⠐⠺⠄⠊⠀⠳⠄⠚⠀⠪⠄⠓⠀⠟
    """
    bm = converter.parse("tinynotation: 2/4 d'8 c' b- a g2 b-4. a8 g4. b-8 a4. g8 f2").flat
    bm.insert(0.0, key.KeySignature(-2))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[2].insert(0.0, expressions.TextExpression('Sehr ruhig'))
    bm[-1].rightBarline = None
    return bm

def example13_17():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example13_17(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠐⠳⠧⠐⠀⠜⠗⠊⠞⠄⠀⠑⠀⠙⠊⠍⠄⠜⠀⠰⠃⠨⠳⠀⠳⠫⠹⠀⠻⠱⠺⠀⠝⠄⠘⠆
    """
    bm = converter.parse("tinynotation: 3/4 g4 r g' g' e' c' f' d' b c'2.").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].insert(2.0, expressions.TextExpression('rit. e dim.'))
    bm[-1].append(spanner.Slur(bm[0].notes[1], bm[-1].notes[0]))
    bm[-1].rightBarline = None
    return bm

def example13_18():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example13_18(), inPlace=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠘⠻⠐⠀⠜⠎⠏⠑⠑⠙⠊⠝⠛⠀⠥⠏⠜⠀⠘⠓⠊⠚⠙⠀⠱⠚⠙⠐
    ⠀⠀⠜⠎⠇⠕⠺⠊⠝⠛⠸⠑⠋⠀⠻⠋⠑⠹
    """
    bm = converter.parse("tinynotation: 3/4 FF4 GG8 AA BB- C D4 BB-8 C D E F4 E8 D C4").flat
    bm.insert(0.0, key.KeySignature(-1))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].insert(1.0, expressions.TextExpression("speeding up"))
    bm[1].insert(2.0, expressions.TextExpression("slowing"))
    bm[-1].rightBarline = None
    return bm

def example13_19():
    bm = converter.parse("tinynotation: 3/4 c'8 d' c' b- a g a2.").flat
    bm.insert(0.0, key.KeySignature(-1))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].insert(0.0, dynamics.Dynamic("pp"))
    bm[0].insert(0.0, expressions.TextExpression("very sweetly"))
    bm[-1].rightBarline = None
    return bm

def example13_26():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example13_26(), inPlace=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠩⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠙⠑⠀⠰⠃⠐⠏⠻⠳⠀⠎⠜⠗⠁⠇⠇⠄⠐⠺⠪⠀⠗⠻⠫⠀⠕⠄⠘⠆⠧⠣⠅⠄⠀⠡⠡⠣⠣
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠏⠗⠑⠎⠞⠕⠲⠀⠣⠣⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠙⠊⠀⠜⠋⠋⠐⠺⠑⠛⠺⠛⠑⠀⠺⠨⠋⠓⠺⠓⠋⠀⠐⠺⠨⠋⠛⠪⠛⠋⠀⠐⠺⠑⠛⠺⠧
    """
    bm = converter.parse("tinynotation: 4/4 e2 f#4 g a2 b4 a g2 f#4 e d2. r4\
    b-4 d'8 f' b'-4 f'8 d'8\
    b-4 e'-8 g' b'-4 g'8 e'-8 b-4 e'-8 f' a'4 f'8 e'- b-4 d'8 f' b'-4 r", makeNotation=False)
    bm.insert(0.0, key.KeySignature(2))
    bm.insert(16.0, key.KeySignature(-2))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[4].append(spanner.Slur(bm[0].notes[0], bm[3].notes[0]))
    for m in bm:
        m.number += 44
    bm[1].insert(2.0, expressions.TextExpression("rall."))
    bm[3].append(bar.Barline("double"))
    bm[4].insert(0.0, expressions.TextExpression("ff"))
    bm[4].insert(0.0, tempo.TempoText("Presto"))
    bm[-1].rightBarline = None
    return bm

#-------------------------------------------------------------------------------
# Chapter 14: Symbols of Expression and Execution

def example14_1():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example14_1(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠣⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀
    ⠨⠦⠐⠛⠊⠨⠦⠙⠊⠨⠦⠓⠨⠙⠨⠦⠐⠋⠓
    """
    bm = converter.parse("tinynotation: 4/4 f8 a c' a g c' e g").flat
    bm.notes[0].articulations.append(articulations.Accent())
    bm.notes[2].articulations.append(articulations.Accent())
    bm.notes[4].articulations.append(articulations.Accent())
    bm.notes[6].articulations.append(articulations.Accent())
    bm.insert(0, key.KeySignature(-1))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None
    return bm

def example14_2():
    u"""
    Doubling of Tenuto marking is demonstrated. Accent is used in place of Reversed Accent because music21
    doesn't support the latter.

    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example14_2(), inPlace=True, showFirstMeasureNumber=False, slurLongPhraseWithBrackets=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠰⠃⠨⠏⠄⠀⠱⠻⠐⠺⠀⠹⠘⠆⠸⠦⠸⠦⠐⠫⠳⠀⠨⠹⠱⠸⠦⠩⠱⠀⠨⠦⠏⠄
    """
    bm = converter.parse("tinynotation: 3/4 e'2. d'4 f' b c' e g c' d' d'# e'2.").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[2].append(spanner.Slur(bm[0].notes[0], bm[2].notes[0]))
    bm[2].notes[1].articulations.append(articulations.Tenuto())
    bm[2].notes[2].articulations.append(articulations.Tenuto())
    bm[3].notes[0].articulations.append(articulations.Tenuto())
    bm[3].notes[1].articulations.append(articulations.Tenuto())
    bm[3].notes[2].articulations.append(articulations.Tenuto())
    bm[4].notes[0].articulations.append(articulations.Accent())
    bm[-1].rightBarline = None
    return bm

def example14_3():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example14_3(), inPlace=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠣⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠰⠃⠨⠦⠨⠑⠋⠙⠑⠚⠊⠓⠛⠘⠆⠀⠦⠳⠦⠫⠸⠦⠏⠀⠫⠉⠦⠋⠭⠳⠉⠦⠓⠭
    ⠀⠀⠸⠦⠐⠻⠉⠸⠦⠻⠫⠈⠉⠋⠭
    """
    bm = converter.parse("tinynotation: 4/4 d'8 e'- c' d' b- a- g f g4 e- e-2 e-4~ e-8 r g4~ g8 r f4~ f e-~ e-8 r").flat
    bm.insert(0, key.KeySignature(-3))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].append(spanner.Slur(bm[0].notes[0], bm[0].notes[-1]))
    bm[0].notes[0].articulations.append(articulations.Accent())
    bm[1].notes[0].articulations.append(articulations.Staccato())
    bm[1].notes[1].articulations.append(articulations.Staccato())
    bm[1].notes[2].articulations.append(articulations.Tenuto())
    bm[2].notes[1].articulations.append(articulations.Staccato())
    bm[2].notes[3].articulations.append(articulations.Staccato())
    bm[3].notes[0].articulations.append(articulations.Tenuto())
    bm[3].notes[1].articulations.append(articulations.Tenuto())
    bm[-1].rightBarline = None
    return bm

def example14_5():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example14_5(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠣⠸⠉⠀⠀⠀⠀⠀⠀⠀⠀
    ⠦⠦⠸⠑⠭⠛⠭⠊⠭⠦⠐⠑⠭⠀⠨⠦⠞⠪⠧
    """
    bm = converter.parse("tinynotation: 2/2 D8 r F r A r d r B-2 A4 r", makeNotation=False)
    bm.replace(bm.getElementsByClass('TimeSignature')[0], meter.TimeSignature('cut'))
    bm.insert(0, key.KeySignature(-1))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].notes[0].articulations.append(articulations.Staccato())
    bm[0].notes[1].articulations.append(articulations.Staccato())
    bm[0].notes[2].articulations.append(articulations.Staccato())
    bm[0].notes[3].articulations.append(articulations.Staccato())
    bm[1].notes[0].articulations.append(articulations.Accent())
    bm[-1].rightBarline = None
    return bm

def example14_6():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example14_6(), inPlace=True, showFirstMeasureNumber=False, debug=True))
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
    >>> print(translate.partToBraille(test.example14_6(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠸⠻⠦⠦⠑⠛⠙⠋⠀⠨⠦⠨⠦⠘⠚⠊⠚⠙⠨⠦⠱⠀⠑⠦⠋⠸⠦⠻⠧
    """
    bm = converter.parse("tinynotation: 3/4 F4 D8 F C E BB AA BB C D4 D8 E F4 r").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    for n in bm.flat.notes[1:-1]:
        n.articulations.append(articulations.Staccato())
    for n in bm[1].notes:
        n.articulations.append(articulations.Accent())
    bm[2].notes[-1].articulations.append(articulations.Tenuto())
    bm[-1].rightBarline = None
    return bm

def example14_7():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example14_7(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀
    ⠦⠨⠦⠸⠹⠦⠨⠦⠫⠦⠨⠦⠻
    """
    bm = converter.parse("tinynotation: 3/4 C4 E F").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    for n in bm[0].notes:
        n.articulations.append(articulations.Accent())
        n.articulations.append(articulations.Staccato())
    bm[0].rightBarline = None
    return bm

def example14_8():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example14_8(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀
    ⠨⠦⠸⠦⠸⠳⠨⠦⠸⠦⠺⠨⠦⠸⠦⠹
    """
    bm = converter.parse("tinynotation: 3/4 G4 B c").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    for n in bm[0].notes:
        #pass
        n.articulations.append(articulations.Tenuto())
        n.articulations.append(articulations.Accent())
    bm[0].rightBarline = None
    return bm

#-------------------------------------------------------------------------------
# Chapter 15: Smaller Values and Regular Note-Grouping, the Music Comma

def example15_1():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example15_1()))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠼⠃⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠚⠀⠐⠑⠀⠓⠄⠿⠓⠚⠀⠊⠄⠷⠊⠚⠀⠓⠄⠷⠚⠑⠀⠫⠄⠋⠀⠑⠄⠾⠚⠓⠀⠊⠄⠷⠊⠚
    ⠀⠀⠐⠓⠄⠯⠋⠑⠀⠳⠄
    """
    bm = converter.parse("tinynotation: 2/4 r4. d8 g8. f#16 g8 b8 a8. g16 a8 b8 g8. g16 b8 d'8 e'4. e'8\
    d'8. b16 b8 g8 a8. g16 a8 b8 g8. e16 e8 d8 g4.", makeNotation=False)
    bm.insert(0, key.KeySignature(1))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].pop(3)
    bm[0].padAsAnacrusis()
    for m in bm:
        m.number -= 1
    bm[-1].rightBarline = None
    return bm
 
def example15_2():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example15_2(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠼⠃⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠨⠑⠍⠯⠑⠍⠩⠽⠀⠱⠚⠭⠀⠚⠍⠽⠚⠍⠩⠮⠀⠺⠓⠭
    """
    bm = converter.parse("tinynotation: 2/4 d'8 r16 e'16 d'8 r16 c'#16 d'4 b8 r8 b8 r16 c'16 b8 r16 a#16 b4 g8 r8").flat
    bm.insert(0, key.KeySignature(1))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None
    return bm

def example15_3():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example15_3(), inPlace=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠋⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠐⠋⠄⠿⠋⠳⠓⠀⠑⠄⠯⠑⠻⠛⠀⠹⠑⠫⠛⠀⠫⠑⠱⠋⠀⠫⠛⠳⠮⠞⠝
    ⠀⠀⠐⠹⠯⠵⠹⠍
    """
    bm = converter.parse("tinynotation: 6/8 e8. f16 e8 g4 g8 d8. e16 d8 f4 f8 c4 d8 e4 f8\
    e4 d8 d4 e8 e4 f8 g4 a16 b32 c'32 c4 e16 d16 c4 r16")
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None
    return bm

def example15_4():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example15_4(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠨⠫⠈⠉⠋⠄⠿⠑⠄⠯⠀⠹⠰⠹⠹⠀⠩⠨⠷⠮⠭⠯⠿⠭⠵⠾⠭⠀⠹⠧⠧
    """
    bm = converter.parse("tinynotation: 3/4 e'4~ e'8. f'16 d'8. e'16 c'4 c''4 c''4 g'#16 a'16 r8 e'16 f'16 r8 d'16 b16 r8 c'4 r4 r4").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None
    return bm

def example15_5():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example15_5(), inPlace=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠩⠩⠼⠉⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠚⠀⠐⠯⠄⠞⠀⠚⠊⠚⠀⠩⠚⠽⠍⠐⠯⠄⠨⠝⠀⠙⠚⠙⠀⠙⠵⠍⠑⠀⠱⠯⠿⠀⠿⠐⠚⠄⠙
    ⠀⠀⠨⠋⠄⠵⠽⠾⠀⠪⠣⠅⠄
    """
    bm = converter.parse("tinynotation: 3/8 r4 e16. b32 b8 a8 b8 b#8 c'#16 r16 e16. c'#32 c'#8 b8 c'#8 c'#8 d'16 r16 d'8\
    d'4 e'16 f'#16 f'#16 b8. c'#8 e'8. d'16 c'#16 b16 a4").flat
    bm.insert(0, key.KeySignature(3))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].pop(3)
    bm[0].padAsAnacrusis()
    bm[3][1].pitch.accidental.displayStatus = False # remove cautionary accidental display
    for m in bm:
        m.number -= 1
    bm[-1].rightBarline = bar.Barline('double')
    return bm

def example15_6a():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example15_6a(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀
    ⠐⠽⠚⠙⠑⠯⠑⠋⠛⠷⠓⠊⠚⠽⠑⠋⠋
    """
    # beamed 16th notes
    bm = converter.parse("tinynotation: 4/4 c16 B c d e d e f g g a b c' d' e' e'").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None
    return bm

def example15_6b():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example15_6b(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀
    ⠐⠽⠾⠽⠵⠯⠵⠯⠿⠷⠷⠮⠾⠽⠵⠯⠯
    """
    # unbeamed 16th notes
    bm = converter.parse("tinynotation: 4/4 c16 B c d e d e f g g a b c' d' e' e'").flat
    # not calling makeNotation because it calls makeBeams
    bm.makeMeasures(inPlace=True)
    bm.makeAccidentals(cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None
    return bm

def example15_7():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example15_7(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠀⠼⠃⠲⠀⠀⠀⠀⠀⠀
    ⠐⠷⠨⠑⠙⠚⠹⠀⠐⠷⠄⠟⠯⠵⠫
    """
    bm = converter.parse("tinynotation: 2/4 g16 d' c' b c'4 g16. f32 e16 d e4").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None
    return bm

def example15_8():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example15_8(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠀⠼⠃⠲⠀⠀⠀⠀⠀⠀⠀
    ⠸⠷⠋⠛⠋⠷⠿⠭⠀⠿⠑⠋⠑⠿⠯⠭
    """
    bm = converter.parse("tinynotation: 2/4 G16 E F E G F r8 F16 D E D F E r8").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None
    return bm

def example15_9():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example15_9(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠼⠃⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠍⠨⠑⠙⠚⠽⠑⠋⠙⠀⠾⠙⠚⠊⠷⠿⠷⠍⠀⠨⠷⠛⠋⠑⠽⠍⠾⠮⠀⠗
    """
    bm = converter.parse("tinynotation: 2/4 r16 d' c' b c' d' e' c' b c' b a g f# g r g' f'# e' d' c' r b a g2").flat
    bm.insert(0, key.KeySignature(1))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None
    return bm

def example15_10():
    # print translate.partToBraille(test.example15_10(), inPlace=True, dummyRestLength = 24)
    # Division of measure at end of line of "4/4" bar occurs in middle of measure, when in reality
    # it could occur 3/4 into the bar. Hypothetical example that might not be worth attacking.
    bm = converter.parse("tinynotation: 4/4 g16 a g f e8 c d16 e f d e8 c").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None
    return bm
    
def example15_11():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example15_11(), inPlace=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠁⠃⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠼⠚⠀⠣⠐⠚⠀⠣⠯⠣⠨⠋⠣⠐⠓⠣⠨⠓⠣⠐⠚⠣⠨⠚⠡⠐⠾⠡⠨⠾⠣⠐⠾⠣⠨⠾⠐
    ⠀⠀⠡⠐⠾⠡⠨⠾⠣⠐⠾⠣⠨⠚⠣⠊⠛⠑⠚⠨⠫⠄
    """
    bm = converter.parse("tinynotation: 12/8 r1 r4 r8 b-8 e-16 e'- g- g'- b- b'- bn b'n b- b'- bn b'n b- b'- a'- f' d' b- e'-4.").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None
    for m in bm:
        m.number -= 1
    for i in range(3):
        bm[0].pop(2)
    bm[-1].notes[7].pitch.accidental = pitch.Accidental('natural')
    bm[-1].notes[11].pitch.accidental = pitch.Accidental('natural')
    return bm

#-------------------------------------------------------------------------------
# Chapter 16: Irregular Note-Grouping

# Triplets
# --------
def example16_1():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example16_1(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠀⠀⠼⠃⠲⠀⠀⠀⠀⠀⠀⠀
    ⠆⠨⠦⠐⠙⠋⠊⠳⠀⠆⠨⠦⠸⠚⠑⠊⠳
    """
    bm = converter.parse("tinynotation: 2/4 trip{c8 e a} g4 trip{B8 d a} g4").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None
    bm[0].notes[0].articulations.append(articulations.Accent())
    bm[1].notes[0].articulations.append(articulations.Accent())
    return bm

def example16_2():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example16_2(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠐⠺⠈⠉⠆⠚⠙⠐⠛⠆⠚⠑⠐⠛⠀⠺⠈⠉⠆⠚⠙⠑⠆⠑⠙⠚
    """
    bm = converter.parse("tinynotation: 3/4 b-4~ trip{b-8 c' f} trip{b- d' f} b-4~ trip{b-8 c' d'} trip{d' c' b-}").flat
    bm.insert(0, key.KeySignature(-2))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None
    return bm

def example16_4():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example16_4(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠣⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠜⠇⠑⠛⠁⠞⠕⠜⠏⠰⠃⠆⠨⠙⠚⠊⠆⠊⠚⠙⠆⠚⠙⠚⠫⠘⠆
    """
    bm = converter.parse("tinynotation: 4/4 trip{c'8 b- a-} trip{a- b- c'} trip{b- c' b-} e-4").flat
    bm.insert(0, key.KeySignature(-4))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[0].insert(0.0, dynamics.Dynamic('p'))
    bm[0].insert(0.0, expressions.TextExpression("legato"))
    bm[0].append(spanner.Slur(bm[0].notes[0], bm[0].notes[-1]))
    bm[-1].rightBarline = None
    return bm

def example16_6():
    bm = converter.parse("tinynotation: 2/4 trip{b'-8 f' d'} trip{b- d' e'-} trip{f' d' b-} trip{f b- d'}").flat
    bm.insert(0, key.KeySignature(-2))
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None
    return bm

#-------------------------------------------------------------------------------
# Chapter 17: Measure Repeats, Full-Measure In-Accords

def example17_1():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example17_1(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀
    ⠐⠹⠫⠪⠳⠀⠶⠀⠸⠺⠱⠪⠳⠀⠷
    """
    bm = converter.parse("tinynotation: 4/4 c4 e a g c e a g B d a g g1").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None
    return bm

def example17_2():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example17_2(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀
    ⠦⠐⠳⠦⠩⠻⠨⠦⠡⠟⠀⠶⠀⠏⠗⠀⠯
    """
    bm = converter.parse("tinynotation: 4/4 g4 f# fn2 g4 f# fn2 e2 g2 e1").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None
    bm[0].notes[0].articulations.append(articulations.Staccato())
    bm[0].notes[1].articulations.append(articulations.Staccato())
    bm[0].notes[2].articulations.append(articulations.Accent())
    bm[1].notes[0].articulations.append(articulations.Staccato())
    bm[1].notes[1].articulations.append(articulations.Staccato())
    bm[1].notes[2].articulations.append(articulations.Accent())
    return bm

def example17_3():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example17_3(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀
    ⠐⠹⠫⠳⠀⠶⠀⠶⠀⠨⠝⠄
    """
    bm = converter.parse("tinynotation: 3/4 c4 e g c e g c e g c'2.").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None
    return bm

def example17_4():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.partToBraille(test.example17_4(), inPlace=True, showFirstMeasureNumber=False))
    ⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀
    ⠐⠹⠫⠳⠀⠶⠀⠶⠀⠎⠄
    """
    bm = converter.parse("tinynotation: 3/4 c4 e g c e g c e g a2.").flat
    bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    bm[-1].rightBarline = None
    return bm

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# PART TWO
# Transcribing Two- and Three-Staff Music
#
#-------------------------------------------------------------------------------
# Chapter 24: Bar-over-Bar Format

def example24_1a():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.measureToBraille(test.example24_1a(), inPlace=True, showHand = 'right', showHeading=True))
    ⠀⠀⠼⠙⠲⠀⠀⠀
    ⠅⠜⠄⠜⠋⠐⠝⠏
    """
    rightHand = converter.parse("tinynotation: 4/4 c2 e2").flat
    rightHand.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    rightHand[0].rightBarline = None
    rightHand[0].insert(0.0, dynamics.Dynamic('f'))
    return rightHand[0]

def example24_1b():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.measureToBraille(test.example24_1b(), inPlace=True, showHand = 'left', showHeading=True))
    ⠀⠀⠼⠃⠲⠀⠀
    ⠇⠜⠸⠙⠭⠋⠭
    """
    leftHand = converter.parse("tinynotation: 2/4 C8 r8 E8 r8").flat
    leftHand.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    leftHand[0].rightBarline = None
    return leftHand[0]

def example24_2():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> rightHand = test.example24_2()[0]
    >>> leftHand = test.example24_2()[1]
    >>> print(translate.keyboardPartsToBraille(rightHand, leftHand, inPlace=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠃⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠁⠀⠅⠜⠨⠙⠐⠓⠋⠓⠀⠐⠛⠓⠋⠊⠀⠐⠓⠛⠋⠑⠀⠐⠋⠋⠑⠭⠀⠐⠋⠑⠋⠓⠀⠐⠛⠓⠊⠛
    ⠀⠀⠇⠜⠸⠙⠓⠐⠙⠚⠀⠸⠊⠚⠙⠙⠀⠸⠚⠊⠓⠚⠀⠐⠙⠙⠚⠓⠀⠐⠙⠭⠣⠺⠀⠸⠊⠭⠙⠭
    ⠛⠀⠅⠜⠐⠋⠓⠓⠛⠀⠐⠏⠣⠅
    ⠀⠀⠇⠜⠐⠙⠭⠚⠓⠀⠐⠝⠣⠅
    """
    rightHand = converter.parse("tinynotation: 2/4 c'8 g8 e8 g8 f8 g8 e8 a8 g8 f8 e8 d8 e8 e8 d8 r8 e8 d8 e8 g8 f8 g8 a8 f8 e8 g8 g8 f8 e2").flat
    leftHand = converter.parse("tinynotation: 2/4 C8 G8 c8 B8 A8 B8 c8 c8 B8 A8 G8 B8 c8 c8 B8 G8 c8 r8 B-4 A8 r8 c8 r8 c8 r8 B8 G8 c2").flat
    rightHand.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    leftHand.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    keyboardPart = stream.Part()
    keyboardPart.append(rightHand)
    keyboardPart.append(leftHand)
    return keyboardPart

def example24_3():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> rightHand = test.example24_3()[0]
    >>> leftHand = test.example24_3()[1]
    >>> print(translate.keyboardPartsToBraille(rightHand, leftHand, inPlace=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠚⠀⠅⠜⠨⠱⠇⠀⠨⠑⠋⠑⠙⠚⠊⠀⠐⠗⠁⠉⠺⠇
    ⠀⠀⠇⠜⠸⠚⠊⠀⠸⠓⠭⠚⠭⠑⠭⠀⠸⠓⠊⠚⠙⠱
    """
    rightHand = converter.parse("tinynotation: 3/4 r2 d'4 d'8 e'-8 d'8 c'8 b-8 a8 g2 b-4").flat
    leftHand = converter.parse("tinynotation: 3/4 r2 B-8 A8 G8 r8 B-8 r8 d8 r8 G8 A8 B-8 c8 d4").flat
    rightHand.insert(0, key.KeySignature(-2))
    leftHand.insert(0, key.KeySignature(-2))
    rightHand.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    leftHand.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    rightHand[-1].append(spanner.Slur(rightHand[-1].notes[0], rightHand[-1].notes[1]))
    rightHand[0].notes[0].fingering = '3'
    rightHand[-1].notes[0].fingering = '1'
    rightHand[-1].notes[1].fingering = '3'
    rightHand[0].pop(3)
    rightHand[0].padAsAnacrusis()
    leftHand[0].pop(3)
    leftHand[0].padAsAnacrusis()
    for m in rightHand:
        m.number -= 1
    for m in leftHand:
        m.number -= 1
    rightHand[-1].rightBarline = None
    leftHand[-1].rightBarline = None
    keyboardPart = stream.Part()
    keyboardPart.append(rightHand)
    keyboardPart.append(leftHand)
    return keyboardPart

def example24_4():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> rightHand = test.example24_4()[0]
    >>> leftHand = test.example24_4()[1]
    >>> print(translate.keyboardPartsToBraille(rightHand, leftHand, inPlace=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠩⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠊⠀⠅⠜⠰⠵⠚⠊⠛⠫⠈⠉⠯⠑⠐⠊⠨⠑⠫⠀⠨⠽⠚⠙⠑⠯⠓⠛⠋⠿⠋⠛⠓⠮⠚⠙⠑
    ⠀⠀⠀⠇⠜⠨⠱⠈⠉⠵⠙⠚⠓⠻⠈⠉⠿⠓⠚⠓⠀⠐⠪⠹⠑⠵⠯⠿⠓⠋⠛⠀⠀⠀⠀⠀⠀⠀
    ⠁⠁⠀⠅⠜⠰⠯⠑⠙⠚⠮⠓⠛⠋⠕⠣⠅
    ⠀⠀⠀⠇⠜⠨⠳⠹⠍⠊⠛⠋⠱⠣⠅⠀⠀
    """
    rightHand = converter.parse("tinynotation: 4/4 d'16 b16 a16 f#16 e4~ e16 d16 A16 d16 e4 c#16 B16 c#16 d16 e16 g16 f#16 e16 f#16 e16 f#16 g16 a16 b16 c'#16 d'16\
    e'16 d'16 c'#16 b16 a16 g16 f#16 e16 d2").flat
    leftHand = converter.parse("tinynotation: 4/4 d'4~ d'16 c'#16 b16 g16 f#4~ f#16 g16 b16 g16 a4 c'#4 d'8 d'16 e'16 f'#16 g'16 e'16 f'#16\
    g'4 c'#4 r16 a16 f#16 e16 d4").flat
    rightHand.transpose('P8', inPlace=True)
    rightHand.insert(0, key.KeySignature(2))
    leftHand.insert(0, key.KeySignature(2))
    rightHand.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    leftHand.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    for m in rightHand:
        m.number += 8
    for m in leftHand:
        m.number += 8
    keyboardPart = stream.Part()
    keyboardPart.append(rightHand)
    keyboardPart.append(leftHand)
    return keyboardPart

def example24_5():
    rightHand = converter.parse("tinynotation: 2/4 trip{d'-8 c' b-} trip{f8 b- d'-} trip{c'8 an f} trip{c'8 d'- e'-} d'-4").flat
    leftHand = converter.parse("tinynotation: 2/4 B-4 B- An F B-2").flat
    rightHand.insert(0, key.KeySignature(-5))
    leftHand.insert(0, key.KeySignature(-5))
    rightHand.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    leftHand.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    for m in rightHand:
        m.number += 9
    for m in leftHand:
        m.number += 9
    rightHand[0].notes[0].fingering = '4'
    rightHand[0].notes[1].fingering = '3'
    rightHand[0].notes[2].fingering = '2'
    rightHand[0].notes[3].fingering = '1'
    rightHand[0].notes[4].fingering = '2'
    rightHand[0].notes[5].fingering = '4'
    rightHand[1].notes[0].fingering = '3'
    rightHand[1].notes[3].fingering = '2'
    keyboardPart = stream.Part()
    keyboardPart.append(rightHand)
    keyboardPart.append(leftHand)
    return keyboardPart

#-------------------------------------------------------------------------------
# Chapter 26: Interval Signs and Chords

def example26_1a():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.measureToBraille(test.example26_1a(), inPlace=True, showHand = 'right', descendingChords=True))
    ⠅⠜⠨⠷⠼⠴⠤
    """
    c1 = chord.Chord(['G4','B4','D5','G5'], quarterLength=4.0)
    m1 = stream.Measure()
    m1.append(c1)
    return m1

def example26_1b():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> print(translate.measureToBraille(test.example26_1b(), inPlace=True, showHand = 'left', descendingChords=False))
    ⠇⠜⠘⠷⠬⠔⠤
    """
    c1 = chord.Chord(['G2','B2','D3','G3'], quarterLength=4.0)
    m1 = stream.Measure()
    m1.append(c1)
    return m1

def example26_2():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> rightHand = test.example26_2()[0]
    >>> leftHand = test.example26_2()[1]
    >>> print(translate.keyboardPartsToBraille(rightHand, leftHand, inPlace=True))
    ⠀⠀⠀⠨⠉⠀⠀⠀
    ⠁⠀⠅⠜⠨⠷⠴⠼
    ⠀⠀⠇⠜⠘⠷⠔⠬
    """
    chord_right = chord.Chord(['D4','B4','G5'], quarterLength=4.0)
    chord_left = chord.Chord(['G2','D3','B3'], quarterLength=4.0)
    part_right = stream.Part()
    part_right.append(meter.TimeSignature('c'))
    part_right.append(chord_right)
    part_left = stream.Part()
    part_left.append(meter.TimeSignature('c'))
    part_left.append(chord_left)
    part_right.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    part_left.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    part_right[-1].rightBarline = None
    part_left[-1].rightBarline = None
    keyboardPart = stream.Part()
    keyboardPart.append(part_right)
    keyboardPart.append(part_left)
    return keyboardPart

def example26_3():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> rightHand = test.example26_3()[0]
    >>> leftHand = test.example26_3()[1]
    >>> print(translate.keyboardPartsToBraille(rightHand, leftHand, inPlace=True))
    ⠀⠀⠀⠨⠉⠀⠀⠀
    ⠁⠀⠅⠜⠨⠯⠐⠬
    ⠀⠀⠇⠜⠘⠽⠸⠬
    """
    chord_right = chord.Chord(['C4','E5'], quarterLength=4.0)
    chord_left = chord.Chord(['C2','E3'], quarterLength=4.0)
    part_right = stream.Part()
    part_right.append(meter.TimeSignature('c'))
    part_right.append(chord_right)
    part_left = stream.Part()
    part_left.append(meter.TimeSignature('c'))
    part_left.append(chord_left)
    part_right.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    part_left.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    part_right[-1].rightBarline = None
    part_left[-1].rightBarline = None
    keyboardPart = stream.Part()
    keyboardPart.append(part_right)
    keyboardPart.append(part_left)
    return keyboardPart

def example26_4():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> rightHand = test.example26_4()[0]
    >>> leftHand = test.example26_4()[1]
    >>> print(translate.keyboardPartsToBraille(rightHand, leftHand, inPlace=True))
    ⠀⠀⠀⠀⠨⠉⠀⠀⠀
    ⠁⠀⠅⠜⠰⠽⠴⠌⠀
    ⠀⠀⠇⠜⠘⠷⠴⠐⠴
    """
    chord_right = chord.Chord(['B4','E5','C6'], quarterLength=4.0)
    chord_left = chord.Chord(['G2','E3','E4'], quarterLength=4.0)
    part_right = stream.Part()
    part_right.append(meter.TimeSignature('c'))
    part_right.append(chord_right)
    part_left = stream.Part()
    part_left.append(meter.TimeSignature('c'))
    part_left.append(chord_left)
    part_right.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    part_left.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    part_right[-1].rightBarline = None
    part_left[-1].rightBarline = None
    keyboardPart = stream.Part()
    keyboardPart.append(part_right)
    keyboardPart.append(part_left)
    return keyboardPart

def example26_5():
    u"""
    >>> from music21.braille import test
    >>> from music21.braille import translate
    >>> rightHand = test.example26_5()[0]
    >>> leftHand = test.example26_5()[1]
    >>> print(translate.keyboardPartsToBraille(rightHand, leftHand, inPlace=True))
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠩⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠁⠀⠅⠜⠐⠚⠬⠙⠑⠬⠐⠓⠨⠋⠬⠛⠓⠴⠐⠓⠀⠀
    ⠀⠀⠇⠜⠘⠓⠔⠸⠋⠘⠓⠔⠸⠚⠸⠙⠔⠊⠓⠔⠸⠚
    """
    all_right = [chord.Chord(['G4', 'B4'], quarterLength=0.5), note.Note('C5', quarterLength=0.5),
                 chord.Chord(['B4', 'D5'], quarterLength=0.5), note.Note('G4', quarterLength=0.5),
                 chord.Chord(['C5', 'E5'], quarterLength=0.5), note.Note('F#5', quarterLength=0.5),
                 chord.Chord(['B4', 'G5'], quarterLength=0.5), note.Note('G4', quarterLength=0.5)]
    part_right = stream.Part()
    part_right.append(key.KeySignature(1))
    part_right.append(meter.TimeSignature('4/4'))
    part_right.append(all_right)

    all_left = [chord.Chord(['G2', 'D3'], quarterLength=0.5), note.Note('E3', quarterLength=0.5),
                chord.Chord(['G2', 'D3'], quarterLength=0.5), note.Note('B3', quarterLength=0.5),
                chord.Chord(['C3', 'G3'], quarterLength=0.5), note.Note('A2', quarterLength=0.5),
                chord.Chord(['G2', 'D3'], quarterLength=0.5), note.Note('B3', quarterLength=0.5)]
    part_left = stream.Part()
    part_left.append(key.KeySignature(1))
    part_left.append(meter.TimeSignature('4/4'))
    part_left.append(all_left)
    
    part_right.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    part_left.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    part_right[-1].rightBarline = None
    part_left[-1].rightBarline = None
    keyboardPart = stream.Part()
    keyboardPart.append(part_right)
    keyboardPart.append(part_left)
    return keyboardPart

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    import music21
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof
