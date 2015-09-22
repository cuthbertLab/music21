# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         base40.py
# Purpose:      Base40/Music21 Pitch/Interval Translator
#
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    Copyright © 2009-2010 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

import unittest
from music21 import exceptions21

from music21 import pitch
from music21 import note
from music21 import interval


#Key => Base40 pitch number
#Value => Music21 Pitch name
base40Equivalent = {1: 'C--',
                    2: 'C-',
                    3: 'C',
                    4: 'C#',
                    5: 'C##',
                    6: None,
                    7: 'D--',
                    8: 'D-',
                    9: 'D',
                    10: 'D#',
                    11: 'D##',
                    12: None,
                    13: 'E--',
                    14: 'E-',
                    15: 'E',
                    16: 'E#',
                    17: 'E##',
                    18: 'F--',
                    19: 'F-',
                    20: 'F',
                    21: 'F#',
                    22: 'F##',
                    23: None,
                    24: 'G--',
                    25: 'G-',
                    26: 'G',
                    27: 'G#',
                    28: 'G##',
                    29: None,
                    30: 'A--',
                    31: 'A-',
                    32: 'A',
                    33: 'A#',
                    34: 'A##',
                    35: None,
                    36: 'B--',
                    37: 'B-',
                    38: 'B',
                    39: 'B#',
                    40: 'B##'}


#Key => Music21 Pitch name
#Value => Base40 pitch number
base40Representation = {'C--': 1,
                        'C-' : 2,
                        'C'  : 3,
                        'C#' : 4,
                        'C##': 5,
                        'D--': 7,
                        'D-' : 8,
                        'D'  : 9,
                        'D#' : 10,
                        'D##': 11,
                        'E--': 13,
                        'E-' : 14,
                        'E'  : 15,
                        'E#' : 16,
                        'E##': 17,
                        'F--': 18,
                        'F-' : 19,
                        'F'  : 20,
                        'F#' : 21,
                        'F##': 22,
                        'G--': 24,
                        'G-' : 25,
                        'G'  : 26,
                        'G#' : 27,
                        'G##': 28,
                        'A--': 30,
                        'A-' : 31,
                        'A'  : 32,
                        'A#' : 33,
                        'A##': 34,
                        'B--': 36,
                        'B-' : 37,
                        'B'  : 38,
                        'B#' : 39,
                        'B##': 40,
                        }


#Key => Base40 delta (difference between two Base40 pitch numbers)
#Value => Corresponding music21 Interval
base40IntervalTable = \
                 {0: 'P1',
                  1: 'A1',
                  
                  4: 'd2',
                  5: 'm2',
                  6: 'M2',
                  7: 'A2',
                  
                  10: 'd3',
                  11: 'm3',
                  12: 'M3',
                  13: 'A3',
                  
                  16: 'd4',
                  17: 'P4',
                  18: 'A4',
                  
                  22: 'd5',
                  23: 'P5',
                  24: 'A5',

                  27: 'd6',
                  28: 'm6',
                  29: 'M6',
                  30: 'A6',

                  33: 'd7',
                  34: 'm7',
                  35: 'M7',
                  36: 'A7',

                  39: 'd8',
                  40: 'P8',
                  }


def base40DeltaToInterval(delta):
    '''
    Returns a music21 Interval between two Base40 pitch numbers
    given the delta (difference) between them.

    Raises a Base40 Exception if the interval is not handled by Base40.
    Base40 can only handle major, minor, perfect, augmented,
    and diminished intervals. Although not for certain, it seems
    that the engineers that designed this system assumed that
    other intervals (doubly augmented intervals, for instance)
    would be of a very rare occurrence, and extreme intervals
    which would trigger an incorrect answer (C-- to C##, for
    instance, would return a diminished second, even though it's
    a quadruple augmented unison) just would not occur.

    
    >>> musedata.base40.base40DeltaToInterval(4)
    <music21.interval.Interval d2>
    >>> musedata.base40.base40DeltaToInterval(11)
    <music21.interval.Interval m3>
    >>> musedata.base40.base40DeltaToInterval(23)
    <music21.interval.Interval P5>
    >>> musedata.base40.base40DeltaToInterval(-23)
    <music21.interval.Interval P-5>
    >>> musedata.base40.base40DeltaToInterval(52)
    <music21.interval.Interval M10>
    >>> musedata.base40.base40DeltaToInterval(-52)
    <music21.interval.Interval M-10>    
    >>> musedata.base40.base40DeltaToInterval(77)
    Traceback (most recent call last):
    Base40Exception: Interval not handled by Base40 37
    '''
    
    direction = 1
    if delta < 0:
        direction = -1
       
    simpleDelta = abs(delta) % 40
    
    try:
        simpleIntervalName = base40IntervalTable[simpleDelta]
        simpleInterval = interval.Interval(simpleIntervalName)
    except KeyError:
        raise Base40Exception('Interval not handled by Base40 ' + str(simpleDelta))

    numOctaves = abs(delta) // 40
    
    sgi = simpleInterval.generic #Simple generic interval
    cgi = interval.GenericInterval(direction * (sgi.value + 7 * numOctaves)) #Compound generic interval
    sdi = simpleInterval.diatonic #Simple diatonic interval
    
    newInterval = interval.convertSpecifier(sdi.specifier)[1] + str(cgi.value)

    return interval.Interval(newInterval)
    

