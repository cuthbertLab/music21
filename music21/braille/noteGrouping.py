# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         noteGrouping.py
# Purpose:      Transcribes note groupings into Braille
# Authors:      Jose Cabal-Ugaz
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2012, 2016 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
import unittest

from music21 import clef
from music21 import dynamics
from music21 import environment
from music21 import expressions

from music21.braille import basic
from music21.braille.basic import BrailleBasicException

environRules = environment.Environment('braille/noteGrouping.py')

class NoteGroupingTranscriber(object):
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
        return u"".join(self.trans)
                

    def transcribeOneElement(self, el):
        '''
        Transcribe a single element...
        '''
        trans = self.trans
        if 'Note' in el.classes:
            currentNote = el
            if self.previousNote is None:
                doShowOctave = self.showLeadingOctave
            else:
                doShowOctave = basic.showOctaveWithNote(self.previousNote, currentNote)
            brailleNote = basic.noteToBraille(currentNote, 
                                        showOctave=doShowOctave,
                                        upperFirstInFingering=self.upperFirstInFingering)
            trans.append(brailleNote)
            self.previousNote = currentNote
            
        elif 'Rest' in el.classes:
            currentRest = el
            trans.append(basic.restToBraille(currentRest))
        
        elif 'Chord' in el.classes:
            currentChord = el
            try:
                allNotes = sorted(currentChord._notes, key=lambda n: n.pitch)
            except AttributeError:
                raise BrailleBasicException(
                        "If you're getting this exception, " +
                        "the '_notes' attribute for a music21 Chord probably " +
                        "became 'notes'. If that's the case, change it and life will be great.")
            if self.brailleElementGrouping.descendingChords:
                currentNote = allNotes[-1]
            else:
                currentNote = allNotes[0]
            if self.previousNote is None:
                doShowOctave = self.showLeadingOctave
            else:
                doShowOctave = basic.showOctaveWithNote(self.previousNote, currentNote)
            
            brailleChord = basic.chordToBraille(currentChord,
                                          descending=self.brailleElementGrouping.descendingChords, 
                                          showOctave=doShowOctave)
            trans.append(brailleChord)
            self.previousNote = currentNote
            
        elif 'Dynamic' in el.classes:
            currentDynamic = el
            brailleDynamic = basic.dynamicToBraille(currentDynamic)
            trans.append(brailleDynamic)
            self.previousNote = None
            self.showLeadingOctave = True
            
        elif 'TextExpression' in el.classes:
            currentExpression = el
            brailleExpression = basic.textExpressionToBraille(currentExpression)
            trans.append(brailleExpression)
            self.previousNote = None
            self.showLeadingOctave = True
            
        elif 'Barline' in el.classes:
            currentBarline = el
            trans.append(basic.barlineToBraille(currentBarline))
            
        elif 'Clef' in el.classes:
            if self.showClefSigns:
                currentClef = el
                trans.append(basic.clefToBraille(currentClef))
                self.previousNote = None
                self.showLeadingOctave = True
        else:
            environRules.warn("{0} not transcribed to braille.".format(el))
        
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
            return False # need to consult previous element in translation

        if el is not None and 'Dynamic' in el.classes:
            return False
        if el is not None and 'TextExpression' in el.classes:
            return False
        
        if ('Dynamic' in prev.classes
                or ('Clef' in prev.classes 
                        and self.showClefSigns)
                or ('TextExpression' in prev.classes
                    and prev.content[-1] != '.') # TE is an abbreviation, no extra dot 3 necessary
            ):
            for dot in basic.yieldDots(self.trans[-1][0]):
                self.trans.insert(-1, dot) # insert one before the end, not append...
                prev._brailleEnglish.append(u"Dot 3 {0}".format(dot))
                return True # only append max one dot.

        return False

def transcribeNoteGrouping(brailleElementGrouping, showLeadingOctave=True):
    '''
    transcribe a group of notes, possibly excluding certain attributes.
    '''
    ngt = NoteGroupingTranscriber()
    ngt.showLeadingOctave = showLeadingOctave
    return ngt.transcribeGroup(brailleElementGrouping)

    trans = []
    previousNote = None
    previousElement = None
    try:
        for brailleElement in brailleElementGrouping:
            upperFirstInFingering = brailleElementGrouping.upperFirstInNoteFingering
            if 'Note' in brailleElement.classes:
                currentNote = brailleElement
                if previousNote is None:
                    doShowOctave = showLeadingOctave
                else:
                    doShowOctave = basic.showOctaveWithNote(previousNote, currentNote)
                brailleNote = basic.noteToBraille(currentNote, 
                                            showOctave=doShowOctave,
                                            upperFirstInFingering=upperFirstInFingering)
                trans.append(brailleNote)
                previousNote = currentNote
                
            elif 'Rest' in brailleElement.classes:
                currentRest = brailleElement
                trans.append(basic.restToBraille(currentRest))
            
            elif 'Chord' in brailleElement.classes:
                currentChord = brailleElement
                try:
                    allNotes = sorted(currentChord._notes, key=lambda n: n.pitch)
                except AttributeError:
                    raise BrailleBasicException(
                            "If you're getting this exception, " +
                            "the '_notes' attribute for a music21 Chord probably " +
                            "became 'notes'. If that's the case, change it and life will be great.")
                if brailleElementGrouping.descendingChords:
                    currentNote = allNotes[-1]
                else:
                    currentNote = allNotes[0]
                if previousNote is None:
                    doShowOctave = showLeadingOctave
                else:
                    doShowOctave = basic.showOctaveWithNote(previousNote, currentNote)
                
                brailleChord = basic.chordToBraille(currentChord,
                                              descending=brailleElementGrouping.descendingChords, 
                                              showOctave=doShowOctave)
                trans.append(brailleChord)
                previousNote = currentNote
                
            elif 'Dynamic' in brailleElement.classes:
                currentDynamic = brailleElement
                brailleDynamic = basic.dynamicToBraille(currentDynamic)
                trans.append(brailleDynamic)
                previousNote = None
                showLeadingOctave = True
                
            elif 'TextExpression' in brailleElement.classes:
                currentExpression = brailleElement
                brailleExpression = basic.textExpressionToBraille(currentExpression)
                trans.append(brailleExpression)
                previousNote = None
                showLeadingOctave = True
                
            elif 'Barline' in brailleElement.classes:
                currentBarline = brailleElement
                trans.append(basic.barlineToBraille(currentBarline))
                
            elif 'Clef' in brailleElement.classes:
                if brailleElementGrouping.showClefSigns:
                    currentClef = brailleElement
                    trans.append(basic.clefToBraille(currentClef))
                    previousNote = None
                    showLeadingOctave = True
            else:
                environRules.warn("{0} not transcribed to braille.".format(brailleElement))
                
            if previousElement is not None:
                if (brailleElementGrouping.showClefSigns 
                        and isinstance(previousElement, clef.Clef) 
                        or isinstance(previousElement, dynamics.Dynamic) 
                        and not isinstance(brailleElement, dynamics.Dynamic) 
                        and not isinstance(brailleElement, expressions.TextExpression)):
                    for dot in basic.yieldDots(trans[-1][0]):
                        trans.insert(-1, dot)
                        previousElement._brailleEnglish.append(u"Dot 3 {0}".format(dot))
                        break
                elif (isinstance(previousElement, expressions.TextExpression)
                      and not isinstance(brailleElement, dynamics.Dynamic)
                      and not isinstance(brailleElement, expressions.TextExpression)):
                    if previousElement.content[-1] != '.': 
                        # abbreviation, no extra dot 3 necessary
                        for dot in basic.yieldDots(trans[-1][0]):
                            trans.insert(-1, dot)
                            previousElement._brailleEnglish.append(u"Dot 3 {0}".format(dot))
                            break
            previousElement = brailleElement
        return u"".join(trans)
    except AttributeError:  # pragma: no cover
        brailleElementGrouping.descendingChords = True
        brailleElementGrouping.showClefSigns = False
        brailleElementGrouping.upperFirstInNoteFingering = True
        return transcribeNoteGrouping(brailleElementGrouping, showLeadingOctave)


#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    import music21
    music21.mainTest(Test) #, runTest='testGetRawSegments')