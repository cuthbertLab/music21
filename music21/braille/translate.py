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

import itertools
import music21
import unittest

from music21 import stream

from music21.braille import basic
from music21.braille import text
from music21.braille import segment

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
        segmentTranscription = brailleElementSegment.transcribe()
        allTrans.append(str(segmentTranscription))
    return u"\n".join(allTrans)

def keyboardPartsToBraille(music21PartUpper, music21PartLower, **keywords):
    '''
    Translates a stream Part consisting of two stream Parts, a right hand and left hand,
    into braille music bar over bar format.
    '''
    maxLineLength = 40
    segmentBreaks = None
    if 'maxLineLength' in keywords:
        maxLineLength = keywords['maxLineLength']
    if 'segmentBreaks' in keywords:
        segmentBreaks = keywords['segmentBreaks']

    rhSegments = segment.findSegments(music21PartUpper, showHand = 'right',\
                                      maxLineLength = maxLineLength, segmentBreaks = segmentBreaks)
    lhSegments = segment.findSegments(music21PartLower, showHand = 'left',\
                                      maxLineLength = maxLineLength, segmentBreaks = segmentBreaks)
    allBrailleText = []
    for (rhSegment, lhSegment) in itertools.izip(rhSegments, lhSegments):
        bt = text.BrailleKeyboard(maxLineLength)
        try:
            brailleHeadingR = rhSegment.extractHeading()
            brailleHeadingL = lhSegment.extractHeading()
            bt.addElement(heading = brailleHeadingR)
            allGroupingKeysR = rhSegment.allGroupingKeys
            allGroupingKeysL = lhSegment.allGroupingKeys
        except basic.BrailleBasicException as bbe:
            if not bbe.args[0] == "No heading can be made.":
                raise bbe
            allGroupingKeysR = sorted(rhSegment.keys())
            allGroupingKeysL = sorted(lhSegment.keys())

        bt.highestMeasureNumberLength = len(str(allGroupingKeysR[-1] / 100))
        
        for (gkR, gkL) in itertools.izip(allGroupingKeysR, allGroupingKeysL):
            if gkR / 100 != gkL / 100 or gkR % 10 < 8 or gkL % 10 < 8:
                print "Cannot continue keyboard transcription: "
                print (gkR, gkL)
                return bt 
            currentMeasureNumber = basic.numberToBraille(gkR / 100, withNumberSign=False)
            if gkR % 10 == 8:
                inaccords = rhSegment[gkR]
                rh_braille = basic.symbols['full_inaccord'].join([segment.transcribeVoice(vc) for vc in inaccords])
            else:
                rh_braille = segment.transcribeNoteGrouping(rhSegment[gkR])
            if gkL % 10 == 8:
                inaccords = lhSegment[gkL]
                lh_braille = basic.symbols['full_inaccord'].join([segment.transcribeVoice(vc) for vc in inaccords])
            else:
                lh_braille = segment.transcribeNoteGrouping(lhSegment[gkL])
            bt.addNoteGroupings(currentMeasureNumber, lh_braille, rh_braille)
        bt.makeNewLine()
        allBrailleText.append(bt)
        
    return u"\n".join([str(bt) for bt in allBrailleText])

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