def base40ToPitch(base40Num):
    '''
    Converts a Base40 pitch number into a music21 Pitch.
    The Base40 number is octave specific.

    Raises a Base40 Exception if the Base40 pitch number given doesn't
    have an associated pitch name. There is one unassigned number
    each time the interval between two letters is a whole step.
    
    
    >>> musedata.base40.base40ToPitch(1)
    <music21.pitch.Pitch C--1>
    >>> musedata.base40.base40ToPitch(40)
    <music21.pitch.Pitch B##1>
    >>> musedata.base40.base40ToPitch(23)
    Traceback (most recent call last):
    Base40Exception: Pitch name not assigned to this Base40 number 23
    >>> musedata.base40.base40ToPitch(186)
    <music21.pitch.Pitch G5>
    '''
    p = pitch.Pitch()
    p.octave = ((base40Num - 1) / 40) + 1
    tableNum = base40Num - 40 * (p.octave - 1)
    pitchName = base40Equivalent[tableNum]
    if pitchName != None:
        p.name = pitchName
        return p

    raise Base40Exception('Pitch name not assigned to this Base40 number ' \
          + str(base40Num))


def pitchToBase40(pitchToConvert):
    '''
    Converts a pitch string or a music21 Pitch into a Base40
    pitch number. The Base40 number is octave specific.
    
    Raises a Base40 Exception if the pitch to convert is outside the set
    of pitches that Base40 can handle; for example, half flats
    and half sharps or triple flats and triple sharps.

    
    >>> musedata.base40.pitchToBase40(pitch.Pitch('C--5'))
    161
    >>> musedata.base40.pitchToBase40('F##4')
    142
    >>> musedata.base40.pitchToBase40('F###4')
    Traceback (most recent call last):
    Base40Exception: Base40 cannot handle this pitch F###4
    '''
    if isinstance(pitchToConvert, str):
        pitchToConvert = pitch.Pitch(pitchToConvert)
    if pitchToConvert.name in base40Representation:
        tableNum = base40Representation[pitchToConvert.name]
        base40Num = (40 * (pitchToConvert.octave - 1)) + tableNum
        return base40Num

    #raise ValueError('Base40 cannot handle this pitch.')
    raise Base40Exception('Base40 cannot handle this pitch ' + \
          pitchToConvert.nameWithOctave)


def base40Interval(base40NumA, base40NumB):
    '''
    Returns a music21 Interval between two base40 pitch
    numbers, using their delta (difference) as defined
    in Base40. The interval provided is without direction.
    
    Raises a Base40 Exception if the delta doesn't correspond
    to an interval in Base40, or if either base40 pitch
    number doesn't correspond to a pitch name.

    
    >>> musedata.base40.base40Interval(163,191)
    <music21.interval.Interval m6>
    >>> musedata.base40.base40Interval(186,174)      #Descending M3
    <music21.interval.Interval M-3> 
    >>> musedata.base40.base40Interval(1,5)          #INCORRECT!
    <music21.interval.Interval d2> 
    >>> musedata.base40.base40Interval(1,3)
    Traceback (most recent call last):
    Base40Exception: Interval not handled by Base40 2
    >>> musedata.base40.base40Interval(2,6)
    Traceback (most recent call last):
    Base40Exception: Pitch name not assigned to this Base40 number 6 Interval does not exist
    '''
    pitchA = base40Equivalent[(base40NumA-1)%40 + 1]
    pitchB = base40Equivalent[(base40NumB-1)%40 + 1]

    if pitchA == None and pitchB == None:
        raise Base40Exception('Pitch name not assigned to these Base40 numbers ' \
              + str(base40NumA) + ' and ' + str(base40NumA) + ' Interval does not exist')
    elif pitchA == None:
        raise Base40Exception('Pitch name not assigned to this Base40 number ' \
              + str(base40NumA) + ' Interval does not exist')
    elif pitchB == None:
        raise Base40Exception('Pitch name not assigned to this Base40 number ' \
              + str(base40NumB) + ' Interval does not exist')
 
    delta = base40NumB - base40NumA
    return base40DeltaToInterval(delta)


def base40ActualInterval(base40NumA, base40NumB):
    '''
    Calculates a music21 Interval between two Base40 pitch
    numbers, as calculated using the music21.interval module.

    Raises a Base40 Exception if (a) Either of the Base40 pitch
    numbers does not correspond to a pitch name or (b) If
    an unusual interval is encountered that can't be handled
    by music21.

    
    >>> musedata.base40.base40ActualInterval(163,191)
    <music21.interval.Interval m6>
    >>> musedata.base40.base40ActualInterval(186,174) #Descending M3
    <music21.interval.Interval M-3> 
    >>> musedata.base40.base40ActualInterval(1,5)
    <music21.interval.Interval AAAA1>
    >>> musedata.base40.base40ActualInterval(1,3)
    <music21.interval.Interval AA1>
    >>> musedata.base40.base40ActualInterval(2,6)
    Traceback (most recent call last):
    Base40Exception: Pitch name not assigned to this Base40 number 6

    OMIT_FROM_DOCS
    >>> musedata.base40.base40ActualInterval(12,6)
    Traceback (most recent call last):
    Base40Exception: Pitch name not assigned to this Base40 number 12
    '''
    pitchA = base40ToPitch(base40NumA)
    pitchB = base40ToPitch(base40NumB)

    noteA = note.Note()
    noteA.pitch = pitchA
    noteB = note.Note()
    noteB.pitch = pitchB
    
    try:
        return interval.notesToInterval(noteA,noteB)
    except IndexError:
        raise Base40Exception('Unusual interval- Limitation of music21.interval')
    
class Base40Exception(exceptions21.Music21Exception):
    pass
    
#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass


#-------------------------------------------------------------------------------
_DOC_ORDER = [base40ActualInterval]


if __name__ == "__main__":
    import music21
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof

