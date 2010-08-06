#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         note.py
# Purpose:      music21 classes for representing notes
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009-2010 The music21 Project
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
#from music21 import midi as midiModule
from music21.midi import translate as midiTranslate
from music21 import expressions
from music21 import pitch
from music21 import beam
from music21 import meter



from music21 import environment
_MOD = "note.py"  
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------
class Tie(music21.Music21Object):
    '''Object added to notes that are tied to other notes. The `type` value is generally one of start or stop.

    >>> from music21 import *
    >>> note1 = note.Note()
    >>> note1.tie = Tie("start")
    >>> note1.tieStyle = "normal" # or could be dotted or dashed
    >>> note1.tie.type
    'start'

    Differences from MusicXML:
       notes do not need to know if they are tied from a
       previous note.  i.e., you can tie n1 to n2 just with
       a tie start on n1.  However, if you want proper musicXML output
       you need a tie stop on n2
       one tie with "continue" implies tied from and tied to

       optional (to know what notes are next:)
          .to = note()   # not implimented yet, b/c of garbage coll.
          .from = note()

    OMIT_FROM_DOCS
    (question: should notes be able to be tied to multiple notes
    for the case where a single note is tied both voices of a
    two-note-head unison?)
    '''

    def __init__(self, tievalue = "start"):
        music21.Music21Object.__init__(self)
        self.type = tievalue

    # use weak-refs for .to and .from
    def _getMX(self):
        '''Return a MusicXML object representation. 
        '''
        mxTieList = []
        mxTie = musicxmlMod.Tie()
        mxTie.set('type', self.type) # start, stop
        mxTieList.append(mxTie) # goes on mxNote.tieList

        mxTiedList = []
        mxTied = musicxmlMod.Tied()
        mxTied.set('type', self.type) 
        mxTiedList.append(mxTied) # goes on mxNote.notationsObj list

        return mxTieList, mxTiedList
    
    def _setMX(self, mxNote):
        '''Load a MusicXML object representation. 
        '''
        mxTieList = mxNote.get('tieList')
        if len(mxTieList) > 0:
            # get all types and see what we have for this note
            typesFound = []
            for mxTie in mxTieList:
                typesFound.append(mxTie.get('type'))
            # trivial case: have only 1
            if len(typesFound) == 1:
                self.type = typesFound[0]
            elif typesFound == ['stop', 'start']:
                # take the second, the start value; do not need a stop
                self.type = typesFound[1]
            else:
                environLocal.printDebug(['found unexpected arrangement of multiple tie types when importing from musicxml:', typesFound])    

    # not sure this is necessary
#         mxNotations = mxNote.get('notations')
#         if mxNotations != None:
#             mxTiedList = mxNotations.getTieds()
            # should be sufficient to only get mxTieList

    mx = property(_getMX, _setMX)


    def __eq__(self, other):
        '''Equality. Based on attributes (such as pitch, accidental, duration, articulations, and ornaments) that are  not dependent on the wider context of a note (such as offset, beams, stem direction).

        >>> t1 = Tie('start')
        >>> t2 = Tie('start')
        >>> t3 = Tie('end')
        >>> t1 == t2
        True
        >>> t2 == t3, t3 == t1
        (False, False)
        >>> t2 == None
        False
        '''
        if other == None or not isinstance(other, Tie):
            return False
        elif self.type == other.type:
            return True
        return False

    def __ne__(self, other):
        '''Inequality. Needed for pitch comparisons.
        '''
        return not self.__eq__(other)



#-------------------------------------------------------------------------------
class LyricException(Exception):
    pass


class Lyric(object):

    def __init__(self, text=None, number=1, syllabic=None):
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
        mxLyric = musicxmlMod.Lyric()
        mxLyric.set('text', self.text)
        mxLyric.set('number', self.number)
        mxLyric.set('syllabic', self.syllabic)
        return mxLyric

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
        self.text = mxLyric.get('text')
        self.number = mxLyric.get('number')
        self.syllabic = mxLyric.get('syllabic')

    mx = property(_getMX, _setMX)    






#-------------------------------------------------------------------------------
class GeneralNote(music21.Music21Object):
    '''A GeneralNote object is the parent object for the :class:`~music21.note.Note`, :class:`~music21.note.Rest`, :class:`~music21.note.Chord`, and related objects. 
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
        music21.Music21Object.__init__(self)

        self.duration = duration.Duration(**keywords)
        self.lyrics = [] # a list of lyric objects

        self.notations = []
        self.articulations = []
        self.editorial = editorial.NoteEditorial()
        self.tie = None # store a Tie object


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


    def _getMeasureOffset(self):
        '''Try to obtain the nearest Measure that contains this Note, and return the offset within that Measure.

        >>> from music21 import *
        >>> n = note.Note()
        >>> n.quarterLength = 2
        >>> m = stream.Measure()
        >>> n._getMeasureOffset() # returns zero when not assigned
        0.0 
        >>> n.quarterLength = .5
        >>> m = stream.Measure()
        >>> m.repeatAppend(n, 4)
        >>> [n._getMeasureOffset() for n in m.notes]
        [0.0, 0.5, 1.0, 1.5]

        '''
        if self.parent != None and self.parent.isMeasure:
            #environLocal.printDebug(['found parent as Measure, using for offset'])
            offsetLocal = self.getOffsetBySite(self.parent)
        else:
            # this method-level import seems unvoidable to be sure to get the 
            # right offset
            from music21 import stream
            # testing sortByCreationTime == true; this may be necessary
            # as we often want the most recent measure
            m = self.getContextByClass(stream.Measure, sortByCreationTime=True)
            if m != None:
                #environLocal.printDebug(['using found Measure for offset access'])            
                offsetLocal = self.getOffsetBySite(m)
            else: # hope that we get the right one
                environLocal.printDebug(['using standard offset access'])
                offsetLocal = self.offset

        #environLocal.printDebug(['_getMeasureOffset(): found local offset as:', offsetLocal, self])
        return offsetLocal

    def _getBeat(self):
        '''Return a beat designation based on local Measure and TimeSignature

        >>> from music21 import *
        >>> n = note.Note()
        >>> n.quarterLength = 2
        >>> m = stream.Measure()
        >>> m.isMeasure
        True
        >>> m.timeSignature = meter.TimeSignature('4/4')
        >>> m.repeatAppend(n, 2)
        >>> m[1].parent # here we get the parent, but not in m.notes
        <music21.stream.Measure 0 offset=0.0>

        >>> m.notes[0]._getBeat()
        1.0
        >>> m.notes[1]._getBeat()
        3.0
        '''
        ts = self.getContextByClass(meter.TimeSignature)
        if ts == None:
            raise NoteException('this Note does not have a TimeSignature in DefinedContexts')                    
        return ts.getBeatProportion(self._getMeasureOffset())


    beat = property(_getBeat,  
        doc = '''Return the beat of this Note as found in the most recently positioned Measure. Beat values count from 1 and contain a floating-point designation between 0 and 1 to show proportional progress through the beat.

        >>> from music21 import *
        >>> n = note.Note()
        >>> n.quarterLength = .5
        >>> m = stream.Measure()
        >>> m.timeSignature = meter.TimeSignature('3/4')
        >>> m.repeatAppend(n, 6)
        >>> [m.notes[i].beat for i in range(6)]
        [1.0, 1.5, 2.0, 2.5, 3.0, 3.5]

        >>> m.timeSignature = meter.TimeSignature('6/8')
        >>> [m.notes[i].beat for i in range(6)]
        [1.0, 1.3333333..., 1.666666666..., 2.0, 2.33333333..., 2.66666...]

        ''')


    def _getBeatStr(self):
        ts = self.getContextByClass(meter.TimeSignature)
        #environLocal.printDebug(['_getBeatStr(): found ts:', ts])
        if ts == None:
            raise NoteException('this Note does not have a TimeSignature in DefinedContexts')                    
        return ts.getBeatProportionStr(self._getMeasureOffset())


    beatStr = property(_getBeatStr,  
        doc = '''Return a string representation of the beat of this Note as found in the most recently positioned Measure. Beat values count from 1 and contain a fractional designation to show progress through the beat.

        >>> from music21 import *
        >>> n = note.Note()
        >>> n.quarterLength = .5
        >>> m = stream.Measure()
        >>> m.timeSignature = meter.TimeSignature('3/4')
        >>> m.repeatAppend(n, 6)
        >>> [m.notes[i].beatStr for i in range(6)]
        ['1', '1 1/2', '2', '2 1/2', '3', '3 1/2']
        >>> m.timeSignature = meter.TimeSignature('6/8')
        >>> [m.notes[i].beatStr for i in range(6)]
        ['1', '1 1/3', '1 2/3', '2', '2 1/3', '2 2/3']
        ''')


    def _getBeatDuration(self):
        '''Return a  designation based on local Measure and TimeSignature

        >>> from music21 import *
        >>> n = note.Note()
        >>> n.quarterLength = 2
        >>> m = stream.Measure()
        >>> m.timeSignature = meter.TimeSignature('4/4')
        >>> m.repeatAppend(n, 2)
        >>> m.notes[0]._getBeatDuration()
        <music21.duration.Duration 1.0>
        >>> m.notes[1]._getBeatDuration()
        <music21.duration.Duration 1.0>
        '''
        ts = self.getContextByClass(meter.TimeSignature)
        if ts == None:
            raise NoteException('this Note does not have a TimeSignature in DefinedContexts')
        return ts.getBeatDuration(self._getMeasureOffset())

    beatDuration = property(_getBeatDuration,  
        doc = '''Return a :class:`~music21.duration.Duration` of the beat active for this Note as found in the most recently positioned Measure.

        >>> from music21 import *
        >>> n = note.Note()
        >>> n.quarterLength = .5
        >>> m = stream.Measure()
        >>> m.timeSignature = meter.TimeSignature('3/4')
        >>> m.repeatAppend(n, 6)
        >>> [m.notes[i].beatDuration.quarterLength for i in range(6)]
        [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]

        >>> m.timeSignature = meter.TimeSignature('6/8')
        >>> [m.notes[i].beatDuration.quarterLength for i in range(6)]
        [1.5, 1.5, 1.5, 1.5, 1.5, 1.5]
        ''')



    def augmentOrDiminish(self, scalar, inPlace=True):
        '''Given a scalar greater than zero, return a Note with a scaled Duration. If `inPlace` is True, this is done in-place and the method returns None. If `inPlace` is False, this returns a modified deep copy.

        >>> from music21 import *
        >>> n = note.Note('g#')
        >>> n.quarterLength = 3
        >>> n.augmentOrDiminish(2)
        >>> n.quarterLength
        6

        >>> from music21 import chord
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
        '''This must call _getMX to get basic mxNote objects
        >>> from music21 import *
        >>> n = note.Note()
        >>> post = n._getMusicXML()
        '''
        # make a copy, as we this process will change tuple types
        selfCopy = copy.deepcopy(self)
        duration.updateTupletType(selfCopy.duration) # modifies in place

        mxNoteList = selfCopy._getMX() # can be rest, note, or chord

        mxMeasure = musicxmlMod.Measure()
        mxMeasure.setDefaults()
        for mxNote in mxNoteList:
            mxMeasure.append(mxNote)

        mxPart = musicxmlMod.Part()
        mxPart.setDefaults()
        mxPart.append(mxMeasure)

        # see if an instrument is defined in this or a parent stream
        if hasattr(self.parent, 'getInstrument'):
            instObj = self.parent.getInstrument()
        else:
            instObj = instrument.Instrument()
            # part id is now configured later in processing
            #instObj.partId = defaults.partId # give a default id
            instObj.instrumentIdRandomize()
            instObj.partIdRandomize()
            instObj.partName = defaults.partName # give a default id

        mxScorePart = musicxmlMod.ScorePart()
        mxScorePart.set('partName', instObj.partName)
        mxScorePart.set('id', instObj.partId)

        # must set this part to the same id
        mxPart.set('id', instObj.partId)

        mxPartList = musicxmlMod.PartList()
        mxPartList.append(mxScorePart)

        mxIdentification = musicxmlMod.Identification()
        mxIdentification.setDefaults() # will create a composer
        mxScore = musicxmlMod.Score()
        mxScore.setDefaults()
        mxScore.set('partList', mxPartList)
        mxScore.set('identification', mxIdentification)
        mxScore.append(mxPart)
        return mxScore.xmlStr()



    musicxml = property(_getMusicXML, 
        doc = '''Return a complete musicxml representation.
        ''')    





    #---------------------------------------------------------------------------
    # duration

#     def appendDuration(self, durationObject):
#         '''
#         Sets the duration of the note to the supplied duration.Duration object
# 
#         >>> a = Note()
#         >>> a.duration.clear() # remove default
#         >>> a.appendDuration(duration.Duration('half'))
#         >>> a.duration.quarterLength
#         2.0
#         >>> a.appendDuration(duration.Duration('whole'))
#         >>> a.duration.quarterLength
#         6.0
# 
#         '''
#         # note: the lower level interface has changed here
#         self.duration.addDurationUnit(durationObject)

#     def clearDurations(self):
#         '''
#         clears all the durations stored in the note.
#         After performing this, it's probably not wise to print the note until 
#         at least one duration.Duration is added
#         '''
#         #self.componentDurations = []
#         #self.durationLinkages = []
#         #self.duration = ComplexDuration(components = self.componentDurations,
#         #                                linkages = self.durationLinkages)
#         self.duration = duration.Duration(components=[], linkages=[])


    def splitAtDurations(self):
        '''
        Takes a Note and returns a list of Notes with only a single
        duration.DurationUnit in each. Ties are added. 

        >>> from music21 import *
        >>> a = note.Note()
        >>> a.duration.clear() # remove defaults
        >>> a.duration.addDurationUnit(duration.Duration('half'))
        >>> a.duration.quarterLength
        2.0
        >>> a.duration.addDurationUnit(duration.Duration('whole'))
        >>> a.duration.quarterLength
        6.0
        >>> b = a.splitAtDurations()
        >>> b[0].pitch == b[1].pitch
        True
        >>> b[0].duration.type
        'half'
        >>> b[1].duration.type
        'whole'
        '''
        returnNotes = []

        if len(self.duration.components) == (len(self.duration.linkages) - 1):
            for i in range(len(self.duration.components)):
                tempNote = copy.deepcopy(self)
                # note that this keeps durations 
                tempNote.duration = self.duration.components[i]
                if i != (len(self.duration.components) - 1):
                    tempNote.tie = self.duration.linkages[i]                
                    # last note just gets the tie of the original Note
                returnNotes.append(tempNote)
        else: 
            for i in range(len(self.duration.components)):
                tempNote = copy.deepcopy(self)
                tempNote.duration = self.duration.components[i]
                if i != (len(self.duration.components) - 1):
                    tempNote.tie = Tie()
                else:
                    # last note just gets the tie of the original Note
                    if self.tie is None:
                        self.tie = Tie("stop")
                returnNotes.append(tempNote)                
        return returnNotes


    def splitByQuarterLengths(self, quarterLengthList):
        '''Given a list of quarter lengths, return a list of Note objects, copied from this Note, that are partitioned and tied with the specified quarter length list durations.

        >>> n = Note()
        >>> n.quarterLength = 3
        >>> post = n.splitByQuarterLengths([1,1,1])
        >>> [n.quarterLength for n in post]
        [1, 1, 1]
        '''
        if sum(quarterLengthList) != self.duration.quarterLength:
            raise NoteException('cannot split by quarter length list that is not equal to the duratoin of the source.')
        if len(quarterLengthList) <= 1:
            raise NoteException('cannot split by this quarter length list: %s.' % quarterLengthList)

        post = []
        for i in range(len(quarterLengthList)):
            ql = quarterLengthList[i]
            n = copy.deepcopy(self)
            n.quarterLength = ql

            # if not last
            if i != (len(quarterLengthList) - 1):
                n.tie = Tie() # need a tie objects
            else: # if last
                # last note just gets the tie of the original Note
                n.tie = Tie("stop")
            post.append(n)

        return post

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
        if len(self.notations) > 0:
            if (isinstance(self.notations[0], music21.expressions.Fermata)):
                ret += " has Fermata"
        return ret




#-------------------------------------------------------------------------------
class NotRest(GeneralNote):
    '''
    Parent class for objects that are not rests; or, object that can be tied.
    '''
    
    # unspecified means that there may be a stem, but its orienation
    # has not been declared. 
    stemDirection = "unspecified"
    
    def __init__(self, *arguments, **keywords):
        GeneralNote.__init__(self, **keywords)

#     def splitNoteAtPoint(self, quarterLength):
#         (note1, note2) = GeneralNote.splitNoteAtPoint(self, quarterLength)
#         note1.tie = Tie("start")  #rests arent tied
#         return [note1, note2]


    #---------------------------------------------------------------------------
    def splitNoteAtPoint(self, quarterLength):
        '''
        Split a Note into two Notes. 

        >>> from music21 import *
        >>> a = note.NotRest()
        >>> a.duration.type = 'whole'
        >>> b, c = a.splitNoteAtPoint(3)
        >>> b.duration.type
        'half'
        >>> b.duration.dots
        1
        >>> b.duration.quarterLength
        3.0
        >>> c.duration.type
        'quarter'
        >>> c.duration.dots
        0
        >>> c.duration.quarterLength
        1.0
        '''
        if quarterLength > self.duration.quarterLength:
            raise duration.DurationException(
            "cannont split a duration (%s) at this quarter length (%s)" % (
            self.duration.quarterLength, quarterLength))

        note1 = copy.deepcopy(self)
        note2 = copy.deepcopy(self)

        lenEnd = self.duration.quarterLength - quarterLength
        lenStart = self.duration.quarterLength - lenEnd

        d1 = duration.Duration()
        d1.quarterLength = lenStart

        d2 = duration.Duration()
        d2.quarterLength = lenEnd

        note1.duration = d1
        note2.duration = d2

        # this is all the functionality of PitchedOrUnpitched
        if hasattr(self, 'isRest') and not self.isRest:
            note1.tie = Tie("start")  #rests arent tied

        return [note1, note2]



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
    
    A ComplexNote will eventually be smart enough that if given a duration in 
    quarters it will try to figure out a way to express itself as best it can if
    it needs to be represented on page.  It does not know this now.
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
    'beams': 'A :class:`~music21.note.Beams` object.',
    'pitch': 'A :class:`~music21.pitch.Pitch` object.',
    }

    # Accepts an argument for pitch
    def __init__(self, *arguments, **keywords):
        NotRest.__init__(self, **keywords)

        if len(arguments) > 0:
            if isinstance(arguments[0], pitch.Pitch):
                self.pitch = arguments[0]
            else:
                self.pitch = pitch.Pitch(arguments[0]) # assume first arg is pitch
        else:
            self.pitch = pitch.Pitch('C4')

#         components = []
#         linkages = []
#         if "components" in keywords:
#             components = keywords["components"]
#         if "linkages" in keywords:
#             linkages = keywords["linkages"]

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

        >>> n1 = Note()
        >>> n1.pitch.name = 'G#'
        >>> n2 = Note()
        >>> n2.pitch.name = 'A-'
        >>> n3 = Note()
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

        >>> n1 = Note()
        >>> n1.pitch.name = 'G#'
        >>> n2 = Note()
        >>> n2.pitch.name = 'A-'
        >>> n3 = Note()
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
        return baseName


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
                    allNames += "~"
                    allNames += " "
                if (i == 0): # first component
                    if self.lyric is not None: # hack that uses markup...
                        allNames += "_\markup { \"" + self.lyric + "\" } "
        else:
            allNames += baseName
            allNames += self.duration.lily
            allNames += self.editorial.lilyAttached()
            if self.lyric is not None: # hack that uses markup...
                allNames += "_\markup { \"" + self.lyric + "\" } "
            
        if (self.tie is not None):
            if (self.tie.type != "stop"):
                allNames += "~"
        if (self.notations):
            for thisNotation in self.notations:
                if dir(thisNotation).count('lily') > 0:
                    allNames += " " + thisNotation.lily

        allNames += self.editorial.lilyEnd()
        
        return LilyString(allNames)

    lily = property(_getLily)


    def _getMidiEvents(self):
        return midiTranslate.noteToMidiEvents(self)


    def _setMidiEvents(self, eventList, ticksPerQuarter=None):
        midiTranslate.midiEventsToNote(eventList, 
            ticksPerQuarter, self)


    midiEvents = property(_getMidiEvents, _setMidiEvents, 
        doc='''Get or set this chord as a list of :class:`music21.midi.base.MidiEvent` objects.

        >>> n = Note()
        >>> n.midiEvents
        [<MidiEvent DeltaTime, t=0, track=None, channel=None>, <MidiEvent NOTE_ON, t=None, track=None, channel=1, pitch=60, velocity=90>, <MidiEvent DeltaTime, t=1024, track=None, channel=None>, <MidiEvent NOTE_OFF, t=None, track=None, channel=1, pitch=60, velocity=0>]
        ''')

    def _getMidiFile(self):
        return midiTranslate.noteToMidiFile(self)


    midiFile = property(_getMidiFile,
        doc = '''Return a complete :class:`music21.midi.base.MidiFile` object.

        >>> n = Note()
        >>> mf = n.midiFile
        ''')


    def _getMX(self):
        '''
        Returns a List of mxNotes
        Attributes of notes are merged from different locations: first from the 
        duration objects, then from the pitch objects. Finally, GeneralNote 
        attributes are added
        '''
        mxNoteList = []
        for mxNote in self.duration.mx: # returns a list of mxNote objs
            # merge method returns a new object
            mxNote = mxNote.merge(self.pitch.mx)
            # get color from within .editorial using attribute
            mxNote.set('color', self.color)
            mxNoteList.append(mxNote)

        # note: lyric only applied to first note
        for lyricObj in self.lyrics:
            mxNoteList[0].lyricList.append(lyricObj.mx)

        # if this note, not a component duration, but this note has a tie, 
        # need to add this to the last-encountered mxNote
        if self.tie != None:
            mxTieList, mxTiedList = self.tie.mx # get mxl objs from tie obj
            # if starting a tie, add to last mxNote in mxNote list
            if self.tie.type == 'start':
                mxNoteList[-1].tieList += mxTieList
                mxNoteList[-1].notationsObj.componentList += mxTiedList
            # if ending a tie, set first mxNote to stop
            # TODO: this may need to continue if there are components here
            elif self.tie.type == 'stop':
                mxNoteList[0].tieList += mxTieList
                mxNoteList[0].notationsObj.componentList += mxTiedList

        # need to apply beams to notes, but application needs to be
        # reconfigured based on what is gotten from self.duration.mx

        # likely, this means that many continue beams will need to be added

        # this is setting the same beams for each part of this 
        # note; this may not be correct, as we may be dividing the note into
        # more than one part
        for mxNote in mxNoteList:
            if self.beams != None:
                mxNote.beamList = self.beams.mx

        # if we have any articulations, they only go on the first of any 
        # component notes
        mxArticulations = musicxmlMod.Articulations()
        for i in range(len(self.articulations)):
            obj = self.articulations[i] # returns mxArticulationMark
            mxArticulations.append(obj.mx) # append to mxArticulations
        if len(mxArticulations) > 0:
            mxNoteList[0].notationsObj.componentList.append(mxArticulations)

        # notations and articulations are mixed in musicxml
        for i in range(len(self.notations)):
            obj = self.notations[i] 
            mxNoteList[0].notationsObj.componentList.append(obj.mx)

        return mxNoteList


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
        >>> n = Note('c')
        >>> n.mx = mxNote
        '''
        # print object == 'no' and grace notes may have a type but not
        # a duration. they may be filtered out at the level of Stream 
        # processing
        if mxNote.get('printObject') == 'no':
            environLocal.printDebug(['got mxNote with printObject == no'])

        mxGrace = mxNote.get('grace')
        if mxGrace != None: # graces have a type but not a duration
            environLocal.printDebug(['got mxNote with an mxGrace', 'duration', mxNote.get('duration')])

        self.pitch.mx = mxNote # required info will be taken from entire note
        self.duration.mx = mxNote
        self.beams.mx = mxNote.beamList

        mxTieList = mxNote.get('tieList')
        if len(mxTieList) > 0:
            tieObj = Tie() # m21 tie object
            tieObj.mx = mxNote # provide entire Note
            # self.tie is defined in GeneralNote as None by default
            self.tie = tieObj

        mxNotations = mxNote.get('notations')
        if mxNotations != None:
            # get a list of mxArticulationMarks, not mxArticulations
            mxArticulationMarkList = mxNotations.getArticulations()
            for mxObj in mxArticulationMarkList:
                articulationObj = articulations.Articulation()
                articulationObj.mx = mxObj
                self.articulations.append(articulationObj)

            # get any fermatas, store on notations
            mxFermataList = mxNotations.getFermatas()
            for mxObj in mxFermataList:
                fermataObj = expressions.Fermata()
                fermataObj.mx = mxObj
                # placing this as an articulation for now
                self.notations.append(fermataObj)

                #environLocal.printDebug(['_setMX(), self.mxFermataList', mxFermataList])

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
        GeneralNote.__init__(self)

    def __repr__(self):
        return "<music21.note.Rest %s>" % self.name

    def _lilyName(self):
        '''The name of the rest as it would appear in Lilypond format.
        
        >>> from music21 import *
        >>> r1 = note.Rest()
        >>> r1.duration.type = "half"
        >>> r1.lily
        'r2'
        '''
        baseName = ""
        baseName += self.editorial.lilyStart()
        baseName += "r"
        baseName += self.duration.lily     
        baseName += self.editorial.lilyAttached()
        baseName += self.editorial.lilyEnd()
        return baseName

    lily = property(_lilyName)


    def _getMX(self):
        '''
        Returns a List of mxNotes
        Attributes of notes are merged from different locations: first from the 
        duration objects, then from the pitch objects. Finally, GeneralNote 
        attributes are added
        '''
        mxNoteList = []
        for mxNote in self.duration.mx: # returns a list of mxNote objs
            # merge method returns a new object
            mxRest = musicxmlMod.Rest()
            mxRest.setDefaults()
            mxNote.set('rest', mxRest)
            # get color from within .editorial using attribute
            mxNote.set('color', self.color)
            mxNoteList.append(mxNote)
        return mxNoteList

    def _setMX(self, mxNote):
        '''Given an mxNote, fille the necessary parameters
        '''
        try:
            self.duration.mx = mxNote
        except duration.DurationException:
            environLocal.printDebug(['failed extaction of duration from musicxml', 'mxNote:', mxNote, self])
            raise

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
    if len(a.notations) > 0:
        if (isinstance(a.notations[0], music21.expressions.Fermata)):
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
            for obj in n.notations:
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
                n.lyric = str(n.beat)
                found.append(n.beat)
            
            for i in range(len(match)):
                self.assertEquals(match[i], found[i])

            #s.show()


    def testNoteEquality(self):
        from music21 import articulations

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
        t1 = Tie()
        t2 = Tie()
        for x, y, match in [(t1, None, False), (t1, t2, True)]:
            n1.tie = x
            n4.tie = y
            self.assertEqual(n1==n4, match) # sub4

        # with ties but different pitches
        for n in [n1, n2, n3, n4]:
            n.quarterLength = 1.0
        t1 = Tie()
        t2 = Tie()
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

#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Note, Rest]

if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        a = Test()
        b = TestExternal()



        #a.testNoteEquality()
        a.testNoteBeatProperty()