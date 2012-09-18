#!/usr/bin/python

## Copyright 2008 Michael Scott Cuthbert, Some Rights Reserved
## part of music21
## License: LGPL
## contact cuthbert@mit.edu for Commercial Licenses

'''
music21.note 
contains classes and functions for creating and manipulating individual notes
'''

import expressions
import copy
import string
import editorial
import common

__MOD__ = "music21.note"

stepnames = 'ABCDEFG'

class GeneralNote(object):
    '''
    A GeneralNote object is the base-class object for the Note, Rest, Unpitched, and SimpleNote, etc. objects
    It contains duration, notations, editorial, and tie fields.
    '''    


#	### commented out because it is not working due to circular imports
#        def __new__(classname, *shortcut, **arguments):
#        if len(shortcut) == 1:
#            try:
#                newnote = tinyNotation.TinyNotationNote(shortcut[0]).note
#                return newnote
#            except Exception:
#                return object.__new__(classname, *shortcut, **arguments)
#        else:
#            return object.__new__(classname, *shortcut, **arguments)
#        #doesn't actually work yet, can't import tinyNotation because of circular imports

    def __init__(self, *shortcut, **arguments):
        if len(shortcut) == 0:

            self.duration = Duration()
            self.notations = []
            self.articulations = []
            self.editorial = editorial.NoteEditorial()
            self.tie = None
            self.reinit()

    def clone(self):
        return copy.deepcopy(self)
        
    def reinit(self):
        pass
    
    def splitNoteAtPoint(self, quarterLength):
        '''
        # usage
        (note1, note2) = music21.note.GeneralNote.splitNoteAtPoint(quarterLength)
        
        # example
        N1 = music21.note.Rest()
        N1.type = "whole"
        (N2, N3) = N1.splitNoteAtPoint(3)
        print N2.type    # half
        print N2.numDots # 1
        print N3.type    # quarter
        '''
        note1 = self.clone()
        note2 = self.clone()
        d1 = Duration()
        d1.__qtrLength = quarterLength
        try: d1.setDurationFromQtrLength(quarterLength)
        except DurationException: pass
        d2 = Duration()
        d2.__qtrLength = self.duration.quarterLength - quarterLength
        try: d2.setDurationFromQtrLength(self.duration.quarterLength - quarterLength)
        except DurationException: pass
        note1.duration = d1
        note2.duration = d2
        return [note1, note2]
    
class PitchedOrUnpitched(GeneralNote):
    '''
    Parent class for methods applicable to Pitched or Unpitched notes that are not rests
    At present it contains only an extension of GeneralNote.splitNoteAtPoint that makes sure
    that the two notes are tied together.
    '''
    
    stemDirection = "unspecified"
    
    def __init__(self, **args):
        GeneralNote.__init__(self)
        self.beams = Beams()
    
    def splitNoteAtPoint(self, quarterLength):
        (note1, note2) = GeneralNote.splitNoteAtPoint(self, quarterLength)
        note1.tie = Tie("start")  #rests arent tied
        return [note1, note2]

