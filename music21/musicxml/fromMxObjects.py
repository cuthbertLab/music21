# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         musicxml/fromMxObjects.py
# Purpose:      Translate from MusicXML mxObjects to music21 objects
# 
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010-2013 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Low-level conversion routines from MusicXML to music21.

This module supposes that the musicxml document has already been parsed by xml.sax (by 
base.Document.read() ) and is stored as a collection of mxObjects -- equivalent parsing 
methods could be created and fed into `mxScoreToScore` to make this work.
'''
import copy
import pprint
import traceback
import unittest

from music21.musicxml import mxObjects

from music21 import common
from music21 import defaults
from music21 import exceptions21
from music21 import xmlnode

# modules that import this include converter.py.
# thus, cannot import these here
from music21 import articulations 
from music21 import bar
from music21 import beam
from music21 import chord
from music21 import clef
from music21 import duration
from music21 import dynamics
from music21 import expressions
from music21 import harmony # for chord symbols
from music21 import instrument
from music21 import interval # for transposing instruments
from music21 import key
from music21 import layout
from music21 import metadata
from music21 import note
from music21 import meter
from music21 import pitch
from music21 import repeat
from music21 import spanner
from music21 import stream
from music21 import tempo
from music21 import text # for text boxes
from music21 import tie

from music21 import environment
_MOD = "musicxml.fromMxObjects"
environLocal = environment.Environment(_MOD)



#-------------------------------------------------------------------------------
class FromMxObjectsException(exceptions21.Music21Exception):
    pass

class XMLBarException(FromMxObjectsException):
    pass



# def mod6IdLocal(spannerObj):
#     '''
#     returns the spanner idLocal as a number from 1-6 since
#     only 6 spanners of each type can be active at a time in musicxml
# 
#     
#     >>> s = stream.Score()
#     >>> for i in range(10):
#     ...    sp = spanner.Glissando()
#     ...    sp.idLocal = i + 1
#     ...    s.insert(0, sp)
#     >>> for sp in s.getElementsByClass('Spanner'):
#     ...    print sp.idLocal, musicxml.fromMxObjects.mod6IdLocal(sp)
#     1 1
#     2 2
#     3 3
#     4 4
#     5 5
#     6 6
#     7 1
#     8 2
#     9 3
#     10 4
#     '''
#     spanId = spannerObj.idLocal 
#     if spanId is None:
#         return 1
#     mod6Id = spanId % 6
#     if mod6Id == 0:
#         mod6Id = 6
#     return mod6Id


def configureStaffGroupFromMxPartGroup(staffGroup, mxPartGroup):
    '''
    Given an already instantiated spanner.StaffGroup, 
    configure it with parameters from an mxPartGroup.
    '''
    staffGroup.name = mxPartGroup.get('groupName')
    staffGroup.abbreviation = mxPartGroup.get('groupAbbreviation')
    staffGroup.symbol = mxPartGroup.get('groupSymbol')
    staffGroup.barTogether = mxPartGroup.get('groupBarline')
    staffGroup.completeStatus = True


def mxCreditToTextBox(mxCredit):
    '''Convert a MusicXML credit to a music21 TextBox

    
    >>> c = musicxml.mxObjects.Credit()
    >>> c.append(musicxml.mxObjects.CreditWords('testing'))
    >>> c.set('page', 2)
    >>> tb = musicxml.fromMxObjects.mxCreditToTextBox(c)
    >>> tb.page
    2
    >>> tb.content
    'testing'
    '''
    tb = text.TextBox()
    tb.page = mxCredit.get('page')
    content = []
    for mxCreditWords in mxCredit: # can iterate
        content.append(mxCreditWords.charData)
    if len(content) == 0: # no text defined
        raise FromMxObjectsException('no credit words defined for a credit tag')
    tb.content = '\n'.join(content) # join with \n
    # take formatting from the first, no matter if multiple are defined
    tb.positionVertical = mxCredit.componentList[0].get('default-y')
    tb.positionHorizontal = mxCredit.componentList[0].get('default-x')
    tb.justify = mxCredit.componentList[0].get('justify')
    tb.style = mxCredit.componentList[0].get('font-style')
    tb.weight = mxCredit.componentList[0].get('font-weight')
    tb.size = mxCredit.componentList[0].get('font-size')
    tb.alignVertical = mxCredit.componentList[0].get('valign')
    tb.alignHorizontal = mxCredit.componentList[0].get('halign')
    return tb



def mxTransposeToInterval(mxTranspose):
    '''Convert a MusicXML Transpose object to a music21 Interval object.
    
    >>> t = musicxml.mxObjects.Transpose()
    >>> t.diatonic = -1
    >>> t.chromatic = -2
    >>> musicxml.fromMxObjects.mxTransposeToInterval(t)
    <music21.interval.Interval M-2>

    >>> t = musicxml.mxObjects.Transpose()
    >>> t.diatonic = -5
    >>> t.chromatic = -9
    >>> musicxml.fromMxObjects.mxTransposeToInterval(t)
    <music21.interval.Interval M-6>

    >>> t = musicxml.mxObjects.Transpose()
    >>> t.diatonic = 3 # a type of 4th
    >>> t.chromatic = 6
    >>> musicxml.fromMxObjects.mxTransposeToInterval(t)
    <music21.interval.Interval A4>

    '''
    ds = None
    if mxTranspose.diatonic is not None:
        ds = int(mxTranspose.diatonic)
    cs = None
    if mxTranspose.chromatic is not None:
        cs = int(mxTranspose.chromatic)

    oc = 0
    if mxTranspose.octaveChange is not None:
        oc = int(mxTranspose.octaveChange) * 12

    # NOTE: presently not dealing with double
    # doubled one octave down from what is currently written 
    # (as is the case for mixed cello / bass parts in orchestral literature)
    #environLocal.printDebug(['ds', ds, 'cs', cs, 'oc', oc])
    if ds is not None and ds != 0 and cs is not None and cs != 0:
        # diatonic step can be used as a generic specifier here if 
        # shifted 1 away from zero
        if ds < 0:
            post = interval.intervalFromGenericAndChromatic(ds - 1, cs + oc)
        else:
            post = interval.intervalFromGenericAndChromatic(ds + 1, cs + oc)
    else: # assume we have chromatic; may not be correct spelling
        post = interval.Interval(cs + oc)
    return post

def mxToTempoIndication(mxMetronome, mxWords=None):
    '''
    Given an mxMetronome, convert to either a TempoIndication subclass, 
    either a tempo.MetronomeMark or tempo.MetricModulation.

    
    >>> m = musicxml.mxObjects.Metronome()
    >>> bu = musicxml.mxObjects.BeatUnit('half')
    >>> pm = musicxml.mxObjects.PerMinute(125)
    >>> m.append(bu)
    >>> m.append(pm)
    >>> musicxml.fromMxObjects.mxToTempoIndication(m)
    <music21.tempo.MetronomeMark Half=125.0>
    '''
    # get lists of durations and texts
    durations = []
    numbers = []

    dActive = None
    for mxObj in mxMetronome.componentList:
        if isinstance(mxObj, mxObjects.BeatUnit):
            durationType = musicXMLTypeToType(mxObj.charData)
            dActive = duration.Duration(type=durationType)
            durations.append(dActive)
        if isinstance(mxObj, mxObjects.BeatUnitDot):
            if dActive is None:
                raise FromMxObjectsException('encountered metronome components out of order')
            dActive.dots += 1 # add one dot each time these are encountered
        # should come last
        if isinstance(mxObj, mxObjects.PerMinute):
            #environLocal.printDebug(['found PerMinute', mxObj])
            # store as a number
            if mxObj.charData != '':
                numbers.append(float(mxObj.charData))

    if mxMetronome.isMetricModulation():
        mm = tempo.MetricModulation()
        #environLocal.printDebug(['found metric modulaton:', 'durations', durations])
        if len(durations) < 2:
            raise FromMxObjectsException('found incompletely specified musicxml metric moduation: '+
                                         'fewer than two durations defined')
        # all we have are referents, no values are defined in musicxml
        # will need to update context after adding to Stream
        mm.oldReferent = durations[0]
        mm.newReferent = durations[1]
    else:
        #environLocal.printDebug(['found metronome mark:', 'numbers', numbers])
        mm = tempo.MetronomeMark()
        if len(numbers) > 0:
            mm.number = numbers[0]
        if len(durations) > 0:
            mm.referent = durations[0]
        # TODO: set text if defined in words
        if mxWords is not None:
            pass

    paren = mxMetronome.get('parentheses')
    if paren is not None:
        if paren in ['yes']:
            mm.parentheses = True
    return mm

def mxToRepeat(mxBarline, inputM21=None):
    '''
    Given an mxBarline (not an mxRepeat object) with repeatObj as a parameter, 
    file the necessary parameters and return a bar.Repeat() object

    
    >>> mxRepeat = musicxml.mxObjects.Repeat()
    >>> mxRepeat.set('direction', 'backward')
    >>> mxRepeat.get('times') == None
    True
    >>> mxBarline = musicxml.mxObjects.Barline()
    >>> mxBarline.set('barStyle', 'light-heavy')
    >>> mxBarline.set('repeatObj', mxRepeat)
    >>> b = musicxml.fromMxObjects.mxToRepeat(mxBarline)
    >>> b
    <music21.bar.Repeat direction=end>

    Test that the music21 style for a backwards repeat is called "final"
    (because it resembles a final barline) but that the musicxml style
    is called light-heavy.

    >>> b.style
    'final'
    >>> b.direction
    'end'
    >>> mxBarline2 = musicxml.toMxObjects.repeatToMx(b)
    >>> mxBarline2.get('barStyle')
    'light-heavy'
    '''
    if inputM21 is None:
        r = bar.Repeat()
    else:
        r = inputM21

    r.style = mxBarline.get('barStyle')
    location = mxBarline.get('location')
    if location is not None:
        r.location = location

    mxRepeat = mxBarline.get('repeatObj')
    if mxRepeat is None:
        raise bar.BarException('attempting to create a Repeat from an MusicXML bar that does not ' +
                               'define a repeat')

    mxDirection = mxRepeat.get('direction')

    #environLocal.printDebug(['mxRepeat', mxRepeat, mxRepeat._attr])

    if mxDirection.lower() == 'forward':
        r.direction = 'start'
    elif mxDirection.lower() == 'backward':
        r.direction = 'end'
    else:
        raise bar.BarException('cannot handle mx direction format:', mxDirection)

    if mxRepeat.get('times') != None:
        # make into a number
        r.times = int(mxRepeat.get('times'))

    if inputM21 is None:
        return r



def mxToBarline(mxBarline, inputM21 = None):
    '''Given an mxBarline, fill the necessary parameters

    
    >>> mxBarline = musicxml.mxObjects.Barline()
    >>> mxBarline.set('barStyle', 'light-light')
    >>> mxBarline.set('location', 'right')
    >>> b = musicxml.fromMxObjects.mxToBarline(mxBarline)
    >>> b.style  # different in music21 than musicxml
    'double'
    >>> b.location
    'right'
    '''
    if inputM21 is None:
        b = bar.Barline()
    else:
        b = inputM21
    b.style = mxBarline.get('barStyle')
    location = mxBarline.get('location')
    if location is not None:
        b.location = location

    if inputM21 is None:
        return b
    
#-------------------------------------------------------------------------------
def mxGraceToGrace(noteOrChord, mxGrace=None):
    '''
    Given a completely formed, non-grace Note or Chord, create and 
    return a m21 grace version of the same.

    If mxGrace is None, no change is made and the same object is returned.
    '''
    if mxGrace is None:
        return noteOrChord

    post = noteOrChord.getGrace()
    if mxGrace.get('slash') in ['yes', None]:

        post.duration.slash = True
    else:
        post.duration.slash = False

    post.duration.stealTimePrevious = mxGrace.get('steal-time-previous')
    post.duration.stealTimeFollowing = mxGrace.get('steal-time-following')

    return post



#-------------------------------------------------------------------------------
# Pitch and pitch components

def mxToAccidental(mxAccidental, inputM21Object = None):
    '''
    
    >>> a = musicxml.mxObjects.Accidental()
    >>> a.set('content', 'half-flat')
    >>> a.get('content')
    'half-flat'

    >>> b = pitch.Accidental()
    >>> bReference = musicxml.fromMxObjects.mxToAccidental(a, b)
    >>> b is bReference
    True
    >>> b.name
    'half-flat'
    >>> b.alter
    -0.5
    '''    
    if inputM21Object == None:
        acc = pitch.Accidental()
    else:
        acc = inputM21Object
 
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
    # need to use set here to get all attributes up to date
    acc.set(name)

    return acc


def mxToPitch(mxNote, inputM21=None):
    '''
    Given a MusicXML Note object, set this Pitch object to its values.

    >>> b = musicxml.mxObjects.Pitch()
    >>> b.set('octave', 3)
    >>> b.set('step', 'E')
    >>> b.set('alter', -1)
    >>> c = musicxml.mxObjects.Note()
    >>> c.set('pitch', b)
    >>> a = pitch.Pitch('g#4')
    >>> a = musicxml.fromMxObjects.mxToPitch(c)
    >>> print(a)
    E-3
    '''
    if inputM21 == None:
        p = pitch.Pitch()
    else:
        p = inputM21

    # assume this is an object
    mxPitch = mxNote.get('pitchObj')
    mxAccidental = mxNote.get('accidentalObj')

    p.step = mxPitch.get('step')

    # sometimes we have an accidental defined but no alter value, due to 
    # a natural; need to look at mxAccidental directly
    mxAccidentalCharData = None
    if mxAccidental != None:
        mxAccidentalCharData = mxAccidental.get('charData')
        #environLocal.printDebug(['found mxAccidental charData', mxAccidentalCharData])

    acc = mxPitch.get('alter')
    # None is used in musicxml but not in music21
    if acc != None or mxAccidentalCharData != None:
        if mxAccidental is not None: # the source had wanted to show alter
            try:
                accObj = mxToAccidental(mxAccidental)
                # used to to just use acc value
                # self.accidental = Accidental(float(acc))
                # better to use accObj if possible
                p.accidental = accObj
                p.accidental.displayStatus = True
            except pitch.AccidentalException:
                # MuseScore 0.9.6 generates Accidentals with empty objects
                pass
        else:
            # here we generate an accidental object from the alter value
            # but in the source, there was not a defined accidental
            try:
                p.accidental = pitch.Accidental(float(acc))
            except pitch.AccidentalException:
                raise FromMxObjectsException('incorrect accidental %s for pitch %s' % (str(acc), p))
            p.accidental.displayStatus = False
    p.octave = int(mxPitch.get('octave'))
    return p

#-------------------------------------------------------------------------------
# Ties

def mxToTie(mxNote, inputM21=None):
    '''
    Translate a MusicXML :class:`~music21.musicxml.mxObjects.Note` (sic!) to a music21 
    :class:`~music21.tie.Tie` object according to its <tieList> parameter.
    
    Only called if the mxObjects.Note has a tieList that is not blank, so as not to
    create additional ties.
    '''
    if inputM21 == None:
        t = tie.Tie()
    else:
        t = inputM21

    mxTieList = mxNote.get('tieList')
    if len(mxTieList) > 0:
        # get all types and see what we have for this note
        typesFound = []
        for mxTie in mxTieList:
            typesFound.append(mxTie.get('type'))
        # trivial case: have only 1
        if len(typesFound) == 1:
            t.type = typesFound[0]
        elif typesFound == ['stop', 'start']:
            t.type = 'continue'
            #self.type = 'start'
        else:
            environLocal.printDebug(['found unexpected arrangement of multiple tie types when ' +
                                     'importing from musicxml:', typesFound])

# from old note.py code
    # not sure this is necessary
#         mxNotations = mxNote.get('notations')
#         if mxNotations != None:
#             mxTiedList = mxNotations.getTieds()
            # should be sufficient to only get mxTieList

    if inputM21 is None:
        return t

#-------------------------------------------------------------------------------
# Lyrics

def mxToLyric(mxLyric, inputM21=None):
    '''
    Translate a MusicXML :class:`~music21.musicxml.mxObjects.Lyric` object to a 
    music21 :class:`~music21.note.Lyric` object.
    
    If inputM21 is a :class:`~music21.note.Lyric` object, then the values of the 
    mxLyric are transfered there and nothing returned.
    
    Otherwise, a new `Lyric` object is created and returned.
    
    
    >>> mxLyric = musicxml.mxObjects.Lyric()
    >>> mxLyric.set('text', 'word')
    >>> mxLyric.set('number', 4)
    >>> mxLyric.set('syllabic', 'single')
    >>> lyricObj = note.Lyric()
    >>> musicxml.fromMxObjects.mxToLyric(mxLyric, lyricObj)
    >>> lyricObj
    <music21.note.Lyric number=4 syllabic=single text="word">
    
    Non-numeric MusicXML lyric "number"s are converted to identifiers:
    
    >>> mxLyric.set('number', 'part2verse1')    
    >>> l2 = musicxml.fromMxObjects.mxToLyric(mxLyric)
    >>> l2
    <music21.note.Lyric number=0 identifier="part2verse1" syllabic=single text="word">
    
    '''
    if inputM21 is None:
        l = note.Lyric()
    else:
        l = inputM21

    l.text = mxLyric.get('text')
    
    
    # This is new to account for identifiers
    
    number = mxLyric.get('number')
    
    if common.isNum(number):
        l.number = number
    else:
        l.number = 0  #If musicXML lyric number is not a number, set it to 0. This tells the caller of
                        #mxToLyric that a new number needs to be given based on the lyrics context amongst other lyrics.
        l.identifier = number
    
    # Used to be l.number = mxLyric.get('number')
    
    l.syllabic = mxLyric.get('syllabic')

    if inputM21 is None:
        return l

#-------------------------------------------------------------------------------
# Durations

def musicXMLTypeToType(value):
    '''
    Utility function to convert a MusicXML duration type to an music21 duration type.
    
    Changes 'long' to 'longa' and deals with a Guitar Pro 5.2 bug in MusicXML
    export, that exports a 32nd note with the type '32th'.

    
    >>> musicxml.fromMxObjects.musicXMLTypeToType('long')
    'longa'
    >>> musicxml.fromMxObjects.musicXMLTypeToType('32th')
    '32nd'
    >>> musicxml.fromMxObjects.musicXMLTypeToType('quarter')
    'quarter'
    >>> musicxml.fromMxObjects.musicXMLTypeToType(None)
    Traceback (most recent call last):
    FromMxObjectsException...
    '''
    # MusicXML uses long instead of longa
    if value not in duration.typeToDuration:
        if value == 'long':
            return 'longa'
        elif value == '32th':
            return '32nd'
        else:
            raise FromMxObjectsException('found unknown MusicXML type: %s' % value)
    else:
        return value

def mxToDuration(mxNote, inputM21=None):
    '''
    Translate a `MusicXML` :class:`~music21.musicxml.mxObjects.Note` object 
    to a music21 :class:`~music21.duration.Duration` object.

    >>> a = musicxml.mxObjects.Note()
    >>> a.setDefaults()
    >>> m = musicxml.mxObjects.Measure()
    >>> m.setDefaults()
    >>> a.external['measure'] = m # assign measure for divisions ref
    >>> a.external['divisions'] = m.external['divisions']

    >>> c = duration.Duration()
    >>> musicxml.fromMxObjects.mxToDuration(a, c)
    <music21.duration.Duration 1.0>
    >>> c.quarterLength
    1.0
    '''
    if inputM21 == None:
        d = duration.Duration()
    else:
        d = inputM21

    if mxNote.external['measure'] == None:
        raise FromMxObjectsException(
        "cannot determine MusicXML duration without a reference to a measure (%s)" % mxNote)

    mxDivisions = mxNote.external['divisions']
    if mxNote.duration is not None:
        if mxNote.get('type') is not None:
            durationType = musicXMLTypeToType(mxNote.get('type'))
            forceRaw = False
        else: # some rests do not define type, and only define duration
            durationType = None # no type to get, must use raw
            forceRaw = True
        mxDotList = mxNote.get('dotList')
        # divide mxNote duration count by divisions to get qL
        qLen = float(mxNote.duration) / float(mxDivisions)
        # mxNotations = mxNote.get('notationsObj')
        mxTimeModification = mxNote.get('timeModificationObj')

        if mxTimeModification is not None:
            tup = mxToTuplet(mxNote)
            # get all necessary config from mxNote
            #environLocal.printDebug(['created Tuplet', tup])
            # need to see if there is more than one component
            #self.components[0]._tuplets.append(tup)
        else:
            tup = None
        # two ways to create durations, raw and cooked
        if forceRaw:
            #environLocal.printDebug(['forced to use raw duration', durRaw])
            durRaw = duration.Duration() # raw just uses qLen
            # the qLen set here may not be computable, but is not immediately
            # computed until setting components
            durRaw.quarterLength = qLen
            try:
                d.components = durRaw.components
            except duration.DurationException:
                environLocal.warn(['mxToDuration', 'supplying quarterLength of 1 as type is not ' +
                                   'defined and raw quarterlength (%s) is not a computable duration' % qLen])
                environLocal.printDebug(['mxToDuration', 'raw qLen', qLen, durationType, 
                                         'mxNote.duration:', mxNote.duration, 
                                         'last mxDivisions:', mxDivisions])
                durRaw.quarterLength = 1.
        else: # a cooked version builds up from pieces
            durUnit = duration.durationTupleFromTypeDots(durationType, len(mxDotList))
            durCooked = duration.Duration(components=[durUnit])
            if not tup == None:
                d.tuplets = (tup,)
            # old way just used qLen
            #self.quarterLength = qLen
            d.components = durCooked.components
    # if mxNote.duration is None, this is a grace note, and duration
    # is based entirely on type
    if mxNote.duration is None:
        d = duration.Duration()
        d.type = musicXMLTypeToType(mxNote.get('type'))
        d.dots = len(mxNote.get('dotList'))
        #environLocal.printDebug(['got mx duration of None', d])

    return d

def mxToOffset(mxDirection, mxDivisions):
    '''
    Translate a MusicXML :class:`~music21.musicxml.mxObjects.Direction` 
    with an offset value to an offset in music21.
    '''
    if mxDivisions is None:
        raise FromMxObjectsException(
        "cannot determine MusicXML duration without a reference to a measure (%s)" % mxDirection)
    if mxDirection.offset is None:
        return 0.0
    else:
        #environLocal.printDebug(['mxDirection.offset', mxDirection.offset, 'mxDivisions', mxDivisions])
        return float(mxDirection.offset) / float(mxDivisions)


def mxToTuplet(mxNote, inputM21Object = None):
    '''
    Given an mxNote, based on mxTimeModification 
    and mxTuplet objects, return a Tuplet object
    (or alter the input object and then return it)
    ''' 
    if inputM21Object is None:
        t = duration.Tuplet()
    else:
        t = inputM21Object
    if t.frozen is True:
        raise duration.TupletException("A frozen tuplet (or one attached to a duration) " +
                                       "is immutable")

    mxTimeModification = mxNote.get('timeModificationObj')
    #environLocal.printDebug(['got mxTimeModification', mxTimeModification])

    t.numberNotesActual = int(mxTimeModification.get('actual-notes'))
    t.numberNotesNormal = int(mxTimeModification.get('normal-notes'))
    mxNormalType = mxTimeModification.get('normal-type')
    # TODO: implement dot
    # mxNormalDot = mxTimeModification.get('normal-dot')



    if mxNormalType != None:
        # this value does not seem to frequently be supplied by mxl
        # encodings, unless it is different from the main duration
        # this sets both actual and noraml types to the same type
        t.setDurationType(musicXMLTypeToType(
                                mxTimeModification.get('normal-type')))
    else: # set to type of duration
        t.setDurationType(musicXMLTypeToType(mxNote.get('type')))

    mxNotations = mxNote.get('notationsObj')
    #environLocal.printDebug(['got mxNotations', mxNotations])

    if mxNotations != None and len(mxNotations.getTuplets()) > 0:
        mxTuplet = mxNotations.getTuplets()[0] # a list, but only use first
        #environLocal.printDebug(['got mxTuplet', mxTuplet])

        t.type = mxTuplet.get('type') 
        t.bracket = mxObjects.yesNoToBoolean(mxTuplet.get('bracket'))
        #environLocal.printDebug(['got bracket', self.bracket])
        showNumber = mxTuplet.get('show-number')
        if showNumber is not None and showNumber == 'none':
            # do something for 'both'; 'actual' is the default
            t.tupletActualShow = 'none'

        t.placement = mxTuplet.get('placement') 

    return t

#-------------------------------------------------------------------------------
# Meters


def mxToTimeSignature(mxTimeList, inputM21=None):
    '''
    Given an mxTimeList, load this object

    if inputM21 is None, create a new TimeSignature
    and return it.

    
    >>> mxTime = musicxml.mxObjects.Time()
    >>> mxTime.setDefaults()
    >>> mxAttributes = musicxml.mxObjects.Attributes()
    >>> mxAttributes.timeList.append(mxTime)
    >>> ts = meter.TimeSignature()
    >>> musicxml.fromMxObjects.mxToTimeSignature(mxAttributes.timeList, ts)
    >>> ts.numerator
    4
    '''
    if inputM21 is None:
        ts = meter.TimeSignature()
    else:
        ts = inputM21

    if not common.isListLike(mxTimeList): # if just one
        mxTime = mxTimeList
    else: # there may be more than one if we have more staffs per part
        mxTime = mxTimeList[0]

    n = []
    d = []
    for obj in mxTime.componentList:
        if isinstance(obj, mxObjects.Beats):
            n.append(obj.charData) # may be 3+2
        if isinstance(obj, mxObjects.BeatType):
            d.append(obj.charData)

    #n = mxTime.get('beats')
    #d = mxTime.get('beat-type')
    # convert into a string
    msg = []
    for i in range(len(n)):
        msg.append('%s/%s' % (n[i], d[i]))

    #environLocal.printDebug(['loading meter string:', '+'.join(msg)])
    ts.load('+'.join(msg))

    if inputM21 is None:
        return ts

#--------------------------------------------------------
# Key/KeySignatures

def mxKeyListToKeySignature(mxKeyList, inputM21 = None):
    '''
    Given a mxKey object or keyList, return a music21.key.KeySignature
    object and return it, or if inputM21 is None, change its
    attributes and return nothing.
    
    >>> mxk = musicxml.mxObjects.Key()
    >>> mxk.set('fifths', 5)
    >>> ks = key.KeySignature()
    >>> musicxml.fromMxObjects.mxKeyListToKeySignature(mxk, ks)
    >>> ks.sharps
    5 
    
    Or just get a new KeySignature object from scratch:
    
    >>> mxk.set('fifths', -2)
    >>> ks2 = musicxml.fromMxObjects.mxKeyListToKeySignature(mxk)
    >>> ks2
    <music21.key.KeySignature of 2 flats>
    '''
    if inputM21 is None:
        ks = key.KeySignature()
    else:
        ks = inputM21

    if not common.isListLike(mxKeyList):
        mxKey = mxKeyList
    else: # there may be more than one if we have more staffs per part
        mxKey = mxKeyList[0]

    fifths = mxKey.get('fifths')
    if fifths is None:
        fifths = 0
    ks.sharps = int(fifths)
    mxMode = mxKey.get('mode')
    if mxMode != None:
        ks.mode = mxMode

    if inputM21 is None:
        return ks

#--------------------------------------------------------
# clefs

def mxClefToClef(mxClefList, inputM21 = None):
    '''
    Given a MusicXML Clef object, return a music21 
    Clef object

    
    >>> a = musicxml.mxObjects.Clef()   
    >>> a.set('sign', 'G')
    >>> a.set('line', 2)
    >>> b = clef.Clef()
    >>> b
    <music21.clef.Clef>
    >>> 'TrebleClef' in b.classes
    False
    >>> musicxml.fromMxObjects.mxClefToClef(a, b)
    >>> b.sign
    'G'
    >>> 'TrebleClef' in b.classes
    True
    >>> b
    <music21.clef.TrebleClef>
    
    
    Create a new clef from thin air:
    
    >>> a = musicxml.mxObjects.Clef()   
    >>> a.set('sign', 'TAB')
    >>> c = musicxml.fromMxObjects.mxClefToClef(a)
    >>> c
    <music21.clef.TabClef>
    '''    
    if not common.isListLike(mxClefList):
        mxClef = mxClefList # its not a list
    else: # just get first for now
        mxClef = mxClefList[0]

    sign = mxClef.get('sign')
    if sign.lower() in ('tab', 'percussion', 'none', 'jianpu'):
        clefObj = clef.clefFromString(sign)
    else:
        line = mxClef.get('line')
        mxOctaveChange = mxClef.get('clefOctaveChange')
        if mxOctaveChange != None:
            octaveChange = int(mxOctaveChange)
        else:
            octaveChange = 0
        clefObj = clef.clefFromString(sign + str(line), octaveChange)

    if inputM21 is None:
        return clefObj
    else:
        inputM21.__class__ = clefObj.__class__
        inputM21.sign = clefObj.sign
        inputM21.line = clefObj.line
        inputM21.octaveChange = clefObj.octaveChange
#-------------------------------------------------------------------------------
# Dynamics

def mxToDynamicList(mxDirection):
    '''
    Given an mxDirection, load instance

    
    >>> mxDirection = musicxml.mxObjects.Direction()
    >>> mxDirectionType = musicxml.mxObjects.DirectionType()
    >>> mxDynamicMark = musicxml.mxObjects.DynamicMark('ff')
    >>> mxDynamics = musicxml.mxObjects.Dynamics()
    >>> mxDynamics.set('default-y', -20)
    >>> mxDynamics.append(mxDynamicMark)
    >>> mxDirectionType.append(mxDynamics)
    >>> mxDirection.append(mxDirectionType)

    >>> a = dynamics.Dynamic()
    >>> a = musicxml.fromMxObjects.mxToDynamicList(mxDirection)[0]
    >>> a.value
    'ff'
    >>> a.englishName
    'very loud'
    >>> a._positionDefaultY
    -20
    '''
    # can probably replace this with mxDirection.getDynamicMark()
    # need to test
    mxDynamics = None
    for mxObj in mxDirection:
        if isinstance(mxObj, mxObjects.DirectionType):
            for mxObjSub in mxObj:
                if isinstance(mxObjSub, mxObjects.Dynamics):
                    mxDynamics = mxObjSub
    if mxDynamics == None:
        raise dynamics.DynamicException('when importing a Dynamics object from MusicXML, ' +
                                        'did not find a DynamicMark')
#     if len(mxDynamics) > 1:
#         raise dynamics.DynamicException('when importing a Dynamics object from MusicXML, '
#                                         'found more than one DynamicMark contained, namely %s' % 
#                                            str(mxDynamics))

    post = []
    for sub in mxDynamics.componentList:
        d = dynamics.Dynamic()
        # palcement is found in outermost object
        if mxDirection.get('placement') is not None:
            d._positionPlacement = mxDirection.get('placement')

        # the tag is the dynamic mark value
        mxDynamicMark = sub.get('tag')
        d.value = mxDynamicMark
        for dst, src in [('_positionDefaultX', 'default-x'),
                         ('_positionDefaultY', 'default-y'),
                         ('_positionRelativeX', 'relative-x'),
                         ('_positionRelativeY', 'relative-y')]:
            if mxDynamics.get(src) is not None:
                setattr(d, dst, mxDynamics.get(src))
        post.append(d)
    return post



def mxToTextExpression(mxDirection):
    '''
    Given an mxDirection, create one or more TextExpressions
    '''
    post = []
    mxWordsList = mxDirection.getWords()
    for mxWords in mxWordsList:
        #environLocal.printDebug(['mxToTextExpression()', mxWords, mxWords.charData])
        # content can be passed with creation argument
        te = expressions.TextExpression(mxWords.charData)

        te.justify = mxWords.get('justify')
        te.size = mxWords.get('font-size')
        te.letterSpacing = mxWords.get('letter-spacing')
        te.enclosure = mxWords.get('enclosure')
        te.positionVertical = mxWords.get('default-y')

        # two parameters that are combined
        style = mxWords.get('font-style')
        if style == 'normal':
            style = None
        weight = mxWords.get('font-weight')
        if weight == 'normal':
            weight = None
        if style is not None and weight is not None:
            if style == 'italic' and weight == 'bold':
                te.style = 'bolditalic'
        # one is None
        elif style == 'italic':
            te.style = 'italic'
        elif weight == 'bold':
            te.style = 'bold'

        post.append(te)

    return post


def mxToCoda(mxCoda):
    '''
    Translate a MusicXML :class:`~music21.musicxml.mxObjects.Coda` object 
    to a music21 :class:`~music21.repeat.Coda` object.
    '''
    rm = repeat.Coda()
    rm._positionDefaultX = mxCoda.get('default-x')
    rm._positionDefaultY = mxCoda.get('default-y')
    return rm

def mxToSegno(mxCoda):
    '''
    Translate a MusicXML :class:`~music21.musicxml.mxObjects.Coda` object 
    to a music21 :class:`~music21.repeat.Coda` object.
    '''
    rm = repeat.Segno()
    rm._positionDefaultX = mxCoda.get('default-x')
    rm._positionDefaultY = mxCoda.get('default-y')
    return rm

def mxToRepeatExpression(mxDirection):
    '''
    Given an mxDirection that may define a coda, segno, or other repeat 
    expression statement, realize the appropriate music21 object.
    '''
    pass
    # note: this may not be needed, as mx text expressions are converted to repeat objects in measure processing

#-------------------------------------------------------------------------------
# Harmony

def mxToChordSymbol(mxHarmony):
    '''
    Convert a musicxml.mxObjects.Harmony() object to a harmony.ChordSymbol object:
    
    >>> mxHarmony = musicxml.mxObjects.Harmony()
    >>> mxKind = musicxml.mxObjects.Kind()
    >>> mxKind.charData = 'major-seventh'
    >>> mxHarmony.kindObj = mxKind
    >>> mxRoot = musicxml.mxObjects.Root()
    >>> mxRoot.set('root-step', 'D')
    >>> mxRoot.set('root-alter', '-1')
    >>> mxHarmony.rootObj = mxRoot
    >>> cs = musicxml.fromMxObjects.mxToChordSymbol(mxHarmony)
    >>> cs
    <music21.harmony.ChordSymbol D-maj7>

    >>> cs.figure
    'D-maj7'

    >>> cs.pitches
    (<music21.pitch.Pitch D-3>, <music21.pitch.Pitch F3>, <music21.pitch.Pitch A-3>, <music21.pitch.Pitch C4>)

    >>> cs.root()
    <music21.pitch.Pitch D-3>
    
    TODO: this is very classically-oriented.  Make more Jazz/Rock like possible/default?.
    
    >>> mxKind.charData = 'major-sixth'
    >>> cs = musicxml.fromMxObjects.mxToChordSymbol(mxHarmony)
    >>> cs
    <music21.harmony.ChordSymbol D-6>

    >>> cs.figure
    'D-6'

    >>> cs.pitches
    (<music21.pitch.Pitch D-3>, <music21.pitch.Pitch F3>, <music21.pitch.Pitch A-3>, <music21.pitch.Pitch B-3>)

    >>> cs.root()
    <music21.pitch.Pitch D-3>  
    '''
    #environLocal.printDebug(['mxToChordSymbol():', mxHarmony])
    cs = harmony.ChordSymbol()
    
    mxKind = mxHarmony.get('kind')
    if mxKind is not None:
        cs.chordKind = mxKind.charData
        mxKindText = mxKind.get('text')
        if mxKindText is not None:
            cs.chordKindStr = mxKindText

    mxRoot = mxHarmony.get('root')
    if mxRoot is not None:
        r = pitch.Pitch(mxRoot.get('rootStep'))
        if mxRoot.get('rootAlter') is not None:
            # can provide integer to create accidental on pitch
            r.accidental = pitch.Accidental(int(mxRoot.get('rootAlter')))
        # set Pitch object on Harmony
        cs.root(r)

    mxBass = mxHarmony.get('bass')
    if mxBass is not None:
        b = pitch.Pitch(mxBass.get('bassStep'))
        if mxBass.get('bassAlter') is not None:
            # can provide integer to create accidental on pitch
            b.accidental = pitch.Accidental(int(mxBass.get('bassAlter')))
        # set Pitch object on Harmony
        cs.bass(b)
    else:
        cs.bass(r) #set the bass to the root if root is none

    mxInversion = mxHarmony.get('inversion')
    if mxInversion is not None:
        cs.inversion(int(mxInversion), transposeOnSet=False) # must be an int

    mxFunction = mxHarmony.get('function')
    if mxFunction is not None:
        cs.romanNumeral = mxFunction # goes to roman property

    mxDegree = mxHarmony.get('degree')
    
    if mxDegree is not None: # a list of components
        ChordStepModifications = []
        hd = None
        for mxSub in mxDegree.componentList:
            # this is the assumed order of triples
            if isinstance(mxSub, mxObjects.DegreeValue):
                if hd is not None: # already set
                    ChordStepModifications.append(hd)
                    hd = None
                if hd is None:
                    hd = harmony.ChordStepModification()
                hd.degree = int(mxSub.charData)
            elif isinstance(mxSub, mxObjects.DegreeAlter):
                hd.interval = int(mxSub.charData)
            elif isinstance(mxSub, mxObjects.DegreeType):
                hd.modType = mxSub.charData
            else:
                raise FromMxObjectsException('found unexpected object in degree tag: %s' % mxSub)
            
        
        
        # must get last on loop exit
        if hd is not None:
            ChordStepModifications.append(hd)
        for hd in ChordStepModifications:
            cs.addChordStepModification(hd)
    cs._updatePitches()
    #environLocal.printDebug(['mxToHarmony(): Harmony object', h])
    if cs.root().name != r.name:
        cs.root(r)
    return cs


#-------------------------------------------------------------------------------
# Instruments


def mxToInstrument(mxScorePart, inputM21=None):
    '''
    Return a generic instrument.Instrument object from this mxScorePart
    '''
    
    # note: transposition values is not set in this operation, but in 
    # mxToStreamPart
    if inputM21 is None:
        i = instrument.Instrument()
    else:
        i = inputM21

    def _cleanStr(badStr):
        # need to remove badly-formed strings
        if badStr is None:
            return None
        badStr = badStr.strip()
        goodStr = badStr.replace('\n', ' ')
        return goodStr

    i.partId = _cleanStr(mxScorePart.get('id'))
    i.partName = _cleanStr(mxScorePart.get('partName'))
    i.partAbbreviation = _cleanStr(mxScorePart.get('partAbbreviation'))

    # for now, just get first instrument
    if len(mxScorePart.scoreInstrumentList) > 0:
        mxScoreInstrument = mxScorePart.scoreInstrumentList[0]
        i.instrumentName = _cleanStr(mxScoreInstrument.get('instrumentName'))
        i.instrumentAbbreviation = _cleanStr(mxScoreInstrument.get(
                                        'instrumentAbbreviation'))
    if len(mxScorePart.midiInstrumentList) > 0:
        # for now, just get first midi instrument
        mxMIDIInstrument = mxScorePart.midiInstrumentList[0]
        # musicxml counts from 1, not zero
        mp = mxMIDIInstrument.get('midiProgram')
        if mp is not None:
            i.midiProgram = int(mp) - 1
        mc = mxMIDIInstrument.get('midiChannel')
        if mc is not None:
            i.midiChannel = int(mc) - 1

    if inputM21 is None:
        return i

#-------------------------------------------------------------------------------
# unified processors for Chords and Notes


def mxNotationsToSpanners(target, mxNotations, spannerBundle):
    '''
    General routines for gathering spanners from notes via mxNotations objects and placing them 
    in a spanner bundle.

    Spanners may be found in musicXML notations and directions objects.

    The passed-in spannerBundle will be edited in-place; existing spanners may be completed, or 
    new spanners may be added.

    The `target` object is a reference to the relevant music21 object this spanner is associated 
    with.
    '''
    mxSlurList = mxNotations.getSlurs()
    for mxObj in mxSlurList:
        # look at all spanners and see if we have an open, matching
        # slur to place this in
        idFound = mxObj.get('number')
        # returns a new spanner bundle with just the result of the search
        #environLocal.printDebug(['spanner bundle: getByCompleteStatus(False)', spannerBundle.getByCompleteStatus(False)])

        #sb = spannerBundle.getByIdLocal(idFound).getByCompleteStatus(False)
        sb = spannerBundle.getByClassIdLocalComplete('Slur', idFound, False)
        if len(sb) > 0: # if we already have a slur
            #environLocal.printDebug(['found a match in SpannerBundle'])
            su = sb[0] # get the first
        else: # create a new slur
            su = spanner.Slur()
            su.idLocal = idFound
            su.placement = mxObj.get('placement')
            spannerBundle.append(su)
        # add a reference of this note to this spanner
        su.addSpannedElements(target)
        #environLocal.printDebug(['adding n', n, id(n), 'su.getSpannedElements', su.getSpannedElements(), su.getSpannedElementIds()])
        if mxObj.get('type') == 'stop':
            su.completeStatus = True
            # only add after complete

    mxWavyLineList = mxNotations.getWavyLines()
    for mxObj in mxWavyLineList:
        #environLocal.printDebug(['waveyLines', mxObj])
        idFound = mxObj.get('number')
        sb = spannerBundle.getByClassIdLocalComplete('TrillExtension',
            idFound, False)
        if len(sb) > 0: # if we already have 
            su = sb[0] # get the first
        else: # create a new spanner
            su = expressions.TrillExtension()
            su.idLocal = idFound
            su.placement = mxObj.get('placement')
            spannerBundle.append(su)
        # add a reference of this note to this spanner
        su.addSpannedElements(target)
        if mxObj.get('type') == 'stop':
            su.completeStatus = True
            # only add after complete

    mxTremoloList = mxNotations.getTremolos()
    for mxObj in mxTremoloList:
        environLocal.printDebug(['mxTremoloList', mxObj])
        tremoloType = mxObj.get('type')
        isSingle = True
        try:
            numMarks = int(mxObj.charData)
        except (ValueError, TypeError):
            #environLocal.warn("could not convert ", dir(mxObj))
            numMarks = 3

        #environLocal.warn('tremoloType', tremoloType)        
        if tremoloType in ('start', 'stop'):
            isSingle = False
        
        if isSingle is True:
            environLocal.printDebug(['creating single Tremolo'])
            ts = expressions.Tremolo()            
            ts.numberOfMarks = numMarks
            target.expressions.append(ts)
            continue
        # else...
        idFound = 1 # mxObj.get('number') -- tremolo has no id number
        sb = spannerBundle.getByClassIdLocalComplete('TremoloSpanner',
            idFound, False)
        if len(sb) > 0: # if we already have 
            su = sb[0] # get the first
        else: # create a new spanner
            #environLocal.warn(['creating TremoloSpanner'])
            su = expressions.TremoloSpanner()
            su.numberOfMarks = numMarks
            su.idLocal = idFound
            #su.placement = mxObj.get('placement')
            spannerBundle.append(su)
        # add a reference of this note to this spanner
        #environLocal.warn('adding target', target)        
        su.addSpannedElements(target)
        # can be stop or None; we can have empty single-element tremolo
        if tremoloType == 'stop':
            su.completeStatus = True
            # only add after complete


    mxGlissandoList = mxNotations.getGlissandi()
    for mxObj in mxGlissandoList:
        idFound = mxObj.get('number')
        sb = spannerBundle.getByClassIdLocalComplete('Glissando',
            idFound, False)
        if len(sb) > 0: # if we already have 
            su = sb[0] # get the first
        else: # create a new spanner
            su = spanner.Glissando()
            su.idLocal = idFound
            su.lineType = mxObj.get('line-type')
            spannerBundle.append(su)
        # add a reference of this note to this spanner
        su.addSpannedElements(target)
        if mxObj.get('type') == 'stop':
            su.completeStatus = True
            # only add after complete


def mxDirectionToSpanners(targetLast, mxDirection, spannerBundle):
    '''Some spanners, such as MusicXML octave-shift, are encoded as MusicXML directions.
    '''    
    mxWedge = mxDirection.getWedge()
    if mxWedge is not None:
        mxType = mxWedge.get('type')
        idFound = mxWedge.get('number')
        #environLocal.printDebug(['mxDirectionToSpanners', 'found mxWedge', mxType, idFound])
        if mxType == 'crescendo':
            sp = dynamics.Crescendo()
            sp.idLocal = idFound
            spannerBundle.append(sp)
            # define this spanner as needing component assignment from
            # the next general note
            spannerBundle.setPendingSpannedElementAssignment(sp, 'GeneralNote')
        elif mxType == 'diminuendo':
            sp = dynamics.Diminuendo()
            sp.idLocal = idFound
            spannerBundle.append(sp)
            spannerBundle.setPendingSpannedElementAssignment(sp, 'GeneralNote')
        elif mxType == 'stop':
            # need to retrieve an existing spanner
            # try to get base class of both Crescendo and Decrescendo
            sp = spannerBundle.getByClassIdLocalComplete('DynamicWedge',
                    idFound, False)[0] # get first
            sp.completeStatus = True
            # will only have a target if this follows the note
            if targetLast is not None:
                sp.addSpannedElements(targetLast)
        else:
            raise FromMxObjectsException('unidentified mxType of mxWedge:', mxType)

    mxBracket = mxDirection.getBracket()
    if mxBracket is not None:
        mxType = mxBracket.get('type')
        idFound = mxBracket.get('number')
        #environLocal.printDebug(['mxDirectionToSpanners', 'found mxBracket', mxType, idFound])
        if mxType == 'start':
            sp = spanner.Line()
            sp.idLocal = idFound
            sp.startTick = mxBracket.get('line-end')
            sp.startHeight = mxBracket.get('end-length')
            sp.lineType = mxBracket.get('line-type')

            spannerBundle.append(sp)
            # define this spanner as needing component assignment from
            # the next general note
            spannerBundle.setPendingSpannedElementAssignment(sp, 'GeneralNote')
        elif mxType == 'stop':
            # need to retrieve an existing spanner
            # try to get base class of both Crescendo and Decrescendo
            sp = spannerBundle.getByClassIdLocalComplete('Line',
                    idFound, False)[0] # get first
            sp.completeStatus = True

            sp.endTick = mxBracket.get('line-end')
            sp.endHeight = mxBracket.get('end-length')
            sp.lineType = mxBracket.get('line-type')

            # will only have a target if this follows the note
            if targetLast is not None:
                sp.addSpannedElements(targetLast)
        else:
            raise FromMxObjectsException('unidentified mxType of mxBracket:', mxType)

    mxDashes = mxDirection.getDashes()
    # import mxDashes as m21 Line objects
    if mxDashes is not None:
        mxType = mxDashes.get('type')
        idFound = mxDashes.get('number')
        #environLocal.printDebug(['mxDirectionToSpanners', 'found mxDashes', mxType, idFound])
        if mxType == 'start':
            sp = spanner.Line()
            sp.idLocal = idFound
            sp.startTick = 'none'
            sp.lineType = 'dashed'
            spannerBundle.append(sp)
            # define this spanner as needing component assignment from
            # the next general note
            spannerBundle.setPendingSpannedElementAssignment(sp, 'GeneralNote')
        elif mxType == 'stop':
            # need to retrieve an existing spanner
            # try to get base class of both Crescendo and Decrescendo
            sp = spannerBundle.getByClassIdLocalComplete('Line',
                    idFound, False)[0] # get first
            sp.completeStatus = True
            sp.endTick = 'none'
            # will only have a target if this follows the note
            if targetLast is not None:
                sp.addSpannedElements(targetLast)
        else:
            raise FromMxObjectsException('unidentified mxType of mxBracket:', mxType)


#-------------------------------------------------------------------------------

def mxFermataToFermata(mxFermata, inputM21 = None):
    '''
    Convert an mxFermata object to a music21 expressions.Fermata
    object.
    
    If inputM21 is None, creates a new Fermata object
    and returns it.  Otherwise changes the current Fermata
    object and returns nothing.
    
    >>> mxFermata = musicxml.mxObjects.Fermata()
    >>> mxFermata.set('type', 'inverted')
    >>> fermata = musicxml.fromMxObjects.mxFermataToFermata(mxFermata)
    >>> fermata.type
    'inverted'
    '''
    if inputM21 is None:
        fermata = expressions.Fermata()
    else:
        fermata = inputM21

    fermata.type = mxFermata.get('type')
    
    if inputM21 is None:
        return fermata

def mxTechnicalToArticulation(mxTechnicalMark, inputM21 = None):
    '''
    Convert an mxTechnicalMark to a music21.articulations.TechnicalIndication object or one
    of its subclasses.

    Example: Provided an musicxml.mxObjects.TechnicalMark object (not an mxTechnical object)
    configure the music21 object.

    Create both a musicxml.mxObjects.ArticulationMark object and a conflicting music21 object:
            
    
    >>> mxTechnicalMark = musicxml.mxObjects.TechnicalMark('up-bow')
    >>> mxTechnicalMark.set('placement', 'below')
    >>> a = articulations.DownBow()
    >>> a.placement = 'above'

    Now override the music21 object with the mxArticulationMark object's characteristics

    >>> musicxml.fromMxObjects.mxTechnicalToArticulation(mxTechnicalMark, inputM21 = a)
    >>> 'DownBow' in a.classes
    False
    >>> 'UpBow' in a.classes
    True
    >>> a.placement
    'below'
    '''    
    mappingList = {'up-bow'          : articulations.UpBow,
                   'down-bow'        : articulations.DownBow,
                   'harmonic'        : articulations.Harmonic,
                   'open-string'     : articulations.OpenString,
                   'thumb-position'  : articulations.StringThumbPosition,
                   'fingering'       : articulations.StringFingering,
                   'pluck'           : articulations.FrettedPluck,
                   'double-tongue'   : articulations.DoubleTongue,
                   'triple-tongue'   : articulations.TripleTongue,
                   'stopped'         : articulations.Stopped,
                   'snap-pizzicato'  : articulations.SnapPizzicato,
                   'fret'            : articulations.FretIndication,
                   'string'          : articulations.StringIndication,
                   'hammer-on'       : articulations.HammerOn,
                   'pull-off'        : articulations.PullOff,
                   'bend'            : articulations.FretBend,
                   'tap'             : articulations.FretTap,
                   'heel'            : articulations.OrganHeel,
                   'toe'             : articulations.OrganToe,
                   'fingernails'     : articulations.HarpFingerNails,
                   'other-technical' : articulations.TechnicalIndication,
                   }
    mxName = mxTechnicalMark.tag
    if mxName not in mappingList:
        environLocal.printDebug("Cannot translate %s in %s." % (mxName, mxTechnicalMark))
    artClass = mappingList[mxName]
        
    if inputM21 is None:
        art = artClass()
    else:
        art = inputM21
        art.__class__ = artClass
        
    try:
        art.placement = mxTechnicalMark.get('placement')
    except xmlnode.XMLNodeException:
        pass
    
    if inputM21 is None:
        return art


def mxArticulationToArticulation(mxArticulationMark, inputM21 = None):
    '''
    Convert an mxArticulationMark to a music21.articulations.Articulation
    object or one of its subclasses.

    Example: Provided an musicxml.mxObjects.ArticulationMark object (not an mxArticulations object)
    configure the music21 object.

    Create both a musicxml.mxObjects.ArticulationMark object and a conflicting music21 object:
            
    
    >>> mxArticulationMark = musicxml.mxObjects.ArticulationMark('accent')
    >>> mxArticulationMark.set('placement', 'below')
    >>> a = articulations.Tenuto()
    >>> a.placement = 'above'

    Now override the music21 object with the mxArticulationMark object's characteristics

    >>> musicxml.fromMxObjects.mxArticulationToArticulation(mxArticulationMark, inputM21 = a)
    >>> 'Tenuto' in a.classes
    False
    >>> 'Accent' in a.classes
    True
    >>> a.placement
    'below'
    '''    
    mappingList = {'accent'          : articulations.Accent,
                   'strong-accent'   : articulations.StrongAccent,
                   'staccato'        : articulations.Staccato,
                   'staccatissimo'   : articulations.Staccatissimo,
                   'spiccato'        : articulations.Spiccato,
                   'tenuto'          : articulations.Tenuto,
                   'detached-legato' : articulations.DetachedLegato,
                   'scoop'           : articulations.Scoop,
                   'plop'            : articulations.Plop,
                   'doit'            : articulations.Doit,
                   'falloff'         : articulations.Falloff,
                   'breath-mark'     : articulations.BreathMark,
                   'caesura'         : articulations.Caesura,
                   'stress'          : articulations.Stress,
                   'unstress'        : articulations.Unstress,
                   'other-articulation': articulations.Articulation,
                   }
    mxName = mxArticulationMark.tag
    if mxName not in mappingList:
        environLocal.printDebug("Cannot translate %s in %s." % (mxName, mxArticulationMark))
    artClass = mappingList[mxName]
        
    if inputM21 is None:
        art = artClass()
    else:
        art = inputM21
        art.__class__ = artClass
        
        
    art.placement = mxArticulationMark.get('placement')
    
    if inputM21 is None:
        return art
    

def mxOrnamentToExpressionOrArticulation(mxOrnament):
    '''
    Convert mxOrnament into a music21 ornament. 
    
    This only processes non-spanner ornaments. 
    Many mxOrnaments are spanners: these are handled elsewhere.

    Returns None if cannot be converted or not defined.
    '''
    orn = None
    #environLocal.printDebug(['calling mxOrnamentToExpressionOrArticulation with', mxOrnament])
    if isinstance(mxOrnament, mxObjects.TrillMark):
        orn = expressions.Trill()
        orn.placement = mxOrnament.get('placement')
    elif isinstance(mxOrnament, mxObjects.Mordent):
        orn = expressions.Mordent()
    elif isinstance(mxOrnament, mxObjects.InvertedMordent):
        orn = expressions.InvertedMordent()

    elif isinstance(mxOrnament, mxObjects.Turn):
        orn = expressions.Turn()
    elif isinstance(mxOrnament, mxObjects.InvertedTurn):
        orn = expressions.InvertedTurn()

    elif isinstance(mxOrnament, mxObjects.Shake):
        orn = expressions.Shake()
    elif isinstance(mxOrnament, mxObjects.Schleifer):
        orn = expressions.Schleifer()

    return orn # may be None



#-------------------------------------------------------------------------------
# Chords

def mxToChord(mxNoteList, inputM21=None, spannerBundle=None):
    '''
    Given an a list of mxNotes, fill the necessary parameters
    
    >>> a = musicxml.mxObjects.Note()
    >>> p = musicxml.mxObjects.Pitch()
    >>> p.set('step', 'A')
    >>> p.set('octave', 3)
    >>> a.setDefaults()
    >>> a.set('pitch', p)
    >>> b = musicxml.mxObjects.Note()
    >>> b.setDefaults()
    >>> b.set('chord', True)
    >>> m = musicxml.mxObjects.Measure()
    >>> m.setDefaults()
    >>> a.external['measure'] = m # assign measure for divisions ref
    >>> a.external['divisions'] = m.external['divisions']
    >>> b.external['measure'] = m # assign measure for divisions ref
    >>> b.external['divisions'] = m.external['divisions']
    >>> c = musicxml.fromMxObjects.mxToChord([a, b])
    >>> len(c.pitches)
    2
    >>> c.pitches[0]
    <music21.pitch.Pitch A3>

    
    >>> a = musicxml.mxObjects.Note()
    >>> a.setDefaults()
    >>> nh1 = musicxml.mxObjects.Notehead()
    >>> nh1.set('charData', 'diamond')
    >>> a.noteheadObj = nh1
    >>> b = musicxml.mxObjects.Note()
    >>> b.setDefaults()
    >>> b.set('chord', True)
    >>> m = musicxml.mxObjects.Measure()
    >>> m.setDefaults()
    >>> a.external['measure'] = m # assign measure for divisions ref
    >>> a.external['divisions'] = m.external['divisions']
    >>> b.external['measure'] = m # assign measure for divisions ref
    >>> b.external['divisions'] = m.external['divisions']
    >>> c = musicxml.fromMxObjects.mxToChord([a, b])
    >>> c.getNotehead(c.pitches[0])
    'diamond'

    '''
    if inputM21 == None:
        c = chord.Chord()
    else:
        c = inputM21

    if spannerBundle is None:
        #environLocal.printDebug(['mxToNote()', 'creating SpannerBundle'])
        spannerBundle = spanner.SpannerBundle()
    else: # if we are passed in as spanner bundle, look for any pending
        # component assignments
        spannerBundle.freePendingSpannedElementAssignment(c)

    # assume that first chord is the same duration for all parts
    mxToDuration(mxNoteList[0], c.duration)

    # assume that first note in list has a grace object (and all do)
    mxGrace = mxNoteList[0].get('graceObj')

    pitches = []
    ties = [] # store equally spaced list; use None if not defined
    noteheads = [] # store notehead attributes that correspond with pitches
    stemDirs = [] # store stem direction attributes that correspond with pitches

    for mxNote in mxNoteList:
        # extract pitch pbjects     
        p = mxToPitch(mxNote)
        pitches.append(p)
        #extract notehead objects; may be None
        nh = mxNote.get('noteheadObj')
        noteheads.append(nh)
        #extract stem directions
        stemDir = mxNote.get('stem')
        stemDirs.append(stemDir)

        if len(mxNote.tieList) > 0:
            tieObj = mxToTie(mxNote)
            #environLocal.printDebug(['found tie in chord', tieObj])
            ties.append(tieObj)
        else: # need place holder for each pitch
            ties.append(None)
    # set all at once
    c.pitches = pitches
    # set beams from first note of chord
    beamsObj = mxToBeams(mxNoteList[0].beamList)
    c.beams = beamsObj

    # set ties based on pitches
    for i, t in enumerate(ties):
        if t is not None:
            # provide pitch to assign tie to based on index number
            c.setTie(t, pitches[i])
    #set notehead based on pitches
    for index, obj in enumerate(noteheads):
        if obj is not None:
            c.setNotehead(obj.charData, c.pitches[index])
            # set color per pitch
            c.setColor(obj.get('color'), c.pitches[index])
    #set stem direction based upon pitches
    for i, sd in enumerate(stemDirs):
        if sd != 'unspecified':
            c.setStemDirection(sd, c.pitches[i])

    if mxGrace is not None:
        c = c.getGrace()

    return c


#-------------------------------------------------------------------------------
# Notes

def mxToNote(mxNote, spannerBundle=None, inputM21=None):
    '''
    Translate a MusicXML :class:`~music21.musicxml.mxObjects.Note` 
    to a :class:`~music21.note.Note`.

    The `spannerBundle` parameter can be a list or a Stream 
    for storing and processing Spanner objects.
    
    If inputM21 is not `None` then that object is used
    for translating. Otherwise a new Note is created.
    
    Returns a `note.Note` object.
    
    
    >>> mxNote = musicxml.mxObjects.Note()
    >>> mxNote.setDefaults()
    >>> mxMeasure = musicxml.mxObjects.Measure()
    >>> mxMeasure.setDefaults()
    >>> mxMeasure.append(mxNote)
    >>> mxNote.external['measure'] = mxMeasure # manually create ref
    >>> mxNote.external['divisions'] = mxMeasure.external['divisions']
    >>> n = musicxml.fromMxObjects.mxToNote(mxNote)
    >>> n
    <music21.note.Note C>
    '''
    if inputM21 is None:
        n = note.Note()
    else:
        n = inputM21
        
    mxToPitch(mxNote, n.pitch) # required info will be taken from entire note

    beamsObj = mxToBeams(mxNote.beamList)
    n.beams = beamsObj 

    mxStem = mxNote.get('stem')
    if mxStem is not None:
        n.stemDirection = mxStem

    # gets the notehead object from the mxNote and sets value of the music21 note 
    # to the value of the notehead object        
    mxNotehead = mxNote.get('noteheadObj')
    if mxNotehead is not None:
        if mxNotehead.charData not in ('', None):
            n.notehead = mxNotehead.charData
        nhf = mxNotehead.get('filled')
        if nhf is not None:
            if nhf == 'yes':
                n.noteheadFill = True 
            elif nhf == 'no':
                n.noteheadFill = False 
        if mxNotehead.get('color') is not None:
            n.color = mxNotehead.get('color')


    # after this, use combined function for notes and rests...
    return mxNoteToGeneralNoteHelper(n, mxNote, spannerBundle)

def mxToRest(mxNote, inputM21=None, spannerBundle=None):
    '''Translate a MusicXML :class:`~music21.musicxml.mxObjects.Note` object to a :class:`~music21.note.Rest`.

    If an `inputM21` object reference is provided, this object will be configured; otherwise, a new :class:`~music21.note.Rest` object is created and returned.
    '''
    if inputM21 == None:
        r = note.Rest()
    else:
        r = inputM21

    return mxNoteToGeneralNoteHelper(r, mxNote, spannerBundle)


def mxNoteToGeneralNoteHelper(n, mxNote, spannerBundle=None):
    '''
    helper function for things common to notes and rests.
    
    n can be a note or rest...
    '''    
    # doing this will create an instance, but will not be passed
    # out of this method, and thus is only for testing
    if spannerBundle is None:
        #environLocal.printDebug(['mxToNote()', 'creating SpannerBundle'])
        spannerBundle = spanner.SpannerBundle()
    else: # if we are passed in as spanner bundle, look for any pending
        # component assignments
        spannerBundle.freePendingSpannedElementAssignment(n)

    # print object == 'no' and grace notes may have a type but not
    # a duration. they may be filtered out at the level of Stream 
    # processing
    if mxNote.get('printObject') == 'no':
        n.hideObjectOnPrint = True
        #environLocal.printDebug(['got mxNote with printObject == no'])

    mxGrace = mxNote.get('graceObj')

    if mxGrace is not None:
        #environLocal.printDebug(['mxGrace', mxGrace, mxNote, n.duration])
        # in some cases grace notes may not have an assigned duration type
        # this default type is set here, before assigning to n.duration
        if mxNote.type is None:
            #environLocal.printDebug(['mxToNote', 'mxNote that is a grace missing duration type'])
            mxNote.type = 'eighth'

    # the n.duration object here will be configured based on mxNote
    mxToDuration(mxNote, n.duration)

    # get color from Note first; if not, try to get from notehead
    if mxNote.get('color') is not None:
        n.color = mxNote.get('color')

    # get x-positioning if any...
    if mxNote.get('default-x') is not None:
        n.xPosition = mxNote.get('default-x')

    # can use mxNote.tieList instead
    mxTieList = mxNote.get('tieList')
    if len(mxTieList) > 0:
        
        tieObj = mxToTie(mxNote) # m21 tie object
                                    # provide entire Note
        # n.tie is defined in GeneralNote as None by default
        n.tie = tieObj

    # things found in notations object:
    # articulations, slurs
    mxNotations = mxNote.get('notationsObj')
    if mxNotations is not None:
        # get a list of mxArticulationMarks, not mxArticulations
        mxArticulationMarkList = mxNotations.getArticulations()
        for mxObj in mxArticulationMarkList:
            articulationObj = mxArticulationToArticulation(mxObj)
            n.articulations.append(articulationObj)

        # get any technical marks, a list of mxTechnicalMarks, not mxTechnical
        # they live with articulations
        mxTechnicalMarkList = mxNotations.getTechnical()
        for mxObj in mxTechnicalMarkList:
            technicalObj = mxTechnicalToArticulation(mxObj)
            n.articulations.append(technicalObj)

        
        # get any fermatas, store on expressions
        mxFermataList = mxNotations.getFermatas()
        for mxObj in mxFermataList:
            fermataObj = mxFermataToFermata(mxObj)
            n.expressions.append(fermataObj)

        mxOrnamentsList = mxNotations.getOrnaments()
#         if len(mxOrnamentsList) > 0:
#             environLocal.printDebug(['mxOrnamentsList:', mxOrnamentsList])
        for mxOrnamentsObj in mxOrnamentsList:
            for mxObj in mxOrnamentsObj:
                post = mxOrnamentToExpressionOrArticulation(mxObj)
                if post is not None:
                    n.expressions.append(post)
                    #environLocal.printDebug(['adding to epxressions', post])

        # create spanners:
        mxNotationsToSpanners(n, mxNotations, spannerBundle)

    # translate if necessary, otherwise leaves unchanged
    n = mxGraceToGrace(n, mxGrace)
    return n




#------------------------------------------------------------------------------
# Defaults

def mxDefaultsToScoreLayout(mxDefaults, inputM21=None):
    '''
    Convert a :class:`~music21.musicxml.mxObjects.Defaults` 
    object to a :class:`~music21.layout.ScoreLayout` 
    object
    '''
    if inputM21 is None:
        scoreLayout = layout.ScoreLayout()
    else:
        scoreLayout = inputM21

    mxScalingObj = mxDefaults.scalingObj    
    if mxScalingObj is not None:
        mms = mxScalingObj.millimeters
        scoreLayout.scalingMillimeters = mms
        tenths = mxScalingObj.tenths
        scoreLayout.scalingTenths = tenths
    
    for mxLayoutObj in mxDefaults.layoutList:
        if mxLayoutObj.tag == 'page-layout':
            scoreLayout.pageLayout = mxPageLayoutToPageLayout(mxLayoutObj)
        elif mxLayoutObj.tag == 'system-layout':
            scoreLayout.systemLayout = mxSystemLayoutToSystemLayout(mxLayoutObj)
        elif mxLayoutObj.tag == 'staff-layout': # according to xsd can be more than one.  meaning?
            scoreLayout.staffLayoutList.append(mxStaffLayoutToStaffLayout(mxLayoutObj))
    
    return scoreLayout



#-------------------------------------------------------------------------------
# Measures

def addToStaffReference(mxObjectOrNumber, music21Object, staffReference):
    '''
    Utility routine for importing musicXML objects; 
    here, we store a reference to the music21 object in a dictionary, 
    where keys are the staff values. Staff values may be None, 1, 2, etc.
    '''
    #environLocal.printDebug(['addToStaffReference(): called with:', music21Object])
    if common.isListLike(mxObjectOrNumber):
        if len(mxObjectOrNumber) > 0:
            mxObjectOrNumber = mxObjectOrNumber[0] # if a chord, get the first components
        else: # if an empty list
            environLocal.printDebug(['got an mxObject as an empty list', mxObjectOrNumber])
            return
    # add to staff reference
    if hasattr(mxObjectOrNumber, 'staff'):
        key = mxObjectOrNumber.staff
    # some objects store staff assignment simply as number
    else:
        try:
            key = mxObjectOrNumber.get('number')
        except xmlnode.XMLNodeException:
            return
        except AttributeError: # a normal number
            key = mxObjectOrNumber
    if key not in staffReference:
        staffReference[key] = []
    staffReference[key].append(music21Object)


def mxToMeasure(mxMeasure, spannerBundle=None, inputM21=None, lastMeasureInfo=None):
    '''
    Translate an mxMeasure (a MusicXML :class:`~music21.musicxml.mxObjects.Measure` object)
    into a music21 :class:`~music21.stream.Measure`.

    If an `inputM21` object reference is provided, this object will be
    configured and returned; otherwise, a new :class:`~music21.stream.Measure` object is created.

    The `spannerBundle` that is passed in is used to accumulate any created Spanners.
    This Spanners are not inserted into the Stream here.


    Returns a tuple of (music21.stream.Measure object, staffReference (a dictionary for partStaffs of
    elements that only belong to a single staff), and a transposition)
    '''
    if inputM21 == None:
        m = stream.Measure()
    else:
        m = inputM21

    # staff assignments: can create a dictionary with components in each
    # staff; this dictionary will then be used to copy this measure and 
    # split components between two parts of more than one staff is defined
    staffReference = {}

    # doing this will create an instance, but will not be passed
    # out of this method, and thus is only for testing
    if spannerBundle is None:
        #environLocal.printDebug(['mxToMeasure()', 'creating SpannerBundle'])
        spannerBundle = spanner.SpannerBundle()

    if lastMeasureInfo is not None:
        lastMNum, lastMSuffix = lastMeasureInfo
    else:
        lastMNum, lastMSuffix = (None, None)

    mNumRaw = mxMeasure.get('number')
    if mNumRaw is None:
        mNum = None
        mSuffix = None
    else:
        mNum, mSuffix = common.getNumFromStr(mNumRaw)

    # assume that measure numbers are integers
    if mNum not in [None, '']:
        m.number = int(mNum)
    if mSuffix not in [None, '']:
        m.numberSuffix = mSuffix

    # fix for Finale which calls unnumbered measures X1, X2, etc. which
    # we convert to 1.X, 2.X, etc. without this...
    if lastMNum is not None:
        if m.numberSuffix == 'X' and m.number != lastMNum + 1:
            newSuffix = m.numberSuffix + str(m.number)
            if lastMSuffix is not None:
                newSuffix = lastMSuffix + newSuffix
            m.number = lastMNum
            m.numberSuffix = newSuffix    
    
    data = mxMeasure.get('width')
    if data != None: # may need to do a format/unit conversion?
        m.layoutWidth = data

    # not yet implemented
    junk = mxMeasure.get('implicit')

    mxAttributes = mxMeasure.get('attributesObj')
    mxAttributesInternal = True
    # if we do not have defined mxAttributes, must get from stored attributes
    if mxAttributes is None:
        # need to keep track of where mxattributes src is coming from
        # if attributes are defined in this measure, mxAttributesInternal 
        # is true
        mxAttributesInternal = False
        # not all measures have attributes definitions; this
        # gets the last-encountered measure attributes
        mxAttributes = mxMeasure.external['attributes']
        if mxAttributes is None:
            raise FromMxObjectsException(
                'no mxAttribues available for this measure')

    #environLocal.printDebug(['mxAttriutes clefList', mxAttributes.clefList, 
    #                        mxAttributesInternal])

    staffLayoutObjects = []

    # getting first for each of these for now
    if mxAttributesInternal:
        if len(mxAttributes.timeList) != 0:
            for mxSub in mxAttributes.timeList:
                ts = mxToTimeSignature(mxSub)
                addToStaffReference(mxSub, ts, staffReference)
                m._insertCore(0, ts)
        if len(mxAttributes.clefList) != 0:
            for mxClef in mxAttributes.clefList:
                cl = mxClefToClef(mxClef)
                addToStaffReference(mxClef, cl, staffReference)
                m._insertCore(0, cl)
        if len(mxAttributes.keyList) != 0:
            for mxSub in mxAttributes.keyList:
                ks = mxKeyListToKeySignature(mxSub)
                addToStaffReference(mxSub, ks, staffReference)
                m._insertCore(0, ks)
        if len(mxAttributes.staffDetailsList) != 0:
            for mxStaffDetails in mxAttributes.staffDetailsList:
                foundMatch = False
                # perhaps we've already put a staffLayout into the measure?
                if mxStaffDetails._attr['number'] is not None:
                    for stl in staffLayoutObjects:
                        if stl.staffNumber == int(mxStaffDetails._attr['number']):
                            try:
                                stl.staffSize = float(mxStaffDetails.staffSize)
                            except TypeError:
                                if mxStaffDetails.staffSize is None:
                                    pass
                                else:
                                    raise TypeError("Incorrect number for mxStaffDetails.staffSize: %s", mxStaffDetails.staffSize)
                            foundMatch = True
                            break
                else:
                    for stl in staffLayoutObjects:
                        if stl.staffSize is None:
                            stl.staffSize = float(mxStaffDetails.staffSize)
                            foundMatch = True
                        if stl.staffLines is None:
                            stl.staffLines = int(mxStaffDetails.staffLines)
                            foundMatch = True
                            
                        
                if foundMatch is False:
                    staffSize = None
                    try:
                        staffSize = float(mxStaffDetails.staffSize)
                    except TypeError:
                        staffSize = None     
                    
                    staffLines = None
                    try:
                        staffLines = int(mxStaffDetails.staffLines)
                    except TypeError:
                        staffLines = 5     
                                       
                    if mxStaffDetails._attr['number'] is not None:
                        stl = layout.StaffLayout(staffSize = staffSize, staffLines = staffLines, staffNumber=int(mxStaffDetails._attr['number']))
                    else:
                        stl = layout.StaffLayout(staffSize = staffSize, staffLines = staffLines)
                    
                    if 'print-object' in mxStaffDetails._attr:
                        staffPrinted = mxStaffDetails._attr['print-object']
                        if staffPrinted == 'no' or staffPrinted is False:
                            stl.hidden = True
                        elif staffPrinted == 'yes' or staffPrinted is True:
                            stl.hidden = False
                    #else:
                    #    print mxStaffDetails._attr
                    
                    addToStaffReference(mxStaffDetails, stl, staffReference)
                    m._insertCore(0, stl)
                    staffLayoutObjects.append(stl)
                    #staffLayoutsAlreadySetList.append(stl)
                    #print "Got an mxStaffDetails %r" % mxStaffDetails
                

    # transposition may be defined for a Part in the Measure attributes
    transposition = None
    if mxAttributesInternal and mxAttributes.transposeObj is not None:
        # get interval object
        transposition = mxTransposeToInterval(mxAttributes.transposeObj)
        #environLocal.printDebug(['mxToMeasure: got transposition', transposition])

    if mxAttributes.divisions is not None:
        divisions = mxAttributes.divisions
    else:
        divisions = mxMeasure.external['divisions']
    if divisions is None:
        environLocal.printDebug(['cannot get a division from mxObject', m, "mxMeasure.external['divisions']", mxMeasure.external['divisions']])
        raise FromMxObjectsException('cannot get a division from mxObject')

    if mxMeasure.getVoiceCount() > 1:
        useVoices = True
        # count from zero
        for voiceId in mxMeasure.getVoiceIndices():
            v = stream.Voice()
            v.id = voiceId
            m._insertCore(0.0, v)
    else:
        useVoices = False

    # iterate through components found on components list
    # set to zero for each measure
    offsetMeasureNote = 0 # offset of note w/n measure        
    mxNoteList = [] # for accumulating notes in chords
    mxLyricList = [] # for accumulating lyrics assigned to chords
    nLast = None # store the last-create music21 note for Spanners
    restAndNoteCount = {'rest': 0, 'note': 0}
    chordVoice = None # Sibelius 7.1 only puts a <voice> tag on the
                        # first note of a chord, so we need to make sure
                        # that we keep track of the last voice...

    for i in range(len(mxMeasure)):
        # try to get the next object for chord comparisons
        mxObj = mxMeasure[i]
        if i < len(mxMeasure) - 1:
            mxObjNext = mxMeasure[i + 1]
        else:
            mxObjNext = None
        
        #environLocal.printDebug(['handling', mxObj])

        # NOTE: tests have shown that using isinstance() here is much faster
        # than checking the .tag attribute.
        # check for backup and forward first
        if isinstance(mxObj, mxObjects.Backup):
            # resolve as quarterLength, subtract from measure offset
            #environLocal.printDebug(['found musicxl backup:', mxObj.duration])
            offsetMeasureNote -= float(mxObj.duration) / float(divisions)
            continue
        elif isinstance(mxObj, mxObjects.Forward):
            # resolve as quarterLength, add to measure offset
            #environLocal.printDebug(['found musicxl forward:', mxObj.duration, 'divisions', divisions])
            offsetMeasureNote += float(mxObj.duration) / float(divisions)
            continue
        elif isinstance(mxObj, mxObjects.Print):
            # mxPrint objects may be found in a Measure's components
            # contain page or system layout information among others
            mxPrint = mxObj
            addPageLayout = False
            addSystemLayout = False
            addStaffLayout = False
            try:
                addPageLayout = mxPrint.get('new-page')
                if addPageLayout is not None:
                    addPageLayout = True # false for No??
                else:
                    addPageLayout = False
            except xmlnode.XMLNodeException:
                pass
            if not addPageLayout:
                try:
                    addPageLayout = mxPrint.get('page-number')
                    if addPageLayout is not None:
                        addPageLayout = True
                    else:
                        addPageLayout = False
                except xmlnode.XMLNodeException:
                    addPageLayout = False
            if not addPageLayout:
                for layoutType in mxPrint.componentList:
                    if isinstance(layoutType, mxObjects.PageLayout):
                        addPageLayout = True
                        break
            try:
                addSystemLayout = mxPrint.get('new-system')
                if addSystemLayout is not None:
                    addSystemLayout = True # false for No?
                else:
                    addSystemLayout = False
            except xmlnode.XMLNodeException:
                pass
            if not addSystemLayout:
                for layoutType in mxPrint.componentList:
                    if isinstance(layoutType, mxObjects.SystemLayout):
                        addSystemLayout = True
                        break

            for layoutType in mxPrint.componentList:
                if isinstance(layoutType, mxObjects.StaffLayout):
                    addStaffLayout = True
                    break
            
            #--- now we know what we need to add, add em
            if addPageLayout:
                pl = mxPrintToPageLayout(mxPrint)
                # store at zero position
                m._insertCore(0, pl)
            if addSystemLayout or not addPageLayout:
                sl = mxPrintToSystemLayout(mxPrint)
                # store at zero position
                m._insertCore(0, sl)
            if addStaffLayout:
                stlList = mxPrintToStaffLayoutList(mxPrint)
                for stl in stlList:
                    foundPrevious = False
                    for stlSetFromAttributes in staffLayoutObjects:
                        if stlSetFromAttributes.staffNumber == stl.staffNumber or stlSetFromAttributes.staffNumber is None or stl.staffNumber is None:
                            foundPrevious = True
                            stlSetFromAttributes.distance = stl.distance
                            if stlSetFromAttributes.hidden is None:
                                stlSetFromAttributes.hidden = stl.hidden
                            break
                    if foundPrevious is False:
                        addToStaffReference(str(stl.staffNumber), stl, staffReference)
                        m._insertCore(0, stl)


        # <sound> tags may be found in the Measure, used to define tempo
        elif isinstance(mxObj, mxObjects.Sound):
            pass

        elif isinstance(mxObj, mxObjects.Barline):
            # repeat is a tag found in the barline object
            mxBarline = mxObj
            mxRepeatObj = mxBarline.get('repeatObj')
            if mxRepeatObj is not None:
                barline = mxToRepeat(mxBarline)
            else:
                barline = mxToBarline(mxBarline)

            # barline objects also store ending objects, that mark begin
            # and end of repeat bracket designations
            mxEndingObj = mxBarline.get('endingObj')
            if mxEndingObj is not None:
                #environLocal.printDebug(['found mxEndingObj', mxEndingObj, 'm', m]) 
                # get all incomplete spanners of the appropriate class that are
                # not complete
                rbSpanners = spannerBundle.getByClass('RepeatBracket').getByCompleteStatus(False)
                # if we have no complete bracket objects, must start a new one
                if len(rbSpanners) == 0:
                    # create with this measure as the object
                    rb = spanner.RepeatBracket(m)
                    # there may just be an ending marker, and no start
                    # this implies just one measure
                    if mxEndingObj.get('type') in ['stop', 'discontinue']:
                        rb.completeStatus = True
                        rb.number = mxEndingObj.get('number')
                    # set number; '' or None is interpreted as 1
                    spannerBundle.append(rb)
                # if we have any incomplete, this must be the end
                else:
                    #environLocal.printDebug(['matching RepeatBracket spanner', 'len(rbSpanners)', len(rbSpanners)])
                    rb = rbSpanners[0] # get RepeatBracket
                    # try to add this measure; may be the same
                    rb.addSpannedElements(m)
                    # in general, any rb found should be the opening, and thus
                    # this is the closing; can check
                    if mxEndingObj.get('type') in ['stop', 'discontinue']:
                        rb.completeStatus = True
                        rb.number = mxEndingObj.get('number')
                    else:
                        environLocal.warn('found mxEnding object that is not stop message, even though there is still an open start message. -- ignoring it')

            if barline.location == 'left':
                #environLocal.printDebug(['setting left barline', barline])
                m.leftBarline = barline
            elif barline.location == 'right':
                #environLocal.printDebug(['setting right barline', barline])
                m.rightBarline = barline
            else:
                environLocal.printDebug(['not handling barline that is neither left nor right', barline, barline.location])

        elif isinstance(mxObj, mxObjects.Note):
            mxNote = mxObj
            if isinstance(mxObjNext, mxObjects.Note):
                mxNoteNext = mxObjNext
            else:
                mxNoteNext = None
            if mxNote.get('print-object') == 'no':
                #environLocal.printDebug(['got mxNote with printObject == no', 'measure number', m.number])
                continue

#             mxGrace = mxNote.get('graceObj')
#             if mxGrace is not None: # graces have a type but not a duration
#                 #environLocal.printDebug(['got mxNote with an mxGrace', 'duration', mxNote.get('duration'), 'measure number', 
#                 #m.number])
#                 continue

            # the first note of a chord is not identified directly; only
            # by looking at the next note can we tell if we have the first
            # note of a chord
            if mxNoteNext is not None and mxNoteNext.get('chord') is True:
                if mxNote.get('chord') is False:
                    mxNote.set('chord', True) # set the first as a chord
                if mxNote.voice is not None:
                    chordVoice = mxNote.voice

            if mxNote.get('rest') in [None, False]: # it is a note
                # if a chord, do not increment until chord is complete
                if mxNote.get('chord') is True:
                    mxNoteList.append(mxNote)
                    offsetIncrement = 0
                    # store lyrics for latter processing
                    for mxLyric in mxNote.lyricList:
                        mxLyricList.append(mxLyric)
                else:
                    restAndNoteCount['note'] += 1
                    try:
                        n = mxToNote(mxNote, spannerBundle=spannerBundle)
                    except FromMxObjectsException as strerror:
                        raise FromMxObjectsException('cannot translate note in measure %s: %s' % (mNumRaw, strerror))

                    addToStaffReference(mxNote, n, staffReference)
                    if useVoices:
                        useVoice = mxNote.voice
                        if useVoice is None:
                            useVoice = chordVoice
                            if useVoice is None:
                                environLocal.warn("Cannot translate a note with a missing voice tag when no previous voice tag was given.  Assuming voice 1... Object is %r " % mxNote)
                                useVoice = 1
                        thisVoice = m.voices[useVoice]
                        if thisVoice is None:
                            environLocal.warn('Cannot find voice %d for Note %r; putting outside of voices...' % (mxNote.voice, mxNote))
                            m._insertCore(offsetMeasureNote, n)
                        else:
                            thisVoice._insertCore(offsetMeasureNote, n)
                    else:
                        m._insertCore(offsetMeasureNote, n)
                    offsetIncrement = n.quarterLength

                    currentLyricNumber = 1
                    for mxLyric in mxNote.lyricList:
                        lyricObj = mxToLyric(mxLyric)
                        if lyricObj.number == 0:
                            lyricObj.number = currentLyricNumber
                        n.lyrics.append(lyricObj)
                        currentLyricNumber += 1
                    nLast = n # update

#                if mxNote.get('notationsObj') is not None:
#                    for mxObjSub in mxNote.get('notationsObj'):
#                        # deal with ornaments, trill, etc
#                        pass
            else: # its a rest
                restAndNoteCount['rest'] += 1
                n = note.Rest()
                mxToRest(mxNote, inputM21=n)
                addToStaffReference(mxNote, n, staffReference)
                #m.insert(offsetMeasureNote, n)
                if useVoices:
                    vCurrent = m.voices[mxNote.voice]
                    if vCurrent is not None:
                        vCurrent._insertCore(offsetMeasureNote, n)
                    else:
                        # this can happen when a part defines multiple staves
                        # where one staff uses voices but the other staff does not
                        m._insertCore(offsetMeasureNote, n)
                        #print m, n, mxNote
                else:
                    m._insertCore(offsetMeasureNote, n)
                offsetIncrement = n.quarterLength
                nLast = n # update

            # if we we have notes in the note list and the next
            # note either does not exist or is not a chord, we 
            # have a complete chord
            if len(mxNoteList) > 0 and (mxNoteNext is None
                or mxNoteNext.get('chord') is False):
                c = mxToChord(mxNoteList, spannerBundle=spannerBundle)
                # add any accumulated lyrics
                currentLyricNumber = 1
                for mxLyric in mxLyricList:
                    lyricObj = mxToLyric(mxLyric)
                    if lyricObj.number == 0:
                        lyricObj.number = currentLyricNumber
                    c.lyrics.append(lyricObj)
                    currentLyricNumber += 1

                addToStaffReference(mxNoteList, c, staffReference)
                if useVoices:
                    useVoice = mxNote.voice
                    if useVoice is None:
                        useVoice = chordVoice
                        if useVoice is None:
                            environLocal.warn("Cannot translate a note with a missing voice tag when no previous voice tag was given.  Assuming voice 1... Object is %r " % mxNote)
                            useVoice = 1
                    thisVoice = m.voices[useVoice]
                    if thisVoice is None:
                        environLocal.warn('Cannot find voice %d for Note %r; putting outside of voices...' % (mxNote.voice, mxNote))
                        m._insertCore(offsetMeasureNote, c)
                    else:          
                        thisVoice._insertCore(offsetMeasureNote, c)
                else:
                    m._insertCore(offsetMeasureNote, c)
                mxNoteList = [] # clear for next chord
                mxLyricList = []

                offsetIncrement = c.quarterLength
                nLast = c # update

            # only increment Chords after completion
            offsetMeasureNote += offsetIncrement

        # mxDirections can be dynamics, repeat expressions, text expressions
        elif isinstance(mxObj, mxObjects.Direction):
            offsetDirection = mxToOffset(mxObj, divisions)
            if mxObj.getDynamicMark() is not None:
                # in rare cases there may be more than one dynamic in the same
                # direction, so we iterate
                for d in mxToDynamicList(mxObj):
                    addToStaffReference(mxObj, d, staffReference)
                    #m.insert(offsetMeasureNote, d)
                    m._insertCore(offsetMeasureNote + offsetDirection, d)

            mxDirectionToSpanners(nLast, mxObj, spannerBundle)
            # TODO: multiple spanners
#             if mxObj.getWedge() is not None:
#                 w = mxToWedge(mxObj)
#                 addToStaffReference(mxObj, w, staffReference)
#                 m._insertCore(offsetMeasureNote, w)

            if mxObj.getSegno() is not None:
                rm = mxToSegno(mxObj.getSegno())
                addToStaffReference(mxObj, rm, staffReference)
                m._insertCore(offsetMeasureNote, rm)
            if mxObj.getCoda() is not None:
                rm = mxToCoda(mxObj.getCoda())
                addToStaffReference(mxObj, rm, staffReference)
                m._insertCore(offsetMeasureNote, rm)

            if mxObj.getMetronome() is not None:
                #environLocal.printDebug(['got getMetronome', mxObj.getMetronome()])
                mm = mxToTempoIndication(mxObj.getMetronome())
                addToStaffReference(mxObj, mm, staffReference)
                # need to look for metronome marks defined above
                # and look for text defined below
                m._insertCore(offsetMeasureNote, mm)

            if mxObj.getWords() is not None:
                # TODO: need to look for tempo words if we have a metro
                #environLocal.printDebug(['found mxWords object', mxObj])
                # convert into a list of TextExpression objects
                # this may be a TextExpression, or a RepeatExpression
                for te in mxToTextExpression(mxObj):
                    #environLocal.printDebug(['got TextExpression object', repr(te)])
                    # offset here is a combination of the current position
                    # (offsetMeasureNote) and and the direction's offset

                    re = te.getRepeatExpression()
                    if re is not None:
                        # the repeat expression stores a copy of the text
                        # expression within it; replace it here on insertion
                        addToStaffReference(mxObj, re, staffReference)
                        m._insertCore(offsetMeasureNote + offsetDirection, re)
                    else:
                        addToStaffReference(mxObj, te, staffReference)
                        m._insertCore(offsetMeasureNote + offsetDirection, te)

        elif isinstance(mxObj, mxObjects.Harmony):
            mxHarmony = mxObj
            h = mxToChordSymbol(mxHarmony)
            addToStaffReference(mxObj, h, staffReference)
            m._insertCore(offsetMeasureNote, h)

        elif isinstance(mxObj, mxObjects.Clef):
            cl = mxClefToClef(mxObj)
            addToStaffReference(mxObj, cl, staffReference)
            m._insertCore(offsetMeasureNote, cl)


    #environLocal.printDebug(['staffReference', staffReference])
    # if we have voices and/or if we used backup/forward, we may have
    # empty space in the stream
    if useVoices:
        for v in m.voices:
            if len(v) > 0: # do not bother with empty voices
                v.makeRests(inPlace=True)
            v.elementsChanged()
    m.elementsChanged()

    if restAndNoteCount['rest'] == 1 and restAndNoteCount['note'] == 0:
        # full measure rest with no notes...
        if useVoices:
            pass # should do this on a per voice basis...
            m._fullMeasureRest = False
        else:
            m._fullMeasureRest = True
    else:
        m._fullMeasureRest = False

    return m, staffReference, transposition


#-------------------------------------------------------------------------------
# Streams


def mxToStreamPart(mxScore, partId, spannerBundle=None, inputM21=None):
    '''
    Load a part into a new Stream or one provided by 
    `inputM21` given an mxScore and a part name.

    The `spannerBundle` reference, when passed in, 
    is used to accumulate Spanners. These are not inserted here.

    Though it is incorrect MusicXML, PDFtoMusic creates 
    empty measures when it should create full
    measures of rests (possibly hidden).  This routine 
    fixes that bug.  See http://musescore.org/en/node/15129
    '''
    #environLocal.printDebug(['calling Stream.mxToStreamPart'])
    if inputM21 == None:
        # need a Score to load parts into
        s = stream.Score()
    else:
        s = inputM21

    if spannerBundle == None:
        spannerBundle = spanner.SpannerBundle()

    mxPart = mxScore.getPart(partId)
    # in some cases there may be more than one instrument defined
    # in each score part; this has not been tested
    mxInstrument = mxScore.getScorePart(partId)

    # create a new music21 instrument
    instrumentObj = instrument.Instrument()
    if mxInstrument is not None: # mxInstrument is a ScorePart
        # need an mxScorePart here   
        mxToInstrument(mxInstrument, instrumentObj)
    # add part id as group
    instrumentObj.groups.append(partId)

    streamPart = stream.Part() # create a part instance for each part
    # always assume at sounding, unless transposition is defined in attributes
    streamPart.atSoundingPitch = True

    # set part id to stream best name
    if instrumentObj.bestName() is not None:
        streamPart.id = instrumentObj.bestName()
    streamPart._insertCore(0, instrumentObj) # add instrument at zero offset

    staffReferenceList = []
    # offset is in quarter note length
    oMeasure = 0.0
    lastTimeSignature = None
    lastTransposition = None # may change at measure boundaries
    lastMeasureWasShort = False  # keep track of whether the last measure was short...

    lastMeasureNumber = 0
    lastMeasureSuffix = None

    for i, mxMeasure in enumerate(mxPart):
        # t here is transposition, if defined; otherwise it is None
        try:
            m, staffReference, t = mxToMeasure(mxMeasure,
                                   spannerBundle=spannerBundle,
                                   lastMeasureInfo=(lastMeasureNumber, lastMeasureSuffix))
        except Exception as e:
            import sys
            measureNumber = "unknown"
            try:
                measureNumber = mxMeasure.get('number')
            except:
                pass
            # see http://stackoverflow.com/questions/6062576/adding-information-to-a-python-exception
            execInfoTuple = sys.exc_info()
            if hasattr(e, 'message'):
                emessage = e.message
            else:
                emessage = execInfoTuple[0].__name__ + " : " #+ execInfoTuple[1].__name__
            message = "In measure (" + measureNumber + "): " + emessage
            raise type(e)(type(e)(message), pprint.pformat(traceback.extract_tb(execInfoTuple[2])))
        if t is not None:
            if lastTransposition is None and i == 0: # if this is the first
                #environLocal.printDebug(['transposition', t])
                instrumentObj.transposition = t
            else: # if not the first measure, need to copy as well
                # for now, copy Instrument, change transposition, 
                # could insert in part, or in measure
                newInst = copy.deepcopy(instrumentObj)
                newInst.transposition = t
                streamPart._insertCore(oMeasure, newInst)
            # if a transposition is defined in musicxml, we assume it is
            # at written pitch
            streamPart.atSoundingPitch = False
            # store last for comparison
            lastTransposition = t

        # there will be one for each measure
        staffReferenceList.append(staffReference)

        if m.number != lastMeasureNumber:
            # we do this check so that we do not compound suffixes, i.e.:
            # 23, 23.X1, 23.X1X2, 23.X1X2X3
            # and instead just do:
            # 23, 23.X1, 23.X2, etc.
            lastMeasureNumber = m.number
            lastMeasureSuffix = m.numberSuffix

        if m.timeSignature is not None:
            lastTimeSignature = m.timeSignature
        elif lastTimeSignature is None and m.timeSignature is None:
            # if no time sigature is defined, need to get a default
            ts = meter.TimeSignature()
            ts.load('%s/%s' % (defaults.meterNumerator,
                               defaults.meterDenominatorBeatType))
            lastTimeSignature = ts
        
        if m._fullMeasureRest is True:
            r1 = m.getElementsByClass('Rest')[0]
            if r1.duration.quarterLength == 4.0 and r1.duration.quarterLength != lastTimeSignature.barDuration.quarterLength:
                r1.duration.quarterLength = lastTimeSignature.barDuration.quarterLength
                m.elementsChanged()
        
        del(m._fullMeasureRest)
        
        # add measure to stream at current offset for this measure
        streamPart._insertCore(oMeasure, m)

        # note: we cannot assume that the time signature properly
        # describes the offsets w/n this bar. need to look at 
        # offsets within measure; if the .highestTime value is greater
        # use this as the next offset

        mHighestTime = m.highestTime
        lastTimeSignatureQuarterLength = lastTimeSignature.barDuration.quarterLength

        if mHighestTime >= lastTimeSignatureQuarterLength :
            mOffsetShift = mHighestTime

        elif mHighestTime == 0.0 and len(m.flat.notesAndRests) == 0:
            ## this routine fixes a bug in PDFtoMusic and other MusicXML writers
            ## that omit empty rests in a Measure.  It is a very quick test if
            ## the measure has any notes.  Slower if it does not.
            r = note.Rest()
            r.duration.quarterLength = lastTimeSignatureQuarterLength
            m.insert(0.0, r)
            mOffsetShift = lastTimeSignatureQuarterLength

        else: # use time signature
            # for the first measure, this may be a pickup
            # must detect this when writing, as next measures offsets will be 
            # incorrect
            if oMeasure == 0.0:
                # cannot get bar duration proportion if cannot get a ts
                if m.barDurationProportion() < 1.0:
                    m.padAsAnacrusis()
                    #environLocal.printDebug(['incompletely filled Measure found on musicxml import; interpreting as a anacrusis:', 'padingLeft:', m.paddingLeft])
                mOffsetShift = mHighestTime
            # assume that, even if measure is incomplete, the next bar should
            # start at the duration given by the time signature, not highestTime

            ### no...let's not do this...
            else:
                mOffsetShift = mHighestTime #lastTimeSignatureQuarterLength
                if lastMeasureWasShort is True:
                    if m.barDurationProportion() < 1.0:
                        m.padAsAnacrusis() # probably a pickup after a repeat or phrase boundary or something
                        lastMeasureWasShort = False
                else:
                    if mHighestTime < lastTimeSignatureQuarterLength:
                        lastMeasureWasShort = True
                    else:
                        lastMeasureWasShort = False
                        
        oMeasure += mOffsetShift

    # if we have multiple staves defined, add more parts, and transfer elements
    # note: this presently has to look at _idLastDeepCopyOf to get matches
    # to find removed elements after copying; this is probably not the
    # best way to do this.   # V2.1 -- is not/will not be doing this. in fact idLastDeepCopyOf is
    # going away...

    # for this part, if any elements are components in the spannerBundle,
    # then then we need to update the spannerBundle after the part is copied

    streamPartStaff = None
    if mxPart.getStavesCount() > 1:
        separateOutPartStaffs(mxPart, streamPart, spannerBundle, s, staffReferenceList, partId)
    else:
        streamPart.addGroupForElements(partId) # set group for components 
        streamPart.groups.append(partId) # set group for stream itself

        # TODO: this does not work with voices; there, Spanners 
        # will be copied into the Score 

        # copy spanners that are complete into the part, as this is the 
        # highest level container that needs them
        rm = []
        for sp in spannerBundle.getByCompleteStatus(True):
            streamPart._insertCore(0, sp)
            rm.append(sp)
        # remove from original spanner bundle
        for sp in rm:
            spannerBundle.remove(sp)
        # s is the score; adding the aprt to the score
        streamPart.elementsChanged()
        s._insertCore(0, streamPart)

    s.elementsChanged()
    # when adding parts to this Score
    # this assumes all start at the same place
    # even if there is only one part, it will be placed in a Stream
    if streamPartStaff is not None:
        return streamPartStaff
    else:
        return streamPart

def separateOutPartStaffs(mxPart, streamPart, spannerBundle, s, staffReferenceList, partId):
    '''
    given an mxPart and other necessary information, insert into the score (s) multiple
    PartStaff objects separating the information for one part from the other
    '''
    # transfer all spanners to the streamPart such that they get
    # updated in copying, then remove them
    rm = []
    for sp in spannerBundle.getByCompleteStatus(True):
        streamPart._insertCore(0, sp)
        rm.append(sp)
    # remove from original spanner bundle
    for sp in rm:
        spannerBundle.remove(sp)

    # get staves will return a number, between 1 and count
    #for staffCount in range(mxPart.getStavesCount()):
    for staffNumber in _getUniqueStaffKeys(staffReferenceList):
        partStaffId = '%s-Staff%s' % (partId, staffNumber)
        #environLocal.printDebug(['partIdStaff', partIdStaff, 'copying streamPart'])
        # this deepcopy is necessary, as we will remove components
        # in each staff that do not belong
        
        # TODO: Do n-1 deepcopies, instead of n, since the last PartStaff can just remove from the original Part
        streamPartStaff = copy.deepcopy(streamPart)
        # assign this as a PartStaff, a subclass of Part
        streamPartStaff.__class__ = stream.PartStaff
        streamPartStaff.id = partStaffId
        # remove all elements that are not part of this staff
        mStream = streamPartStaff.getElementsByClass('Measure')
        for i, staffReference in enumerate(staffReferenceList):
            staffExclude = _getStaffExclude(staffReference, staffNumber)
            if len(staffExclude) > 0:
                m = mStream[i]
                for eRemove in staffExclude:
                    for eMeasure in m:
                        if eMeasure.derivation.origin is eRemove and eMeasure.derivation.method == '__deepcopy__':
                            m.remove(eMeasure)
                            break
                    for v in m.voices:
                        v.remove(eRemove)
                        for eVoice in v.elements:
                            if eVoice.derivation.origin is eRemove and eVoice.derivation.method == '__deepcopy__':
                                v.remove(eVoice)
            # after adjusting voices see if voices can be reduced or
            # removed
            #environLocal.printDebug(['calling flattenUnnecessaryVoices: voices before:', len(m.voices)])
            m.flattenUnnecessaryVoices(force=False, inPlace=True)
            #environLocal.printDebug(['calling flattenUnnecessaryVoices: voices after:', len(m.voices)])
        # TODO: copying spanners may have created orphaned
        # spanners that no longer have valid connections
        # in this part; should be deleted
        streamPartStaff.addGroupForElements(partStaffId)
        streamPartStaff.groups.append(partStaffId)
        streamPartStaff.elementsChanged()
        s._insertCore(0, streamPartStaff)

def _getUniqueStaffKeys(staffReferenceList):
    '''
    Given a list of staffReference dictionaries, 
    collect and return a list of all unique keys except None
    '''
    post = []
    for staffReference in staffReferenceList:
        for key in staffReference:
            if key is not None and key not in post:
                post.append(key)
    post.sort()
#    if len(post) > 0:
#        print post
    return post

def _getStaffExclude(staffReference, targetKey):
    '''
    Given a staff reference dictionary, remove and combine in a list all elements that 
    are not part of the given key. Thus, return a list of all entries to remove.
    It keeps those elements under staff key None (common to all) and 
    those under given key. This then is the list of all elements that should be deleted.
    '''
    post = []
    for key in staffReference:
        if key is None or int(key) == int(targetKey):
            continue
        post += staffReference[key]
    return post


def mxScoreToScore(mxScore, spannerBundle=None, inputM21=None):
    '''
    Translate an mxScore into a music21 Score object 
    or puts it into the
    given inputM21 object (which does not necessarily 
    have to be a :class:`~music21.stream.Score`
    object.  It can be any :class:`~music21.stream.Stream` 
    object)

    All spannerBundles accumulated at all lower levels 
    are inserted here.
    '''
    # TODO: may not want to wait to this leve to insert spanners; may want to 
    # insert in lower positions if it makes sense
    if inputM21 == None:
        s = stream.Score()
    else:
        s = inputM21
        
    if spannerBundle == None:
        spannerBundle = spanner.SpannerBundle()

    mxPartIds = mxScore.getPartIdsFromPartListObj()
    #print mxPartIds
    #mxPartIdDictionary = mxScore.partIdToNameDict()
    m21PartIdDictionary = {}
    # values are part names
    #partNameIds = mxPartIdDictionary.keys()
    #partNameIds.sort()
    #for partId in partNameIds: # part names are part ids
    for pNum, partId in enumerate(mxPartIds): # part names are part ids
        # NOTE: setting partId not partId: might change
        # return the part; however, it is still already attached to the Score
        try:
            part = mxToStreamPart(mxScore, partId=partId,
                                  spannerBundle=spannerBundle, inputM21=s)
        except Exception as e:
            import sys
            # see http://stackoverflow.com/questions/6062576/adding-information-to-a-python-exception
            execInfoTuple = sys.exc_info()
            if hasattr(e, 'message'):
                emessage = e.message
            else:
                emessage = str(execInfoTuple[1])
            
            message = "For part number " + str(pNum + 1) + ", with Id (" + partId + "): " + emessage
            raise type(e)(type(e)(message), pprint.pformat(traceback.extract_tb(execInfoTuple[2])))


        # update dictionary to store music21 part
        m21PartIdDictionary[partId] = part
        #print("%r %s %r" % (m21PartIdDictionary, partId, part))

    # get part/staff groups
    #environLocal.printDebug(['partgroups:', mxScore.getPartGroupData()])
    partGroupData = mxScore.getPartGroupData()
    for partGroup in partGroupData: # a list of dictionaries
        # create music21 spanner np
        sg = layout.StaffGroup()
        for partId in partGroup['scorePartIds']:
            # get music21 part from partIdDictionary
            try:
                sg.addSpannedElements(m21PartIdDictionary[partId])
            except KeyError as ke:
                raise FromMxObjectsException("Cannot find part in m21PartIdDictionary: %s \n   Full Dict:\n   %r " % (ke, m21PartIdDictionary))
        # use configuration routine to transfer/set attributes;
        # sets complete status as well
        configureStaffGroupFromMxPartGroup(sg, partGroup['partGroup'])
        spannerBundle.append(sg) # will be added to the Score

    # add metadata object; this is placed after all other parts now
    # these means that both Parts and other objects live on Stream.
    md = mxScoreToMetadata(mxScore)
    s._insertCore(0, md)

    if mxScore.defaultsObj is not None:
        scoreLayout = mxDefaultsToScoreLayout(mxScore.defaultsObj)
        s._insertCore(0, scoreLayout)

    # store credits on Score stream
    for mxCredit in mxScore.creditList:
        co = mxCreditToTextBox(mxCredit)
        s._insertCore(0, co) # insert position does not matter

    ## get supports information
    mxIdentification = mxScore.identificationObj
    if mxIdentification is not None:
        mxEncoding = mxIdentification.encodingObj
        if mxEncoding is not None:
            for mxSupports in mxEncoding.supportsList:
                if (mxSupports.get('attribute') == 'new-system' and
                    mxSupports.get('value') == 'yes'):
                    s.definesExplicitSystemBreaks = True
                    for p in s.parts:
                        p.definesExplicitSystemBreaks = True
                elif (mxSupports.get('attribute') == 'new-page' and
                    mxSupports.get('value') == 'yes'):
                    s.definesExplicitPageBreaks = True
                    for p in s.parts:
                        p.definesExplicitPageBreaks = True
                    
    # only insert complete spanners; at each level possible, complete spanners
    # are inserted into either the Score or the Part
    # storing complete Part spanners in a Part permits extracting parts with spanners
    rm = []
    for sp in spannerBundle.getByCompleteStatus(True):
        s._insertCore(0, sp)
        rm.append(sp)
    for sp in rm:
        spannerBundle.remove(sp)

    s.elementsChanged()
    return s

#------------------------------------------------------------------------------
# beam and beams
def mxToBeam(mxBeam, inputM21 = None):
    '''
    given an mxBeam object return a :class:`~music21.beam.Beam` object

    
    >>> mxBeam = musicxml.mxObjects.Beam()
    >>> mxBeam.set('charData', 'begin')
    >>> a = musicxml.fromMxObjects.mxToBeam(mxBeam)
    >>> a.type
    'start'

    >>> mxBeam.set('charData', 'continue')
    >>> a = musicxml.fromMxObjects.mxToBeam(mxBeam)
    >>> a.type
    'continue'

    >>> mxBeam.set('charData', 'end')
    >>> a = musicxml.fromMxObjects.mxToBeam(mxBeam)
    >>> a.type
    'stop'

    >>> mxBeam.set('charData', 'forward hook')
    >>> a = musicxml.fromMxObjects.mxToBeam(mxBeam)
    >>> a.type
    'partial'
    >>> a.direction
    'right'

    >>> mxBeam.set('charData', 'backward hook')
    >>> a = musicxml.fromMxObjects.mxToBeam(mxBeam)
    >>> a.type
    'partial'
    >>> a.direction
    'left'

    >>> mxBeam.set('charData', 'crazy')
    >>> a = musicxml.fromMxObjects.mxToBeam(mxBeam)
    Traceback (most recent call last):
    FromMxObjectsException: unexpected beam type encountered (crazy)
    '''
    if inputM21 is None:
        beamOut = beam.Beam()
    else:
        beamOut = inputM21
    mxType = mxBeam.get('charData')
    if mxType == 'begin':
        beamOut.type = 'start'
    elif mxType == 'continue':
        beamOut.type = 'continue'
    elif mxType == 'end':
        beamOut.type = 'stop'
    elif mxType == 'forward hook':
        beamOut.type = 'partial'
        beamOut.direction = 'right'
    elif mxType == 'backward hook':
        beamOut.type = 'partial'
        beamOut.direction = 'left'
    else:
        raise FromMxObjectsException('unexpected beam type encountered (%s)' % mxType)

    return beamOut


def mxToBeams(mxBeamList, inputM21 = None):
    '''given a list of mxBeam objects, sets the beamsList

    
    >>> a = beam.Beams()
    >>> a.fill(2, type='start')
    >>> mxBeamList = musicxml.toMxObjects.beamsToMx(a)
    >>> b = musicxml.fromMxObjects.mxToBeams(mxBeamList)
    >>> b
    <music21.beam.Beams <music21.beam.Beam 1/start>/<music21.beam.Beam 2/start>>
    '''
    if inputM21 is None:
        beamsOut = beam.Beams()
    else:
        beamsOut = inputM21
    
    for i, mxBeam in enumerate(mxBeamList):
        beamObj = mxToBeam(mxBeam)
        beamObj.number = i + 1
        beamsOut.beamsList.append(beamObj)

    return beamsOut

#---------------------------------------------------------
# layout

def mxPrintToPageLayout(mxPrint, inputM21 = None):
    '''
    Given an mxPrint object, set object data for 
    the print section of a layout.PageLayout object

    
    >>> mxPrint = musicxml.mxObjects.Print()
    >>> mxPrint.set('new-page', 'yes')
    >>> mxPrint.set('page-number', 5)
    >>> mxPageLayout = musicxml.mxObjects.PageLayout()
    >>> mxPageLayout.pageHeight = 4000
    >>> mxPageMargins = musicxml.mxObjects.PageMargins()
    >>> mxPageMargins.set('leftMargin', 20)
    >>> mxPageMargins.set('rightMargin', 30.2)
    >>> mxPageLayout.append(mxPageMargins) 
    >>> mxPrint.append(mxPageLayout)

    >>> pl = musicxml.fromMxObjects.mxPrintToPageLayout(mxPrint)
    >>> pl.isNew
    True
    >>> pl.rightMargin > 30.1 and pl.rightMargin < 30.3
    True
    >>> pl.leftMargin
    20.0
    >>> pl.pageNumber
    5


    Alternatively, pass a music21 object into this routine.

    >>> plAlt = layout.PageLayout()
    >>> musicxml.fromMxObjects.mxPrintToPageLayout(mxPrint, plAlt)
    >>> plAlt.pageNumber
    5
    >>> plAlt.pageHeight
    4000.0
    >>> plAlt.isNew
    True
    '''
    if inputM21 is None:
        pageLayout = layout.PageLayout()
    else:
        pageLayout = inputM21
    
    data = mxPrint.get('newPage')
    if data == 'yes': # encoded as yes/no in musicxml
        pageLayout.isNew = True
    else:
        pageLayout.isNew = False
        
    number = mxPrint.get('page-number')
    if number is not None and number != "":
        if common.isStr(number):
            pageLayout.pageNumber = int(number)
        else:
            pageLayout.pageNumber = number

    mxPageLayout = None # blank
    for x in mxPrint:
        if isinstance(x, mxObjects.PageLayout):
            mxPageLayout = x
            break # find first and break

    if mxPageLayout is not None:
        mxPageLayoutToPageLayout(mxPageLayout, inputM21 = pageLayout)


    if inputM21 is None:
        return pageLayout

def mxPageLayoutToPageLayout(mxPageLayout, inputM21 = None):
    '''
    get a PageLayout object from an mxPageLayout
    
    Called out from mxPrintToPageLayout because it
    is also used in the <defaults> tag
    '''
    if inputM21 is None:
        pageLayout = layout.PageLayout()
    else:
        pageLayout = inputM21

    pageHeight = mxPageLayout.get('pageHeight')
    if pageHeight is not None:
        pageLayout.pageHeight = float(pageHeight)
    pageWidth = mxPageLayout.get('pageWidth')
    if pageWidth is not None:
        pageLayout.pageWidth = float(pageWidth)

    mxPageMargins = None
    for x in mxPageLayout:
        if isinstance(x, mxObjects.PageMargins):
            mxPageMargins = x

    if mxPageMargins != None:
        data = mxPageMargins.get('leftMargin')
        if data != None:
            # may be floating point values
            pageLayout.leftMargin = float(data)
        data = mxPageMargins.get('rightMargin')
        if data != None:
            pageLayout.rightMargin = float(data)

        data = mxPageMargins.get('topMargin')
        if data != None:
            pageLayout.topMargin = float(data)

        data = mxPageMargins.get('bottomMargin')
        if data != None:
            pageLayout.bottomMargin = float(data)

    if inputM21 is None:
        return pageLayout

def mxPrintToSystemLayout(mxPrint, inputM21 = None):
    '''
    Given an mxPrint object, set object data

    
    >>> mxPrint = musicxml.mxObjects.Print()
    >>> mxPrint.set('new-system', 'yes')
    >>> mxSystemLayout = musicxml.mxObjects.SystemLayout()
    >>> mxSystemLayout.systemDistance = 55
    >>> mxSystemMargins = musicxml.mxObjects.SystemMargins()
    >>> mxSystemMargins.set('leftMargin', 20)
    >>> mxSystemMargins.set('rightMargin', 30.2)
    >>> mxSystemLayout.append(mxSystemMargins) 
    >>> mxPrint.append(mxSystemLayout)

    >>> sl = musicxml.fromMxObjects.mxPrintToSystemLayout(mxPrint)
    >>> sl.isNew
    True
    >>> sl.rightMargin > 30.1 and sl.rightMargin <= 30.2
    True
    >>> sl.leftMargin
    20.0
    >>> sl.distance
    55.0
    '''
    if inputM21 is None:
        systemLayout = layout.SystemLayout()
    else:
        systemLayout = inputM21

    data = mxPrint.get('newSystem')
    if data == 'yes': # encoded as yes/no in musicxml
        systemLayout.isNew = True
    elif data == 'no':
        systemLayout.isNew = False

    #mxSystemLayout = mxPrint.get('systemLayout')
    mxSystemLayout = None # blank
    for x in mxPrint:
        if isinstance(x, mxObjects.SystemLayout):
            mxSystemLayout = x
            break # find first and break

    if mxSystemLayout is not None:
        mxSystemLayoutToSystemLayout(mxSystemLayout, inputM21 = systemLayout)

    if inputM21 is None:
        return systemLayout

def mxSystemLayoutToSystemLayout(mxSystemLayout, inputM21 = None):
    '''
    get a SystemLayout object from an mxSystemLayout
    
    Called out from mxPrintToSystemLayout because it
    is also used in the <defaults> tag
    '''
    if inputM21 is None:
        systemLayout = layout.SystemLayout()
    else:
        systemLayout = inputM21

    mxSystemMargins = None
    for x in mxSystemLayout:
        if isinstance(x, mxObjects.SystemMargins):
            mxSystemMargins = x
            break

    if mxSystemMargins is not None:
        data = mxSystemMargins.get('leftMargin')
        if data != None:
            # may be floating point values
            systemLayout.leftMargin = float(data)
        data = mxSystemMargins.get('rightMargin')
        if data != None:
            systemLayout.rightMargin = float(data)
        data = mxSystemMargins.get('topMargin')
        if data != None:
            systemLayout.rightMargin = float(data)
        data = mxSystemMargins.get('bottomMargin')
        if data != None:
            systemLayout.rightMargin = float(data)
    
    if mxSystemLayout.systemDistance != None:
        systemLayout.distance = float(mxSystemLayout.systemDistance)
    if mxSystemLayout.topSystemDistance != None:
        systemLayout.topDistance = float(mxSystemLayout.topSystemDistance)


    if inputM21 is None:
        return systemLayout


def mxPrintToStaffLayoutList(mxPrint, inputM21 = None):
    '''
    Given an mxPrint object, return a list of StaffLayout objects (may be empty)

    
    >>> mxPrint = musicxml.mxObjects.Print()
    
    # this is a red-herring... does nothing here...
    >>> mxPrint.set('new-system', 'yes')
    
    >>> mxStaffLayout = musicxml.mxObjects.StaffLayout()
    >>> mxStaffLayout.staffDistance = 55
    >>> mxStaffLayout.set('number', 1)
    >>> mxPrint.append(mxStaffLayout)

    >>> slList = musicxml.fromMxObjects.mxPrintToStaffLayoutList(mxPrint)
    >>> sl = slList[0]
    >>> sl.distance
    55.0
    >>> sl.staffNumber
    1
    '''
    staffLayoutList = []

    for x in mxPrint:
        if isinstance(x, mxObjects.StaffLayout):
            sl = mxStaffLayoutToStaffLayout(x)
            staffLayoutList.append(sl)
    
    return staffLayoutList

def mxStaffLayoutToStaffLayout(mxStaffLayout, inputM21 = None):
    '''
    get a StaffLayout object from an mxStaffLayout
    
    Called out from mxPrintToStaffLayoutList because it
    is also used in the <defaults> tag
    '''
    if inputM21 is None:
        staffLayout = layout.StaffLayout()
    else:
        staffLayout = inputM21
    
    if mxStaffLayout.staffDistance != None:
        staffLayout.distance = float(mxStaffLayout.staffDistance)
    try:
        data = mxStaffLayout.get('number')
        if data is not None:
            staffLayout.staffNumber = int(data)
    except xmlnode.XMLNodeException:
        pass



    if inputM21 is None:
        return staffLayout




#-----------------------------------------------------------------
# metadata
def mxScoreToMetadata(mxScore, inputM21 = None):
    '''
    Use an mxScore, to fill in parameters of a 
    :class:`~music21.metadata.Metadata` object.
    
    if `inputM21` is None, a new `Metadata` object
    is created and returned at the end.
    
    Otherwise, the parameters of this Metadata object
    are changed and nothing is returned.
    '''
    if inputM21 is not None:
        md = inputM21
    else:
        md = metadata.Metadata()
    
    mxMovementNumber = mxScore.get('movementNumber')
    if mxMovementNumber != None:
        md.movementNumber = mxMovementNumber

    # xml calls this title not name
    mxName = mxScore.get('movementTitle')
    if mxName != None:
        md.movementName = mxName

    mxWork = mxScore.get('workObj')
    if mxWork != None: # may be set to none
        md.title = mxWork.get('workTitle')
        #environLocal.printDebug(['mxScoreToMetadata, got title', md.title])
        md.number = mxWork.get('workNumber')
        md.opusNumber = mxWork.get('opus')

    mxIdentification = mxScore.get('identificationObj')
    if mxIdentification != None:
        for mxCreator in mxIdentification.get('creatorList'):
            # do an mx conversion for mxCreator to Contributor
            c = mxCreatorToContributor(mxCreator)
            md.addContributor(c)

    # not yet supported; an encoding is also found in identification obj
    # mxEncoding = mxScore.get('encodingObj')
    
    if inputM21 is None:
        return md

def mxCreatorToContributor(mxCreator, inputM21 = None):
    '''
    Given an mxCreator, fill the necessary parameters of a Contributor.

    
    >>> mxCreator = musicxml.mxObjects.Creator()
    >>> mxCreator.set('type', 'composer')
    >>> mxCreator.set('charData', 'Beethoven, Ludwig van')

    >>> c = musicxml.fromMxObjects.mxCreatorToContributor(mxCreator)
    >>> c
    <music21.metadata.primitives.Contributor object at 0x...>
    >>> c.role
    'composer'
    >>> c.name
    'Beethoven, Ludwig van'
    '''
    if inputM21 is None:
        c = metadata.Contributor()
    else:
        c = inputM21
    
    mxCreatorType = mxCreator.get('type')
    if mxCreatorType != None and \
        mxCreatorType in metadata.Contributor.roleNames:
        c.role = mxCreatorType
    else: # roles are not defined in musicxml
        pass
        #environLocal.printDebug(['mxCreatorToContributor:', 'received unknown Contributor role: %s' % mxCreatorType])
    # remove any whitespace found
    c.name = mxCreator.get('charData').strip()

    if inputM21 is None:
        return c

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testBasic(self):
        pass

    def pitchOut(self, listIn):
        '''
        make it so that the tests that look for the old-style pitch.Pitch 
        representation still work.
        '''
        out = "["
        for p in listIn:
            out += str(p) + ', '
        out = out[0:len(out)-2]
        out += "]"
        return out


    def testBarRepeatConversion(self):
        from music21 import corpus, converter

        #a = converter.parse(testPrimitive.simpleRepeat45a)
        # this is a good example with repeats
        s = converter.parse(corpus.getWorkList('k80/movement3')[0], format='oldmusicxml')
        for p in s.parts:
            post = p.flat.getElementsByClass('Repeat')
            self.assertEqual(len(post), 6)

        #a = converter.parse(corpus.getWorkList('opus41no1/movement3')[0], format='oldmusicxml')
        #s.show()

    def testVoices(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.voiceDouble, format='oldmusicxml')
        m1 = s.parts[0].getElementsByClass('Measure')[0]
        self.assertEqual(m1.hasVoices(), True)

        self.assertEqual([v.id for v in m1.voices], [u'1', u'2'])

        self.assertEqual([e.offset for e in m1.voices[0]], [0.0, 1.0, 2.0, 3.0])
        self.assertEqual([e.offset for e in m1.voices['1']], [0.0, 1.0, 2.0, 3.0])

        self.assertEqual([e.offset for e in m1.voices[1]], [0.0, 2.0, 2.5, 3.0, 3.5])
        self.assertEqual([e.offset for e in m1.voices['2']], [0.0, 2.0, 2.5, 3.0, 3.5])
        #s.show()


    def testSlurInputA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.spannersSlurs33c, format='oldmusicxml')
        # have 10 spanners
        self.assertEqual(len(s.flat.getElementsByClass('Spanner')), 5)

        # can get the same from a getAll search
        self.assertEqual(len(s.getAllContextsByClass('Spanner')), 5)

        # try to get all spanners from the first note
        self.assertEqual(len(s.flat.notesAndRests[0].getAllContextsByClass('Spanner')), 5)
        #s.show('t')
        #s.show()


    def testMultipleStavesPerPartA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive
        from music21.musicxml import xmlHandler

        mxDoc = xmlHandler.Document()
        mxDoc.read(testPrimitive.pianoStaff43a)

        # parts are stored in component list
        p1 = mxDoc.score.componentList[0]
        self.assertEqual(p1.getStavesCount(), 2)

        s = converter.parse(testPrimitive.pianoStaff43a, format='oldmusicxml')
        self.assertEqual(len(s.parts), 2)
        #s.show()
        self.assertEqual(len(s.parts[0].flat.getElementsByClass('Note')), 1)
        self.assertEqual(len(s.parts[1].flat.getElementsByClass('Note')), 1)

        self.assertEqual(isinstance(s.parts[0], stream.PartStaff), True)
        self.assertEqual(isinstance(s.parts[1], stream.PartStaff), True)


    def testMultipleStavesPerPartB(self):
        from music21 import converter
        from music21.musicxml import testFiles

        s = converter.parse(testFiles.moussorgskyPromenade, format='oldmusicxml') # @UndefinedVariable
        self.assertEqual(len(s.parts), 2)

        self.assertEqual(len(s.parts[0].flat.getElementsByClass('Note')), 19)
        # only chords in the second part
        self.assertEqual(len(s.parts[1].flat.getElementsByClass('Note')), 0)

        self.assertEqual(len(s.parts[0].flat.getElementsByClass('Chord')), 11)
        self.assertEqual(len(s.parts[1].flat.getElementsByClass('Chord')), 11)

        #s.show()


    def testMultipleStavesPerPartC(self):
        from music21 import corpus, converter
        s = converter.parse(corpus.getWorkList('schoenberg/opus19/movement2')[0], format='oldmusicxml')
        self.assertEqual(len(s.parts), 2)

        s = converter.parse(corpus.getWorkList('schoenberg/opus19/movement6')[0], format='oldmusicxml')
        self.assertEqual(len(s.parts), 2)

        #s.show()


    def testSpannersA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.spanners33a, format='oldmusicxml')
        # this number will change as more are being imported
        self.assertEqual(len(s.flat.spanners) >= 2, True)


        #environLocal.printDebug(['pre s.measures(2,3)', 's', s])
        ex = s.measures(2, 3) # this needs to get all spanners too

        # all spanners are referenced over; even ones that may not be relevant
        self.assertEqual(len(ex.flat.spanners), 14)
        #ex.show()

        # slurs are on measures 2, 3
        # crescendos are on measures 4, 5
        # wavy lines on measures 6, 7
        # brackets etc. on measures 10-14
        # glissando on measure 16


    def testTextExpressionsA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.textExpressions, format='oldmusicxml')
        #s.show() 
        self.assertEqual(len(s.flat.getElementsByClass('TextExpression')), 3)

        p1 = s.parts[0]
        m1 = p1.getElementsByClass('Measure')[0]
        self.assertEqual(len(m1.getElementsByClass('TextExpression')), 0)
        # all in measure 2
        m2 = p1.getElementsByClass('Measure')[1]
        self.assertEqual(len(m2.getElementsByClass('TextExpression')), 3)

        teStream = m2.getElementsByClass('TextExpression')
        self.assertEqual([te.offset for te in teStream], [1.0, 1.5, 4.0])

        #s.show()


    def testTextExpressionsC(self):
        from music21 import corpus, converter
        s = converter.parse(corpus.getWorkList('bwv66.6')[0], format='oldmusicxml')
        p = s.parts[0]
        for m in p.getElementsByClass('Measure'):
            for n in m.flat.notes:
                if n.pitch.name in ['B']:
                    msg = '%s\n%s' % (n.pitch.nameWithOctave, n.duration.quarterLength)
                    te = expressions.TextExpression(msg)
                    te.size = 14
                    te.style = 'bold'
                    te.justify = 'center'
                    te.enclosure = 'rectangle'
                    te.positionVertical = -80
                    m.insert(n.offset, te)
        #p.show()        


    def testTextExpressionsD(self):
        from music21 import corpus, converter
        # test placing text expression in arbitrary locations
        s = converter.parse(corpus.getWorkList('bwv66.6')[0], format='oldmusicxml')
        p = s.parts[-1] # get bass
        for m in p.getElementsByClass('Measure')[1:]:
            for pos in [1.5, 2.5]:
                te = expressions.TextExpression(pos)
                te.style = 'bold'
                te.justify = 'center'
                te.enclosure = 'rectangle'
                m.insert(pos, te)
        #p.show()

    def testTextExpressionsE(self):
        import random
        s = stream.Stream()
        for i in range(6):
            m = stream.Measure(number=i + 1)
            m.append(layout.SystemLayout(isNew=True))
            m.append(note.Rest(type='whole'))
            s.append(m)
        for m in s.getElementsByClass('Measure'):
            offsets = [x * .25 for x in range(16)]
            random.shuffle(offsets)
            offsets = offsets[:4]
            for o in offsets:
                te = expressions.TextExpression(o)
                te.style = 'bold'
                te.justify = 'center'
                te.enclosure = 'rectangle'
                m.insert(o, te)
        #s.show()      



    def testImportRepeatExpressionsA(self):
        # test importing from musicxml
        from music21.musicxml import testPrimitive
        from music21 import converter

        # has one segno
        s = converter.parse(testPrimitive.repeatExpressionsA, format='oldmusicxml')
        self.assertEqual(len(s.flat.getElementsByClass(repeat.Segno)), 1)
        self.assertEqual(len(s.flat.getElementsByClass(repeat.Fine)), 1)
        self.assertEqual(len(s.flat.getElementsByClass(repeat.DalSegnoAlFine)), 1)

        # has two codas
        s = converter.parse(testPrimitive.repeatExpressionsB, format='oldmusicxml')
        self.assertEqual(len(s.flat.getElementsByClass(repeat.Coda)), 2)
        # has one d.c.al coda
        self.assertEqual(len(s.flat.getElementsByClass(repeat.DaCapoAlCoda)), 1)

    def testImportRepeatBracketA(self):
        from music21 import corpus, converter
        # has repeats in it; start with single emasure
        s = corpus.parse('opus74no1', 3)
        # there are 2 for each part, totaling 8
        self.assertEqual(len(s.flat.getElementsByClass('RepeatBracket')), 8)
        # can get for each part as spanners are stored in Part now

        # TODO: need to test getting repeat brackets after measure extraction
        #s.parts[0].show() # 72 through 77
        sSub = s.parts[0].measures(72, 77)
        # 2 repeat brackets are gathered b/c they are stored at the Part by 
        # default
        rbSpanners = sSub.getElementsByClass('RepeatBracket')
        self.assertEqual(len(rbSpanners), 2)


    def testImportVoicesA(self):
        # testing problematic voice imports

        from music21.musicxml import testPrimitive
        from music21 import converter
        # this 2 part segments was importing multiple voices within
        # a measure, even though there was no data in the second voice
        s = converter.parse(testPrimitive.mixedVoices1a, format='oldmusicxml')
        self.assertEqual(len(s.parts), 2)
        # there are voices, but they have been removed
        self.assertEqual(len(s.parts[0].getElementsByClass(
            'Measure')[0].voices), 0)

        #s.parts[0].show('t')
        #self.assertEqual(len(s.parts[0].voices), 2)
        s = converter.parse(testPrimitive.mixedVoices1b, format='oldmusicxml')
        self.assertEqual(len(s.parts), 2)
        self.assertEqual(len(s.parts[0].getElementsByClass(
            'Measure')[0].voices), 0)
        #s.parts[0].show('t')

        # this case, there were 4, but there should be 2
        s = converter.parse(testPrimitive.mixedVoices2, format='oldmusicxml')
        self.assertEqual(len(s.parts), 2)
        self.assertEqual(len(s.parts[0].getElementsByClass(
            'Measure')[0].voices), 2)
        self.assertEqual(len(s.parts[1].getElementsByClass(
            'Measure')[0].voices), 2)

        #s.parts[0].show('t')

#         s = converter.parse(testPrimitive.mixedVoices1b)
#         s = converter.parse(testPrimitive.mixedVoices2)


    def testImportMetronomeMarksA(self):
        from music21.musicxml import testPrimitive
        from music21 import converter
        # has metronome marks defined, not with sound tag
        s = converter.parse(testPrimitive.metronomeMarks31c, format='oldmusicxml')
        # get all tempo indications
        mms = s.flat.getElementsByClass('TempoIndication')
        self.assertEqual(len(mms) > 3, True)


    def testImportMetronomeMarksB(self):
        pass
        # TODO: look for files that only have sound tags and create MetronomeMarks
        # need to look for bundling of Words text expressions with tempo

        # has only sound tempo=x tag
        #s = converter.parse(testPrimitive.articulations01)
        #s.show()

    def xtestImportGraceNotesA(self):
        # test importing from musicxml
        from music21.musicxml import testPrimitive
        from music21 import converter
        unused_s = converter.parse(testPrimitive.graceNotes24a, format='oldmusicxml')

        #s.show()

    def testChordalStemDirImport(self):
        #NB: Finale apparently will not display a pitch that is a member of a chord without a stem
        #unless all chord members are without stems.
        from music21.musicxml import m21ToString
        from music21 import converter

        n1 = note.Note('f3')
        n1.notehead = 'diamond'
        n1.stemDirection = 'down'
        n2 = note.Note('c4')
        n2.stemDirection = 'noStem'
        c = chord.Chord([n1, n2])
        c.quarterLength = 2
        
        xml = m21ToString.fromMusic21Object(c)
        #print xml
        #c.show()
        inputStream = converter.parse(xml, format='oldmusicxml')
        chordResult = inputStream.flat.notes[0]
#         for n in chordResult:
#             print n.stemDirection       

        self.assertEqual(chordResult.getStemDirection(chordResult.pitches[0]), 'down')
        self.assertEqual(chordResult.getStemDirection(chordResult.pitches[1]), 'noStem')


    def testStaffGroupsA(self):
        from music21.musicxml import testPrimitive
        from music21 import converter

        s = converter.parse(testPrimitive.staffGroupsNested41d, format='oldmusicxml')
        self.assertEqual(len(s.getElementsByClass('StaffGroup')), 2)
        #raw = s.musicxml
        sg1 = s.getElementsByClass('StaffGroup')[0]
        self.assertEqual(sg1.symbol, 'brace')
        self.assertEqual(sg1.barTogether, True)

        sg2 = s.getElementsByClass('StaffGroup')[1]
        self.assertEqual(sg2.symbol, 'line')
        self.assertEqual(sg2.barTogether, True)

    def testInstrumentTranspositionA(self):
        from music21.musicxml import testPrimitive
        from music21 import converter

        s = converter.parse(testPrimitive.transposingInstruments72a, format='oldmusicxml')
        i1 = s.parts[0].flat.getElementsByClass('Instrument')[0]
        i2 = s.parts[1].flat.getElementsByClass('Instrument')[0]
        i3 = s.parts[2].flat.getElementsByClass('Instrument')[0]

        self.assertEqual(str(i1.transposition), '<music21.interval.Interval M-2>')
        self.assertEqual(str(i2.transposition), '<music21.interval.Interval M-6>')


    def testInstrumentTranspositionB(self):
        from music21.musicxml import testPrimitive
        from music21 import converter

        s = converter.parse(testPrimitive.transposing01, format='oldmusicxml')
        iStream1 = s.parts[0].flat.getElementsByClass('Instrument')
        # three instruments; one initial, and then one for each transposition
        self.assertEqual(len(iStream1), 3)
        # should be 3
        iStream2 = s.parts[1].flat.getElementsByClass('Instrument')
        self.assertEqual(len(iStream2), 3)
        i2 = iStream2[0]

        iStream3 = s.parts[2].flat.getElementsByClass('Instrument')
        self.assertEqual(len(iStream3), 1)
        i3 = iStream3[0]


        self.assertEqual(str(iStream1[0].transposition), 'None')
        self.assertEqual(str(iStream1[1].transposition), '<music21.interval.Interval P-5>')
        self.assertEqual(str(iStream1[2].transposition), '<music21.interval.Interval P1>')

        self.assertEqual(str(iStream2[0].transposition), '<music21.interval.Interval M-2>')
        self.assertEqual(str(iStream2[1].transposition), '<music21.interval.Interval m3>')

        self.assertEqual(str(i3.transposition), '<music21.interval.Interval P-5>')

        self.assertEqual(self.pitchOut([p for p in s.parts[0].flat.pitches]), '[A4, A4, A4, A4, A4, A4, A4, A4, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, A4, A4, A4, A4]')
        self.assertEqual(self.pitchOut([p for p in s.parts[1].flat.pitches]), '[B4, B4, B4, B4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, B4, B4, B4, B4, B4, B4]')
        self.assertEqual(self.pitchOut([p for p in s.parts[2].flat.pitches]), '[E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5]')

        sSounding = s.toSoundingPitch(inPlace=False)
        self.assertEqual(self.pitchOut([p for p in sSounding.parts[0].flat.pitches]), '[A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4]')
        self.assertEqual(self.pitchOut([p for p in sSounding.parts[1].flat.pitches]), '[A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4]')
        self.assertEqual(self.pitchOut([p for p in sSounding.parts[2].flat.pitches]), '[A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4]')

        # chordification by default places notes at sounding pitch
        sChords = s.chordify()
        self.assertEqual(self.pitchOut([p for p in sChords.flat.pitches]), '[A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4]')
        #sChords.show()


    def testInstrumentTranspositionC(self):
        # generate all transpositions on output
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.transposing01, format='oldmusicxml')
        instStream = s.flat.getElementsByClass('Instrument')
        #for i in instStream:
        #    print(i.offset, i, i.transposition)
        self.assertEqual(len(instStream), 7)
        #s.show()



    def testHarmonyA(self):
        from music21 import corpus, converter

        s = converter.parse(corpus.getWorkList('leadSheet/berlinAlexandersRagtime')[0], format='oldmusicxml')
        self.assertEqual(len(s.flat.getElementsByClass('ChordSymbol')), 19)

        match = [h.chordKind for h in s.flat.getElementsByClass('ChordSymbol')]
        self.assertEqual(match, [u'major', u'dominant', u'major', u'major', u'major', u'major', u'dominant', u'major', u'dominant', u'major', u'dominant', u'major', u'dominant', u'major', u'dominant', u'major', u'dominant', u'major', u'major'])

        match = [str(h.root()) for h in s.flat.getElementsByClass('ChordSymbol')]
        
        self.assertEqual(match, ['F3', 'C3', 'F3', 'B-2', 'F3', 'C3', 'G2', 'C3', 'C3', 'F3', 'C3', 'F3', 'F2', 'B-2', 'F2', 'F3', 'C3', 'F3', 'C3'])

        match = set([str(h.figure) for h in s.flat.getElementsByClass('ChordSymbol')])
        
        self.assertEqual(match, set(['F','F7','B-','C7','G7','C']))


        s = converter.parse(corpus.getWorkList('monteverdi/madrigal.3.12')[0], format='oldmusicxml')
        self.assertEqual(len(s.flat.getElementsByClass('ChordSymbol')), 10)

        s = converter.parse(corpus.getWorkList('leadSheet/fosterBrownHair')[0], format='oldmusicxml')
        self.assertEqual(len(s.flat.getElementsByClass('ChordSymbol')), 40)

        #s.show()

    def testOrnamentandTechnical(self):
        from music21 import corpus, converter

        s = converter.parse(corpus.getWorkList('opus133')[0], format='oldmusicxml')
        ex = s.parts[0]
        countTrill = 0
        for n in ex.flat.notes:
            for e in n.expressions:
                if 'Trill' in e.classes:
                    countTrill += 1
        self.assertEqual(countTrill, 54)
        
        # TODO: Get a better test... the single harmonic in the viola part, m. 482 is probably a mistake!
        countTechnical = 0
        for n in s.parts[2].flat.notes:
            for a in n.articulations:
                if 'TechnicalIndication' in a.classes:
                    countTechnical += 1
        self.assertEqual(countTechnical, 1)


    def testOrnamentC(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        # has many ornaments
        s = converter.parse(testPrimitive.notations32a, format='oldmusicxml')

        #s.flat.show('t')
        self.assertEqual(len(s.flat.getElementsByClass('TremoloSpanner')), 0) # no spanned tremolos
        
        count = 0
        for n in s.flat.notes:
            for e in n.expressions:
                if 'Tremolo' in e.classes:
                    count += 1
        self.assertEqual(count, 1) # One single Tremolo


        count = 0
        for n in s.flat.notes:
            for e in n.expressions:
                if 'Turn' in e.classes:
                    count += 1
        self.assertEqual(count, 4) # include inverted turn

        count = 0
        for n in s.flat.notes:
            for e in n.expressions:
                if 'InvertedTurn' in e.classes:
                    count += 1
        self.assertEqual(count, 1)

        count = 0
        for n in s.flat.notes:
            for e in n.expressions:
                if 'Shake' in e.classes:
                    count += 1
        self.assertEqual(count, 1)

        count = 0
        for n in s.flat.notes:
            for e in n.expressions:
                if 'Schleifer' in e.classes:
                    count += 1
        self.assertEqual(count, 1)

    def testTextBoxA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.textBoxes01, format='oldmusicxml')
        tbs = s.flat.getElementsByClass('TextBox')
        self.assertEqual(len(tbs), 5)

        msg = []
        for tb in tbs:
            msg.append(tb.content)
        self.assertEqual(msg, [u'This is a text box!', u'pos 200/300 (lower left)', u'pos 1000/300 (lower right)', u'pos 200/1500 (upper left)', u'pos 1000/1500 (upper right)'])

    def testImportSlursA(self):
        from music21 import corpus, converter
        # this is a good test as this encoding uses staffs, not parts
        # to encode both parts; this requires special spanner handling
        s = converter.parse(corpus.getWorkList('mozart/k545/movement1_exposition')[0], format='oldmusicxml')
        sf = s.flat       
        slurs = sf.getElementsByClass(spanner.Slur)
        # TODO: this value should be 2, but due to staff encoding we 
        # have orphaned spanners that are not cleaned up
        self.assertEqual(len(slurs), 4)

        n1, n2 = s.parts[0].flat.notes[3], s.parts[0].flat.notes[5]
        #environLocal.printDebug(['n1', n1, 'id(n1)', id(n1), slurs[0].getSpannedElementIds(), slurs[0].getSpannedElementIds()])
        self.assertEqual(id(n1) == slurs[0].getSpannedElementIds()[0], True)
        self.assertEqual(id(n2) == slurs[0].getSpannedElementIds()[1], True)

        #environLocal.printDebug(['n2', n2, 'id(n2)', id(n2), slurs[0].getSpannedElementIds()])


    def testImportWedgeA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.spanners33a, format='oldmusicxml')
        self.assertEqual(len(s.flat.getElementsByClass('Crescendo')), 1)
        self.assertEqual(len(s.flat.getElementsByClass('Diminuendo')), 1)


    def testImportWedgeB(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        # this produces a single component cresc
        s = converter.parse(testPrimitive.directions31a, format='oldmusicxml')
        self.assertEqual(len(s.flat.getElementsByClass('Crescendo')), 2)


    def testBracketImportB(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.spanners33a, format='oldmusicxml')
        #s.show()
        self.assertEqual(len(s.flat.getElementsByClass('Line')), 6)


    def testTrillExtensionImportA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive
        s = converter.parse(testPrimitive.notations32a, format='oldmusicxml')
        #s.show()
        self.assertEqual(len(s.flat.getElementsByClass('TrillExtension')), 2)


    def testGlissandoImportA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive
        s = converter.parse(testPrimitive.spanners33a, format='oldmusicxml')
        #s.show()
        self.assertEqual(len(s.flat.getElementsByClass('Glissando')), 1)


    def testImportDashes(self):
        # dashes are imported as Lines (as are brackets)
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.spanners33a, format='oldmusicxml')
        self.assertEqual(len(s.flat.getElementsByClass('Line')), 6)


    def testImportGraceA(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.graceNotes24a, format='oldmusicxml')
        #s.show()        
        match = [str(p) for p in s.pitches]
        #print match
        self.assertEqual(match, ['D5', 'C5', 'E5', 'D5', 'C5', 'D5', 'C5', 'D5', 'C5', 'D5', 'C5', 'E5', 'D5', 'C5', 'D5', 'C5', 'D5', 'C5', 'E5', 'E5', 'F4', 'C5', 'D#5', 'C5', 'D-5', 'A-4', 'C5', 'C5'])


    def testBarException(self):
        mxBarline = mxObjects.Barline()
        mxBarline.set('barStyle', 'light-heavy')
        #Rasing the BarException
        self.assertRaises(bar.BarException, mxToRepeat, mxBarline)

        mxRepeat = mxObjects.Repeat()
        mxRepeat.set('direction', 'backward')
        mxBarline.set('repeatObj', mxRepeat)

        #all fine now, no exceptions here
        mxToRepeat(mxBarline)

        #Raising the BarException       
        mxBarline.set('barStyle', 'wunderbar')
        self.assertRaises(bar.BarException, mxToRepeat, mxBarline)


    def testStaffLayout(self):
        from music21 import corpus, converter
        c = converter.parse(corpus.getWorkList('demos/layoutTest.xml')[0], format='oldmusicxml', forceSource=True)
        #c = corpus.parse('demos/layoutTest.xml')        
        layouts = c.flat.getElementsByClass('LayoutBase')
        systemLayouts = layouts.getElementsByClass('SystemLayout')
        self.assertEqual(len(systemLayouts), 42)
        staffLayouts = layouts.getElementsByClass('StaffLayout')
#         for i,p in enumerate(c.parts):
#             print(i)
#             for l in p.flat.getElementsByClass('StaffLayout'):
#                 print(l.distance)        
        self.assertEqual(len(staffLayouts), 20)
        pageLayouts = layouts.getElementsByClass('PageLayout')
        self.assertEqual(len(pageLayouts), 10)
        scoreLayouts = layouts.getElementsByClass('ScoreLayout')
        self.assertEqual(len(scoreLayouts), 1)
        #score1 = scoreLayouts[0]
        #for sltemp in score1.staffLayoutList:
        #    print(sltemp, sltemp.distance)


        self.assertEqual(len(layouts), 73)

        
        sl0 = systemLayouts[0]
        self.assertEqual(sl0.distance, None)
        self.assertEqual(sl0.topDistance, 211.0)
        self.assertEqual(sl0.leftMargin, 70.0)
        self.assertEqual(sl0.rightMargin, 0.0)

                
        sizes = []
        for s in staffLayouts:
            if s.staffSize is not None:
                sizes.append(s.staffSize)
        self.assertEqual(sizes, [80.0, 120.0, 80.0])

    def testStaffLayoutMore(self):
        from music21 import corpus, converter
        c = converter.parse(corpus.getWorkList('demos/layoutTestMore.xml')[0], format='oldmusicxml', forceSource=True)
        #c = corpus.parse('demos/layoutTest.xml')        
        layouts = c.flat.getElementsByClass('LayoutBase')
        self.assertEqual(len(layouts), 76)
        systemLayouts = layouts.getElementsByClass('SystemLayout')
        sl0 = systemLayouts[0]
        self.assertEqual(sl0.distance, None)
        self.assertEqual(sl0.topDistance, 211.0)
        self.assertEqual(sl0.leftMargin, 70.0)
        self.assertEqual(sl0.rightMargin, 0.0)
#         for s in layouts:
#             if hasattr(s, 'staffSize'):
#                 print(s, s.staffSize)
                
        staffLayouts = layouts.getElementsByClass('StaffLayout')
        sizes = []
        for s in staffLayouts:
            if s.staffSize is not None:
                sizes.append(s.staffSize)
        self.assertEqual(sizes, [80.0, 120.0, 80.0])
        
    def testCountDynamics(self):
        from music21 import  corpus, converter
        c = converter.parse(corpus.getWorkList('schoenberg/opus19/movement2.mxl')[0], format='oldmusicxml', forceSource=True)
        #c.show('musicxml.png')
        dynAll = c.flat.getElementsByClass('Dynamic')
        self.assertEqual(len(dynAll), 6)
        notesOrChords = (note.Note, chord.Chord)
        allNotesOrChords = c.flat.getElementsByClass(notesOrChords)
        self.assertEqual(len(allNotesOrChords), 50)
        allChords = c.flat.getElementsByClass('Chord')
        self.assertEqual(len(allChords), 45)
        pCount = 0
        for cc in allChords:
            pCount += len(cc.pitches)
        self.assertEqual(pCount, 97)
        
    def xtestLucaGloriaSpanners(self):
        '''
        lots of lines, including overlapping here
        
        problem in m. 99 of part 2 -- spanner seems to be in the score
        but not being output to musicxml
        '''
        from music21 import  corpus, converter
        c = converter.parse(corpus.getWorkList('luca/gloria.xml')[0], format='oldmusicxml', forceSource=True)
        print(c.parts[1].measure(99).notes[0].getSpannerSites())
        
#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [mxScoreToScore]

if __name__ == "__main__":
    # sys.arg test options will be used in mainTest()
    import music21
    music21.mainTest(Test)
   
#------------------------------------------------------------------------------
# eof
