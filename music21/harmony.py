# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         harmony.py
# Purpose:      music21 classes for representing harmonies and chord symbols
#
# Authors:      Beth Hadley
#               Christopher Ariza
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''
An object representation of harmony, as encountered as chord symbols or other chord representations with a defined root.
'''

import unittest

import music21
from music21 import common
from music21 import pitch
from music21 import roman
from music21 import interval
from music21 import chord


import re
import copy

from music21 import environment
from music21.figuredBass import realizerScale


_MOD = "harmony.py"
environLocal = environment.Environment(_MOD)
#-------------------------------------------------------------------------------
# kind values defined in musicxml

# <xs:enumeration value="major"/>
# <xs:enumeration value="minor"/>
# <xs:enumeration value="augmented"/>
# <xs:enumeration value="diminished"/>
# <xs:enumeration value="dominant"/>
# <xs:enumeration value="major-seventh"/>
# <xs:enumeration value="minor-seventh"/>
# <xs:enumeration value="diminished-seventh"/>
# <xs:enumeration value="augmented-seventh"/>
# <xs:enumeration value="half-diminished"/>
# <xs:enumeration value="major-minor"/>
# <xs:enumeration value="major-sixth"/>
# <xs:enumeration value="minor-sixth"/>
# <xs:enumeration value="dominant-ninth"/>
# <xs:enumeration value="major-ninth"/>
# <xs:enumeration value="minor-ninth"/>
# <xs:enumeration value="dominant-11th"/>
# <xs:enumeration value="major-11th"/>
# <xs:enumeration value="minor-11th"/>
# <xs:enumeration value="dominant-13th"/>
# <xs:enumeration value="major-13th"/>
# <xs:enumeration value="minor-13th"/>
# <xs:enumeration value="suspended-second"/>
# <xs:enumeration value="suspended-fourth"/>
# <xs:enumeration value="Neapolitan"/>
# <xs:enumeration value="Italian"/>
# <xs:enumeration value="French"/>
# <xs:enumeration value="German"/>
# <xs:enumeration value="pedal"/>
# <xs:enumeration value="power"/>
# <xs:enumeration value="Tristan"/>
# <xs:enumeration value="other"/>
# <xs:enumeration value="none"/>
CHORD_TYPES = {
             'major': ['', 'Maj'] , 
             'minor': ['m', '-', 'min'] ,
             'augmented' : ['+', '#5'] , 
             'diminished' : ['dim', 'o'] ,
             'dominant' : ['7'],
             'major-seventh' : [ 'M7', 'Maj7'],
             'minor-seventh' : ['m7' , 'min7'] ,
             'diminished-seventh' : ['dim7' , 'o7'] ,
             'augmented-seventh' : ['7+', '7#5'] ,
             'half-diminished' : ['m7b5'] ,
             'major-minor' : ['mMaj7'] , 
             'major-sixth' : ['6'] ,
             'minor-sixth' : ['m6', 'min6'] ,
             'dominant-ninth' : ['9'] ,
             'major-ninth' : ['M9' , 'Maj9'] ,
             'minor-ninth' : ['m9', 'min9'] ,
             'dominant-11th' : ['11'] ,
             'major-11th' : ['M11' , 'Maj11'] ,
             'minor-11th' : ['m11' , 'min11'] ,
             'dominant-13th' : ['13'] ,
             'major-13th' : ['M13', 'Maj13'] ,
             'minor-13th' : ['m13' , 'min13'] ,
             'suspended-second' : ['sus2'] ,
             'suspended-fourth' : ['sus' , 'sus4'] ,
             'Neapolitan' : ['N6'] ,
             'Italian' : ['It+6'] ,
             'French' : ['Fr+6'] ,
             'German' : ['Gr+6'] ,
             'pedal' : ['pedal'] ,
             'power' : ['power'] ,
             'Tristan' : ['tristan']
             }

'''XML DESCRIPTION OF ABOVE TYPES OF CHORDS:
Triads:
    major (major third, perfect fifth) [C]
    minor (minor third, perfect fifth) [Cm]
    augmented (major third, augmented fifth) [C+]
    diminished (minor third, diminished fifth) [Cdim]
Sevenths:
    dominant (major triad, minor seventh) [C7]
    major-seventh (major triad, major seventh) [CMaj7]
    minor-seventh (minor triad, minor seventh) [Cm7]
    diminished-seventh (diminished triad, diminished seventh) [Cdim7]
    augmented-seventh (augmented triad, minor seventh) [C7+]
    half-diminished (diminished triad, minor seventh) [Cm7b5]
    major-minor (minor triad, major seventh) [CmMaj7]
Sixths:
    major-sixth (major triad, added sixth) [C6]
    minor-sixth (minor triad, added sixth) [Cm6]
Ninths:
    dominant-ninth (dominant-seventh, major ninth) [C9]
    major-ninth (major-seventh, major ninth) [CMaj9]
    minor-ninth (minor-seventh, major ninth) [Cm9]
11ths (usually as the basis for alteration):
    dominant-11th (dominant-ninth, perfect 11th) [C9]
    major-11th (major-ninth, perfect 11th) [CMaj9]
    minor-11th (minor-ninth, perfect 11th) [Cm9]
13ths (usually as the basis for alteration):
    dominant-13th (dominant-11th, major 13th) [C13]
    major-13th (major-11th, major 13th) [CMaj13]
    minor-13th (minor-11th, major 13th) [Cm13]
Suspended:
    suspended-second (major second, perfect fifth) [Csus2]
    suspended-fourth (perfect fourth, perfect fifth) [Csus]
Functional sixths:
    Neapolitan 
    Italian
    French
    German
Other:
    pedal (pedal-point bass)
    power (perfect fifth)
    Tristan [FTristan]'''

def realizeChordSymbolDurations(piece):
    '''Returns Music21 score object with duration attribute of chord symbols correctly set. 
    Duration of chord symbols is based on the surrounding chord symbols; The chord symbol
    continues duration until another chord symbol is located or the piece ends.

    >>> from music21 import *
    >>> s = stream.Score()
    >>> s.append(harmony.ChordSymbol('C'))
    >>> s.repeatAppend(note.Note('C'), 4)
    >>> s.append(harmony.ChordSymbol('C'))
    >>> s.repeatAppend(note.Note('C'), 4)
    >>> s = s.makeMeasures()

    >>> harmony.realizeChordSymbolDurations(s).show('text')
    {0.0} <music21.clef.TrebleClef>
    {0.0} <music21.meter.TimeSignature 4/4>
    {0.0} <music21.harmony.ChordSymbol C>
    {0.0} <music21.note.Note C>
    {1.0} <music21.note.Note C>
    {2.0} <music21.note.Note C>
    {3.0} <music21.note.Note C>
    {4.0} <music21.harmony.ChordSymbol C>
    {4.0} <music21.note.Note C>
    {5.0} <music21.note.Note C>
    {6.0} <music21.note.Note C>
    {7.0} <music21.note.Note C>
    {8.0} <music21.bar.Barline style=final>
    

    If only one chord symbol object is present:

    >>> s = stream.Score()
    >>> s.append(harmony.ChordSymbol('C'))
    >>> s.repeatAppend(note.Note('C'), 4)
    >>> s = s.makeMeasures()
    >>> harmony.realizeChordSymbolDurations(s).show('text') 
    {0.0} <music21.clef.TrebleClef>
    {0.0} <music21.meter.TimeSignature 4/4>
    {0.0} <music21.harmony.ChordSymbol C>
    {0.0} <music21.note.Note C>
    {1.0} <music21.note.Note C>
    {2.0} <music21.note.Note C>
    {3.0} <music21.note.Note C>
    {4.0} <music21.bar.Barline style=final>

       
    If a ChordSymbol object exists followed by many notes, duration represents all those notes
    (how else can the computer know to end the chord? if there's not chord following it other than
    end the chord at the end of the piece?)

    >>> s = stream.Score()
    >>> s.repeatAppend(note.Note('C'), 4)
    >>> s.append(harmony.ChordSymbol('C'))
    >>> s.repeatAppend(note.Note('C'), 8)  
    >>> s = s.makeMeasures()
    >>> harmony.realizeChordSymbolDurations(s).show('text')        
    {0.0} <music21.clef.TrebleClef>
    {0.0} <music21.meter.TimeSignature 4/4>
    {0.0} <music21.note.Note C>
    {1.0} <music21.note.Note C>
    {2.0} <music21.note.Note C>
    {3.0} <music21.note.Note C>
    {4.0} <music21.harmony.ChordSymbol C>
    {4.0} <music21.note.Note C>
    {5.0} <music21.note.Note C>
    {6.0} <music21.note.Note C>
    {7.0} <music21.note.Note C>
    {8.0} <music21.note.Note C>
    {9.0} <music21.note.Note C>
    {10.0} <music21.note.Note C>
    {11.0} <music21.note.Note C>
    {12.0} <music21.bar.Barline style=final>
    '''
    pf = piece.flat
    onlyChords = pf.getElementsByClass(Harmony)

    first = True
    if len(onlyChords) > 1:
        for cs in onlyChords:
            if first:
                first = False
                lastchord = cs
                continue
            else:
                lastchord.duration.quarterLength = cs.getOffsetBySite(pf) - lastchord.getOffsetBySite(pf)
                if onlyChords.index(cs) == (len(onlyChords) - 1):
                    cs.duration.quarterLength = pf.highestTime - cs.getOffsetBySite(pf)
                lastchord = cs
        return pf
    elif len(onlyChords) == 1:
        onlyChords[0].duration.quarterLength = pf.highestOffset - onlyChords[0].getOffsetBySite(pf) 
        return pf
    else:
        return piece

#-------------------------------------------------------------------------------
class ChordStepModificationException(Exception):
    pass

class HarmonyException(Exception):
    pass

#-------------------------------------------------------------------------------
class ChordStepModification(object):
    '''ChordStepModification objects define the specification of harmony degree alterations, subtractions, or additions, 
     used in :class:`~music21.harmony.Harmony` objects, which includes harmony.ChordSymbol objects (and
     will include harmony.RomanNumeral objects)

        degree-value element: indicates degree in chord, positive integers only
        degree-alter: indicates semitone alteration of degree, positive and negative integers only
        degree-type: add, alter, or subtract

        if add:  degree-alter is relative to a dominant chord (major and perfect intervals except for a minor seventh)

        if alter or subtract: degree-alter is relative to degree already in the chord based on its kind element
        
        <!-- FROM XML DOCUMENTATION
        http://www.google.com/codesearch#AHKd_kdk32Q/trunk/musicXML/dtd/direction.mod&q=Chord%20Symbols%20package:http://bmml%5C.googlecode%5C.com&l=530
        The degree element is used to add, alter, or subtract
        individual notes in the chord. The degree-value element
        is a number indicating the degree of the chord (1 for
        the root, 3 for third, etc). The degree-alter element
        is like the alter element in notes: 1 for sharp, -1 for
        flat, etc. The degree-type element can be add, alter, or
        subtract. If the degree-type is alter or subtract, the
        degree-alter is relative to the degree already in the
        chord based on its kind element. If the degree-type is
        add, the degree-alter is relative to a dominant chord
        (major and perfect intervals except for a minor
        seventh). The print-object attribute can be used to
        keep the degree from printing separately when it has
        already taken into account in the text attribute of
        the kind element. The plus-minus attribute is used to
        indicate if plus and minus symbols should be used
        instead of sharp and flat symbols to display the degree
        alteration; it is no by default. The degree-value and
        degree-type text attributes specify how the value and
        type of the degree should be displayed.

        A harmony of kind "other" can be spelled explicitly by
        using a series of degree elements together with a root.
        -->
        
    >>> from music21 import *
    >>> hd = harmony.ChordStepModification('add', 4)
    >>> hd
    <music21.harmony.ChordStepModification modType=add degree=4 interval=None>
    >>> hd = harmony.ChordStepModification('alter', 3, 1)
    >>> hd
    <music21.harmony.ChordStepModification modType=alter degree=3 interval=<music21.interval.Interval A1>>

    '''
    def __init__(self, modType=None, degree=None, interval=None):
        self._modType = None # add, alter, subtract
        self._interval = None # alteration of degree, alter ints in mxl
        self._degree = None # the degree number, where 3 is the third

        # use properties if defined
        if modType is not None:    
            self.modType = modType
        if degree is not None:
            self.degree = degree
        if interval is not None:
            self.interval = interval
    
    def __repr__(self):
        return '<music21.harmony.ChordStepModification modType=%s degree=%s interval=%s>' %\
             (self.modType, self.degree, self.interval)
        
    #---------------------------------------------------------------------------
    def _setModType(self, value):
        if value is not None and common.isStr(value):
            if value.lower() in ['add', 'subtract', 'alter']:
                self._modType = value.lower()
                return            
        raise ChordStepModificationException('not a valid degree modification type: %s' % value)

    def _getModType(self):
        return self._modType

    modType = property(_getModType, _setModType, doc= '''
        Get or set the ChordStepModification modification type, where permitted types are the strings add, subtract, or alter.

        >>> from music21 import *
        >>> hd = harmony.ChordStepModification()
        >>> hd.modType = 'add'
        >>> hd.modType
        'add'
        >>> hd.modType = 'juicy'
        Traceback (most recent call last):
        ChordStepModificationException: not a valid degree modification type: juicy
        ''')

    #---------------------------------------------------------------------------
    def _setInterval(self, value):
        if value in [None]: 
            self._interval = None

        elif hasattr(value, 'classes') and 'Interval' in value.classes:
            # an interval object: set directly
            self._interval = value
        else:
            # accept numbers to permit loading from mxl alter specs
            if value in [1]:
                self._interval = interval.Interval('a1')
            elif value in [2]: # double augmented
                self._interval = interval.Interval('aa1')
            elif value in [-1]:
                self._interval = interval.Interval('-a1')
            elif value in [-2]:
                self._interval = interval.Interval('-aa1')
            else: # try to create interval object
                self._interval = interval.Interval(value)

    def _getInterval(self):
        return self._interval

    interval = property(_getInterval, _setInterval, doc= '''
        Get or set the alteration of this degree as a :class:`~music21.interval.Interval` object.

        >>> from music21 import *
        >>> hd = harmony.ChordStepModification()
        >>> hd.interval = 1
        >>> hd.interval
        <music21.interval.Interval A1>
        >>> hd.interval = -2
        >>> hd.interval
        <music21.interval.Interval AA-1>
        ''')

    #---------------------------------------------------------------------------
    def _setDegree(self, value):
        if value is not None and common.isNum(value):
            self._degree = int(value) # should always be an integer
            return            
        raise ChordStepModificationException('not a valid degree: %s' % value)

    def _getDegree(self):
        return self._degree

    degree = property(_getDegree, _setDegree, doc= '''

        >>> from music21 import *
        >>> hd = harmony.ChordStepModification()
        >>> hd.degree = 3
        >>> hd.degree
        3
        >>> hd.degree = 'juicy'
        Traceback (most recent call last):
        ChordStepModificationException: not a valid degree: juicy

        ''')

#-------------------------------------------------------------------------------
class Harmony(music21.Music21Object):
    '''
    >>> from music21 import *
    >>> h = harmony.ChordSymbol() 
    >>> h.XMLroot = 'b-'
    >>> h.XMLbass = 'd'
    >>> h.XMLinversion = 1
    >>> h.addChordStepModification(harmony.ChordStepModification('add', 4))
    >>> h
    <music21.harmony.ChordSymbol B-/D add 4>
    >>> p = harmony.ChordSymbol(root='C', bass='E', inversion=1, duration=4.0)
    >>> p
    <music21.harmony.ChordSymbol C/E>

    Harmony objects in music21 are special types of chords. Although on a page of music they exist as symbols
    rather than notes, musicians consider them to be chords. Thus, harmony objects in music21 are not a subclass
    of Chord, although they do contain a chord object within them and all of the methods of class chord can
    be used to operate directly on the harmony object. NB - h.root() is analogous to calling h.chord.root()
    
    For example,
    
    >>> from music21 import *
    >>> h = harmony.ChordSymbol('C7/E')
    >>> h.root()
    C4
    >>> h.bass()
    E3
    >>> h.inversion()
    1
    >>> h.isSeventh()
    True
    >>> h.pitches
    [E3, G3, B-3, C4]
    ''' 
    
    def __init__(self, figure = None, **keywords):
        
        music21.Music21Object.__init__(self)
        
        self._XMLroot = None # a pitch object
        self._XMLbass = None # a pitch object

        self._XMLinversion = None # an integer
        self._chord = music21.chord.Chord()
        
        
        #for a harmony object's duration is 0. Users can run realizeChordSymbolDuraitons method to
        #assign the correct duration to each harmony object given a score
        
        #TODO: deal with the roman numeral property of harmonies...music xml documentation is ambiguous: 
        #A root is a pitch name like C, D, E, where a function is an 
        #indication like I, II, III. It is an either/or choice to avoid data inconsistency.    
        self._roman = None # a romanNumeral numeral object, musicxml stores this within a node called <function> which might conflict with the Harmony...
                  
        # specify an array of degree alteration objects
        self.chordStepModifications = []
        self._degreesList = []
        self._pitchesAndDegrees = []
           
        self.duration = music21.duration.Duration(0)
        
        for kw in keywords:
            if kw == 'root':
                self._XMLroot = music21.pitch.Pitch(keywords[kw])
            elif kw == 'bass':
                self._XMLbass= music21.pitch.Pitch(keywords[kw])
            elif kw == 'inversion':
                self._XMLinversion = int(keywords[kw])
            elif kw == 'duration' or kw == 'quarterLength':
                self.duration = music21.duration.Duration(keywords[kw])
            else:
                pass
        
        #figure is the string representation of a Harmony object
        #for example, for Chord Symbols the figure might be 'Cm7'
        #for roman numerals, the figure might be 'I7'
        self._figure = figure
        if self._figure is not None:
            self._parseFigure(self._figure)

    def _getFigure(self):
        if self._figure == None:
            return self.findFigure()
        else:
            return self._figure
        
    def _setFigure(self, value):
        self._figure = value
        if self._figure is not None:
            self._parseFigure(self._figure)
            
    figure = property(_getFigure, _setFigure, doc = '''
        Get or set the figure of the harmony object. The figure is the character (string)
        representation of the object. For example, 'I', 'CM', '3#'
        
        when you instantiate a harmony object, if you pass in a figure it is stored internally
        and returned when you access the figure property. if you don't instantiate the object
        with a figure, this property calls :meth:`music21.harmony.findFigure` method which
        deduces the figure provided other information about the object, especially the chord
        
        if the pitches of the harmony object have been modified after being instantiated,
        call :meth:`music21.harmony.findFigure` to deduce the new figure
        
        >>> from music21 import *
        >>> h = harmony.ChordSymbol('CM')
        >>> h.figure
        'CM'
        >>> harmony.ChordSymbol(root = 'C', bass = 'A', kind = 'minor').figure
        'Cm/A'
        >>> h.bass(note.Note('E'))
        >>> h.figure
        'CM'
        ''')
    
    def findFigure(self):
        return None
    
    def __repr__(self):
        return '<music21.harmony.%s %s >' % (self.__class__.__name__, self.figure)
#        if len(self.chordStepModifications) == 0:         
#                (self.__class__.__name__, self.XMLroot, self.XMLbass, \
#                    self.XMLinversion, self.duration.quarterLength)
#            return '<music21.harmony.%s root=%s bass=%s inversion=%s duration=%s>' % \
#                (self.__class__.__name__, self.XMLroot, self.XMLbass, \
#                    self.XMLinversion, self.duration.quarterLength)
#        else:
#            return '<music21.harmony.%s root=%s bass=%s inversion=%s duration=%s ChordStepModifications=%s>' % \
#                (self.__class__.__name__, self.XMLroot, self.XMLbass, self.XMLinversion, self.duration.quarterLength, \
#                                    ''.join([str(x) for x in self.chordStepModifications]))

    #---------------------------------------------------------------------------
    def _realizePitches(self):
        '''method must be overridden in each subclass of Harmony because each harmony object uses
        a different method to extract pitches form the harmony symbol'''
        pass
    
    def _parseFigure(self):
        '''method must be overriden in each subclass of Harmony because each harmony object 
        uses a different method to parse the figure'''
        pass
    
    def _setChord(self, value):
        if hasattr(value, 'classes') and 'Chord' in value.classes:
            self._chord = value
            return
        try: # try to create 
            self._chord = chord.Chord(value)
            return
        except music21.Music21Exception: 
            pass
        raise HarmonyException('not a valid music21 chord specification: %s' % value)


    def _getChord(self):
        if self._chord.pitches == [] and self.XMLroot:
            self._realizePitches()   
        return self._chord

    chord = property(_getChord, _setChord, doc = '''
        Get or set the chord object of this harmony object. The chord object will
        be returned with the realized pitches as an attribute. The user could 
        override these pitches by manually setting the chord.pitches.


        ''')
    
      
    
    def addChordStepModification(self, degree):
        '''Add a harmony degree specification to this Harmony as a :class:`~music21.harmony.ChordStepModification` object.

        >>> from music21 import *
        >>> hd = harmony.ChordStepModification('add', 4)
        >>> h = harmony.ChordSymbol()
        >>> h.addChordStepModification(hd)
        >>> h.addChordStepModification('juicy')
        Traceback (most recent call last):
        HarmonyException: cannot add this object as a degree: juicy

        '''
        if not isinstance(degree, ChordStepModification):
            # TODO: possibly create ChordStepModification objects from other 
            # specifications
            raise HarmonyException('cannot add this object as a degree: %s' % degree)
        else:
            self.chordStepModifications.append(degree)
            
    def getChordStepModifications(self):
        '''Return all harmony degrees as a list.
        '''
        return self.chordStepModifications

    def getPitchesAndDegrees(self):
        '''pitchesAndDegrees is the compiled list of the pitches in the chord and their 
        respective degrees (with alterations, a '-' for flat, a '#' for sharp, and an 'A'
        for altered. It is a list of lists of two units, the pitch and the degree. The list is 
        not ordered.
        
        >>> from music21 import *
        >>> h = harmony.ChordSymbol('CMaj7')
        >>> h.getPitchesAndDegrees()
        [[C3, '1'], [E3, '3'], [G3, '5'], [B3, '7']]
        
        >>> h = harmony.ChordSymbol('Dm7/Fomit5')
        >>> h.getPitchesAndDegrees()
        [[D4, '1'], [F3, '-3'], [C4, '-7']]
        
        >>> h = harmony.ChordSymbol('Dm7/F')
        >>> h.getPitchesAndDegrees()
        [[D4, '1'], [F3, '-3'], [A3, '5'], [C4, '-7']]
        '''
        #just update octaves here
        
        for pitch, pitchAndDegree in zip(self.pitches, self._pitchesAndDegrees):
            if pitch.name == pitchAndDegree[0]:
                pitchAndDegree[0] = pitch
        return self._pitchesAndDegrees
    
    def getDegrees(self):
        '''Return list of all the degrees associated with the pitches of the Harmony Chord
        
        >>> from music21 import *
        >>> h = harmony.ChordSymbol('Dm7/F')
        >>> h.getDegrees()
        ['1', '-3', '5', '-7']
        '''
        if self.pitches == []:
            self._realizePitches()
        return self._degreesList

    def _setRoot(self, value):
        if hasattr(value, 'classes') and 'Pitch' in value.classes:
            self._XMLroot = value
            self._chord.root(self._XMLroot )
            return
        try: # try to create a Pitch object
            self._XMLroot = pitch.Pitch(value)
            self._chord.root(self._XMLroot )
            return
        except music21.Music21Exception: 
            pass
        raise HarmonyException('not a valid pitch specification: %s' % value)

    def _getRoot(self):
        return self._XMLroot

    XMLroot = property(_getRoot, _setRoot, doc= '''
        Get or set the XMLroot attribute of the Harmony as a :class:`~music21.pitch.Pitch` object. 
        String representations accepted by Pitch are also accepted. Also updates the associated 
        chord object's root

        >>> from music21 import *
        >>> h = harmony.ChordSymbol()
        >>> h.XMLroot= 'a#'
        >>> h.XMLroot
        A#
        >>> h.XMLroot= pitch.Pitch('c#')
        >>> h.XMLroot
        C#
        >>> h.XMLroot= 'juicy'
        Traceback (most recent call last):
        HarmonyException: not a valid pitch specification: juicy
        ''')


    #---------------------------------------------------------------------------
    def _setBass(self, value):
        if hasattr(value, 'classes') and 'Pitch' in value.classes:
            self._XMLbass = value
            self._chord.bass(self._XMLbass )
            return
        try: # try to create a Pitch object
            self._XMLbass = pitch.Pitch(value)
            self._chord.bass(self._XMLbass )
            return
        except music21.Music21Exception: 
            pass
        raise HarmonyException('not a valid pitch specification: %s' % value)

    def _getBass(self):
        if self._XMLbass:
            return self._XMLbass
        else:
            return self._XMLroot

    XMLbass = property(_getBass, _setBass, doc= '''
        Get or set the XMLbass of the Harmony as a :class:`~music21.pitch.Pitch` object. 
        String representations accepted by Pitch are also accepted. Also updates the associated 
        chord object's bass. If the bass is 'None' (commonly read in from music xml) then it returns
        the root pitch.
        
        >>> from music21 import *
        >>> h = harmony.ChordSymbol()
        >>> h.XMLbass = 'a#'
        >>> h.XMLbass
        A#
        >>> h.XMLbass = pitch.Pitch('d-')
        >>> h.XMLbass
        D-
        >>> h.XMLbass = 'juicy'
        Traceback (most recent call last):
        HarmonyException: not a valid pitch specification: juicy
        ''')

    #---------------------------------------------------------------------------
    def _setInversion(self, value):
        if common.isNum(value):
            self._XMLinversion = int(value)
            #self.inversion(self._XMLinversion)
            return
        elif value == None:
            self._XMLinversion = value
            #self.inversion(self._XMLinversion)
            return
        raise HarmonyException('not a valid inversion specification: %s' % value)

    def _getInversion(self):
        return self._XMLinversion

    XMLinversion = property(_getInversion, _setInversion, doc= '''
        Get or set the inversion of this Harmony as a positive integer. Also updates the associated 
        chord object's bass. 

        >>> from music21 import *
        >>> h = harmony.ChordSymbol()
        >>> h.XMLinversion = 2
        >>> h.XMLinversion
        2
        ''')

    #---------------------------------------------------------------------------
    #TODO: move this attribute to roman class which inherets from harmony.Harmony objects
    def _setRoman(self, value):
        if hasattr(value, 'classes') and 'RomanNumeral' in value.classes:
            self._roman = value
            return
        try: # try to create 
            self._roman = roman.RomanNumeral(value)
            return
        except music21.Music21Exception: 
            pass
        raise HarmonyException('not a valid pitch specification: %s' % value)

    def _getRoman(self):
        return self._roman

    romanNumeral = property(_getRoman, _setRoman, doc= '''
        Get or set the romanNumeral numeral function of the Harmony as a :class:`~music21.romanNumeral.RomanNumeral` object. String representations accepted by RomanNumeral are also accepted.

        >>> from music21 import *
        >>> h = harmony.ChordSymbol()
        >>> h.romanNumeral = 'III'
        >>> h.romanNumeral
        <music21.roman.RomanNumeral III>
        >>> h.romanNumeral = roman.RomanNumeral('vii')
        >>> h.romanNumeral
        <music21.roman.RomanNumeral vii>

        ''')
    
    #--------------------------------------------------------------
    #----------------------- CHORD METHODS ------------------------
    # These methods use the harmony object's chord object to access
    # chord methods directly. If a method is added to chord, it must
    # manually be added here. script to run through chord.py and 
    # generate this is below.
    '''
    f = open('C:/Users/bhadley/chord.txt', 'r')
    import re
    
       
    getThese = False
    methodDict = {}
    propertyDict = {}
    for line in f:
        if line.startswith('class Chord'):
            getThese = True
        elif line.startswith('class'):
            getThese = False
        if getThese:
            if line.startswith('    def ') and True not in [c in line for c in [ '__init__','__repr__', '__deepcopy__']]:
                methodName = line.split()[1][0:line.split()[1].find('(')]
                a = re.sub(r'\s', '', line)
                remList = [('def',''),('self,',''), ('self','')]
                for i, j in remList:
                    a = a.replace(i, j)
                skip = False
                ret = ''
                for x in a:
                    if x == '=': skip = True
                    elif skip and x ==',' or x == ')':
                        ret +=x
                        skip = False
                    elif skip == False and x not in ':': ret +=x
                if 'def _' not in line:
                    code = line + '        \'\'\'directly calls :meth:`~music21.chord.Chord.' + methodName + '`\'\'\'\n' + \
                           '        return self.chord.' + ret + '\n'
                else:
                    code = line + '        return self.chord.' + ret + '\n'
                methodDict[methodName] = code 
                
            if '= property' in line:
                propertyName = line[0:line.find('=')].strip()
                line = line.replace('doc=\'\'\'', '')
                if line.strip().endswith(',') or line.strip().endswith(')'):
                    line = line.strip()[:-1]
                code = '    ' + line.strip() + ', \n        doc = \'\'\'directly references :attr:`music21.chord.Chord.' + propertyName + '`\'\'\') \n'
                #code = '    ' + propertyName + ' = property(self.chord.'+ propertyName + ', self.chord.' + \
                #       propertyName + ', \n        doc = \'\'\'directly references :attr:`music21.chord.Chord.' + propertyName + '\'\'\' ) \n'
    
                propertyDict[propertyName] = code
    
    
    for i,j in methodDict.items():
        print j
    
    for i,j in propertyDict.items():
        print j
            
    '''     
     
 
    def seekChordTablesAddress(self):
        '''directly calls :meth:`~music21.chord.Chord.seekChordTablesAddress`'''
        return self.chord.seekChordTablesAddress()

    def getVolume(self, p):
        '''directly calls :meth:`~music21.chord.Chord.getVolume`'''
        return self.chord.getVolume(p)

    #def _getMX(self):
    #    return self.chord._getMX()

    def getZRelation(self):
        '''directly calls :meth:`~music21.chord.Chord.getZRelation`'''
        return self.chord.getZRelation()

    def _removePitchByRedundantAttribute(self, attribute, inPlace):
        return self.chord._removePitchByRedundantAttribute(attribute,inPlace)

    def isDominantSeventh(self):
        '''directly calls :meth:`~music21.chord.Chord.isDominantSeventh`'''
        return self.chord.isDominantSeventh()

    def _getSeventh(self):
        return self.chord._getSeventh()

    def _getPitches(self):
        return self.chord._getPitches()

    def _getForteClass(self):
        return self.chord._getForteClass()

    def isItalianAugmentedSixth(self, restrictDoublings = False):
        '''directly calls :meth:`~music21.chord.Chord.isItalianAugmentedSixth`'''
        return self.chord.isItalianAugmentedSixth(restrictDoublings)

    def closedPosition(self, forceOctave=None, inPlace=False):
        '''directly calls :meth:`~music21.chord.Chord.closedPosition`'''
        return self.chord.closedPosition(forceOctave,inPlace)

    def hasComponentVolumes(self):
        '''directly calls :meth:`~music21.chord.Chord.hasComponentVolumes`'''
        return self.chord.hasComponentVolumes()

    def sortFrequencyAscending(self):
        '''directly calls :meth:`~music21.chord.Chord.sortFrequencyAscending`'''
        return self.chord.sortFrequencyAscending()

    def findRoot(self):
        '''directly calls :meth:`~music21.chord.Chord.findRoot`'''
        return self.chord.findRoot()

    def isHalfDiminishedSeventh(self):
        '''directly calls :meth:`~music21.chord.Chord.isHalfDiminishedSeventh`'''
        return self.chord.isHalfDiminishedSeventh()

    def getTie(self, p):
        '''directly calls :meth:`~music21.chord.Chord.getTie`'''
        return self.chord.getTie(p)

    def _getScaleDegrees(self):
        return self.chord._getScaleDegrees()

    def __getitem__(self, key):
        return self.chord.__getitem__(key)

    def removeRedundantPitchNames(self, inPlace=True):
        '''directly calls :meth:`~music21.chord.Chord.removeRedundantPitchNames`'''
        return self.chord.removeRedundantPitchNames(inPlace)

    def getColor(self, pitchTarget):
        '''directly calls :meth:`~music21.chord.Chord.getColor`'''
        return self.chord.getColor(pitchTarget)

    def _findBass(self):
        return self.chord._findBass()

    def _getMidiFile(self):
        return self.chord._getMidiFile()

    def isConsonant(self):
        '''directly calls :meth:`~music21.chord.Chord.isConsonant`'''
        return self.chord.isConsonant()

    def setNotehead(self, nh, pitchTarget):
        '''directly calls :meth:`~music21.chord.Chord.setNotehead`'''
        return self.chord.setNotehead(nh,pitchTarget)

    def _getFifth(self):
        return self.chord._getFifth()

    def getChordStep(self, chordStep, testRoot = None):
        '''directly calls :meth:`~music21.chord.Chord.getChordStep`'''
        return self.chord.getChordStep(chordStep,testRoot)

    def inversion(self):
        '''directly calls :meth:`~music21.chord.Chord.inversion`'''
        return self.chord.inversion()

    def hasAnyRepeatedDiatonicNote(self, testRoot = None):
        '''directly calls :meth:`~music21.chord.Chord.hasAnyRepeatedDiatonicNote`'''
        return self.chord.hasAnyRepeatedDiatonicNote(testRoot)

    #def _setMX(self, mxNoteList):
    #    return self.chord._setMX(mxNoteList)

    def getStemDirection(self, p):
        '''directly calls :meth:`~music21.chord.Chord.getStemDirection`'''
        return self.chord.getStemDirection(p)

    def isGermanAugmentedSixth(self):
        '''directly calls :meth:`~music21.chord.Chord.isGermanAugmentedSixth`'''
        return self.chord.isGermanAugmentedSixth()

    def _getPrimeFormString(self):        
        return self.chord._getPrimeFormString()

    def semitonesFromChordStep(self, chordStep, testRoot = None):
        '''directly calls :meth:`~music21.chord.Chord.semitonesFromChordStep`'''
        return self.chord.semitonesFromChordStep(chordStep,testRoot)

    def _semiClosedPosition(self):
        return self.chord._semiClosedPosition()

    def sortDiatonicAscending(self, inPlace=False):
        '''directly calls :meth:`~music21.chord.Chord.sortDiatonicAscending`'''
        return self.chord.sortDiatonicAscending(inPlace)

    def _getVolume(self):    
        return self.chord._getVolume()

    def _getDuration(self):
        return self.chord._getDuration()

    def isFalseDiminishedSeventh(self):
        '''directly calls :meth:`~music21.chord.Chord.isFalseDiminishedSeventh`'''
        return self.chord.isFalseDiminishedSeventh()

    def _updateChordTablesAddress(self):
        return self.chord._updateChordTablesAddress()

    def _getCommonName(self):
        return self.chord._getCommonName()

    def isMinorTriad(self):
        '''directly calls :meth:`~music21.chord.Chord.isMinorTriad`'''
        return self.chord.isMinorTriad()

    def bass(self, newbass = 0):
        '''directly calls :meth:`~music21.chord.Chord.bass`'''
        return self.chord.bass(newbass)

    def transpose(self, value, inPlace=False):
        '''directly calls :meth:`~music21.chord.Chord.transpose`'''
        return self.chord.transpose(value,inPlace)

    def hasRepeatedChordStep(self, chordStep, testRoot = None):
        '''directly calls :meth:`~music21.chord.Chord.hasRepeatedChordStep`'''
        return self.chord.hasRepeatedChordStep(chordStep,testRoot)

    def _getMidiEvents(self):
        return self.chord._getMidiEvents()

    def containsTriad(self):
        '''directly calls :meth:`~music21.chord.Chord.containsTriad`'''
        return self.chord.containsTriad()

    def _getQuality(self):
        return self.chord._getQuality()

    def _getTie(self):
        return self.chord._getTie()

    def _getPitchClasses(self):
        return self.chord._getPitchClasses()

    def _setPitches(self, value):
        return self.chord._setPitches(value)

    def isIncompleteMajorTriad(self):
        '''directly calls :meth:`~music21.chord.Chord.isIncompleteMajorTriad`'''
        return self.chord.isIncompleteMajorTriad()

    def setColor(self, value, pitchTarget=None):
        '''directly calls :meth:`~music21.chord.Chord.setColor`'''
        return self.chord.setColor(value,pitchTarget)

    def isFrenchAugmentedSixth(self):        
        '''directly calls :meth:`~music21.chord.Chord.isFrenchAugmentedSixth`'''
        return self.chord.isFrenchAugmentedSixth()

    def _getMultisetCardinality(self):
        return self.chord._getMultisetCardinality()

    def _preDurationLily(self):
        return self.chord._preDurationLily()

    def _setPitchNames(self, value):
        return self.chord._setPitchNames(value)

    def isMajorTriad(self):
        '''directly calls :meth:`~music21.chord.Chord.isMajorTriad`'''
        return self.chord.isMajorTriad()

    def _getNormalFormString(self):        
        return self.chord._getNormalFormString()

    def _setColor(self, value): 
        return self.chord._setColor(value)

    def isTriad(self):
        '''directly calls :meth:`~music21.chord.Chord.isTriad`'''
        return self.chord.isTriad()

    def _setDuration(self, durationObj):
        return self.chord._setDuration(durationObj)

    def setTie(self, t, pitchTarget):
        '''directly calls :meth:`~music21.chord.Chord.setTie`'''
        return self.chord.setTie(t,pitchTarget)

    def _setTie(self, value):
        return self.chord._setTie(value)

    def removeRedundantPitches(self, inPlace=True):
        '''directly calls :meth:`~music21.chord.Chord.removeRedundantPitches`'''
        return self.chord.removeRedundantPitches(inPlace)

    def _setMidiEvents(self, eventList, ticksPerQuarter):
        return self.chord._setMidiEvents(eventList,ticksPerQuarter)

    def isDiminishedSeventh(self):
        '''directly calls :meth:`~music21.chord.Chord.isDiminishedSeventh`'''
        return self.chord.isDiminishedSeventh()

    def isAugmentedSixth(self):
        '''directly calls :meth:`~music21.chord.Chord.isAugmentedSixth`'''
        return self.chord.isAugmentedSixth()

    def inversionName(self):
        '''directly calls :meth:`~music21.chord.Chord.inversionName`'''
        return self.chord.inversionName()

    def _getChordTablesAddress(self):
        return self.chord._getChordTablesAddress()

    def _isPrimeFormInversion(self):
        return self.chord._isPrimeFormInversion()

    def __len__(self):
        return self.chord.__len__()

    def setVolume(self, vol, pitchTarget=None):
        '''directly calls :meth:`~music21.chord.Chord.setVolume`'''
        return self.chord.setVolume(vol,pitchTarget)

    def _getIntervalVectorString(self):        
        return self.chord._getIntervalVectorString()

    def isAugmentedTriad(self):
        '''directly calls :meth:`~music21.chord.Chord.isAugmentedTriad`'''
        return self.chord.isAugmentedTriad()

    def _hasZRelation(self):
        return self.chord._hasZRelation()

    def isSwissAugmentedSixth(self):
        '''directly calls :meth:`~music21.chord.Chord.isSwissAugmentedSixth`'''
        return self.chord.isSwissAugmentedSixth()

    def __iter__(self):
        return self.chord.__iter__()

    def _getPitchClassCardinality(self):
        return self.chord._getPitchClassCardinality()

    def getNotehead(self, p):
        '''directly calls :meth:`~music21.chord.Chord.getNotehead`'''
        return self.chord.getNotehead(p)

    def canBeTonic(self):
        '''directly calls :meth:`~music21.chord.Chord.canBeTonic`'''
        return self.chord.canBeTonic()

    def _getForteClassTnI(self):
        return self.chord._getForteClassTnI()

    def intervalFromChordStep(self, chordStep, testRoot = None):
        '''directly calls :meth:`~music21.chord.Chord.intervalFromChordStep`'''
        return self.chord.intervalFromChordStep(chordStep,testRoot)

    def _getPrimeForm(self):
        return self.chord._getPrimeForm()

    def _getColor(self):
        return self.chord._getColor()

    def _getNormalForm(self):
        return self.chord._getNormalForm()

    def _formatVectorString(self, vectorList):
        return self.chord._formatVectorString(vectorList)

    def root(self, newroot=False):
        '''directly calls :meth:`~music21.chord.Chord.root`'''
        return self.chord.root(newroot)

    def annotateIntervals(self, inPlace = True, stripSpecifiers=True, sortPitches=True):
        '''directly calls :meth:`~music21.chord.Chord.annotateIntervals`'''
        return self.chord.annotateIntervals(inPlace,stripSpecifiers,sortPitches)

    def removeRedundantPitchClasses(self, inPlace=True):
        '''directly calls :meth:`~music21.chord.Chord.removeRedundantPitchClasses`'''
        return self.chord.removeRedundantPitchClasses(inPlace)

    def canBeDominantV(self):
        '''directly calls :meth:`~music21.chord.Chord.canBeDominantV`'''
        return self.chord.canBeDominantV()

    def _getIntervalVector(self):
        return self.chord._getIntervalVector()

    def _setVolume(self, value):
        return self.chord._setVolume(value)

    def isIncompleteMinorTriad(self):
        '''directly calls :meth:`~music21.chord.Chord.isIncompleteMinorTriad`'''
        return self.chord.isIncompleteMinorTriad()

    def _getThird(self):
        return self.chord._getThird()

    def areZRelations(self, other):
        '''directly calls :meth:`~music21.chord.Chord.areZRelations`'''
        return self.chord.areZRelations(other)

    def isDiminishedTriad(self):
        '''directly calls :meth:`~music21.chord.Chord.isDiminishedTriad`'''
        return self.chord.isDiminishedTriad()

    def _getForteClassNumber(self):
        return self.chord._getForteClassNumber()

    def isSeventh(self):
        '''directly calls :meth:`~music21.chord.Chord.isSeventh`'''
        return self.chord.isSeventh()

    def _getPitchedCommonName(self):
        return self.chord._getPitchedCommonName()

    def _getPitchNames(self):
        return self.chord._getPitchNames()

    def _getFullName(self):
        return self.chord._getFullName()

    def containsSeventh(self):
        '''directly calls :meth:`~music21.chord.Chord.containsSeventh`'''
        return self.chord.containsSeventh()

    def sortAscending(self, inPlace=False):
        '''directly calls :meth:`~music21.chord.Chord.sortAscending`'''
        return self.chord.sortAscending(inPlace)

    def setStemDirection(self, stem, pitchTarget):
        '''directly calls :meth:`~music21.chord.Chord.setStemDirection`'''
        return self.chord.setStemDirection(stem,pitchTarget)

    def _getOrderedPitchClassesString(self):        
        return self.chord._getOrderedPitchClassesString()

    def sortChromaticAscending(self):
        '''directly calls :meth:`~music21.chord.Chord.sortChromaticAscending`'''
        return self.chord.sortChromaticAscending()

    def _getOrderedPitchClasses(self):
        return self.chord._getOrderedPitchClasses()

    color = property(_getColor, _setColor, 
        doc = '''directly references :attr:`music21.chord.Chord.color`''') 

    intervalVector = property(_getIntervalVector, 
        doc = '''directly references :attr:`music21.chord.Chord.intervalVector`''') 

    midiEvents = property(_getMidiEvents, _setMidiEvents, 
        doc = '''directly references :attr:`music21.chord.Chord.midiEvents`''') 

    forteClassTnI = property(_getForteClassTnI, 
        doc = '''directly references :attr:`music21.chord.Chord.forteClassTnI`''') 

    normalForm = property(_getNormalForm, 
        doc = '''directly references :attr:`music21.chord.Chord.normalForm`''') 

    multisetCardinality = property(_getMultisetCardinality, 
        doc = '''directly references :attr:`music21.chord.Chord.multisetCardinality`''') 

    forteClass = property(_getForteClass, 
        doc = '''directly references :attr:`music21.chord.Chord.forteClass`''') 

    primeFormString = property(_getPrimeFormString, 
        doc = '''directly references :attr:`music21.chord.Chord.primeFormString`''') 

    duration = property(_getDuration, _setDuration, 
        doc = '''directly references :attr:`music21.chord.Chord.duration`''') 

    isPrimeFormInversion = property(_isPrimeFormInversion, 
        doc = '''directly references :attr:`music21.chord.Chord.isPrimeFormInversion`''') 

    quality = property(_getQuality, 
        doc = '''directly references :attr:`music21.chord.Chord.quality`''') 

    chordTablesAddress = property(_getChordTablesAddress, 
        doc = '''directly references :attr:`music21.chord.Chord.chordTablesAddress`''') 

    fifth = property(_getFifth, 
        doc = '''directly references :attr:`music21.chord.Chord.fifth`''') 

    pitchClassCardinality = property(_getPitchClassCardinality, 
        doc = '''directly references :attr:`music21.chord.Chord.pitchClassCardinality`''') 

    commonName = property(_getCommonName, 
        doc = '''directly references :attr:`music21.chord.Chord.commonName`''') 

    orderedPitchClasses = property(_getOrderedPitchClasses, 
        doc = '''directly references :attr:`music21.chord.Chord.orderedPitchClasses`''') 

    tie = property(_getTie, _setTie, 
        doc = '''directly references :attr:`music21.chord.Chord.tie`''') 

    pitchedCommonName = property(_getPitchedCommonName, 
        doc = '''directly references :attr:`music21.chord.Chord.pitchedCommonName`''') 

    scaleDegrees = property(_getScaleDegrees, 
        doc = '''directly references :attr:`music21.chord.Chord.scaleDegrees`''') 

    hasZRelation = property(_hasZRelation, 
        doc = '''directly references :attr:`music21.chord.Chord.hasZRelation`''') 

    intervalVectorString = property(_getIntervalVectorString, 
        doc = '''directly references :attr:`music21.chord.Chord.intervalVectorString`''') 

    seventh = property(_getSeventh, 
        doc = '''directly references :attr:`music21.chord.Chord.seventh`''') 

    pitches = property(_getPitches, _setPitches, 
        doc = '''directly references :attr:`music21.chord.Chord.pitches`''') 

    primeForm = property(_getPrimeForm, 
        doc = '''directly references :attr:`music21.chord.Chord.primeForm`''') 

    orderedPitchClassesString = property(_getOrderedPitchClassesString, 
        doc = '''directly references :attr:`music21.chord.Chord.orderedPitchClassesString`''') 

    volume = property(_getVolume, _setVolume, 
        doc = '''directly references :attr:`music21.chord.Chord.volume`''') 

    fullName = property(_getFullName, 
        doc = '''directly references :attr:`music21.chord.Chord.fullName`''') 

    forteClassTn = property(_getForteClass, 
        doc = '''directly references :attr:`music21.chord.Chord.forteClassTn`''') 

    third = property(_getThird, 
        doc = '''directly references :attr:`music21.chord.Chord.third`''') 

    pitchNames = property(_getPitchNames, _setPitchNames, 
        doc = '''directly references :attr:`music21.chord.Chord.pitchNames`''') 

    midiFile = property(_getMidiFile, 
        doc = '''directly references :attr:`music21.chord.Chord.midiFile`''') 

    pitchClasses = property(_getPitchClasses, 
        doc = '''directly references :attr:`music21.chord.Chord.pitchClasses`''') 

    forteClassNumber = property(_getForteClassNumber, 
        doc = '''directly references :attr:`music21.chord.Chord.forteClassNumber`''') 

    normalFormString = property(_getNormalFormString, 
        doc = '''directly references :attr:`music21.chord.Chord.normalFormString`''') 

    #mx = property(_getMX, _setMX, 
    #    doc = '''directly references :attr:`music21.chord.Chord.mx`''')  
    
    
class ChordSymbol(Harmony): 
    '''
    Class representing the Chord Symbols commonly found on lead sheets. Chord Symbol objects
    can be instantiated one of two main ways:
    1) when music xml is parsed by the music21 converter, xml Chord Symbol tags are
    interpreted as Chord Symbol objects with a root and kind attribute. If bass is not specified,
    the bass is assumed to be the root
    
    2) by creating a chord symbol object with music21 by passing in the expression commonly found on
    leadsheets. Due to the relative diversity of lead sheet chord syntax, not all expressions
    are supported. Consult the examples for the supported syntax, or email us for help.
    
    When a Chord Symbol object is instantiated, it creates a 'chord' property, which is the chord
    representation of the Chord Symbol object. This chord is of :class:`~music21.chord.Chord` and 
    can be manipulated in the same was as any other chord object. However, when you access the chord
    attribute of the Chord Symbol, the pitches associated with that chord symbol are realized. This is true
    for both Chord Symbol objects instantiated from music xml and directly with music21.
    
    The music xml-based approach to instantiating Chord Symbol objects:
     
    >>> from music21 import *
    >>> cs = harmony.ChordSymbol(kind='minor',kindStr = 'm', root='C', bass = 'E-')
    >>> cs
    <music21.harmony.ChordSymbol Cm/E->
    >>> cs.XMLkind
    'minor'
    >>> cs.XMLroot
    C
    >>> cs.XMLbass
    E-
    
    The second approach to creating a Chord Symbol object, by passing a regular expression:
    
    >>> harmony.ChordSymbol('C').pitches
    [C3, E3, G3]
    >>> harmony.ChordSymbol('Cm').pitches
    [C3, E-3, G3]
    >>> harmony.ChordSymbol('C+').pitches
    [C3, E3, G#3]
    >>> harmony.ChordSymbol('Cdim').pitches
    [C3, E-3, G-3]
    >>> harmony.ChordSymbol('C7').pitches
    [C3, E3, G3, B-3]
    >>> harmony.ChordSymbol('CM7').pitches
    [C3, E3, G3, B3]
    >>> harmony.ChordSymbol('Cm7').pitches
    [C3, E-3, G3, B-3]
    >>> harmony.ChordSymbol('Cdim7').pitches
    [C3, E-3, G-3, B--3]
    >>> harmony.ChordSymbol('C7+').pitches
    [C3, E3, G#3, B-3]
    >>> harmony.ChordSymbol('Cm7b5').pitches #half-diminished
    [C3, E3, G-3, B-3]
    >>> harmony.ChordSymbol('CmMaj7').pitches
    [C3, E-3, G3, B3]
    >>> harmony.ChordSymbol('C6').pitches
    [C3, E3, G3, A3]
    >>> harmony.ChordSymbol('Cm6').pitches
    [C3, E-3, G3, A3]
    >>> harmony.ChordSymbol('C9').pitches
    [C3, E3, G3, B-3, D4]
    >>> harmony.ChordSymbol('CMaj9').pitches
    [C3, E3, G3, B3, D4]
    >>> harmony.ChordSymbol('Cm9').pitches
    [C3, E-3, G3, B-3, D4]
    >>> harmony.ChordSymbol('C11').pitches
    [C2, E2, G2, B-2, D3, F3]
    >>> harmony.ChordSymbol('CMaj11').pitches
    [C2, E2, G2, B2, D3, F3]
    >>> harmony.ChordSymbol('Cm11').pitches
    [C2, E-2, G2, B-2, D3, F3]
    >>> harmony.ChordSymbol('C13').pitches
    [C2, E2, G2, B-2, D3, F3, A3]
    >>> harmony.ChordSymbol('CMaj13').pitches
    [C2, E2, G2, B2, D3, F3, A3]
    >>> harmony.ChordSymbol('Cm13').pitches
    [C2, E-2, G2, B-2, D3, F3, A3]
    >>> harmony.ChordSymbol('Csus2').pitches     
    [C3, D3, G3]
    >>> harmony.ChordSymbol('Csus4').pitches 
    [C3, F3, G3]
    >>> harmony.ChordSymbol('CN6').pitches
    [C3, D-3, E3, G-3]
    >>> harmony.ChordSymbol('CIt+6').pitches     
    [C3, F#3, A-3]
    >>> harmony.ChordSymbol('CFr+6').pitches 
    [C3, D3, F#3, A-3]
    >>> harmony.ChordSymbol('CGr+6').pitches
    [C3, E-3, F#3, A-3]
    >>> harmony.ChordSymbol('Cpedal').pitches     
    [C3]
    >>> harmony.ChordSymbol('Cpower').pitches   
    [C3, G3]
    >>> harmony.ChordSymbol('Ftristan').pitches 
    [F3, G#3, B3, D#4]
    >>> harmony.ChordSymbol('C/E').pitches
    [E3, G3, C4]
    >>> harmony.ChordSymbol('Dm7/F').pitches
    [F3, A3, C4, D4]
    >>> harmony.ChordSymbol('Cadd2').pitches
    [C3, D3, E3, G3]
    >>> harmony.ChordSymbol('C7omit3').pitches
    [C3, G3, B-3]
    
    You can also create a Chord Symbol by writing out each degree, and any alterations to that degree:
    You must explicitly indicate EACH degree (a triad is NOT necessarily implied)

    >>> harmony.ChordSymbol('C35b7b9#11b13').pitches
    [C3, D-3, E3, F#3, G3, A-3, B-3]
    
    >>> harmony.ChordSymbol('C35911').pitches
    [C3, D3, E3, F3, G3]
    
    Ambiguity in notation: if the expression is ambiguous, for example 'Db35' (is this
    the key of Db with a third and a fifth, or is this key of D with a flat 3 and 
    normal fifth?) To prevent ambiguity, insert a comma after the root.
     
    >>> harmony.ChordSymbol('Db,35').pitches
    [D-3, F3, A-3]
    >>> harmony.ChordSymbol('D,b35').pitches
    [D3, F3, A3]
    >>> harmony.ChordSymbol('D,35b7b9#11b13').pitches
    [D3, E-3, F#3, G#3, A3, B-3, C4]

    '''
        
            
    def __init__(self, figure = None, **keywords):
        self.XMLkind = '' # a string from defined list of chord symbol harmonies
        self.XMLkindStr = '' # the presentation of the kind or label of symbol
        
        for kw in keywords:
            if kw == 'kind':
                self.XMLkind = keywords[kw]
            if kw == 'kindStr':
                self.XMLkindStr = keywords[kw]
                
        Harmony.__init__(self, figure, **keywords)
    
    def __repr__(self):
        return '<music21.harmony.%s %s>' % (self.__class__.__name__, self.figure)
#        if len(self.chordStepModifications) == 0:
#            return '<music21.harmony.%s kind=%s (%s) root=%s bass=%s inversion=%s duration=%s>' % \
#                (self.__class__.__name__, self.XMLkind, self.XMLkindStr, self.XMLroot, self.XMLbass, \
#                 self.XMLinversion, self.duration.quarterLength)
#        else:
#            return '<music21.harmony.%s kind=%s (%s) root=%s bass=%s inversion=%s duration=%s ChordStepModifications=%s>' %\
#                 (self.__class__.__name__, self.XMLkind, self.XMLkindStr, self.XMLroot, self.XMLbass, self.XMLinversion, \
#                  self.duration.quarterLength,''.join([str(x) for x in self.chordStepModifications]))
#---------------------------------------------------------------------------

    

    def _parseFigure(self, prelimFigure):
        '''
        translate the figure string (regular expression) into a meaningful Harmony object 
        by identifying the root, bass, inversion, kind, and kindStr.
        
        Examples of figures (could include spaces in these figures or not, 
        case is not sensitive except in the case of 'M' or 'm') all examples have C as root
                
        Triads:
            major (major third, perfect fifth)                           C        
            minor (minor third, perfect fifth)                           Cm        C-    Cmin
            augmented (major third, augmented fifth)                     C+        C#5
            diminished (minor third, diminished fifth)                   Cdim      Co

        Sevenths:
            dominant (major triad, minor seventh)                        C7        
            major-seventh (major triad, major seventh)                   CMaj7    CM7
            minor-seventh (minor triad, minor seventh)                   Cm7      Cmin
            diminished-seventh (diminished triad, diminished seventh)    Cdim7    Co7
            augmented-seventh (augmented triad, minor seventh)           C7+      C7#5
            half-diminished (diminished triad, minor seventh)            Cm7b5    
            major-minor (minor triad, major seventh)                     CmMaj7

        Sixths:
            major-sixth (major triad, added sixth)                       C6
            minor-sixth (minor triad, added sixth)                       Cm6      Cmin6

        Ninths:
            dominant-ninth (dominant-seventh, major ninth)               C9        
            major-ninth (major-seventh, major ninth)                     CMaj9    CM9
            minor-ninth (minor-seventh, major ninth)                     Cm9      Cmin9

        11ths (usually as the basis for alteration):
            dominant-11th (dominant-ninth, perfect 11th)                 C11
            major-11th (major-ninth, perfect 11th)                       CMaj11   CM11
            minor-11th (minor-ninth, perfect 11th)                       Cm11     Cmin11

        13ths (usually as the basis for alteration):
            dominant-13th (dominant-11th, major 13th)                    C13
            major-13th (major-11th, major 13th)                          CMaj13
            minor-13th (minor-11th, major 13th)                          Cm13     Cmin13

        Suspended:
            suspended-second (major second, perfect fifth)               Csus2
            suspended-fourth (perfect fourth, perfect fifth)             Csus    Csus4

        Functional sixths:
            Neapolitan                                                   CN6
            Italian                                                      CIt+6
            French                                                       CFr+6
            German                                                       CGr+6

        Other:
            pedal (pedal-point bass)                                     Cpedal
            power (perfect fifth)                                        Cpower
            Tristan                                                      Ctristan
                
       
        Inversions: (Root String / Bass Note)
        C/E
        
        Harmony Degree (Additions, Subtractions, Alterations)
        Add:
           Cadd3 ('regular figure expression' 'add' 'scale degree')
           Comit5 ('regular figure expression' 'omit' or 'subtract' scale degree')
        
        Or just spell out the harmonies by degrees
    
        '''
        
        #remove spaces from prelim Figure...
        prelimFigure = re.sub(r'\s', '', prelimFigure)

        #Get Root:
        if ',' in prelimFigure:
            root = prelimFigure[0:prelimFigure.index(',')]
            st = prelimFigure.replace(',','')
            st = prelimFigure.replace(root,'')
            prelimFigure = prelimFigure.replace(',','')
        else:
            m1 = re.match(r"[A-Ga-g][b#]?", prelimFigure) #match not case sensitive, 
            if m1:
                root = m1.group()
                st = prelimFigure.replace(m1.group(), '')  #remove the root and bass from the string and any additions/omitions/alterations/

        if root:
            if 'b' in root:
                root = root.replace('b', '-')
            self._chord.root( pitch.Pitch(root) )
            self.XMLroot = pitch.Pitch(root)

        #Get optional Bass:
        m2 = re.search(r"/[A-Ga-g][b#]?", prelimFigure) #match not case sensitive
        remaining = st
        if m2:
            bass = m2.group()

            if 'b' in bass:
                bass = bass.replace('b', '-')
   
            bass = bass.replace('/', '')
            self._chord.bass ( pitch.Pitch(bass) ) 
            self.XMLbass = pitch.Pitch(bass)     
            remaining = st.replace(m2.group(), '')   #remove the root and bass from the string and any additions/omitions/alterations/
        
     
        st = self._getKindFromShortHand(remaining)
    
        if 'add' in remaining:
            degree = remaining[remaining.index('add') + 3: ]
            self.addChordStepModification(music21.harmony.ChordStepModification('add', int(degree) ) )
            return
        if 'alter' in remaining:
            degree = remaining[remaining.index('alter') + 5: ]
            self.addChordStepModification(music21.harmony.ChordStepModification('alter', int(degree) ) )
            return
        if 'omit' in remaining or 'subtract' in remaining:
            degree = remaining[remaining.index('omit') + 4: ]
            self.addChordStepModification(music21.harmony.ChordStepModification('subtract', int(degree) ) )
            return       

        st = st.replace(',','')
        if 'b' in st or '#' in st:
            splitter = re.compile('([b#]+[^b#]+)')
            alterations = splitter.split(st)
        else:
            alterations = [st]
        
        indexes = []
    
        for itemString in alterations:
            try:
                justints = itemString.replace('b','')
                justints = justints.replace('#','')
            
                if int(justints) > 20:
                    alterations.remove(itemString)
                    skipNext = False
                    i = 0
                    charString = ''
                    for char in itemString:
                        if skipNext == False:
                            if char == '1':
                                indexes.append(itemString[i] + itemString[i+1])
                                skipNext = True
                            else:
                                if char == 'b' or char == '#':
                                    charString = charString + char
                                else:
                                    charString = charString + char
                                    indexes.append(charString)
                                    charString = ''
                        else:
                            skipNext = False
                        i = i + 1
                        
            except:
                continue

        for item in indexes:
            alterations.append(item) 
        
        degrees = []
        for alteration in alterations:
            if alteration != '':
                if 'b' in alteration:
                    semiToneAlter = -1 * alteration.count('b')
                else:
                    semiToneAlter = alteration.count('#')
                m3 = re.search(r"[1-9]+", alteration)
                if m3:
                    degrees.append([int(m3.group()), semiToneAlter])
       
        for degree, alterBy in degrees:
            self.addChordStepModification(music21.harmony.ChordStepModification('add', degree, alterBy))
    
    def findFigure(self):
        '''
        return the chord symbol figure associated with this chord. the XMLroot, XMLbass and XMLkind
        attributes must be specified
        
        Needs development - TODO: chord step modifications need actually pitches rather than numeric degrees
        
        >>> from music21 import *
        >>> h = harmony.ChordSymbol(root = 'F', bass = 'D-', kind = 'Neapolitan')
        >>> h.figure
        'FN6/D-'
        '''
        figure = self.XMLroot.name
        if self.XMLkind in CHORD_TYPES.keys():
            figure += CHORD_TYPES[self.XMLkind][0]
        if self.XMLroot.name != self.XMLbass.name:
            figure+='/' + self.XMLbass.name
        
        for csmod in self.chordStepModifications:
            if csmod.modType != 'alter':
                figure += ' ' + csmod.modType + ' ' + str(csmod.degree)
            else:
                figure += ' ' + csmod.modType + ' ' + csmod.interval.simpleName
        
        return figure
    
    def _getKindFromShortHand(self, sH):
        
        if 'add' in sH:
            sH = sH[0:sH.index('add')]
        elif 'omit' in sH:
            sH = sH[0:sH.index('omit')]
    
        for chordType in CHORD_TYPES:
            for charString in CHORD_TYPES[chordType]:
                if sH == charString:
                    self.XMLkind = chordType
                    return sH.replace(charString,'')
        return sH

    
    
    def _realizePitches(self):
        '''calculate the pitches in the chord symbol and update all associated
        variables, including bass, root, inversion and chord

        >>> from music21 import *
        >>> harmony.ChordSymbol(root='C', bass='E', kind='major').pitches
        [E3, G3, C4]
        >>> harmony.ChordSymbol(root='C', bass='G', kind='major').pitches
        [G2, C3, E3]
        >>> harmony.ChordSymbol(root='C', kind='minor').pitches
        [C3, E-3, G3]
        
        >>> harmony.ChordSymbol(root='C', bass='B', kind='major-ninth').pitches
        [B1, D2, C3, E3, G3]
        
        >>> harmony.ChordSymbol(root='D', bass='F', kind='minor-seventh').pitches
        [F3, A3, C4, D4]
        '''
        nineElevenThirteen = ['dominant-ninth', 'major-ninth', 'minor-ninth','dominant-11th', 'major-11th', 'minor-11th','dominant-13th', 'major-13th', 'minor-13th']


        fbScale = realizerScale.FiguredBassScale(self.XMLroot, 'major' ) #create figured bass scale with root as scale
        self._chord.root(copy.deepcopy(self.XMLroot))
        self._chord.root().octave = 3 #render in the 3rd octave by default
    
        if self._notationString():
            pitches = fbScale.getSamplePitches(self._chord.root(), self._notationString())
            pitches.pop(0) #remove duplicated bass note due to figured bass method.
        else:
            tempRoot = self.XMLroot
            tempRoot.octave = 3
            pitches = []
            pitches.append(tempRoot)
        
        pitches = self._adjustOctaves(pitches)
        
        inversionNum = 0
        if self.XMLbass != self.XMLroot: 
            self._chord.bass(copy.deepcopy(self.XMLbass))
            inversionNum = self._chord.inversion()
            if not self.inversionIsValid(inversionNum):
                #there is a bass, yet no normal inversion was found....must be added note 
                
                inversionNum = 0
                self._chord.bass().octave = 2 #arbitrary octave, must be below root, which was arbitrarily chosen as 3 above
                pitches.append(self._chord.bass())
        elif self.XMLinversion:
            inversionNum = self.XMLinversion

        if inversionNum != 0:
            index = -1
            for p in pitches[0:inversionNum]:
                index = index + 1
                if self.XMLkind in nineElevenThirteen:
                    p.octave = p.octave + 2 #bump octave up by two for nineths,elevenths, and thirteenths
                    #this creates more spacing....
                else:
                    p.octave = p.octave + 1 #only bump up by one for triads and sevenths.

            #if after bumping up the octaves, there are still pitches below bass pitch
            #bump up their octaves
            bassPitch = pitches[inversionNum]
            self._chord.bass(bassPitch)
            for p in pitches:
                if p.diatonicNoteNum < bassPitch.diatonicNoteNum:
                    p.octave = p.octave + 1
            
        for pitch, degree in zip(pitches, self._degreesList):
            self._pitchesAndDegrees.append([pitch, degree])
            
        pitches = self._adjustPitchesForChordStepModifications(pitches)

        while self._hasPitchAboveC4(pitches) :
            i = -1
            for pitch in pitches:
                i = i + 1
                temp = str(pitch.name) + str((pitch.octave - 1))
                pitches[i] = music21.pitch.Pitch(temp)
        
        #but if this has created pitches below lowest note (the A 3 octaves below middle C)
        #on a standard piano, we're going to have to bump all the octaves back up
        while self._hasPitchBelowA1(pitches) :
            i = -1
            for pitch in pitches:
                i = i + 1
                temp = str(pitch.name) + str((pitch.octave + 1))
                pitches[i] = music21.pitch.Pitch(temp)   
        
        self._chord.pitches = pitches
        self._chord = self._chord.sortDiatonicAscending()
        
        
    def inversionIsValid(self, inversion):
        '''
        returns true if the provided inversion is exists for the given pitches of the chord. If not, it returns
        false and the getPitches method then appends the bass pitch to the chord.
        '''

        sevenths = ['dominant', 'major-seventh', 'minor-seventh', \
                    'diminished-seventh', 'augmented-seventh', 'half-diminished', 'major-minor', \
                    'Neapolitan', 'Italian', 'French', 'German', 'Tristan']
        ninths = ['dominant-ninth', 'major-ninth', 'minor-ninth']
        elevenths = ['dominant-11th', 'major-11th', 'minor-11th']
        thirteenths = ['dominant-13th', 'major-13th', 'minor-13th']

        if inversion == 5 and (self.XMLkind in thirteenths or self.XMLkind in elevenths):
            return True
        elif inversion == 4 and (self.XMLkind in elevenths or self.XMLkind in thirteenths or self.XMLkind in ninths):
            return True
        elif inversion == 3 and (self.XMLkind in sevenths or self.XMLkind in ninths or self.XMLkind in elevenths or self.XMLkind in thirteenths):
            return True
        elif (inversion == 2 or inversion == 1) and not self.XMLkind == 'pedal':
            return True
        else:
            return False
            
        
    def _adjustPitchesForChordStepModifications(self, pitches):
        '''
        degree-value element: indicates degree in chord, positive integers only
        degree-alter: indicates semitone alteration of degree, positive and negative integers only
        degree-type: add, alter, or subtract
            if add: 
                degree-alter is relative to a dominant chord (major and perfect intervals except for a minor seventh)
            if alter or subtract:
                degree-alter is relative to degree already in the chord based on its kind element
        
        <!-- FROM XML DOCUMENTATION
        http://www.google.com/codesearch#AHKd_kdk32Q/trunk/musicXML/dtd/direction.mod&q=Chord%20Symbols%20package:http://bmml%5C.googlecode%5C.com&l=530
        The degree element is used to add, alter, or subtract
        individual notes in the chord. The degree-value element
        is a number indicating the degree of the chord (1 for
        the root, 3 for third, etc). The degree-alter element
        is like the alter element in notes: 1 for sharp, -1 for
        flat, etc. The degree-type element can be add, alter, or
        subtract. If the degree-type is alter or subtract, the
        degree-alter is relative to the degree already in the
        chord based on its kind element. If the degree-type is
        add, the degree-alter is relative to a dominant chord
        (major and perfect intervals except for a minor
        seventh). The print-object attribute can be used to
        keep the degree from printing separately when it has
        already taken into account in the text attribute of
        the kind element. The plus-minus attribute is used to
        indicate if plus and minus symbols should be used
        instead of sharp and flat symbols to display the degree
        alteration; it is no by default. The degree-value and
        degree-type text attributes specify how the value and
        type of the degree should be displayed.

        A harmony of kind "other" can be spelled explicitly by
        using a series of degree elements together with a root.
        -->
        
        '''

        ChordStepModifications = self.chordStepModifications
        if ChordStepModifications != None:
            for hD in ChordStepModifications:
                
                sc = music21.scale.MajorScale(self._chord.root())
                if hD.modType == 'add':
                    if self._chord.bass() != None:
                        p = sc.pitchFromDegree(hD.degree, self._chord.bass())
                    else:
                        p = sc.pitchFromDegree(hD.degree, self._chord.root())
                    if hD.degree == 7 and self.XMLkind != None and self.XMLkind!= '':
                        #don't know why anyone would want
                        #to add a seventh to a dominant chord already...but according to documentation
                        #added degrees are relative to dominant chords, which have all major degrees
                        #except for the seventh which is minor, thus the transposition down one half step
                        p = p.transpose(-1)
                        self._degreesList.append('-7')
                        degreeForList = '-7'
                    else:
                        self._degreesList.append(hD.degree)
                        degreeForList = str(hD.degree)
                    #adjust the added pitch by degree-alter interval
                    if hD.interval:
                        p = p.transpose(hD.interval)
                    pitches.append(p)
                    self._pitchesAndDegrees.append([p, degreeForList] )
                elif hD.modType == 'subtract':
                    pitchFound = False
                    degrees = self._degreesList
                    if degrees != None:
                        for pitch, degree in zip(pitches, degrees):
                            degree = degree.replace('-','')
                            degree = degree.replace('#','')
                            degree = degree.replace('A','')#A is for 'Altered'
                            if hD.degree == int(degree):
                                pitches.remove(pitch)
                                pitchFound = True
                                for entry in self._pitchesAndDegrees:
                                    if str(hD.degree) in entry[1]:
                                        self._pitchesAndDegrees.remove(entry)
                                for degreeString in self._degreesList:
                                    if str(hD.degree) in degreeString:
                                        self._degreesList.remove(degreeString)
                                        
                                        break
                                #if hD.degree not in string, 
                                #should we throw an exception???? for now yes, but maybe later we
                                #will be more lenient....
                        if pitchFound == False:
                            raise ChordStepModificationException('Degree not in specified chord: %s' % hD.degree)     
                elif hD.modType == 'alter':
                    pitchFound = False
                    degrees = self._degreesList
                    
                    for pitch, degree in zip(pitches, degrees):
                        degree = degree.replace('-','')
                        degree = degree.replace('#','')
                        degree = degree.replace('A','') #A is for 'Altered'
                        if hD.degree == int(degree):
                            pitch = pitch.transpose(hD.interval) #transpose by semitones (positive for up, negative for down)
                            pitchFound = True
                            for entry in self._pitchesAndDegrees:
                                if hD.degree == entry[1]:
                                    entry[1] = 'A' + str(hD.degree)
                            for degreeString in self._degreesList:
                                if str(hD.degree) in degreeString:
                                    self._degreesList = self._degreesList.replace(degreeString, ('A' + str(hD.degree)))
                                    #the 'A' stands for altered...
                                    break
                            #if hD.degree not in string:
                            #should we throw an exception???? for now yes, but maybe later we should....
                                
                    if pitchFound == False:
                        raise ChordStepModificationException('Degree not in specified chord: %s' % hD.degree)                
        return pitches
        
    def _hasPitchAboveC4(self, pitches):
        for pitch in pitches:
            if pitch.diatonicNoteNum > 30: #if there are pitches above middle C, bump the octave down
                return True
        return False

    def _hasPitchBelowA1(self, pitches):
        for pitch in pitches:
            if pitch.diatonicNoteNum < 13: #anything below this is just obnoxious
                return True
        return False
                
                
    def _adjustOctaves(self, pitches):
        #do this for all ninth, thirteenth, and eleventh chords...
        #this must be done to get octave spacing right
        #possibly rewrite figured bass function with this integrated????....
        ninths = ['dominant-ninth', 'major-ninth', 'minor-ninth']
        elevenths = ['dominant-11th', 'major-11th', 'minor-11th']
        thirteenths = ['dominant-13th', 'major-13th', 'minor-13th']
  
        if self.XMLkind in ninths:
            pitches[1] = pitch.Pitch(pitches[1].name + str(pitches[1].octave + 1))
        elif self.XMLkind in elevenths:
            pitches[1] = pitch.Pitch(pitches[1].name + str(pitches[1].octave + 1))
            pitches[3] = pitch.Pitch(pitches[3].name + str(pitches[3].octave + 1))
            
        elif self.XMLkind in thirteenths:
            pitches[1] = pitch.Pitch(pitches[1].name + str(pitches[1].octave + 1))
            pitches[3] = pitch.Pitch(pitches[3].name + str(pitches[3].octave + 1))
            pitches[5] = pitch.Pitch(pitches[5].name + str(pitches[5].octave + 1))
        else:
            return pitches
        c = music21.chord.Chord(pitches) 
        c = c.sortDiatonicAscending()

        return c.pitches

    def _notationString(self):
        '''returns NotationString of ChordSymbolObject which dictates which scale
        degrees and how those scale degrees are altered in this chord'''
        notationString = ""

        kind = self.XMLkind

        if kind == 'major':
            notationString =  '1,3,5'
        elif kind == 'minor':
            notationString =  '1,-3,5'
        elif kind == 'augmented':
            notationString =  '1,3,#5'
        elif kind == 'diminished':
            notationString =  '1,-3,-5'
        elif kind == 'dominant':
            notationString = '1,3,5,-7'
        elif kind == 'major-seventh':
            notationString = '1,3,5,7'
        elif kind == 'minor-seventh':
            notationString = '1,-3,5,-7'
        elif kind == 'diminished-seventh':
            notationString = '1,-3,-5,--7'
        elif kind == 'augmented-seventh':
            notationString = '1,3,#5,-7'
        elif kind == 'half-diminished':
            notationString = '1,3,-5,-7'
        elif kind == 'major-minor' or kind == 'minor-major':
            notationString = '1,-3,5,7'
        elif kind == 'major-sixth':
            notationString = '1,3,5,6'
        elif kind == 'minor-sixth':
            notationString = '1,-3,5,6'
        elif kind == 'dominant-ninth':
            notationString = '1,3,5,-7,9'
        elif kind == 'major-ninth':
            notationString = '1,3,5,7,9'
        elif kind == 'minor-ninth':
            notationString = '1,-3,5,-7,9'
        elif kind == 'dominant-11th':
            notationString = '1,3,5,-7,9,11'
        elif kind == 'major-11th':
            notationString = '1,3,5,7,9,11'
        elif kind == 'minor-11th':
            notationString = '1,-3,5,-7,9,11'
        elif kind == 'dominant-13th':
            notationString = '1,3,5,-7,9,11,13'
        elif kind == 'major-13th':
            notationString = '1,3,5,7,9,11,13'
        elif kind == 'minor-13th':
            notationString = '1,-3,5,-7,9,11,13'
        elif kind == 'suspended-second':
            notationString = '1,2,5'
        elif kind == 'suspended-fourth':
            notationString = '1,4,5'
        elif kind == 'Neapolitan':
            notationString = '1,2-,3,5-'
        elif kind == 'Italian':
            notationString = '1,#4,-6'
        elif kind == 'French':
            notationString = '1,2,#4,-6'
        elif kind == 'German':
            notationString = '1,-3,#4,-6'
        elif kind == 'pedal':
            notationString = '1' #returns two identical pitches...weird. 
        elif kind == 'power':
            notationString = '1,5' #also returns two identical bass pitches...weird. 
        elif kind == 'Tristan' or kind == 'tristan':
            notationString =  '1,#4,#6,#9'
        else:
            notationString = '' #for kind of 'other' or 'none' where chord is explicity spelled out with add/alter Harmony Degrees
        degrees = notationString.replace(',', ' ')
        self._degreesList = degrees.split()

        return notationString

#-------------------------------------------------------------------------------

class Test(unittest.TestCase):
    
    def runTest(self):
        pass

    def testBasic(self):
        from music21 import harmony
        h = harmony.Harmony()
        hd = harmony.ChordStepModification('add', 4)
        h.addChordStepModification(hd)
        self.assertEqual(len(h.chordStepModifications), 1)
    
    def testCountHarmonicMotion(self):
        from music21 import converter
        s = converter.parse('http://wikifonia.org/node/8859')
        harms = s.flat.getElementsByClass('Harmony')
        
        totMotion = [0,0,0,0,0,0,0,0,0,0,0,0]
        totalHarmonicMotion = 0
        lastHarm = None
        
        for thisHarm in harms:
            if lastHarm is None:
                lastHarm = thisHarm
            else:
                if lastHarm.XMLbass is not None:
                    lastBass = lastHarm.XMLbass
                else:
                    lastBass = lastHarm.XMLroot
                    
                if thisHarm.XMLbass is not None:
                    thisBass = thisHarm.XMLbass
                else:
                    thisBass = thisHarm.XMLroot
                    
                if lastBass.pitchClass == thisBass.pitchClass:
                    pass
                else:
                    halfStepMotion = (lastBass.pitchClass - thisBass.pitchClass) % 12
                    totMotion[halfStepMotion] += 1
                    totalHarmonicMotion += 1
                    lastHarm = thisHarm
                    
        if totalHarmonicMotion == 0:
            vector = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        else:
            totHarmonicMotionFraction = [0.0, 0,0, 0,0,0, 0,0,0, 0,0,0]
            for i in range(1, 12):
                totHarmonicMotionFraction[i] = float(totMotion[i]) / totalHarmonicMotion
            vector = totHarmonicMotionFraction

        self.assertEqual( len(vector), 12)


class TestExternal(unittest.TestCase):
    def runTest(self):
        pass
    
    def testReadInXML(self):  
        from music21 import harmony
        from music21 import corpus
        testFile = corpus.parse('leadSheet/fosterBrownHair.xml')
        testFile = harmony.realizeChordSymbolDurations(testFile)
       
        chordSymbols = testFile.flat.getElementsByClass(harmony.ChordSymbol)
        s = music21.stream.Stream()

        for cS in chordSymbols:
            s.append(cS.chord)
            
        csChords = s.flat.getElementsByClass(chord.Chord)
        self.assertEqual(len(csChords), 40)

    def testChordRealization(self):
        from music21 import harmony, corpus
        #There is a test file under demos called ComprehensiveChordSymbolsTestFile.xml
        #that should contain a complete iteration of tests of chord symbol objects
        #this test makes sure that no error exists, and checks that 57 chords were
        #created out of that file....feel free to add to file if you find missing
        #tests, and adjust 57 accordingly
        testFile = corpus.parse('demos/ComprehensiveChordSymbolsTestFile.xml')
    
        testFile = harmony.realizeChordSymbolDurations(testFile)
        chords = testFile.flat.getElementsByClass(harmony.ChordSymbol)
        
        s = music21.stream.Stream()
        for x in chords:
            s.append(x.chord)
            
        csChords = s.flat.getElementsByClass(chord.Chord)
        self.assertEqual(len(csChords), 57)

    #def realizeCSwithFB(self):
    #see demos.bhadley.HarmonyRealizer
        

#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Harmony, ChordStepModification, ChordSymbol]


if __name__ == "__main__":
    music21.mainTest(Test, TestExternal)
    
    #test = music21.harmony.Test()
    #test.testCountHarmonicMotion()
    
    #test = music21.harmony.TestExternal()
    #test.testChordRealization()
    
#------------------------------------------------------------------------------
# eof

