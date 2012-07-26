# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         musicxml/translate.py
# Purpose:      Translate MusicXML and music21 objects
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2010-2012 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''Low-level conversion routines between MusicXML and music21.
'''


import unittest
import copy

import music21
from music21 import musicxml as musicxmlMod
from music21 import defaults
from music21 import common
from music21 import xmlnode

# modules that import this include stream.py, chord.py, note.py
# thus, cannot import these here

from music21 import environment
_MOD = "musicxml.translate.py"  
environLocal = environment.Environment(_MOD)





#-------------------------------------------------------------------------------
class TranslateException(Exception):
    pass

class NoteheadException(TranslateException):
    pass

class XMLBarException(TranslateException):
    pass

# def mod6IdLocal(spannerObj):
#     '''
#     returns the spanner idLocal as a number from 1-6 since
#     only 6 spanners of each type can be active at a time in musicxml
# 
#     >>> from music21 import *
#     >>> s = stream.Score()
#     >>> for i in range(10):
#     ...    sp = spanner.Glissando()
#     ...    sp.idLocal = i + 1
#     ...    s.insert(0, sp)
#     >>> for sp in s.getElementsByClass('Spanner'):
#     ...    print sp.idLocal, musicxml.translate.mod6IdLocal(sp)
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
    '''Given an already instantiated spanner.StaffGroup, configure it with parameters from an mxPartGroup.
    '''
    staffGroup.name = mxPartGroup.get('groupName')
    staffGroup.abbreviation = mxPartGroup.get('groupAbbreviation')
    staffGroup.symbol = mxPartGroup.get('groupSymbol')
    staffGroup.barTogether = mxPartGroup.get('groupBarline')
    staffGroup.completeStatus = True


def configureMxPartGroupFromStaffGroup(staffGroup):
    '''Create and configure an mxPartGroup object from a staff group spanner. Note that this object is not completely formed by this procedure.
    '''
    mxPartGroup = musicxmlMod.PartGroup()    
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
    '''Convert a music21 TextBox to a MusicXML Credit. 

    >>> from music21 import *
    >>> tb = text.TextBox('testing')
    >>> tb.positionVertical = 500
    >>> tb.positionHorizontal = 500
    >>> tb.page = 3
    >>> mxCredit = musicxml.translate.textBoxToMxCredit(tb)
    >>> print mxCredit
    <credit page=3 <credit-words halign=center default-y=500 default-x=500 valign=top charData=testing>>

    '''
    # use line carriages to separate messages
    mxCredit = musicxmlMod.Credit()
    # add all credit words to components
    count = 0

    mxCredit.set('page', textBox.page)
    for l in textBox.content.split('\n'):
        cw = musicxmlMod.CreditWords(l)
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

def mxCreditToTextBox(mxCredit):
    '''Convert a MusicXML credit to a music21 TextBox

    >>> from music21 import *
    >>> c = musicxml.Credit()
    >>> c.append(musicxml.CreditWords('testing'))
    >>> c.set('page', 2)
    >>> tb = musicxml.translate.mxCreditToTextBox(c)
    >>> tb.page
    2
    >>> tb.content
    'testing'
    '''
    from music21 import text
    tb = text.TextBox()
    tb.page = mxCredit.get('page')
    content = []
    for mxCreditWords in mxCredit: # can iterate
        content.append(mxCreditWords.charData)
    if len(content) == 0: # no text defined
        raise TranslateException('no credit words defined for a credit tag')
    tb.content = '\n'.join(content) # join with \n
    # take formatting from the first, no matter if multiple are defined
    tb.positionVertical = mxCredit.componentList[0].get('default-x')
    tb.positionHorizontal = mxCredit.componentList[0].get('default-y')
    tb.justify = mxCredit.componentList[0].get('justify')
    tb.style = mxCredit.componentList[0].get('font-style')
    tb.weight = mxCredit.componentList[0].get('font-weight')
    tb.size = mxCredit.componentList[0].get('font-size')
    tb.alignVertical = mxCredit.componentList[0].get('valign')
    tb.alignHorizontal = mxCredit.componentList[0].get('halign')
    return tb



def mxTransposeToInterval(mxTranspose):
    '''Convert a MusicXML Transpose object to a music21 Interval object.

    >>> from music21 import *
    >>> t = musicxml.Transpose()
    >>> t.diatonic = -1
    >>> t.chromatic = -2
    >>> musicxml.translate.mxTransposeToInterval(t)
    <music21.interval.Interval M-2>

    >>> t = musicxml.Transpose()
    >>> t.diatonic = -5
    >>> t.chromatic = -9
    >>> musicxml.translate.mxTransposeToInterval(t)
    <music21.interval.Interval M-6>

    >>> t = musicxml.Transpose()
    >>> t.diatonic = 3 # a type of 4th
    >>> t.chromatic = 6
    >>> musicxml.translate.mxTransposeToInterval(t)
    <music21.interval.Interval A4>

    '''
    from music21 import interval

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
    #environLocal.pd(['ds', ds, 'cs', cs, 'oc', oc])
    if ds is not None and ds != 0 and cs is not None and cs != 0:
        # diatonic step can be used as a generic specifier here if 
        # shifted 1 away from zero
        if ds < 0:
            post = interval.intervalFromGenericAndChromatic(ds-1, cs+oc)
        else:
            post = interval.intervalFromGenericAndChromatic(ds+1, cs+oc)
    else: # assume we have chromatic; may not be correct spelling
        post = interval.Interval(cs + oc)
    return post

def intervalToMXTranspose(int):
    '''Convert a music21 Interval into a musicxml transposition specification
    
    >>> from music21 import *
    >>> musicxml.translate.intervalToMXTranspose(interval.Interval('m6'))
    <transpose diatonic=5 chromatic=8>
    >>> musicxml.translate.intervalToMXTranspose(interval.Interval('-M6'))
    <transpose diatonic=-5 chromatic=-9>
    '''
    mxTranspose = musicxmlMod.Transpose()

    rawSemitones = int.chromatic.semitones # will be directed
    octShift = 0
    if abs(rawSemitones) > 12:
        octShift, semitones = divmod(rawSemitones, 12)
    else:
        semitones = rawSemitones

    rawGeneric = int.diatonic.generic.directed
    if octShift != 0:
        # need to shift 7 for each octave; sign will be correct
        generic = rawGeneric + (octShift * 7)
    else:
        generic = rawGeneric

    # must implement the necessary shifts
    if int.generic.directed > 0:
        mxTranspose.diatonic = generic - 1
    elif int.generic.directed < 0:    
        mxTranspose.diatonic = generic + 1

    mxTranspose.chromatic = semitones

    if octShift != 0:
        mxTranspose.octaveChange = octShift
    return mxTranspose


def mxToTempoIndication(mxMetronome, mxWords=None):
    '''Given an mxMetronome, convert to either a TempoIndication subclass, either a tempo.MetronomeMark or tempo.MetricModulation. 

    >>> from music21 import *
    >>> m = musicxml.Metronome()
    >>> bu = musicxml.BeatUnit('half')
    >>> pm = musicxml.PerMinute(125)
    >>> m.append(bu)
    >>> m.append(pm)
    >>> musicxml.translate.mxToTempoIndication(m)
    <music21.tempo.MetronomeMark Half=125.0>
    '''
    from music21 import tempo, duration
    # get lists of durations and texts
    durations = []
    numbers = [] 

    dActive = None
    for mxObj in mxMetronome.componentList:
        if isinstance(mxObj, musicxmlMod.BeatUnit):
            type = duration.musicXMLTypeToType(mxObj.charData)
            dActive = duration.Duration(type=type)
            durations.append(dActive)
        if isinstance(mxObj, musicxmlMod.BeatUnitDot):
            if dActive is None:
                raise TranslateException('encountered metronome components out of order')
            dActive.dots += 1 # add one dot each time these are encountered
        # should come last
        if isinstance(mxObj, musicxmlMod.PerMinute):      
            #environLocal.printDebug(['found PerMinute', mxObj])
            # store as a number
            if mxObj.charData != '':
                numbers.append(float(mxObj.charData))

    if mxMetronome.isMetricModulation():
        mm = tempo.MetricModulation()
        #environLocal.printDebug(['found metric modulaton:', 'durations', durations])
        if len(durations) < 2:
            raise TranslateException('found incompletely specified musicxml metric moduation: less than 2 duration defined')
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


def tempoIndicationToMx(ti):
    '''Given a music21 MetronomeMark or MetricModulation, produce a musicxml Metronome tag wrapped in a <direction> tag.

    >>> from music21 import *
    >>> mm = tempo.MetronomeMark("slow", 40, note.HalfNote())
    >>> mxList = musicxml.translate.tempoIndicationToMx(mm)
    >>> mxList
    [<direction <direction-type <metronome parentheses=no <beat-unit charData=half> <per-minute charData=40>>> <sound tempo=80.0>>, <direction <direction-type <words default-y=45.0 font-weight=bold justify=left charData=slow>>>]

    >>> mm = tempo.MetronomeMark("slow", 40, duration.Duration(quarterLength=1.5))
    >>> mxList = musicxml.translate.tempoIndicationToMx(mm)
    >>> mxList
    [<direction <direction-type <metronome parentheses=no <beat-unit charData=quarter> <beat-unit-dot > <per-minute charData=40>>> <sound tempo=60.0>>, <direction <direction-type <words default-y=45.0 font-weight=bold justify=left charData=slow>>>]

    '''
    from music21 import duration

    # if writing just a sound tag, place an empty words tag in a durection type and then follow with sound declaration

    # storing lists to accomodate metric modulations
    durs = [] # duration objects
    numbers = [] # tempi
    hideNumericalMetro = False # if numbers implicit, hide metro
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
            hideNumber.append(True) # cannot show numbers in a metric mod
            durs.append(sub.referent)
            numbers.append(sub.number)
        # soundingQuarterBPM should be obtained from the last MetronomeMark
        soundingQuarterBPM = ti.newMetronome.getQuarterBPM()

        #environLocal.printDebug(['found metric modulation', ti, durs, numbers])

    mxComponents = []
    for i, d in enumerate(durs):
        # charData of BeatUnit is the type string
        mxSub = musicxmlMod.BeatUnit(duration.typeToMusicXMLType(d.type))
        mxComponents.append(mxSub)
        for x in range(d.dots):
            mxComponents.append(musicxmlMod.BeatUnitDot())
        if len(numbers) > 0:
            if not hideNumber[i]:
                mxComponents.append(musicxmlMod.PerMinute(numbers[0]))

    #environLocal.printDebug(['mxComponents', mxComponents])

    # store all accumulated mxDirection objects
    mxObjects = [] 

    if not hideNumericalMetro:
        mxMetro = musicxmlMod.Metronome()
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
        mxDirectionType = musicxmlMod.DirectionType()
        mxDirectionType.append(mxMetro)
        mxDirection = musicxmlMod.Direction()
        mxDirection.append(mxDirectionType)

        # sound tag goes last, in mxDirection, not mxDirectionType
        if soundingQuarterBPM is not None:
            mxSound = musicxmlMod.Sound()
            mxSound.set('tempo', soundingQuarterBPM)
            mxDirection.append(mxSound)

        mxObjects.append(mxDirection)    

    # if there is an explicit text entry, add to list of mxObjets
    # for now, only getting text expressions for non-metric mods
    if 'MetronomeMark' in ti.classes:
        if ti.getTextExpression(returnImplicit=False) is not None:
            mxDirection = textExpressionToMx(
                          ti.getTextExpression(returnImplicit=False))
            mxObjects.append(mxDirection)    

    return mxObjects


def repeatToMx(r):
    '''
    >>> from music21 import *
    >>> b = bar.Repeat(direction='end')
    >>> mxBarline = b.mx
    >>> mxBarline.get('barStyle')
    'light-heavy'
    '''
    mxBarline = musicxmlMod.Barline()
    if r.style is not None:
        mxBarline.set('barStyle', r.musicXMLBarStyle)

    if r.location is not None:
        mxBarline.set('location', r.location)

    mxRepeat = musicxmlMod.Repeat()
    if r.direction == 'start':
        mxRepeat.set('direction', 'forward')
    elif r.direction == 'end':
        mxRepeat.set('direction', 'backward')
#         elif self.direction == 'bidirectional':
#             environLocal.printDebug(['skipping bi-directional repeat'])
    else:
        raise music21.bar.BarException('cannot handle direction format:', r.direction)

    if r.times != None:
        mxRepeat.set('times', r.times)

    mxBarline.set('repeatObj', mxRepeat)
    return mxBarline

def mxToRepeat(mxBarline, inputM21=None):
    '''Given an mxBarline, file the necessary parameters

    >>> from music21 import *
    >>> mxRepeat = musicxml.Repeat()
    >>> mxRepeat.set('direction', 'backward')
    >>> mxRepeat.get('times') == None
    True
    >>> mxBarline = musicxml.Barline()
    >>> mxBarline.set('barStyle', 'light-heavy')
    >>> mxBarline.set('repeatObj', mxRepeat)
    >>> b = bar.Repeat()
    >>> b.mx = mxBarline
    
    Test that the music21 style for a backwards repeat is called "final"
    (because it resembles a final barline) but that the musicxml style
    is called light-heavy.
    
    >>> b.style
    'final'
    >>> b.direction
    'end'
    >>> b.mx.get('barStyle')
    'light-heavy'
    '''
    from music21 import bar
    if inputM21 == None:
        r = bar.Repeat()
    else:
        r = inputM21

    r.style = mxBarline.get('barStyle')
    location = mxBarline.get('location')
    if location != None:
        r.location = location

    mxRepeat = mxBarline.get('repeatObj')
    if mxRepeat == None:
        raise music21.bar.BarException('attempting to create a Repeat from an MusicXML bar that does not define a repeat')

    mxDirection = mxRepeat.get('direction')

    #environLocal.printDebug(['mxRepeat', mxRepeat, mxRepeat._attr])

    if mxDirection.lower() == 'forward':
        r.direction = 'start'
    elif mxDirection.lower() == 'backward':
        r.direction = 'end'
    else:
        raise music21.bar.BarException('cannot handle mx direction format:', mxDirection)

    if mxRepeat.get('times') != None:
        # make into a number
        r.times = int(mxRepeat.get('times'))



#-------------------------------------------------------------------------------
def mxGraceToGrace(noteOrChord, mxGrace=None):
    '''Given a completely formed, non-grace Note or Chord, create and return a m21 grace version of the same.

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


def durationToMxGrace(d, mxNoteList):
    '''Given a music21 duration and a list of mxNotes, edit the mxNotes in place if the duration is a GraceDuration
    '''
    if d.isGrace: # this is a class attribute, not a property/method
        for mxNote in mxNoteList:
            mxGrace = musicxmlMod.Grace()
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

def pitchToMx(p):
    '''
    Returns a musicxml.Note() object

    >>> from music21 import *
    >>> a = pitch.Pitch('g#4')
    >>> c = musicxml.translate.pitchToMx(a)
    >>> c.get('pitch').get('step')
    'G'
    '''
    mxPitch = musicxmlMod.Pitch()
    mxPitch.set('step', p.step)
    if p.accidental is not None:
        # need to use integers when possible in order to support
        # xml readers that force alter to be an integer
        mxPitch.set('alter', common.numToIntOrFloat(p.accidental.alter))
    mxPitch.set('octave', p.implicitOctave)

    mxNote = musicxmlMod.Note()
    mxNote.setDefaults() # note: this sets the duration to a default value
    mxNote.set('pitch', mxPitch)

    if (p.accidental is not None and 
        p.accidental.displayStatus in [True, None]):
        mxNote.set('accidental', p.accidental.mx)
    # should this also return an xml accidental object
    return mxNote # return element object

def mxToPitch(mxNote, inputM21=None):
    '''
    Given a MusicXML Note object, set this Pitch object to its values. 

    >>> from music21 import *
    >>> b = musicxml.Pitch()
    >>> b.set('octave', 3)
    >>> b.set('step', 'E')
    >>> b.set('alter', -1)
    >>> c = musicxml.Note()
    >>> c.set('pitch', b)
    >>> a = pitch.Pitch('g#4')
    >>> a = musicxml.translate.mxToPitch(c)
    >>> print(a)
    E-3
    '''
    from music21 import pitch
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
            accObj = pitch.Accidental()
            accObj.mx = mxAccidental
        # used to to just use acc value
        #self.accidental = Accidental(float(acc))
        # better to use accObj if possible
            p.accidental = accObj
            p.accidental.displayStatus = True
        else:
            # here we generate an accidental object from the alter value
            # but in the source, there was not a defined accidental
            try:
                p.accidental = pitch.Accidental(float(acc))
            except music21.pitch.AccidentalException:
                raise TranslateException('incorrect accidental %s for pitch %s' % (str(acc), p))
            p.accidental.displayStatus = False
    p.octave = int(mxPitch.get('octave'))
    p._pitchSpaceNeedsUpdating = True
    return p

def pitchToMusicXML(p):
    from music21 import stream, note
    n = note.Note()
    n.pitch = copy.deepcopy(p)
    out = stream.Stream()
    out.append(n)
    # call the musicxml property on Stream
    return out.musicxml


#-------------------------------------------------------------------------------
# Ties

def tieToMx(t):
    '''
    Translate a music21 :class:`~music21.tie.Tie` object to 
    MusicXML :class:`~music21.musicxml.Tie` (representing sound) and 
    :class:`~music21.musicxml.Tied` (representing notation) 
    objects as two component lists.

    '''
    mxTieList = []
    mxTie = musicxmlMod.Tie()
    if t.type == 'continue':
        musicxmlTieType = 'stop'
    else:
        musicxmlTieType = t.type
    mxTie.set('type', musicxmlTieType) # start, stop
    mxTieList.append(mxTie) # goes on mxNote.tieList

    if t.type == 'continue':
        mxTie = musicxmlMod.Tie()
        mxTie.set('type', 'start')
        mxTieList.append(mxTie) # goes on mxNote.tieList

    mxTiedList = []
    if t.style != 'hidden': # tie style -- dotted and dashed not supported yet        
        mxTied = musicxmlMod.Tied()
        mxTied.set('type', musicxmlTieType) # start, stop
        mxTiedList.append(mxTied) # goes on mxNote.notationsObj list
    if t.type == 'continue':
        if t.style != 'hidden': # tie style -- dotted and dashed not supported yet        
            mxTied = musicxmlMod.Tied()
            mxTied.set('type', 'start')
            mxTiedList.append(mxTied) 
    
    #environLocal.printDebug(['mxTieList', mxTieList])
    return mxTieList, mxTiedList


def mxToTie(mxNote, inputM21=None):
    '''Translate a MusicXML :class:`~music21.musicxml.Note` to a music21 :class:`~music21.tie.Tie` object.
    '''
    from music21 import note
    from music21 import tie

    if inputM21 == None:
        from music21 import note
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
            environLocal.printDebug(['found unexpected arrangement of multiple tie types when importing from musicxml:', typesFound])    

# from old note.py code
    # not sure this is necessary
#         mxNotations = mxNote.get('notations')
#         if mxNotations != None:
#             mxTiedList = mxNotations.getTieds()
            # should be sufficient to only get mxTieList



#-------------------------------------------------------------------------------
# Lyrics

def lyricToMx(l):
    '''Translate a music21 :class:`~music21.note.Lyric` object to a MusicXML :class:`~music21.musicxml.Lyric` object. 
    '''
    mxLyric = musicxmlMod.Lyric()
    mxLyric.set('text', l.text)
    mxLyric.set('number', l.number)
    # mxl expects begin, middle, end, as well as single
    mxLyric.set('syllabic', l.syllabic)
    return mxLyric


def mxToLyric(mxLyric, inputM21=None):
    '''Translate a MusicXML :class:`~music21.musicxml.Lyric` object to a music21 :class:`~music21.note.Lyric` object. 
    '''
    if inputM21 == None:
        from music21 import note
        l = note.Lyric()
    else:
        l = inputM21

    l.text = mxLyric.get('text')
    l.number = mxLyric.get('number')
    l.syllabic = mxLyric.get('syllabic')


#-------------------------------------------------------------------------------
# Durations

def mxToDuration(mxNote, inputM21=None):
    '''Translate a MusicXML :class:`~music21.musicxml.Note` object to a music21 :class:`~music21.duration.Duration` object. 

    >>> from music21 import *
    >>> a = musicxml.Note()
    >>> a.setDefaults()
    >>> m = musicxml.Measure()
    >>> m.setDefaults()
    >>> a.external['measure'] = m # assign measure for divisions ref
    >>> a.external['divisions'] = m.external['divisions']
    >>> c = duration.Duration()
    >>> musicxml.translate.mxToDuration(a, c)
    <music21.duration.Duration 1.0>
    >>> c.quarterLength
    1.0

    '''
    from music21 import duration
    if inputM21 == None:
        d = duration.Duration
    else:
        d = inputM21

    if mxNote.external['measure'] == None:
        raise TranslateException(
        "cannont determine MusicXML duration without a reference to a measure (%s)" % mxNote)

    mxDivisions = mxNote.external['divisions']
    if mxNote.duration is not None: 
        if mxNote.get('type') is not None:
            type = duration.musicXMLTypeToType(mxNote.get('type'))
            forceRaw = False
        else: # some rests do not define type, and only define duration
            type = None # no type to get, must use raw
            forceRaw = True
        mxDotList = mxNote.get('dotList')
        # divide mxNote duration count by divisions to get qL
        qLen = float(mxNote.duration) / float(mxDivisions)
        mxNotations = mxNote.get('notationsObj')
        mxTimeModification = mxNote.get('timeModificationObj')

        if mxTimeModification is not None:
            tup = duration.Tuplet()
            tup.mx = mxNote # get all necessary config from mxNote
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
                environLocal.warn(['Duration._setMX', 'supplying quarterLength of 1 as type is not defined and raw quarterlength (%s) is not a computable duration' % qLen])
                environLocal.printDebug(['Duration._setMX', 'raw qLen', qLen, type, 'mxNote.duration:', mxNote.duration, 'last mxDivisions:', mxDivisions])
                durRaw.quarterLength = 1.
        else: # a cooked version builds up from pieces
            durUnit = duration.DurationUnit()
            durUnit.type = type
            durUnit.dots = len(mxDotList)
            if not tup == None:
                durUnit.appendTuplet(tup)
            durCooked = duration.Duration(components=[durUnit])
            if durUnit.quarterLength != durCooked.quarterLength:
                environLocal.printDebug(['error in stored MusicXML representaiton and duration value', durCooked])
            # old way just used qLen
            #self.quarterLength = qLen
            d.components = durCooked.components
    # if mxNote.duration is None, this is a grace note, and duration
    # is based entirely on type
    if mxNote.duration is None: 
        durUnit = duration.DurationUnit()
        durUnit.type = duration.musicXMLTypeToType(mxNote.get('type'))
        durUnit.dots = len(mxNote.get('dotList'))
        d.components = [durUnit]
        #environLocal.pd(['got mx duration of None', d])

    return d


def durationToMx(d):
    '''
    Translate a music21 :class:`~music21.duration.Duration` object to a list 
    of one or more MusicXML :class:`~music21.musicxml.Note` objects. 


    All rhythms and ties necessary in the MusicXML Notes are configured. The returned mxNote objects are incompletely specified, lacking full representation and information on pitch, etc.


    >>> from music21 import *
    >>> a = duration.Duration()
    >>> a.quarterLength = 3
    >>> b = musicxml.translate.durationToMx(a)
    >>> len(b) == 1
    True
    >>> isinstance(b[0], musicxmlMod.Note)
    True


    >>> a = duration.Duration()
    >>> a.quarterLength = .33333333
    >>> b = musicxml.translate.durationToMx(a)
    >>> len(b) == 1
    True
    >>> isinstance(b[0], musicxmlMod.Note)
    True



    >>> a = duration.Duration()
    >>> a.quarterLength = .625
    >>> b = musicxml.translate.durationToMx(a)
    >>> len(b) == 2
    True
    >>> isinstance(b[0], musicxmlMod.Note)
    True



    >>> a = duration.Duration()
    >>> a.type = 'half'
    >>> a.dotGroups = [1,1]
    >>> b = musicxml.translate.durationToMx(a)
    >>> len(b) == 2
    True
    >>> isinstance(b[0], musicxmlMod.Note)
    True

    '''
    from music21 import duration
    post = [] # rename mxNoteList for consistencuy
        
    #environLocal.printDebug(['in _getMX', d, d.quarterLength, 'isGrace', d.isGrace])

    if d.dotGroups is not None and len(d.dotGroups) > 1:
        d = d.splitDotGroups()
    # most common case...
    # a grace is not linked, but still needs to be processed as a grace
    if (d.isLinked is True or len(d.components) > 1 or 
        (len(d.components) > 1 and d.isGrace)): 
        for dur in d.components:
            mxDivisions = int(defaults.divisionsPerQuarter * 
                              dur.quarterLength)
            mxType = duration.typeToMusicXMLType(dur.type)
            # check if name is not in collection of MusicXML names, which does 
            # not have maxima, etc.
            mxDotList = []
            # only presently looking at first dot group
            # also assuming that these are integer values
            # need to handle fractional dots differently
            for x in range(int(dur.dots)):
                # only need to create object
                mxDotList.append(musicxmlMod.Dot())
            mxNote = musicxmlMod.Note()
            if not d.isGrace:
                mxNote.set('duration', mxDivisions)
            mxNote.set('type', mxType)
            mxNote.set('dotList', mxDotList)
            post.append(mxNote)
    else: # simple duration that is unlinked
        mxDivisions = int(defaults.divisionsPerQuarter * 
                          d.quarterLength)
        mxType = duration.typeToMusicXMLType(d.type)
        # check if name is not in collection of MusicXML names, which does 
        # not have maxima, etc.
        mxDotList = []
        # only presently looking at first dot group
        # also assuming that these are integer values
        # need to handle fractional dots differently
        for x in range(int(d.dots)):
            # only need to create object
            mxDotList.append(musicxmlMod.Dot())
        mxNote = musicxmlMod.Note()
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
        mxNotations = musicxmlMod.Notations()
        # only need ties if more than one component
        mxTieList = []
        if len(d.components) > 1:
            if i == 0:
                mxTie = musicxmlMod.Tie()
                mxTie.set('type', 'start') # start, stop
                mxTieList.append(mxTie)
                mxTied = musicxmlMod.Tied()
                mxTied.set('type', 'start') 
                mxNotations.append(mxTied)
            elif i == len(d.components) - 1: #end 
                mxTie = musicxmlMod.Tie()
                mxTie.set('type', 'stop') # start, stop
                mxTieList.append(mxTie)
                mxTied = musicxmlMod.Tied()
                mxTied.set('type', 'stop') 
                mxNotations.append(mxTied)
            else: # continuation
                for type in ['stop', 'start']:
                    mxTie = musicxmlMod.Tie()
                    mxTie.set('type', type) # start, stop
                    mxTieList.append(mxTie)
                    mxTied = musicxmlMod.Tied()
                    mxTied.set('type', type) 
                    mxNotations.append(mxTied)
        if len(d.components) > 1:
            mxNote.set('tieList', mxTieList)
        if len(dur.tuplets) > 0:
            # only getting first tuplet here
            mxTimeModification, mxTupletList = dur.tuplets[0].mx
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
#             mxGrace = musicxmlMod.Grace()
#             mxNote.graceObj = mxGrace
#             #environLocal.pd(['final mxNote with mxGrace duration', mxNote.get('duration')])
    return post # a list of mxNotes


def durationToMusicXML(d):
    '''Translate a music21 :class:`~music21.duration.Duration` into a complete MusicXML representation. 
    '''
    from music21 import duration, note

    # make a copy, as we this process will change tuple types
    dCopy = copy.deepcopy(d)
    n = note.Note()
    n.duration = dCopy
    # call the musicxml property on Stream
    return generalNoteToMusicXML(n)



def mxToOffset(mxDirection, mxDivisions):
    '''Translate a MusicXML :class:`~music21.musicxml.Direction` with an offset value to an offset in music21. 
    '''
    if mxDivisions is None:
        raise TranslateException(
        "cannont determine MusicXML duration without a reference to a measure (%s)" % mxDirection)
    if mxDirection.offset is None:
        return 0.0
    else:
        #environLocal.printDebug(['mxDirection.offset', mxDirection.offset, 'mxDivisions', mxDivisions])
        return float(mxDirection.offset) / float(mxDivisions)




#-------------------------------------------------------------------------------
# Meters

def timeSignatureToMx(ts):
    '''Returns a single mxTime object.
    
    Compound meters are represented as multiple pairs of beat
    and beat-type elements

    >>> from music21 import *
    >>> a = meter.TimeSignature('3/4')
    >>> b = timeSignatureToMx(a)
    >>> a = meter.TimeSignature('3/4+2/4')
    >>> b = timeSignatureToMx(a)
    '''
    from music21 import meter
    #mxTimeList = []
    mxTime = musicxmlMod.Time()
    # always get a flat version to display any subivisions created
    fList = [(mt.numerator, mt.denominator) for mt in ts.displaySequence.flat._partition]
    if ts.summedNumerator:
        # this will try to reduce any common denominators into 
        # a common group
        fList = meter.fractionToSlashMixed(fList)

    for n,d in fList:
        mxBeats = musicxmlMod.Beats(n)
        mxBeatType = musicxmlMod.BeatType(d)
        mxTime.componentList.append(mxBeats)
        mxTime.componentList.append(mxBeatType)

    # can set this to common when necessary
    mxTime.set('symbol', None)
    # for declaring no time signature present
    mxTime.set('senza-misura', None)
    #mxTimeList.append(mxTime)
    #return mxTimeList
    return mxTime

def mxToTimeSignature(mxTimeList, inputM21=None):
    '''Given an mxTimeList, load this object 

    >>> from music21 import *
    >>> a = musicxml.Time()
    >>> a.setDefaults()
    >>> b = musicxml.Attributes()
    >>> b.timeList.append(a)
    >>> c = meter.TimeSignature()
    >>> mxToTimeSignature(b.timeList, c)
    >>> c.numerator
    4
    '''
    from music21 import meter
    if inputM21 == None:
        ts = meter.TimeSignature()
    else:
        ts = inputM21

    if not common.isListLike(mxTimeList): # if just one
        mxTime = mxTimeList
    else: # there may be more than one if we have more staffs per part
        mxTime = mxTimeList[0]

#         if len(mxTimeList) == 0:
#             raise MeterException('cannot create a TimeSignature from an empty MusicXML timeList: %s' % musicxml.Attributes() )
#         mxTime = mxTimeList[0] # only one for now

    n = []
    d = []
    for obj in mxTime.componentList:
        if isinstance(obj, musicxmlMod.Beats):
            n.append(obj.charData) # may be 3+2
        if isinstance(obj, musicxmlMod.BeatType):
            d.append(obj.charData)

    #n = mxTime.get('beats')
    #d = mxTime.get('beat-type')
    # convert into a string
    msg = []
    for i in range(len(n)):
        msg.append('%s/%s' % (n[i], d[i]))

    #environLocal.printDebug(['loading meter string:', '+'.join(msg)])
    ts.load('+'.join(msg))
    

def timeSignatureToMusicXML(ts):
    # return a complete musicxml representation
    from music21 import stream, note
    tsCopy = copy.deepcopy(ts)
#         m = stream.Measure()
#         m.timeSignature = tsCopy
#         m.append(note.Rest())
    out = stream.Stream()
    out.append(tsCopy)
    return out.musicxml

#-------------------------------------------------------------------------------
# Dyanmics

def dynamicToMx(d):
    '''
    Return an mx direction
    returns a musicxml.Direction object

    >>> from music21 import *
    >>> a = dynamics.Dynamic('ppp')
    >>> a.volumeScalar
    0.15
    >>> a._positionRelativeY = -10
    >>> b = musicxml.translate.dynamicToMx(a)
    >>> b[0][0][0].get('tag')
    'ppp'
    >>> b[1].get('tag')
    'sound'
    >>> b[1].get('dynamics')
    '19'

    '''
    mxDynamicMark = musicxmlMod.DynamicMark(d.value)
    mxDynamics = musicxmlMod.Dynamics()
    for src, dst in [(d._positionDefaultX, 'default-x'), 
                     (d._positionDefaultY, 'default-y'), 
                     (d._positionRelativeX, 'relative-x'),
                     (d._positionRelativeY, 'relative-y')]:
        if src is not None:
            mxDynamics.set(dst, src)
    mxDynamics.append(mxDynamicMark) # store on component list
    mxDirectionType = musicxmlMod.DirectionType()
    mxDirectionType.append(mxDynamics)
    mxDirection = musicxmlMod.Direction()
    mxDirection.append(mxDirectionType)
    
    # sound...
    vS = d.volumeScalar
    if vS is not None:
        mxSound = musicxmlMod.Sound()
        dynamicVolume = int(vS * 127)
        mxSound.set('dynamics', str(dynamicVolume))
        mxDirection.append(mxSound)

    mxDirection.set('placement', d._positionPlacement)
    return mxDirection


def mxToDynamicList(mxDirection):
    '''
    Given an mxDirection, load instance

    >>> from music21 import *
    >>> mxDirection = musicxml.Direction()
    >>> mxDirectionType = musicxml.DirectionType()
    >>> mxDynamicMark = musicxml.DynamicMark('ff')
    >>> mxDynamics = musicxml.Dynamics()
    >>> mxDynamics.set('default-y', -20)
    >>> mxDynamics.append(mxDynamicMark)
    >>> mxDirectionType.append(mxDynamics)
    >>> mxDirection.append(mxDirectionType)

    >>> a = dynamics.Dynamic()
    >>> a = musicxml.translate.mxToDynamicList(mxDirection)[0]
    >>> a.value
    'ff'
    >>> a.englishName
    'very loud'
    >>> a._positionDefaultY
    -20
    '''
    from music21 import dynamics

    # can probably replace this with mxDirection.getDynamicMark()
    # need to test
    mxDynamics = None
    for mxObj in mxDirection:
        if isinstance(mxObj, musicxmlMod.DirectionType):
            for mxObjSub in mxObj:
                if isinstance(mxObjSub, musicxmlMod.Dynamics):
                    mxDynamics = mxObjSub
    if mxDynamics == None:
        raise dynamics.DynamicException('when importing a Dynamics object from MusicXML, did not find a DynamicMark')            
#     if len(mxDynamics) > 1:
#         raise dynamics.DynamicException('when importing a Dynamics object from MusicXML, found more than one DynamicMark contained, namely %s' % str(mxDynamics))

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


def textExpressionToMx(te):
    '''Convert a TextExpression to a MusicXML mxDirection type.
    returns a musicxml.Direction object
    '''
    mxWords = musicxmlMod.Words(te.content)
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

    mxDirectionType = musicxmlMod.DirectionType()
    mxDirectionType.append(mxWords)

    mxDirection = musicxmlMod.Direction()
    mxDirection.append(mxDirectionType)
    # this parameter does not seem to do anything with text expressions
    #mxDirection.set('placement', d._positionPlacement)
    return mxDirection


def mxToTextExpression(mxDirection):
    '''
    Given an mxDirection, create one or more TextExpressions
    '''
    from music21 import expressions
    post = []
    mxWordsList = mxDirection.getWords()
    for mxWords in mxWordsList:
        #environLocal.printDebug(['mxToTextExpression()', mxWords, mxWords.charData])
        # content can be be passed with creation argument
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
    '''Translate a MusicXML :class:`~music21.musicxml.Coda` object to a music21 :class:`~music21.repeat.Coda` object. 
    '''
    from music21 import repeat
    rm = repeat.Coda()
    rm._positionDefaultX = mxCoda.get('default-x')
    rm._positionDefaultY = mxCoda.get('default-y')
    return rm

def codaToMx(rm):
    '''Returns a musicxml.Direction object

    >>> from music21 import *
    '''
    if rm.useSymbol:
        mxCoda = musicxmlMod.Coda()
        for src, dst in [(rm._positionDefaultX, 'default-x'), 
                         (rm._positionDefaultY, 'default-y'), 
                         (rm._positionRelativeX, 'relative-x'),
                         (rm._positionRelativeY, 'relative-y')]:
            if src is not None:
                mxCoda.set(dst, src)
        mxDirectionType = musicxmlMod.DirectionType()
        mxDirectionType.append(mxCoda)
        mxDirection = musicxmlMod.Direction()
        mxDirection.append(mxDirectionType)
        mxDirection.set('placement', rm._positionPlacement)
        return mxDirection
    else:
        # simply get the text expression version and convert
        # returns an mxDirection
        return textExpressionToMx(rm.getTextExpression()) 

def mxToSegno(mxCoda):
    '''Translate a MusicXML :class:`~music21.musicxml.Coda` object to a music21 :class:`~music21.repeat.Coda` object. 
    '''
    from music21 import repeat
    rm = repeat.Segno()
    rm._positionDefaultX = mxCoda.get('default-x')
    rm._positionDefaultY = mxCoda.get('default-y')
    return rm

def segnoToMx(rm):
    '''Returns a musicxml.Direction object

    >>> from music21 import *
    '''
    mxSegno = musicxmlMod.Segno()
    for src, dst in [(rm._positionDefaultX, 'default-x'), 
                     (rm._positionDefaultY, 'default-y'), 
                     (rm._positionRelativeX, 'relative-x'),
                     (rm._positionRelativeY, 'relative-y')]:
        if src is not None:
            mxSegno.set(dst, src)
    mxDirectionType = musicxmlMod.DirectionType()
    mxDirectionType.append(mxSegno)
    mxDirection = musicxmlMod.Direction()
    mxDirection.append(mxDirectionType)
    mxDirection.set('placement', rm._positionPlacement)
    return mxDirection


def mxToRepeatExpression(mxDirection):
    '''Given an mxDirection that may define a coda, segno, or other repeat expression statement, realize the appropriate music21 object. 
    '''
    pass
    # note: this may not be needed, as mx text expressions are converted to repeat objects in measure processing

#-------------------------------------------------------------------------------
# Harmony

def mxToChordSymbol(mxHarmony):
    #environLocal.printDebug(['mxToChordSymbol():', mxHarmony])
    from music21 import harmony
    from music21 import pitch

    cs = harmony.ChordSymbol()

    mxKind = mxHarmony.get('kind')
    if mxKind is not None:
        cs.XMLkind = mxKind.charData
        mxKindText = mxKind.get('text')
        if mxKindText is not None:
            cs.XMLkindStr = mxKindText
    
    mxRoot = mxHarmony.get('root')
    if mxRoot is not None:
        r = pitch.Pitch(mxRoot.get('rootStep'))
        if mxRoot.get('rootAlter') is not None:
            # can provide integer to create accidental on pitch
            r.accidental = pitch.Accidental(int(mxRoot.get('rootAlter')))
        # set Pitch object on Harmony
        cs.XMLroot = r

    mxBass = mxHarmony.get('bass')
    if mxBass is not None:
        b = pitch.Pitch(mxBass.get('bassStep'))
        if mxBass.get('bassAlter') is not None:
            # can provide integer to create accidental on pitch
            b.accidental = pitch.Accidental(int(mxBass.get('bassAlter')))
        # set Pitch object on Harmony
        cs.XMLbass = b

    mxInversion = mxHarmony.get('inversion')
    if mxInversion is not None:
        cs.XMLinversion = int(mxInversion) # must be an int

    mxFunction = mxHarmony.get('function')
    if mxFunction is not None:
        cs.romanNumeral = mxFunction # goes to roman property

    mxDegree = mxHarmony.get('degree')
    if mxDegree is not None: # a list of components
        ChordStepModifications = []
        hd = None
        for mxSub in mxDegree.componentList:
            # this is the assumed order of triples
            if isinstance(mxSub, musicxmlMod.DegreeValue):
                if hd is not None: # already set
                    ChordStepModifications.append(hd)
                    hd = None
                if hd is None:
                    hd = harmony.ChordStepModification() 
                hd.degree = int(mxSub.charData)
            elif isinstance(mxSub, musicxmlMod.DegreeAlter):
                hd.interval = int(mxSub.charData)
            elif isinstance(mxSub, musicxmlMod.DegreeType):
                hd.type = mxSub.charData
            else:
                raise TranslateException('found unexpected object in degree tag: %s' % mxSub)
        # must get last on loop exit
        if hd is not None: 
            ChordStepModifications.append(hd)
        for hd in ChordStepModifications:
            cs.addChordStepModification(hd)

    #environLocal.printDebug(['mxToHarmony(): Harmony object', h])
    return cs
    

def chordSymbolToMx(cs):
    '''
    >>> from music21 import *
    >>> cs = harmony.ChordSymbol()
    >>> cs.XMLroot = 'E-'
    >>> cs.XMLbass = 'B-'
    >>> cs.XMLinversion = 2
    >>> cs.romanNumeral = 'I64'
    >>> cs.XMLkind = 'major'
    >>> cs.XMLkindStr = 'M'
    >>> cs
    <music21.harmony.ChordSymbol E-/B->
    >>> mxHarmony = musicxml.translate.chordSymbolToMx(cs)
    >>> mxHarmony
    <harmony <root root-step=E root-alter=-1> function=I64 <kind text=M charData=major> inversion=2 <bass bass-step=B bass-alter=-1>>

    >>> hd = harmony.ChordStepModification()
    >>> hd.type = 'alter'
    >>> hd.interval = -1
    >>> hd.degree = 3
    >>> cs.addChordStepModification(hd)

    >>> mxHarmony = musicxml.translate.chordSymbolToMx(cs)
    >>> mxHarmony
    <harmony <root root-step=E root-alter=-1> function=I64 <kind text=M charData=major> inversion=2 <bass bass-step=B bass-alter=-1> <degree <degree-value charData=3> <degree-alter charData=-1> <degree-type charData=alter>>>        
    '''
    mxHarmony = musicxmlMod.Harmony()

    mxKind = musicxmlMod.Kind()
    mxKind.set('charData', cs.XMLkind)
    mxKind.set('text', cs.XMLkindStr)
    mxHarmony.set('kind', mxKind)

    # can assign None to these if None
    mxHarmony.set('inversion', cs.XMLinversion)
    if cs._roman is not None:
        mxHarmony.set('function', cs.romanNumeral.figure)

    if cs.XMLroot is not None:        
        mxRoot = musicxmlMod.Root()
        mxRoot.set('rootStep', cs.XMLroot.step)
        if cs.XMLroot.accidental is not None:
            mxRoot.set('rootAlter', int(cs.XMLroot.accidental.alter))
        mxHarmony.set('root', mxRoot)

    if cs.XMLbass != cs.XMLroot and cs.XMLbass is not None:        
        mxBass = musicxmlMod.Bass()
        mxBass.set('bassStep', cs.XMLbass.step)
        if cs.XMLbass.accidental is not None:
            mxBass.set('bassAlter', int(cs.XMLbass.accidental.alter))
        mxHarmony.set('bass', mxBass)

    if len(cs.getChordStepModifications()) > 0:
        mxDegree = musicxmlMod.Degree()
        for hd in cs.getChordStepModifications():
            # types should be compatible
            mxDegreeValue = musicxmlMod.DegreeValue()
            mxDegreeValue.set('charData', hd.degree)
            mxDegree.componentList.append(mxDegreeValue)
            if hd.interval is not None:
                mxDegreeAlter = musicxmlMod.DegreeAlter()
                # will return -1 for '-a1'
                mxDegreeAlter.set('charData', hd.interval.chromatic.directed)
                mxDegree.componentList.append(mxDegreeAlter)

            mxDegreeType = musicxmlMod.DegreeType()
            mxDegreeType.set('charData', hd.type)
            mxDegree.componentList.append(mxDegreeType)

        mxHarmony.set('degree', mxDegree)
    # degree only thing left
    return mxHarmony

#-------------------------------------------------------------------------------
# Instruments


def instrumentToMx(i):
    '''
    >>> from music21 import *
    >>> i = instrument.Celesta()
    >>> mxScorePart = musicxml.translate.instrumentToMx(i)
    >>> len(mxScorePart.scoreInstrumentList)
    1
    >>> mxScorePart.scoreInstrumentList[0].instrumentName
    'Celesta'
    >>> mxScorePart.midiInstrumentList[0].midiProgram
    9
    '''
    mxScorePart = musicxmlMod.ScorePart()

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
        mxScoreInstrument = musicxmlMod.ScoreInstrument()
        # set id to same as part for now
        mxScoreInstrument.set('id', i.instrumentId)
        # can set these to None
        mxScoreInstrument.instrumentName = i.instrumentName
        mxScoreInstrument.instrumentAbbreviation = i.instrumentAbbreviation
        # add to mxScorePart
        mxScorePart.scoreInstrumentList.append(mxScoreInstrument)

    if i.midiProgram is not None:
        mxMIDIInstrument = musicxmlMod.MIDIInstrument()
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


def mxToInstrument(mxScorePart, inputM21=None):
    # note: transposition values is not set in this operation, but in 
    # mxToStreamPart
    if inputM21 is None:
        i = music21.instrument.Instrument()
    else:
        i = inputM21

    def _cleanStr(str):
        # need to remove badly-formed strings
        if str is None: 
            return None
        str = str.strip()
        str = str.replace('\n', ' ')        
        return str

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


#-------------------------------------------------------------------------------
# unified processors for Chords and Notes


def spannersToMx(target, mxNoteList, mxDirectionPre, mxDirectionPost, 
    spannerBundle):
    '''Convenience routine to create and add MusicXML objects from music21 objects provided as a target and as a SpannerBundle. 

    The `target` parameter here may be music21 Note or Chord. 
    This may edit the mxNoteList and direction lists in place, and thus returns None.
    '''
    if spannerBundle is None or len(spannerBundle) == 0:
        return

    # already filtered for just the spanner that have this note as
    # a component
    #environLocal.pd(['noteToMxNotes()', 'len(spannerBundle)', len(spannerBundle) ])

    for su in spannerBundle.getByClass('Slur'):     
        mxSlur = musicxmlMod.Slur()
        mxSlur.set('number', su.idLocal)
        mxSlur.set('placement', su.placement)
        # is this note first in this spanner?
        if su.isFirst(target):
            mxSlur.set('type', 'start')
        elif su.isLast(target):
            mxSlur.set('type', 'stop')
        else:
            # this may not always be an error
            environLocal.printDebug(['spanner w/ a component that is neither a start nor an end.', su, target])
            continue
        mxNoteList[0].notationsObj.componentList.append(mxSlur)

    for su in spannerBundle.getByClass('TrillExtension'):     
        mxWavyLine = musicxmlMod.WavyLine()
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
            mxOrnaments = musicxmlMod.Ornaments()
            mxNoteList[0].notationsObj.componentList.append(mxOrnaments)
            mxOrnamentsList = [mxOrnaments] # emulate returned obj
        mxOrnamentsList[0].append(mxWavyLine) # add to first
        #environLocal.pd(['wl', 'mxOrnamentsList', mxOrnamentsList ])

    for su in spannerBundle.getByClass('Glissando'):     
        mxGlissando = musicxmlMod.Glissando()
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
        #environLocal.pd(['gliss', 'notationsObj', mxNoteList[0].notationsObj])

    for su in spannerBundle.getByClass('Ottava'):     
        if len(su) == 1: # have a one element wedge
            proc = ['first', 'last']
        else:
            if su.isFirst(target):
                proc = ['first']
            else:
                proc = ['last']
        for posSub in proc:
            mxOctaveShift = musicxmlMod.OctaveShift()
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
            mxDirection = musicxmlMod.Direction()
            mxDirection.set('placement', su.placement) # placement goes here
            mxDirectionType = musicxmlMod.DirectionType()
            mxDirectionType.append(mxOctaveShift)
            mxDirection.append(mxDirectionType)
            environLocal.pd(['os', 'mxDirection', mxDirection ])
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
            else:
                proc = ['last']

        for posSub in proc:
            mxWedge = musicxmlMod.Wedge()
            mxWedge.set('number', su.idLocal)
            if posSub == 'first':
                pmtrs = su.getStartParameters()
                mxWedge.set('type', pmtrs['type'])
                mxWedge.set('spread', pmtrs['spread'])
            elif posSub == 'last':
                pmtrs = su.getEndParameters()
                mxWedge.set('type', pmtrs['type'])
                mxWedge.set('spread', pmtrs['spread'])

            mxDirection = musicxmlMod.Direction()
            mxDirection.set('placement', su.placement) # placement goes here
            mxDirectionType = musicxmlMod.DirectionType()
            mxDirectionType.append(mxWedge)
            mxDirection.append(mxDirectionType)
            #environLocal.pd(['os', 'mxDirection', mxDirection ])
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
            else:
                proc = ['last']
        for posSub in proc:
            mxBracket = musicxmlMod.Bracket()
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
            mxDirection = musicxmlMod.Direction()
            mxDirection.set('placement', su.placement) # placement goes here
            mxDirectionType = musicxmlMod.DirectionType()
            mxDirectionType.append(mxBracket)
            mxDirection.append(mxDirectionType)
            #environLocal.pd(['os', 'mxDirection', mxDirection ])
    
            if posSub == 'first':
                mxDirectionPre.append(mxDirection)
            else:
                mxDirectionPost.append(mxDirection)

#     for su in spannerBundle.getByClass('DashedLine'):     
#         mxDashes = musicxmlMod.Dashes()
#         mxDashes.set('number', su.idLocal)
#         # is this note first in this spanner?
#         if su.isFirst(target):
#             mxDashes.set('type', 'start')
#         elif su.isLast(target):
#             mxDashes.set('type', 'stop')
#         else: # this may not always be an error
#             environLocal.printDebug(['spanner w/ a component that is neither a start nor an end.', su, target])
#         mxDirection = musicxmlMod.Direction()
#         mxDirection.set('placement', su.placement) # placement goes here
#         mxDirectionType = musicxmlMod.DirectionType()
#         mxDirectionType.append(mxDashes)
#         mxDirection.append(mxDirectionType)
#         environLocal.pd(['os', 'mxDirection', mxDirection ])
# 
#         if su.isFirst(target):
#             mxDirectionPre.append(mxDirection)
#         else:
#             mxDirectionPost.append(mxDirection)


def mxNotationsToSpanners(target, mxNotations, spannerBundle):
    '''General routines for gathering spanners from notes via mxNotations objects and placing them in a spanner bundle. 

    Spanners may be found in musicXML notations and directions objects. 

    The passed-in spannerBundle will be edited in-place; existing spanners may be completed, or new spanners may be added. 

    The `target` object is a reference to the relevant music21 object this spanner is associated with.
    '''
    from music21 import spanner
    from music21 import expressions

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
        su.addComponents(target)
        #environLocal.pd(['adding n', n, id(n), 'su.getComponents', su.getComponents(), su.getComponentIds()])
        if mxObj.get('type') == 'stop':
            su.completeStatus = True
            # only add after complete

    mxWavyLineList = mxNotations.getWavyLines()
    for mxObj in mxWavyLineList:
        #environLocal.pd(['waveyLines', mxObj])
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
        su.addComponents(target)
        if mxObj.get('type') == 'stop':
            su.completeStatus = True
            # only add after complete

    mxTremoloList = mxNotations.getTremolos()
    for mxObj in mxTremoloList:
        environLocal.pd(['mxTremoloList', mxObj])
        idFound = mxObj.get('number')
        sb = spannerBundle.getByClassIdLocalComplete('Tremolo', 
            idFound, False)
        if len(sb) > 0: # if we already have 
            su = sb[0] # get the first
        else: # create a new spanner
            environLocal.pd(['creating Tremolo'])
            su = expressions.Tremolo()
            su.idLocal = idFound
            #su.placement = mxObj.get('placement')
            spannerBundle.append(su)
        # add a reference of this note to this spanner
        su.addComponents(target)
        # can be stop or None; we can have empty single-element tremolo
        if mxObj.get('type') in ['stop', None]:
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
        su.addComponents(target)
        if mxObj.get('type') == 'stop':
            su.completeStatus = True
            # only add after complete


def mxDirectionToSpanners(targetLast, mxDirection, spannerBundle):
    '''Some spanners, such as MusicXML octave-shift, are encoded as MusicXML directions.
    '''
    from music21 import spanner
    from music21 import dynamics

    mxWedge = mxDirection.getWedge() 
    if mxWedge is not None:
        mxType = mxWedge.get('type')
        idFound = mxWedge.get('number')
        #environLocal.pd(['mxDirectionToSpanners', 'found mxWedge', mxType, idFound])
        if mxType == 'crescendo':
            sp = dynamics.Crescendo()
            sp.idLocal = idFound
            spannerBundle.append(sp)
            # define this spanner as needing component assignment from
            # the next general note
            spannerBundle.setPendingComponentAssignment(sp, 'GeneralNote')
        elif mxType == 'diminuendo':
            sp = dynamics.Diminuendo()
            sp.idLocal = idFound
            spannerBundle.append(sp)
            spannerBundle.setPendingComponentAssignment(sp, 'GeneralNote')
        elif mxType == 'stop':
            # need to retrieve an existing spanner
            # try to get base class of both Crescendo and Decrescendo
            sp = spannerBundle.getByClassIdLocalComplete('DynamicWedge', 
                    idFound, False)[0] # get first
            sp.completeStatus = True
            # will only have a target if this follows the note
            if targetLast is not None:
                sp.addComponents(targetLast)
        else:
            raise TranslateException('unidentified mxType of mxWedge:', mxType)

    mxBracket = mxDirection.getBracket() 
    if mxBracket is not None:
        mxType = mxBracket.get('type')
        idFound = mxBracket.get('number')
        #environLocal.pd(['mxDirectionToSpanners', 'found mxBracket', mxType, idFound])
        if mxType == 'start':
            sp = spanner.Line()
            sp.idLocal = idFound
            sp.startTick = mxBracket.get('line-end')
            sp.startHeight = mxBracket.get('end-length')
            sp.lineType = mxBracket.get('line-type')

            spannerBundle.append(sp)
            # define this spanner as needing component assignment from
            # the next general note
            spannerBundle.setPendingComponentAssignment(sp, 'GeneralNote')
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
                sp.addComponents(targetLast)
        else:
            raise TranslateException('unidentified mxType of mxBracket:', mxType)

    mxDashes = mxDirection.getDashes() 
    # import mxDashes as m21 Line objects
    if mxDashes is not None:
        mxType = mxDashes.get('type')
        idFound = mxDashes.get('number')
        #environLocal.pd(['mxDirectionToSpanners', 'found mxDashes', mxType, idFound])
        if mxType == 'start':
            sp = spanner.Line()
            sp.idLocal = idFound
            sp.startTick = 'none'
            sp.lineType = 'dashed'
            spannerBundle.append(sp)
            # define this spanner as needing component assignment from
            # the next general note
            spannerBundle.setPendingComponentAssignment(sp, 'GeneralNote')
        elif mxType == 'stop':
            # need to retrieve an existing spanner
            # try to get base class of both Crescendo and Decrescendo
            sp = spannerBundle.getByClassIdLocalComplete('Line', 
                    idFound, False)[0] # get first
            sp.completeStatus = True
            sp.endTick = 'none'
            # will only have a target if this follows the note
            if targetLast is not None:
                sp.addComponents(targetLast)
        else:
            raise TranslateException('unidentified mxType of mxBracket:', mxType)


#-------------------------------------------------------------------------------


def articulationsAndExpressionsToMx(target, mxNoteList):
    '''The `target` parameter is the music21 object. 
    '''
    # if we have any articulations, they only go on the first of any 
    # component notes
    mxArticulations = musicxmlMod.Articulations()
    for artObj in target.articulations:
        mxArticulations.append(artObj.mx) # returns mxArticulationMark to append to mxArticulations
    if len(mxArticulations) > 0:
        mxNoteList[0].notationsObj.componentList.append(mxArticulations)

    # notations and articulations are mixed in musicxml
    for expObj in target.expressions:
        # TODO: this is relying on the presence of an MX attribute
        # to determine if it can be shown; another method should
        # be used
        #replace with calls to 
        mx = ornamentToMx(expObj)
        if mx is not None:
            # some expressions must be wrapped in a musicxml ornament
            # a m21 Ornament subclass may not be the same as a mxl ornament
            if 'Ornament' in expObj.classes:
                ornamentsObj = musicxmlMod.Ornaments()
                ornamentsObj.append(mx)
                mxNoteList[0].notationsObj.componentList.append(ornamentsObj)
            else:
                mxNoteList[0].notationsObj.componentList.append(mx)


def mxOrnamentToOrnament(mxOrnament):
    '''Convert mxOrnament into a music21 ornament. This only processes non-spanner ornaments. Many mxOrnaments are spanners: these are handled elsewhere. 

    Returns None if cannot be converted or not defined. 
    '''
    from music21 import expressions
    orn = None
    #environLocal.pd(['calling mxOrnamentToOrnament with', mxOrnament])
    if isinstance(mxOrnament, musicxmlMod.TrillMark):
        orn = expressions.Trill()
        orn.placement = mxOrnament.get('placement')
    elif isinstance(mxOrnament, musicxmlMod.Mordent):
        orn = expressions.Mordent()
    elif isinstance(mxOrnament, musicxmlMod.InvertedMordent):
        orn = expressions.InvertedMordent()

    elif isinstance(mxOrnament, musicxmlMod.Turn):
        orn = expressions.Turn()
    elif isinstance(mxOrnament, musicxmlMod.InvertedTurn):
        orn = expressions.InvertedTurn()

    elif isinstance(mxOrnament, musicxmlMod.Shake):
        orn = expressions.Shake()
    elif isinstance(mxOrnament, musicxmlMod.Schleifer):
        orn = expressions.Schleifer()

    return orn # may be None


def ornamentToMx(orn):
    '''Convert a music21 object to musicxml object; return None if no conversion is possible. 
    '''
    mx = None
    if 'Shake' in orn.classes:
        pass # not yet translating, but a subclass of Trill
    elif 'Trill' in orn.classes:
        mx = musicxmlMod.TrillMark()
        mx.set('placement', orn.placement)
    elif 'Fermata' in orn.classes:
        mx = musicxmlMod.Fermata()
        mx.set('type', orn.type)
    elif 'Mordent' in orn.classes:
        mx = musicxmlMod.Mordent()
    elif 'InvertedMordent' in orn.classes:
        mx = musicxmlMod.InvertedMordent()
    elif 'Trill' in orn.classes:
        mx = musicxmlMod.TrillMark()
        mx.set('placement', orn.placement)

    elif 'Turn' in orn.classes:
        mx = musicxmlMod.Turn()
    elif 'DelayedTurn' in orn.classes:
        mx = musicxmlMod.DelayedTurn()
    elif 'InvertedTurn' in orn.classes:
        mx = musicxmlMod.InvertedTurn()

    elif 'Schleifer' in orn.classes:
        mx = musicxmlMod.Schleifer()

    else:
        environLocal.pd(['no musicxml conversion for:', orn])

    return mx


#-------------------------------------------------------------------------------
# Chords

def chordToMx(c, spannerBundle=None):
    '''
    Returns a List of mxNotes
    Attributes of notes are merged from different locations: first from the 
    duration objects, then from the pitch objects. Finally, GeneralNote 
    attributes are added

    >>> from music21 import *
    >>> a = chord.Chord()
    >>> a.quarterLength = 2
    >>> b = pitch.Pitch('A-')
    >>> c = pitch.Pitch('D-')
    >>> d = pitch.Pitch('E-')
    >>> e = a.pitches = [b, c, d]
    >>> len(e)
    3
    >>> mxNoteList = musicxml.translate.chordToMx(a)
    >>> len(mxNoteList) # get three mxNotes
    3
    >>> mxNoteList[0].get('chord')
    False
    >>> mxNoteList[1].get('chord')
    True
    >>> mxNoteList[2].get('chord')
    True
    
    >>> g = note.Note('c4')
    >>> g.notehead = 'diamond'
    >>> h = pitch.Pitch('g3')
    >>> i = chord.Chord([h, g])
    >>> i.quarterLength = 2
    >>> listOfMxNotes = musicxml.translate.chordToMx(i)
    >>> listOfMxNotes[0].get('chord')
    False
    >>> listOfMxNotes[1].noteheadObj.get('charData')
    'diamond'
    
    
    >>> rn = roman.RomanNumeral('V', key.Key('A-'))
    >>> rn.pitches
    [E-5, G5, B-5]
    '''
    if spannerBundle is not None and len(spannerBundle) > 0:
        # this will get all spanners that participate with this note
        # get a new spanner bundle that only has components relevant to this 
        # note.
        spannerBundle = spannerBundle.getByComponent(c)
        #environLocal.printDebug(['noteToMxNotes(): spannerBundle post-filter by component:', spannerBundle, n, id(n)])

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

            #environLocal.pd(['final note stem', mxNote.stem])
            # only add beam to first note in group
            if c.beams is not None and chordPos == 0:
                mxNote.beamList = c.beams.mx

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
            # get mxl objs from tie obj
            tieObj = n.tie
            if tieObj is not None:
                #environLocal.printDebug(['chordToMx: found tie for pitch', pitchObj])
                mxTieList, mxTiedList = tieObj.mx 
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

#     mxArticulations = musicxmlMod.Articulations()
#     for i in range(len(c.articulations)):
#         obj = c.articulations[i]
#         if hasattr(obj, 'mx'):
#             mxArticulations.append(obj.mx)
#     #if mxArticulations != None:
#     if len(mxArticulations) > 0:
#         mxNoteList[0].notationsObj.componentList.append(mxArticulations)
# 
#     # notations and articulations are mixed in musicxml
#     for i in range(len(c.expressions)):
#         obj = c.expressions[i]
#         if hasattr(obj, 'mx'):
#             # some expressions must be wrapped in a musicxml ornament
#             if 'Ornament' in obj.classes:
#                 ornamentsObj = musicxmlMod.Ornaments()
#                 ornamentsObj.append(obj.mx)
#                 mxNoteList[0].notationsObj.componentList.append(ornamentsObj)
#             else: 
#                 mxNoteList[0].notationsObj.componentList.append(obj.mx)

    # some spanner produce direction tags, and sometimes these need
    # to go before or after the notes of this element
    mxDirectionPre = []
    mxDirectionPost = []
    # will update and fill all lists passed in as args
    spannersToMx(c, mxNoteList, mxDirectionPre, mxDirectionPost, spannerBundle)

    return mxDirectionPre + mxNoteList + mxDirectionPost



def mxToChord(mxNoteList, inputM21=None, spannerBundle=None):
    '''
    Given an a list of mxNotes, fill the necessary parameters


    >>> from music21 import *
    >>> a = musicxml.Note()
    >>> a.setDefaults()
    >>> b = musicxml.Note()
    >>> b.setDefaults()
    >>> b.set('chord', True)
    >>> m = musicxml.Measure()
    >>> m.setDefaults()
    >>> a.external['measure'] = m # assign measure for divisions ref
    >>> a.external['divisions'] = m.external['divisions']
    >>> b.external['measure'] = m # assign measure for divisions ref
    >>> b.external['divisions'] = m.external['divisions']
    >>> c = chord.Chord()
    >>> c.mx = [a, b]
    >>> len(c.pitches)
    2
    
    >>> from music21 import *
    >>> a = musicxml.Note()
    >>> a.setDefaults()
    >>> nh1 = musicxml.Notehead()
    >>> nh1.set('charData', 'diamond')
    >>> a.noteheadObj = nh1
    >>> b = musicxml.Note()
    >>> b.setDefaults()
    >>> b.set('chord', True)
    >>> m = musicxml.Measure()
    >>> m.setDefaults()
    >>> a.external['measure'] = m # assign measure for divisions ref
    >>> a.external['divisions'] = m.external['divisions']
    >>> b.external['measure'] = m # assign measure for divisions ref
    >>> b.external['divisions'] = m.external['divisions']
    >>> c = musicxml.translate.mxToChord([a, b])
    >>> c.getNotehead(c.pitches[0])
    'diamond'
    
    '''
    from music21 import chord
    from music21 import pitch
    from music21 import tie
    from music21 import spanner

    if inputM21 == None:
        c = chord.Chord()
    else:
        c = inputM21

    if spannerBundle is None:
        #environLocal.printDebug(['mxToNote()', 'creating SpannerBundle'])
        spannerBundle = spanner.SpannerBundle()
    else: # if we are passed in as spanner bundle, look for any pending
        # component assignments
        spannerBundle.freePendingComponentAssignment(c)

    # assume that first chord is the same duration for all parts
    #c.duration.mx = mxNoteList[0]
    mxToDuration(mxNoteList[0], c.duration)

    # assume that first note in list has a grace object (and all do)
    mxGrace = mxNoteList[0].get('graceObj')

    pitches = []
    ties = [] # store equally spaced list; use None if not defined
    noteheads = [] # store notehead attributes that correspond with pitches
    stemDirs = [] # store stem direction attributes that correspond with pitches
    
    for mxNote in mxNoteList:
        # extract pitch pbjects     
        p = pitch.Pitch()
        p.mx = mxNote # will extract pitch info from mxNote
        pitches.append(p)
        #extract notehead objects; may be None
        nh = mxNote.get('noteheadObj')
        noteheads.append(nh)
        #extract stem directions
        stemDir = mxNote.get('stem')
        stemDirs.append(stemDir)

        if len(mxNote.tieList) > 0:
            tieObj = tie.Tie() # m21 tie object
            tieObj.mx = mxNote # provide entire Note
            #environLocal.printDebug(['found tie in chord', tieObj])
            ties.append(tieObj)
        else: # need place holder for each pitch
            ties.append(None)
    # set all at once
    c.pitches = pitches
    # set beams from first note of chord
    c.beams.mx = mxNoteList[0].beamList

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

def generalNoteToMusicXML(n):
    '''Translate a music21 :class:`~music21.note.Note` into a complete MusicXML representation. 

    >>> from music21 import *
    >>> n = note.Note('c3')
    >>> n.quarterLength = 3
    >>> post = musicxml.translate.generalNoteToMusicXML(n)
    '''
    from music21 import stream, duration
    # make a copy, as we this process will change tuple types
    # this method is called infrequently, and only for display of a single 
    # note
    nCopy = copy.deepcopy(n)
    duration.updateTupletType(nCopy.duration) # modifies in place

    out = stream.Stream()
    out.append(nCopy)

    # call the musicxml property on Stream
    return out.musicxml
    
def noteheadToMxNotehead(obj, defaultColor=None):
    '''
    Translate a music21 :class:`~music21.note.Note` object or :class:`~music21.pitch.Pitch` object to a
    into a musicxml.Notehead object.

    >>> from music21 import *
    >>> n = note.Note('C#4')
    >>> n.notehead = 'diamond'
    >>> mxN = musicxml.translate.noteheadToMxNotehead(n)
    >>> mxN.get('charData')
    'diamond'
    
    >>> n1 = note.Note('c3')
    >>> n1.notehead = 'diamond'
    >>> n1.noteheadParen = 'yes'
    >>> n1.noteheadFill = 'no'
    >>> mxN4 = musicxml.translate.noteheadToMxNotehead(n1)
    >>> mxN4._attr['filled']
    'no'
    >>> mxN4._attr['parentheses']
    'yes'
    '''
    from music21 import note # needed for note.noteheadTypeNames
    mxNotehead = musicxmlMod.Notehead()
    nh = None
    nhFill = 'default'
    nhParen = False
    
    # default noteheard, regardless of if set as attr
    nh = 'normal'
    if hasattr(obj, 'notehead'):
        nh = obj.notehead
    nhFill = 'default'
    if hasattr(obj, 'noteheadFill'):
        nhFill = obj.noteheadFill
    nhParen = False
    if hasattr(obj, 'noteheadParen'):
        nhParen = obj.noteheadParen    
    
    if nh not in note.noteheadTypeNames:
        raise NoteheadException('This notehead type is not supported by MusicXML: "%s"' % nh)
    else:
        # should only set if needed, otherwise creates extra mxl data
        #if nh not in ['normal']: 
        mxNotehead.set('charData', nh)
    if nhFill != 'default':
        mxNotehead.set('filled', nhFill)
    if nhParen is not False:
        mxNotehead.set('parentheses', nhParen)
    if obj.color not in [None, '']:
        mxNotehead.set('color', obj.color)
    return mxNotehead

def noteToMxNotes(n, spannerBundle=None):
    '''
    Translate a music21 :class:`~music21.note.Note` into a 
    list of :class:`~music21.musicxml.Note` objects.

    Note that, some note-attached spanners, such as octave shifts, produce direction (and direction types) in this method. 
    '''
    #Attributes of notes are merged from different locations: first from the 
    #duration objects, then from the pitch objects. Finally, GeneralNote 
    #attributes are added.
    if spannerBundle is not None and len(spannerBundle) > 0:
        # this will get all spanners that participate with this note
        # get a new spanner bundle that only has components relevant to this 
        # note.
        spannerBundle = spannerBundle.getByComponent(n)
        #environLocal.printDebug(['noteToMxNotes(): spannerBundle post-filter by component:', spannerBundle, n, id(n)])

    mxNoteList = []
    #pitchMx = n.pitch.mx
    pitchMx = pitchToMx(n.pitch)
    noteColor = n.color

    # todo: this is not yet implemented in music21 note objects; to do
    #mxNotehead = musicxmlMod.Notehead()
    #mxNotehead.set('charData', defaults.noteheadUnpitched)

    for mxNote in durationToMx(n.duration): # returns a list of mxNote objs
    #for mxNote in n.duration.mx: # returns a list of mxNote objs
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
        #mxNoteList[0].lyricList.append(lyricObj.mx)
        mxNoteList[0].lyricList.append(lyricToMx(lyricObj))

    # if this note, not a component duration, but this note has a tie, 
    # need to add this to the last-encountered mxNote
    if n.tie is not None:
        #mxTieList, mxTiedList = n.tie.mx # get mxl objs from tie obj
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
    # reconfigured based on what is gotten from n.duration.mx
    # likely, this means that many continue beams will need to be added

    # this is setting the same beams for each part of this 
    # note; this may not be correct, as we may be dividing the note into
    # more than one part
    nBeams = n.beams
    if nBeams:
        nBeamsMx = n.beams.mx
        for mxNote in mxNoteList:
            mxNote.beamList = nBeamsMx

    #Adds the notehead type if it is not set to the default 'normal'.
    if (n.notehead != 'normal' or n.noteheadFill != 'default' or 
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



def mxToNote(mxNote, spannerBundle=None, inputM21=None):
    '''Translate a MusicXML :class:`~music21.musicxml.Note` to a :class:`~music21.note.Note`.

    The `spanners` parameter can be a list or a Stream for storing and processing Spanner objects. 
    '''
    from music21 import articulations
    from music21 import expressions
    from music21 import note
    from music21 import tie
    from music21 import spanner

    if inputM21 is None:
        n = note.Note()
    else:
        n = inputM21
    # doing this will create an instance, but will not be passed
    # out of this method, and thus is only for testing
    if spannerBundle is None:
        #environLocal.printDebug(['mxToNote()', 'creating SpannerBundle'])
        spannerBundle = spanner.SpannerBundle()
    else: # if we are passed in as spanner bundle, look for any pending
        # component assignments
        spannerBundle.freePendingComponentAssignment(n)

    # print object == 'no' and grace notes may have a type but not
    # a duration. they may be filtered out at the level of Stream 
    # processing
    if mxNote.get('printObject') == 'no':
        n.hideObjectOnPrint = True
        #environLocal.printDebug(['got mxNote with printObject == no'])

    mxGrace = mxNote.get('graceObj')

    #n.pitch.mx = mxNote # required info will be taken from entire note
    mxToPitch(mxNote, n.pitch)

    if mxGrace is not None:
        #environLocal.pd(['mxGrace', mxGrace, mxNote, n.duration])
        # in some casses grace notes may not have an assigned duration type
        # this default type is set here, before assigning to n.duration
        if mxNote.type is None:
            #environLocal.pd(['mxToNote', 'mxNote that is a grace missing duration type'])
            mxNote.type = 'eighth'    

    # the n.duration object here will be configured based on mxNote
    mxToDuration(mxNote, n.duration)
    n.beams.mx = mxNote.beamList
    
    mxStem = mxNote.get('stem')
    if mxStem is not None:
        n.stemDirection = mxStem

    # get color from Note first; if not, try to get from notehead
    if mxNote.get('color') is not None:
        n.color = mxNote.get('color')

    # can use mxNote.tieList instead
    mxTieList = mxNote.get('tieList')
    if len(mxTieList) > 0:
        tieObj = tie.Tie() # m21 tie object
        tieObj.mx = mxNote # provide entire Note
        # n.tie is defined in GeneralNote as None by default
        n.tie = tieObj

    # things found in notations object:
    # articulations, slurs
    mxNotations = mxNote.get('notationsObj')
    if mxNotations is not None:
        # get a list of mxArticulationMarks, not mxArticulations
        mxArticulationMarkList = mxNotations.getArticulations()
        for mxObj in mxArticulationMarkList:
            articulationObj = articulations.Articulation()
            articulationObj.mx = mxObj
            n.articulations.append(articulationObj)

        # get any fermatas, store on notations
        mxFermataList = mxNotations.getFermatas()
        for mxObj in mxFermataList:
            fermataObj = expressions.Fermata()
            fermataObj.mx = mxObj
            n.expressions.append(fermataObj)

        mxOrnamentsList = mxNotations.getOrnaments()
#         if len(mxOrnamentsList) > 0:
#             environLocal.printDebug(['mxOrnamentsList:', mxOrnamentsList])
        for mxOrnamentsObj in mxOrnamentsList:
            for mxObj in mxOrnamentsObj:
                post = mxOrnamentToOrnament(mxObj)
                if post is not None:
                    n.expressions.append(post)
                    #environLocal.printDebug(['adding to epxressions', post])

        # create spanners:
        mxNotationsToSpanners(n, mxNotations, spannerBundle)

    # gets the notehead object from the mxNote and sets value of the music21 note to the value of the notehead object        
    mxNotehead = mxNote.get('noteheadObj')
    if mxNotehead is not None:
        if mxNotehead.charData not in ['', None]:
            n.notehead = mxNotehead.charData
        if mxNotehead.get('color') is not None:
            n.color = mxNotehead.get('color')

    # translate if necessary, otherwise leaves unchanged
    n = mxGraceToGrace(n, mxGrace)
    return n


def restToMxNotes(r):
    '''Translate a :class:`~music21.note.Rest` to a MusicXML :class:`~music21.musicxml.Note` object configured with a :class:`~music21.musicxml.Rest`.
    '''
    mxNoteList = []
    for mxNote in durationToMx(r.duration): # returns a list of mxNote objs
        # merge method returns a new object
        mxRest = musicxmlMod.Rest()
        mxRest.setDefaults()
        mxNote.set('rest', mxRest)
        # get color from within .editorial using attribute
        mxNote.set('color', r.color)
        if r.hideObjectOnPrint == True:
            mxNote.set('printObject', "no")
            mxNote.set('printSpacing', "yes")        
        mxNoteList.append(mxNote)
    return mxNoteList




def mxToRest(mxNote, inputM21=None):
    '''Translate a MusicXML :class:`~music21.musicxml.Note` object to a :class:`~music21.note.Rest`.

    If an `inputM21` object reference is provided, this object will be configured; otherwise, a new :class:`~music21.note.Rest` object is created and returned.
    '''
    from music21 import note

    if inputM21 == None:
        r = note.Rest()
    else:
        r = inputM21

    try:
        #r.duration.mx = mxNote
        mxToDuration(mxNote, r.duration)
    except music21.duration.DurationException:
        #environLocal.printDebug(['failed extaction of duration from musicxml', 'mxNote:', mxNote, r])
        raise

    if mxNote.get('color') is not None:
        r.color = mxNote.get('color')

    return r



#-------------------------------------------------------------------------------
# Measures


def measureToMx(m, spannerBundle=None, mxTranspose=None):
    '''Translate a :class:`~music21.stream.Measure` to a MusicXML :class:`~music21.musicxml.Measure` object.
    '''
    from music21 import duration

    #environLocal.printDebug(['measureToMx(): m.isSorted:', m.isSorted, 'm._mutable', m._mutable, 'len(spannerBundle)', len(spannerBundle)])
    if spannerBundle is not None:
        # get all spanners that have this measure as a component    
        rbSpanners = spannerBundle.getByComponentAndClass(m, 'RepeatBracket')
    else:
        rbSpanners = [] # for size comparison

    mxMeasure = musicxmlMod.Measure()
    mxMeasure.set('number', m.number)
    if m.layoutWidth is not None:
        mxMeasure.set('width', m.layoutWidth)

    # print objects come before attributes
    # note: this class match is a problem in cases where the object is created in the module itself, as in a test. 
    mxPrint = None
    found = m.getElementsByClass('PageLayout')
    if len(found) > 0:
        sl = found[0] # assume only one per measure
        mxPrint = sl.mx
    found = m.getElementsByClass('SystemLayout')
    if len(found) > 0:
        sl = found[0] # assume only one per measure
        if mxPrint is None:
            mxPrint = sl.mx
        else:
            mxPrint.merge(sl.mx)
    
    if mxPrint is not None:
        mxMeasure.componentList.append(mxPrint)

    # get an empty mxAttributes object
    mxAttributes = musicxmlMod.Attributes()
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
        mxAttributes.clefList = [m.clef.mx]
    if m.keySignature is not None: 
        # key.mx returns a Key ojbect, needs to be in a list
        mxAttributes.keyList = [m.keySignature.mx]
    if m.timeSignature is not None:
        mxAttributes.timeList = [m.timeSignature.mx]
        #mxAttributes.timeList = m.timeSignature.mx
    mxMeasure.set('attributes', mxAttributes)

    # see if we have barlines
    if (m.leftBarline != None or 
        (len(rbSpanners) > 0 and rbSpanners[0].isFirst(m))):
        if m.leftBarline is None:
            # create a simple barline for storing ending
            mxBarline = musicxmlMod.Barline()
        else:
            mxBarline = m.leftBarline.mx # this may be a repeat object
        # setting location outside of object based on that this attribute
        # is the leftBarline
        mxBarline.set('location', 'left')
        # if we have spanners here, we can be sure they are relevant
        if len(rbSpanners) > 0:
            mxEnding = musicxmlMod.Ending()
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
                        sub.voice = voiceId # the voice id is the voice number
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
                        sub.voice = voiceId # the voice id is the voice number
                    mxMeasure.componentList += objList
                elif 'GeneralNote' in classes:
                    offsetMeasureNote += obj.quarterLength
                    objList = obj.mx # .mx here returns a list of notes
                    # need to set voice for each contained mx object
                    for sub in objList:
                        sub.voice = voiceId # the voice id is the voice number
                    mxMeasure.componentList += objList
            # create backup object configured to duration of accumulated
            # notes, meaning that we always return to the start of the measure
            mxBackup = musicxmlMod.Backup()
            mxBackup.duration = int(divisions * offsetMeasureNote)
            mxMeasure.componentList.append(mxBackup)

    if not m.hasVoices() or nonVoiceMeasureItems is not None: # no voices
        if nonVoiceMeasureItems is not None:
            mFlat = nonVoiceMeasureItems # this is a Stream
        else:
            mFlat = m.flat

        for obj in mFlat:
            #environLocal.pd(['iterating flat M components', obj, obj.offset])
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
            elif 'GeneralNote' in classes: # this includes chords
                # .mx here returns a list of notes; this could be a rest
                mxMeasure.componentList += obj.mx
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
                # convert m21 offset to mxl divisions
                mxOffset = int(defaults.divisionsPerQuarter * 
                           obj.getOffsetBySite(mFlat))
                # get a list of objects: may be a text expression + metro
                mxList = tempoIndicationToMx(obj)
                for mxDirection in mxList: # a list of mxdirections
                    mxDirection.offset = mxOffset 
                    # uses internal offset positioning, can insert at zero
                    mxMeasure.insert(0, mxDirection)
                    #mxMeasure.componentList.append(mxObj)
            elif 'TextExpression' in classes:
                # convert m21 offset to mxl divisions
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
            else: # other objects may have already been added
                pass
                #environLocal.printDebug(['_getMX of Measure is not processing', obj])

    # TODO: create bar ending positions
    # right barline must follow all notes
    if (m.rightBarline != None or 
        (len(rbSpanners) > 0 and rbSpanners[0].isLast(m))):
        if m.rightBarline is None:
            # create a simple barline for storing ending
            mxBarline = musicxmlMod.Barline()
        else:
            mxBarline = m.rightBarline.mx # this may be a repeat
        # setting location outside of object based on that this attribute
        # is the leftBarline
        mxBarline.set('location', 'right')

        # if we have spanners here, we can be sure they are relevant
        if len(rbSpanners) > 0:
            mxEnding = musicxmlMod.Ending()
            # must use stop, not discontinue
            mxEnding.set('type', 'stop')
            mxEnding.set('number', rbSpanners[0].number)
            mxBarline.set('endingObj', mxEnding)

        mxMeasure.componentList.append(mxBarline)

    return mxMeasure


def _addToStaffReference(mxObject, target, staffReference):
    '''Utility routine for importing musicXML objects; here, we store a reference to the music21 object in a dictionary, where keys are the staff values. Staff values may be None, 1, 2, etc.  
    '''
    #environLocal.printDebug(['_addToStaffReference(): called with:', target])
    if common.isListLike(mxObject):
        if len(mxObject) > 0:
            mxObject = mxObject[0] # if a chord, get the first components
        else: # if an empty list
            environLocal.printDebug(['got an mxObject as an empty list', mxObject])
            return 
    # add to staff reference
    if hasattr(mxObject, 'staff'):
        key = mxObject.staff
    # some objects store staff assignment simply as number
    else:
        try:
            key = mxObject.get('number')
        except xmlnode.XMLNodeException:
            return 
    if key not in staffReference.keys():
        staffReference[key] = []
    staffReference[key].append(target)


def mxToMeasure(mxMeasure, spannerBundle=None, inputM21=None):
    '''Translate an mxMeasure (a MusicXML :class:`~music21.musicxml.Measure` object) 
    into a music21 :class:`~music21.stream.Measure`.

    If an `inputM21` object reference is provided, this object will be 
    configured and returned; otherwise, a new :class:`~music21.stream.Measure` object is created.  

    The `spannerBundle` that is passed in is used to accumulate any created Spanners. 
    This Spanners are not inserted into the Stream here. 
        
    '''
    from music21 import stream
    from music21 import chord
    from music21 import dynamics
    from music21 import harmony
    from music21 import key
    from music21 import note
    from music21 import layout
    from music21 import bar
    from music21 import clef
    from music21 import meter
    from music21 import spanner

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
            raise TranslateException(
                'no mxAttribues available for this measure')

    #environLocal.printDebug(['mxAttriutes clefList', mxAttributes.clefList, 
    #                        mxAttributesInternal])

    # getting first for each of these for now
    if mxAttributesInternal and len(mxAttributes.timeList) != 0:
        for mxSub in mxAttributes.timeList:
            ts = meter.TimeSignature()
            ts.mx = mxSub
            _addToStaffReference(mxSub, ts, staffReference)
            m._insertCore(0, ts)
            #m.timeSignature = meter.TimeSignature()
            #m.timeSignature.mx = mxSub
    if mxAttributesInternal and len(mxAttributes.clefList) != 0:
        for mxSub in mxAttributes.clefList:
            cl = clef.Clef()
            cl.mx = mxSub
            _addToStaffReference(mxSub, cl, staffReference)
            m._insertCore(0, cl)
            #m.clef = clef.Clef()
            #m.clef.mx = mxSub
    if mxAttributesInternal and len(mxAttributes.keyList) != 0:
        for mxSub in mxAttributes.keyList:
            ks = key.KeySignature()
            ks.mx = mxSub
            _addToStaffReference(mxSub, ks, staffReference)
            m._insertCore(0, ks)
            #m.keySignature = key.KeySignature()
            #m.keySignature.mx = mxSub

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
        raise TranslateException('cannot get a division from mxObject')

    if mxMeasure.getVoiceCount() > 1:
        useVoices = True
        # count from zero
        for id in mxMeasure.getVoiceIndices():
            v = stream.Voice()
            v.id = id
            m._insertCore(0, v)
    else:
        useVoices = False

    # iterate through components found on components list
    # set to zero for each measure
    offsetMeasureNote = 0 # offset of note w/n measure        
    mxNoteList = [] # for accumulating notes in chords
    mxLyricList = [] # for accumulating lyrics assigned to chords
    nLast = None # store the last-create music21 note for Spanners

    for i in range(len(mxMeasure)):
        # try to get the next object for chord comparisons
        mxObj = mxMeasure[i]
        if i < len(mxMeasure)-1:
            mxObjNext = mxMeasure[i+1]
        else:
            mxObjNext = None
        #environLocal.printDebug(['handling', mxObj])

        # NOTE: tests have shown that using isinstance() here is much faster
        # than checking the .tag attribute.
        # check for backup and forward first
        if isinstance(mxObj, musicxmlMod.Backup):
            # resolve as quarterLength, subtract from measure offset
            #environLocal.printDebug(['found mxl backup:', mxObj.duration])
            offsetMeasureNote -= float(mxObj.duration) / float(divisions)
            continue
        elif isinstance(mxObj, musicxmlMod.Forward):
            # resolve as quarterLength, add to measure offset
            #environLocal.printDebug(['found mxl forward:', mxObj.duration, 'divisions', divisions])
            offsetMeasureNote += float(mxObj.duration) / float(divisions)
            continue
        elif isinstance(mxObj, musicxmlMod.Print):
            # mxPrint objects may be found in a Measure's components
            # contain page or system layout information among others
            mxPrint = mxObj
            addPageLayout = False
            addSystemLayout = False
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
                    if isinstance(layoutType, musicxmlMod.PageLayout):
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
                    if isinstance(layoutType, musicxmlMod.SystemLayout):
                        addSystemLayout = True
                        break
            if addPageLayout:
                pl = layout.PageLayout()
                pl.mx = mxPrint
                # store at zero position
                m._insertCore(0, pl)
            if addSystemLayout or not addPageLayout:
                sl = layout.SystemLayout()
                sl.mx = mxPrint
                # store at zero position
                m._insertCore(0, sl)

        # <sound> tags may be found in the Measure, used to define tempo
        elif isinstance(mxObj, musicxmlMod.Sound):
            pass

        elif isinstance(mxObj, musicxmlMod.Barline):
            # repeat is a tag found in the barline object
            mxBarline = mxObj
            mxRepeatObj = mxBarline.get('repeatObj')
            if mxRepeatObj is not None:
                barline = bar.Repeat()
            else:
                barline = bar.Barline()

            # barline objects also store ending objects, that mark begin
            # and end of repeat bracket designations
            mxEndingObj = mxBarline.get('endingObj')
            if mxEndingObj is not None:
                #environLocal.printDebug(['found mxEndingObj', mxEndingObj, 'm', m]) 
                # get all incomplete spanners of the appropriate class that are
                # not complete
                rbSpanners = spannerBundle.getByClassComplete(
                            'RepeatBracket', False)
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
                    rb.addComponents(m)
                    # in general, any rb found should be the opening, and thus
                    # this is the closing; can check
                    if mxEndingObj.get('type') in ['stop', 'discontinue']:
                        rb.completeStatus = True
                        rb.number = mxEndingObj.get('number')
                    else:
                        raise TranslateException('found mx Ending object that is not stop message, even though there is still an open start message.')

            barline.mx = mxBarline # configure
            if barline.location == 'left':
                #environLocal.printDebug(['setting left barline', barline])
                m.leftBarline = barline
            elif barline.location == 'right':
                #environLocal.printDebug(['setting right barline', barline])
                m.rightBarline = barline
            else:
                environLocal.printDebug(['not handling barline that is neither left nor right', barline, barline.location])

        elif isinstance(mxObj, musicxmlMod.Note):
            mxNote = mxObj
            if isinstance(mxObjNext, musicxmlMod.Note):
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

            if mxNote.get('rest') in [None, False]: # it is a note
                # if a chord, do not increment until chord is complete
                if mxNote.get('chord') is True:
                    mxNoteList.append(mxNote)
                    offsetIncrement = 0
                    # store lyrics for latter processing
                    for mxLyric in mxNote.lyricList:
                        mxLyricList.append(mxLyric)
                else:
                    try:
                        n = mxToNote(mxNote, spannerBundle=spannerBundle)
                    except TranslateException as strerror:
                        raise TranslateException('cannot translate note in measure %s: %s' % (mNumRaw, strerror))
                    
                    _addToStaffReference(mxNote, n, staffReference)
                    if useVoices:
                        m.voices[mxNote.voice]._insertCore(offsetMeasureNote, n)
                    else:
                        m._insertCore(offsetMeasureNote, n)
                    offsetIncrement = n.quarterLength

                    for mxLyric in mxNote.lyricList:
                        lyricObj = note.Lyric()
                        #lyricObj.mx = mxLyric
                        mxToLyric(mxLyric, lyricObj)
                        n.lyrics.append(lyricObj)
                    nLast = n # update

                if mxNote.get('notationsObj') is not None:
                    for mxObjSub in mxNote.get('notationsObj'):
                        # deal with ornaments, trill, etc
                        pass
            else: # its a rest
                n = note.Rest()
                n.mx = mxNote # assign mxNote to rest obj
                _addToStaffReference(mxNote, n, staffReference)
                #m.insert(offsetMeasureNote, n)
                if useVoices:
                    m.voices[mxNote.voice]._insertCore(offsetMeasureNote, n)
                else:
                    m._insertCore(offsetMeasureNote, n)
                offsetIncrement = n.quarterLength
                nLast = n # update

            # if we we have notes in the note list and the next
            # note either does not exist or is not a chord, we 
            # have a complete chord
            if len(mxNoteList) > 0 and (mxNoteNext is None 
                or mxNoteNext.get('chord') is False):
                #c = chord.Chord()
                #c.mx = mxNoteList
                c = mxToChord(mxNoteList, spannerBundle=spannerBundle)
                # add any accumulated lyrics
                for mxLyric in mxLyricList:
                    lyricObj = note.Lyric()
                    #lyricObj.mx = mxLyric
                    mxToLyric(mxLyric, lyricObj)
                    c.lyrics.append(lyricObj)

                _addToStaffReference(mxNoteList, c, staffReference)
                if useVoices:
                    m.voices[mxNote.voice]._insertCore(offsetMeasureNote, c)
                else:
                    m._insertCore(offsetMeasureNote, c)
                mxNoteList = [] # clear for next chord
                mxLyricList = []

                offsetIncrement = c.quarterLength
                nLast = c # update

            # only increment Chords after completion
            offsetMeasureNote += offsetIncrement

        # mxDirections can be dynamics, repeat expressions, text expressions
        elif isinstance(mxObj, musicxmlMod.Direction):
            offsetDirection = mxToOffset(mxObj, divisions)
            if mxObj.getDynamicMark() is not None:
                #d = dynamics.Dynamic()
                #d.mx = mxObj
                # in rare cases there may be more than one dynamic in the same
                # direction
                for d in mxToDynamicList(mxObj):
                    _addToStaffReference(mxObj, d, staffReference)
                    #m.insert(offsetMeasureNote, d)
                    m._insertCore(offsetMeasureNote + offsetDirection, d)

            mxDirectionToSpanners(nLast, mxObj, spannerBundle)
            # TODO: a spanner
#             if mxObj.getWedge() is not None:
#                 w = dynamics.Wedge()
#                 w.mx = mxObj     
#                 _addToStaffReference(mxObj, w, staffReference)
#                 m._insertCore(offsetMeasureNote, w)

            if mxObj.getSegno() is not None:
                rm = mxToSegno(mxObj.getSegno())
                _addToStaffReference(mxObj, rm, staffReference)
                m._insertCore(offsetMeasureNote, rm)
            if mxObj.getCoda() is not None:
                rm = mxToCoda(mxObj.getCoda())
                _addToStaffReference(mxObj, rm, staffReference)
                m._insertCore(offsetMeasureNote, rm)

            if mxObj.getMetronome() is not None:
                #environLocal.printDebug(['got getMetronome', mxObj.getMetronome()])
                mm = mxToTempoIndication(mxObj.getMetronome())
                _addToStaffReference(mxObj, mm, staffReference)
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
                        _addToStaffReference(mxObj, re, staffReference)
                        m._insertCore(offsetMeasureNote + offsetDirection, re)
                    else:
                        _addToStaffReference(mxObj, te, staffReference)
                        m._insertCore(offsetMeasureNote + offsetDirection, te)

        elif isinstance(mxObj, musicxmlMod.Harmony):
            mxHarmony = mxObj
            h = mxToChordSymbol(mxHarmony)
            _addToStaffReference(mxObj, h, staffReference)
            m._insertCore(offsetMeasureNote, h)


    #environLocal.printDebug(['staffReference', staffReference])
    # if we have voices and/or if we used backup/forward, we may have
    # empty space in the stream
    if useVoices:
        for v in m.voices:
            if len(v) > 0: # do not bother with empty voices
                v.makeRests(inPlace=True)
            v._elementsChanged()
    m._elementsChanged()

    return m, staffReference, transposition

def measureToMusicXML(m):
    '''Translate a music21 Measure into a complete MusicXML string representation.

    Note: this method is called for complete MusicXML representation of a Measure, not for partial solutions in Part or Stream production. 

    >>> from music21 import *
    >>> m = stream.Measure()
    >>> m.repeatAppend(note.Note('g3'), 4)
    >>> post = musicxml.translate.measureToMusicXML(m)
    '''
    from music21 import stream, duration
    # search for time signatures, either defined locally or in context
    #environLocal.printDebug(['measureToMusicXML', m]) 
    # we already have a deep copy passed in, which happens in 
    # stream.Measure._getMusicXML()
    m.makeNotation(inPlace=True)

    out = stream.Part()
    out.append(m)
    # call the musicxml property on Stream
    return out.musicxml




#-------------------------------------------------------------------------------
# Streams


def streamPartToMx(part, instStream=None, meterStream=None,
                   refStreamOrTimeRange=None, spannerBundle=None):
    '''
    If there are Measures within this stream, use them to create and
    return an MX Part and ScorePart. 

    An `instObj` may be assigned from caller; this Instrument is pre-collected 
    from this Stream in order to configure id and midi-channel values. 

    The `meterStream`, if given, provides a template of meters. 
    '''
    from music21 import spanner
    from music21 import stream

    #environLocal.printDebug(['calling Stream._getMXPart', 'len(spannerBundle)', len(spannerBundle)])
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
    #environLocal.printDebug(['calling Stream._getMXPart', 'mxScorePart', mxScorePart, mxScorePart.get('id')])

    mxPart = musicxmlMod.Part()
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

        #environLocal.printDebug(['Stream._getMXPart: post makeNotation, length', len(measureStream)])

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
        if not measureStream.haveBeamsBeenMade():
            # if making beams, have to make a deep copy, as modifying notes
            try:
                measureStream.makeBeams(inPlace=True)
            except: # cannot match StreamException, must catch all
                pass
        if spannerBundle is None:
            spannerBundle = spanner.SpannerBundle(measureStream.flat)

    # make sure that all instances of the same class have unique ids
    spannerBundle.setIdLocals()

    # for each measure, call .mx to get the musicxml representation
    for obj in measureStream:
        # get instrument for every measure position
        moStart = obj.getOffsetBySite(measureStream)
        instSubStream = instStream.getElementsByOffset(moStart, 
                         moStart+obj.duration.quarterLength, 
                         includeEndBoundary=False)
        mxTranspose = None   
        if len(instSubStream) > 0:
            instSubObj = instSubStream[0]
            if part.atSoundingPitch in [False]:
                # if not at sounding pitch, encode transposition from instrument
                if instSubObj.transposition is not None:
                    mxTranspose = intervalToMXTranspose(
                                    instSubObj.transposition)
                    #raise TranslateException('cannot get transposition for a part that is not at sounding pitch.')
        mxPart.append(measureToMx(obj, spannerBundle=spannerBundle, 
                 mxTranspose=mxTranspose))
    # might to post processing after adding all measures to the Stream
    # TODO: need to find all MetricModulations and updateByContext
    # mxScorePart contains mxInstrument
    return mxScorePart, mxPart


def streamToMx(s, spannerBundle=None):
    '''
    Create and return a musicxml Score object from a Stream or Score

    This is the most common entry point for 
    conversion of a Stream to MusicXML. This method is 
    called on Stream from the musicxml property. 


    >>> from music21 import *
    >>> n1 = note.Note()
    >>> measure1 = stream.Measure()
    >>> measure1.insert(n1)
    >>> s1 = stream.Stream()
    >>> s1.insert(measure1)
    >>> mxScore = musicxml.translate.streamToMx(s1)
    >>> mxPartList = mxScore.get('partList')
    '''
    #environLocal.printDebug(['streamToMx:'])
    from music21 import spanner

    if len(s) == 0:
        # create an empty work
        from music21 import stream, note, metadata
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

    #environLocal.printDebug('calling Stream._getMX')
    # stores pairs of mxScorePart and mxScore
    mxComponents = []
    instList = []
    
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

    if s.hasPartLikeStreams():
        #environLocal.printDebug('Stream._getMX: interpreting multipart')
        # must set spanner after copying
        if spannerBundle is None: 
            # no spanner bundle provided, get one from the flat stream
            #spannerBundle = spanner.SpannerBundle(s.flat)
            spannerBundle = s.spannerBundle
            #environLocal.printDebug(['streamToMx(), hasPartLikeStreams(): loaded spannerBundle of size:', len(spannerBundle), 'id(spannerBundle)', id(spannerBundle)])
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
                raise TranslateException('infinite stream encountered')

            # only things that can be treated as parts are in finalStream
            # get a default instrument if not assigned
            instStream = obj.getInstruments(returnDefault=True)
            inst = instStream[0] # store first, as handled differently
            instIdList = [x.partId for x in instList]

            if inst.partId in instIdList: # must have unique ids 
                inst.partIdRandomize() # set new random id

            if (inst.midiChannel == None or 
                inst.midiChannel in midiChannelList):
                inst.autoAssignMidiChannel(usedChannels=midiChannelList)
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
            #mxComponents.append(obj._getMXPart(inst, meterStream, refStreamOrTimeRange))

    else: # assume this is the only part
        #environLocal.printDebug('Stream._getMX(): handling single-part Stream')
        # if no instrument is provided it will be obtained through s
        # when _getMxPart is called
        #mxComponents.append(s._getMXPart(None, meterStream))

        if spannerBundle is None: 
            # no spanner bundle provided, get one from the flat stream
            #spannerBundle = spanner.SpannerBundle(s.flat)
            spannerBundle = s.spannerBundle
            #environLocal.printDebug(['streamToMx(): loaded spannerBundle of size:', len(spannerBundle), 'id(spannerBundle)', id(spannerBundle)])
        mxScorePart, mxPart = streamPartToMx(s, meterStream=meterStream, 
                              spannerBundle=spannerBundle)
        mxComponents.append([mxScorePart, mxPart, s])
        #environLocal.pd(['mxComponents', mxComponents])

    # create score and part list
    # try to get mxScore from lead meta data first
    if s.metadata != None:
        mxScore = s.metadata.mx # returns an mx score
    else:
        mxScore = musicxmlMod.Score()

    # add text boxes
    for tb in textBoxes: # a stream of text boxes
        mxScore.creditList.append(textBoxToMxCredit(tb))

    mxScoreDefault = musicxmlMod.Score()
    mxScoreDefault.setDefaults()
    mxIdDefault = musicxmlMod.Identification()
    mxIdDefault.setDefaults() # will create a composer
    mxScoreDefault.set('identification', mxIdDefault)

    # merge metadata derived with default created
    mxScore = mxScore.merge(mxScoreDefault, returnDeepcopy=False)

    mxPartList = musicxmlMod.PartList()
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
        for sg in staffGroups:
            if sg.isLast(p):
                # find the spanner in the dictionary already-assigned
                for key, value in partGroupIndexRef.items():
                    if value is sg:
                        activeIndex = key
                        break
                mxPartGroup = musicxmlMod.PartGroup()
                mxPartGroup.set('type', 'stop')
                mxPartGroup.set('number', activeIndex)
                mxPartList.append(mxPartGroup)

    # addition of parts must simply be in the same order as above
    for mxScorePart, mxPart, p in mxComponents:
        mxScore.append(mxPart) # mxParts go on component list

    # set the mxPartList
    mxScore.set('partList', mxPartList)
    return mxScore

def _getUniqueStaffKeys(staffReferenceList):
    '''Given a list of staffReference dictionaries, collect and return a list of all unique keys except None
    '''
    post = []
    for staffReference in staffReferenceList:
        for key in staffReference.keys():
            if key is not None and key not in post:
                post.append(key)
    post.sort()
    return post

def _getStaffExclude(staffReference, targetKey):
    '''Given a staff reference dictionary, remove and combine in a list all elements that are not part of the given key. Thus, remove all entries under None (common to all) and th e given key. This then is the list of all elements that should be deleted.
    '''
    post = []
    for key in staffReference.keys():
        if key is None or int(key) == int(targetKey):
            continue
        post += staffReference[key]
    return post


def mxToStreamPart(mxScore, partId, spannerBundle=None, inputM21=None):
    '''Load a part into a new Stream or one provided by `inputM21` given an mxScore and a part name.

    The `spannerBundle` reference, when passed in, is used to accumulate Spanners. These are not inserted here. 

    Though it is incorrect MusicXML, PDFtoMusic creates empty measures when it should create full 
    measures of rests (possibly hidden).  This routine fixes that bug.  See http://musescore.org/en/node/15129 
    '''
    #environLocal.printDebug(['calling Stream._setMXPart'])

    from music21 import chord
    from music21 import dynamics
    from music21 import key
    from music21 import note
    from music21 import layout
    from music21 import bar
    from music21 import clef
    from music21 import meter
    from music21 import instrument
    from music21 import stream
    from music21 import spanner

    if inputM21 == None:
        # need a Score to load parts into
        from music21 import stream
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
        #instrumentObj.mx = mxInstrument
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

    for i, mxMeasure in enumerate(mxPart):
        # t here is transposition, if defined; otherwise it is None
        m, staffReference, t = mxToMeasure(mxMeasure, 
                               spannerBundle=spannerBundle)
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

        if m.timeSignature is not None:
            lastTimeSignature = m.timeSignature
        elif lastTimeSignature is None and m.timeSignature is None:
            # if no time sigature is defined, need to get a default
            ts = meter.TimeSignature()
            ts.load('%s/%s' % (defaults.meterNumerator, 
                               defaults.meterDenominatorBeatType))
            lastTimeSignature = ts
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
            else:
                mOffsetShift = lastTimeSignatureQuarterLength
        oMeasure += mOffsetShift

    # if we have multiple staves defined, add more parts, and transfer elements
    # note: this presently has to look at _idLastDeepCopyOf to get matches
    # to find removed elements after copying; this is probably not the
    # best way to do this. 

    # for this part, if any elements are components in the spannerBundle,
    # then then we need to update the spannerBundle after the part is copied

    streamPartStaff = None
    if mxPart.getStavesCount() > 1:
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
        for staffCount in _getUniqueStaffKeys(staffReferenceList):
            partIdStaff = '%s-Staff%s' % (partId, staffCount)
            #environLocal.printDebug(['partIdStaff', partIdStaff, 'copying streamPart'])
            # this deepcopy is necessary, as we will remove components
            # in each staff that do not belong
            streamPartStaff = copy.deepcopy(streamPart)
            # assign this as a PartStaff, a subclass of Part
            streamPartStaff.__class__ = stream.PartStaff
            # remove all elements that are not part of this staff
            mStream = streamPartStaff.getElementsByClass('Measure')
            for i, staffReference in enumerate(staffReferenceList):
                staffExclude = _getStaffExclude(staffReference, staffCount)
                m = mStream[i]
                for eRemove in staffExclude:
                    for eMeasure in m:
                        if eMeasure._idLastDeepCopyOf == id(eRemove):
                            m.remove(eMeasure)
                    for v in m.voices:
                        v.remove(eRemove)
                        for eVoice in v.elements:
                            if eVoice._idLastDeepCopyOf == id(eRemove):
                                v.remove(eVoice)
                # after adjusting voices see if voices can be reduced or
                # removed
                #environLocal.printDebug(['calling flattenUnnecessaryVoices: voices before:', len(m.voices)])
                m.flattenUnnecessaryVoices(force=False, inPlace=True)
                #environLocal.printDebug(['calling flattenUnnecessaryVoices: voices after:', len(m.voices)])
            # TODO: copying spanners may have created orphaned
            # spanners that no longer have valid connections
            # in this part; should be deleted
            streamPartStaff.addGroupForElements(partIdStaff) 
            streamPartStaff.groups.append(partIdStaff) 
            streamPartStaff._elementsChanged()
            s._insertCore(0, streamPartStaff)
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
        streamPart._elementsChanged()
        s._insertCore(0, streamPart)

    s._elementsChanged()
    # when adding parts to this Score
    # this assumes all start at the same place
    # even if there is only one part, it will be placed in a Stream
    if streamPartStaff is not None:
        return streamPartStaff
    else:
        return streamPart

def mxToStream(mxScore, spannerBundle=None, inputM21=None):
    '''Translate an mxScore into a music21 Score object.

    All spannerBundles accumulated at all lower levels are inserted here.
    '''
    # TODO: may not want to wait to this leve to insert spanners; may want to 
    # insert in lower positions if it makes sense

    from music21 import metadata
    from music21 import spanner
    from music21 import layout
    from music21 import text

    if inputM21 == None:
        from music21 import stream
        s = stream.Score()
    else:
        s = inputM21
    if spannerBundle == None:
        spannerBundle = spanner.SpannerBundle()

    partIdDictionary = mxScore.getPartNames()
    # values are part names
    partNameIds = partIdDictionary.keys()
    partNameIds.sort()
    for partId in partNameIds: # part names are part ids
        # NOTE: setting partId not partId: might change
        # return the part; however, it is still already attached to the Score
        try:
            part = mxToStreamPart(mxScore, partId=partId, 
                                  spannerBundle=spannerBundle, inputM21=s)
        except TranslateException as strerror:
            raise TranslateException('cannot translate part %s: %s' % (partId, strerror))
        # update dictionary to store music21 part
        partIdDictionary[partId] = part

    # get part/staff groups
    #environLocal.printDebug(['partgroups:', mxScore.getPartGroupData()])
    partGroupData = mxScore.getPartGroupData()
    for partGroup in partGroupData: # a list of dictionaries
        # create music21 spanner StaffGroup
        sg = layout.StaffGroup()
        for partId in partGroup['scorePartIds']:
            # get music21 part from partIdDictionary
            sg.addComponents(partIdDictionary[partId])
        # use configuration routine to transfer/set attributes;
        # sets complete status as well
        configureStaffGroupFromMxPartGroup(sg, partGroup['partGroup'])
        spannerBundle.append(sg) # will be added to the Score

    # add metadata object; this is placed after all other parts now
    # these means that both Parts and other objects live on Stream.
    md = metadata.Metadata()
    md.mx = mxScore # TODO: this needs to be updated to normal translation
    s._insertCore(0, md)

    # store credits on Score stream
    for mxCredit in mxScore.creditList:
        co = mxCreditToTextBox(mxCredit)
        s._insertCore(0, co) # insert position does not matter

    # only insert complete spanners; at each level possible, complete spanners
    # are inserted into either the Score or the Part
    # storing complete Part spanners in a Part permits extracting parts with spanners
    rm = []
    for sp in spannerBundle.getByCompleteStatus(True):
        s._insertCore(0, sp)
        rm.append(sp)
    for sp in rm:
        spannerBundle.remove(sp)

    s._elementsChanged()
    return s




#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass

    def testBasic(self):
        pass

    def testBarRepeatConversion(self):

        from music21 import converter, corpus, bar
        from music21.musicxml import testPrimitive
        

        #a = converter.parse(testPrimitive.simpleRepeat45a)
        # this is a good example with repeats
        s = corpus.parse('k80/movement3')
        for p in s.parts:
            post = p.flat.getElementsByClass('Repeat')
            self.assertEqual(len(post), 6)

        #a = corpus.parse('opus41no1/movement3')
        #s.show()

    def testVoices(self):

        from music21 import converter, stream
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.voiceDouble)
        m1 = s.parts[0].getElementsByClass('Measure')[0]
        self.assertEqual(m1.hasVoices(), True)

        self.assertEqual([v.id for v in m1.voices], [u'1', u'2'])

        self.assertEqual([e.offset for e in m1.voices[0]], [0.0, 1.0, 2.0, 3.0])
        self.assertEqual([e.offset for e in m1.voices['1']], [0.0, 1.0, 2.0, 3.0])

        self.assertEqual([e.offset for e in m1.voices[1]], [0.0, 2.0, 2.5, 3.0, 3.5])
        self.assertEqual([e.offset for e in m1.voices['2']], [0.0, 2.0, 2.5, 3.0, 3.5])
        post = s.musicxml
        #s.show()


    def testSlurInputA(self):
        from music21 import converter, stream
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.spannersSlurs33c)
        # have 10 spanners
        self.assertEqual(len(s.flat.getElementsByClass('Spanner')), 5)

        # can get the same from a a getAll search
        self.assertEqual(len(s.getAllContextsByClass('Spanner')), 5)

        # try to get all spanners from the first note
        self.assertEqual(len(s.flat.notesAndRests[0].getAllContextsByClass('Spanner')), 5)
        post = s.musicxml
        #s.show('t')
        #s.show()
        

    def testMultipleStavesPerPartA(self):
        from music21 import converter, stream
        from music21.musicxml import testPrimitive
        from music21.musicxml import testFiles
        from music21.musicxml import base

        mxDoc = base.Document()
        mxDoc.read(testPrimitive.pianoStaff43a)

        # parts are stored in component list
        p1 = mxDoc.score.componentList[0] 
        self.assertEqual(p1.getStavesCount(), 2)

        s = converter.parse(testPrimitive.pianoStaff43a)
        self.assertEqual(len(s.parts), 2)
        #s.show()
        self.assertEqual(len(s.parts[0].flat.getElementsByClass('Note')), 1)
        self.assertEqual(len(s.parts[1].flat.getElementsByClass('Note')), 1)

        self.assertEqual(isinstance(s.parts[0], stream.PartStaff), True)
        self.assertEqual(isinstance(s.parts[1], stream.PartStaff), True)


    def testMultipleStavesPerPartB(self):
        from music21 import converter, stream
        from music21.musicxml import testPrimitive
        from music21.musicxml import testFiles
        from music21.musicxml import base

        s = converter.parse(testFiles.moussorgskyPromenade)
        self.assertEqual(len(s.parts), 2)

        self.assertEqual(len(s.parts[0].flat.getElementsByClass('Note')), 19)
        # only chords in the second part
        self.assertEqual(len(s.parts[1].flat.getElementsByClass('Note')), 0)

        self.assertEqual(len(s.parts[0].flat.getElementsByClass('Chord')), 11)
        self.assertEqual(len(s.parts[1].flat.getElementsByClass('Chord')), 11)

        #s.show()


    def testMultipleStavesPerPartC(self):

        from music21 import corpus
        s = corpus.parse('schoenberg/opus19/movement2')        
        self.assertEqual(len(s.parts), 2)

        s = corpus.parse('schoenberg/opus19/movement6')        
        self.assertEqual(len(s.parts), 2)

        #s.show()


    def testSpannersA(self):

        from music21 import converter, stream
        from music21.musicxml import testPrimitive
        
        s = converter.parse(testPrimitive.spanners33a)
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

        from music21 import converter, stream, expressions
        from music21.musicxml import testPrimitive
    
        s = converter.parse(testPrimitive.textExpressions)
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

    def testTextExpressionsB(self):
        from music21 import stream, expressions, note
        textSrc = ['loud', 'soft', 'with\nspirit', 'with\nless\nintensity']
        sizeSrc = [8, 10, 12, 18, 24]
        positionVerticalSrc = [20, -80, 20]
        enclosureSrc = [None, None, None, 'rectangle', 'oval']
        styleSrc = ['italic', 'bold', None, 'bolditalic']
        
        p = stream.Part()
        for i in range(20):
            te = expressions.TextExpression(textSrc[i%len(textSrc)])
            te.size = sizeSrc[i%len(sizeSrc)]
            te.justify = 'left'
            te.positionVertical = positionVerticalSrc[
                                    i%len(positionVerticalSrc)]
            te.enclosure = enclosureSrc[i%len(enclosureSrc)]
            te.style = styleSrc[i%len(styleSrc)]
        
            p.append(te)
            p.append(note.Note(type='quarter'))
            for x in range(4):
                p.append(note.Rest(type='16th'))
        
        s = stream.Score()
        s.insert(0, p)
        #s.show()

        musicxml = s.musicxml
        #print musicxml
        match = """<direction>
        <direction-type>
          <words default-y="20.0" enclosure="rectangle" font-size="18.0" justify="left">with
spirit</words>
        </direction-type>
        <offset>0</offset>
      </direction>"""
        self.assertEqual(match in musicxml, True)


    def testTextExpressionsC(self):
        from music21 import corpus, expressions
        s =  corpus.parse('bwv66.6')
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
        from music21 import corpus, expressions
        # test placing text expression in arbitrary locations
        s =  corpus.parse('bwv66.6')
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
        from music21 import stream, note, expressions, layout
        s = stream.Stream()
        for i in range(6):
            m = stream.Measure(number=i+1)
            m.append(layout.SystemLayout(isNew=True))
            m.append(note.Rest(type='whole'))
            s.append(m)
        for m in s.getElementsByClass('Measure'):
            offsets = [x*.25 for x in range(16)]
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

        # test importing from muscixml
        from music21.musicxml import testPrimitive
        from music21 import converter, repeat

        # has one segno
        s = converter.parse(testPrimitive.repeatExpressionsA)
        self.assertEqual(len(s.flat.getElementsByClass(repeat.Segno)), 1)
        self.assertEqual(len(s.flat.getElementsByClass(repeat.Fine)), 1)
        self.assertEqual(len(s.flat.getElementsByClass(repeat.DalSegnoAlFine)), 1)

        raw = s.musicxml
        self.assertEqual(raw.find('<segno') > 0, True)
        self.assertEqual(raw.find('Fine') > 0, True)
        self.assertEqual(raw.find('D.S. al Fine') > 0, True)

        # has two codas
        s = converter.parse(testPrimitive.repeatExpressionsB)
        self.assertEqual(len(s.flat.getElementsByClass(repeat.Coda)), 2)
        # has one d.c.al coda
        self.assertEqual(len(s.flat.getElementsByClass(repeat.DaCapoAlCoda)), 1)

        raw = s.musicxml
        self.assertEqual(raw.find('<coda') > 0, True)
        self.assertEqual(raw.find('D.C. al Coda') > 0, True)


    def testImportRepeatBracketA(self):
        from music21 import corpus
        # has repeats in it; start with single emasure
        s = corpus.parse('opus74no1', 3)
        # there are 2 for each part, totaling 8
        self.assertEqual(len(s.flat.getElementsByClass('RepeatBracket')), 8)
        # can get for each part as spanners are stored in Part now
        raw = s.parts[1].musicxml
        self.assertEqual(raw.find("""<ending number="1" type="start"/>""")>1, True)    
        self.assertEqual(raw.find("""<ending number="1" type="stop"/>""")>1, True)    

        self.assertEqual(raw.find("""<ending number="2" type="start"/>""")>1, True)    
        self.assertEqual(raw.find("""<ending number="2" type="stop"/>""")>1, True)    

        # TODO: need to test getting repeat brackets after measure extraction
        #s.parts[0].show() # 72 through 77
        sSub = s.parts[0].measures(72, 77)
        # 2 repeat brackets are gathered b/c they are stored at the Part by 
        # default
        rbSpanners = sSub.getElementsByClass('RepeatBracket')
        self.assertEqual(len(rbSpanners), 2)

#         for m in sSub:
#             print m, id(m)
#         for rb in rbSpanners:
#             print rb, [id(x) for x in rb.getComponents()]

        #sSub.show('t')


    def testImportVoicesA(self):
        # testing problematic voice imports
        
        from music21.musicxml import testPrimitive
        from music21 import converter
        # this 2 part segments was importing multiple voices within
        # a measure, even though there was no data in the second voice
        s = converter.parse(testPrimitive.mixedVoices1a)
        self.assertEqual(len(s.parts), 2)
        # there are voices, but they have been removed
        self.assertEqual(len(s.parts[0].getElementsByClass(
            'Measure')[0].voices), 0)
        
        #s.parts[0].show('t')
        #self.assertEqual(len(s.parts[0].voices), 2)
        s = converter.parse(testPrimitive.mixedVoices1b)
        self.assertEqual(len(s.parts), 2)
        self.assertEqual(len(s.parts[0].getElementsByClass(
            'Measure')[0].voices), 0)
        #s.parts[0].show('t')
        
        # this case, there were 4, but there should be 2
        s = converter.parse(testPrimitive.mixedVoices2)
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
        from music21 import converter, repeat
        # has metronome marks defined, not with sound tag
        s = converter.parse(testPrimitive.metronomeMarks31c)
        # get all tempo indications
        mms = s.flat.getElementsByClass('TempoIndication')
        self.assertEqual(len(mms) > 3, True)
        #s.show()
        raw = s.musicxml.replace(' ', '').replace('\n', '')
        match = '<beat-unit>long</beat-unit><per-minute>100.0</per-minute>'
        self.assertEqual(raw.find(match) > 0, True)

        match = '<beat-unit>quarter</beat-unit><beat-unit-dot/><per-minute>100.0</per-minute>'
        self.assertEqual(raw.find(match) > 0, True)

        match = '<beat-unit>long</beat-unit><beat-unit>32nd</beat-unit><beat-unit-dot/>'
        self.assertEqual(raw.find(match) > 0, True)

        match = '<beat-unit>quarter</beat-unit><beat-unit-dot/><beat-unit>half</beat-unit><beat-unit-dot/>'
        self.assertEqual(raw.find(match) > 0, True)

        match = '<metronomeparentheses="yes">'
        self.assertEqual(raw.find(match) > 0, True)


    def testImportMetronomeMarksB(self):
        pass
        # TODO: look for files that only have sound tags and create MetronomeMarks
        # need to look for bundling of Words text expressions with tempo

        # has only sound tempo=x tag
        #s = converter.parse(testPrimitive.articulations01)
        #s.show()


    def testExportMetronomeMarksA(self):
        from music21 import stream, note, tempo
        p = stream.Part()
        p.repeatAppend(note.Note('g#3'), 8)
        # default quarter assumed
        p.insert(0, tempo.MetronomeMark(number=121.6))

        raw = p.musicxml
        match1 = '<beat-unit>quarter</beat-unit>'
        match2 = '<per-minute>121.6</per-minute>'
        self.assertEqual(raw.find(match1) > 0, True)
        self.assertEqual(raw.find(match2) > 0, True)

    def testExportMetronomeMarksB(self):
        from music21 import stream, note, tempo, duration

        p = stream.Part()
        p.repeatAppend(note.Note('g#3'), 8)
        # default quarter assumed
        p.insert(0, tempo.MetronomeMark(number=222.2, 
                referent=duration.Duration(quarterLength=.75)))
        #p.show()
        raw = p.musicxml
        match1 = '<beat-unit>eighth</beat-unit>'
        match2 = '<beat-unit-dot/>'
        match3 = '<per-minute>222.2</per-minute>'
        self.assertEqual(raw.find(match1) > 0, True)
        self.assertEqual(raw.find(match2) > 0, True)
        self.assertEqual(raw.find(match3) > 0, True)

    def testExportMetronomeMarksC(self):
        from music21 import stream, note, tempo, duration
        # set metronome positions at different offsets in a measure or part
        p = stream.Part()
        p.repeatAppend(note.Note('g#3'), 8)
        # default quarter assumed
        p.insert(0, tempo.MetronomeMark(number=222.2, 
                referent=duration.Duration(quarterLength=.75)))
        p.insert(3, tempo.MetronomeMark(number=106, parentheses=True))
        p.insert(7, tempo.MetronomeMark(number=93, 
                referent=duration.Duration(quarterLength=.25)))
        #p.show()
        
        raw = p.musicxml
        match1 = '<beat-unit>eighth</beat-unit>'
        match2 = '<beat-unit-dot/>'
        match3 = '<per-minute>222.2</per-minute>'
        match4 = '<metronome parentheses="yes">'
        match5 = '<metronome parentheses="no">'
        self.assertEqual(raw.find(match1) > 0, True)
        self.assertEqual(raw.find(match2) > 0, True)
        self.assertEqual(raw.find(match3) > 0, True)
        self.assertEqual(raw.count(match4) == 1, True)
        self.assertEqual(raw.count(match5) == 2, True)
        

    def testExportMetronomeMarksD(self):
        from music21 import stream, note, tempo
        p = stream.Part()
        p.repeatAppend(note.Note('g#3'), 8)
        # default quarter assumed
        p.insert(0, tempo.MetronomeMark('super fast', number=222.2))

        match1 = '<words default-y="45.0" font-weight="bold" justify="left">super fast</words>'
        match2 = '<per-minute>222.2</per-minute>'
        raw = p.musicxml
        self.assertEqual(raw.find(match1) > 0, True)
        self.assertEqual(raw.find(match2) > 0, True)

        p = stream.Part()
        p.repeatAppend(note.Note('g#3'), 8)
        # text does not show when implicit
        p.insert(0, tempo.MetronomeMark(number=132))
        match1 = '<words default-y="45.0" font-weight="bold" justify="left">fast</words>'
        match2 = '<per-minute>132</per-minute>'
        raw = p.musicxml
        self.assertEqual(raw.find(match1) > 0, False)
        self.assertEqual(raw.find(match2) > 0, True)

        p = stream.Part()
        p.repeatAppend(note.Note('g#3'), 8)
        mm = tempo.MetronomeMark('very slowly')
        self.assertEqual(mm.number, None)
        p.insert(0, mm)
        # text but no number
        match1 = '<words default-y="45.0" font-weight="bold" justify="left">very slowly</words>'
        match2 = '<per-minute>'
        raw = p.musicxml
        self.assertEqual(raw.find(match1) > 0, True)
        self.assertEqual(raw.find(match2) > 0, False)


    def testExportMetronomeMarksE(self):
        '''Test writing of sound tags
        '''
        from music21 import stream, note, tempo, meter
        p = stream.Part()
        p.repeatAppend(note.Note('g#3'), 8)
        # default quarter assumed
        p.insert(0, tempo.MetronomeMark('super slow', number=30.2))

        raw = p.musicxml    
        match1 = '<sound tempo="30.2"/>'
        self.assertEqual(raw.find(match1) > 0, True)
        #p.show()


        p = stream.Part()
        p.repeatAppend(note.Note('g#3'), 14)
        # default quarter assumed
        p.insert(meter.TimeSignature('2/4'))
        p.insert(0, tempo.MetronomeMark(number=30))
        p.insert(2, tempo.MetronomeMark(number=60))
        p.insert(4, tempo.MetronomeMark(number=120))
        p.insert(6, tempo.MetronomeMark(number=240))
        p.insert(8, tempo.MetronomeMark(number=240, referent=.75))
        p.insert(10, tempo.MetronomeMark(number=240, referent=.5))
        p.insert(12, tempo.MetronomeMark(number=240, referent=.25))
        #p.show()

        raw = p.musicxml    
        match1 = '<sound tempo="30.0"/>'
        self.assertEqual(raw.find(match1) > 0, True)
        match2 = '<sound tempo="60.0"/>'
        self.assertEqual(raw.find(match2) > 0, True)
        match3 = '<sound tempo="120.0"/>'
        self.assertEqual(raw.find(match3) > 0, True)
        match4 = '<sound tempo="240.0"/>'
        self.assertEqual(raw.find(match4) > 0, True)
        # from the dotted value
        match5 = '<sound tempo="180.0"/>'
        self.assertEqual(raw.find(match5) > 0, True)



    def testMetricModulationA(self):
        from music21 import stream, note, tempo

        s = stream.Stream()
        m1 = stream.Measure()
        m1.repeatAppend(note.Note(duration=1), 4)    
        mm1 = tempo.MetronomeMark(number=60.0)
        m1.insert(0, mm1)
        
        m2 = stream.Measure()
        m2.repeatAppend(note.Note(duration=1), 4)    
        # tempo.MetronomeMark(number=120.0)
        mmod1 = tempo.MetricModulation()
        # assign with an equivalent statement of the eight
        mmod1.oldMetronome = mm1.getEquivalentByReferent(.5)
        # set the other side of eq based on the desired  referent
        mmod1.setOtherByReferent(referent='quarter')
        m2.insert(0, mmod1)
        
        m3 = stream.Measure()
        m3.repeatAppend(note.Note(duration=1), 4)    
        mmod2 = tempo.MetricModulation()
        mmod2.oldMetronome = mmod1.newMetronome.getEquivalentByReferent(1.5)
        # set the other side of eq based on the desired  referent
        mmod2.setOtherByReferent(referent=1)
        m3.insert(0, mmod2)
        
        s.append([m1, m2, m3])
        raw = s.musicxml

        match = '<sound tempo="60.0"/>'
        self.assertEqual(raw.find(match) > 0, True)
        match = '<per-minute>60.0</per-minute>'
        self.assertEqual(raw.find(match) > 0, True)
        match = '<sound tempo="120.0"/>'
        self.assertEqual(raw.find(match) > 0, True)
        match = '<sound tempo="80.0"/>'
        self.assertEqual(raw.find(match) > 0, True)

        #s.show('t')
        #s.show()


    def testImportGraceNotesA(self):
        # test importing from muscixml
        from music21.musicxml import testPrimitive
        from music21 import converter, repeat
        s = converter.parse(testPrimitive.graceNotes24a)

        #s.show()
        
    def testNoteheadConversion(self):
        # test to ensure notehead functionality
        
        from music21 import note
        from music21.musicxml import translate
        n = note.Note('c3')
        n.notehead = 'diamond'
        
        out = n.musicxml
        match1 = '<notehead>diamond</notehead>'
        self.assertEqual(out.find(match1) > 0, True)
        
    def testNoteheadSmorgasbord(self):
        # tests the of many different types of noteheads
        
        from music21 import note, stream, expressions
        from music21.musicxml import translate
        p = stream.Part()
        n = note.Note('c3')
        n.notehead = 'diamond'
        tn = expressions.TextExpression('diamond')
        m = note.Note('c3')
        m.notehead = 'cross'
        tm = expressions.TextExpression('cross')
        l = note.Note('c3')
        l.notehead = 'triangle'
        tl = expressions.TextExpression('triangle')
        k = note.Note('c3')
        k.notehead = 'circle-x'
        tk = expressions.TextExpression('circle-x')
        j = note.Note('c3')
        j.notehead = 'x'
        tj = expressions.TextExpression('x')
        i = note.Note('c3')
        i.notehead = 'slash'
        ti = expressions.TextExpression('slash')
        h = note.Note('c3')
        h.notehead = 'square'
        th = expressions.TextExpression('square')
        g = note.Note('c3')
        g.notehead = 'arrow down'
        tg = expressions.TextExpression('arrow down')
        f = note.Note('c3')
        f.notehead = 'inverted triangle'
        tf = expressions.TextExpression('inverted triangle')
        f.addLyric('inverted triangle')
        e = note.Note('c3')
        e.notehead = 'back slashed'
        te = expressions.TextExpression('back slashed')
        d = note.Note('c3')
        d.notehead = 'fa'
        td = expressions.TextExpression('fa')
        c = note.Note('c3')
        c.notehead = 'normal'
        tc = expressions.TextExpression('normal')
        
        noteList = [tc, c, tn, n, th, h, tl, l, tf, f, tg, g, te, e, ti, i, tj, j, tm, m, tk, k, td, d]
        for note in noteList:
            p.append(note)
            
        #p.show()
        raw = p.musicxml    
        self.assertEqual(raw.find('<notehead>diamond</notehead>') > 0, True)
        self.assertEqual(raw.find('<notehead>square</notehead>') > 0, True)
        self.assertEqual(raw.find('<notehead>triangle</notehead>') > 0, True)
        self.assertEqual(raw.find('<notehead>inverted triangle</notehead>') > 0, True)
        self.assertEqual(raw.find('<notehead>arrow down</notehead>') > 0, True)
        self.assertEqual(raw.find('<notehead>back slashed</notehead>') > 0, True)
        self.assertEqual(raw.find('<notehead>slash</notehead>') > 0, True)
        self.assertEqual(raw.find('<notehead>x</notehead>') > 0, True)
        self.assertEqual(raw.find('<notehead>cross</notehead>') > 0, True)
        self.assertEqual(raw.find('<notehead>circle-x</notehead>') > 0, True)
        self.assertEqual(raw.find('<notehead>fa</notehead>') > 0, True)


    
    def testMusicXMLNoteheadtoMusic21Notehead(self):
        # test to ensure noteheads can be imported from MusicXML
        
        from music21 import note, converter
        from music21.musicxml import translate
        
        n = note.Note('c3')
        n.notehead = 'cross'
        noteMusicXML = n.musicxml
        m = converter.parse(noteMusicXML)
        self.assertEqual(m.flat.notes[0].notehead, 'cross')
        
        #m.show()
        
    def testNoteheadWithTies(self):
        #what happens when you have notes with two different noteheads tied together?
        
        from music21 import note, converter, spanner, stream, tie
        from music21.musicxml import translate
        
        n1 = note.Note('c3')
        n1.notehead = 'diamond'
        n1.tie = tie.Tie('start')
        n2 = note.Note('c3')
        n2.notehead = 'cross'
        n2.tie = tie.Tie('end')
        p = stream.Part()
        p.append(n1)
        p.append(n2)
        
        xml = p.musicxml
        m = converter.parse(xml)
        self.assertEqual(m.flat.notes[0].notehead, 'diamond')
        self.assertEqual(m.flat.notes[1].notehead, 'cross')
        
        #m.show()
        
    def testStemDirection(self):
        #testing the ability to changing stem directions
        
        from music21 import note, converter, spanner, stream, tie
        from music21.musicxml import translate
        
        n1 = note.Note('c3')
        n1.notehead = 'diamond'
        n1._setStemDirection('double')
        p = stream.Part()
        p.append(n1)
        xml = p.musicxml
        match1 = '<stem>double</stem>'
        self.assertEqual(xml.find(match1) > 0, True)
    
    def testStemDirImport(self):
        
        from music21 import note, converter, spanner, stream, tie
        from music21.musicxml import translate
        
        n1 = note.Note('c3')
        n1.notehead = 'diamond'
        n1._setStemDirection('double')
        p = stream.Part()
        p.append(n1)
        
        xml = p.musicxml
        m = converter.parse(xml)
        self.assertEqual(m.flat.notes[0].stemDirection, 'double')
    
    def testChordalStemDirImport(self):
        
        #NB: Finale apparently will not display a pitch that is a member of a chord without a stem
        #unless all chord members are without stems.
        
        from music21 import note, converter, spanner, stream, tie, chord
        from music21.musicxml import translate
        
        n1 = note.Note('f3')
        n1.notehead = 'diamond'
        n1.stemDirection ='down'
        n2 = note.Note('c4')
        n2.stemDirection ='noStem'
        c = chord.Chord([n1, n2])
        c.quarterLength = 2
        xml = c.musicxml
        #c.show()
        input = converter.parse(xml)
        chordResult = input.flat.notes[0]
#         for n in chordResult:
#             print n.stemDirection       

        self.assertEqual(chordResult.getStemDirection(chordResult.pitches[0]), 'down')
        self.assertEqual(chordResult.getStemDirection(chordResult.pitches[1]), 'noStem')
        
        

    def testStaffGroupsA(self):
        from music21.musicxml import testPrimitive
        from music21 import converter, spanner
        
        s = converter.parse(testPrimitive.staffGroupsNested41d)
        self.assertEqual(len(s.getElementsByClass('StaffGroup')), 2)
        #raw = s.musicxml
        sg1 = s.getElementsByClass('StaffGroup')[0]
        self.assertEqual(sg1.symbol, 'brace')
        self.assertEqual(sg1.barTogether, True)

        sg2 = s.getElementsByClass('StaffGroup')[1]
        self.assertEqual(sg2.symbol, 'line')
        self.assertEqual(sg2.barTogether, True)
            

    def testStaffGroupsB(self):
        from music21 import stream, note, spanner, layout
        p1 = stream.Part()
        p1.repeatAppend(note.Note(), 8)
        p2 = stream.Part()
        p3 = stream.Part()
        p4 = stream.Part()
        p5 = stream.Part()
        p6 = stream.Part()
        p7 = stream.Part()
        p8 = stream.Part()
        
        sg1 = layout.StaffGroup([p1, p2], symbol='brace', name='marimba')
        sg2 = layout.StaffGroup([p3, p4], symbol='bracket', name='xlophone')
        sg3 = layout.StaffGroup([p5, p6], symbol='line', barTogether=False)
        sg4 = layout.StaffGroup([p5, p6, p7], symbol='line', barTogether=False)
        
        s = stream.Score()
        s.insert([0, p1, 0, p2, 0, p3, 0, p4, 0, p5, 0, p6, 0, p7, 0, p8, 0, sg1, 0, sg2, 0, sg3, 0, sg4])
        #s.show()

        raw = s.musicxml
        match = '<group-symbol>brace</group-symbol>'
        self.assertEqual(raw.find(match) > 0, True)
        match = '<group-symbol>bracket</group-symbol>'
        self.assertEqual(raw.find(match) > 0, True)
        match = '<part-group number="1" type="start">'
        self.assertEqual(raw.find(match) > 0, True)
        match = '<part-group number="1" type="stop"/>'
        self.assertEqual(raw.find(match) > 0, True)
        match = '<part-group number="2" type="start">'
        self.assertEqual(raw.find(match) > 0, True)
        match = '<part-group number="2" type="stop"/>'
        self.assertEqual(raw.find(match) > 0, True)


    def testInstrumentTranspositionA(self):

        from music21.musicxml import testPrimitive        
        from music21 import converter

        s = converter.parse(testPrimitive.transposingInstruments72a)
        i1 = s.parts[0].flat.getElementsByClass('Instrument')[0]
        i2 = s.parts[1].flat.getElementsByClass('Instrument')[0]
        i3 = s.parts[2].flat.getElementsByClass('Instrument')[0]

        self.assertEqual(str(i1.transposition), '<music21.interval.Interval M-2>')
        self.assertEqual(str(i2.transposition), '<music21.interval.Interval M-6>')

        #s.show()
        # check output
        raw = s.musicxml
        self.assertEqual(raw.find('<diatonic>-5</diatonic>') > 0, True)
        self.assertEqual(raw.find('<chromatic>-9</chromatic>') > 0, True)
        self.assertEqual(raw.find('<diatonic>-1</diatonic>') > 0, True)
        self.assertEqual(raw.find('<chromatic>-2</chromatic>') > 0, True)


    def testInstrumentTranspositionB(self):

        from music21.musicxml import testPrimitive        
        from music21 import converter
        
        s = converter.parse(testPrimitive.transposing01)
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
        
        self.assertEqual(str([p for p in s.parts[0].flat.pitches]), '[A4, A4, A4, A4, A4, A4, A4, A4, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, A4, A4, A4, A4]')
        self.assertEqual(str([p for p in s.parts[1].flat.pitches]), '[B4, B4, B4, B4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, F#4, B4, B4, B4, B4, B4, B4]')
        self.assertEqual(str([p for p in s.parts[2].flat.pitches]), '[E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5, E5]')
        
        sSounding = s.toSoundingPitch(inPlace=False)
        self.assertEqual(str([p for p in sSounding.parts[0].flat.pitches]), '[A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4]')
        self.assertEqual(str([p for p in sSounding.parts[1].flat.pitches]), '[A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4]')
        self.assertEqual(str([p for p in sSounding.parts[2].flat.pitches]), '[A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4]')
        
        # chordification by default places notes at sounding pitch
        sChords = s.chordify()
        self.assertEqual(str([p for p in sChords.flat.pitches]), '[A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4, A4]')
        #sChords.show()
        

    def testInstrumentTranspositionC(self):
        # generate all transpositions on output
        from music21 import converter, stream
        from music21.musicxml import testPrimitive        

        s = converter.parse(testPrimitive.transposing01)
        self.assertEqual(len(s.flat.getElementsByClass('Instrument')), 7)
        #s.show()

        raw = s.musicxml
        self.assertEqual(raw.count('<transpose>'), 6)


    def testHarmonyA(self):
        from music21.musicxml import testPrimitive        
        from music21 import converter, corpus

        s = corpus.parse('leadSheet/berlinAlexandersRagtime.xml')
        self.assertEqual(len(s.flat.getElementsByClass('ChordSymbol')), 19)

        match = [h.XMLkind for h in s.flat.getElementsByClass('ChordSymbol')]
        self.assertEqual(match, [u'major', u'dominant', u'major', u'major', u'major', u'major', u'dominant', u'major', u'dominant', u'major', u'dominant', u'major', u'dominant', u'major', u'dominant', u'major', u'dominant', u'major', u'major'])

        match = [str(h.XMLroot) for h in s.flat.getElementsByClass('ChordSymbol')]
        self.assertEqual(match, ['F', 'C', 'F', 'B-', 'F', 'C', 'G', 'C', 'C', 'F', 'C', 'F', 'F', 'B-', 'F', 'F', 'C', 'F', 'C'])

        s = corpus.parse('monteverdi/madrigal.3.12.xml')
        self.assertEqual(len(s.flat.getElementsByClass('ChordSymbol')), 10)

        s = corpus.parse('leadSheet/fosterBrownHair.xml')
        self.assertEqual(len(s.flat.getElementsByClass('ChordSymbol')), 40)

        #s.show()
    def testHarmonyB(self):
        from music21 import stream, harmony, key
        s = stream.Stream()
        s.append(key.KeySignature(-2))
        
        h1 = harmony.ChordSymbol()
        h1.XMLroot = 'c'
        h1.XMLkind = 'minor-seventh'
        h1.XMLkindStr = 'm7'
        h1.duration.quarterLength = 4
        s.append(h1)
        
        h2 = harmony.ChordSymbol()
        h2.XMLroot = 'f'
        h2.XMLkind = 'dominant'
        h2.XMLkindStr = '7'
        h2.duration.quarterLength = 4
        s.append(h2)
        
        h3 = harmony.ChordSymbol()
        h3.XMLroot = 'b-'
        h3.XMLkind = 'major-seventh'
        h3.XMLkindStr = 'Maj7'
        h3.duration.quarterLength = 4
        s.append(h3)
        
        h4 = harmony.ChordSymbol()
        h4.XMLroot = 'e-'
        h4.XMLkind = 'major-seventh'
        h4.XMLkindStr = 'Maj7'
        h4.duration.quarterLength = 4
        s.append(h4)
        
        h5 = harmony.ChordSymbol()
        h5.XMLroot = 'a'
        h5.XMLkind = 'half-diminished'
        h5.XMLkindStr = 'm7b5'
        h5.duration.quarterLength = 4
        s.append(h5)
        
        h6 = harmony.ChordSymbol()
        h6.XMLroot = 'd'
        h6.XMLkind = 'dominant'
        h6.XMLkindStr = '7'
        h6.duration.quarterLength = 4
        s.append(h6)
        
        h7 = harmony.ChordSymbol()
        h7.XMLroot = 'g'
        h7.XMLkind = 'minor-sixth'
        h7.XMLkindStr = 'm6'
        h7.duration.quarterLength = 4
        s.append(h7)
        
        #s.show()
        raw = s.musicxml
        self.assertEqual(raw.find('<kind text="m7">minor-seventh</kind>') > 0, True)
        self.assertEqual(raw.find('<kind text="7">dominant</kind>') > 0, True)
        self.assertEqual(raw.find('<kind text="Maj7">major-seventh</kind>') > 0, True)
        self.assertEqual(raw.find('<kind text="Maj7">major-seventh</kind>') > 0, True)
        self.assertEqual(raw.find('<kind text="m7b5">half-diminished</kind>') > 0, True)

        self.assertEqual(raw.find('<root-step>C</root-step>') > 0, True)
        self.assertEqual(raw.find('<root-alter>-1</root-alter>') > 0, True)


    def testHarmonyC(self):

        from music21 import harmony, stream

        h = harmony.ChordSymbol()
        h.XMLroot = 'E-'
        h.XMLbass = 'B-'
        h.XMLinversion = 2
        #h.romanNumeral = 'I64'
        h.XMLkind = 'major'
        h.XMLkindStr = 'M'
        
        hd = harmony.ChordStepModification()
        hd.type = 'alter'
        hd.interval = -1
        hd.degree = 3
        h.addChordStepModification(hd)
        
        s = stream.Stream()
        s.append(h)
        #s.show()
        raw = s.musicxml
        self.assertEqual(raw.find('<root-alter>-1</root-alter>') > 0, True)
        self.assertEqual(raw.find('<degree-value>3</degree-value>') > 0, True)
        self.assertEqual(raw.find('<degree-type>alter</degree-type>') > 0, True)


    def testChordNoteheadFillA(self):
        from music21 import chord
        c = chord.Chord(['c4', 'g4'])
        c[0].noteheadFill = 'no'
        raw = c.musicxml
        self.assertEqual(raw.count('<notehead filled="no">normal</notehead>'), 1)
        c[1].noteheadFill = 'no'
        raw = c.musicxml
        self.assertEqual(raw.count('<notehead filled="no">normal</notehead>'), 2)

    def testSummedNumerators(self):
        from music21 import meter, stream, note

        # this forces a call to summed numerator translation
        ts1 = meter.TimeSignature('5/8') # assumes two partitions
        ts1.displaySequence.partition(['3/16','1/8','5/16'])
        
        ts2 = meter.TimeSignature('5/8') # assumes two partitions
        ts2.displaySequence.partition(['2/8', '3/8'])
        ts2.summedNumerator = True
        
        s = stream.Stream()
        for ts in [ts1, ts2]:            
            m = stream.Measure()
            m.timeSignature = ts
            n = note.Note('b')
            n.quarterLength = 0.5
            m.repeatAppend(n, 5)
            s.append(m)
        raw = s.musicxml


    def testOrnamentA(self):
        from music21 import stream, note, expressions, chord
        s = stream.Stream()
        s.repeatAppend(note.Note(), 4)
        s.repeatAppend(chord.Chord(['c4','g5']), 4)

        #s.insert(4, expressions.Trill())
        s.notes[3].expressions.append(expressions.Trill())
        s.notes[2].expressions.append(expressions.Mordent())
        s.notes[1].expressions.append(expressions.InvertedMordent())

        s.notes[6].expressions.append(expressions.Trill())
        s.notes[7].expressions.append(expressions.Mordent())
        s.notes[5].expressions.append(expressions.InvertedMordent())
        
        raw = s.musicxml
        #s.show()

        self.assertEqual(raw.count('<trill-mark'), 2)
        self.assertEqual(raw.count('<ornaments>'), 6)
        self.assertEqual(raw.count('<inverted-mordent/>'), 2)
        self.assertEqual(raw.count('<mordent/>'), 2)


    def testOrnamentB(self):
        from music21 import stream, note, expressions, chord, corpus

        s = corpus.parse('opus133')
        ex = s.parts[0]        
        countTrill = 0
        for n in ex.flat.notes:
            for e in n.expressions:
                if 'Trill' in e.classes:
                    countTrill += 1
        self.assertEqual(countTrill, 54)


    def testOrnamentC(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        # has many ornaments
        s = converter.parse(testPrimitive.notations32a)

        #s.flat.show('t')
        self.assertEqual(len(s.flat.getElementsByClass('Tremolo')), 1)


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


            

    def testNoteColorA(self):
        from music21 import note, stream, chord
        n1 = note.Note()
        n2 = note.Note()
        n2.color = '#ff1111'
        n3 = note.Note()
        n3.color = '#1111ff'
        r1 = note.Rest()
        r1.color = '#11ff11'

        c1 = chord.Chord(['c2', 'd3', 'e4'])
        c1.color = '#ff0000'
        s = stream.Stream()
        s.append([n1, n2, n3, r1, c1])
        #s.show()

        raw = s.musicxml
        # three color indications
        self.assertEqual(raw.count("color="), 8) #exports to notehead AND note, so increased from 6 to 8
        # color set at note level only for rest, so only 1
        self.assertEqual(raw.count('note color="#11ff11"'), 1)
    

    def testNoteColorB(self):
        from music21 import converter, stream
        from music21.musicxml import testPrimitive        

        s = converter.parse(testPrimitive.colors01)
        #s.show()
        raw = s.musicxml
        self.assertEqual(raw.count("color="), 8) #exports to notehead AND note, so increased from 6 to 8
        # color set at note level only for rest, so only 1
        self.assertEqual(raw.count('note color="#11ff11"'), 1)


    def testTextBoxA(self):
        from music21 import converter, stream
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.textBoxes01)
        tbs = s.flat.getElementsByClass('TextBox')
        self.assertEqual(len(tbs), 5)

        msg = []
        for tb in tbs:
            msg.append(tb.content)
        self.assertEqual(msg, [u'This is a text box!', u'pos 200/300 (lower left)', u'pos 1000/300 (lower right)', u'pos 200/1500 (upper left)', u'pos 1000/1500 (upper right)'])
        
    def testTextBoxB(self):
        from music21 import converter, stream, text
        y = 1000
        s = stream.Stream()
        
        tb3 = text.TextBox('c', 200, y)
        tb3.size = 40
        tb3.alignVertical = 'bottom'
        s.append(tb3)
        
        tb2 = text.TextBox('B', 300, y)
        tb2.size = 60
        tb2.alignVertical = 'bottom'
        s.append(tb2)
        
        tb2 = text.TextBox('!*&', 500, y)
        tb2.size = 100
        tb2.alignVertical = 'bottom'
        s.append(tb2)
        
        tb1 = text.TextBox('slowly', 700, y)
        tb1.alignVertical = 'bottom'
        tb1.size = 20
        tb1.style = 'italic'
        s.append(tb1)
        
        
        tb1 = text.TextBox('A', 850, y)
        tb1.alignVertical = 'bottom'
        tb1.size = 80
        tb1.weight = 'bold'
        tb1.style = 'italic'
        s.append(tb1)
        
        raw = s.musicxml
        self.assertEqual(raw.count('</credit>'), 5)
        self.assertEqual(raw.count('font-size'), 5)


    def testImportSlursA(self):
        from music21 import corpus, spanner
        # this is a good test as this encoding uses staffs, not parts
        # to encode both parts; this requires special spanner handling
        s = corpus.parse('k545')
        slurs = s.flat.getElementsByClass(spanner.Slur)
        # TODO: this value should be 2, but due to staff encoding we 
        # have orphaned spanners that are not cleaned up
        self.assertEqual(len(slurs), 4)

        n1, n2 = s.parts[0].flat.notes[3], s.parts[0].flat.notes[5]
        #environLocal.pd(['n1', n1, 'id(n1)', id(n1), slurs[0].getComponentIds(), slurs[0].getComponents()])
        self.assertEqual(id(n1) == slurs[0].getComponentIds()[0], True)
        self.assertEqual(id(n2) == slurs[0].getComponentIds()[1], True)

        #environLocal.pd(['n2', n2, 'id(n2)', id(n2), slurs[0].getComponentIds()])
        raw = s.musicxml
        self.assertEqual(raw.count('<slur'), 4) # 2 pairs of start/stop
        #s.show()


    def testImportWedgeA(self):

        from music21 import converter, stream
        from music21.musicxml import testPrimitive        

        s = converter.parse(testPrimitive.spanners33a)
        self.assertEqual(len(s.flat.getElementsByClass('Crescendo')), 1)
        self.assertEqual(len(s.flat.getElementsByClass('Diminuendo')), 1)

        raw = s.musicxml # test roundtrip output
        self.assertEqual(raw.count('type="crescendo"'), 1)
        self.assertEqual(raw.count('type="diminuendo"'), 1)
        #s.show('t')
        #s.show()


    def testImportWedgeB(self):
        from music21 import converter, stream
        from music21.musicxml import testPrimitive        

        # this produces a single component cresc
        s = converter.parse(testPrimitive.directions31a)
        self.assertEqual(len(s.flat.getElementsByClass('Crescendo')), 2)
        raw = s.musicxml # test roundtrip output
        self.assertEqual(raw.count('type="crescendo"'), 2)

        #s.show()


    def testBracketImportA(self):
        from music21 import converter, stream
        from music21.musicxml import testPrimitive        

        s = converter.parse(testPrimitive.directions31a)
        #s.show()
        self.assertEqual(len(s.flat.getElementsByClass('Line')), 2)
        raw = s.musicxml # test roundtrip output
        self.assertEqual(raw.count('<bracket'), 4)


    def testBracketImportB(self):
        from music21 import converter, stream
        from music21.musicxml import testPrimitive        

        s = converter.parse(testPrimitive.spanners33a)
        #s.show()
        self.assertEqual(len(s.flat.getElementsByClass('Line')), 6)
        raw = s.musicxml # test roundtrip output
        self.assertEqual(raw.count('<bracket'), 12)


    def testTrillExtensionImportA(self):
        from music21 import converter, stream
        from music21.musicxml import testPrimitive        
        s = converter.parse(testPrimitive.notations32a)
        #s.show()
        self.assertEqual(len(s.flat.getElementsByClass('TrillExtension')), 2)
        raw = s.musicxml # test roundtrip output
        self.assertEqual(raw.count('<wavy-line'), 4)


    def testGlissandoImportA(self):
        from music21 import converter, stream
        from music21.musicxml import testPrimitive        
        s = converter.parse(testPrimitive.spanners33a)
        #s.show()
        self.assertEqual(len(s.flat.getElementsByClass('Glissando')), 1)
        raw = s.musicxml # test roundtrip output
        self.assertEqual(raw.count('<glissando'), 2)


    def testImportDashes(self):
        # dashes are imported as Lines (as are brackets)
        from music21 import converter, stream
        from music21.musicxml import testPrimitive        

        s = converter.parse(testPrimitive.spanners33a)
        self.assertEqual(len(s.flat.getElementsByClass('Line')), 6)

        #s.show()

        raw = s.musicxml # test roundtrip output
        self.assertEqual(raw.count('<bracket'), 12)


    def testImportGraceA(self):
        from music21 import converter, stream
        from music21.musicxml import testPrimitive        

        s = converter.parse(testPrimitive.graceNotes24a)
        #s.show()        
        match = [str(p) for p in s.pitches]
        #print match
        self.assertEqual(match, ['D5', 'C5', 'E5', 'D5', 'C5', 'D5', 'C5', 'D5', 'C5', 'D5', 'C5', 'E5', 'D5', 'C5', 'D5', 'C5', 'D5', 'C5', 'E5', 'E5', 'F4', 'C5', 'D#5', 'C5', 'D-5', 'A-4', 'C5', 'C5'])
        
        raw = s.musicxml
        self.assertEqual(raw.count('<grace'), 15)



    def testImportGraceB(self):
        from music21 import note, stream

        ng1 = note.Note('c4', quarterLength=.5).getGrace()
        ng1.duration.stealTimeFollowing = .5
        ng1.duration.slash = False
        n1 = note.Note('g4', quarterLength=2)

        ng2 = note.Note('c4', quarterLength=.5).getGrace()
        ng2.duration.stealTimePrevious = .25
        n2 = note.Note('d4', quarterLength=2)
        
        s = stream.Stream()
        s.append([ng1, n1, ng2, n2])
        #s.show()

        raw = s.musicxml
        self.assertEqual(raw.count('slash="no"'), 1)
        self.assertEqual(raw.count('slash="yes"'), 1)
        
        
    def testBarException(self):
        from music21 import musicxml
        from music21 import bar
        mxBarline = musicxml.Barline()
        mxBarline.set('barStyle', 'light-heavy')
        #Rasing the BarException
        self.assertRaises( bar.BarException, mxToRepeat, mxBarline)
        
        mxRepeat = musicxml.Repeat()
        mxRepeat.set('direction', 'backward')
        mxBarline.set('repeatObj', mxRepeat)
        
        #all fine now, no exceptions here
        mxToRepeat(mxBarline)
        
        #Raising the BarException       
        mxBarline.set('barStyle', 'wunderbar')
        self.assertRaises( bar.BarException, mxToRepeat, mxBarline)
        
        
        




#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [mxToStream, streamToMx]

if __name__ == "__main__":
    # sys.arg test options will be used in mainTest()
    music21.mainTest(Test)




#------------------------------------------------------------------------------
# eof
