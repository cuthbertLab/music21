# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         text.py
# Purpose:      music21 class which allows for accurate formatting of braille transcription
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    Copyright © 2011 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
import unittest

from music21.braille import lookup
from music21 import exceptions21
from music21.ext import six

symbols = lookup.symbols
binary_dots = lookup.binary_dots

if six.PY3:
    unicode = str # @ReservedAssignment

class BrailleText():
    """
    Object that handles all the formatting associated with braille music notation.
    """
    def __init__(self, lineLength = 40, showHand = None):
        self.lineLength = lineLength
        self.allLines = []
        self.makeNewLine()
        self.rightHandSymbol = False
        self.leftHandSymbol = False
        if showHand == 'right':
            self.rightHandSymbol = True
        elif showHand == 'left':
            self.leftHandSymbol = True
        elif not showHand is None:
            raise BrailleTextException("Illegal hand sign request.")
        self.allHeadings = []

    def addElement(self, **elementKeywords):
        withHyphen = False
        if 'withHyphen' in elementKeywords:
            withHyphen = elementKeywords['withHyphen']
        if 'heading' in elementKeywords:
            self.addHeading(elementKeywords['heading'])
        elif 'measureNumber' in elementKeywords:
            self.addMeasureNumber(elementKeywords['measureNumber'], withHyphen)
        elif 'keyOrTimeSig' in elementKeywords:
            self.addSignatures(elementKeywords['keyOrTimeSig'], withHyphen)
        elif 'noteGrouping' in elementKeywords:
            noteGrouping = elementKeywords['noteGrouping']
            showLeadingOctave = elementKeywords['showLeadingOctave']
            forceHyphen = False
            forceNewline = False
            if 'forceHyphen' in elementKeywords:
                forceHyphen = elementKeywords['forceHyphen']
            if 'forceNewline' in elementKeywords:
                forceNewline = elementKeywords['forceNewline']
            self.addNoteGrouping(noteGrouping, showLeadingOctave, withHyphen, forceHyphen, forceNewline)
        elif 'inaccord' in elementKeywords:
            inaccord = elementKeywords['inaccord']
            self.addInaccord(inaccord)
        elif 'longExpression' in elementKeywords:
            longExpression = elementKeywords['longExpression']
            self.addLongExpression(longExpression, withHyphen)
        else:
            raise BrailleTextException("Invalid Keyword.")
    
    def addHeading(self, heading):
        if not self.currentLine.textLocation == 0:
            self.makeNewLine()
        indexStart = len(self.allLines) - 1
        indexFinal = indexStart
        for line in heading.splitlines():
            self.currentLine.isHeading = True
            self.currentLine.append(line, addSpace = False)
            self.makeNewLine()
            indexFinal += 1
        self.allHeadings.append((indexStart, indexFinal))
        
    def addLongExpression(self, longExpr, withHyphen = False):
        if withHyphen:
            self.currentLine.append(symbols['music_hyphen'], addSpace = False)
        for brailleExpr in longExpr.split(symbols['space']):
            try:
                self.currentLine.append(brailleExpr)
            except BrailleTextException:
                self.makeNewLine()
                self.currentLine.insert(2, brailleExpr)
        return
    
    def addInaccord(self, inaccord):
        addSpace = True
        if not self.currentLine.containsNoteGrouping:
            if self.rightHandSymbol or self.leftHandSymbol:
                if not self.currentLine.textLocation:
                    addSpace = False
                if self.rightHandSymbol:
                    self.currentLine.append(symbols['rh_keyboard'], addSpace = addSpace)
                elif self.leftHandSymbol:
                    self.currentLine.append(symbols['lh_keyboard'], addSpace = addSpace)
                for dots in binary_dots[inaccord[0]]:
                    if dots == '10' or dots == '11':
                        self.currentLine.append(symbols['dot'], addSpace = False)
                addSpace = False
        try:
            if not self.currentLine.textLocation:
                addSpace = False
            self.currentLine.append(inaccord, addSpace = addSpace)
        except BrailleTextException:
            self.makeNewLine()
            if self.rightHandSymbol or self.leftHandSymbol:
                if self.rightHandSymbol:
                    self.currentLine.insert(2, symbols['rh_keyboard'])
                elif self.leftHandSymbol:
                    self.currentLine.insert(2, symbols['lh_keyboard'])
                for dots in binary_dots[inaccord[0]]:
                    if dots == '10' or dots == '11':
                        self.currentLine.append(symbols['dot'], addSpace = False)
                self.currentLine.append(inaccord, addSpace = False)
            else:
                self.currentLine.insert(2, inaccord)
        self.currentLine.containsNoteGrouping = True
    
    def addMeasureNumber(self, measureNumber, withHyphen = False):
        if withHyphen:
            self.currentLine.append(symbols['music_hyphen'], addSpace = False)
            self.makeNewLine()
        elif not self.currentLine.textLocation == 0:
            self.makeNewLine()
        self.currentLine.append(measureNumber, addSpace = False)

    def addNoteGrouping(self, noteGrouping, showLeadingOctave = False, withHyphen = False,
                         forceHyphen = False, forceNewline = False):
        addSpace = True
        if not self.currentLine.containsNoteGrouping:
            if self.rightHandSymbol or self.leftHandSymbol:
                if not self.currentLine.textLocation:
                    addSpace = False
                if self.rightHandSymbol:
                    self.currentLine.append(symbols['rh_keyboard'], addSpace = addSpace)
                elif self.leftHandSymbol:
                    self.currentLine.append(symbols['lh_keyboard'], addSpace = addSpace)
                for dots in binary_dots[noteGrouping[0]]:
                    if dots == '10' or dots == '11':
                        self.currentLine.append(symbols['dot'], addSpace = False)
                addSpace = False
        try:
            if not self.currentLine.textLocation:
                addSpace = False
            if withHyphen:
                self.currentLine.append(u"".join([noteGrouping, symbols['music_hyphen']]), addSpace = addSpace)
            else:
                self.currentLine.append(noteGrouping, addSpace = addSpace)
        except BrailleTextException:
            if not forceNewline and self.lineLength - self.currentLine.textLocation > self.lineLength / 4 <= len(noteGrouping):
                raise BrailleTextException("Split Note Grouping")
            elif not showLeadingOctave:
                raise BrailleTextException("Recalculate Note Grouping With Leading Octave")
            else:
                if not forceHyphen:
                    prevChar = self.currentLine.allChars[self.currentLine.textLocation - 1]
                    if prevChar == symbols['music_hyphen']:
                        self.currentLine.allChars[self.currentLine.textLocation - 1] = symbols['space']
                        self.currentLine.textLocation -= 1
                self.makeNewLine()
                if self.rightHandSymbol or self.leftHandSymbol:
                    if self.rightHandSymbol:
                        self.currentLine.insert(2, symbols['rh_keyboard'])
                    elif self.leftHandSymbol:
                        self.currentLine.insert(2, symbols['lh_keyboard'])
                    for dots in binary_dots[noteGrouping[0]]:
                        if dots == '10' or dots == '11':
                            self.currentLine.append(symbols['dot'], addSpace = False)
                    self.currentLine.append(noteGrouping, addSpace = False)
                else:
                    self.currentLine.insert(2, noteGrouping)
                if withHyphen:
                    self.currentLine.append(symbols['music_hyphen'], addSpace = False)
        self.currentLine.containsNoteGrouping = True

    def addSignatures(self, signatures, withHyphen = False):
        if withHyphen:
            self.currentLine.append(symbols['music_hyphen'], addSpace = False)
        try:
            addSpace = True
            if not self.currentLine.textLocation:
                addSpace = False
            self.currentLine.append(signatures, addSpace = addSpace)
        except BrailleTextException:
            self.makeNewLine()
            self.currentLine.insert(2, signatures)

    def makeNewLine(self):
        self.currentLine = BrailleTextLine(self.lineLength)
        self.allLines.append(self.currentLine)
        self.currentLine.isHeading = False
        self.currentLine.containsNoteGrouping = False
            
    def recenterHeadings(self):
        for (indexStart, indexFinal) in self.allHeadings:
            maxLineLength = 0
            for i in range(indexFinal, len(self.allLines)):
                if self.allLines[i].isHeading:
                    break
                lineLength = self.allLines[i].textLocation
                if lineLength > maxLineLength:
                    maxLineLength = lineLength
            if self.lineLength == maxLineLength:
                continue
            for j in range(indexStart, indexFinal):
                lineToCenter = unicode(self.allLines[j])
                lineToCenter = lineToCenter.strip(symbols['space'])
                if maxLineLength > len(lineToCenter):
                    lineToCenter = lineToCenter.center(maxLineLength, symbols['space'])
                    self.allLines[j].insert(0, lineToCenter)
                    self.allLines[j].textLocation = maxLineLength
    
    def __str__(self):
        self.recenterHeadings()
        return u"\n".join([unicode(l) for l in self.allLines])

class BrailleKeyboard():
    def __init__(self, lineLength = 40):
        self.lineLength = lineLength
        self.allLines = []
        self.makeNewLine()
        self.allHeadings = []
        self.rightHand = None
        self.leftHand = None

    def addElement(self, **elementKeywords):
        if 'heading' in elementKeywords:
            self.addHeading(elementKeywords['heading'])
        elif 'pair' in elementKeywords:
            (measureNumber, noteGroupingR, noteGroupingL) = elementKeywords['pair']
            self.addNoteGroupings(measureNumber, noteGroupingL, noteGroupingR)
        else:
            raise BrailleTextException("Invalid Keyword.")
    
    def addHeading(self, heading):
        if not self.currentLine.textLocation == 0:
            self.makeNewLine()
        indexStart = len(self.allLines) - 1
        indexFinal = indexStart
        for line in heading.splitlines():
            self.currentLine.isHeading = True
            self.currentLine.append(line, addSpace = False)
            self.makeNewLine()
            indexFinal += 1
        self.allHeadings.append((indexStart, indexFinal))

    def makeNewLine(self):
        self.currentLine = BrailleTextLine(self.lineLength)
        self.allLines.append(self.currentLine)
        self.currentLine.isHeading = False
        self.currentLine.containsNoteGrouping = False

    def makeNewLines(self):
        if not self.currentLine.textLocation:
            self.rightHand = self.currentLine
        else:
            self.rightHand = BrailleTextLine(self.lineLength)
            self.allLines.append(self.rightHand)
        self.rightHand.isHeading = False
        self.rightHand.containsNoteGrouping = False

        self.leftHand = BrailleTextLine(self.lineLength)
        self.leftHand.isHeading = False
        self.leftHand.containsNoteGrouping = False
        self.allLines.append(self.leftHand)

    def addNoteGroupings(self, measureNumber, noteGroupingR, noteGroupingL):
        if self.rightHand is None and self.leftHand is None:
            self.makeNewLines()
        if not self.rightHand.textLocation:
            self.rightHand.insert(self.highestMeasureNumberLength - len(measureNumber), measureNumber)
            self.leftHand.textLocation = self.rightHand.textLocation
        addSpace = True
        if not self.rightHand.containsNoteGrouping:
            addSpace = False
            self.rightHand.append(symbols['rh_keyboard'], addSpace = True)
            self.leftHand.append(symbols['lh_keyboard'], addSpace = True)
            for dots in binary_dots[noteGroupingR[0]]:
                if dots == '10' or dots == '11':
                    self.rightHand.append(symbols['dot'], addSpace = False)
            for dots in binary_dots[noteGroupingL[0]]:
                if dots == '10' or dots == '11':
                    self.leftHand.append(symbols['dot'], addSpace = False)
        if self.rightHand.canAppend(noteGroupingR, addSpace = addSpace) and \
             self.leftHand.canAppend(noteGroupingL, addSpace = addSpace):
            self.leftHand.append(noteGroupingL, addSpace = addSpace)
            self.rightHand.append(noteGroupingR, addSpace = addSpace)
            if self.rightHand.textLocation > self.leftHand.textLocation:
                self.leftHand.textLocation = self.rightHand.textLocation
            else:
                self.rightHand.textLocation = self.leftHand.textLocation
        else:   
            self.makeNewLines()
            self.rightHand.insert(self.highestMeasureNumberLength - len(measureNumber), measureNumber)
            self.leftHand.textLocation = self.rightHand.textLocation
            self.rightHand.append(symbols['rh_keyboard'], addSpace = True)
            self.leftHand.append(symbols['lh_keyboard'], addSpace = True)
            for dots in binary_dots[noteGroupingR[0]]:
                if dots == '10' or dots == '11':
                    self.rightHand.append(symbols['dot'], addSpace = False)
            for dots in binary_dots[noteGroupingL[0]]:
                if dots == '10' or dots == '11':
                    self.leftHand.append(symbols['dot'], addSpace = False)
            self.leftHand.append(noteGroupingL, addSpace = False)
            self.rightHand.append(noteGroupingR, addSpace = False)
            if self.rightHand.textLocation > self.leftHand.textLocation:
                self.leftHand.textLocation = self.rightHand.textLocation
            else:
                self.rightHand.textLocation = self.leftHand.textLocation
        self.rightHand.containsNoteGrouping = True
        self.leftHand.containsNoteGrouping = True

    def recenterHeadings(self):
        for (indexStart, indexFinal) in self.allHeadings:
            maxLineLength = 0
            for i in range(indexFinal, len(self.allLines)):
                if self.allLines[i].isHeading:
                    break
                lineLength = self.allLines[i].textLocation
                if lineLength > maxLineLength:
                    maxLineLength = lineLength
            if self.lineLength == maxLineLength:
                continue
            for j in range(indexStart, indexFinal):
                lineToCenter = unicode(self.allLines[j])
                lineToCenter = lineToCenter.strip(symbols['space'])
                if maxLineLength > len(lineToCenter):
                    lineToCenter = lineToCenter.center(maxLineLength, symbols['space'])
                    self.allLines[j].insert(0, lineToCenter)
                    self.allLines[j].textLocation = maxLineLength
                    
    def __str__(self):
        self.recenterHeadings()
        return u"\n".join([unicode(l) for l in self.allLines])
            
    
class BrailleTextLine():
    def __init__(self, lineLength):
        self.isHeading = False
        self.containsNoteGrouping = False
        self.lineLength = lineLength
        self.allChars = self.lineLength * [symbols['space']]
        self.textLocation = 0
        self.endOfLine = 0
        
    def append(self, text, addSpace = True):
        if not self.canAppend(text, addSpace):
            raise BrailleTextException("Text does not fit at end of braille text line.")
        if addSpace:
            self.textLocation += 1
        for char in list(text):
            self.allChars[self.textLocation] = char
            self.textLocation += 1
        self.endOfLine = self.textLocation
        return True
    
    def insert(self, textLocation, text):
        if not self.canInsert(textLocation, text):
            raise BrailleTextException("Text cannot be inserted at specified location.")
        self.textLocation = textLocation
        for char in list(text):
            self.allChars[self.textLocation] = char
            self.textLocation += 1
        if self.textLocation > self.endOfLine:
            self.endOfLine = self.textLocation
        return True

    def canAppend(self, text, addSpace = True):
        if self.endOfLine > self.textLocation:
            self.textLocation = self.endOfLine
        if self.textLocation + len(text) + int(addSpace) > self.lineLength:
            return False
        else:
            return True
    
    def canInsert(self, textLocation, text):
        if textLocation + len(text) > self.lineLength:
            return False
        else:
            return True
    
    def __str__(self):
        return u"".join(self.allChars[0:self.textLocation])
    
#-------------------------------------------------------------------------------        

class BrailleTextException(exceptions21.Music21Exception):
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
