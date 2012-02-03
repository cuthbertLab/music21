# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         segment.py
# Purpose:      music21 class which allows division of streams into braille segments.
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2012 The music21 Project
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
from music21 import environment
from music21 import expressions
from music21 import key
from music21 import layout
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

environRules = environment.Environment('segment.py')

#-------------------------------------------------------------------------------
class BrailleElementGrouping(list):
    pass

class BrailleSegment(collections.defaultdict):
    def __init__(self):
        # Internal attributes
        # -------------------
        self.default_factory = BrailleElementGrouping
        self.allGroupingKeys = None
        self.currentGroupingKey = None
        self.isFirstNoteGrouping = True
        self.lastNote = None
        self.previousGroupingKey = None
        # External attributes
        # -------------------
        self.cancelOutgoingKeySig = True
        self.dummyRestLength = None
        self.isHyphenated = False
        self.maxLineLength = 40
        self.showFirstMeasureNumber = True
        self.showHand = None
        self.showHeading = True
        self.showLeadingOctave = True

    def __str__(self):
        name = "<music21.braille.segment BrailleSegment {0}>".format(id(self))
        hyphenation = "isHyphenated = {0}".format(self.isHyphenated)
        allGroupings = u"\n".join(["{0}: {1}".format(item[0],item[1]) for item in sorted(self.items())])
        return u"\n".join(["---begin segment---", name, hyphenation, allGroupings, "---end segment---"])
    
    def __repr__(self):
        return str(self)

    def transcribe(self):
        bt = text.BrailleText(self.maxLineLength, self.showHand)
        self.allGroupingKeys = sorted(self.keys())
        
        # Heading
        # -------
        try:
            bt.addElement(heading = self.extractHeading())
        except basic.BrailleBasicException as bbe:
            if not bbe.args[0] == "No heading can be made.":
                raise bbe

        # Measure Number
        # --------------
        if self.showFirstMeasureNumber:
            bt.addElement(measureNumber = self.getMeasureNumber())
        
        # Dummy Rests
        # -----------
        if self.dummyRestLength is not None:
            dummyRests = [self.dummyRestLength * lookup.rests['dummy']]
            bt.addElement(keyOrTimeSig = u"".join(dummyRests), withHyphen = False)

        # Everything else
        # ---------------
        while True:
            try:
                self.previousGroupingKey = self.currentGroupingKey
                self.currentGroupingKey = self.allGroupingKeys.pop(0)
                # Note Grouping
                # -------------
                if self.currentGroupingKey % 10 == 9:
                    self.extractNoteGrouping(bt)
                # In Accord Grouping
                # ------------------
                if self.currentGroupingKey % 10 == 8:
                    bt.addElement(inaccord=self.extractInaccords())
                # Signature(s) Grouping
                # ---------------------
                if self.currentGroupingKey % 10 == 3:
                    withHyphen = False
                    if self.previousGroupingKey is not None and (self.currentGroupingKey - self.previousGroupingKey) == 4:
                        withHyphen = True
                    try:
                        bt.addElement(keyOrTimeSig = self.extractSignatures(), withHyphen = withHyphen)
                    except basic.BrailleBasicException as bbe:
                        if not bbe.args[0] == "No key or time signature to transcribe!":
                            raise bbe
                # Long Expression(s) Grouping
                # ---------------------------
                if self.currentGroupingKey % 10 == 7:
                    brailleExpr = self.extractLongExpression()
                    if not self.currentGroupingKey % 100 == 7:
                        bt.addElement(longExpression = brailleExpr, withHyphen = True)
                    else:
                        bt.addElement(longExpression = brailleExpr, withHyphen = False)
                # Tempo Text Grouping
                # -------------------
                if self.currentGroupingKey % 10 == 4:
                    self.allGroupingKeys.insert(0, self.currentGroupingKey)
                    if self.previousGroupingKey % 10 == 3:
                        self.allGroupingKeys.insert(0, self.previousGroupingKey)
                    bt.addElement(heading = self.extractHeading())
                    bt.addElement(measureNumber = self.getMeasureNumber())
            except IndexError as ie:
                if ie.args[0] == "pop from empty list":
                    break
                raise ie

        return bt

    def extractHeading(self):   
        keySignature = None
        timeSignature = None
        tempoText = None
        metronomeMark = None
        
        while True:
            try:
                if self.allGroupingKeys[0] % 10 > 5:
                    break
            except TypeError as te:
                if te.args[0] == "'NoneType' object is not subscriptable":
                    self.allGroupingKeys = sorted(self.keys())
                    return self.extractHeading()
            self.currentGroupingKey = self.allGroupingKeys.pop(0)
            if self.currentGroupingKey % 10 == 3:
                try:
                    keySignature, timeSignature = self.get(self.currentGroupingKey)[0], self.get(self.currentGroupingKey)[1]
                except IndexError:
                    keyOrTimeSig = self.get(self.currentGroupingKey)[0]
                    if isinstance(keyOrTimeSig, key.KeySignature):
                        keySignature = keyOrTimeSig
                    else:
                        timeSignature = keyOrTimeSig
            elif self.currentGroupingKey % 10 == 4:
                tempoText = self.get(self.currentGroupingKey)[0]
            elif self.currentGroupingKey % 10 == 5:
                metronomeMark = self.get(self.currentGroupingKey)[0]

        brailleHeading = basic.transcribeHeading(keySignature, timeSignature, tempoText, metronomeMark, self.maxLineLength)
        return brailleHeading

    def getMeasureNumber(self):
        initMeasureNumber = self.allGroupingKeys[0] / 100
        return basic.numberToBraille(initMeasureNumber)

    def extractSignatures(self):
        keySignature = None
        timeSignature = None
        try:
            keySignature, timeSignature = self.get(self.currentGroupingKey)[0], self.get(self.currentGroupingKey)[1]
        except IndexError:
            keyOrTimeSig = self.get(self.currentGroupingKey)[0]
            if isinstance(keyOrTimeSig, key.KeySignature):
                keySignature = keyOrTimeSig
            else:
                timeSignature = keyOrTimeSig
        
        outgoingKeySig = None
        if self.cancelOutgoingKeySig and not keySignature is None:
            outgoingKeySig = keySignature.outgoingKeySig
        
        brailleSig = basic.transcribeSignatures(keySignature, timeSignature, outgoingKeySig)
        return brailleSig

    def extractLongExpression(self):
        longExpr = self.get(self.currentGroupingKey)[0]
        return basic.textExpressionToBraille(longExpr)

    def extractNoteGrouping(self, brailleText):
        noteGrouping = self.get(self.currentGroupingKey)
        allNotes = [n for n in noteGrouping if isinstance(n, note.Note)]
        withHyphen = False
        if self.previousGroupingKey is not None:
            if (self.currentGroupingKey - self.previousGroupingKey) == 10:
                withHyphen = True
                self.lastNote = None
            if self.previousGroupingKey % 10 != 9:
                self.lastNote = None
        if len(allNotes) > 0:
            if self.lastNote is not None:
                firstNote = allNotes[0]
                self.showLeadingOctave = basic.showOctaveWithNote(self.lastNote, firstNote)
            elif not self.isFirstNoteGrouping:
                self.showLeadingOctave = True
            self.lastNote = allNotes[-1]
        try:
            brailleNoteGrouping = transcribeNoteGrouping(noteGrouping, self.showLeadingOctave)
            brailleText.addElement(noteGrouping = brailleNoteGrouping,\
                          showLeadingOctave = self.showLeadingOctave, withHyphen = withHyphen)
        except text.BrailleTextException as bte:
            if bte.args[0] == "Recalculate Note Grouping With Leading Octave":
                self.showLeadingOctave = True
                brailleNoteGrouping = transcribeNoteGrouping(noteGrouping, self.showLeadingOctave)
                brailleText.addElement(noteGrouping = brailleNoteGrouping,\
                               showLeadingOctave = self.showLeadingOctave, withHyphen = withHyphen)
            elif bte.args[0] == "Split Note Grouping":
                isSolved = False
                bdo = 0
                while not isSolved:
                    (sngA, sngB) = splitNoteGrouping(noteGrouping, beatDivisionOffset = bdo)
                    brailleNoteGroupingA = transcribeNoteGrouping(sngA, self.showLeadingOctave)
                    try:
                        brailleText.addElement(noteGrouping = brailleNoteGroupingA,\
                                       showLeadingOctave = self.showLeadingOctave, withHyphen = withHyphen)
                    except text.BrailleTextException:
                        bdo += 1
                        continue
                    self.showLeadingOctave = True
                    brailleNoteGroupingB = transcribeNoteGrouping(sngB, self.showLeadingOctave)
                    brailleText.addElement(noteGrouping = brailleNoteGroupingB,\
                                            showLeadingOctave = True, withHyphen = True, forceHyphen=True)
                    isSolved = True
        self.isFirstNoteGrouping = False
    
    def extractInaccords(self):
        inaccords = self.get(self.currentGroupingKey)
        return symbols['full_inaccord'].join([transcribeVoice(vc) for vc in inaccords])

#-------------------------------------------------------------------------------

def findSegments(music21Part, **partKeywords):
    # Slurring
    # --------
    slurLongPhraseWithBrackets = True
    showShortSlursAndTiesTogether, showLongSlursAndTiesTogether = False, False

    if 'slurLongPhraseWithBrackets' in partKeywords:
        slurLongPhraseWithBrackets = partKeywords['slurLongPhraseWithBrackets']
    if 'showShortSlursAndTiesTogether' in partKeywords:
        showShortSlursAndTiesTogether = partKeywords['showShortSlursAndTiesTogether']
    if 'showLongSlursAndTiesTogether' in partKeywords:
        showLongSlursAndTiesTogether = partKeywords['showLongSlursAndTiesTogether']
    else:
        if slurLongPhraseWithBrackets:
            showLongSlursAndTiesTogether = True
            
    prepareSlurredNotes(music21Part, slurLongPhraseWithBrackets, showShortSlursAndTiesTogether, showLongSlursAndTiesTogether)

    # Raw Segments
    # ------------
    segmentBreaks = None
    if 'segmentBreaks' in partKeywords:
        segmentBreaks = partKeywords['segmentBreaks']
    allSegments = getRawSegments(music21Part, segmentBreaks)
    
    # Grouping Attributes
    # -------------------
    addGroupingAttributes(allSegments, music21Part, **partKeywords)
    
    # Segment Attributes
    # ------------------
    addSegmentAttributes(allSegments, music21Part, **partKeywords)

    # Articulations
    # -------------
    fixArticulations(allSegments)
    
    return allSegments

#                 music21Class        affinityCode    classSortOrder
affinityCodes = [(note.Note,            9,                   10),
                 (note.Rest,            9,                   10),
                 (chord.Chord,          9,                   10),
                 (dynamics.Dynamic,     9,                    9),
                 (clef.Clef,            9,                    7),
                 (bar.Barline,          9.5,                  0),
                 (key.KeySignature,     3,                    1),
                 (meter.TimeSignature,  3,                    2),
                 (tempo.TempoText,      4,                    3),
                 (tempo.MetronomeMark,  5,                    4),
                 (stream.Voice,         8,                   10)]

def setAffinityCode(music21Object):
    for (music21Class, code, sortOrder) in affinityCodes:
        if isinstance(music21Object, music21Class):
            music21Object.affinityCode = code
            music21Object.classSortOrder = sortOrder
            return
    
    if isinstance(music21Object, expressions.TextExpression):
        music21Object.affinityCode = 9
        if len(music21Object.content.split()) > 1:
            music21Object.affinityCode = 7
        music21Object.classSortOrder = 8
        return

    raise BrailleSegmentException("{0} cannot be transcribed to braille.".format(music21Object))

excludeClasses = [spanner.Slur, layout.SystemLayout, layout.PageLayout]

def extractBrailleElements(music21Measure):
    allElements = BrailleElementGrouping()
    for music21Object in music21Measure:
        try:
            setAffinityCode(music21Object)
            allElements.append(music21Object)
        except BrailleSegmentException as notSupportedException:
            isExempt = [isinstance(music21Object, music21Class) for music21Class in excludeClasses]
            if isExempt.count(True) == 0:
                environRules.warn("{0}".format(notSupportedException))

    allElements.sort(cmp = lambda x, y: cmp(x.offset, y.offset) or cmp(x.classSortOrder, y.classSortOrder))
    if len(allElements) >= 2 and isinstance(allElements[-1], dynamics.Dynamic):
        if isinstance(allElements[-2], bar.Barline):
            allElements[-1].classSortOrder = -1
            allElements.sort(cmp = lambda x, y: cmp(x.offset, y.offset) or cmp(x.classSortOrder, y.classSortOrder))
            
    return allElements

def getRawSegments(music21Part, segmentBreaks=None):
    allSegments = []
    mnStart = 10E5
    offsetStart = 0.0
    if not segmentBreaks == None:
        segmentIndex = 0
        (mnStart, offsetStart) = segmentBreaks[segmentIndex]
    currentSegment = BrailleSegment()
    for music21Measure in music21Part.getElementsByClass(['Measure', 'Voice']):
        prepareBeamedNotes(music21Measure)
        brailleElements = extractBrailleElements(music21Measure)
        offsetFactor = 0
        previousCode = -1
        for brailleElement in brailleElements:
            if (music21Measure.number > mnStart or\
                music21Measure.number == mnStart and brailleElement.offset >= offsetStart):
                if offsetStart != 0.0:
                    currentSegment.isHyphenated = True
                allSegments.append(currentSegment)
                currentSegment = BrailleSegment()
                try:
                    segmentIndex += 1
                    (mnStart, offsetStart) = segmentBreaks[segmentIndex]
                except IndexError:
                    (mnStart, offsetStart) = (10E5, 0.0)
            if brailleElement.affinityCode < previousCode:
                offsetFactor += 1
            bucketNumber = music21Measure.number * 100 +  offsetFactor * 10 + int(brailleElement.affinityCode)
            currentSegment[bucketNumber].append(brailleElement)
            previousCode = brailleElement.affinityCode
    allSegments.append(currentSegment)
    return allSegments

def addSegmentAttributes(allSegments, music21Part, **partKeywords):        
    for brailleSegment in allSegments:
        if 'cancelOutgoingKeySig' in partKeywords:
            brailleSegment.cancelOutgoingKeySig = partKeywords['cancelOutgoingKeySig']
        if 'dummyRestLength' in partKeywords:
            brailleSegment.dummyRestLength = partKeywords['dummyRestLength']
        if 'maxLineLength' in partKeywords:
            brailleSegment.maxLineLength = partKeywords['maxLineLength']
        if 'showFirstMeasureNumber' in partKeywords:
            brailleSegment.showFirstMeasureNumber = partKeywords['showFirstMeasureNumber']
        if 'showHand' in partKeywords:
            brailleSegment.showHand = partKeywords['showHand']
        if 'showHeading' in partKeywords:
            brailleSegment.showHeading = partKeywords['showHeading']
        if 'showLeadingOctave' in partKeywords:
            brailleSegment.showLeadingOctave = partKeywords['showLeadingOctave']  
    return

def addGroupingAttributes(allSegments, music21Part, **partKeywords):
    currentKeySig = key.KeySignature(0)
    try:
        currentTimeSig = music21Part.getElementsByClass(['Measure','Voice'])[0].bestTimeSignature()
    except stream.StreamException:
        currentTimeSig = meter.TimeSignature('4/4')

    descendingChords = None
    showClefSigns = False
    upperFirstInNoteFingering = True

    if 'showClefSigns' in partKeywords:
        showClefSigns = partKeywords['showClefSigns']
    if 'upperFirstInNoteFingering' in partKeywords:
        upperFirstInNoteFingering = partKeywords['upperFirstInNoteFingering']
    if 'showHand' in partKeywords:
        if partKeywords['showHand'] == 'left':
            descendingChords = False
        elif partKeywords['showHand'] == 'right':
            descendingChords = True
    if descendingChords is None:
        try:
            bc = music21Part.getElementsByClass(['Measure','Voice'])[0].getClefs()[0]
            descendingChords = False
            if isinstance(bc, clef.TrebleClef) or isinstance(bc, clef.AltoClef):
                descendingChords = True
        except stream.StreamException:
            descendingChords = True
            
    for brailleSegment in allSegments:
        for (groupingKey, groupingList) in sorted(brailleSegment.items()):
            if groupingKey % 10 == 3:
                for brailleElement in groupingList:
                    if isinstance(brailleElement, meter.TimeSignature):
                        currentTimeSig = brailleElement
                    elif isinstance(brailleElement, key.KeySignature):
                        brailleElement.outgoingKeySig = currentKeySig
                        currentKeySig = brailleElement
            elif groupingKey % 10 == 9:
                groupingList.keySignature = currentKeySig
                groupingList.timeSignature = currentTimeSig
                groupingList.descendingChords = descendingChords
                groupingList.showClefSigns = showClefSigns
                groupingList.upperFirstInNoteFingering = upperFirstInNoteFingering
                allGeneralNotes = [n for n in groupingList if isinstance(n, note.GeneralNote)]
                if len(allGeneralNotes) == 1 and isinstance(allGeneralNotes[0], note.Rest):
                    if allGeneralNotes[0].quarterLength == currentTimeSig.totalLength:
                        allGeneralNotes[0].quarterLength = 4.0
            elif groupingKey % 10 == 8:
                groupingList.timeSignature = currentTimeSig
    return

def fixArticulations(allSegments):
    for brailleSegment in allSegments:
        newSegment = consolidateSegment(brailleSegment)
        for noteGrouping in [newSegment[gpKey] for gpKey in newSegment.keys() if gpKey % 10 == 9]:
            allNotes = [n for n in noteGrouping if isinstance(n,note.Note)]
            for noteIndexStart in range(len(allNotes)):
                music21NoteStart = allNotes[noteIndexStart]
                for artc in music21NoteStart.articulations:
                    if isinstance(artc, articulations.Staccato) or isinstance(artc, articulations.Tenuto):
                        if not music21NoteStart.tie == None:
                            if music21NoteStart.tie.type == 'stop':
                                allNotes[noteIndexStart-1].tie = None
                                allNotes[noteIndexStart-1].shortSlur = True
                            else:
                                allNotes[noteIndexStart+1].tie = None
                                music21NoteStart.shortSlur = True
                            music21NoteStart.tie = None
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
    return

def consolidateSegment(brailleSegment):
    newSegment = BrailleSegment()
    pngKey = None
    for (groupingKey, groupingList) in sorted(brailleSegment.items()):
        if groupingKey % 10 != 9:
            newSegment[groupingKey] = groupingList
            pngKey = None
        else:
            if pngKey == None:
                pngKey = groupingKey
            for item in groupingList:
                newSegment[pngKey].append(item)
    return newSegment
    
#-------------------------------------------------------------------------------
# Segment Transcription Methods

def transcribeNoteGrouping(brailleElements, showLeadingOctave = True):
    trans = []
    previousNote = None
    previousElement = None
    for brailleElement in brailleElements:
        if isinstance(brailleElement, note.Note):
            currentNote = brailleElement
            if previousNote == None:
                doShowOctave = showLeadingOctave
            else:
                doShowOctave = basic.showOctaveWithNote(previousNote, currentNote)
            trans.append(basic.noteToBraille(currentNote, showOctave = doShowOctave, upperFirstInFingering = brailleElements.upperFirstInNoteFingering))
            previousNote = currentNote
        elif isinstance(brailleElement, note.Rest):
            currentRest = brailleElement
            trans.append(basic.restToBraille(currentRest))
        elif isinstance(brailleElement, chord.Chord):
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
        elif isinstance(brailleElement, dynamics.Dynamic):
            currentDynamic = brailleElement
            trans.append(basic.dynamicToBraille(currentDynamic))
            previousNote = None
            showLeadingOctave = True
        elif isinstance(brailleElement, expressions.TextExpression):
            currentExpression = brailleElement
            trans.append(basic.textExpressionToBraille(currentExpression))
            previousNote = None
            showLeadingOctave = True
        elif isinstance(brailleElement, bar.Barline):
            currentBarline = brailleElement
            trans.append(basic.barlineToBraille(currentBarline))
        elif isinstance(brailleElement, clef.Clef):
            if brailleElements.showClefSigns:
                currentClef = brailleElement
                trans.append(basic.clefToBraille(currentClef))
                previousNote = None
                showLeadingOctave = True
        else:
            raise BrailleSegmentException("Unknown Note Grouping Element")
        if not previousElement == None:
            if brailleElements.showClefSigns and isinstance(previousElement, clef.Clef) or\
               isinstance(previousElement, dynamics.Dynamic) and\
                not isinstance(brailleElement, dynamics.Dynamic) and not isinstance(brailleElement, expressions.TextExpression):
                for dots in binary_dots[trans[-1][0]]:
                    if (dots == '10' or dots == '11'):
                        trans.insert(-1, symbols['dot'])
                        break
            elif isinstance(previousElement, expressions.TextExpression) and\
                not isinstance(brailleElement, dynamics.Dynamic) and not isinstance(brailleElement, expressions.TextExpression):
                if not previousElement.content[-1] == '.': # abbreviation, no extra dot 3 necessary
                    for dots in binary_dots[trans[-1][0]]:
                        if (dots == '10' or dots == '11'):
                            trans.insert(-1, symbols['dot'])
                            break
        previousElement = brailleElement
        
    return u"".join(trans)

def transcribeVoice(music21Voice):
    music21Part = stream.Part()
    music21Measure = stream.Measure()
    for brailleElement in music21Voice:
        music21Measure.append(brailleElement)
    music21Part.append(music21Measure)
    music21Measure.number = music21Voice.measureNumber
    allSegments = findSegments(music21Part, showHeading=False, showFirstMeasureNumber=False)
    allTrans = []
    for brailleElementSegment in allSegments:
        segmentTranscription = brailleElementSegment.transcribe()
        allTrans.append(str(segmentTranscription))
    return u"\n".join(allTrans)

#-------------------------------------------------------------------------------
# Helper Methods

# Splits a note grouping
def splitNoteGrouping(noteGrouping, value = 2, beatDivisionOffset = 0):
    music21Measure = stream.Measure()
    for brailleElement in noteGrouping:
        music21Measure.insert(brailleElement.offset, brailleElement)
    newMeasures = splitMeasure(music21Measure, value, beatDivisionOffset, noteGrouping.timeSignature)
    
    leftBrailleElements = BrailleElementGrouping()
    for brailleElement in newMeasures[0]:
        leftBrailleElements.append(brailleElement)
    leftBrailleElements.__dict__ = noteGrouping.__dict__.copy()

    rightBrailleElements = BrailleElementGrouping()
    for brailleElement in newMeasures[1]:
        rightBrailleElements.append(brailleElement)
    rightBrailleElements.__dict__ = noteGrouping.__dict__.copy()

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