class SimpleNote(PitchedOrUnpitched):
    '''
    Note class for notes that can be represented by a single notational unit
    Attributes:
        name :  note name (C#, B-, D, etc.)
        step :  scale step (C, B, D, etc. -- automatically set if name is set)
        octave : octave number (A4 = 440 hz)
        isNote : True
        isUnpitched: False
        isRest  : False
        freq440   : frequency if A=440 and 12ET is used (set automatically, but can be overridden)
        frequency : same as above, but should be overridden by modules that alter frequency assumptions
        pitchClass : a number from 0 (C) to 11 (B)
    '''

    _name = "C" # name could be "B-"
    _step = "C" # but step can only be "B"
    accidental = None
    octave    = 4
    isNote = True
    isUnpitched = False
    isRest = False
    
    def _getname(self): return self._name
    def _setname(self, value):
        self._name = value
        self.step = value[0]
        if len(value) > 1:
            accidentalChars = value[1:]
            self.accidental = Accidental(accidentalChars)
    
    def _getstep(self): return self._step
    def _setstep(self, value):
        if len(value) == 1:
            if value in stepnames.lower():
                self._step = value.capitalize()
            elif value in stepnames:
                self._step = value
            else:
                raise NoteException("Cannot make a step out of %s", value)
        else:
            raise NoteException("Steps should be 1 letter long, not %s", value)
    
    name = property(_getname, _setname)
    step = property(_getstep, _setstep)

    _overridden_freq440 = None
    _twelfth_root_of_two = 2.0 ** (1.0/12)

    def _getfreq440(self):
        if self._overridden_freq440:
            return self._overridden_freq440
        else:
            A4offset = self.midiNote() - 69
            return 440.0 * (self._twelfth_root_of_two ** A4offset)
            
    def _setfreq440(self, value):
        self._overridden_freq440 = value

    freq440 = property(_getfreq440, _setfreq440)
    frequency = freq440 # override this for non 440 or not ET

    def _preDurationLily(self):
        '''
        Method to return all the lilypond information that appears before the duration number.
        Is the same for simple and complex notes.
        '''
        baseName = ""
        baseName += self.editorial.lilyStart()
        baseName += self.step.lower()
        if (self.accidental):
            baseName += self.accidental.lilyName
        elif (self.editorial.ficta is not None):
            baseName += self.editorial.ficta.lilyName
        octaveModChars = ""
        if (self.octave < 3):
            correctedOctave = 3 - self.octave
            octaveModChars = ',' * correctedOctave #  C2 = c,  C1 = c,,
        else:
            correctedOctave = self.octave - 3
            octaveModChars  = '\'' * correctedOctave # C4 = c', C5 = c''  etc.
        baseName += octaveModChars
        if (self.editorial.ficta is not None):
            baseName += "!"  # always display ficta
        return baseName

        
    def _lilyName(self):
        '''
        The name of the note as it would appear in Lilypond format.
        '''
        baseName = self._preDurationLily()
        baseName += self.duration.lilySimple
        if (self.tie is not None):
            if (self.tie.type != "stop"):
                baseName += "~"
        if (self.notations):
            for thisNotation in self.notations:
                if dir(thisNotation).count('lily') > 0:
                    baseName += " " + thisNotation.lily

        return baseName

    lilyName = property(_lilyName)

    def appendDuration(self, durationObject):
        '''
        Sets the duration of the note to the supplied Duration object
        '''
        self.duration = durationObject
    
    def addAccidentalObj(self, accidental):
        '''
        Adds an accidental to the Note, given as an Accidental object.
        Also alters the name of the note
        
        N1 = music21.note.Note()
        N1.step = "D"
        print N1.name # D
        S1 = music21.note.Accidental("sharp")
        N1.addAccidentalObj(S1)
        print N1.name # D#
        '''
        
        self.accidental = accidental
        self.name = self.step + accidental.modifier

    def addAccidentalStr(self, accstring):
        '''
        Adds an accidental to the Note if given a string
        
        Valid strings are: 
            natural, sharp, double-sharp, flat, double-flat
            0, 1, 2, -1, -2
            n, #, ##, -, --
        To add more exotic accidentals (half-flats, triple sharps, etc.) use addAccidentalObj
        after creating the appropriate accidental object.
        '''
        stringAccs = ['natural', 'sharp', 'double-sharp', 'flat', 'double-flat']
        numAccs = ['0', '1', '2', '-1', '-2']
        symAccs = ['n', '#', '##', '-', '--']
 
        if accstring in stringAccs:
            accstring = accstring
            self.addAccidentalObj(Accidental(accstring))
        elif accstring in numAccs:
            ind = numAccs.index(accstring)
            accstring = stringAccs[ind]
            self.addAccidentalObj(Accidental(accstring))
        elif accstring in symAccs:
            ind = symAccs.index(accstring)
            accstring = stringAccs[ind]
            self.addAccidentalObj(Accidental(accstring))
        else:
            print accstring + ' is not a valid accidental'

    def diatonicNoteNum(self):
        '''
        Returns an int that uniquely identifies the note, ignoring accidentals.
        
        C4 (middleC) = 28, C#4 = 28, D-4 = 29, D4 = 29, etc.
        
        Numbers can be negative for very low notes.        
        '''
        if ['C','D','E','F','G','A','B'].count(self.step.upper()):
            noteNumber = ['C','D','E','F','G','A','B'].index(self.step.upper())
            return (noteNumber + (7 * self.octave))
        else:
            raise NoteException("Could not find " + self.step + " in the index of notes") 

    def midiNote(self):
        '''
        Returns the note's midi number.  
        
        C4 (middle C) = 60, C#4 = 61, D-4 = 61, D4 = 62; A4 = 69
        '''
        notes = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
        noteVals = [0, 2, 4, 5, 7, 9, 11]
        ind = notes.index(self.step.upper())
        noteVal = noteVals[ind]
        octa = self.octave
        if self.accidental != None:
            accVal = int(self.accidental.alter)
        else:
            accVal = 0
        return (accVal + noteVal + (octa + 1) * 12)

    def _getPitchClass(self):
        mn = self.midiNote()
        pc = mn % 12
        return pc

    pitchClass = property(_getPitchClass)

class ComplexNote(SimpleNote):
    '''
    A ComplexNote is a "Note" that knows both its total duration
    and how to express itself as a set of tied notes of different
    lengths.  For instance, a note of 2.5 quarters in length could
    be half tied to eighth or dotted quarter tied to quarter.
    
    A ComplexNote will eventually be smart enough that if given a duration in quarters
    it will try to figure out a way to express itself as best it can if
    it needs to be represented on page.  It does not know this now.


    '''

    def __init__(self, *shortcut, **arguments):
        SimpleNote.__init__(self)
        self.componentDurations = []
        self.durationLinkages = []
        self.duration = ComplexDuration(components = self.componentDurations,
                                        linkages = self.durationLinkages)

    def appendDuration(self, durationObject):
        '''
        appendDuration(Duration) #
        
        adds a durationObject to the componentDurations list        
        '''
        self.componentDurations.append(durationObject)
    
    def clearDurations(self):
        '''
        clears all the durations stored in the note.
        After performing this, it's probably not wise to print the note until at least one Duration is added
        '''
        
        self.componentDurations = []
        self.durationLinkages = []
        self.duration = ComplexDuration(components = self.componentDurations,
                                        linkages = self.durationLinkages)

    def splitAtDurations(self):
        '''
        Takes a ComplexNote and returns a list of notes with only a single
        Duration each.
        
        Note that what are returned are also technically ComplexNotes but can
        be used exactly like SimpleNotes in that they have a single duration
        attribute.
        '''
        returnNotes = []
        if len(self.componentDurations) == 0:
            returnNotes[0] = self.clone()  ## is already a simpleNote
        elif len(self.componentDurations) == (len(self.durationLinkages) - 1):
            for i in range(len(self.componentDurations)):
                tempNote = self.clone()            
                tempNote.clearDurations()
                tempNote.duration = self.componentDurations[i]
                if i != (len(self.componentDurations) - 1):
                    tempNote.tie = self.durationLinkages[i]                
                    ## last note just gets the tie of the original ComplexNote
                returnNotes.append(tempNote)
        else:
            for i in range(len(self.componentDurations)):
                tempNote = self.clone()            
                tempNote.clearDurations()
                tempNote.duration = self.componentDurations[i]
                if i != (len(self.componentDurations) - 1):
                    tempNote.tie = Tie()
                else:
                    ## last note just gets the tie of the original ComplexNote
                    if self.tie is None:
                        self.tie = Tie("stop")
                returnNotes.append(tempNote)                
        return returnNotes

    def _lilyName(self):
        '''
        The name of the note as it would appear in Lilypond format.
        '''
        allNames = ""
        baseName = self._preDurationLily()
        if hasattr(self.duration, "components") and len(self.duration.components) > 0:
            for i in range(0, len(self.duration.components)):
                thisDuration = self.duration.components[i]            
                allNames += baseName
                allNames += thisDuration.lilySimple
                if (i != len(self.duration.components) - 1):
                    allNames += "~"
                    allNames += " "
        else:
            allNames += baseName
            allNames += self.duration.lilySimple
            
        if (self.tie is not None):
            if (self.tie.type != "stop"):
                allNames += "~"
        if (self.notations):
            for thisNotation in self.notations:
                if dir(thisNotation).count('lily') > 0:
                    allNames += " " + thisNotation.lily

        return allNames

    lilyName = property(_lilyName)

'''
Note is an alias for ComplexNote.  We suggest using Note() in all code 
since future Note() objects will be backwards compatible but perhaps add additional features.
'''
Note = ComplexNote

class Unpitched(PitchedOrUnpitched):
    '''
    General class of unpitched objects which appear at different places
    on the staff.  Examples: percussion notation
    '''
    
    displayStep = "C"
    displayOctave = 4
    isNote = False
    isUnpitched = True
    isRest = False

class Rest(GeneralNote):
    '''General rest class'''
    isNote = False
    isUnpitched = False
    isRest = True
    name = "rest"

    def __lilyName(self):
        '''The name of the rest as it would appear in Lilypond format.'''
        baseName = "r"
        baseName += self.duration.lilySimple        
        return baseName

    lilyName = property(__lilyName)

class Accidental(object):
    
    '''Accidental class.
    '''

    alter     = 0.0     # semitones to alter step
    #alterFrac = [0,0]   # fractional alteration (e.g., 1/6); fraction class in 2.6
    #alterExp  = [0,0,0] # exponental alteration (e.g., [2,3,19] = 2**(3/19))
    #alterHarm = 0       # altered according to a harmonic
    displayType = "normal"  # display if first in measure; other valid terms:
                            # "always", "never", "unless-repeated" (show always unless
                            # the immedately preceding note is the same), "even-tied"
                            # (stronger than always: shows even if it is tied to the
                            # previous note
    displayStatus = ""   # given the displayType, should this accidental be displayed?
                            # can be "yes", "no" or "" for unsure.  For contexts where
                            # the next program down the line cannot evaluate displayType
    displayStyle = "normal" # "parentheses", "bracket", "both"
    displaySize  = "full"   # "cue", "large", or a percentage
    modifier = ''

    def __init__(self, name='natural'):
        self.setAccidental(name)
        
    def setAccidental(self, name):
        if name == 'natural' or name == "n":
            self.name = 'natural'
            self.alter = 0.0
            self.modifier = ''
        elif name == 'sharp' or name == "#" or name == "is":
            self.name = 'sharp'
            self.alter = 1.0
            self.modifier = '#'
        elif name == 'double-sharp' or name == "##" or name == "isis":
            self.name = 'double-sharp'
            self.alter = 2.0
            self.modifier = '##'
        elif name == 'flat' or name == "-" or name == "es":
            self.name = 'flat'
            self.alter = -1.0
            self.modifier = '-'
        elif name == 'double-flat' or name == "--" or name == "eses":
            self.name = 'double-flat'
            self.alter = -2.0
            self.modifier = '--'
        
        elif name == 'half-sharp' or name == 'quarter-sharp' or name == 'ih':
            self.name = 'half-sharp'
            self.alter = 0.5
        elif name == 'one-and-a-half-sharp' or name == 'three-quarter-sharp' \
             or name == 'three-quarters-sharp' or name == 'isih':
            self.name = 'one-and-a-half-sharp'
            self.alter = 1.5  
        elif name == 'half-flat' or name == 'quarter-flat' or name == 'eh':
            self.name = 'half-flat'
            self.alter = -0.5
        elif name == 'one-and-a-half-flat' or name == 'three-quarter-flat' \
             or name == 'three-quarters-flat' or name == 'eseh':
            self.name = 'one-and-a-half-flat'
            self.alter = -1.5
        else:
            raise Exception(name + ' is not a supported accidental type')
        
        
    def __getLily(self):
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
        
        if self.displayStatus == "yes" or self.displayType == "always" \
           or self.displayType == "even-tied":
            lilyRet += "!"
        
        if self.displayStyle == "parentheses" or self.displayStyle == "both":
            lilyRet += "?"
            ## no brackets for now
        return lilyRet
        
    def __setLily(self, value):
        if (value.count("isis") > 0): self.setAccidental("double-sharp")
        elif (value.count("eses") > 0): self.setAccidental("double-flat")
        elif (value.count("isih") > 0): self.setAccidental("one-and-a-half-sharp")
        elif (value.count("eseh") > 0): self.setAccidental("one-and-a-half-flat")
        elif (value.count("is") > 0): self.setAccidental("sharp")
        elif (value.count("es") > 0): self.setAccidental("flat")
        elif (value.count("ih") > 0): self.setAccidental("half-sharp")
        elif (value.count("eh") > 0): self.setAccidental("half-flat")

        if value.count("!") > 0:
            self.displayType = "always"
            
        if value.count("?") > 0:
            self.displayStyle = "parentheses"
        
    lilyName = property(__getLily, __setLily)

class NoteException(Exception):
    pass

class Tie(object):
    '''tie class: add to notes that are tied to other notes

    note1.tie = Tie("start")
    note1.tieStyle = "normal" # could be dotted or dashed
    print note1.tie.type # prints start

    Differences from MusicXML:
       notes do not need to know if they are tied from a
       previous note.  i.e., you can tie n1 to n2 just with
       a tie start on n1.  However, if you want proper musicXML output
       you need a tie stop on n2

       one tie with "continue" implies tied from and tied to

       optional (to know what notes are next:)
          .to = note()   # not implimented yet, b/c of garbage coll.
          .from = note()

    (question: should notes be able to be tied to multiple notes
    for the case where a single note is tied both voices of a
    two-note-head unison?)
    '''

    def __init__(self, tievalue = "start"):
        self.type = tievalue

    ### NOTE: READ UP ON weak references BEFORE adding .to and .from
    ### THESE MUST BE WEAK otherwise garbage collection will not take place properly



class Duration(object):
    '''duration class: adds duration objects to notes, rests, etc.'''
    
    type      = ""         # graphic representation of the duration w/o dots
    ## type can be any string not just common ones or "unknown" or "unrepresentable"

    dots      = 0.0          # how many dots; a float for Crumb dots (1/2 dots)
    isComplex = False
    
    typeToDuration = {'longa': 16.0, 'breve': 8.0, 'whole': 4.0,
                      'half': 2.0, 'quarter': 1.0, 'eighth': 0.5,
                      '16th': 0.25, '32nd': 0.125,
                      '64th': 0.0625, '128th': 0.03125, '256th': 0.015625} 
    typeFromNumDict = {'1': 'whole', '2': 'half', '4': 'quarter',
                       '8': 'eighth', '16': '16th', '32': '32nd', '64': '64th', '128': '128th',
                       '256': '256th'}
                   
    __qtrLength = 0.0

    def __init__(self):
        self.dotGroups = []  # rarely used: dotted-dotted notes; e.g. dotted-dotted half in 9/8
                             # list element so that someone could conceivably have dotted-dotted-dotted groups
        self.tuplets   = []
        self.timeInfo  = []  # the timeInfo from the noteStream object (q.v.) 
    
    def getQuarterLength(self):
        '''determine the length in quarter notes from current information'''

        if (self.__qtrLength):
            return self.__qtrLength
        
        if (self.typeToDuration.has_key(self.type)):
            durationFromType = self.typeToDuration[self.type]
        else:
            raise KeyError, "No key in typeToDuration for " + self.type

        if (durationFromType == 0):
            raise ("Error: no correct Duration for " + self.type)
        qtrLength = 0.0
        qtrLength = durationFromType * common.dotMultiplier(self.dots)

        ###
        if (len(self.dotGroups) > 0):
            for thisDot in self.dotGroups:
                qtrLength *= common.dotMultiplier(thisDot)

        if (len(self.tuplets) > 0):
            for thisTuplet in self.tuplets:
                qtrLength *= thisTuplet.tupletMultiplier()

        return qtrLength

    def setQuarterLength(self, value):
        '''Set the quarter note length to the specified value'''
        self.__qtrLength = value


    # quarterLength is a special attribute: if unknown it gets automatically computed
    quarterLength = property(getQuarterLength, setQuarterLength)
    
    def setDurationFromQtrLength(self, qL):
        ### rewrite using common.decimalToTuplet

        noDotQL = qL * (2.0/3)
        # JR  -- assumes dots are of 14th-cent. nested form:
        # MSC -- Do not assume that.  Or if they are, set:
        #        note.duration.dots = 1
        #        note.duration.dotGroups = [1]
        # test double dots with qL * 
        noDotQL2 = noDotQL * (2.0/3)

        ## look for functions already defined and reuse them
        noDblDotQL = qL / common.dotMultiplier(2.0)
        noTrpDotQL = qL / common.dotMultiplier(3.0)
        # etc...

        ## clear old data
        self.type = ""
        self.dots = 0
        self.dotGroups = []
        self.tuplets = []
        
        if (common.isPowerOfTwo(qL)):
            tempType = self.getTypeFromQtrLength(qL)
            if (tempType): self.type = tempType
            else: raise DurationException("couldnt get type from Power of Two: %f" % qL)

        elif (common.isPowerOfTwo(noDotQL)):
            self.dots = 1
            tempType = self.getTypeFromQtrLength(noDotQL)
            if (tempType): self.type = tempType
            else: raise DurationException

        elif (common.isPowerOfTwo(noDblDotQL)):
            self.dots = 2
            tempType = self.getTypeFromQtrLength(noDblDotQL)
            if (tempType): self.type = tempType
            else: raise DurationException
            
        elif (common.isPowerOfTwo(noTrpDotQL)):
            self.dots = 3
            tempType = self.getTypeFromQtrLength(noTrpDotQL)
            if (tempType): self.type = tempType
            else: raise DurationException

            ## add code for 4 dots...

        elif (common.isPowerOfTwo(noDotQL2)):  # medieval dotted dotted notes
            self.dots = 1
            self.dotGroups = [1]
            tempType = self.getTypeFromQtrLength(noDotQL2)
            if (tempType): self.type = tempType
            else: raise DurationException

        #(check for simple tuplets, but don't spend too much time on it
        #python2.6 will have a Fraction class which will make finding the
        #closest tuplet representation much easier)

        else: raise DurationException("couldnt get type from Length: %f" % qL)

    def getTypeFromQtrLength(self, qL):
        if common.almostEquals(qL, 64.0): return 'duplex-maxima'
        if common.almostEquals(qL, 32.0): return 'maxima'
        if common.almostEquals(qL, 16.0): return 'longa'
        if common.almostEquals(qL, 8.0):  return 'breve'
        if common.almostEquals(qL, 4.0):  return 'whole'
        if common.almostEquals(qL, 2.0):  return 'half'
        if common.almostEquals(qL, 1.0):  return 'quarter'
        if common.almostEquals(qL, 0.5):  return 'eighth'
        if common.almostEquals(qL, 0.25): return '16th'
        if common.almostEquals(qL, 0.125): return '32nd'
        if common.almostEquals(qL, 0.0625): return '64th'
        if common.almostEquals(qL, 0.03125): return '128th'
        if common.almostEquals(qL, 0.015625): return '256th'
        
    ### given "4" set quarter, etc.
    def typeFromNum(self, typeNum):
        if (self.typeFromNumDict.has_key(str(typeNum))):
            self.type = self.typeFromNumDict[str(typeNum)]
        else:
            raise DurationException("cannot find number %s" % str(typeNum))
        return self.type

    def numFromType(self):
        ty = self.type
        if   ty == "whole"     : return 1
        elif ty == "half"      : return 2
        elif ty == "quarter"   : return 4
        elif ty == "eighth"    : return 8
        elif ty == "16th" : return 16
        elif ty == "32nd" : return 32
        elif ty == "64th" : return 64
        else:
            raise DurationException("Could not determine durationNumber from " + ty)

    def ordinalNumFromType(self):
        ty = self.type
        if   ty == "longa"     : return 2
        elif ty == "breve"     : return 3
        elif ty == "whole"     : return 4
        elif ty == "half"      : return 5
        elif ty == "quarter"   : return 6
        elif ty == "eighth"    : return 7
        elif ty == "16th" : return 8
        elif ty == "32nd" : return 9
        elif ty == "64th" : return 10
        else:
            raise DurationException("Could not determine durationNumber from " + ty)

    ordinalTypeFromNum = ["duplex-maxima", "maxima", "longa", "breve", "whole", "half", "quarter", "eighth", "16th", "32nd", "64th", "128th", "256th", "512th", "1024th"]

        
    def clone(self):
        return copy.deepcopy(self)

    def __lilySimple(self):
        '''Simple lily duration: does not include tuplets'''
        number_type = self.numFromType()
        dots = "." * int(self.dots)
        return (str(number_type) + dots)
        
    lilySimple = property(__lilySimple)

    def aggregateTupletRatio(self):
        '''say you have 3:2 under a 5:4.  Returns (15,8).

        Needed for MusicXML time-modification 
        '''
        
        currentMultiplier = 1
        if (len(self.tuplets) > 0):
            for thisTuplet in self.tuplets:
                currentMultiplier *= thisTuplet.tupletMultiplier()
        return decimalToTuplet(1.0/currentMultiplier)


