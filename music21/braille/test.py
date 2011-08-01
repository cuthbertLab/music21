# -*- coding: utf-8 -*-
#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         test.py
# Purpose:      music21 class which allows for test cases of music21 to braille translation.
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import codecs
import music21
import unittest

from music21.braille import translate

from music21 import bar
from music21 import clef
from music21 import key
from music21 import meter
from music21 import note
from music21 import stream
from music21 import tinyNotation

# Introduction to Braille Music Transcription, Second Edition
#-------------------------------------------------------------------------------
# NOTE: Octave marks which precede the first note in a line of braille music
# are omitted in Chapters 2-6 in the transcription manual because the concept is
# not introduced until Chapter 7. They are NOT omitted in the examples below,
# however, because they are required in transcription.
# 
# Chapter 2: Eighth Notes, the Eighth Rest, and Other Basic Signs

def example2_1():
    '''
    >>> from music21.braille import translate
    >>> inBraille = translate.partToBraille(example2_1())
    >>> inBraille[0] == "⠼⠁⠀⠐⠓⠭⠋⠀⠛⠭⠊⠀⠓⠭⠛⠀⠋⠭⠭⠀⠋⠭⠙⠀⠑⠭⠛⠀⠋⠭⠑⠀⠙⠭⠭⠀⠑⠭⠛⠀"
    True
    >>> inBraille[1] == "⠀⠀⠐⠋⠭⠓⠀⠛⠓⠊⠀⠓⠭⠭⠀⠊⠭⠛⠀⠓⠭⠋⠀⠛⠋⠑⠀⠙⠭⠭⠣⠅⠀⠀⠀⠀⠀⠀⠀⠀"
    True
    '''
    bm = tinyNotation.TinyNotationStream("g8 r8 e8 f8 r8 a8 g8 r8 f8 e8 r8 r8 e8 r8 c8 d8 r8 f8 e8 r8 d8 c8 r8 r8 \
    d8 r8 f8 e8 r8 g8 f8 g8 a8 g8 r8 r8 a8 r8 f8 g8 r8 e8 f8 e8 d8 c8 r8 r8")
    bm.insert(0, meter.TimeSignature('3/8'))
    bm.makeMeasures(inPlace = True)
    bm[0].pop(0) # remove time signature
    bm[-1].append(bar.Barline('light-heavy'))
    return bm

def example2_2():
    '''
    >>> from music21.braille import translate
    >>> inBraille = translate.partToBraille(example2_2())
    >>> inBraille[0] == "⠼⠚⠀⠐⠑⠀⠑⠙⠚⠑⠀⠙⠚⠊⠙⠀⠚⠊⠓⠚⠀⠊⠊⠑⠭⠀⠋⠋⠓⠋⠀⠑⠋⠓⠚⠀⠑⠙⠚⠊"
    True
    >>> inBraille[1] == "⠀⠀⠸⠓⠓⠓⠭⠣⠅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"
    True
    '''
    bm = tinyNotation.TinyNotationStream("r8 r8 r8 d8 d8 c8 B8 d8 c8 B8 A8 c8 B8 A8 G8 B8 A8 A8 D8 r8 E8 E8 G8 E8 \
    D8 E8 G8 B8 d8 c8 B8 A8 G8 G8 G8 r8")
    bm.insert(0, meter.TimeSignature('4/8'))
    bm.makeMeasures(inPlace = True)
    for numRest in range(3):
        bm[0].pop(2)
    bm[0].padAsAnacrusis()
    for measure in bm:
        measure.number -= 1
    bm[0].pop(0) # remove time signature
    bm[-1].append(bar.Barline('light-heavy'))
    return bm

def example2_3():
    '''
    >>> from music21.braille import translate
    >>> inBraille = translate.partToBraille(example2_3())
    >>> inBraille[0] == "⠼⠁⠀⠐⠋⠋⠀⠓⠊⠀⠓⠛⠀⠋⠓⠀⠛⠋⠀⠑⠛⠀⠋⠙⠀⠑⠭⠀⠋⠋⠀⠛⠛⠀⠓⠊⠀⠚⠙⠀"
    True
    >>> inBraille[1] == "⠀⠀⠐⠊⠛⠀⠋⠑⠀⠙⠚⠀⠙⠭⠣⠅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"
    True
    '''
    bm = tinyNotation.TinyNotationStream("e8 e8 g8 a8 g8 f8 e8 g8 f8 e8 d8 f8 e8 c8 d8 r8 e8 e8 f8 f8 g8 a8 b8 c'8 \
    a8 f8 e8 d8 c8 B8 c8 r8")
    bm.insert(0, meter.TimeSignature('2/8'))
    bm.makeMeasures(inPlace = True)
    bm[0].pop(0) # remove time signature
    bm[-1].append(bar.Barline('light-heavy'))
    return bm

def example2_4():
    '''
    >>> from music21.braille import translate
    >>> inBraille = translate.partToBraille(example2_4())
    >>> inBraille[0] == "⠼⠁⠀⠸⠊⠙⠋⠀⠑⠙⠚⠀⠙⠭⠚⠀⠊⠭⠭⠀⠚⠚⠙⠀⠑⠙⠚⠀⠊⠭⠊⠀⠚⠭⠭⠣⠅⠄⠀⠀"
    True
    >>> inBraille[1] == "⠀⠀⠸⠊⠋⠊⠀⠙⠚⠊⠀⠊⠚⠙⠀⠑⠭⠭⠀⠋⠑⠙⠀⠚⠋⠚⠀⠊⠭⠊⠀⠊⠭⠭⠣⠅⠀⠀⠀⠀"
    True
    '''
    bm = tinyNotation.TinyNotationStream("A8 c8 e8 d8 c8 B8 c8 r8 B8 A8 r8 r8 B8 B8 c8 d8 c8 B8 A8 r8 A8 B8 r8 r8 \
    A8 E8 A8 c8 B8 A8 A8 B8 c8 d8 r8 r8 e8 d8 c8 B8 E8 B8 A8 r8 A8 A8 r8 r8")
    bm.insert(0, meter.TimeSignature('3/8'))
    bm.makeMeasures(inPlace = True)
    bm[7].append(bar.Barline('light-light'))
    bm[-1].append(bar.Barline('light-heavy'))
    bm[0].pop(0) # remove time signature
    return bm

def example2_5():
    '''
    >>> from music21.braille import translate
    >>> inBraille = translate.partToBraille(example2_5())
    >>> inBraille[0] == "⠼⠚⠀⠨⠑⠋⠀⠛⠙⠊⠙⠀⠑⠙⠊⠙⠀⠊⠙⠊⠓⠀⠋⠓⠛⠭⠀⠑⠋⠛⠑⠀⠙⠑⠋⠛⠀⠀⠀⠀"
    True
    >>> inBraille[1] == "⠀⠀⠐⠓⠋⠙⠋⠀⠛⠭⠣⠅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"
    True
    '''
    bm = tinyNotation.TinyNotationStream("r8 r8 d'8 e'8 f'8 c'8 a8 c'8 d'8 c'8 a8 c'8 a8 c'8 a8 g8 e8 g8 f8 r8 \
    d8 e8 f8 d8 c8 d8 e8 f8 g8 e8 c8 e8 f8 r8")
    bm.insert(0, meter.TimeSignature('4/8'))
    bm.makeMeasures(inPlace = True)
    for numRest in range(2):
        bm[0].pop(2)
    bm[0].padAsAnacrusis()
    for measure in bm:
        measure.number -= 1
    bm[0].pop(0) # remove time signature
    bm[-1].append(bar.Barline('light-heavy'))
    return bm

def example2_6():
    '''
    >>> from music21.braille import translate
    >>> inBraille = translate.partToBraille(example2_6())
    >>> inBraille[0] == "⠼⠁⠀⠸⠓⠓⠓⠓⠋⠛⠀⠊⠓⠓⠓⠭⠓⠀⠊⠊⠊⠙⠚⠊⠀⠊⠓⠓⠓⠭⠭⠀⠓⠛⠛⠛⠭⠭⠀⠀"
    True
    >>> inBraille[1] == "⠀⠀⠸⠛⠋⠋⠋⠭⠭⠀⠑⠋⠑⠓⠛⠑⠀⠙⠋⠑⠙⠭⠭⠣⠅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"
    True
    '''
    bm = tinyNotation.TinyNotationStream("G8 G8 G8 G8 E8 F8 A8 G8 G8 G8 r8 G8 A8 A8 A8 c8 B8 A8 A8 G8 G8 G8 r8 r8 \
    G8 F8 F8 F8 r8 r8 F8 E8 E8 E8 r8 r8 D8 E8 D8 G8 F8 D8 C8 E8 D8 C8 r8 r8")
    bm.insert(0, meter.TimeSignature('6/8'))
    bm.makeMeasures(inPlace = True)
    bm[-1].append(bar.Barline('light-heavy'))
    bm[0].pop(0)
    return bm

def example2_7():
    '''
    >>> from music21.braille import translate
    >>> inBraille = translate.partToBraille(example2_7())
    >>> inBraille[0] == "⠼⠁⠀⠐⠋⠭⠋⠛⠭⠛⠀⠑⠭⠑⠋⠭⠋⠀⠙⠑⠋⠓⠛⠋⠀⠋⠑⠑⠑⠭⠭⠀⠙⠭⠙⠋⠭⠋⠀⠀"
    True
    >>> inBraille[1] == "⠀⠀⠐⠛⠭⠛⠊⠭⠊⠀⠓⠭⠓⠓⠊⠚⠀⠑⠙⠙⠙⠭⠭⠣⠅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"
    True
    '''
    bm = tinyNotation.TinyNotationStream("e8 r8 e8 f8 r8 f8 d8 r8 d8 e8 r8 e8 c8 d8 e8 g8 f8 e8 e8 d8 d8 d8 r8 r8 \
    c8 r8 c8 e8 r8 e8 f8 r8 f8 a8 r8 a8 g8 r8 g8 g8 a8 b8 d'8 c'8 c'8 c'8 r8 r8")
    bm.insert(0, meter.TimeSignature('6/8'))
    bm.makeMeasures(inPlace = True)
    bm[-1].append(bar.Barline('light-heavy'))
    bm[0].pop(0)
    return bm

#-------------------------------------------------------------------------------
# Chapter 3: Quarter Notes, the Quarter Rest, and the Dot

def example3_1():
    '''
    >>> from music21.braille import translate
    >>> inBraille = translate.partToBraille(example3_1())
    >>> inBraille[0] == "⠼⠁⠀⠨⠱⠺⠳⠺⠀⠹⠺⠪⠧⠀⠺⠳⠫⠳⠀⠱⠺⠱⠧⠀⠫⠳⠪⠳⠀⠱⠳⠺⠱⠀⠫⠱⠹⠪⠀⠀"
    True
    >>> inBraille[1] == "⠀⠀⠐⠳⠱⠳⠧⠣⠅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"
    True
    '''
    bm = tinyNotation.TinyNotationStream("d'4 b4 g4 b4 c'4 b4 a4 r4 b4 g4 e4 g4 d4 B4 d4 r4 e4 g4 a4 g4 d4 g4 b4 \
    d'4 e'4 d'4 c'4 a4 g4 d4 g4 r4")
    bm.makeMeasures(inPlace = True)
    bm[-1].append(bar.Barline('light-heavy'))
    bm[0].pop(0)
    return bm

def example3_2():
    '''
    >>> from music21.braille import translate
    >>> inBraille = translate.partToBraille(example3_2())
    >>> inBraille[0] == "⠼⠁⠀⠸⠪⠻⠹⠻⠀⠳⠫⠹⠫⠀⠻⠳⠪⠻⠀⠱⠫⠻⠧⠀⠳⠪⠳⠹⠀⠻⠪⠹⠱⠀⠹⠪⠳⠹⠀⠀"
    True
    >>> inBraille[1] == "⠀⠀⠸⠱⠫⠻⠧⠣⠅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"
    True
    '''
    bm = tinyNotation.TinyNotationStream("A4 F4 C4 F4 G4 E4 C4 E4 F4 G4 A4 F4 D4 E4 F4 r4 G4 A4 G4 C4 F4 A4 c4 d4 \
    c4 A4 G4 C4 D4 E4 F4 r4")
    bm.makeMeasures(inPlace = True)
    bm[-1].append(bar.Barline('light-heavy'))
    bm[0].pop(0)
    return bm

def example3_3():
    '''
    >>> from music21.braille import translate
    >>> inBraille = translate.partToBraille(example3_3())
    >>> inBraille[0] == "⠼⠁⠀⠐⠳⠫⠀⠪⠳⠀⠻⠧⠀⠱⠧⠀⠹⠄⠙⠀⠱⠄⠑⠀⠫⠧⠀⠹⠧⠀⠳⠳⠀⠪⠺⠀⠹⠧⠀⠀"
    True
    >>> inBraille[1] == "⠀⠀⠐⠪⠧⠀⠳⠄⠓⠀⠻⠱⠀⠹⠫⠀⠹⠧⠣⠅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"
    True
    '''
    bm = tinyNotation.TinyNotationStream("g4 e4 a4 g4 f4 r4 d4 r4 c4. c8 d4. d8 e4 r4 c4 r4 g4 g4 a4 b4 c'4 r4 a4 r4 \
    g4. g8 f4 d4 c4 e4 c4 r4")
    bm.insert(0, meter.TimeSignature('2/4'))
    bm.makeMeasures(inPlace = True)
    bm[-1].append(bar.Barline('light-heavy'))
    bm[0].pop(0)
    return bm

def example3_4():
    '''
    >>> from music21.braille import translate
    >>> inBraille = translate.partToBraille(example3_4())
    >>> inBraille[0] == "⠼⠁⠀⠸⠫⠙⠑⠫⠧⠀⠻⠊⠛⠫⠧⠀⠱⠋⠛⠓⠋⠹⠀⠱⠱⠳⠧⠀⠻⠋⠑⠫⠧⠀⠳⠛⠋⠻⠧⠀"
    True
    >>> inBraille[1] == "⠀⠀⠸⠪⠓⠛⠋⠛⠳⠀⠻⠱⠹⠧⠣⠅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"
    True
    '''
    bm = tinyNotation.TinyNotationStream("E4 C8 D8 E4 r4 F4 A8 F8 E4 r4 D4 E8 F8 G8 E8 C4 D4 D4 G4 r4 \
    F4 E8 D8 E4 r4 G4 F8 E8 F4 r4 A4 G8 F8 E8 F8 G4 F4 D4 C4 r4")
    bm.makeMeasures(inPlace = True)
    bm[-1].append(bar.Barline('light-heavy'))
    bm[0].pop(0)
    return bm

def example3_5():
    '''
    >>> from music21.braille import translate
    >>> inBraille = translate.partToBraille(example3_5())
    >>> inBraille[0] == "⠼⠁⠀⠐⠻⠄⠙⠱⠫⠀⠻⠄⠓⠪⠻⠀⠪⠹⠱⠹⠀⠪⠻⠳⠧⠣⠅⠄⠀⠳⠄⠋⠹⠫⠀⠻⠄⠙⠻⠪"
    True
    >>> inBraille[1] == "⠀⠀⠐⠳⠳⠻⠫⠀⠻⠪⠻⠧⠣⠅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"
    True
    '''
    bm = tinyNotation.TinyNotationStream("f4. c8 d4 e4 f4. g8 a4 f4 a4 c'4 d'4 c'4 a4 f4 g4 r4 \
    g4. e8 c4 e4 f4. c8 f4 a4 g4 g4 f4 e4 f4 a4 f4 r4")
    bm.makeMeasures(inPlace = True)
    bm[3].append(bar.Barline('light-light'))
    bm[-1].append(bar.Barline('light-heavy'))
    bm[0].pop(0)
    return bm

def example3_6():
    '''
    >>> from music21.braille import translate
    >>> inBraille = translate.partToBraille(example3_6())
    >>> inBraille[0] == "⠼⠁⠀⠐⠳⠓⠱⠑⠀⠳⠚⠑⠚⠓⠀⠪⠊⠊⠚⠙⠀⠺⠚⠳⠭⠀⠪⠊⠱⠑⠀⠳⠚⠪⠙⠀⠀⠀⠀⠀"
    True
    >>> inBraille[1] == "⠀⠀⠐⠚⠙⠑⠹⠊⠀⠳⠓⠳⠭⠣⠅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"
    True
    '''
    bm = tinyNotation.TinyNotationStream("g4 g8 d4 d8 g4 b8 d'8 b8 g8 a4 a8 a8 b8 c'8 b4 b8 g4 r8 a4 a8 d4 d8 g4 b8 a4 c'8\
    b8 c'8 d'8 c'4 a8 g4 g8 g4 r8")
    bm.insert(0, meter.TimeSignature('3/4'))
    bm.makeMeasures(inPlace = True)
    bm[-1].append(bar.Barline('light-heavy'))
    bm[0].pop(0)
    return bm

#-------------------------------------------------------------------------------
# Chapter 4: Half Notes, the Half Rest, and the Tie

def example4_1():
    '''
    >>> from music21.braille import translate
    >>> inBraille = translate.partToBraille(example4_1())
    >>> inBraille[0] == "⠼⠁⠀⠐⠝⠏⠀⠕⠟⠀⠏⠗⠀⠟⠎⠀⠗⠞⠀⠎⠝⠀⠞⠕⠀⠝⠥⠣⠅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"
    True
    '''
    bm = tinyNotation.TinyNotationStream("c2 e2 d2 f2 e2 g2 f2 a2 g2 b2 a2 c'2 b2 d'2 c'2 r2")
    bm.makeMeasures(inPlace = True)
    bm[-1].append(bar.Barline('light-heavy'))
    bm[0].pop(0)
    return bm

def example4_2():
    '''
    >>> from music21.braille import translate
    >>> inBraille = translate.partToBraille(example4_2())
    >>> inBraille[0] == "⠼⠁⠀⠸⠟⠎⠀⠗⠝⠀⠱⠹⠱⠫⠀⠟⠥⠀⠕⠟⠀⠝⠟⠀⠫⠻⠳⠪⠀⠟⠥⠣⠅⠀⠀⠀⠀⠀⠀⠀"
    True
    '''
    bm = tinyNotation.TinyNotationStream("F2 A2 G2 C2 D4 C4 D4 E4 F2 r2 D2 F2 C2 F2 E4 F4 G4 A4 F2 r2")
    bm.makeMeasures(inPlace = True)
    bm[-1].append(bar.Barline('light-heavy'))
    bm[0].pop(0)
    return bm    

def example4_3():
    '''
    >>> from music21.braille import translate
    >>> inBraille = translate.partToBraille(example4_3())
    >>> inBraille[0] == "⠼⠁⠀⠐⠝⠹⠀⠑⠙⠚⠙⠱⠀⠏⠫⠀⠛⠋⠑⠋⠻⠀⠗⠳⠀⠊⠓⠛⠓⠪⠀⠚⠊⠓⠊⠚⠑⠀⠹⠥"
    True
    >>> inBraille[1] == "⠀⠀⠨⠏⠫⠀⠑⠙⠚⠙⠱⠀⠝⠹⠀⠚⠊⠓⠊⠺⠀⠎⠪⠀⠓⠛⠋⠛⠳⠀⠛⠋⠑⠋⠛⠑⠀⠀⠀⠀"
    True
    >>> inBraille[2] == "⠀⠀⠐⠹⠥⠣⠅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"
    True
    '''
    bm = tinyNotation.TinyNotationStream("c2 c4 d8 c8 B8 c8 d4 e2 e4 f8 e8 d8 e8 f4 g2 g4 a8 g8 f8 g8 a4 \
    b8 a8 g8 a8 b8 d'8 c'4 r2 e'2 e'4 d'8 c'8 b8 c'8 d'4 c'2 c'4 b8 a8 g8 a8 b4 a2 a4 g8 f8 e8 f8 g4 \
    f8 e8 d8 e8 f8 d8 c4 r2")
    bm.insert(0, meter.TimeSignature('3/4'))
    bm.makeMeasures(inPlace = True)
    bm[-1].append(bar.Barline('light-heavy'))
    bm[0].pop(0)
    return bm

def example4_4():
    '''
    >>> from music21.braille import translate
    >>> measure1 = example4_4()[0]
    >>> translate.measureToBraille(measure1, showLeadingOctave = False) == "⠟⠈⠉⠻⠄⠛"
    True
    '''
    bm = tinyNotation.TinyNotationStream("f2~ f4. f8")
    bm.makeMeasures(inPlace = True)
    bm[0].pop(0)
    return bm

def example4_5():
    '''
    >>> from music21.braille import translate
    >>> measure1 = example4_5()[0]
    >>> translate.measureToBraille(measure1, showLeadingOctave = False) == "⠳⠄⠈⠉⠓⠊⠓"
    True
    '''
    bm = tinyNotation.TinyNotationStream("g4.~ g8 a8 g8")
    bm.insert(0, meter.TimeSignature("3/4"))
    bm.makeMeasures(inPlace = True)
    bm[0].pop(0)
    return bm

def example4_6():
    '''
    >>> from music21.braille import translate
    >>> bm = example4_6()
    >>> measure1 = bm[0]
    >>> measure2 = bm[1]
    >>> translate.measureToBraille(measure1, showLeadingOctave = False) == "⠗⠳⠈⠉"
    True
    >>> translate.measureToBraille(measure2, showLeadingOctave = False) == "⠗⠧"
    True
    '''
    bm = tinyNotation.TinyNotationStream("g2 g4~ g2 r4")
    bm.insert(0, meter.TimeSignature("3/4"))
    bm.makeMeasures(inPlace = True)
    bm[0].pop(0)
    return bm

