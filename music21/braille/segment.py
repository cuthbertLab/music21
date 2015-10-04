# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         segment.py
# Purpose:      Division of stream.Part into segments for individual handling
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    Copyright © 2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

"""
Inner classes and methods for transcribing musical segments into braille.


This module was made in consultation with the manual "Introduction to Braille 
Music Transcription, Second Edition" by Mary Turner De Garmo, 2005. It is
available from the Library of Congress `here <http://www.loc.gov/nls/music/>`_,
and will henceforth be referred to as BMTM.
"""

from music21 import bar
from music21 import chord
from music21 import clef
from music21 import dynamics
from music21 import expressions
from music21 import exceptions21
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

from music21.common import opFrac

try:  # gives Py2 the zip of Py3
    from future_builtins import zip
except ImportError:
    pass

import collections
import copy
import unittest


symbols = lookup.symbols

from music21 import environment
environRules = environment.Environment('segment.py')

AFFINITY_SIGNATURE = 3
AFFINITY_TTEXT = 4
AFFINITY_MMARK = 5
AFFINITY_LONG_TEXTEXPR = 7
AFFINITY_INACCORD = 8
AFFINITY_NOTEGROUP = 9
AFFINITY_BARLINE = 9.5
AFFINITY_SPLIT1_NOTEGROUP = 8.5
AFFINITY_SPLIT2_NOTEGROUP = 9.5

CSO_NOTE = 10
CSO_REST = 10
CSO_CHORD = 10
CSO_DYNAMIC = 9
CSO_CLEF = 7
CSO_BARLINE = 0
CSO_KEYSIG = 1
CSO_TIMESIG = 2
CSO_TTEXT = 3
CSO_MMARK = 4
CSO_VOICE = 10

# (music21Object, affinity code, class sort order)
affinityCodes = [(note.Note,            AFFINITY_NOTEGROUP,   CSO_NOTE),
                 (note.Rest,            AFFINITY_NOTEGROUP,   CSO_REST),
                 (chord.Chord,          AFFINITY_NOTEGROUP,   CSO_CHORD),
                 (dynamics.Dynamic,     AFFINITY_NOTEGROUP,   CSO_DYNAMIC),
                 (clef.Clef,            AFFINITY_NOTEGROUP,   CSO_CLEF),
                 (bar.Barline,          AFFINITY_BARLINE,     CSO_BARLINE),
                 (key.KeySignature,     AFFINITY_SIGNATURE,   CSO_KEYSIG),
                 (meter.TimeSignature,  AFFINITY_SIGNATURE,   CSO_TIMESIG),
                 (tempo.TempoText,      AFFINITY_TTEXT,       CSO_TTEXT),
                 (tempo.MetronomeMark,  AFFINITY_MMARK,       CSO_MMARK),
                 (stream.Voice,         AFFINITY_INACCORD,    CSO_VOICE)]

affinityNames = {AFFINITY_SIGNATURE: "Signature Grouping",
                 AFFINITY_TTEXT: "Tempo Text Grouping",
                 AFFINITY_MMARK: "Metronome Mark Grouping",
                 AFFINITY_LONG_TEXTEXPR: "Long Text Expression Grouping",
                 AFFINITY_INACCORD: "Inaccord Grouping",
                 AFFINITY_NOTEGROUP: "Note Grouping",
                 AFFINITY_SPLIT1_NOTEGROUP: "Split Note Grouping",
                 AFFINITY_SPLIT2_NOTEGROUP: "Split Note Grouping"}

excludeFromBrailleElements = [spanner.Slur, layout.SystemLayout, layout.PageLayout, layout.StaffLayout]

GROUPING_GLOBALS = {'keySignature': 0,
                    'timeSignature': '4/4'}
GROUPING_DESC_CHORDS = True
GROUPING_SHOW_CLEFS = False
GROUPING_UPPERFIRST_NOTEFINGERING = True
GROUPING_WITHHYPHEN = False
GROUPING_NUMREPEATS = 0

SEGMENT_CANCEL_OUTGOINGKEYSIG = True
SEGMENT_DUMMYRESTLENGTH = None
SEGMENT_MAXLINELENGTH = 40
SEGMENT_SHOWFIRSTMEASURENUMBER = True
SEGMENT_SHOWHAND = None
SEGMENT_SHOWHEADING = True
SEGMENT_SUPPRESSOCTAVEMARKS = False
SEGMENT_ENDHYPHEN = False
SEGMENT_MEASURENUMBERWITHDOT = False

SEGMENT_SLURLONGPHRASEWITHBRACKETS = True
SEGMENT_SHOWSHORTSLURSANDTIESTOGETHER = False
SEGMENT_SHOWLONGSLURSANDTIESTOGETHER = False
SEGMENT_SEGMENTBREAKS=[]

#-------------------------------------------------------------------------------

class BrailleElementGrouping(list):
    _DOC_ATTR = {'keySignature': 'The last :class:`~music21.key.KeySignature` preceding the grouping.',
                 'timeSignature': 'The last :class:`~music21.meter.TimeSignature` preceding the grouping.',
                 'descendingChords': 'True if a :class:`~music21.chord.Chord` should be spelled from highest to lowest pitch\
                 in braille, False if the opposite is the case.',
                 'showClefSigns' : 'If true, clef signs are shown in braille. Representation of music in braille is not\
                 dependent upon clefs and staves, so the clef signs would be displayed for referential or historical purposes.',
                 'upperFirstInNoteFingering' : 'No documentation.',
                 'withHyphen': 'If True, this grouping will end with a music hyphen.',
                 'numRepeats': 'The number of times this grouping is repeated.'}
    def __init__(self):
        """
        Intended to be a list of objects which should be displayed
        without a space in braille.
        
        >>> from music21.braille import segment
        >>> bg = segment.BrailleElementGrouping()
        >>> bg.append(note.Note("C4"))
        >>> bg.append(note.Note("D4"))
        >>> bg.append(note.Rest())
        >>> bg.append(note.Note("F4"))
        >>> bg
        <music21.note.Note C>
        <music21.note.Note D>
        <music21.note.Rest rest>
        <music21.note.Note F>
        """
        list.__init__(self)

        if GROUPING_GLOBALS['keySignature'] == None:
            GROUPING_GLOBALS['keySignature'] = key.KeySignature(0)
        if GROUPING_GLOBALS['timeSignature'] == None:
            GROUPING_GLOBALS['timeSignature'] = meter.TimeSignature('4/4')
        

        self.keySignature = GROUPING_GLOBALS['keySignature']
        self.timeSignature = GROUPING_GLOBALS['timeSignature']
        self.descendingChords = GROUPING_DESC_CHORDS
        self.showClefSigns = GROUPING_SHOW_CLEFS
        self.upperFirstInNoteFingering = GROUPING_UPPERFIRST_NOTEFINGERING
        self.withHyphen = GROUPING_WITHHYPHEN
        self.numRepeats = GROUPING_NUMREPEATS
    
    def __str__(self):
        allObjects = []
        for obj in self:
            if isinstance(obj, stream.Voice):
                for obj2 in obj:
                    try:
                        allObjects.append(u"\n".join(obj2._brailleEnglish))
                    except (AttributeError, TypeError):
                        allObjects.append(str(obj2))
            else:
                try:
                    allObjects.append(u"\n".join(obj._brailleEnglish))
                except (AttributeError, TypeError):
                    allObjects.append(str(obj))
        if self.numRepeats > 0:
            allObjects.append(u"** Grouping x {0} **".format(self.numRepeats+1))
        if self.withHyphen is True:
            allObjects.append(u"** Music Hyphen **")
        return u"\n".join(allObjects)
        
    def __repr__(self):
        return str(self)
    
class BrailleSegment(collections.defaultdict):
    _DOC_ATTR = {'cancelOutgoingKeySig': 'If True, the previous key signature should be cancelled immediately before a new key signature is encountered.',
                 'dummyRestLength': 'For a given positive integer n, adds n "dummy rests" near the beginning of a segment. Designed for test purposes, as they\
                 are used to demonstrate measure division at the end of braille lines.',
                 'maxLineLength': 'The maximum amount of braille characters that should be present in a line. The standard is 40 characters.',
                 'showFirstMeasureNumber': 'If True, then a measure number is shown following the heading (if applicable) and preceding the music.',
                 'showHand': 'If set to "right" or "left", shows the corresponding hand sign at the beginning of the first line.',
                 'showHeading': 'If True, then a braille heading is displayed. See :meth:`~music21.braille.basic.transcribeHeading` for more details on headings.',
                 'suppressOctaveMarks': 'If True, then all octave marks are suppressed. Designed for test purposes, as octave marks were not presented\
                 until Chapter 7 of BMTM.',
                 'endHyphen': 'If True, then the last :class:`~music21.braille.segment.BrailleElementGrouping` of this segment will be followed by a music hyphen.\
                 The last grouping is incomplete, because a segment break occured in the middle of a measure.',
                 'measureNumberWithDot': 'If True, then the initial measure number of this segment should be followed by a dot. This segment\
                 is starting in the middle of a measure.'}
    def __init__(self):
        """
        A segment is "a group of measures occupying more than one braille line." 
        Music is divided into segments so as to "present the music to the reader 
        in a meaningful manner and to give him convenient reference points to 
        use in memorization" (BMTM, 71).
        """
        super(BrailleSegment, self).__init__(BrailleElementGrouping)
        self._allGroupingKeys = None
        self._currentGroupingKey = None
        self._lastNote = None
        self._previousGroupingKey = None
        self.cancelOutgoingKeySig = SEGMENT_CANCEL_OUTGOINGKEYSIG
        self.dummyRestLength = SEGMENT_DUMMYRESTLENGTH
        self.maxLineLength = SEGMENT_MAXLINELENGTH
        self.showFirstMeasureNumber = SEGMENT_SHOWFIRSTMEASURENUMBER
        self.showHand = SEGMENT_SHOWHAND
        self.showHeading = SEGMENT_SHOWHEADING
        self.suppressOctaveMarks = SEGMENT_SUPPRESSOCTAVEMARKS
        self.endHyphen = SEGMENT_ENDHYPHEN
        self.measureNumberWithDot = SEGMENT_MEASURENUMBERWITHDOT
        
    def __str__(self):
        name = "<music21.braille.segment BrailleSegment>"
        allItems = sorted(self.items())
        allKeys = []
        allGroupings = []
        prevKey = None
        for (itemKey, grouping) in allItems:
            try:
                if prevKey % 10 == AFFINITY_SPLIT1_NOTEGROUP:
                    prevKey = itemKey
                    continue
            except TypeError:
                pass
            allKeys.append("Measure {0}, {1} {2}:\n".format(int(itemKey//100),
                affinityNames[itemKey%10], int(itemKey%100)//10 + 1))
            allGroupings.append(str(grouping))
            prevKey = itemKey
        allElementGroupings = u"\n".join([u"".join([k, g, "\n==="])
                                          for (k,g) in list(zip(allKeys, allGroupings))])
        return u"\n".join(["---begin segment---", name, allElementGroupings, "---end segment---"])
    
    def __repr__(self):
        return str(self)

    def transcribe(self):
        """
        Heading (if applicable)
        Measure Number
        Rest of Note Groupings
        """
        bt = text.BrailleText(self.maxLineLength, self.showHand)
        self._allGroupingKeys = sorted(self.keys())
        
        if self.showHeading:
            self.extractHeading(bt) # Heading
        if self.showFirstMeasureNumber:
            self.addMeasureNumber(bt) # Measure Number
        if self.dummyRestLength is not None:
            self.addDummyRests(bt) # Dummy Rests

        while self._allGroupingKeys:
            self._previousGroupingKey = self._currentGroupingKey
            self._currentGroupingKey = self._allGroupingKeys.pop(0)

            if self._currentGroupingKey % 10 == AFFINITY_NOTEGROUP:
                self.extractNoteGrouping(bt) # Note Grouping
            elif self._currentGroupingKey % 10 == AFFINITY_SIGNATURE:
                self.extractSignatureGrouping(bt) # Signature(s) Grouping
            elif self._currentGroupingKey % 10 == AFFINITY_LONG_TEXTEXPR:
                self.extractLongExpressionGrouping(bt) # Long Expression(s) Grouping
            elif self._currentGroupingKey % 10 == AFFINITY_INACCORD:
                self.extractInaccordGrouping(bt) # In Accord Grouping
            elif self._currentGroupingKey % 10 == AFFINITY_TTEXT:
                self.extractTempoTextGrouping(bt) # Tempo Text Grouping

        return bt

    def addDummyRests(self, brailleText):
        dummyRests = [self.dummyRestLength * lookup.rests['dummy']]
        brailleText.addElement(keyOrTimeSig = u"".join(dummyRests))

    def addMeasureNumber(self, brailleText):
        """
        Takes in a braille text instance and adds a measure number 
        """
        if self.measureNumberWithDot:
            brailleText.addElement(measureNumber = self._getMeasureNumber(withDot=True))
        else:
            brailleText.addElement(measureNumber = self._getMeasureNumber())

    def consolidate(self):
        """
        TODO: define this method
        """
        newSegment = BrailleSegment()
        pngKey = None
        for (groupingKey, groupingList) in sorted(self.items()):
            if groupingKey % 10 != AFFINITY_NOTEGROUP:
                newSegment[groupingKey] = groupingList
                pngKey = None
            else:
                if pngKey is None:
                    pngKey = groupingKey
                for item in groupingList:
                    newSegment[pngKey].append(item)
        return newSegment

    def extractHeading(self, brailleText):
        """
        Extract a :class:`~music21.key.KeySignature`, :class:`~music21.meter.TimeSignature,
        :class:`~music21.tempo.TempoText` and :class:`~music21.tempo.MetronomeMark` and
        add an appropriate braille heading to the brailleText object inputted.    
        """
        keySignature = None
        timeSignature = None
        tempoText = None
        metronomeMark = None
        
        while True:
            try:
                if self._allGroupingKeys[0] % 10 > AFFINITY_MMARK:
                    break
            except TypeError as te:
                if te.args[0] == "'NoneType' object is not subscriptable":
                    self._allGroupingKeys = sorted(self.keys())
                    return self.extractHeading(brailleText)
            self._currentGroupingKey = self._allGroupingKeys.pop(0)
            if self._currentGroupingKey % 10 == AFFINITY_SIGNATURE:
                try:
                    keySignature, timeSignature = self.get(
                        self._currentGroupingKey)[0], self.get(self._currentGroupingKey)[1]
                except IndexError:
                    keyOrTimeSig = self.get(self._currentGroupingKey)[0]
                    if isinstance(keyOrTimeSig, key.KeySignature):
                        keySignature = keyOrTimeSig
                    else:
                        timeSignature = keyOrTimeSig
            elif self._currentGroupingKey % 10 == AFFINITY_TTEXT:
                tempoText = self.get(self._currentGroupingKey)[0]
            elif self._currentGroupingKey % 10 == AFFINITY_MMARK:
                metronomeMark = self.get(self._currentGroupingKey)[0]

        try:
            brailleHeading = basic.transcribeHeading(keySignature, timeSignature,
                tempoText, metronomeMark, self.maxLineLength)
            brailleText.addElement(heading = brailleHeading)
        except basic.BrailleBasicException as bbe:
            if not bbe.args[0] == "No heading can be made.":
                raise bbe
            
    def extractInaccordGrouping(self, brailleText):
        inaccords = self.get(self._currentGroupingKey)
        voice_trans = []
        for music21Voice in inaccords:
            noteGrouping = extractBrailleElements(music21Voice)
            noteGrouping.descendingChords = inaccords.descendingChords
            noteGrouping.showClefSigns = inaccords.showClefSigns
            noteGrouping.upperFirstInNoteFingering = inaccords.upperFirstInNoteFingering
            voice_trans.append(basic.transcribeNoteGrouping(noteGrouping))
        brailleInaccord = symbols['full_inaccord'].join(voice_trans)
        brailleText.addElement(inaccord=brailleInaccord)

    def extractLongExpressionGrouping(self, brailleText):
        longExpr = basic.textExpressionToBraille(self.get(self._currentGroupingKey)[0])
        if not self._currentGroupingKey % 100 == AFFINITY_LONG_TEXTEXPR:
            brailleText.addElement(longExpression = longExpr)
        else:
            brailleText.addElement(longExpression = longExpr)

    def extractNoteGrouping(self, brailleText):
        noteGrouping = self.get(self._currentGroupingKey)
        allNotes = [n for n in noteGrouping if isinstance(n, note.Note)]
        if self._previousGroupingKey is not None:
            if (self._currentGroupingKey - self._previousGroupingKey) == 10 or self._previousGroupingKey % 10 != AFFINITY_NOTEGROUP:
                self._lastNote = None
        showLeadingOctave = True
        if allNotes:
            if not self.suppressOctaveMarks:
                if self._lastNote is not None:
                    firstNote = allNotes[0]
                    showLeadingOctave = basic.showOctaveWithNote(self._lastNote, firstNote)
            else:
                showLeadingOctave = False
            self._lastNote = allNotes[-1]
        else:
            if self.suppressOctaveMarks:
                showLeadingOctave = False
        try:
            brailleNoteGrouping = basic.transcribeNoteGrouping(noteGrouping, showLeadingOctave)
            brailleText.addElement(noteGrouping = brailleNoteGrouping,
                showLeadingOctave = showLeadingOctave, withHyphen = noteGrouping.withHyphen)
        except text.BrailleTextException as bte:
            if bte.args[0] == "Recalculate Note Grouping With Leading Octave":
                showLeadingOctave = True
                if self.suppressOctaveMarks:
                    showLeadingOctave = False  
                brailleNoteGrouping = basic.transcribeNoteGrouping(noteGrouping, showLeadingOctave)
                brailleText.addElement(noteGrouping = brailleNoteGrouping,
                    showLeadingOctave = True, withHyphen = noteGrouping.withHyphen)
            elif bte.args[0] == "Split Note Grouping":
                isSolved = False
                bdo = 0
                while not isSolved:
                    (sngA, sngB) = splitNoteGrouping(noteGrouping, beatDivisionOffset = bdo)
                    brailleNoteGroupingA = basic.transcribeNoteGrouping(sngA, showLeadingOctave)
                    try:
                        brailleText.addElement(noteGrouping = brailleNoteGroupingA,
                            showLeadingOctave = showLeadingOctave, withHyphen = True)
                    except text.BrailleTextException:
                        bdo += 1
                        continue
                    showLeadingOctave = True
                    if self.suppressOctaveMarks:
                        showLeadingOctave = False
                    brailleNoteGroupingB = basic.transcribeNoteGrouping(sngB, showLeadingOctave)
                    try:
                        brailleText.addElement(noteGrouping = brailleNoteGroupingB,
                            showLeadingOctave = True, withHyphen = noteGrouping.withHyphen, forceHyphen = True)
                    except text.BrailleTextException as bte:
                        brailleText.addElement(noteGrouping = brailleNoteGroupingB,
                            showLeadingOctave = True, withHyphen = noteGrouping.withHyphen, forceHyphen = True,
                            forceNewline=True)
                    isSolved = True
                    self[self._currentGroupingKey-0.5] = sngA
                    self[self._currentGroupingKey+0.5] = sngB
                    
        if noteGrouping.numRepeats > 0:
            for unused_repeatCounter in range(noteGrouping.numRepeats):
                brailleText.addElement(keyOrTimeSig = symbols['repeat'])

    def extractSignatureGrouping(self, brailleText):
        keySignature = None
        timeSignature = None
        try:
            keySignature, timeSignature = self.get(self._currentGroupingKey)[0], \
                                          self.get(self._currentGroupingKey)[1]
        except IndexError:
            keyOrTimeSig = self.get(self._currentGroupingKey)[0]
            if isinstance(keyOrTimeSig, key.KeySignature):
                keySignature = keyOrTimeSig
            else:
                timeSignature = keyOrTimeSig
        
        outgoingKeySig = None
        if self.cancelOutgoingKeySig and not keySignature is None:
            try:
                outgoingKeySig = keySignature.outgoingKeySig
            except AttributeError:
                pass

        try:
            brailleSig = basic.transcribeSignatures(keySignature, timeSignature, outgoingKeySig)
            brailleText.addElement(keyOrTimeSig = brailleSig)
        except basic.BrailleBasicException as bbe:
            if not bbe.args[0] == "No key or time signature to transcribe!":
                raise bbe

    def extractTempoTextGrouping(self, brailleText):
        self._allGroupingKeys.insert(0, self._currentGroupingKey)
        if self._previousGroupingKey % 10 == AFFINITY_SIGNATURE:
            self._allGroupingKeys.insert(0, self._previousGroupingKey)
        self.extractHeading(brailleText)
        self.addMeasureNumber(brailleText)

    def _getMeasureNumber(self, withDot=False):
        initMeasureNumber = self._allGroupingKeys[0] // 100
        brailleNumber = basic.numberToBraille(initMeasureNumber)
        if not withDot:
            return brailleNumber
        else:
            return u"".join([brailleNumber, symbols['dot']])

class BrailleGrandSegment():
    def __init__(self, rightSegment, leftSegment):
        self.rightSegment = rightSegment
        self.leftSegment = leftSegment
        self.previousGroupingPair = None
        self.currentGroupingPair = None
        self.maxLineLength = self.rightSegment.maxLineLength
        self.transcription = self.transcribe()

    def __str__(self):
        name = "<music21.braille.segment BrailleGrandSegment>\n==="
        allPairs = []
        allKeyPairs = self.combineGroupingKeys(self.rightSegment, self.leftSegment)
        for (rightKey, leftKey) in allKeyPairs:
            a = "Measure {0} Right, {1} {2}:\n".format(
                int(rightKey//100), affinityNames[rightKey%10], int(rightKey%100)//10 + 1)
            b = str(self.rightSegment[rightKey])
            c = "\nMeasure {0} Left, {1} {2}:\n".format(int(leftKey//100),
                affinityNames[leftKey%10], int(leftKey%100)//10 + 1)
            d = str(self.leftSegment[leftKey])
            ab = u"".join([a,b]) 
            cd = u"".join([c,d])
            allPairs.append(u"\n".join([ab, cd, "====\n"]))
        return u"\n".join(["---begin grand segment---", name, u"".join(allPairs), "---end grand segment---"])

    def combineGroupingKeys(self, rightSegment, leftSegment):
        groupingKeysRight = sorted(rightSegment.keys())
        groupingKeysLeft = sorted(leftSegment.keys())
        combinedGroupingKeys = []
        
        while groupingKeysRight:
            gkRight = groupingKeysRight.pop(0)
            try:
                groupingKeysLeft.remove(gkRight)
                combinedGroupingKeys.append((gkRight, gkRight))
            except ValueError:
                if gkRight % 10 < AFFINITY_INACCORD:
                    combinedGroupingKeys.append((gkRight, None))
                else:
                    if gkRight % 10 == AFFINITY_INACCORD:
                        gkLeft = gkRight+1
                    else:
                        gkLeft = gkRight-1
                    try:
                        groupingKeysLeft.remove(gkLeft)
                    except ValueError:
                        raise BrailleSegmentException("Misaligned braille groupings: groupingKeyLeft was %s, groupingKeyRight was %s, rightSegment was %s, leftSegment was %s" % (gkLeft, gkRight, rightSegment, leftSegment))

                    try:
                        combinedGroupingKeys.append((gkRight,gkLeft))
                    except ValueError:
                        raise BrailleSegmentException("Misaligned braille groupings could not append combinedGroupingKeys")

        
        while groupingKeysLeft:
            gkLeft = groupingKeysLeft.pop(0)
            combinedGroupingKeys.append((None, gkLeft))
        
        return combinedGroupingKeys
    
    def transcribe(self):
        """
        TODO: define this method
        """
        bk = text.BrailleKeyboard(self.maxLineLength)
        self.allKeyPairs = self.combineGroupingKeys(self.rightSegment, self.leftSegment)   
        bk.highestMeasureNumberLength = len(str(self.allKeyPairs[-1][0] // 100))

        self.extractHeading(bk) # Heading
    
        while self.allKeyPairs:
            self.previousGroupingPair = self.currentGroupingPair
            self.currentGroupingPair = self.allKeyPairs.pop(0)
            (rightKey, leftKey) = self.currentGroupingPair

            if rightKey >= AFFINITY_INACCORD or leftKey >= AFFINITY_INACCORD:
                self.extractNoteGrouping(bk) # Note or Inaccord Grouping
            elif rightKey == AFFINITY_SIGNATURE or leftKey == AFFINITY_SIGNATURE:
                self.extractSignatureGrouping(bk) # Signature Grouping
            elif rightKey == AFFINITY_LONG_TEXTEXPR or leftKey == AFFINITY_LONG_TEXTEXPR:
                self.extractLongExpressionGrouping(bk) # Long Expression Grouping
            elif rightKey == AFFINITY_TTEXT or leftKey == AFFINITY_TTEXT:
                self.extractTempoTextGrouping(bk) # Tempo Text Grouping
                
        return bk
    
    def extractHeading(self, brailleKeyboard):
        keySignature = None
        timeSignature = None
        tempoText = None
        metronomeMark = None
        
        while True:
            (rightKey, leftKey) = self.allKeyPairs[0]
            useKey = rightKey
            try:
                useElement = self.rightSegment[rightKey]
            except KeyError as ke:
                if ke.args[0] == "None":
                    useElement = self.leftSegment[leftKey]
                    useKey = leftKey
                else:
                    raise ke
            if useKey % 10 > AFFINITY_MMARK:
                break
            self.allKeyPairs.pop(0)
            if useKey % 10 == AFFINITY_SIGNATURE:
                try:
                    keySignature, timeSignature = useElement[0], useElement[1]
                except IndexError:
                    if isinstance(useElement, key.KeySignature):
                        keySignature = useElement[0]
                    else:
                        timeSignature = useElement[0]
            elif useKey % 10 == AFFINITY_TTEXT:
                tempoText = useElement[0]
            elif useKey % 10 == AFFINITY_MMARK:
                metronomeMark = useElement[0]

        try:
            brailleHeading = basic.transcribeHeading(keySignature, timeSignature,
                tempoText, metronomeMark, self.maxLineLength)
            brailleKeyboard.addElement(heading = brailleHeading)
        except basic.BrailleBasicException as bbe:
            if not bbe.args[0] == "No heading can be made.":
                raise bbe
        return None
    
    def extractNoteGrouping(self, brailleKeyboard):
        (rightKey, leftKey) = self.currentGroupingPair
        currentMeasureNumber = basic.numberToBraille(rightKey // 100, withNumberSign=False)
        if rightKey % 10 == AFFINITY_INACCORD:
            inaccords = self.rightSegment[rightKey]
            voice_trans = []
            for music21Voice in inaccords:
                noteGrouping = extractBrailleElements(music21Voice)
                noteGrouping.descendingChords = inaccords.descendingChords
                noteGrouping.showClefSigns = inaccords.showClefSigns
                noteGrouping.upperFirstInNoteFingering = inaccords.upperFirstInNoteFingering
                voice_trans.append(basic.transcribeNoteGrouping(noteGrouping))
            rh_braille = symbols['full_inaccord'].join(voice_trans)
        else:
            rh_braille = basic.transcribeNoteGrouping(self.rightSegment[rightKey])
        if leftKey % 10 == AFFINITY_INACCORD:
            inaccords = self.leftSegment[leftKey]
            voice_trans = []
            for music21Voice in inaccords:
                noteGrouping = extractBrailleElements(music21Voice)
                noteGrouping.descendingChords = inaccords.descendingChords
                noteGrouping.showClefSigns = inaccords.showClefSigns
                noteGrouping.upperFirstInNoteFingering = inaccords.upperFirstInNoteFingering
                voice_trans.append(basic.transcribeNoteGrouping(noteGrouping))
            lh_braille = symbols['full_inaccord'].join(voice_trans)
        else:
            lh_braille = basic.transcribeNoteGrouping(self.leftSegment[leftKey])
        brailleKeyboard.addNoteGroupings(currentMeasureNumber, rh_braille, lh_braille)
        return None

    #noinspection PyUnusedLocal
    def extractSignatureGrouping(self, brailleKeyboard):
        pass

    #noinspection PyUnusedLocal
    def extractLongExpressionGrouping(self, brailleKeyboard):
        pass

    #noinspection PyUnusedLocal
    def extractTempoTextGrouping(self, brailleKeyboard):
        pass
            
def splitNoteGrouping(noteGrouping, value = 2, beatDivisionOffset = 0):
    """
    Almost identical to :meth:`~music21.braille.segment.splitMeasure`, but
    functions on a :class:`~music21.braille.segment.BrailleElementGrouping`
    instead.
    """
    music21Measure = stream.Measure()
    for brailleElement in noteGrouping:
        music21Measure.insert(brailleElement.offset, brailleElement)
    newMeasures = splitMeasure(music21Measure, value, beatDivisionOffset, noteGrouping.timeSignature)
    
    leftBrailleElements = BrailleElementGrouping()
    for brailleElement in newMeasures[0]:
        leftBrailleElements.append(brailleElement)
    leftBrailleElements.__dict__ = noteGrouping.__dict__.copy() # pylint: disable=attribute-defined-outside-init

    rightBrailleElements = BrailleElementGrouping()
    for brailleElement in newMeasures[1]:
        rightBrailleElements.append(brailleElement)
    rightBrailleElements.__dict__ = noteGrouping.__dict__.copy() # pylint: disable=attribute-defined-outside-init

    return leftBrailleElements, rightBrailleElements

#-------------------------------------------------------------------------------
# Grouping + Segment creation from music21.stream Part

def findSegments(music21Part, **partKeywords):
    """
    Takes in a :class:`~music21.stream.Part`
    and a list of partKeywords. Returns a list of :class:`~music21.segment.BrailleSegment` instances.
    
    
    Five methods get called in the generation of segments:
    
    * :meth:`~music21.braille.segment.prepareSlurredNotes`
    * :meth:`~music21.braille.segment.getRawSegments`
    * :meth:`~music21.braille.segment.addGroupingAttributes`
    * :meth:`~music21.braille.segment.addSegmentAttributes`
    * :meth:`~music21.braille.segment.fixArticulations`

    
    >>> from music21.braille import test
    >>> example = test.example11_2()
    >>> allSegments = braille.segment.findSegments(example, segmentBreaks = [(8, 3.0)])
    >>> allSegments[0]
    ---begin segment---
    <music21.braille.segment BrailleSegment>
    Measure 0, Signature Grouping 1:
    <music21.key.KeySignature of 3 flats>
    <music21.meter.TimeSignature 4/4>
    ===
    Measure 0, Note Grouping 1:
    <music21.clef.TrebleClef>
    <music21.note.Note B->
    ===
    Measure 1, Note Grouping 1:
    <music21.note.Note G>
    <music21.note.Note E->
    <music21.note.Note D>
    <music21.note.Note E->
    ===
    Measure 2, Note Grouping 1:
    <music21.note.Note G>
    <music21.note.Note F>
    <music21.note.Note E->
    ===
    Measure 3, Note Grouping 1:
    <music21.note.Note A->
    <music21.note.Note G>
    <music21.note.Note C>
    <music21.note.Note C>
    ===
    Measure 4, Note Grouping 1:
    <music21.note.Note B->
    <music21.note.Note B->
    ===
    Measure 5, Note Grouping 1:
    <music21.note.Note E->
    <music21.note.Note B->
    <music21.note.Note A->
    <music21.note.Note G>
    ===
    Measure 6, Note Grouping 1:
    <music21.note.Note G>
    <music21.note.Note F>
    <music21.note.Note C>
    ===
    Measure 7, Note Grouping 1:
    <music21.note.Note C>
    <music21.note.Note F>
    <music21.note.Note A->
    <music21.note.Note D>
    ===
    Measure 8, Note Grouping 1:
    <music21.note.Note E->
    ** Music Hyphen **
    ===
    ---end segment---
    >>> allSegments[1]
    ---begin segment---
    <music21.braille.segment BrailleSegment>
    Measure 8, Note Grouping 1:
    <music21.note.Note G>
    ===
    Measure 9, Note Grouping 1:
    <music21.note.Note G>
    <music21.note.Note F>
    <music21.note.Note F>
    <music21.note.Note F>
    ===
    Measure 10, Note Grouping 1:
    <music21.note.Note A->
    <music21.note.Note G>
    <music21.note.Note B->
    ===
    Measure 11, Note Grouping 1:
    <music21.note.Note B->
    <music21.note.Note A>
    <music21.note.Note A>
    <music21.note.Note C>
    ===
    Measure 12, Note Grouping 1:
    <music21.note.Note B->
    <music21.note.Note B->
    ===
    Measure 13, Note Grouping 1:
    <music21.note.Note E->
    <music21.note.Note B->
    <music21.note.Note A->
    <music21.note.Note G>
    ===
    Measure 14, Note Grouping 1:
    <music21.note.Note G>
    <music21.note.Note F>
    <music21.note.Note C>
    ===
    Measure 15, Note Grouping 1:
    <music21.note.Note C>
    <music21.note.Rest rest>
    <music21.note.Note F>
    <music21.note.Rest rest>
    ===
    Measure 16, Note Grouping 1:
    <music21.note.Note A->
    <music21.note.Note D>
    ===
    Measure 17, Note Grouping 1:
    <music21.note.Note E->
    <music21.bar.Barline style=final>
    ===
    ---end segment---
    """
    # Slurring
    # --------
    slurLongPhraseWithBrackets = SEGMENT_SLURLONGPHRASEWITHBRACKETS
    showShortSlursAndTiesTogether, showLongSlursAndTiesTogether = \
    SEGMENT_SHOWSHORTSLURSANDTIESTOGETHER, SEGMENT_SHOWLONGSLURSANDTIESTOGETHER

    if 'slurLongPhraseWithBrackets' in partKeywords:
        slurLongPhraseWithBrackets = partKeywords['slurLongPhraseWithBrackets']
    if 'showShortSlursAndTiesTogether' in partKeywords:
        showShortSlursAndTiesTogether = partKeywords['showShortSlursAndTiesTogether']
    if 'showLongSlursAndTiesTogether' in partKeywords:
        showLongSlursAndTiesTogether = partKeywords['showLongSlursAndTiesTogether']
    else:
        if slurLongPhraseWithBrackets:
            showLongSlursAndTiesTogether = True
            
    prepareSlurredNotes(music21Part, slurLongPhraseWithBrackets,
        showShortSlursAndTiesTogether, showLongSlursAndTiesTogether)

    # Raw Segments
    # ------------
    segmentBreaks = SEGMENT_SEGMENTBREAKS
    if 'segmentBreaks' in partKeywords:
        segmentBreaks = partKeywords['segmentBreaks']
    allSegments = getRawSegments(music21Part, segmentBreaks)
    # Grouping Attributes
    # -------------------
    addGroupingAttributes(allSegments, **partKeywords)
    # Segment Attributes
    # ------------------
    addSegmentAttributes(allSegments, **partKeywords)
    # Articulations
    # -------------
    fixArticulations(allSegments)
    
    return allSegments


def prepareSlurredNotes(music21Part, slurLongPhraseWithBrackets = SEGMENT_SLURLONGPHRASEWITHBRACKETS,
                        showShortSlursAndTiesTogether = SEGMENT_SHOWSHORTSLURSANDTIESTOGETHER, 
                        showLongSlursAndTiesTogether = SEGMENT_SHOWLONGSLURSANDTIESTOGETHER):
    """
    Takes in a :class:`~music21.stream.Part` and three keywords:
    
    * slurLongPhraseWithBrackets
    * showShortSlursAndTiesTogether
    * showLongSlursAndTiesTogether
    
    
    For any slurs present in the Part, the appropriate notes are labeled
    with attributes indicating where to put the symbols that represent 
    slurring in braille. For purposes of slurring in braille, there is 
    a distinction between short and long phrases. In a short phrase, a 
    slur covers up to four notes. A short slur symbol should follow each 
    note except the last. 
    
    
    >>> import copy
    >>> from music21.braille import segment
    >>> short = converter.parse("tinynotation: 3/4 c4 d e")
    >>> s1 = spanner.Slur(short.flat.notes[0], short.flat.notes[-1])
    >>> short.append(s1)
    >>> short.show("text")
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 3/4>
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note D>
        {2.0} <music21.note.Note E>
        {3.0} <music21.bar.Barline style=final>
    {3.0} <music21.spanner.Slur <music21.note.Note C><music21.note.Note E>>
    >>> shortA = copy.deepcopy(short)
    >>> segment.prepareSlurredNotes(shortA)
    >>> shortA.flat.notes[0].shortSlur
    True
    >>> shortA.flat.notes[1].shortSlur
    True
    
    
    In a long phrase, a slur covers more than four notes. There are two 
    options for slurring long phrases. The first is by using the bracket 
    slur. By default, slurLongPhraseWithBrackets is True. The opening
    bracket sign is put before the first note, and the closing bracket
    sign is put before the last note.
    
    
    >>> long = converter.parse("tinynotation: 3/4 c8 d e f g a")
    >>> s2 = spanner.Slur(long.flat.notes[0], long.flat.notes[-1])
    >>> long.append(s2)
    >>> long.show("text")
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 3/4>
        {0.0} <music21.note.Note C>
        {0.5} <music21.note.Note D>
        {1.0} <music21.note.Note E>
        {1.5} <music21.note.Note F>
        {2.0} <music21.note.Note G>
        {2.5} <music21.note.Note A>
        {3.0} <music21.bar.Barline style=final>
    {3.0} <music21.spanner.Slur <music21.note.Note C><music21.note.Note A>>
    >>> longA = copy.deepcopy(long)
    >>> segment.prepareSlurredNotes(longA)
    >>> longA.flat.notes[0].beginLongBracketSlur
    True
    >>> longA.flat.notes[-1].endLongBracketSlur
    True
    
    
    The other way is by using the double slur, setting slurLongPhraseWithBrackets
    to False. The opening sign of the double slur is put after the first note
    (i.e. before the second note) and the closing sign is put before the last
    note (i.e. before the second to last note).
    
    
    >>> longB = copy.deepcopy(long)
    >>> segment.prepareSlurredNotes(longB, slurLongPhraseWithBrackets=False)
    >>> longB.flat.notes[1].beginLongDoubleSlur
    True
    >>> longB.flat.notes[-2].endLongDoubleSlur
    True
    
    
    In the event that slurs and ties are shown together in print, the slur is
    redundant. Examples are shown for slurring a short phrase; the process is
    identical for slurring a long phrase.
    
    
    Below, a tie has been added between the first two notes of the short phrase
    defined above. If showShortSlursAndTiesTogether is set to its default value of 
    False, then the slur on either side of the phrase is reduced by the amount that 
    ties are present, as shown below.


    >>> short.flat.notes[0].tie = tie.Tie("start")
    >>> shortB = copy.deepcopy(short)
    >>> segment.prepareSlurredNotes(shortB)
    >>> shortB.flat.notes[0].shortSlur
    Traceback (most recent call last):
    AttributeError: 'Note' object has no attribute 'shortSlur'
    >>> shortB.flat.notes[0].tie
    <music21.tie.Tie start>
    >>> shortB.flat.notes[1].shortSlur
    True
  
  
    If showShortSlursAndTiesTogether is set to True, then the slurs and ties are 
    shown together (i.e. the note has both a shortSlur and a tie).

  
    >>> shortC = copy.deepcopy(short)
    >>> segment.prepareSlurredNotes(shortC, showShortSlursAndTiesTogether=True)
    >>> shortC.flat.notes[0].shortSlur
    True
    >>> shortC.flat.notes[0].tie
    <music21.tie.Tie start>
    """
    if music21Part.spannerBundle:
        allNotes = music21Part.flat.notes
        for slur in music21Part.spannerBundle.getByClass(spanner.Slur):
            try:
                slur[0].index = allNotes.index(slur[0])
                slur[1].index = allNotes.index(slur[1])
            except exceptions21.StreamException:
                continue
            beginIndex = slur[0].index
            endIndex = slur[1].index
            delta = abs(endIndex - beginIndex) + 1
            if not showShortSlursAndTiesTogether and delta <= 4:
                if allNotes[beginIndex].tie is not None and allNotes[beginIndex].tie.type == 'start':
                    beginIndex += 1
                if allNotes[endIndex].tie is not None and allNotes[endIndex].tie.type == 'stop':
                    endIndex -= 1
            if not showLongSlursAndTiesTogether and delta > 4:
                if allNotes[beginIndex].tie is not None and allNotes[beginIndex].tie.type == 'start':
                    beginIndex += 1
                if allNotes[endIndex].tie is not None and allNotes[endIndex].tie.type == 'stop':
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

def getRawSegments(music21Part, segmentBreaks=None):
    """
    Takes in a :class:`~music21.stream.Part` and a segmentBreaks list which 
    contains (measureNumber, offsetStart) tuples. These tuples determine how
    the Part is divided up into segments (i.e. instances of
    :class:`~music21.braille.segment.BrailleSegment`). This method assumes 
    that the Part is already divided up into measures 
    (see :class:`~music21.stream.Measure`). An acceptable input is shown below.
    
    
    Two methods are called on each measure during the creation of segments: 
    
    * :meth:`~music21.braille.segment.prepareBeamedNotes`
    * :meth:`~music21.braille.segment.extractBrailleElements`
    
    
    >>> tn = converter.parse("tinynotation: 3/4 c4 c c e e e g g g c'2.")
    >>> tn = tn.makeNotation(cautionaryNotImmediateRepeat=False)
    >>> tn.show("text")
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 3/4>
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note C>
        {2.0} <music21.note.Note C>
    {3.0} <music21.stream.Measure 2 offset=3.0>
        {0.0} <music21.note.Note E>
        {1.0} <music21.note.Note E>
        {2.0} <music21.note.Note E>
    {6.0} <music21.stream.Measure 3 offset=6.0>
        {0.0} <music21.note.Note G>
        {1.0} <music21.note.Note G>
        {2.0} <music21.note.Note G>
    {9.0} <music21.stream.Measure 4 offset=9.0>
        {0.0} <music21.note.Note C>
        {3.0} <music21.bar.Barline style=final>

    
    By default, there is no break anywhere within the Part,
    and a segmentList of size 1 is returned.
    
    
    >>> import copy
    >>> from music21.braille import segment
    >>> tnA = copy.deepcopy(tn)
    >>> segment.getRawSegments(tnA)[0]
    ---begin segment---
    <music21.braille.segment BrailleSegment>
    Measure 1, Signature Grouping 1:
    <music21.meter.TimeSignature 3/4>
    ===
    Measure 1, Note Grouping 1:
    <music21.clef.TrebleClef>
    <music21.note.Note C>
    <music21.note.Note C>
    <music21.note.Note C>
    ===
    Measure 2, Note Grouping 1:
    <music21.note.Note E>
    <music21.note.Note E>
    <music21.note.Note E>
    ===
    Measure 3, Note Grouping 1:
    <music21.note.Note G>
    <music21.note.Note G>
    <music21.note.Note G>
    ===
    Measure 4, Note Grouping 1:
    <music21.note.Note C>
    <music21.bar.Barline style=final>
    ===
    ---end segment---

    
    Now, a segment break occurs at measure 2, offset 1.0 within that measure.
    The two segments are shown below.
    
    
    >>> tnB = copy.deepcopy(tn)
    >>> allSegments = segment.getRawSegments(tnB, segmentBreaks=[(2,1.0)])
    >>> allSegments[0]
    ---begin segment---
    <music21.braille.segment BrailleSegment>
    Measure 1, Signature Grouping 1:
    <music21.meter.TimeSignature 3/4>
    ===
    Measure 1, Note Grouping 1:
    <music21.clef.TrebleClef>
    <music21.note.Note C>
    <music21.note.Note C>
    <music21.note.Note C>
    ===
    Measure 2, Note Grouping 1:
    <music21.note.Note E>
    ===
    ---end segment---
    
    >>> allSegments[1]
    ---begin segment---
    <music21.braille.segment BrailleSegment>
    Measure 2, Note Grouping 1:
    <music21.note.Note E>
    <music21.note.Note E>
    ===
    Measure 3, Note Grouping 1:
    <music21.note.Note G>
    <music21.note.Note G>
    <music21.note.Note G>
    ===
    Measure 4, Note Grouping 1:
    <music21.note.Note C>
    <music21.bar.Barline style=final>
    ===
    ---end segment---
    """
    if segmentBreaks is None:
        segmentBreaks = SEGMENT_SEGMENTBREAKS
        
    allSegments = []
    mnStart = 1000000.0
    offsetStart = 0.0
    segmentIndex = 0
    if segmentBreaks:
        (mnStart, offsetStart) = segmentBreaks[segmentIndex]
    currentSegment = BrailleSegment()
    for music21Measure in music21Part.getElementsByClass(stream.Measure, stream.Voice):
        prepareBeamedNotes(music21Measure)
        if music21Measure.number >= mnStart:
            music21Measure.sliceAtOffsets(offsetList=[offsetStart], inPlace=True)
        brailleElements = extractBrailleElements(music21Measure)
        offsetFactor = 0
        previousCode = -1
        for brailleElement in brailleElements:
            if (music21Measure.number > mnStart or
                music21Measure.number == mnStart and brailleElement.offset >= offsetStart):
                if offsetStart != 0.0:
                    currentSegment.endHyphen = True
                allSegments.append(currentSegment)
                currentSegment = BrailleSegment()
                if offsetStart != 0.0:
                    currentSegment.measureNumberWithDot = True
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

def extractBrailleElements(music21Measure):
    """
    Takes in a :class:`~music21.stream.Measure` and returns a 
    :class:`~music21.braille.segment.BrailleElementGrouping` of correctly ordered
    :class:`~music21.base.Music21Object` instances which can be directly transcribed to
    braille.
    

    >>> from music21.braille import segment
    >>> tn = converter.parse("tinynotation: 2/4 c16 c c c d d d d", makeNotation=False)
    >>> tn = tn.makeNotation(cautionaryNotImmediateRepeat=False)
    >>> measure = tn[0]
    >>> measure.append(spanner.Slur(measure.notes[0],measure.notes[-1]))
    >>> measure.show("text")
    {0.0} <music21.clef.TrebleClef>
    {0.0} <music21.meter.TimeSignature 2/4>
    {0.0} <music21.note.Note C>
    {0.25} <music21.note.Note C>
    {0.5} <music21.note.Note C>
    {0.75} <music21.note.Note C>
    {1.0} <music21.note.Note D>
    {1.25} <music21.note.Note D>
    {1.5} <music21.note.Note D>
    {1.75} <music21.note.Note D>
    {2.0} <music21.spanner.Slur <music21.note.Note C><music21.note.Note D>>
    {2.0} <music21.bar.Barline style=final>
    
    
    Spanners are dealt with in :meth:`~music21.braille.segment.prepareSlurredNotes`,
    so they are not returned by this method, as seen below.
    
    
    >>> segment.extractBrailleElements(measure)
    <music21.meter.TimeSignature 2/4>
    <music21.clef.TrebleClef>
    <music21.note.Note C>
    <music21.note.Note C>
    <music21.note.Note C>
    <music21.note.Note C>
    <music21.note.Note D>
    <music21.note.Note D>
    <music21.note.Note D>
    <music21.note.Note D>
    <music21.bar.Barline style=final>
    """
    allElements = BrailleElementGrouping()
    for music21Object in music21Measure:
        try:
            if isinstance(music21Object, bar.Barline):
                if music21Object.style == 'regular':
                    continue
            setAffinityCode(music21Object)
            music21Object._brailleEnglish = [str(music21Object)]
            allElements.append(music21Object)
        except BrailleSegmentException as notSupportedException:
            isExempt = [isinstance(music21Object, music21Class) for music21Class in excludeFromBrailleElements]
            if not isExempt.count(True):
                environRules.warn("{0}".format(notSupportedException))

    allElements.sort(key = lambda x: (x.offset, x.classSortOrder))
    if len(allElements) >= 2 and isinstance(allElements[-1], dynamics.Dynamic):
        if isinstance(allElements[-2], bar.Barline):
            allElements[-1].classSortOrder = -1
            allElements.sort(key = lambda x: (x.offset, x.classSortOrder))
            
    return allElements

def prepareBeamedNotes(music21Measure):
    """
    Takes in a :class:`~music21.stream.Measure` and labels beamed notes
    of smaller value than an 8th with beamStart and beamContinue keywords
    in accordance with beaming rules in braille music.
    
    
    A more in-depth explanation of beaming in braille can be found in 
    Chapter 15 of Introduction to Braille Music Transcription, Second 
    Edition, by Mary Turner De Garmo.
    

    >>> from music21.braille import segment
    >>> tn = converter.parse("tinynotation: 2/4 c16 c c c d d d d")
    >>> tn = tn.makeNotation(cautionaryNotImmediateRepeat=False)
    >>> tn.show("text")
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 2/4>
        {0.0} <music21.note.Note C>
        {0.25} <music21.note.Note C>
        {0.5} <music21.note.Note C>
        {0.75} <music21.note.Note C>
        {1.0} <music21.note.Note D>
        {1.25} <music21.note.Note D>
        {1.5} <music21.note.Note D>
        {1.75} <music21.note.Note D>
        {2.0} <music21.bar.Barline style=final>
    >>> measure = tn[0]
    >>> segment.prepareBeamedNotes(measure)
    >>> measure.notes[0].beamStart
    True
    >>> measure.notes[1].beamContinue
    True
    >>> measure.notes[2].beamContinue
    True
    >>> measure.notes[3].beamContinue
    True
    """
    allNotes = music21Measure.notes
    for sampleNote in allNotes:
        sampleNote.beamStart = False
        sampleNote.beamContinue = False
    allNotesAndRests = music21Measure.notesAndRests
    allNotesWithBeams = allNotes.splitByClass(
        None, lambda sampleNote: not(sampleNote.beams is None) and len(sampleNote.beams) > 0)[0]
    allStart = allNotesWithBeams.splitByClass(
        None, lambda sampleNote: sampleNote.beams.getByNumber(1).type is 'start')[0]
    allStop  = allNotesWithBeams.splitByClass(
        None, lambda sampleNote: sampleNote.beams.getByNumber(1).type is 'stop')[0]
    if not(len(allStart) == len(allStop)):
        environRules.warn("Incorrect beaming: number of start notes != to number of stop notes.")
        return
    
    for beamIndex in range(len(allStart)):
        startNote = allStart[beamIndex]
        stopNote = allStop[beamIndex]
        startIndex = allNotesAndRests.index(startNote)
        stopIndex = allNotesAndRests.index(stopNote)
        delta = stopIndex - startIndex + 1
        if delta < 3: # 2. The group must be composed of at least three notes.
            continue
        # Eighth notes cannot be beamed in braille (redundant, because beamed 
        # notes look like eighth notes, but nevertheless useful).
        if startNote.quarterLength == 0.5:
            continue
        # 1. All notes in the group must have precisely the same value.
        # 3. A rest of the same value may take the place of the first note in a group, 
        # but if the rest is located anywhere else, grouping may not be used.
        allNotesOfSameValue = True
        for noteIndex in range(startIndex+1, stopIndex+1):
            if not(allNotesAndRests[noteIndex].duration.type == startNote.duration.type)\
             or isinstance(allNotesAndRests[noteIndex], note.Rest):
                allNotesOfSameValue = False
                break
        try:
            afterStopNote = allNotesAndRests[stopIndex+1]
            if isinstance(afterStopNote, note.Rest) and (int(afterStopNote.beat) == int(stopNote.beat)):
                allNotesOfSameValue = False
        except exceptions21.StreamException: # stopNote is last note of measure.
            pass
        if not allNotesOfSameValue:
            continue
        try:
            # 4. If the notes in the group are followed immediately by a true eighth note or by an eighth rest, 
            # grouping may not be used, unless the eighth is located in a new measure.
            if allNotesAndRests[stopIndex+1].quarterLength == 0.5:
                continue
        except exceptions21.StreamException: # stopNote is last note of measure.
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

def setAffinityCode(music21Object):
    """
    Takes in a :class:`~music21.base.Music21Object`, and does two things:
    
    * Modifies the :attr:`~music21.base.Music21Object.classSortOrder` attribute of the 
      object to fit the slightly modified ordering of objects in braille music.
    
    * Adds an affinity code to the object. This code indicates which surrounding
      objects the object should be grouped with.
    

    A BrailleSegmentException is raised if an affinity code cannot be assigned to
    the object.
    
    
    As seen in the following example, the affinity code of a :class:`~music21.note.Note`
    and a :class:`~music21.clef.TrebleClef` are the same, because they should be grouped
    together. However, the classSortOrder indicates that the TrebleClef should come first
    in the braille.
    
    >>> n1 = note.Note("D5")
    >>> braille.segment.setAffinityCode(n1)
    >>> n1.affinityCode
    9
    >>> n1.classSortOrder
    10
    >>> c1 = clef.TrebleClef()
    >>> braille.segment.setAffinityCode(c1)
    >>> c1.affinityCode
    9
    >>> c1.classSortOrder
    7
    """
    for (music21Class, code, sortOrder) in affinityCodes:
        if isinstance(music21Object, music21Class):
            music21Object.affinityCode = code
            music21Object.classSortOrder = sortOrder
            return
        
    if isinstance(music21Object, expressions.TextExpression):
        music21Object.affinityCode = AFFINITY_NOTEGROUP
        if len(music21Object.content.split()) > 1:
            music21Object.affinityCode = AFFINITY_LONG_TEXTEXPR
        music21Object.classSortOrder = 8
        return

    raise BrailleSegmentException("{0} cannot be transcribed to braille.".format(music21Object))

def addGroupingAttributes(allSegments, **partKeywords):
    """
    Modifies the attributes of all :class:`~music21.braille.segment.BrailleElementGrouping`
    instances in a list of :class:`~music21.braille.segment.BrailleSegment` instances. The
    necessary information is retrieved both by passing in partKeywords as an argument and
    by taking into account the linear progression of the groupings and segments.
    """
    currentKeySig = key.KeySignature(0)
    currentTimeSig = meter.TimeSignature("4/4")
    
    descendingChords = GROUPING_DESC_CHORDS
    showClefSigns = GROUPING_SHOW_CLEFS
    upperFirstInNoteFingering = GROUPING_UPPERFIRST_NOTEFINGERING

    if 'showClefSigns' in partKeywords:
        showClefSigns = partKeywords['showClefSigns']
    if 'upperFirstInNoteFingering' in partKeywords:
        upperFirstInNoteFingering = partKeywords['upperFirstInNoteFingering']
    if 'descendingChords' in partKeywords:
        descendingChords = partKeywords['descendingChords']
            
    for brailleSegment in allSegments:
        allGroupings = sorted(brailleSegment.items())
        (previousKey, previousList) = None, None
        for (groupingKey, groupingList) in allGroupings:
            if previousKey is not None:
                if groupingKey % 100 >= 10:
                    previousList.withHyphen = True
                if previousKey % 100 == AFFINITY_NOTEGROUP and groupingKey % 100 == AFFINITY_NOTEGROUP:
                    if isinstance(previousList[0], clef.Clef):
                        measureRepeats = compareNoteGroupings(previousList[1:], groupingList)
                    else:
                        measureRepeats = compareNoteGroupings(previousList, groupingList)
                    if measureRepeats:
                        previousList.numRepeats += 1
                        del brailleSegment[groupingKey]
                        continue
            if groupingKey % 10 == AFFINITY_SIGNATURE:
                for brailleElement in groupingList:
                    if isinstance(brailleElement, meter.TimeSignature):
                        currentTimeSig = brailleElement
                    elif isinstance(brailleElement, key.KeySignature):
                        brailleElement.outgoingKeySig = currentKeySig
                        currentKeySig = brailleElement
            elif groupingKey % 10 == AFFINITY_NOTEGROUP:
                if isinstance(groupingList[0], clef.Clef):
                    if isinstance(groupingList[0], clef.TrebleClef) or isinstance(groupingList[0], clef.AltoClef):
                        descendingChords = True
                    elif isinstance(groupingList[0], clef.BassClef) or isinstance(groupingList[0], clef.TenorClef):
                        descendingChords = False
                allGeneralNotes = [n for n in groupingList if isinstance(n, note.GeneralNote)]
                if len(allGeneralNotes) == 1 and isinstance(allGeneralNotes[0], note.Rest):
                    allGeneralNotes[0].quarterLength = 4.0
            groupingList.keySignature = currentKeySig
            groupingList.timeSignature = currentTimeSig
            groupingList.descendingChords = descendingChords
            groupingList.showClefSigns = showClefSigns
            groupingList.upperFirstInNoteFingering = upperFirstInNoteFingering
            (previousKey, previousList) = (groupingKey, groupingList)
        if brailleSegment.endHyphen:
            previousList.withHyphen = True

def compareNoteGroupings(noteGroupingA, noteGroupingB):
    """
    Takes in two note groupings, noteGroupingA and noteGroupingB. Returns True
    if both groupings have identical contents. False otherwise.
    """
    if len(noteGroupingA) == len(noteGroupingB):
        for (elementA, elementB) in zip(noteGroupingA, noteGroupingB):
            if elementA != elementB:
                return False
        return True
    return False

def addSegmentAttributes(allSegments, **partKeywords):
    """
    Modifies the attributes of a :class:`~music21.braille.segment.BrailleSegment`
    by passing partKeywords as an argument.
    """
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
        if 'suppressOctaveMarks' in partKeywords:
            brailleSegment.suppressOctaveMarks = partKeywords['suppressOctaveMarks']  

def fixArticulations(allSegments):
    """
    Goes through each :class:`~music21.braille.segment.BrailleSegment` and modifies the 
    list of :attr:`~music21.note.GeneralNote.articulations` of a :class:`~music21.note.Note` 
    if appropriate. In particular, two rules are applied:
    
    * Doubling rule => If four or more of the same :class:`~music21.articulations.Articulation`
      are found in a row, the first instance of the articulation is doubled and the rest are 
      omitted.
    
    * Staccato, Tenuto rule => "If two repeated notes appear to be tied, but either is marked 
      staccato or tenuto, they are treated as slurred instead of tied." (BMTM, 112)
    """
    from music21 import articulations
    for brailleSegment in allSegments:
        newSegment = brailleSegment.consolidate()
        for noteGrouping in [newSegment[gpKey] for gpKey in newSegment.keys() if gpKey % 10 == AFFINITY_NOTEGROUP]:
            allNotes = [n for n in noteGrouping if isinstance(n,note.Note)]
            for noteIndexStart in range(len(allNotes)):
                music21NoteStart = allNotes[noteIndexStart]
                for artc in music21NoteStart.articulations:
                    artcName = artc.name
                    if isinstance(artc, articulations.Staccato) or isinstance(artc, articulations.Tenuto):
                        if not music21NoteStart.tie is None:
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
                        if artcName in [a.name for a in music21NoteContinue.articulations]:
                            numSequential+=1
                            continue
                        break
                    if numSequential >= 3:
                        # double the articulation on the first note and remove from the next...
                        music21NoteStart.articulations.append(artc)
                        for noteIndexContinue in range(noteIndexStart+1, noteIndexStart+numSequential):
                            music21NoteContinue = allNotes[noteIndexContinue]
                            for artOther in music21NoteContinue.articulations:
                                if artOther.name == artcName:
                                    music21NoteContinue.articulations.remove(artOther)

#-------------------------------------------------------------------------------
# Helper Methods

def splitMeasure(music21Measure, value = 2, beatDivisionOffset = 0, useTimeSignature = None):
    """
    Takes a :class:`~music21.stream.Measure`, divides it in two parts, and returns a
    :class:`~music21.stream.Part` containing the two halves. The parameters are as
    follows:
    
    * value => the number of partitions to split a time signature into. The first half will
      contain all elements found within the offsets of the first partition, while the last
      half will contain all other elements.
    * beatDivisionOffset => Adjusts the end offset of the first partition by a certain amount
      of beats to the left.
    * useTimeSignature => In the event that the Measure comes from the middle of a Part
      and thus does not define an explicit :class:`~music21.meter.TimeSignature`. If not
      provided, a TimeSignature is retrieved by using :meth:`~music21.stream.Measure.bestTimeSignature`.
    """
    if not useTimeSignature is None:
        ts = useTimeSignature
    else:
        ts = music21Measure.bestTimeSignature()
    
    offset = 0.0
    if not(beatDivisionOffset == 0):
        if abs(beatDivisionOffset) > len(ts.beatDivisionDurations):
            raise Exception()
        i = len(ts.beatDivisionDurations) - abs(beatDivisionOffset)
        try:
            offset += opFrac(ts.beatDivisionDurations[i].quarterLength)
        except IndexError:
            environRules.warn('Problem in converting a time signature in measure %d, offset may be wrong' % music21Measure.number)
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
        if x.offset >= startOffsetZero and\
           (x.offset < endOffsetZero or (x.offset == endOffsetZero and isinstance(x, bar.Barline))):
            newMeasures[0].insert(x.offset, x)
        else:
            newMeasures[1].insert(x.offset, x)
    for n in newMeasures[1].notes:
        if n.tie is not None:
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
    if newMeasures[0].timeSignature is None:
        ts0_delete = True
        newMeasures[0].timeSignature = ts
    newMeasures[1].timeSignature = ts
    newMeasures[0].mergeAttributes(music21Measure)
    newMeasures[1].mergeAttributes(music21Measure)
    newMeasures[0].makeBeams(inPlace=True)
    newMeasures[1].makeBeams(inPlace=True)
    prepareBeamedNotes(newMeasures[0])
    prepareBeamedNotes(newMeasures[1])
    newMeasures[0].remove(r0)
    newMeasures[1].remove(r1)
    if ts0_delete:
        newMeasures[0].remove(ts)
    newMeasures[1].remove(ts)
    return newMeasures

#-------------------------------------------------------------------------------

class BrailleSegmentException(exceptions21.Music21Exception):
    pass
    
#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass


if __name__ == "__main__":
    import music21
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof
