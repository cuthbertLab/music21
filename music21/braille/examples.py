# -*- coding: utf-8 -*-
#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         examples.py
# Purpose:      Transcribing popular music into braille music using music21.
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2012 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import music21
import unittest

from music21 import converter
from music21 import key
from music21 import note
from music21 import tempo
from music21 import tinyNotation

from music21.braille import translate

def happyBirthday():
    '''
    If you would like to wish a visually-impaired friend happy birthday,
    this would be the way to go :-D
    
    >>> from music21.braille import examples     
    >>> print examples.happyBirthday()
    ⠀⠀⠀⠀⠀⠀⠠⠃⠗⠊⠛⠓⠞⠇⠽⠲⠀⠹⠶⠼⠁⠃⠚⠀⠩⠼⠉⠲⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠐⠑⠄⠵⠫⠱⠀⠳⠟⠀⠑⠄⠵⠫⠱⠀⠪⠗⠀⠑⠄⠵⠨⠱⠺⠀⠓⠄⠷⠻⠫
    ⠀⠀⠨⠙⠄⠽⠺⠳⠀⠪⠗⠣⠅
    '''
    hb = tinyNotation.TinyNotationStream("d8. d16 e4 d g f#2 d8. d16 e4 d a g2 d8. d16 d'4 b g8. g16 f#4 e c'8. c'16 b4 g a g2", "3/4")
    hb.insert(0, key.KeySignature(1))
    hb.insert(0, tempo.TempoText("Brightly"))
    hb.insert(0, tempo.MetronomeMark(number = 120, referent = note.QuarterNote()))
    hb.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
    return translate.partToBraille(hb)

def laDonnaEMobile():
    '''
    A piano reduction of Giuseppi Verdi's famous aria from Rigoletto,
    "La Donna É Mobile," transcribed into braille music.
     
    >>> from music21.braille import examples  
    >>> print examples.laDonnaEMobile()
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠼⠉⠦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠁⠀⠅⠜⠄⠜⠁⠇⠇⠑⠛⠗⠑⠞⠞⠕⠜⠋⠄⠍⠀⠦⠨⠑⠦⠑⠦⠑⠀⠀
    ⠀⠀⠇⠜⠘⠚⠸⠛⠼⠴⠛⠼⠴⠀⠀⠀⠀⠀⠀⠀⠀⠘⠚⠸⠛⠼⠴⠛⠼⠴
    ⠉⠀⠅⠜⠨⠦⠨⠿⠄⠏⠹⠀⠀⠀⠀⠀⠀⠀⠀⠀⠨⠙⠙⠙⠀⠀⠀⠀⠀
    ⠀⠀⠇⠜⠄⠄⠭⠸⠛⠬⠒⠛⠬⠒⠣⠜⠘⠻⠄⠀⠘⠛⠸⠛⠬⠒⠛⠬⠒
    ⠑⠀⠅⠜⠨⠦⠨⠯⠄⠕⠺⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠇⠜⠄⠄⠭⠸⠛⠼⠴⠛⠼⠴⠣⠜⠘⠻⠄
    <BLANKLINE>
    ⠋⠀⠅⠜⠄⠄⠦⠨⠑⠦⠙⠦⠚⠀⠐⠾⠄⠎⠪⠀⠀⠀⠀⠀⠀⠀⠀⠀⠨⠙⠚⠓⠀⠀⠀⠀⠀
    ⠀⠀⠇⠜⠘⠛⠸⠛⠼⠴⠛⠼⠴⠀⠭⠐⠋⠬⠒⠋⠬⠒⠣⠜⠘⠻⠄⠀⠘⠛⠸⠛⠔⠒⠛⠔⠒
    ⠊⠀⠅⠜⠐⠷⠄⠟⠻⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠇⠜⠄⠄⠭⠸⠛⠼⠴⠛⠼⠴⠣⠜⠘⠺⠄
    <BLANKLINE>
    ⠁⠚⠀⠅⠜⠄⠜⠋⠋⠄⠦⠨⠑⠦⠑⠦⠑⠀⠨⠦⠨⠿⠄⠏⠹⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠇⠜⠘⠾⠸⠛⠾⠬⠛⠾⠬⠛⠀⠀⠀⠍⠸⠛⠮⠔⠛⠮⠔⠛⠣⠜⠘⠻⠄
    ⠁⠃⠀⠅⠜⠨⠙⠙⠙⠀⠀⠀⠀⠀⠀⠀⠨⠦⠨⠯⠄⠕⠺⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠇⠜⠘⠿⠸⠛⠮⠔⠛⠮⠔⠛⠀⠍⠸⠛⠾⠬⠛⠾⠬⠛⠣⠜⠘⠺⠄
    <BLANKLINE>
    ⠁⠙⠀⠅⠜⠄⠄⠦⠨⠑⠦⠙⠦⠚⠀⠀⠐⠾⠄⠎⠪⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠇⠜⠘⠾⠸⠛⠾⠬⠛⠾⠬⠛⠀⠍⠸⠛⠮⠔⠛⠮⠔⠛⠣⠜⠘⠻⠄
    ⠁⠋⠀⠅⠜⠨⠙⠚⠓⠀⠀⠀⠀⠀⠀⠀⠐⠷⠄⠟⠻⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠇⠜⠘⠿⠸⠛⠮⠔⠛⠮⠔⠛⠀⠍⠸⠛⠾⠬⠛⠾⠬⠛⠣⠜⠘⠺⠄
    <BLANKLINE>
    ⠁⠓⠀⠅⠜⠨⠽⠄⠕⠙⠙⠀⠀⠀⠀⠀⠀⠀⠨⠿⠴⠍⠹⠬⠔⠀⠀⠀⠀⠀⠨⠵⠄⠏⠑⠑⠀⠀⠀
    ⠀⠀⠀⠇⠜⠄⠜⠍⠋⠸⠋⠓⠬⠼⠓⠬⠼⠀⠭⠸⠊⠬⠊⠬⠣⠜⠸⠻⠄⠀⠣⠸⠓⠊⠬⠼⠊⠬⠼
    ⠃⠁⠀⠅⠜⠄⠡⠨⠷⠴⠍⠱⠬⠔⠀⠀⠀⠀
    ⠀⠀⠀⠇⠜⠄⠄⠭⠐⠑⠬⠑⠬⠣⠜⠸⠳⠄
    <BLANKLINE>
    ⠃⠃⠀⠅⠜⠨⠿⠄⠗⠛⠛⠀⠀⠀⠜⠋⠋⠨⠳⠴⠛⠀⠦⠨⠯⠦⠿⠦⠯⠵⠍⠽⠍⠀⠀
    ⠀⠀⠀⠇⠜⠸⠊⠙⠬⠼⠙⠬⠼⠀⠸⠺⠄⠬⠀⠀⠀⠀⠸⠯⠬⠴⠍⠿⠼⠴⠍⠿⠬⠒⠍
    ⠃⠑⠀⠅⠜⠐⠺⠀⠀⠀
    ⠀⠀⠀⠇⠜⠸⠚⠬⠚⠬
    <BLANKLINE>
    ⠃⠑⠀⠅⠜⠄⠜⠍⠋⠨⠿⠄⠰⠟⠀⠰⠻⠨⠿⠄⠰⠟⠣⠜⠍⠀⠀⠀⠀⠰⠻⠨⠿⠄⠰⠟⠀⠀⠀⠀
    ⠀⠀⠀⠇⠜⠄⠄⠭⠀⠀⠀⠀⠀⠀⠀⠭⠸⠛⠬⠔⠭⠣⠜⠸⠻⠄⠬⠔⠀⠭⠐⠑⠬⠭⠣⠜⠐⠱⠄⠬
    ⠃⠓⠀⠅⠜⠰⠯⠿⠯⠦⠵⠍⠦⠽⠍⠀⠀⠀⠀⠨⠺⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠇⠜⠸⠯⠬⠴⠍⠿⠼⠴⠍⠿⠬⠒⠍⠀⠘⠾⠸⠿⠼⠴⠛⠼⠴
    <BLANKLINE>
    ⠃⠊⠀⠅⠜⠄⠜⠋⠨⠿⠄⠰⠟⠀⠰⠯⠨⠮⠰⠿⠋⠨⠿⠄⠰⠟⠣⠜⠍
    ⠀⠀⠀⠇⠜⠸⠛⠼⠴⠀⠀⠀⠀⠀⠭⠸⠛⠬⠒⠛⠬⠒⠣⠜⠘⠻⠄⠀⠀
    ⠉⠁⠀⠅⠜⠰⠵⠨⠿⠰⠿⠑⠨⠿⠄⠰⠟⠀⠀⠀⠀⠆⠰⠯⠨⠊⠰⠛⠋⠨⠊⠰⠛⠋⠨⠊⠰⠛
    ⠀⠀⠀⠇⠜⠄⠄⠭⠸⠛⠼⠴⠛⠼⠴⠣⠜⠘⠻⠄⠀⠘⠛⠸⠛⠔⠒⠛⠔⠒⠀⠀⠀⠀⠀⠀⠀⠀
    ⠉⠉⠀⠅⠜⠨⠚⠀
    ⠀⠀⠀⠇⠜⠸⠚⠬
    <BLANKLINE>
    ⠉⠉⠀⠅⠜⠄⠄⠭⠩⠨⠛⠀⠜⠋⠋⠨⠦⠨⠮⠄⠗⠿⠄⠏⠵⠄⠝
    ⠀⠀⠀⠇⠜⠄⠄⠄⠧⠀⠀⠀⠧⠸⠛⠬⠒⠣⠜⠸⠫⠄⠬⠴⠀⠀⠀
    ⠉⠑⠀⠅⠜⠐⠾⠍⠜⠋⠋⠋⠨⠚⠼⠴⠭⠣⠅
    ⠀⠀⠀⠇⠜⠸⠾⠬⠍⠘⠚⠬⠔⠭⠣⠅⠀⠀⠀
    <BLANKLINE>
    '''
    mob = converter.parse("http://static.musescore.com/29836/5862119bda/score.mxl").getElementsByClass('Part')
    upperPart = mob[0].makeNotation(cautionaryNotImmediateRepeat=False)
    lowerPart = mob[1].makeNotation(cautionaryNotImmediateRepeat=False)
    segmentBreaks = [(6,0.0),(10,0.0),(14,0.0),(18,0.0),(22,0.0),(25,1.0),(29,1.0),(33,0.5)]
    return translate.keyboardPartsToBraille(upperPart, lowerPart, segmentBreaks=segmentBreaks)

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof
