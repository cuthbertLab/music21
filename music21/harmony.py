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
An object representation of harmony, a subclass of chord, as encountered as chord symbols or 
roman numerals, or other chord representations with a defined root.
'''

import unittest

import music21
from music21 import common
from music21 import pitch
#from music21 import roman
from music21 import interval
from music21 import chord


import re
import copy

from music21 import environment
from music21.figuredBass import realizerScale


_MOD = "harmony.py"
environLocal = environment.Environment(_MOD)

CHORD_TYPES = {
             'major': ['', 'Maj'] , 
             'minor': ['m', 'min'] ,
             'augmented' : ['+', '#5'] , 
             'diminished' : ['dim', 'o'] ,
             'dominant' : ['7'],
             'major-seventh' : [  'Maj7','M7'],
             'minor-seventh' : ['m7' , 'min7'] ,
             'diminished-seventh' : [ 'o7', 'dim7'] ,
             'augmented-seventh' : ['7+', '7#5'] ,
             'half-diminished' : ['/o7','m7b5'] ,
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
               
    >>> from music21 import *
    >>> hd = harmony.ChordStepModification('add', 4)
    >>> hd
    <music21.harmony.ChordStepModification modType=add degree=4 interval=None>
    >>> hd = harmony.ChordStepModification('alter', 3, 1)
    >>> hd
    <music21.harmony.ChordStepModification modType=alter degree=3 interval=<music21.interval.Interval A1>>

    '''
    ''' FROM MUSIC XML DOCUMENTATION - FOR DEVELOPER'S REFERENCE
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
class Harmony(chord.Chord):
    '''
    >>> from music21 import *
    >>> h = harmony.ChordSymbol() 
    >>> h.XMLroot = 'b-'
    >>> h.XMLbass = 'd'
    >>> h.XMLinversion = 1
    >>> h.addChordStepModification(harmony.ChordStepModification('add', 4))
    >>> h
    <music21.harmony.ChordSymbol B-/D add 4>
    >>> p = harmony.ChordSymbol(root='C', bass='E', kind = 'major')
    >>> p
    <music21.harmony.ChordSymbol C/E>
    
    Harmony objects in music21 are a special type of chord - they retain all the same functionality as a chord (and
    inherit from chord directly), although they have special representations symbolically. They contain a figure 
    representation, a shorthand, for the actual pitches they contain. This shorthand is commonly used on musical
    scores rather than writing out the chord pitches. Thus, each harmony object has an attribute, self.writeAsChord
    that dictates whether the object will be written to a score as a chord (with pitches realized) or with just the 
    figure (as in Chord Symbols).
    
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
        
        _DOC_ATTR = {
    'writeAsChord': 'Boolean attribute of all harmony objects \
    that specifies how this object will be written to the musicxml of a stream. If true (default for romanNumerals), \
    the chord with pitches is written. If False (default for ChordSymbols) the harmony symbol is written'
    }
        self._writeAsChord = False
        chord.Chord.__init__(self)
        self._XMLroot = None # a pitch object
        self._XMLbass = None # a pitch object

        self._XMLinversion = None # an integer
        #self = music21.chord.Chord()
        
        #TODO: deal with the roman numeral property of harmonies...music xml documentation is ambiguous: 
        #A root is a pitch name like C, D, E, where a function is an 
        #indication like I, II, III. It is an either/or choice to avoid data inconsistency.    
        self._roman = None # a romanNumeral numeral object, musicxml stores this within a node called <function> which might conflict with the Harmony...
                  
        # specify an array of degree alteration objects
        self.chordStepModifications = []
        self._degreesList = []
        self._pitchesAndDegrees = []
        
        for kw in keywords:
            if kw == 'root':
                if common.isStr(keywords[kw]):
                    self._XMLroot = music21.pitch.Pitch(keywords[kw])
                else:
                    self._XMLroot = keywords[kw]
            elif kw == 'bass':
                if common.isStr(keywords[kw]):
                    self._XMLbass = music21.pitch.Pitch(keywords[kw])
                else:
                    self._XMLbass = keywords[kw]
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
            self._parseFigure()
        if self._figure is not None or self._XMLroot or self._XMLbass:
            self._updatePitches()
            
    def _setWriteAsChord(self, val):
        self._writeAsChord =  val
        try:
            self._updatePitches()
        except:
            pass
        if val and self.duration.quarterLength == 0:
            self.duration = music21.duration.Duration(1)
            
    def _getWriteAsChord(self):
        return self._writeAsChord
    
    writeAsChord = property( _getWriteAsChord, _setWriteAsChord)
            
    def _getFigure(self):
        if self._figure == None:
            return self.findFigure()
        else:
            return self._figure
        
    def _setFigure(self, value):
        self._figure = value
        if self._figure is not None:
            self._parseFigure(self._figure)
            self._updatePitches()
            
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
        if self.writeAsChord:
            return '<music21.harmony.%s %s>' % (self.__class__.__name__, self.pitches)
        else:
            return '<music21.harmony.%s %s>' % (self.__class__.__name__, self.figure)
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
    #def _updatePitches(self):
    #    '''method must be overridden in each subclass of Harmony because each harmony object uses
    #    a different method to extract pitches form the harmony symbol'''
    #    pass
    
    #def _parseFigure(self):
     #   '''method must be overriden in each subclass of Harmony because each harmony object 
     #   uses a different method to parse the figure'''
     #   pass
    
#    def _setChord(self, value):
#        if hasattr(value, 'classes') and 'Chord' in value.classes:
#            self._chord = value
#            return
#        try: # try to create 
#            self._chord = chord.Chord(value)
#            return
#        except music21.Music21Exception: 
#            pass
#        raise HarmonyException('not a valid music21 chord specification: %s' % value)
#
#
#    def _getChord(self):
#        if self._chord.pitches == []: #and self.XMLroot:
#            self._updatePitches()   
#        return self._chord
#
#    chord = property(_getChord, _setChord, doc = '''
#        Get or set the chord object of this harmony object. The chord object will
#        be returned with the realized pitches as an attribute. The user could 
#        override these pitches by manually setting chord.pitches.
#
#
#        ''')
    
      
    
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

#    def getPitchesAndDegrees(self):
#        '''pitchesAndDegrees is the compiled list of the pitches in the chord and their 
#        respective degrees (with alterations, a '-' for flat, a '#' for sharp, and an 'A'
#        for altered. It is a list of lists of two units, the pitch and the degree. The list is 
#        not ordered.
#        
#        >>> from music21 import *
#        >>> h = harmony.ChordSymbol('CMaj7')
#        >>> h.getPitchesAndDegrees()
#        [[C3, '1'], [E3, '3'], [G3, '5'], [B3, '7']]
#        
#        >>> h = harmony.ChordSymbol('Dm7/Fomit5')
#        >>> h.getPitchesAndDegrees()
#        [[D4, '1'], [F3, '-3'], [C4, '-7']]
#        
#        >>> h = harmony.ChordSymbol('Dm7/F')
#        >>> h.getPitchesAndDegrees()
#        [[D4, '1'], [F3, '-3'], [A3, '5'], [C4, '-7']]
#        '''
#        #just update octaves here
#        
#        for pitch, pitchAndDegree in zip(self.pitches, self._pitchesAndDegrees):
#            if pitch.name == pitchAndDegree[0]:
#                pitchAndDegree[0] = pitch
#        return self._pitchesAndDegrees
#    
#    def getDegrees(self):
#        '''Return list of all the degrees associated with the pitches of the Harmony Chord
#        
#        >>> from music21 import *
#        >>> h = harmony.ChordSymbol('Dm7/F')
#        >>> h.getDegrees()
#        ['1', '-3', '5', '-7']
#        '''
#        if self.pitches == []:
#            self._updatePitches()
#        return self._degreesList


    def _setRoot(self, value):
        if hasattr(value, 'classes') and 'Pitch' in value.classes:
            self._XMLroot = value
            self.root(self._XMLroot )
            return
        try: # try to create a Pitch object
            self._XMLroot = pitch.Pitch(value)
            self.root(self._XMLroot )
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
            self.bass(self._XMLbass )
            return
        try: # try to create a Pitch object
            self._XMLbass = pitch.Pitch(value)
            self.bass(self._XMLbass )
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
    
#    def __getattr__(self, attr):
#        try:
#            return getattr(self.chord, attr)
#        except:
#            raise HarmonyException('not a valid method or attribute call: %s' % attr)
        
        

    #---------------------------------------------------------------------------
    #TODO: move this attribute to roman class which inherets from harmony.Harmony objects
    def _setRoman(self, value):
        if hasattr(value, 'classes') and 'RomanNumeral' in value.classes:
            self._roman = value
            return
        try: # try to create
            self._roman = music21.roman.RomanNumeral(value)
            return
        except music21.Music21Exception:
            pass
        raise HarmonyException('not a valid pitch specification: %s' % value)

    def _getRoman(self):
        if self._roman is None:
            from music21 import roman
            self._roman = roman.romanNumeralFromChord(self)
        
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



'''XML DESCRIPTION OF CHORD SYMBOLS:
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
    
    All :class:`~music21.harmony.ChordSymbol` inherit from :class:`~music21.chord.Chord` so you can
    consider these objects as chords, although they have a unique representation in a score. ChordSymbols,
    unlike chords, by default appear as chord symbols in a score and have duration of 0.
    To obtain the chord representation of the in the score, change the 
    :attr:`music21.harmony.ChordSymbol.writeAsChord` to True. Unless otherwise specified, the duration
    of this chord object will become 1.0. If you have a leadsheet, run 
    :meth:`music21.harmony.realizeChordSymbolDurations` on the stream to assign the correct (according to
    offsets) duration to each harmony object.)
    
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
    [C3, E-3, G-3, B-3]
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
    
    The '-' symbol and the 'b' symbol are interchangeable, they correspond to flat, not minor.
    
    >>> harmony.ChordSymbol('Am').pitches
    [A2, C3, E3]
    >>> harmony.ChordSymbol('Abm').pitches
    [A-2, C-3, E-3]
    >>> harmony.ChordSymbol('A-m').pitches
    [A-2, C-3, E-3]
    >>> harmony.ChordSymbol('F-dim7').pitches
    [F-2, A--2, C--3, E---3]
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
        if 'duration' not in keywords and 'quarterLength' not in keywords:  
            self.duration = music21.duration.Duration(0)
    
    #def __repr__(self):
    #    return '<music21.harmony.%s %s>' % (self.__class__.__name__, self.figure)
#        if len(self.chordStepModifications) == 0:
#            return '<music21.harmony.%s kind=%s (%s) root=%s bass=%s inversion=%s duration=%s>' % \
#                (self.__class__.__name__, self.XMLkind, self.XMLkindStr, self.XMLroot, self.XMLbass, \
#                 self.XMLinversion, self.duration.quarterLength)
#        else:
#            return '<music21.harmony.%s kind=%s (%s) root=%s bass=%s inversion=%s duration=%s ChordStepModifications=%s>' %\
#                 (self.__class__.__name__, self.XMLkind, self.XMLkindStr, self.XMLroot, self.XMLbass, self.XMLinversion, \
#                  self.duration.quarterLength,''.join([str(x) for x in self.chordStepModifications]))
#---------------------------------------------------------------------------

    

    def _parseFigure(self):
        '''
        translate the figure string (regular expression) into a meaningful Harmony object 
        by identifying the root, bass, inversion, kind, and kindStr.
        
        Examples of figures (could include spaces in these figures or not, 
        case is not sensitive except in the case of 'M' or 'm') all examples have C as root
                
        Triads:
            major (major third, perfect fifth)                           C        
            minor (minor third, perfect fifth)                           Cm        Cmin
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
        prelimFigure = self.figure
        prelimFigure = re.sub(r'\s', '', prelimFigure)

        #Get Root:
        if ',' in prelimFigure:
            root = prelimFigure[0:prelimFigure.index(',')]
            st = prelimFigure.replace(',','')
            st = st.replace(root,'')
            prelimFigure = prelimFigure.replace(',','')
        else:
            m1 = re.match(r"[A-Ga-g][b#-]?", prelimFigure) #match not case sensitive, 
            if m1:
                root = m1.group()
                st = prelimFigure.replace(m1.group(), '')  #remove the root and bass from the string and any additions/omitions/alterations/

        if root:
            if 'b' in root:
                root = root.replace('b', '-')
            self.root( pitch.Pitch(root) )
            self._XMLroot = pitch.Pitch(root)

        #Get optional Bass:
        m2 = re.search(r"/[A-Ga-g][b#]?", prelimFigure) #match not case sensitive
        remaining = st
        if m2:
            bass = m2.group()

            if 'b' in bass:
                bass = bass.replace('b', '-')
   
            bass = bass.replace('/', '')
            self.bass ( pitch.Pitch(bass) ) 
            self._XMLbass = pitch.Pitch(bass)     
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
        
        Needs development - TODO: chord step modifications need actual pitches rather than numeric degrees
        
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
                figure += ' ' + csmod.modType +  ' ' + str(csmod.degree)
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
    
    def _updatePitches(self):
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
        
        if self.XMLroot == None or self.XMLkind == None:
            return

        fbScale = realizerScale.FiguredBassScale(self.XMLroot, 'major' ) #create figured bass scale with root as scale
        self.root(copy.deepcopy(self.XMLroot))
        self.root().octave = 3 #render in the 3rd octave by default
    
        if self._notationString():
            pitches = fbScale.getSamplePitches(self.root(), self._notationString())
            pitches.pop(0) #remove duplicated bass note due to figured bass method.
        else:
            tempRoot = self.XMLroot
            tempRoot.octave = 3
            pitches = []
            pitches.append(tempRoot)
        
        pitches = self._adjustOctaves(pitches)
        
        inversionNum = 0
        if self.XMLbass != self.XMLroot: 
            self.bass(copy.deepcopy(self.XMLbass))
            inversionNum = self.inversion()
            if not self.inversionIsValid(inversionNum):
                #there is a bass, yet no normal inversion was found....must be added note 
                
                inversionNum = 0
                self.bass().octave = 2 #arbitrary octave, must be below root, which was arbitrarily chosen as 3 above
                pitches.append(self.bass())
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

            self.bass(bassPitch)
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
        
        self.pitches = pitches
        junk = self.sortDiatonicAscending(inPlace=True)
        
        
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
                
                sc = music21.scale.MajorScale(self.root())
                if hD.modType == 'add':
                    if self.bass() != None:
                        p = sc.pitchFromDegree(hD.degree, self.bass())
                    else:
                        p = sc.pitchFromDegree(hD.degree, self.root())
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
            notationString = '1,-3,-5,-7'
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
    
def realizeChordSymbolDurations(piece):
    '''Returns music21 stream with duration attribute of chord symbols correctly set. 
    Duration of chord symbols is based on the surrounding chord symbols; The chord symbol
    continues duration until another chord symbol is located or the piece ends. Useful for 
    

    >>> from music21 import *
    >>> s = stream.Score()
    >>> s.append(harmony.ChordSymbol('C'))
    >>> s.repeatAppend(note.Note('C'), 4)
    >>> s.append(harmony.ChordSymbol('C'))
    >>> s.repeatAppend(note.Note('C'), 4)
    >>> s = s.makeMeasures()

    >>> harmony.realizeChordSymbolDurations(s).show('text')
    {0.0} <music21.clef.BassClef>
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
    {0.0} <music21.clef.BassClef>
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
    {0.0} <music21.clef.BassClef>
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
    onlyChords = pf.getElementsByClass(ChordSymbol)

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

class Test(unittest.TestCase):
    
    def runTest(self):
        pass


    def testChordAttributes(self):
        from music21 import harmony
        cs = harmony.ChordSymbol('Cm')
        self.assertEqual(str(cs), '<music21.harmony.ChordSymbol Cm>')
        self.assertEqual(str(cs.pitches), '[C3, E-3, G3]')
        self.assertEqual(str(cs.bass()), 'C3')
        self.assertEqual(cs.isConsonant(), True)
        
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
        
        
        testFile.show('text')
        testFile = harmony.realizeChordSymbolDurations(testFile)
        #testFile.show()
        chordSymbols = testFile.flat.getElementsByClass(harmony.ChordSymbol)
        s = music21.stream.Stream()
        
        for cS in chordSymbols:
            cS.writeAsChord = False
            s.append(cS)
            
        #csChords = s.flat.getElementsByClass(chord.Chord)
        #s.show()
        #self.assertEqual(len(csChords), 40)
#
    def testChordRealization(self):
        from music21 import harmony, corpus, note
        #There is a test file under demos called ComprehensiveChordSymbolsTestFile.xml
        #that should contain a complete iteration of tests of chord symbol objects
        #this test makes sure that no error exists, and checks that 57 chords were
        #created out of that file....feel free to add to file if you find missing
        #tests, and adjust 57 accordingly
        testFile = corpus.parse('demos/ComprehensiveChordSymbolsTestFile.xml')
    
        testFile = harmony.realizeChordSymbolDurations(testFile)
        chords = testFile.flat.getElementsByClass(harmony.ChordSymbol)
        #testFile.show()
        s = music21.stream.Stream()
#        i = 0
        for x in chords:
            # print x.pitchesu
            x.quarterLength = 0
            s.insert(x.offset, x)
            #i += 4
            
            #x.show()
        
        s.makeRests(fillGaps= True, inPlace=True)    
        s.append(note.Rest(quarterLength=4))
        csChords = s.flat.getElementsByClass(chord.Chord)
        #self.assertEqual(len(csChords), 57)
        #s.show()
        #s.show('text')
    #def realizeCSwithFB(self):
    #see demos.bhadley.HarmonyRealizer
        
    def testALLChordTypes(self):
        chordtypes = {'major': ['', 'Maj'] , 
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
             'Tristan' : ['tristan'] }
    
        notes = ['A', 'B', 'C', 'D','E','F','G']
        mod = ['','-','#']
        for n in notes:
            for m in mod:
                for key, val in chordtypes.items():
                    for type in val:
                        print n+m+','+type, music21.harmony.ChordSymbol(n+m+','+type).pitches
#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Harmony, ChordSymbol, ChordStepModification]


if __name__ == "__main__":
  
    music21.mainTest(Test)
    
    #test =  music21.harmony.TestExternal()
    #test.testChordRealization()
    
    #test = music21.harmony.Test()
    #test.testCountHarmonicMotion()
    
   # test = music21.harmony.TestExternal()
    #test.testReadInXML()
    
#------------------------------------------------------------------------------
# eof

