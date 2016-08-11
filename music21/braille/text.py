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
from music21.braille.basic import numberToBraille, yieldDots
from music21.ext import six

symbols = lookup.symbols

if six.PY3:
    unicode = str # @ReservedAssignment

class BrailleText(object):
    """
    Object that handles all the formatting associated with braille music notation on multiple lines.
    
    >>> bt = braille.text.BrailleText(lineLength=10, showHand='right')
    >>> bt.lineLength
    10
    >>> bt.allLines
    [<music21.braille.text.BrailleTextLine object at 0x10af8a6a0>]
    >>> bt.rightHandSymbol
    True
    >>> bt.leftHandSymbol
    False
    >>> bt.allHeadings
    []
    """
    def __init__(self, lineLength=40, showHand=None):
        self.lineLength = lineLength
        self.allLines = []
        self.makeNewLine()
        
        self._showHand = None
        self.rightHandSymbol = False
        self.leftHandSymbol = False
        self.allHeadings = []
        
        self.showHand = showHand

    @property
    def showHand(self):
        return self._showHand

    @showHand.setter
    def showHand(self, newHand):
        if newHand == 'right':
            self.rightHandSymbol = True
        elif newHand == 'left':
            self.leftHandSymbol = True
        elif newHand is not None:
            raise BrailleTextException("Illegal hand sign request.")


    def addHeading(self, heading):
        u'''
        adds a heading to the BrailleText.  Heading can be a single or multiple line
        Unicode string representing a heading.
        
        These headings are not stored in allHeadings, but instead in .allLines,
        what .allHeadings stores is the index of the start of a heading section
        and the index of the end of a heading section.
        
        (since each BrailleTextLine knows whether it is a heading or not, storing
        the index of headings might be overkill)
        
        >>> if ext.six.PY2: str = unicode #_DOCS_HIDE
        >>> bt = braille.text.BrailleText(lineLength=10)
        >>> headingText = braille.basic.timeSigToBraille(meter.TimeSignature('4/8'))        
        >>> bt.addHeading(headingText)
        >>> len(bt.allLines)
        2
        >>> bt.allLines[0].isHeading
        True
        >>> print(str(bt.allLines[0]))
        ⠼⠙⠦
        >>> bt.allHeadings
        [(0, 1)]
        >>> bt.addMeasureNumber(7)
        >>> headingText = braille.basic.timeSigToBraille(meter.TimeSignature('3/4'))        
        >>> bt.addHeading(headingText)
        >>> len(bt.allLines)
        4
        >>> bt.allHeadings
        [(0, 1), (2, 3)]
        '''
        if self.currentLine.textLocation != 0:
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
        
    def addLongExpression(self, longExpr):
        '''
        Adds an expression long enough that it is split at
        each space symbol such that line wrapping could occur.
        
        
        >>> if ext.six.PY2: str = unicode #_DOCS_HIDE
        >>> bt = braille.text.BrailleText(lineLength=10)
        >>> 
        '''
        for brailleExpr in longExpr.split(symbols['space']):
            self.appendOrInsertCurrent(brailleExpr)
        
    
    def addToNewLine(self, brailleNoteGrouping):
        u'''
        Adds a NoteGrouping to a new line, prefacing that new line
        with the appropriate spaces or keyboard symbols and dots.
        
        >>> if ext.six.PY2: str = unicode #_DOCS_HIDE
        >>> bt = braille.text.BrailleText(10)
        >>> bt.currentLine.append('hi', addSpace=False)
        >>> print(str(bt))
        hi
        >>> c = braille.lookup.pitchNameToNotes['C']['quarter']  # dots 1456
        >>> bt.addToNewLine(c + c + c)
        >>> print(str(bt))
        hi
        ⠀⠀⠹⠹⠹

        It is done differently if there are hand symbols involved:
        
        >>> bt = braille.text.BrailleText(10)
        >>> bt.showHand = 'right'
        >>> bt.currentLine.append('hi', addSpace=False)
        >>> bt.addToNewLine(c + c + c)
        >>> print(str(bt))
        hi
        ⠨⠜⠄⠹⠹⠹
        
        '''
        self.makeNewLine()
        if self.rightHandSymbol or self.leftHandSymbol:
            self.optionalAddKeyboardSymbolsAndDots(brailleNoteGrouping)
            self.currentLine.append(brailleNoteGrouping, addSpace=False)
        else:
            self.currentLine.insert(2, brailleNoteGrouping)        
        
    
    def appendOrInsertCurrent(self, brailleExpr, addSpace=True):
        u'''
        append expression to the current line if it is possible,
        or make a new line and insert it there:
        
        >>> if ext.six.PY2: str = unicode #_DOCS_HIDE
        >>> bt = braille.text.BrailleText(lineLength=10)
        >>> bt.appendOrInsertCurrent(u"hello", addSpace=False)
        >>> print(str(bt))
        hello
        >>> bt.appendOrInsertCurrent(braille.lookup.symbols['space'] + u"hi")
        >>> print(str(bt))
        hello⠀⠀hi
        >>> bt.appendOrInsertCurrent(braille.lookup.symbols['space'] + u"there")
        >>> print(str(bt))
        hello⠀⠀hi
        ⠀⠀⠀there
        '''
        if self.currentLine.canAppend(brailleExpr, addSpace=addSpace):
            self.currentLine.append(brailleExpr, addSpace=addSpace)
        else:
            self.makeNewLine()
            self.currentLine.insert(2, brailleExpr)
    
    
    
#     def addInaccord(self, inaccord):
#         addSpace = self.optionalAddKeyboardSymbolsAndDots(inaccord)
# 
#         try:
#             self.currentLine.append(inaccord, addSpace=addSpace)
#         except BrailleTextException:
#             self.makeNewLine()
#             if self.rightHandSymbol or self.leftHandSymbol:
#                 if self.rightHandSymbol:
#                     self.currentLine.insert(2, symbols['rh_keyboard'])
#                 elif self.leftHandSymbol:
#                     self.currentLine.insert(2, symbols['lh_keyboard'])
#                 for dot in yieldDots(inaccord[0]):
#                     self.currentLine.append(dot, addSpace=False)
#                 self.currentLine.append(inaccord, addSpace=False)
#             else:
#                 self.currentLine.insert(2, inaccord)
#         self.currentLine.containsNoteGrouping = True
    
    def addMeasureNumber(self, measureNumber):
        u'''
        Add a measure number (either a braille number or an int).
        
        >>> if ext.six.PY2: str = unicode #_DOCS_HIDE
        >>> bt = braille.text.BrailleText(lineLength=10)
        >>> bt.allLines
        [<music21.braille.text.BrailleTextLine object at 0x10af8a6a0>]
        >>> bt.addMeasureNumber(4)
        >>> print(str(bt.allLines[0]))
        ⠼⠙
        >>> bt.currentLine.textLocation
        2
        
        If there are already lines, then add a new one:
        
        >>> bt.addMeasureNumber(5)
        >>> bt.allLines
        [<music21.braille.text.BrailleTextLine object at 0x10af8a6a0>,
         <music21.braille.text.BrailleTextLine object at 0x10af8a6b3>]
        >>> print(str(bt.allLines[-1]))
        ⠼⠑
        '''
        if isinstance(measureNumber, int):
            measureNumber = numberToBraille(measureNumber)
            
        if self.currentLine.textLocation != 0:
            self.makeNewLine()
        self.currentLine.append(measureNumber, addSpace=False)

    
    def optionalAddKeyboardSymbolsAndDots(self, noteGrouping=None):
        '''
        Adds symbols for rh_keyboard or lh_keyboard depending on what
        is appropriate
        
        returns a boolean indicating whether a space needs to be added
        before the next symbol is needed. 
        '''
        addSpace = True
        if (not self.currentLine.containsNoteGrouping
                and (self.rightHandSymbol or self.leftHandSymbol)):
            if self.currentLine.textLocation == 0:
                addSpace = False
            if self.rightHandSymbol:
                self.currentLine.append(symbols['rh_keyboard'], addSpace=addSpace)
            elif self.leftHandSymbol:
                self.currentLine.append(symbols['lh_keyboard'], addSpace=addSpace)
            if noteGrouping:
                for dot in yieldDots(noteGrouping[0]):
                    self.currentLine.append(dot, addSpace=False)
            addSpace = False

        if self.currentLine.textLocation == 0:
            addSpace = False
        
        return addSpace
        

    def addSignatures(self, signatures):
        u'''
        Appends signatures to the current location if there is space, otherwise appends to
        a new line:
        
        >>> if ext.six.PY2: str = unicode #_DOCS_HIDE
        >>> bt = braille.text.BrailleText(lineLength=5)
        >>> bt.addSignatures(braille.basic.timeSigToBraille(meter.TimeSignature('4/8')))
        >>> print(str(bt.currentLine))
        ⠼⠙⠦
        >>> bt.addSignatures(braille.basic.timeSigToBraille(meter.TimeSignature('3/4')))
        >>> print(str(bt.currentLine))
        ⠀⠀⠼⠉⠲
        >>> len(bt.allLines)
        2
        '''
        addSpace = True
        if self.currentLine.textLocation == 0:
            addSpace = False

        self.appendOrInsertCurrent(signatures, addSpace=addSpace)

    def makeNewLine(self):
        u'''
        Add a newline to the BrailleText
        
        >>> bt = braille.text.BrailleText(lineLength=10)
        >>> len(bt.allLines)
        1
        >>> bt.makeNewLine()
        >>> len(bt.allLines)
        2
        >>> bt.makeNewLine()
        >>> len(bt.allLines)
        3
        '''
        self.currentLine = BrailleTextLine(self.lineLength)
        self.allLines.append(self.currentLine)
            
    def recenterHeadings(self):
        u'''
        Recenter each of the headings so that they exactly align
        with the text beneath them.
        
        Demonstration with non braille text...
        
        >>> if ext.six.PY2: str = unicode #_DOCS_HIDE
        >>> heading1 = u'hello'
        >>> body1 = u'anyoneHome?' + braille.lookup.symbols['space'] + u'yup!'
        >>> bt = braille.text.BrailleText(lineLength=12)
        >>> bt.addHeading(heading1)
        >>> bt.addLongExpression(body1)
        >>> bt.allHeadings
        [(0, 1)]
        >>> bt.recenterHeadings()
        >>> print(str(bt))
        ⠀⠀⠀hello⠀⠀⠀⠀
        ⠀anyoneHome?
        ⠀⠀yup!

        Each heading is aligned with its own text
        
        >>> heading2 = u'buh'
        >>> body2 = u'short' + braille.lookup.symbols['space'] + u'court'
        >>> bt.addHeading(heading2)
        >>> bt.addLongExpression(body2)
        >>> bt.allHeadings
        [(0, 1), (3, 4)]
        >>> bt.recenterHeadings()
        >>> print(str(bt))
        ⠀⠀⠀hello⠀⠀⠀⠀
        ⠀anyoneHome?
        ⠀⠀yup!
        ⠀⠀⠀⠀buh⠀⠀⠀⠀⠀
        ⠀short⠀court
        '''
        for (indexStart, indexFinal) in self.allHeadings:
            maxLineLength = 0
            for i in range(indexFinal, len(self.allLines)):
                if self.allLines[i].isHeading:
                    break
                lineLength = self.allLines[i].textLocation
                if lineLength > maxLineLength:
                    maxLineLength = lineLength
            for j in range(indexStart, indexFinal):
                brailleTextLine = self.allLines[j]
                lineStrToCenter = unicode(brailleTextLine)
                lineStrToCenter = lineStrToCenter.strip(symbols['space'])
                if maxLineLength > len(lineStrToCenter):
                    lineStrToCenter = lineStrToCenter.center(maxLineLength, symbols['space'])
                    brailleTextLine.insert(0, lineStrToCenter)
                    brailleTextLine.textLocation = maxLineLength
                    
    
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
        super(BrailleKeyboard, self).__init__(lineLength=lineLength)
        self.rightHandLine = None
        self.leftHandLine = None
        self.highestMeasureNumberLength = 0 # used in BraileKeyboard layouts

#     def addElement(self, **elementKeywords):
#         if 'pair' in elementKeywords:
#             (measureNumber, noteGroupingR, noteGroupingL) = elementKeywords['pair']
#             self.addNoteGroupings(measureNumber, noteGroupingL, noteGroupingR)
#         else:
#             return super(BrailleKeyboard, self).addElement(**elementKeywords)


    def makeNewLines(self):
        if self.currentLine.textLocation == 0:
            self.rightHandLine = self.currentLine
        else:
            self.rightHandLine = BrailleTextLine(self.lineLength)
            self.allLines.append(self.rightHandLine)

        self.leftHandLine = BrailleTextLine(self.lineLength)
        self.allLines.append(self.leftHandLine)

    def addNoteGroupings(self, measureNumber, noteGroupingR, noteGroupingL):
        if self.rightHandLine is None and self.leftHandLine is None:
            self.makeNewLines()
        if self.rightHandLine.textLocation == 0:
            self.rightHandLine.insert(self.highestMeasureNumberLength - len(measureNumber), 
                                  measureNumber)
            self.leftHandLine.textLocation = self.rightHandLine.textLocation
        addSpace = True
        if self.rightHandLine.containsNoteGrouping is False:
            addSpace = False
            self.rightHandLine.append(symbols['rh_keyboard'], addSpace=True)
            self.leftHandLine.append(symbols['lh_keyboard'], addSpace=True)
            if len(noteGroupingR) > 0:
                for dot in yieldDots(noteGroupingR[0]):
                    self.rightHandLine.append(dot, addSpace=False)
            if len(noteGroupingL) > 0:
                for dot in yieldDots(noteGroupingL[0]):
                    self.leftHandLine.append(dot, addSpace=False)
        if (self.rightHandLine.canAppend(noteGroupingR, addSpace=addSpace) 
                and self.leftHandLine.canAppend(noteGroupingL, addSpace=addSpace)):
            if noteGroupingL:
                self.leftHandLine.append(noteGroupingL, addSpace=addSpace)
            if noteGroupingR:
                self.rightHandLine.append(noteGroupingR, addSpace=addSpace)
            if self.rightHandLine.textLocation > self.leftHandLine.textLocation:
                self.leftHandLine.textLocation = self.rightHandLine.textLocation
            else:
                self.rightHandLine.textLocation = self.leftHandLine.textLocation
        else:   
            self.makeNewLines()
            self.rightHandLine.insert(self.highestMeasureNumberLength - len(measureNumber), 
                                  measureNumber)
            self.leftHandLine.textLocation = self.rightHandLine.textLocation
            self.rightHandLine.append(symbols['rh_keyboard'], addSpace=True)
            self.leftHandLine.append(symbols['lh_keyboard'], addSpace=True)
            if len(noteGroupingR) > 0:
                for dot in yieldDots(noteGroupingR[0]):
                    self.rightHandLine.append(dot, addSpace=False)
                self.rightHandLine.append(noteGroupingR, addSpace=False)
            
            if len(noteGroupingL) > 0:
                for dot in yieldDots(noteGroupingL[0]):
                    self.leftHandLine.append(dot, addSpace=False)
                self.leftHandLine.append(noteGroupingL, addSpace=False)
            if self.rightHandLine.textLocation > self.leftHandLine.textLocation:
                self.leftHandLine.textLocation = self.rightHandLine.textLocation
            else:
                self.rightHandLine.textLocation = self.leftHandLine.textLocation
        self.rightHandLine.containsNoteGrouping = True
        self.leftHandLine.containsNoteGrouping = True

            
    
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
    >>> if ext.six.PY2: str = unicode #_DOCS_HIDE
    >>> print(str(btl))
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
        >>> if ext.six.PY2: str = unicode #_DOCS_HIDE
        >>> print(str(btl))
        ⠈⠉
        >>> btl.textLocation
        2
        >>> btl.highestUsedLocation
        2
        
        Default is to add a space:
        
        >>> btl.append(braille.lookup.symbols['tie'])
        >>> print(str(btl))
        ⠈⠉⠀⠈⠉

        Out of room:
        
        >>> btl.append(braille.lookup.symbols['tie'])
        Traceback (most recent call last):
        music21.braille.text.BrailleTextException: Text does not fit at end of braille text line.
        
        Text is appended at `textLocation`, overwriting other text that might be there.
        
        >>> btl.textLocation = btl.highestUsedLocation = 0
        >>> btl.append('hi', addSpace=False)
        >>> btl.textLocation = btl.highestUsedLocation = 5
        >>> print(str(btl))
        hi⠀⠈⠉
        '''
        if not self.canAppend(text, addSpace):
            raise BrailleTextException("Text does not fit at end of braille text line.")
        if addSpace:
            self.allChars[self.textLocation] = symbols['space']
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
        >>> if ext.six.PY2: str = unicode #_DOCS_HIDE
        >>> print(str(btl))
        ⠀⠀⠈⠉
        >>> btl.textLocation
        4
        >>> btl.highestUsedLocation
        4
        
        >>> btl.insert(0, braille.lookup.symbols['tie'])
        
        It looks like we have deleted the previous tie:
        
        >>> print(str(btl))
        ⠈⠉
        
        But that's because only characters up to .textLocation are printed
        (this may change later)
        
        >>> btl.textLocation
        2
        >>> btl.highestUsedLocation
        4
        
        Let's change textLocation and now see:
        
        >>> btl.textLocation = btl.highestUsedLocation
        >>> print(str(btl))
        ⠈⠉⠈⠉
        
        Inserting beyond the end creates an error:

        >>> btl.insert(5, braille.lookup.symbols['tie'])
        Traceback (most recent call last):
        music21.braille.text.BrailleTextException: Text cannot be inserted at specified location.
        
        Unlike list inserts, this insert overwrites the previous text:
        
        >>> btl.insert(0, "hi")
        >>> btl.textLocation = btl.highestUsedLocation
        >>> print(str(btl))
        hi⠈⠉
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
        
    def lastHyphenToSpace(self):
        u'''
        Occasionally a line ends with a hyphen because
        the last appender thought it would be helpful, such as
        to put more characters into a line.  But in case it
        is not, then this method will change that last character
        to a space and set textLocation back one character
        so it is not printed.
        
        >>> bt = braille.text.BrailleTextLine(10)
        >>> bt.append('hi', addSpace=False)
        >>> bt.append(braille.lookup.symbols['music_hyphen'], addSpace=False)
        >>> if ext.six.PY2: str = unicode # _DOCS_HIDE
        >>> print(str(bt))
        hi⠐
        >>> bt.textLocation
        3
        >>> print(bt.allChars[2])
        ⠐
        >>> bt.lastHyphenToSpace()
        >>> print(str(bt))
        hi
        >>> bt.allChars[2] == braille.lookup.symbols['space']
        True
        >>> bt.textLocation
        2
        '''
        prevLoc = self.textLocation - 1
        if prevLoc < 0:
            return
        prevChar = self.allChars[prevLoc]
        if prevChar == symbols['music_hyphen']: # and not forceHyphen:
            self.allChars[prevLoc] = symbols['space']
            self.textLocation -= 1
    
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
