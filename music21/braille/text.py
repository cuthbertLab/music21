# -*- coding: utf-8 -*-
#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         text.py
# Purpose:      music21 class which allows for accurate formatting of braille transcription
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import music21
import collections

from music21.braille import lookup

symbols = lookup.symbols
binary_dots = lookup.binary_dots

class BrailleText():
    '''
    Object that handles all the formatting associated with braille music notation.
    '''
    def __init__(self, maxLineLength):
        self.lineNumber = 1
        self.linePos = 0
        self.allLines = collections.defaultdict(str)
        self.maxLineLength = maxLineLength
        
    def addElement(self, **elementKeywords):
        if 'heading' in elementKeywords:
            if not (self.lineNumber == 1 or self.linePos == 0):
                self.lineNumber += 1
                self.linePos = 0
            for headingLine in elementKeywords['heading'].splitlines():
                self.allLines[self.lineNumber] = headingLine
                self.lineNumber += 1
            return
        if 'measureNumber' in elementKeywords:
            withHyphen = False
            if 'withHyphen' in elementKeywords:
                withHyphen = elementKeywords['withHyphen']
            if not(len(self.allLines[self.lineNumber]) == 0):
                if withHyphen:
                    self.allLines[self.lineNumber] += symbols['music_hyphen']
                self.lineNumber += 1
                self.linePos = 0
            self.allLines[self.lineNumber] = elementKeywords['measureNumber']
            self.linePos += len(elementKeywords['measureNumber'])
            return
        if 'longExpression' in elementKeywords:
            longExpression = elementKeywords['longExpression']
            withHyphen = elementKeywords['withHyphen']
            if withHyphen == True:
                if self.linePos == 40:
                    raise BrailleTranslateException("Crazy error I can't deal with right now.")
                self.allLines[self.lineNumber] += symbols['music_hyphen']
                self.linePos += 1
                
            for brailleExpr in longExpression.split(u"\u2800"):
                if self.linePos + len(brailleExpr) + 1 > self.maxLineLength:
                    self.allLines[self.lineNumber] += symbols['space'] * (self.maxLineLength - self.linePos)
                    self.lineNumber += 1
                    self.allLines[self.lineNumber] = u"".join([symbols['double_space'], brailleExpr])
                    self.linePos = len(brailleExpr) + 2
                else:
                    self.allLines[self.lineNumber] += u"".join([symbols['space'], brailleExpr])
                    self.linePos += len(brailleExpr) + 1
            return
        if 'keyOrTimeSig' in elementKeywords:
            keyOrTimeSig = elementKeywords['keyOrTimeSig']
            withHyphen = elementKeywords['withHyphen']
            if self.linePos + len(keyOrTimeSig) + 1 + int(withHyphen) > self.maxLineLength:
                self.allLines[self.lineNumber] += symbols['space'] * (self.maxLineLength - self.linePos)
                self.lineNumber += 1
                self.allLines[self.lineNumber] = u"".join([symbols['double_space'], keyOrTimeSig])
                self.linePos = len(keyOrTimeSig) + 2
            else:
                if not len(self.allLines[self.lineNumber]) == 0:
                    if withHyphen:
                        self.allLines[self.lineNumber] += symbols['music_hyphen']
                        self.linePos += 1
                    self.allLines[self.lineNumber] += symbols['space']
                    self.linePos += 1
                self.allLines[self.lineNumber] += keyOrTimeSig
                self.linePos += len(keyOrTimeSig)
            return
        if 'noteGrouping' in elementKeywords:
            noteGrouping = elementKeywords['noteGrouping']
            showLeadingOctave = elementKeywords['showLeadingOctave']
            withHyphen = elementKeywords['withHyphen']
            try:
                forceHyphen = elementKeywords['forceHyphen']
            except KeyError:
                forceHyphen = True
            if self.linePos + len(noteGrouping) + 1 + int(withHyphen) > self.maxLineLength:
                if (self.maxLineLength - self.linePos > self.maxLineLength / 4 and len(noteGrouping) >= self.maxLineLength / 4):
                    #"Note grouping needs to be split in two parts."
                    raise BrailleTextException("Split Note Grouping")
                elif showLeadingOctave == False:
                    #"Note grouping needs to be recalculated with a leading octave."
                    raise BrailleTextException("Recalculate Note Grouping With Leading Octave")
                else:
                    if withHyphen and forceHyphen:
                        self.allLines[self.lineNumber] += symbols['music_hyphen']
                        self.linePos += 1
                    self.allLines[self.lineNumber] += symbols['space'] * (self.maxLineLength - self.linePos)
                    self.lineNumber += 1
                    self.allLines[self.lineNumber] = u"".join([symbols['double_space'], noteGrouping])
                    self.linePos = len(noteGrouping) + 2
            else:
                if not len(self.allLines[self.lineNumber]) == 0 and not self.linePos == 0:
                    if withHyphen:
                        self.allLines[self.lineNumber] += symbols['music_hyphen']
                        self.linePos += 1
                    self.allLines[self.lineNumber] += symbols['space']
                    self.linePos += 1
                self.allLines[self.lineNumber] += noteGrouping
                self.linePos += len(noteGrouping)
            return
        if 'pair' in elementKeywords:
            (measureNumber, rh_braille, lh_braille) = elementKeywords['pair']
            isFirstOfLine = False
            rh_all = []
            lh_all = []
            if len(self.allLines[self.lineNumber]) == 0:
                rh_all.append((self.highestMeasureNumberLength - len(measureNumber)) * symbols['space'])
                rh_all.append(measureNumber)
                lh_all.append(symbols['space'] * self.highestMeasureNumberLength)
                self.linePos = self.highestMeasureNumberLength
                isFirstOfLine = True
            if self.linePos + len(rh_braille) + 1 > self.maxLineLength or self.linePos + len(lh_braille) + 1 > self.maxLineLength:
                rh_all.append((self.highestMeasureNumberLength - len(measureNumber)) * symbols['space'])
                self.fillLine(self.lineNumber)
                self.fillLine(self.lineNumber + 1)
                self.lineNumber += 2
                rh_all.append(measureNumber)
                lh_all.append(symbols['space'] * self.highestMeasureNumberLength)
                self.linePos = self.highestMeasureNumberLength
                isFirstOfLine = True
            rh_all.append(symbols['space'])
            lh_all.append(symbols['space'])
            rh_length = len(rh_braille)
            lh_length = len(lh_braille)
            if isFirstOfLine:
                rh_all.append(symbols['rh_keyboard'])
                lh_all.append(symbols['lh_keyboard'])
                rh_length += 2
                lh_length += 2
                for dots in binary_dots[rh_braille[0]]:
                    if (dots == '10' or dots == '11'):
                        rh_all.append(symbols['dot'])
                        rh_length += 1
                for dots in binary_dots[lh_braille[0]]:
                    if (dots == '10' or dots == '11'):
                        lh_all.append(symbols['dot'])
                        lh_length += 1
            if rh_length > lh_length:
                rh_all.append(rh_braille)
                lh_all.append(lh_braille)
                #if not(rh_length - lh_length > 6):
                lh_all.append(symbols['space'] * (rh_length - lh_length))
                #else:
                #    lh_all.append(symbols['space'])
                #    lh_all.append(symbols['dot'] * (rh_length - lh_length - 1)) # tracker dots
                self.linePos += rh_length + 1
            else:
                lh_all.append(lh_braille)
                rh_all.append(rh_braille)
                #if not(lh_length - rh_length > 6):
                rh_all.append(symbols['space'] * (lh_length - rh_length))
                #else:
                #    rh_all.append(symbols['space'])
                #    rh_all.append(symbols['dot'] * (lh_length - rh_length - 1)) # tracker dots
                self.linePos += lh_length + 1
            self.allLines[self.lineNumber] += u"".join(rh_all)
            self.allLines[self.lineNumber + 1] += u"".join(lh_all)
            return
        raise BrailleTextException("Invalid Keyword.")
    
    def recenterHeading(self):
        '''
        Temporary method which manually recenters the heading if the melody is too short for a complete line.
        '''
        lineToCenter = self.allLines[1]
        lineToCenter = lineToCenter.strip(symbols['space'])
        nextLine = self.allLines[2]
        self.allLines[2] = nextLine.strip(symbols['space'])
        nextLineLength = len(self.allLines[2])
        self.allLines[1] = lineToCenter.center(nextLineLength, symbols['space'])

    def fillLine(self, lineNumberToFill):
        self.allLines[lineNumberToFill] += u"".join(symbols['space'] * (self.maxLineLength - self.linePos))

    def __str__(self):
        return u"\n".join([j for (i, j) in sorted(self.allLines.items())])
        

class BrailleTextException(music21.Music21Exception):
    pass
