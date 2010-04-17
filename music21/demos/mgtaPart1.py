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
import sys

import music21
from music21 import clef
from music21 import converter
from music21 import instrument
from music21 import interval
from music21 import note
from music21 import pitch

from music21 import environment
_MOD = 'mgtaPart1.py'
environLocal = environment.Environment(_MOD)



#-------------------------------------------------------------------------------
# CHAPTER 1 


#-------------------------------------------------------------------------------
# Basic Elements

#-------------------------------------------------------------------------------
# I. Using keyboard diagrams


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



def ch1_basic_I_B(show=True, *arguments, **keywords):
    '''
    p2.
    given 2 pitches, mark on a keyboard their positions and mark 
    intervals as W for whole step and H for half step, otherwise N
    '''
    pitches = [('a#', 'b'), ('b-', 'c#'), ('g-', 'a'), ('d-', 'c##'), 
               ('f', 'e'), ('f#', 'e')]
    for i,j in pitches:
        n1 = note.Note(i)
        n2 = note.Note(j)
        i1 = interval.generateInterval(n1, n2)
        if i1.intervalClass == 1: # by interval class
            mark = "H"
        elif i1.intervalClass == 2:
            mark = "W"
        else:
            mark = "N"

# no keyboard diagram yet!
#         k1 = keyboard.Diagram()
#         k1.mark(n1, mark)
#         k1.mark(n2)
#         if show:
#             k1.show()


    
def ch1_basic_I_C_1(show=True, *arguments, **keywords):
    '''
    p3.
    start at a key marked with an ex, move finger according to pattern 
    of half and whole steps; mark key at end with an asterisk
    '''
    from music21 import stream, interval
    nStart = note.Note('a4')
    intervals = [interval.Interval('w'), interval.Interval('-h'), 
                 interval.Interval('-w'), interval.Interval('-w'),
                 interval.Interval('h')]
    s = stream.Stream()
    n = nStart
    s.append(n)
    for i in intervals:
        i.noteStart = n
        n = i.noteEnd
        s.append(n)
    if show:
        s.show()
        s.plot('PlotHorizontalBarPitchSpaceOffset')

def ch1_basic_I_C_2(show=True, *arguments, **keywords):
    '''
    p3.
    start at a key marked with an ex, move finger according to pattern of 
    half and whole steps; mark key at end with an asterisk
    '''
    from music21 import stream
    nStart = note.Note('e4')
    intervals = [interval.Interval('w'), interval.Interval('w'), 
                 interval.Interval('w'), interval.Interval('-h'),
                 interval.Interval('w'), interval.Interval('h')]
    s = stream.Stream()
    n = nStart
    s.append(n)
    for i in intervals:
        i.noteStart = n
        n = i.noteEnd
        s.append(n)
    if show:
        s.show()
        s.plot('PlotHorizontalBarPitchSpaceOffset')


#-------------------------------------------------------------------------------
# II. Staff notation


def ch1_basic_II_A_1(show=True, *arguments, **keywords):
    '''
    p3.
    Write letter names and octave designations for the pitches written 
    in the treble and bass clefs below.

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
    for n in exercise.flat.notes: # have to use flat here
        n.lyric = n.nameWithOctave
    if show: 
        exercise.show()


def ch1_basic_II_A_2(show=True, *arguments, **keywords):
    '''
    p3.
    Write letter names and octave designations for the pitches written 
    in the treble and bass clefs below.
    '''
    from music21 import clef
    humdata = '''
**kern
1BBD
1C##
1B
1DD-
1f#
1FF
1D-
1d
1CC#
1AA-
1c
1F
*-
'''
    exercise = converter.parseData(humdata)
    for n in exercise.flat.notes: # have to use flat here
        n.lyric = n.nameWithOctave
    exercise.insert(0, clef.BassClef())
    exercise = exercise.sorted # need sorted to get clef
    if show: 
        exercise.show()



def ch1_basic_II_B_1(show=True, *arguments, **keywords):
    '''
    p4.
    For each of the five trebleclef pitches on the left, write the alto-clef equivalent on the right. Then label each pitch with the correct name and octave designation.
    '''
    from music21 import clef
    humdata = '''
**kern
1B-
1f#
1a-
1c
1G#
*-
'''
    exercise = converter.parseData(humdata)
    for n in exercise.flat.notes: # have to use flat here
        n.lyric = n.nameWithOctave
    exercise.insert(0, clef.AltoClef())
    if show: 
        exercise.show()


def ch1_basic_II_B_2(show=True, *arguments, **keywords):
    '''
    p4.
    For each of the five bass clef pitches on the left, write the tenord-clef equivalent on the right. Then label each pitch with the correct name and octave designation.
    '''
    from music21 import clef, converter
    humdata = '**kern\n1F#1e-\n1B\n1D-\n1c\n*-'
    exercise = converter.parseData(humdata)
    for n in exercise.flat.notes: # have to use flat here
        n.lyric = n.nameWithOctave
    exercise.insert(0, clef.TenorClef())
    if show: 
        exercise.show()



#-----------------------------------------------------------------||||||||||||--
# Writing Exercises

#-----------------------------------------------------------------||||||||||||--
# !. Arranging


def ch1_writing_I_A_1(show=True, *arguments, **keywords):
    pass

def ch1_writing_I_A_2(show=True, *arguments, **keywords):
    pass



def ch1_writing_I_B_1(show=True, *arguments, **keywords):
    pass


def ch1_writing_I_B_2(show=True, *arguments, **keywords):
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
# !I. Composing melodies






#-----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):
    
    def runTest(self):
        pass

    def testBasic(self):
        for func in [
            ch1_basic_I_A, 
            ch1_basic_I_B,
            ch1_basic_I_C_1,
            ch1_basic_II_A_1,
            ch1_basic_I_C_2,
            ch1_basic_II_A_1,
            ch1_basic_II_A_2,
            ch1_basic_II_B_1,
            ch1_basic_II_B_2,
            ]:
            func(show=False, play=False)



        

#-----------------------------------------------------------------||||||||||||--
if __name__ == "__main__":
    if len(sys.argv) == 1:
        music21.mainTest(Test)
    else:
        ch1_basic_II_B_1(show=True)
        ch1_basic_II_B_2(show=True)

        #t = Test()
        #t.testImportClefAssign()


