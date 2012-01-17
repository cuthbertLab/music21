# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         segment.py
# Purpose:      music21 class which allows division of streams into braille segments.
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import music21
import collections
import unittest
import copy

from music21 import articulations
from music21 import bar
from music21 import chord
from music21 import clef
from music21 import dynamics
from music21 import expressions
from music21 import key
from music21 import meter
from music21 import note
from music21 import spanner
from music21 import stream
from music21 import tempo

from music21.braille import basic
from music21.braille import lookup
from music21.braille import text

symbols = lookup.symbols
binary_dots = lookup.binary_dots

#-------------------------------------------------------------------------------
# Segment Grouping Methods

class BrailleElementGrouping(list):
    pass

class BrailleSegment(collections.defaultdict):
    pass



'''
Part keywords:
- slurLongPhraseWithBrackets
- showShortSlursAndTiesTogether
- showLongSlursAndTiesTogether
- segmentBreaks
- showHand

'''
def findSegments(music21Part, **partKeywords):
    '''
    How do you explain all this?
    
    Fudge.
    
    Blast.
    
    Takes in a :class:`~music21.stream.Part`
    
    Organizes the elements of the stream Part into segments
    
    
    
    
    '''
    slurLongPhraseWithBrackets = True
    showShortSlursAndTiesTogether, showLongSlursAndTiesTogether = False, False
    segmentBreaks = None
    descendingChords = True

    if 'slurLongPhraseWithBrackets' in partKeywords:
        slurLongPhraseWithBrackets = partKeywords['slurLongPhraseWithBrackets']
    if 'showShortSlursAndTiesTogether' in partKeywords:
        showShortSlursAndTiesTogether = partKeywords['showShortSlursAndTiesTogether']
    if 'showLongSlursAndTiesTogether' in partKeywords:
        showLongSlursAndTiesTogether = partKeywords['showLongSlursAndTiesTogether']
    else:
        if slurLongPhraseWithBrackets:
            showLongSlursAndTiesTogether = True
    if 'segmentBreaks' in partKeywords:
        segmentBreaks = partKeywords['segmentBreaks']
    if 'showHand' in partKeywords:
        if partKeywords['showHand'] == 'left':
            descendingChords = False
        elif partKeywords['showHand'] == 'right':
            descendingChords = True

    prepareSlurredNotes(music21Part, slurLongPhraseWithBrackets, showShortSlursAndTiesTogether, showLongSlursAndTiesTogether)
    allSegments = []
    currentSegment = BrailleSegment(BrailleElementGrouping)
    measureNumberStart = 10E5
    offsetStart = 0.0
    if not segmentBreaks == None:
        firstSegmentBreak = segmentBreaks.pop()
        (measureNumberStart, offsetStart) = firstSegmentBreak
    currentKeySig = key.KeySignature(0)
    try:
        currentTimeSig = music21Part.getElementsByClass('Measure')[0].bestTimeSignature()
    except stream.StreamException:
        currentTimeSig = meter.TimeSignature('4/4')
    if descendingChords is None:
        # run get clefs on first measure of music21Part. 
        pass    
    
    greaterOffsetFactor = 0
    greaterPreviousCode = -1
    biggerPicture = BrailleSegment(BrailleElementGrouping)
    for music21Measure in music21Part.getElementsByClass('Measure'):
        prepareBeamedNotes(music21Measure)
        brailleElements = []
        for music21Object in music21Measure:
            try:
                setBrailleElementProperties(music21Object)
                brailleElements.append(music21Object)
            except BrailleSegmentException:
                pass
        brailleElements.sort(cmp = lambda x, y: cmp(x.offset, y.offset) or cmp(x.classSortOrder, y.classSortOrder))
        if len(brailleElements) > 0 and brailleElements[-1].type == 'Dynamic':
            brailleElements[-1].classSortOrder = -6
            brailleElements.sort(cmp = lambda x, y: cmp(x.offset, y.offset) or cmp(x.classSortOrder, y.classSortOrder))
        lesserOffsetFactor = 0
        lesserPreviousCode = -1
        for brailleElement in brailleElements:
            if music21Measure.number > measureNumberStart or\
                music21Measure.number == measureNumberStart and brailleElement.offset >= offsetStart:
                allSegments.append(currentSegment)
                currentSegment = BrailleSegment(BrailleElementGrouping)
                try:
                    nextSegmentBreak = segmentBreaks.pop()
                    (measureNumberStart, offsetStart) = nextSegmentBreak
                except IndexError:
                    (measureNumberStart, offsetStart) = (10E5, 0.0)
                greaterOffsetFactor += 1
            if brailleElement.type == 'Key Signature':
                brailleElement.outgoingKeySig = currentKeySig
                currentKeySig = brailleElement
            elif brailleElement.type == 'Time Signature':
                currentTimeSig = brailleElement
            elif brailleElement.type == 'Rest' and brailleElement.duration == music21Measure.duration:
                brailleElement.quarterLength = 4.0
            if brailleElement.affinityCode < lesserPreviousCode:
                lesserOffsetFactor += 1
            if brailleElement.affinityCode < greaterPreviousCode:
                greaterOffsetFactor += 1
            lesserBucketNumber = music21Measure.number * 100 +  lesserOffsetFactor * 10 + int(brailleElement.affinityCode)
            greaterBucketNumber = 10*greaterOffsetFactor + int(brailleElement.affinityCode)
            currentSegment[lesserBucketNumber].append(brailleElement)
            biggerPicture[greaterBucketNumber].append(brailleElement)
            if brailleElement.affinityCode == 9:
                try:
                    currentSegment[lesserBucketNumber].keySignature
                    currentSegment[lesserBucketNumber].timeSignature
                    currentSegment[lesserBucketNumber].descendingChords
                except AttributeError:
                    currentSegment[lesserBucketNumber].keySignature = currentKeySig
                    currentSegment[lesserBucketNumber].timeSignature = currentTimeSig
                    currentSegment[lesserBucketNumber].descendingChords = descendingChords
            lesserPreviousCode = brailleElement.affinityCode
            greaterPreviousCode = lesserPreviousCode

    # check each consolidated note grouping for articulation doublings
    for bucketNumber in sorted([n for n in biggerPicture if n%10==9]):
        allNotes = [n for n in biggerPicture[bucketNumber] if n.type == "Note"]
        for noteIndexStart in range(len(allNotes)):
            music21NoteStart = allNotes[noteIndexStart]
            for artcIndex in range(len(music21NoteStart.articulations)):
                artc = music21NoteStart.articulations[artcIndex]
                # "If two repeated notes appear to be tied, but either is marked staccato or tenuto,
                # they are treated as slurred instead of tied"
                if isinstance(artc, articulations.Staccato) or isinstance(artc, articulations.Tenuto):
                    if not music21NoteStart.tie == None:
                        if music21NoteStart.tie.type == 'stop':
                            music21NoteStart.tie = None
                            allNotes[noteIndexStart-1].tie = None
                            allNotes[noteIndexStart-1].shortSlur = True
                        else:
                            music21NoteStart.tie = None
                            music21NoteStart.shortSlur = True
                            allNotes[noteIndexStart+1].tie = None
                numSequential=0
                for noteIndexContinue in range(noteIndexStart+1, len(allNotes)):
                    music21NoteContinue = allNotes[noteIndexContinue]
                    if artc in music21NoteContinue.articulations:
                        numSequential+=1
                        continue
                    break
                if numSequential >= 3:
                    music21NoteStart.articulations.append(artc)
                    for noteIndexContinue in range(noteIndexStart+1, noteIndexStart+numSequential):
                        music21NoteContinue = allNotes[noteIndexContinue]
                        music21NoteContinue.articulations.remove(artc)            
            
    allSegments.append(currentSegment)
    return allSegments

brailleElements = collections.OrderedDict({'Note':    (9, 20),
                                           'Rest':    (9, 20),
                                           'Chord':   (9, 20),
                                           'Dynamic': (9, 19),
                                           'Clef':    (9, 15),
                                           'KeySignature':  (3, 2),
                                           'TimeSignature': (3, 3),
                                           'Barline': (9.5, -5),
                                           'TempoText': (4, 5),
                                           'MetronomeMark': (5, 6)})

def setBrailleElementProperties(music21Object):
    if isinstance(music21Object, note.Note):
        music21Object.type = "Note"
        music21Object.affinityCode = 9
        music21Object.classSortOrder = 20
    elif isinstance(music21Object, note.Rest):
        music21Object.type = "Rest"
        music21Object.affinityCode = 9
        music21Object.classSortOrder = 20
    elif isinstance(music21Object, chord.Chord):
        music21Object.type = "Chord"
        music21Object.affinityCode = 9
        music21Object.classSortOrder = 20
    elif isinstance(music21Object, dynamics.Dynamic):
        music21Object.type = "Dynamic"
        music21Object.affinityCode = 9
        music21Object.classSortOrder = 19
    elif isinstance(music21Object, key.KeySignature):
        music21Object.type = "Key Signature"
        music21Object.affinityCode = 3
        music21Object.outgoingKeySig = None
    elif isinstance(music21Object, meter.TimeSignature):
        music21Object.type = "Time Signature"
        music21Object.affinityCode = 3
    elif isinstance(music21Object, bar.Barline):
        music21Object.type = "Barline"
        music21Object.affinityCode = 9.5
    elif isinstance(music21Object, clef.Clef):
        music21Object.type = "Clef"
        music21Object.affinityCode = 9
        music21Object.classSortOrder = 15   
    elif isinstance(music21Object, tempo.TempoText):
        music21Object.type = "Tempo Text"
        music21Object.affinityCode = 4
        music21Object.classSortOrder = 5
    elif isinstance(music21Object, tempo.MetronomeMark):
        music21Object.type = "Metronome Mark"
        music21Object.affinityCode = 5
        music21Object.classSortOrder = 6
    elif isinstance(music21Object, expressions.TextExpression):
        music21Object.type = "Text Expression"
        if len(music21Object.content.split()) > 1:
            music21Object.affinityCode = 8
        else:
            music21Object.affinityCode = 9
        music21Object.classSortOrder = 18
    else:
        raise BrailleSegmentException()
    
    return True

#-------------------------------------------------------------------------------
# Segment Extraction Methods

def extractHeading(brailleSegment, maxLineLength):
    allGroupingKeys = sorted(brailleSegment.keys())
    if allGroupingKeys[0] % 10 == 9:
        raise BrailleSegmentException("No heading elements to extract!")

    initMeasureNumber = allGroupingKeys[0] / 100
    initGroupingNumber = initMeasureNumber * 100
    sigLoc = initGroupingNumber + 3
    tempoTextLoc = initGroupingNumber + 4
    metroMarkLoc = initGroupingNumber + 5
    
    keySignature = None
    timeSignature = None
    tempoText = None
    metronomeMark = None
    if sigLoc in allGroupingKeys:
        signaturesGrouping = brailleSegment[sigLoc]
        del brailleSegment[sigLoc]
        if len(signaturesGrouping) == 2:
            keySignature = signaturesGrouping[0]
            timeSignature = signaturesGrouping[1]
        elif signaturesGrouping[0].type == 'Key Signature':
            keySignature = signaturesGrouping[0]
        elif signaturesGrouping[0].type == 'Time Signature':
            timeSignature = signaturesGrouping[0]
    if tempoTextLoc in allGroupingKeys:
        tempoTextGrouping = brailleSegment[tempoTextLoc]
        del brailleSegment[tempoTextLoc]
        tempoText = tempoTextGrouping[0]
    if metroMarkLoc in allGroupingKeys:
        metroMarkGrouping = brailleSegment[metroMarkLoc]
        del brailleSegment[metroMarkLoc]
        metronomeMark = metroMarkGrouping[0]

    try:
        brailleHeading = basic.transcribeHeading(keySignature, timeSignature, tempoText, metronomeMark, maxLineLength)
        return brailleHeading
    except basic.BrailleBasicException:
        raise BrailleSegmentException("Heading elements correspond to a zero-length braille expression.")

def extractLongExpression(brailleSegment):
    allGroupingKeys = sorted(brailleSegment.keys())
    if allGroupingKeys[0] % 10 != 8:
        raise BrailleSegmentException("No long expression to extract!")

    exprLoc = allGroupingKeys[0]
    longExpr = brailleSegment[exprLoc][0]
    del brailleSegment[exprLoc]
    return basic.textExpressionToBraille(longExpr)

def extractMeasureNumber(brailleSegment):
    allGroupingKeys = sorted(brailleSegment.keys())
    initMeasureNumber = allGroupingKeys[0] / 100
    return basic.numberToBraille(initMeasureNumber)

def extractNoteGroupings(brailleSegment):
    allGroupingKeys = sorted(brailleSegment.keys())
    if allGroupingKeys[0] % 10 != 9:
        raise BrailleSegmentException("No note groupings to extract!")
    
    consecNoteGroupings = []
    for gk in allGroupingKeys:
        if gk % 10 != 9:
            break
        noteGrouping = brailleSegment[gk]
        del brailleSegment[gk]
        consecNoteGroupings.append((gk, noteGrouping))
    
    return consecNoteGroupings

def extractSignatures(brailleSegment, cancelOutgoingKeySig):
    allGroupingKeys = sorted(brailleSegment.keys())
    if allGroupingKeys[0] % 10 != 3:
        raise BrailleSegmentException("No signatures to extract!")

    keySignature = None
    timeSignature = None
    sigLoc = allGroupingKeys[0]
    signaturesGrouping = brailleSegment[sigLoc]
    if not (sigLoc+1) in allGroupingKeys:
        del brailleSegment[sigLoc]
    if len(signaturesGrouping) != 0:
        if len(signaturesGrouping) == 2:
            keySignature = signaturesGrouping[0]
            timeSignature = signaturesGrouping[1]
        elif signaturesGrouping[0].type == 'Key Signature':
            keySignature = signaturesGrouping[0]
        elif signaturesGrouping[0].type == 'Time Signature':
            timeSignature = signaturesGrouping[0]
    outgoingKeySig = None
    if cancelOutgoingKeySig and not keySignature is None:
        outgoingKeySig = keySignature.outgoingKeySig
    
    try:
        brailleSig = basic.transcribeSignatures(keySignature, timeSignature, outgoingKeySig)
        return brailleSig
    except basic.BrailleBasicException:
        raise BrailleSegmentException("Signatures correspond to a zero-length braille expression.")

#-------------------------------------------------------------------------------
# Segment Transcription Methods

'''
Segment keywords:
- cancelOutgoingKeySig
- dummyRestLength
- maxLineLength
- showClefSigns
- showFirstMeasureNumber
- showHand
- showHeading
- showLeadingOctave
- upperFirstInNoteFingering
'''
def transcribeSegment(brailleSegment, **segmentKeywords):
    cancelOutgoingKeySig = True
    dummyRestLength = None
    maxLineLength = 40
    showClefSigns = False
    showFirstMeasureNumber = True
    showHand = None
    showHeading = True
    showLeadingOctave = True
    upperFirstInNoteFingering = True

    if 'cancelOutgoingKeySig' in segmentKeywords:
        cancelOutgoingKeySig = segmentKeywords['cancelOutgoingKeySig']
    if 'dummyRestLength' in segmentKeywords:
        dummyRestLength = segmentKeywords['dummyRestLength']
    if 'maxLineLength' in segmentKeywords:
        maxLineLength = segmentKeywords['maxLineLength']
    if 'showClefSigns' in segmentKeywords:
        showClefSigns = segmentKeywords['showClefSigns']
    if 'showFirstMeasureNumber' in segmentKeywords:
        showFirstMeasureNumber = segmentKeywords['showFirstMeasureNumber']
    if 'showHand' in segmentKeywords:
        showHand = segmentKeywords['showHand']
    if 'showHeading' in segmentKeywords:
        showHeading = segmentKeywords['showHeading']
    if 'showLeadingOctave' in segmentKeywords:
        showLeadingOctave = segmentKeywords['showLeadingOctave']
    if 'upperFirstInNoteFingering' in segmentKeywords:
        upperFirstInNoteFingering = segmentKeywords['upperFirstInNoteFingering']

    bt = text.BrailleText(maxLineLength, showHand = showHand)
    try:
        if showHeading is True:
            brailleHeading = extractHeading(brailleSegment, maxLineLength)
            bt.addElement(heading = brailleHeading, withHyphen = False)
    except BrailleSegmentException:
        pass # No heading to make

    if showFirstMeasureNumber:
        bt.addElement(measureNumber = extractMeasureNumber(brailleSegment))
    if not dummyRestLength == None:
        bt.addElement(keyOrTimeSig = u"".join([dummyRestLength * lookup.rests['dummy']]), withHyphen = False)

    isFirstNoteGrouping = True
    lastGK = None
    while True:
        allGroupingKeys = sorted(brailleSegment.keys())
        if len(allGroupingKeys) == 0:
            break
        initGroupingKey = allGroupingKeys[0]
        if not (lastGK is None) and initGroupingKey == lastGK:
            initGroupingKey = allGroupingKeys[1]
        if initGroupingKey % 10 == 9:
            noteGroupings = extractNoteGroupings(brailleSegment)
            lastNote = None
            for (gk, noteGrouping) in noteGroupings:
                allNotes = [be for be in noteGrouping if be.type == 'Note']
                withHyphen = False
                if not (lastGK is None) and (gk - lastGK) == 10:
                    withHyphen = True
                    lastNote = None
                lastGK = gk
                if len(allNotes) > 0:
                    if not lastNote == None:
                        firstNote = allNotes[0]
                        showLeadingOctave = basic.showOctaveWithNote(lastNote, firstNote)
                    elif not isFirstNoteGrouping:
                        showLeadingOctave = True
                    lastNote = allNotes[-1]
                try:
                    brailleNoteGrouping = transcribeNoteGrouping(noteGrouping, showLeadingOctave, showClefSigns, upperFirstInNoteFingering)
                    bt.addElement(noteGrouping = brailleNoteGrouping,\
                                   showLeadingOctave = showLeadingOctave, withHyphen = withHyphen, forceHyphen = False)
                except text.BrailleTextException as bte:
                    if bte.args[0] == "Recalculate Note Grouping With Leading Octave":
                        showLeadingOctave = True
                        brailleNoteGrouping = transcribeNoteGrouping(noteGrouping, showLeadingOctave, showClefSigns, upperFirstInNoteFingering)
                        bt.addElement(noteGrouping = brailleNoteGrouping,\
                                       showLeadingOctave = showLeadingOctave, withHyphen = withHyphen, forceHyphen = False)
                    elif bte.args[0] == "Split Note Grouping":
                        isSolved = False
                        bdo = 0
                        while not isSolved:
                            sng = splitNoteGrouping(noteGrouping, beatDivisionOffset = bdo)
                            brailleNoteGroupingA = transcribeNoteGrouping(sng[0], showLeadingOctave, showClefSigns, upperFirstInNoteFingering)
                            try:
                                bt.addElement(noteGrouping = brailleNoteGroupingA,\
                                               showLeadingOctave = showLeadingOctave, withHyphen = withHyphen, forceHyphen = False)
                            except text.BrailleTextException:
                                bdo += 1
                                continue
                            showLeadingOctave = True
                            brailleNoteGroupingB = transcribeNoteGrouping(sng[1], showLeadingOctave, showClefSigns, upperFirstInNoteFingering)
                            bt.addElement(noteGrouping = brailleNoteGroupingB, showLeadingOctave = True, withHyphen = True)
                            isSolved = True
                isFirstNoteGrouping = False     
        elif initGroupingKey % 10 == 3:
            withHyphen = False
            if not (lastGK is None) and (initGroupingKey - lastGK) == 4:
                withHyphen = True
            try:
                brailleSig = extractSignatures(brailleSegment, cancelOutgoingKeySig)
                bt.addElement(keyOrTimeSig = brailleSig, withHyphen = withHyphen)
            except BrailleSegmentException:
                pass
            lastGK = initGroupingKey
        elif initGroupingKey % 10 == 4:
            brailleHeading = extractHeading(brailleSegment, maxLineLength)
            bt.addElement(heading = brailleHeading, withHyphen = False)
            bt.addElement(measureNumber = extractMeasureNumber(brailleSegment))
            lastGK = initGroupingKey
        elif initGroupingKey % 10 == 8:
            brailleExpr = extractLongExpression(brailleSegment)
            if not initGroupingKey % 100 == 8:
                bt.addElement(longExpression = brailleExpr, withHyphen = True)
            else:
                bt.addElement(longExpression = brailleExpr, withHyphen = False)
            lastGK = initGroupingKey
        else:
            break
    
    return bt

def transcribeNoteGrouping(brailleElements, showLeadingOctave = True, showClefSigns = False, upperFirstInNoteFingering = True):
    trans = []
    previousNote = None
    previousElement = None
    for brailleElement in brailleElements:
        if brailleElement.type == 'Note':
            currentNote = brailleElement
            if previousNote == None:
                doShowOctave = showLeadingOctave
            else:
                doShowOctave = basic.showOctaveWithNote(previousNote, currentNote)
            trans.append(basic.noteToBraille(currentNote, showOctave = doShowOctave, upperFirstInFingering = upperFirstInNoteFingering))
            previousNote = currentNote
        elif brailleElement.type == 'Rest':
            currentRest = brailleElement
            trans.append(basic.restToBraille(currentRest))
        elif brailleElement.type == "Chord":
            currentChord = brailleElement
            try:
                allNotes = sorted(currentChord._components, key=lambda n: n.pitch)
            except AttributeError as e:
                raise BrailleSegmentException("If you're getting this exception, the '_components' attribute for a music21 Chord probably\
                became 'notes'. If that's the case, change it and life will be great.")
            if brailleElements.descendingChords:
                currentNote = allNotes[-1]
            else:
                currentNote = allNotes[0]
            if previousNote == None:
                doShowOctave = showLeadingOctave
            else:
                doShowOctave = basic.showOctaveWithNote(previousNote, currentNote)
            trans.append(basic.chordToBraille(currentChord, descending = brailleElements.descendingChords, showOctave = doShowOctave))
            previousNote = currentNote
        elif brailleElement.type == 'Dynamic':
            currentDynamic = brailleElement
            trans.append(basic.dynamicToBraille(currentDynamic))
            previousNote = None
            showLeadingOctave = True
        elif brailleElement.type == 'Text Expression':
            currentExpression = brailleElement
            trans.append(basic.textExpressionToBraille(currentExpression))
            previousNote = None
            showLeadingOctave = True
        elif brailleElement.type == 'Barline':
            currentBarline = brailleElement
            trans.append(basic.barlineToBraille(currentBarline))
        elif brailleElement.type == 'Clef':
            if showClefSigns:
                currentClef = brailleElement
                trans.append(basic.clefToBraille(currentClef))
                previousNote = None
                showLeadingOctave = True
        else:
            raise BrailleSegmentException("Unknown Note Grouping Element")
        if not previousElement == None:
            if showClefSigns and previousElement.type == 'Clef' or\
                previousElement.type == 'Dynamic' and\
                not brailleElement.type == 'Dynamic' and not brailleElement.type == 'Text Expression':
                for dots in binary_dots[trans[-1][0]]:
                    if (dots == '10' or dots == '11'):
                        trans.insert(-1, symbols['dot'])
                        break
            elif previousElement.type == 'Text Expression' and\
                not brailleElement.type == 'Dynamic' and not brailleElement.type == 'Text Expression':
                if not previousElement.content[-1] == '.': # abbreviation, no extra dot 3 necessary
                    for dots in binary_dots[trans[-1][0]]:
                        if (dots == '10' or dots == '11'):
                            trans.insert(-1, symbols['dot'])
                            break
        previousElement = brailleElement
        
    return u"".join(trans)

#-------------------------------------------------------------------------------
# Helper Methods

# Splits a note grouping
def splitNoteGrouping(brailleNoteGrouping, value = 2, beatDivisionOffset = 0):
    music21Measure = stream.Measure()
    for brailleElement in brailleNoteGrouping:
        music21Measure.insert(brailleElement.offset, brailleElement)
    newMeasures = splitMeasure(music21Measure, value, beatDivisionOffset, brailleNoteGrouping.timeSignature)
    leftBrailleElements = []
    for brailleElement in newMeasures[0]:
        leftBrailleElements.append(brailleElement)
    rightBrailleElements = []
    for brailleElement in newMeasures[1]:
        rightBrailleElements.append(brailleElement)
    return (leftBrailleElements, rightBrailleElements)

# Prepares notes for braille beaming in a measure
def prepareBeamedNotes(music21Measure):
    allNotes = music21Measure.notes
    for sampleNote in allNotes:
        sampleNote.beamStart = False
        sampleNote.beamContinue = False
    allNotesAndRests = music21Measure.notesAndRests
    allNotesWithBeams = allNotes.splitByClass(None, lambda sampleNote: not(sampleNote.beams == None) and len(sampleNote.beams) > 0)[0]
    allStart = allNotesWithBeams.splitByClass(None, lambda sampleNote: sampleNote.beams.getByNumber(1).type is 'start')[0]
    allStop  = allNotesWithBeams.splitByClass(None, lambda sampleNote: sampleNote.beams.getByNumber(1).type is 'stop')[0]
    
    if not(len(allStart) == len(allStop)):
        raise BrailleSegmentException("Incorrect beaming: number of start notes != to number of stop notes.")
    
    for beamIndex in range(len(allStart)):
        startNote = allStart[beamIndex]
        stopNote = allStop[beamIndex]
        startIndex = allNotesAndRests.index(startNote)
        stopIndex = allNotesAndRests.index(stopNote)
        delta = stopIndex - startIndex + 1
        if delta < 3: # 2. The group must be composed of at least three notes.
            continue
        # 1. All notes in the group must have precisely the same value.
        # 3. A rest of the same value may take the place of the first note in a group, 
        # but if the rest is located anywhere else, grouping may not be used.
        allNotesOfSameValue = True
        for noteIndex in range(startIndex+1, stopIndex+1):
            if not(allNotesAndRests[noteIndex].duration.type == startNote.duration.type) or isinstance(allNotesAndRests[noteIndex], note.Rest):
                allNotesOfSameValue = False
                break
        try:
            afterStopNote = allNotesAndRests[stopIndex+1]
            if isinstance(afterStopNote, note.Rest) and (int(afterStopNote.beat) == int(stopNote.beat)):
                allNotesOfSameValue = False
                continue
        except stream.StreamException: # stopNote is last note of measure.
            pass
        if not allNotesOfSameValue:
            continue
        try:
            # 4. If the notes in the group are followed immediately by a true eighth note or by an eighth rest, 
            # grouping may not be used, unless the eighth is located in a new measure.
            if allNotesAndRests[stopIndex+1].quarterLength == 0.5:
                continue
        except stream.StreamException: # stopNote is last note of measure.
            pass
        startNote.beamStart = True
        try:
            beforeStartNote = allNotesAndRests[startIndex - 1]
            if isinstance(beforeStartNote, note.Rest) and (int(beforeStartNote.beat) == int(startNote.beat)) and \
                (beforeStartNote.duration.type == startNote.duration.type):
                startNote.beamContinue = True
        except IndexError: # startNote is first note of measure.
            pass
        for noteIndex in range(startIndex+1, stopIndex+1):
            allNotesAndRests[noteIndex].beamContinue = True
    
    return True

# Prepares notes for braille slurring in a part
def prepareSlurredNotes(music21Part, slurLongPhraseWithBrackets = True, showShortSlursAndTiesTogether = True, showLongSlursAndTiesTogether = True):
    if not len(music21Part.spannerBundle) > 0:
        return True
    allNotes = music21Part.flat.notes
    for slur in music21Part.spannerBundle.getByClass(spanner.Slur):
        slur[0].index = allNotes.index(slur[0])
        slur[1].index = allNotes.index(slur[1])
        beginIndex = slur[0].index
        endIndex = slur[1].index
        delta = abs(endIndex - beginIndex) + 1
        if not showShortSlursAndTiesTogether and delta <= 4:
            if allNotes[beginIndex].tie != None and allNotes[beginIndex].tie.type == 'start':
                beginIndex += 1
            if allNotes[endIndex].tie != None and allNotes[endIndex].tie.type == 'stop':
                endIndex -= 1
        if not showLongSlursAndTiesTogether and delta > 4:
            if allNotes[beginIndex].tie != None and allNotes[beginIndex].tie.type == 'start':
                beginIndex += 1
            if allNotes[endIndex].tie != None and allNotes[endIndex].tie.type == 'stop':
                endIndex -= 1
        if not(delta > 4):
            for noteIndex in range(beginIndex, endIndex):
                allNotes[noteIndex].shortSlur = True
        else:
            if slurLongPhraseWithBrackets:
                allNotes[beginIndex].beginLongBracketSlur = True
                allNotes[endIndex].endLongBracketSlur = True
            else:
                allNotes[beginIndex + 1].beginLongDoubleSlur = True
                allNotes[endIndex - 1].endLongDoubleSlur = True
    
    return True

def splitMeasure(music21Measure, value = 2, beatDivisionOffset = 0, useTimeSignature = None):
    '''
    Takes a measure and splits it in two parts, although not necessarily in half.
    Value is the number of partitions to split a time signature into.
    The first part will contain all elements found within the offsets of the first partition..
    The last part will contain all elements not found within the offsets of the first partition.
    beatDivisionOffset is meant to adjust the end offset of the first partition by a certain
    number of beats to the left.
    '''
    if not useTimeSignature == None:
        ts = useTimeSignature
    else:
        ts = music21Measure.timeSignature
    
    offset = 0.0
    if not(beatDivisionOffset == 0):
        if abs(beatDivisionOffset) > ts.beatDivisionDurations:
            raise Exception()
        i = len(ts.beatDivisionDurations) - abs(beatDivisionOffset)
        offset += ts.beatDivisionDurations[i].quarterLength
        
    bs = copy.deepcopy(ts.beatSequence)
    try:  
        bs.partitionByCount(value, loadDefault = False)
        (startOffsetZero, endOffsetZero) = bs.getLevelSpan()[0]
    except meter.MeterException:
        value += 1
        bs.partitionByCount(value, loadDefault = False)
        startOffsetZero = bs.getLevelSpan()[0][0]
        endOffsetZero = bs.getLevelSpan()[-2][-1]
    endOffsetZero -= offset
    newMeasures = stream.Part()
    newMeasures.append(stream.Measure())
    newMeasures.append(stream.Measure())
    for x in music21Measure:
        if x.offset >= startOffsetZero and (x.offset < endOffsetZero or (x.offset == endOffsetZero and isinstance(x, bar.Barline))):
            newMeasures[0].insert(x.offset, x)
        else:
            newMeasures[1].insert(x.offset, x)
    for n in newMeasures[1].notes:
        if n.tie != None:
            newMeasures[0].append(n)
            newMeasures[1].remove(n)
            endOffsetZero += n.duration.quarterLength
            continue
        break

    r0 = note.Rest(quarterLength = music21Measure.duration.quarterLength - endOffsetZero)
    newMeasures[0].insert(endOffsetZero, r0)
    r1 = note.Rest(quarterLength = endOffsetZero)
    newMeasures[1].insert(0.0, r1)
    
    ts0_delete = False
    if newMeasures[0].timeSignature == None:
        ts0_delete = True
        newMeasures[0].timeSignature = ts
    newMeasures[1].timeSignature = ts
    newMeasures[0].mergeAttributes(music21Measure)
    newMeasures[1].mergeAttributes(music21Measure)
    newMeasures[0].makeBeams()
    newMeasures[1].makeBeams()
    prepareBeamedNotes(newMeasures[0])
    prepareBeamedNotes(newMeasures[1])
    newMeasures[0].remove(r0)
    newMeasures[1].remove(r1)
    if ts0_delete == True:
        newMeasures[0].remove(ts)
    newMeasures[1].remove(ts)
    return newMeasures

def splitStreamByClass(music21Measure, classFilterList, groupWithPrevious = False):
    elementsOfClasses = music21Measure.getElementsByClass(classFilterList)
    if len(elementsOfClasses) == 0:
        return [music21Measure]
    
    elementsByOffset = elementsOfClasses.groupElementsByOffset(returnDict = True)
    if len(elementsByOffset.keys()) == 1 and 0.0 in elementsByOffset:
        return [music21Measure]

    allStreams = []
    startIndex = 0
    endIndex = 0
    for offset in elementsByOffset:
        if not(offset == 0.0):
            if not groupWithPrevious:
                endIndex = music21Measure.index(elementsByOffset[offset][0])
            else:
                endIndex = music21Measure.index(elementsByOffset[offset][-1]) + 1
            allStreams.append(music21Measure[startIndex:endIndex])
            startIndex = endIndex
    endIndex = len(music21Measure)
    allStreams.append(music21Measure[startIndex:endIndex])
    return allStreams

#-------------------------------------------------------------------------------

class BrailleSegmentException(music21.Music21Exception):
    pass
    
#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass


if __name__ == "__main__":
    import sys
    reload(sys)
    sys.setdefaultencoding("UTF-8")
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof