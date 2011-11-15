# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         translate.py
# Purpose:      music21 class which allows transcription of music21 data to braille
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''
Objects for exporting music21 data as braille.
'''

import music21
import unittest

from music21 import stream

from music21.braille import basic
from music21.braille import lookup
from music21.braille import text
from music21.braille import segment

symbols = lookup.symbols
#-------------------------------------------------------------------------------
# music21 streams to BrailleText objects.

def measureToBraille(music21Measure, **measureKeywords):
    if not 'showHeading' in measureKeywords:
        measureKeywords['showHeading'] = False
    if not 'showFirstMeasureNumber' in measureKeywords:
        measureKeywords['showFirstMeasureNumber'] = False
        
    music21Part = stream.Part()
    music21Part.append(music21Measure)
    return partToBraille(music21Part, **measureKeywords)

def partToBraille(music21Part, **partKeywords):
    allSegments = segment.findSegments(music21Part, **partKeywords)
    allTrans = []
    for brailleElementSegment in allSegments:
        segmentTranscription = segment.transcribeSegment(brailleElementSegment, **partKeywords)
        allTrans.append(str(segmentTranscription))
    return u"\n".join(allTrans)

def keyboardPartsToBraille(music21PartUpper, music21PartLower, **keywords):
    '''
    Translates a stream Part consisting of two stream Parts, a right hand and left hand,
    into braille music bar over bar format.
    '''
    maxLineLength = 40
    if 'maxLineLength' in keywords:
        maxLineLength = keywords['maxLineLength']

    bt = text.BrailleKeyboard(maxLineLength)
    rhSegment = segment.findSegments(music21PartUpper, showHand = 'right')[0]
    lhSegment = segment.findSegments(music21PartLower, showHand = 'left')[0]
    
    try:
        brailleHeadingR = segment.extractHeading(rhSegment, maxLineLength)
        brailleHeadingL = segment.extractHeading(lhSegment, maxLineLength)
        bt.addElement(heading = brailleHeadingR)
    except segment.BrailleSegmentException:
        pass

    allGroupingKeysR = sorted(rhSegment.keys())
    allGroupingKeysL = sorted(lhSegment.keys())

    bt.highestMeasureNumberLength = len(str(allGroupingKeysR[-1] / 100))
    
    rhNoteGroupings = segment.extractNoteGroupings(rhSegment)
    lhNoteGroupings = segment.extractNoteGroupings(lhSegment)
    
    while True:
        try:
            (gkR, noteGroupingR) = rhNoteGroupings.pop(0)
            (gkL, noteGroupingL) = lhNoteGroupings.pop(0)
            rh_braille = segment.transcribeNoteGrouping(noteGroupingR)
            lh_braille = segment.transcribeNoteGrouping(noteGroupingL)
            bt.addElement(pair = (basic.numberToBraille(gkR / 100)[1:], rh_braille, lh_braille))
        except:
            break

    return bt

#-------------------------------------------------------------------------------

class BrailleTranslateException(music21.Music21Exception):
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