# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         noteGrouping.py
# Purpose:      Transcribes note groupings into Braille
# Authors:      Jose Cabal-Ugaz
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2012, 2016 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
import unittest

from collections import OrderedDict

from music21 import environment
from music21.braille import basic
from music21.braille.lookup import symbols

environRules = environment.Environment('braille/noteGrouping.py')


class NoteGroupingTranscriber:
    '''
    Object that can transcribe note groupings...
    '''
    def __init__(self, brailleElementGrouping=None):
        self.showLeadingOctave = True
        self.brailleElementGrouping = brailleElementGrouping
        self._upperFirstInFingering = None
        self._showClefSigns = None

        # duplicate of reset...
        self.previousNote = None
        self.previousElement = None
        self.trans = []
        self.transText = None

    def reset(self):
        self.previousNote = None
        self.previousElement = None
        self.trans = []
        self.transText = None

    @property
    def showClefSigns(self):
        '''
        Generally, in Braille, clef signs are not used.  However, they
        can be shown for pedagogical purposes or to make a facsimile
        transcription of the sighted text.

        If not set but self.brailleElementGrouping.showClefSigns
        is set, uses that instead.

        >>> ngt = braille.noteGrouping.NoteGroupingTranscriber()
        >>> ngt.showClefSigns
        False
        >>> beg = braille.segment.BrailleElementGrouping()
        >>> ngt.brailleElementGrouping = beg
        >>> ngt.showClefSigns
        False
        >>> beg.showClefSigns = True
        >>> ngt.showClefSigns
        True
        >>> ngt.showClefSigns = False
        >>> ngt.showClefSigns
        False
        '''
        if self._showClefSigns is not None:
            return self._showClefSigns
        elif self.brailleElementGrouping is not None:
            return self.brailleElementGrouping.showClefSigns
        else:
            return False

    @showClefSigns.setter
    def showClefSigns(self, new):
        self._showClefSigns = new

    @property
    def upperFirstInFingering(self):
        '''
        When there are multiple fingering patterns listed at the same time,
        should the highest be listed first (default True) or last?

        If not set but self.brailleElementGrouping.upperFirstInNoteFingering
        is set, uses that instead. (note the slight difference in names... NoteFingering)

        >>> ngt = braille.noteGrouping.NoteGroupingTranscriber()
        >>> ngt.upperFirstInFingering
        True
        >>> beg = braille.segment.BrailleElementGrouping()
        >>> ngt.brailleElementGrouping = beg
        >>> ngt.upperFirstInFingering
        True
        >>> beg.upperFirstInNoteFingering = False
        >>> ngt.upperFirstInFingering
        False
        >>> ngt.upperFirstInFingering = True
        >>> ngt.upperFirstInFingering
        True
        '''
        if self._upperFirstInFingering is not None:
            return self._upperFirstInFingering
        elif self.brailleElementGrouping is not None:
            return self.brailleElementGrouping.upperFirstInNoteFingering
        else:
            return True

    @upperFirstInFingering.setter
    def upperFirstInFingering(self, new):
        self._upperFirstInFingering = new

    def transcribeGroup(self, brailleElementGrouping=None):
        '''
        transcribe a group of notes, possibly excluding certain attributes.

        Returns a (unicode) string of brailleElementGrouping transcribed.

        '''
        self.reset()
        if brailleElementGrouping is not None:
            self.brailleElementGrouping = brailleElementGrouping

        for brailleElement in self.brailleElementGrouping:
            self.transcribeOneElement(brailleElement)

        if brailleElementGrouping.withHyphen:
            self.trans.append(symbols['music_hyphen'])

        return ''.join(self.trans)

    def translateNote(self, currentNote):
        if self.previousNote is None:
            doShowOctave = self.showLeadingOctave
        else:
            doShowOctave = basic.showOctaveWithNote(self.previousNote, currentNote)
        brailleNote = basic.noteToBraille(currentNote,
                                          showOctave=doShowOctave,
                                          upperFirstInFingering=self.upperFirstInFingering)
        self.previousNote = currentNote
        return brailleNote

    def translateRest(self, currentRest):
        return basic.restToBraille(currentRest)

    def translateChord(self, currentChord):
        allNotes = sorted(currentChord.notes, key=lambda n: n.pitch)

        if self.brailleElementGrouping.descendingChords:
            currentNote = allNotes[-1]
        else:
            currentNote = allNotes[0]
        if self.previousNote is None:
            doShowOctave = self.showLeadingOctave
        else:
            doShowOctave = basic.showOctaveWithNote(self.previousNote, currentNote)

        descendingChords = self.brailleElementGrouping.descendingChords
        brailleChord = basic.chordToBraille(currentChord,
                                            descending=descendingChords,
                                            showOctave=doShowOctave)
        self.previousNote = currentNote
        return brailleChord

    def translateDynamic(self, currentDynamic):
        brailleDynamic = basic.dynamicToBraille(currentDynamic)
        self.previousNote = None
        self.showLeadingOctave = True
        return brailleDynamic

    def translateTextExpression(self, currentExpression):
        brailleExpression = basic.textExpressionToBraille(currentExpression)
        self.previousNote = None
        self.showLeadingOctave = True
        return brailleExpression

    def translateBarline(self, currentBarline):
        return basic.barlineToBraille(currentBarline)

    def translateClef(self, currentClef):
        '''
        translate Clefs to braille IF self.showClefSigns is True
        '''
        if self.showClefSigns:
            brailleClef = basic.clefToBraille(currentClef)
            self.previousNote = None
            self.showLeadingOctave = True
            return brailleClef

    translateDict = OrderedDict([
        ('Note', translateNote),
        ('Rest', translateRest),
        ('Chord', translateChord),
        ('Dynamic', translateDynamic),
        ('TextExpression', translateTextExpression),
        ('Barline', translateBarline),
        ('Clef', translateClef),
    ])

    def transcribeOneElement(self, el):
        '''
        Transcribe a single element and add it to self.trans, setting self.previousElement
        along the way.

        >>> ngt = braille.noteGrouping.NoteGroupingTranscriber()
        >>> n = note.Note('C4')
        >>> ngt.transcribeOneElement(n)
        >>> ''.join(ngt.trans)
        '⠐⠹'
        >>> ngt.previousElement
        <music21.note.Note C>
        '''
        elClasses = el.classes
        for className, classMethod in self.translateDict.items():
            if className in elClasses:
                addBraille = classMethod(self, el)
                if addBraille is not None:
                    self.trans.append(addBraille)
                break
        else:
            environRules.warn(f'{el} not transcribed to braille.')

        self.optionallyAddDotToPrevious(el)
        self.previousElement = el

    def optionallyAddDotToPrevious(self, el=None):
        '''
        if el is None or not a Dynamic or TextExpression, add a dot-3 Dot
        before the current transcription
        under certain circumstances:

        1. self.previousElement exists
        2. the last character in the current transcription (self.trans) fits the criteria for
           basic.yieldDots()
        3. one of these three.  PreviousElement was...:
            a. a Dynamic.
            b. a Clef and clef signs are being transcribed
            c. a TextExpression not ending in "."

        Returns True if a dot as added, or False otherwise.
        '''
        prev = self.previousElement
        if prev is None:
            return False
        if not self.trans:
            return False  # need to consult previous element in translation

        if el is not None and 'Dynamic' in el.classes:
            return False
        if el is not None and 'TextExpression' in el.classes:
            return False

        if ('Dynamic' in prev.classes
            or ('Clef' in prev.classes
                and self.showClefSigns)
            or ('TextExpression' in prev.classes  # TE is an abbreviation, no extra dot 3 necessary
                and prev.content[-1] != '.')):
            for dot in basic.yieldDots(self.trans[-1][0]):
                self.trans.insert(-1, dot)  # insert one before the end, not append...
                prev.editorial.brailleEnglish.append(f'Dot 3 {dot}')
                return True  # only append max one dot.

        return False


def transcribeNoteGrouping(brailleElementGrouping, showLeadingOctave=True):
    '''
    transcribe a group of notes, possibly excluding certain attributes.

    To be DEPRECATED -- called only be BrailleGrandSegment now.
    '''
    ngt = NoteGroupingTranscriber()
    ngt.showLeadingOctave = showLeadingOctave
    return ngt.transcribeGroup(brailleElementGrouping)


# ------------------------------------------------------------------------------
class Test(unittest.TestCase):
    pass


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)  # , runTest='testGetRawSegments')
