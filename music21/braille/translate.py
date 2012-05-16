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

from music21 import metadata, stream, tinyNotation
from music21.braille import segment
import itertools
import music21
import unittest

#-------------------------------------------------------------------------------

"""
inPlace
debug

findSegments:
slurLongPhraseWithBrackets 
showShortSlursAndTiesTogether
showLongSlursAndTiesTogether
segmentBreaks

groupingAttributes:
showClefSigns
upperFirstInNoteFingering
descendingChords

segmentAttributes:
cancelOutgoingKeySig
dummyRestLength
maxLineLength
showFirstMeasureNumber
showHand
showHeading
suppressOctaveMarks
"""



def objectToBraille(music21Obj, debug=False, **keywords):
    ur"""
    
    Translates an arbitrary object to braille.

    >>> from music21.braille import translate
    >>> from music21 import tinyNotation
    >>> samplePart = tinyNotation.TinyNotationStream("C4 D16 E F G# r4 e2.", "3/4")
    >>> print translate.objectToBraille(samplePart)    
    ⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠸⠹⠵⠋⠛⠩⠓⠧⠀⠐⠏⠄⠣⠅


    For normal users, you'll just call this, which starts a text editor:


    >>> #_DOCS_SHOW samplePart.show('braille')
    ⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠸⠹⠵⠋⠛⠩⠓⠧⠀⠐⠏⠄⠣⠅


    Other examples:


    >>> from music21 import note
    >>> sampleNote = note.Note("C3")
    >>> print translate.objectToBraille(sampleNote)
    ⠸⠹
    >>> #_DOCS_SHOW sampleNote.show('braille')
    ⠸⠹
    
    >>> from music21 import dynamics
    >>> sampleDynamic = dynamics.Dynamic("fff")
    >>> print translate.objectToBraille(sampleDynamic)
    ⠜⠋⠋⠋
    >>> #_DOCS_SHOW sampleDynamic.show('braille')
    ⠜⠋⠋⠋
    """
    if isinstance(music21Obj, stream.Stream):
        return streamToBraille(music21Obj, inPlace=False, debug=debug, **keywords)
    else:
        music21Measure = stream.Measure()
        music21Measure.append(music21Obj)
        return measureToBraille(music21Measure, inPlace=True, debug=debug, **keywords)

def streamToBraille(music21Stream, inPlace=False, debug=False, **keywords):
    """
    Translates a :class:`~music21.stream.Stream` to braille.
    
    
    If inPlace is False, then :meth:`~music21.stream.Stream.makeNotation` is called
    on all :class:`~music21.stream.Measure`, :class:`~music21.stream.Part`, and 
    :class:`~music21.stream.PartStaff` instances. Copies of those objects are then
    used to transcribe the music. 
    

    In inPlace is True, the transcription is done "as is," useful for strict transcription
    because sometimes :meth:`~music21.stream.Stream.makeNotation` introduces some unwanted
    artifacts in the music.
    
    
    Explain debug argument here.
    """
    if isinstance(music21Stream, stream.Part) or isinstance(music21Stream, tinyNotation.TinyNotationStream):
        return partToBraille(music21Stream, inPlace=inPlace, debug=debug, **keywords)
    if isinstance(music21Stream, stream.Measure):
        return measureToBraille(music21Stream, inPlace=inPlace, debug=debug, **keywords)
    keyboardParts = music21Stream.getElementsByClass(stream.PartStaff)
    if len(keyboardParts) == 2:
        return keyboardPartsToBraille(keyboardParts[0], keyboardParts[1], inPlace=inPlace, debug=debug, **keywords)
    if isinstance(music21Stream, stream.Score):
        return scoreToBraille(music21Stream, inPlace=inPlace, debug=debug, **keywords)
    if isinstance(music21Stream, stream.Opus):
        return opusToBraille(music21Stream, inPlace=inPlace, debug=debug, **keywords)
    raise BrailleTranslateException("Stream cannot be translated to Braille.")
    
def scoreToBraille(music21Score, inPlace=False, debug=False, **keywords):
    """
    Translates a :class:`~music21.stream.Score` to braille.
    
    See :meth:`~music21.braille.translate.streamToBraille` for an explanation of
    the inPlace and debug keywords.
    
    
    """
    allBrailleLines = []
    for music21Metadata in music21Score.getElementsByClass(metadata.Metadata):
        if music21Metadata.title is not None:
            allBrailleLines.append(unicode(music21Metadata.title, "utf-8"))
        if music21Metadata.composer is not None:
            allBrailleLines.append(unicode(music21Metadata.composer, "utf-8"))
    for p in music21Score.getElementsByClass(stream.Part):
        braillePart = partToBraille(p, inPlace=inPlace, debug=debug, **keywords)
        allBrailleLines.append(braillePart)            
    return u"\n".join(allBrailleLines)

def metadataToString(music21Metadata):
    allBrailleLines = []
    if music21Metadata.title is not None:
        allBrailleLines.append(unicode("Title: " + music21Metadata.title, "utf-8"))
    if music21Metadata.composer is not None:
        allBrailleLines.append(unicode("Composer: " + music21Metadata.composer, "utf-8"))
        
    return u"\n".join(allBrailleLines)

def opusToBraille(music21Opus, inPlace=False, debug=False, **keywords):
    """
    Translates an :class:`~music21.stream.Opus` to braille.
    
    See :meth:`~music21.braille.translate.streamToBraille` for an explanation of
    the inPlace and debug keywords.

    """
    raise BrailleTranslateException("Cannot translate Opus to braille.")
    
def measureToBraille(music21Measure, inPlace=False, debug=False, **keywords):
    """
    Translates a :class:`~music21.stream.Measure` to braille.
    
    See :meth:`~music21.braille.translate.streamToBraille` for an explanation of
    the inPlace and debug keywords.
    
    >>> from music21.braille import translate
    """
    
    if not 'showHeading' in keywords:
        keywords['showHeading'] = False
    if not 'showFirstMeasureNumber' in keywords:
        keywords['showFirstMeasureNumber'] = False
    measureToTranscribe = music21Measure
    if not inPlace:
        measureToTranscribe = music21Measure.makeNotation(cautionaryNotImmediateRepeat=False)
    music21Part = stream.Part()
    music21Part.append(measureToTranscribe)
    return partToBraille(music21Part, inPlace=True, debug = debug, **keywords)

def partToBraille(music21Part, inPlace=False, debug=False, **keywords):
    """
    Translates a :class:`~music21.stream.Part` to braille.
    
    See :meth:`~music21.braille.translate.streamToBraille` for an explanation of
    the inPlace and debug keywords.

    """
    partToTranscribe = music21Part
    if not inPlace:
        partToTranscribe = music21Part.makeNotation(cautionaryNotImmediateRepeat=False)
    allSegments = segment.findSegments(partToTranscribe, **keywords)
    allBrailleText = []
    for brailleSegment in allSegments:
        allBrailleText.append(brailleSegment.transcribe())
        if debug:
            print brailleSegment
    return u"\n".join([unicode(bt) for bt in allBrailleText])
    
def keyboardPartsToBraille(music21PartStaffUpper, music21PartStaffLower, inPlace=False, debug=False, **keywords):
    """
    Translates two :class:`~music21.stream.Part` instances to braille, an upper part and a lower
    part. Assumes that the two parts are aligned and well constructed. Bar over bar format is used.
    
    See :meth:`~music21.braille.translate.streamToBraille` for an explanation of
    the inPlace and debug keywords.

    """
    upperPartToTranscribe = music21PartStaffUpper
    if not inPlace:
        upperPartToTranscribe = music21PartStaffUpper.makeNotation(cautionaryNotImmediateRepeat=False)
    lowerPartToTranscribe = music21PartStaffLower
    if not inPlace:
        lowerPartToTranscribe = music21PartStaffLower.makeNotation(cautionaryNotImmediateRepeat=False)
    rhSegments = segment.findSegments(upperPartToTranscribe, **keywords)
    lhSegments = segment.findSegments(lowerPartToTranscribe, **keywords)
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