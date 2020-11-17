# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         examples.py
# Purpose:      Transcribing popular music into braille music using music21.
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    Copyright © 2012 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
The melody to the "Happy Birthday" song, in G major and 3/4 time.


>>> from music21.braille import examples
>>> hb = examples.happyBirthday()
>>> #_DOCS_SHOW hb.show('braille')
⠀⠀⠀⠀⠀⠀⠠⠃⠗⠊⠛⠓⠞⠇⠽⠲⠀⠹⠶⠼⠁⠃⠚⠀⠩⠼⠉⠲⠀⠀⠀⠀⠀⠀
⠼⠁⠀⠐⠑⠄⠵⠫⠱⠀⠳⠟⠀⠑⠄⠵⠫⠱⠀⠪⠗⠀⠑⠄⠵⠨⠱⠺⠀⠓⠄⠷⠻⠫
⠀⠀⠨⠙⠄⠽⠺⠳⠀⠪⠗⠣⠅


A piano reduction of Giuseppi Verdi's famous aria from the opera
Rigoletto, "La Donna É Mobile," in Bb major and 3/8 time.


>>> verdi = corpus.parse('verdi/laDonnaEMobile')
>>> #_DOCS_SHOW verdi.show('braille')
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠼⠉⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠁⠀⠨⠜⠄⠜⠁⠇⠇⠑⠛⠗⠑⠞⠞⠕⠜⠋⠄⠍⠀⠦⠨⠑⠦⠑⠦⠑⠀⠀
⠀⠀⠀⠸⠜⠘⠚⠸⠛⠼⠴⠛⠼⠴⠀⠀⠀⠀⠀⠀⠀⠀⠘⠚⠸⠛⠼⠴⠛⠼⠴
⠀⠉⠀⠨⠜⠨⠦⠨⠿⠄⠉⠏⠉⠹⠀⠀⠀⠀⠀⠀⠀⠨⠙⠙⠙⠀⠀⠀⠀⠀
⠀⠀⠀⠸⠜⠄⠄⠭⠸⠛⠬⠒⠛⠬⠒⠣⠜⠘⠻⠄⠀⠘⠛⠸⠛⠬⠒⠛⠬⠒
⠀⠑⠀⠨⠜⠨⠦⠨⠯⠄⠉⠕⠉⠺⠀⠀⠀⠀⠀⠀⠀⠦⠨⠑⠦⠙⠦⠚⠀⠀
⠀⠀⠀⠸⠜⠄⠄⠭⠸⠛⠼⠴⠛⠼⠴⠣⠜⠘⠻⠄⠀⠘⠛⠸⠛⠼⠴⠛⠼⠴
⠀⠛⠀⠨⠜⠐⠾⠄⠉⠎⠪⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠨⠙⠉⠚⠉⠓⠀⠀⠀
⠀⠀⠀⠸⠜⠄⠄⠭⠸⠛⠔⠒⠛⠔⠒⠣⠜⠘⠻⠄⠀⠘⠛⠸⠛⠔⠒⠛⠔⠒
⠀⠊⠀⠨⠜⠐⠷⠄⠉⠟⠻⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠜⠋⠋⠄⠦⠨⠑⠦⠑⠦⠑
⠀⠀⠀⠸⠜⠄⠄⠭⠸⠛⠼⠴⠛⠼⠴⠣⠜⠘⠺⠄⠀⠘⠾⠸⠛⠾⠬⠛⠾⠬⠛⠀
⠁⠁⠀⠨⠜⠨⠦⠨⠿⠄⠉⠏⠉⠹⠀⠀⠀⠀⠀⠀⠀⠀⠨⠙⠙⠙⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠸⠜⠄⠄⠍⠸⠿⠮⠔⠿⠮⠔⠿⠣⠜⠘⠻⠄⠀⠘⠿⠸⠛⠮⠔⠛⠮⠔⠛
⠁⠉⠀⠨⠜⠨⠦⠨⠯⠄⠉⠕⠉⠺⠀⠀⠀⠀⠀⠀⠀⠀⠦⠨⠑⠉⠦⠙⠉⠦⠚⠀
⠀⠀⠀⠸⠜⠄⠄⠍⠸⠿⠾⠬⠿⠾⠬⠿⠣⠜⠘⠺⠄⠀⠘⠾⠸⠛⠾⠬⠛⠾⠬⠛
⠁⠑⠀⠨⠜⠐⠾⠄⠉⠎⠪⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠨⠙⠉⠚⠉⠓⠀⠀⠀⠀
⠀⠀⠀⠸⠜⠄⠄⠍⠸⠿⠮⠔⠿⠮⠔⠿⠣⠜⠘⠻⠄⠀⠘⠿⠸⠛⠮⠔⠛⠮⠔⠛
⠁⠛⠀⠨⠜⠐⠷⠄⠉⠟⠻⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠨⠽⠄⠉⠕⠉⠙⠙⠀⠀⠀
⠀⠀⠀⠸⠜⠄⠄⠍⠸⠿⠾⠬⠿⠾⠬⠿⠣⠜⠘⠺⠄⠀⠜⠍⠋⠸⠋⠓⠬⠼⠓⠬⠼
⠁⠊⠀⠨⠜⠨⠿⠴⠍⠹⠬⠔⠀⠀⠀⠀⠀⠀⠀⠨⠵⠄⠉⠏⠉⠑⠑⠀⠀⠡⠨⠷⠴⠍⠱⠬⠔⠀⠀⠀
⠀⠀⠀⠸⠜⠄⠄⠭⠸⠊⠬⠊⠬⠣⠜⠸⠻⠄⠀⠣⠸⠓⠊⠬⠼⠊⠬⠼⠀⠭⠸⠚⠬⠚⠬⠣⠜⠸⠳⠄
⠃⠃⠀⠨⠜⠨⠿⠄⠉⠗⠉⠛⠛⠀⠜⠋⠋⠨⠳⠴⠛⠀⠦⠨⠯⠦⠿⠦⠯⠵⠍⠽⠍⠀⠀
⠀⠀⠀⠸⠜⠸⠊⠙⠬⠼⠙⠬⠼⠀⠸⠺⠄⠬⠀⠀⠀⠀⠸⠯⠬⠴⠍⠿⠼⠴⠍⠿⠬⠒⠍
⠃⠑⠀⠨⠜⠐⠺⠜⠍⠋⠨⠿⠄⠉⠰⠟⠀⠰⠻⠨⠿⠄⠉⠰⠟⠣⠜⠧⠄⠀
⠀⠀⠀⠸⠜⠸⠚⠬⠚⠬⠭⠀⠀⠀⠀⠀⠀⠭⠸⠛⠬⠔⠭⠣⠜⠸⠻⠄⠬⠔
⠃⠛⠀⠨⠜⠰⠻⠨⠿⠄⠉⠰⠟⠀⠀⠀⠀⠀⠀⠰⠯⠿⠯⠦⠵⠍⠦⠽⠍⠀⠀⠀
⠀⠀⠀⠸⠜⠄⠄⠭⠸⠚⠬⠭⠣⠜⠸⠺⠄⠬⠀⠸⠯⠬⠴⠍⠿⠼⠴⠍⠿⠬⠒⠍
⠃⠊⠀⠨⠜⠨⠺⠜⠋⠨⠿⠄⠉⠰⠟⠀⠀⠀⠰⠯⠉⠨⠮⠉⠰⠿⠉⠋⠨⠿⠄⠉⠰⠟⠣⠜⠧⠄
⠀⠀⠀⠸⠜⠘⠾⠸⠿⠼⠴⠛⠼⠴⠛⠼⠴⠀⠭⠸⠛⠬⠒⠛⠬⠒⠣⠜⠘⠻⠄⠀⠀⠀⠀⠀⠀⠀
⠉⠁⠀⠨⠜⠰⠵⠉⠨⠿⠉⠰⠿⠉⠑⠨⠿⠄⠉⠰⠟
⠀⠀⠀⠸⠜⠄⠄⠭⠸⠛⠼⠴⠛⠼⠴⠣⠜⠘⠻⠄⠀
⠉⠃⠀⠨⠜⠰⠃⠆⠰⠯⠨⠮⠰⠿⠯⠨⠮⠰⠿⠯⠨⠮⠰⠿⠀⠨⠚⠘⠆⠭⠩⠛
⠀⠀⠀⠸⠜⠘⠛⠸⠛⠔⠒⠛⠔⠒⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⠚⠬⠧⠀⠀⠀
⠉⠙⠀⠨⠜⠄⠜⠋⠋⠰⠃⠨⠦⠨⠮⠄⠗⠿⠄⠏⠵⠄⠝⠀⠐⠾⠘⠆⠍⠜⠋⠋⠋⠨⠚⠼⠴⠭⠣⠅
⠀⠀⠀⠸⠜⠄⠄⠄⠧⠸⠛⠬⠒⠣⠜⠸⠫⠄⠬⠴⠀⠀⠀⠀⠸⠾⠬⠍⠘⠚⠬⠔⠭⠣⠅⠀⠀⠀⠀⠀


The exposition to movement 1 of Mozart's K545.


>>> #_DOCS_SHOW mozart = converter.parse('mozart_k545_exposition.xml')
>>> #_DOCS_SHOW mozart.show('braille')
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠙⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠁⠀⠨⠜⠄⠜⠁⠇⠇⠑⠛⠗⠕⠨⠝⠫⠳⠀⠐⠺⠄⠉⠽⠉⠵⠹⠧⠀⠨⠎⠳⠰⠹⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠸⠜⠐⠙⠓⠋⠓⠙⠓⠋⠓⠀⠀⠀⠀⠀⠐⠑⠓⠛⠓⠙⠓⠋⠓⠀⠐⠙⠐⠊⠛⠊⠐⠙⠓⠋⠓
⠀⠙⠀⠨⠜⠨⠳⠛⠉⠯⠉⠿⠫⠧⠀⠀⠐⠊⠾⠽⠵⠋⠛⠓⠮⠓⠛⠋⠵⠙⠚⠊
⠀⠀⠀⠸⠜⠸⠚⠐⠓⠑⠓⠙⠓⠋⠓⠀⠐⠻⠧⠧⠸⠻⠔⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠋⠀⠨⠜⠐⠓⠮⠾⠽⠑⠋⠛⠷⠛⠋⠑⠽⠚⠊⠓⠀⠐⠛⠷⠮⠾⠙⠑⠋⠿⠋⠑⠙⠾⠊⠓⠛
⠀⠀⠀⠸⠜⠸⠫⠴⠧⠧⠫⠴⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⠱⠴⠧⠧⠱⠴⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠓⠀⠨⠜⠐⠋⠿⠷⠮⠚⠙⠑⠯⠑⠙⠚⠮⠓⠛⠋⠀⠐⠑⠯⠿⠷⠊⠚⠩⠙⠵⠐⠊⠚⠙⠵⠋⠛⠓
⠀⠀⠀⠸⠜⠸⠹⠤⠧⠧⠹⠬⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⠿⠬⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠁⠚⠀⠨⠜⠨⠮⠚⠙⠚⠮⠓⠛⠋⠿⠓⠊⠓⠿⠋⠑⠙
⠀⠀⠀⠸⠜⠸⠻⠄⠓⠪⠄⠩⠛⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠁⠁⠀⠨⠜⠐⠚⠨⠓⠋⠙⠑⠓⠋⠙⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠨⠱⠳⠼⠴⠐⠳⠧⠣⠅
⠀⠀⠀⠸⠜⠘⠷⠚⠑⠓⠘⠷⠸⠙⠋⠓⠘⠷⠚⠑⠓⠘⠷⠸⠙⠋⠓⠀⠘⠳⠸⠳⠘⠳⠧⠣⠅⠀




