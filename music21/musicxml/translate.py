# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         musicxml/translate.py
# Purpose:      Translate MusicXML and music21 objects
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2010-11 The music21 Project
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




def mxToTempoIndication(mxMetronome, mxWords=None):
    '''Given an mxMetronome, convert to either a TempoIndication subclass, either a tempo.MetronomeMark or tempo.MetricModulation. 

    >>> from music21 import *
    >>> m = musicxml.Metronome()
    >>> bu = musicxml.BeatUnit('half')
    >>> pm = musicxml.PerMinute(125)
    >>> m.append(bu)
    >>> m.append(pm)
    >>> musicxml.translate.mxToTempoIndication(m)
    <music21.tempo.MetronomeMark Quarter=125.0>

    '''
    from music21 import tempo, duration

    # get lists of durations and texts
    durations = []
    numbers = [] 

    dActive = None
    for mxObj in mxMetronome.componentList:
        if isinstance(mxObj, musicxmlMod.BeatUnit):
            # if we have not yet stored the dActive
            if dActive is not None:
                durations.append(dActive)
                dActive = None # clear
            type = duration.musicXMLTypeToType(mxObj.charData)
            dActive = duration.Duration(type=type)
        if isinstance(mxObj, musicxmlMod.BeatUnitDot):
            if dActive is None:
                raise TranslateException('encountered metronome components out of order')
            dActive.dots += 1 # add one dot each time these are encountered
        # should come last
        if isinstance(mxObj, musicxmlMod.PerMinute):            
            # store as a number
            if mxObj.charData != '':
                numbers.append(float(mxObj.charData))


    if mxMetronome.isMetricModulation():
        mm = tempo.MetricModulation()
        # create two metronome marks and set
    else:
        mm = tempo.MetronomeMark()
        if len(numbers) > 0:
            mm.number = numbers[0]
        if len(durations) > 0:
            mm.referent = durations[0]
        # TODO: set text if defined in words
        if mxWords is not None:
            pass

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
    hideNumericalMetro = [] # if numbers implicit, hide metro; a lost
    # store the last value necessary as a sounding tag in bpm
    soundingQuarterBPM = None 
    if 'MetronomeMark' in ti.classes:
        # will not show a number of implicit
        if ti.numberImplicit or ti.number is None:
            #environLocal.printDebug(['found numberImplict', ti.numberImplicit])
            hideNumericalMetro.append(True) 
        else:
            durs.append(ti.referent)
            numbers.append(ti.number)
        # determine number sounding; first, get from numberSounding, then
        # number (if implicit, that is fine); get in terms of quarter bpm
        soundingQuarterBPM = ti.getQuarterBPM()
        
    elif 'MetricModulation' in ti.classes:
        pass
        return []
        # add two ti.referents from each contained
        # check that len of numbers is == to len of durs; required here
        # soundingQuarterBPM should be obtained from the last MetronomeMark

    mxComponents = []
    for i, d in enumerate(durs):
        # charData of BeatUnit is the type string
        mxSub = musicxmlMod.BeatUnit(duration.typeToMusicXMLType(d.type))
        mxComponents.append(mxSub)
        for x in range(d.dots):
            mxComponents.append(musicxmlMod.BeatUnitDot())
        if len(numbers) > 0:
            mxComponents.append(musicxmlMod.PerMinute(numbers[0]))

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
    if ti.getTextExpression(returnImplicit=False) is not None:
        mxDirection = textExpressionToMx(
                      ti.getTextExpression(returnImplicit=False))
        mxObjects.append(mxDirection)    

    return mxObjects


def repeatToMx(r):
    '''
    >>> from music21 import *
    >>> b = bar.Repeat('light-heavy')
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
        raise BarException('cannot handle direction format:', r.direction)

    if r.times != None:
        mxRepeat.set('times', r.times)

    mxBarline.set('repeatObj', mxRepeat)
    return mxBarline

def mxToRepeat(mxBarline, inputM21=None):
    '''Given an mxBarline, file the necessary parameters

    >>> from music21 import *
    >>> mxRepeat = musicxml.Repeat()
    >>> mxRepeat.set('direction', 'forward')
    >>> mxRepeat.get('times') == None
    True
    >>> mxBarline = musicxml.Barline()
    >>> mxBarline.set('barStyle', 'light-heavy')
    >>> mxBarline.set('repeatObj', mxRepeat)
    >>> b = bar.Repeat()
    >>> b.mx = mxBarline
    >>> b.style
    'final'
    >>> b.direction
    'start'
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
        raise BarException('attempting to create a Repeat from an MusicXML bar that does not define a repeat')

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






#-------------------------------------------------------------------------------
# Pitch and pitch components

def pitchToMx(p):
    '''
    Returns a musicxml.Note() object

    >>> from music21 import *
    >>> a = pitch.Pitch('g#4')
    >>> c = a.mx
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
    mxNote.setDefaults()
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
    >>> a.mx = c
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
            p.accidental = pitch.Accidental(float(acc))
            p.accidental.displayStatus = False
    p.octave = int(mxPitch.get('octave'))
    p._pitchSpaceNeedsUpdating = True


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

def mxToDuration(mxNote, inputM21):
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
    if mxNote.duration != None: 
        if mxNote.get('type') != None:
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

        if mxTimeModification != None:
            tup = duration.Tuplet()
            tup.mx = mxNote # get all necessary config from mxNote

            #environLocal.printDebug(['created Tuplet', tup])
            # need to see if there is more than one component
            #self.components[0]._tuplets.append(tup)
        else:
            tup = None

        # two ways to create durations, raw and cooked
        durRaw = duration.Duration() # raw just uses qLen
        # the qLen set here may not be computable, but is not immediately
        # computed until setting components
        durRaw.quarterLength = qLen

        if forceRaw:
            #environLocal.printDebug(['forced to use raw duration', durRaw])
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

            #environLocal.printDebug(['got durRaw, durCooked:', durRaw, durCooked])
            if durUnit.quarterLength != durCooked.quarterLength:
                environLocal.printDebug(['error in stored MusicXML representaiton and duration value', durRaw, durCooked])
            # old way just used qLen
            #self.quarterLength = qLen
            d.components = durCooked.components
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
    #environLocal.printDebug(['in _getMX', d, d.quarterLength])

    if d.dotGroups is not None and len(d.dotGroups) > 1:
        d = d.splitDotGroups()

    if d.isLinked == True or len(d.components) > 1: # most common case...
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

    return post # a list of mxNotes


def durationToMusicXML(d):
    '''Translate a music21 :class:`~music21.duration.Duration` into a complete MusicXML representation. 
    '''
    from music21 import duration, note

    # make a copy, as we this process will change tuple types
    dCopy = copy.deepcopy(d)
    # this update is done in note output
    #updateTupletType(dCopy.components) # modifies in place

    n = note.Note()
    n.duration = dCopy
    # call the musicxml property on Stream
    return generalNoteToMusicXML(n)



def mxToOffset(mxDirection, mxDivisions):
    '''Translate a MusicXML :class:`~music21.musicxml.Direction` with an offset value to an offset in music21. 
    '''
    if mxDivisions is None:
        raise TranslateException(
        "cannont determine MusicXML duration without a reference to a measure (%s)" % mxNote)
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
    >>> b = a.mx
    >>> a = meter.TimeSignature('3/4+2/4')
    >>> b = a.mx
    '''
    #mxTimeList = []
    mxTime = musicxmlMod.Time()
    # always get a flat version to display any subivisions created
    fList = [(mt.numerator, mt.denominator) for mt in ts.displaySequence.flat._partition]
    if ts.summedNumerator:
        # this will try to reduce any common denominators into 
        # a common group
        fList = fractionToSlashMixed(fList)

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
    >>> c.mx = b.timeList
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
    >>> a._positionRelativeY = -10
    >>> b = a.mx
    >>> b[0][0][0].get('tag')
    'ppp'
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
    >>> a.mx = mxDirection
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

    >>> from music21 import *
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
# Instruments


def instrumentToMx(i):
    '''
    >>> from music21 import *
    >>> i = instrument.Celesta()
    >>> mxScorePart = i.mx
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

    if i.partName != None:
        mxScorePart.partName = i.partName
    elif i.partName == None: # get default, as required
        mxScorePart.partName = defaults.partName

    if i.partAbbreviation != None:
        mxScorePart.partAbbreviation = i.partAbbreviation

    if i.instrumentName != None or i.instrumentAbbreviation != None:
        mxScoreInstrument = musicxmlMod.ScoreInstrument()
        # set id to same as part for now
        mxScoreInstrument.set('id', i.instrumentId)
        # can set these to None
        mxScoreInstrument.instrumentName = i.instrumentName
        mxScoreInstrument.instrumentAbbreviation = i.instrumentAbbreviation
        # add to mxScorePart
        mxScorePart.scoreInstrumentList.append(mxScoreInstrument)

    if i.midiProgram != None:
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
    if inputM21 is None:
        i = instrument.Instrument()
    else:
        i = inputM21

    i.partId = mxScorePart.get('id')
    i.partName = mxScorePart.get('partName')
    i.partAbbreviation = mxScorePart.get('partAbbreviation')

    # for now, just get first instrument
    if len(mxScorePart.scoreInstrumentList) > 0:
        mxScoreInstrument = mxScorePart.scoreInstrumentList[0]
        i.instrumentName = mxScoreInstrument.get('instrumentName')
        i.instrumentAbbreviation = mxScoreInstrument.get(
                                        'instrumentAbbreviation')
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
# Chords

def chordToMx(c):
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
    >>> mxNoteList = a.mx
    >>> len(mxNoteList) # get three mxNotes
    3
    >>> mxNoteList[0].get('chord')
    False
    >>> mxNoteList[1].get('chord')
    True
    >>> mxNoteList[2].get('chord')
    True
    '''
    #environLocal.printDebug(['chordToMx', c])
    mxNoteList = []
    durPos = 0 # may have more than one dur
    durPosLast = len(c.duration.mx) - 1
    for mxNoteBase in c.duration.mx: # returns a list of mxNote objs
        # merge method returns a new object
        chordPos = 0
        mxNoteChordGroup = []
        for pitchObj in c.pitches:
            # copy here, before merge
            mxNote = copy.deepcopy(mxNoteBase)
            mxNote = mxNote.merge(pitchObj.mx, returnDeepcopy=False)
            if chordPos > 0:
                mxNote.set('chord', True)
            # get color from within .editorial using attribute
            mxNote.set('color', c.color)

            # only add beam to first note in group
            if c.beams != None and chordPos == 0:
                mxNote.beamList = c.beams.mx

            # if this note, not a component duration,
            # need to add this to the last-encountered mxNote

            # get mxl objs from tie obj
            #mxTieList, mxTiedList = c.tie.mx 
            tieObj = c.getTie(pitchObj) # get for each pitch
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
                    #environLocal.printDebug(['rejecting tie creation', 'tieObj.type', tieObj.type, 'durPos', durPos])
            chordPos += 1
            mxNoteChordGroup.append(mxNote)
        
        # add chord group to note list
        mxNoteList += mxNoteChordGroup
        durPos += 1

    # only applied to first note
    for lyricObj in c.lyrics:
        mxNoteList[0].lyricList.append(lyricObj.mx)

    # if we have any articulations, they only go on the first of any 
    # component notes
    mxArticulations = musicxmlMod.Articulations()
    for i in range(len(c.articulations)):
        obj = c.articulations[i]
        if hasattr(obj, 'mx'):
#             if i == 0: # assign first
#                 mxArticulations = obj.mx # mxArt... stores more than one artic
#             else: # concatenate any remaining
#                 mxArticulations += obj.mx
            mxArticulations.append(obj.mx)
    #if mxArticulations != None:
    if len(mxArticulations) > 0:
        mxNoteList[0].notationsObj.componentList.append(mxArticulations)

    # notations and articulations are mixed in musicxml
    for i in range(len(c.expressions)):
        obj = c.expressions[i]
        if hasattr(obj, 'mx'): 
            mxNoteList[0].notationsObj.componentList.append(obj.mx)

    return mxNoteList

def mxToChord(mxNoteList, inputM21=None):
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
    '''
    from music21 import chord
    from music21 import pitch
    from music21 import tie

    if inputM21 == None:
        c = chord.Chord()
    else:
        c = inputM21

    # assume that first chord is the same duration for all parts
    c.duration.mx = mxNoteList[0]
    pitches = []
    ties = [] # store equally spaced list; use None if not defined
    for mxNote in mxNoteList:
        # extract pitch pbjects     
        p = pitch.Pitch()
        p.mx = mxNote # will extract pitch info from mxNote
        pitches.append(p)

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


#-------------------------------------------------------------------------------
# Notes

def generalNoteToMusicXML(n):
    '''Translate a music21 :class:`~music21.note.Note` into a complete MusicXML representation. 

    >>> from music21 import *
    >>> n = note.Note('c3')
    >>> n.quarterLength = 3
    >>> post = musicxml.translate.generalNoteToMusicXML(n)
    >>> post[-100:].replace('\\n', '')
    '/type>        <dot/>        <notations/>      </note>    </measure>  </part></score-partwise>'
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
    
def noteheadToMxNotehead(n, spannerBundle=None):
    '''
    Translate a music21 :class:`~music21.note.Note` object 
    into a musicxml.Notehead object.
    '''
    
    mxNotehead = musicxmlMod.Notehead()

	#Ensures that the music21 notehead value is supported by MusicXML, and then sets the MusicXML notehead's 'charaData' to the value of the Music21 notehead.
    supportedValues = ['slash', 'triangle', 'diamond', 'square', 'cross', 'x' , 'circle-x', 'inverted', 'triangle', 'arrow down', 'arrow up', 'slashed', 'back slashed', 'normal', 'cluster', 'none', 'do', 're', 'mi', 'fa', 'so', 'la', 'ti', 'circle dot', 'left triangle', 'rectangle']
    if n.notehead not in supportedValues:
        raise NoteheadException('This notehead type is not supported by MusicXML.')
    else:
        mxNotehead.set('charData', n.notehead)
        
    return mxNotehead

def noteToMxNotes(n, spannerBundle=None):
    '''
    Translate a music21 :class:`~music21.note.Note` into a 
    list of :class:`~music21.musicxml.Note` objects.
    '''
    #Attributes of notes are merged from different locations: first from the 
    #duration objects, then from the pitch objects. Finally, GeneralNote 
    #attributes are added.
    if spannerBundle is not None:
        # this will get all spanners that participate with this note
        if len(spannerBundle) > 0:
            pass # assume have already gathered
            #environLocal.printDebug(['noteToMxNotes(): spannerBundle pre-filter:', spannerBundle, 'spannerBundle[0]', spannerBundle[0], 'id(spannerBundle[0])', id(spannerBundle[0]), 'spannerBundle[0].getComponentIds()', spannerBundle[0].getComponentIds(), 'id(n)', id(n)])

        # get a new spanner bundle that only has components relevant to this 
        # note.
        spannerBundle = spannerBundle.getByComponent(n)

        #environLocal.printDebug(['noteToMxNotes(): spannerBundle post-filter by component:', spannerBundle])

    mxNoteList = []
    pitchMx = n.pitch.mx
    noteColor = n.color

    # todo: this is not yet implemented in music21 note objects; to do
    #mxNotehead = musicxmlMod.Notehead()
    #mxNotehead.set('charData', defaults.noteheadUnpitched)


    for mxNote in n.duration.mx: # returns a list of mxNote objs
        # merge method returns a new object; but can use existing here
        mxNote = mxNote.merge(pitchMx, returnDeepcopy=False)
        # get color from within .editorial using attribute
        if noteColor != "":
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

    # if we have any articulations, they only go on the first of any 
    # component notes
    mxArticulations = musicxmlMod.Articulations()
    for artObj in n.articulations:
        mxArticulations.append(artObj.mx) # returns mxArticulationMark to append to mxArticulations
    if len(mxArticulations) > 0:
        mxNoteList[0].notationsObj.componentList.append(mxArticulations)

    # notations and articulations are mixed in musicxml
    for expObj in n.expressions:
        if hasattr(expObj, 'mx'):
            mxNoteList[0].notationsObj.componentList.append(expObj.mx)

    

    if spannerBundle is not None:
        # already filtered for just the spanner that have this note as
        # a component
        for su in spannerBundle.getByClass('Slur'):     
            mxSlur = musicxmlMod.Slur()
            mxSlur.set('number', su.idLocal)
            mxSlur.set('placement', su.placement)
            # is this note first in this spanner?
            if su.isFirst(n):
                mxSlur.set('type', 'start')
            elif su.isLast(n):
                mxSlur.set('type', 'stop')
            else:
                # this may not always be an error
                environLocal.printDebug(['have a slur that has this note as a component but that note is neither a start nor an end.', su, n])
                #raise TranslateException('have a slur that has this note as a component but that note is neither a start nor an end.')
                continue

            mxNoteList[0].notationsObj.componentList.append(mxSlur)
            
    #Adds the notehead type if it is not set to the default 'normal'.
    if n.notehead != 'normal':
       mxNoteList[0].noteheadObj = noteheadToMxNotehead(n)

    return mxNoteList



def mxToNote(mxNote, spannerBundle=None, inputM21=None):
    '''Translate a MusicXML :class:`~music21.musicxml.Note` to a :class:`~music21.note.Note`.

    The `spanners` parameter can be a list or a Stream for storing and processing Spanner objects. 
    '''
    from music21 import articulations
    from music21 import expressions
    from music21 import note
    from music21 import tie
    from music21 import spanner

    if inputM21 == None:
        n = note.Note()
    else:
        n = inputM21
 
    # doing this will create an instance, but will not be passed
    # out of this method, and thus is only for testing
    if spannerBundle == None:
        #environLocal.printDebug(['mxToNote()', 'creating SpannerBundle'])
        spannerBundle = spanner.SpannerBundle()

    # print object == 'no' and grace notes may have a type but not
    # a duration. they may be filtered out at the level of Stream 
    # processing
    if mxNote.get('printObject') == 'no':
        n.hideObjectOnPrint = True
        environLocal.printDebug(['got mxNote with printObject == no'])

    mxGrace = mxNote.get('graceObj')
    if mxGrace != None: # graces have a type but not a duration
        environLocal.printDebug(['got mxNote with an mxGrace', 'duration', mxNote.get('duration')])

    n.pitch.mx = mxNote # required info will be taken from entire note
    n.duration.mx = mxNote
    n.beams.mx = mxNote.beamList

    # can use mxNote.tieList instead
    mxTieList = mxNote.get('tieList')
    if len(mxTieList) > 0:
        tieObj = tie.Tie() # m21 tie object
        tieObj.mx = mxNote # provide entire Note
        # n.tie is defined in GeneralNote as None by default
        n.tie = tieObj

    # things found in notations object:
    # articulations
    # slurs
    mxNotations = mxNote.get('notationsObj')
    if mxNotations != None:
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

            #environLocal.printDebug(['_setMX(), n.mxFermataList', mxFermataList])

        # get slurs; requires a spanner bundle
        mxSlurList = mxNotations.getSlurs()
        for mxObj in mxSlurList:
            # look at all spanners and see if we have an open, matching
            # slur to place this in
            idFound = mxObj.get('number')
            # returns a new spanner bundle with just the result of the search
            #environLocal.printDebug(['spanner bundle: getByCompleteStatus(False)', spannerBundle.getByCompleteStatus(False)])

            #sb = spannerBundle.getByIdLocal(idFound).getByCompleteStatus(False)
            sb = spannerBundle.getByClassIdLocalComplete('Slur', idFound, False)
            if len(sb) > 0:
                #environLocal.printDebug(['found a match in SpannerBundle'])
                su = sb[0] # get the first
            else:    
                # create a new slur
                su = spanner.Slur()
                su.idLocal = idFound
                su.placement = mxObj.get('placement')
                # type attribute, defined as start or stop, 
                spannerBundle.append(su)

            # add a reference of this note to this spanner
            su.addComponents(n)
            if mxObj.get('type') == 'stop':
                su.completeStatus = True
                # only add after complete
                

            #environLocal.printDebug(['got slur:', su, mxObj.get('placement'), mxObj.get('number')])


    return n


def restToMxNotes(r):
    '''Translate a :class:`~music21.note.Rest` to a MusicXML :class:`~music21.musicxml.Note` object configured with a :class:`~music21.musicxml.Rest`.
    '''
    mxNoteList = []
    for mxNote in r.duration.mx: # returns a list of mxNote objs
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
        r.duration.mx = mxNote
    except duration.DurationException:
        environLocal.printDebug(['failed extaction of duration from musicxml', 'mxNote:', mxNote, r])
        raise
    return r



#-------------------------------------------------------------------------------
# Measures


def measureToMx(m, spannerBundle=None):
    '''Translate a :class:`~music21.stream.Measure` to a MusicXML :class:`~music21.musicxml.Measure` object.
    '''
    #environLocal.printDebug(['measureToMx(): got spannerBundle:', spannerBundle])
    if spannerBundle is not None:
        # get all spanners that have this measure as a component    
        rbSpanners = spannerBundle.getByComponentAndClass(
                          m, 'RepeatBracket')
        #environLocal.printDebug(['measureToMx', 'm', m, 'len(rbSpanners)',
        #                     len(rbSpanners)])
    else:
        rbSpanners = [] # for size comparison

    mxMeasure = musicxmlMod.Measure()
    mxMeasure.set('number', m.number)

    if m.layoutWidth != None:
        mxMeasure.set('width', m.layoutWidth)

    # print objects come before attributes
    # note: this class match is a problem in cases where the object is created in the module itself, as in a test. 
    found = m.getElementsByClass('SystemLayout')
    if len(found) > 0:
        sl = found[0] # assume only one
        mxPrint = sl.mx
        mxMeasure.componentList.append(mxPrint)

    # get an empty mxAttributes object
    mxAttributes = musicxmlMod.Attributes()
    # best to only set dvisions here, as clef, time sig, meter are not
    # required for each measure
    mxAttributes.setDefaultDivisions()

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
    
    if m.hasVoices():
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
                elif 'GeneralNote' in classes:
                    # increment offset before getting mx, as this way a single
                    # chord provides only one value
                    offsetMeasureNote += obj.quarterLength
                    # .mx here returns a list of notes
                    objList = obj.mx
                    # need to set voice for each contained mx object
                    for sub in objList:
                        sub.voice = voiceId # the voice id is the voice number
                    mxMeasure.componentList += objList
            # create backup object configured to duration of accumulated
            # notes, meaning that we always return to the start of the measure
            mxBackup = musicxmlMod.Backup()
            mxBackup.duration = int(divisions * offsetMeasureNote)
            mxMeasure.componentList.append(mxBackup)

    else: # no voices
        mFlat = m.flat
        for obj in mFlat:
            classes = obj.classes # store result of property call once
            if 'Note' in classes:
                mxMeasure.componentList += noteToMxNotes(obj, 
                    spannerBundle=spannerBundle)
            elif 'GeneralNote' in classes:
                # .mx here returns a list of notes
                mxMeasure.componentList += obj.mx
            elif 'Dynamic' in classes:
                # returns an mxDirection object
                mxOffset = int(defaults.divisionsPerQuarter * 
                           obj.getOffsetBySite(mFlat))
                mxDirection = dynamicToMx(obj)
                mxDirection.offset = mxOffset 
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
                # get a lost of objects: may be a text expression + metro
                mxList = tempoIndicationToMx(obj)
                for mxDirection in mxList: # a list of mxdirections
                    mxDirection.offset = mxOffset 
                    # use offset positioning, can insert at zero
                    mxMeasure.insert(0, mxDirection)
                    #mxMeasure.componentList.append(mxObj)

            elif 'TextExpression' in classes:
                # convert m21 offset to mxl divisions
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
    '''Translate an mxMeasure (a MusicXML :class:`~music21.musicxml.Measure` object) into a music21 :class:`~music21.stream.Measure`.

    If an `inputM21` object reference is provided, this object will be configured and returned; otherwise, a new :class:`~music21.stream.Measure` object is created.  

    The `spannerBundle` that is passed in is used to accumulate any created Spanners. This Spanners are not inserted into the Stream here. 
    '''
    from music21 import stream
    from music21 import chord
    from music21 import dynamics
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
    if mxAttributesInternal is True and len(mxAttributes.clefList) != 0:
        for mxSub in mxAttributes.clefList:
            cl = clef.Clef()
            cl.mx = mxSub
            _addToStaffReference(mxSub, cl, staffReference)
            m._insertCore(0, cl)
            #m.clef = clef.Clef()
            #m.clef.mx = mxSub
    if mxAttributesInternal is True and len(mxAttributes.keyList) != 0:
        for mxSub in mxAttributes.keyList:
            ks = key.KeySignature()
            ks.mx = mxSub
            _addToStaffReference(mxSub, ks, staffReference)
            m._insertCore(0, ks)
            #m.keySignature = key.KeySignature()
            #m.keySignature.mx = mxSub

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
    for i in range(len(mxMeasure)):

        # try to get the next object for chord comparisons
        mxObj = mxMeasure[i]
        if i < len(mxMeasure)-1:
            mxObjNext = mxMeasure[i+1]
        else:
            mxObjNext = None

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
            # mxPrint objects may be found in a Measure's componetns
            # contain system layout information
            mxPrint = mxObj
            sl = layout.SystemLayout()
            sl.mx = mxPrint
            # store at zero position
            m._insertCore(0, sl)

        # <sound> tags may be found in the Measure, used to define tempo
        elif isinstance(mxObj, musicxmlMod.Sound):
            #environLocal.printDebug(['found musicxmlMod.Sound object in mxMeasure'])
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

            mxGrace = mxNote.get('graceObj')
            if mxGrace is not None: # graces have a type but not a duration
                #TODO: add grace notes with duration equal to ZeroDuration
                #environLocal.printDebug(['got mxNote with an mxGrace', 'duration', mxNote.get('duration'), 'measure number', 
                #m.number])
                continue

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
                    #n = note.Note()
                    #n.mx = mxNote
                    n = mxToNote(mxNote, spannerBundle=spannerBundle)
                    _addToStaffReference(mxNote, n, staffReference)
                    if useVoices:
                        m.voices[mxNote.voice]._insertCore(offsetMeasureNote, n)
                    else:
                        m._insertCore(offsetMeasureNote, n)
                    offsetIncrement = n.quarterLength

                    for mxLyric in mxNote.lyricList:
                        lyricObj = note.Lyric()
                        lyricObj.mx = mxLyric
                        n.lyrics.append(lyricObj)

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

            # if we we have notes in the note list and the next
            # note either does not exist or is not a chord, we 
            # have a complete chord
            if len(mxNoteList) > 0 and (mxNoteNext is None 
                or mxNoteNext.get('chord') is False):
                c = chord.Chord()
                # TODO: use chord conversion
                c.mx = mxNoteList
                # add any accumulated lyrics
                for mxLyric in mxLyricList:
                    lyricObj = note.Lyric()
                    lyricObj.mx = mxLyric
                    c.lyrics.append(lyricObj)

                _addToStaffReference(mxNoteList, c, staffReference)
                if useVoices:
                    m.voices[mxNote.voice]._insertCore(offsetMeasureNote, c)
                else:
                    m._insertCore(offsetMeasureNote, c)
                mxNoteList = [] # clear for next chord
                mxLyricList = []

                offsetIncrement = c.quarterLength
            # only increment Chords after completion
            offsetMeasureNote += offsetIncrement

        # load dynamics into Measure, not into Voice
        # mxDirections can be dynamics, repeat expressions, text expressions
        elif isinstance(mxObj, musicxmlMod.Direction):
#                 mxDynamicsFound, mxWedgeFound = m._getMxDynamics(mxObj)
#                 for mxDirection in mxDynamicsFound:
            # will return 0 if not defined
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
            if mxObj.getWedge() is not None:
                w = dynamics.Wedge()
                w.mx = mxObj     
                _addToStaffReference(mxObj, w, staffReference)
                m._insertCore(offsetMeasureNote, w)

            if mxObj.getSegno() is not None:
                rm = mxToSegno(mxObj.getSegno())
                _addToStaffReference(mxObj, rm, staffReference)
                m._insertCore(offsetMeasureNote, rm)
            if mxObj.getCoda() is not None:
                rm = mxToCoda(mxObj.getCoda())
                _addToStaffReference(mxObj, rm, staffReference)
                m._insertCore(offsetMeasureNote, rm)

            if mxObj.getMetronome() is not None:
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

    #environLocal.printDebug(['staffReference', staffReference])
    # if we have voices and/or if we used backup/forward, we may have
    # empty space in the stream
    if useVoices:
        for v in m.voices:
            if len(v) > 0: # do not bother with empty voices
                v.makeRests(inPlace=True)
            v._elementsChanged()
    m._elementsChanged()

    return m, staffReference

def measureToMusicXML(m):
    '''Translate a music21 Measure into a complete MusicXML string representation.

    Note: this method is called for complete MusicXML representation of a Measure, not for partial solutions in Part or Stream production. 

    >>> from music21 import *
    >>> m = stream.Measure()
    >>> m.repeatAppend(note.Note('g3'), 4)
    >>> post = musicxml.translate.measureToMusicXML(m)
    >>> post[-100:].replace('\\n', '')
    ' <type>quarter</type>        <notations/>      </note>    </measure>  </part></score-partwise>'
    '''
    from music21 import stream, duration
    # search for time signatures, either defined locally or in context

    #environLocal.printDebug(['measureToMusicXML', m]) 

    # we already have a deep copy passed in, which happens in 
    # stream.Measure._getMusicXML()
    m.makeNotation(inPlace=True)

# this is now in Measure.makeNotation
#     found = m.getTimeSignatures(returnDefault=False)
#     if len(found) == 0:
#         try:
#             ts = m.bestTimeSignature()
#         # may raise an exception if cannot find a rational match
#         except stream.StreamException:
#             ts = None # get the default
#     else:
#         ts = found[0]

    # might similarly look for key signature, instrument, and clef
    # must copy here b/c do not want to alter original, and need to set
    # new objects in some cases (time signature, etc)
#     mCopy = copy.deepcopy(m)    
#     if ts != None:
#         mCopy.timeSignature = ts

    out = stream.Part()
    out.append(m)
    # call the musicxml property on Stream
    return out.musicxml




#-------------------------------------------------------------------------------
# Streams


def streamPartToMx(part, instObj=None, meterStream=None,
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

    #environLocal.printDebug(['calling Stream._getMXPart'])
    # note: meterStream may have TimeSignature objects from an unrelated
    # Stream.
    if instObj is None:
        # see if an instrument is defined in this or a parent stream
        instObj = part.getInstrument()
    # must set a unique part id, if not already assigned
    if instObj.partId == None:
        instObj.partIdRandomize()

    #environLocal.printDebug(['calling Stream._getMXPart', repr(instObj), instObj.partId])

    # instrument object returns a configured mxScorePart, that may
    # also include midi or score instrument definitions
    mxScorePart = instObj.mx

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
        measureStream = part.makeNotation(meterStream=meterStream,
                        refStreamOrTimeRange=refStreamOrTimeRange)
        #environLocal.printDebug(['Stream._getMXPart: post makeNotation, length', len(measureStream)])

        # after calling measuresStream, need to update Spanners, as a deepcopy
        # has been made
        # might need to getAll b/c might need spanners 
        # from a higher level container
        #spannerBundle = spanner.SpannerBundle(
        #                measureStream.flat.getAllContextsByClass('Spanner'))
        # only getting spanners at this level
        #spannerBundle = spanner.SpannerBundle(measureStream.flat)
        spannerBundle = measureStream.spannerBundle
    # if this is a Measure, see if it needs makeNotation
    else: # there are measures
        # check that first measure has any atributes in outer Stream
        # this is for non-standard Stream formations (some kern imports)
        # that place key/clef information in the containing stream
        if measureStream[0].clef == None:
            measureStream[0].makeMutable() # must mutate
            outerClefs = part.getElementsByClass('Clef')
            if len(outerClefs) > 0:
                measureStream[0].clef = outerClefs[0]
        if measureStream[0].keySignature == None:
            measureStream[0].makeMutable() # must mutate
            outerKeySignatures = part.getElementsByClass('KeySignature')
            if len(outerKeySignatures) > 0:
                measureStream[0].keySignature = outerKeySignatures[0]

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


    # for each measure, call .mx to get the musicxml representation
    for obj in measureStream:
        #mxPart.append(obj.mx)
        mxPart.append(measureToMx(obj, spannerBundle=spannerBundle))

    # mxScorePart contains mxInstrument
    return mxScorePart, mxPart


def streamToMx(s, spannerBundle=None):
    '''
    Create and return a musicxml Score object. 


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
        r = note.Rest()
        r.duration.type = 'whole'
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

    # we need independent sub-stream elements to shift in presentation
    highestTime = 0

    if s.hasPartLikeStreams():
        #environLocal.printDebug('Stream._getMX: interpreting multipart')
        # NOTE: a deepcopy has already been made; do not copy again
        #partStream = copy.deepcopy(s)
        #partStream = s

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
            inst = obj.getInstrument(returnDefault=True)
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
            mxComponents.append(streamPartToMx(obj, instObj=inst, 
                meterStream=meterStream, 
                refStreamOrTimeRange=refStreamOrTimeRange, 
                spannerBundle=spannerBundle))
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

        mxComponents.append(streamPartToMx(s,
                meterStream=meterStream, 
                spannerBundle=spannerBundle))

    # create score and part list
    # try to get mxScore from lead meta data first
    if s.metadata != None:
        mxScore = s.metadata.mx # returns an mx score
    else:
        mxScore = musicxmlMod.Score()

    mxScoreDefault = musicxmlMod.Score()
    mxScoreDefault.setDefaults()
    mxIdDefault = musicxmlMod.Identification()
    mxIdDefault.setDefaults() # will create a composer
    mxScoreDefault.set('identification', mxIdDefault)

    # merge metadata derived with default created
    mxScore = mxScore.merge(mxScoreDefault, returnDeepcopy=False)

    mxPartList = musicxmlMod.PartList()
    mxScore.set('partList', mxPartList)

    for mxScorePart, mxPart in mxComponents:
        mxPartList.append(mxScorePart)
        mxScore.append(mxPart)

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
    mxInstrument = mxScore.getInstrument(partId)

    # create a new music21 instrument
    instrumentObj = instrument.Instrument()
    if mxInstrument is not None:
        instrumentObj.mx = mxInstrument

    # add part id as group
    instrumentObj.groups.append(partId)

    streamPart = stream.Part() # create a part instance for each part
    # set part id to stream best name
    if instrumentObj.bestName() is not None:
        streamPart.id = instrumentObj.bestName()
    streamPart._insertCore(0, instrumentObj) # add instrument at zero offset

    staffReferenceList = []
    # offset is in quarter note length
    oMeasure = 0.0
    lastTimeSignature = None
    for mxMeasure in mxPart:
        m, staffReference = mxToMeasure(mxMeasure, spannerBundle=spannerBundle)
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

        if m.highestTime >= lastTimeSignature.barDuration.quarterLength:
            mOffsetShift = m.highestTime
        else: # use time signature
            # for the first measure, this may be a pickup
            # must detect this when writing, as next measures offsets will be 
            # incorrect
            if oMeasure == 0.0:
                # cannot get bar duration proportion if cannot get a ts
                if m.barDurationProportion() < 1.0:
                    m.padAsAnacrusis()
                    #environLocal.printDebug(['incompletely filled Measure found on musicxml import; interpreting as a anacrusis:', 'padingLeft:', m.paddingLeft])
                mOffsetShift = m.highestTime
            # assume that, even if measure is incomplete, the next bar should
            # start at the duration given by the time signature, not highestTime
            else:
                mOffsetShift = lastTimeSignature.barDuration.quarterLength 
        oMeasure += mOffsetShift

    # if we have multiple staves defined, add more parts, and transfer elements
    # note: this presently has to look at _idLastDeepCopyOf to get matches
    # to find removed elements after copying; this is probably not the
    # best way to do this. 
    if mxPart.getStavesCount() > 1:
        # get staves will return a number, between 1 and count
        #for staffCount in range(mxPart.getStavesCount()):
        for staffCount in _getUniqueStaffKeys(staffReferenceList):
            partIdStaff = '%s-Staff%s' % (partId, staffCount)
            #environLocal.printDebug(['partIdStaff', partIdStaff])
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
                # after adjusting voices see of voices can be reduced or
                # removed
                #environLocal.printDebug(['calling flattenUnnecessaryVoices: voices before:', len(m.voices)])
                m.flattenUnnecessaryVoices(force=False, inPlace=True)
                #environLocal.printDebug(['calling flattenUnnecessaryVoices: voices after:', len(m.voices)])

            streamPartStaff.addGroupForElements(partIdStaff) 
            streamPartStaff.groups.append(partIdStaff) 
            s._insertCore(0, streamPartStaff)
    else:
        streamPart.addGroupForElements(partId) # set group for components 
        streamPart.groups.append(partId) # set group for stream itself

        # TODO: this does not work with voices; there, Spanners 
        # will be copied into the Score 

        # copy spanners that are complete into the part, as this is the 
        # highest level container that needs them
        # note that this may cause problems when creating staff copies, 
        # as is down below
        rm = []
        for sp in spannerBundle.getByCompleteStatus(True):
            streamPart._insertCore(0, sp)
            rm.append(sp)
        # remove from original spanner bundle
        for sp in rm:
            spannerBundle.remove(sp)
    
        s._insertCore(0, streamPart)

    s._elementsChanged()
    # when adding parts to this Score
    # this assumes all start at the same place
    # even if there is only one part, it will be placed in a Stream


def mxToStream(mxScore, spannerBundle=None, inputM21=None):
    '''Translate an mxScore into a music21 Score object.

    All spannerBundles accumulated at all lower levels are inserted here.
    '''
    # TODO: may not want to wait to this leve to insert spanners; may want to 
    # insert in lower positions if it makes sense

    from music21 import metadata
    from music21 import spanner

    if inputM21 == None:
        from music21 import stream
        s = stream.Score()
    else:
        s = inputM21

    if spannerBundle == None:
        spannerBundle = spanner.SpannerBundle()

    partNames = mxScore.getPartNames().keys()
    partNames.sort()
    for partName in partNames: # part names are part ids
        mxToStreamPart(mxScore, partId=partName, 
            spannerBundle=spannerBundle, inputM21=s)
        #s._setMXPart(mxScore, partName)

    # add metadata object; this is placed after all other parts now
    # these means that both Parts and other objects live on Stream.
    md = metadata.Metadata()
    md.mx = mxScore
    s._insertCore(0, md)

    # only insert complete spanners; at each level possible, complete spanners
    # are inserted into either the Score or the Part
    # storing complet Part spanners in a Part permits extracting parts with spanners
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


        environLocal.printDebug(['pre s.measures(2,3)', 's', s])
        ex = s.measures(2, 3) # this needs to get all spanners too

        # all spanners are referenced over; even ones that may not be relevant
        self.assertEqual(len(ex.flat.spanners), 2)
        #ex.show()
        
        # slurs are on measures 2, 3
        # crescendos are on measures 4, 5


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

        # has only sound tempo=x tag
        s = converter.parse(testPrimitive.articulations01)
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



    def testImportGraceNotesA(self):
        # test importing from muscixml
        from music21.musicxml import testPrimitive
        from music21 import converter, repeat
        s = converter.parse(testPrimitive.graceNotes24a)

        #s.show()
        
    def testNoteheadConversion(self):
        # test to ensure notehead functionality
        
        from music21 import note
        n = note.Note('c3')
        n.notehead = 'diamond'
        
        out = n.musicxml
        match1 = '<notehead>diamond</notehead>'
        self.assertEqual(out.find(match1) > 0, True)
        

if __name__ == "__main__":
    # sys.arg test options will be used in mainTest()
    music21.mainTest(Test)




#------------------------------------------------------------------------------
# eof
