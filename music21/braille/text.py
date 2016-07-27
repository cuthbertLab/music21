# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         text.py
# Purpose:      music21 class which allows for accurate formatting of braille transcription
# Authors:      Jose Cabal-Ugaz
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2011, 2016 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
from __future__ import division, print_function

import unittest

from music21 import exceptions21

from music21.braille import lookup
from music21.ext import six

symbols = lookup.symbols
binary_dots = lookup.binary_dots

if six.PY3:
    unicode = str # @ReservedAssignment

class BrailleText(object):
    """
    Object that handles all the formatting associated with braille music notation.
    """
    def __init__(self, lineLength=40, showHand=None):
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
        if 'withHyphen' in elementKeywords:
            withHyphen = elementKeywords['withHyphen']
        else:
            withHyphen = False

        if 'forceHyphen' in elementKeywords:
            forceHyphen = elementKeywords['forceHyphen']
        else:
            forceHyphen = False
        if 'forceNewline' in elementKeywords:
            forceNewline = elementKeywords['forceNewline']
        else:
            forceNewline = False
            
        if 'heading' in elementKeywords:
            self.addHeading(elementKeywords['heading'])
        elif 'measureNumber' in elementKeywords:
            self.addMeasureNumber(elementKeywords['measureNumber'], withHyphen)
        elif 'keyOrTimeSig' in elementKeywords:
            self.addSignatures(elementKeywords['keyOrTimeSig'], withHyphen)
        elif 'noteGrouping' in elementKeywords:
            noteGrouping = elementKeywords['noteGrouping']
            showLeadingOctave = elementKeywords['showLeadingOctave']
            self.addNoteGrouping(noteGrouping, 
                                 showLeadingOctave, 
                                 withHyphen, 
                                 forceHyphen, 
                                 forceNewline)
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
        
        brailleCurrentLine = self.currentLine
        for headingLine in heading.splitlines():
            brailleCurrentLine.isHeading = True
            brailleCurrentLine.append(headingLine, addSpace=False)
            self.makeNewLine()
            indexFinal += 1
        self.allHeadings.append((indexStart, indexFinal))
        
    def addLongExpression(self, longExpr, withHyphen=False):
        if withHyphen:
            self.currentLine.append(symbols['music_hyphen'], addSpace=False)
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
                    self.currentLine.append(symbols['rh_keyboard'], addSpace=addSpace)
                elif self.leftHandSymbol:
                    self.currentLine.append(symbols['lh_keyboard'], addSpace=addSpace)
                for dots in binary_dots[inaccord[0]]:
                    if dots == '10' or dots == '11':
                        self.currentLine.append(symbols['dot'], addSpace=False)
                addSpace = False
        try:
            if not self.currentLine.textLocation:
                addSpace = False
            self.currentLine.append(inaccord, addSpace=addSpace)
        except BrailleTextException:
            self.makeNewLine()
            if self.rightHandSymbol or self.leftHandSymbol:
                if self.rightHandSymbol:
                    self.currentLine.insert(2, symbols['rh_keyboard'])
                elif self.leftHandSymbol:
                    self.currentLine.insert(2, symbols['lh_keyboard'])
                for dots in binary_dots[inaccord[0]]:
                    if dots == '10' or dots == '11':
                        self.currentLine.append(symbols['dot'], addSpace=False)
                self.currentLine.append(inaccord, addSpace=False)
            else:
                self.currentLine.insert(2, inaccord)
        self.currentLine.containsNoteGrouping = True
    
    def addMeasureNumber(self, measureNumber, withHyphen=False):
        if withHyphen:
            self.currentLine.append(symbols['music_hyphen'], addSpace=False)
            self.makeNewLine()
        elif not self.currentLine.textLocation == 0:
            self.makeNewLine()
        self.currentLine.append(measureNumber, addSpace=False)

    def addNoteGrouping(self, 
                        noteGrouping, 
                        showLeadingOctave=False, 
                        withHyphen=False,
                        forceHyphen=False, 
                        forceNewline=False):
        addSpace = True
        if not self.currentLine.containsNoteGrouping:
            if self.rightHandSymbol or self.leftHandSymbol:
                if not self.currentLine.textLocation:
                    addSpace = False
                if self.rightHandSymbol:
                    self.currentLine.append(symbols['rh_keyboard'], addSpace=addSpace)
                elif self.leftHandSymbol:
                    self.currentLine.append(symbols['lh_keyboard'], addSpace=addSpace)
                for dots in binary_dots[noteGrouping[0]]:
                    if dots == '10' or dots == '11':
                        self.currentLine.append(symbols['dot'], addSpace=False)
                addSpace = False
        try:
            if not self.currentLine.textLocation:
                addSpace = False
            if withHyphen:
                self.currentLine.append(u"".join([noteGrouping, symbols['music_hyphen']]), 
                                        addSpace=addSpace)
            else:
                self.currentLine.append(noteGrouping, addSpace=addSpace)
        except BrailleTextException:
            ll4 = self.lineLength // 4
            if (not forceNewline 
                    and self.lineLength - self.currentLine.textLocation > ll4 
                    and ll4 <= len(noteGrouping)):
                raise BrailleTextException("Split Note Grouping")
            elif not showLeadingOctave:
                raise BrailleTextException("Recalculate Note Grouping With Leading Octave")
            else:
                if not forceHyphen:
                    prevChar = self.currentLine.allChars[self.currentLine.textLocation - 1]
                    if prevChar == symbols['music_hyphen']:
                        prevLoc = self.currentLine.textLocation - 1
                        self.currentLine.allChars[prevLoc] = symbols['space']
                        self.currentLine.textLocation -= 1
                self.makeNewLine()
                if self.rightHandSymbol or self.leftHandSymbol:
                    if self.rightHandSymbol:
                        self.currentLine.insert(2, symbols['rh_keyboard'])
                    elif self.leftHandSymbol:
                        self.currentLine.insert(2, symbols['lh_keyboard'])
                    for dots in binary_dots[noteGrouping[0]]:
                        if dots == '10' or dots == '11':
                            self.currentLine.append(symbols['dot'], addSpace=False)
                    self.currentLine.append(noteGrouping, addSpace=False)
                else:
                    self.currentLine.insert(2, noteGrouping)
                if withHyphen:
                    self.currentLine.append(symbols['music_hyphen'], addSpace=False)
        self.currentLine.containsNoteGrouping = True

    def addSignatures(self, signatures, withHyphen=False):
        if withHyphen:
            self.currentLine.append(symbols['music_hyphen'], addSpace=False)
        try:
            addSpace = True
            if not self.currentLine.textLocation:
                addSpace = False
            self.currentLine.append(signatures, addSpace=addSpace)
        except BrailleTextException:
            self.makeNewLine()
            self.currentLine.insert(2, signatures)

    def makeNewLine(self):
        '''
        Add a newline to the BrailleText
        '''
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
    
    def __unicode__(self):
        self.recenterHeadings()
        return u"\n".join([unicode(l) for l in self.allLines])

    if six.PY3:
        __str__ = __unicode__
        del(__unicode__)


class BrailleKeyboard(BrailleText):
    '''
    A subclass of BrailleText that handles both hands at once.
    '''
    def __init__(self, lineLength=40):
        self.lineLength = lineLength
        self.allLines = []
        self.makeNewLine()
        self.allHeadings = []
        self.rightHand = None
        self.leftHand = None

    def addElement(self, **elementKeywords):
        if 'pair' in elementKeywords:
            (measureNumber, noteGroupingR, noteGroupingL) = elementKeywords['pair']
            self.addNoteGroupings(measureNumber, noteGroupingL, noteGroupingR)
        else:
            return super(BrailleKeyboard, self).addElement(**elementKeywords)


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
            self.rightHand.insert(self.highestMeasureNumberLength - len(measureNumber), 
                                  measureNumber)
            self.leftHand.textLocation = self.rightHand.textLocation
        addSpace = True
        if not self.rightHand.containsNoteGrouping:
            addSpace = False
            self.rightHand.append(symbols['rh_keyboard'], addSpace=True)
            self.leftHand.append(symbols['lh_keyboard'], addSpace=True)
            for dots in binary_dots[noteGroupingR[0]]:
                if dots == '10' or dots == '11':
                    self.rightHand.append(symbols['dot'], addSpace=False)
            for dots in binary_dots[noteGroupingL[0]]:
                if dots == '10' or dots == '11':
                    self.leftHand.append(symbols['dot'], addSpace=False)
        if (self.rightHand.canAppend(noteGroupingR, addSpace=addSpace) 
                and self.leftHand.canAppend(noteGroupingL, addSpace=addSpace)):
            self.leftHand.append(noteGroupingL, addSpace=addSpace)
            self.rightHand.append(noteGroupingR, addSpace=addSpace)
            if self.rightHand.textLocation > self.leftHand.textLocation:
                self.leftHand.textLocation = self.rightHand.textLocation
            else:
                self.rightHand.textLocation = self.leftHand.textLocation
        else:   
            self.makeNewLines()
            self.rightHand.insert(self.highestMeasureNumberLength - len(measureNumber), 
                                  measureNumber)
            self.leftHand.textLocation = self.rightHand.textLocation
            self.rightHand.append(symbols['rh_keyboard'], addSpace=True)
            self.leftHand.append(symbols['lh_keyboard'], addSpace=True)
            for dots in binary_dots[noteGroupingR[0]]:
                if dots == '10' or dots == '11':
                    self.rightHand.append(symbols['dot'], addSpace=False)
            for dots in binary_dots[noteGroupingL[0]]:
                if dots == '10' or dots == '11':
                    self.leftHand.append(symbols['dot'], addSpace=False)
            self.leftHand.append(noteGroupingL, addSpace=False)
            self.rightHand.append(noteGroupingR, addSpace=False)
            if self.rightHand.textLocation > self.leftHand.textLocation:
                self.leftHand.textLocation = self.rightHand.textLocation
            else:
                self.rightHand.textLocation = self.leftHand.textLocation
        self.rightHand.containsNoteGrouping = True
        self.leftHand.containsNoteGrouping = True

            
    
class BrailleTextLine(object):
    u"""
    An object representing a single line of braille text:
    
    The initial value is the length of the line:
    
    >>> btl = braille.text.BrailleTextLine(40)
    >>> btl.isHeading
    False
    >>> btl.containsNoteGrouping
    False
    >>> btl.lineLength
    40
    >>> btl.textLocation
    0
    >>> btl.highestUsedLocation
    0
    >>> btl.allChars == 40 * [braille.lookup.symbols['space']]
    True

    >>> btl.append(braille.lookup.symbols['tie'])
    >>> btl
    <music21.braille.text.BrailleTextLine object at 0x10af9c630>
    >>> if ext.six.PY3: unicode = str #_DOCS_HIDE
    >>> print(unicode(btl))
    ⠀⠈⠉
    """
    def __init__(self, lineLength=40):
        self.isHeading = False
        self.containsNoteGrouping = False
        self.lineLength = lineLength
        self.allChars = self.lineLength * [symbols['space']]
        self.textLocation = 0
        self.highestUsedLocation = 0
        
    def append(self, text, addSpace=True):
        u'''
        Appends text (with optional space at the beginning) or raises an
        exception if it cannot be appended.
        
        >>> btl = braille.text.BrailleTextLine(6)
        >>> btl.append(braille.lookup.symbols['tie'], addSpace=False)
        >>> if ext.six.PY3: unicode = str #_DOCS_HIDE
        >>> print(unicode(btl))
        ⠈⠉
        >>> btl.textLocation
        2
        >>> btl.highestUsedLocation
        2
        
        Default is to add a space:
        
        >>> btl.append(braille.lookup.symbols['tie'])
        >>> print(unicode(btl))
        ⠈⠉⠀⠈⠉

        Out of room:
        
        >>> btl.append(braille.lookup.symbols['tie'])
        Traceback (most recent call last):
        BrailleTextException: Text does not fit at end of braille text line.
        '''
        if not self.canAppend(text, addSpace):
            raise BrailleTextException("Text does not fit at end of braille text line.")
        if addSpace:
            self.textLocation += 1
        for char in list(text):
            self.allChars[self.textLocation] = char
            self.textLocation += 1
        self.highestUsedLocation = self.textLocation
    
    def insert(self, textLocation, text):
        u'''
        Inserts text at a certain location, updating textLocation and possibly
        highestUsedLocation:
        
        >>> btl = braille.text.BrailleTextLine(6)
        >>> btl.insert(2, braille.lookup.symbols['tie'])
        >>> if ext.six.PY3: unicode = str #_DOCS_HIDE
        >>> print(unicode(btl))
        ⠀⠀⠈⠉
        >>> btl.textLocation
        4
        >>> btl.highestUsedLocation
        4
        
        >>> btl.insert(0, braille.lookup.symbols['tie'])
        
        It looks like we have deleted the previous tie:
        
        >>> print(unicode(btl))
        ⠈⠉
        
        But that's because only characters up to .textLocation are printed
        (this may change later)
        
        >>> btl.textLocation
        2
        >>> btl.highestUsedLocation
        4
        
        Let's change textLocation and now see:
        
        >>> btl.textLocation = btl.highestUsedLocation
        >>> print(unicode(btl))
        ⠈⠉⠈⠉
        
        Inserting beyond the end creates an error:

        >>> btl.insert(5, braille.lookup.symbols['tie'])
        Traceback (most recent call last):
        BrailleTextException: Text cannot be inserted at specified location.
        '''
        if not self.canInsert(textLocation, text):
            raise BrailleTextException("Text cannot be inserted at specified location.")
        self.textLocation = textLocation
        for char in list(text):
            self.allChars[self.textLocation] = char
            self.textLocation += 1
        if self.textLocation > self.highestUsedLocation:
            self.highestUsedLocation = self.textLocation

    def canAppend(self, text, addSpace=True):
        '''
        Returns True if there is enough space in this line to append the text, or False
        if not:
        
        >>> btl = braille.text.BrailleTextLine(10)
        >>> btl.canAppend('1234567890', addSpace=False)
        True
        >>> btl.canAppend('12345678901', addSpace=False)
        False
        >>> btl.canAppend('1234567890', addSpace=True)
        False
        >>> btl.textLocation
        0
        >>> btl.textLocation = 5
        >>> btl.canAppend('12345', addSpace=False)
        True
        >>> btl.canAppend('123456', addSpace=False)
        False
        
        If highestUsedLocation > textLocation, highestUsedLocation is used instead:
        
        >>> btl.highestUsedLocation = 7
        >>> btl.canAppend('123', addSpace=False)
        True
        >>> btl.canAppend('1234', addSpace=False)
        False
        '''
        if self.highestUsedLocation > self.textLocation:
            searchLocation = self.highestUsedLocation
        else:
            searchLocation = self.textLocation
        addSpaceAmount = 1 if addSpace else 0
        if (searchLocation + len(text) + addSpaceAmount) > self.lineLength:
            return False
        else:
            return True
    
    def canInsert(self, textLocation, text):
        '''
        Returns True if there is enough space starting at textLocation to append
        the text. False otherwise:
        
        >>> btl = braille.text.BrailleTextLine(10)
        >>> btl.canInsert(4, '123456')
        True
        >>> btl.canInsert(5, '123456')
        False
        '''
        if textLocation + len(text) > self.lineLength:
            return False
        else:
            return True
    
    def __unicode__(self):
        return u"".join(self.allChars[0:self.textLocation])

    if six.PY3:
        __str__ = __unicode__
        del(__unicode__)
    
    
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
