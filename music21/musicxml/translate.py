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
def measureToMx(m):
    '''Given a measure, translate to musicxml objects
    '''

    mxMeasure = musicxmlMod.Measure()
    mxMeasure.set('number', m.measureNumber)

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
    if m.clef is not None:
        mxAttributes.clefList = [m.clef.mx]

    if m.keySignature is not None: 
        # key.mx returns a Key ojbect, needs to be in a list
        mxAttributes.keyList = [m.keySignature.mx]
    
    if m.timeSignature is not None:
        mxAttributes.timeList = m.timeSignature.mx 

    #mxAttributes.keyList = []
    mxMeasure.set('attributes', mxAttributes)

    # see if we have a left barline
    if m.leftBarline != None:
        mxBarline = m.leftBarline.mx
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

    # see if we have a right barline
    # presently turning barline output off b/c of performance concerns
#     if m.rightBarline != None:
#         mxBarline = m.rightBarline.mx
#         # setting location outside of object based on attribute
#         mxBarline.set('location', 'right')
#         mxMeasure.componentList.append(mxBarline)

    return mxMeasure


def mxToMeasure(mxMeasure, inputM21):
    '''
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

    mNum, mSuffix = common.getNumFromStr(mxMeasure.get('number'))
    # assume that measure numbers are integers
    if mNum not in [None, '']:
        m.measureNumber = int(mNum)
    if mSuffix not in [None, '']:
        m.measureNumberSuffix = mSuffix

    data = mxMeasure.get('width')
    if data != None: # may need to do a format/unit conversion?
        m.layoutWidth = data
        
    junk = mxMeasure.get('implicit')
#         environLocal.printDebug(['_setMX: working on measure:',
#                                 m.measureNumber])

    mxAttributes = mxMeasure.get('attributes')
    mxAttributesInternal = True
    if mxAttributes is None:    
        # need to keep track of where mxattributessrc is coming from
        mxAttributesInternal = False
        # not all measures have attributes definitions; this
        # gets the last-encountered measure attributes
        mxAttributes = mxMeasure.external['attributes']
        if mxAttributes is None:
            raise StreamException(
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
            mxBarline = mxObj
            barline = bar.Barline()
            barline.mx = mxBarline # configure
            if barline.location == 'left':
                m.leftBarline = barline
            elif barline.location == 'right':
                # there may be problems importing a right barline
                # as we may not have  time signature
                # presently, the rightBarline property uses the the 
                # highestTime value
                #m.rightBarline = barline
                # this avoids doing a context search, but may have non
                # final offset
                m.insert(m.highestTime, barline)

            else:
                environLocal.printDebug(['not handling barline that is neither left nor right', barline, barline.location])

        elif isinstance(mxObj, musicxmlMod.Note):
            mxNote = mxObj
            if isinstance(mxObjNext, musicxmlMod.Note):
                mxNoteNext = mxObjNext
            else:
                mxNoteNext = None

            if mxNote.get('print-object') == 'no':
                #environLocal.printDebug(['got mxNote with printObject == no', 'measure number', m.measureNumber])
                continue

            mxGrace = mxNote.get('grace')
            if mxGrace is not None: # graces have a type but not a duration
                #TODO: add grace notes with duration equal to ZeroDuration
                #environLocal.printDebug(['got mxNote with an mxGrace', 'duration', mxNote.get('duration'), 'measure number', 
                #m.measureNumber])
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
                if mxNote.get('notations') is not None:
                    for mxObjSub in mxNote.get('notations'):
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
    '''Convert a music21 measure into a complete musicXML string representation
    '''

    mxMeasure = m._getMX()

    mxPart = musicxmlMod.Part()
    mxPart.setDefaults()
    mxPart.append(mxMeasure) # append measure here


    # see if an instrument is defined in this or a prent stream
    instObj = m.getInstrument()
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



#-------------------------------------------------------------------------------





