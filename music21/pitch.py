#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         pitch.py
# Purpose:      music21 classes for representing pitches
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''
Classes and functions for creating and manipulating pitches, pitch-space, and accidentals.
Used extensively by note.py
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


from music21 import environment
_MOD = "pitch.py"
environLocal = environment.Environment(_MOD)



STEPREF = {
           'C' : 0,
           'D' : 2,
           'E' : 4,
           'F' : 5,
           'G' : 7,
           'A' : 9,
           'B' : 11,
               }
STEPNAMES = ['C','D','E','F','G','A','B']



#-------------------------------------------------------------------------------
# utility functions
def convertPitchClassToNumber(ps):
    '''Given a pitch class or pitch class value, look for strings. If a string is found, replace it with the default pitch class representation.

    >>> convertPitchClassToNumber(3)
    3
    >>> convertPitchClassToNumber('a')
    10
    >>> convertPitchClassToNumber('B')
    11
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

    >>> convertNameToPs('c4')
    60
    >>> convertNameToPs('c2#')
    37.0
    >>> convertNameToPs('d7-')
    97.0
    >>> convertNameToPs('e1--')
    26.0
    >>> convertNameToPs('b2##')
    49.0
    '''
    # use pitch name reading in Pitch object, 
    # as an Accidental object is created.
    p = Pitch(pitchName)
    return p.ps

def convertPsToOct(ps):
    '''Utility conversion; does not process internals.
    Assume C4 middle C, so 60 returns 4
    >>> [convertPsToOct(59), convertPsToOct(60), convertPsToOct(61)]
    [3, 4, 4]
    >>> [convertPsToOct(12), convertPsToOct(0), convertPsToOct(-12)]
    [0, -1, -2]
    >>> convertPsToOct(135)
    10
    '''
    return int(math.floor(ps / 12.)) - 1

def convertPsToStep(ps):
    '''Utility conversion; does not process internals.
    Takes in a midiNote number (Assume C4 middle C, so 60 returns 4)
    Returns a tuple of Step name and either a natural or a sharp
    
    >>> convertPsToStep(60)
    ('C', <accidental natural>)
    >>> convertPsToStep(66)
    ('F', <accidental sharp>)
    >>> convertPsToStep(67)
    ('G', <accidental natural>)
    >>> convertPsToStep(68)
    ('G', <accidental sharp>)
    >>> convertPsToStep(-2)
    ('A', <accidental sharp>)

    >>> convertPsToStep(60.5)
    ('C', <accidental half-sharp>)
    >>> convertPsToStep(61.5)
    ('C', <accidental one-and-a-half-sharp>)
    >>> convertPsToStep(62)
    ('D', <accidental natural>)
    >>> convertPsToStep(62.5)
    ('D', <accidental half-sharp>)
    >>> convertPsToStep(135)
    ('D', <accidental sharp>)
    '''
    # if this is a microtone it may have floating point vals
    pcReal = ps % 12 
    pc, micro = divmod(pcReal, 1)
    if round(micro, 1) == 0.5:
        micro = 0.5
    else:
        micro = 0

    pc = int(pc)
    if pc in STEPREF.values():
        acc = Accidental(0+micro)
        pcName = pc 
    elif pc-1 in STEPREF.values():
        acc = Accidental(1+micro)
        pcName = pc-1
    elif pc+1 in STEPREF.values():
        acc = Accidental(-1+micro)  # can't happen
        pcName = pc+1
    for key, value in STEPREF.items():
        if pcName == value:
            name = key
            break
    return name, acc

def convertStepToPs(step, oct, acc=None):
    '''Utility conversion; does not process internals.
    >>> convertStepToPs('c', 4, 1)
    61
    >>> convertStepToPs('d', 2, -2)
    36
    >>> convertStepToPs('b', 3, 3)
    62
    '''
    step = step.strip().upper()
    ps = ((oct + 1) * 12) + STEPREF[step]
    if acc is None:
        return ps
    # this does not work
    elif common.isNum(acc):
        return ps + acc
    else: # assume that this is an accidental object
        return ps + acc.alter

def convertPsToFq(ps):
    '''Utility conversion; does not process internals.
    
    Assumes A4 = 440 Hz
    >>> convertPsToFq(69)
    440.0
    >>> convertPsToFq(60)
    261.62556530059862
    >>> convertPsToFq(2)
    9.1770239974189884
    >>> convertPsToFq(135)
    19912.126958213179

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
    Assumes A4 = 440 Hz
    >>> convertFqToPs(440)
    69.0
    >>> convertFqToPs(261.62556530059862)
    60.0
    '''
    return 12 * (math.log(fq / 440.0) / math.log(2)) + 69   

#-------------------------------------------------------------------------------
class AccidentalException(Exception):
    pass

class PitchException(Exception):
    pass




#-------------------------------------------------------------------------------
class Accidental(music21.Music21Object):
    '''Accidental class.
    '''
    displayType = "normal" # always, never, unless-repeated, even-tied
    displayStatus = None
    displayStyle = "normal" # "parentheses", "bracket", "both"
    displaySize  = "full"   # "cue", "large", or a percentage
    displayLocation = "normal" # "normal", "above" = ficta, "below"
    # above and below could also be useful for gruppetti, etc.

    # define order to present names in documentation; use strings
    _DOC_ORDER = ['set']
    # documentation for all attributes (not properties or methods)
    _DOC_ATTR = {
    'displayType': '''Display if first in measure; other valid terms:
        "always", "never", "unless-repeated" (show always unless
        the immediately preceding note is the same), "even-tied"
        (stronger than always: shows even if it is tied to the
        previous note)''',
    'displayStatus': '''Given the displayType, should 
        this accidental be displayed?
        Can be True, False, or None if not defined. For contexts where
        the next program down the line cannot evaluate displayType
        ''',
    'displaySize': 'Size in display: "cue", "large", or a percentage.',
    'displayStyle': 'Style of display: "parentheses", "bracket", "both".',
    }

    def __init__(self, specifier='natural'):
        self.name = None
        self.modifier = ''
        self.alter = 0.0     # semitones to alter step
        #alterFrac = [0,0]   # fractional alteration 
        # (e.g., 1/6); fraction class in 2.6
        #alterExp  = [0,0,0] # exponental alteration 
        # (e.g., [2,3,19] = 2**(3/19))
        #alterHarm = 0       # altered according to a harmonic

        self.set(specifier)

    def __repr__(self):
        return '<accidental %s>' % self.name
        

    def __eq__(self, other):
        '''Equality. Needed for pitch comparisons.

        >>> a = Accidental('double-flat')
        >>> b = Accidental('double-flat')
        >>> c = Accidental('double-sharp')
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
        '''Greater than.

        >>> a = Accidental('sharp')
        >>> b = Accidental('flat')
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

    def __lt__(self, other):
        '''Less than

        >>> a = Accidental('natural')
        >>> b = Accidental('flat')
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

    def set(self, name):
        '''
        Provide a value to the Accidental. Strings values, numbers, and Lilypond
        Abbreviations are all accepted.  

        >>> a = Accidental()
        >>> a.set('sharp')
        >>> a.alter == 1
        True

        >>> a = Accidental()
        >>> a.set(2)
        >>> a.modifier == "##"
        True

        >>> a = Accidental()
        >>> a.set(2.0)
        >>> a.modifier == "##"
        True

        >>> a = Accidental('--')
        >>> a.alter
        -2.0
        '''
        if common.isStr(name):
            name = name.lower() # sometimes args get capitalized
        if name in ['natural', "n", 0]: 
            self.name = 'natural'
            self.alter = 0.0
            self.modifier = ''
        elif name in ['sharp', "#", "is", 1, 1.0]:
            self.name = 'sharp'
            self.alter = 1.0
            self.modifier = '#'
        elif name in ['double-sharp', "##", "isis", 2]:
            self.name = 'double-sharp'
            self.alter = 2.0
            self.modifier = '##'
        elif name in ['flat', "-", "es", -1]:
            self.name = 'flat'
            self.alter = -1.0
            self.modifier = '-'
        elif name in ['double-flat', "--", "eses", -2]:
            self.name = 'double-flat'
            self.alter = -2.0
            self.modifier = '--'
        
        elif name in ['half-sharp', 'quarter-sharp', 'ih', 'semisharp', .5]:
            self.name = 'half-sharp'
            self.alter = 0.5
        elif name in ['one-and-a-half-sharp', 'three-quarter-sharp', \
             'three-quarters-sharp', 'isih', 'sesquisharp', 1.5]:
            self.name = 'one-and-a-half-sharp'
            self.alter = 1.5  
        elif name in ['half-flat', 'quarter-flat', 'eh', 'semiflat', -.5]:
            self.name = 'half-flat'
            self.alter = -0.5
        elif name in ['one-and-a-half-flat', 'three-quarter-flat', \
             'three-quarters-flat', 'eseh', 'sesquiflat', -1.5]:
            self.name = 'one-and-a-half-flat'
            self.alter = -1.5
        else:
            raise AccidentalException('%s is not a supported accidental type' % name)
        
    def inheritDisplay(self, other):
        '''Given another Accidental object, inherit all the display properites
        of that object. 

        This is needed when transposing Pitches: we need to retain accidental display properties. 

        >>> a = Accidental('double-flat')
        >>> a.displayType = 'always'
        >>> b = Accidental('sharp')
        >>> b.inheritDisplay(a)
        >>> b.displayType
        'always'
        '''        
        if other != None: # empty accidental attributes are None
            for attr in ['displayType', 'displayStatus', 
                        'displayStyle', 'displaySize', 'displayLocation']:
                value = getattr(other, attr)
                setattr(self, attr, value)

    def _getLily(self):
        lilyRet = ""
        if (self.name == "sharp"): lilyRet = "is"
        if (self.name == "double-sharp"): lilyRet = "isis"
        if (self.name == "flat"): lilyRet = "es"
        if (self.name == "double-flat"): lilyRet = "eses"
        if (self.name == "natural"): lilyRet = ""
        if (self.name == "half-sharp"): lilyRet = "ih"
        if (self.name == "one-and-a-half-sharp"): lilyRet = "isih"
        if (self.name == "half-flat"): lilyRet = "eh"
        if (self.name == "one-and-a-half-flat"): lilyRet = "eseh"
        
        if self.displayStatus == True or self.displayType == "always" \
           or self.displayType == "even-tied":
            lilyRet += "!"
        
        if self.displayStyle == "parentheses" or self.displayStyle == "both":
            lilyRet += "?"
            ## no brackets for now
        return lilyRet
        
    def _setLily(self, value):
        if (value.count("isis") > 0): self.setAccidental("double-sharp")
        elif (value.count("eses") > 0): self.setAccidental("double-flat")
        elif (value.count("isih") > 0): 
            self.setAccidental("one-and-a-half-sharp")
        elif (value.count("eseh") > 0): 
            self.setAccidental("one-and-a-half-flat")
        elif (value.count("is") > 0): self.setAccidental("sharp")
        elif (value.count("es") > 0): self.setAccidental("flat")
        elif (value.count("ih") > 0): self.setAccidental("half-sharp")
        elif (value.count("eh") > 0): self.setAccidental("half-flat")

        if value.count("!") > 0:
            self.displayType = "always"            
        if value.count("?") > 0:
            self.displayStyle = "parentheses"

    # property
    lily = property(_getLily, _setLily)

    def _getMx(self):
        """From music21 to MusicXML
        >>> a = Accidental()
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
            
        mxAccidental.set('content', mxName)

        return mxAccidental


    def _setMx(self, mxAccidental):
        """From MusicXML to Music21
        
        >>> a = musicxml.Accidental()
        >>> a.set('content', 'half-flat')
        >>> a.get('content')
        'half-flat'
        >>> b = Accidental()
        >>> b.mx = a
        >>> b.name
        'half-flat'
        """
        mxName = mxAccidental.get('content')
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
    '''An object for storing pitch values. All values are represented internally as a scale step (self.step), and octave and an accidental object. In addition, pitches know their pitchSpace representation (self._ps); altering any of the first three changes the pitchSpace representation. Similarly, altering the pitchSpace representation alters the first three.
    '''

    # define order to present names in documentation; use strings
    _DOC_ORDER = ['name', 'nameWithOctave', 'step', 'pitchClass', 'octave', 'midi']
    # documentation for all attributes (not properties or methods)
    _DOC_ATTR = {
    }
    def __init__(self, name=None):
        '''Create a Pitch.

        Optional parameter name should include a step and accidental character(s)

        it can also include a non-negative octave number.  ("C#4", "B--3", etc.)

        >>> p1 = Pitch('a#')
        >>> p1
        A#
        >>> p2 = Pitch(3)
        >>> p2
        D#
        '''
        music21.Music21Object.__init__(self)

        # this should not be set, as will be updated when needed
        self._ps = None # pitch space representation, w C4=60 (midi)
        # self._ps must correspond to combination of step and alter
        self._step = defaults.pitchStep # this is only the pitch step
        # keep an accidental object based on self._alter
        
        self._overridden_freq440 = None
        self._twelfth_root_of_two = 2.0 ** (1.0/12)
        self._accidental = None

        # should this remain an attribute or only refer to value in defaults
        self.defaultOctave = defaults.pitchOctave
        self._octave = None
        self._pitchSpaceNeedsUpdating = True

        # name combines step, octave, and accidental
        if name is not None and not common.isNum(name):       
            self._setName(name)
        elif name is not None and common.isNum(name):
            self._setPitchClass(name)

    def __repr__(self):
        return self.nameWithOctave

    def __eq__(self, other):
        '''Do not accept enharmonic equivalance.
        >>> a = Pitch('c2')
        >>> a.octave
        2
        >>> b = Pitch('c4')
        >>> b.octave
        4
        >>> a == b
        False
        >>> a != b
        True
        '''
        if other is None:
            return False
        if (self.octave == other.octave and self.step == other.step and 
            self.accidental == other.accidental):
            return True
        else:
            return False

    def __lt__(self, other):
        '''Do not accept enharmonic equivalence. Based entirely on pitch space 
        representation.
        >>> a = Pitch('c4')
        >>> b = Pitch('c#4')
        >>> a < b
        True
        '''
        if self.ps < other.ps:
            return True
        else:
            return False

    def __gt__(self, other):
        '''Do not accept enharmonic equivialance. Based entirely on pitch space 
        representation.
        >>> a = Pitch('d4')
        >>> b = Pitch('d8')
        >>> a > b
        False
        '''
        if self.ps > other.ps:
            return True
        else:
            return False

    #---------------------------------------------------------------------------
    def _getAccidental(self):
        '''
        >>> a = Pitch('D-2')
        >>> a.accidental.alter
        -1.0
        '''
        return self._accidental
    
    def _setAccidental(self, value):
        '''
        >>> a = Pitch('E')
        >>> a.ps  # here this is an int
        64
        >>> a.accidental = '#'
        >>> a.ps  # here this is a float
        65.0
        '''
        if (isinstance(value, basestring) or common.isNum(value)):
            self._accidental = Accidental(value)
        else:
            self._accidental = value
        self._pitchSpaceNeedsUpdating = True
    
    accidental = property(_getAccidental, _setAccidental)

    def _getPs(self):
        if self._pitchSpaceNeedsUpdating:
            self._updatePitchSpace()
        return self._ps
    
    def _setPs(self, value):
        self._ps = value
        self._pitchSpaceNeedsUpdating = False

        ### this should eventually change to "stepEtcNeedsUpdating"
        ### but we'll see if it's a bottleneck
        self.step, self.accidental = convertPsToStep(self._ps)
        self.octave = convertPsToOct(self._ps)

    ps = property(_getPs, _setPs, 
        doc='''The ps property permits getting and setting a pitch space value, a floating point number representing pitch space, where 60 is C4, middle C, integers are half-steps, and floating point values are microtonal tunings (.01 is equal to one cent).

        >>> a = Pitch()
        >>> a.ps = 45
        >>> a
        A2
        >>> a.ps = 60
        >>> a
        C4

        ''')

    def _updatePitchSpace(self):
        '''
        recalculates the pitchSpace number (called when self.step, self.octave 
        or self.accidental are changed.
        '''
        self._ps = convertStepToPs(self._step, self.implicitOctave,
                                   self.accidental)

    def _getMidi(self):
        '''
        >>> a = Pitch('C3')
        >>> a.midi
        48
        >>> a.midi =  23.5
        >>> a.midi
        24
        >>> a.midi = 128
        >>> a.midi
        116
        >>> a.midi = -10
        >>> a.midi
        2
        '''
        if self._pitchSpaceNeedsUpdating:
            self._updatePitchSpace()
            self._pitchSpaceNeedsUpdating = False
        return int(round(self.ps))

    def _setMidi(self, value):
        '''
        midi values are constrained within the range of 0 to 127
        floating point values,
        '''
        value = int(round(value))
        if value > 127:
            value = (12 * 9) + (value % 12) # highest oct plus modulus
        elif value < 0:
            value = 0 + (value % 12) # lowest oct plus modulus            
        self.ps = value      
        self._pitchSpaceNeedsUpdating = True

    
    midi = property(_getMidi, _setMidi, doc="midi is ps (pitchSpace) as a rounded int; ps can accomodate floats")

    def _getName(self):
        '''Name presently returns pitch name and accidental without octave.

        Perhaps better named getNameClass

        >>> a = Pitch('G#')
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

        if len(usrStr) == 1 and usrStr in STEPREF.keys():
            self._step = usrStr
            self.accidental = None
        elif len(usrStr) > 1 and usrStr[0] in STEPREF.keys():
            self._step = usrStr[0]
            self.accidental = Accidental(usrStr[1:])
        else:
            raise PitchException("Cannot make a name out of %s" % usrStr)
        if octFound != '': 
            octave = int(octFound)
            self.octave = octave
        self._pitchSpaceNeedsUpdating = True
    
    name = property(_getName, _setName)


    def _getNameWithOctave(self):
        '''Returns pitch name with octave

        Perhaps better default action for getName

        >>> a = Pitch('G#4')
        >>> a.nameWithOctave
        'G#4'
        '''
        if self.octave is None:
            return self.name
        else:
            return self.name + str(self.octave)

    nameWithOctave = property(_getNameWithOctave, 
        doc = '''The pitch name with an octave designation. If no octave as been set, no octave value is returned. 
        ''')

    def _getStep(self):
        '''
        >>> a = Pitch('C#3')
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
            raise PitchException("Cannot make a step out of %s" % usrStr)
        self._pitchSpaceNeedsUpdating = True

    step = property(_getStep, _setStep)


    def _getStepWithOctave(self):
        if self.octave is None:
            return self.step
        else:
            return self.step + str(self.octave)

    stepWithOctave = property(_getStepWithOctave, 
        doc = '''Returns the pitch step (F, G, etc) with octave designation. If no octave as been set, no octave value is returned. 

        >>> a = Pitch('G#4')
        >>> a.stepWithOctave
        'G4'

        >>> a = Pitch('A#')
        >>> a.stepWithOctave
        'A'
        ''')


    def _getPitchClass(self):
        '''
        >>> a = Pitch('a3')
        >>> a._getPitchClass()
        9
        >>> dis = Pitch('d3')
        >>> dis.pitchClass
        2
        >>> dis.accidental = Accidental("#")
        >>> dis.pitchClass
        3
        >>> dis.pitchClass = 11
        >>> dis.pitchClass
        11
        >>> dis.name
        'B'
        '''
        return int(round(self.ps % 12))

    def _setPitchClass(self, value):
        '''Set the pitchClass.

        >>> a = Pitch('a3')
        >>> a.pitchClass = 3
        >>> a
        D#3
        >>> a.pitchClass = 'A'
        >>> a
        A#3
        '''
        # permit the submission of strings, like A an dB
        value = convertPitchClassToNumber(value)
        # get step and accidental w/o octave
        self._step, self._accidental = convertPsToStep(value)  
        self._pitchSpaceNeedsUpdating = True

        #self.ps = convertStepToPs(self.step, self.implicitOctave, self.accidental)
      
    pitchClass = property(_getPitchClass, _setPitchClass)


    def _getPitchClassString(self):
        '''
        >>> a = Pitch('a3')
        >>> a._getPitchClassString()
        '9'
        >>> a = Pitch('a#3')
        >>> a._getPitchClassString()
        'A'
        '''
        return convertPitchClassToStr(self._getPitchClass())

    pitchClassString = property(_getPitchClassString, _setPitchClass, 
        doc = '''Return a string representation of the pitch class, where integers greater than 10 are replaced by A and B, respectively. Can be used to set pitch class by a string representation as well (though this is also possible with :attr:`~music21.pitch.Pitch.pitchClass`.
    
        >>> a = Pitch('a3')
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
        returns or sets the octave of the note.  Setting the octave
        updates the pitchSpace attribute.

        >>> a = Pitch('g')
        >>> a.octave is None
        True
        >>> a.implicitOctave
        4
        >>> a.ps  ## will use implicitOctave
        67
        >>> a.name
        'G'
        >>> a.octave = 14
        >>> a.implicitOctave
        14
        >>> a.name
        'G'
        >>> a.ps
        187
    ''')

    def _getImplicitOctave(self):
        if self.octave is None: return self.defaultOctave
        else: return self.octave
        
    implicitOctave = property(_getImplicitOctave, doc='''
    returns the octave of the Pitch, or defaultOctave if octave was never set
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
            if tempAlter >= 0:
                tempStep = 'H'
            else:
                tempAlter += 1
        if tempAlter == 0:
            return tempStep
        elif tempAlter > 0:
            tempName = tempStep + (tempAlter * 'is')
            return tempName
        else: # flats
            if self.name in ['C','D','F','G']:
                firstFlatName = 'es'
            else: # A, E.  Hb should never occur...
                firstFlatName = 's'
            multipleFlats = abs(tempAlter) - 1
            tempName =  tempStep + firstFlatName + (multipleFlats * 'es')
            return tempName
    
    german = property(_getGerman, doc ='''
    returns the name of a Pitch in the German system (where B-flat = B, B = H, etc.)
    (Microtones raise an error).
    
    >>> print Pitch('B-').german
    B
    >>> print Pitch('B').german
    H
    >>> print Pitch('E-').german
    Es
    >>> print Pitch('C#').german
    Cis
    >>> print Pitch('A--').german
    Ases
    >>> p1 = Pitch('C')
    >>> p1.accidental = Accidental('half-sharp')
    >>> p1.german
    Traceback (most recent call last):
    PitchException: Es geht nicht "german" zu benutzen mit Microtoenen.  Schade!
    ''')


    def _getFrequency(self):        
        return self._getfreq440()

    def _setFrequency(self, value):
        '''
        >>> a = Pitch()
        >>> a.frequency = 440.0
        >>> a.frequency
        440.0
        >>> a.name
        'A'
        >>> a.octave
        4
        '''
        
        # store existing octave
        ps = convertFqToPs(value)
        # should get microtones
        self.ps = int(round(ps))
        self.step, self.accidental = convertPsToStep(self.ps)  
        self.octave = convertPsToOct(self.ps)
      
    frequency = property(_getFrequency, _setFrequency, doc='''
        The frequency property gets or sets the frequency of
        the pitch in hertz.  
        If the frequency has not been overridden, then
        it is computed based on A440Hz and equal temperament
    ''')


    # these methods may belong in in a temperament object
    # name of method and property could be more clear
    def _getfreq440(self):
        '''
        >>> a = Pitch('A4')
        >>> a.freq440
        440.0
        '''
        if self._overridden_freq440:
            return self._overridden_freq440
        else:
            A4offset = self.ps - 69
            return 440.0 * (self._twelfth_root_of_two ** A4offset)
            
    def _setfreq440(self, value):
        self._overridden_freq440 = value

    freq440 = property(_getfreq440, _setfreq440)


    def _getMX(self):
        '''
        returns a musicxml.Note() object

        >>> a = Pitch('g#4')
        >>> c = a.mx
        >>> c.get('pitch').get('step')
        'G'
        '''
        mxPitch = musicxmlMod.Pitch()
        mxPitch.set('step', self.step)
        if self.accidental is not None:
            mxPitch.set('alter', self.accidental.alter)
        mxPitch.set('octave', self.implicitOctave)

        mxNote = musicxmlMod.Note()
        mxNote.setDefaults()
        mxNote.set('pitch', mxPitch)

        if (self.accidental is not None and 
            self.accidental.displayStatus in [True, None]):
            mxNote.set('accidental', self.accidental.mx)
        # should this also return an xml accidental object
        return mxNote # return element object

    def _setMX(self, mxNote):
        '''
        Given a MusicXML Note object, set this Ptich object to its values. 

        >>> b = musicxml.Pitch()
        >>> b.set('octave', 3)
        >>> b.set('step', 'E')
        >>> b.set('alter', -1)
        >>> c = musicxml.Note()
        >>> c.set('pitch', b)
        >>> a = Pitch('g#4')
        >>> a.mx = c
        >>> print(a)
        E-3
        '''
        # assume this is an object
        mxPitch = mxNote.get('pitch')
        mxAccidental = mxNote.get('accidental')

        self.step = mxPitch.get('step')

        acc = mxPitch.get('alter')
        if acc is not None: # None is used in musicxml but not in music21
            if mxAccidental is not None: # the source had wanted to show alter
                accObj = Accidental()
                accObj.mx = mxAccidental
            # used to to just use acc value
            #self.accidental = Accidental(float(acc))
            # better to use accObj if possible
                self.accidental = accObj
                self.accidental.displayStatus = True
            else:
                # here we generate an accidental object from the alter value
                # but in the source, there was not a defined accidental
                self.accidental = Accidental(float(acc))
                self.accidental.displayStatus = False
        self.octave = int(mxPitch.get('octave'))
        self._pitchSpaceNeedsUpdating = True

    mx = property(_getMX, _setMX)



    def _getMusicXML(self):
        '''Provide a complete MusicXML representation. Presently, this is based on 
        '''
        mxNote = self._getMX()
        mxMeasure = musicxml.Measure()
        mxMeasure.setDefaults()
        mxMeasure.append(mxNote)
        mxPart = musicxml.Part()
        mxPart.setDefaults()
        mxPart.append(mxMeasure)

        mxScorePart = musicxml.ScorePart()
        mxScorePart.setDefaults()
        mxPartList = musicxml.PartList()
        mxPartList.append(mxScorePart)

        mxIdentification = musicxml.Identification()
        mxIdentification.setDefaults() # will create a composer

        mxScore = musicxml.Score()
        mxScore.setDefaults()
        mxScore.set('partList', mxPartList)
        mxScore.set('identification', mxIdentification)
        mxScore.append(mxPart)

        return mxScore.xmlStr()

    def _setMusicXML(self, mxNote):
        '''
        '''
        pass

    musicxml = property(_getMusicXML, _setMusicXML)



    #---------------------------------------------------------------------------
    def _getDiatonicNoteNum(self):
        '''
        Returns an integer that uniquely identifies the note, ignoring accidentals.
        The number returned is the diatonic interval above C0 (the lowest C on
        a Boesendorfer Imperial Grand), so G0 = 5, C1 = 8, etc.
        Numbers can be negative for very low notes.        
        
        C4 (middleC) = 29, C#4 = 29, C##4 = 29, D-4 = 30, D4 = 30, etc.
        
        >>> c = Pitch('c4')
        >>> c.diatonicNoteNum
        29
        >>> c = Pitch('c#4')
        >>> c.diatonicNoteNum
        29
        >>> d = Pitch('d--4')
        >>> d.accidental.name
        'double-flat'
        >>> d.diatonicNoteNum
        30
        >>> b = Pitch()
        >>> b.step = "B"
        >>> b.octave = -1 
        >>> b.diatonicNoteNum
        0
        >>> c = Pitch("C")
        >>> c.diatonicNoteNum  #implicitOctave
        29
        '''
        if ['C','D','E','F','G','A','B'].count(self.step.upper()):
            noteNumber = ['C','D','E','F','G','A','B'].index(self.step.upper())
            return (noteNumber + 1 + (7 * self.implicitOctave))
        else:
            raise PitchException("Could not find " + self.step + " in the index of notes") 

    diatonicNoteNum = property(_getDiatonicNoteNum,
        doc = _getDiatonicNoteNum.__doc__)
        #Read-only property.\n"

                                    
    def transpose(self, value, inPlace=False):
        '''Transpose the pitch by the user-provided value. If the value is an integer, the transposition is treated in half steps. If the value is a string, any Interval string specification can be provided. Alternatively, a :class:`music21.interval.Interval` object can be supplied.

        >>> aPitch = Pitch('g4')
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
        '''
        #environLocal.printDebug(['Pitch.transpose()', value])
        if hasattr(value, 'diatonic'): # its an Interval class
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
            self._setName(p.nameWithOctave)
            # manually copy accidental object
            self.accidental = p.accidental
            return None


    def inheritDisplay(self, other):
        '''Inherit display properties from another Pitch, including those found on the Accidental object.

        >>> 
        >>> a = Pitch('c#')
        >>> a.accidental.displayType = 'always'
        >>> b = Pitch('c-')
        >>> b.inheritDisplay(a)
        >>> b.accidental.displayType
        'always'

        '''
        # if other.accidental is None no problem
        if self._accidental != None:
            self._accidental.inheritDisplay(other.accidental)


    def updateAccidentalDisplay(self, pitchPast=[],     
            cautionaryPitchClass=True, cautionaryAll=False, 
            overrideStatus=False):
        '''Given a list of Pitch objects in `pitchPast`, determine if this pitch's Accidental object needs to be created or updated with a natural or other cautionary accidental.

        Changes to this Pitch object's Accidental object are made in-place.

        If `overrideStatus` is True, this method will ignore any current `displayStatus` stetting found on the accidental. By default this does not happen.

        >>> a = Pitch('a')
        >>> past = [Pitch('a#'), Pitch('c#'), Pitch('c')]
        >>> a.updateAccidentalDisplay(past, cautionaryAll=True)
        >>> a.accidental, a.accidental.displayStatus
        (<accidental natural>, True)

        >>> b = Pitch('a')
        >>> past = [Pitch('a#'), Pitch('c#'), Pitch('c')]
        >>> b.updateAccidentalDisplay(past) # should add a natural
        >>> b.accidental, b.accidental.displayStatus
        (<accidental natural>, True)

        >>> c = Pitch('a4')
        >>> past = [Pitch('a3#'), Pitch('c#'), Pitch('c')]
        >>> # will not add a natural because match is pitchSpace
        >>> c.updateAccidentalDisplay(past, cautionaryPitchClass=False)
        >>> c.accidental == None
        True

        '''
        # TODO: this presently deals with chords as simply a list
        # we might permit pitch Past to contain a list of pitches, to represent
        # a simultaneity


        if overrideStatus == False: # go with what we have defined
            if self.accidental == None:
                pass # no accidental defined; we may need to add one
            elif (self.accidental != None and 
            self.accidental.displayStatus == None): # not set; need to set  
                # configure based on displayStatus alone, continue w/ normal
                pass
            elif (self.accidental != None and 
            self.accidental.displayStatus in [True, False]): 
                return # exit: already set, do not override

        if len(pitchPast) == 0:
            # if we have no past, we always need to show the accidental 
            if (self.accidental != None and  
                self.accidental.displayStatus in [False, None]):
                self.accidental.displayStatus = True

        # need to step through pitchPast in reverse
        for i in reversed(range(len(pitchPast))): 

            # create pitch objects for comparison; remove pitch space
            # information if we are only doing a pitch class comparison
            if cautionaryPitchClass: # no octave; create new without oct
                pPast = Pitch(pitchPast[i].name)
                pSelf = Pitch(self.name)
                # must manually assign reference to the same accidentals
                # as name alone will not transfer display status
                pPast.accidental = pitchPast[i].accidental
                pSelf.accidental = self.accidental
            else: # cautionary in terms of pitch space
                pPast = pitchPast[i]
                pSelf = self

            #environLocal.printDebug(['updateAccidentalDisplay() comparing', pPast, pSelf, pPast.nameWithOctave, pSelf.nameWithOctave, pPast.stepWithOctave, pSelf.stepWithOctave, pPast.accidental, pSelf.accidental, pPast.accidental != None, pSelf.accidental == None])

            # if we have a previous identical match
            # A# to A# or A3 to A4
            # here tied and always are treated the same; we assume that
            # making ties sets the displayStatus, and thus we would not be 
            # overriding that display status here
            if cautionaryAll or (self.accidental != None 
            and self.accidental.displayType in ['even-tied', 'always']): 
                # show all no matter
                if self.accidental == None:
                    self.accidental = Accidental('natural')
                # show all accidentals, even if past encountered
                self.accidental.displayStatus = True
                break

            # if we do not patch names, we can get a new pitch for comparison
            if pPast.stepWithOctave != pSelf.stepWithOctave:
                continue

            # repeats of the same immediately following
            # if An to An or A# to A#: do not need unless repeats requested
            if (i == len(pitchPast) - 1 and pPast.accidental != None and pSelf.accidental != None and pPast.accidental.name == pSelf.accidental.name):
                environLocal.printDebug(['match exact past accidental'])
                # both are not None, we are immediately following w same name
                if self.accidental.displayStatus in [None, True]:
                    self.accidental.displayStatus = False
                    break

            # if An to A: do not need another natural
            # we use stepWithOctave though not necessarily a ps comparison
            elif (pPast.accidental != None and 
                pPast.accidental.name == 'natural' and
                    (pSelf.accidental == None or 
                     pSelf.accidental.name == 'natural')):
                if (self.accidental != None and  
                    self.accidental.displayStatus == True):
                    self.accidental.displayStatus = False
                #environLocal.printDebug(['match previous natural'])
                break

            # if A# to A, or A- to A, but not A# to A#
            # we use stepWithOctave though not necessarily a ps comparison
            elif (pPast.accidental != None and 
                pPast.accidental.name != 'natural' and
                    (pSelf.accidental == None or 
                     pSelf.accidental.displayStatus == False)):
                if self.accidental == None:
                    self.accidental = Accidental('natural')
                self.accidental.displayStatus = True
                #environLocal.printDebug(['match previous mark'])
                break

            # if An or A or A- to A#: need to make sure display is set
            # if nothing, or if different
            elif (((pPast.accidental == None or 
                pPast.accidental.name != 'natural') or 
                (pPast.accidental != None and pSelf.accidental != None and
                pPast.accidental.name != pSelf.accidental.name))):
                if (self.accidental != None and  
                    self.accidental.displayStatus in [False, None]):
                    self.accidental.displayStatus = True
                #environLocal.printDebug(['match previous natural'])
                break

            # going from a natural to an accidental, we should already be
            # showing the accidental, but just to check
            # we use stepWithOctave though not necessarily a ps comparison
            # if A to A#, or A to A-, but not A# to A
            elif (pPast.accidental == None and 
                pSelf.accidental != None):
                self.accidental.displayStatus = True
                #environLocal.printDebug(['match previous no mark'])
                break
            else:
                pass
                environLocal.printDebug(['no match'])


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
        '''Test copyinng all objects defined in this module
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


    def testOctave(self):
        b = Pitch("B#3")
        self.assertEqual(b.octave, 3)
    

    def testAccidentalImport(self):
        '''Test that we are getting the properly set accidentals
        '''
        from music21 import corpus
        s = corpus.parseWork('bwv438.xml')
        tenorMeasures = s[2].measures
        pAltered = tenorMeasures[0].pitches[1]
        self.assertEqual(pAltered.accidental.name, 'flat')
        self.assertEqual(pAltered.accidental.displayType, 'normal')
        # in key signature, so shuold not be shown
        self.assertEqual(pAltered.accidental.displayStatus, False)

        altoMeasures = s[1].measures
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



    def testUpdateAccidentalDisplayComplete(self):
        '''Test updating accidental display.
        '''

        def proc(pList, past=[]):
            for p in pList:
                p.updateAccidentalDisplay(past)
                past.append(p)

        def compare(past, result):
            environLocal.printDebug(['accidental compare'])
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

                environLocal.printDebug(['accidental test', p, pName, pDisplayStatus, targetName, targetDisplayStatus]) # test
                self.assertEqual(pName, targetName)
                #self.assertEqual(pDisplayStatus, targetDisplayStatus)

        # alternating, in a sequence, same pitch space
        pList = [Pitch('a#3'), Pitch('a3'), Pitch('a#3'), 
        Pitch('a3'), Pitch('a#3')]
        # pairs of accidental, displayStatus
        result = [('sharp', True), ('natural', True), ('sharp', True), 
        ('natural', True), ('sharp', True)]
        proc(pList)        
        compare(pList, result)

        # alternating, in a sequence, different pitch space
        pList = [Pitch('a#2'), Pitch('a6'), Pitch('a#1'), 
        Pitch('a5'), Pitch('a#3')]
        # pairs of accidental, displayStatus
        result = [('sharp', True), ('natural', True), ('sharp', True), 
        ('natural', True), ('sharp', True)]
        proc(pList)        
        compare(pList, result)

        # alternating, after gaps
        pList = [Pitch('a-2'), Pitch('g3'), Pitch('a5'), 
        Pitch('a#5'), Pitch('g-3'), Pitch('a3')]
        # pairs of accidental, displayStatus
        result = [('flat', True), (None, None), ('natural', True), 
        ('sharp', True), ('flat', True), ('natural', True)]
        proc(pList)        
        compare(pList, result)

        # repeats of the same
        pList = [Pitch('a-2'), Pitch('a-3'), Pitch('a-5'), 
        Pitch('a#5'), Pitch('a#3'), Pitch('a3'), Pitch('a2')]
        # pairs of accidental, displayStatus
        result = [('flat', True), ('flat', False), ('flat', False), 
        ('sharp', True), ('sharp', False), ('natural', True), (None, None)]
        proc(pList)        
        compare(pList, result)


        #TODO: repeats of the same with 'unless-repeated' set

        #TODO: test passing getting past pitches from a key signatures .alteredPitches parameter; then applying to a pitch sequence


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Pitch, Accidental]


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        a = Test()
        b = TestExternal()

        a.testUpdateAccidentalDisplayComplete()