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


def ch1_basic_II_C(data, intervalShift):
    '''Function for C1, C2, C3, and C4
    '''
    from music21 import stream, clef, common, chord
    ex = stream.Stream()
    for chunk in data:
        m = stream.Measure()    
        for e in chunk:
            if common.isStr(e):
                n1 = note.Note(e)
                n1.quarterLength = 4
                n2 = n1.transpose(intervalShift)
                m.append(chord.Chord([n1, n2])) # chord to show both
            else:
                m.append(e)
        m.timeSignature = m.bestTimeSignature()
        ex.append(m)
    return ex

def ch1_basic_II_C_1(show=True, *arguments, **keywords):
    '''
    p. 4
    Practice writing whole and half steps. Watch for changes in clef.
    Write hole steps
    '''
    data = [[clef.TrebleClef(), 'g#4', 'b-4', 'd-4'], 
            [clef.BassClef(), 'e3', 'a-2'], 
            [clef.TenorClef(), 'c#']]
    ex = ch1_basic_II_C(data, 'w')
    if show: 
        ex.show()

def ch1_basic_II_C_2(show=True, *arguments, **keywords):
    data = [[clef.BassClef(), 'c3', 'f#3'], 
            [clef.AltoClef(), 'f4', 'c-4'], 
            [clef.TrebleClef(), 'a-4', 'b--4']]
    ex = ch1_basic_II_C(data, '-w')
    if show: 
        ex.show()

def ch1_basic_II_C_3(show=True, *arguments, **keywords):
    data = [[clef.BassClef(), 'f#2', 'c-3'], 
            [clef.TrebleClef(), 'e4', 'b-5', 'a#4'], 
            [clef.AltoClef(), 'f-3']]
    ex = ch1_basic_II_C(data, 'h')
    if show: 
        ex.show()

def ch1_basic_II_C_4(show=True, *arguments, **keywords):
    data = [[clef.TrebleClef(), 'b#4', 'e4', 'd#5'], 
            [clef.AltoClef(), 'c-4'], 
            [clef.BassClef(), 'f#3', 'c3']]
    ex = ch1_basic_II_C(data, '-h')
    if show: 
        ex.show()



#-------------------------------------------------------------------------------
# Writing Exercises

#-------------------------------------------------------------------------------
# I. Arranging


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


#-------------------------------------------------------------------------------
# II. Composing melodies

def ch1_writing_II_A(show=True, *arguments, **keywords):
    '''p. 7

    Compose a melody using whole and half steps in any musical style.

    This technique uses a random walk of whole or half steps with direction 
    choices determined by whether the present note is above or below the 
    target end.
    '''
    import copy, random
    from music21 import interval, stream, expressions

    dirWeight = [-1, 1] # start with an even distribution
    s = stream.Stream()

    nStart = note.Note('g4')
    n = copy.deepcopy(nStart)

    while True:
        n.quarterLength = random.choice([.25, .5, 1])
        s.append(n)
        # if we have written more than fifteen notes 
        # and the last notes matches the first pitch class, then end.
        if len(s) > 4 and n.pitch.pitchClass == nStart.pitch.pitchClass:
            n.notations.append(expressions.Fermata())
            break
        if len(s) > 30: # emergency break in case the piece is too long
            break
        dir = random.choice(dirWeight)
        if dir == 1:
            i = random.choice(['w', 'h'])
        else:
            i = random.choice(['w-', 'h-'])
        n = n.transpose(i)
        
        iSpread = interval.notesToInterval(nStart, n)
        if iSpread.direction == -1: # we are below our target, favor upward
            dirWeight = [-1, 1, 1]
        if iSpread.direction == 1: # we are above our target, favor down
            dirWeight = [-1, -1, 1]

    if show:
        s.show()


def ch1_writing_II_B(show=True, *arguments, **keywords):
    '''p. 7
    '''
    pass
    # see ch1_writing_II_A



#-------------------------------------------------------------------------------
# Analysis

def ch1_analysis_A_1(show=True, *arguments, **keywords):
    '''p. 8

    Circle all pitches written on ledger lines, identify pitch name and octave
    '''
    pass


def ch1_analysis_A_2(show=True, *arguments, **keywords):
    '''p. 8
    '''
    pass


def ch1_analysis_B_1(show=True, *arguments, **keywords):
    '''p. 9

    Circle each whole step, but a box around each half step. 
    '''
    pass

def ch1_analysis_B_2(show=True, *arguments, **keywords):
    '''p. 9
    '''
    pass



#-------------------------------------------------------------------------------
# CHAPTER 2 
#-------------------------------------------------------------------------------
# Basic Elements
#-------------------------------------------------------------------------------
# I. Meter Signatures

def ch2_basic_I_A_1(show=True, *arguments, **keywords):
    '''p. 11
    For each of the melodies below, provide the correct meter signature.
    Next to the signature, write in the meter type.
    '''
    pass

def ch2_basic_I_A_2(show=True, *arguments, **keywords):
    '''p. 11
    '''
    pass

def ch2_basic_I_A_3(show=True, *arguments, **keywords):
    '''p. 12
    '''
    pass

def ch2_basic_I_A_4(show=True, *arguments, **keywords):
    '''p. 12
    '''
    pass


def ch2_basic_I_B(show=True, *arguments, **keywords):
    '''p. 12
    '''
    pass

def ch2_basic_I_C(show=True, *arguments, **keywords):
    '''p. 13
    '''
    pass


def ch2_basic_II(show=True, *arguments, **keywords):
    '''p. 13
    '''
    pass


#-------------------------------------------------------------------------------
# Writing

#-------------------------------------------------------------------------------
# I Incomplete measures


def ch2_writing_I_A_1(show=True, *arguments, **keywords):
    '''p. 14
    '''
    pass

def ch2_writing_I_A_2(show=True, *arguments, **keywords):
    '''p. 14
    '''
    pass

def ch2_writing_I_A_3(show=True, *arguments, **keywords):
    '''p. 14
    '''
    pass

def ch2_writing_I_A_4(show=True, *arguments, **keywords):
    '''p. 14
    '''
    pass

def ch2_writing_I_A_5(show=True, *arguments, **keywords):
    '''p. 14
    '''
    pass



def ch2_writing_I_B_1(show=True, *arguments, **keywords):
    '''p. 14
    '''
    pass

def ch2_writing_I_B_2(show=True, *arguments, **keywords):
    '''p. 14
    '''
    pass

def ch2_writing_I_B_3(show=True, *arguments, **keywords):
    '''p. 14
    '''
    pass

def ch2_writing_I_B_4(show=True, *arguments, **keywords):
    '''p. 14
    '''
    pass

def ch2_writing_I_B_5(show=True, *arguments, **keywords):
    '''p. 14
    '''
    pass


#-------------------------------------------------------------------------------
# II Anacrusis notation

def ch2_writing_II_A(show=True, *arguments, **keywords):
    '''p. 15
    '''
    pass

def ch2_writing_II_B(show=True, *arguments, **keywords):
    '''p. 15
    '''
    pass

def ch2_writing_II_C(show=True, *arguments, **keywords):
    '''p. 15
    '''
    pass



#-------------------------------------------------------------------------------
# III Dots and ties

def ch2_writing_III_A_1(show=True, *arguments, **keywords):
    '''p. 16
    '''
    pass


def ch2_writing_III_A_2(show=True, *arguments, **keywords):
    '''p. 16
    '''
    pass

def ch2_writing_III_A_3(show=True, *arguments, **keywords):
    '''p. 16
    '''
    pass


def ch2_writing_III_B_1(show=True, *arguments, **keywords):
    '''p. 17
    '''
    pass

def ch2_writing_III_B_2(show=True, *arguments, **keywords):
    '''p. 17
    '''
    pass

def ch2_writing_III_B_3(show=True, *arguments, **keywords):
    '''p. 17
    '''
    pass



#-------------------------------------------------------------------------------
# IV Beaming to reflect meter


def ch2_writing_IV_A(show=True, *arguments, **keywords):
    '''p. 17
    '''
    pass

def ch2_writing_IV_B(show=True, *arguments, **keywords):
    '''p. 18
    '''
    pass


#-------------------------------------------------------------------------------
# V Inserting bar lines

def ch2_writing_V_A(show=True, *arguments, **keywords):
    '''p. 18
    '''
    pass

def ch2_writing_V_B(show=True, *arguments, **keywords):
    '''p. 18
    '''
    pass



#-------------------------------------------------------------------------------
# VI Rhythmic compositions

def ch2_writing_VI(show=True, *arguments, **keywords):
    '''p. 19
    '''
    pass


#-------------------------------------------------------------------------------
# Analysis




#-------------------------------------------------------------------------------
FUNCTIONS = [ch1_basic_I_A, 
            ch1_basic_I_B,
            ch1_basic_I_C_1,
            ch1_basic_I_C_2,

            ch1_basic_II_A_1,
            ch1_basic_II_A_2,
            ch1_basic_II_B_1,
            ch1_basic_II_B_2,

            ch1_basic_II_C_1,
            ch1_basic_II_C_2,
            ch1_basic_II_C_3,
            ch1_basic_II_C_4,

            ch1_writing_I_A_1,
            ch1_writing_I_A_2,
            ch1_writing_I_B_1,
            ch1_writing_I_B_2,
            ch1_writing_I_B_3,

            ch1_writing_II_A,
            ch1_writing_II_B,
            ]

class TestExternal(unittest.TestCase):
    def runTest(self):
        pass

    def testBasic(self):
        for func in FUNCTIONS:
            func(show=True, play=False)
    

class Test(unittest.TestCase):
    def runTest(self):
        pass

    def testBasic(self):
        for func in FUNCTIONS:
            func(show=False, play=False)


        

#-------------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) == 1:
        music21.mainTest(Test)
    else:
        #b = TestExternal()
        #b.testBasic()

        #ch1_writing_I_B_1(show=True)
        #ch1_writing_I_B_2(show=True)
        #ch1_writing_I_B_3(show=True)
        #ch1_basic_II_C_2(show=True)
        ch1_writing_II_A(show=True)