class ComplexDuration(Duration):
    '''A ComplexDuration can calculate its total length from each of its component
    durations.  An example of a complex duration is a quarter note tied to a 16th note.
    It is not expressable as a single note value, but we can give its length in 
    quarter notes, etc.
    '''

    def __init__(self, *shortcut, **arguments):
        Duration.__init__(self)
        if "components" in arguments:
            self.components = arguments["components"]
        else:
            self.components = []
        
        ## linkages are a list of things used to connect durations.  If undefined,
        ## Ties are used.  Other sorts of things could be dotted-ties, arrows, none, etc.
        ## As of Sep. 2008 -- not used.
        if "linkages" in arguments:
            self.linkages = arguments["linkages"]
        else:
            self.linkages = []
        
               
    def _isComplex(self):
        if len(self.components) > 1: return True
        else: return False
        
    isComplex = property(_isComplex)
    __qtrLength = 0.0
    
    def getQuarterLength(self):
        if (self.__qtrLength):
            return self.__qtrLength

        if (len(self.components) > 0):
            currentLength = 0.0
            for thisDuration in self.components:
                currentLength += thisDuration.quarterLength
            return currentLength
        else:
            return Duration.getQuarterLength(self)
        
    def setQuarterLength(self, value):
        '''Set the quarter note length to the specified value'''
        self.__qtrLength = value

    quarterLength = property(getQuarterLength, setQuarterLength)         
    
    def transferDurationToComponent0(self):
        '''transfers all the relevant information from the main ComplexDuration
        object to the first component object.  Necessary before the duration
        can be sliced up.
        
        Usage:
        d1 = ComplexDuration()
        d1.type = "half"
        d1.dots = 1
        d1.quarterLength  # 3.0
        d1.components # []
        d1.transferDurationToComponent0()
        d1.components[0].type # "half"
        d1.components[0].dots # 1.0
        d1.sliceComponentAtPosition(2)
        for thisDur in d1.components:
           print thisDur.type, thisDur.dots
           ##  half    0
           ##  quarter 0
        
        clears anything in components (but not linkages) first
        '''
        
        del(self.components[:]) # keeps linkage in any notes that use this duration
        newDur = Duration()
        newDur.type = self.type
        newDur.dots = self.dots
        newDur.dotGroups = copy.copy(self.dotGroups)
        newDur.tuplets = copy.deepcopy(self.tuplets)
        newDur.timeInfo = copy.deepcopy(self.timeInfo)
        self.components.append(newDur)
    
    def componentIndexAtQtrPosition(self, quarterPosition):
        '''returns the index number of the duration component sounding at
        the given quarter position.
        
        e.g. given d1, d2, d3 as 3 quarter notes and
        self.components = [d1, d2, d3]
        then
        self.getComponentIndexAtQtrPosition(1.5) == d2
        self.getComponentIndexAtQtrPosition(2.0) == d3
        self.getComponentIndexAtQtrPosition(2.5) == d3
        '''
        
        if self.components == []:
            raise DurationException("Need components to run getComponentIndexAtQtrPosition")
        elif quarterPosition > self.quarterLength:
            raise DurationException("quarterPosition is after the end of the duration")
        elif quarterPosition < 0:
            raise DurationException("Okay, now you're just being silly, with negative positions")
        
        if common.almostEquals(quarterPosition, 0):
            return self.components[0]
        elif common.almostEquals(quarterPosition, self.quarterLength):
            return self.components[-1]
        
        currentPosition = 0.0

        for i in range(len(self.components)):
            currentPosition += self.components[i].quarterLength
            if currentPosition > quarterPosition and not common.almostEquals(currentPosition, quarterPosition):
                return i
        
        raise DurationException("Okay, so how did this happen?")
        
    def componentStartTime(self, componentIndex):
        currentPosition = 0.0
        for i in range(0, componentIndex):
            currentPosition += self.components[i].quarterLength
        return currentPosition
           
    def sliceComponentAtPosition(self, quarterPosition):
        sliceIndex = self.componentIndexAtQtrPosition(quarterPosition)
        sliceDuration = self.components[sliceIndex]
        durationStartTime = self.componentStartTime(sliceIndex)
        slicePoint = quarterPosition - durationStartTime
        remainder = sliceDuration.quarterLength - slicePoint
        d1 = Duration()
        d1.__qtrLength = slicePoint
        try: d1.setDurationFromQtrLength(slicePoint)
        except DurationException: pass
        d2 = Duration()
        d2.__qtrLength = remainder
        try: d2.setDurationFromQtrLength(remainder)
        except DurationException: pass
        self.components[sliceIndex:sliceIndex + 1] = [d1, d2]
        
class GraceDuration(ComplexDuration):
    '''
    defines durations for Acciaccature (grace notes)
    '''
    pass

class LongGraceDuration(ComplexDuration):
    '''
    defines durations for unstemmed, long grace notes
    '''
    pass

class AppogiaturaStartDuration(ComplexDuration):
    pass

class AppogiaturaStopDuration(ComplexDuration):
    pass

        
class DurationException(Exception):
    pass

class QuarterNote(ComplexDuration):
    type = "quarter"
    __qtrLength = 1


class Tuplet(object):
    '''tuplet class: creates tuplet objects which modify duration objects

    note that this is a duration modifier.  We should also have a tupletGroup
    object that groups note objects into larger groups.
    '''

    def __init__(self):
        self.tupletId            = 0        # necessary for some complex tuplets, interrupted, for instance
        self.nestedLevel         = 1

        self.numberNotesActual   = 3.0
        self.durationActual      = Duration() 
        self.durationActual.type = "eighth"

        self.numberNotesNormal   = 2.0
        self.durationNormal      = Duration()
        self.durationNormal.type = "eighth"

        self.nestedInside       = ""  # could be a tuplet object
        self.type               = ""  # "start" to imply start of tuplet; "stop" to end; optional; needed for MusicXML
        self.tupletActualShow   = "number" # could be "number","type", or "none"
        self.tupletNormalShow   = "none"

    def _setTupletActual(self, tupList = []):
        [self.numberNotesActual, self.durationActual] = tupList   
    def _getTupletActual(self):
        return [self.numberNotesActual, self.durationActual]
    def _setTupletNormal(self, tupList = []):
        [self.numberNotesNormal, self.durationNormal] = tupList    
    def _getTupletNormal(self):
        return [self.numberNotesNormal, self.durationNormal]
    tupletActual = property(_getTupletActual, _setTupletActual)
    tupletNormal = property(_getTupletNormal, _setTupletNormal)
    
    def tupletMultiplier(self):
        '''
        tupletMultiplier(3qtr in the place of 2qtr) = 0.6666
        '''
        (numA,durA) = self.tupletActual
        lengthActual = durA.quarterLength
        return (self.totalTupletLength() / float(numA*lengthActual))

    def totalTupletLength(self):
        '''the total length in quarters of the total tuplet as defined
        
        totalTupletLength(3qtr in the place of 2qtr) = 2.0
        '''
        
        (numN,durN) = self.tupletNormal
        lengthBottom = 0.0
        lengthBottom = durN.quarterLength
        return (numN*lengthBottom);

class Beams(object):
    
    def __init__(self):
        self.beamsList = []
        self.feathered = False
        
    def addNext(self, type = None, direction = None):
        self.beamsList.append(Beam(type, direction))

class Beam(object):

    def __init__(self, type = None, direction = None):
        self.type = type # start, stop, partial
        self.direction = direction # left or right for partial
        self.independentAngle = None


def noteFromDiatonicNumber(number):
    octave = int(number / 7)
    noteIndex = number % 7
    noteNames = ['C','D','E','F','G','A','B']
    thisName = noteNames[noteIndex]
    note1 = Note()
    note1.octave = octave
    note1.name = thisName
    return note1


def test():
#    note1 = Note("c#1")
#    assert note1.duration.quarterLength == 4
#    note1.duration.dots = 1
#    assert note1.duration.quarterLength == 6
#    note1.duration.type = "eighth"
#    assert note1.duration.quarterLength == 0.75
#    assert note1.octave == 4
#    assert note1.step == "C"
    note2 = Rest()
    assert note2.isRest is True
    note3 = Note()
    note3.name = "B-"
    assert note3.accidental is not None
    assert note3.accidental.name == "flat"
    assert note3.pitchClass == 10

    a5 = Note()
    a5.name = "A"
    a5.octave = 5
    assert common.almostEquals(a5.freq440, 880.0) is True
    assert a5.pitchClass == 9

def complexTest():
    note1 = ComplexNote()
    d1 = Duration()
    d1.type = "whole"
    d2 = Duration()
    d2.type = "quarter"
    note1.appendDuration(d1)
    note1.appendDuration(d2)
    assert common.almostEquals(note1.duration.quarterLength, 5.0)
    assert note1.duration.componentIndexAtQtrPosition(2) == 0    
    assert note1.duration.componentIndexAtQtrPosition(4) == 1    
    assert note1.duration.componentIndexAtQtrPosition(4.5) == 1    
    note1.duration.sliceComponentAtPosition(1.0)
    print note1.lilyName
    for thisNote in (note1.splitAtDurations()):
        print thisNote.lilyName
    
def tupletTest():
    note1 = Note()
    note1.duration.type = "quarter"

    ### create a tuplet with 5 dotted eighths in the place of 3 double-dotted eighths
    dur1 = Duration()
    dur1.type = "eighth"
    dur1.dots = 1

    dur2 = Duration()
    dur2.type = "eighth"
    dur2.dots = 2

    tup1 = Tuplet()
    tup1.tupletActual = [5,dur1]
    tup1.tupletNormal = [3,dur2]

    print "For 5 dotted eighths in the place of 3 double-dotted eighths"
    print "Total tuplet length is",
    print tup1.totalTupletLength(),
    assert common.almostEquals(tup1.totalTupletLength(), 2.625)

    print "quarter notes.\nEach note is",
    print tup1.tupletMultiplier(),
    assert common.almostEquals(tup1.tupletMultiplier(), 0.7)
    print "times as long as it would normally be."
    
    ### create a new dotted quarter and apply the tuplet to it
    dur3 = Duration()
    dur3.type = "quarter"
    dur3.dots = 1
    dur3.tuplets = [tup1]
    print "So a tuplet-dotted-quarter's length is",
    print dur3.getQuarterLength(),
    assert common.almostEquals(dur3.getQuarterLength(), 1.05)
    print "quarter notes"

    ### create a tuplet with 3 sixteenths in the place of 2 sixteenths
    tup2 = Tuplet()
    dur4 = Duration()
    dur4.type = "16th"
    tup2.tupletActual = [3, dur4]
    tup2.tupletNormal = [2, dur4]

    print "\nTup2 (3 sixteenths in the place of 2 16ths):\nTotal tuplet length is",
    print tup2.totalTupletLength(),
    assert common.almostEquals(tup2.totalTupletLength(), 0.5)
    print "quarter notes.\nEach note is",
    print tup2.tupletMultiplier(),
    assert common.almostEquals(tup2.tupletMultiplier(), 0.66666666667)

    print "times as long as it would normally be."

    dur3.tuplets = [tup1,tup2]
    print "So a tuplet-dotted-quarter's length under both tuplets is",
    print dur3.getQuarterLength(),
    assert common.almostEquals(dur3.getQuarterLength(), 0.7)
    print "quarter notes"


if (__name__ == "__main__"):
    test()
