#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         note.py
# Purpose:      music21 classes for representing notes
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009-2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''Classes and functions for creating and manipulating notes, ties, and durations.

The :class:`~music21.pitch.Pitch` object is stored within, and used to configure, :class:`~music21.note.Note` objects.
'''

import copy
import unittest

import music21
from music21 import articulations
from music21 import common
from music21 import defaults
from music21 import duration
from music21 import instrument
from music21 import interval
from music21 import editorial
from music21.lily import LilyString
from music21 import musicxml as musicxmlMod
from music21.musicxml import translate as musicxmlTranslate
#from music21 import midi as midiModule
from music21.midi import translate as midiTranslate
from music21 import expressions
from music21 import pitch
from music21 import beam
from music21 import meter
from music21 import tie



from music21 import environment
_MOD = "note.py"  
environLocal = environment.Environment(_MOD)





#-------------------------------------------------------------------------------
class LyricException(Exception):
    pass


class Lyric(object):

    def __init__(self, text=None, number=1, syllabic=None):
        if not common.isStr(text):
            # do not want to do this unless we are sure this is not a string
            # possible might alter unicode or other string-like representations
            self.text = str(text)         
        else:
            self.text = text
        if not common.isNum(number):
            raise LyricException('Number best be number')
        self.number = number
        self.syllabic = syllabic # can be begin, middle, or end


    #---------------------------------------------------------------------------
    def _getMX(self):
        '''
        Returns an mxLyric

        >>> from music21 import *
        >>> a = note.Lyric()
        >>> a.text = 'hello'
        >>> mxLyric = a.mx
        >>> mxLyric.get('text')
        'hello'
        '''
        return musicxmlTranslate.lyricToMx(self)

    def _setMX(self, mxLyric):
        '''Given an mxLyric, fill the necessary parameters
        
        >>> from music21 import *
        >>> mxLyric = musicxml.Lyric()
        >>> mxLyric.set('text', 'hello')
        >>> a = Lyric()
        >>> a.mx = mxLyric
        >>> a.text
        'hello'
        '''
        musicxmlTranslate.mxToLyric(mxLyric, inputM21=self)

    mx = property(_getMX, _setMX)    






#-------------------------------------------------------------------------------
class GeneralNote(music21.Music21Object):
    '''A GeneralNote object is the base class object for the :class:`~music21.note.Note`, :class:`~music21.note.Rest`, :class:`~music21.note.Chord`, and related objects. 
    '''    
    isChord = False

    # define order to present names in documentation; use strings
    _DOC_ORDER = ['duration', 'quarterLength', 'editorial']
    # documentation for all attributes (not properties or methods)
    _DOC_ATTR = {
    'editorial': 'a :class:`~music21.editorial.NoteEditorial` object that stores editorial information (comments, harmonic information, ficta) and certain display information (color, hidden-state).',
    'isChord': 'Boolean read-only value describing if this object is a Chord.',
    'lyrics': 'A list of :class:`~music21.note.Lyric` objects.',
    'tie': 'either None or a :class:`~music21.note.Tie` object.'
    }    
    def __init__(self, *arguments, **keywords):
        tempDuration = duration.Duration(**keywords)
        music21.Music21Object.__init__(self, duration = tempDuration)
        self._duration = tempDuration

        # only apply default if components are empty
        # looking at private _components so as not to trigger
        # _updateComponents

        if self.duration.quarterLength == 0 and len(self.duration._components) == 0:
            self.duration.addDurationUnit(duration.DurationUnit('quarter'))

        self.lyrics = [] # a list of lyric objects
        self.expressions = []
        self.articulations = []
        self.editorial = editorial.NoteEditorial()

        # note: Chord inherits this object, and thus has one Tie object
        # chords may need Tie objects for each pitch
        self.tie = None # store a Tie object

    def compactNoteInfo(self):
        '''A debugging info tool, returning information about a note
        E- E 4 flat 16th 0.166666666667 & is a tuplet (in fact STOPS the tuplet)
        '''
        
        ret = ""
        if (self.isNote is True):
            ret += self.name + " " + self.step + " " + str(self.octave)
            if (self.accidental is not None):
                ret += " " + self.accidental.name
        elif (self.isRest is True):
            ret += "rest"
        else:
            ret += "other note type"
        if (self.tie is not None):
            ret += " (Tie: " + self.tie.type + ")"
        ret += " " + self.duration.type
        ret += " " + str(self.duration.quarterLength)
        if len(self.duration.tuplets) > 0:
            ret += " & is a tuplet"
            if self.duration.tuplets[0].type == "start":
                ret += " (in fact STARTS the tuplet)"
            elif self.duration.tuplets[0].type == "stop":
                ret += " (in fact STOPS the tuplet)"
        if len(self.expressions) > 0:
            if (isinstance(self.expressions[0], music21.expressions.Fermata)):
                ret += " has Fermata"
        return ret


    #---------------------------------------------------------------------------
    def _getColor(self):
        '''Return the Note color. 
        '''
        return self.editorial.color

    def _setColor(self, value): 
        '''should check data here
        uses this re: #[\dA-F]{6}([\dA-F][\dA-F])?
        No: because Lilypond supports "blue", "red" etc., as does CSS; musicxml also supports alpha

        >>> from music21 import *
        >>> a = note.GeneralNote()
        >>> a.duration.type = 'whole'
        >>> a.color = '#235409'
        >>> a.color
        '#235409'
        >>> a.editorial.color
        '#235409'

        '''
        self.editorial.color = value

    color = property(_getColor, _setColor)


    def _getLyric(self):
        '''
        returns the first Lyric's text
        
        todo: should return a \\n separated string of lyrics
        '''
        
        if len(self.lyrics) > 0:
            return self.lyrics[0].text
        else:
            return None

    def _setLyric(self, value): 
        '''
        
        TODO: should check data here
        should split \\n separated lyrics into different lyrics

        presently only creates one lyric, and destroys any existing
        lyrics

        >>> from music21 import *
        >>> a = note.GeneralNote()
        >>> a.lyric = 'test'
        >>> a.lyric
        'test'
        '''
        self.lyrics = [] 
        self.lyrics.append(Lyric(value))

    lyric = property(_getLyric, _setLyric, 
        doc = '''The lyric property can be used to get and set a lyric for this Note, Chord, or Rest. In most cases the :meth:`~music21.note.GeneralNote.addLyric` method should be used.
        ''')

    def addLyric(self, text, lyricNumber = None):
        '''Adds a lyric, or an additional lyric, to a Note, Chord, or Rest's lyric list. If `lyricNumber` is not None, a specific line of lyric text can be set. 

        >>> from music21 import *
        >>> n1 = note.Note()
        >>> n1.addLyric("hello")
        >>> n1.lyrics[0].text
        'hello'
        >>> n1.lyrics[0].number
        1
        
        >>> # note that the option number specified gives the lyric number, not the list position
        >>> n1.addLyric("bye", 3)
        >>> n1.lyrics[1].text
        'bye'
        >>> n1.lyrics[1].number
        3
        
        >>> # replace existing lyric
        >>> n1.addLyric("ciao", 3)
        >>> n1.lyrics[1].text
        'ciao'
        >>> n1.lyrics[1].number
        3
        '''
        if not common.isStr(text):
            text = str(text)
        if lyricNumber is None:
            maxLyrics = len(self.lyrics) + 1
            self.lyrics.append(Lyric(text, maxLyrics))
        else:
            foundLyric = False
            for thisLyric in self.lyrics:
                if thisLyric.number == lyricNumber:
                    thisLyric.text = text
                    foundLyric = True
                    break
            if foundLyric is False:
                self.lyrics.append(Lyric(text, lyricNumber))


    def hasLyrics(self):
        '''Return True if this object has any lyrics defined
        '''
        if len(self.lyrics) > 0:
            return True
        else:
            return False


    #---------------------------------------------------------------------------
    # properties common to Notes, Rests, 
    def _getQuarterLength(self):
        '''Return quarter length

        >>> from music21 import *
        >>> n = note.Note()
        >>> n.quarterLength = 2.0
        >>> n.quarterLength
        2.0
        '''
        return self.duration.quarterLength

    def _setQuarterLength(self, value):
        self.duration.quarterLength = value

    quarterLength = property(_getQuarterLength, _setQuarterLength, 
        doc = '''Return the Duration as represented in Quarter Length.

        >>> from music21 import *
        >>> n = note.Note()
        >>> n.quarterLength = 2.0
        >>> n.quarterLength
        2.0
        ''')

    #---------------------------------------------------------------------------
    def augmentOrDiminish(self, scalar, inPlace=True):
        '''Given a scalar greater than zero, return a Note with a scaled Duration. If `inPlace` is True, this is done in-place and the method returns None. If `inPlace` is False, this returns a modified deep copy.

        >>> from music21 import *
        >>> n = note.Note('g#')
        >>> n.quarterLength = 3
        >>> n.augmentOrDiminish(2)
        >>> n.quarterLength
        6

        >>> c = chord.Chord(['g#','A#','d'])
        >>> n.quarterLength = 2
        >>> n.augmentOrDiminish(.25)
        >>> n.quarterLength
        0.5

        >>> n = note.Note('g#')
        >>> n.augmentOrDiminish(-1)
        Traceback (most recent call last):
        NoteException: scalar must be greater than zero
        '''
        if not scalar > 0:
            raise NoteException('scalar must be greater than zero')

        if inPlace:
            post = self
        else:
            post = copy.deepcopy(self)

        # inPlace always True b/c we have already made a copy if necessary
        post.duration.augmentOrDiminish(scalar, inPlace=True)

        if not inPlace:
            return post
        else:
            return None


    #---------------------------------------------------------------------------
    def _getMusicXML(self):
        '''Return a complete musicxml representation as an xml string. This must call _getMX to get basic mxNote objects

        >>> from music21 import *
        >>> n = note.Note()
        >>> post = n._getMusicXML()
        '''
        return musicxmlTranslate.generalNoteToMusicXML(self)

    musicxml = property(_getMusicXML, 
        doc = '''Return a complete musicxml representation.
        ''')    



    #---------------------------------------------------------------------------
    def _preDurationLily(self):
        '''
        Method to return all the lilypond information that appears before the 
        duration number.
        Is the same for simple and complex notes.
        '''
        baseName = ""
        baseName += self.editorial.lilyStart()
        if self.pitch is not None:
            baseName += self.pitch.lilyNoOctave()
        elif (self.editorial.ficta is not None):
            baseName += self.editorial.ficta.lily
        octaveModChars = ""
        spio = self.pitch.implicitOctave
        if (spio < 3):
            correctedOctave = 3 - spio
            octaveModChars = ',' * correctedOctave #  C2 = c,  C1 = c,,
        else:
            correctedOctave = spio - 3
            octaveModChars  = '\'' * correctedOctave # C4 = c', C5 = c''  etc.
        baseName += octaveModChars
        if (self.editorial.ficta is not None):
            baseName += "!"  # always display ficta
        elif self.pitch is not None and self.pitch.accidental is not None:
            baseName += self.pitch.accidental.lilyDisplayType()
        return baseName

    _lilyInternalTieCharacter = '~' # will be blank for rests

    def _getLily(self):
        '''
        The name of the note as it would appear in Lilypond format.
        '''
        allNames = ""
        baseName = self._preDurationLily()
        if hasattr(self.duration, "components") and len(
            self.duration.components) > 0:
            for i in range(0, len(self.duration.components)):
                thisDuration = self.duration.components[i]            
                allNames += baseName
                allNames += thisDuration.lily
                allNames += self.editorial.lilyAttached()
                if (i != len(self.duration.components) - 1):
                    allNames += self._lilyInternalTieCharacter
                    allNames += " "
                if (i == 0): # first component
                    if self.lyric is not None: # hack that uses markup...
                        allNames += "_\markup { \"" + self.lyric + "\" } "
        else:
            allNames += baseName
            allNames += self.duration.lily
            allNames += self.editorial.lilyAttached()
            if self.lyric is not None: # hack that uses markup...
                allNames += "_\markup { \"" + self.lyric + "\" }\n "
                #allNames += "_\markup { \"" + self.lyric + "\" } "
            
        if (self.tie is not None):
            if (self.tie.type != "stop"):
                allNames += "~"
        if (self.expressions):
            for thisExpression in self.expressions:
                if dir(thisExpression).count('lily') > 0:
                    allNames += " " + thisNotation.lily

        allNames += self.editorial.lilyEnd()
        
        return LilyString(allNames)

    lily = property(_getLily, doc='''
        read-only property that returns a LilyString of the lilypond representation of
        a note (or via subclassing, rest or chord)
        
        >>> from music21 import *
        >>> n1 = note.Note("C#5")
        >>> n1.tie = tie.Tie('start')
        >>> n1.articulations = [articulations.Accent()]  ## DOES NOTHING RIGHT NOW
        >>> n1.quarterLength = 1.25
        >>> n1.lily
        cis''4~ cis''16~

        >>> r1 = note.Rest()
        >>> r1.duration.type = "half"
        >>> r1.lily
        r2
        
        >>> r2 = note.Rest()
        >>> r2.quarterLength = 1.25
        >>> r2.lily
        r4 r16
        
        >>> c1 = chord.Chord(["C#2", "E4", "D#5"])
        >>> c1.quarterLength = 2.5   # BUG: 2.333333333 doesnt work yet
        >>> c1.lily
        <cis, e' dis''>2~ <cis, e' dis''>8
        
    ''')




#-------------------------------------------------------------------------------
class NotRest(GeneralNote):
    '''
    Parent class for objects that are not rests; or, object that can be tied.
    '''
    
    # unspecified means that there may be a stem, but its orientation
    # has not been declared. 
    # TODO: import from MusicXML
    stemDirection = "unspecified"
    
    def __init__(self, *arguments, **keywords):
        GeneralNote.__init__(self, **keywords)


#-------------------------------------------------------------------------------
class NoteException(Exception):
    pass


#-------------------------------------------------------------------------------
class Note(NotRest):
    '''
    Note class for notes (not rests or unpitched elements) 
    that can be represented by one or more notational units

    A Note knows both its total duration and how to express itself as a set of 
    tied notes of different lengths. For instance, a note of 2.5 quarters in 
    length could be half tied to eighth or dotted quarter tied to quarter.
    '''

    isNote = True
    isUnpitched = False
    isRest = False
    
    # define order to present names in documentation; use strings
    _DOC_ORDER = ['duration', 'quarterLength', 'nameWithOctave', 'pitchClass']
    # documentation for all attributes (not properties or methods)
    _DOC_ATTR = {
    'isNote': 'Boolean read-only value describing if this object is a Note.',
    'isUnpitched': 'Boolean read-only value describing if this is Unpitched.',
    'isRest': 'Boolean read-only value describing if this is a Rest.',
    'beams': 'A :class:`~music21.beam.Beams` object.',
    'pitch': 'A :class:`~music21.pitch.Pitch` object.',
    }

    # Accepts an argument for pitch
    def __init__(self, *arguments, **keywords):
        NotRest.__init__(self, **keywords)

        if len(arguments) > 0:
            if isinstance(arguments[0], pitch.Pitch):
                self.pitch = arguments[0]
            else: # assume first arg is pitch
                self.pitch = pitch.Pitch(arguments[0]) 
        else: # supply a default pitch
            self.pitch = pitch.Pitch('C4')

        if "beams" in keywords:
            self.beams = keywords["beams"]
        else:
            self.beams = beam.Beams()

    #---------------------------------------------------------------------------
    # operators, representations, and transformatioins

    def __repr__(self):
        return "<music21.note.Note %s>" % self.name


    def __eq__(self, other):
        '''Equality. Based on attributes (such as pitch, accidental, duration, articulations, and ornaments) that are  not dependent on the wider context of a note (such as offset, beams, stem direction).

        This presently does not look at lyrics in establishing equality.

        >>> from music21 import *
        >>> n1 = note.Note()
        >>> n1.pitch.name = 'G#'
        >>> n2 = note.Note()
        >>> n2.pitch.name = 'A-'
        >>> n3 = note.Note()
        >>> n3.pitch.name = 'G#'
        >>> n1 == n2
        False
        >>> n1 == n3
        True
        >>> n3.duration.quarterLength = 3
        >>> n1 == n3
        False

        '''
        if other == None or not isinstance(other, Note):
            return False
        # checks pitch.octave, pitch.accidental, uses Pitch.__eq__
        if self.pitch == other.pitch: 
            # checks type, dots, tuplets, quarterlength, uses Pitch.__eq__
            if self.duration == other.duration:
                # articulations are a list of Articulation objects
                # converting to sets produces ordered cols that remove duplicate
                # however, must then convert to list to match based on class ==
                # not on class id()
                if (sorted(list(set(self.articulations))) ==
                    sorted(list(set(other.articulations)))):
                    # Tie objects if present compare only type
                    if self.tie == other.tie:
                        return True
#                     else:
#                         environLocal.printDebug('not matching note on tie')
#                 else:
#                     environLocal.printDebug('not matching note on articulations')
#             else:
#                 environLocal.printDebug('not matching note on duration')
#         else:
#             environLocal.printDebug('not matching note on pitch')
        return False

    def __ne__(self, other):
        '''Inequality. 

        >>> from music21 import *
        >>> n1 = note.Note()
        >>> n1.pitch.name = 'G#'
        >>> n2 = note.Note()
        >>> n2.pitch.name = 'A-'
        >>> n3 = note.Note()
        >>> n3.pitch.name = 'G#'
        >>> n1 != n2
        True
        >>> n1 != n3
        False
        >>> n3.duration.quarterLength = 3
        >>> n1 != n3
        True
        '''
        return not self.__eq__(other)



    #---------------------------------------------------------------------------
    # property access


    def _getName(self): 
        return self.pitch.name
    
    def _setName(self, value): 
        self.pitch.name = value

    name = property(_getName, _setName, 
        doc = '''Return or set the pitch name from the :class:`~music21.pitch.Pitch` object. See :attr:`~music21.pitch.Pitch.name`.
        ''')

    def _getNameWithOctave(self): 
        return self.pitch.nameWithOctave

    nameWithOctave = property(_getNameWithOctave, 
        doc = '''Return or set the pitch name with octave from the :class:`~music21.pitch.Pitch` object. See :attr:`~music21.pitch.Pitch.nameWithOctave`.
        ''')


    def _getPitchNames(self):
        return [self.pitch.name]

    def _setPitchNames(self, value):
        if common.isListLike(value):
            if 'Pitch' in value[0].classes:
                self.pitch.name = value[0].name
            else:
                raise NoteException('must provide a list containing a Pitch, not: %s' % value)
        else:
            raise NoteException('cannot set pitch name with provided object: %s' % value)

    pitchNames = property(_getPitchNames, _setPitchNames, 
        doc = '''Return a list of Pitch names from  :attr:`~music21.pitch.Pitch.name`. This property is designed to provide an interface analogous to that found on :class:`~music21.chord.Chord`.

        >>> from music21 import *
        >>> n = note.Note('g#')
        >>> n.name
        'G#'
        >>> n.pitchNames
        ['G#']
        >>> n.pitchNames = [pitch.Pitch('c2'), pitch.Pitch('g2')]
        >>> n.name
        'C'
        >>> n.pitchNames
        ['C']
        ''')


    def _getAccidental(self): 
        return self.pitch.accidental

    # do we no longer need setAccidental(), below?
    def _setAccidental(self, value):
        '''
        Adds an accidental to the Note, given as an Accidental object.
        Also alters the name of the note
        
        >>> from music21 import *
        >>> a = note.Note()
        >>> a.step = "D"
        >>> a.name 
        'D'
        >>> b = pitch.Accidental("sharp")
        >>> a.setAccidental(b)
        >>> a.name 
        'D#'
        '''
        if common.isStr(value):
            accidental = pitch.Accidental(value)
        else: 
            accidental = value
        self.pitch.accidental = accidental


    # backwards compat; remove when possible
    def setAccidental(self, accidental):
        '''This method is obsolete: use the `accidental` property instead.
        '''
        self._setAccidental(accidental)

    accidental = property(_getAccidental, _setAccidental,
        doc = '''Return or set the :class:`~music21.pitch.Accidental` object from the :class:`~music21.pitch.Pitch` object.
        ''') 


    def _getStep(self): 
        return self.pitch.step

    def _setStep(self, value): 
        self.pitch.step = value

    step = property(_getStep, _setStep, 
        doc = '''Return or set the pitch step from the :class:`~music21.pitch.Pitch` object. See :attr:`~music21.pitch.Pitch.step`.
        ''')

    def _getFrequency(self): 
        return self.pitch.frequency

    def _setFrequency(self, value): 
        self.pitch.frequency = value

    frequency = property(_getFrequency, _setFrequency, 
        doc = '''Return or set the frequency from the :class:`~music21.pitch.Pitch` object. See :attr:`~music21.pitch.Pitch.frequency`.
        ''')
    
    def _getFreq440(self): 
        return self.pitch.freq440

    def _setFreq440(self, value): 
        self.pitch.freq440 = value

    freq440 = property(_getFreq440, _setFreq440, 
        doc = '''Return or set the freq440 value from the :class:`~music21.pitch.Pitch` object. See :attr:`~music21.pitch.Pitch.freq440`.
        ''')

    def _getOctave(self): 
        return self.pitch.octave

    def _setOctave(self, value): 
        self.pitch.octave = value

    octave = property(_getOctave, _setOctave, 
        doc = '''Return or set the octave value from the :class:`~music21.pitch.Pitch` object. See :attr:`~music21.pitch.Pitch.octave`.''')

    def _getMidi(self):
        '''
        Returns the note's midi number.  
        
        C4 (middle C) = 60, C#4 = 61, D-4 = 61, D4 = 62; A4 = 69

        >>> from music21 import *
        >>> a = note.Note()
        >>> a.pitch = pitch.Pitch('d-4')
        >>> a.midi
        61
        '''
        return self.pitch.midi

    def _setMidi(self, value): 
        self.pitch.midi = value

    midi = property(_getMidi, _setMidi, 
        doc = '''Return or set the numerical MIDI pitch representation from the :class:`~music21.pitch.Pitch` object. See :attr:`~music21.pitch.Pitch.midi`.
        ''')


    def _getPs(self):
        '''
        Returns the note's midi number.  
        
        C4 (middle C) = 60, C#4 = 61, D-4 = 61, D4 = 62; A4 = 69

        >>> from music21 import *
        >>> a = note.Note()
        >>> a.ps = 60.5
        >>> a.midi
        61
        >>> a.ps
        60.5
        '''
        return self.pitch.ps

    def _setPs(self, value): 
        self.pitch.ps = value

    ps = property(_getPs, _setPs, 
        doc = '''Return or set the numerical pitch space representation from the :class:`music21.pitch.Pitch` object. See :attr:`music21.pitch.Pitch.ps`.
        ''')


    
    def _getPitchClass(self):
        '''Return pitch class

        >>> from music21 import *
        >>> d = note.Note()
        >>> d.pitch = pitch.Pitch('d-4')
        >>> d.pitchClass
        1
        >>> 
        '''
        return self.pitch.pitchClass

    def _setPitchClass(self, value):
        self.pitch.pitchClass = value

    pitchClass = property(_getPitchClass, _setPitchClass, 
        doc = '''Return or set the pitch class from the :class:`music21.pitch.Pitch` object. See :attr:`music21.pitch.Pitch.pitchClass`.
        ''')


    def _getPitchClassString(self):
        '''Return pitch class string, replacing 10 and 11 as needed. 

        >>> from music21 import *
        >>> d = note.Note()
        >>> d.pitch = pitch.Pitch('b')
        >>> d.pitchClassString
        'B'
        '''
        return self.pitch.pitchClassString

    def _setPitchClassString(self, value):
        '''

        >>> from music21 import *
        >>> d = note.Note()
        >>> d.pitch = pitch.Pitch('b')
        >>> d.pitchClassString = 'a'
        >>> d.pitchClass
        10
        '''
        self.pitch.pitchClassString = value

    pitchClassString = property(_getPitchClassString, _setPitchClassString,
        doc = '''Return or set the pitch class string from the :class:`~music21.pitch.Pitch` object. See :attr:`~music21.pitch.Pitch.pitchClassString`.
        ''')


    # was diatonicNoteNum
    def _getDiatonicNoteNum(self):
        ''' 
        see Pitch.diatonicNoteNum
        '''         
        return self.pitch.diatonicNoteNum

    diatonicNoteNum = property(_getDiatonicNoteNum, 
        doc = '''Return the diatonic note number from the :class:`~music21.pitch.Pitch` object. See :attr:`~music21.pitch.Pitch.diatonicNoteNum`.
        ''')



    def _getPitches(self):
        return [self.pitch]

    def _setPitches(self, value):
        if common.isListLike(value):
            if 'Pitch' in value[0].classes:
                self.pitch = value[0]
            else:
                raise NoteException('must provide a list containing a Pitch, not: %s' % value)
        else:
            raise NoteException('cannot set pitches with provided object: %s' % value)

    pitches = property(_getPitches, _setPitches, 
        doc = '''Return the :class:`~music21.pitch.Pitch` object in a list. This property is designed to provide an interface analogous to that found on :class:`~music21.chord.Chord`.

        >>> from music21 import *
        >>> n = note.Note('g#')
        >>> n.nameWithOctave
        'G#'
        >>> n.pitches
        [G#]
        >>> n.pitches = [pitch.Pitch('c2'), pitch.Pitch('g2')]
        >>> n.nameWithOctave
        'C2'
        >>> n.pitches
        [C2]
        ''')



    def transpose(self, value, inPlace=False):
        '''Transpose the Note by the user-provided value. If the value is an integer, the transposition is treated in half steps. If the value is a string, any Interval string specification can be provided.

        >>> from music21 import *
        >>> a = note.Note('g4')
        >>> b = a.transpose('m3')
        >>> b
        <music21.note.Note B->
        >>> aInterval = interval.Interval(-6)
        >>> b = a.transpose(aInterval)
        >>> b
        <music21.note.Note C#>
        
        >>> a.transpose(aInterval, inPlace=True)
        >>> a
        <music21.note.Note C#>

        '''
        if hasattr(value, 'diatonic'): # its an Interval class
            intervalObj = value
        else: # try to process
            intervalObj = interval.Interval(value)

        if not inPlace:
            post = copy.deepcopy(self)
        else:
            post = self

        # use inPlace, b/c if we are inPlace, we operate on self;
        # if we are not inPlace, post is a copy
        post.pitch.transpose(intervalObj, inPlace=True)

        if not inPlace:
            return post
        else:
            return None

    def _getMidiEvents(self):
        return midiTranslate.noteToMidiEvents(self)


    def _setMidiEvents(self, eventList, ticksPerQuarter=None):
        midiTranslate.midiEventsToNote(eventList, 
            ticksPerQuarter, self)


    midiEvents = property(_getMidiEvents, _setMidiEvents, 
        doc='''Get or set this chord as a list of :class:`music21.midi.base.MidiEvent` objects.

        >>> from music21 import *
        >>> n = note.Note()
        >>> n.midiEvents
        [<MidiEvent DeltaTime, t=0, track=None, channel=None>, <MidiEvent NOTE_ON, t=None, track=None, channel=1, pitch=60, velocity=90>, <MidiEvent DeltaTime, t=1024, track=None, channel=None>, <MidiEvent NOTE_OFF, t=None, track=None, channel=1, pitch=60, velocity=0>]
        ''')

    def _getMidiFile(self):
        # this method is defined in GeneralNote
        return midiTranslate.noteToMidiFile(self)


    midiFile = property(_getMidiFile,
        doc = '''Return a complete :class:`music21.midi.base.MidiFile` object based on the Note.

        The :class:`music21.midi.base.MidiFile` object can be used to write a MIDI file of this Note with default parameters using the :meth:`music21.midi.base.MidiFile.write` method, given a file path. The file must be opened in 'wb' mode.  

        >>> from music21 import *
        >>> n = note.Note()
        >>> mf = n.midiFile
        >>> #_DOCS_SHOW mf.open('/Volumes/xdisc/_scratch/midi.mid', 'wb')
        >>> #_DOCS_SHOW mf.write()
        >>> #_DOCS_SHOW mf.close()
        ''')


    def _getMX(self):
        return musicxmlTranslate.noteToMxNotes(self)

    def _setMX(self, mxNote):
        '''Given an mxNote, fill the necessary parameters of a Note
    
        >>> from music21 import *
        >>> mxNote = musicxml.Note()
        >>> mxNote.setDefaults()
        >>> mxMeasure = musicxml.Measure()
        >>> mxMeasure.setDefaults()
        >>> mxMeasure.append(mxNote)
        >>> mxNote.external['measure'] = mxMeasure # manually create ref
        >>> mxNote.external['divisions'] = mxMeasure.external['divisions']
        >>> n = note.Note('c')
        >>> n.mx = mxNote
        '''
        musicxmlTranslate.mxToNote(mxNote, inputM21=self)


    mx = property(_getMX, _setMX)    







#-------------------------------------------------------------------------------
# convenience classes

class EighthNote(Note):
    def __init__(self, *arguments, **keywords):
        Note.__init__(self, *arguments, **keywords)
        self.duration.type = "eighth"

class QuarterNote(Note):
    def __init__(self, *arguments, **keywords):
        Note.__init__(self, *arguments, **keywords)
        self.duration.type = "quarter"

class HalfNote(Note):
    def __init__(self, *arguments, **keywords):
        Note.__init__(self, *arguments, **keywords)
        self.duration.type = "half"

class WholeNote(Note):
    def __init__(self, *arguments, **keywords):
        Note.__init__(self, *arguments, **keywords)
        self.duration.type = "whole"




#-------------------------------------------------------------------------------
class Unpitched(GeneralNote):
    '''
    General class of unpitched objects which appear at different places
    on the staff.  Examples: percussion notation
    '''    
    displayStep = "C"
    displayOctave = 4
    isNote = False
    isUnpitched = True
    isRest = False


#-------------------------------------------------------------------------------
class Rest(GeneralNote):
    '''General rest class'''
    isNote = False
    isUnpitched = False
    isRest = True
    name = "rest"

    # TODO: may need to set a display pitch, 
    # as this is necessary in mxl

    def __init__(self, *arguments, **keywords):
        GeneralNote.__init__(self, **keywords)

    def __repr__(self):
        return "<music21.note.Rest %s>" % self.name

    def _preDurationLily(self):
        return "r"
    
    _lilyInternalTieCharacter = ' ' # when separating components, dont tie them


    def _getMX(self):
        '''
        Returns a List of mxNotes
        Attributes of notes are merged from different locations: first from the 
        duration objects, then from the pitch objects. Finally, GeneralNote 
        attributes are added
        '''
        return musicxmlTranslate.restToMxNotes(self)

    def _setMX(self, mxNote):
        '''Given an mxNote, fille the necessary parameters
        '''
        musicxmlTranslate.mxToRest(mxNote, inputM21=self)

    mx = property(_getMX, _setMX)    





#-------------------------------------------------------------------------------

def noteFromDiatonicNumber(number):
    octave = int(number / 7)
    noteIndex = number % 7
    noteNames = ['C','D','E','F','G','A','B']
    thisName = noteNames[noteIndex]
    note1 = Note()
    note1.octave = octave
    note1.name = thisName
    return note1


#-------------------------------------------------------------------------------
# test methods and classes

def sendNoteInfo(music21noteObject):
    '''
    Debugging method to print information about a music21 note
    called by trecento.trecentoCadence, among other places
    '''
    retstr = ""
    a = music21noteObject  
    if (isinstance(a, music21.note.Note)):
        retstr += "Name: " + a.name + "\n"
        retstr += "Step: " + a.step + "\n"
        retstr += "Octave: " + str(a.octave) + "\n"
        if (a.accidental is not None):
            retstr += "Accidental: " + a.accidental.name + "\n"
    else:
        retstr += "Is a rest\n"
    if (a.tie is not None):
        retstr += "Tie: " + a.tie.type + "\n"
    retstr += "Duration Type: " + a.duration.type + "\n"
    retstr += "QuarterLength: " + str(a.duration.quarterLength) + "\n"
    if len(a.duration.tuplets) > 0:
        retstr += "Is a tuplet\n"
        if a.duration.tuplets[0].type == "start":
            retstr += "   in fact STARTS the tuplet group\n"
        elif a.duration.tuplets[0].type == "stop":
            retstr += "   in fact STOPS the tuplet group\n"
    if len(a.expressions) > 0:
        if (isinstance(a.expressions[0], music21.expressions.Fermata)):
            retstr += "Has a fermata on it\n"
    return retstr


class TestExternal(unittest.TestCase):
    '''These are tests that open windows and rely on external software
    '''

    def runTest(self):
        pass

    def testSingle(self):
        '''Need to test direct meter creation w/o stream
        '''
        a = Note('d-3')
        a.quarterLength = 2.25
        a.show()

    def testBasic(self):
        from music21 import stream
        a = stream.Stream()

        for pitchName, qLen in [('d-3', 2.5), ('c#6', 3.25), ('a--5', .5),
                           ('f', 1.75), ('g3', 1.5), ('d##4', 1.25),
                           ('d-3', 2.5), ('c#6', 3.25), ('a--5', .5),
                           ('f#2', 1.75), ('g-3', 1.33333), ('d#6', .6666)
                ]:
            b = Note()
            b.quarterLength = qLen
            b.name = pitchName
            b.color = '#FF00FF'
            # print a.musicxml
            a.append(b)

        a.show()



#-------------------------------------------------------------------------------
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
                self.assertNotEqual(id(a), id(b))


    def testComplex(self):
        note1 = Note()
        note1.duration.clear()
        d1 = duration.Duration()
        d1.type = "whole"
        d2 = duration.Duration()
        d2.type = "quarter"
        note1.duration.components.append(d1)
        note1.duration.components.append(d2)
        self.assertEqual(note1.duration.quarterLength, 5.0)
        self.assertEqual(note1.duration.componentIndexAtQtrPosition(2), 0)    
        self.assertEqual(note1.duration.componentIndexAtQtrPosition(4), 1)    
        self.assertEqual(note1.duration.componentIndexAtQtrPosition(4.5), 1)
        note1.duration.sliceComponentAtPosition(1.0)
        
        matchStr = "c'4~ c'2.~ c'4"
        self.assertEqual(str(note1.lily), matchStr)
        i = 0
        for thisNote in (note1.splitAtDurations()):
            matchSub = matchStr.split(' ')[i]
            self.assertEqual(str(thisNote.lily), matchSub)
            i += 1
       

    def testNote(self):
    #    note1 = Note("c#1")
    #    assert note1.duration.quarterLength == 4
    #    note1.duration.dots = 1
    #    assert note1.duration.quarterLength == 6
    #    note1.duration.type = "eighth"
    #    assert note1.duration.quarterLength == 0.75
    #    assert note1.octave == 4
    #    assert note1.step == "C"

        note2 = Rest()
        self.assertEqual(note2.isRest, True)
        note3 = Note()
        note3.pitch.name = "B-"
        # not sure how to test not None
        #self.assertFalse (note3.pitch.accidental, None)
        self.assertEqual (note3.accidental.name, "flat")
        self.assertEqual (note3.pitchClass, 10)
        
        a5 = Note()
        a5.name = "A"
        a5.octave = 5
        self.assertAlmostEquals(a5.freq440, 880.0)
        self.assertEqual(a5.pitchClass, 9)
    


    def testCopyNote(self):
        a = Note()
        a.quarterLength = 3.5
        a.name = 'D'
        b = copy.deepcopy(a)
        self.assertEqual(b.name, a.name)
        self.assertEqual(b.quarterLength, a.quarterLength)


    def testMusicXMLOutput(self):
        mxNotes = []
        for pitchName, durType in [('g#', 'quarter'), ('g#', 'half'), 
                ('g#', 'quarter'), ('g#', 'quarter'), ('g#', 'quarter')]:

            dur = duration.Duration(durType)
            p = pitch.Pitch(pitchName)

            # a lost of one ore more notes (tied groups)
            for mxNote in dur.mx: # returns a list of mxNote objs
                # merger returns a new object
                mxNotes.append(mxNote.merge(p.mx))

        self.assertEqual(len(mxNotes), 5)
        self.assertEqual(mxNotes[0].get('pitch').get('alter'), 1)


    def testMusicXMLFermata(self):
        from music21 import corpus
        a = corpus.parseWork('bach/bwv5.7')
        found = []
        for n in a.flat.notes:
            for obj in n.expressions:
                if isinstance(obj, expressions.Fermata):
                    found.append(obj)
        self.assertEqual(len(found), 6)


    def testNoteBeatProperty(self):

        from music21 import stream, meter, note

        data = [
    ['3/4', .5, 6, [1.0, 1.5, 2.0, 2.5, 3.0, 3.5], 
            [1.0]*6, ],
    ['3/4', .25, 8, [1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75],
            [1.0]*8],
    ['3/2', .5, 8, [1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75],
            [2.0]*8],

    ['6/8', .5, 6, [1.0, 1.3333, 1.66666, 2.0, 2.3333, 2.666666],
            [1.5]*6],
    ['9/8', .5, 6, [1.0, 1.3333, 1.66666, 2.0, 2.3333, 2.666666],
            [1.5]*6],
    ['12/8', .5, 6, [1.0, 1.3333, 1.66666, 2.0, 2.3333, 2.666666],
            [1.5]*6],

    ['6/16', .25, 6, [1.0, 1.3333, 1.66666, 2.0, 2.3333, 2.666666],
            [0.75]*6],

    ['5/4', 1, 5, [1.0, 2.0, 3.0, 4.0, 5.0],
            [1.]*5],

    ['2/8+3/8+2/8', .5, 6, [1.0, 1.5, 2.0, 2.33333, 2.66666, 3.0],
            [1., 1., 1.5, 1.5, 1.5, 1.]],

        ]

        # one measure case
        for tsStr, nQL, nCount, matchBeat, matchBeatDur in data:
            n = note.Note() # need fully qualified name
            n.quarterLength = nQL
            m = stream.Measure()
            m.timeSignature = meter.TimeSignature(tsStr)
            m.repeatAppend(n, nCount)
            
            self.assertEqual(len(m), nCount+1)

            # test matching beat proportion value
            post = [m.notes[i].beat for i in range(nCount)]
            for i in range(len(matchBeat)):
                self.assertAlmostEquals(post[i], matchBeat[i], 4)

            # test getting beat duration
            post = [m.notes[i].beatDuration.quarterLength for i in range(nCount)]

            for i in range(len(matchBeat)):
                self.assertAlmostEquals(post[i], matchBeatDur[i], 4)

        # two measure case
        for tsStr, nQL, nCount, matchBeat, matchBeatDur in data:
            p = stream.Part()
            n = note.Note()
            n.quarterLength = nQL

            # m1 has time signature
            m1 = stream.Measure()
            m1.timeSignature = meter.TimeSignature(tsStr)
            p.append(m1)

            # m2 does not have time signature
            m2 = stream.Measure()
            m2.repeatAppend(n, nCount)
            self.assertEqual(len(m2), nCount)
            self.assertEqual(len(m2.notes), nCount)

            p.append(m2)

            # test matching beat proportion value
            post = [m2.notes[i].beat for i in range(nCount)]
            for i in range(len(matchBeat)):
                self.assertAlmostEquals(post[i], matchBeat[i], 4)
            # test getting beat duration
            post = [m2.notes[i].beatDuration.quarterLength for i in range(nCount)]
            for i in range(len(matchBeat)):
                self.assertAlmostEquals(post[i], matchBeatDur[i], 4)



    def testNoteBeatPropertyCorpus(self):

        data = [['bach/bwv255', [4.0, 1.0, 2.0, 2.5, 3.0, 4.0, 4.5, 1.0, 1.5]], 
                ['bach/bwv153.9', [1.0, 2.0, 3.0, 1.0, 2.0, 3.0, 1.0, 3.0, 1.0]]
                ]

        for work, match in data:
            from music21 import corpus
            s = corpus.parseWork(work)
            # always use tenor line    
            found = []
            for n in s[2].flat.notes:
                n.lyric = n.beatStr
                found.append(n.beat)
            
            for i in range(len(match)):
                self.assertEquals(match[i], found[i])

            #s.show()


    def testNoteEquality(self):
        from music21 import articulations, tie

        n1 = Note('a#')
        n2 = Note('g')
        n3 = Note('a-')
        n4 = Note('a#')

        self.assertEqual(n1==n2, False)
        self.assertEqual(n1==n3, False)
        self.assertEqual(n1==n4, True)

        # test durations with the same pitch
        for x, y, match in [(1, 1, True), (1, .5, False), 
                     (1, 2, False), (1, 1.5, False)]:
            n1.quarterLength = x
            n4.quarterLength = y
            self.assertEqual(n1==n4, match) # sub1

        # test durations with different pitch
        for x, y, match in [(1, 1, False), (1, .5, False), 
                     (1, 2, False), (1, 1.5, False)]:
            n1.quarterLength = x
            n2.quarterLength = y
            self.assertEqual(n1==n2, match) # sub2

        # same pitches different octaves
        n1.quarterLength = 1.0
        n4.quarterLength = 1.0
        for x, y, match in [(4, 4, True), (3, 4, False), (2, 4, False)]:
            n1.pitch.octave = x
            n4.pitch.octave = y
            self.assertEqual(n1==n4, match) # sub4

        # with and without ties
        n1.pitch.octave = 4
        n4.pitch.octave = 4
        t1 = tie.Tie()
        t2 = tie.Tie()
        for x, y, match in [(t1, None, False), (t1, t2, True)]:
            n1.tie = x
            n4.tie = y
            self.assertEqual(n1==n4, match) # sub4

        # with ties but different pitches
        for n in [n1, n2, n3, n4]:
            n.quarterLength = 1.0
        t1 = tie.Tie()
        t2 = tie.Tie()
        for a, b, match in [(n1, n2, False), (n1, n3, False), 
                            (n2, n3, False), (n1, n4, True)]:
            a.tie = t1
            b.tie = t2
            self.assertEqual(a==b, match) # sub5

        # articulation groups
        a1 = [articulations.Accent()]
        a2 = [articulations.Accent(), articulations.StrongAccent()]
        a3 = [articulations.StrongAccent(), articulations.Accent()]
        a4 = [articulations.StrongAccent(), articulations.Accent(), 
             articulations.Tenuto()]
        a5 = [articulations.Accent(), articulations.Tenuto(),
             articulations.StrongAccent()]

        for a, b, c, d, match in [(n1, n4, a1, a1, True), 
                (n1, n2, a1, a1, False), (n1, n3, a1, a1, False),
                # same pitch different orderings
                (n1, n4, a2, a3, True), (n1, n4, a4, a5, True),
                # different pitch same orderings
               (n1, n2, a2, a3, False), (n1, n3, a4, a5, False),
            ]:
            a.articulations = c
            b.articulations = d
            self.assertEqual(a==b, match) # sub6



    def testMetricalAccent(self):
        from music21 import note, meter, stream
        data = [
('4/4', 8, .5, [1.0, 0.125, 0.25, 0.125, 0.5, 0.125, 0.25, 0.125]),
('3/4', 6, .5, [1.0, 0.25, 0.5, 0.25, 0.5, 0.25] ),
('6/8', 6, .5, [1.0, 0.25, 0.25, 0.5, 0.25, 0.25]  ),

('12/32', 12, .125, [1.0, 0.125, 0.125, 0.25, 0.125, 0.125, 0.5, 0.125, 0.125, 0.25, 0.125, 0.125]  ),

('5/8', 10, .25, [1.0, 0.25, 0.5, 0.25, 0.5, 0.25, 0.5, 0.25, 0.5, 0.25]  ),

# test notes that do not have defined accents
('4/4', 16, .25, [1.0, 0.0625, 0.125, 0.0625, 0.25, 0.0625, 0.125, 0.0625, 0.5, 0.0625, 0.125, 0.0625, 0.25, 0.0625, 0.125, 0.0625]),

('4/4', 32, .125, [1.0, 0.0625, 0.0625, 0.0625, 0.125, 0.0625, 0.0625, 0.0625, 0.25, 0.0625, 0.0625, 0.0625, 0.125, 0.0625, 0.0625, 0.0625, 0.5, 0.0625, 0.0625, 0.0625, 0.125, 0.0625, 0.0625, 0.0625, 0.25, 0.0625, 0.0625, 0.0625, 0.125, 0.0625, 0.0625, 0.0625]),


                ]

        for tsStr, nCount, dur, match in data:

            m = stream.Measure()
            m.timeSignature = meter.TimeSignature(tsStr)
            n = note.Note()
            n.quarterLength = dur   
            m.repeatAppend(n, nCount)

            self.assertEqual([n.beatStrength for n in m.notes], match)
            



    def testTieContinue(self):
        from music21 import stream

        n1 = Note()
        n1.tie = tie.Tie()
        n1.tie.type = 'start'

        n2 = Note()
        n2.tie = tie.Tie()
        n2.tie.type = 'continue'

        n3 = Note()
        n3.tie = tie.Tie()
        n3.tie.type = 'stop'

        s = stream.Stream()
        s.append([n1, n2, n3])

        # need to test that this gets us a continue tie, but hard to test
        # post musicxml processing
        #s.show()

#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Note, Rest]

if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        t = Test()
        te = TestExternal()

        

        #t.testNoteEquality()
        #t.testNoteBeatProperty()

        #t.testMetricalAccent()
        t.testTieContinue()


#------------------------------------------------------------------------------
# eof