>>> print(braille.translate.objectToBraille(verdi.measures(1, 3), debug=True))
---begin grand segment---
<music21.braille.segment BrailleGrandSegment>
===
Measure 1 Right, Signature Grouping 1:
Key Signature 2 flat(s) ⠣⠣
Time Signature 3/8 ⠼⠉⠦
<BLANKLINE>
Measure 1 Left, Signature Grouping 1:
B- major
<music21.meter.TimeSignature 3/8>
====
Measure 1 Right, Note Grouping 1:
<music21.clef.TrebleClef>
Word ⠜
Text Expression Allegretto ⠁⠇⠇⠑⠛⠗⠑⠞⠞⠕
Word: ⠜
Dynamic f ⠋
Dot 3 ⠄
Rest whole ⠍
<BLANKLINE>
Measure 1 Left, Note Grouping 1:
<music21.clef.BassClef>
Octave 2 ⠘
B eighth ⠚
Ascending Chord:
Octave 3 ⠸
F eighth ⠛
Interval 4 ⠼
Interval 6 ⠴
Ascending Chord:
F eighth ⠛
Interval 4 ⠼
Interval 6 ⠴
** Grouping x 2 **
====
Measure 2 Right, Note Grouping 1:
Articulation staccato ⠦
Octave 5 ⠨
D eighth ⠑
Articulation staccato ⠦
D eighth ⠑
Articulation staccato ⠦
D eighth ⠑
<BLANKLINE>
====
Measure 3 Right, Note Grouping 1:
Articulation accent ⠨⠦
Octave 5 ⠨
F 16th ⠿
Dot ⠄
Opening single slur ⠉
E 32nd ⠏
Opening single slur ⠉
C quarter ⠹
<BLANKLINE>
Measure 3 Left, Inaccord Grouping 1:
Rest eighth ⠭
Ascending Chord:
Octave 3 ⠸
F eighth ⠛
Interval 3 ⠬
Interval 7 ⠒
Ascending Chord:
F eighth ⠛
Interval 3 ⠬
Interval 7 ⠒
Octave 2 ⠘
F quarter ⠻
Dot ⠄
====
<BLANKLINE>
---end grand segment---

'''

import unittest

from music21 import key
from music21 import note
from music21 import tempo
from music21 import converter

def cp(strIn):
    return converter.parse(strIn, makeNotation=False)

def happyBirthday():
    '''
    fully copyright free!
    '''
    hb = cp("tinynotation: 3/4 d8. d16 e4 d g f#2 d8. d16 e4 d a g2 d8. "
            + "d16 d'4 b g8. g16 f#4 e c'8. c'16 b4 g a g2")
    hb.insert(0, key.KeySignature(1))
    hb.insert(0, tempo.TempoText('Brightly'))
    hb.insert(0, tempo.MetronomeMark(number=120, referent=note.Note(type='quarter')))
    hb.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return hb

# ------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def testHappyBirthdayDebug(self):
        from music21.braille.translate import objectToBraille
        hb = happyBirthday()
        x = objectToBraille(hb, debug=True)
        y = '''---begin segment---
<music21.braille.segment BrailleSegment>
Measure 1, Signature Grouping 1:
Key Signature 1 sharp(s) ⠩
Time Signature 3/4 ⠼⠉⠲
===
Measure 1, Tempo Text Grouping 1:
Tempo Text Brightly ⠠⠃⠗⠊⠛⠓⠞⠇⠽⠲
===
Measure 1, Metronome Mark Grouping 1:
Metronome Note C quarter ⠹
Metronome symbol ⠶
Metronome number 120 ⠼⠁⠃⠚
===
Measure 1, Note Grouping 1:
<music21.clef.TrebleClef>
Octave 4 ⠐
D eighth ⠑
Dot ⠄
D 16th ⠵
E quarter ⠫
D quarter ⠱
===
Measure 2, Note Grouping 1:
G quarter ⠳
F half ⠟
===
Measure 3, Note Grouping 1:
D eighth ⠑
Dot ⠄
D 16th ⠵
E quarter ⠫
D quarter ⠱
===
Measure 4, Note Grouping 1:
A quarter ⠪
G half ⠗
===
Measure 5, Note Grouping 1:
D eighth ⠑
Dot ⠄
D 16th ⠵
Octave 5 ⠨
D quarter ⠱
B quarter ⠺
===
Measure 6, Note Grouping 1:
G eighth ⠓
Dot ⠄
G 16th ⠷
F quarter ⠻
E quarter ⠫
===
Measure 7, Note Grouping 1:
Octave 5 ⠨
C eighth ⠙
Dot ⠄
C 16th ⠽
B quarter ⠺
G quarter ⠳
===
Measure 8, Note Grouping 1:
A quarter ⠪
G half ⠗
Barline final ⠣⠅
===
---end segment---
'''
        self.assertEqual(x.splitlines(), y.splitlines())

    def testVerdiDebug(self):
        # self.maxDiff = None
        from music21 import corpus
        from music21.braille.translate import objectToBraille
        verdi = corpus.parse('verdi/laDonnaEMobile')
        x = objectToBraille(verdi, debug=True)
        y = '''---begin grand segment---
<music21.braille.segment BrailleGrandSegment>
===
Measure 1 Right, Signature Grouping 1:
Key Signature 2 flat(s) ⠣⠣
Time Signature 3/8 ⠼⠉⠦

Measure 1 Left, Signature Grouping 1:
B- major
<music21.meter.TimeSignature 3/8>
====
Measure 1 Right, Note Grouping 1:
<music21.clef.TrebleClef>
Word ⠜
Text Expression Allegretto ⠁⠇⠇⠑⠛⠗⠑⠞⠞⠕
Word: ⠜
Dynamic f ⠋
Dot 3 ⠄
Rest whole ⠍

Measure 1 Left, Note Grouping 1:
<music21.clef.BassClef>
Octave 2 ⠘
B eighth ⠚
Ascending Chord:
Octave 3 ⠸
F eighth ⠛
Interval 4 ⠼
Interval 6 ⠴
Ascending Chord:
F eighth ⠛
Interval 4 ⠼
Interval 6 ⠴
** Grouping x 2 **
====
Measure 2 Right, Note Grouping 1:
Articulation staccato ⠦
Octave 5 ⠨
D eighth ⠑
Articulation staccato ⠦
D eighth ⠑
Articulation staccato ⠦
D eighth ⠑

====
Measure 3 Right, Note Grouping 1:
Articulation accent ⠨⠦
Octave 5 ⠨
F 16th ⠿
Dot ⠄
Opening single slur ⠉
E 32nd ⠏
Opening single slur ⠉
C quarter ⠹

Measure 3 Left, Inaccord Grouping 1:
Rest eighth ⠭
Ascending Chord:
Octave 3 ⠸
F eighth ⠛
Interval 3 ⠬
Interval 7 ⠒
Ascending Chord:
F eighth ⠛
Interval 3 ⠬
Interval 7 ⠒
Octave 2 ⠘
F quarter ⠻
Dot ⠄
====
Measure 4 Right, Note Grouping 1:
Octave 5 ⠨
C eighth ⠙
C eighth ⠙
C eighth ⠙

Measure 4 Left, Note Grouping 1:
Octave 2 ⠘
F eighth ⠛
Ascending Chord:
Octave 3 ⠸
F eighth ⠛
Interval 3 ⠬
Interval 7 ⠒
Ascending Chord:
F eighth ⠛
Interval 3 ⠬
Interval 7 ⠒
====
Measure 5 Right, Note Grouping 1:
Articulation accent ⠨⠦
Octave 5 ⠨
E 16th ⠯
Dot ⠄
Opening single slur ⠉
D 32nd ⠕
Opening single slur ⠉
B quarter ⠺

Measure 5 Left, Inaccord Grouping 1:
Rest eighth ⠭
Ascending Chord:
Octave 3 ⠸
F eighth ⠛
Interval 4 ⠼
Interval 6 ⠴
Ascending Chord:
F eighth ⠛
Interval 4 ⠼
Interval 6 ⠴
Octave 2 ⠘
F quarter ⠻
Dot ⠄
====
Measure 6 Right, Note Grouping 1:
Articulation staccato ⠦
Octave 5 ⠨
D eighth ⠑
Articulation staccato ⠦
C eighth ⠙
Articulation staccato ⠦
B eighth ⠚

Measure 6 Left, Note Grouping 1:
Octave 2 ⠘
F eighth ⠛
Ascending Chord:
Octave 3 ⠸
F eighth ⠛
Interval 4 ⠼
Interval 6 ⠴
Ascending Chord:
F eighth ⠛
Interval 4 ⠼
Interval 6 ⠴
====
Measure 7 Right, Note Grouping 1:
Octave 5 ⠨
C eighth Gracenote--not supported ⠙
B 16th ⠾
Dot ⠄
Opening single slur ⠉
A 32nd ⠎
A quarter ⠪

Measure 7 Left, Inaccord Grouping 1:
Rest eighth ⠭
Ascending Chord:
Octave 3 ⠸
F eighth ⠛
Interval 5 ⠔
Interval 7 ⠒
Ascending Chord:
F eighth ⠛
Interval 5 ⠔
Interval 7 ⠒
Octave 2 ⠘
F quarter ⠻
Dot ⠄
====
Measure 8 Right, Note Grouping 1:
Octave 5 ⠨
C eighth ⠙
Opening single slur ⠉
B eighth ⠚
Opening single slur ⠉
G eighth ⠓

Measure 8 Left, Note Grouping 1:
Octave 2 ⠘
F eighth ⠛
Ascending Chord:
Octave 3 ⠸
F eighth ⠛
Interval 5 ⠔
Interval 7 ⠒
Ascending Chord:
F eighth ⠛
Interval 5 ⠔
Interval 7 ⠒
====
Measure 9 Right, Note Grouping 1:
Octave 4 ⠐
A eighth Gracenote--not supported ⠊
G 16th ⠷
Dot ⠄
Opening single slur ⠉
F 32nd ⠟
F quarter ⠻

Measure 9 Left, Inaccord Grouping 1:
Rest eighth ⠭
Ascending Chord:
Octave 3 ⠸
F eighth ⠛
Interval 4 ⠼
Interval 6 ⠴
Ascending Chord:
F eighth ⠛
Interval 4 ⠼
Interval 6 ⠴
Octave 2 ⠘
B quarter ⠺
Dot ⠄
====
Measure 10 Right, Note Grouping 1:
Word: ⠜
Dynamic ff ⠋⠋
Dot 3 ⠄
Articulation staccato ⠦
Octave 5 ⠨
D eighth ⠑
Articulation staccato ⠦
D eighth ⠑
Articulation staccato ⠦
D eighth ⠑

Measure 10 Left, Note Grouping 1:
Octave 2 ⠘
B 16th ⠾
Octave 3 ⠸
F beam ⠛
Ascending Chord:
B 16th ⠾
Interval 3 ⠬
F beam ⠛
Ascending Chord:
B 16th ⠾
Interval 3 ⠬
F beam ⠛
====
Measure 11 Right, Note Grouping 1:
Articulation accent ⠨⠦
Octave 5 ⠨
F 16th ⠿
Dot ⠄
Opening single slur ⠉
E 32nd ⠏
Opening single slur ⠉
C quarter ⠹

Measure 11 Left, Inaccord Grouping 1:
Rest 16th ⠍
Octave 3 ⠸
F 16th ⠿
Ascending Chord:
A 16th ⠮
Interval 5 ⠔
F 16th ⠿
Ascending Chord:
A 16th ⠮
Interval 5 ⠔
F 16th ⠿
Octave 2 ⠘
F quarter ⠻
Dot ⠄
====
Measure 12 Right, Note Grouping 1:
Octave 5 ⠨
C eighth ⠙
C eighth ⠙
C eighth ⠙

Measure 12 Left, Note Grouping 1:
Octave 2 ⠘
F 16th ⠿
Octave 3 ⠸
F beam ⠛
Ascending Chord:
A 16th ⠮
Interval 5 ⠔
F beam ⠛
Ascending Chord:
A 16th ⠮
Interval 5 ⠔
F beam ⠛
====
Measure 13 Right, Note Grouping 1:
Articulation accent ⠨⠦
Octave 5 ⠨
E 16th ⠯
Dot ⠄
Opening single slur ⠉
D 32nd ⠕
Opening single slur ⠉
B quarter ⠺

Measure 13 Left, Inaccord Grouping 1:
Rest 16th ⠍
Octave 3 ⠸
F 16th ⠿
Ascending Chord:
B 16th ⠾
Interval 3 ⠬
F 16th ⠿
Ascending Chord:
B 16th ⠾
Interval 3 ⠬
F 16th ⠿
Octave 2 ⠘
B quarter ⠺
Dot ⠄
====
Measure 14 Right, Note Grouping 1:
Articulation staccato ⠦
Octave 5 ⠨
D eighth ⠑
Opening single slur ⠉
Articulation staccato ⠦
C eighth ⠙
Opening single slur ⠉
Articulation staccato ⠦
B eighth ⠚

Measure 14 Left, Note Grouping 1:
Octave 2 ⠘
B 16th ⠾
Octave 3 ⠸
F beam ⠛
Ascending Chord:
B 16th ⠾
Interval 3 ⠬
F beam ⠛
Ascending Chord:
B 16th ⠾
Interval 3 ⠬
F beam ⠛
====
Measure 15 Right, Note Grouping 1:
Octave 5 ⠨
C eighth Gracenote--not supported ⠙
B 16th ⠾
Dot ⠄
Opening single slur ⠉
A 32nd ⠎
A quarter ⠪

Measure 15 Left, Inaccord Grouping 1:
Rest 16th ⠍
Octave 3 ⠸
F 16th ⠿
Ascending Chord:
A 16th ⠮
Interval 5 ⠔
F 16th ⠿
Ascending Chord:
A 16th ⠮
Interval 5 ⠔
F 16th ⠿
Octave 2 ⠘
F quarter ⠻
Dot ⠄
====
Measure 16 Right, Note Grouping 1:
Octave 5 ⠨
C eighth ⠙
Opening single slur ⠉
B eighth ⠚
Opening single slur ⠉
G eighth ⠓

Measure 16 Left, Note Grouping 1:
Octave 2 ⠘
F 16th ⠿
Octave 3 ⠸
F beam ⠛
Ascending Chord:
A 16th ⠮
Interval 5 ⠔
F beam ⠛
Ascending Chord:
A 16th ⠮
Interval 5 ⠔
F beam ⠛
====
Measure 17 Right, Note Grouping 1:
Octave 4 ⠐
A eighth Gracenote--not supported ⠊
G 16th ⠷
Dot ⠄
Opening single slur ⠉
F 32nd ⠟
F quarter ⠻

Measure 17 Left, Inaccord Grouping 1:
Rest 16th ⠍
Octave 3 ⠸
F 16th ⠿
Ascending Chord:
B 16th ⠾
Interval 3 ⠬
F 16th ⠿
Ascending Chord:
B 16th ⠾
Interval 3 ⠬
F 16th ⠿
Octave 2 ⠘
B quarter ⠺
Dot ⠄
====
Measure 18 Right, Note Grouping 1:
Octave 5 ⠨
C 16th ⠽
Dot ⠄
Opening single slur ⠉
D 32nd ⠕
Opening single slur ⠉
C eighth ⠙
C eighth ⠙

Measure 18 Left, Note Grouping 1:
Word: ⠜
Dynamic mf ⠍⠋
Octave 3 ⠸
E eighth ⠋
Ascending Chord:
G eighth ⠓
Interval 3 ⠬
Interval 4 ⠼
Ascending Chord:
G eighth ⠓
Interval 3 ⠬
Interval 4 ⠼
====
Measure 19 Right, Note Grouping 1:
Accidental natural ⠡
Octave 5 ⠨
E eighth Gracenote--not supported ⠋
Descending Chord:
F 16th ⠿
Interval 6 ⠴
Rest 16th ⠍
Descending Chord:
C quarter ⠹
Interval 3 ⠬
Interval 5 ⠔

Measure 19 Left, Inaccord Grouping 1:
Rest eighth ⠭
Ascending Chord:
Octave 3 ⠸
A eighth ⠊
Interval 3 ⠬
Ascending Chord:
A eighth ⠊
Interval 3 ⠬
Octave 3 ⠸
F quarter ⠻
Dot ⠄
====
Measure 20 Right, Note Grouping 1:
Octave 5 ⠨
D 16th ⠵
Dot ⠄
Opening single slur ⠉
E 32nd ⠏
Opening single slur ⠉
D eighth ⠑
D eighth ⠑

Measure 20 Left, Note Grouping 1:
Accidental flat ⠣
Octave 3 ⠸
G eighth ⠓
Ascending Chord:
A eighth ⠊
Interval 3 ⠬
Interval 4 ⠼
Ascending Chord:
A eighth ⠊
Interval 3 ⠬
Interval 4 ⠼
====
Measure 21 Right, Note Grouping 1:
Accidental flat ⠣
Octave 5 ⠨
G eighth Gracenote--not supported ⠓
Descending Chord:
Accidental natural ⠡
G 16th ⠷
Interval 6 ⠴
Rest 16th ⠍
Descending Chord:
D quarter ⠱
Interval 3 ⠬
Interval 5 ⠔

Measure 21 Left, Inaccord Grouping 1:
Rest eighth ⠭
Ascending Chord:
Octave 3 ⠸
B eighth ⠚
Interval 3 ⠬
Ascending Chord:
B eighth ⠚
Interval 3 ⠬
Octave 3 ⠸
G quarter ⠳
Dot ⠄
====
Measure 22 Right, Note Grouping 1:
Octave 5 ⠨
F 16th ⠿
Dot ⠄
Opening single slur ⠉
G 32nd ⠗
Opening single slur ⠉
F eighth ⠛
F eighth ⠛

Measure 22 Left, Note Grouping 1:
Octave 3 ⠸
A eighth ⠊
Ascending Chord:
C eighth ⠙
Interval 3 ⠬
Interval 4 ⠼
Ascending Chord:
C eighth ⠙
Interval 3 ⠬
Interval 4 ⠼
====
Measure 23 Right, Note Grouping 1:
Word: ⠜
Dynamic ff ⠋⠋
Descending Chord:
Octave 5 ⠨
G quarter ⠳
Interval 6 ⠴
F eighth ⠛

Measure 23 Left, Note Grouping 1:
Ascending Chord:
Octave 3 ⠸
B quarter ⠺
Dot ⠄
Interval 3 ⠬
====
Measure 24 Right, Note Grouping 1:
Triplet ⠆
Articulation staccato ⠦
Octave 5 ⠨
E 16th ⠯
Articulation staccato ⠦
F 16th ⠿
Articulation staccato ⠦
E 16th ⠯
D 16th ⠵
Rest 16th ⠍
C 16th ⠽
Rest 16th ⠍

Measure 24 Left, Note Grouping 1:
Ascending Chord:
Octave 3 ⠸
E 16th ⠯
Interval 3 ⠬
Interval 6 ⠴
Rest 16th ⠍
Ascending Chord:
F 16th ⠿
Interval 4 ⠼
Interval 6 ⠴
Rest 16th ⠍
Ascending Chord:
F 16th ⠿
Interval 3 ⠬
Interval 7 ⠒
Rest 16th ⠍
====
Measure 25 Right, Note Grouping 1:
Octave 4 ⠐
B quarter ⠺
Word: ⠜
Dynamic mf ⠍⠋
Octave 5 ⠨
F 16th ⠿
Dot ⠄
Opening single slur ⠉
Octave 6 ⠰
F 32nd ⠟

Measure 25 Left, Note Grouping 1:
Ascending Chord:
Octave 3 ⠸
B eighth ⠚
Interval 3 ⠬
Ascending Chord:
B eighth ⠚
Interval 3 ⠬
Rest eighth ⠭
====
Measure 26 Right, Inaccord Grouping 1:
Octave 6 ⠰
F quarter ⠻
Octave 5 ⠨
F 16th ⠿
Dot ⠄
Opening single slur ⠉
Octave 6 ⠰
F 32nd ⠟
Rest quarter ⠧
Dot ⠄

Measure 26 Left, Inaccord Grouping 1:
Rest eighth ⠭
Ascending Chord:
Octave 3 ⠸
F eighth ⠛
Interval 3 ⠬
Interval 5 ⠔
Rest eighth ⠭
Ascending Chord:
Octave 3 ⠸
F quarter ⠻
Dot ⠄
Interval 3 ⠬
Interval 5 ⠔
====
Measure 27 Right, Note Grouping 1:
Octave 6 ⠰
F quarter ⠻
Octave 5 ⠨
F 16th ⠿
Dot ⠄
Opening single slur ⠉
Octave 6 ⠰
F 32nd ⠟

Measure 27 Left, Inaccord Grouping 1:
Rest eighth ⠭
Ascending Chord:
Octave 3 ⠸
B eighth ⠚
Interval 3 ⠬
Rest eighth ⠭
Ascending Chord:
Octave 3 ⠸
B quarter ⠺
Dot ⠄
Interval 3 ⠬
====
Measure 28 Right, Note Grouping 1:
Triplet ⠆
Octave 6 ⠰
E 16th ⠯
F 16th ⠿
E 16th ⠯
Articulation staccato ⠦
D 16th ⠵
Rest 16th ⠍
Articulation staccato ⠦
C 16th ⠽
Rest 16th ⠍

Measure 28 Left, Note Grouping 1:
Ascending Chord:
Octave 3 ⠸
E 16th ⠯
Interval 3 ⠬
Interval 6 ⠴
Rest 16th ⠍
Ascending Chord:
F 16th ⠿
Interval 4 ⠼
Interval 6 ⠴
Rest 16th ⠍
Ascending Chord:
F 16th ⠿
Interval 3 ⠬
Interval 7 ⠒
Rest 16th ⠍
====
Measure 29 Right, Note Grouping 1:
Octave 5 ⠨
B quarter ⠺
Word: ⠜
Dynamic f ⠋
Octave 5 ⠨
F 16th ⠿
Dot ⠄
Opening single slur ⠉
Octave 6 ⠰
F 32nd ⠟

Measure 29 Left, Note Grouping 1:
Octave 2 ⠘
B 16th ⠾
Ascending Chord:
Octave 3 ⠸
F 16th ⠿
Interval 4 ⠼
Interval 6 ⠴
Ascending Chord:
F eighth ⠛
Interval 4 ⠼
Interval 6 ⠴
Ascending Chord:
F eighth ⠛
Interval 4 ⠼
Interval 6 ⠴
====
Measure 30 Right, Inaccord Grouping 1:
Octave 6 ⠰
E 16th ⠯
Opening single slur ⠉
Octave 5 ⠨
A 16th ⠮
Opening single slur ⠉
Octave 6 ⠰
F 16th ⠿
Opening single slur ⠉
E eighth ⠋
Octave 5 ⠨
F 16th ⠿
Dot ⠄
Opening single slur ⠉
Octave 6 ⠰
F 32nd ⠟
Rest quarter ⠧
Dot ⠄

Measure 30 Left, Inaccord Grouping 1:
Rest eighth ⠭
Ascending Chord:
Octave 3 ⠸
F eighth ⠛
Interval 3 ⠬
Interval 7 ⠒
Ascending Chord:
F eighth ⠛
Interval 3 ⠬
Interval 7 ⠒
Octave 2 ⠘
F quarter ⠻
Dot ⠄
====
Measure 31 Right, Note Grouping 1:
Octave 6 ⠰
D 16th ⠵
Opening single slur ⠉
Octave 5 ⠨
F 16th ⠿
Opening single slur ⠉
Octave 6 ⠰
F 16th ⠿
Opening single slur ⠉
D eighth ⠑
Octave 5 ⠨
F 16th ⠿
Dot ⠄
Opening single slur ⠉
Octave 6 ⠰
F 32nd ⠟

Measure 31 Left, Inaccord Grouping 1:
Rest eighth ⠭
Ascending Chord:
Octave 3 ⠸
F eighth ⠛
Interval 4 ⠼
Interval 6 ⠴
Ascending Chord:
F eighth ⠛
Interval 4 ⠼
Interval 6 ⠴
Octave 2 ⠘
F quarter ⠻
Dot ⠄
====
Measure 32 Right, Note Grouping 1:
Opening bracket slur ⠰⠃
Triplet ⠆
Octave 6 ⠰
E 16th ⠯
Octave 5 ⠨
A 16th ⠮
Octave 6 ⠰
F 16th ⠿
Triplet ⠆
E 16th ⠯
Octave 5 ⠨
A 16th ⠮
Octave 6 ⠰
F 16th ⠿
Triplet ⠆
E 16th ⠯
Octave 5 ⠨
A 16th ⠮
Octave 6 ⠰
F 16th ⠿

Measure 32 Left, Note Grouping 1:
Octave 2 ⠘
F eighth ⠛
Ascending Chord:
Octave 3 ⠸
F eighth ⠛
Interval 5 ⠔
Interval 7 ⠒
Ascending Chord:
F eighth ⠛
Interval 5 ⠔
Interval 7 ⠒
====
Measure 33 Right, Note Grouping 1:
Octave 5 ⠨
B eighth ⠚
Closing bracket slur ⠘⠆
Rest eighth ⠭
Accidental sharp ⠩
F eighth ⠛

Measure 33 Left, Note Grouping 1:
Ascending Chord:
Octave 3 ⠸
B eighth ⠚
Interval 3 ⠬
Rest quarter ⠧
====
Measure 34 Right, Note Grouping 1:
Word: ⠜
Dynamic ff ⠋⠋
Opening bracket slur ⠰⠃
Articulation accent ⠨⠦
Octave 5 ⠨
A 16th ⠮
Dot ⠄
G 32nd ⠗
F 16th ⠿
Dot ⠄
E 32nd ⠏
D 16th ⠵
Dot ⠄
C 32nd ⠝

Measure 34 Left, Inaccord Grouping 1:
Rest quarter ⠧
Ascending Chord:
Octave 3 ⠸
F eighth ⠛
Interval 3 ⠬
Interval 7 ⠒
Ascending Chord:
Octave 3 ⠸
E quarter ⠫
Dot ⠄
Interval 3 ⠬
Interval 6 ⠴
====
Measure 35 Right, Note Grouping 1:
Octave 4 ⠐
B 16th ⠾
Closing bracket slur ⠘⠆
Rest 16th ⠍
Word: ⠜
Dynamic fff ⠋⠋⠋
Descending Chord:
Octave 5 ⠨
B eighth ⠚
Interval 4 ⠼
Interval 6 ⠴
Rest eighth ⠭
Barline final ⠣⠅

Measure 35 Left, Note Grouping 1:
Ascending Chord:
Octave 3 ⠸
B 16th ⠾
Interval 3 ⠬
Rest 16th ⠍
Ascending Chord:
Octave 2 ⠘
B eighth ⠚
Interval 3 ⠬
Interval 5 ⠔
Rest eighth ⠭
Barline final ⠣⠅
====

---end grand segment---
'''
        self.maxDiff = None
        self.assertEqual(x.splitlines(), y.splitlines())


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)  # , runTest='testVerdiDebug')

