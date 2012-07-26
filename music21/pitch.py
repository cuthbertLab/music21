# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         pitch.py
# Purpose:      music21 classes for representing pitches
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009-2012 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''
Classes and functions for creating and manipulating pitches, pitch-space, and accidentals.
Used extensively by note.py8
'''

import os
import string, copy, math
import unittest, doctest

import music21
from music21 import common
from music21 import musicxml
musicxmlMod = musicxml # alias as to avoid name conflict below
from music21 import defaults
from music21 import interval
from music21.musicxml import translate as musicxmlTranslate


from music21 import environment
_MOD = "pitch.py"
environLocal = environment.Environment(_MOD)



STEPREF = {
           'C' : 0,
           'D' : 2, #2
           'E' : 4,
           'F' : 5,
           'G' : 7,
           'A' : 9, #9
           'B' : 11,
               }
STEPNAMES = ['C','D','E','F','G','A','B']

TWELFTH_ROOT_OF_TWO = 2.0 ** (1.0/12)

# how many significant digits to keep in pitch space resolution
# where 1 is a half step. this means that 4 sig digits of cents will be kept
PITCH_SPACE_SIG_DIGITS = 6

# basic accidental string and symbol definitions; additional symbolic and text-based alternatives are given in the set Accidental.set() method
MICROTONE_OPEN = '('
MICROTONE_CLOSE = ')'
accidentalNameToModifier = {
    'natural' : '',
    'sharp' : '#',
    'double-sharp':'##',
    'triple-sharp':'###',
    'quadruple-sharp':'####',
    'flat':'-',
    'double-flat':'--',
    'triple-flat':'---',
    'quadruple-flat':'----',
    'half-sharp':'~',
    'one-and-a-half-sharp':'#~',
    'half-flat':'`',
    'one-and-a-half-flat':'-`',
}

# sort modifiers by length, from longest to shortest
accidentalModifiersSorted = []
for i in (4,3,2,1):
    for sym in accidentalNameToModifier.values():
        if len(sym) == i:
            accidentalModifiersSorted.append(sym)


#-------------------------------------------------------------------------------
# utility functions
def convertPitchClassToNumber(ps):
    '''Given a pitch class or pitch class value, 
    look for strings. If a string is found, 
    replace it with the default pitch class representation.

    >>> from music21 import *
    >>> pitch.convertPitchClassToNumber(3)
    3
    >>> pitch.convertPitchClassToNumber('a')
    10
    >>> pitch.convertPitchClassToNumber('B')
    11
    >>> pitch.convertPitchClassToNumber('3')
    3
    '''
    if common.isNum(ps):
        return ps
    else: # assume is is a string
        if ps in ['a', 'A']:
            return 10
        if ps in ['b', 'B']:
            return 11
        # maybe its a string of an integer?
        return int(ps)
        
def convertPitchClassToStr(pc):
    '''Given a pitch class number, return a string. 

    >>> convertPitchClassToStr(3)
    '3'
    >>> convertPitchClassToStr(10)
    'A'
    '''
    pc = pc % 12 # do just in case
    # replace 10 with A and 11 with B
    return '%X' % pc  # using hex conversion, good up to 15
        

def convertNameToPitchClass(pitchName):
    '''Utility conversion: from a pitch name to a pitch class integer between 0 and 11.

    >>> convertNameToPitchClass('c4')
    0
    >>> convertNameToPitchClass('c#')
    1
    >>> convertNameToPitchClass('d-')
    1
    >>> convertNameToPitchClass('e--')
    2
    >>> convertNameToPitchClass('b2##')
    1
    '''
    # use pitch name reading in Pitch object, 
    # as an Accidental object is created.
    p = Pitch(pitchName)
    return p.pitchClass

def convertNameToPs(pitchName):
    '''Utility conversion: from a pitch name to a pitch space number (floating point MIDI pitch values).

    >>> from music21 import *
    >>> pitch.convertNameToPs('c4')
    60.0
    >>> pitch.convertNameToPs('c2#')
    37.0
    >>> pitch.convertNameToPs('d7-')
    97.0
    >>> pitch.convertNameToPs('e1--')
    26.0
    >>> pitch.convertNameToPs('b2##')
    49.0
    >>> pitch.convertNameToPs('c~4')
    60.5
    '''
    # use pitch name reading in Pitch object, 
    # as an Accidental object is created.
    p = Pitch(pitchName)
    return p.ps

def convertPsToOct(ps):
    '''Utility conversion; does not process internals.
    Converts a midiNote number to an octave number.
    Assume C4 middle C, so 60 returns 4
    >>> [convertPsToOct(59), convertPsToOct(60), convertPsToOct(61)]
    [3, 4, 4]
    >>> [convertPsToOct(12), convertPsToOct(0), convertPsToOct(-12)]
    [0, -1, -2]
    >>> convertPsToOct(135)
    10
    '''
    #environLocal.printDebug(['convertPsToOct: input', ps])
    return int(math.floor(ps / 12.)) - 1

def convertPsToStep(ps):
    '''Utility conversion; does not process internal representations. 

    Takes in a pitch space floating-point value or a MIDI note number (Assume C4 middle C, so 60 returns 4).

    Returns a tuple of Step, an Accidental object, and a Microtone object or None.
    
    >>> convertPsToStep(60)
    ('C', <accidental natural>, (+0c), 0)
    >>> convertPsToStep(66)
    ('F', <accidental sharp>, (+0c), 0)
    >>> convertPsToStep(67)
    ('G', <accidental natural>, (+0c), 0)
    >>> convertPsToStep(68)
    ('G', <accidental sharp>, (+0c), 0)
    >>> convertPsToStep(-2)
    ('B', <accidental flat>, (+0c), 0)

    >>> convertPsToStep(60.5)
    ('C', <accidental half-sharp>, (+0c), 0)
    >>> convertPsToStep(61.5)
    ('C', <accidental one-and-a-half-sharp>, (+0c), 0)
    >>> convertPsToStep(62)
    ('D', <accidental natural>, (+0c), 0)
    >>> convertPsToStep(62.5)
    ('D', <accidental half-sharp>, (+0c), 0)
    >>> convertPsToStep(135)
    ('E', <accidental flat>, (+0c), 0)
    >>> convertPsToStep(70)
    ('B', <accidental flat>, (+0c), 0)
    >>> convertPsToStep(70.5)
    ('B', <accidental half-flat>, (+0c), 0)
    '''
    # rounding here is essential
    ps = round(ps, PITCH_SPACE_SIG_DIGITS)
    pcReal = ps % 12 
    # micro here will be between 0 and 1
    pc, micro = divmod(pcReal, 1)

    #environLocal.printDebug(['convertPsToStep(): post divmod',  'ps', repr(ps), 'pcReal', repr(pcReal), 'pc', repr(pc), 'micro', repr(micro)])

    # if close enough to a quarter tone
    if round(micro, 1) == 0.5:
        # if can round to .5, than this is a quartertone accidental
        alter = 0.5
        # need to find microtonal alteration around this value
        # of alter is 0.5 and micro is .7 than  micro should be .2
        # of alter is 0.5 and micro is .4 than  micro should be -.1
        micro = micro - alter

    # if greater than .5
    elif micro > .25 and micro < .75:
        alter = 0.5
        micro = micro - alter
    # if closer to 1, than go to the higher alter and get negative micro
    elif micro >= .75 and micro < 1:
        alter = 1
        micro = micro - alter
    # not greater than .25
    elif micro > 0:
        alter = 0
        micro = micro # no change necessary
    else:
        alter = 0
        micro = 0

    pc = int(pc)

    #environLocal.printDebug(['convertPsToStep(): post', 'alter', alter, 'micro', micro, 'pc', pc])

    octShift = 0
    # check for unnecessary enharmonics
    if pc in [4, 11] and alter == 1:
        acc = Accidental(0)
        pcName = (pc + 1) % 12
        # if a B, we are shifting out of this octave, and need to get 
        # the above octave, which may not be represented in ps value 
        if pc == 11:
            octShift = 1
    # its a natural; nothing to do
    elif pc in STEPREF.values():
        acc = Accidental(0+alter)
        pcName = pc 
    # if we take the pc down a half-step, do we get a stepref (natural) value
    elif pc-1 in [0, 5, 7]: # c, f, g: can be sharped
        # then we need an accidental to accommodate; here, a sharp
        acc = Accidental(1+alter)
        pcName = pc-1
    # if we take the pc up a half-step, do we get a stepref (natural) value
    elif pc+1 in [11, 4]: # b, e: can be flattened
        # then we need an accidental to accommodate; here, a flat
        acc = Accidental(-1+alter) 
        pcName = pc+1
    else:
        raise PitchException('cannot match condition for pc: %s' % pc)

    for key, value in STEPREF.items():
        if pcName == value:
            name = key
            break

    # if a micro is present, create object, else return None
    if micro != 0:
        # provide cents value; these are alter values
        micro = Microtone(micro*100)
    else:
        micro = Microtone(0)

    return name, acc, micro, octShift

def convertStepToPs(step, oct, acc=None, microtone=None):
    '''Utility conversion; does not process internals.
    Takes in a note name string, octave number, and optional 
    Accidental object.

    Returns a pitch space value as a floating point MIDI note number.

    >>> from music21 import *
    >>> pitch.convertStepToPs('c', 4, pitch.Accidental('sharp'))
    61.0
    >>> pitch.convertStepToPs('d', 2, pitch.Accidental(-2))
    36.0
    >>> pitch.convertStepToPs('b', 3, pitch.Accidental(3))
    62.0
    >>> pitch.convertStepToPs('c', 4, pitch.Accidental('half-flat'))
    59.5
    '''
    step = step.strip().upper()
    ps = float(((oct + 1) * 12) + STEPREF[step])

    if acc is not None:
        # assume that this is an accidental object
        ps = ps + acc.alter
    if microtone is not None:
        # assume that this is an accidental object
        ps = ps + microtone.alter
    return ps


def convertPsToFq(ps):
    '''Utility conversion; does not process internals.
    
    Converts a midiNote number to a frequency in Hz.
    Assumes A4 = 440 Hz
    
    
    >>> from music21 import *
    >>> pitch.convertPsToFq(69)
    440.0
    >>> str(pitch.convertPsToFq(60))
    '261.625565301'
    >>> str(pitch.convertPsToFq(2))
    '9.17702399742'
    >>> str(pitch.convertPsToFq(135))
    '19912.1269582'

    OMIT_FROM_DOCS
    NOT CURRENTLY USED: since freq440 had its own conversion
    methods, and wanted the numbers to be EXACTLY the same
    either way
    '''
    try:
        fq = 440.0 * pow(2, (((ps-60)-9)/12.0))
    except OverflowError:
        fq = 0
    return fq

def convertFqToPs(fq):
    '''Utility conversion; does not process internals.
    Converts a frequency in Hz into a midiNote number.
    Assumes A4 = 440 Hz
    >>> convertFqToPs(440)
    69.0
    >>> convertFqToPs(261.62556530059862)
    60.0
    '''
    post = 12 * (math.log(fq / 440.0) / math.log(2)) + 69 
    #environLocal.printDebug(['convertFqToPs():', 'input', fq, 'output', repr(post)])
    # rounding here is essential
    return round(post, PITCH_SPACE_SIG_DIGITS)  



def convertCentsToAlterAndCents(shift):
    '''Given any floating point value, split into accidental and microtone components. 
    
    >>> from music21 import *
    >>> pitch.convertCentsToAlterAndCents(125)
    (1, 25.0)
    >>> pitch.convertCentsToAlterAndCents(-75)
    (-0.5, -25.0)
    >>> pitch.convertCentsToAlterAndCents(-125)
    (-1, -25.0)
    >>> pitch.convertCentsToAlterAndCents(-200)
    (-2, 0.0)
    >>> pitch.convertCentsToAlterAndCents(235)
    (2.5, -15.0)
    '''
    value = shift

    alterAdd = 0
    if value > 150:
        while value > 100:
            value -= 100
            alterAdd += 1
    elif value < -150:
        while value < 100:
            value += 100
            alterAdd -= 1

    if value < -75: 
        alterShift = -1
        cents = value + 100
    elif value >= -75 and value < -25:
        alterShift = -.5
        cents = value + 50
    elif value >= -25 and value <= 25:
        alterShift = 0
        cents = value
    elif value > 25 and value <= 75:
        alterShift = .5
        cents = value - 50
    elif value > 75: 
        alterShift = 1
        cents = value - 100
    else:
        raise Exception('value exceeded range: %s' % value)
    return alterShift+alterAdd, float(cents)


def convertHarmonicToCents(value):
    '''Given a harmonic number, return the total number shift in cents assuming 12 tone equal temperament. 
    
    >>> convertHarmonicToCents(8)
    3600
    >>> [convertHarmonicToCents(x) for x in [5, 6, 7, 8]]
    [2786, 3102, 3369, 3600]
    >>> [convertHarmonicToCents(x) for x in [16, 17, 18, 19]]
    [4800, 4905, 5004, 5098]

    >>> [convertHarmonicToCents(x) for x in range(1, 33)]
    [0, 1200, 1902, 2400, 2786, 3102, 3369, 3600, 3804, 3986, 4151, 4302, 4441, 4569, 4688, 4800, 4905, 5004, 5098, 5186, 5271, 5351, 5428, 5502, 5573, 5641, 5706, 5769, 5830, 5888, 5945, 6000]


    Works with subHarmonics as well by specifying them as either 1/x or negative numbers.
    note that -2 is the first subharmonic, since -1 == 1:
    
    >>> [convertHarmonicToCents(1.0/x) for x in [1, 2, 3, 4]]
    [0, -1200, -1902, -2400]
    >>> [convertHarmonicToCents(x) for x in [-1, -2, -3, -4]]
    [0, -1200, -1902, -2400]
    
    So the fifth subharmonic of the 7th harmonic (remember floating point division for Python 2.x!),
    which is C2->C3->G3->C4->E4->G4->B\`4 --> B\`3->E\`3->B\`2->G-\`2
    
    >>> convertHarmonicToCents(7.0/5.0)
    583
    >>> convertHarmonicToCents(7.0) - convertHarmonicToCents(5.0)
    583
    '''
    if value < 0: #subharmonics
        value = 1.0/(abs(value))
    return int(round(1200*math.log(value, 2), 0))




#-------------------------------------------------------------------------------
class AccidentalException(music21.Music21Exception):
    pass

class PitchException(music21.Music21Exception):
    pass

class MicrotoneException(music21.Music21Exception):
    pass

#-------------------------------------------------------------------------------
class Microtone(music21.JSONSerializer):
    '''
    The Microtone object defines a pitch transformation above 
    or below a standard Pitch and its Accidental.

    >>> from music21 import *
    >>> m = pitch.Microtone(20)
    >>> m.cents
    20
    >>> m.alter
    0.2...
    >>> m
    (+20c)


    Microtones can be shifted according to the harmonic. Here we take the 3rd
    harmonic of the previous microtone

    >>> m.harmonicShift = 3
    >>> m
    (+20c+3rdH)
    >>> m.cents
    1922
    >>> m.alter
    19.2...


    Microtonal changes can be positive or negative.
    Both Positive and negative numbers can optionally be placed in parentheses
    Negative numbers in parentheses still need the minus sign.
    

    >>> m = pitch.Microtone('(-33.333333)')
    >>> m
    (-33c)
    >>> m = pitch.Microtone('33.333333')
    >>> m
    (+33c)
    
    
    Note that we round the display of microtones to the nearest cent,
    but we keep the exact alteration in both .cents and .alter:

    >>> m.cents
    33.333...
    >>> m.alter
    0.3333...
    '''
    def __init__(self, centsOrString=0):
        music21.JSONSerializer.__init__(self)

        self._centShift = 0
        self._harmonicShift = 1 # the first harmonic is the start

        if common.isNum(centsOrString):
            self._centShift = centsOrString # specify harmonic in cents
        else:
            self._parseString(centsOrString)
        # need to additional store a reference to a position in a 
        # another pitches overtone series? 
        # such as: A4(+69c [7thH/C3])?

    def _parseString(self, value):
        '''Parse a string representation.
        '''
        # strip any delimiters
        value = value.replace(MICROTONE_OPEN, '')
        value = value.replace(MICROTONE_CLOSE, '')

        # need to look for and split off harmonic definitions

        if value[0] in ['+'] or value[0].isdigit():
            # positive cent representation
            num, junk = common.getNumFromStr(value, numbers='0123456789.')
            if num == '':
                raise MicrotoneException('no numbers found in string value: %s' % value)
            else:
                centValue = float(num)
        elif value[0] in ['-']:
            num, junk = common.getNumFromStr(value[1:], numbers='0123456789.')
            centValue = float(num) * -1
        
        self._centShift = centValue


    def __repr__(self):
        '''Return a string representation
        '''
        # cent values may be of any resolution, but round to nearest int
        
        if self._centShift >= 0:
            sub = '+%sc' % int(round(self._centShift))
        elif self._centShift < 0:
            sub = '%sc' % int(round(self._centShift))
        # only show a harmonic if present
        if self._harmonicShift != 1:
            sub += '+%s%sH' % (self._harmonicShift,
                            common.ordinalAbbreviation(self._harmonicShift))
        return '%s%s%s' % (MICROTONE_OPEN, sub, MICROTONE_CLOSE)


    def __eq__(self, other):
        '''Compare cents.

        >>> from music21 import *
        >>> m1 = pitch.Microtone(20)
        >>> m2 = pitch.Microtone(20)
        >>> m3 = pitch.Microtone(21)
        >>> m1 == m2
        True
        >>> m1 == m3
        False
        '''
        if other is None:
            return False
        if other.cents == self.cents:
            return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def _getHarmonicShift(self):
        return self._harmonicShift

    def _setHarmonicShift(self, value):
        self._harmonicShift = value

    harmonicShift = property(_getHarmonicShift, _setHarmonicShift, 
        doc = '''Set or get the harmonic shift, altering the microtone
        ''')


    def _getCents(self):
        '''Return the cents.
        '''
        return convertHarmonicToCents(self._harmonicShift) + self._centShift

    cents = property(_getCents, 
        doc = '''Return the microtone value in cents. 
        This is not a settable property. To set the value in cents, 
        simply use that value as a creation argument. 
        ''')

    def _getAlter(self):
        '''Return the value as an alter value, where 1 is 1 half step.
        '''
        return self._getCents() * .01
        
    alter = property(_getAlter, 
        doc = '''Return the microtone value in accidental alter values. 
        ''')



#-------------------------------------------------------------------------------

def _getSpanishCardinal(int):
    if int == 1:
        return ''
    elif int == 2:
        return 'doble'
    elif int == 3:
        return 'triple'
    elif int == 4:
        return 'cuádruple'

def _getSpanishSolfege(pitch):
        if pitch == 'A':
            return 'la '
        if pitch == 'B':
            return 'si '
        if pitch == 'C':
            return 'do '
        if pitch == 'D':
            return 're '
        if pitch == 'E':
            return 'mi '
        if pitch == 'F':
            return 'fa '
        if pitch == 'G':
            return 'sol '
        
class Accidental(music21.Music21Object):
    '''
    Accidental class, representing the symbolic and numerical representation of pitch deviation from a pitch name (e.g., G, B). 
    
    Two accidentals are considered equal if their names are equal.

    Accidentals have three defining attributes: a name, a modifier, and an alter. 
    For microtonal specifications, the name and modifier are the same except in
    the case of half-sharp, half-flat, one-and-a-half-flat, and one-and-a-half-sharp.
    
    Accidentals up to quadruple-sharp and quadruple-flat are allowed.

    Natural-sharp etc. (for canceling a previous flat) are not yet supported.


    >>> from music21 import *
    >>> a = pitch.Accidental('sharp')
    >>> a.name, a.alter, a.modifier
    ('sharp', 1.0, '#')

    '''
    # define order to present names in documentation; use strings
    _DOC_ORDER = ['name', 'modifier', 'alter', 'set']
    # documentation for all attributes (not properties or methods)
    _DOC_ATTR = {
    'name': '''A string name of the Accidental, such as "sharp" or 
        "double-flat".''',
    'modifier': '''A string symbol used to modify the pitch name, such as "#" or 
        "-" for sharp and flat, respectively.''',
    'alter': '''A signed decimal representing the number of half-steps shifted
         by this Accidental, such as 1.0 for a sharp and -.5 for a quarter tone flat.''',
    'displaySize': 'Size in display: "cue", "large", or a percentage.',
    'displayStyle': 'Style of display: "parentheses", "bracket", "both".',
    'displayStatus': 'Determines if this Accidental is to be displayed; can be None (for not set), True, or False.',
    'displayLocation': 'Location of accidental: "normal", "above", "below".'
    }

    def __init__(self, specifier='natural'):
        music21.Music21Object.__init__(self)

        # managed by properties
        self._displayType = "normal" # always, never, unless-repeated, even-tied
        self._displayStatus = None # None, True, False
    
        # not yet managed by properties: TODO
        self.displayStyle = "normal" # "parentheses", "bracket", "both"
        self.displaySize  = "full"   # "cue", "large", or a percentage
        self.displayLocation = "normal" # "normal", "above" = ficta, "below"
        # above and below could also be useful for gruppetti, etc.

        self._name = None
        self._modifier = ''
        self._alter = 0.0     # semitones to alter step
        #alterFrac = [0,0]   # fractional alteration 
        # (e.g., 1/6); fraction class in 2.6
        #alterExp  = [0,0,0] # exponental alteration 
        # (e.g., [2,3,19] = 2**(3/19))
        #alterHarm = 0       # altered according to a harmonic
        #environLocal.printDebug(['specifier', specifier])
        self.set(specifier)

    def __repr__(self):
        return '<accidental %s>' % self.name
        

    def __eq__(self, other):
        '''Equality. Needed for pitch comparisons.

        >>> from music21 import *
        >>> a = pitch.Accidental('double-flat')
        >>> b = pitch.Accidental('double-flat')
        >>> c = pitch.Accidental('double-sharp')
        >>> a == b   
        True
        >>> a == c
        False

        '''
        if other is None or not isinstance(other, Accidental):
            return False
        if self.name == other.name: 
            return True
        else: 
            return False

    def __ne__(self, other):
        '''Inequality. Needed for pitch comparisons.
        '''
        if other is None:
            return True
        if self.name == other.name: 
            return False
        else: 
            return True


    def __gt__(self, other):
        '''Greater than.  Based on the accidentals' alter function.

        >>> from music21 import *
        >>> a = pitch.Accidental('sharp')
        >>> b = pitch.Accidental('flat')
        >>> a < b   
        False
        >>> a > b
        True
        '''
        if other is None:
            return False
        if self.alter > other.alter: 
            return True
        else: 
            return False

    def __ge__(self, other):
        '''Greater than or equal.  Based on the accidentals' alter function.

        >>> from music21 import *
        >>> a = pitch.Accidental('sharp')
        >>> b = pitch.Accidental('flat')
        >>> a >= b
        True
        '''
        return self.__gt__(other) or self.__eq__(other)

    def __lt__(self, other):
        '''Less than

        >>> from music21 import *
        >>> a = pitch.Accidental('natural')
        >>> b = pitch.Accidental('flat')
        >>> a > b   
        True
        >>> a < b
        False
        '''
        if other is None:
            return True
        if self.alter < other.alter: 
            return True
        else: 
            return False

    def __le__(self, other):
        '''Less than or equal.  Based on the accidentals' alter function.

        >>> from music21 import *
        >>> a = pitch.Accidental('sharp')
        >>> b = pitch.Accidental('flat')
        >>> c = pitch.Accidental('sharp')
        >>> a <= b
        False
        >>> a <= c
        True
        '''
        return self.__lt__(other) or self.__eq__(other)


    def set(self, name):
        '''
        Provide a value to the Accidental. Strings values, numbers, and Lilypond
        Abbreviations are all accepted.  

        >>> from music21 import *
        >>> a = pitch.Accidental()
        >>> a.set('sharp')
        >>> a.alter == 1
        True

        >>> a = pitch.Accidental()
        >>> a.set(2)
        >>> a.modifier == "##"
        True

        >>> a = pitch.Accidental()
        >>> a.set(2.0)
        >>> a.modifier == "##"
        True

        >>> a = pitch.Accidental('--')
        >>> a.alter
        -2.0
        '''
        if common.isStr(name):
            name = name.lower() # sometimes args get capitalized
        if name in ['natural', "n", 0]: 
            self._name = 'natural'
            self._alter = 0.0
        elif name in ['sharp', accidentalNameToModifier['sharp'], "is", 1, 1.0]:
            self._name = 'sharp'
            self._alter = 1.0
        elif name in ['double-sharp', accidentalNameToModifier['double-sharp'], 
            "isis", 2]:
            self._name = 'double-sharp'
            self._alter = 2.0
        elif name in ['flat', accidentalNameToModifier['flat'], "es", -1]:
            self._name = 'flat'
            self._alter = -1.0
        elif name in ['double-flat', accidentalNameToModifier['double-flat'], 
            "eses", -2]:
            self._name = 'double-flat'
            self._alter = -2.0
        
        elif name in ['half-sharp', accidentalNameToModifier['half-sharp'], 
            'quarter-sharp', 'ih', 'semisharp', .5]:
            self._name = 'half-sharp'
            self._alter = 0.5
        elif name in ['one-and-a-half-sharp', 
            accidentalNameToModifier['one-and-a-half-sharp'],
            'three-quarter-sharp', 'three-quarters-sharp', 'isih', 
            'sesquisharp', 1.5]:
            self._name = 'one-and-a-half-sharp'
            self._alter = 1.5  
        elif name in ['half-flat', accidentalNameToModifier['half-flat'], 
            'quarter-flat', 'eh', 'semiflat', -.5]:
            self._name = 'half-flat'
            self._alter = -0.5
        elif name in ['one-and-a-half-flat', 
            accidentalNameToModifier['one-and-a-half-flat'],
            'three-quarter-flat', 'three-quarters-flat', 'eseh', 
            'sesquiflat', -1.5]:
            self._name = 'one-and-a-half-flat'
            self._alter = -1.5
        elif name in ['triple-sharp', accidentalNameToModifier['triple-sharp'], 
            'isisis', 3]:
            self._name = 'triple-sharp'
            self._alter = 3.0
        elif name in ['quadruple-sharp', 
            accidentalNameToModifier['quadruple-sharp'], 'isisisis', 4]:
            self._name = 'quadruple-sharp'
            self._alter = 4.0
        elif name in ['triple-flat', accidentalNameToModifier['triple-flat'],
            'eseses', -3]:
            self._name = 'triple-flat'
            self._alter = -3.0
        elif name in ['quadruple-flat', 
            accidentalNameToModifier['quadruple-flat'], 'eseseses', -4]:
            self._name = 'quadruple-flat'
            self._alter = -4.0
        else:
            raise AccidentalException('%s is not a supported accidental type' % name)

        self._modifier = accidentalNameToModifier[self._name]


    def isTwelveTone(self):
        '''Return a boolean if this Accidental describes a twelve-tone pitch.

        >>> from music21 import *
        >>> a = pitch.Accidental('~')
        >>> a.isTwelveTone()
        False

        >>> a = pitch.Accidental('###')
        >>> a.isTwelveTone()
        True

        '''
        if self.name in ['half-sharp', 'one-and-a-half-sharp', 'half-flat', 
            'one-and-a-half-flat', ]:
            return False
        return True


    #---------------------------------------------------------------------------
    # main properties
    def _getName(self):
        return self._name

    def _setName(self, value):
        # can alternatively call set()
        self._name = value
    
    name = property(_getName, _setName, 
        doc = '''Get or set the name of the Accidental, like 'sharp' or 'double-flat'
        ''')

    def _getAlter(self):
        return self._alter

    def _setAlter(self, value):
        # can alternatively call set()
        self._alter = value
    
    alter = property(_getAlter, _setAlter, 
        doc = '''Get or set the alter of the Accidental, or the semitone shift caused by the Accidental.'
        ''')


    def _getModifier(self):
        return self._modifier

    def _setModifier(self, value):
        # can alternatively call set()
        self._modifier = value
    
    modifier = property(_getModifier, _setModifier, 
        doc = '''Get or set the alter of the modifier, or the string representation.'
        ''')


    def _getDisplayType(self):
        return self._displayType

    def _setDisplayType(self, value):
        if value not in ['normal', 'always', 'never', 
            'unless-repeated', 'even-tied']:
            raise AccidentalException('supplied display type is not supported: %s' % value)
        self._displayType = value
    
    displayType = property(_getDisplayType, _setDisplayType, 
        doc = '''
        Returns or sets the display type of the accidental
        
        "normal" (default) displays it if it is the first in measure,
        or is needed to contradict a previous accidental, etc.
        
        other valid terms:
        "always", "never", "unless-repeated" (show always unless
        the immediately preceding note is the same), "even-tied"
        (stronger than always: shows even if it is tied to the
        previous note)
        ''')


    def _getDisplayStatus(self):
        return self._displayStatus

    def _setDisplayStatus(self, value):
        if value not in [True, False, None]:
            raise AccidentalException('supplied display status is not supported: %s' % value)
        self._displayStatus = value
    
    displayStatus = property(_getDisplayStatus, _setDisplayStatus, 
        doc = '''
        Given the displayType, should this accidental be displayed?

        In general, a display status of None is assumed to mean that no high-level 
        processing of accidentals has happened. 

        Can be True, False, or None if not defined. For contexts where
        the next program down the line cannot evaluate displayType.  See
        stream.makeAccidentals() for more information.
        ''')


    def _getUnicode(self):
        '''Return a unicode representation of this accidental.
        '''
        # all unicode musical symbols can be found here:
        # http://www.fileformat.info/info/unicode/block/musical_symbols/images.htm

        if self.name == 'natural':
            # 266E
            return u'\u266e'

        elif self.name == 'sharp':
            # 266F
            return u'\u266f'
        # http://www.fileformat.info/info/unicode/char/1d12a/index.htm
        elif self.name == 'double-sharp':
            # 1D12A
            # note that this must be expressed as a surrogate pair
            return u'\uD834\uDD2A'
        elif self.name == 'half-sharp':
            # 1D132
            return u"\uD834\uDD32"

        elif self.name == 'flat':
            # 266D
            return u'\u266D'
        elif self.name == 'double-flat':
            # 1D12B
            return u'\uD834\uDD2B'
        elif self.name == 'half-flat':
            # 1D133
            # raised flat: 1D12C
            return u"\uD834\uDD33" 

        else: # get our best ascii representation
            return self.modifier

    unicode = property(_getUnicode, 
        doc = '''
        Return a unicode representation of this accidental or the best ascii representation
        if that is not possible.
        ''')



    def _getFullName(self):
        # keep lower case for now
        return self.name

    fullName = property(_getFullName, 
        doc = '''Return the most complete representation of this Accidental. 

        >>> from music21 import *
        >>> a = pitch.Accidental('double-flat')
        >>> a.fullName
        'double-flat'

        Note that non-standard microtones are converted to standard ones
        
        >>> a = pitch.Accidental('quarter-flat')
        >>> a.fullName
        'half-flat'

        ''')


    #---------------------------------------------------------------------------
    def inheritDisplay(self, other):
        '''Given another Accidental object, inherit all the display properites
        of that object. 

        This is needed when transposing Pitches: we need to retain accidental display properties. 

        >>> from music21 import *
        >>> a = pitch.Accidental('double-flat')
        >>> a.displayType = 'always'
        >>> b = pitch.Accidental('sharp')
        >>> b.inheritDisplay(a)
        >>> b.displayType
        'always'
        '''        
        if other != None: # empty accidental attributes are None
            for attr in ['displayType', 'displayStatus', 
                        'displayStyle', 'displaySize', 'displayLocation']:
                value = getattr(other, attr)
                setattr(self, attr, value)


    def _getMx(self):
        """From music21 to MusicXML

        >>> from music21 import *
        >>> a = pitch.Accidental()
        >>> a.set('half-sharp')
        >>> a.alter == .5
        True
        >>> mxAccidental = a.mx
        >>> mxAccidental.get('content')
        'quarter-sharp'
        """
        if self.name == "half-sharp": 
            mxName = "quarter-sharp"
        elif self.name == "one-and-a-half-sharp": 
            mxName = "three-quarters-sharp"
        elif self.name == "half-flat": 
            mxName = "quarter-flat"
        elif self.name == "one-and-a-half-flat": 
            mxName = "three-quarters-flat"
        else: # all others are the same
            mxName = self.name

        mxAccidental = musicxmlMod.Accidental()
# need to remove display in this case and return None
#         if self.displayStatus == False:
#             pass
        mxAccidental.set('charData', mxName)
        return mxAccidental


    def _setMx(self, mxAccidental):
        """From MusicXML to Music21
        
        >>> from music21 import *
        >>> a = musicxml.Accidental()
        >>> a.set('content', 'half-flat')
        >>> a.get('content')
        'half-flat'
        >>> b = pitch.Accidental()
        >>> b.mx = a
        >>> b.name
        'half-flat'
        """
        mxName = mxAccidental.get('charData')
        if mxName == "quarter-sharp": 
            name = "half-sharp"
        elif mxName == "three-quarters-sharp": 
            name = "one-and-a-half-sharp"
        elif mxName == "quarter-flat": 
            name = "half-flat"
        elif mxName == "three-quarters-flat": 
            name = "one-and-a-half-flat"
        elif mxName == "flat-flat": 
            name = "double-flat"
        elif mxName == "sharp-sharp": 
            name = "double-sharp"
        else:
            name = mxName
        # need to use set her to get all attributes up to date
        self.set(name)

    # property
    mx = property(_getMx, _setMx)








#-------------------------------------------------------------------------------
class Pitch(music21.Music21Object):
    '''
    An object for storing pitch values. 
    All values are represented internally as a 
    scale step (self.step), and octave and an 
    accidental object. In addition, pitches know their 
    pitch space representation (self.ps); altering any 
    of the first three changes the pitch space (ps) representation. 
    Similarly, altering the .ps representation 
    alters the first three.
    
    
    Two Pitches are equal if they represent the same
    pitch and are spelled the same.  A Pitch is greater
    than another Pitch if its pitchSpace is greater than
    the other.  Thus C##4 > D-4.
    
    '''
    # define order to present names in documentation; use strings
    _DOC_ORDER = ['name', 'nameWithOctave', 'step', 'pitchClass', 'octave', 'midi', 'german', 'french', 'spanish', 'italian','dutch']
    # documentation for all attributes (not properties or methods)
    _DOC_ATTR = {
    }

    # constants shared by all classes
    _twelfth_root_of_two = TWELFTH_ROOT_OF_TWO

    def __init__(self, name=None, **keywords):
        '''Create a Pitch.

        Optional parameter name should include a step and accidental character(s)

        it can also include an octave number ("C#4", "B--3", etc.) so long 
        as it's 0 or higher.

        >>> from music21 import *
        >>> p1 = pitch.Pitch('a#')
        >>> p1
        A#
        >>> p2 = pitch.Pitch(3)
        >>> p2
        E-
        
        
        This is B-double flat in octave 3, not B- in octave -3.
        
        
        >>> p3 = pitch.Pitch("B--3")
        >>> p3.accidental
        <accidental double-flat>
        >>> p3.octave
        3
        
        
        Just about everything can be specified in keywords too:
        
        
        >>> p4 = pitch.Pitch(name = 'C', accidental = '#', octave = 7, microtone = -30)
        >>> p4.fullName
        'C7-sharp (-30c)'
        
        
        '''
        music21.Music21Object.__init__(self)

        # this should not be set, as will be updated when needed
        self._ps = None # pitch space representation, w C4=60 (midi)
        # self._ps must correspond to combination of step and alter
        self._step = defaults.pitchStep # this is only the pitch step
        # keep an accidental object based on self._alter
        
        self._overridden_freq440 = None

        # store an Accidental and Microtone objects
        # note that creating an Accidental objects is much more time consuming
        # than a microtone
        self._accidental = None
        self._microtone = Microtone() 

        # should this remain an attribute or only refer to value in defaults
        self.defaultOctave = defaults.pitchOctave
        self._octave = None
        self._pitchSpaceNeedsUpdating = True

        # if True, accidental is not known; is determined algorithmically
        # likely due to pitch data from midi or pitch space/class numbers
        self.implicitAccidental = False

        # name combines step, octave, and accidental
        if name is not None:
            if not common.isNum(name):       
                self._setName(name) # set based on string
            else: # is a number
                self._setPitchClass(name)

        # the fundamental attribute stores an optional pitch
        # that defines the fundamental used to create this Pitch
        self.fundamental = None

        # override just about everything with keywords
        # necessary for ImmutablePitch objects
        if len(keywords) > 0:
            if 'name' in keywords:
                self._setName(keywords['name']) # set based on string
            if 'octave' in keywords:
                self._octave = keywords['octave']
            if 'accidental' in keywords:
                if isinstance(keywords['accidental'], Accidental):
                    self.accidental = keywords['accidental']
                else:
                    self.accidental = Accidental(keywords['accidental'])
            if 'microtone' in keywords:
                if isinstance(keywords['microtone'], Microtone):
                    self.microtone = keywords['microtone']
                else:
                    self.microtone = Microtone(keywords['microtone'])
            if 'pitchClass' in keywords:
                self._setPitchClass(keywords['pitchClass'])
            if 'fundamental' in keywords:
                self.fundamental = keywords['fundamental']
            if 'midi' in keywords:
                self.midi = keywords['midi']
            if 'ps' in keywords:
                self.ps = keywords['ps']

    def __repr__(self):
        name = self.nameWithOctave
        if self.microtone.cents != 0:
            return name + self._microtone.__repr__()
        else:
            return name

    def __eq__(self, other):
        '''Do not accept enharmonic equivalance.
        
        >>> from music21 import *
        >>> a = pitch.Pitch('c2')
        >>> a.octave
        2
        >>> b = pitch.Pitch('c#4')
        >>> b.octave
        4
        >>> a == b
        False
        >>> a != b
        True
        
        >>> c = 7
        >>> a == c
        False
        
        >>> a != c
        True
        
        >>> d = pitch.Pitch('d-4')
        >>> b == d
        False
        
        '''
        if other is None:
            return False
        elif (hasattr(other, 'octave') == False or hasattr(other, 'step') == False or
              hasattr(other, 'step') == False):
            return False
        elif (self.octave == other.octave and self.step == other.step and 
            self.accidental == other.accidental and self.microtone == other.microtone):
            return True
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        '''Do not accept enharmonic equivalence. Based entirely on pitch space 
        representation.
        
        >>> from music21 import *
        >>> a = pitch.Pitch('c4')
        >>> b = pitch.Pitch('c#4')
        >>> a < b
        True
        '''
        if self.ps < other.ps:
            return True
        else:
            return False

    def __le__(self, other):
        '''Less than or equal.  Based on the accidentals' alter function.

        >>> from music21 import *
        >>> a = pitch.Pitch('d4')
        >>> b = pitch.Pitch('d8')
        >>> c = pitch.Pitch('d4')
        >>> a >= b
        False
        >>> a >= c
        True
        '''
        return self.__lt__(other) or self.__eq__(other)

    def __gt__(self, other):
        '''Do not accept enharmonic equivialance. Based entirely on pitch space 
        representation.
        
        >>> from music21 import *
        >>> a = pitch.Pitch('d4')
        >>> b = pitch.Pitch('d8')
        >>> a > b
        False
        '''
        if self.ps > other.ps:
            return True
        else:
            return False

    def __ge__(self, other):
        '''Greater than or equal.  Based on the accidentals' alter function.

        >>> from music21 import *
        >>> a = pitch.Pitch('d4')
        >>> b = pitch.Pitch('d8')
        >>> c = pitch.Pitch('d4')
        >>> a >= b
        False
        >>> a >= c
        True
        '''
        return self.__gt__(other) or self.__eq__(other)

    #---------------------------------------------------------------------------
    def _getAccidental(self):
        return self._accidental
    
    def _setAccidental(self, value):
        if isinstance(value, basestring):
            self._accidental = Accidental(value)
        elif common.isNum(value):
            # check and add any microtones
            alter, cents = convertCentsToAlterAndCents(value*100.0)
            self._accidental = Accidental(alter)
            if abs(cents) > .01:
                self._setMicrotone(cents)
        else: # assume an accidental object
            self._accidental = value
        self._pitchSpaceNeedsUpdating = True
    
    accidental = property(_getAccidental, _setAccidental,
        doc='''
        Stores an optional accidental object contained within the
        Pitch object.  This might return None, which is different
        than a natural accidental:
        

        >>> from music21 import *
        >>> a = pitch.Pitch('E-')
        >>> a.accidental.alter
        -1.0
        >>> a.accidental.modifier
        '-'
        
        >>> b = pitch.Pitch('C4')
        >>> b.accidental is None
        True
        >>> b.accidental = pitch.Accidental('natural')
        >>> b.accidental is None
        False
        >>> b.accidental
        <accidental natural>
        
        >>> b = pitch.Pitch('C4')
        >>> b.accidental = 1.5
        >>> b
        C#4(+50c)
        >>> b.accidental = 1.65
        >>> b
        C#~4(+15c)
        >>> b.accidental = 1.95
        >>> b
        C##4(-5c)
        ''')


    def _getMicrotone(self):
        return self._microtone
    
    def _setMicrotone(self, value):
        if (isinstance(value, basestring) or common.isNum(value)):
            self._microtone = Microtone(value)
        elif value is None: # set to zero
            self._microtone = Microtone(0)
        elif isinstance(value, Microtone):
            self._microtone = value
        else:
            raise PitchException("Cannot get a microtone object from %s", value)
        # look for microtones of 0 and set-back to None

#         if common.almostEquals(self._microtone.cents, 0.0):
#             self._microtone = None

        self._pitchSpaceNeedsUpdating = True
    
    microtone = property(_getMicrotone, _setMicrotone,
        doc='''
        Sets the microtone object contained within the
        Pitch object. Microtones must be supplied in cents.

        >>> from music21 import *
        >>> p = pitch.Pitch('E4-')
        >>> p.microtone.cents == 0
        True
        >>> p.ps
        63.0
        >>> p.microtone = 33 # adjustment in cents     
        >>> p
        E-4(+33c)
        >>> (p.name, p.nameWithOctave) # these representations are unchanged
        ('E-', 'E-4')
        >>> p.microtone = '(-12c' # adjustment in cents     
        >>> p
        E-4(-12c)
        >>> p.microtone = pitch.Microtone(-30)
        >>> p
        E-4(-30c)
        
        ''')


    def isTwelveTone(self):
        '''
        Return True if this Pitch is 
        one of the twelve tones available on a piano
        keyboard. Returns False if it instead 
        has a non-zero microtonal adjustment or 
        has a quarter tone accidental.


        >>> from music21 import *
        >>> p = pitch.Pitch('g4')
        >>> p.isTwelveTone()
        True
        >>> p.microtone = -20
        >>> p.isTwelveTone()
        False
        
        
        >>> p2 = pitch.Pitch('g~4')
        >>> p2.isTwelveTone()
        False            
        '''
        if self.accidental is not None:
            if not self.accidental.isTwelveTone():
                return False
        if self.microtone.cents != 0:
            return False
        return True


    def getCentShiftFromMidi(self):
        '''Get cent deviation of this pitch from MIDI pitch.

        >>> from music21 import *
        >>> p = pitch.Pitch('c~4')
        >>> p.midi # midi values automatically round up
        61 
        >>> p.getCentShiftFromMidi()
        50
        >>> p = pitch.Pitch('c#4')
        >>> p.microtone = -25
        >>> p.getCentShiftFromMidi()
        -25

        >>> p = pitch.Pitch('c#~4')
        >>> p.getCentShiftFromMidi()
        50
        >>> p.microtone = 3
        >>> p.getCentShiftFromMidi()
        53

        >>> p = pitch.Pitch('c`4') # quarter tone flat
        >>> p.getCentShiftFromMidi()
        -50
        >>> p.microtone = 3
        >>> p.getCentShiftFromMidi()
        -47
        '''
        #return (self.ps - self.midi) * 100 # wrong way
        #return int(round(self._getAlter() * 100))

        # see if we have a quarter tone alter

        # if a quarter tone, get necessary shift above or below the 
        # standard accidental
        shift = 0
        if self.accidental is not None:
            if self.accidental.name in ['half-sharp', 'one-and-a-half-sharp']:
                shift = 50
            elif self.accidental.name in ['half-flat', 'one-and-a-half-flat']:
                shift = -50
        return int(round(shift + self.microtone.cents))

    def _getAlter(self):
        post = 0
        if self.accidental is not None:
            post += self.accidental.alter
        post += self.microtone.alter
        return post

    alter = property(_getAlter, 
        doc = '''Return the pitch alteration as a numeric value, where 1 is the space of one half step and all base pitch values are given by step alone. Thus, the alter value combines the pitch change suggested by the Accidental and the Microtone combined.

        >>> from music21 import *
        >>> p = pitch.Pitch('g#4')
        >>> p.alter
        1.0
        >>> p.microtone = -25 # in cents
        >>> p.alter
        0.75
        '''
        )


    def convertQuarterTonesToMicrotones(self, inPlace=True):
        '''Convert any quarter tone Accidentals to Microtones.

        >>> from music21 import *
        >>> p = pitch.Pitch('G#~')
        >>> p, p.microtone
        (G#~, (+0c))
        >>> p.convertQuarterTonesToMicrotones(inPlace=True)
        >>> p.ps
        68.5
        >>> p, p.microtone
        (G#(+50c), (+50c))
        
        >>> p = pitch.Pitch('A`')
        >>> p, p.microtone
        (A`, (+0c))
        >>> x = p.convertQuarterTonesToMicrotones(inPlace=False)
        >>> x, x.microtone
        (A(-50c), (-50c))
        >>> p, p.microtone
        (A`, (+0c))
        '''
        if inPlace:
            returnObj = self
        else:
            returnObj = copy.deepcopy(self)

        if returnObj.accidental is not None:
            if returnObj.accidental.name in ['half-flat']:
                returnObj.accidental = None
                returnObj.microtone = returnObj.microtone.cents - 50 # in cents
    
            elif returnObj.accidental.name in ['half-sharp']:
                returnObj.accidental = None
                returnObj.microtone = returnObj.microtone.cents + 50 # in cents
    
            elif returnObj.accidental.name in ['one-and-a-half-sharp']:
                returnObj.accidental = 1.0
                returnObj.microtone = returnObj.microtone.cents + 50 # in cents
    
            elif returnObj.accidental.name in ['one-and-a-half-flat']:
                returnObj.accidental = -1.0
                returnObj.microtone = returnObj.microtone.cents - 50 # in cents

        if inPlace:
            return None
        else:
            return returnObj



    def convertMicrotonesToQuarterTones(self, inPlace=True):
        '''Convert any Microtones available to quarter tones, if possible. 

        >>> from music21 import *
        >>> p = pitch.Pitch('g3')
        >>> p.microtone = 78
        >>> p
        G3(+78c)
        >>> p.convertMicrotonesToQuarterTones(inPlace=True)
        >>> p
        G#3(-22c)
        
        >>> p = pitch.Pitch('d#3')
        >>> p.microtone = 46
        >>> p
        D#3(+46c)
        >>> p.convertMicrotonesToQuarterTones(inPlace=True)
        >>> p
        D#~3(-4c)
        
        >>> p = pitch.Pitch('f#2')
        >>> p.microtone = -38
        >>> p.convertMicrotonesToQuarterTones(inPlace=True)
        >>> p
        F~2(+12c)

        '''
        if inPlace:
            returnObj = self
        else:
            returnObj = copy.deepcopy(self)

        value = returnObj.microtone.cents
        alterShift, cents = convertCentsToAlterAndCents(value)

        if returnObj.accidental is not None:
            returnObj.accidental = Accidental(
                            returnObj.accidental.alter + alterShift)
        else:
            returnObj.accidental = Accidental(alterShift)
        returnObj.microtone = cents        

        if inPlace:
            return None
        else:
            return returnObj




    #---------------------------------------------------------------------------

    def _getPs(self):
        if self._pitchSpaceNeedsUpdating:
            self._updatePitchSpace()
        return self._ps
    
    def _setPs(self, value):
        '''
        >>> from music21 import *
        >>> p = pitch.Pitch()
        >>> p.ps = 61
        >>> p.ps
        61.0
        >>> p.implicitAccidental
        True
        >>> p.ps = 61.5 # get a quarter tone
        >>> p
        C#~4
        >>> p.ps = 61.7 # set a microtone
        >>> p
        C#~4(+20c)
        >>> p.ps = 61.4 # set a microtone
        >>> p
        C#~4(-10c)

        '''
        # set default enharmonics to minor key names

        self._ps = float(value)
        #environLocal.printDebug(['_setPs(): self._ps', self._ps])
        self._pitchSpaceNeedsUpdating = False

        ### this should eventually change to "stepEtcNeedsUpdating"
        ### but we'll see if it's a bottleneck

        # can assign microtone here; will be either None or a Microtone object
        self.step, acc, self._microtone, octShift = convertPsToStep(value)
        # replace a natural with a None
        if acc.name == 'natural':
            self.accidental = None
        else:
            self.accidental = acc
        self.octave = convertPsToOct(value) + octShift

        # all ps settings must set implicit to True, as we do not know
        # what accidental this is
        self.implicitAccidental = True


    ps = property(_getPs, _setPs, 
        doc='''
        The ps property permits getting and setting 
        a pitch space value, a floating point number 
        representing pitch space, where 60.0 is C4, middle C, 
        61.0 is C#4 or D-4, and floating point values are 
        microtonal tunings (.01 is equal to one cent), so
        a quarter-tone sharp above C5 is 72.5.
        
        Note that the choice of 60.0 for C4 makes it identical
        to the integer value of 60 for .midi, but .midi
        does not allow for microtones and is limited to 0-127
        while .ps allows for notes before midi 0 or above midi 127.
        

        >>> from music21 import *
        >>> a = pitch.Pitch("C4")
        >>> a.ps
        60.0
        
        
        Changing the ps value for
        A will change the step and octave:
        
        
        >>> a.ps = 45
        >>> a
        A2
        >>> a.ps
        45.0

        
        Notice that ps 61 represents both
        C# and D-flat.  Thus "implicitAccidental"
        will be true after setting our pitch to 61:
        
        
        >>> a.ps = 61
        >>> a
        C#4
        >>> a.ps
        61.0
        >>> a.implicitAccidental
        True
        
        
        Microtones are allowed, as are extreme ranges:
        
        
        >>> b = pitch.Pitch('B9')
        >>> b.accidental = pitch.Accidental('half-flat')
        >>> b
        B`9
        >>> b.ps
        130.5
        
        ''')

    def _updatePitchSpace(self):
        '''
        recalculates the pitchSpace number (called when self.step, self.octave 
        or self.accidental are changed.
        '''
        self._ps = convertStepToPs(self._step, self.implicitOctave,
                                   self.accidental, self.microtone)


    def _getMidi(self):
        '''
        see docs below, under property midi
        '''
        if self._pitchSpaceNeedsUpdating:
            self._updatePitchSpace()
            self._pitchSpaceNeedsUpdating = False
        roundedPS = int(round(self.ps))
        if roundedPS > 127:
            value = (12 * 9) + (roundedPS % 12)
            if value < (127-12):
                value += 12
        elif roundedPS < 0:
            value = 0 + (roundedPS % 12)
        else:
            value = roundedPS
        return value

    def getMidiPreCentShift(self):
        '''If pitch bend will be used to adjust MIDI values, the given pitch values for microtones should go to the nearest non-microtonal pitch value, not rounded up or down. This method is used in MIDI output generation.

        >>> from music21 import *
        >>> p = pitch.Pitch('c~4')
        >>> p.getMidiPreCentShift()
        60
        >>> p = pitch.Pitch('c#4')
        >>> p.getMidiPreCentShift()
        61
        >>> p.microtone = 65
        >>> p.getMidiPreCentShift()
        61
        >>> p.getCentShiftFromMidi()
        65
        '''
        return int(((round(self.ps, 2) * 100) - self.getCentShiftFromMidi()) * .01)

    def _setMidi(self, value):
        '''
        midi values are constrained within the range of 0 to 127
        floating point values,
        '''
        value = int(round(value))
        if value > 127:
            value = (12 * 9) + (value % 12) # highest oct plus modulus
            if value < (127-12):
                value += 12
        elif value < 0:
            value = 0 + (value % 12) # lowest oct plus modulus            
        self._setPs(value)
        self._pitchSpaceNeedsUpdating = True

        # all midi settings must set implicit to True, as we do not know
        # what accidental this is
        self.implicitAccidental = True

    
    midi = property(_getMidi, _setMidi, 
        doc=''' 
        Get or set a pitch value in MIDI. 
        MIDI pitch values are like ps values (pitchSpace) rounded to 
        the nearest integer; while the ps attribute will accommodate floats.


        >>> from music21 import *
        >>> c = pitch.Pitch('C4')
        >>> c.midi
        60
        >>> c.midi =  23.5
        >>> c.midi
        24


        Note that like ps (pitchSpace), MIDI notes do not distinguish between 
        sharps and flats, etc.


        >>> dSharp = pitch.Pitch('D#4')
        >>> dSharp.midi
        63
        >>> eFlat = pitch.Pitch('E-4')
        >>> eFlat.midi
        63
        

        Midi values are constrained to the space 0-127.  Higher or lower
        values will be transposed octaves to fit in this space.


        
        >>> veryHighFHalfFlat = pitch.Pitch("F")
        >>> veryHighFHalfFlat.octave = 12
        >>> veryHighFHalfFlat.accidental = pitch.Accidental('half-flat')
        >>> veryHighFHalfFlat
        F`12
        >>> veryHighFHalfFlat.ps
        160.5
        >>> veryHighFHalfFlat.midi
        125
        
        
        >>> notAsHighNote = pitch.Pitch()
        >>> notAsHighNote.ps = veryHighFHalfFlat.midi
        >>> notAsHighNote
        F9



        Note that the conversion of improper midi values to proper
        midi values is done before assigning .ps:


        >>> a = pitch.Pitch()
        >>> a.midi = -10
        >>> a.midi
        2
        >>> a.ps
        2.0
        >>> a.implicitAccidental
        True
        ''')

    def _getName(self):
        '''Name presently returns pitch name and accidental without octave.

        >>> from music21 import *
        >>> a = pitch.Pitch('G#')
        >>> a.name
        'G#'
        '''
        if self.accidental is not None:
            return self.step + self.accidental.modifier
        else:
            return self.step
        
    def _setName(self, usrStr):
        '''
        Set name, which may be provided with or without octave values. C4 or D-3
        are both accepted.         
        '''
        usrStr = usrStr.strip().upper()
        # extract any numbers that may be octave designations
        octFound = []
        octNot = []
        for char in usrStr:
            if char in [str(x) for x in range(10)]:
                octFound.append(char)
            else:
                octNot.append(char)
        usrStr = ''.join(octNot)
        octFound = ''.join(octFound)
        # we have nothing but pitch specification
        if len(usrStr) == 1 and usrStr in STEPREF.keys():
            self._step = usrStr
            self.accidental = None
        # assume everything following pitch is accidental specification
        elif len(usrStr) > 1 and usrStr[0] in STEPREF.keys():
            self._step = usrStr[0]
            self.accidental = Accidental(usrStr[1:])
        else:
            raise PitchException("Cannot make a name out of %s" % repr(usrStr))
        if octFound != '': 
            octave = int(octFound)
            self.octave = octave

        # when setting by name, we assume that the accidental intended
        self.implicitAccidental = False

        self._pitchSpaceNeedsUpdating = True
    
    name = property(_getName, _setName, doc='''
        Gets or sets the name (pitch name with accidental but
        without octave) of the Pitch.


        >>> from music21 import *
        >>> p = pitch.Pitch()
        >>> p.name = 'C#'
        >>> p.implicitAccidental 
        False
        >>> p.ps = 61
        >>> p.implicitAccidental 
        True
        >>> p.name
        'C#'
        >>> p.ps = 58
        >>> p.name
        'B-'

        >>> p.name = 'C#'
        >>> p.implicitAccidental 
        False

    ''')


    def _getUnicodeName(self):
        '''Name presently returns pitch name and accidental without octave.

        >>> from music21 import *
        >>> a = pitch.Pitch('G#')
        >>> a.name
        'G#'
        '''
        if self.accidental is not None:
            return self.step + self.accidental.unicode
        else:
            return self.step

    unicodeName = property(_getUnicodeName, 
        doc = '''Return the pitch name in a unicode encoding. 
        ''')

    def _getNameWithOctave(self):
        '''Returns pitch name with octave
        '''
        if self.octave is None:
            return self.name
        else:
            return self.name + str(self.octave)

    def _setNameWithOctave(self, value):
        '''
        Sets pitch name and octave
        
        Test exception:
        >>> from music21 import *
        >>> a = pitch.Pitch()
        >>> a.nameWithOctave = 'C#9'
        >>> a.nameWithOctave = 'C#'
        Traceback (most recent call last):
        PitchException: Cannot set a nameWithOctave with 'C#'
        '''
        try:
            lenVal = len(value)
            name = value[0:lenVal-1]
            octave = int(value[-1])
            self.name = name
            self.octave = octave
        except:
            raise PitchException("Cannot set a nameWithOctave with '%s'" % value)
        
    nameWithOctave = property(_getNameWithOctave, 
                              _setNameWithOctave,
                              doc = '''
        Return or set the pitch name with an octave designation. 
        If no octave as been set, no octave value is returned. 
        
        >>> from music21 import *
        >>> gSharp = pitch.Pitch('G#4')
        >>> gSharp.nameWithOctave
        'G#4'

        >>> dFlatFive = pitch.Pitch()
        >>> dFlatFive.step = 'D'
        >>> dFlatFive.accidental = pitch.Accidental('flat')
        >>> dFlatFive.octave = 5
        >>> dFlatFive.nameWithOctave
        'D-5'
        >>> dFlatFive.nameWithOctave = 'C#6'
        >>> dFlatFive.name
        'C#'
        >>> dFlatFive.octave
        6


        N.B. -- it's generally better to set the name and octave separately, especially
        since you may at some point encounter very low pitches such as "A octave -1", which
        will be interpreted as "A-flat, octave 1".  Our crude setting algorithm also does
        not support octaves above 9.

        >>> lowA = pitch.Pitch()
        >>> lowA.name = 'A'
        >>> lowA.octave = -1
        >>> lowA.nameWithOctave
        'A-1'                
        >>> lowA.nameWithOctave = lowA.nameWithOctave
        >>> lowA.name
        'A-'
        >>> lowA.octave
        1
        ''')

    def _getUnicodeNameWithOctave(self):
        '''Returns pitch name with octave and unicode accidentals
        '''
        if self.octave is None:
            return self.unicodeName
        else:
            return self.unicodeName + str(self.octave)

    unicodeNameWithOctave = property(_getUnicodeNameWithOctave, 
        doc = '''Return the pitch name with octave with unicode accidental symbols, if available. 
        ''')


    def _getFullName(self):
        name = '%s' % self._step
        if self.octave is not None:
            name += '%s' % self.octave

        if self.accidental is not None:
            name += '-%s' % self.accidental._getFullName()

        if self.microtone.cents != 0:
            return name + ' ' + self._microtone.__repr__()
        else:
            return name

    fullName = property(_getFullName, 
        doc = '''
        Return the most complete representation of this Pitch, 
        providing name, octave, accidental, and any 
        microtonal adjustments. 

        >>> from music21 import *
        >>> p = pitch.Pitch('A-3')
        >>> p.microtone = 33.33
        >>> p.fullName
        'A3-flat (+33c)'
        
        >>> p = pitch.Pitch('A`7')
        >>> p.fullName
        'A7-half-flat'
        ''')


    def _getStep(self):
        '''
        >>> from music21 import *
        >>> a = pitch.Pitch('C#3')
        >>> a._getStep()
        'C'
        '''
        return self._step

    def _setStep(self, usrStr):
        '''This does not change octave or accidental, only step
        '''
        usrStr = usrStr.strip().upper()
        if len(usrStr) == 1 and usrStr in STEPNAMES:
            self._step = usrStr
        else:
            raise PitchException("Cannot make a step out of '%s'" % usrStr)
        self._pitchSpaceNeedsUpdating = True

    step = property(_getStep, _setStep,
        doc='''The diatonic name of the note; i.e. does not give the 
        accidental or octave.  Is case insensitive.


        >>> from music21 import *
        >>> a = pitch.Pitch('B-3')
        >>> a.step
        'B'
        
        >>> a.step = "c"
        >>> a.nameWithOctave
        'C-3'
        
        
        Giving a name with an accidental raises a PitchException.
        Use .name instead.
        
        >>> from music21 import *
        >>> b = pitch.Pitch('E4')
        >>> b.step = "E-"
        Traceback (most recent call last):
        PitchException: Cannot make a step out of 'E-'
        ''')


    def _getStepWithOctave(self):
        if self.octave is None:
            return self.step
        else:
            return self.step + str(self.octave)

    stepWithOctave = property(_getStepWithOctave, 
        doc = '''
        Returns the pitch step (F, G, etc) with 
        octave designation. If no octave has been set, 
        no octave value is returned. 

        >>> from music21 import *
        >>> a = pitch.Pitch('G#4')
        >>> a.stepWithOctave
        'G4'


        >>> a = pitch.Pitch('A#')
        >>> a.stepWithOctave
        'A'

        ''')


    def _getPitchClass(self):
        return int(round(self.ps % 12))

    def _setPitchClass(self, value):
        '''Set the pitchClass.

        >>> from music21 import *
        >>> a = pitch.Pitch('a3')
        >>> a.pitchClass = 3
        >>> a
        E-3
        >>> a.implicitAccidental
        True
        >>> a.pitchClass = 'A'
        >>> a
        B-3
        '''
        # permit the submission of strings, like A an dB
        value = convertPitchClassToNumber(value)
        # get step and accidental w/o octave
        self._step, self._accidental, self._microtone, octShift = convertPsToStep(value)  
        self._pitchSpaceNeedsUpdating = True

        # do not know what accidental is
        self.implicitAccidental = True

      
    pitchClass = property(_getPitchClass, _setPitchClass,
        doc='''
        Returns or sets the integer value for the pitch, 0-11, where C=0,
        C#=1, D=2...B=11. Can be set using integers (0-11) or 'A' or 'B'
        for 10 or 11.
        
        
        >>> from music21 import *
        >>> a = pitch.Pitch('a3')
        >>> a.pitchClass
        9
        >>> dis = pitch.Pitch('d3')
        >>> dis.pitchClass
        2
        >>> dis.accidental = pitch.Accidental("#")
        >>> dis.pitchClass
        3
        >>> dis.pitchClass = 11
        >>> dis.pitchClass
        11
        >>> dis.name
        'B'
        ''')


    def _getPitchClassString(self):
        '''
        >>> from music21 import *

        >>> a = pitch.Pitch('a3')
        >>> a._getPitchClassString()
        '9'
        >>> a = pitch.Pitch('a#3')
        >>> a._getPitchClassString()
        'A'
        '''
        return convertPitchClassToStr(self._getPitchClass())

    pitchClassString = property(_getPitchClassString, _setPitchClass, 
        doc = '''
        Returns or sets a string representation of the pitch class, 
        where integers greater than 10 are replaced by A and B, 
        respectively. Can be used to set pitch class by a 
        string representation as well (though this is also 
        possible with :attr:`~music21.pitch.Pitch.pitchClass`.
    
    
        >>> from music21 import *
        >>> a = pitch.Pitch('a3')
        >>> a.pitchClassString = 'B'
        >>> a.pitchClass
        11
        >>> a.pitchClassString
        'B'
        ''')

    def _getOctave(self): 
        '''
        This is _octave, not implicitOctave
        '''
        return self._octave

    def _setOctave(self,value):
        if value is not None:
            self._octave = int(value)
        else:
            self._octave = None
        self._pitchSpaceNeedsUpdating = True

    octave = property(_getOctave, _setOctave, doc='''
        Returns or sets the octave of the note.  
        Setting the octave
        updates the pitchSpace attribute.

        >>> from music21 import *

        >>> a = pitch.Pitch('g')
        >>> a.octave is None
        True
        >>> a.implicitOctave
        4
        >>> a.ps  ## will use implicitOctave
        67.0
        >>> a.name
        'G'

        >>> a.octave = 14
        >>> a.octave
        14
        >>> a.implicitOctave
        14
        >>> a.name
        'G'
        >>> a.ps
        187.0
    ''')

    def _getImplicitOctave(self):
        if self.octave is None: return self.defaultOctave
        else: return self.octave
        
    implicitOctave = property(_getImplicitOctave, doc='''
    Returns the octave of the Pitch, or defaultOctave if 
    octave was never set. To set an octave, use .octave.
    Default octave is usually 4.
    ''')


    def _getGerman(self):
        if self.accidental is not None:
            tempAlter = self.accidental.alter
        else:
            tempAlter = 0
        tempStep = self.step
        if tempAlter != int(tempAlter):
            raise PitchException('Es geht nicht "german" zu benutzen mit Microtoenen.  Schade!')
        else:
            tempAlter = int(tempAlter)
        if tempStep == 'B':
            if tempAlter != -1:
                tempStep = 'H'
            else:
                tempAlter += 1
        if tempAlter == 0:
            return tempStep
        elif tempAlter > 0:
            tempName = tempStep + (tempAlter * 'is')
            return tempName
        else: # flats
            if tempStep in ['C','D','F','G','H']:
                firstFlatName = 'es'
            else: # A, E.  Bs should never occur...
                firstFlatName = 's'
            multipleFlats = abs(tempAlter) - 1
            tempName =  tempStep + firstFlatName + (multipleFlats * 'es')
            return tempName
    
    german = property(_getGerman, 
        doc ='''
        Read-only attribute. Returns the name 
        of a Pitch in the German system 
        (where B-flat = B, B = H, etc.)
        (Microtones and Quartertones raise an error).  Note that 
        Ases is used instead of the also acceptable Asas.
        
        
        >>> from music21 import *
        >>> print pitch.Pitch('B-').german
        B
        >>> print pitch.Pitch('B').german
        H
        >>> print pitch.Pitch('E-').german
        Es
        >>> print pitch.Pitch('C#').german
        Cis
        >>> print pitch.Pitch('A--').german
        Ases
        >>> p1 = pitch.Pitch('C')
        >>> p1.accidental = pitch.Accidental('half-sharp')
        >>> p1.german
        Traceback (most recent call last):
        PitchException: Es geht nicht "german" zu benutzen mit Microtoenen.  Schade!
    
        
        Note these rarely used pitches:
        
        
        >>> print pitch.Pitch('B--').german
        Heses
        >>> print pitch.Pitch('B#').german
        His
    ''')
    
    def _getDutch(self):
        if self.accidental is not None:
            tempAlter = self.accidental.alter
        else:
            tempAlter = 0
        tempStep = self.step
        if tempAlter != int(tempAlter):
            raise PitchException('Quarter-tones not supported')
        else:
            tempAlter = int(tempAlter)
        if tempAlter == 0:
            return tempStep
        if tempAlter > 0:
            return tempStep + (tempAlter * 'is')
        else:
            if tempStep in ['C','D','F','G','B']:
                firstFlatName = 'es'
            else:
                firstFlatName = 's'
            multipleFlats = abs(tempAlter) - 1
            return tempStep + firstFlatName + (multipleFlats * 'es')
        
    dutch = property(_getDutch,
                      doc ='''
        Read-only attribute. Returns the name 
        of a Pitch in the German system 
        (where B-flat = B, B = H, etc.)
        (Microtones and Quartertones raise an error).
        
        
        >>> from music21 import *
        >>> print pitch.Pitch('B-').dutch
        Bes
        >>> print pitch.Pitch('B').dutch
        B
        >>> print pitch.Pitch('E-').dutch
        Es
        >>> print pitch.Pitch('C#').dutch
        Cis
        >>> print pitch.Pitch('A--').dutch
        Ases
        >>> p1 = pitch.Pitch('C')
        >>> p1.accidental = pitch.Accidental('half-sharp')
        >>> p1.dutch
        Traceback (most recent call last):
        PitchException: Quarter-tones not supported
    ''')
        
    
    def _getItalian(self):
        if self.accidental is not None:
            tempAlter = self.accidental.alter
        else:
            tempAlter = 0
        tempStep = self.step
        if tempAlter != int(tempAlter):
            raise PitchException('Incompatible with quarter-tones')
        else:
            tempAlter = int(tempAlter)
            
        cardinalityMap = {1: " ", 2: " doppio ", 3: " triplo ", 4: " quadruplo "}
        solfeggeMap = {"C": "do", "D": "re", "E": "mi", "F": "fa", "G": "sol", "A": "la", "B": "si"}
        
        if tempAlter == 0:
            return solfeggeMap[tempStep]
        elif tempAlter > 0:
            if tempAlter > 4:
                raise PitchException('Entirely too many sharps')
            return solfeggeMap[tempStep] + cardinalityMap[tempAlter] + "diesis"
        else: # flats
            tempAlter = tempAlter*-1
            if tempAlter > 4:
                raise PitchException('Entirely too many flats')
            return solfeggeMap[tempStep] + cardinalityMap[tempAlter] + "bemolle"
    
    italian = property(_getItalian, 
        doc ='''
        Read-only attribute. Returns the name 
        of a Pitch in the Italian system 
        (F-sharp is fa diesis, C-flat is do bemolle, etc.)
        (Microtones and Quartertones raise an error).  
        
        
        >>> from music21 import *
        >>> print pitch.Pitch('B-').italian
        si bemolle
        >>> print pitch.Pitch('B').italian
        si
        >>> print pitch.Pitch('E-9').italian
        mi bemolle
        >>> print pitch.Pitch('C#').italian
        do diesis
        >>> print pitch.Pitch('A--4').italian
        la doppio bemolle
        >>> p1 = pitch.Pitch('C')
        >>> p1.accidental = pitch.Accidental('half-sharp')
        >>> p1.italian
        Traceback (most recent call last):
        PitchException: Incompatible with quarter-tones
    
        
        Note these rarely used pitches:
        
        
        >>> print pitch.Pitch('E####').italian
        mi quadruplo diesis
        >>> print pitch.Pitch('D---').italian
        re triplo bemolle
    ''')
    

        
    
    def _getSpanish(self):
        if self.accidental is not None:
            tempAlter = self.accidental.alter
        else:
            tempAlter = 0
        tempStep = self.step
        solfege = _getSpanishSolfege(tempStep)
        if tempAlter != int(tempAlter):
            raise PitchException('Unsupported accidental type.')
        else:
            if tempAlter == 0:
                return solfege
            elif abs(tempAlter) > 4:
                raise PitchException('Unsupported accidental type.')
            elif tempAlter in [-4,-3,-2,-1]:
                return solfege + _getSpanishCardinal(abs(tempAlter)) + ' bèmol'
            elif tempAlter in [1,2,3,4]:
                return solfege + _getSpanishCardinal(abs(tempAlter)) + ' sostenido'
    
    spanish = property(_getSpanish, 
        doc ='''
        Read-only attribute. Returns the name 
        of a Pitch in Spanish
        (Microtones and Quartertones raise an error).
        
        
        >>> from music21 import *
        >>> print pitch.Pitch('B-').spanish
        si bèmol
        >>> print pitch.Pitch('E-').spanish
        mi bèmol
        >>> print pitch.Pitch('C#').spanish
        do sostenido
        >>> print pitch.Pitch('A--').spanish
        la doble bèmol
        >>> p1 = pitch.Pitch('C')
        >>> p1.accidental = pitch.Accidental('half-sharp')
        >>> p1.spanish
        Traceback (most recent call last):
        PitchException: Unsupported accidental type.
    
        
        Note these rarely used pitches:
        
        
        >>> print pitch.Pitch('B--').spanish
        si doble bèmol
        >>> print pitch.Pitch('B#').spanish
        si sostenido
    ''')
    

    def _getFrench(self):
        if self.accidental is not None:
            tempAlter = self.accidental.alter
        else:
            tempAlter = 0
        tempStep = self.step
        if tempAlter != int(tempAlter):
            raise PitchException('On ne peut pas utiliser les microtones avec "french." Quelle Dommage!')
        elif abs(tempAlter) > 4.0:
            raise PitchException('On ne peut pas utiliser les altération avec puissance supérieure à quatre avec "french." Ça me fait une belle jambe!')
        else:
            tempAlter = int(tempAlter)
        if tempStep == 'A':
            tempStep = 'la'
        if tempStep == 'B':
            tempStep = 'si'
        if tempStep == 'C':
            tempStep = 'do'
        if tempStep == 'D':
            tempStep = 'ré'
        if tempStep == 'E':
            tempStep = 'mi'
        if tempStep == 'F':
            tempStep = 'fa'
        if tempStep == 'G':
            tempStep = 'sol'
        
        if tempAlter == 0:
            return tempStep
        elif abs(tempAlter) == 1.0:
            tempNumberedStep = tempStep
        elif abs(tempAlter) == 2.0:
            tempNumberedStep = tempStep + ' double'
        elif abs(tempAlter) == 3.0:
            tempNumberedStep = tempStep + ' triple'
        elif abs(tempAlter) == 4.0:  
            tempNumberedStep = tempStep + ' quadruple'
        
        if tempAlter/abs(tempAlter) == 1.0: #sharps are positive
            tempName = tempNumberedStep + ' dièse'
            return tempName
        else: # flats are negative
            tempName = tempNumberedStep + ' bémol'
            return tempName
        
    
    french = property(_getFrench, 
        doc ='''
        Read-only attribute. Returns the name 
        of a Pitch in the French system 
        (where A = la, B = si, B-flat = si bémol, C-sharp = do dièse, etc.)
        (Microtones and Quartertones raise an error).  Note that 
        do is used instead of the also acceptable ut.
        
        
        >>> from music21 import *
        >>> print pitch.Pitch('B-').french
        si bémol
        >>> print pitch.Pitch('B').french
        si
        >>> print pitch.Pitch('E-').french
        mi bémol
        >>> print pitch.Pitch('C#').french
        do dièse
        >>> print pitch.Pitch('A--').french
        la double bémol
        >>> p1 = pitch.Pitch('C')
        >>> p1.accidental = pitch.Accidental('half-sharp')
        >>> p1.french
        Traceback (most recent call last):
        PitchException: On ne peut pas utiliser les microtones avec "french." Quelle Dommage!
    ''')

    def _getFrequency(self):        
        return self._getfreq440()

    def _setFrequency(self, value):     
        #environLocal.printDebug(['_setFrequency(): calling'])
        # store existing octave
    
        # setting the .ps property sets step, accidental, microtone
        # and octave, and implicitAccidental
        self.ps = convertFqToPs(value)

        #environLocal.printDebug(['_setFrequency(), post convertFqToPs()', 'value', value, 'self', self, 'self.ps', self.ps])


    frequency = property(_getFrequency, _setFrequency, doc='''
        The frequency property gets or sets the frequency of
        the pitch in hertz.  
        If the frequency has not been overridden, then
        it is computed based on A440Hz and equal temperament

        >>> from music21 import *
        >>> a = pitch.Pitch()
        >>> a.frequency = 440.0
        >>> a.frequency
        440.0
        >>> a.name
        'A'
        >>> a.octave
        4
        >>> a.frequency = 450.0 # microtones are captured
        >>> a
        A~4(-11c)

    ''')


    # these methods may belong in in a temperament object
    # name of method and property could be more clear
    def _getfreq440(self):
        '''
        >>> from music21 import *
        >>> a = pitch.Pitch('A4')
        >>> a.freq440
        440.0
        '''
        if self._overridden_freq440:
            return self._overridden_freq440
        else:
            # works off of .ps values and thus will capture microtones
            A4offset = self.ps - 69
            return 440.0 * (self._twelfth_root_of_two ** A4offset)
            
    def _setfreq440(self, value):
        self._overridden_freq440 = value

    freq440 = property(_getfreq440, _setfreq440, doc='''
    Gets the frequency of the note as if it's in an equal temperment
    context where A4 = 440hz.  The same as .frequency so long
    as no other temperments are currently being used.
    
    
    Since we don't have any other temperament objects as
    of alpha 7, this is the same as .frequency always.
    
    ''')


    def _getMX(self):
        return musicxmlTranslate.pitchToMx(self)

    def _setMX(self, mxNote):
        return musicxmlTranslate.mxToPitch(mxNote, self)

    mx = property(_getMX, _setMX)



    def _getMusicXML(self):
        '''Provide a complete MusicXML representation. Presently, this is based on 
        '''
        return musicxmlTranslate.pitchToMusicXML(self)

    musicxml = property(_getMusicXML)



    #---------------------------------------------------------------------------
    def getHarmonic(self, number):
        '''Return a Pitch object representing the harmonic found above this Pitch.

        >>> from music21 import *
        >>> p = pitch.Pitch('a4')
        >>> p.getHarmonic(2)
        A5
        >>> p.getHarmonic(3)
        E6(+2c)
        >>> p.getHarmonic(4)
        A6
        >>> p.getHarmonic(5)
        C#7(-14c)
        >>> p.getHarmonic(6)
        E7(+2c)
        >>> p.getHarmonic(7)
        F#~7(+19c)
        >>> p.getHarmonic(8)
        A7
        

        >>> p2 = p.getHarmonic(2)
        >>> p2
        A5
        >>> p2.fundamental
        A4
        >>> p2.transpose('p5', inPlace=True)
        >>> p2
        E6
        >>> p2.fundamental
        E5

        
        Or we can iterate over a list of the next 8 odd harmonics:
        
        
        >>> for i in [9,11,13,15,17,19,21,23]:
        ...     print p.getHarmonic(i),
        B7(+4c) D~8(+1c) F~8(-9c) G#8(-12c) B-8(+5c) C9(-2c) C#~9(+21c) E`9(-22c)


        Microtonally adjusted notes also generate harmonics:
        
        
        >>> q = pitch.Pitch('C4')
        >>> q.microtone = 10
        >>> q.getHarmonic(2)
        C5(+10c)
        >>> q.getHarmonic(3)
        G5(+12c)
        
        
        The fundamental is stored with the harmonic. 


        >>> h7 = pitch.Pitch("A4").getHarmonic(7)
        >>> h7
        F#~7(+19c)
        >>> h7.fundamental
        A4
        >>> h7.harmonicString()
        '7thH/A4'
        >>> h7.harmonicString('A3')
        '14thH/A3'

        
        >>> h2 = h7.getHarmonic(2)
        >>> h2
        F#~8(+19c)
        >>> h2.fundamental
        F#~7(+19c)
        >>> h2.fundamental.fundamental
        A4
        >>> h2.transpose(-24, inPlace=True)
        >>> h2
        F#~6(+19c)
        >>> h2.fundamental.fundamental
        A2
        
        '''
        centShift = convertHarmonicToCents(number)
        temp = copy.deepcopy(self)
        # if no change, just return what we start with
        if centShift == 0:
            return temp
        # add this pitch's microtones plus the necessary cent shift
        if temp.microtone is not None:
            temp.microtone = temp.microtone.cents + centShift
        else:
            temp.microtone = centShift    

        #environLocal.printDebug(['getHarmonic()', 'self', self, 'self.frequency', self.frequency, 'centShift', centShift, 'temp', temp, 'temp.frequency', temp.frequency, 'temp.microtone', temp.microtone])

        # possibly optimize this to use only two Pitch objects
        final = Pitch()
        # set with this frequency
        final.frequency = temp.frequency
        # store a copy as the fundamental
        final.fundamental = copy.deepcopy(self)

        #environLocal.printDebug(['getHarmonic()', 'final', final, 'final.frequency', final.frequency])
        return final


    def harmonicFromFundamental(self, fundamental):
        '''
        Given another Pitch as a fundamental, find the harmonic 
        of that pitch that is equal to this Pitch. 


        Returns a tuple of harmonic number and the number of cents that
        the first Pitch object would have to be shifted to be the exact
        harmonic of this fundamental. 


        Microtones applied to the fundamental are irrelevant, 
        as the fundamental may be microtonally shifted to find a match to this Pitch.         


        Example: G4 is the third harmonic of C3, albeit 2 cents flatter than
        the true 3rd harmonic.
        

        >>> from music21 import *
        >>> p = pitch.Pitch('g4')
        >>> f = pitch.Pitch('c3')
        >>> p.harmonicFromFundamental(f)
        (3, 2.0)
        >>> p.microtone = p.harmonicFromFundamental(f)[1] # adjust microtone
        >>> int(f.getHarmonic(3).frequency) == int(p.frequency)
        True


        
        The shift from B-5 to the 7th harmonic of C3 is more substantial
        and likely to be noticed by the audience.  To make p the 7th harmonic
        it'd have to be lowered by 31 cents.  Note that the
        second argument is a float, but because the default rounding of
        music21 is to the nearest cent, the .0 is not a significant digit.
        I.e. it might be more like 31.3 cents.
        

        >>> p = pitch.Pitch('B-5')
        >>> f = pitch.Pitch('C3')
        >>> p.harmonicFromFundamental(f)
        (7, -31.0)
        
        '''
        
        if common.isStr(fundamental):
            fundamental = Pitch(fundamental)
        # else assume a Pitch object
        # got through all harmonics and find the one closes to this ps value
        target = self

        if target.ps <= fundamental.ps:
            raise PitchException('cannot find an equivalent harmonic for a fundamental (%s) that is not above this Pitch (%s)' % (fundamental, self))

        # up to the 32 harmonic
        found = [] # store a list
        for i in range(1, 32):
            # gather all until we are above the target
            p = fundamental.getHarmonic(i)
            found.append((i, p))
            if p.ps > target.ps:
                break

        #environLocal.printDebug(['harmonicFromFundamental():', 'fundamental', fundamental, 'found', found])

        # it is either the last or the second to last
        if len(found) < 2: # only 1
            harmonicMatch, match = found[0]
            if match.ps > target.ps:
                gap = match.ps - target.ps
            elif match.ps < target.ps:
                gap = target.ps - match.ps
            else:
                gap = 0
        else:
            harmonicLower, candidateLower = found[-2]
            harmonicHigher, candidateHigher = found[-1]

            distanceLower = target.ps - candidateLower.ps
            distanceHigher = candidateHigher.ps - target.ps

            #environLocal.printDebug(['harmonicFromFundamental():', 'distanceLower', distanceLower, 'distanceHigher', distanceHigher, 'target', target])

            if distanceLower <= distanceHigher:
                #environLocal.printDebug(['harmonicFromFundamental():', 'distanceLower (%s); distanceHigher (%s); distance lower is closer to target: %s'  % (candidateLower, candidateHigher, target)])

                # the lower is closer, thus we need to raise gap
                match = candidateLower
                gap = -abs(distanceLower)
                harmonicMatch = harmonicLower
            else:
                # the higher is closer, thus we need to lower the gap
                #environLocal.printDebug(['harmonicFromFundamental():', 'distanceLower (%s); distanceHigher (%s); distance higher is closer to target: %s'  % (candidateLower, candidateHigher, target)])

                match = candidateHigher
                gap = abs(distanceHigher)
                harmonicMatch = harmonicHigher

        gap = round(gap, PITCH_SPACE_SIG_DIGITS) * 100

        return harmonicMatch, gap

        #environLocal.printDebug(['harmonicFromFundamental():', 'match', match, 'gap', gap, 'harmonicMatch', harmonicMatch])

        # need to found gap, otherwise may get very small values
#         gap = round(gap, PITCH_SPACE_SIG_DIGITS)
#         # create a pitch with the appropriate gap as a Microtone
#         if fundamental.microtone is not None:
#             # if the result is zero, .microtone will automatically 
#             # be set to None
#             fundamental.microtone = fundamental.microtone.cents + (gap * 100)
#         else:
#             if gap != 0:
#                 fundamental.microtone = gap * 100
#         return harmonicMatch, fundamental



    def harmonicString(self, fundamental=None):
        '''
        Return a string representation of a harmonic equivalence. 


        N.B. this has nothing to do with what string a string player
        would use to play the harmonic on.  (Perhaps should be 
        renamed).
        


        >>> from music21 import *
        >>> pitch.Pitch('g4').harmonicString('c3')
        '3rdH(-2c)/C3'
        
        
        >>> pitch.Pitch('c4').harmonicString('c3')
        '2ndH/C3'
        
        
        >>> p = pitch.Pitch('c4')
        >>> p.microtone = 20 # raise 20 
        >>> p.harmonicString('c3')
        '2ndH(+20c)/C3'
        
        
        >>> p.microtone = -20 # lower 20 
        >>> p.harmonicString('c3')
        '2ndH(-20c)/C3'
        
        
        >>> p = pitch.Pitch('c4')
        >>> f = pitch.Pitch('c3')
        >>> f.microtone = -20
        >>> p.harmonicString(f)
        '2ndH(+20c)/C3(-20c)'
        >>> f.microtone = +20
        >>> p.harmonicString(f)
        '2ndH(-20c)/C3(+20c)'
        
        
        >>> p = pitch.Pitch('A4')
        >>> p.microtone = 69
        >>> p.harmonicString('c2')
        '7thH/C2'
        
        
        >>> p = pitch.Pitch('A4')
        >>> p.harmonicString('c2')
        '7thH(-69c)/C2'
        '''
        if fundamental is None:
            if self.fundamental is None:
                raise PitchException('no fundamental is defined for this Pitch: provide one as an arugment')
            else:
                fundamental = self.fundamental
        if common.isStr(fundamental):
            fundamental = Pitch(fundamental)

        harmonic, cents = self.harmonicFromFundamental(fundamental)
        # need to invert cent shift, as we are suggesting a shifted harmonic
        microtone = Microtone(-cents)
        if cents == 0:
            return '%s%sH/%s' % (harmonic, common.ordinalAbbreviation(harmonic), fundamental)
        else:
            return '%s%sH%s/%s' % (harmonic, common.ordinalAbbreviation(harmonic), 
                            microtone, fundamental)




    def harmonicAndFundamentalFromPitch(self, target):
        '''Given a Pitch that is a plausible target for a fundamental, return the harmonic number and a potentially shifted fundamental that describes this Pitch.

        >>> from music21 import *
        >>> pitch.Pitch('g4').harmonicAndFundamentalFromPitch('c3')
        (3, C3(-2c))

        '''
        if common.isStr(target):
            target = Pitch(target)
        else: # make a copy
            target = copy.deepcopy(target) 

        harmonic, cents = self.harmonicFromFundamental(target)
        # flip direction
        cents = -cents

        # create a pitch with the appropriate gap as a Microtone
        if target.microtone is not None:
            # if the result is zero, .microtone will automatically 
            # be set to None
            target.microtone = target.microtone.cents + cents
        else:
            if cents != 0:
                target.microtone = cents
        return harmonic, target



    def harmonicAndFundamentalStringFromPitch(self, fundamental):
        '''Given a Pitch that is a plausible target for a fundamental, return the harmonic number and a potentially shifted fundamental that describes this Pitch. Return a string representation.

        >>> from music21 import *
        >>> pitch.Pitch('g4').harmonicAndFundamentalStringFromPitch('c3')
        '3rdH/C3(-2c)'
        
        >>> pitch.Pitch('c4').harmonicAndFundamentalStringFromPitch('c3')
        '2ndH/C3'
        
        >>> p = pitch.Pitch('c4')
        >>> p.microtone = 20 # raise 20 
        >>> p.harmonicAndFundamentalStringFromPitch('c3')
        '2ndH/C3(+20c)'
        
        >>> p.microtone = -20 # lower 20 
        >>> p.harmonicAndFundamentalStringFromPitch('c3')
        '2ndH/C3(-20c)'
        
        >>> p = pitch.Pitch('c4')
        >>> f = pitch.Pitch('c3')
        >>> f.microtone = -20
        >>> p.harmonicAndFundamentalStringFromPitch(f)
        '2ndH/C3'
        >>> f.microtone = +20
        >>> p.harmonicAndFundamentalStringFromPitch(f)
        '2ndH/C3'
        
        >>> p = pitch.Pitch('A4')
        >>> p.microtone = 69
        >>> p.harmonicAndFundamentalStringFromPitch('c2')
        '7thH/C2'
        
        >>> p = pitch.Pitch('A4')
        >>> p.harmonicAndFundamentalStringFromPitch('c2')
        '7thH/C2(-69c)'

        '''
        harmonic, fundamental = self.harmonicAndFundamentalFromPitch(
            fundamental)
        return '%s%sH/%s' % (harmonic, common.ordinalAbbreviation(harmonic), 
                            fundamental)




    #---------------------------------------------------------------------------
    def isEnharmonic(self, other):
        '''Return True if other is an enharmonic equivalent of self. 

        >>> from music21 import *
        >>> p1 = pitch.Pitch('C#3')
        >>> p2 = pitch.Pitch('D-3')
        >>> p3 = pitch.Pitch('D#3')
        >>> p1.isEnharmonic(p2)
        True
        >>> p2.isEnharmonic(p1)
        True
        >>> p3.isEnharmonic(p1)
        False
        
        OMIT_FROM_DOCS
        >>> p4 = pitch.Pitch('B##3')
        >>> p5 = pitch.Pitch('D-4')
        >>> p4.isEnharmonic(p5)
        True
        '''
        # if pitch space are equal, these are enharmonics
        if other.ps == self.ps:
            return True
        return False

    def getHigherEnharmonic(self, inPlace=False):
        '''Returns a Pitch enharmonic note that a dim-second above the current note.

        >>> from music21 import *
        >>> p1 = pitch.Pitch('C#3')
        >>> p2 = p1.getHigherEnharmonic()
        >>> p2
        D-3

        >>> p1 = pitch.Pitch('C#3')
        >>> p1.getHigherEnharmonic(inPlace=True)
        >>> p1
        D-3
        
        
        
        The method even works for certain CRAZY enharmonics
        
        
        >>> p3 = pitch.Pitch('D--3')
        >>> p4 = p3.getHigherEnharmonic()
        >>> p4
        E----3
        
        
        But not for things that are just utterly insane:
        
        
        >>> p4.getHigherEnharmonic()
        Traceback (most recent call last):
        AccidentalException: -5 is not a supported accidental type
        
        '''
        intervalObj = interval.Interval('d2')
        octaveStored = self.octave # may be None
        if not inPlace:
            post = intervalObj.transposePitch(self, maxAccidental=None)
            if octaveStored is None:
                post.octave = None
            return post
        else:
            p = intervalObj.transposePitch(self, maxAccidental=None)
            self._setName(p.nameWithOctave)
            self.accidental = p.accidental
            if octaveStored is None:
                self.octave = None
            return None
    
    def getLowerEnharmonic(self, inPlace=False):
        '''
        returns a Pitch enharmonic note that is a diminished second 
        below the current note
        
        If `inPlace` is set to true, changes the current Pitch.
        
        
        >>> from music21 import *
        >>> p1 = pitch.Pitch('C-3')
        >>> p2 = p1.getLowerEnharmonic()
        >>> p2
        B2

        >>> p1 = pitch.Pitch('C#3')
        >>> p1.getLowerEnharmonic(inPlace=True)
        >>> p1
        B##2
        '''
        intervalObj = interval.Interval('-d2')
        octaveStored = self.octave # may be None
        if not inPlace:
            post = intervalObj.transposePitch(self)
            if octaveStored is None:
                post.octave = None
            return post
        else:
            p = intervalObj.transposePitch(self)
            self._setName(p.nameWithOctave)
            self.accidental = p.accidental
            if octaveStored is None:
                self.octave = None
            return None

    def simplifyEnharmonic(self, inPlace=False, mostCommon=False):
        '''
        Returns a new Pitch (or sets the current one if inPlace is True)
        that is either the same as the current pitch or has fewer
        sharps or flats if possible.  For instance, E# returns F,
        while A# remains A# (i.e., does not take into account that B- is
        more common than A#).  Useful to call if you ever have an
        algorithm that might take your piece far into the realm of
        double or triple flats or sharps.
        
        
        If mostCommon is set to true, then the most commonly used 
        enharmonic spelling is chosen (that is, the one that appears
        first in key signatures as you move away from C on the circle
        of fifths).  Thus G-flat becomes F#, A# becomes B-flat,
        D# becomes E-flat, D-flat becomes C#, G# and A-flat are left
        alone.
        
        
        TODO: should be called automatically after ChromaticInterval
        transpositions.
        
        
        >>> from music21 import *
        >>> p1 = pitch.Pitch("B#5")
        >>> p1.simplifyEnharmonic().nameWithOctave
        'C6'
        
        >>> p2 = pitch.Pitch("A#2")
        >>> p2.simplifyEnharmonic(inPlace = True)
        >>> p2
        A#2
        
        >>> p3 = pitch.Pitch("E--3")
        >>> p4 = p3.transpose(interval.Interval('-A5'))
        >>> p4.simplifyEnharmonic()
        F#2


        Setting mostCommon = True simplifies enharmonics
        even further.


        >>> pList = [pitch.Pitch("A#4"), pitch.Pitch("B-4"), pitch.Pitch("G-4"), pitch.Pitch("F#4")]
        >>> [p.simplifyEnharmonic(mostCommon = True) for p in pList]
        [B-4, B-4, F#4, F#4]




        
        Note that pitches with implicit octaves retain their implicit octaves.
        This might change the pitch space for B#s and C-s.


        >>> pList = [pitch.Pitch("B"), pitch.Pitch("C#"), pitch.Pitch("G"), pitch.Pitch("A--")]
        >>> [p.simplifyEnharmonic() for p in pList]
        [B, C#, G, G]


        >>> pList = [pitch.Pitch("C-"), pitch.Pitch("B#")]
        >>> [p.ps for p in pList]
        [59.0, 72.0]
        >>> [p.simplifyEnharmonic().ps for p in pList]
        [71.0, 60.0]

        '''

        if inPlace:
            returnObj = self
        else:
            returnObj = copy.deepcopy(self)

        if returnObj.accidental != None:
            if abs(returnObj.accidental.alter) < 2.0 and \
                returnObj.name not in ('E#', 'B#', 'C-', 'F-'):
                pass
            else:
                # by reseting the pitch space value, we will get a simplyer
                # enharmonic spelling
                saveOctave = self.octave
                returnObj.ps = self.ps
                if saveOctave is None:
                    returnObj.octave = None

        if mostCommon == True:
            if returnObj.name == 'D#':
                returnObj.step = 'E'
                returnObj.accidental = Accidental('flat')
            elif returnObj.name == 'A#':
                returnObj.step = 'B'
                returnObj.accidental = Accidental('flat')
            elif returnObj.name == 'G-':
                returnObj.step = 'F'
                returnObj.accidental = Accidental('sharp')
            elif returnObj.name == 'D-':
                returnObj.step = 'C'
                returnObj.accidental = Accidental('sharp')
        
        
        if inPlace:
            return None
        else:
            return returnObj


    def getEnharmonic(self, inPlace=False):
        '''
        Returns a new Pitch that is the(/an) enharmonic equivalent of this Pitch.
    
    
        N.B.: n1.name == getEnharmonic(getEnharmonic(n1)).name is not necessarily true.
        For instance: 
        
            getEnharmonic(E##) => F#; getEnharmonic(F#) => G-
            
            getEnharmonic(A--) => G; getEnharmonic(G) => F##


        However, for all cases not involving double sharps or flats 
        (and even many that do), getEnharmonic(getEnharmonic(n)) = n
    
    
        For the most ambiguous cases, it's good to know that these are the enharmonics:
        
               C <-> B#, D <-> C##, E <-> F-; F <-> E#, G <-> F##, A <-> B--, B <-> C-
    
    
        However, isEnharmonic() for A## and B certainly returns true.
    

        >>> from music21 import *
        >>> p = pitch.Pitch('d#')
        >>> p.getEnharmonic()
        E-
        >>> p = pitch.Pitch('e-8')
        >>> p.getEnharmonic()
        D#8
        
        
        Other tests:
        
        
        >>> pitch.Pitch('c-3').getEnharmonic()
        B2
        >>> pitch.Pitch('e#2').getEnharmonic()
        F2
        >>> pitch.Pitch('f#2').getEnharmonic()
        G-2
        >>> pitch.Pitch('c##5').getEnharmonic()
        D5
        >>> pitch.Pitch('g3').getEnharmonic() 
        F##3
        >>> pitch.Pitch('B7').getEnharmonic()
        C-8


        Octaveless Pitches remain octaveless:
        

        >>> p = pitch.Pitch('a-')
        >>> p.getEnharmonic()
        G#
        >>> p = pitch.Pitch('B#')
        >>> p.getEnharmonic()
        C

        '''
        psRef = self.ps
        if inPlace:
            post = self
        else:
            post = copy.deepcopy(self)

        if post.accidental != None:
            if post.accidental.alter > 0:
                # we have a sharp, need to get the equivalent flat
                post.getHigherEnharmonic(inPlace=True)
            elif post.accidental.alter < 0:
                post.getLowerEnharmonic(inPlace=True)
            else: # assume some direction, perhaps using a dictionary
                if self.step in ['C','D','G']:               
                    post.getLowerEnharmonic(inPlace=True)
                else:
                    post.getHigherEnharmonic(inPlace=True)

        else:
            if self.step in ['C','D','G']:               
                post.getLowerEnharmonic(inPlace=True)
            else:
                post.getHigherEnharmonic(inPlace=True)

        
        if inPlace:
            return None
        else:
            return post
        

# not sure these are necessary
# def getQuarterToneEnharmonic(note1):
#     '''like getEnharmonic but handles quarterTones as well'''
#     pass
# 
# def flipQuarterToneEnharmonic(note1):
#     pass
# 
# def areQuarterToneEnharmonics(note1, note2):
#     pass


#         OMIT_FROM_DOCS
#         Perhaps a getFirstNEnharmonics(n) needs to be defined which returns a list of the
#         first n Enharmonics according to a particular algorithm, moving into triple sharps, etc.
#         if need be.  Or getAllCommonEnharmonics(note) which returns all possible enharmonics that
#         do not involve triple or more accidentals.
# 
    def getAllCommmonEnharmonics(self, alterLimit=2):
        '''Return all common unique enharmonics for a pitch, or those that do not involve more than two accidentals.

        >>> from music21 import *
        >>> p = pitch.Pitch('c#3')
        >>> p.getAllCommmonEnharmonics()
        [D-3, B##2]
        >>> p = pitch.Pitch('g-6')
        >>> p.getAllCommmonEnharmonics()
        [F#6, E##6]
        >>> p.getAllCommmonEnharmonics(alterLimit=3)
        [A---6, F#6, E##6]
        '''
        post = []
        c = self.simplifyEnharmonic(inPlace=False)
        if c.name != self.name:
            post.append(c)
        # iterative scan upward
        c = self
        while True:
            try:
                c = c.getHigherEnharmonic(inPlace=False)
            except AccidentalException:
                break # ran out of accidentals
            if c.accidental is not None:
                if abs(c.accidental.alter) > alterLimit:
                    break
            if c not in post:
                post.append(c)
            else: # we are looping
                break
        # iterative scan downward
        c = self
        while True:
            try:
                c = c.getLowerEnharmonic(inPlace=False)
            except AccidentalException:
                break # ran out of accidentals
            if c.accidental is not None:
                if abs(c.accidental.alter) > alterLimit:
                    break
            if c not in post:
                post.append(c)
            else: # we are looping
                break
        return post


    #---------------------------------------------------------------------------
    def _getDiatonicNoteNum(self):
        '''
        Returns (or takes) an integer that uniquely identifies the 
        diatonic version of a note, that is ignoring accidentals.
        The number returned is the diatonic interval above C0 (the lowest C on
        a Boesendorfer Imperial Grand), so G0 = 5, C1 = 8, etc.
        Numbers can be negative for very low notes.        
        
        C4 (middleC) = 29, C#4 = 29, C##4 = 29, D-4 = 30, D4 = 30, etc.
        
        >>> from music21 import *
        >>> c = pitch.Pitch('c4')
        >>> c.diatonicNoteNum
        29
        >>> c = pitch.Pitch('c#4')
        >>> c.diatonicNoteNum
        29
        >>> d = pitch.Pitch('d--4')
        >>> d.accidental.name
        'double-flat'
        >>> d.diatonicNoteNum
        30
        >>> lowc = pitch.Pitch('c1')
        >>> lowc.diatonicNoteNum
        8

        >>> b = pitch.Pitch()
        >>> b.step = "B"
        >>> b.octave = -1 
        >>> b.diatonicNoteNum
        0
        >>> c = pitch.Pitch("C")
        >>> c.diatonicNoteNum  #implicitOctave
        29

        >>> lowDSharp = pitch.Pitch("C#7") # start high !!!
        >>> lowDSharp.diatonicNoteNum = 9  # move low
        >>> lowDSharp.octave
        1
        >>> lowDSharp.name
        'D#'

        OMIT_FROM_DOCS
        
        >>> lowlowA = pitch.Pitch("A")
        >>> lowlowA.octave = -1
        >>> lowlowA.diatonicNoteNum
        -1
        
        >>> lowlowlowD = pitch.Pitch("D")
        >>> lowlowlowD.octave = -3
        >>> lowlowlowD.diatonicNoteNum
        -19
        
        '''
        if ['C','D','E','F','G','A','B'].count(self.step.upper()):
            noteNumber = ['C','D','E','F','G','A','B'].index(self.step.upper())
            return (noteNumber + 1 + (7 * self.implicitOctave))
        else:
            raise PitchException("Could not find " + self.step + " in the index of notes") 

    def _setDiatonicNoteNum(self, newNum):
        octave = int((newNum-1)/7)
        noteNameNum = newNum - 1 - (7*octave)
        pitchList = ['C','D','E','F','G','A','B']
        noteName = pitchList[noteNameNum]
        self.octave = octave
        self.step = noteName
        return self

    diatonicNoteNum = property(_getDiatonicNoteNum, _setDiatonicNoteNum,
        doc = _getDiatonicNoteNum.__doc__)

                                    
    def transpose(self, value, inPlace=False):
        '''Transpose the pitch by the user-provided value. 
        If the value is an integer, the transposition is 
        treated in half steps. If the value is a string, 
        any Interval string specification can be provided. 
        Alternatively, a :class:`music21.interval.Interval` 
        object can be supplied.

        >>> from music21 import *
        >>> aPitch = pitch.Pitch('g4')
        >>> bPitch = aPitch.transpose('m3')
        >>> bPitch
        B-4
        >>> aInterval = interval.Interval(-6)
        >>> bPitch = aPitch.transpose(aInterval)
        >>> bPitch
        C#4
        
        >>> aPitch
        G4
        >>> aPitch.transpose(aInterval, inPlace=True)
        >>> aPitch
        C#4
        
        OMIT_FROM_DOCS
        
        Test to make sure that extreme ranges work
        >>> dPitch = pitch.Pitch('D2')
        >>> lowC = dPitch.transpose('m-23')
        >>> lowC
        C#-1
        
        
        >>> otherPitch = pitch.Pitch('D2')
        >>> otherPitch.transpose('m-23', inPlace = True)
        >>> otherPitch
        C#-1
        '''
        #environLocal.printDebug(['Pitch.transpose()', value])
        if hasattr(value, 'diatonic'): # its an Interval class with a DiatonicInterval class
            intervalObj = value
        else: # try to process
            intervalObj = interval.Interval(value)
        if not inPlace:
            return intervalObj.transposePitch(self)
        else:
            p = intervalObj.transposePitch(self)
            # can setName with nameWithOctave to recreate all essential
            # pitch attributes
            # NOTE: in some cases this may not return exactly the proper config            
            self._setName(p.name)
            self._setOctave(p.octave)
            # manually copy accidental object
            self.accidental = p.accidental
            # set fundamental
            self.fundamental = p.fundamental
            return None

    #---------------------------------------------------------------------------
    # utilities for pitch object manipulation

    def transposeBelowTarget(self, target, minimize=False):
        '''Given a source Pitch, shift it down octaves until it is below the target. Note: this manipulates src inPlace.
    
        If `minimize` is True, a pitch below the the target will move up to the nearest octave. 

        >>> from music21 import *
        >>> pitch.Pitch('g5').transposeBelowTarget(pitch.Pitch('c#4'))
        G3
        >>> # if already below the target, make no change
        >>> pitch.Pitch('g#3').transposeBelowTarget(pitch.Pitch('c#6'))
        G#3
        >>> # accept the same pitch
        >>> pitch.Pitch('g#8').transposeBelowTarget(pitch.Pitch('g#1'))
        G#1

        >>> pitch.Pitch('g#2').transposeBelowTarget(pitch.Pitch('f#8'))
        G#2
        >>> pitch.Pitch('g#2').transposeBelowTarget(pitch.Pitch('f#8'), minimize=True)
        G#7
        >>> pitch.Pitch('f#2').transposeBelowTarget(pitch.Pitch('f#8'), minimize=True)
        F#8
        '''
        # TODO: add inPlace as an option, default is True
        src = self
        while True:
            # ref 20, min 10, lower ref
            # ref 5, min 10, do not lower
            if src.ps - target.ps <= 0:
                break
            # lower one octave
            src.octave -= 1

        # case where self is below target and minimize is True
        if minimize:
            while True:
                if target.ps - src.ps < 12:
                    break
                else:
                    src.octave += 1


        return src
    
    
    def transposeAboveTarget(self, target, minimize=False):
        '''Given a source Pitch, shift it up octaves until it is above the target. Note: this manipulates src inPlace.

        If `minimize` is True, a pitch above the the target will move down to the nearest octave. 

        >>> from music21 import *
        >>> pitch.Pitch('d2').transposeAboveTarget(pitch.Pitch('e4'))
        D5
        >>> # if already above the target, make no change
        >>> pitch.Pitch('d7').transposeAboveTarget(pitch.Pitch('e2'))
        D7
        >>> # accept the same pitch
        >>> pitch.Pitch('d2').transposeAboveTarget(pitch.Pitch('d8'))
        D8

        >>> # if minimize is True, we go the closest position
        >>> pitch.Pitch('d#8').transposeAboveTarget(pitch.Pitch('d2'), minimize=True)
        D#2
        >>> pitch.Pitch('d7').transposeAboveTarget(pitch.Pitch('e2'), minimize=True)
        D3
        >>> pitch.Pitch('d0').transposeAboveTarget(pitch.Pitch('e2'), minimize=True)
        D3

        '''
        src = self
        # case where self is below target
        while True:
            # ref 20, max 10, do not raise ref
            # ref 5, max 10, raise ref to above max
            if src.ps - target.ps >= 0:
                break
            # raise one octave
            src.octave += 1

        # case where self is above target and minimize is True
        if minimize:
            while True:
                if src.ps - target.ps < 12:
                    break
                else:
                    src.octave -= 1 


        return src
    
    

    #---------------------------------------------------------------------------

    def inheritDisplay(self, other):
        '''Inherit display properties from another Pitch, including those found on the Accidental object.

        >>> from music21 import *

        >>> a = pitch.Pitch('c#')
        >>> a.accidental.displayType = 'always'
        >>> b = pitch.Pitch('c-')
        >>> b.inheritDisplay(a)
        >>> b.accidental.displayType
        'always'

        '''
        # if other.accidental is None no problem
        if self._accidental != None:
            self._accidental.inheritDisplay(other.accidental)



#     def updateAccidentalKeySignature(self, alteredPitches=[], 
#         overrideStatus=False):
#         '''Given the pitches in a key signature, adjust the display of
#         this accidental. To get the pitches from a :class:`music21.key.KeySignature`, use the :attr:`~music21.key.KeySignature.alteredPitches` property.
# 
#         Note: this will only set the status of the present Accidental; this will not provide cautionary Accidentals. for that, use updateAccidentalDisplay() method.
#         '''
#         if overrideStatus == False: # go with what we have defined
#             if self.accidental == None:
#                 pass # no accidental defined; we may need to add one
#             elif (self.accidental != None and 
#             self.accidental.displayStatus == None): # not set; need to set  
#                 # configure based on displayStatus alone, continue w/ normal
#                 pass
#             elif (self.accidental != None and 
#             self.accidental.displayStatus in [True, False]): 
#                 return # exit: already set, do not override
# 
#         for p in alteredPitches: # all are altered tones, must have acc
#             if p.step == self.step: # A# to A or A# to A-, etc
#                 # we have an altered tone in key sig but none here;
#                 # we need a natural 
#                 if self.accidental == None: 
#                     self.accidental = Accidental('natural')
#                     self.accidental.displayStatus = True 
#                 # a different accidental, do need to show
#                 elif self.accidental.name != p.accidental.name: 
#                     self.accidental.displayStatus = True 
#                 # the same accidental, do not need to show
#                 elif self.accidental.name == p.accidental.name: 
#                     self.accidental.displayStatus = False
#                 break # only looking for one match
#                 

    def _nameInKeySignature(self, alteredPitches):
        '''Determine if this pitch is in the collection of supplied altered pitches, derived from a KeySignature object

        >>> from music21 import *
        >>> a = pitch.Pitch('c#')
        >>> b = pitch.Pitch('g#')
        >>> ks = key.KeySignature(2)
        >>> a._nameInKeySignature(ks.alteredPitches)
        True
        >>> b._nameInKeySignature(ks.alteredPitches)
        False
        ''' 
        for p in alteredPitches: # all are altered tones, must have acc
            if p.step == self.step: # A# to A or A# to A-, etc
                if p.accidental.name == self.accidental.name:
                    return True
        return False

    def _stepInKeySignature(self, alteredPitches):
        '''Determine if this pitch is in the collection of supplied altered pitches, derived from a KeySignature object

        >>> from music21 import *
        >>> a = pitch.Pitch('c')
        >>> b = pitch.Pitch('g')
        >>> ks = key.KeySignature(2)
        >>> a._stepInKeySignature(ks.alteredPitches)
        True
        >>> b._stepInKeySignature(ks.alteredPitches)
        False
        ''' 
        for p in alteredPitches: # all are altered tones, must have acc
            if p.step == self.step: # A# to A or A# to A-, etc
                return True
        return False



    def setAccidentalDisplay(self, value=None):
        '''If this Pitch has an accidental, set its displayStatus, which can be True, False, or None. 

        >>> from music21 import *

        >>> a = pitch.Pitch('a')
        >>> past = [pitch.Pitch('a#'), pitch.Pitch('c#'), pitch.Pitch('c')]
        >>> a.updateAccidentalDisplay(past, cautionaryAll=True)
        >>> a.accidental, a.accidental.displayStatus
        (<accidental natural>, True)
        >>> a.setAccidentalDisplay(None)
        >>> a.accidental, a.accidental.displayStatus
        (<accidental natural>, None)
        '''
        if self.accidental != None:
            self.accidental.displayStatus = value 


    def updateAccidentalDisplay(self, pitchPast=[], pitchPastMeasure=[],
                                alteredPitches=[],
            cautionaryPitchClass=True, cautionaryAll=False, 
            overrideStatus=False, cautionaryNotImmediateRepeat=True,
            lastNoteWasTied=False,
            ):
        '''
        Given an ordered list of Pitch objects in `pitchPast`, 
        determine if this pitch's Accidental object needs 
        to be created or updated with a natural or other cautionary accidental.


        Changes to this Pitch object's Accidental object are made in-place.

        `pitchPast` is a list of pitches preceeding this pitch
        
        `pitchPastMeasure` is a list of pitches preceeding this pitch but in a previous measure

        The `alteredPitches` list supplies pitches from a :class:`~music21.key.KeySignature` object using the :attr:`~music21.key.KeySignature.alteredPitches` property. 


        If `cautionaryPitchClass` is True, comparisons to past accidentals 
        are made regardless of register. That is, if a past sharp is found two 
        octaves above a present natural, a natural sign is still displayed. 
        Note that this has nothing to do with whether a sharp (not in the key signature)
        is found in a different octave from the same note in a different octave.  The
        sharp must always be displayed.
        

        If `overrideStatus` is True, this method will ignore any current 
        `displayStatus` stetting found on the Accidental. By default this 
        does not happen. If `displayStatus` is set to None, the 
        Accidental's `displayStatus` is set. 


        If `cautionaryNotImmediateRepeat` is True, cautionary accidentals will be displayed 
        for an altered pitch even if that pitch had already been displayed as altered (unless
        it's an immediate repetition).


        If `lastNoteWasTied` is True then this note will be treated as immediately following a tie.


        >>> from music21 import *

        >>> a = pitch.Pitch('a')
        >>> past = [pitch.Pitch('a#'), pitch.Pitch('c#'), pitch.Pitch('c')]
        >>> a.updateAccidentalDisplay(past, cautionaryAll=True)
        >>> a.accidental, a.accidental.displayStatus
        (<accidental natural>, True)

        >>> b = pitch.Pitch('a')
        >>> past = [pitch.Pitch('a#'), pitch.Pitch('c#'), pitch.Pitch('c')]
        >>> b.updateAccidentalDisplay(past) # should add a natural
        >>> b.accidental, b.accidental.displayStatus
        (<accidental natural>, True)

        >>> a4 = pitch.Pitch('a4')
        >>> past = [pitch.Pitch('a#3'), pitch.Pitch('c#'), pitch.Pitch('c')]
        >>> # will not add a natural because match is pitchSpace
        >>> a4.updateAccidentalDisplay(past, cautionaryPitchClass=False)
        >>> a4.accidental == None
        True

        '''
        # TODO: this presently deals with chords as simply a list
        # we might permit pitchPast to contain a list of pitches, to represent
        # a simultaneity?

        # should we display accidental if no previous accidentals have been displayed
        # i.e. if it's the first instance of an accidental after a tie
        displayAccidentalIfNoPreviousAccidentals = False

        pitchPastAll = pitchPastMeasure + pitchPast

        if overrideStatus == False: # go with what we have defined
            if self.accidental is None:
                pass # no accidental defined; we may need to add one
            elif self.accidental.displayStatus == None: # not set; need to set  
                # configure based on displayStatus alone, continue w/ normal
                pass
            elif (self.accidental != None and 
                self.accidental.displayStatus in [True, False]): 
                return # exit: already set, do not override

        if lastNoteWasTied == True:
            if self.accidental is not None:
                if self.accidental.displayType != 'even-tied':
                    self.accidental.displayStatus = False
                return
            else:
                return # exit: nothing more to do

        ### no pitches in past...
        if len(pitchPastAll) == 0:
            # if we have no past, we always need to show the accidental, 
            # unless this accidental is in the alteredPitches list
            if (self.accidental != None 
            and self.accidental.displayStatus in [False, None]):
                if not self._nameInKeySignature(alteredPitches):
                    self.accidental.displayStatus = True
                else:
                    self.accidental.displayStatus = False

            # in case display set to True and in alteredPitches, makeFalse
            elif (self.accidental != None 
                  and self.accidental.displayStatus == True 
                  and self._nameInKeySignature(alteredPitches)):
                self.accidental.displayStatus = False

            # if no accidental or natural but matches step in key sig
            # we need to show or add or an accidental
            elif ((self.accidental == None or self.accidental.name == 'natural')
                  and self._stepInKeySignature(alteredPitches)):
                if self.accidental == None:
                    self.accidental = Accidental('natural')
                self.accidental.displayStatus = True
            return # do not search past

        #### pitches in past... first search if last pitch in measure
        #### at this octave contradicts this pitch.  if so then no matter what
        #### we need an accidental.
        for i in reversed(range(len(pitchPast))):
            thisPPast = pitchPast[i]
            if thisPPast.step == self.step and thisPPast.octave == self.octave:
                if thisPPast.name != self.name: # conflicting alters, need accidental and return
                    if self.accidental is None:
                        self.accidental = Accidental('natural')
                    self.accidental.displayStatus = True
                    return
                else: #names are the same, skip this line of questioning
                    break
        # nope, no previous pitches in this octave and register, now more complex things...


        # here tied and always are treated the same; we assume that
        # making ties sets the displayStatus, and thus we would not be 
        # overriding that display status here
        if (cautionaryAll == True or 
            (self.accidental != None 
             and self.accidental.displayType in ['even-tied', 'always'])): 
            # show all no matter
            if self.accidental == None:
                self.accidental = Accidental('natural')
            # show all accidentals, even if past encountered
            self.accidental.displayStatus = True
            return # do not search past

        # store if a match was found and display set from past pitches
        setFromPitchPast = False 

        if cautionaryPitchClass is True: # warn no mater what octave; thus create new without oct
            pSelf = Pitch(self.name)
            pSelf.accidental = self.accidental
        else:
            pSelf = self

        #where does the line divide between in measure and out of measure
        outOfMeasureLength = len(pitchPastMeasure)

        # need to step through pitchPast in reverse
        # comparing this pitch to the past pitches; if we find a match
        # in terms of name, then decide what to do

        ## are we only comparing a list of past pitches all of
        ## which are the same as this one and in the same measure?
        ## if so, set continuousRepeatsInMeasure to True
        ## else, set to False
        
        ## figure out if this pitch is in the measure (pPastInMeasure = True)
        ## or not.
        for i in reversed(range(len(pitchPastAll))):            
            # is the past pitch in the measure or out of the measure?
            if i < outOfMeasureLength:
                pPastInMeasure = False
                continuousRepeatsInMeasure = False
            else:
                pPastInMeasure = True
                for j in range(i, len(pitchPastAll)):
                    # do we have a continuous stream of the same note leading up to this one...
                    if pitchPastAll[j].nameWithOctave != self.nameWithOctave:                    
                        continuousRepeatsInMeasure = False
                        break
                else:
                    continuousRepeatsInMeasure = True
            # if the pitch is the first of a measure, has an accidental, 
            # it is not an altered key signature pitch, 
            # and it is not a natural, it should always be set to display
            if (pPastInMeasure == False
                and self.accidental != None 
                and not self._nameInKeySignature(alteredPitches)):
                self.accidental.displayStatus = True
                return # do not search past
             
            # create Pitch objects for comparison; remove pitch space
            # information if we are only doing a pitch class comparison
            if cautionaryPitchClass == True: # no octave; create new without oct
                pPast = Pitch(pitchPastAll[i].name)
                # must manually assign reference to the same accidentals
                # as name alone will not transfer display status
                pPast.accidental = pitchPastAll[i].accidental
            else: # cautionary in terms of pitch space; must match exact
                pPast = pitchPastAll[i]

            # if we do not match steps (A and A#), we can continue
            if pPast.step != pSelf.step:
                continue

            # store whether these match at the same octave; needed for some
            # comparisons even if not matching pitchSpace
            if self.octave == pitchPastAll[i].octave:
                octaveMatch = True
            else:
                octaveMatch = False

            # repeats of the same pitch immediately following, in the same measure
            # where one previous pitch has displayStatus = True; don't display
            if (continuousRepeatsInMeasure == True
                and pPast.accidental != None
                and pPast.accidental.displayStatus == True
                ):
                if pSelf.accidental != None: #only needed if one has a natural and this does not
                    self.accidental.displayStatus = False
                return

            # repeats of the same accidentally immediately following
            # if An to An or A# to A#: do not need unless repeats requested,
            # regardless of if 'unless-repeated' is set, this will catch 
            # a repeated case
            
            elif (continuousRepeatsInMeasure == True
                and pPast.accidental != None 
                and pSelf.accidental != None 
                and pPast.accidental.name == pSelf.accidental.name):

                ### BUG! what about C#4 C#5 C#4 C#5 -- last C#4 and C#5 should not show accidental if cautionaryNotImmediateRepeat is False
                                
                # if not in the same octave, and not in the key sig, do show accidental
                if (self._nameInKeySignature(alteredPitches) == False
                    and (octaveMatch == False
                         or pPast.accidental.displayStatus == False)
                    ):
                    displayAccidentalIfNoPreviousAccidentals = True
                    continue
                else:
                    self.accidental.displayStatus = False
                    setFromPitchPast = True
                    break

            # if An to A: do not need another natural
            # yet, if we are against the key sig, then we need another natural if in another octave
            elif (pPast.accidental != None 
                  and pPast.accidental.name == 'natural' 
                  and (pSelf.accidental == None 
                       or pSelf.accidental.name == 'natural')):
                if continuousRepeatsInMeasure == True: # an immediate repeat; do not show
                    # unless we are altering the key signature and in 
                    # a different register
                    if (self._stepInKeySignature(alteredPitches) == True
                        and octaveMatch == False):
                        if self.accidental == None:
                            self.accidental = Accidental('natural')
                        self.accidental.displayStatus = True
                    else:
                        if self.accidental != None:
                            self.accidental.displayStatus = False
                # if we match the step in a key signature and we want 
                # cautionary not immediate repeated
                elif (self._stepInKeySignature(alteredPitches) == True
                      and cautionaryNotImmediateRepeat == True):
                    if self.accidental == None:
                        self.accidental = Accidental('natural')
                    self.accidental.displayStatus = True

                # cautionaryNotImmediateRepeat == False
                # but the previous note was not in this measure,
                # so do the previous step anyhow
                elif (self._stepInKeySignature(alteredPitches) == True
                      and cautionaryNotImmediateRepeat == False
                      and pPastInMeasure == False):
                    if self.accidental == None:
                        self.accidental = Accidental('natural')
                    self.accidental.displayStatus = True

                
                
                # other cases: already natural in past usage, do not need 
                # natural again (and not in key sig)
                else:
                    if self.accidental != None:
                        self.accidental.displayStatus = False
                setFromPitchPast = True
                break

            # if A# to A, or A- to A, but not A# to A#
            # we use stepWithOctave though not necessarily a ps comparison
            elif (pPast.accidental != None 
                  and pPast.accidental.name != 'natural' 
                  and (pSelf.accidental == None 
                       or pSelf.accidental.displayStatus == False)):
                if octaveMatch == False and cautionaryPitchClass == False:
                    continue
                if self.accidental == None:
                    self.accidental = Accidental('natural')
                self.accidental.displayStatus = True
                setFromPitchPast = True
                break

            # if An or A to A#: need to make sure display is set
            elif ((pPast.accidental == None 
                   or pPast.accidental.name == 'natural') 
                  and pSelf.accidental != None 
                  and pSelf.accidental.name != 'natural'):
                self.accidental.displayStatus = True
                setFromPitchPast = True
                break

            # if A- or An to A#: need to make sure display is set
            elif (pPast.accidental != None and pSelf.accidental != None 
                  and pPast.accidental.name != pSelf.accidental.name):
                self.accidental.displayStatus = True
                setFromPitchPast = True
                break

            # going from a natural to an accidental, we should already be
            # showing the accidental, but just to check
            # if A to A#, or A to A-, but not A# to A
            elif (pPast.accidental == None and pSelf.accidental != None):
                self.accidental.displayStatus = True
                #environLocal.printDebug(['match previous no mark'])
                setFromPitchPast = True
                break

            # if A# to A# and not immediately repeated:
            # default is to show accidental
            # if cautionaryNotImmediateRepeat is False, will not be shown
            elif (continuousRepeatsInMeasure == False
                  and pPast.accidental != None 
                  and pSelf.accidental != None 
                  and pPast.accidental.name == pSelf.accidental.name
                  and octaveMatch == True):
                if (cautionaryNotImmediateRepeat == False 
                    and pPast.accidental.displayStatus != False): 
                    # do not show (unless previous note's accidental wasn't displayed
                    # because of a tie or some other reason)
                    # result will be False, do not need to check altered tones
                    self.accidental.displayStatus = False
                    displayAccidentalIfNoPreviousAccidentals = False
                    setFromPitchPast = True
                    break
                elif pPast.accidental.displayStatus == False:
                    # in case of ties...
                    displayAccidentalIfNoPreviousAccidentals = True
                else:
                    if not self._nameInKeySignature(alteredPitches):
                        self.accidental.displayStatus = True
                    else:
                        self.accidental.displayStatus = False
                    setFromPitchPast = True
                    return
            
            else:
                pass

        # if we have no previous matches for this pitch and there is 
        # an accidental: show, unless in alteredPitches
        # cases of displayAlways and related are matched above
        if displayAccidentalIfNoPreviousAccidentals == True:
            # not the first pitch of this nameWithOctave in the measure
            # but, because of ties, the first to be displayed
            if self._nameInKeySignature(alteredPitches) == False:
                if self.accidental is None:
                    self.accidental = Accidental('natural')
                self.accidental.displayStatus = True
            else:
                self.accidental.displayStatus = False
            displayAccidentalIfNoPreviousAccidentals = False #just to be sure
        elif not setFromPitchPast and self.accidental != None:
            if not self._nameInKeySignature(alteredPitches):
                self.accidental.displayStatus = True
            else:
                self.accidental.displayStatus = False

        # if we have natural that alters the key sig, create a natural
        elif not setFromPitchPast and self.accidental == None:
            if self._stepInKeySignature(alteredPitches):
                self.accidental = Accidental('natural')
                self.accidental.displayStatus = True
                
    def getStringHarmonic(self, chordIn):
        '''Given a chord, determines whether the chord constitutes a string harmonic and then
        returns a new chord with the proper sounding pitch added.


        >>> from music21 import *
        >>> n1 = note.Note('d3')
        >>> n2 = note.Note('g3')
        >>> n2.notehead = 'diamond'
        >>> n2.noteheadFill = 'no'
        >>> p1 = pitch.Pitch('d3')
        >>> harmChord = chord.Chord([n1, n2])
        >>> harmChord.quarterLength = 1
        >>> newChord = p1.getStringHarmonic(harmChord)
        >>> newChord.quarterLength = 1
        >>> pitchList = newChord.pitches
        >>> pitchList
        [D3, G3, D5]
        '''
        
        #Takes in a chord, finds the interval between the notes
        from music21 import note, pitch, chord
        
        pitchList = chordIn.pitches
        isStringHarmonic = False
        
        if chordIn.getNotehead(pitchList[1]) == 'diamond':
            isStringHarmonic = True 
            
        if isStringHarmonic == True:
            chordInt = interval.notesToChromatic(pitchList[0], pitchList[1])
            
            if chordInt.intervalClass == 12:
                soundingPitch = pitchList[0].getHarmonic(2)
            elif chordInt.intervalClass == 7:
                soundingPitch = pitchList[0].getHarmonic(3)
            elif chordInt.intervalClass == 5:
                soundingPitch = pitchList[0].getHarmonic(4)
            elif chordInt.intervalClass == 4:
                soundingPitch = pitchList[0].getHarmonic(5)
            elif chordInt.intervalClass == 3:
                soundingPitch = pitchList[0].getHarmonic(6) 
            elif chordInt.intervalClass == 6:
                soundingPitch = pitchList[0].getHarmonic(7)
            elif chordInt.intervalClass == 8:
                soundingPitch = pitchList[0].getHarmonic(8)
            else:
                #make this give an error or something
                soundingPitch = pitchList[0]
            
        noteOut = note.Note(soundingPitch.nameWithOctave)
        noteOut.noteheadParen = True
        noteOut.noteheadFill = 'yes'
        noteOut.stemDirection = 'noStem'
        
        note1 = note.Note(pitchList[0].nameWithOctave)
        note2 = note.Note(pitchList[1].nameWithOctave)
        note2.notehead = chordIn.getNotehead(pitchList[1])
        
        #to do: make note small
        
        chordOut = chord.Chord([note1, note2, noteOut])
        
        return chordOut
        
        
        
            
        
        



#-------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):
    
    def runTest(self):
        pass
    
    def testSingle(self):
        a = Pitch()
        a.name = 'c#'
        a.show()



class Test(unittest.TestCase):
    
    def runTest(self):
        pass

    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
        '''
        import sys, types, copy
        for part in sys.modules[self.__module__].__dict__.keys():
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            name = getattr(sys.modules[self.__module__], part)
            if callable(name) and not isinstance(name, types.FunctionType):
                try: # see if obj can be made w/ args
                    obj = name()
                except TypeError:
                    continue
                a = copy.copy(obj)
                b = copy.deepcopy(obj)

        p1 = Pitch("C#3")
        p2 = copy.deepcopy(p1)
        self.assertTrue(p1 is not p2)
        self.assertTrue(p1.accidental is not p2.accidental)


    def testOctave(self):
        b = Pitch("B#3")
        self.assertEqual(b.octave, 3)
    

    def testAccidentalImport(self):
        '''Test that we are getting the properly set accidentals
        '''
        from music21 import corpus
        s = corpus.parse('bwv438.xml')
        tenorMeasures = s.parts[2].getElementsByClass('Measure')
        pAltered = tenorMeasures[0].pitches[1]
        self.assertEqual(pAltered.accidental.name, 'flat')
        self.assertEqual(pAltered.accidental.displayType, 'normal')
        # in key signature, so shuold not be shown
        self.assertEqual(pAltered.accidental.displayStatus, False)

        altoMeasures = s.parts[1].getElementsByClass('Measure')
        pAltered = altoMeasures[6].pitches[2]
        self.assertEqual(pAltered.accidental.name, 'sharp')
        self.assertEqual(pAltered.accidental.displayStatus, True)


    def testUpdateAccidentalDisplaySimple(self):
        '''Test updating accidental display.
        '''

        past = [Pitch('a3#'), Pitch('c#'), Pitch('c')]

        a = Pitch('c')
        a.accidental = Accidental('natural')
        a.accidental.displayStatus = False # hide
        self.assertEqual(a.name, 'C')
        self.assertEqual(a.accidental.displayStatus, False)

        a.updateAccidentalDisplay(past, overrideStatus=True)
        self.assertEqual(a.accidental.displayStatus, True)


        b = copy.deepcopy(a)
        self.assertEqual(b.accidental.displayStatus, True)
        self.assertEqual(b.accidental.name, 'natural')




    def testUpdateAccidentalDisplaySeries(self):
        '''Test updating accidental display.
        '''

        def proc(pList, past=[]):
            for p in pList:
                p.updateAccidentalDisplay(past)
                past.append(p)

        def compare(past, result):
            #environLocal.printDebug(['accidental compare'])
            for i in range(len(result)):
                p = past[i]
                if p.accidental == None:
                    pName = None
                    pDisplayStatus = None
                else:
                    pName = p.accidental.name
                    pDisplayStatus = p.accidental.displayStatus

                targetName = result[i][0]
                targetDisplayStatus = result[i][1]

                #environLocal.printDebug(['accidental test:', p, pName, pDisplayStatus, 'target:', targetName, targetDisplayStatus]) # test
                self.assertEqual(pName, targetName, "name error for %d: %s instead of desired %s" % (i, pName, targetName))
                self.assertEqual(pDisplayStatus, targetDisplayStatus, "%d: %s display: %s, target %s" % (i, p, pDisplayStatus, targetDisplayStatus))

        # alternating, in a sequence, same pitch space
        pList = [Pitch('a#3'), Pitch('a3'), Pitch('a#3'), 
                 Pitch('a3'), Pitch('a#3')]
        result = [('sharp', True), ('natural', True), ('sharp', True), 
                  ('natural', True), ('sharp', True)]
        proc(pList, [])        
        compare(pList, result)

        # alternating, in a sequence, different pitch space
        pList = [Pitch('a#2'), Pitch('a6'), Pitch('a#1'), 
                 Pitch('a5'), Pitch('a#3')]
        result = [('sharp', True), ('natural', True), ('sharp', True), 
                  ('natural', True), ('sharp', True)]
        proc(pList, [])        
        compare(pList, result)

        # alternating, after gaps
        pList = [Pitch('a-2'), Pitch('g3'), Pitch('a5'), 
                 Pitch('a#5'), Pitch('g-3'), Pitch('a3')]
        result = [('flat', True), (None, None), ('natural', True), 
                  ('sharp', True), ('flat', True), ('natural', True)]
        proc(pList, [])        
        compare(pList, result)

        # repeats of the same: show at different registers
        pList = [Pitch('a-2'), Pitch('a-2'), Pitch('a-5'), 
                 Pitch('a#5'), Pitch('a#3'), Pitch('a3'), Pitch('a2')]
        result = [('flat', True), ('flat', False), ('flat', True), 
                  ('sharp', True), ('sharp', True), ('natural', True), ('natural', True)]
        proc(pList, [])        
        compare(pList, result)

        #the always- 'unless-repeated' setting 
        # first, with no modification, repeated accidentals are not shown
        pList = [Pitch('a-2'), Pitch('a#3'), Pitch('a#5')]
        result = [('flat', True), ('sharp', True), ('sharp', True)]
        proc(pList, [])        
        compare(pList, result)

        # second, with status set to always 
        pList = [Pitch('a-2'), Pitch('a#3'), Pitch('a#3')]
        pList[2].accidental.displayType = 'always'
        result = [('flat', True), ('sharp', True), ('sharp', True)]
        proc(pList, [])        
        compare(pList, result)

        # status set to always 
        pList = [Pitch('a2'), Pitch('a3'), Pitch('a5')]
        pList[2].accidental = Accidental('natural')
        pList[2].accidental.displayType = 'always'
        result = [(None, None), (None, None), ('natural', True)]
        proc(pList, [])        
        compare(pList, result)

        # first use after other pitches in different register
        # note: this will force the display of the accidental
        pList = [Pitch('a-2'), Pitch('g3'), Pitch('a-5')]
        result = [('flat', True), (None, None), ('flat', True)]
        proc(pList, [])        
        compare(pList, result)

        # first use after other pitches in different register
        # note: this will force the display of the accidental
        pList = [Pitch('a-2'), Pitch('g3'), Pitch('a-2')]
        # pairs of accidental, displayStatus
        result = [('flat', True), (None, None), ('flat', True)]
        proc(pList, [])        
        compare(pList, result)


        # accidentals, first usage, not first pitch
        pList = [Pitch('a2'), Pitch('g#3'), Pitch('d-2')]
        result = [(None, None), ('sharp', True), ('flat', True)]
        proc(pList, [])        
        compare(pList, result)



    def testUpdateAccidentalDisplaySeriesKeySignature(self):
        '''Test updating accidental display.
        '''
        from music21 import key

        def proc(pList, past=[], alteredPitches=[]):
            for p in pList:
                p.updateAccidentalDisplay(past, alteredPitches=alteredPitches)
                past.append(p)

        def compare(past, result):
            #environLocal.printDebug(['accidental compare'])
            for i in range(len(result)):
                p = past[i]
                if p.accidental == None:
                    pName = None
                    pDisplayStatus = None
                else:
                    pName = p.accidental.name
                    pDisplayStatus = p.accidental.displayStatus

                targetName = result[i][0]
                targetDisplayStatus = result[i][1]

                #environLocal.printDebug(['accidental test:', p, pName, pDisplayStatus, 'target:', targetName, targetDisplayStatus]) # test
                self.assertEqual(pName, targetName)
                self.assertEqual(pDisplayStatus, targetDisplayStatus, "%d: %s display: %s, target %s" % (i, p, pDisplayStatus, targetDisplayStatus))

        # chromatic alteration of key
        pList = [Pitch('f#3'), Pitch('f#2'), Pitch('f3'), 
            Pitch('f#3'), Pitch('f#3'), Pitch('g3'), Pitch('f#3')]
        result = [('sharp', False), ('sharp', False), ('natural', True), 
            ('sharp', True), ('sharp', False), (None, None), ('sharp', False)]
        ks = key.KeySignature(1) # f3
        proc(pList, [], ks.alteredPitches)        
        compare(pList, result)

        # non initial scale tones
        pList = [Pitch('a3'), Pitch('b2'), Pitch('c#3'), 
            Pitch('f#3'), Pitch('g#3'), Pitch('f#3'), Pitch('a4')]
        result = [(None, None), (None, None), ('sharp', False), 
            ('sharp', False), ('sharp', False), ('sharp', False), (None, None)]
        ks = key.KeySignature(3) 
        proc(pList, [], ks.alteredPitches)        
        compare(pList, result)

        # non initial scale tones with chromatic alteration
        pList = [Pitch('a3'), Pitch('c#3'), Pitch('g#3'), 
        Pitch('g3'), Pitch('c#4'), Pitch('g#4')]
        result = [(None, None), ('sharp', False), ('sharp', False), 
            ('natural', True), ('sharp', False), ('sharp', True)]
        ks = key.KeySignature(3) 
        proc(pList, [], ks.alteredPitches)        
        compare(pList, result)

        # non initial scale tones with chromatic alteration
        pList = [Pitch('a3'), Pitch('c#3'), Pitch('g#3'), 
        Pitch('g3'), Pitch('c#4'), Pitch('g#4')]
        result = [(None, None), ('sharp', False), ('sharp', False), 
            ('natural', True), ('sharp', False), ('sharp', True)]
        ks = key.KeySignature(3) 
        proc(pList, [], ks.alteredPitches)        
        compare(pList, result)

        # initial scale tones with chromatic alteration, repeated tones
        pList = [Pitch('f#3'), Pitch('f3'), Pitch('f#3'), 
                 Pitch('g3'), Pitch('f#4'), Pitch('f#4')]
        result = [('sharp', False), ('natural', True), ('sharp', True), 
                   (None, None), ('sharp', True), ('sharp', False)]  # no 4 is a dicey affair; could go either way
        ks = key.KeySignature(1) 
        proc(pList, [], ks.alteredPitches)        
        compare(pList, result)

        # initial scale tones with chromatic alteration, repeated tones
        pList = [Pitch('d3'), Pitch('e3'), Pitch('f#3'), 
        Pitch('g3'), Pitch('f4'), Pitch('g#4'),
        Pitch('c#3'), Pitch('f#4'), Pitch('c#4')]
        result = [(None, None), (None, None), ('sharp', False), 
            (None, None), ('natural', True), ('sharp', True),
            ('sharp', False), ('sharp', True), ('sharp', False)]
        ks = key.KeySignature(2) 
        proc(pList, [], ks.alteredPitches)        
        compare(pList, result)

        # altered tones outside of key
        pList = [Pitch('b3'), Pitch('a3'), Pitch('e3'), 
        Pitch('b-3'), Pitch('a-3'), Pitch('e-3'), 
        Pitch('b-3'), Pitch('a-3'), Pitch('e-3'),
        Pitch('b-3'), Pitch('a-3'), Pitch('e-3')]
        result = [('natural', True), ('natural', True), ('natural', True), 
            ('flat', True), ('flat', True), ('flat', True),
            ('flat', False), ('flat', False), ('flat', False),
            ('flat', False), ('flat', False), ('flat', False),]
        ks = key.KeySignature(-3) # b-, e-, a- 
        proc(pList, [], ks.alteredPitches)        
        compare(pList, result)


        # naturals against the key signature are required for each and every use
        pList = [Pitch('b3'), Pitch('a3'), Pitch('e3'), 
                 Pitch('b4'), Pitch('a-3'), Pitch('e-3'), 
                 Pitch('b3'), Pitch('a3'), Pitch('e3')]
        result = [('natural', True), ('natural', True), ('natural', True), 
            ('natural', True), ('flat', True), ('flat', True),
            ('natural', True), ('natural', True), ('natural', True)]
        ks = key.KeySignature(-3) # b-, e-, a- 
        proc(pList, [], ks.alteredPitches)        
        compare(pList, result)

    def testUpdateAccidentalDisplayOctaves(self):
        '''
        test if octave display is working
        '''

        def proc1(pList, past=[]):
            for p in pList:
                p.updateAccidentalDisplay(past, cautionaryPitchClass=True, cautionaryNotImmediateRepeat=False)
                past.append(p)

        def proc2(pList, past=[]):
            for p in pList:
                p.updateAccidentalDisplay(past, cautionaryPitchClass=False, cautionaryNotImmediateRepeat=False)
                past.append(p)


        def compare(past, result):
            #environLocal.printDebug(['accidental compare'])
            for i in range(len(result)):
                p = past[i]
                if p.accidental == None:
                    pName = None
                    pDisplayStatus = None
                else:
                    pName = p.accidental.name
                    pDisplayStatus = p.accidental.displayStatus

                targetName = result[i][0]
                targetDisplayStatus = result[i][1]

                #environLocal.printDebug(['accidental test:', p, pName, pDisplayStatus, 'target:', targetName, targetDisplayStatus]) # test
                self.assertEqual(pName, targetName)
                self.assertEqual(pDisplayStatus, targetDisplayStatus, "%d: %s display: %s, target %s" % (i, p, pDisplayStatus, targetDisplayStatus))

        pList = [Pitch('c#3'), Pitch('c#4'), Pitch('c#3'), 
                 Pitch('c#4')]
        result = [('sharp', True), ('sharp', True), ('sharp', False), 
                  ('sharp', False)]
        proc1(pList, [])        
        compare(pList, result)
        pList = [Pitch('c#3'), Pitch('c#4'), Pitch('c#3'), 
                 Pitch('c#4')]
        proc2(pList, [])        
        compare(pList, result)

        a4 = Pitch('a4')
        past = [Pitch('a#3'), Pitch('c#'), Pitch('c')]
        # will not add a natural because match is pitchSpace
        a4.updateAccidentalDisplay(past, cautionaryPitchClass=False)
        self.assertEqual(a4.accidental, None)

    def testAccidentalsCautionary(self):
        '''
        a nasty test from Jose about octave leaps, cautionaryNotImmediateRepeat = False
        and key signature conflicts
        '''
        from music21 import tinyNotation, key
        bm = tinyNotation.TinyNotationStream("fn1 fn1 e-8 e'-8 fn4 en4 e'n4", "4/4")
        bm.insert(0, key.KeySignature(1))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        bm.flat.notes
        assert(bm.flat.notes[0].accidental.name == 'natural')     # Fn
        assert(bm.flat.notes[0].accidental.displayStatus == True)
        assert(bm.flat.notes[1].accidental.name == 'natural')     # Fn
        assert(bm.flat.notes[1].accidental.displayStatus == True)
        assert(bm.flat.notes[2].accidental.name == 'flat')        # E-4
        assert(bm.flat.notes[2].accidental.displayStatus == True)
        assert(bm.flat.notes[3].accidental.name == 'flat')        # E-5
        assert(bm.flat.notes[3].accidental.displayStatus == True)
        assert(bm.flat.notes[4].accidental.name == 'natural')     # En4 
        assert(bm.flat.notes[4].accidental.displayStatus == True)
        assert(bm.flat.notes[5].accidental.name == 'natural')     # En4 
        assert(bm.flat.notes[5].accidental.displayStatus == True)

        assert(bm.flat.notes[6].accidental != None)               # En5
        assert(bm.flat.notes[6].accidental.name == 'natural')
        assert(bm.flat.notes[6].accidental.displayStatus == True)
    
        return


    def testPitchEquality(self):
        '''Test updating accidental display.
        '''
        data = [('a', 'b', False), ('a', 'a', True), ('a#', 'a', False),
                ('a#', 'b-', False), ('a#', 'a-', False), ('a##', 'a#', False),
            ('a#4', 'a#4', True), ('a-3', 'a-4', False), ('a#3', 'a#4', False),
            ]
        for x, y, match in data:
            p1 = Pitch(x)
            p2 = Pitch(y)
            self.assertEqual(p1==p2, match)

        # specific case of changing octave
        p1 = Pitch('a#')
        p2 = Pitch('a#')
        self.assertEqual(p1==p2, True)

        p1.octave = 4
        p2.octave = 3
        self.assertEqual(p1==p2, False)
        p1.octave = 4
        p2.octave = 4
        self.assertEqual(p1==p2, True)

    def testLowNotes(self):
        dPitch = Pitch('D2')
        lowC = dPitch.transpose('M-23')
        self.assertEqual(lowC.name, "C")
        self.assertEqual(lowC.octave, -1)


    def testQuarterToneA(self):
        from music21 import stream, note, scale

        p1 = Pitch('D#~')
        #environLocal.printDebug([p1, p1.accidental])
        self.assertEqual(str(p1), 'D#~')
        # test generation of raw musicxml output
        xmlout = p1.musicxml
        #p1.show()
        match = '<step>D</step><alter>1.5</alter><octave>4</octave>'
        xmlout = xmlout.replace(' ', '')
        xmlout = xmlout.replace('\n', '')
        self.assertEqual(xmlout.find(match), 621)

        s = stream.Stream()
        for pStr in ['A~', 'A#~', 'A`', 'A-`']:
            p = Pitch(pStr)
            self.assertEqual(str(p), pStr)
            n = note.Note()
            n.pitch = p
            s.append(n)
        self.assertEqual(len(s), 4)
        match = [e.ps for e in s]
        self.assertEqual(match, [69.5, 70.5, 68.5, 67.5] )

        s = stream.Stream()
        alterList = [None, .5, 1.5, -1.5, -.5, 'half-sharp', 'one-and-a-half-sharp', 'half-flat', 'one-and-a-half-flat', '~']
        sc = scale.MajorScale('c4')
        for x in range(1, 10):
            n = note.Note(sc.pitchFromDegree(x % sc.getDegreeMaxUnique()))
            n.quarterLength = .5
            n.pitch.accidental = Accidental(alterList[x])
            s.append(n)

        match = [str(n.pitch) for n in s.notes]
        self.assertEqual(match, ['C~4', 'D#~4', 'E-`4', 'F`4', 'G~4', 'A#~4', 'B`4', 'C-`4', 'D~4'])

        
        match = [e.ps for e in s]
        self.assertEqual(match, [60.5, 63.5, 62.5, 64.5, 67.5, 70.5, 70.5, 58.5, 62.5] )


    def testMicrotoneA(self):
        
        from music21 import pitch


        p = pitch.Pitch('a4')
        p.microtone = 25
        
        self.assertEqual(repr(p), 'A4(+25c)')
        self.assertEqual(p.ps, 69.25)

        p.microtone = '-10'
        self.assertEqual(repr(p), 'A4(-10c)')
        self.assertEqual(p.ps, 68.90)

        self.assertEqual(p.pitchClass, 9)


        p = p.transpose(12)
        self.assertEqual(repr(p), 'A5(-10c)')
        self.assertEqual(p.ps, 80.90)



    def testMicrotoneB(self):
        from music21 import pitch

        self.assertEqual(str(pitch.Pitch('c4').getHarmonic(1)), 'C4')

        p = pitch.Pitch('c4')
        p.microtone = 20
        self.assertEqual(str(p), 'C4(+20c)')
        self.assertEqual(str(p.getHarmonic(1)), 'C4(+20c)')

        self.assertEqual(str(pitch.Pitch('c4').getHarmonic(2)), 'C5')
        self.assertEqual(str(pitch.Pitch('c4').getHarmonic(3)), 'G5(+2c)')
        self.assertEqual(str(pitch.Pitch('c4').getHarmonic(4)), 'C6')
        self.assertEqual(str(pitch.Pitch('c4').getHarmonic(5)), 'E6(-14c)')
        self.assertEqual(str(pitch.Pitch('c4').getHarmonic(6)), 'G6(+2c)')
        self.assertEqual(str(pitch.Pitch('c4').getHarmonic(7)), 'A~6(+19c)')


        self.assertEqual(pitch.Pitch('g4').harmonicString('c3'), '3rdH(-2c)/C3')

        #self.assertEqual(str(convertPsToStep(60.0)), "('C', <accidental natural>, None, 0)")

        self.assertEqual(str(pitch.Pitch('c4').getHarmonic(1)), 'C4')
        self.assertEqual(str(pitch.Pitch('c3').getHarmonic(2)), 'C4')
        self.assertEqual(str(pitch.Pitch('c2').getHarmonic(2)), 'C3')

        self.assertEqual(pitch.Pitch('c4').harmonicString('c3'), '2ndH/C3')


        f = pitch.Pitch('c3')
        f.microtone = -10
        self.assertEqual(str(f.getHarmonic(2)), 'C4(-10c)')


        p = pitch.Pitch('c4')
        f = pitch.Pitch('c3')
        f.microtone = -20
        # the third harmonic of c3 -20 is closer than the 
        self.assertEqual(p.harmonicString(f), '2ndH(+20c)/C3(-20c)')

        f.microtone = +20
        self.assertEqual(p.harmonicString(f), '2ndH(-20c)/C3(+20c)')

        p1 = pitch.Pitch('c1')
        self.assertEqual(str(p1.getHarmonic(13)), 'G#~4(-9c)')
        
        p2 = pitch.Pitch('a1')
        self.assertEqual(str(p2.getHarmonic(13)), 'F~5(-9c)')
        
        self.assertEqual(str(p1.transpose('M6')), 'A1')
        # not sure if this is correct:
        #self.assertEqual(str(p1.getHarmonic(13).transpose('M6')), 'E##5(-9c)')


    def testMicrotoneC(self):
        import copy
        from music21 import pitch

        match = []
        p = pitch.Pitch("C4")
        p.microtone = 5
        for i in range(11):
            match.append(copy.deepcopy(p))
            p.microtone = p.microtone.cents - 1
        self.assertEqual(str(match), '[C4(+5c), C4(+4c), C4(+3c), C4(+2c), C4(+1c), C4, C4(-1c), C4(-2c), C4(-3c), C4(-4c), C4(-5c)]')



    def testMicrotoneD(self):
        from music21 import pitch
        # the microtonal scale used by padberg
        f = [440, 458+1/3., 476+2/3., 495, 513+1/3., 531+2/3., 550, 568+1/3.,
            586+2/3., 605, 623+1/3., 641+2/3., 660, 678+1/3., 696+2/3., 715, 733+1/3., 751+2/3., 770, 788+1/3., 806+2/3., 825, 843+1/3., 861+2/3.]
        self.assertEqual(len(f), 24)
        pList = []
        for fq in f:
            p = pitch.Pitch()
            p.frequency = fq
            pList.append(p)
        self.assertEqual(str(pList), '[A4, A~4(+21c), B`4(-11c), B4(+4c), B~4(+17c), C~5(-22c), C#5(-14c), C#~5(-7c), C##5(-2c), D~5(+1c), E-5(+3c), E`5(+3c), E5(+2c), E~5(-1c), F5(-4c), F~5(-9c), F#5(-16c), F#~5(-23c), F#~5(+19c), G5(+10c), G~5(-1c), G#5(-12c), G#~5(-24c), G#~5(+14c)]')


    def testJsonSerializationA(self):
        from music21 import pitch
        
        m = pitch.Microtone(40)
        self.assertEqual(str(m), '(+40c)')

        mAlt = pitch.Microtone()
        mAlt.json = m.json
        self.assertEqual(str(mAlt), '(+40c)')
    
        a = pitch.Accidental('##')
        self.assertEqual(str(a), '<accidental double-sharp>')
        aAlt = pitch.Accidental()
        aAlt.json = a.json
        self.assertEqual(str(aAlt), '<accidental double-sharp>')

        p = pitch.Pitch(ps=61.2)
        self.assertEqual(str(p), 'C#4(+20c)')
        pAlt = pitch.Pitch()
        pAlt.json = p.json
        self.assertEqual(str(pAlt), 'C#4(+20c)')

        
        
#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Pitch, Accidental]


if __name__ == "__main__":
    # sys.arg test options will be used in mainTest()
    music21.mainTest(Test)
    #t = Test()
    #t.testAccidentalsCautionary()

#------------------------------------------------------------------------------
# eof

