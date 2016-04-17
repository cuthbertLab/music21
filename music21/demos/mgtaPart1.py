# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         mgtaPart1.py
# Purpose:      demonstration
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2010, 2013 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

import copy
import unittest
import sys

import music21
from music21 import clef
from music21 import converter
from music21 import instrument
from music21 import interval
from music21 import note
from music21 import musicxml

from music21.ext import six
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
        unused_n = note.Note(p)
        
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
            unused_mark = "H"
        elif i1.intervalClass == 2:
            unused_mark = "W"
        else:
            unused_mark = "N"

# no keyboard diagram yet!
#         k1 = keyboard.Diagram()
#         k1.mark(n1, mark)
#         k1.mark(n2)
#         if show:
#             k1.show()


    
def ch1_basic_I_C_1(show=True, *arguments, **keywords):
    '''
    p3.
    start at a note on the piano keyboard marked with an "X", 
    move the performer's finger according to a pattern 
    of half and whole steps and then mark the key at the end 
    with an asterisk.
    '''
    from music21 import stream
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
    from music21 import stream, common, chord
    ex = stream.Stream()
    for chunk in data:
        m = stream.Measure()    
        for e in chunk:
            if isinstance(e, six.string_types):
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
    Write whole steps
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
    Rewrite these melodies from music literature, placing the pitches 
    one octave higher or lower as specified, by using ledger lines. 
    Do not change to a new clef.

    Rewrite one active higher 
    '''

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
    # camptown races
    ex = converter.parse("tinynotation: 2/4 g8 g e g", makeNotation=False)
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
    import random
    from music21 import stream, expressions, pitch

    dirWeight = [-1, 1] # start with an even distribution
    s = stream.Stream()

    nStart = note.Note('g4')
    n = copy.deepcopy(nStart)

    while True:
#        n.quarterLength = random.choice([.25, .5, 1])
        n.duration.type = random.choice(['16th', 'eighth', 'quarter'])
        s.append(n)
        # if we have written more than fifteen notes 
        # and the last notes matches the first pitch class, then end.
        if len(s) > 4 and n.pitch.pitchClass == nStart.pitch.pitchClass:
            n.expressions.append(expressions.Fermata())
            break
        if len(s) > 30: # emergency break in case the piece is too long
            break
        direction = random.choice(dirWeight)
        if direction == 1:
            i = random.choice(['w', 'h'])
        else:
            i = random.choice(['w-', 'h-'])
        try:
            n = n.transpose(i)
        except pitch.AccidentalException:
            break # end b/c our transposition have exceeded accidental range
        
        iSpread = interval.notesToInterval(nStart, n)
        if iSpread.direction == -1: # we are below our target, favor upward
            dirWeight = [-1, 1, 1]
        if iSpread.direction == 1: # we are above our target, favor down
            dirWeight = [-1, -1, 1]

    if show:
        s.show()
    else:
        unused_post = musicxml.m21ToXml.GeneralObjectExporter().parse(s)


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

    Circle each whole step, put a box around each half step. 
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
    Next to the signature, write in the meter type (e.g. simple triple).
    '''
    from music21 import stream, key
    ex = stream.Stream()
    ex.insert(key.KeySignature(1))    

    data = [[('d6',1.5)], 
            [('d6',1.5)],
            [('d6',.5),('c6',.5),('b5',.5)],
            [('rest',.5),('b5',.25),('c6',.25),('d6',.5)],
           ]

    for mData in data:
        m = stream.Measure()
        for p, d in mData:
            if p == 'rest': 
                n = note.Rest()
            else:
                n = note.Note(p)
            n.quarterLength = d
            m.append(n)
        ex.append(m)
    
    # get the best time signature; make sure it agrees with the next
    # time signature, just to be sure
    ts1 = ex.getElementsByClass('Measure')[0].bestTimeSignature()
    ts2 = ex.getElementsByClass('Measure')[1].bestTimeSignature()

    # make sure these time signatures agree
    assert ts1.ratioEqual(ts2)
    for m in ex.getElementsByClass('Measure'):
        m.insert(0, copy.deepcopy(ts1))
    # append answers to first note
    ex.flat.notesAndRests[0].addLyric('Meter: %s' % ts1)
    ex.flat.notesAndRests[0].addLyric('Meter type: %s' % ts1.classification)

    if show:
        ex.show()
    else:
        unused_post = musicxml.m21ToXml.GeneralObjectExporter().parse(ex)


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
    Using the information given, complete the chart below. 
    (Given meter type and one of meter, beat unit, 
    beat division, full bar divisions, provide the other data)
    '''
    # a brute force way to do this might have a function in meter.py that returns a number of candidates for a given meter type and some other parameter (bar duration). then, these values can be tested for match.
    pass
    

def ch2_basic_I_C(show=True, *arguments, **keywords):
    '''p. 13
    Complete the chart below. (For a given meter, provide meter type, beat unit, beat division, and beat subdivision.)
    '''
    from music21 import meter, stream

    def prepareMeter(ts):
        m = stream.Measure()
        m.timeSignature = ts
        n = note.Note()
        n.lyric = str(ts)
        n.duration = ts.beatSequence.duration
        m.append(n)
        return m

    def prepareMeterType(ts):
        m = stream.Measure()
        m.timeSignature = ts
        n = note.Note()
        n.lyric = ts.classification
        n.duration = ts.beatSequence.duration
        m.append(n)
        return m

    def prepareBeatUnit(ts):
        m = stream.Measure()
        m.timeSignature = ts
        n = note.Note()
        n.lyric = 'Beat Unit'
        n.duration = ts.beatDuration
        m.append(n)
        return m

    def prepareBeatDivision(ts):
        m = stream.Measure()
        m.timeSignature = ts
        for i in range(len(ts.beatDivisionDurations)):
            d = ts.beatDivisionDurations[i]
            n = note.Note()
            if i == 0:
                n.lyric = 'Beat Division'
            n.duration = d
            m.append(n)
        m.makeBeams(inPlace=True)
        return m

    def prepareBeatSubDivision(ts):
        m = stream.Measure()
        m.timeSignature = ts
        for i in range(len(ts.beatSubDivisionDurations)):
            d = ts.beatSubDivisionDurations[i]
            n = note.Note()
            if i == 0:
                n.lyric = 'Beat Subdivision'
            n.duration = d
            m.append(n)
        m.makeBeams(inPlace=True)
        return m

    ex = stream.Stream()
    for tsStr in ['2/4', '3/16', '4/4', '3/8', '2/2', '4/8', '6/8', '9/16', '15/4']:
        ts = meter.TimeSignature(tsStr)

        ex.append(prepareMeter(copy.deepcopy(ts)))
        ex.append(prepareMeterType(copy.deepcopy(ts)))
        ex.append(prepareBeatUnit(copy.deepcopy(ts)))
        ex.append(prepareBeatDivision(copy.deepcopy(ts)))
        ex.append(prepareBeatSubDivision(copy.deepcopy(ts)))
        
    if show:
        ex.show()
    else:
        unused_post = musicxml.m21ToXml.GeneralObjectExporter().parse(ex)


def ch2_basic_II(show=True, *arguments, **keywords):
    '''p. 13

    Write the rhythms that use the same counting pattern as those in the same row. 
    '''
    pass


#-------------------------------------------------------------------------------
# Writing

#-------------------------------------------------------------------------------
# I Incomplete measures

def ch2_writing_I_A(tsStr, barGroups):    
    from music21 import meter, stream

    ts = meter.TimeSignature(tsStr)

    ex = stream.Stream()
    ex.insert(0, ts)
    for b in barGroups:
        summation = 0
        for ql in b:
            if ql > 0: # quick encoding: negative values for rests
                n = note.Note()
            else:
                n = note.Rest()
            n.quarterLength = abs(ql)
            summation += abs(ql)
            ex.append(n)
        if ts.barDuration.quarterLength - summation > 0:
            nFill = note.Note()
            # subtract bar dur from sum of existing notes
            nFill.quarterLength = ts.barDuration.quarterLength - summation
            ex.append(nFill)
    
    return ex

def ch2_writing_I_A_1(show=True, *arguments, **keywords):
    '''p. 14

    Complete the rhythms below by adding one note value that completes any measure with too few beats.
    '''
    barGroups = ([.5], [.75, .25], [.5, .75], [.25, .25, .25, .25], [.5], [])
    ex = ch2_writing_I_A('3/8', barGroups)
    if show:
        ex.show()
    else:
        unused_post = musicxml.m21ToXml.GeneralObjectExporter().parse(ex)


def ch2_writing_I_A_2(show=True, *arguments, **keywords):
    '''p. 14
    '''
    barGroups = ([.75, .25, .25, .25, .25, .25, 1.5], [.25, .25, .5, -.5, .5], [2, .25, .25, .25, .25, .25, .25], [3])
    ex = ch2_writing_I_A('4/4', barGroups)
    if show:
        ex.show()
    else:
        unused_post = musicxml.m21ToXml.GeneralObjectExporter().parse(ex)

def ch2_writing_I_A_3(show=True, *arguments, **keywords):
    '''p. 14
    '''
    barGroups = ([2, 1.5, .5, .5, .5, .5], [-.5, .5, .5, .5, 1, 1, 1], [4, 1.5], [.5, .5, .5, .5, .5, 1, .5])
    ex = ch2_writing_I_A('3/2', barGroups)
    if show:
        ex.show()
    else:
        unused_post = musicxml.m21ToXml.GeneralObjectExporter().parse(ex)

def ch2_writing_I_A_4(show=True, *arguments, **keywords):
    '''p. 14
    '''
    barGroups = ([1.25, .25, .25, .25], [-.5, .5, -.5], [1.25], [.25, .25, .5, .75], [1])
    ex = ch2_writing_I_A('2/4', barGroups)
    if show:
        ex.show()
    else:
        unused_post = musicxml.m21ToXml.GeneralObjectExporter().parse(ex)

def ch2_writing_I_A_5(show=True, *arguments, **keywords):
    '''p. 14
    '''
    barGroups = ([2, 1, 1, 3], [.5, .5, .5, .5, 2], [3, 1, 1, 2], [2])
    ex = ch2_writing_I_A('4/2', barGroups)
    if show:
        ex.show()
    else:
        unused_post = musicxml.m21ToXml.GeneralObjectExporter().parse(ex)



def ch2_writing_I_B_1(show=True, *arguments, **keywords):
    '''p. 14

    Complete the rhythms below by adding rests to complete any measure with too few beats. 
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

    Each of these pieces begins with an anacrusis. What note value (or note value plus rest) could the composer use to fill the last measure of the compositions correctly. 
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

def ch2_writing_III_A(quarterLengthSrc, meterStr):
    '''Function for A1, A2, A3: Add ties. 
    '''
    from music21 import meter, stream
    ex = stream.Stream()

    # the source rhythms
    s1 = stream.Stream()
    s1.append(meter.TimeSignature(meterStr))
    for ql in quarterLengthSrc:
        n = note.Note()
        n.quarterLength = ql
        s1.append(n)
    ex.insert(s1)

    # the modified
    s2 = stream.Stream()
    s2.append(meter.TimeSignature(meterStr))
    for ql in quarterLengthSrc:
        n = note.Note()
        n.quarterLength = ql
        if ql == .75:
            nSub = n.splitByQuarterLengths([.5, .25])
        elif ql == 1.5:
            nSub = n.splitByQuarterLengths([1, .5])
        elif ql == 3:
            nSub = n.splitByQuarterLengths([2, 1])
        else:
            nSub = [n]
        for n in nSub:
            s2.append(n)
    ex.insert(s2)
    return ex

def ch2_writing_III_A_1(show=True, *arguments, **keywords):
    '''p. 16

    Renotate the following rhythms with ties instead of dotted notes.
    '''
    quarterLengthSrc = [3, 1, 2, 2, 1.5, .5, 2, .5, 1.5, 2, 2, 3]
    ex = ch2_writing_III_A(quarterLengthSrc, '3/2')
    if show:
        ex.show()
    else:
        unused_post = musicxml.m21ToXml.GeneralObjectExporter().parse(ex)

def ch2_writing_III_A_2(show=True, *arguments, **keywords):
    '''p. 16
    '''
    quarterLengthSrc = [.75, .25, .75, .25, 1.5, .5, 3, .5, .5, .25, .75, 1, 2]
    ex = ch2_writing_III_A(quarterLengthSrc, '4/4')
    if show:
        ex.show()
    else:
        unused_post = musicxml.m21ToXml.GeneralObjectExporter().parse(ex)

def ch2_writing_III_A_3(show=True, *arguments, **keywords):
    '''p. 16
    '''
    quarterLengthSrc = [3, 1, .5, .5, .5, .5, 1.5, .5, 2, 1, 1, 1, 3]
    ex = ch2_writing_III_A(quarterLengthSrc, '2/2')
    if show:
        ex.show()
    else:
        unused_post = musicxml.m21ToXml.GeneralObjectExporter().parse(ex)


def ch2_writing_III_B(src):
    '''Function for B1, B2, B3: Remove ties.
    '''
    from music21 import stream
    ex = stream.Stream()

    # the source rhythms
    s1 = copy.deepcopy(src)
    ex.insert(s1)

    # the modified
    s2 = copy.deepcopy(src)
    ex.insert(s2)

    # note that ending ties are not given with tiny notation
    group = []
    for n in s2.notesAndRests:
        #environLocal.printDebug([n, n.tie])
        if n.tie != None or len(group) > 0:
            if n.tie != None and n.tie.type != 'stop':
                group.append(n)
            else: # end of tied notes
                group.append(n)
                ql= sum([x.quarterLength for x in group])
                for i in range(len(group)):
                    if i == 0: # keep first, extend dur
                        group[i].quarterLength = ql
                        group[i].tie = None # remove tie
                    else: # remove from source
                        s2.remove(group[i])
                group = [] # reset

    environLocal.printDebug(['post editing'])

    return ex


def ch2_writing_III_B_1(show=True, *arguments, **keywords):
    '''p. 17

    Renotate the following rhythms without ties. 
    '''
    ex = converter.parse("tinynotation: 3/8 c8~ c16 c16 c16 c16 c8~ c8 c c16 c~ c c c8 c4~ c8")

    ex = ch2_writing_III_B(ex)
    if show:
        ex.show()
    else:
        unused_post = musicxml.m21ToXml.GeneralObjectExporter().parse(ex)


def ch2_writing_III_B_2(show=True, *arguments, **keywords):
    '''p. 17
    '''
    ex = converter.parse("tinynotation: 4/4 c4~ c8 c16 c c8 c~ c c c2~ c4 c8 c8 c8~ c16 c c8~ c16 c c2")

    ex = ch2_writing_III_B(ex)
    if show:
        ex.show()
    else:
        unused_post = musicxml.m21ToXml.GeneralObjectExporter().parse(ex)


def ch2_writing_III_B_3(show=True, *arguments, **keywords):
    '''p. 17
    '''
    ex = converter.parse("tinynotation: 3/2 c2~ c4 c c~ c8 c c4 c~ c c c2 c2 c2~ c4 c c1~ c2")

    ex = ch2_writing_III_B(ex)
    if show:
        ex.show()
    else:
        unused_post = musicxml.m21ToXml.GeneralObjectExporter().parse(ex)



#-------------------------------------------------------------------------------
# IV Beaming to reflect meter


def ch2_writing_IV_A(show=True, *arguments, **keywords):
    '''p. 17

    Rebeam each of the vocal lines to reflect the meter and beat unit instead. 
    '''
    pass



def ch2_writing_IV_B(show=True, *arguments, **keywords):
    '''p. 18
    '''
    ex = converter.parse("tinynotation: 2/4 c8. c16 e8 g c'4. r8 a8. a16 c'8 a g4. e16 f g8 g8 e16 e g16 g a8 g8 e4 d8 e16 f e d8 d16 c4.")
    
    ex = ex.makeMeasures() 
    ex.makeBeams(inPlace=True)

    if show:
        ex.show()
    else:
        unused_post = musicxml.m21ToXml.GeneralObjectExporter().parse(ex)


#-------------------------------------------------------------------------------
# V Inserting bar lines

def ch2_writing_V_A(show=True, *arguments, **keywords):
    '''p. 18

    Using the meter signature given, add bar lines to the following melodies. 
    '''
    from music21 import key

    # note: tiny is not encoding C#s for c'#4 properly (it seems)
    ex = converter.parse("tinynotation: 3/2 g#1 f#4 g#4 a1 g#2 f#1 g#4. en8 g#2 f#4 r4 f#4 d#8 B8 e2 r4 e4 a4. a8 a2 g#4 g# b4. e8 a2~ a4 a4 d'n4. d'8 d'n2 c'#4 c'# c'# c'#")
    
    ex.insert(0, key.KeySignature(4))
    # presently, this only works if makeAccidentals is called before make measures
    ex.makeAccidentals(inPlace=True)
    ex = ex.makeMeasures() 
    ex.makeBeams(inPlace=True)

    if show:
        ex.show()
    else:
        unused_post = musicxml.m21ToXml.GeneralObjectExporter().parse(ex)

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

def ch2_analysis_A_1(show=True, *arguments, **keywords):
    '''p. 20
    '''
    pass


def ch2_analysis_A_2(show=True, *arguments, **keywords):
    '''p. 21
    '''
    pass


def ch2_analysis_A_3(show=True, *arguments, **keywords):
    '''p. 21
    '''
    pass


def ch2_analysis_B_1(show=True, *arguments, **keywords):
    '''p. 22
    '''
    pass


def ch2_analysis_B_2(show=True, *arguments, **keywords):
    '''p. 22
    '''
    pass

def ch2_analysis_B_3(show=True, *arguments, **keywords):
    '''p. 22
    '''
    pass




#-------------------------------------------------------------------------------
# CHAPTER 3
#-------------------------------------------------------------------------------
# Pitch Collections, Scales, and Major Keys
#-------------------------------------------------------------------------------
# Basic Elements

# I. Writing scales


def ch3_basic_I_A(show=True, *arguments, **keywords):
    '''p. 23

    Write a chromatic scale beginning and ending with the 
    given pitches. Use sharps in ascending chromatic and 
    flats in descending.
    '''
    pass



def ch3_basic_I_B(show=True, *arguments, **keywords):
    '''p. 23

    Creating major scales.
    '''
    pass


#-------------------------------------------------------------------------------
# II. Key signatures

def ch3_basic_II_A(show=True, *arguments, **keywords):
    '''p. 24

    Writing seven sharps and flats in order; say the name of the 
    major key that goes with the signature. 
    '''
    pass



def ch3_basic_II_B(show=True, *arguments, **keywords):
    '''p. 24

    Write correct key signature for each major key indicated.
    '''
    pass


def ch3_basic_II_C(show=True, *arguments, **keywords):
    '''p. 24

    Identify the name of the major key associated with each of the key signatures below. 
    '''
    pass

#-------------------------------------------------------------------------------
# III. Scale degrees

def ch3_basic_III_A(show=True, *arguments, **keywords):
    '''p. 25

    Given the scale degree, write the rest of the scale. 
    Begin by writing whole notes on the lines and spaces 
    above and below the given pitch, then fill in the necessary accidentals. 
    '''
    pass


def ch3_basic_III_B(show=True, *arguments, **keywords):
    '''p. 25-26

    For each key listed, write the pitch-class name of the scale degree requested. 
    '''
    pass


#-------------------------------------------------------------------------------
# IV. At your instrument

def ch3_basic_IV_A(show=True, *arguments, **keywords):
    '''p. 26

    Play a chromatic scale starting with the lowest pitch of your instrument 
    and ending with the highest pitch you can play. 
    '''
    pass


def ch3_basic_IV_B(show=True, *arguments, **keywords):
    '''p. 26

    Play a major scale starting on these pitches: E-, G, B-, E, F, B
    '''
    pass


#-------------------------------------------------------------------------------
# Writing Exercises
#-------------------------------------------------------------------------------
# I. Writing melodies from scale degrees

def ch3_writing_I_A(show=True, *arguments, **keywords):
    '''p. 26

    Writing melodies from scale degrees. 
    '''
    pass

def ch3_writing_I_B(show=True, *arguments, **keywords):
    '''p. 26

    Writing melodies from scale degrees. 
    '''
    pass


def ch3_writing_I_C(show=True, *arguments, **keywords):
    '''p. 26

    Writing melodies from scale degrees. 
    '''
    pass

def ch3_writing_I_D(show=True, *arguments, **keywords):
    '''p. 26

    Writing melodies from scale degrees. 
    '''
    pass

#-------------------------------------------------------------------------------
# I. Composing your own melody in a major key. 


def ch3_writing_II(show=True, *arguments, **keywords):
    '''p. 27

    Compose a folk-like melody in a major key, using the melodies given above as examples. 
    '''
    pass




#-------------------------------------------------------------------------------
# Analysis
#-------------------------------------------------------------------------------
# I. Brief analysis


def ch3_analysis_I_A_1(show=True, *arguments, **keywords):
    '''p. 28
    '''
    pass

def ch3_analysis_I_A_2(show=True, *arguments, **keywords):
    '''p. 29
    '''
    pass

def ch3_analysis_I_A_3(show=True, *arguments, **keywords):
    '''p. 29
    '''
    pass

def ch3_analysis_I_B_1(show=True, *arguments, **keywords):
    '''p. 30
    '''
    pass

def ch3_analysis_I_B_2(show=True, *arguments, **keywords):
    '''p. 30
    '''
    pass

def ch3_analysis_I_B_3(show=True, *arguments, **keywords):
    '''p. 30
    '''
    pass

#-------------------------------------------------------------------------------
# II. Extended analysis

def ch3_analysis_II_A(show=True, *arguments, **keywords):
    '''p. 31
    '''
    pass

def ch3_analysis_II_B(show=True, *arguments, **keywords):
    '''p. 31
    '''
    pass





#-------------------------------------------------------------------------------
# CHAPTER 4
#-------------------------------------------------------------------------------
# Minor Keys and Diatonic Modes
#-------------------------------------------------------------------------------
# Basic Elements

# I. Writing minor scales


def ch4_basic_I_A(show=True, *arguments, **keywords):
    '''p. 33

    For each major key, write out the scale. Circle degree 6. Write out a new scale that begins ont he pitch class you circled. Write the name of this relative-minor scale on the line indicated. 
    '''
    pass


def ch4_basic_I_B(show=True, *arguments, **keywords):
    '''p. 34
    '''
    pass


def ch4_basic_I_C(show=True, *arguments, **keywords):
    '''p. 34
    '''
    pass



def ch4_basic_I_D(show=True, *arguments, **keywords):
    '''p. 35
    '''
    pass


# II. Forms of the minor scale

def ch4_basic_II(show=True, *arguments, **keywords):
    '''p. 35
    '''
    pass


# II. Writing the diatonic modes

def ch4_basic_III_A(show=True, *arguments, **keywords):
    '''p. 36
    '''
    pass

def ch4_basic_III_B(show=True, *arguments, **keywords):
    '''p. 36
    '''
    pass

# IV. Scale degrees in minor


def ch4_basic_IV_A(show=True, *arguments, **keywords):
    '''p. 37
    '''
    pass


def ch4_basic_IV_B(show=True, *arguments, **keywords):
    '''p. 37
    '''
    pass



def ch4_basic_IV_C(show=True, *arguments, **keywords):
    '''p. 37
    '''
    pass


# V. Playing and singing minor scales

def ch4_basic_V_A(show=True, *arguments, **keywords):
    '''p. 38
    '''
    pass

def ch4_basic_V_B(show=True, *arguments, **keywords):
    '''p. 38
    '''
    pass


#-------------------------------------------------------------------------------
# Writing Exercises
# I. Writing melodies from scale degrees

def ch4_writing_I_A(show=True, *arguments, **keywords):
    '''p. 38
    '''
    pass

def ch4_writing_I_B(show=True, *arguments, **keywords):
    '''p. 39
    '''
    pass

def ch4_writing_I_C(show=True, *arguments, **keywords):
    '''p. 39
    '''
    pass


# II. Composing your own melodies

def ch4_writing_II(show=True, *arguments, **keywords):
    '''p. 39
    '''
    pass





#-------------------------------------------------------------------------------
# Analysis
# I. Brief analysis

def ch4_analysis_I_A_1(show=True, *arguments, **keywords):
    '''p. 40
    '''
    pass

def ch4_analysis_I_A_2(show=True, *arguments, **keywords):
    '''p. 40
    '''
    pass

def ch4_analysis_I_A_3(show=True, *arguments, **keywords):
    '''p. 40
    '''
    pass


def ch4_analysis_I_B_1(show=True, *arguments, **keywords):
    '''p. 41
    '''
    pass

def ch4_analysis_I_B_2(show=True, *arguments, **keywords):
    '''p. 41
    '''
    pass

def ch4_analysis_I_B_3(show=True, *arguments, **keywords):
    '''p. 41
    '''
    pass

def ch4_analysis_I_B_4(show=True, *arguments, **keywords):
    '''p. 41
    '''
    pass



#-------------------------------------------------------------------------------
# II. Extended analysis


def ch4_analysis_II_A(show=True, *arguments, **keywords):
    '''p. 42
    '''
    pass

def ch4_analysis_II_B(show=True, *arguments, **keywords):
    '''p. 42
    '''
    pass







#-------------------------------------------------------------------------------
# CHAPTER 5
#-------------------------------------------------------------------------------
# Beat, Meter, and Rhythm: Compound Meters
#-------------------------------------------------------------------------------
# Basic Elements

# I. Meter signatures


def ch5_basic_I_A_1(show=True, *arguments, **keywords):
    '''p. 43
    '''
    pass


def ch5_basic_I_A_2(show=True, *arguments, **keywords):
    '''p. 44
    '''
    pass

def ch5_basic_I_A_3(show=True, *arguments, **keywords):
    '''p. 44
    '''
    pass

def ch5_basic_I_A_4(show=True, *arguments, **keywords):
    '''p. 44
    '''
    pass


def ch5_basic_I_B(show=True, *arguments, **keywords):
    '''p. 45
    '''
    pass


def ch5_basic_I_C(show=True, *arguments, **keywords):
    '''p. 45
    '''
    pass



# II. Divisions and subdivisions with different beat units

def ch5_basic_II(show=True, *arguments, **keywords):
    '''p. 45
    '''
    pass


#-------------------------------------------------------------------------------
# Writing Exercises

# I. Incomplete measures


def ch5_writing_I_A(show=True, *arguments, **keywords):
    '''p. 46
    '''
    pass


def ch5_writing_I_B(show=True, *arguments, **keywords):
    '''p. 47
    '''
    pass


# II. Anacrusis notation


def ch5_writing_II_A(show=True, *arguments, **keywords):
    '''p. 47
    '''
    pass

def ch5_writing_II_B(show=True, *arguments, **keywords):
    '''p. 48
    '''
    pass


def ch5_writing_II_C(show=True, *arguments, **keywords):
    '''p. 48
    '''
    pass


# III. Beaming to reflect the meter


def ch5_writing_III_A(show=True, *arguments, **keywords):
    '''p. 49

    Beam by syllables of the sung text by meter, not text.
    '''
    pass


def ch5_writing_III_B(show=True, *arguments, **keywords):
    '''p. 49
    '''
    pass


# IV. Inserting bar lines: Simple and compound meters

def ch5_writing_IV_A(show=True, *arguments, **keywords):
    '''p. 50

    Note the meter signature, then add bar lines. 
    '''
    from music21 import stream, meter, key
    ex = stream.Stream()
    
    ex.insert(clef.BassClef())
    ex.insert(meter.TimeSignature('6/4'))
    ex.insert(key.KeySignature(3))
    
    for p, d in [(None,1), ('f#3',1),('g#3',1),('a3',4),
                 ('g#3',.5),('a#3',.5),('b3',2),
                 ('a#3',.5),('g#3',.5),('a#3',.5),('b#3',.5),
                 ('c#4',1.5),('b3',.5),('a3',.5),('c#4',.5),('b3',.5),('a3',.5),
                 ('g#3',2),('f#3',3), (None,.5), ('c#4',.5),('c#4',.5),
                 ('b3',.5),('b3',.5),('a#3',.5)]:
        if p == None: 
            n = note.Rest()
        else:
            n = note.Note(p)
        n.quarterLength = d
        ex.append(n)
    
    if show:
        # calling show creates measures and allocates notes for the time sig
        ex.show()
    else:
        unused_post = musicxml.m21ToXml.GeneralObjectExporter().parse(ex)


def ch5_writing_IV_B(show=True, *arguments, **keywords):
    '''p. 50
    '''
    pass


def ch5_writing_IV_C(show=True, *arguments, **keywords):
    '''p. 50
    '''
    pass


# V. Rhythmic compositions

def ch5_writing_V(show=True, *arguments, **keywords):
    '''p. 50
    '''
    pass


#-------------------------------------------------------------------------------
# Analysis

def ch5_analysis_A(show=True, *arguments, **keywords):
    '''p. 51
    '''
    pass

def ch5_analysis_B(show=True, *arguments, **keywords):
    '''p. 52
    '''
    pass

def ch5_analysis_C(show=True, *arguments, **keywords):
    '''p. 53
    '''
    pass



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

            ch1_analysis_A_1, 
            ch1_analysis_A_2,
            ch1_analysis_B_1,
            ch1_analysis_B_2,

            ch2_basic_I_A_1,
            ch2_basic_I_A_2,
            ch2_basic_I_A_3,
            ch2_basic_I_A_4,

            ch2_basic_I_B,

            ch2_basic_I_C,
            ch2_basic_II,

            ch2_writing_I_A_1,
            ch2_writing_I_A_2,
            ch2_writing_I_A_3,
            ch2_writing_I_A_4,
            ch2_writing_I_A_5,

            ch2_writing_I_B_1,
            ch2_writing_I_B_2,
            ch2_writing_I_B_3,
            ch2_writing_I_B_4,
            ch2_writing_I_B_5,

            ch2_writing_II_A,
            ch2_writing_II_B,
            ch2_writing_II_C,

            ch2_writing_III_A_1,
            ch2_writing_III_A_2,
            ch2_writing_III_A_3,
            ch2_writing_III_B_1,
            ch2_writing_III_B_2,
            ch2_writing_III_B_3,

            ch2_writing_IV_A,
            ch2_writing_IV_B,

            ch2_writing_V_A,
            ch2_writing_V_B,

            ch2_writing_VI,

            ch2_analysis_A_1,
            ch2_analysis_A_2,
            ch2_analysis_A_3,
            ch2_analysis_B_1,
            ch2_analysis_B_2,
            ch2_analysis_B_3,

            ch3_basic_I_A,
            ch3_basic_I_B,

            ch3_basic_II_A,
            ch3_basic_II_B,
            ch3_basic_II_C,

            ch3_basic_III_A,
            ch3_basic_III_B,

            ch3_basic_IV_A,
            ch3_basic_IV_B,

            ch3_writing_I_A,
            ch3_writing_I_B,
            ch3_writing_I_C,
            ch3_writing_I_D,

            ch3_writing_II,

            ch3_analysis_I_A_1,
            ch3_analysis_I_A_2,
            ch3_analysis_I_A_3,
            ch3_analysis_I_B_1,
            ch3_analysis_I_B_2,
            ch3_analysis_I_B_3,

            ch3_analysis_II_A,
            ch3_analysis_II_B,

            ch4_basic_I_A,
            ch4_basic_I_B,
            ch4_basic_I_C,
            ch4_basic_I_D,

            ch4_basic_II,

            ch4_basic_III_A,
            ch4_basic_III_B,
            ch4_basic_IV_A,
            ch4_basic_IV_B,
            ch4_basic_V_A,
            ch4_basic_V_B,

            ch4_writing_I_A,
            ch4_writing_I_B,
            ch4_writing_I_C,

            ch4_writing_II,

            ch4_analysis_I_A_1,
            ch4_analysis_I_A_2,
            ch4_analysis_I_A_3,
            ch4_analysis_I_B_1,
            ch4_analysis_I_B_2,
            ch4_analysis_I_B_3,
            ch4_analysis_I_B_4,

            ch4_analysis_II_A,
            ch4_analysis_II_B,

            ch5_basic_I_A_1,
            ch5_basic_I_A_2,
            ch5_basic_I_A_3,
            ch5_basic_I_A_4,
            ch5_basic_I_B,
            ch5_basic_I_C,

            ch5_basic_II,
            ch5_writing_I_A,
            ch5_writing_I_B,

            ch5_writing_II_A,
            ch5_writing_II_B,
            ch5_writing_II_C,

            ch5_writing_III_A,
            ch5_writing_III_B,

            ch5_writing_IV_A,
            ch5_writing_IV_B,
            ch5_writing_IV_C,

            ch5_writing_V,
            ch5_analysis_A,
            ch5_analysis_B,
            ch5_analysis_C,

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
    #ch2_writing_III_A_1(show = True)
    if len(sys.argv) == 1:
        music21.mainTest(Test)
    else:
        pass
        #b = TestExternal()
        #b.testBasic()

        #ch1_writing_I_B_1(show=True)
        #ch1_writing_I_B_2(show=True)
        #ch1_writing_I_B_3(show=True)
        #ch1_basic_II_C_2(show=True)

        #ch5_writing_IV_A(show=True)


        #ch2_basic_I_A_1(show=True)


        #ch2_writing_III_A_1(show=True)
        #ch2_writing_III_A_2(show=True)
        #ch2_writing_III_A_3(show=True)

        #ch2_writing_III_B_3(show=True)


        #ch2_writing_I_A_1(show=True)
        #ch2_writing_I_A_2(show=True)
        #ch2_writing_I_A_3(show=True)
        #ch2_writing_I_A_4(show=True)
        #ch2_writing_I_A_5(show=True)

        #ch2_writing_IV_B(show=True)
        #ch2_writing_V_A(show=True)
        
        #ch2_writing_III_B_1()

#------------------------------------------------------------------------------
# eof

