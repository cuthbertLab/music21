#-------------------------------------------------------------------------------
# Name:         interval.py
# Purpose:      music21 classes for representing intervals
#
# Authors:      Michael Scott Cuthbert
#               Jackie Rogoff
#               Amy Hailes 
#
# Copyright:    (c) 2009 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
"""Interval.py is a module for creating and manipulating interval objects.
Included classes are Interval, DiatonicInterval, GenericInterval, and ChromaticInterval.
There are also a number of useful lists included in the module."""

_MOD = "interval.py"

import copy
import math
import unittest, doctest

import music21
from music21 import pitch
from music21 import common 

DESCENDING = -1
OBLIQUE    = 0
ASCENDING  = 1

PERFECT    = 1
MAJOR      = 2
MINOR      = 3
AUGMENTED  = 4
DIMINISHED = 5
DBLAUG     = 6
DBLDIM     = 7
TRPAUG     = 8
TRPDIM     = 9


niceSpecNames = ['ERROR', 'Perfect', 'Major', 'Minor', 'Augmented', 'Diminished', 'Doubly-Augmented', 'Doubly-Diminished', 'Triply-Augmented', 'Triply-Diminished']

prefixSpecs = [None, 'P', 'M', 'm', 'A', 'd', 'AA', 'dd', 'AAA', 'ddd']

orderedPerfSpecs = ['ddd', 'dd', 'd', 'P', 'A', 'AA', 'AAA']

perfspecifiers = [TRPDIM, DBLDIM, DIMINISHED, PERFECT, AUGMENTED, DBLAUG, TRPAUG]
perfoffset = 3 ## that is, Perfect is third on the list.

orderedImperfSpecs = ['ddd', 'dd', 'd', 'm', 'M', 'A', 'AA', 'AAA']

specifiers = [TRPDIM, DBLDIM, DIMINISHED, MINOR, MAJOR, AUGMENTED, DBLAUG, TRPAUG]
majoffset  = 4

stepList = ["C", "D", "E", "F", "G", "A", "B"]

semitonesGeneric = {1:0, 2:2, 3:4, 4:5, 5:7, 6:9, 7:11} #assuming Perfect or Major

semitonesAdjustPerfect = {"P":0, "A":1, "AA":2, "AAA":3, "d":-1, "dd":-2, "ddd":-3} #offset from Perfect
semitonesAdjustImperf = {"M":0, "m":-1, "A":1, "AA":2, "AAA":3, "d":-2, "dd":-3, "ddd":-4} #offset from Major
directionTerms = {DESCENDING:"Descending", OBLIQUE:"Oblique", ASCENDING:"Ascending"}


class Interval(music21.Music21Object):
    '''

    requires either (1) a string ("P5" etc.) or    
    (2) named arguments:
    (2a) either both of
       diatonic  = DiatonicInterval object
       chromatic = ChromaticInterval object
    (2b) or both of
       note1     = Pitch (or Note) object
       note2     = Pitch (or Note) object
    in which case it figures out the diatonic and chromatic intervals itself'''

    diatonic = None
    chromatic = None
    direction = None
    generic   = None
    note1 = None  # n.b. -- at present, changing these does NOT change
    note2 = None  #   the interval.  Get an interval from two notes from generateInterval(n1, n2)
    type = "" # harmonic or melodic
    diatonicType = 0
    niceName = ""

    def __init__(self, *args, **keydict):
        music21.Music21Object.__init__(self)
        if len(args) == 1 and isinstance(args[0], basestring):
            (dInterval, cInterval) = _separateIntervalFromString(args[0])
            self.diatonic = dInterval
            self.chromatic = cInterval
        else:
            if ("diatonic" in keydict):
                self.diatonic = keydict['diatonic']
            if ("chromatic" in keydict):
                self.chromatic = keydict['chromatic']
            if ("note1" in keydict):
                self.note1 = keydict['note1']
            if ("note2" in keydict):
                self.note2 = keydict['note2']

        self.reinit()

    def reinit(self):
        '''Reinitialize the internal interval objects in case something has changed.  Called
        also during __init__'''
        if self.note1 is not None and self.note2 is not None:
            genericInterval = generateGeneric(self.note1, self.note2)
            chromaticInterval = generateChromatic(self.note1, self.note2)
            diatonicInterval = generateDiatonic(genericInterval, chromaticInterval)
            self.diatonic = diatonicInterval
            self.chromatic = chromaticInterval

        if self.chromatic:
            self.direction = self.chromatic.direction
        elif self.diatonic:
            self.direction = self.diatonic.generic.direction
            
        if self.diatonic:
            self.specifier      = self.diatonic.specifier
            self.diatonicType   = self.diatonic.specifier
            self.specificName   = self.diatonic.specificName
            self.generic        = self.diatonic.generic

            self.name           = self.diatonic.name
            self.niceName       = self.diatonic.niceName
            self.simpleName     = self.diatonic.simpleName
            self.simpleNiceName = self.diatonic.simpleNiceName
            self.semiSimpleName = self.diatonic.semiSimpleName
            self.semiSimpleNiceName = self.diatonic.semiSimpleNiceName
            
            self.directedName   = self.diatonic.directedName
            self.directedNiceName = self.diatonic.directedNiceName
            self.directedSimpleName = self.diatonic.directedSimpleName
            self.directedSimpleNiceName = self.diatonic.directedSimpleNiceName

class DiatonicInterval(music21.Music21Object):
    #TODO: add more documentation
    def __init__(self, specifier = None, generic = None):
        music21.Music21Object.__init__(self)

        if (specifier is not None and generic is not None):
            if type(generic) is int:
                self.generic = GenericInterval(generic)
            else:
                self.generic = generic

        self.name = ""
        self.specifier = specifier
        if (specifier):
            self.name = prefixSpecs[specifier] + str(self.generic.undirected)
            self.niceName = niceSpecNames[specifier] + " " + self.generic.niceName
            self.directedName = prefixSpecs[specifier] + str(self.generic.directed)
            self.directedNiceName = directionTerms[self.generic.direction] + " " + self.niceName
            self.simpleName = prefixSpecs[specifier] + str(self.generic.simpleUndirected)
            self.simpleNiceName = niceSpecNames[specifier] + " " + self.generic.simpleNiceName
            self.semiSimpleName = prefixSpecs[specifier] + str(self.generic.semiSimpleUndirected)
            self.semiSimpleNiceName = niceSpecNames[specifier] + " " + self.generic.semiSimpleNiceName
            self.directedSimpleName = prefixSpecs[specifier] + str(self.generic.simpleDirected)
            self.directedSimpleNiceName = directionTerms[self.generic.direction] + " " + self.simpleNiceName
            self.specificName = niceSpecNames[specifier]
            self.prefectable = self.generic.perfectable

            ### for inversions 
            if self.prefectable:
                ### generate inversions.  P <-> P; d <-> A; dd <-> AA; etc. 
                self.orderedSpecifierIndex = orderedPerfSpecs.index(prefixSpecs[specifier])
                self.invertedOrderedSpecIndex = len(orderedPerfSpecs) - 1 - self.orderedSpecifierIndex
                self.invertedOrderedSpecifier = orderedPerfSpecs[self.invertedOrderedSpecIndex]
            else:
                ### generate inversions.  m <-> M; d <-> A; etc.
                self.orderedSpecifierIndex = orderedImperfSpecs.index(prefixSpecs[specifier])
                self.invertedOrderedSpecIndex = len(orderedImperfSpecs) - 1 - self.orderedSpecifierIndex
                self.invertedOrderedSpecifier = orderedImperfSpecs[self.invertedOrderedSpecIndex]
            self.mod7inversion = self.invertedOrderedSpecifier + str(self.generic.mod7inversion)
            if self.generic.direction == DESCENDING:
                self.mod7 = self.mod7inversion
            else:
                self.mod7 = self.simpleName

    def mod7_object(self):
        '''generates a new Interval (not DiatonicInterval) object where descending 3rds are 6ths, etc.'''
        return generateIntervalFromString(self.mod7)
            
class GenericInterval(music21.Music21Object):
    '''
    A generic interval is an interval such as Third, Seventh, Octave, Tenth.
    Constructor takes an int specifying the interval and direction:
    
    staffDistance: the number of lines or spaces apart;  
        E.g. C4 to C4 = 0;  C4 to D4 = 1;  C4 to B3 = -1
    '''
    
    def __init__(self, value):
        music21.Music21Object.__init__(self)

        self.value    = value
        self.directed = value
        self.undirected = abs(value)

        if (self.directed == 1):
            self.direction = OBLIQUE
        elif (self.directed == -1):
            raise IntervalException("Descending P1s not allowed")
        elif (self.directed == 0):
            raise IntervalException("The Zeroth is not an interval")
        elif (self.directed == self.undirected):
            self.direction = ASCENDING
        else:
            self.direction = DESCENDING

        if (self.undirected > 2): self.isSkip = True
        else: self.isSkip = False
        if (self.undirected == 2): self.isStep = True
        else: self.isStep = False
        
        ## unisons (even augmented) are neither steps nor skips.

        (steps, octaves) = math.modf(self.undirected/7.0)
        steps = int(steps*7 + .001)
        octaves = int(octaves)
        if (steps == 0):
            octaves = octaves - 1
            steps = 7
        self.simpleUndirected = steps

        ## semiSimpleUndirected, same as simple, but P8 != P1
        self.semiSimpleUndirected = steps
        self.undirectedOctaves = octaves
        
        if (steps == 1 and octaves >= 1):
            self.semiSimpleUndirected = 8

        if (self.direction == DESCENDING):
            self.octaves = -1 * octaves
            if (steps != 1):
                self.simpleDirected = -1 * steps
            else:
                self.simpleDirected = 1  # no descending unisons...
            self.semiSimpleDirected = -1 * self.semiSimpleUndirected
        else:
            self.octaves = octaves
            self.simpleDirected = steps
            self.semiSimpleDirected = self.semiSimpleUndirected
            
        if (self.simpleUndirected==1) or \
           (self.simpleUndirected==4) or \
           (self.simpleUndirected==5):
            self.perfectable = True
        else:
            self.perfectable = False
        
        self.niceName = common.musicOrdinals[self.undirected]
        self.simpleNiceName = common.musicOrdinals[self.simpleUndirected]
        self.semiSimpleNiceName = common.musicOrdinals[self.semiSimpleUndirected]

        if self.directed == 1:
            self.staffDistance = 0
        elif self.directed > 1:
            self.staffDistance = self.directed - 1
        elif self.directed < -1:
            self.staffDistance = self.directed + 1
        else:
            raise Exception("Who the hell is using non-integer or -1 or 0 as a diatonic interval????")

        self.mod7inversion = 9 - self.semiSimpleUndirected #  2 -> 7; 3 -> 6; 8 -> 1 etc.

        if self.direction == DESCENDING:
            self.mod7 = self.mod7inversion  ## see chord.hasScaleX for usage...
        else:
            self.mod7 = self.simpleDirected

    def __int__(self):
        return self.directed

    def mod7_object(self):
        '''generates a new GenericInterval object where descending 3rds are 6ths, etc.'''
        return GenericInterval(self.mod7)

class ChromaticInterval(music21.Music21Object):
    '''Chromatic interval class -- thinks of everything in semitones

    chromInt = chromaticInterval (-14)

    attributes:
       semitones     # -14
       undirected    # 14
       mod12         # 10
       intervalClass #  2
       cents         # -1400
    '''

    def __init__(self, value = None):
        music21.Music21Object.__init__(self)

        self.semitones = value
        self.cents     = value * 100
        self.directed = value
        self.undirected = abs(value)
        if (self.directed == 0):
            self.direction = OBLIQUE
        elif (self.directed == self.undirected):
            self.direction = ASCENDING
        else:
            self.direction = DESCENDING

        self.mod12            = self.semitones % 12
        self.simpleUndirected = self.undirected % 12
        if (self.direction == DESCENDING):
            self.simpleDirected = -1 * self.simpleUndirected
        else:
            self.simpleDirected = self.simpleUndirected

        self.intervalClass = self.mod12
        if (self.mod12 > 6):
            self.intervalClass = 12 - self.mod12

class IntervalException(Exception):
    pass

def getWrittenHigherNote(note1, note2):
    '''Given two notes, returns the higher note based on diatonic note
    numbers. Returns the note higher in pitch if the diatonic number is
    the same, or the first note if pitch is also the same.

    >>> cis = pitch.Pitch("C#")
    >>> deses = pitch.Pitch("D--")
    >>> higher = getWrittenHigherNote(cis, deses)
    >>> higher is deses
    True
    '''
    
    num1 = note1.diatonicNoteNum
    num2 = note2.diatonicNoteNum
    if num1 > num2: return note1
    elif num1 < num2: return note2
    else: return getAbsoluteHigherNote(note1, note2)

def getAbsoluteHigherNote(note1, note2):
    '''Given two notes, returns the higher note based on actual pitch.
    If both pitches are the same, returns the first note given.'''
    chromatic = generateChromatic(note1, note2)
    semitones = chromatic.semitones
    if semitones > 0: return note2
    elif semitones < 0: return note1
    else: return note1

def getWrittenLowerNote(note1, note2):
    '''Given two notes, returns the lower note based on diatonic note
    number. Returns the note lower in pitch if the diatonic number is
    the same, or the first note if pitch is also the same.'''
    num1 = note1.diatonicNoteNum
    num2 = note2.diatonicNoteNum
    if num1 < num2: return note1
    elif num1 > num2: return note2
    else: return getAbsoluteLowerNote(note1, note2)

def getAbsoluteLowerNote(note1, note2):
    '''Given two notes, returns the lower note based on actual pitch.
    If both pitches are the same, returns the first note given.'''
    chromatic = generateChromatic(note1, note2)
    semitones = chromatic.semitones
    if semitones > 0: return note1
    elif semitones < 0: return note2
    else: return note1

def generateInterval(n1, n2 = None):  
    #note to self:  what's going on with the Note() representation in help?
    '''generateInterval(Note [,Note]) -> Interval

    Generates an interval from note1 to a generic note, or from note1 
    to note2.  The generic, chromatic, and diatonic parts of the 
    interval are also generated.
    '''
    
    if n2 is None: n2 = music21.note.Note() ## this is not done in the constructor because of looping
         ## problems with tinyNotationNote
    
    gInt = generateGeneric(n1, n2)
    cInt = generateChromatic(n1, n2)
    dInt = generateDiatonic(gInt, cInt)
    Int1 = Interval(diatonic = dInt, chromatic = cInt,
                   note1 = n1, note2 = n2)
    return Int1

def generatePitch(pitch1, interval1):
    '''generatePitch(Pitch1 (or Note1), Interval1) -> Pitch
    
    Generates a Pitch object at the specified interval from the specified Pitch.  
    ''' 
    # check if interval1 is a string,
    # then convert it to interval object if necessary
    #print note1.name, "first note"
    if str(interval1) == interval1:
        #print interval1, "same name"
        interval1 = generateIntervalFromString(interval1) 
        #print interval1.name, " int name" # del me
        
    firstStep = pitch1.step
    distance = interval1.diatonic.generic.staffDistance
    #print distance, " staff distance"

    newDiatonicNumber = pitch1.diatonicNoteNum + distance
    pitch2 = pitch.Pitch()
    (newStep, newOctave) = pitch.convertDiatonicNumberToStep(newDiatonicNumber)
    pitch2.step = newStep
    pitch2.octave = newOctave
       ## at this point note2 has the right note name (step), but possibly
       ## the wrong accidental.  We fix that below

    #print note2.name, "note 2"

    interval2 = generateInterval(pitch1, pitch2)
    #print interval2.name, "interval name"
    
    halfStepsToFix = interval1.chromatic.semitones - interval2.chromatic.semitones
    pitch2.accidental = halfStepsToFix
    #print note2.name, "note name"

    return pitch2

def generateNote(note1, intervalString):
    newPitch = generatePitch(note1, intervalString)
    newNote = copy.deepcopy(note1)
    newNote.pitch = newPitch
    return newNote

def _separateIntervalFromString(string):
    generic = int(string.lstrip('PMmAd'))
    specName = string.rstrip('-0123456789')
    gInterval = GenericInterval(generic)

    # DiatonicInterval needs a GenericInterval object as well as a "specifier,"
    # a number corresponding to the interval type, as I understand it - JDR
    if gInterval.perfectable:
        specIndex = orderedPerfSpecs.index(specName)
        specifier = perfspecifiers[specIndex]
    else:
        specIndex = orderedImperfSpecs.index(specName)
        specifier = specifiers[specIndex]
        
    dInterval = DiatonicInterval(specifier, gInterval)

    # calculating number of semitones
    octaveOffset = int(abs(gInterval.staffDistance)/7)
    semitonesStart = semitonesGeneric[gInterval.simpleUndirected]
    # dictionary of semitones for major/perfect intervals

    if gInterval.perfectable:
        semitonesAdjust = semitonesAdjustPerfect[specName] # dictionary of semitones distance from perfect
    else:
        semitonesAdjust = semitonesAdjustImperf[specName] # dictionary of semitones distance from major

    semitones = (octaveOffset*12) + semitonesStart + semitonesAdjust
    if generic < 0: semitones *= -1 # want direction to be same as original direction
                                    # (automatically positive until this step)

    cInterval = ChromaticInterval(semitones)
    return (dInterval, cInterval)

def generateIntervalFromString(string):
    '''generateIntervalFromString(string) -> Interval

    Generates an interval object based on the given string,
    such as "P5", "m3", "A2".
    '''
    (dInterval, cInterval) = _separateIntervalFromString(string)
    allInterval = Interval(diatonic = dInterval, chromatic = cInterval)
    return allInterval
        
def generateChromatic(n1, n2):
    '''generateChromatic(Note, Note) -> ChromaticInterval
    
    Generates a ChromaticInterval from the two given notes.
    '''
    return ChromaticInterval(n2.midi - n1.midi)

def generateGeneric(n1, n2):
    '''generateGeneric(Note, Note) -> GenericInterval
    
    Generates a GenericInterval from the two given notes.
    '''
    staffDist = n2.diatonicNoteNum - n1.diatonicNoteNum
    genDist   = convertStaffDistanceToInterval(staffDist)
    return GenericInterval(genDist)

def convertStaffDistanceToInterval(staffDist):
    '''convertStaffDistanceToInterval(staffDistance) -> intervalDistance
    
    Returns the interval number from the given staff distance.
    '''
    if staffDist == 0:
        return 1
    elif staffDist > 0:
        return staffDist + 1
    else:
        return staffDist - 1
    
def generateDiatonic(gInt, cInt):
    '''generateDiatonic(GenericInterval, ChromaticInterval) -> DiatonicInterval
    
    Generates a DiatonicInterval from the given Generic and Chromatic intervals.
    '''
    specifier = getSpecifier(gInt, cInt)
    return DiatonicInterval(specifier, gInt)
    
def getSpecifier(gInt, cInt):
    '''getSpecifier(GenericInterval, ChromaticInterval) -> specifier
    
    Returns the specifier (i.e. MAJOR, MINOR, etc...) of the diatonic interval 
    defined by the given Generic and Chromatic intervals.
    '''
    noteVals = [None, 0, 2, 4, 5, 7, 9, 11]
    normalSemis = noteVals[gInt.simpleUndirected] + 12 * gInt.undirectedOctaves
    theseSemis  = cInt.undirected
    if gInt.perfectable:
        specifier = perfspecifiers[perfoffset + theseSemis - normalSemis]
    else:
        specifier = specifiers[majoffset + theseSemis - normalSemis]
    return specifier    

#-----------------------------------------------------------

class Test(unittest.TestCase):

    def runTest(self):
        pass
    
    def testFirst(self):       
        from music21.note import Note
        from music21.pitch import Accidental
        n1 = Note()
        n2 = Note()
        
        n1.step = "C"
        n1.octave = 4
        
        n2.step = "B"
        n2.octave = 5
        n2.accidental = Accidental("-")
        
        #int1 = interval.generateInterval(n1, n2)   # returns music21.interval.Interval object
        int1  = Interval(note1 = n1, note2 = n2)
        dInt1 = int1.diatonic   # returns same as gInt1 -- just a different way of thinking of things
        gInt1 = dInt1.generic
    
        ## TODO: rewrite all assertion code using self.assertEqual etc.
        assert gInt1.isStep == False
        assert gInt1.isSkip == True
        
        n1.accidental = Accidental("#")
        int1.reinit()
        
        cInt1 = generateChromatic(n1,n2) # returns music21.interval.ChromaticInterval object
        cInt2 = int1.chromatic        # returns same as cInt1 -- just a different way of thinking of things
        assert cInt1.semitones == cInt2.semitones
        
        assert int1.simpleNiceName == "Diminished Seventh", "Got %s" % int1.niceName
        assert int1.directedSimpleNiceName == "Ascending Diminished Seventh"
        assert int1.name == "d14"
        assert int1.specifier == DIMINISHED
        
        assert gInt1.directed == 14
        assert gInt1.undirected == 14
        assert gInt1.simpleDirected == 7
        assert gInt1.simpleUndirected == 7
        
        assert cInt1.semitones == 21, cInt1.semitones
        assert cInt1.undirected == 21
        assert cInt1.mod12 == 9
        assert cInt1.intervalClass == 3
        
        n4 = Note()
        n4.step = "D"
        n4.octave = 3
        n4.accidental = "-"
        
        ##n3 = interval.generatePitch(n4, "AA8")
        ##if n3.accidental is not None:
        ##    print n3.step, n3.accidental.name, n3.octave
        ##else:
        ##    print n3.step, n3.octave
        ##print n3.name
        ##print
     
        cI = ChromaticInterval (-14)
        assert cI.semitones==-14
        assert cI.cents==-1400
        assert cI.undirected==14
        assert cI.mod12==10
        assert cI.intervalClass==2, "Interval Class should be 2"
    
        lowB = Note()
        lowB.name = "B"
        highBb = Note()
        highBb.name = "B-"
        highBb.octave = 5
        dimOct = generateInterval(lowB, highBb)
        assert dimOct.niceName == "Diminished Octave", dimOct.niceName
    
        noteA1 = Note()
        noteA1.name = "E-"
        noteA1.octave = 4
        noteA2 = Note()
        noteA2.name = "F#"
        noteA2.octave = 5
        intervalA1 = generateInterval(noteA1, noteA2)
    
        noteA3 = Note()
        noteA3.name = "D"
        noteA3.octave = 1
    
        noteA4 = generatePitch(noteA3, intervalA1)
        assert noteA4.name == "E#"
        assert noteA4.octave == 2
        
        interval1 = generateIntervalFromString("P-5")
        
        n5 = generatePitch(n4, interval1)
        n6 = generatePitch(n4, "P-5")
        assert n5.name == "G-"
        assert n6.name == n5.name
        n7 = Note()
        n8 = generatePitch(n7, "P8")
        assert n8.name == "C"
        assert n8.octave == 5

        ## same thing using newer syntax:
        
        interval1 = Interval("P-5")
        
        n5 = generatePitch(n4, interval1)
        n6 = generatePitch(n4, "P-5")
        assert n5.name == "G-"
        assert n6.name == n5.name
        n7 = Note()
        n8 = generatePitch(n7, "P8")
        assert n8.name == "C"
        assert n8.octave == 5

        
        n9 = generatePitch(n7, "m7")  ## should be B-
        assert n9.name == "B-"
        assert n9.octave == 4
        n10 = generatePitch(n7, "dd-2")  ## should be B##
        assert n10.name == "B##"
        assert n10.octave == 3
    
        ## test getWrittenHigherNote fuctions
        (nE, nEsharp, nFflat, nF1, nF2) = (Note(), Note(), Note(), Note(), Note())
        
        nE.name      = "E"
        nEsharp.name = "E#"
        nFflat.name  = "F-"
        nF1.name     = "F"
        nF2.name     = "F"
        
        higher1 = getWrittenHigherNote(nE, nEsharp)
        higher2 = getWrittenHigherNote(nEsharp, nFflat)
        higher3 = getWrittenHigherNote(nF1, nF2)
        
        assert higher1 == nEsharp
        assert higher2 == nFflat
        assert higher3 == nF1  ### in case of ties, first is returned
        
        higher4 = getAbsoluteHigherNote(nE, nEsharp)
        higher5 = getAbsoluteHigherNote(nEsharp, nFflat)
        higher6 = getAbsoluteHigherNote(nEsharp, nF1)
        higher7 = getAbsoluteHigherNote(nF1, nEsharp)
        
        assert higher4 == nEsharp
        assert higher5 == nEsharp
        assert higher6 == nEsharp
        assert higher7 == nF1
        
        lower1 = getWrittenLowerNote(nEsharp, nE)
        lower2 = getWrittenLowerNote(nFflat, nEsharp)
        lower3 = getWrittenLowerNote(nF1, nF2)
        
        assert lower1 == nE
        assert lower2 == nEsharp
        assert lower3 == nF1  ## still returns first.
        
        lower4 = getAbsoluteLowerNote(nEsharp, nE)
        lower5 = getAbsoluteLowerNote(nFflat, nEsharp)
        lower6 = getAbsoluteLowerNote(nEsharp, nF1)
        
        assert lower4 == nE
        assert lower5 == nFflat
        assert lower6 == nEsharp
    
        middleC = Note()
        lowerC  = Note()
        lowerC.octave = 3
        descendingOctave = generateInterval(middleC, lowerC)
        assert descendingOctave.generic.simpleDirected == 1  # no descending unisons ever
        assert descendingOctave.generic.semiSimpleDirected == -8  # no descending unisons ever
        assert descendingOctave.directedName == "P-8"
        assert descendingOctave.directedSimpleName == "P1"
    
        lowerG  = Note()
        lowerG.name = "G"
        lowerG.octave = 3
        descendingFourth = generateInterval(middleC, lowerG)
        assert descendingFourth.diatonic.directedNiceName == "Descending Perfect Fourth"
        assert descendingFourth.diatonic.directedSimpleName == "P-4"
        assert descendingFourth.diatonic.simpleName == "P4"
        assert descendingFourth.diatonic.mod7 == "P5"
        assert descendingFourth.diatonic.mod7_object().niceName == "Perfect Fifth"
        assert descendingFourth.diatonic.mod7_object().diatonic.mod7_object().niceName == "Perfect Fifth"

if __name__ == "__main__":
    music21.mainTest(Test)