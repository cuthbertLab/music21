#-------------------------------------------------------------------------------
# Name:         base40.py
# Purpose:      Base40/Music21 Pitch/Interval Translator
#
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import music21
import unittest
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
                 {0: interval.Interval('P1'),
                  1: interval.Interval('A1'),
                  
                  4: interval.Interval('d2'),
                  5: interval.Interval('m2'),
                  6: interval.Interval('M2'),
                  7: interval.Interval('A2'),
                  
                  10: interval.Interval('d3'),
                  11: interval.Interval('m3'),
                  12: interval.Interval('M3'),
                  13: interval.Interval('A3'),
                  
                  16: interval.Interval('d4'),
                  17: interval.Interval('P4'),
                  18: interval.Interval('A4'),
                  
                  22: interval.Interval('d5'),
                  23: interval.Interval('P5'),
                  24: interval.Interval('A5'),

                  27: interval.Interval('d6'),
                  28: interval.Interval('m6'),
                  29: interval.Interval('M6'),
                  30: interval.Interval('A6'),

                  33: interval.Interval('d7'),
                  34: interval.Interval('m7'),
                  35: interval.Interval('M7'),
                  36: interval.Interval('A7'),

                  39: interval.Interval('d8'),
                  40: interval.Interval('P8')
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

    >>> from music21 import *
    >>> base40DeltaToInterval(4)
    <music21.interval.Interval d2>
    >>> base40DeltaToInterval(11)
    <music21.interval.Interval m3>
    >>> base40DeltaToInterval(23)
    <music21.interval.Interval P5>
    >>> base40DeltaToInterval(-23)
    <music21.interval.Interval P-5>
    >>> base40DeltaToInterval(52)
    <music21.interval.Interval M10>
    >>> base40DeltaToInterval(-52)
    <music21.interval.Interval M-10>    
    >>> base40DeltaToInterval(77)
    Traceback (most recent call last):
    Base40Exception: Interval not handled by Base40 37
    '''
    
    direction = 1
    if delta < 0:
       direction = -1
       
    simpleDelta = abs(delta) % 40
    
    try:
        simpleInterval = base40IntervalTable[simpleDelta]
    except KeyError:
        raise Base40Exception('Interval not handled by Base40 ' + str(simpleDelta))

    numOctaves = abs(delta) / 40
    
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
    
    >>> from music21 import *
    >>> base40ToPitch(1)
    C--1
    >>> base40ToPitch(40)
    B##1
    >>> base40ToPitch(23)
    Traceback (most recent call last):
    Base40Exception: Pitch name not assigned to this Base40 number 23
    >>> base40ToPitch(186)
    G5
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

    >>> from music21 import *
    >>> pitchToBase40(pitch.Pitch('C--5'))
    161
    >>> pitchToBase40('F##4')
    142
    >>> pitchToBase40('F###4')
    Traceback (most recent call last):
    Base40Exception: Base40 cannot handle this pitch F###4
    '''
    if type(pitchToConvert) == str:
            pitchToConvert = pitch.Pitch(pitchToConvert)
    if pitchToConvert.name in base40Representation.keys():
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

    >>> from music21 import *
    >>> base40Interval(163,191)
    <music21.interval.Interval m6>
    >>> base40Interval(186,174)      #Descending M3
    <music21.interval.Interval M-3> 
    >>> base40Interval(1,5)          #INCORRECT!
    <music21.interval.Interval d2> 
    >>> base40Interval(1,3)
    Traceback (most recent call last):
    Base40Exception: Interval not handled by Base40 2
    >>> base40Interval(2,6)
    Traceback (most recent call last):
    Base40Exception: Pitch name not assigned to this Base40 number 6 Interval does not exist
    '''
    pitchA = base40Equivalent[(base40NumA-1)%40 + 1]
    pitchB = base40Equivalent[(base40NumB-1)%40 + 1]

    if pitchA == None and pitchB == None:
        raise Base40Exception('Pitch name not assigned to these Base40 numbers ' \
              + str(base40NumA) + ' and ' + str(base40NumA) + ' Interval does not exist')
        return None
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

    >>> from music21 import *
    >>> base40ActualInterval(163,191)
    <music21.interval.Interval m6>
    >>> base40ActualInterval(186,174) #Descending M3
    <music21.interval.Interval M-3> 
    >>> base40ActualInterval(1,5)
    <music21.interval.Interval AAAA1>
    >>> base40ActualInterval(1,3)
    <music21.interval.Interval AA1>
    >>> base40ActualInterval(2,6)
    Traceback (most recent call last):
    Base40Exception: Pitch name not assigned to this Base40 number 6

    OMIT_FROM_DOCS
    >>> base40ActualInterval(12,6)
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
    
class Base40Exception(music21.Music21Exception):
    pass
    
#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof

