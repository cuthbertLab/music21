#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         musicxml.translate.py
# Purpose:      Translate MusicXML and music21 objects
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2010 The music21 Project
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
from music21 import node

# modules that import this include stream.py, chord.py, note.py
# thus, cannot import these here

from music21 import environment
_MOD = "musicxml.translate.py"  
environLocal = environment.Environment(_MOD)





#-------------------------------------------------------------------------------
class TranslateException(Exception):
    pass



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
    '''Translate a music21 :class:`~music21.tie.Tie` object to MusicXML :class:`~music21.musicxml.Tie` and :class:`~music21.musicxml.Tied` objects as two component lists.

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
    mxTied = musicxmlMod.Tied()
    mxTied.set('type', musicxmlTieType) # start, stop
    mxTiedList.append(mxTied) # goes on mxNote.notationsObj list
    if t.type == 'continue':
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
        raise DurationException(
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
            except DurationException:
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
    '''Translate a music21 :class:`~music21.duration.Duration` object to a list of one or more MusicXML :class:`~music21.musicxml.Note` objects. 

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
    '''
    from music21 import duration

    post = [] # rename mxNoteList for consistencuy
    #environLocal.printDebug(['in _getMX', d, d.quarterLength])

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

    # todo: this is not yet implemented in music21 note objects; to do
    #mxNotehead = musicxmlMod.Notehead()
    #mxNotehead.set('charData', defaults.noteheadUnpitched)

    # make a copy, as we this process will change tuple types
    dCopy = copy.deepcopy(d)
    # this update is done in note output
    #updateTupletType(dCopy.components) # modifies in place

    n = note.Note()
    n.duration = dCopy
    # call the musicxml property on Stream
    return generalNoteToMusicXML(n)



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

def dyanmicToMx(d):
    'Return an mx direction'
    '''
    returns a musicxml.Direction object

    >>> from music21 import *
    >>> a = dynamics.Dynamic('pp# p')
    >>> a.posRelativeY = -10
    >>> b = a.mx
    >>> b[0][0][0].get('tag')
    'ppp'
    >>> b.get('placement')
    'below'
    '''
    mxDynamicMark = musicxmlMod.DynamicMark(d.value)
    mxDynamics = musicxmlMod.Dynamics()
    for src, dst in [(d.posDefaultX, 'default-x'), 
                     (d.posDefaultY, 'default-y'), 
                     (d.posRelativeX, 'relative-x'),
                     (d.posRelativeY, 'relative-y')]:
        if src is not None:
            mxDynamics.set(dst, src)
    mxDynamics.append(mxDynamicMark) # store on component list
    mxDirectionType = musicxmlMod.DirectionType()
    mxDirectionType.append(mxDynamics)
    mxDirection = musicxmlMod.Direction()
    mxDirection.append(mxDirectionType)
    mxDirection.set('placement', d.posPlacement)
    return mxDirection


def mxToDynamic(mxDirection, inputM21=None):
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
    >>> a.posDefaultY
    -20
    >>> a.posPlacement
    'below'
    '''

    from music21 import dynamics
    if inputM21 is None:
        d = dynamics.Dynamic()
    else:
        d = inputM21

    mxDynamics = None
    for mxObj in mxDirection:
        if isinstance(mxObj, musicxmlMod.DirectionType):
            for mxObjSub in mxObj:
                if isinstance(mxObjSub, musicxmlMod.Dynamics):
                    mxDynamics = mxObjSub
    if mxDynamics == None:
        raise dynamics.DynamicException('when importing a Dyanmics object from MusicXML, did not find a DyanmicMark')            
    if len(mxDynamics) > 1:
        raise dynamics.DynamicException('when importing a Dyanmics object from MusicXML, found more than one DyanmicMark contained')

    # palcement is found in outermost object
    if mxDirection.get('placement') is not None:
        d.posPlacement = mxDirection.get('placement') 

    # the tag is the dynmic mark value
    mxDynamicMark = mxDynamics.componentList[0].get('tag')
    d.value = mxDynamicMark
    for dst, src in [('posDefaultX', 'default-x'), 
                     ('posDefaultY', 'default-y'), 
                     ('posRelativeX', 'relative-x'),
                     ('posRelativeY', 'relative-y')]:
        if mxDynamics.get(src) is not None:
            setattr(d, dst, mxDynamics.get(src))





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
            mxNote = copy.deepcopy(mxNoteBase)

            #mxNote.pitch = None # clear before each iteration
            mxNote = mxNote.merge(pitchObj.mx)
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
    mxArticulations = None
    for i in range(len(c.articulations)):
        obj = c.articulations[i]
        if hasattr(obj, 'mx'):
            if i == 0: # assign first
                mxArticulations = obj.mx # mxArt... stores more than one artic
            else: # concatenate any remaining
                mxArticulations += obj.mx
    if mxArticulations != None:
        mxNoteList[0].notationsObj.componentList.append(mxArticulations)

    # notations and articulations are mixed in musicxml
    for i in range(len(c.expressions)):
        obj = c.expressions[i]
        if hasattr(obj, 'mx'): 
            mxNoteList[0].notationsObj.componentList.append(obj.mx)

    return mxNoteList

def mxToChord(mxNoteList, inputM21=None):
    '''Given an a list of mxNotes, fill the necessary parameters

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
        p.mx = mxNote # will extract pitch info form mxNote
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
    nCopy = copy.deepcopy(n)
    duration.updateTupletType(nCopy.duration) # modifies in place

    out = stream.Stream()
    out.append(nCopy)
    # call the musicxml property on Stream
    return out.musicxml
    


def noteToMxNotes(n, spannerBundle=None):
    '''Translate a music21 :class:`~music21.note.Note` into a list of :class:`~music21.musicxml.Note` objects.
    '''
    #Attributes of notes are merged from different locations: first from the 
    #duration objects, then from the pitch objects. Finally, GeneralNote 
    #attributes are added.

    if spannerBundle is not None:
        # this will get all spanners that participate with this note
        if len(spannerBundle) > 0:
            pass
            #environLocal.printDebug(['noteToMxNotes(): spannerBundle pre-filter:', spannerBundle, 'spannerBundle[0]', spannerBundle[0], 'id(spannerBundle[0])', id(spannerBundle[0]), 'spannerBundle[0].getComponentIds()', spannerBundle[0].getComponentIds(), 'id(n)', id(n)])

        spannerBundle = spannerBundle.getByComponent(n)

        #environLocal.printDebug(['noteToMxNotes(): spannerBundle post-filter by component:', spannerBundle])

    mxNoteList = []
    for mxNote in n.duration.mx: # returns a list of mxNote objs
        # merge method returns a new object
        mxNote = mxNote.merge(n.pitch.mx)
        # get color from within .editorial using attribute
        mxNote.set('color', n.color)
        mxNoteList.append(mxNote)

    # note: lyric only applied to first note
    for lyricObj in n.lyrics:
        mxNoteList[0].lyricList.append(lyricObj.mx)

    # if this note, not a component duration, but this note has a tie, 
    # need to add this to the last-encountered mxNote
    if n.tie is not None:
        mxTieList, mxTiedList = n.tie.mx # get mxl objs from tie obj
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
    for mxNote in mxNoteList:
        if n.beams != None:
            mxNote.beamList = n.beams.mx

    # if we have any articulations, they only go on the first of any 
    # component notes
    mxArticulations = musicxmlMod.Articulations()
    for i in range(len(n.articulations)):
        obj = n.articulations[i] # returns mxArticulationMark
        mxArticulations.append(obj.mx) # append to mxArticulations
    if len(mxArticulations) > 0:
        mxNoteList[0].notationsObj.componentList.append(mxArticulations)

    # notations and articulations are mixed in musicxml
    for i in range(len(n.expressions)):
        obj = n.expressions[i]
        if hasattr(obj, 'mx'):
            mxNoteList[0].notationsObj.componentList.append(obj.mx)

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

            sb = spannerBundle.getByIdLocal(idFound).getByCompleteStatus(False)
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
    if m.leftBarline != None:
        mxBarline = m.leftBarline.mx # this may be a repeat object
        # setting location outside of object based on that this attribute
        # is the leftBarline
        mxBarline.set('location', 'left')
        mxMeasure.componentList.append(mxBarline)
    
    # need to handle objects in order when creating musicxml 
    # we thus assume that objects are sorted here

    if m.hasVoices():
        # store divisions for use in calculating backup of voices 
        divisions = mxAttributes.divisions
        for v in m.voices:
            # iterate over each object in this voice
            offsetMeasureNote = 0 # offset of notes w/n measure  
            for obj in v.flat:
                classes = obj.classes # store result of property call once
                if 'Note' in classes:
                    offsetMeasureNote += obj.quarterLength
                    objList = noteToMxNotes(obj, spannerBundle=spannerBundle)
                    for sub in objList:
                        sub.voice = v.id # the voice id is the voice number
                    mxMeasure.componentList += objList
                elif 'GeneralNote' in classes:
                    # increment offset before getting mx, as this way a single
                    # chord provides only one value
                    offsetMeasureNote += obj.quarterLength
                    # .mx here returns a list of notes
                    objList = obj.mx
                    # need to set voice for each contained mx object
                    for sub in objList:
                        sub.voice = v.id # the voice id is the voice number
                    mxMeasure.componentList += objList
            # create backup object configured to duration of accumulated
            # notes, meaning that we always return to the start of the measure
            mxBackup = musicxmlMod.Backup()
            mxBackup.duration = int(divisions * offsetMeasureNote)
            mxMeasure.componentList.append(mxBackup)

    else: # no voices
        for obj in m.flat:
            classes = obj.classes # store result of property call once
            if 'Note' in classes:
                mxMeasure.componentList += noteToMxNotes(obj, 
                    spannerBundle=spannerBundle)
            elif 'GeneralNote' in classes:
                # .mx here returns a list of notes
                mxMeasure.componentList += obj.mx
            elif 'Dynamic' in classes:
                # returns an mxDirection object
                mxMeasure.append(obj.mx)
            else: # other objects may have already been added
                pass
                #environLocal.printDebug(['_getMX of Measure is not processing', obj])

    # right barline must follow all notes
    if m.rightBarline != None:
        mxBarline = m.rightBarline.mx # this may be a repeat
        # setting location outside of object based on that this attribute
        # is the leftBarline
        mxBarline.set('location', 'right')
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
        except node.NodeException:
            return 
    if key not in staffReference.keys():
        staffReference[key] = []
    staffReference[key].append(target)


def mxToMeasure(mxMeasure, spannerBundle=None, inputM21=None):
    '''Translate an mxMeasure (a MusicXML :class:`~music21.musicxml.Measure` object) into a music21 :class:`~music21.stream.Measure`.

    If an `inputM21` object reference is provided, this object will be configured and returned; otherwise, a new :class:`~music21.stream.Measure` object is created.  
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
    if spannerBundle == None:
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
            m.insert(0, ts)
            #m.timeSignature = meter.TimeSignature()
            #m.timeSignature.mx = mxSub
    if mxAttributesInternal is True and len(mxAttributes.clefList) != 0:
        for mxSub in mxAttributes.clefList:
            cl = clef.Clef()
            cl.mx = mxSub
            _addToStaffReference(mxSub, cl, staffReference)
            m.insert(0, cl)
            #m.clef = clef.Clef()
            #m.clef.mx = mxSub
    if mxAttributesInternal is True and len(mxAttributes.keyList) != 0:
        for mxSub in mxAttributes.keyList:
            ks = key.KeySignature()
            ks.mx = mxSub
            _addToStaffReference(mxSub, ks, staffReference)
            m.insert(0, ks)
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
            m.insert(0, v)
    else:
        useVoices = False

    # iterate through components found on components list
    # set to zero for each measure
    offsetMeasureNote = 0 # offset of note w/n measure        
    mxNoteList = [] # for accumulating notes in chords
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
            m.insert(0, sl)

        elif isinstance(mxObj, musicxmlMod.Barline):
            # repeat is a tag found in the barline object
            mxBarline = mxObj
            mxRepeatObj = mxBarline.get('repeatObj')

            if mxRepeatObj != None:
                barline = bar.Repeat()
            else:
                barline = bar.Barline()

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
                else:
                    #n = note.Note()
                    #n.mx = mxNote
                    n = mxToNote(mxNote, spannerBundle=spannerBundle)
                    _addToStaffReference(mxNote, n, staffReference)
                    if useVoices:
                        m.voices[mxNote.voice].insert(offsetMeasureNote, n)
                    else:
                        m.insert(offsetMeasureNote, n)
                    offsetIncrement = n.quarterLength

                for mxLyric in mxNote.lyricList:
                    lyricObj = note.Lyric()
                    lyricObj.mx = mxLyric
                    n.lyrics.append(lyricObj)
                if mxNote.get('notationsObj') is not None:
                    for mxObjSub in mxNote.get('notationsObj'):
                        # deal with ornaments, strill, etc
                        pass
            else: # its a rest
                n = note.Rest()
                n.mx = mxNote # assign mxNote to rest obj
                _addToStaffReference(mxNote, n, staffReference)
                #m.insert(offsetMeasureNote, n)
                if useVoices:
                    m.voices[mxNote.voice].insert(offsetMeasureNote, n)
                else:
                    m.insert(offsetMeasureNote, n)
                offsetIncrement = n.quarterLength

            # if we we have notes in the note list and the next
            # note either does not exist or is not a chord, we 
            # have a complete chord
            if len(mxNoteList) > 0 and (mxNoteNext is None 
                or mxNoteNext.get('chord') is False):
                c = chord.Chord()
                # TODO: use chord conversion
                c.mx = mxNoteList
                _addToStaffReference(mxNoteList, c, staffReference)
                if useVoices:
                    m.voices[mxNote.voice].insert(offsetMeasureNote, c)
                else:
                    m.insert(offsetMeasureNote, c)
                mxNoteList = [] # clear for next chord
                offsetIncrement = c.quarterLength
            # only increment Chords after completion
            offsetMeasureNote += offsetIncrement

        # load dynamics into Measure, not into Voice
        elif isinstance(mxObj, musicxmlMod.Direction):
#                 mxDynamicsFound, mxWedgeFound = m._getMxDynamics(mxObj)
#                 for mxDirection in mxDynamicsFound:
            if mxObj.getDynamicMark() is not None:
                d = dynamics.Dynamic()
                d.mx = mxObj
                _addToStaffReference(mxObj, d, staffReference)
                m.insert(offsetMeasureNote, d)  
            if mxObj.getWedge() is not None:
                w = dynamics.Wedge()
                w.mx = mxObj     
                _addToStaffReference(mxObj, w, staffReference)
                m.insert(offsetMeasureNote, w)
    #environLocal.printDebug(['staffReference', staffReference])

    # if we have voices and/or if we used backup/forward, we may have
    # empty space in the stream
    if useVoices:
        for v in m.voices:
            if len(v) > 0: # do not bother with empty voices
                v.makeRests(inPlace=True)
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
    found = m.getTimeSignatures(returnDefault=False)
    if len(found) == 0:
        try:
            ts = m.bestTimeSignature()
        # may raise an exception if cannot find a rational match
        except stream.StreamException:
            ts = None # get the default
    else:
        ts = found[0]
    # might similarly look for key signature, instrument, and clef
    # must copy here b/c do not want to alter original, and need to set
    # new objects in some cases (time signature, etc)
    mCopy = copy.deepcopy(m)    
    if ts != None:
        mCopy.timeSignature = ts

    out = stream.Stream()
    out.append(mCopy)
    # call the musicxml property on Stream
    return out.musicxml




#-------------------------------------------------------------------------------
# Streams


def streamPartToMx(s, instObj=None, meterStream=None,
                   refStreamOrTimeRange=None, spannerBundle=None):
    '''If there are Measures within this stream, use them to create and
    return an MX Part and ScorePart. 

    An `instObj` may be assigned from caller; this Instrument is pre-collected from this Stream in order to configure id and midi-channel values. 

    The `meterStream`, if provides a template of meters. 
    '''
    from music21 import spanner

    #environLocal.printDebug(['calling Stream._getMXPart'])
    # note: meterStream may have TimeSignature objects from an unrelated
    # Stream.
    if instObj is None:
        # see if an instrument is defined in this or a parent stream
        instObj = s.getInstrument()
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
    measureStream = s.getElementsByClass('Measure')
    if len(measureStream) == 0:
        # try to add measures if none defined
        # returns a new stream w/ new Measures but the same objects
        measureStream = s.makeNotation(meterStream=meterStream,
                        refStreamOrTimeRange=refStreamOrTimeRange)
        #environLocal.printDebug(['Stream._getMXPart: post makeNotation, length', len(measureStream)])

        # after calling measuresStream, need to update Spanners, as a deepcopy
        # has been made
        # might need to getAll b/c might need spanners 
        # from a higher level container
        #spannerBundle = spanner.SpannerBundle(
        #                measureStream.flat.getAllContextsByClass('Spanner'))
        # only getting spanners at this level
        spannerBundle = spanner.SpannerBundle(measureStream.flat)

    else: # there are measures
        # check that first measure has any atributes in outer Stream
        # this is for non-standard Stream formations (some kern imports)
        # that place key/clef information in the containing stream
        if measureStream[0].clef == None:
            outerClefs = s.getElementsByClass('Clef')
            if len(outerClefs) > 0:
                measureStream[0].clef = outerClefs[0]
        if measureStream[0].keySignature == None:
            outerKeySignatures = s.getElementsByClass('KeySignature')
            if len(outerKeySignatures) > 0:
                measureStream[0].keySignature = outerKeySignatures[0]

    # for each measure, call .mx to get the musicxml representation
    for obj in measureStream:
        #mxPart.append(obj.mx)
        mxPart.append(measureToMx(obj, spannerBundle=spannerBundle))

    # mxScorePart contains mxInstrument
    return mxScorePart, mxPart


def streamToMx(s, spannerBundle=None):
    '''Create and return a musicxml Score object. 

    >>> from music21 import *
    >>> n1 = note.Note()
    >>> measure1 = stream.Measure()
    >>> measure1.insert(n1)
    >>> s1 = stream.Stream()
    >>> s1.insert(measure1)
    >>> mxScore = musicxml.translate.streamToMx(s1)
    >>> mxPartList = mxScore.get('partList')
    '''
    environLocal.printDebug(['streamToMx:'])
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
    # this meter  stream is passed to makeMeasures()
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

        # making a deepcopy, as we are going to edit internal objs
        partStream = copy.deepcopy(s)

        # must set spanner after copying
        if spannerBundle is None: 
            # no spanner bundle provided, get one from the flat stream
            spannerBundle = spanner.SpannerBundle(partStream.flat)
            #environLocal.printDebug(['streamToMx(), hasPartLikeStreams(): loaded spannerBundle of size:', len(spannerBundle), 'id(spannerBundle)', id(spannerBundle)])

        for obj in partStream.getElementsByClass('Stream'):
            # may need to copy element here
            # apply this streams offset to elements
            obj.transferOffsetToElements() 
            ht = obj.highestTime
            if ht > highestTime:
                highestTime = ht

        refStreamOrTimeRange = [0, highestTime]

        # would like to do something like this but cannot
        # replace object inside of the stream
        for obj in partStream.getElementsByClass('Stream'):
            obj.makeRests(refStreamOrTimeRange, inPlace=True)

        #environLocal.printDebug(['Stream._getMX(): handling multi-part Stream of length:', len(partStream)])
        count = 0
        midiChannelList = []
        for obj in partStream.getElementsByClass('Stream'):
            count += 1
            if count > len(partStream):
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
            spannerBundle = spanner.SpannerBundle(s.flat)
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
    mxScore = mxScore.merge(mxScoreDefault)

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
    streamPart.insert(instrumentObj) # add instrument at zero offset

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
        streamPart.insert(oMeasure, m)

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

    # if we have multiple staves defined, add more parts
    # note: this presently has to look at _idLastDeepCopyOf to get matches
    # to find removed elements after copying; this is probably not the
    # best way to do this. 
    if mxPart.getStavesCount() > 1:
        # get staves will return a number, between 1 and count
        #for staffCount in range(mxPart.getStavesCount()):
        for staffCount in _getUniqueStaffKeys(staffReferenceList):
            partIdStaff = '%s-Staff%s' % (partId, staffCount)
            #environLocal.printDebug(['partIdStaff', partIdStaff])
            streamPartStaff = copy.deepcopy(streamPart)
            # assign this as a PartStaff, a subclass of Part
            streamPartStaff.__class__ = stream.PartStaff
            # remove all elements that are not part of this staff
            mStream = streamPartStaff.getElementsByClass('Measure')
            for i, staffReference in enumerate(staffReferenceList):
                staffExclude = _getStaffExclude(staffReference, staffCount)
                m = mStream[i]
                # may need to look for elements in voices as well
                for eRemove in staffExclude:
                    for eMeasure in m:
                        if eMeasure._idLastDeepCopyOf == id(eRemove):
                            m.remove(eMeasure)
                    for v in m.voices:
                        v.remove(eRemove)
                        for eVoice in v:
                            if eVoice._idLastDeepCopyOf == id(eRemove):
                                v.remove(eVoice)

            streamPartStaff.addGroupForElements(partIdStaff) 
            streamPartStaff.groups.append(partIdStaff) 
            s.insert(0, streamPartStaff)
    else:
        streamPart.addGroupForElements(partId) # set group for components 
        streamPart.groups.append(partId) # set group for stream itself
        s.insert(0, streamPart)

    # when adding parts to this Score
    # this assumes all start at the same place
    # even if there is only one part, it will be placed in a Stream


def mxToStream(mxScore, spannerBundle=None, inputM21=None):
    '''Translate an mxScore into a music21 Score object.
    '''

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
    s.insert(0, md)

    # for now, just adding spanners to top-most level
    for sp in spannerBundle:
        s.insert(0, sp)
    # add spanners to highest level object




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
        s = corpus.parseWork('k80/movement3')
        for p in s.parts:
            post = p.flat.getElementsByClass('Repeat')
            self.assertEqual(len(post), 6)

        #a = corpus.parseWork('opus41no1/movement3')
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
        self.assertEqual(len(s.flat.notes[0].getAllContextsByClass('Spanner')), 5)
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
        s = corpus.parseWork('schoenberg/opus19/movement2')        
        self.assertEqual(len(s.parts), 2)

        s = corpus.parseWork('schoenberg/opus19/movement6')        
        self.assertEqual(len(s.parts), 2)

        #s.show()


    def testSpannersA(self):

        from music21 import converter, stream
        from music21.musicxml import testPrimitive
        
        s = converter.parse(testPrimitive.spanners33a)
        # this number will change as more are being imported
        self.assertEqual(len(s.spanners), 2)

        self.assertEqual(len(s.spanners), 2)

        environLocal.printDebug(['pre s.measures(2,3)', 's', s])
        ex = s.measures(2, 3) # this needs to get all spanners too

        # all spanners are referenced over; even ones that may not be relevant
        self.assertEqual(len(ex.spanners), 2)
        #ex.show()
        
        # slurs are on measures 2, 3
        # crescendos are on measures 4, 5

if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        t = Test()
        #t.testVoices()
        #t.testSlurInputA()
        #t.testMultipleStavesPerPartA()
        #t.testMultipleStavesPerPartC()
        t.testSpannersA()




#------------------------------------------------------------------------------
# eof




