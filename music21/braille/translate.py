# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         translate.py
# Purpose:      music21 class which allows transcription of music21 data to braille
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

"""
Objects for exporting music21 data as braille.
"""

import itertools
import music21
import unittest

from music21 import metadata
from music21 import stream
from music21 import tinyNotation

from music21.braille import segment

#-------------------------------------------------------------------------------
# music21 streams to BrailleText objects.

def objectToBraille(music21Obj, debug=False, **keywords):
    ur"""

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
    """
    if isinstance(music21Obj, stream.Stream):
        return streamToBraille(music21Obj, debug, **keywords)
    else:
        music21Measure = stream.Measure()
        music21Measure.append(music21Obj)
        return measureToBraille(music21Measure, debug, **keywords)

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
    if isinstance(music21Stream, stream.Score):
        allBrailleLines = []
        for music21Metadata in music21Stream.getElementsByClass(metadata.Metadata):
            if music21Metadata.title is not None:
                allBrailleLines.append(music21Metadata.title)
            if music21Metadata.composer is not None:
                allBrailleLines.append(music21Metadata.composer)
        for p in music21Stream.getElementsByClass(stream.Part):
            try:
                music21Part = p.makeNotation(cautionaryNotImmediateRepeat=False)
            except Exception as e:
                allBrailleLines.append("Make Notation bug / {0}".format(e))
                continue
            try:
                braillePart = partToBraille(music21Part, debug, **keywords)
                allBrailleLines.append(braillePart)
            except Exception as e:
                allBrailleLines.append("Transcription bug / {0}".format(e))
        return u"\n".join(allBrailleLines)
    if isinstance(music21Stream, stream.Opus):
        pass
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
    """
    Translates a stream Part consisting of two stream Parts, a right hand and left hand,
    into braille music bar over bar format.
    """
    rhSegments = segment.findSegments(music21PartStaffUpper, **keywords)
    lhSegments = segment.findSegments(music21PartStaffLower, **keywords)
    allBrailleText = []
    for (rhSegment, lhSegment) in itertools.izip(rhSegments, lhSegments):
        bg = segment.BrailleGrandSegment(rhSegment, lhSegment)
        if debug:
            print bg
        allBrailleText.append(bg.transcription)
    return u"\n".join([unicode(bt) for bt in allBrailleText])

#-------------------------------------------------------------------------------

class BrailleTranslateException(music21.Music21Exception):
    pass
    
#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof