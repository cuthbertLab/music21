# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         musicxml/toMxObjects.py
# Purpose:      Translate from music21 objects to musicxml.mxObject representation
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Low-level conversion routines from music21 objects to 
musicxml.mxObject representation.
'''
import unittest
import copy

from music21.ext import webcolors

from music21.musicxml import mxObjects

from music21 import common
from music21 import defaults
from music21 import exceptions21

# modules that import this include converter.py.
# thus, cannot import these here
from music21 import bar
from music21 import key
from music21 import metadata
from music21 import note
from music21 import meter
from music21 import spanner
from music21 import stream

from music21 import environment
_MOD = "musicxml.toMxObjects"
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------
class ToMxObjectsException(exceptions21.Music21Exception):
    pass

class NoteheadException(ToMxObjectsException):
    pass

def normalizeColor(color):
    if color in (None, ''):
        return color
    if '#' not in color:
        return (webcolors.css3_names_to_hex[color]).upper()
    return color 

def configureMxPartGroupFromStaffGroup(staffGroup):
    '''
    Create and configure an mxPartGroup object 
    from a staff group spanner. Note that this object 
    is not completely formed by this procedure.
    '''
    mxPartGroup = mxObjects.PartGroup()
    mxPartGroup.set('groupName', staffGroup.name)
    mxPartGroup.set('groupAbbreviation', staffGroup.abbreviation)
    mxPartGroup.set('groupSymbol', staffGroup.symbol)
    if staffGroup.barTogether in [True]:
        mxPartGroup.set('groupBarline', 'yes')
    elif staffGroup.barTogether in [False]:
        mxPartGroup.set('groupBarline', 'no')
    elif staffGroup.barTogether == 'Mensurstrich':
        mxPartGroup.set('groupBarline', 'Mensurstrich')
    #environLocal.printDebug(['configureMxPartGroupFromStaffGroup: mxPartGroup', mxPartGroup])
    return mxPartGroup


def textBoxToMxCredit(textBox):
    '''
    Convert a music21 TextBox to a MusicXML Credit.
    
    >>> tb = text.TextBox('testing')
    >>> tb.positionVertical = 500
    >>> tb.positionHorizontal = 300
    >>> tb.page = 3
    >>> mxCredit = musicxml.toMxObjects.textBoxToMxCredit(tb)
    >>> print(mxCredit)
    <credit page=3 <credit-words default-x=300 default-y=500 halign=center valign=top charData=testing>>
    '''
    # use line carriages to separate messages
    mxCredit = mxObjects.Credit()
    # add all credit words to components
    count = 0

    mxCredit.set('page', textBox.page)
    for l in textBox.content.split('\n'):
        cw = mxObjects.CreditWords(l)
        if count == 0: # on first, configure properties         
            cw.set('default-x', textBox.positionHorizontal)
            cw.set('default-y', textBox.positionVertical)
            cw.set('justify', textBox.justify)
            cw.set('font-style', textBox.style)
            cw.set('font-weight', textBox.weight)
            cw.set('font-size', textBox.size)
            cw.set('valign', textBox.alignVertical)
            cw.set('halign', textBox.alignHorizontal)
        mxCredit.append(cw)
        count += 1
    return mxCredit


def intervalToMXTranspose(intervalObj):
    '''Convert a music21 Interval into a musicxml transposition specification

    
    >>> musicxml.toMxObjects.intervalToMXTranspose(interval.Interval('m6'))
    <transpose diatonic=5 chromatic=8>
    >>> musicxml.toMxObjects.intervalToMXTranspose(interval.Interval('-M6'))
    <transpose diatonic=-5 chromatic=-9>
    '''
    mxTranspose = mxObjects.Transpose()

    rawSemitones = intervalObj.chromatic.semitones # will be directed
    octShift = 0
    if abs(rawSemitones) > 12:
        octShift, semitones = divmod(rawSemitones, 12)
    else:
        semitones = rawSemitones

    rawGeneric = intervalObj.diatonic.generic.directed
    if octShift != 0:
        # need to shift 7 for each octave; sign will be correct
        generic = rawGeneric + (octShift * 7)
    else:
        generic = rawGeneric

    # must implement the necessary shifts
    if intervalObj.generic.directed > 0:
        mxTranspose.diatonic = generic - 1
    elif intervalObj.generic.directed < 0:
        mxTranspose.diatonic = generic + 1

    mxTranspose.chromatic = semitones

    if octShift != 0:
        mxTranspose.octaveChange = octShift
    return mxTranspose


def tempoIndicationToMx(ti):
    '''
    Given a music21 MetronomeMark or MetricModulation, produce a musicxml Metronome 
    tag wrapped in a <direction> tag.

    
    >>> mm = tempo.MetronomeMark("slow", 40, note.Note(type='half'))
    >>> mxList = musicxml.toMxObjects.tempoIndicationToMx(mm)
    >>> mxList
    [<direction 
          <direction-type 
               <metronome parentheses=no 
                     <beat-unit charData=half> 
                     <per-minute charData=40>>> 
           <sound tempo=80.0>>, 
     <direction 
         <direction-type 
             <words default-y=45.0 font-weight=bold justify=left charData=slow>>>]

    >>> mm = tempo.MetronomeMark("slow", 40, duration.Duration(quarterLength=1.5))
    >>> mxList = musicxml.toMxObjects.tempoIndicationToMx(mm)
    >>> mxList
    [<direction <direction-type <metronome parentheses=no <beat-unit charData=quarter> <beat-unit-dot > <per-minute charData=40>>> <sound tempo=60.0>>, <direction <direction-type <words default-y=45.0 font-weight=bold justify=left charData=slow>>>]

    '''
    # if writing just a sound tag, place an empty words tag in a direction type and then follow with sound declaration

    # storing lists to accommodate metric modulations
    durs = [] # duration objects
    numbers = [] # tempi
    hideNumericalMetro = False # if numbers implicit, hide metronome numbers
    hideNumber = [] # hide the number after equal, e.g., quarter=120, hide 120
    # store the last value necessary as a sounding tag in bpm
    soundingQuarterBPM = False
    if 'MetronomeMark' in ti.classes:
        # will not show a number of implicit
        if ti.numberImplicit or ti.number is None:
            #environLocal.printDebug(['found numberImplict', ti.numberImplicit])
            hideNumericalMetro = True
        else:
            durs.append(ti.referent)
            numbers.append(ti.number)
            hideNumber.append(False)
        # determine number sounding; first, get from numberSounding, then
        # number (if implicit, that is fine); get in terms of quarter bpm
        soundingQuarterBPM = ti.getQuarterBPM()

    elif 'MetricModulation' in ti.classes:
        # may need to reverse order if classical style or otherwise
        # may want to show first number
        hideNumericalMetro = False # must show for metric modulation
        for sub in [ti.oldMetronome, ti.newMetronome]:
            hideNumber.append(True) # cannot show numbers in a metric modulation
            durs.append(sub.referent)
            numbers.append(sub.number)
        # soundingQuarterBPM should be obtained from the last MetronomeMark
        soundingQuarterBPM = ti.newMetronome.getQuarterBPM()

        #environLocal.printDebug(['found metric modulation', ti, durs, numbers])

    mxComponents = []
    for i, d in enumerate(durs):
        # charData of BeatUnit is the type string
        mxSub = mxObjects.BeatUnit(typeToMusicXMLType(d.type))
        mxComponents.append(mxSub)
        for i in range(d.dots):
            mxComponents.append(mxObjects.BeatUnitDot())
        if len(numbers) > 0:
            if not hideNumber[i]:
                mxComponents.append(mxObjects.PerMinute(numbers[0]))

    #environLocal.printDebug(['mxComponents', mxComponents])

    # store all accumulated mxDirection objects
    accumulatedDirections = []

    if not hideNumericalMetro:
        mxMetro = mxObjects.Metronome()
        # all have this attribute
        if ti.parentheses:
            mxMetro.set('parentheses', 'yes') # only attribute
        else:
            mxMetro.set('parentheses', 'no') # only attribute        
        # simply add sub to components of mxMetro
        # if there are no components this may only be a text indication
        for mxSub in mxComponents:
            mxMetro.componentList.append(mxSub)

        # wrap in mxDirection
        mxDirectionType = mxObjects.DirectionType()
        mxDirectionType.append(mxMetro)
        mxDirection = mxObjects.Direction()
        mxDirection.append(mxDirectionType)

        # sound tag goes last, in mxDirection, not mxDirectionType
        if soundingQuarterBPM is not None:
            mxSound = mxObjects.Sound()
            mxSound.set('tempo', soundingQuarterBPM)
            mxDirection.append(mxSound)

        accumulatedDirections.append(mxDirection)

    # if there is an explicit text entry, add to list of mxObjets
    # for now, only getting text expressions for non-metric mods
    if 'MetronomeMark' in ti.classes:
        if ti.getTextExpression(returnImplicit=False) is not None:
            mxDirection = textExpressionToMx(
                          ti.getTextExpression(returnImplicit=False))
            accumulatedDirections.append(mxDirection)

    return accumulatedDirections


def repeatToMx(r):
    '''
    
    >>> b = bar.Repeat(direction='end')
    >>> mxBarline = musicxml.toMxObjects.repeatToMx(b)
    >>> mxBarline.get('barStyle')
    'light-heavy'
    '''
    mxBarline = mxObjects.Barline()
    if r.style is not None:
        mxBarline.set('barStyle', r.musicXMLBarStyle)

    if r.location is not None:
        mxBarline.set('location', r.location)

    mxRepeat = mxObjects.Repeat()
    if r.direction == 'start':
        mxRepeat.set('direction', 'forward')
    elif r.direction == 'end':
        mxRepeat.set('direction', 'backward')
#         elif self.direction == 'bidirectional':
#             environLocal.printDebug(['skipping bi-directional repeat'])
    else:
        raise bar.BarException('cannot handle direction format:', r.direction)

    if r.times != None:
        mxRepeat.set('times', r.times)

    mxBarline.set('repeatObj', mxRepeat)
    return mxBarline


def barlineToMx(barObject):
    '''
    Translate a music21 bar.Bar object to an mxBar
    while making two substitutions: double -> light-light
    and final -> light-heavy as shown below.
    
    
    >>> b = bar.Barline('final')
    >>> mxBarline = musicxml.toMxObjects.barlineToMx(b)
    >>> mxBarline.get('barStyle')
    'light-heavy'
    '''
    mxBarline = mxObjects.Barline()
    mxBarline.set('barStyle', barObject.musicXMLBarStyle)
    if barObject.location is not None:
        mxBarline.set('location', barObject.location)
    return mxBarline


    
#-------------------------------------------------------------------------------
def durationToMxGrace(d, mxNoteList):
    '''
    Given a music21 duration and a list of mxNotes, edit the 
    mxNotes in place if the duration is a GraceDuration
    '''
    if d.isGrace: # this is a class attribute, not a property/method
        for mxNote in mxNoteList:
            mxGrace = mxObjects.Grace()
            mxGrace.set('stealTimePrevious', d.stealTimePrevious)
            mxGrace.set('stealTimeFollowing', d.stealTimeFollowing)
            if d.slash:
                mxGrace.set('slash', 'yes')
            else:
                mxGrace.set('slash', 'no')
            # need to convert from duration to divisions
            #mxGrace.set('makeTime', d.makeTime)
            mxNote.graceObj = mxGrace


#-------------------------------------------------------------------------------
# Pitch and pitch components

def accidentalToMx(a):
    '''
    returns a `musicxml` :class:`~music21.musicxml.mxObjects.Accidental` object
    from a music21 `pitch` :class:`~music21.pitch.Accidental` object
    
    
    >>> a = pitch.Accidental()
    >>> a.set('half-sharp')
    >>> a.alter == .5
    True
    >>> mxAccidental = musicxml.toMxObjects.accidentalToMx(a)
    >>> mxAccidental.get('content')
    'quarter-sharp'
    '''
    if a.name == "half-sharp": 
        mxName = "quarter-sharp"
    elif a.name == "one-and-a-half-sharp": 
        mxName = "three-quarters-sharp"
    elif a.name == "half-flat": 
        mxName = "quarter-flat"
    elif a.name == "one-and-a-half-flat": 
        mxName = "three-quarters-flat"
    else: # all others are the same
        mxName = a.name

    mxAccidental = mxObjects.Accidental()
# need to remove display in this case and return None
#         if self.displayStatus == False:
#             pass
    mxAccidental.set('charData', mxName)
    return mxAccidental


def pitchToMx(p):
    '''
    Returns a musicxml.mxObjects.Note() object

    
    >>> a = pitch.Pitch('g#4')
    >>> c = musicxml.toMxObjects.pitchToMx(a)
    >>> c.get('pitch').get('step')
    'G'
    '''
    mxPitch = mxObjects.Pitch()
    mxPitch.set('step', p.step)
    if p.accidental is not None:
        # need to use integers when possible in order to support
        # xml readers that force alter to be an integer
        mxPitch.set('alter', common.numToIntOrFloat(p.accidental.alter))
    mxPitch.set('octave', p.implicitOctave)

    mxNote = mxObjects.Note()
    mxNote.setDefaults() # note: this sets the duration to a default value
    mxNote.set('pitch', mxPitch)

    if (p.accidental is not None and
        p.accidental.displayStatus in [True, None]):
        mxAccidental = accidentalToMx(p.accidental)
        mxNote.set('accidental', mxAccidental)
    # should this also return an xml accidental object
    return mxNote # return element object


#-------------------------------------------------------------------------------
# Ties

def tieToMx(t):
    '''
    Translate a music21 :class:`~music21.tie.Tie` object to
    MusicXML :class:`~music21.musicxml.mxObjects.Tie` (representing sound) and
    :class:`~music21.musicxml.mxObjects.Tied` (representing notation)
    objects as two component lists.

    '''
    mxTieList = []
    mxTie = mxObjects.Tie()
    if t.type == 'continue':
        musicxmlTieType = 'stop'
    else:
        musicxmlTieType = t.type
    mxTie.set('type', musicxmlTieType) # start, stop
    mxTieList.append(mxTie) # goes on mxNote.tieList

    if t.type == 'continue':
        mxTie = mxObjects.Tie()
        mxTie.set('type', 'start')
        mxTieList.append(mxTie) # goes on mxNote.tieList

    mxTiedList = []
    if t.style != 'hidden': # tie style -- dotted and dashed not supported yet        
        mxTied = mxObjects.Tied()
        mxTied.set('type', musicxmlTieType) # start, stop
        mxTiedList.append(mxTied) # goes on mxNote.notationsObj list
    if t.type == 'continue':
        if t.style != 'hidden': # tie style -- dotted and dashed not supported yet        
            mxTied = mxObjects.Tied()
            mxTied.set('type', 'start')
            mxTiedList.append(mxTied)

    #environLocal.printDebug(['mxTieList', mxTieList])
    return mxTieList, mxTiedList



#-------------------------------------------------------------------------------
# Lyrics

def lyricToMx(l):
    '''
    Translate a music21 :class:`~music21.note.Lyric` object 
    to a MusicXML :class:`~music21.musicxml.Lyric` object.
    '''
    mxLyric = mxObjects.Lyric()
    mxLyric.set('text', l.text)
    # The next line may or may not be the best behavior. Saving the identifier in the case where it differs from the number may change the lyric ordering. I'm not sure yet.
    mxLyric.set('number', l.identifier)      # Before identifier property added to note.Lyric() ---> mxLyric.set('number', l.number)
    # musicxl  expects begin, middle, end, as well as single
    mxLyric.set('syllabic', l.syllabic)
    return mxLyric



#-------------------------------------------------------------------------------
# Durations

def typeToMusicXMLType(value):
    '''Convert a music21 type to a MusicXML type.

    
    >>> musicxml.toMxObjects.typeToMusicXMLType('longa')
    'long'
    >>> musicxml.toMxObjects.typeToMusicXMLType('quarter')
    'quarter'
    '''
    # MusicXML uses long instead of longa
    if value == 'longa': 
        return 'long'
    elif value == '2048th':
        raise ToMxObjectsException('Cannot convert "2048th" duration to MusicXML (too short).')
    else:
        return value


def durationToMx(d):
    '''
    Translate a music21 :class:`~music21.duration.Duration` object to a list
    of one or more MusicXML :class:`~music21.musicxml.mxObjects.Note` objects.

    All rhythms and ties necessary in the MusicXML Notes are configured. The returned mxNote objects are incompletely specified, lacking full representation and information on pitch, etc.

    
    >>> a = duration.Duration()
    >>> a.quarterLength = 3
    >>> b = musicxml.toMxObjects.durationToMx(a)
    >>> len(b) == 1
    True
    >>> isinstance(b[0], musicxml.mxObjects.Note)
    True

    >>> a = duration.Duration()
    >>> a.quarterLength = .33333333
    >>> b = musicxml.toMxObjects.durationToMx(a)
    >>> len(b) == 1
    True
    >>> isinstance(b[0], musicxml.mxObjects.Note)
    True

    >>> a = duration.Duration()
    >>> a.quarterLength = .625
    >>> b = musicxml.toMxObjects.durationToMx(a)
    >>> len(b) == 2
    True
    >>> isinstance(b[0], musicxml.mxObjects.Note)
    True

    >>> a = duration.Duration()
    >>> a.type = 'half'
    >>> a.dotGroups = (1,1)
    >>> b = musicxml.toMxObjects.durationToMx(a)
    >>> len(b) == 2
    True
    >>> isinstance(b[0], musicxml.mxObjects.Note)
    True
    '''
    post = [] # rename mxNoteList for consistencuy

    #environLocal.printDebug(['in durationToMx', d, d.quarterLength, 'isGrace', d.isGrace])

    if d.quarterLength >0 and d.dotGroups is not None and len(d.dotGroups) > 1:
        d = d.splitDotGroups()
    # most common case...
    # a grace is not linked, but still needs to be processed as a grace
    if (d.linked is True or len(d.components) > 1 or
        (len(d.components) > 1 and d.isGrace)):
        for dur in d.components:
            mxDivisions = int(defaults.divisionsPerQuarter *
                              dur.quarterLength)
            mxType = typeToMusicXMLType(dur.type)
            # check if name is not in collection of MusicXML names, which does 
            # not have maxima, etc.
            mxDotList = []
            # only presently looking at first dot group
            # also assuming that these are integer values
            # need to handle fractional dots differently
            for i in range(int(dur.dots)):
                # only need to create object
                mxDotList.append(mxObjects.Dot())
            mxNote = mxObjects.Note()
            if not d.isGrace:
                mxNote.set('duration', mxDivisions)
            mxNote.set('type', mxType)
            mxNote.set('dotList', mxDotList)
            post.append(mxNote)
    else: # simple duration that is unlinked
        mxDivisions = int(defaults.divisionsPerQuarter *
                          d.quarterLength)
        mxType = typeToMusicXMLType(d.type)
        # check if name is not in collection of MusicXML names, which does 
        # not have maxima, etc.
        mxDotList = []
        # only presently looking at first dot group
        # also assuming that these are integer values
        # need to handle fractional dots differently
        for i in range(int(d.dots)):
            # only need to create object
            mxDotList.append(mxObjects.Dot())
        mxNote = mxObjects.Note()
        if not d.isGrace:
            mxNote.set('duration', mxDivisions)
        mxNote.set('type', mxType)
        mxNote.set('dotList', mxDotList)
        post.append(mxNote)

    # second pass for ties if more than one components
    # this assumes that all component are tied
    for i in range(len(d.components)):
        dur = d.components[i]
        mxNote = post[i]
        # contains Tuplet, Dynamcs, Articulations
        mxNotations = mxObjects.Notations()
        # only need ties if more than one component
        mxTieList = []
        if len(d.components) > 1:
            if i == 0:
                mxTie = mxObjects.Tie()
                mxTie.set('type', 'start') # start, stop
                mxTieList.append(mxTie)
                mxTied = mxObjects.Tied()
                mxTied.set('type', 'start')
                mxNotations.append(mxTied)
            elif i == len(d.components) - 1: #end 
                mxTie = mxObjects.Tie()
                mxTie.set('type', 'stop') # start, stop
                mxTieList.append(mxTie)
                mxTied = mxObjects.Tied()
                mxTied.set('type', 'stop')
                mxNotations.append(mxTied)
            else: # continuation
                for tieType in ['stop', 'start']:
                    mxTie = mxObjects.Tie()
                    mxTie.set('type', tieType) # start, stop
                    mxTieList.append(mxTie)
                    mxTied = mxObjects.Tied()
                    mxTied.set('type', tieType)
                    mxNotations.append(mxTied)
        if len(d.components) > 1:
            mxNote.set('tieList', mxTieList)
        if len(d.tuplets) > 0:
            # only getting first tuplet here
            mxTimeModification, mxTupletList = tupletToMx(d.tuplets[0])
            mxNote.set('timemodification', mxTimeModification)
            if mxTupletList != []:
                mxNotations.componentList += mxTupletList
        # add notations to mxNote
        mxNote.set('notations', mxNotations)

    # third pass: see if these are graces; will edit in place if necessary
    durationToMxGrace(d, post)

#     if d.isGrace: # this is a class attribute, not a property/method
#         for mxNote in post:
#             # TODO: configure this object with per-duration configurations
#             mxGrace = mxObjects.Grace()
#             mxNote.graceObj = mxGrace
#             #environLocal.printDebug(['final mxNote with mxGrace duration', mxNote.get('duration')])
    return post # a list of mxNotes

def tupletToMx(tuplet):
    '''
    return a tuple of mxTimeModification and mxTuplet from
    a :class:`~music21.duration.Tuplet` object
    
    
    >>> a = duration.Tuplet(6, 4, "16th")
    >>> a.type = 'start'
    >>> a.bracket = True
    >>> b, c = musicxml.toMxObjects.tupletToMx(a)
    >>> b
    <time-modification actual-notes=6 normal-notes=4 normal-type=16th>
    >>> c
    [<tuplet bracket=yes placement=above type=start>]
    '''
    mxTimeModification = mxObjects.TimeModification()
    mxTimeModification.set('actual-notes', int(tuplet.numberNotesActual))
    mxTimeModification.set('normal-notes', int(tuplet.numberNotesNormal))
    mxTimeModification.set('normal-type', tuplet.durationNormal.type)
    if tuplet.durationNormal.dots > 0: # only one dot supported...
        mxTimeModification.set('normal-dot', True)
        if tuplet.durationNormal.dots > 1:
            environLocal.warn("Converting a tuplet based on notes with %d dots to a single dotted tuplet; musicxml does not support these tuplets" % tuplet.durationNormal.dots)
    # need to permit a tuplet type that is startStop, that
    # create two mxTuplet objects, one for starting and one
    # for stopping
    # can have type 'start' with bracket 'no'
    mxTupletList = []
    if tuplet.type not in [None, '']:
        if tuplet.type not in ['start', 'stop', 'startStop']:
            raise ToMxObjectsException("Cannot create music XML from a tuplet of type " + tuplet.type)

        if tuplet.type == 'startStop': # need two musicxml
            localType = ['start', 'stop']
        else:
            localType = [tuplet.type] # place in list

        for tupletType in localType:
            mxTuplet = mxObjects.Tuplet()
            # start/stop; needs to bet set by group
            mxTuplet.set('type', tupletType) 
            # only provide other parameters if this tuplet is a start
            if tupletType == 'start':
                mxTuplet.set('bracket', mxObjects.booleanToYesNo(
                             tuplet.bracket)) 
                mxTuplet.set('placement', tuplet.placement)
                if tuplet.tupletActualShow == 'none':
                    mxTuplet.set('show-number', 'none') 
            # append each
            mxTupletList.append(mxTuplet)

    return mxTimeModification, mxTupletList

#-------------------------------------------------------------------------------
# Meters

def timeSignatureToMx(ts):
    '''
    Returns a single mxTime object from a meter.TimeSignature object.

    Compound meters are represented as multiple pairs of beat
    and beat-type elements

    
    >>> a = meter.TimeSignature('3/4')
    >>> b = musicxml.toMxObjects.timeSignatureToMx(a)
    >>> b
    <time <beats charData=3> <beat-type charData=4>>
    
    >>> a = meter.TimeSignature('3/4+2/4')
    >>> b = musicxml.toMxObjects.timeSignatureToMx(a)
    >>> b
    <time <beats charData=3> <beat-type charData=4> <beats charData=2> <beat-type charData=4>>
    
    >>> a.setDisplay('5/4')
    >>> b = musicxml.toMxObjects.timeSignatureToMx(a)
    >>> b
    <time <beats charData=5> <beat-type charData=4>>
    '''
    #mxTimeList = []
    mxTime = mxObjects.Time()
    # always get a flat version to display any subivisions created
    fList = [(mt.numerator, mt.denominator) for mt in ts.displaySequence.flat._partition]
    if ts.summedNumerator:
        # this will try to reduce any common denominators into 
        # a common group
        fList = meter.fractionToSlashMixed(fList)

    for n, d in fList:
        mxBeats = mxObjects.Beats(n)
        mxBeatType = mxObjects.BeatType(d)
        mxTime.componentList.append(mxBeats)
        mxTime.componentList.append(mxBeatType)

    # can set this to common when necessary
    mxTime.set('symbol', None)
    # for declaring no time signature present
    mxTime.set('senza-misura', None)
    #mxTimeList.append(mxTime)
    #return mxTimeList
    return mxTime

#--------------------------------------------------------
# Key/KeySignatures

def keySignatureToMx(keySignature):
    '''
    Returns a musicxml.mxObjects.Key object from a music21
    key.KeySignature or key.Key object
       
    
    >>> ks = key.KeySignature(-3)
    >>> ks
    <music21.key.KeySignature of 3 flats>
    >>> mxKey = musicxml.toMxObjects.keySignatureToMx(ks)
    >>> mxKey.get('fifths')
    -3
    '''
    mxKey = mxObjects.Key()
    mxKey.set('fifths', keySignature.sharps)
    if keySignature.mode is not None:
        mxKey.set('mode', keySignature.mode)
    return mxKey


#--------------------------------------------------------
# clefs

def clefToMxClef(clefObj):
    '''
    Given a music21 Clef object, return a MusicXML Clef 
    object.

    
    >>> gc = clef.GClef()
    >>> gc
    <music21.clef.GClef>
    >>> mxc = musicxml.toMxObjects.clefToMxClef(gc)
    >>> mxc.get('sign')
    'G'

    >>> b = clef.Treble8vbClef()
    >>> b.octaveChange
    -1
    >>> mxc2 = musicxml.toMxObjects.clefToMxClef(b)
    >>> mxc2.get('sign')
    'G'
    >>> mxc2.get('clefOctaveChange')
    -1

    >>> pc = clef.PercussionClef()
    >>> mxc3 = musicxml.toMxObjects.clefToMxClef(pc)
    >>> mxc3.get('sign')
    'percussion'
    >>> mxc3.get('line') is None
    True
    
    
    Clefs without signs get exported as G clefs with a warning
    
    >>> generic = clef.Clef()
    >>> mxc4 = musicxml.toMxObjects.clefToMxClef(generic)
    Clef with no .sign exported; setting as a G clef
    >>> mxc4.get('sign')
    'G'
    >>> mxc4.get('line') is None
    True 
    '''
    mxClef = mxObjects.Clef()
    sign = clefObj.sign
    if sign is None:
        print("Clef with no .sign exported; setting as a G clef")
        sign = 'G'
    
    mxClef.set('sign', sign) # we use musicxml signs internally, so no problem...
    if clefObj.line is not None:
        mxClef.set('line', clefObj.line)
    if clefObj.octaveChange != 0:
        mxClef.set('clefOctaveChange', clefObj.octaveChange)
    return mxClef

#-------------------------------------------------------------------------------
# Dynamics

def dynamicToMx(d):
    '''
    Return an mx direction
    returns a musicxml.mxObjects.Direction object

    
    >>> a = dynamics.Dynamic('ppp')
    >>> print('%.2f' % a.volumeScalar)
    0.15
    >>> a._positionRelativeY = -10
    >>> b = musicxml.toMxObjects.dynamicToMx(a)
    >>> b[0][0][0].get('tag')
    'ppp'
    >>> b[1].get('tag')
    'sound'
    >>> b[1].get('dynamics')
    '19'

    '''
    mxDynamicMark = mxObjects.DynamicMark(d.value)
    mxDynamics = mxObjects.Dynamics()
    for src, dst in [(d._positionDefaultX, 'default-x'),
                     (d._positionDefaultY, 'default-y'),
                     (d._positionRelativeX, 'relative-x'),
                     (d._positionRelativeY, 'relative-y')]:
        if src is not None:
            mxDynamics.set(dst, src)
    mxDynamics.append(mxDynamicMark) # store on component list
    mxDirectionType = mxObjects.DirectionType()
    mxDirectionType.append(mxDynamics)
    mxDirection = mxObjects.Direction()
    mxDirection.append(mxDirectionType)

    # sound...
    vS = d.volumeScalar
    if vS is not None:
        mxSound = mxObjects.Sound()
        dynamicVolume = int(vS * 127)
        mxSound.set('dynamics', str(dynamicVolume))
        mxDirection.append(mxSound)

    mxDirection.set('placement', d._positionPlacement)
    return mxDirection


def textExpressionToMx(te):
    '''Convert a TextExpression to a MusicXML mxDirection type.
    returns a musicxml.mxObjects.Direction object
    '''
    mxWords = mxObjects.Words(te.content)
    for src, dst in [#(te._positionDefaultX, 'default-x'), 
                     (te.positionVertical, 'default-y'),
#                      (te._positionRelativeX, 'relative-x'),
#                      (te._positionRelativeY, 'relative-y')]:
                      (te.enclosure, 'enclosure'),
                      (te.justify, 'justify'),
                      (te.size, 'font-size'),
                      (te.letterSpacing, 'letter-spacing'),
                    ]:
        if src is not None:
            mxWords.set(dst, src)
    if te.style == 'bolditalic':
        mxWords.set('font-style', 'italic')
        mxWords.set('font-weight', 'bold')
    elif te.style == 'italic':
        mxWords.set('font-style', 'italic')
    elif te.style == 'bold':
        mxWords.set('font-weight', 'bold')

    mxDirectionType = mxObjects.DirectionType()
    mxDirectionType.append(mxWords)

    mxDirection = mxObjects.Direction()
    mxDirection.append(mxDirectionType)
    # this parameter does not seem to do anything with text expressions
    #mxDirection.set('placement', d._positionPlacement)
    return mxDirection


def codaToMx(rm):
    '''
    Returns a musicxml.mxObjects.Direction object with a musicxml.mxObjects.Coda mark in it
    '''
    if rm.useSymbol:
        mxCoda = mxObjects.Coda()
        for src, dst in [(rm._positionDefaultX, 'default-x'),
                         (rm._positionDefaultY, 'default-y'),
                         (rm._positionRelativeX, 'relative-x'),
                         (rm._positionRelativeY, 'relative-y')]:
            if src is not None:
                mxCoda.set(dst, src)
        mxDirectionType = mxObjects.DirectionType()
        mxDirectionType.append(mxCoda)
        mxDirection = mxObjects.Direction()
        mxDirection.append(mxDirectionType)
        mxDirection.set('placement', rm._positionPlacement)
        return mxDirection
    else:
        # simply get the text expression version and convert
        # returns an mxDirection
        return textExpressionToMx(rm.getTextExpression())

def segnoToMx(rm):
    '''
    Returns a musicxml.mxObjects.Direction object with a musicxml.mxObjects.Segno mark in it
    '''
    mxSegno = mxObjects.Segno()
    for src, dst in [(rm._positionDefaultX, 'default-x'),
                     (rm._positionDefaultY, 'default-y'),
                     (rm._positionRelativeX, 'relative-x'),
                     (rm._positionRelativeY, 'relative-y')]:
        if src is not None:
            mxSegno.set(dst, src)
    mxDirectionType = mxObjects.DirectionType()
    mxDirectionType.append(mxSegno)
    mxDirection = mxObjects.Direction()
    mxDirection.append(mxDirectionType)
    mxDirection.set('placement', rm._positionPlacement)
    return mxDirection

#-------------------------------------------------------------------------------
# Harmony


def chordSymbolToMx(cs):
    '''
    Convert a ChordSymbol object to an mxHarmony object.
       
    >>> cs = harmony.ChordSymbol()
    >>> cs.root('E-')
    >>> cs.bass('B-')
    >>> cs.inversion(2, transposeOnSet = False)
    >>> cs.romanNumeral = 'I64'
    >>> cs.chordKind = 'major'
    >>> cs.chordKindStr = 'M'
    >>> cs
    <music21.harmony.ChordSymbol E-/B->
    >>> mxHarmony = musicxml.toMxObjects.chordSymbolToMx(cs)
    >>> mxHarmony
    <harmony <root root-step=E root-alter=-1> function=I64 <kind text=M charData=major> inversion=2 <bass bass-step=B bass-alter=-1>>
 
    >>> hd = harmony.ChordStepModification()
    >>> hd.modType = 'alter'
    >>> hd.interval = -1
    >>> hd.degree = 3
    >>> cs.addChordStepModification(hd)
 
    >>> mxHarmony = musicxml.toMxObjects.chordSymbolToMx(cs)
    >>> mxHarmony
    <harmony <root root-step=E root-alter=-1> function=I64 <kind text=M charData=major> inversion=2 <bass bass-step=B bass-alter=-1> <degree <degree-value charData=3> <degree-alter charData=-1> <degree-type charData=alter>>>

    Test altered chords:
    
    Is this correct?

    >>> f = harmony.ChordSymbol('F sus add 9')
    >>> mxF = musicxml.toMxObjects.chordSymbolToMx(f)
    >>> mxF
    <harmony <root root-step=G> <kind text= charData=suspended-fourth> inversion=3 <bass bass-step=F> <degree <degree-value charData=9> <degree-alter > <degree-type charData=add>>>
    
    MusicXML uses "dominant" for "dominant-seventh" so check aliases back...

    >>> dom7 = harmony.ChordSymbol('C7')
    >>> dom7.chordKind
    'dominant-seventh'
    >>> mxF = musicxml.toMxObjects.chordSymbolToMx(dom7)
    >>> mxF
    <harmony <root root-step=C> <kind text= charData=dominant> inversion=0>    
    '''
    from music21 import harmony
    mxHarmony = mxObjects.Harmony()

    mxKind = mxObjects.Kind()
    cKind = cs.chordKind
    for xmlAlias in harmony.CHORD_ALIASES:
        if harmony.CHORD_ALIASES[xmlAlias] == cKind:
            cKind = xmlAlias
    mxKind.set('charData', cKind)
    mxKind.set('text', cs.chordKindStr)
    mxHarmony.set('kind', mxKind)

    # can assign None to these if None
    mxHarmony.set('inversion', cs.inversion())
    if cs._roman is not None:
        mxHarmony.set('function', cs.romanNumeral.figure)

    if cs.root(find=False) is not None:
        mxRoot = mxObjects.Root()
        mxRoot.set('rootStep', cs.root().step)
        if cs.root().accidental is not None:
            mxRoot.set('rootAlter', int(cs.root().accidental.alter))
        mxHarmony.set('root', mxRoot)

    if cs.bass(find=False) != cs.root(find=False) and cs.bass(find=False) is not None:
        mxBass = mxObjects.Bass()
        mxBass.set('bassStep', cs.bass().step)
        if cs.bass().accidental is not None:
            mxBass.set('bassAlter', int(cs.bass().accidental.alter))
        mxHarmony.set('bass', mxBass)

    if len(cs.getChordStepModifications()) > 0:
        mxDegree = mxObjects.Degree()
        for hd in cs.getChordStepModifications():
            # types should be compatible
            mxDegreeValue = mxObjects.DegreeValue()
            mxDegreeValue.set('charData', hd.degree)
            mxDegree.componentList.append(mxDegreeValue)
            mxDegreeAlter = mxObjects.DegreeAlter()
            if hd.interval is not None:
                # will return -1 for '-a1'
                mxDegreeAlter.set('charData', hd.interval.chromatic.directed)
            mxDegree.componentList.append(mxDegreeAlter)

            mxDegreeType = mxObjects.DegreeType()
            mxDegreeType.set('charData', hd.modType)
            mxDegree.componentList.append(mxDegreeType)

        mxHarmony.set('degree', mxDegree)
    # degree only thing left
    return mxHarmony

#-------------------------------------------------------------------------------
# Instruments


def instrumentToMx(i):
    '''
    
    >>> i = instrument.Celesta()
    >>> mxScorePart = musicxml.toMxObjects.instrumentToMx(i)
    >>> len(mxScorePart.scoreInstrumentList)
    1
    >>> mxScorePart.scoreInstrumentList[0].instrumentName
    'Celesta'
    >>> mxScorePart.midiInstrumentList[0].midiProgram
    9
    '''
    mxScorePart = mxObjects.ScorePart()

    # get a random id if None set
    if i.partId == None:
        i.partIdRandomize()

    if i.instrumentId == None:
        i.instrumentIdRandomize()

    # note: this is id, not partId!
    mxScorePart.set('id', i.partId)

    if i.partName is not None:
        mxScorePart.partName = i.partName
    elif i.partName is None: # get default, as required
        mxScorePart.partName = defaults.partName

    if i.partAbbreviation is not None:
        mxScorePart.partAbbreviation = i.partAbbreviation

    if i.instrumentName is not None or i.instrumentAbbreviation is not None:
        mxScoreInstrument = mxObjects.ScoreInstrument()
        # set id to same as part for now
        mxScoreInstrument.set('id', i.instrumentId)
        # can set these to None
        mxScoreInstrument.instrumentName = i.instrumentName
        mxScoreInstrument.instrumentAbbreviation = i.instrumentAbbreviation
        # add to mxScorePart
        mxScorePart.scoreInstrumentList.append(mxScoreInstrument)

    if i.midiProgram is not None:
        mxMIDIInstrument = mxObjects.MIDIInstrument()
        mxMIDIInstrument.set('id', i.instrumentId)
        # shift to start from 1
        mxMIDIInstrument.midiProgram = i.midiProgram + 1

        if i.midiChannel == None:
            # TODO: need to allocate channels from a higher level
            i.autoAssignMidiChannel()
        mxMIDIInstrument.midiChannel = i.midiChannel + 1
        # add to mxScorePart
        mxScorePart.midiInstrumentList.append(mxMIDIInstrument)

    return mxScorePart


#-------------------------------------------------------------------------------
# unified processors for Chords and Notes

def spannersToMx(target, mxNoteList, mxDirectionPre, mxDirectionPost,
    spannerBundle):
    '''
    Convenience routine to create and add MusicXML objects from music21 objects provided 
    as a target and as a SpannerBundle. 

    The `target` parameter here may be music21 Note, Rest, or Chord.
    This may edit the mxNoteList and direction lists in place, and thus returns None.
    
    mxNoteList is a list of <mxNote> objects that represent the note or Chord (multiple for chords)
    
    some spanner produce direction tags, and sometimes these need
    to go before or after the notes of this element, hence the mxDirectionPre and mxDirectionPost lists
    
    spannerBundle is a bundle that has already been created by getBySpannedElement, so not
    a big deal to iterate over it.
    
    
    TODO: Show a test...
    '''
    if spannerBundle is None or len(spannerBundle) == 0:
        return

    # already filtered for just the spanner that have this note as
    # a component
    #environLocal.printDebug(['noteToMxNotes()', 'len(spannerBundle)', len(spannerBundle) ])

    for su in spannerBundle.getByClass('Slur'):
        mxSlur = mxObjects.Slur()
        mxSlur.set('number', su.idLocal)
        mxSlur.set('placement', su.placement)
        # is this note first in this spanner?
        if su.isFirst(target):
            mxSlur.set('type', 'start')
        elif su.isLast(target):
            mxSlur.set('type', 'stop')
        else:
            # this may not always be an error
            #environLocal.printDebug(['spanner w/ a component that is neither a start nor an end.', su, target])
            continue
        mxNoteList[0].notationsObj.componentList.append(mxSlur)

    for su in spannerBundle.getByClass('TremoloSpanner'):
        mxTrem = mxObjects.Tremolo()
        mxTrem.charData = str(su.numberOfMarks)
        if su.isFirst(target):
            mxTrem.set('type', 'start')
        elif su.isLast(target):
            mxTrem.set('type', 'stop')
        else:
            # this is always an error for tremolos
            environLocal.printDebug(['spanner w/ a component that is neither a start nor an end.', su, target])
        mxOrnamentsList = mxNoteList[0].notationsObj.getOrnaments()
        if mxOrnamentsList == []: # need to create ornaments obj
            mxOrnaments = mxObjects.Ornaments()
            mxNoteList[0].notationsObj.componentList.append(mxOrnaments)
            mxOrnamentsList = [mxOrnaments] # emulate returned obj

        mxOrnamentsList[0].append(mxTrem)
        

    for su in spannerBundle.getByClass('TrillExtension'):
        mxWavyLine = mxObjects.WavyLine()
        mxWavyLine.set('number', su.idLocal)
        mxWavyLine.set('placement', su.placement)
        # is this note first in this spanner?
        if su.isFirst(target):
            mxWavyLine.set('type', 'start')
        elif su.isLast(target):
            mxWavyLine.set('type', 'stop')
        else:
            # this may not always be an error
            environLocal.printDebug(['spanner w/ a component that is neither a start nor an end.', su, target])
        mxOrnamentsList = mxNoteList[0].notationsObj.getOrnaments()
        if mxOrnamentsList == []: # need to create ornaments obj
            mxOrnaments = mxObjects.Ornaments()
            mxNoteList[0].notationsObj.componentList.append(mxOrnaments)
            mxOrnamentsList = [mxOrnaments] # emulate returned obj
        mxOrnamentsList[0].append(mxWavyLine) # add to first
        #environLocal.printDebug(['wl', 'mxOrnamentsList', mxOrnamentsList ])

    for su in spannerBundle.getByClass('Glissando'):
        mxGlissando = mxObjects.Glissando()
        mxGlissando.set('number', su.idLocal)
        mxGlissando.set('line-type', su.lineType)
        # is this note first in this spanner?
        if su.isFirst(target):
            mxGlissando.set('charData', su.label)
            mxGlissando.set('type', 'start')
        elif su.isLast(target):
            mxGlissando.set('type', 'stop')
        else:
            # this may not always be an error
            environLocal.printDebug(['spanner w/ a component that is neither a start nor an end.', su, target])
        mxNoteList[0].notationsObj.append(mxGlissando) # add to first
        #environLocal.printDebug(['gliss', 'notationsObj', mxNoteList[0].notationsObj])

    for su in spannerBundle.getByClass('Ottava'):
        if len(su) == 1: # have a one element wedge
            proc = ['first', 'last']
        else:
            if su.isFirst(target):
                proc = ['first']
            elif su.isLast(target):
                proc = ['last']
            else:
                proc = []
        for posSub in proc:
            mxOctaveShift = mxObjects.OctaveShift()
            mxOctaveShift.set('number', su.idLocal)
            # is this note first in this spanner?
            if posSub == 'first':
                pmtrs = su.getStartParameters()
                mxOctaveShift.set('type', pmtrs['type'])
                mxOctaveShift.set('size', pmtrs['size'])
            elif posSub == 'last':
                pmtrs = su.getEndParameters()
                mxOctaveShift.set('type', pmtrs['type'])
                mxOctaveShift.set('size', pmtrs['size'])
            mxDirection = mxObjects.Direction()
            mxDirection.set('placement', su.placement) # placement goes here
            mxDirectionType = mxObjects.DirectionType()
            mxDirectionType.append(mxOctaveShift)
            mxDirection.append(mxDirectionType)
            environLocal.printDebug(['os', 'mxDirection', mxDirection ])
            if posSub == 'first':
                mxDirectionPre.append(mxDirection)
            else:
                mxDirectionPost.append(mxDirection)

    # get common base class of cresc and decresc
    # may have the same note as a start and end
    for su in spannerBundle.getByClass('DynamicWedge'):
        if len(su) == 1: # have a one element wedge
            proc = ['first', 'last']
        else:
            if su.isFirst(target):
                proc = ['first']
            elif su.isLast(target):
                proc = ['last']
            else:
                proc = []

        for posSub in proc:
            mxWedge = mxObjects.Wedge()
            mxWedge.set('number', su.idLocal)
            if posSub == 'first':
                pmtrs = su.getStartParameters()
                mxWedge.set('type', pmtrs['type'])
                mxWedge.set('spread', pmtrs['spread'])
            elif posSub == 'last':
                pmtrs = su.getEndParameters()
                mxWedge.set('type', pmtrs['type'])
                mxWedge.set('spread', pmtrs['spread'])

            mxDirection = mxObjects.Direction()
            mxDirection.set('placement', su.placement) # placement goes here
            mxDirectionType = mxObjects.DirectionType()
            mxDirectionType.append(mxWedge)
            mxDirection.append(mxDirectionType)
            #environLocal.printDebug(['os', 'mxDirection', mxDirection ])
            if posSub == 'first':
                mxDirectionPre.append(mxDirection)
            else:
                mxDirectionPost.append(mxDirection)


    for su in spannerBundle.getByClass('Line'):
        if len(su) == 1: # have a one element wedge
            proc = ['first', 'last']
        else:
            if su.isFirst(target):
                proc = ['first']
            elif su.isLast(target):
                proc = ['last']
            else:
                proc = []
        for posSub in proc:
            mxBracket = mxObjects.Bracket()
            mxBracket.set('number', su.idLocal)
            mxBracket.set('line-type', su.lineType)
            if posSub == 'first':
                pmtrs = su.getStartParameters()
                mxBracket.set('type', pmtrs['type'])
                mxBracket.set('line-end', pmtrs['line-end'])
                mxBracket.set('end-length', pmtrs['end-length'])
            elif posSub == 'last':
                pmtrs = su.getEndParameters()
                mxBracket.set('type', pmtrs['type'])
                mxBracket.set('line-end', pmtrs['line-end'])
                mxBracket.set('end-length', pmtrs['end-length'])
            else:
                # this may not always be an error
                environLocal.printDebug(['spanner w/ a component that is neither a start nor an end.', su, target])
            mxDirection = mxObjects.Direction()
            mxDirection.set('placement', su.placement) # placement goes here
            mxDirectionType = mxObjects.DirectionType()
            mxDirectionType.append(mxBracket)
            mxDirection.append(mxDirectionType)
            #environLocal.printDebug(['os', 'mxDirection', mxDirection ])

            if posSub == 'first':
                mxDirectionPre.append(mxDirection)
            else:
                mxDirectionPost.append(mxDirection)

#     for su in spannerBundle.getByClass('DashedLine'):     
#         mxDashes = mxObjects.Dashes()
#         mxDashes.set('number', su.idLocal)
#         # is this note first in this spanner?
#         if su.isFirst(target):
#             mxDashes.set('type', 'start')
#         elif su.isLast(target):
#             mxDashes.set('type', 'stop')
#         else: # this may not always be an error
#             environLocal.printDebug(['spanner w/ a component that is neither a start nor an end.', su, target])
#         mxDirection = mxObjects.Direction()
#         mxDirection.set('placement', su.placement) # placement goes here
#         mxDirectionType = mxObjects.DirectionType()
#         mxDirectionType.append(mxDashes)
#         mxDirection.append(mxDirectionType)
#         environLocal.printDebug(['os', 'mxDirection', mxDirection ])
# 
#         if su.isFirst(target):
#             mxDirectionPre.append(mxDirection)
#         else:
#             mxDirectionPost.append(mxDirection)


#-------------------------------------------------------------------------------

def articulationsAndExpressionsToMx(target, mxNoteList):
    '''
    The `target` parameter is the music21 object (Note, Chord, etc.) that
    will have the articulation or expression applied.
    
    mxNoteList is a list of mxNotes to which these articulations or expressions 
    apply.  Only the first of the component notes (e.g., of a chord) get the
    articulations.
    '''
    # if we have any articulations, they only go on the first of any 
    # component notes
    mxArticulations = None # create only as needed
    mxTechnical = None # create only as needed

    for artObj in target.articulations:
        if 'TechnicalIndication' not in artObj.classes:
            if mxArticulations is None:
                mxArticulations = mxObjects.Articulations()
            mxArticulationMark = articulationToMxArticulation(artObj)
            mxArticulations.append(mxArticulationMark)
        elif 'Pizzicato' not in artObj.classes: # TechnicalIndication that is not Pizzicato
            if mxTechnical is None:
                mxTechnical = mxObjects.Technical()
            mxTechnicalMark = articulationToMxTechnical(artObj)
            mxTechnical.append(mxTechnicalMark)
        else: #pizzicato:
            mxNoteList[0].set('pizzicato', 'yes')
    
    if mxArticulations is not None and len(mxArticulations) > 0:
        mxNoteList[0].notationsObj.componentList.append(mxArticulations)

    if mxTechnical is not None and len(mxTechnical) > 0:
        mxNoteList[0].notationsObj.componentList.append(mxTechnical)


    # notations and articulations are mixed in musicxml
    for expObj in target.expressions:
        # TODO: this is relying on the presence of an MX attribute
        # to determine if it can be shown; another method should
        # be used
        #replace with calls to 
        mx = expressionToMx(expObj)
        if mx is not None:
            # some expressions must be wrapped in a musicxml ornament
            # a m21 Ornament subclass may not be the same as a musicxl  ornament
            if 'Ornament' in expObj.classes:
                ornamentsObj = mxObjects.Ornaments()
                ornamentsObj.append(mx)
                mxNoteList[0].notationsObj.componentList.append(ornamentsObj)
            else:
                mxNoteList[0].notationsObj.componentList.append(mx)


def fermataToMxFermata(fermata):
    '''
    Convert an expressions.Fermata object to a musicxml.mxObject.Fermata
    object.  Note that the default musicxml is inverted fermatas -- 
    those are what most of us think of as 'upright' fermatas
    
    >>> fermata = expressions.Fermata()
    >>> fermata.type
    'inverted'
    >>> mxFermata = musicxml.toMxObjects.fermataToMxFermata(fermata)
    >>> mxFermata.get('type')
    'inverted'
    '''
    mxFermata = mxObjects.Fermata()
    mxFermata.set('type', fermata.type)
    return mxFermata


def articulationToMxArticulation(articulationMark):
    '''
    Returns a class (mxArticulationMark) that represents the
    MusicXML structure of an articulation mark.

    
    >>> a = articulations.Accent()
    >>> a.placement = 'below'
    >>> mxArticulationMark = musicxml.toMxObjects.articulationToMxArticulation(a)
    >>> mxArticulationMark
    <accent placement=below>
    '''
    
    mappingList = {'Accent'         : 'accent',
                   'StrongAccent'   : 'strong-accent',
                   'Staccato'       : 'staccato',
                   'Staccatissimo'  : 'staccatissimo',
                   'Spiccato'       : 'spiccato',
                   'Tenuto'         : 'tenuto',
                   'DetachedLegato' : 'detached-legato',
                   'Scoop'          : 'scoop',
                   'Plop'           : 'plop',
                   'Doit'           : 'doit',
                   'Falloff'        : 'falloff',
                   'BreathMark'     : 'breath-mark',
                   'Caesura'        : 'caesura',
                   'Stress'         : 'stress',
                   'Unstress'       : 'unstress',
                   'Articulation'   : 'staccato', # WRONG, BUT NO GENERIC MARK EXISTS
                   }
    
    musicXMLArticulationName = None
    for c in articulationMark.classes:
        # go in order of classes to get most specific first...
        if c in mappingList:
            musicXMLArticulationName = mappingList[c]
            break
    if musicXMLArticulationName is None:
        raise ToMxObjectsException("Cannot translate %s to musicxml" % articulationMark)
    mxArticulationMark = mxObjects.ArticulationMark(musicXMLArticulationName)
    mxArticulationMark.set('placement', articulationMark.placement)
    #mxArticulations.append(mxArticulationMark)
    return mxArticulationMark

def articulationToMxTechnical(articulationMark):
    '''
    Returns a class (mxTechnicalMark) that represents the
    MusicXML structure of an articulation mark that is primarily a TechnicalIndication.

    
    >>> a = articulations.UpBow()
    >>> a.placement = 'below'
    >>> mxTechnicalMark = musicxml.toMxObjects.articulationToMxTechnical(a)
    >>> mxTechnicalMark
    <up-bow placement=below>
    '''
    mappingList = {'UpBow': 'up-bow',
                   'DownBow': 'down-bow',
                   'Harmonic': 'harmonic',
                   'OpenString': 'open-string',
                   'StringThumbPosition': 'thumb-position',
                   'StringFingering': 'fingering',
                   'FrettedPluck': 'pluck',
                   'DoubleTongue': 'double-tongue',
                   'TripleTongue': 'triple-tongue',
                   'Stopped': 'stopped',
                   'SnapPizzicato': 'snap-pizzicato',
                   'FretIndication': 'fret',
                   'StringIndication': 'string',
                   'HammerOn': 'hammer-on',
                   'PullOff': 'pull-off',
                   'FretBend': 'bend',
                   'FretTap': 'tap',
                   'OrganHeel': 'heel',
                   'OrganToe': 'toe',
                   'HarpFingerNails': 'fingernails',
#                   'TechnicalIndication': 'other-technical',
                   }
    
    musicXMLTechnicalName = None
    for c in articulationMark.classes:
        # go in order of classes to get most specific first...
        if c in mappingList:
            musicXMLTechnicalName = mappingList[c]
            break
    if musicXMLTechnicalName is None:
        raise ToMxObjectsException("Cannot translate technical indication %s to musicxml" % articulationMark)
    mxTechnicalMark = mxObjects.TechnicalMark(musicXMLTechnicalName)
    mxTechnicalMark.set('placement', articulationMark.placement)
    #mxArticulations.append(mxArticulationMark)
    return mxTechnicalMark


def expressionToMx(orn):
    '''
    Convert a music21 Expression (expression or ornament)
    to a musicxml object; 
    return None if no conversion is possible.
    '''
    mx = None
    if 'Shake' in orn.classes:
        mx = mxObjects.Shake()
        #mx.set('placement', orn.placement)
        #pass # not yet translating, but a subclass of Trill
    if 'Trill' in orn.classes:
        mx = mxObjects.TrillMark()
        mx.set('placement', orn.placement)
    elif 'Fermata' in orn.classes:
        mx = fermataToMxFermata(orn)
    elif 'Tremolo' in orn.classes:
        mx = mxObjects.Tremolo()
        mx.charData = orn.numberOfMarks
        mx.set('type', 'single')
    elif 'Mordent' in orn.classes:
        mx = mxObjects.Mordent()
    elif 'InvertedMordent' in orn.classes:
        mx = mxObjects.InvertedMordent()
    elif 'Turn' in orn.classes:
        mx = mxObjects.Turn()
    elif 'DelayedTurn' in orn.classes:
        mx = mxObjects.DelayedTurn()
    elif 'InvertedTurn' in orn.classes:
        mx = mxObjects.InvertedTurn()
    elif 'Schleifer' in orn.classes:
        mx = mxObjects.Schleifer()
    else:
        environLocal.printDebug(['no musicxml conversion for:', orn])

    return mx


#-------------------------------------------------------------------------------
# Chords

def chordToMx(c, spannerBundle=None):
    '''
    Returns a List of mxNotes
    Attributes of notes are merged from different locations: first from the
    duration objects, then from the pitch objects. Finally, GeneralNote
    attributes are added

    
    >>> a = chord.Chord()
    >>> a.quarterLength = 2
    >>> b = pitch.Pitch('A-')
    >>> c = pitch.Pitch('D-')
    >>> d = pitch.Pitch('E-')
    >>> e = a.pitches = [b, c, d]
    >>> len(e)
    3
    >>> mxNoteList = musicxml.toMxObjects.chordToMx(a)
    >>> len(mxNoteList) # get three mxNotes
    3
    >>> mxNoteList[0].get('chord')
    False
    >>> mxNoteList[1].get('chord')
    True
    >>> mxNoteList[2].get('chord')
    True
    >>> mxNoteList[0].get('pitch')
    <pitch step=A alter=-1 octave=4>
    >>> mxNoteList[1].get('pitch')
    <pitch step=D alter=-1 octave=4>
    >>> mxNoteList[2].get('pitch')
    <pitch step=E alter=-1 octave=4>
        

    Test that notehead translation works:
    
    >>> g = note.Note('c4')
    >>> g.notehead = 'diamond'
    >>> h = pitch.Pitch('g3')
    >>> i = chord.Chord([h, g])
    >>> i.quarterLength = 2
    >>> listOfMxNotes = musicxml.toMxObjects.chordToMx(i)
    >>> listOfMxNotes[0].get('chord')
    False
    >>> listOfMxNotes[1].noteheadObj.get('charData')
    'diamond'
    '''
    if spannerBundle is not None and len(spannerBundle) > 0:
        # this will get all spanners that participate with this note
        # get a new spanner bundle that only has components relevant to this 
        # note.
        spannerBundle = spannerBundle.getBySpannedElement(c)
        #environLocal.printDebug(['noteToMxNotes(): spannerBundle post-filter by spannedElement:', spannerBundle, n, id(n)])

    #environLocal.printDebug(['chordToMx', c])
    mxNoteList = []
    durPos = 0 # may have more than one dur
    mxDurationNotes = durationToMx(c.duration)
    durPosLast = len(mxDurationNotes) - 1
    for mxNoteBase in mxDurationNotes: # returns a list of mxNote objs
        # merge method returns a new object
        mxNoteChordGroup = []
        for chordPos, n in enumerate(c): # iterate component notes
        #for pitchObj in c.pitches:
            # copy here, before merge
            mxNote = copy.deepcopy(mxNoteBase)
            mxPitch = pitchToMx(n.pitch)
            mxNote = mxNote.merge(mxPitch, returnDeepcopy=False)
            if c.duration.isGrace:
                mxNote.set('duration', None)
            if chordPos > 0:
                mxNote.set('chord', True)
            # if we do not have a component color, set color from the chord
            # working with a deepcopy, so this change is ok
            if n.color is None:
                n.color = c.color
            mxNote.noteheadObj = noteheadToMxNotehead(n)
            #get the stem direction from the chord, not the pitch
            if c.stemDirection != 'unspecified':
                if c.stemDirection in ['noStem']:
                    mxNote.stem = 'none'
                else:
                    mxNote.stem = c.stemDirection
            # if not specified, try to get from note
            elif c.stemDirection == 'unspecified':
                if n.stemDirection != 'unspecified':
                    #environLocal.printDebug(['found specified component stemdirection', n.stemDirection])
                    if n.stemDirection in ['noStem']:
                        mxNote.stem = 'none'
                    else:
                        mxNote.stem = n.stemDirection

            #environLocal.printDebug(['final note stem', mxNote.stem])
            # only add beam to first note in group
            if c.beams is not None and chordPos == 0:
                mxNote.beamList = beamsToMx(c.beams)

            # if the durations included tuplets, there will be a tuplet
            # notations indication in each of the components of the chord; thus
            # all those other than first must be removed
            if chordPos != 0 and mxNote.notationsObj is not None:
                rmTargets = []
                for i, sub in enumerate(mxNote.notationsObj.componentList):
                    if sub.tag == 'tuplet':
                        rmTargets.append(i)
                # remove in reverse order
                rmTargets.reverse()
                for i in rmTargets:
                    mxNote.notationsObj.componentList.pop(i)

            # if this note, not a component duration,
            # need to add this to the last-encountered mxNote
            # get musicxl  mx objs from tie obj
            tieObj = n.tie
            if tieObj is not None:
                #environLocal.printDebug(['chordToMx: found tie for pitch', pitchObj])
                mxTieList, mxTiedList = tieToMx(tieObj)
                # if starting a tie, add to all mxNotes in the chord
                # but only add to the last duration in the dur group
                if (tieObj.type in ['start', 'continue'] and
                    durPos == durPosLast):
                    mxNote.tieList += mxTieList
                    mxNote.notationsObj.componentList += mxTiedList
                # if ending a tie, set first duration of dur group
                elif (tieObj.type == 'stop' and durPos == 0):
                    mxNote.tieList += mxTieList
                    mxNote.notationsObj.componentList += mxTiedList
                else:
                    pass
            mxNoteChordGroup.append(mxNote)

        # add chord group to note list
        mxNoteList += mxNoteChordGroup
        durPos += 1

    # only applied to first note
    for lyricObj in c.lyrics:
        mxNoteList[0].lyricList.append(lyricToMx(lyricObj))


    # if we have any articulations, they only go on the first of any 
    # component notes
    # our source target 
    articulationsAndExpressionsToMx(c, mxNoteList)

    # some spanner produce direction tags, and sometimes these need
    # to go before or after the notes of this element
    mxDirectionPre = []
    mxDirectionPost = []
    # will update and fill all lists passed in as args
    spannersToMx(c, mxNoteList, mxDirectionPre, mxDirectionPost, spannerBundle)

    return mxDirectionPre + mxNoteList + mxDirectionPost


#-------------------------------------------------------------------------------
# Notes

def noteheadToMxNotehead(obj, defaultColor=None):
    '''
    Translate a music21 :class:`~music21.note.Note` object or :class:`~music21.pitch.Pitch` object to a
    into a musicxml.mxObjects.Notehead object.

    
    >>> n = note.Note('C#4')
    >>> n.notehead = 'diamond'
    >>> mxN = musicxml.toMxObjects.noteheadToMxNotehead(n)
    >>> mxN.get('charData')
    'diamond'

    >>> n1 = note.Note('c3')
    >>> n1.notehead = 'diamond'
    >>> n1.noteheadParenthesis = True
    >>> n1.noteheadFill = False
    >>> mxN4 = musicxml.toMxObjects.noteheadToMxNotehead(n1)
    >>> mxN4._attr['filled']
    'no'
    >>> mxN4._attr['parentheses']
    'yes'
    '''
    mxNotehead = mxObjects.Notehead()
    nh = 'normal'
    nhFill = None
    nhParen = False

    # default noteheard, regardless of if set as attr
    if hasattr(obj, 'notehead'):
        nh = obj.notehead
    if hasattr(obj, 'noteheadFill'):
        nhFill = obj.noteheadFill
    if hasattr(obj, 'noteheadParenthesis'):
        nhParen = obj.noteheadParenthesis

    if nhParen is True:
        nhParen = 'yes'    

    if nhFill is True:
        nhFill = 'yes'
    elif nhFill is False:
        nhFill = 'no'


    if nh not in note.noteheadTypeNames:
        if nh is None:
            nh = 'none'
        else:
            raise NoteheadException('This notehead type is not supported by MusicXML: "%s"' % nh)
    else:
        # should only set if needed, otherwise creates extra musicxl  data
        #if nh not in ['normal']: 
        mxNotehead.set('charData', nh)
    if nhFill is not None:
        mxNotehead.set('filled', nhFill)
    if nhParen is not False:
        mxNotehead.set('parentheses', nhParen)
    if obj.color not in [None, '']:
        color = normalizeColor(obj.color)
        mxNotehead.set('color', color)
    return mxNotehead

def noteToMxNotes(n, spannerBundle=None):
    '''
    Translate a music21 :class:`~music21.note.Note` into a
    list of :class:`~music21.musicxml.mxObjects.Note` objects.

    Because of "complex" durations, the number of 
    `musicxml.mxObjects.Note` objects could be more than one.

    Note that, some note-attached spanners, such 
    as octave shifts, produce direction (and direction types) 
    in this method.
    
    
    >>> n = note.Note('D#5')
    >>> n.quarterLength = 2.25
    >>> musicxmlNoteList = musicxml.toMxObjects.noteToMxNotes(n)
    >>> len(musicxmlNoteList)
    2
    >>> musicxmlHalf = musicxmlNoteList[0]
    >>> musicxmlHalf
    <note <pitch step=D alter=1 octave=5> duration=20160 <tie type=start> type=half <accidental charData=sharp> <notations <tied type=start>>> 


    TODO: Test with spannerBundle != None
    '''
    #Attributes of notes are merged from different locations: first from the 
    #duration objects, then from the pitch objects. Finally, GeneralNote 
    #attributes are added.
    if spannerBundle is not None and len(spannerBundle) > 0:
        # this will get all spanners that participate with this note
        # get a new spanner bundle that only has spanned elements relevant to this 
        # note.
        spannerBundle = spannerBundle.getBySpannedElement(n)
        #environLocal.printDebug(['noteToMxNotes(): spannerBundle post-filter by spannedElement:', spannerBundle, n, id(n)])

    mxNoteList = []
    pitchMx = pitchToMx(n.pitch)
    noteColor = normalizeColor(n.color)

    # todo: this is not yet implemented in music21 note objects; to do
    #mxNotehead = mxObjects.Notehead()
    #mxNotehead.set('charData', defaults.noteheadUnpitched)

    for mxNote in durationToMx(n.duration): # returns a list of mxNote objs
        # merge method returns a new object; but can use existing here
        mxNote = mxNote.merge(pitchMx, returnDeepcopy=False)
        if n.duration.isGrace:
            # defaults may have been set; need to override here if a grace
            mxNote.set('duration', None)
        # get color from within .editorial using property
        # exports color on note tag and notehead tag (there is no consensus on where to 
        # export the color, so we do it to both
        if noteColor is not None: # and n.isRest:
            mxNote.set('color', noteColor)
        if n.hideObjectOnPrint == True:
            mxNote.set('printObject', "no")
            mxNote.set('printSpacing', "yes")
        mxNoteList.append(mxNote)

    # note: lyric only applied to first note
    for lyricObj in n.lyrics:
        mxNoteList[0].lyricList.append(lyricToMx(lyricObj))

    # if this note, not a component duration, but this note has a tie, 
    # need to add this to the last-encountered mxNote
    if n.tie is not None:
        mxTieList, mxTiedList = tieToMx(n.tie)
        # if starting or continuing tie, add to last mxNote in mxNote list
        if n.tie.type in ['start', 'continue']:
            mxNoteList[-1].tieList += mxTieList
            mxNoteList[-1].notationsObj.componentList += mxTiedList
        # if ending a tie, set first mxNote to stop
        elif n.tie.type == 'stop':
            mxNoteList[0].tieList += mxTieList
            mxNoteList[0].notationsObj.componentList += mxTiedList

    # need to apply beams to notes, but application needs to be
    # reconfigured based on what is gotten from n.duration
    # likely, this means that many continue beams will need to be added

    # this is setting the same beams for each part of this 
    # note; this may not be correct, as we may be dividing the note into
    # more than one part
    nBeams = n.beams
    if nBeams:
        nBeamsMx = beamsToMx(n.beams)
        for mxNote in mxNoteList:
            mxNote.beamList = nBeamsMx

    #Adds the notehead type if it is not set to the default 'normal'.
    if (n.notehead != 'normal' or n.noteheadFill is not None or
        n.color not in [None, '']):
        mxNoteList[0].noteheadObj = noteheadToMxNotehead(n)

    #If the stem direction is not 'unspecified'    
    if n.stemDirection != 'unspecified':
        if n.stemDirection in ['noStem']:
            mxNoteList[0].stem = 'none'
        else:
            mxNoteList[0].stem = n.stemDirection

    articulationsAndExpressionsToMx(n, mxNoteList)

    # some spanner produce direction tags, and sometimes these need
    # to go before or after the notes of this element
    mxDirectionPre = []
    mxDirectionPost = []
    # will update and fill all lists passed in as args
    spannersToMx(n, mxNoteList, mxDirectionPre, mxDirectionPost, spannerBundle)

    return mxDirectionPre + mxNoteList + mxDirectionPost



def restToMxNotes(r, spannerBundle=None):
    '''Translate a :class:`~music21.note.Rest` to a MusicXML :class:`~music21.musicxml.mxObjects.Note` object 
    configured with a :class:`~music21.musicxml.mxObjects.Rest`.
    '''
    if spannerBundle is not None and len(spannerBundle) > 0:
        # this will get all spanners that participate with this note
        # get a new spanner bundle that only has spanned elements relevant to this 
        # note.
        spannerBundle = spannerBundle.getBySpannedElement(r)
        #environLocal.printDebug(['noteToMxNotes(): spannerBundle post-filter by spannedElement:', spannerBundle, n, id(n)])

    mxNoteList = []
    for mxNote in durationToMx(r.duration): # returns a list of mxNote objs
        # merge method returns a new object
        mxRest = mxObjects.Rest()
        mxRest.setDefaults()
        mxNote.set('rest', mxRest)
        # TODO: get color from within .editorial using attribute or delete .editorial...
        mxNote.set('color', normalizeColor(r.color))

        if r.hideObjectOnPrint == True:
            mxNote.set('printObject', "no")
            mxNote.set('printSpacing', "yes")
        mxNoteList.append(mxNote)
    articulationsAndExpressionsToMx(r, mxNoteList)

    # some spanner produce direction tags, and sometimes these need
    # to go before or after the notes of this element
    mxDirectionPre = []
    mxDirectionPost = []
    # will update and fill all lists passed in as args
    spannersToMx(r, mxNoteList, mxDirectionPre, mxDirectionPost, spannerBundle)

    return mxDirectionPre + mxNoteList + mxDirectionPost
    
    
    return mxNoteList



#-------------------------------------------------------------------------------
# Measures

def measureToMx(m, spannerBundle=None, mxTranspose=None):
    '''Translate a :class:`~music21.stream.Measure` to a MusicXML :class:`~music21.musicxml.Measure` object.
    '''

    #environLocal.printDebug(['measureToMx(): m.isSorted:', m.isSorted, 'm._mutable', m._mutable, 'len(spannerBundle)', len(spannerBundle)])
    if spannerBundle is not None:
        # get all spanners that have this measure as a component    
        rbSpanners = spannerBundle.getBySpannedElement(m).getByClass('RepeatBracket')
    else:
        rbSpanners = [] # for size comparison

    mxMeasure = mxObjects.Measure()
    mxMeasure.set('number', m.measureNumberWithSuffix())
    if m.layoutWidth is not None:
        mxMeasure.set('width', m.layoutWidth)

    # print objects come before attributes
    # note: this class match is a problem in cases where the object is created in the module itself, as in a test. 

    # do a quick search for any layout objects before searching individually...
    foundAny = m.getElementsByClass('LayoutBase')
    if len(foundAny) > 0:
        mxPrint = None
        found = m.getElementsByClass('PageLayout')
        if len(found) > 0:
            pl = found[0] # assume only one per measure
            mxPrint = pageLayoutToMxPrint(pl)
        found = m.getElementsByClass('SystemLayout')
        if len(found) > 0:
            sl = found[0] # assume only one per measure
            if mxPrint is None:
                mxPrint = systemLayoutToMxPrint(sl)
            else:
                mxPrintTemp = systemLayoutToMxPrint(sl)
                mxPrint.merge(mxPrintTemp, returnDeepcopy = False)
        found = m.getElementsByClass('StaffLayout')
        if len(found) > 0:
            sl = found[0] # assume only one per measure
            if mxPrint is None:
                mxPrint = staffLayoutToMxPrint(sl)
            else:
                mxPrintTemp = staffLayoutToMxPrint(sl)
                mxPrint.merge(mxPrintTemp, returnDeepcopy = False)

        if mxPrint is not None:
            mxMeasure.componentList.append(mxPrint)

    # get an empty mxAttributes object
    mxAttributes = mxObjects.Attributes()
    # best to only set dvisions here, as clef, time sig, meter are not
    # required for each measure
    mxAttributes.setDefaultDivisions()
    # set the mxAttributes transposition; this assumes it is 
    # constant for an entire Part
    mxAttributes.transposeObj = mxTranspose # may be None

    # may need to look here at the parent, and try to find
    # the clef in the clef last defined in the parent
    # often m.clef will be None b/c a clef has already been defined
    if m.clef is not None:
        mxAttributes.clefList = [clefToMxClef(m.clef)]
    if m.keySignature is not None:
        # keySignatureToMx returns a mxKey ojbect, needs to be in a list
        mxAttributes.keyList = [keySignatureToMx(m.keySignature)]
    if m.timeSignature is not None:
        # timeSignatureToMx returns a mxTime ojbect, needs to be in a list
        mxAttributes.timeList = [timeSignatureToMx(m.timeSignature)]
 
    found = m.getElementsByClass('StaffLayout')
    if len(found) > 0:
        sl = found[0] # assume only one per measure
        mxAttributes.staffDetailsList = [staffLayoutToMxStaffDetails(sl)]
 
    mxMeasure.set('attributes', mxAttributes)
       
    # see if we have barlines
    if (m.leftBarline != None or
        (len(rbSpanners) > 0 and rbSpanners[0].isFirst(m))):
        if m.leftBarline is None:
            # create a simple barline for storing ending
            mxBarline = mxObjects.Barline()
        else:
            if 'Repeat' in m.leftBarline.classes:
                mxBarline = repeatToMx(m.leftBarline)
            else:
                mxBarline = barlineToMx(m.leftBarline)

        # setting location outside of object based on that this attribute
        # is the leftBarline
        mxBarline.set('location', 'left')
        # if we have spanners here, we can be sure they are relevant
        if len(rbSpanners) > 0:
            mxEnding = mxObjects.Ending()
            mxEnding.set('type', 'start')
            mxEnding.set('number', rbSpanners[0].number)
            mxBarline.set('endingObj', mxEnding)
        mxMeasure.componentList.append(mxBarline)

    # need to handle objects in order when creating musicxml 
    # we thus assume that objects are sorted here

    nonVoiceMeasureItems = None
    if m.hasVoices():
        # all things that are not a Stream; elements simply positioned freely
        nonVoiceMeasureItems = m.getElementsNotOfClass('Stream')
        # store divisions for use in calculating backup of voices 
        divisions = mxAttributes.divisions
        for v in m.voices:
            # iterate over each object in this voice
            voiceId = v.id
            offsetMeasureNote = 0 # offset of notes w/n measure  
            for obj in v.flat:
                classes = obj.classes # store result of property call once
                if 'Note' in classes:
                    offsetMeasureNote += obj.quarterLength
                    objList = noteToMxNotes(obj, spannerBundle=spannerBundle)
                    for sub in objList:
                        try:
                            sub.voice = voiceId + 1 # the voice id is the voice number # musescore -- add one
                        except TypeError:
                            sub.voice = voiceId
                    mxMeasure.componentList += objList
                elif 'ChordSymbol' in classes:
                    if obj.writeAsChord:
                        mxMeasure.componentList += chordToMx(obj,
                        spannerBundle=spannerBundle)
                    else:
                        mxMeasure.componentList.append(chordSymbolToMx(obj))
                elif 'Chord' in classes:
                    # increment offset before getting mx, as this way a single
                    # chord provides only one value
                    offsetMeasureNote += obj.quarterLength
                    objList = chordToMx(obj, spannerBundle=spannerBundle)
                    for sub in objList:
                        try:
                            sub.voice = voiceId + 1 # the voice id is the voice number
                        except TypeError:
                            sub.voice = voiceId

                    mxMeasure.componentList += objList
                elif 'GeneralNote' in classes:
                    offsetMeasureNote += obj.quarterLength

                    ## returns a list of note objects...
                    if 'Note' in classes:
                        objList = noteToMxNotes(obj, spannerBundle=spannerBundle)
                    elif 'Rest' in classes:
                        objList = restToMxNotes(obj, spannerBundle=spannerBundle)
                    elif 'Unpitched' in classes:
                        environLocal.warn("skipping Unpitched object")
                    # need to set voice for each contained mx object
                    for sub in objList:
                        try:
                            sub.voice = voiceId + 1 # the voice id is the voice number
                        except TypeError:
                            sub.voice = voiceId

                    mxMeasure.componentList += objList
            # create backup object configured to duration of accumulated
            # notes, meaning that we always return to the start of the measure
            mxBackup = mxObjects.Backup()
            mxBackup.duration = int(divisions * offsetMeasureNote)
            mxMeasure.componentList.append(mxBackup)

    if not m.hasVoices() or nonVoiceMeasureItems is not None: # no voices
        if nonVoiceMeasureItems is not None:
            mFlat = nonVoiceMeasureItems # this is a Stream
        else:
            mFlat = m.flat

        for obj in mFlat:
            #environLocal.printDebug(['iterating flat M components', obj, obj.offset])
            classes = obj.classes # store result of property call once
            if 'Note' in classes:
                mxMeasure.componentList += noteToMxNotes(obj,
                    spannerBundle=spannerBundle)
            elif 'ChordSymbol' in classes:
                if obj.writeAsChord:
                    mxMeasure.componentList += chordToMx(obj,
                    spannerBundle=spannerBundle)
                else:
                    mxMeasure.componentList.append(chordSymbolToMx(obj))
            elif 'Chord' in classes:
                mxMeasure.componentList += chordToMx(obj,
                    spannerBundle=spannerBundle)
            elif 'GeneralNote' in classes: # this includes chords so caught before.
                mxList = None
                if 'Note' in classes:
                    mxList = noteToMxNotes(obj, spannerBundle=spannerBundle)
                elif 'Rest' in classes:
                    mxList = restToMxNotes(obj, spannerBundle=spannerBundle)
                
                mxMeasure.componentList += mxList
            elif 'Dynamic' in classes:
                # returns an mxDirection object
                mxOffset = int(defaults.divisionsPerQuarter *
                           obj.getOffsetBySite(mFlat))
                mxDirection = dynamicToMx(obj)
                mxDirection.offset = mxOffset
                # positioning dynamics by offset, not position in measure
                mxMeasure.insert(0, mxDirection)
            elif 'Segno' in classes:
                mxOffset = int(defaults.divisionsPerQuarter *
                           obj.getOffsetBySite(mFlat))
                mxDirection = segnoToMx(obj)
                mxDirection.offset = mxOffset
                mxMeasure.insert(0, mxDirection)
            elif 'Coda' in classes:
                mxOffset = int(defaults.divisionsPerQuarter *
                           obj.getOffsetBySite(mFlat))
                mxDirection = codaToMx(obj)
                mxDirection.offset = mxOffset
                mxMeasure.insert(0, mxDirection)
            elif 'MetronomeMark' in classes or 'MetricModulation' in classes:
                #environLocal.printDebug(['measureToMx: found:', obj])
                # convert m21 offset to musicxl  divisions
                mxOffset = int(defaults.divisionsPerQuarter *
                           obj.getOffsetBySite(mFlat))
                # get a list of objects: may be a text expression + metro
                try:
                    mxList = tempoIndicationToMx(obj)
                    for mxDirection in mxList: # a list of mxdirections
                        mxDirection.offset = mxOffset
                        # uses internal offset positioning, can insert at zero
                        mxMeasure.insert(0, mxDirection)
                        #mxMeasure.componentList.append(mxObj)
                except Exception as e:
                    environLocal.warn("Could not convert MetronomeMark/MetricModulation %s: %s" % (obj, e))
            
            elif 'TextExpression' in classes:
                # convert m21 offset to musicxl  divisions
                #environLocal.printDebug(['found TextExpression', obj])

                mxOffset = int(defaults.divisionsPerQuarter *
                           obj.getOffsetBySite(mFlat))
                mxDirection = textExpressionToMx(obj)
                mxDirection.offset = mxOffset
                # place at zero position, as offset value determines horizontal position, not location amongst notes
                mxMeasure.insert(0, mxDirection)
            elif 'RepeatExpression' in classes:
                # subclass of RepeatMark and Expression
                mxOffset = int(defaults.divisionsPerQuarter *
                           obj.getOffsetBySite(mFlat))
                # just get the TextExpression stored in the RepeatExpression
                mxDirection = textExpressionToMx(obj.getTextExpression())
                mxDirection.offset = mxOffset
                # place at zero position, as offset value determines horizontal position, not location amongst notes
                mxMeasure.insert(0, mxDirection)
            elif 'Clef' in classes and obj.offset != 0.0:
                # clef within bar
                clefAttributes = mxObjects.Attributes()
                clefAttributes.clefList = [clefToMxClef(obj)]
                mxMeasure.componentList.append(clefAttributes)
            else: # other objects may have already been added
                pass
                #environLocal.printDebug(['mesureToMx of Measure is not processing', obj])

    # TODO: create bar ending positions
    # right barline must follow all notes
    if (m.rightBarline != None or
        (len(rbSpanners) > 0 and rbSpanners[0].isLast(m))):
        if m.rightBarline is None:
            # create a simple barline for storing ending
            mxBarline = mxObjects.Barline()
        else:
            if 'Repeat' in m.rightBarline.classes:
                mxBarline = repeatToMx(m.rightBarline)
            else:
                mxBarline = barlineToMx(m.rightBarline)
        # setting location outside of object based on that this attribute
        # is the leftBarline
        mxBarline.set('location', 'right')

        # if we have spanners here, we can be sure they are relevant
        if len(rbSpanners) > 0:
            mxEnding = mxObjects.Ending()
            # must use stop, not discontinue
            mxEnding.set('type', 'stop')
            mxEnding.set('number', rbSpanners[0].number)
            mxBarline.set('endingObj', mxEnding)

        mxMeasure.componentList.append(mxBarline)

    return mxMeasure


#-------------------------------------------------------------------------------
# Streams

def streamPartToMx(part, instStream=None, meterStream=None,
                   refStreamOrTimeRange=None, spannerBundle=None):
    '''
    Convert a Part object (or any Stream representing a Part)
    to musicxml
    
    If there are Measures within this Stream, use them 
    to create and return an mxPart and mxScorePart.

    An `instObj` may be assigned from caller; this Instrument is pre-collected
    from this Stream in order to configure id and midi-channel values.

    The `meterStream`, if given, provides a template of meters.
    '''
    #environLocal.printDebug(['calling Stream.streamPartToMx', 'len(spannerBundle)', len(spannerBundle)])
    # note: meterStream may have TimeSignature objects from an unrelated
    # Stream.
    if instStream is None:
        # see if an instrument is defined in this or a parent stream
        instObj = part.getInstrument()
        instStream = stream.Stream()
        instStream.insert(0, instObj) # create for storage
    else:
        instObj = instStream[0]
    # must set a unique part id, if not already assigned
    if instObj.partId == None:
        instObj.partIdRandomize()
    # returns an mxScorePart
    mxScorePart = instrumentToMx(instObj)
    #environLocal.printDebug(['calling Stream.streamPartToMx', 'mxScorePart', mxScorePart, mxScorePart.get('id')])

    mxPart = mxObjects.Part()
    #mxPart.setDefaults()
    mxPart.set('id', instObj.partId) # need to set id

    # get a stream of measures
    # if flat is used here, the Measure is not obtained
    # may need to be semi flat?
    measureStream = part.getElementsByClass('Measure')
    if len(measureStream) == 0:
        part.makeMutable() # must mutate
        # try to add measures if none defined
        # returns a new stream w/ new Measures but the same objects
        part.makeNotation(meterStream=meterStream,
                        refStreamOrTimeRange=refStreamOrTimeRange,
                        inPlace=True)
        measureStream = part.getElementsByClass('Measure')

        #environLocal.printDebug(['Stream.streamPartToMx: post makeNotation, length', len(measureStream)])

        # after calling measuresStream, need to update Spanners, as a deepcopy
        # has been made
        # might need to getAll b/c might need spanners 
        # from a higher level container
        #spannerBundle = spanner.SpannerBundle(
        #                measureStream.flat.getAllContextsByClass('Spanner'))
        # only getting spanners at this level
        #spannerBundle = spanner.SpannerBundle(measureStream.flat)
        spannerBundle = part.spannerBundle
    # if this is a Measure, see if it needs makeNotation
    else: # there are measures
        # check that first measure has any atributes in outer Stream
        # this is for non-standard Stream formations (some kern imports)
        # that place key/clef information in the containing stream
        if measureStream[0].clef is None:
            measureStream[0].makeMutable() # must mutate
            outerClefs = part.getElementsByClass('Clef')
            if len(outerClefs) > 0:
                measureStream[0].clef = outerClefs[0]
        if measureStream[0].keySignature is None:
            measureStream[0].makeMutable() # must mutate
            outerKeySignatures = part.getElementsByClass('KeySignature')
            if len(outerKeySignatures) > 0:
                measureStream[0].keySignature = outerKeySignatures[0]
        if measureStream[0].timeSignature is None:
            measureStream[0].makeMutable() # must mutate
            outerTimeSignatures = part.getElementsByClass('TimeSignature')
            if len(outerTimeSignatures) > 0:
                measureStream[0].timeSignature = outerTimeSignatures[0]
        # see if accidentals/beams can be processed
        if not measureStream.haveAccidentalsBeenMade():
            measureStream.makeAccidentals(inPlace=True)
        if not measureStream.streamStatus.haveBeamsBeenMade():
            # if making beams, have to make a deep copy, as modifying notes
            try:
                measureStream.makeBeams(inPlace=True)
            except exceptions21.StreamException: 
                pass
        if spannerBundle is None:
            spannerBundle = spanner.SpannerBundle(measureStream.flat)

    # make sure that all instances of the same class have unique ids
    spannerBundle.setIdLocals()

    # for each measure, call measureToMx to get the musicxml representation
    for obj in measureStream:
        # get instrument for every measure position
        moStart = obj.getOffsetBySite(measureStream)
        instSubStream = instStream.getElementsByOffset(moStart,
                         moStart + obj.duration.quarterLength,
                         includeEndBoundary=False)
        mxTranspose = None
        if len(instSubStream) > 0:
            instSubObj = instSubStream[0]
            if part.atSoundingPitch in [False]:
                # if not at sounding pitch, encode transposition from instrument
                if instSubObj.transposition is not None:
                    mxTranspose = intervalToMXTranspose(
                                    instSubObj.transposition)
                    #raise ToMxObjectsException('cannot get transposition for a part that is not at sounding pitch.')
        mxPart.append(measureToMx(obj, spannerBundle=spannerBundle,
                 mxTranspose=mxTranspose))
    # might to post processing after adding all measures to the Stream
    # TODO: need to find all MetricModulations and updateByContext
    # mxScorePart contains mxInstrument
    return mxScorePart, mxPart

def emptyObjectToMx():
    '''
    Create a blank score with 'This Page Intentionally Left blank' as a gag...

    
    >>> musicxml.toMxObjects.emptyObjectToMx()
    <score-partwise <work work-title=This Page Intentionally Left Blank>...<measure number=0 <attributes divisions=10080> <note <rest > duration=40320 type=whole...>>>>    
    '''
    out = stream.Stream()
    m = stream.Measure()
    r = note.Rest(quarterLength=4)
    m.append(r)
    out.append(m)
    # return the processing of this Stream
    md = metadata.Metadata(title='This Page Intentionally Left Blank')
    out.insert(0, md)
    # recursive call to this non-empty stream
    return streamToMx(out)


def streamToMx(s, spannerBundle=None):
    '''
    Create and return a musicxml Score object from a Stream or Score

    This is the most common entry point for
    conversion of a Stream to MusicXML.

    
    >>> n1 = note.Note()
    >>> measure1 = stream.Measure()
    >>> measure1.insert(n1)
    >>> s1 = stream.Stream()
    >>> s1.insert(measure1)
    >>> mxScore = musicxml.toMxObjects.streamToMx(s1)
    >>> mxPartList = mxScore.get('partList')
    '''
    # returns an mxScore object; a deepcopy has already been made

    #environLocal.printDebug(['streamToMx:'])
    if len(s) == 0:
        return emptyObjectToMx()
    
    #environLocal.printDebug('calling streamToMx')
    # stores pairs of mxScorePart and mxScore
    mxComponents = []
    instList = []

    scoreLayouts = s.getElementsByClass('ScoreLayout')
    if len(scoreLayouts) > 0:
        scoreLayout = scoreLayouts[0]
    else:
        scoreLayout = None

    # search context probably should always be True here
    # to search container first, we need a non-flat version
    # searching a flattened version, we will get contained and non-container
    # this meter  stream is passed to makeNotation()
    meterStream = s.getTimeSignatures(searchContext=False,
                    sortByCreationTime=False, returnDefault=False)
    #environLocal.printDebug(['streamToMx: post meterStream search', meterStream, meterStream[0]])
    if len(meterStream) == 0:
        # note: this will return a default if no meters are found
        meterStream = s.flat.getTimeSignatures(searchContext=False,
                    sortByCreationTime=True, returnDefault=True)

    # get all text boxes
    textBoxes = s.flat.getElementsByClass('TextBox')

    # we need independent sub-stream elements to shift in presentation
    highestTime = 0

    if spannerBundle is None: 
        # no spanner bundle provided, get one from the flat stream
        #spannerBundle = spanner.SpannerBundle(s.flat)
        spannerBundle = s.spannerBundle
        #environLocal.printDebug(['streamToMx(): loaded spannerBundle of size:', len(spannerBundle), 'id(spannerBundle)', id(spannerBundle)])


    if s.hasPartLikeStreams():
        #environLocal.printDebug('streamToMx(): interpreting multipart')
        streamOfStreams = s.getElementsByClass('Stream')
        for obj in streamOfStreams:
            # may need to copy element here
            # apply this streams offset to elements
            obj.transferOffsetToElements()
            ht = obj.highestTime
            if ht > highestTime:
                highestTime = ht

        refStreamOrTimeRange = [0, highestTime]
        # would like to do something like this but cannot
        # replace object inside of the stream
        for obj in streamOfStreams:
            obj.makeRests(refStreamOrTimeRange, inPlace=True)

        count = 0
        midiChannelList = []
        for obj in streamOfStreams:
            count += 1
            if count > len(streamOfStreams):
                raise ToMxObjectsException('infinite stream encountered')

            # only things that can be treated as parts are in finalStream
            # get a default instrument if not assigned
            instStream = obj.getInstruments(returnDefault=True)
            inst = instStream[0] # store first, as handled differently
            instIdList = [x.partId for x in instList]

            if inst.partId in instIdList: # must have unique ids 
                inst.partIdRandomize() # set new random id

            if (inst.midiChannel == None or
                inst.midiChannel in midiChannelList):
                try:
                    inst.autoAssignMidiChannel(usedChannels=midiChannelList)
                except exceptions21.InstrumentException as e:
                    environLocal.warn(str(e))
            midiChannelList.append(inst.midiChannel)
            #environLocal.printDebug(['midiChannel list', midiChannelList])

            # add to list for checking on next round
            instList.append(inst)

            # force this instrument into this part
            # meterStream is only used here if there are no measures
            # defined in this part
            mxScorePart, mxPart = streamPartToMx(obj, instStream=instStream,
                        meterStream=meterStream,
                        refStreamOrTimeRange=refStreamOrTimeRange,
                        spannerBundle=spannerBundle)
            mxComponents.append([mxScorePart, mxPart, obj])
            #mxComponents.append(obj.streamPartToMx(inst, meterStream, refStreamOrTimeRange))

    else: # assume this is the only part
        #environLocal.printDebug('streamPartToMx: handling single-part Stream')
        # if no instrument is provided it will be obtained through s
        # when streamPartToMx is called
        mxScorePart, mxPart = streamPartToMx(s, meterStream=meterStream,
                              spannerBundle=spannerBundle)
        mxComponents.append([mxScorePart, mxPart, s])
        #environLocal.printDebug(['mxComponents', mxComponents])

    # create score and part list
    # try to get mxScore from lead meta data first
    if s.metadata != None:
        mxScore = metadataToMxScore(s.metadata) # returns an mx score
    else:
        mxScore = mxObjects.Score()

    # add text boxes
    for tb in textBoxes: # a stream of text boxes
        mxScore.creditList.append(textBoxToMxCredit(tb))

    mxScoreDefault = mxObjects.Score()
    mxScoreDefault.setDefaults()
    mxIdDefault = mxObjects.Identification()
    mxIdDefault.setDefaults() # will create a composer
    mxScoreDefault.set('identification', mxIdDefault)

    # merge metadata derived with default created
    mxScore = mxScore.merge(mxScoreDefault, returnDeepcopy=False)
    # get score defaults if any:
    if scoreLayout is None:
        from music21 import layout
        scoreLayout = layout.ScoreLayout()
        scoreLayout.scalingMillimeters = defaults.scalingMillimeters
        scoreLayout.scalingTenths = defaults.scalingTenths

    mxDefaults = scoreLayoutToMxDefaults(scoreLayout)
    mxScore.defaultsObj = mxDefaults


    addSupportsToMxScore(s, mxScore)

    mxPartList = mxObjects.PartList()
    # mxComponents is just a list 
    # returns a spanner bundle
    staffGroups = spannerBundle.getByClass('StaffGroup')
    #environLocal.printDebug(['got staff groups', staffGroups])

    # first, find which parts are start/end of partGroups
    partGroupIndexRef = {} # have id be key
    partGroupIndex = 1 # start by 1 by convetion
    for mxScorePart, mxPart, p in mxComponents:
        # check for first
        for sg in staffGroups:
            if sg.isFirst(p):
                mxPartGroup = configureMxPartGroupFromStaffGroup(sg)
                mxPartGroup.set('type', 'start')
                mxPartGroup.set('number', partGroupIndex)
                # assign the spanner in the dictionary
                partGroupIndexRef[partGroupIndex] = sg
                partGroupIndex += 1 # increment for next usage
                mxPartList.append(mxPartGroup)
        # add score part
        mxPartList.append(mxScorePart)
        # check for last
        activeIndex = None
        for sg in staffGroups:
            if sg.isLast(p):
                # find the spanner in the dictionary already-assigned
                for key, value in partGroupIndexRef.items():
                    if value is sg:
                        activeIndex = key
                        break
                mxPartGroup = mxObjects.PartGroup()
                mxPartGroup.set('type', 'stop')
                if activeIndex is not None:
                    mxPartGroup.set('number', activeIndex)
                mxPartList.append(mxPartGroup)

    # addition of parts must simply be in the same order as above
    for mxScorePart, mxPart, p in mxComponents:
        mxScore.append(mxPart) # mxParts go on component list

    # set the mxPartList
    mxScore.set('partList', mxPartList)
    return mxScore

def addSupportsToMxScore(s, mxScore):
    '''
    add information about what this score actually supports

    Currently, if Stream.definesExplicitSystemBreaks is set to True
    then a supports new-system tag is added.
    
    '''
    if s.definesExplicitSystemBreaks or s.definesExplicitPageBreaks:
        mxIdentification = mxScore.get('identification')
        if mxIdentification is not None:
            mxEncoding = mxIdentification.get('encoding')
            if mxEncoding is None:
                mxEncoding = mxObjects.Encoding()
                mxIdentification.encodingObj = mxEncoding
            if s.definesExplicitSystemBreaks is True:
                mxSupports = mxObjects.Supports()
                mxSupports.set('attribute', 'new-system')
                mxSupports.set('type', 'yes')
                mxSupports.set('value', 'yes')
                mxSupports.set('element', 'print')
                mxEncoding.supportsList.append(mxSupports)
            if s.definesExplicitPageBreaks is True:
                mxSupports = mxObjects.Supports()
                mxSupports.set('attribute', 'new-page')
                mxSupports.set('type', 'yes')
                mxSupports.set('value', 'yes')
                mxSupports.set('element', 'print')
                mxEncoding.supportsList.append(mxSupports)



#------------------------------------------------------------------------------
# beam and beams

def beamToMx(beamObject):
    '''

    
    >>> a = beam.Beam()
    >>> a.type = 'start'
    >>> a.number = 1
    >>> b = musicxml.toMxObjects.beamToMx(a)
    >>> b.get('charData')
    'begin'
    >>> b.get('number')
    1

    >>> a.type = 'continue'
    >>> b = musicxml.toMxObjects.beamToMx(a)
    >>> b.get('charData')
    'continue'

    >>> a.type = 'stop'
    >>> b = musicxml.toMxObjects.beamToMx(a)
    >>> b
    <beam number=1 charData=end>
    >>> b.get('charData')
    'end'

    >>> a.type = 'partial'
    >>> a.direction = 'left'
    >>> b = musicxml.toMxObjects.beamToMx(a)
    >>> b.get('charData')
    'backward hook'

    >>> a.direction = 'right'
    >>> b = musicxml.toMxObjects.beamToMx(a)
    >>> b.get('charData')
    'forward hook'

    >>> a.direction = None
    >>> b = musicxml.toMxObjects.beamToMx(a)
    Traceback (most recent call last):
    ToMxObjectsException: partial beam defined without a proper direction set (set to None)

    >>> a.type = 'crazy'
    >>> b = musicxml.toMxObjects.beamToMx(a)
    Traceback (most recent call last):
    ToMxObjectsException: unexpected beam type encountered (crazy)
    '''
    mxBeam = mxObjects.Beam()
    if beamObject.type == 'start':
        mxBeam.set('charData', 'begin') 
    elif beamObject.type == 'continue':
        mxBeam.set('charData', 'continue') 
    elif beamObject.type == 'stop':
        mxBeam.set('charData', 'end') 
    elif beamObject.type == 'partial':
        if beamObject.direction == 'left':
            mxBeam.set('charData', 'backward hook')
        elif beamObject.direction == 'right':
            mxBeam.set('charData', 'forward hook') 
        else:
            raise ToMxObjectsException('partial beam defined without a proper direction set (set to %s)' % beamObject.direction)
    else:
        raise ToMxObjectsException('unexpected beam type encountered (%s)' % beamObject.type)

    mxBeam.set('number', beamObject.number)
    return mxBeam


def beamsToMx(beamsObj):
    '''
    Returns a list of mxBeam objects from a :class:`~music21.beam.Beams` object

    
    >>> a = beam.Beams()
    >>> a.fill(2, type='start')
    >>> mxBeamList = musicxml.toMxObjects.beamsToMx(a)
    >>> len(mxBeamList)
    2
    >>> mxBeamList[0]
    <beam number=1 charData=begin>
    >>> mxBeamList[1]
    <beam number=2 charData=begin>
    '''
    mxBeamList = []
    for beamObj in beamsObj.beamsList:
        mxBeamList.append(beamToMx(beamObj))
    return mxBeamList

#---------------------------------------------------------
# layout
def scoreLayoutToMxDefaults(scoreLayout):
    '''
    Return a :class:`~music21.musicxml.mxObjects.Defaults` ('mxDefaults')
    object for a :class:`~music21.layout.ScoreLayout` object.
    
    the mxDefaults object might include an mxScaling object.
    
    
    >>> sl = layout.ScoreLayout()
    >>> sl.scalingMillimeters = 7.24342
    >>> sl.scalingTenths = 40
    >>> mxDefaults = musicxml.toMxObjects.scoreLayoutToMxDefaults(sl)
    >>> mxDefaults
    <defaults <scaling millimeters=7.24342 tenths=40>>
    '''
    mxDefaults = mxObjects.Defaults()
    if scoreLayout.scalingMillimeters is not None or scoreLayout.scalingTenths is not None:
        mxScaling = mxObjects.Scaling()
        mxScaling.millimeters = scoreLayout.scalingMillimeters
        mxScaling.tenths = scoreLayout.scalingTenths
        mxDefaults.scalingObj = mxScaling

    if scoreLayout.pageLayout is not None:
        mxPageLayout = pageLayoutToMxPageLayout(scoreLayout.pageLayout)
        if mxPageLayout is not None:
            mxDefaults.layoutList.append(mxPageLayout)
    if scoreLayout.systemLayout is not None:
        mxSystemLayout = systemLayoutToMxSystemLayout(scoreLayout.systemLayout)
        if mxSystemLayout is not None:
            mxDefaults.layoutList.append(mxSystemLayout)
    for staffLayout in scoreLayout.staffLayoutList:
        mxStaffLayout = staffLayoutToMxStaffLayout(staffLayout)
        mxDefaults.layoutList.append(mxStaffLayout)

    return mxDefaults


def pageLayoutToMxPrint(pageLayout):
    '''
    Return a :class:`~music21.musicxml.mxObjects.Print` (`mxPrint`) 
    object for a 
    :class:`~music21.layout.PageLayout` object.

    the mxPrint object includes an :class:`~music21.musicxml.mxObjects.PageLayout` (`mxPageLayout`)
    object inside it.
    
    
    >>> pl = layout.PageLayout(pageNumber = 5, leftMargin=234, rightMargin=124, pageHeight=4000, pageWidth=3000, isNew=True)
    >>> mxPrint = musicxml.toMxObjects.pageLayoutToMxPrint(pl)
    >>> mxPrint.get('new-page')
    'yes'
    >>> mxPrint.get('page-number')
    5
    '''
    mxPrint = mxObjects.Print()
    if pageLayout.isNew:
        mxPrint.set('new-page', 'yes')
    if pageLayout.pageNumber is not None:
        mxPrint.set('page-number', pageLayout.pageNumber)
    
    mxPageLayout = pageLayoutToMxPageLayout(pageLayout)
    if mxPageLayout is not None:
        mxPrint.append(mxPageLayout)

    return mxPrint

def pageLayoutToMxPageLayout(pageLayout):
    '''
    returns either an mxPageLayout object from a layout.PageLayout
    object, or None if there's nothing to set.

    
    >>> pl = layout.PageLayout(pageNumber = 5, leftMargin=234, rightMargin=124, pageHeight=4000, pageWidth=3000, isNew=True)
    >>> mxPageLayout = musicxml.toMxObjects.pageLayoutToMxPageLayout(pl)
    >>> mxPageLayout.get('page-height')
    4000
    '''
    addMxPageLayoutObj = False # true if anything set...
    mxPageLayout = mxObjects.PageLayout()
    if pageLayout.pageHeight != None:
        addMxPageLayoutObj = True
        mxPageLayout.set('pageHeight', pageLayout.pageHeight)
    if pageLayout.pageWidth != None:
        addMxPageLayoutObj = True
        mxPageLayout.set('pageWidth', pageLayout.pageWidth)

    # TODO- set attribute PageMarginsType
    mxPageMargins = mxObjects.PageMargins()

    # musicxml requires both left and right defined
    matchLeft = False
    matchRight = False
    if pageLayout.leftMargin != None:
        mxPageMargins.set('leftMargin', pageLayout.leftMargin)
        matchLeft = True
    if pageLayout.rightMargin != None:
        mxPageMargins.set('rightMargin', pageLayout.rightMargin)
        matchRight = True

    if matchLeft and not matchRight:
        mxPageMargins.set('rightMargin', 0)
    if matchRight and not matchLeft:
        mxPageMargins.set('leftMargin', 0)

    if pageLayout.topMargin != None:
        mxPageMargins.set('topMargin', pageLayout.topMargin)
    if pageLayout.bottomMargin != None:
        mxPageMargins.set('bottomMargin', pageLayout.bottomMargin)


    # stored on components list
    if matchLeft or matchRight:
        addMxPageLayoutObj = True
        mxPageLayout.append(mxPageMargins)


    if addMxPageLayoutObj is True:
        return mxPageLayout
    else:
        return None


def systemLayoutToMxPrint(systemLayout):
    '''
    Return a mxPrint object

    
    >>> sl = layout.SystemLayout(leftmargin=234, rightmargin=124, distance=3, isNew=True)
    >>> mxPrint = musicxml.toMxObjects.systemLayoutToMxPrint(sl)
    >>> mxPrint
    <print new-system=yes <system-layout <system-margins left-margin=234 right-margin=124> system-distance=3>>
    '''
    mxPrint = mxObjects.Print()
    if systemLayout.isNew:
        mxPrint.set('new-system', 'yes')

    mxSystemLayout = systemLayoutToMxSystemLayout(systemLayout)
    if mxSystemLayout is not None:
        mxPrint.append(mxSystemLayout)

    return mxPrint

def systemLayoutToMxSystemLayout(systemLayout):
    '''
    returns either an mxSystemLayout object from a layout.SystemLayout
    object, or None if there's nothing to set.

    
    >>> sl = layout.SystemLayout(leftmargin=234, rightmargin=124, distance=3, isNew=True)
    >>> mxSystemLayout = musicxml.toMxObjects.systemLayoutToMxSystemLayout(sl)
    >>> mxSystemLayout.get('system-distance')
    3
    '''
    addMxSystemLayout = False # only add if anything set
    mxSystemLayout = mxObjects.SystemLayout()
    mxSystemMargins = mxObjects.SystemMargins()

    # musicxml requires both left and right defined
    matchLeft = False
    matchRight = False
    if systemLayout.leftMargin != None:
        mxSystemMargins.set('leftMargin', systemLayout.leftMargin)
        matchLeft = True
    if systemLayout.rightMargin != None:
        mxSystemMargins.set('rightMargin', systemLayout.rightMargin)
        matchRight = True

    if matchLeft and not matchRight:
        mxSystemMargins.set('rightMargin', 0)
    if matchRight and not matchLeft:
        mxSystemMargins.set('leftMargin', 0)

    # does not exist!
#    if systemLayout.topMargin != None:
#        mxSystemMargins.set('topMargin', systemLayout.topMargin)
#    if systemLayout.rightMargin != None:
#        mxSystemMargins.set('bottomMargin', systemLayout.bottomMargin)
 

    # stored on components list
    if matchLeft or matchRight:
        addMxSystemLayout = True
        mxSystemLayout.append(mxSystemMargins) 

    if systemLayout.distance != None:
        #mxSystemDistance = mxObjects.SystemDistance()
        #mxSystemDistance.set('charData', systemLayout.distance)
        # only append if defined
        addMxSystemLayout = True
        mxSystemLayout.systemDistance = systemLayout.distance
    if systemLayout.topDistance != None:
        addMxSystemLayout = True
        mxSystemLayout.topSystemDistance = systemLayout.topDistance

    if addMxSystemLayout is True:
        return mxSystemLayout
    else:
        return None

def staffLayoutToMxPrint(staffLayout):
    mxPrint = mxObjects.Print()
    mxStaffLayout = staffLayoutToMxStaffLayout(staffLayout)
    mxPrint.append(mxStaffLayout)
    return mxPrint

def staffLayoutToMxStaffLayout(staffLayout):
    '''
    
    >>> sl = layout.StaffLayout(distance=34.0, staffNumber=2)
    >>> mxStaffLayout = musicxml.toMxObjects.staffLayoutToMxStaffLayout(sl)    
    >>> mxStaffLayout
    <staff-layout number=2 staff-distance=34.0>
    '''
    mxStaffLayout = mxObjects.StaffLayout()
    mxStaffLayout.staffDistance = staffLayout.distance
    mxStaffLayout.set('number', staffLayout.staffNumber)
    return mxStaffLayout

def staffLayoutToMxStaffDetails(staffLayout):
    '''
    
    >>> sl = layout.StaffLayout(distance=34.0, staffNumber=2)
    >>> mxStaffLayout = musicxml.toMxObjects.staffLayoutToMxStaffLayout(sl)    
    >>> mxStaffLayout
    <staff-layout number=2 staff-distance=34.0>
    '''
    mxStaffDetails = mxObjects.StaffDetails()
    mxStaffDetails.staffLines = staffLayout.staffLines
    if staffLayout.hidden is True:
        mxStaffDetails._attr['print-object'] = 'no'
    return mxStaffDetails

#-----------------------------------------------------------------
# metadata

def metadataToMxScore(mdObj):
    '''
    Return a mxScore object from a :class:`~music21.metadata.Metadata` object.

    Note that an mxScore object is also where all the music is
    stored, so normally we call mxScore.merge(otherMxScore) where
    otherMxScore comes from converting the rest of the stream.
    
    '''
    mxScore = mxObjects.Score()

    # create and add work obj
    mxWork = mxObjects.Work()
    match = False
    if mdObj.title not in [None, '']:
        #environLocal.printDebug(['metadataToMx, got title', mdObj.title])
        match = True
        mxWork.set('workTitle', str(mdObj.title))
        #mxWork.set('workNumber', None)
    if match == True: # only attach if needed
        mxScore.set('workObj', mxWork)

    # musicxml often defaults to show only movement title       
    # if no movement title is found, get the .title attr
    if mdObj.movementName not in [None, '']:
        mxScore.set('movementTitle', str(mdObj.movementName))
    else: # it is none
        if mdObj.title != None:
            mxScore.set('movementTitle', str(mdObj.title))

    if mdObj.movementNumber not in [None, '']:
        mxScore.set('movementNumber', str(mdObj.movementNumber))

    # create and add identification obj
    mxId = mxObjects.Identification()
    hasContributor = False
    mxCreatorList = []
    for c in mdObj._contributors: # look at each contributor
        hasContributor = True # if more than zero
        # get an mx object
        mxCreator = contributorToMxCreator(c)
        mxCreatorList.append(mxCreator)
    if hasContributor is True: # only attach if needed
        mxId.set('creatorList', mxCreatorList)        
        mxScore.set('identificationObj', mxId)

    return mxScore

def contributorToMxCreator(contribObj):
    '''
    Return a mxCreator object from a :class:`~music21.metadata.Contributor` object.
    
    
    >>> md = metadata.Metadata()
    >>> md.composer = 'frank'
    >>> contrib = md._contributors[0]
    >>> contrib
    <music21.metadata.primitives.Contributor object at 0x...>
    >>> mxCreator = musicxml.toMxObjects.contributorToMxCreator(contrib)
    >>> mxCreator.get('charData')
    'frank'
    >>> mxCreator.get('type')
    'composer'
    '''
    mxCreator = mxObjects.Creator()
    # not sure what do if we have multiple names
    mxCreator.set('type', contribObj.role)
    mxCreator.set('charData', contribObj.name)        
    return mxCreator


#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testBasic(self):
        pass

    def testDuration2048(self):
        '''
        typeToMusicXMLType(): when converting a Duration to a MusicXML duration, 2048th notes will
            not be exported to MusicXML, for which 1024th is the shortest duration. 2048th notes
            are valid in MEI, which is how they appeared in music21 in the first place.
        '''
        expectedError = 'Cannot convert "2048th" duration to MusicXML (too short).'
        self.assertRaises(ToMxObjectsException, typeToMusicXMLType, '2048th')
        try:
            typeToMusicXMLType('2048th')
        except ToMxObjectsException as exc:
            self.assertEqual(expectedError, exc.args[0])


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [streamToMx, streamPartToMx, measureToMx]



if __name__ == "__main__":
    # sys.arg test options will be used in mainTest()
    import music21
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof
