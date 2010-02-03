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
from music21 import pitch
from music21 import clef
from music21 import note
from music21 import instrument
from music21 import converter

#-------------------------------------------------------------------------------
# CHAPTER 1 


def ch1_basic_I_A(show=True, *arguments, **keywords):
    '''
    p2.
    For a given pitch name, give two possible enharmonic equivalents with
    octave designation
    '''
    pitches = ['d#3', 'g3', 'g#3', 'c#4', 'd4', 'a4', 'a#4', 'e5', 'f#5', 'a5']
    found = []
    for p in pitches:
        n = note.Note(p)
        
        # get direction of enharmonic move?
        # a move upward goes from f to g-, then a---
        #n.pitch.getEnharmonic(1) 
        found.append(None)
    if show:
        for i in range(len(pitches)):
            print(str(pitches[i]).ljust(10) + str(found[i]))

def ch1_basic_II_A_1(show=True, *arguments, **keywords):
    '''
    p3.
    Write letter names and octave designations for the pitches written in the treble and bass clefs below.

    (Data in Finale/musicxml format)
    '''
    humdata = '''
**kern
1gg#
1B
1a##
1ddd-
1c#
1dd
1G
1b-
1ccc
1f-
1aa-
1e--
*-
'''
    exercise = converter.parseData(humdata)
    #exercise = music21.parseData("ch1_basic_II_A_1.xml")
    for thisNote in exercise.flat.notes: # have to use flat here
        thisNote.lyric = thisNote.nameWithOctave
    if show: exercise.show()

def ch1_basic_II_A_2(show=True, *arguments, **keywords):
    '''
    bass clef
    '''
    pass


def ch1_writing_I_B_3(show=True, *arguments, **keywords):
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
            
    def testBasic(self):
        for func in [ch1_basic_I_A, 
                     ch1_basic_II_A_1]:
            func(show=False, play=False)



        

#-----------------------------------------------------------------||||||||||||--
if __name__ == "__main__":
    music21.mainTest(Test)


