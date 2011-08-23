# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         thinkdifferent.py
# Purpose:      music21 class inspired by steve jobs.
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''
Measures

Key signature, time signature, tempo mark, metronome mark.

Key signature, time signature

Make heading
Translate notesAndRests/barline of measure.

Concept of sections, I guess?

Having a method which "precuts" the measure into submeasures based on locations of key and
time signatures, so that one stream returns two different streams which can then be translated
individually. 

Looking for key/time signatures not at offset 0.0.

Useful information for a piece: offset

Conflict is always what to do when a note grouping is set to false and it is forced to a newline.
'''
import collections
import music21

from music21 import bar
from music21 import clef
from music21 import dynamics
from music21 import key
from music21 import meter
from music21 import note
from music21 import stream

from music21.braille import translate
from music21.braille import test

class BrailleText():
    '''
    Object that handles all the formatting associated with braille music notation.
    '''
    def __init__(self):
        self.lineNumber = 1
        self.linePos = 0
        self.allLines = collections.defaultdict(str)
        self.maxLineLength = 40
        self.highestMeasureNumberLength = 2
        
    def addElement(self, **elementKeywords):
        if 'heading' in elementKeywords:
            if not self.lineNumber == 1:
                self.lineNumber += 1
            for headingLine in elementKeywords['heading'].splitlines():
                self.allLines[self.lineNumber] = headingLine
                self.lineNumber += 1
        if 'pair' in elementKeywords:
            (measureNumber, rh_braille, lh_braille) = elementKeywords['pair']
            isFirstOfLine = False
            rh_all = []
            lh_all = []
            if len(self.allLines[self.lineNumber]) == 0:
                rh_all.append((self.highestMeasureNumberLength - len(measureNumber)) * translate.symbols['space'])
                rh_all.append(measureNumber)
                lh_all.append(translate.symbols['space'] * self.highestMeasureNumberLength)
                self.linePos = self.highestMeasureNumberLength
                isFirstOfLine = True
            if self.linePos + len(rh_braille) + 1 > self.maxLineLength or self.linePos + len(lh_braille) + 1 > self.maxLineLength:
                rh_all.append((self.highestMeasureNumberLength - len(measureNumber)) * translate.symbols['space'])
                self.fillLine(self.lineNumber)
                self.fillLine(self.lineNumber + 1)
                self.lineNumber += 2
                rh_all.append(measureNumber)
                lh_all.append(translate.symbols['space'] * self.highestMeasureNumberLength)
                self.linePos = self.highestMeasureNumberLength
                isFirstOfLine = True
            rh_all.append(translate.symbols['space'])
            lh_all.append(translate.symbols['space'])
            rh_length = len(rh_braille)
            lh_length = len(lh_braille)
            if isFirstOfLine:
                rh_all.append(translate.symbols['rh_keyboard'])
                lh_all.append(translate.symbols['lh_keyboard'])
                rh_length += 2
                lh_length += 2
                for dots in translate.binary_dots[rh_braille[0]]:
                    if (dots == '10' or dots == '11'):
                        rh_all.append(translate.symbols['dot'])
                        rh_length += 1
                for dots in translate.binary_dots[lh_braille[0]]:
                    if (dots == '10' or dots == '11'):
                        lh_all.append(translate.symbols['dot'])
                        lh_length += 1
            if rh_length > lh_length:
                rh_all.append(rh_braille)
                lh_all.append(lh_braille)
                if not(rh_length - lh_length > 6):
                    lh_all.append(translate.symbols['space'] * (rh_length - lh_length))
                else:
                    lh_all.append(translate.symbols['space'])
                    lh_all.append(translate.symbols['dot'] * (rh_length - lh_length - 1)) # tracker dots
                self.linePos += rh_length + 1
            else:
                lh_all.append(lh_braille)
                rh_all.append(rh_braille)
                if not(lh_length - rh_length > 6):
                    rh_all.append(translate.symbols['space'] * (lh_length - rh_length))
                else:
                    rh_all.append(translate.symbols['space'])
                    rh_all.append(translate.symbols['dot'] * (lh_length - rh_length - 1)) # tracker dots
                self.linePos += lh_length + 1
            self.allLines[self.lineNumber] += u"".join(rh_all)
            self.allLines[self.lineNumber + 1] += u"".join(lh_all)
    
    def recenterLine(self, lineNumberToCenter):
        lineToCenter = self.allLines[lineNumberToCenter]
        lineToCenter = lineToCenter.strip(translate.symbols['space'])
        nextLineLength = len(self.allLines[lineNumberToCenter + 1])
        self.allLines[lineNumberToCenter] = lineToCenter.center(nextLineLength, translate.symbols['space'])
    
    def fillLine(self, lineNumberToFill):
        self.allLines[lineNumberToFill] += u"".join(translate.symbols['space'] * (self.maxLineLength - self.linePos))
        
    def __str__(self):
        return u"\n".join([j for (i, j) in sorted(self.allLines.items())])

def splitStreamByClass(sampleMeasure, classFilterList, groupWithPrevious = False):
    '''
    keywords groupWithPrevious, includeF
    '''
    elementsOfClasses = sampleMeasure.getElementsByClass(classFilterList)
    if len(elementsOfClasses) == 0:
        return [sampleMeasure]
    
    elementsByOffset = elementsOfClasses.groupElementsByOffset(returnDict = True)
    if len(elementsByOffset.keys()) == 1 and 0.0 in elementsByOffset:
        return [sampleMeasure]

    allStreams = []
    startIndex = 0
    endIndex = 0
    for offset in elementsByOffset:
        if not(offset == 0.0):
            if not groupWithPrevious:
                endIndex = sampleMeasure.index(elementsByOffset[offset][0])
            else:
                endIndex = sampleMeasure.index(elementsByOffset[offset][-1]) + 1
            allStreams.append(sampleMeasure[startIndex:endIndex])
            startIndex = endIndex
    endIndex = len(sampleMeasure)
    allStreams.append(sampleMeasure[startIndex:endIndex])
    return allStreams
    
def noteGroupingsToBraille(sampleMeasure = stream.Measure(), showLeadingOctave = True):
    '''
    Notes, rests, barlines, and dynamics in a measure stream to braille.
    Returns a list of note groupings for a stream.
    Right now, those are divisions based on locations of double barlines.
    '''
    allNoteGroupings = []
    noteGroupingTrans = []
    previousNote = None
    for element in sampleMeasure.getElementsByClass([note.Note, note.Rest, bar.Barline, dynamics.Dynamic]):
        if isinstance(element, note.Note):
            if previousNote == None:
                doShowOctave = showLeadingOctave
            else:
                doShowOctave = translate.showOctaveWithNote(previousNote, element)
            noteGroupingTrans.append(translate.noteToBraille(sampleNote = element, showOctave = doShowOctave))
            previousNote = element                
        elif isinstance(element, note.Rest):
            if element.duration == sampleMeasure.duration:
                noteGroupingTrans.append(translate.restToBraille(sampleRest = note.Rest(quarterLength = 4.0)))
            else:
                noteGroupingTrans.append(translate.restToBraille(sampleRest = element))
        elif isinstance(element, dynamics.Dynamic):
            noteGroupingTrans.append(translate.symbols['word'])
            noteGroupingTrans.append(translate.wordToBraille(element.value))
            previousNote = None
            showLeadingOctave = True
        elif isinstance(element, bar.Barline):
            noteGroupingTrans.append(translate.barlines[element.style])
            allNoteGroupings.append(u"".join(noteGroupingTrans))
            noteGroupingTrans = []
            previousNote = None
            showLeadingOctave = True

    if not(len(noteGroupingTrans) == 0):
        allNoteGroupings.append(u"".join(noteGroupingTrans))
    return allNoteGroupings

def keyboardPartsToBraille(keyboardStyle = stream.Part()):
    '''
    Translates a stream Part consisting of two stream Parts, a right hand and left hand,
    into braille music bar over bar format.
    '''
    rightHand = keyboardStyle[0]
    leftHand = keyboardStyle[1]

    bt = BrailleText()
    bt.addElement(heading = translate.extractBrailleHeading(rightHand[0]))
    bt.highestMeasureNumberLength = len(str(rightHand.getElementsByClass(stream.Measure)[-1].number))
    
    for rhMeasure in rightHand:
        lhMeasure = leftHand.measure(rhMeasure.number)
        rh_braille = noteGroupingsToBraille(rhMeasure)[0]
        lh_braille = noteGroupingsToBraille(lhMeasure)[0]
        bt.addElement(pair = (translate.numberToBraille(sampleNumber = rhMeasure.number)[1:], rh_braille, lh_braille))

    return bt
    
if __name__ == "__main__":
    pass
