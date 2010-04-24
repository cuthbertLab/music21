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
        i1 = interval.notesToInterval(n1, n2)
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
    For each of the five bass clef pitches on the left, write the tenor-clef equivalent on the right. Then label each pitch with the correct name and octave designation.
    '''
    from music21 import clef, converter
    humdata = '**kern\n1F#1e-\n1B\n1D-\n1c\n*-'
    exercise = converter.parseData(humdata)
    for n in exercise.flat.notes: # have to use flat here
        n.lyric = n.nameWithOctave
    exercise.insert(0, clef.TenorClef())
    if show: 
        exercise.show()



def ch1_basic_II_C_1(show=True, *arguments, **keywords):
    '''
    p. 4
    Practice writing whole and half steps. Watch for changes in clef.
    Write hole steps
    '''
    from music21 import stream, clef, common
    ex = stream.Stream()
    data = [[clef.TrebleClef(), 'g#4', 'b-4', 'd-4'], 
            [clef.BassClef(), 'e3', 'a-2'], 
            [clef.TenorClef(), 'c#']]
    for chunk in data:
        m = stream.Measure()    
        for e in chunk:
            if common.isStr(e):
                n = note.Note(e)
                n.quarterLength = 4
                m.append(n)
            else:
                m.append(e)
        m.timeSignature = m.bestTimeSignature()
        ex.append(m)
    #ex.show('t')
    ex.show()

def ch1_basic_II_C_2(show=True, *arguments, **keywords):
    pass

def ch1_basic_II_C_3(show=True, *arguments, **keywords):
    pass


def ch1_basic_II_C_4(show=True, *arguments, **keywords):
    pass



#-----------------------------------------------------------------||||||||||||--
# Writing Exercises

#-----------------------------------------------------------------||||||||||||--
# !. Arranging


def ch1_writing_I_A_1(show=True, *arguments, **keywords):
    '''
    p. 5
    Rewrite these melodies from music literature, placing the pitches one octave higher or lower as specified, by using ledger lines. Do not change to a new clef.

    Rewrite one active higher 
    '''
    from music21 import converter, clef

    # Purcell, "Music for a While"
    humdata = '''
**kern
8C
8D
8E
8EE
8AA
8E
8F
8AA
8BB
8F#
8G
8BB
8C
8G#
8A
8C#
*-
'''
    ex = converter.parseData(humdata)
    ex = ex.transpose('p8')
    ex.insert(0, clef.BassClef()) # maintain clef
    if show:
        ex.show()


def ch1_writing_I_A_2(show=True, *arguments, **keywords):
    '''
    p. 5 
    Rewrite one octave higher
    '''
    humdata = '''
**kern
6e
6e
6e
6e
6f
6g
*-
'''
    # this notation excerpt is incomplete
    ex = converter.parseData(humdata)
    ex = ex.transpose('p8')
    ex.insert(0, clef.TrebleClef()) # maintain clef
    if show:
        ex.show()


def ch1_writing_I_B_1(show=True, *arguments, **keywords):
    '''
    p.6 
    Transcribe these melodies into the clef specified without changing octaves.
    '''
    from music21 import converter, clef, tinyNotation

    # camptown races
    ex = tinyNotation.TinyNotationStream("g8 g e g", "2/4")
    ex.insert(0, clef.AltoClef()) # maintain clef
    if show:
        ex.show()



def ch1_writing_I_B_2(show=True, *arguments, **keywords):
    '''
    Transcribe the melody into treble clef
    '''
    # Mozart no. 41, 4th movement
    humdata = '''
**kern
*clefC3 
4g
4g
4G
4G
*-
'''
    # this notation excerpt is incomplete
    ex = converter.parseData(humdata)
    clefOld = ex.flat.getElementsByClass(clef.Clef)[0]
    ex.flat.replace(clefOld, clef.TrebleClef())
    if show:
        ex.show()


def ch1_writing_I_B_3(show=True, *arguments, **keywords):
    '''
    p. 7.
    Transcribe Purcell, "Music for a While" for bassoon in tenor clef

    >>> a = True
    '''

    from music21 import converter, clef, parse

    # Purcell, "Music for a While"
    humdata = '''
**kern
*clefF4 
8C
8D
8E
8EE
8AA
8E
8F
8AA
8BB
8F#
8G
8BB
8C
8G#
8A
8C#
*-
'''
    ex = converter.parseData(humdata)

    clefOld = ex.flat.getElementsByClass(clef.Clef)[0]
    # replace the old clef
    ex.flat.replace(clefOld, clef.TenorClef())
    ex.insert(0, instrument.Bassoon())

    if show:
        ex.show()

#     purcellScore = music21.parseData("Music_for_a_while.musicxml")
#     thisClef = purcellScore.getElementsByClass(clef.Clef)[0]
#     thisClef.__class__ = clef.TenorClef
#     purcellScore.insert(0, instrument.Instrument('bassoon'))
#     assert purcellScore.allInRange() is True
#     purcellScore.playMidi()   ## will play on bassoon
#     purcellScore.show() 


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

            ch1_writing_I_A_1,
            ch1_writing_I_A_2,
            ch1_writing_I_B_1,
            ch1_writing_I_B_2,
            ch1_writing_I_B_3,
            ]:
            func(show=False, play=False)



        

#-----------------------------------------------------------------||||||||||||--
if __name__ == "__main__":
    if len(sys.argv) == 1:
        music21.mainTest(Test)
    else:

        #t = Test()
        #t.testImportClefAssign()

        #ch1_writing_I_B_1(show=True)
        #ch1_writing_I_B_2(show=True)
        #ch1_writing_I_B_3(show=True)
        ch1_basic_II_C_1(show=True)