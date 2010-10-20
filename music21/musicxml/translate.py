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





import unittest
import copy

import music21
from music21 import musicxml as musicxmlMod
from music21 import defaults
from music21 import common

# modules that import this include stream.py, chord.py, note.py
# thus, cannot import these here

from music21 import environment
_MOD = "musicxml.translate.py"  
environLocal = environment.Environment(_MOD)





#-------------------------------------------------------------------------------
class TranslateException(Exception):
    pass




#-------------------------------------------------------------------------------
# Ties

def tieToMx(t):
    '''Convert an m21 Tie to lists of MusicXML Tie or Tied objects. Return two component lists. 
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
    '''Based on properties in an mxNote, configure or create an m21 Tie object
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

    mxLyric = musicxmlMod.Lyric()
    mxLyric.set('text', l.text)
    mxLyric.set('number', l.number)
    mxLyric.set('syllabic', l.syllabic)
    return mxLyric


def mxToLyric(mxLyric, inputM21=None):

    if inputM21 == None:
        from music21 import note
        l = note.Lyric()
    else:
        l = inputM21

    l.text = mxLyric.get('text')
    l.number = mxLyric.get('number')
    l.syllabic = mxLyric.get('syllabic')






#-------------------------------------------------------------------------------
# Notes

def generalNoteToMusicXML(n):

    from music21 import stream, duration

    # make a copy, as we this process will change tuple types
    nCopy = copy.deepcopy(n)
    duration.updateTupletType(nCopy.duration) # modifies in place

    out = stream.Stream()
    out.append(nCopy)
    # call the musicxml property on Stream
    return out.musicxml
    


def noteToMxNotes(n):

    '''Translate a music21 Note into a List of mxNotes
    Attributes of notes are merged from different locations: first from the 
    duration objects, then from the pitch objects. Finally, GeneralNote 
    attributes are added
    '''
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
    if n.tie != None:
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
    for i in range(len(n.notations)):
        obj = n.notations[i] 
        mxNoteList[0].notationsObj.componentList.append(obj.mx)

    return mxNoteList



def mxToNote(mxNote, inputM21):
    '''Translate an mxNote into a music21 Note.
    '''
    from music21 import articulations
    from music21 import expressions
    from music21 import note
    from music21 import tie

    if inputM21 == None:
        n = note.Measure()
    else:
        n = inputM21


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

    mxTieList = mxNote.get('tieList')
    if len(mxTieList) > 0:
        tieObj = tie.Tie() # m21 tie object
        tieObj.mx = mxNote # provide entire Note
        # n.tie is defined in GeneralNote as None by default
        n.tie = tieObj

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
            # placing this as an articulation for now
            n.notations.append(fermataObj)

            #environLocal.printDebug(['_setMX(), n.mxFermataList', mxFermataList])





def restToMxNotes(r):

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

    from music21 import duration

    if inputM21 == None:
        r = note.Rest()
    else:
        r = inputM21

    try:
        r.duration.mx = mxNote
    except duration.DurationException:
        environLocal.printDebug(['failed extaction of duration from musicxml', 'mxNote:', mxNote, r])
        raise





#-------------------------------------------------------------------------------
# Measures


def measureToMx(m):
    '''Given a measure, translate to musicxml objects
    '''

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
        mxAttributes.timeList = m.timeSignature.mx 

    #mxAttributes.keyList = []
    mxMeasure.set('attributes', mxAttributes)

    # see if we have barlines
    if m.leftBarline != None:
        mxBarline = m.leftBarline.mx # this may be a repeat object
        # setting location outside of object based on that this attribute
        # is the leftBarline
        mxBarline.set('location', 'left')
        mxMeasure.componentList.append(mxBarline)
    
    #need to handle objects in order when creating musicxml 
    for obj in m.flat:
        classes = obj.classes # store result of property call oince
        if 'GeneralNote' in classes:
            # .mx here returns a list of notes
            mxMeasure.componentList += obj.mx
        elif 'Dynamic' in classes:
        #elif obj.isClass(dynamics.Dynamic):
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


def mxToMeasure(mxMeasure, inputM21):
    '''Translate an mxMeasure into a music21 Measure.
    Can optionally provide an inputM21 object reference to configure that object; else, an object is created. 
    '''
    from music21 import chord
    from music21 import dynamics
    from music21 import key
    from music21 import note
    from music21 import layout
    from music21 import bar
    from music21 import clef
    from music21 import meter

    if inputM21 == None:
        from music21 import stream
        m = stream.Measure()
    else:
        m = inputM21

    #print mxMeasure
    #print

    mNum, mSuffix = common.getNumFromStr(mxMeasure.get('number'))
    # assume that measure numbers are integers
    if mNum not in [None, '']:
        m.number = int(mNum)
    if mSuffix not in [None, '']:
        m.numberSuffix = mSuffix

    data = mxMeasure.get('width')
    if data != None: # may need to do a format/unit conversion?
        m.layoutWidth = data
        
    junk = mxMeasure.get('implicit')
#         environLocal.printDebug(['_setMX: working on measure:',
#                                 m.number])

    mxAttributes = mxMeasure.get('attributesObj')
    mxAttributesInternal = True
    if mxAttributes is None:    
        # need to keep track of where mxattributessrc is coming from
        mxAttributesInternal = False
        # not all measures have attributes definitions; this
        # gets the last-encountered measure attributes
        mxAttributes = mxMeasure.external['attributes']
        if mxAttributes is None:
            raise TranslateException(
                'no mxAttribues available for this measure')

    #environLocal.printDebug(['mxAttriutes clefList', mxAttributes.clefList, 
    #                        mxAttributesInternal])

    if mxAttributesInternal and len(mxAttributes.timeList) != 0:
        m.timeSignature = meter.TimeSignature()
        m.timeSignature.mx = mxAttributes.timeList

    if mxAttributesInternal is True and len(mxAttributes.clefList) != 0:
        m.clef = clef.Clef()
        m.clef.mx = mxAttributes.clefList

    if mxAttributesInternal is True and len(mxAttributes.keyList) != 0:
        m.keySignature = key.KeySignature()
        m.keySignature.mx = mxAttributes.keyList

    # iterate through components found on components list
    # set to zero for each measure
    offsetMeasureNote = 0 # offset of note w/n measure        
    mxNoteList = [] # for chords
    for i in range(len(mxMeasure)):
        mxObj = mxMeasure[i]
        if i < len(mxMeasure)-1:
            mxObjNext = mxMeasure[i+1]
        else:
            mxObjNext = None

        if isinstance(mxObj, musicxmlMod.Print):
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
            # by looking at the next note can we tell if we have a chord
            if mxNoteNext is not None and mxNoteNext.get('chord') is True:
                if mxNote.get('chord') is False:
                    mxNote.set('chord', True) # set the first as a chord

            if mxNote.get('rest') in [None, False]: # it is a note

                if mxNote.get('chord') is True:
                    mxNoteList.append(mxNote)
                    offsetIncrement = 0
                else:
                    n = note.Note()
                    n.mx = mxNote
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
                m.insert(offsetMeasureNote, n)            
                offsetIncrement = n.quarterLength

            # if we we have notes in the note list and the next
            # not either does not exist or is not a chord, we 
            # have a complete chord
            if len(mxNoteList) > 0 and (mxNoteNext is None 
                or mxNoteNext.get('chord') is False):
                c = chord.Chord()
                c.mx = mxNoteList
                mxNoteList = [] # clear for next chord
                m.insert(offsetMeasureNote, c)
                offsetIncrement = c.quarterLength

            # do not need to increment for musicxml chords
            offsetMeasureNote += offsetIncrement

        # load dynamics into measure
        elif isinstance(mxObj, musicxmlMod.Direction):
#                 mxDynamicsFound, mxWedgeFound = m._getMxDynamics(mxObj)
#                 for mxDirection in mxDynamicsFound:
            if mxObj.getDynamicMark() is not None:
                d = dynamics.Dynamic()
                d.mx = mxObj
                m.insert(offsetMeasureNote, d)  
            if mxObj.getWedge() is not None:
                w = dynamics.Wedge()
                w.mx = mxObj     
                m.insert(offsetMeasureNote, w)  


def measureToMusicXML(m):
    '''Translate a music21 Measure into a complete musicXML string representation.

    Note: this method is called for complete musicxml representation of a Measure, not in in Part or Stream production. 
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



#     mxMeasure = m._getMX()
# 
#     mxPart = musicxmlMod.Part()
#     mxPart.setDefaults()
#     mxPart.append(mxMeasure) # append measure here
# 
#     # see if an instrument is defined in this or a prent stream
#     instObj = m.getInstrument()
# 
#     if instObj.partId == None:
#         instObj.instrumentIdRandomize()
#         instObj.partIdRandomize()
# 
#     mxScorePart = musicxmlMod.ScorePart()
#     mxScorePart.set('partName', instObj.partName)
#     mxScorePart.set('id', instObj.partId)
#     # must set this part to the same id
#     mxPart.set('id', instObj.partId)
# 
#     mxPartList = musicxmlMod.PartList()
#     mxPartList.append(mxScorePart)
# 
#     mxIdentification = musicxmlMod.Identification()
#     mxIdentification.setDefaults() # will create a composer
#     mxScore = musicxmlMod.Score()
#     mxScore.setDefaults()
#     mxScore.set('partList', mxPartList)
#     mxScore.set('identification', mxIdentification)
#     mxScore.append(mxPart)
# 
#     return mxScore.xmlStr()


#-------------------------------------------------------------------------------
# Streams


def streamPartToMx(s, instObj=None, meterStream=None,
                        refStreamOrTimeRange=None):
    '''If there are Measures within this stream, use them to create and
    return an MX Part and ScorePart. 

    An `instObj` may be assigned from caller; this Instrument is pre-collected from this Stream in order to configure id and midi-channel values. 

    The `meterStream`, if provides a template of meters. 
    '''
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
        mxPart.append(obj.mx)

    # mxScorePart contains mxInstrument
    return mxScorePart, mxPart


def streamToMx(s):
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
    mxComponents = []
    instList = []
    
    # search context probably should always be True here
    # to search container first, we need a non-flat version
    # searching a flattened version, we will get contained and non-container
    # this meter  stream is passed to makeMeasures()
    meterStream = s.getTimeSignatures(searchContext=False,
                    sortByCreationTime=False, returnDefault=False) 
    if len(meterStream) == 0:
        meterStream = s.flat.getTimeSignatures(searchContext=False,
                    sortByCreationTime=True, returnDefault=True) 

    # we need independent sub-stream elements to shift in presentation
    highestTime = 0

    if s.hasPartLikeStreams():
        #environLocal.printDebug('Stream._getMX: interpreting multipart')
        # need to edit streams contained within streams
        # must repack into a new stream at each step
        #midStream = Stream()
        #finalStream = Stream()

        # NOTE: used to make a shallow copy here
        # TODO: check; removed 4/16/2010
        # TODO: now making a deepcopy, as we are going to edit internal objs
        partStream = copy.deepcopy(s)

        for obj in partStream.getElementsByClass('Stream'):
            # may need to copy element here
            # apply this streams offset to elements
            obj.transferOffsetToElements() 

# its not clear that this gathering, at the level of each part
# is necessary, given how this is done for the entire score, or the 
# flat score. 

#             ts = obj.getTimeSignatures(sortByCreationTime=True, 
#                  searchContext=False)
#             # the longest meterStream is the meterStream for all parts
#             if len(ts) > meterStream:
#                 meterStream = ts

            ht = obj.highestTime
            if ht > highestTime:
                highestTime = ht
            # used to place in intermediary stream
            #midStream.insert(obj)

        #refStream = Stream()
        #refStream.insert(0, music21.Music21Object()) # placeholder at 0
        #refStream.insert(highestTime, music21.Music21Object()) 

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
                inst.midiChannelAutoAssign(usedChannels=midiChannelList)
            midiChannelList.append(inst.midiChannel)

            #environLocal.printDebug(['midiChannel list', midiChannelList])

            # add to list for checking on next round
            instList.append(inst)

            # force this instrument into this part
            # meterStream is only used here if there are no measures
            # defined in this part
            # this method calls streamPartToMx()
            mxComponents.append(obj._getMXPart(inst, meterStream,
                            refStreamOrTimeRange))

    else: # assume this is the only part
        #environLocal.printDebug('Stream._getMX(): handling single-part Stream')
        # if no instrument is provided it will be obtained through s
        # when _getMxPart is called
        mxComponents.append(s._getMXPart(None, meterStream))

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


def mxToStreamPart(mxScore, partId, inputM21):
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


    if inputM21 == None:
        from music21 import stream
        s = stream.Stream()
    else:
        s = inputM21

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

    # offset is in quarter note length
    oMeasure = 0.0
    lastTimeSignature = None
    for mxMeasure in mxPart:
        # create a music21 measure and then assign to mx attribute
        m = stream.Measure()
        m.mx = mxMeasure  # assign data into music21 measure 
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

    streamPart.addGroupForElements(partId) # set group for components 
    streamPart.groups.append(partId) # set group for stream itself

    # add to this Stream
    # this assumes all start at the same place
    # even if there is only one part, it will be placed in a Stream
    s.insert(0, streamPart)


def mxToStream(mxScore, inputM21):
    '''Given an mxScore, build into this stream.
    '''

    from music21 import metadata

    if inputM21 == None:
        from music21 import stream
        s = stream.Score()
    else:
        s = inputM21

    partNames = mxScore.getPartNames().keys()
    partNames.sort()
    for partName in partNames: # part names are part ids
        s._setMXPart(mxScore, partName)

    # add metadata object; this is placed after all other parts now
    # these means that both Parts and other objects live on Stream.
    md = metadata.Metadata()
    md.mx = mxScore
    s.insert(0, md)




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


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        t = Test()
        t.testBarRepeatConversion()