def example4_7():
    '''
    >>> from music21.braille import translate
    >>> inBraille = translate.partToBraille(example4_7())
    >>> inBraille[0] == "⠼⠁⠀⠐⠗⠄⠀⠏⠄⠀⠝⠄⠀⠏⠄⠀⠹⠱⠫⠀⠳⠻⠫⠀⠕⠄⠈⠉⠀⠕⠄⠀⠏⠫⠀⠫⠻⠳⠀⠀"
    True
    >>> inBraille[1] == "⠀⠀⠐⠎⠪⠀⠪⠳⠻⠀⠏⠻⠀⠕⠫⠀⠝⠄⠈⠉⠀⠝⠄⠣⠅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"
    True
    '''
    bm = tinyNotation.TinyNotationStream("g2. e2. c2. e2. c4 d4 e4 g4 f4 e4 d2.~ d2.\
    e2 e4 e4 f4 g4 a2 a4 a4 g4 f4 e2 f4 d2 e4 c2.~ c2.")
    bm.insert(0, meter.TimeSignature("3/4"))
    bm.makeMeasures(inPlace = True)
    bm[-1].append(bar.Barline('light-heavy'))
    bm[0].pop(0)
    return bm

#-------------------------------------------------------------------------------
# Chapter 5: Whole and Double Whole Notes and Rests, Measure Rests, and
# Transcriber-Added Signs

def example5_1():
    '''
    >>> from music21.braille import translate
    >>> inBraille = translate.partToBraille(example5_1())
    >>> inBraille[0] == "⠼⠁⠀⠨⠽⠀⠮⠀⠿⠀⠮⠀⠽⠀⠵⠀⠽⠈⠉⠀⠽⠀⠵⠀⠯⠀⠿⠀⠵⠀⠽⠀⠷⠀⠿⠈⠉⠀⠀⠀"
    True
    >>> inBraille[1] == "⠀⠀⠨⠿⠣⠅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"
    True
    '''
    bm = tinyNotation.TinyNotationStream("c'1 a1 f1 a1 c'1 d'1 c'1~ c'1 d'1 e'1 f'1 d'1 c'1 g'1 f'1~ f'1")
    bm.makeMeasures(inPlace = True)
    bm[-1].append(bar.Barline('light-heavy'))
    bm[0].pop(0)
    return bm

def example5_2():
    '''
    >>> from music21.braille import translate
    >>> inBraille = translate.partToBraille(example5_2())
    >>> inBraille[0] == "⠼⠁⠀⠸⠽⠀⠯⠀⠷⠀⠮⠀⠾⠀⠮⠀⠷⠈⠉⠀⠷⠀⠮⠀⠽⠀⠮⠀⠿⠀⠷⠀⠾⠀⠷⠀⠯⠀⠿⠀"
    True
    >>> inBraille[1] == "⠀⠀⠸⠮⠀⠿⠀⠵⠀⠾⠀⠵⠀⠽⠈⠉⠀⠽⠣⠅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"
    True
    '''
    bm = tinyNotation.TinyNotationStream("C1 E1 G1 A1 B1 A1 G1~ G1 A1 c1 A1 F1 G1 B1 G1 E1 F1 A1 F1 D1 BB1 D1 C1~ C1")
    bm.makeMeasures(inPlace = True)
    bm[-1].append(bar.Barline('light-heavy'))
    bm[0].pop(0)
    return bm

def example5_3():
    '''
    >>> from music21.braille import translate
    >>> inBraille = translate.partToBraille(example5_3())
    >>> inBraille[0] == "⠼⠁⠀⠍⠐⠗⠀⠗⠗⠗⠀⠳⠳⠍⠣⠅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"
    True
    '''
    bm = tinyNotation.TinyNotationStream("r1 g2 g2 g2 g2 g4 g4 r1")
    bm.insert(0, meter.TimeSignature("3/2"))
    bm.makeMeasures(inPlace = True)
    bm[-1].append(bar.Barline('light-heavy'))
    bm[0].pop(0)
    return bm

def example5_4():
    '''
    >>> from music21.braille import translate
    >>> inBraille = translate.partToBraille(example5_4())
    >>> inBraille[0] == "⠼⠁⠀⠸⠏⠟⠀⠷⠀⠏⠕⠀⠽⠀⠕⠏⠀⠟⠏⠀⠵⠀⠍⠀⠝⠕⠀⠯⠀⠟⠗⠀⠮⠀⠗⠟⠀⠏⠕⠀"
    True
    >>> inBraille[1] == "⠀⠀⠸⠽⠀⠍⠣⠅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"
    True
    '''
    bm = tinyNotation.TinyNotationStream("E2 F2 G1 E2 D2 C1 D2 E2 F2 E2 D1 r1 \
    C2 D2 E1 F2 G2 A1 G2 F2 E2 D2 C1 r1")
    bm.makeMeasures(inPlace = True)
    bm[-1].append(bar.Barline('light-heavy'))
    bm[0].pop(0)
    return bm

def example5_5():
    '''
    >>> from music21.braille import translate
    >>> inBraille = translate.partToBraille(example5_5())
    >>> inBraille[0] == "⠼⠁⠀⠸⠟⠄⠀⠍⠀⠎⠄⠀⠍⠀⠻⠳⠪⠀⠹⠪⠻⠀⠳⠥⠀⠍⠀⠏⠄⠀⠍⠀⠗⠄⠀⠍⠀⠹⠱⠫"
    True
    >>> inBraille[1] == "⠀⠀⠸⠳⠫⠹⠀⠻⠥⠀⠍⠣⠅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"
    True
    '''
    bm = tinyNotation.TinyNotationStream("F2. r2. A2. r2. F4 G4 A4 c4 A4 F4 G4 r2 r2. \
    E2. r2. G2. r2. C4 D4 E4 G4 E4 C4 F4 r2 r2.")
    bm.insert(0, meter.TimeSignature("3/4"))
    bm.makeMeasures(inPlace = True)
    bm[-1].append(bar.Barline('light-heavy'))
    bm[0].pop(0)
    bm.show()
    return bm

#-------------------------------------------------------------------------------

def example10_1():
    bm = stream.Part()
    
    m1 = stream.Measure(number = 1)
    m1.append(clef.TrebleClef())
    m1.append(key.KeySignature(-4))
    m1.append(meter.TimeSignature('6/8'))
    m1.append(note.Note('F4'))
    m1.append(note.Note('C5', quarterLength = 0.5))
    m1.append(note.Note('D-5', quarterLength = 0.5))
    m1.append(note.Note('C5', quarterLength = 0.5))
    m1.append(note.Note('B-4', quarterLength = 0.5))
    bm.append(m1)
    
    m2 = stream.Measure(number = 2)
    m2.append(meter.TimeSignature('2/4'))
    m2.append(note.Note('A-4'))
    m2.append(note.Note('G4'))
    m2.append(bar.Barline('light-light'))
    bm.append(m2)
    
    m3 = stream.Measure(number = 3)
    m3.append(key.KeySignature(-3))
    m3.append(meter.TimeSignature('6/8'))
    m3.append(note.Note('E-4', quarterLength = 0.5))
    m3.append(note.Note('E-5', quarterLength = 0.5))
    m3.append(note.Note('D5', quarterLength = 0.5))
    m3.append(note.Note('E-5'))
    m3.append(note.Note('G4'))
    bm.append(m3)
    
    m4 = stream.Measure(number = 4)
    m4.append(meter.TimeSignature('3/4'))
    m4.append(note.Note('A-4'))
    m4.append(note.Note('G4'))
    m4.append(note.Note('F4'))
    m4.append(bar.Barline('light-light'))
    bm.append(m4)
    
    m5 = stream.Measure(number = 5)
    m5.append(key.KeySignature(0))
    m5.append(note.Note('G4', quarterLength = 0.5))
    m5.append(note.Note('F4', quarterLength = 0.5))
    m5.append(note.Note('E4', quarterLength = 0.5))
    m5.append(note.Note('D4', quarterLength = 0.5))
    m5.append(note.Note('C4', quarterLength = 0.5))
    m5.append(note.Note('B3', quarterLength = 0.5))
    bm.append(m5)
    
    m6 = stream.Measure(number = 6)
    m6.append(note.Note('C4', quarterLength = 3.0))
    m6.append(bar.Barline('light-heavy'))
    bm.append(m6)
    
    return bm

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    t = translate.partToBraille(example5_5())
    for i in sorted(t.keys()):
        print t[i]
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof