# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         segment.py
# Purpose:      Division of stream.Part into segments for individual handling
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    Copyright © 2012 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Inner classes and methods for transcribing musical segments into braille.

This module was made in consultation with the manual "Introduction to Braille
Music Transcription, Second Edition" by Mary Turner De Garmo, 2005. It is
available from the Library of Congress `here <http://www.loc.gov/nls/music/>`_,
and will henceforth be referred to as BMTM.
'''
import collections
import copy
import enum
import unittest

from music21 import bar
from music21 import chord
from music21 import clef
from music21 import dynamics
from music21 import exceptions21
from music21 import environment
from music21 import expressions
from music21 import key
from music21 import layout
from music21 import meter
from music21 import note
from music21 import spanner
from music21 import stream
from music21 import tempo
from music21.prebase import ProtoM21Object

from music21.braille import basic
from music21.braille import lookup
from music21.braille import noteGrouping as ngMod
from music21.braille import text
from music21.braille.objects import BrailleTranscriptionHelper

from music21.common.numberTools import opFrac

symbols = lookup.symbols
environRules = environment.Environment('segment.py')


# ------------------------------------------------------------------------------
class BrailleSegmentException(exceptions21.Music21Exception):
    pass


class Affinity(enum.IntEnum):
    _LOWEST = -1
    SIGNATURE = 3
    TTEXT = 4
    MMARK = 5
    LONG_TEXTEXPR = 6
    INACCORD = 7

    SPLIT1_NOTEGROUP = 8
    NOTEGROUP = 9
    SPLIT2_NOTEGROUP = 10


# Class Sort Order -- differs for Braille than for general music21
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
affinityCodes = [(note.Note, Affinity.NOTEGROUP, CSO_NOTE),
                 (note.Rest, Affinity.NOTEGROUP, CSO_REST),
                 (chord.Chord, Affinity.NOTEGROUP, CSO_CHORD),
                 (dynamics.Dynamic, Affinity.NOTEGROUP, CSO_DYNAMIC),
                 (clef.Clef, Affinity.NOTEGROUP, CSO_CLEF),
                 (bar.Barline, Affinity.SPLIT2_NOTEGROUP, CSO_BARLINE),
                 (key.KeySignature, Affinity.SIGNATURE, CSO_KEYSIG),
                 (meter.TimeSignature, Affinity.SIGNATURE, CSO_TIMESIG),
                 (tempo.TempoText, Affinity.TTEXT, CSO_TTEXT),
                 (tempo.MetronomeMark, Affinity.MMARK, CSO_MMARK),
                 (stream.Voice, Affinity.INACCORD, CSO_VOICE)]

affinityNames = {Affinity.SIGNATURE: 'Signature Grouping',
                 Affinity.TTEXT: 'Tempo Text Grouping',
                 Affinity.MMARK: 'Metronome Mark Grouping',
                 Affinity.LONG_TEXTEXPR: 'Long Text Expression Grouping',
                 Affinity.INACCORD: 'Inaccord Grouping',
                 Affinity.NOTEGROUP: 'Note Grouping',
                 Affinity.SPLIT1_NOTEGROUP: 'Split Note Grouping A',
                 Affinity.SPLIT2_NOTEGROUP: 'Split Note Grouping B',
                 }

excludeFromBrailleElements = [spanner.Slur,
                              layout.SystemLayout,
                              layout.PageLayout,
                              layout.StaffLayout]

# Uncomment when Python 3.8 is the minimum version
# from typing import TypedDict, Optional
# class GroupingGlobals(TypedDict):
#    keySignature: Optional[key.KeySignature]
#    timeSignature: Optional[meter.TimeSignature]
# GROUPING_GLOBALS: GroupingGlobals = {...}


GROUPING_GLOBALS = {
    'keySignature': None,  # will be key.KeySignature(0) on first call
    'timeSignature': None,  # will be meter.TimeSignature('4/4') on first call
}
GROUPING_DESC_CHORDS = True
GROUPING_SHOW_CLEFS = False
GROUPING_UPPERFIRST_NOTEFINGERING = True
GROUPING_WITHHYPHEN = False
GROUPING_NUMREPEATS = 0


def setGroupingGlobals():
    '''
    sets defaults for grouping globals.  Called first time anything
    in Braille is run, but saves creating two expensive objects if never run
    '''
    if GROUPING_GLOBALS['keySignature'] is None:
        # remove noinspection when Python 3.8 is the minimum
        # noinspection PyTypeChecker
        GROUPING_GLOBALS['keySignature'] = key.KeySignature(0)
    if GROUPING_GLOBALS['timeSignature'] is None:
        # remove noinspection when Python 3.8 is the minimum
        # noinspection PyTypeChecker
        GROUPING_GLOBALS['timeSignature'] = meter.TimeSignature('4/4')

# defaults for BrailleSegments


SEGMENT_CANCEL_OUTGOINGKEYSIG = True
SEGMENT_DUMMYRESTLENGTH = None
SEGMENT_LINELENGTH = 40
SEGMENT_SHOWFIRSTMEASURENUMBER = True
SEGMENT_SHOWHAND = None  # override with None, 'left', or 'right'
SEGMENT_SHOWHEADING = True
SEGMENT_SUPPRESSOCTAVEMARKS = False
SEGMENT_ENDHYPHEN = False

SEGMENT_SLURLONGPHRASEWITHBRACKETS = True
SEGMENT_SHOWSHORTSLURSANDTIESTOGETHER = False
SEGMENT_SHOWLONGSLURSANDTIESTOGETHER = False
SEGMENT_MAXNOTESFORSHORTSLUR = 4

MAX_ELEMENTS_IN_SEGMENT = 48  # 8 measures of 6 notes, etc. each


_ThreeDigitNumber = collections.namedtuple('_ThreeDigitNumber', 'hundreds tens ones')

SegmentKey = collections.namedtuple('SegmentKey', 'measure ordinal affinity hand')
SegmentKey.__new__.__defaults__ = (0, 0, None, None)


# ------------------------------------------------------------------------------

class BrailleElementGrouping(ProtoM21Object):
    _DOC_ATTR = {
        'keySignature': 'The last :class:`~music21.key.KeySignature` preceding the grouping.',
        'timeSignature': 'The last :class:`~music21.meter.TimeSignature` preceding the grouping.',
        'descendingChords': '''True if a :class:`~music21.chord.Chord` should be spelled
             from highest to lowest pitch
             in braille, False if the opposite is the case.''',
        'showClefSigns': '''If True, clef signs are shown in braille.
             Representation of music in braille is not
             dependent upon clefs and staves, so the clef signs would be displayed
             for referential or historical purposes.''',
        #         'upperFirstInNoteFingering' : 'No documentation.',
        'withHyphen': 'If True, this grouping will end with a music hyphen.',
        'numRepeats': 'The number of times this grouping is repeated.'
    }
    def __init__(self, *args):
        '''
        A BrailleElementGrouping is a superclass of list of objects which should be displayed
        without a space in braille.

        >>> from music21.braille import segment
        >>> bg = segment.BrailleElementGrouping()
        >>> bg.append(note.Note('C4'))
        >>> bg.append(note.Note('D4'))
        >>> bg.append(note.Rest())
        >>> bg.append(note.Note('F4'))
        >>> bg
        <music21.braille.segment.BrailleElementGrouping [<music21.note.Note C>,
            <music21.note.Note D>, <music21.note.Rest rest>, <music21.note.Note F>]>
        >>> print(bg)
        <music21.note.Note C>
        <music21.note.Note D>
        <music21.note.Rest rest>
        <music21.note.Note F>

        These are the defaults and they are shared across all objects...

        >>> bg.keySignature
        <music21.key.KeySignature of no sharps or flats>
        >>> bg.timeSignature
        <music21.meter.TimeSignature 4/4>

        >>> bg.descendingChords
        True

        >>> bg.showClefSigns
        False

        >>> bg.upperFirstInNoteFingering
        True

        >>> bg.withHyphen
        False

        >>> bg.numRepeats
        0
        '''
        super().__init__()
        self.internalList = list(*args)
        setGroupingGlobals()

        self.keySignature = GROUPING_GLOBALS['keySignature']
        self.timeSignature = GROUPING_GLOBALS['timeSignature']
        self.descendingChords = GROUPING_DESC_CHORDS
        self.showClefSigns = GROUPING_SHOW_CLEFS
        self.upperFirstInNoteFingering = GROUPING_UPPERFIRST_NOTEFINGERING
        self.withHyphen = GROUPING_WITHHYPHEN  # False
        self.numRepeats = GROUPING_NUMREPEATS

    def __getitem__(self, item):
        return self.internalList[item]

    def __setitem__(self, pos, item):
        self.internalList[pos] = item

    def __len__(self):
        return len(self.internalList)

    def __getattr__(self, attr):
        if attr == 'internalList':
            raise AttributeError('internalList not defined yet')
        return getattr(self.internalList, attr)

    def __str__(self):
        '''
        Return an unicode braille representation
        of each object in the BrailleElementGrouping.
        '''
        allObjects = []
        for obj in self:
            if isinstance(obj, stream.Voice):
                for obj2 in obj:
                    try:
                        allObjects.append('\n'.join(obj2.editorial.brailleEnglish))
                    except (AttributeError, TypeError):
                        allObjects.append(str(obj2))
            else:
                try:
                    allObjects.append('\n'.join(obj.editorial.brailleEnglish))
                except (AttributeError, TypeError):
                    allObjects.append(str(obj))
        if self.numRepeats > 0:
            allObjects.append(f'** Grouping x {self.numRepeats + 1} **')
        if self.withHyphen is True:
            allObjects.append(f'music hyphen {lookup.symbols["music_hyphen"]}')
        out = '\n'.join(allObjects)
        return out

    def _reprInternal(self):
        return repr(self.internalList)


class BrailleSegment(text.BrailleText):
    _DOC_ATTR = {
        'cancelOutgoingKeySig': '''If True, the previous key signature should be
                 cancelled immediately before a new key signature is encountered.''',
        'dummyRestLength': '''For a given positive integer n, adds n "dummy rests"
                 near the beginning of a segment. Designed for test purposes, as they
                 are used to demonstrate measure division at the end of braille lines.''',
        'lineLength': '''The maximum amount of braille characters that should be
                 present in a line. The standard is 40 characters.''',
        'showFirstMeasureNumber': '''If True, then a measure number is shown
                 following the heading (if applicable) and preceding the music.''',
        'showHand': '''If set to "right" or "left", shows the corresponding
                 hand sign at the beginning of the first line.''',
        'showHeading': '''If True, then a braille heading is displayed.
                 See :meth:`~music21.braille.basic.transcribeHeading`
                 for more details on headings.''',
        'suppressOctaveMarks': '''If True, then all octave marks are suppressed.
                 Designed for test purposes, as octave marks were not presented
                 until Chapter 7 of BMTM.''',
        'endHyphen': '''If True, then the last
                 :class:`~music21.braille.segment.BrailleElementGrouping` of this
                 segment will be followed by a music hyphen.
                 The last grouping is incomplete, because a segment
                 break occurred in the middle of a measure.''',
        'beginsMidMeasure': '''If True, then the initial measure number of this
                 segment should be followed by a dot. This segment
                 is starting in the middle of a measure.'''
    }

    def __init__(self):
        '''
        A segment is "a group of measures occupying more than one braille line."
        Music is divided into segments so as to "present the music to the reader
        in a meaningful manner and to give him convenient reference points to
        use in memorization" (BMTM, 71).

        >>> brailleSeg = braille.segment.BrailleSegment()

        >>> brailleSeg.cancelOutgoingKeySig
        True
        >>> brailleSeg.dummyRestLength

        >>> brailleSeg.lineLength
        40

        >>> brailleSeg.showFirstMeasureNumber
        True


        Possible showHand values are None, 'right', 'left':

        >>> brailleSeg.showHand is None
        True

        >>> brailleSeg.showHeading
        True

        >>> brailleSeg.suppressOctaveMarks
        False

        >>> brailleSeg.endHyphen
        False

        >>> brailleSeg.beginsMidMeasure
        False


        A BrailleSegment is a type of defaultdict that returns a BrailleElementGrouping
        when a key is missing.

        >>> len(brailleSeg.keys())
        0
        >>> beg = brailleSeg[braille.segment.SegmentKey(4, 1, 9)]
        >>> type(beg) is braille.segment.BrailleElementGrouping
        True


        Of course, creating random keys like this will have consequences:

        >>> print(str(brailleSeg))
        ---begin segment---
        <music21.braille.segment BrailleSegment>
        Measure 4, Note Grouping 2:
        <BLANKLINE>
        ===
        ---end segment---
        '''
        super().__init__(lineLength=SEGMENT_LINELENGTH)
        self._groupingDict = {}

        self.groupingKeysToProcess = None
        self.currentGroupingKey = None
        self.lastNote = None
        self.previousGroupingKey = None

        self.cancelOutgoingKeySig = SEGMENT_CANCEL_OUTGOINGKEYSIG
        self.dummyRestLength = SEGMENT_DUMMYRESTLENGTH
        self.showFirstMeasureNumber = SEGMENT_SHOWFIRSTMEASURENUMBER
        self.showHand = SEGMENT_SHOWHAND
        self.showHeading = SEGMENT_SHOWHEADING
        self.suppressOctaveMarks = SEGMENT_SUPPRESSOCTAVEMARKS
        self.endHyphen = SEGMENT_ENDHYPHEN
        self.beginsMidMeasure = False

    def __setitem__(self, item, value):
        self._groupingDict[item] = value

    def __getitem__(self, item):
        if item not in self._groupingDict:
            self._groupingDict[item] = BrailleElementGrouping()
        return self._groupingDict[item]

    def __delitem__(self, item):
        if item not in self.__dict__:
            del self._groupingDict[item]
        else:
            return ValueError(f'No item {item!r} in Segment')

    def __getattr__(self, item):
        return getattr(self._groupingDict, item)

    def __contains__(self, item):
        return item in self._groupingDict

    def __iter__(self):
        return iter(self._groupingDict)

    def __len__(self):
        return len(self._groupingDict)

    @property
    def brailleText(self):
        '''
        Returns the string from the BrailleText object
        '''
        return text.BrailleText.__str__(self)

    def __str__(self):
        name = '<music21.braille.segment BrailleSegment>'

        allItems = sorted(self.items())
        allKeys = []
        allGroupings = []
        # noinspection PyArgumentList
        prevKey = SegmentKey()  # defaults are defined.

        for (itemKey, grouping) in allItems:
            try:
                if prevKey.affinity == Affinity.SPLIT1_NOTEGROUP:
                    prevKey = itemKey
                    continue
            except TypeError:
                pass
            allKeys.append('Measure {0}, {1} {2}:\n'.format(itemKey.measure,
                                                             affinityNames[itemKey.affinity],
                                                             itemKey.ordinal + 1))
            gStr = str(grouping)
            allGroupings.append(gStr)
            prevKey = itemKey
        allElementGroupings = '\n'.join([''.join([k, g, '\n==='])
                                          for (k, g) in list(zip(allKeys, allGroupings))])
        out = '\n'.join(['---begin segment---',
                          name,
                          allElementGroupings,
                          '---end segment---'])
        return out

    def transcribe(self):
        '''
        transcribes all of the noteGroupings in this dict by:

        first transcribing the Heading (if applicable)
        then the Measure Number
        then adds appropriate numbers of dummyRests
        then adds the Rest of the Note Groupings

        returns brailleText
        '''
        # noinspection PyAttributeOutsideInit
        self.groupingKeysToProcess = list(sorted(self.keys()))

        if self.showHeading:
            self.extractHeading()  # Heading

        if self.showFirstMeasureNumber:
            self.extractMeasureNumber()  # Measure Number

        if self.dummyRestLength is not None:
            self.addDummyRests()  # Dummy Rests

        self.previousGroupingKey = None
        while self.groupingKeysToProcess:
            # noinspection PyAttributeOutsideInit
            self.currentGroupingKey = self.groupingKeysToProcess.pop(0)

            cgkAffinityGroup = self.currentGroupingKey.affinity

            if cgkAffinityGroup == Affinity.NOTEGROUP:
                self.extractNoteGrouping()  # Note Grouping
            elif cgkAffinityGroup == Affinity.SIGNATURE:
                self.extractSignatureGrouping()  # Signature(s) Grouping
            elif cgkAffinityGroup == Affinity.LONG_TEXTEXPR:
                self.extractLongExpressionGrouping()  # Long Expression(s) Grouping
            # elif cgkAffinityGroup == Affinity.INACCORD:
            #     self.extractInaccordGrouping()  # In Accord Grouping
            elif cgkAffinityGroup == Affinity.TTEXT:
                self.extractTempoTextGrouping()  # Tempo Text Grouping
            # noinspection PyAttributeOutsideInit
            self.previousGroupingKey = self.currentGroupingKey

        return self.brailleText

    def addDummyRests(self):
        '''
        Adds as many dummy rests as self.dummyRestLength to the signatures of
        brailleText

        >>> seg = braille.segment.BrailleSegment()
        >>> seg.dummyRestLength = 4

        >>> print(braille.lookup.rests['dummy'])
        ⠄
        >>> seg.addDummyRests()
        >>> print(seg.brailleText)
        ⠄⠄⠄⠄
        '''
        dummyRests = [self.dummyRestLength * lookup.rests['dummy']]
        self.addSignatures(''.join(dummyRests))

    def extractMeasureNumber(self):
        '''
        Adds a measure number from the segmentKey needing processing

        >>> segKey = braille.segment.SegmentKey(measure=4, ordinal=1, affinity=9)
        >>> seg = braille.segment.BrailleSegment()

        Initialize a new Key

        >>> type(seg[segKey])
        <class 'music21.braille.segment.BrailleElementGrouping'>
        >>> seg.extractMeasureNumber()
        >>> print(seg.brailleText)
        ⠼⠙

        Add a dot to the measure number if the segment begins mid-measure

        >>> seg = braille.segment.BrailleSegment()
        >>> seg[segKey]
        <music21.braille.segment.BrailleElementGrouping []>

        >>> seg.beginsMidMeasure = True
        >>> seg.extractMeasureNumber()
        >>> print(seg.brailleText)
        ⠼⠙⠄
        '''
        gkp = self.groupingKeysToProcess or sorted(self.keys())
        firstSegmentKey = gkp[0]
        initMeasureNumber = firstSegmentKey.measure
        brailleNumber = basic.numberToBraille(initMeasureNumber)
        if self.beginsMidMeasure:
            brailleNumber += symbols['dot']

        self.addMeasureNumber(brailleNumber)

    def extractHeading(self):
        '''
        Extract a :class:`~music21.key.KeySignature`, :class:`~music21.meter.TimeSignature,
        :class:`~music21.tempo.TempoText` and :class:`~music21.tempo.MetronomeMark` and
        add an appropriate braille heading to the brailleText object inputted.
        '''
        keySignature = None
        timeSignature = None
        tempoText = None
        metronomeMark = None
        # find the first keySignature and timeSignature...

        groupingKeysToProcess = self.groupingKeysToProcess or sorted(self.keys())

        while groupingKeysToProcess:
            if groupingKeysToProcess[0].affinity > Affinity.MMARK:
                break
            cgk = groupingKeysToProcess.pop(0)  # cgk = currentGroupingKey

            cgkAffinityGroup = cgk.affinity
            currentBrailleGrouping = self._groupingDict.get(cgk)  # currentGrouping...

            if cgkAffinityGroup == Affinity.SIGNATURE:
                if len(currentBrailleGrouping) >= 2:
                    keySignature, timeSignature = (currentBrailleGrouping[0],
                                                   currentBrailleGrouping[1])
                elif len(currentBrailleGrouping) == 1:
                    keyOrTimeSig = currentBrailleGrouping[0]
                    if isinstance(keyOrTimeSig, key.KeySignature):
                        keySignature = keyOrTimeSig
                    else:
                        timeSignature = keyOrTimeSig
            elif cgkAffinityGroup == Affinity.TTEXT:
                tempoText = currentBrailleGrouping[0]
            elif cgkAffinityGroup == Affinity.MMARK:
                metronomeMark = currentBrailleGrouping[0]

        if any([keySignature, timeSignature, tempoText, metronomeMark]):
            brailleHeading = basic.transcribeHeading(
                keySignature,
                timeSignature,
                tempoText,
                metronomeMark,
                maxLineLength=self.lineLength
            )
            self.addHeading(brailleHeading)


    # def extractInaccordGrouping(self):
    #     inaccords = self._groupingDict.get(self.currentGroupingKey)
    #     voice_trans = []
    #     for music21Voice in inaccords:
    #         noteGrouping = extractBrailleElements(music21Voice)
    #         noteGrouping.descendingChords = inaccords.descendingChords
    #         noteGrouping.showClefSigns = inaccords.showClefSigns
    #         noteGrouping.upperFirstInNoteFingering = inaccords.upperFirstInNoteFingering
    #         voice_trans.append(ngMod.transcribeNoteGrouping(noteGrouping))
    #     brailleInaccord = symbols['full_inaccord'].join(voice_trans)
    #     self.addInaccord(brailleInaccord)


    def extractLongExpressionGrouping(self):
        '''
        Extract the Long Expression that is in the ElementGrouping in cgk
        and add it to brailleText.
        '''
        cgk = self.currentGroupingKey
        currentElementGrouping = self._groupingDict.get(cgk)
        longTextExpression = currentElementGrouping[0]
        longExprInBraille = basic.textExpressionToBraille(longTextExpression)
        self.addLongExpression(longExprInBraille)

    def showLeadingOctaveFromNoteGrouping(self, noteGrouping):
        '''
        Given a noteGrouping, should we show the octave symbol?

        >>> n1 = note.Note('C1')
        >>> n2 = note.Note('D1')
        >>> n3 = note.Note('E1')

        >>> beg1 = braille.segment.BrailleElementGrouping([n1, n2, n3])
        >>> bs1 = braille.segment.BrailleSegment()

        This is True because last note is None

        >>> bs1.lastNote is None
        True
        >>> bs1.showLeadingOctaveFromNoteGrouping(beg1)
        True

        But if we run it again, now we have a note within a fourth, so we do not
        need to show the octave:

        >>> bs1.lastNote
        <music21.note.Note E>
        >>> bs1.showLeadingOctaveFromNoteGrouping(beg1)
        False

        And that is true no matter how many ties we call it on the same
        BrailleElementGrouping:

        >>> bs1.showLeadingOctaveFromNoteGrouping(beg1)
        False

        But if we give a new, much higher BrailleElementGrouping, we
        will see octave marks again.

        >>> nHigh1 = note.Note('C6')
        >>> nHigh2 = note.Note('D6')
        >>> beg2 = braille.segment.BrailleElementGrouping([nHigh1, nHigh2])
        >>> bs1.showLeadingOctaveFromNoteGrouping(beg2)
        True

        But if we set `self.suppressOctaveMarks` to True, we won't see any
        when we switch back to beg1:

        >>> bs1.suppressOctaveMarks = True
        >>> bs1.showLeadingOctaveFromNoteGrouping(beg2)
        False


        We also show octaves if for some reason two noteGroups in the same measure have
        different BrailleElementGroupings keyed to consecutive ordinals.  The code simulates
        that situation.

        >>> bs1.suppressOctaveMarks = False
        >>> bs1.previousGroupingKey = braille.segment.SegmentKey(measure=3, ordinal=1,
        ...                                          affinity=braille.segment.Affinity.NOTEGROUP)
        >>> bs1.currentGroupingKey = braille.segment.SegmentKey(measure=3, ordinal=2,
        ...                                          affinity=braille.segment.Affinity.NOTEGROUP)
        >>> bs1.showLeadingOctaveFromNoteGrouping(beg2)
        True
        >>> bs1.showLeadingOctaveFromNoteGrouping(beg1)
        True
        >>> bs1.showLeadingOctaveFromNoteGrouping(beg1)
        True

        '''
        currentKey = self.currentGroupingKey
        previousKey = self.previousGroupingKey

        # if the previousKey did not exist
        # or if the previousKey was not a collection of notes,
        # or if the currentKey is split from the previous key for some reason
        # while remaining in the same measure, then the lastNote is irrelevant
        if (previousKey is not None
                and currentKey is not None):
            if (previousKey.affinity != Affinity.NOTEGROUP
                or currentKey.affinity != Affinity.NOTEGROUP
                or (currentKey.measure == previousKey.measure
                    and currentKey.ordinal == previousKey.ordinal + 1
                    and currentKey.hand == previousKey.hand)):
                self.lastNote = None

        if self.suppressOctaveMarks:
            return False

        # can't use Filter because noteGrouping is list-like not Stream-like
        allNotes = [n for n in noteGrouping if 'Note' in n.classes]
        showLeadingOctave = True
        if allNotes:
            if self.lastNote is not None:
                firstNote = allNotes[0]
                showLeadingOctave = basic.showOctaveWithNote(self.lastNote, firstNote)
            # noinspection PyAttributeOutsideInit
            self.lastNote = allNotes[-1]  # probably should not be here...

        return showLeadingOctave

    def needsSplitToFit(self, brailleNoteGrouping) -> bool:
        '''
        Returns boolean on whether a note grouping needs to be split in order to fit.

        Generally a noteGrouping will need to be split if the amount of space left
        is more than 1/4 of the line length and the brailleNoteGrouping cannot fit.

        >>> n1 = note.Note('C1')
        >>> n2 = note.Note('D1')
        >>> n3 = note.Note('E1')

        >>> beg1 = braille.segment.BrailleElementGrouping([n1, n2, n3])
        >>> seg = braille.segment.BrailleSegment()
        >>> seg.needsSplitToFit(beg1)
        False
        >>> seg.lineLength = 10
        >>> seg.needsSplitToFit(beg1)
        True
        '''
        quarterLineLength = self.lineLength // 4
        spaceLeft = self.lineLength - self.currentLine.textLocation
        if (spaceLeft > quarterLineLength
                and len(brailleNoteGrouping) > quarterLineLength):
            return True
        else:
            return False

    def splitNoteGroupingAndTranscribe(self,
                                       noteGrouping,
                                       showLeadingOctaveOnFirst=False,
                                       addSpaceToFirst=False):
        '''
        Take a noteGrouping and split it at a logical place,
        returning braille transcriptions of each section.
        '''
        transcriber = ngMod.NoteGroupingTranscriber()

        beatDivisionOffset = 0
        REASONABLE_LIMIT = 10
        (splitNoteGroupA, splitNoteGroupB) = (None, None)
        brailleNoteGroupingA = None

        while beatDivisionOffset < REASONABLE_LIMIT:
            (splitNoteGroupA, splitNoteGroupB) = splitNoteGrouping(
                noteGrouping,
                beatDivisionOffset=beatDivisionOffset
            )
            transcriber.showLeadingOctave = showLeadingOctaveOnFirst
            splitNoteGroupA.withHyphen = True
            brailleNoteGroupingA = transcriber.transcribeGroup(splitNoteGroupA)
            if self.currentLine.canAppend(brailleNoteGroupingA, addSpace=addSpaceToFirst):
                break

            beatDivisionOffset += 1
            continue

        showLeadingOctave = not self.suppressOctaveMarks
        transcriber.showLeadingOctave = showLeadingOctave
        brailleNoteGroupingB = transcriber.transcribeGroup(splitNoteGroupB)

        currentKey = self.currentGroupingKey

        # noinspection PyProtectedMember
        aKey = currentKey._replace(affinity=Affinity.SPLIT1_NOTEGROUP)
        # noinspection PyProtectedMember
        bKey = currentKey._replace(affinity=Affinity.SPLIT2_NOTEGROUP)

        self[aKey] = splitNoteGroupA
        self[bKey] = splitNoteGroupB

        return (brailleNoteGroupingA, brailleNoteGroupingB)

    def extractNoteGrouping(self):
        '''
        Fundamentally important method that adds a noteGrouping to the braille line.
        '''
        transcriber = ngMod.NoteGroupingTranscriber()
        noteGrouping = self._groupingDict.get(self.currentGroupingKey)

        showLeadingOctave = self.showLeadingOctaveFromNoteGrouping(noteGrouping)
        transcriber.showLeadingOctave = showLeadingOctave
        brailleNoteGrouping = transcriber.transcribeGroup(noteGrouping)

        addSpace = self.optionalAddKeyboardSymbolsAndDots(brailleNoteGrouping)

        if self.currentLine.canAppend(brailleNoteGrouping, addSpace=addSpace):
            self.currentLine.append(brailleNoteGrouping, addSpace=addSpace)
        else:
            if self.needsSplitToFit(brailleNoteGrouping):
                # there is too much space left in the current line to leave it blank
                # but not enough space left to insert the current brailleNoteGrouping
                # hence -- let us split this noteGrouping into two noteGroupings.
                bngA, bngB = self.splitNoteGroupingAndTranscribe(noteGrouping,
                                                                 showLeadingOctave,
                                                                 addSpace)
                self.currentLine.append(bngA, addSpace=addSpace)
                self.addToNewLine(bngB)

            else:
                # not enough space left on this line to use, so
                # move the whole group to another line
                if showLeadingOctave is False and self.suppressOctaveMarks is False:
                    # if we didn't show the octave before, retranscribe with the octave
                    # displayed
                    transcriber.showLeadingOctave = True
                    brailleNoteGrouping = transcriber.transcribeGroup(noteGrouping)
                # if not forceHyphen:
                self.currentLine.lastHyphenToSpace()
                self.addToNewLine(brailleNoteGrouping)

        self.addRepeatSymbols(noteGrouping.numRepeats)

    def addRepeatSymbols(self, repeatTimes):
        '''
        Adds the appropriate number of repeat symbols, following DeGarmo chapter 17.

        >>> seg = braille.segment.BrailleSegment()
        >>> seg.addRepeatSymbols(0)
        >>> print(seg.brailleText)
        >>> seg.addRepeatSymbols(1)
        >>> print(seg.brailleText)
        ⠶

        >>> seg = braille.segment.BrailleSegment()
        >>> seg.addRepeatSymbols(2)
        >>> print(seg.brailleText)
        ⠶⠀⠶

        >>> seg = braille.segment.BrailleSegment()
        >>> seg.addRepeatSymbols(3)
        >>> print(seg.brailleText)
        ⠶⠼⠉

        Does not yet handle situations beginning with Example 17-6 (repeats at
        different octaves), and further
        '''
        if 0 < repeatTimes < 3:
            for unused_repeatCounter in range(repeatTimes):
                self.addSignatures(symbols['repeat'])
        elif repeatTimes >= 3:  # 17.3 -- repeat plus number.
            self.addSignatures(symbols['repeat'] + basic.numberToBraille(repeatTimes))
            # noinspection PyAttributeOutsideInit
            self.lastNote = None  # this is set up to force an octave symbol on next note

    def extractSignatureGrouping(self):
        '''
        Extracts a key signature, time signature, and possibly an outgoing key signature
        from the currentGroupingKey and adds it to the BrailleText object.
        '''
        keySignature = None
        timeSignature = None

        cgk = self.currentGroupingKey
        noteGrouping = self._groupingDict.get(cgk)

        if len(noteGrouping) >= 2:
            keySignature, timeSignature = noteGrouping[0], noteGrouping[1]
        elif len(noteGrouping) == 1:
            keyOrTimeSig = self._groupingDict.get(self.currentGroupingKey)[0]
            if isinstance(keyOrTimeSig, key.KeySignature):
                keySignature = keyOrTimeSig
            else:
                timeSignature = keyOrTimeSig

        outgoingKeySig = None
        if self.cancelOutgoingKeySig and keySignature is not None:
            try:
                outgoingKeySig = keySignature.outgoingKeySig
            except AttributeError:
                pass

        brailleSig = basic.transcribeSignatures(keySignature, timeSignature, outgoingKeySig)
        if brailleSig != '':
            self.addSignatures(brailleSig)

    def extractTempoTextGrouping(self):
        '''
        extracts a tempo text and processes it...
        '''
        self.groupingKeysToProcess.insert(0, self.currentGroupingKey)
        if self.previousGroupingKey.affinity == Affinity.SIGNATURE:
            self.groupingKeysToProcess.insert(0, self.previousGroupingKey)
        self.extractHeading()
        self.extractMeasureNumber()

    def consolidate(self):
        '''
        Puts together certain types of elements according to the last digit of their key
        (if it is the same as Affinity.NOTEGROUP or not.

        >>> SK = braille.segment.SegmentKey
        >>> BS1 = braille.segment.BrailleSegment()
        >>> BS1[SK(ordinal=0, affinity=2)] = ['hi', 'hello', 'there']
        >>> BS1[SK(ordinal=1, affinity=9)] = ['these', 'get']
        >>> BS1[SK(ordinal=2, affinity=9)] = ['put', 'together']
        >>> BS1[SK(ordinal=3, affinity=4)] = ['in', 'new', 'group']
        >>> BS1[SK(ordinal=4, affinity=9)] = ['with', 'the', 'previous']
        >>> BS2 = BS1.consolidate()
        >>> for (groupingKey, groupingList) in sorted(BS2.items()):
        ...     print(groupingKey, groupingList)
        SegmentKey(measure=0, ordinal=0, affinity=2, hand=None) ['hi', 'hello', 'there']
        SegmentKey(measure=0, ordinal=1, affinity=9, hand=None) these
        get
        put
        together
        SegmentKey(measure=0, ordinal=3, affinity=4, hand=None) ['in', 'new', 'group']
        SegmentKey(measure=0, ordinal=4, affinity=9, hand=None) with
        the
        previous
        '''
        newSegment = BrailleSegment()
        pngKey = None
        for (groupingKey, groupingList) in sorted(self.items()):
            if groupingKey.affinity != Affinity.NOTEGROUP:
                newSegment[groupingKey] = groupingList
                pngKey = None
            else:
                if pngKey is None:
                    pngKey = groupingKey
                for item in groupingList:
                    newSegment[pngKey].append(item)
        return newSegment

    def addGroupingAttributes(self, **partKeywords):
        '''
        Modifies the attributes of all :class:`~music21.braille.segment.BrailleElementGrouping`
        instances in a list of :class:`~music21.braille.segment.BrailleSegment` instances. The
        necessary information is retrieved both by passing in partKeywords as an argument and
        by taking into account the linear progression of the groupings and segments.
        '''
        currentKeySig = key.KeySignature(0)
        currentTimeSig = meter.TimeSignature('4/4')

        descendingChords = GROUPING_DESC_CHORDS
        showClefSigns = GROUPING_SHOW_CLEFS
        upperFirstInNoteFingering = GROUPING_UPPERFIRST_NOTEFINGERING

        if 'showClefSigns' in partKeywords:
            showClefSigns = partKeywords['showClefSigns']
        if 'upperFirstInNoteFingering' in partKeywords:
            upperFirstInNoteFingering = partKeywords['upperFirstInNoteFingering']
        if 'descendingChords' in partKeywords:
            descendingChords = partKeywords['descendingChords']

        allGroupings = sorted(self.items())
        (previousKey, previousList) = (None, None)

        for (groupingKey, groupingList) in allGroupings:
            if previousKey is not None:
                if groupingKey.ordinal >= 1:
                    previousList.withHyphen = True
                if (previousKey.ordinal == 0
                        and previousKey.affinity == Affinity.NOTEGROUP
                        and groupingKey.ordinal == 0
                        and groupingKey.affinity == Affinity.NOTEGROUP):
                    if isinstance(previousList[0], clef.Clef):
                        isRepetition = areGroupingsIdentical(previousList[1:], groupingList)
                    else:
                        isRepetition = areGroupingsIdentical(previousList, groupingList)
                    if isRepetition:
                        previousList.numRepeats += 1
                        del self[groupingKey]
                        continue
            if groupingKey.affinity == Affinity.SIGNATURE:
                for brailleElement in groupingList:
                    if isinstance(brailleElement, meter.TimeSignature):
                        currentTimeSig = brailleElement
                    elif isinstance(brailleElement, key.KeySignature):
                        brailleElement.outgoingKeySig = currentKeySig
                        currentKeySig = brailleElement
            elif groupingKey.affinity == Affinity.NOTEGROUP:
                if isinstance(groupingList[0], clef.Clef):
                    if isinstance(groupingList[0], (clef.TrebleClef, clef.AltoClef)):
                        descendingChords = True
                    elif isinstance(groupingList[0], (clef.BassClef, clef.TenorClef)):
                        descendingChords = False

                # make a whole rest no matter the length of the rest if only one note.
                allGeneralNotes = [n for n in groupingList if isinstance(n, note.GeneralNote)]
                if len(allGeneralNotes) == 1 and isinstance(allGeneralNotes[0], note.Rest):
                    allGeneralNotes[0].fullMeasure = True
            groupingList.keySignature = currentKeySig
            groupingList.timeSignature = currentTimeSig
            groupingList.descendingChords = descendingChords
            groupingList.showClefSigns = showClefSigns
            groupingList.upperFirstInNoteFingering = upperFirstInNoteFingering
            (previousKey, previousList) = (groupingKey, groupingList)
        if self.endHyphen:
            previousList.withHyphen = True

    def addSegmentAttributes(self, **partKeywords):
        '''
        Modifies the attributes of a :class:`~music21.braille.segment.BrailleSegment`
        by passing partKeywords as an argument.
        '''
        if 'cancelOutgoingKeySig' in partKeywords:
            self.cancelOutgoingKeySig = partKeywords['cancelOutgoingKeySig']
        if 'dummyRestLength' in partKeywords:
            self.dummyRestLength = partKeywords['dummyRestLength']
        if 'lineLength' in partKeywords:
            self.lineLength = partKeywords['lineLength']
        if 'showFirstMeasureNumber' in partKeywords:
            self.showFirstMeasureNumber = partKeywords['showFirstMeasureNumber']
        if 'showHand' in partKeywords:
            self.showHand = partKeywords['showHand']
        if 'showHeading' in partKeywords:
            self.showHeading = partKeywords['showHeading']
        if 'suppressOctaveMarks' in partKeywords:
            self.suppressOctaveMarks = partKeywords['suppressOctaveMarks']

    def fixArticulations(self):
        '''
        Goes through each :class:`~music21.braille.segment.BrailleSegment` and modifies the
        list of :attr:`~music21.note.GeneralNote.articulations` of a :class:`~music21.note.Note`
        if appropriate. In particular, two rules are applied:

        * Doubling rule => If four or more of the same :class:`~music21.articulations.Articulation`
          are found in a row, the first instance of the articulation is doubled and the rest are
          omitted.

        * Staccato, Tenuto rule => "If two repeated notes appear to be tied, but either is marked
          staccato or tenuto, they are treated as slurred instead of tied." (BMTM, 112)
        '''
        from music21 import articulations

        def fixOneArticulation(artic, music21NoteStart, allNotes, noteIndexStart):
            articName = artic.name
            if articName == 'fingering':  # fingerings are not considered articulations...
                return
            if (isinstance(artic, (articulations.Staccato, articulations.Tenuto))
                    and music21NoteStart.tie is not None):
                if music21NoteStart.tie.type == 'stop':
                    allNotes[noteIndexStart - 1].tie = None
                    allNotes[noteIndexStart - 1].shortSlur = True
                else:
                    allNotes[noteIndexStart + 1].tie = None
                    music21NoteStart.shortSlur = True
                music21NoteStart.tie = None
            numSequential = 0
            for noteIndexContinue in range(noteIndexStart + 1, len(allNotes)):
                music21NoteContinue = allNotes[noteIndexContinue]
                if articName in [a.name for a in music21NoteContinue.articulations]:
                    numSequential += 1
                    continue
                break
            if numSequential < 3:
                return
            # else:
            # double the articulation on the first note and remove from the next...
            music21NoteStart.articulations.append(artic)
            for noteIndexContinue in range(noteIndexStart + 1,
                                           noteIndexStart + numSequential):
                music21NoteContinue = allNotes[noteIndexContinue]
                for artOther in music21NoteContinue.articulations:
                    if artOther.name == articName:
                        music21NoteContinue.articulations.remove(artOther)

        newSegment = self.consolidate()
        noteGroupings = [newSegment[gpKey]
                             for gpKey in newSegment.keys()
                                if gpKey.affinity == Affinity.NOTEGROUP]
        for noteGrouping in noteGroupings:
            allNotes_outer = [n for n in noteGrouping if isinstance(n, note.Note)]
            for noteIndexStart_outer in range(len(allNotes_outer)):
                music21NoteStart_outer = allNotes_outer[noteIndexStart_outer]
                for artic_outer in music21NoteStart_outer.articulations:
                    fixOneArticulation(
                        artic_outer,
                        music21NoteStart_outer,
                        allNotes_outer,
                        noteIndexStart_outer
                    )


class BrailleGrandSegment(BrailleSegment, text.BrailleKeyboard):
    '''
    A BrailleGrandSegment represents a pair of segments (rightSegment, leftSegment)
    representing the right and left hands of a piano staff (or other two-staff object)
    '''
    def __init__(self):
        BrailleSegment.__init__(self)
        text.BrailleKeyboard.__init__(self, lineLength=SEGMENT_LINELENGTH)
        self.allKeyPairs = []
        self.previousGroupingPair = None
        self.currentGroupingPair = None

    @property
    def brailleText(self):
        return text.BrailleKeyboard.__str__(self)

    def __str__(self):
        name = '<music21.braille.segment BrailleGrandSegment>\n==='
        allPairs = []
        for (rightKey, leftKey) in self.yieldCombinedGroupingKeys():
            if rightKey is not None:
                rightHeading = 'Measure {0} Right, {1} {2}:\n'.format(
                    rightKey.measure, affinityNames[rightKey.affinity], rightKey.ordinal + 1)
                rightContents = str(self._groupingDict.get(rightKey))
                rightFull = ''.join([rightHeading, rightContents])
            else:
                rightFull = ''
            if leftKey is not None:
                leftHeading = '\nMeasure {0} Left, {1} {2}:\n'.format(
                    leftKey.measure, affinityNames[leftKey.affinity], leftKey.ordinal + 1)
                leftContents = str(self._groupingDict.get(leftKey))
                leftFull = ''.join([leftHeading, leftContents])
            else:
                leftFull = ''
            allPairs.append('\n'.join([rightFull, leftFull, '====\n']))
        out = '\n'.join(['---begin grand segment---', name, ''.join(allPairs),
                           '---end grand segment---'])
        return out

    def yieldCombinedGroupingKeys(self):
        '''
        yields all the keys in order as a tuple of (rightKey, leftKey) where
        two keys are grouped if they have the same segmentKey except for the hand.

        >>> bgs = braille.segment.BrailleGrandSegment()
        >>> SegmentKey = braille.segment.SegmentKey  # namedtuple
        >>> bgs[SegmentKey(1, 1, 1, 'right')] = '1r'
        >>> bgs[SegmentKey(1, 1, 1, 'left')]  = '1l'
        >>> bgs[SegmentKey(1, 2, 3, 'right')] = '2r'
        >>> bgs[SegmentKey(1, 2, 4, 'left')] = '3l'
        >>> bgs[SegmentKey(2, 1, 9, 'left')] = '4l'
        >>> bgs[SegmentKey(2, 1, 9, 'right')] = '4r'
        >>> bgs[SegmentKey(3, 1, 9, 'right')] = '5r'
        >>> for l, r in bgs.yieldCombinedGroupingKeys():
        ...     (bgs[l], bgs[r])
        ('1r', '1l')
        ('2r', <music21.braille.segment.BrailleElementGrouping []>)
        (<music21.braille.segment.BrailleElementGrouping []>, '3l')
        ('4r', '4l')
        ('5r', <music21.braille.segment.BrailleElementGrouping []>)
        '''
        def segmentKeySortKey(segmentKey):
            '''
            sort by measure, then ordinal, then affinity, then hand (r then l)
            '''
            if segmentKey.hand == 'right':
                skH = -1
            else:
                skH = 1
            return (segmentKey.measure, segmentKey.ordinal, segmentKey.affinity, skH)

        def matchOther(thisKey_inner, otherKey):
            if (thisKey_inner.measure == otherKey.measure
                    and thisKey_inner.ordinal == otherKey.ordinal
                    and thisKey_inner.affinity == otherKey.affinity):
                return True
            else:
                return False

        storedRight = None
        storedLeft = None
        for thisKey in sorted(self.keys(), key=segmentKeySortKey):
            if thisKey.hand == 'right':
                if storedLeft is not None:
                    if matchOther(thisKey, storedLeft):
                        yield(thisKey, storedLeft)
                    elif (thisKey.affinity == Affinity.NOTEGROUP
                          and matchOther(thisKey._replace(affinity=Affinity.INACCORD), storedLeft)):
                        # r.h. notegroup goes before an lh inaccord, despite this being out of order
                        yield(thisKey, storedLeft)
                    else:
                        yield(None, storedLeft)
                        storedRight = thisKey
                    storedLeft = None
                else:
                    storedRight = thisKey
            elif thisKey.hand == 'left':
                if storedRight is not None:
                    if matchOther(thisKey, storedRight):
                        yield(storedRight, thisKey)
                    elif storedRight.affinity < Affinity.INACCORD:
                        yield(storedRight, None)
                        yield(None, thisKey)
                    else:
                        yield(storedRight, None)
                        storedLeft = thisKey
                    storedRight = None
                else:
                    storedLeft = thisKey

        if storedRight:
            yield (storedRight, None)
        if storedLeft:
            yield (None, storedLeft)

    # def combineGroupingKeys(self, rightSegment, leftSegment):
    #     # return list(self.yieldCombinedGroupingKeys())
    #
    #     groupingKeysRight = sorted(rightSegment.keys())
    #     groupingKeysLeft = sorted(leftSegment.keys())
    #     combinedGroupingKeys = []
    #
    #     while groupingKeysRight:
    #         gkRight = groupingKeysRight.pop(0)
    #         try:
    #             groupingKeysLeft.remove(gkRight)
    #             combinedGroupingKeys.append((gkRight, gkRight))
    #         except ValueError:
    #             if gkRight.affinity < Affinity.INACCORD:
    #                 combinedGroupingKeys.append((gkRight, None))
    #             else:
    #                 if gkRight.affinity == Affinity.INACCORD:
    #                     gkLeft = gkRight._replace(affinity=gkRight.affinity + 1)
    #                 else:
    #                     gkLeft = gkRight._replace(affinity=gkRight.affinity - 1)
    #                 try:
    #                     groupingKeysLeft.remove(gkLeft)
    #                 except ValueError:
    #                     raise BrailleSegmentException(
    #                         'Misaligned braille groupings: ' +
    #                         'groupingKeyLeft was %s' % gkLeft +
    #                         'groupingKeyRight was %s' % gkRight +
    #                         'rightSegment was %s, leftSegment was %s' %
    #                                    (rightSegment, leftSegment))
    #
    #                 try:
    #                     combinedGroupingTuple = (gkRight, gkLeft)
    #                     combinedGroupingKeys.append(combinedGroupingTuple)
    #                 except ValueError:
    #                     raise BrailleSegmentException(
    #                         'Misaligned braille groupings could not append combinedGroupingKeys')
    #
    #
    #     while groupingKeysLeft:
    #         gkLeft = groupingKeysLeft.pop(0)
    #         combinedGroupingTuple = (None, gkLeft)
    #         combinedGroupingKeys.append(combinedGroupingTuple)
    #
    #     return combinedGroupingKeys


    def transcribe(self):
        '''
        Returns the BrailleText from the combined grouping keys
        '''
        self.allKeyPairs = list(self.yieldCombinedGroupingKeys())
        lastPair = self.allKeyPairs[-1]
        highestMeasure = lastPair[0].measure if lastPair[0] else lastPair[1].measure
        self.highestMeasureNumberLength = len(str(highestMeasure))

        self.extractHeading()  # Heading
        self.currentGroupingPair = None
        while self.allKeyPairs:
            self.previousGroupingPair = self.currentGroupingPair
            self.currentGroupingPair = self.allKeyPairs.pop(0)
            (rightKey, leftKey) = self.currentGroupingPair

            if ((rightKey is not None and rightKey.affinity >= Affinity.INACCORD)
                    or (leftKey is not None and leftKey.affinity >= Affinity.INACCORD)):
                self.extractNoteGrouping()  # Note or Inaccord Grouping
            # elif (rightKey.affinity == Affinity.SIGNATURE
            #        or leftKey.affinity == Affinity.SIGNATURE):
            #     self.extractSignatureGrouping()  # Signature Grouping
            # elif (rightKey.affinity == Affinity.LONG_TEXTEXPR
            #        or leftKey.affinity == Affinity.LONG_TEXTEXPR):
            #     self.extractLongExpressionGrouping()  # Long Expression Grouping
            # elif rightKey.affinity == Affinity.TTEXT or leftKey.affinity == Affinity.TTEXT:
            #     self.extractTempoTextGrouping()  # Tempo Text Grouping
        return self.brailleText

    def extractHeading(self):
        '''
        Finds KeySignatures, TimeSignatures, TempoText, and Metronome Marks
        within the keyPairs, and removes some from allKeyPairs.
        '''
        keySignature = None
        timeSignature = None
        tempoText = None
        metronomeMark = None

        while True:
            (rightKey, leftKey) = self.allKeyPairs[0]
            useKey = rightKey
            try:
                useElement = self._groupingDict.get(rightKey)
            except KeyError as ke:
                if ke.args[0] == 'None':
                    useElement = self._groupingDict.get(leftKey)
                    useKey = leftKey
                else:
                    raise ke
            if useKey.affinity > Affinity.MMARK:
                break
            self.allKeyPairs.pop(0)
            if useKey.affinity == Affinity.SIGNATURE:
                try:
                    keySignature, timeSignature = useElement[0], useElement[1]
                except IndexError:
                    if isinstance(useElement, key.KeySignature):
                        keySignature = useElement[0]
                    else:
                        timeSignature = useElement[0]
            elif useKey.affinity == Affinity.TTEXT:
                tempoText = useElement[0]
            elif useKey.affinity == Affinity.MMARK:
                metronomeMark = useElement[0]

        try:
            brailleHeading = basic.transcribeHeading(
                keySignature,
                timeSignature,
                tempoText,
                metronomeMark,
                maxLineLength=self.lineLength
            )
            self.addHeading(brailleHeading)
        except basic.BrailleBasicException as bbe:
            if bbe.args[0] != 'No heading can be made.':
                raise bbe

    def extractNoteGrouping(self):
        (rightKey, leftKey) = self.currentGroupingPair
        if rightKey:
            mNum = rightKey.measure
        elif leftKey:
            mNum = leftKey.measure
        else:
            raise ValueError('Measure must be defined for leftKey or rightKey')

        currentMeasureNumber = basic.numberToBraille(mNum, withNumberSign=False)

        def brailleFromKey(rightOrLeftKey):
            if rightOrLeftKey is not None and rightOrLeftKey.affinity == Affinity.INACCORD:
                inaccords = self._groupingDict.get(rightOrLeftKey)
                voice_trans = []
                for music21Voice in inaccords:
                    noteGrouping = extractBrailleElements(music21Voice)
                    noteGrouping.descendingChords = inaccords.descendingChords
                    noteGrouping.showClefSigns = inaccords.showClefSigns
                    noteGrouping.upperFirstInNoteFingering = inaccords.upperFirstInNoteFingering
                    voice_trans.append(ngMod.transcribeNoteGrouping(noteGrouping))
                brailleStr = symbols['full_inaccord'].join(voice_trans)
            elif rightOrLeftKey is not None:
                brailleStr = ngMod.transcribeNoteGrouping(self._groupingDict.get(rightOrLeftKey))
            else:
                brailleStr = ''

            return brailleStr

        rhBraille = brailleFromKey(rightKey)
        lhBraille = brailleFromKey(leftKey)

        self.addNoteGroupings(currentMeasureNumber, rhBraille, lhBraille)

    # # noinspection PyUnusedLocal
    # def extractSignatureGrouping(self, brailleKeyboard):
    #     pass
    #
    # # noinspection PyUnusedLocal
    # def extractLongExpressionGrouping(self, brailleKeyboard):
    #     pass
    #
    # # noinspection PyUnusedLocal
    # def extractTempoTextGrouping(self, brailleKeyboard):
    #     pass


# ------------------------------------------------------------------------------
# Grouping + Segment creation from music21.stream Part

def findSegments(music21Part, **partKeywords):
    '''
    Takes in a :class:`~music21.stream.Part`
    and a list of partKeywords.

    Returns a list of :class:`~music21.segment.BrailleSegment` instances.

    Five methods get called in the generation of segments:

    * :meth:`~music21.braille.segment.prepareSlurredNotes`
    * :meth:`~music21.braille.segment.getRawSegments`
    * :meth:`~music21.braille.segment.BrailleSegment.addGroupingAttributes`
    * :meth:`~music21.braille.segment.BrailleSegment.addSegmentAttributes`
    * :meth:`~music21.braille.segment.BrailleSegment.fixArticulations`

    >>> from music21.braille import test
    >>> example = test.example11_2()
    >>> allSegments = braille.segment.findSegments(example)

    >>> print(str(allSegments[0]))
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
    music hyphen ⠐
    ===
    ---end segment---


    Second segment

    >>> print(str(allSegments[1]))
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
    <music21.bar.Barline type=final>
    ===
    ---end segment---
    '''
    # Slurring
    # --------
    prepareSlurredNotes(music21Part, **partKeywords)

    # Raw Segments
    # ------------
    setHand = partKeywords['setHand'] if 'setHand' in partKeywords else None
    allSegments = getRawSegments(music21Part, setHand=setHand)
    # Grouping Attributes
    # -------------------
    for seg in allSegments:
        seg.addGroupingAttributes(**partKeywords)
        # Segment Attributes
        # ------------------
        seg.addSegmentAttributes(**partKeywords)
        # Articulations
        # -------------
        seg.fixArticulations()

    return allSegments


def prepareSlurredNotes(music21Part, **keywords):
    '''
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
    >>> short = converter.parse('tinynotation: 3/4 c4 d e')
    >>> s1 = spanner.Slur(short.flat.notes[0], short.flat.notes[-1])
    >>> short.append(s1)
    >>> short.show('text')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 3/4>
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note D>
        {2.0} <music21.note.Note E>
        {3.0} <music21.bar.Barline type=final>
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


    >>> long = converter.parse('tinynotation: 3/4 c8 d e f g a')
    >>> s2 = spanner.Slur(long.flat.notes[0], long.flat.notes[-1])
    >>> long.append(s2)
    >>> long.show('text')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 3/4>
        {0.0} <music21.note.Note C>
        {0.5} <music21.note.Note D>
        {1.0} <music21.note.Note E>
        {1.5} <music21.note.Note F>
        {2.0} <music21.note.Note G>
        {2.5} <music21.note.Note A>
        {3.0} <music21.bar.Barline type=final>
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


    >>> short.flat.notes[0].tie = tie.Tie('start')
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

    TODO: This should not add attributes to Note objects but instead return a collection
    of sets of notes that have each element applied to it.
    '''
    if not music21Part.spannerBundle:
        return

    slurLongPhraseWithBrackets = keywords.get('slurLongPhraseWithBrackets',
                                                  SEGMENT_SLURLONGPHRASEWITHBRACKETS)
    showShortSlursAndTiesTogether = keywords.get('showShortSlursAndTiesTogether',
                                                     SEGMENT_SHOWSHORTSLURSANDTIESTOGETHER)
    if 'showLongSlursAndTiesTogether' in keywords:
        showLongSlursAndTiesTogether = keywords['showLongSlursAndTiesTogether']
    elif slurLongPhraseWithBrackets:
        showLongSlursAndTiesTogether = True
    else:
        showLongSlursAndTiesTogether = SEGMENT_SHOWLONGSLURSANDTIESTOGETHER

    if slurLongPhraseWithBrackets is False:
        pass

    allNotes = music21Part.flat.notes.stream()
    for slur in music21Part.spannerBundle.getByClass(spanner.Slur):
        firstNote = slur[0]
        lastNote = slur[1]

        try:
            beginIndex = allNotes.index(firstNote)
            endIndex = allNotes.index(lastNote)
        except exceptions21.StreamException:
            continue

        delta = abs(endIndex - beginIndex) + 1

        if not showShortSlursAndTiesTogether and delta <= SEGMENT_MAXNOTESFORSHORTSLUR:
            # normally slurs are not shown on a tied notes (unless
            # showShortSlursAndTiesTogether is True, for facsimile transcriptions).
            if (allNotes[beginIndex].tie is not None
                    and allNotes[beginIndex].tie.type == 'start'):
                beginIndex += 1
            if allNotes[endIndex].tie is not None and allNotes[endIndex].tie.type == 'stop':
                endIndex -= 1

        if not showLongSlursAndTiesTogether and delta > SEGMENT_MAXNOTESFORSHORTSLUR:
            if (allNotes[beginIndex].tie is not None
                    and allNotes[beginIndex].tie.type == 'start'):
                beginIndex += 1
            if allNotes[endIndex].tie is not None and allNotes[endIndex].tie.type == 'stop':
                endIndex -= 1

        if delta <= SEGMENT_MAXNOTESFORSHORTSLUR:
            for noteIndex in range(beginIndex, endIndex):
                allNotes[noteIndex].shortSlur = True
        else:
            if slurLongPhraseWithBrackets:
                allNotes[beginIndex].beginLongBracketSlur = True
                allNotes[endIndex].endLongBracketSlur = True
            else:
                allNotes[beginIndex + 1].beginLongDoubleSlur = True
                allNotes[endIndex - 1].endLongDoubleSlur = True


def getRawSegments(music21Part, setHand=None):
    '''
    Takes in a :class:`~music21.stream.Part` divided it up into segments (i.e. instances of
    :class:`~music21.braille.segment.BrailleSegment`). This method assumes
    that the Part is already divided up into measures
    (see :class:`~music21.stream.Measure`). An acceptable input is shown below.

    This will automatically find appropriate segment breaks at braille.objects.BrailleSegmentBreak
    or braille.objects.BrailleOptionalSegmentBreak or after 48 elements if a double bar or
    repeat sign is encountered.

    Two methods are called on each measure during the creation of segments:

    * :meth:`~music21.braille.segment.prepareBeamedNotes`
    * :meth:`~music21.braille.segment.extractBrailleElements`

    >>> tn = converter.parse("tinynotation: 3/4 c4 c c e e e g g g c'2.")
    >>> tn = tn.makeNotation(cautionaryNotImmediateRepeat=False)
    >>> tn.show('text')
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
        {3.0} <music21.bar.Barline type=final>

    By default, there is no break anywhere within the Part,
    and a segmentList of size 1 is returned.

    >>> import copy
    >>> from music21.braille import segment
    >>> tnA = copy.deepcopy(tn)
    >>> rawSegments = segment.getRawSegments(tnA)
    >>> len(rawSegments)
    1
    >>> rawSegments[0]
    <music21.braille.segment.BrailleSegment 1 line, 0 headings, 40 cols>

    >>> print(rawSegments[0])
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
    <music21.bar.Barline type=final>
    ===
    ---end segment---

    Now, a segment break occurs at measure 2, offset 1.0 within that measure.
    The two segments are shown below.

    >>> tnB = copy.deepcopy(tn)
    >>> tnB.measure(2).insert(1.0, braille.objects.BrailleSegmentDivision())
    >>> allSegments = segment.getRawSegments(tnB)
    >>> len(allSegments)
    2

    >>> allSegments[0]
    <music21.braille.segment.BrailleSegment 1 line, 0 headings, 40 cols>

    >>> print(allSegments[0])
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
    <music21.braille.segment.BrailleSegment 1 line, 0 headings, 40 cols>

    >>> print(allSegments[1])
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
    <music21.bar.Barline type=final>
    ===
    ---end segment---
    '''
    allSegments = []

    currentSegment = BrailleSegment()

    for music21Measure in music21Part.getElementsByClass([stream.Measure, stream.Voice]):
        prepareBeamedNotes(music21Measure)
        brailleElements = extractBrailleElements(music21Measure)
        elementsInCurrentSegment = 0

        offsetFactor = 0
        previousAffinityCode = Affinity._LOWEST  # -1
        for brailleElement in brailleElements:
            # TODO: use objects.BrailleSegmentDivision() here...
            startANewSegment = False
            if 'BrailleOptionalSegmentDivision' in brailleElement.classes:
                # do not factor these two ifs into one, so that we fall through
                # 'BrailleSegmentDivision' of which this is a subclass...
                if elementsInCurrentSegment > MAX_ELEMENTS_IN_SEGMENT:
                    startANewSegment = True
            elif 'BrailleSegmentDivision' in brailleElement.classes:
                startANewSegment = True
            elif 'Barline' in brailleElement.classes:
                if (elementsInCurrentSegment > MAX_ELEMENTS_IN_SEGMENT
                        and brailleElement.type in ('double', 'final')):
                    startANewSegment = True

            if startANewSegment:
                # end of segment, get new one...
                if brailleElement.offset != 0.0:
                    currentSegment.endHyphen = True
                allSegments.append(currentSegment)
                currentSegment = BrailleSegment()
                elementsInCurrentSegment = 0

                if brailleElement.offset != 0.0:
                    currentSegment.beginsMidMeasure = True

                startANewSegment = False
                if 'BrailleSegmentDivision' in brailleElement.classes:
                    continue

            if brailleElement.affinityCode < previousAffinityCode:
                offsetFactor += 1

            affinityCode = brailleElement.affinityCode
            if affinityCode == Affinity.SPLIT1_NOTEGROUP:
                affinityCode = Affinity.INACCORD
            elif affinityCode == Affinity.SPLIT2_NOTEGROUP:
                affinityCode = Affinity.NOTEGROUP

            segmentKey = SegmentKey(music21Measure.number,
                                    offsetFactor,
                                    affinityCode,
                                    setHand
                                    )
            if segmentKey not in currentSegment:
                currentSegment[segmentKey] = BrailleElementGrouping()
            brailleElementGrouping = currentSegment[segmentKey]
            brailleElementGrouping.append(brailleElement)
            elementsInCurrentSegment += 1

            previousAffinityCode = brailleElement.affinityCode
    allSegments.append(currentSegment)
    return allSegments


def extractBrailleElements(music21Measure):
    '''
    Takes in a :class:`~music21.stream.Measure` and returns a
    :class:`~music21.braille.segment.BrailleElementGrouping` of correctly ordered
    :class:`~music21.base.Music21Object` instances which can be directly transcribed to
    braille.

    >>> from music21.braille import segment
    >>> tn = converter.parse('tinynotation: 2/4 c16 c c c d d d d', makeNotation=False)
    >>> tn = tn.makeNotation(cautionaryNotImmediateRepeat=False)
    >>> measure = tn[0]
    >>> measure.append(spanner.Slur(measure.notes[0],measure.notes[-1]))
    >>> measure.show('text')
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
    {2.0} <music21.bar.Barline type=final>


    Spanners are dealt with in :meth:`~music21.braille.segment.prepareSlurredNotes`,
    so they are not returned by this method, as seen below.

    >>> print(segment.extractBrailleElements(measure))
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
    <music21.bar.Barline type=final>
    '''
    allElements = BrailleElementGrouping()
    for music21Object in music21Measure:
        try:
            if isinstance(music21Object, bar.Barline):
                if music21Object.type == 'regular':
                    continue
            setAffinityCode(music21Object)
            music21Object.editorial.brailleEnglish = [str(music21Object)]
            allElements.append(music21Object)
        except BrailleSegmentException as notSupportedException:  # pragma: no cover
            isExempt = [isinstance(music21Object, music21Class)
                        for music21Class in excludeFromBrailleElements]
            if isExempt.count(True) == 0:
                environRules.warn(f'{notSupportedException}')

    allElements.sort(key=lambda x: (x.offset, x.classSortOrder))
    if len(allElements) >= 2 and isinstance(allElements[-1], dynamics.Dynamic):
        if isinstance(allElements[-2], bar.Barline):
            allElements[-1].classSortOrder = -1
            allElements.sort(key=lambda x: (x.offset, x.classSortOrder))

    return allElements


def prepareBeamedNotes(music21Measure):
    '''
    Takes in a :class:`~music21.stream.Measure` and labels beamed notes
    of smaller value than an 8th with beamStart and beamContinue keywords
    in accordance with beaming rules in braille music.

    A more in-depth explanation of beaming in braille can be found in
    Chapter 15 of Introduction to Braille Music Transcription, Second
    Edition, by Mary Turner De Garmo.

    >>> from music21.braille import segment
    >>> tn = converter.parse('tinynotation: 2/4 c16 c c c d d d d')
    >>> tn = tn.makeNotation(cautionaryNotImmediateRepeat=False)
    >>> tn.show('text')
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
        {2.0} <music21.bar.Barline type=final>
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
    '''
    allNotes = music21Measure.notes.stream()

    for sampleNote in allNotes:
        sampleNote.beamStart = False
        sampleNote.beamContinue = False
    allNotesAndRests = music21Measure.notesAndRests.stream()

    def withBeamFilter(el, unused):
        return (el.beams is not None) and len(el.beams) > 0

    def beamStartFilter(el, unused):
        return el.beams.getByNumber(1).type == 'start'

    def beamStopFilter(el, unused):
        return el.beams.getByNumber(1).type == 'stop'

    allStartIter = allNotes.iter.addFilter(withBeamFilter).addFilter(beamStartFilter)
    allStopIter = allNotes.iter.addFilter(withBeamFilter).addFilter(beamStopFilter)

    if len(allStartIter) != len(allStopIter):
        environRules.warn('Incorrect beaming: number of start notes != to number of stop notes.')
        return

    for beamIndex, startNote in enumerate(allStartIter):
        # Eighth notes cannot be beamed in braille (redundant, because beamed
        # notes look like eighth notes, but nevertheless useful).
        if startNote.quarterLength == 0.5:
            continue

        stopNote = allStopIter[beamIndex]
        startIndex = allNotesAndRests.index(startNote)
        stopIndex = allNotesAndRests.index(stopNote)

        delta = stopIndex - startIndex + 1
        if delta < 3:  # 2. The group must be composed of at least three notes.
            continue
        # 1. All notes in the group must have precisely the same value.
        # 3. A rest of the same value may take the place of the first note in a group,
        # but if the rest is located anywhere else, grouping may not be used.
        allNotesOfSameValue = True
        for noteIndex in range(startIndex + 1, stopIndex + 1):
            if (allNotesAndRests[noteIndex].quarterLength != startNote.quarterLength
                    or isinstance(allNotesAndRests[noteIndex], note.Rest)):
                allNotesOfSameValue = False
                break
        try:
            afterStopNote = allNotesAndRests[stopIndex + 1]
            if (isinstance(afterStopNote, note.Rest)
                    and (int(afterStopNote.beat) == int(stopNote.beat))):
                allNotesOfSameValue = False
        except exceptions21.StreamException:  # stopNote is last note of measure.
            pass
        if not allNotesOfSameValue:
            continue
        try:
            # 4. If the notes in the group are followed immediately by a
            # true eighth note or by an eighth rest,
            # grouping may not be used, unless the eighth is located in a new measure.
            if allNotesAndRests[stopIndex + 1].quarterLength == 0.5:
                continue
        except exceptions21.StreamException:  # stopNote is last note of measure.
            pass

        startNote.beamStart = True
        try:
            beforeStartNote = allNotesAndRests[startIndex - 1]
            if (isinstance(beforeStartNote, note.Rest)
                    and int(beforeStartNote.beat) == int(startNote.beat)
                    and beforeStartNote.quarterLength == startNote.quarterLength):
                startNote.beamContinue = True
        except IndexError:  # startNote is first note of measure.
            pass
        for noteIndex in range(startIndex + 1, stopIndex + 1):
            allNotesAndRests[noteIndex].beamContinue = True


def setAffinityCode(music21Object):
    '''
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

    >>> n1 = note.Note('D5')
    >>> braille.segment.setAffinityCode(n1)
    >>> n1.affinityCode
    <Affinity.NOTEGROUP: 9>
    >>> n1.classSortOrder
    10
    >>> c1 = clef.TrebleClef()
    >>> braille.segment.setAffinityCode(c1)
    >>> c1.affinityCode
    <Affinity.NOTEGROUP: 9>
    >>> c1.classSortOrder
    7
    '''
    for (music21Class, code, sortOrder) in affinityCodes:
        if isinstance(music21Object, music21Class):
            music21Object.affinityCode = code
            music21Object.classSortOrder = sortOrder
            return

    if isinstance(music21Object, expressions.TextExpression):
        music21Object.affinityCode = Affinity.NOTEGROUP
        if len(music21Object.content.split()) > 1:
            music21Object.affinityCode = Affinity.LONG_TEXTEXPR
        music21Object.classSortOrder = 8
        return

    if isinstance(music21Object, BrailleTranscriptionHelper):
        return

    raise BrailleSegmentException(f'{music21Object} cannot be transcribed to braille.')


def areGroupingsIdentical(noteGroupingA, noteGroupingB):
    '''
    Takes in two note groupings, noteGroupingA and noteGroupingB. Returns True
    if both groupings have identical contents. False otherwise.

    Helper for numRepeats...

    Needs two identical length groupings.

    >>> a = [note.Note('C4'), note.Note('D4')]
    >>> b = [note.Note('C4'), note.Note('D4')]
    >>> braille.segment.areGroupingsIdentical(a, b)
    True

    >>> d = b.pop()
    >>> braille.segment.areGroupingsIdentical(a, b)
    False
    >>> c = [note.Rest(), note.Note('D4')]
    >>> braille.segment.areGroupingsIdentical(a, c)
    False
    '''
    if len(noteGroupingA) == len(noteGroupingB):
        for (elementA, elementB) in zip(noteGroupingA, noteGroupingB):
            if elementA != elementB:
                return False
        return True
    return False


# ------------------------------------------------------------------------------
# Helper Methods

def splitNoteGrouping(noteGrouping, beatDivisionOffset=0):
    '''
    Almost identical to :meth:`~music21.braille.segment.splitMeasure`, but
    functions on a :class:`~music21.braille.segment.BrailleElementGrouping`
    instead.

    >>> from music21.braille import segment
    >>> bg = segment.BrailleElementGrouping()
    >>> bg.timeSignature = meter.TimeSignature('2/2')
    >>> s = converter.parse('tinyNotation: 2/2 c4 d r e')
    >>> for n in s.recurse().notesAndRests:
    ...     bg.append(n)
    >>> left, right = segment.splitNoteGrouping(bg)
    >>> left
    <music21.braille.segment.BrailleElementGrouping
        [<music21.note.Note C>, <music21.note.Note D>]>

    >>> print(left)
    <music21.note.Note C>
    <music21.note.Note D>

    >>> right
    <music21.braille.segment.BrailleElementGrouping
        [<music21.note.Rest rest>, <music21.note.Note E>]>


    Now split one beat division earlier than it should be.  For 2/2 that means
    one half of a beat, or one quarter note earlier:

    >>> left, right = segment.splitNoteGrouping(bg, beatDivisionOffset=1)
    >>> left
    <music21.braille.segment.BrailleElementGrouping
        [<music21.note.Note C>]>
    >>> right
    <music21.braille.segment.BrailleElementGrouping
        [<music21.note.Note D>, <music21.note.Rest rest>, <music21.note.Note E>]>
    '''
    music21Measure = stream.Measure()
    for brailleElement in noteGrouping:
        music21Measure.insert(brailleElement.offset, brailleElement)
    (leftMeasure, rightMeasure) = splitMeasure(music21Measure,
                                               beatDivisionOffset,
                                               noteGrouping.timeSignature)
    leftBrailleElements = copy.copy(noteGrouping)
    leftBrailleElements.internalList = []
    for brailleElement in leftMeasure:
        leftBrailleElements.append(brailleElement)

    rightBrailleElements = copy.copy(noteGrouping)
    rightBrailleElements.internalList = []
    for brailleElement in rightMeasure:
        rightBrailleElements.append(brailleElement)

    return leftBrailleElements, rightBrailleElements


def splitMeasure(music21Measure, beatDivisionOffset=0, useTimeSignature=None):
    '''
    Takes a :class:`~music21.stream.Measure`, divides it in two parts, and returns a
    two-tuple of (leftMeasure, rightMeasure). The parameters are as
    follows:

    * beatDivisionOffset => Adjusts the end offset of the first partition by a certain amount
      of beats to the left.
    * useTimeSignature => In the event that the Measure comes from the middle of a Part
      and thus does not define an explicit :class:`~music21.meter.TimeSignature`. If not
      provided, a TimeSignature is retrieved by
      using :meth:`~music21.stream.Measure.bestTimeSignature`.

    >>> m = stream.Measure()
    >>> m.append(note.Note('C4'))
    >>> m.append(note.Note('D4'))
    >>> left, right = braille.segment.splitMeasure(m)
    >>> left.show('text')
    {0.0} <music21.note.Note C>
    >>> right.show('text')
    {1.0} <music21.note.Note D>
    '''
    if useTimeSignature is not None:
        ts = useTimeSignature
    else:
        ts = music21Measure.bestTimeSignature()

    offset = 0.0
    if beatDivisionOffset != 0:
        if abs(beatDivisionOffset) > len(ts.beatDivisionDurations):
            raise BrailleSegmentException(
                f'beatDivisionOffset {beatDivisionOffset} is outside '
                + f'of ts.beatDivisionDurations {ts.beatDivisionDurations}'
            )
        duration_index = len(ts.beatDivisionDurations) - abs(beatDivisionOffset)
        try:
            offset += opFrac(ts.beatDivisionDurations[duration_index].quarterLength)
            offset = opFrac(offset)
        except IndexError:
            environRules.warn('Problem in converting a time signature in measure '
                              + f'{music21Measure.number}, offset may be wrong')
    bs = copy.deepcopy(ts.beatSequence)

    numberOfPartitions = 2
    try:
        bs.partitionByCount(numberOfPartitions, loadDefault=False)
        (startOffsetZero, endOffsetZero) = bs.getLevelSpan()[0]
    except meter.MeterException:
        numberOfPartitions += 1
        bs.partitionByCount(numberOfPartitions, loadDefault=False)
        startOffsetZero = bs.getLevelSpan()[0][0]
        endOffsetZero = bs.getLevelSpan()[-2][-1]
    endOffsetZero -= offset

    leftMeasure = stream.Measure()
    rightMeasure = stream.Measure()
    for x in music21Measure:
        if (x.offset >= startOffsetZero
                and (x.offset < endOffsetZero
                     or (x.offset == endOffsetZero
                         and isinstance(x, bar.Barline)))):
            leftMeasure.insert(x.offset, x)
        else:
            rightMeasure.insert(x.offset, x)
    for n in rightMeasure.notes:
        if n.tie is not None:
            leftMeasure.append(n)
            rightMeasure.remove(n)
            endOffsetZero += n.duration.quarterLength
            continue
        break

    rest0Length = music21Measure.duration.quarterLength - endOffsetZero
    r0 = note.Rest(quarterLength=rest0Length)
    leftMeasure.insert(endOffsetZero, r0)

    r1 = note.Rest(quarterLength=endOffsetZero)
    rightMeasure.insert(0.0, r1)

    ts0_delete = False
    if leftMeasure.timeSignature is None:
        ts0_delete = True
        leftMeasure.timeSignature = ts
    rightMeasure.timeSignature = ts
    leftMeasure.mergeAttributes(music21Measure)
    rightMeasure.mergeAttributes(music21Measure)
    leftMeasure.makeBeams(inPlace=True)
    rightMeasure.makeBeams(inPlace=True)
    prepareBeamedNotes(leftMeasure)
    prepareBeamedNotes(rightMeasure)
    leftMeasure.remove(r0)
    rightMeasure.remove(r1)
    if ts0_delete:
        leftMeasure.remove(ts)
    rightMeasure.remove(ts)
    return (leftMeasure, rightMeasure)


# ------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def testGetRawSegments(self):
        from music21 import converter

        tn = converter.parse("tinynotation: 3/4 c4 c c e e e g g g c'2.")
        tn = tn.makeNotation(cautionaryNotImmediateRepeat=False)

        rawSegList = getRawSegments(tn)
        unused = str(rawSegList[0])


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)  # , runTest='testGetRawSegments')

