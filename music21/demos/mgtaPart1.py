#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         mgtaPart1.py
# Purpose:      demonstration
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


import unittest, doctest

import music21
from music21 import clef
from music21 import instrument

#-------------------------------------------------------------------------------
# CHAPTER 1 


def ch1_basic_I_A():
    '''
    p2.
    Two possible letter names for each pitch parked above and below a position    
    '''
    pass


def ch1_basic_II_A_1():
    '''
    p3.
    Write letter names and octave designations for the pitches written in the treble and bass clefs below.

    (Data in Finale/musicxml format)
    '''
    exercise = music21.parseData("p3_II_A_1.xml")
    for thisNote in exercise.notes:
        thisNote.lyric = thisNote.noteNameWithOctave
    exercise.show()

def ch1_II_A_2():
    '''
    bass clef
    '''
    pass


def ch1_writing_I_B_3():
    '''
    p. 7.
    Transcribe Purcell, "Music for a While" for bassoon in tenor clef

    >>> a = True
    '''
    purcellScore = music21.parseData("Music_for_a_while.musicxml")
    thisClef = purcellScore.getElementsByClass(clef.Clef)[0]
    thisClef.__class__ = clef.TenorClef
    purcellScore.insert(0, instrument.Instrument('bassoon'))
    assert purcellScore.allInRange() is True
    purcellScore.playMidi()   ## will play on bassoon
    purcellScore.show() 



#-----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
            
    def testDummy(self):
        self.assertEqual(True, True)



        

#-----------------------------------------------------------------||||||||||||--
if __name__ == "__main__":
    music21.mainTest(Test)


