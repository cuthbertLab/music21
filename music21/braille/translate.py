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
from music21 import tinyNotation

from music21.braille import segment

#-------------------------------------------------------------------------------
# music21 streams to BrailleText objects.

def objectToBraille(music21Obj, debug=False, **keywords):
    '''
    Translates an arbitrary object to Braille.  Doesn't yet work on notes:
    
    >>> from music21 import *

    >>> tns = tinyNotation.TinyNotationStream('C4 D16 E F G# r4 e2.', '3/4')    
    >>> x = braille.translate.objectToBraille(tns)
    >>> print x
    ⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠸⠹⠵⠋⠛⠩⠓⠧⠀⠐⠏⠄⠣⠅

    For normal users, you'll just call this, which starts a text editor:


    >>> #_DOCS_SHOW tns.show('braille')
    
    ⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠸⠹⠵⠋⠛⠩⠓⠧⠀⠐⠏⠄⠣⠅
    '''
    if isinstance(music21Obj, stream.Stream):
        return streamToBraille(music21Obj, debug, **keywords)
    else:
        m = stream.Measure()
        m.insert(0, music21Obj)
        return measureToBraille(music21Obj, debug, **keywords)

def streamToBraille(music21Stream, debug=False, **keywords):
    if isinstance(music21Stream, stream.Part) or isinstance(music21Stream, tinyNotation.TinyNotationStream):
        music21Part = music21Stream.makeNotation(cautionaryNotImmediateRepeat=False)
        return partToBraille(music21Part, debug=debug, **keywords)
    if isinstance(music21Stream, stream.Measure):
        music21Measure = music21Stream.makeNotation(cautionaryNotImmediateRepeat=False)
        return measureToBraille(music21Measure, debug=debug, **keywords)
    keyboardParts = music21Stream.getElementsByClass(stream.PartStaff)
    if len(keyboardParts) == 2:
        rightHand = keyboardParts[0].makeNotation(cautionaryNotImmediateRepeat=False)
        leftHand = keyboardParts[1].makeNotation(cautionaryNotImmediateRepeat=False)
        return keyboardPartsToBraille(rightHand, leftHand, debug=debug, **keywords)
    raise BrailleTranslateException("Cannot transcribe stream to braille")
    
def measureToBraille(music21Measure, debug=False, **keywords):
    if not 'showHeading' in keywords:
        keywords['showHeading'] = False
    if not 'showFirstMeasureNumber' in keywords:
        keywords['showFirstMeasureNumber'] = False
    music21Part = stream.Part()
    music21Part.append(music21Measure)
    return partToBraille(music21Part, debug = debug, **keywords)

def partToBraille(music21Part, debug = False, **keywords):
    allSegments = segment.findSegments(music21Part, **keywords)
    allBrailleText = []
    for brailleSegment in allSegments:
        allBrailleText.append(brailleSegment.transcribe())
        if debug:
            print brailleSegment
    return u"\n".join([unicode(bt) for bt in allBrailleText])
    
def keyboardPartsToBraille(music21PartStaffUpper, music21PartStaffLower, debug=False, **keywords):
    '''
    Translates a stream Part consisting of two stream Parts, a right hand and left hand,
    into braille music bar over bar format.
    '''
    rhSegments = segment.findSegments(music21PartStaffUpper, **keywords)
    lhSegments = segment.findSegments(music21PartStaffLower, **keywords)
    allBrailleText = []
    for (rhSegment, lhSegment) in itertools.izip(rhSegments, lhSegments):
        bg = segment.BrailleGrandSegment(rhSegment, lhSegment)
        if debug:
            print bg
        allBrailleText.append(bg.transcription)
    return u"\n\n".join([unicode(bt) for bt in allBrailleText])

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