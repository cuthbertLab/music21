# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         translate.py
# Purpose:      music21 class which allows transcription of music21 data to braille
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    Copyright © 2012 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
Methods for exporting music21 data as braille.

This module was made in consultation with the manual "Introduction to Braille
Music Transcription, Second Edition" by Mary Turner De Garmo, 2005. It is
available from the Library of Congress `here <http://www.loc.gov/nls/music/>`_,
and will henceforth be referred to as BMTM.


The most important method, and the only one that is needed to translate music
into braille, is :meth:`~music21.braille.translate.objectToBraille`. This method,
as well as the others, accept keyword arguments that serve to modify the output.
If no keyword arguments are needed, then using the method is equivalent to
calling :meth:`~music21.base.Music21Object.show` on the music.


Keywords:


* **inPlace** (False): If False, then :meth:`~music21.stream.Stream.makeNotation` is called
  on all :class:`~music21.stream.Measure`, :class:`~music21.stream.Part`, and
  :class:`~music21.stream.PartStaff` instances. Copies of those objects are then
  used to transcribe the music. If True, the transcription is done "as is."
  This is useful for strict transcription because
  sometimes :meth:`~music21.stream.Stream.makeNotation`
  introduces some unwanted artifacts in the music. However, the music needs
  to be organized into measures for transcription to work.
* **debug** (False): If True, a braille-english representation of the music is returned. Useful
  for knowing how the music was interpreted by the braille transcriber.


The rest of the keywords are segment keywords. A segment is "a group of measures occupying
more than one braille line." Music is divided into segments so as to "present the music to
the reader in a meaningful manner and to give him convenient reference points to use in
memorization" (BMTM, 71). Some of these keywords are changed automatically in context.

* **cancelOutgoingKeySig** (True): If True, whenever a key signature change is
    encountered, the new signature should be preceded by the old one.
* **descendingChords** (True): If True, then chords are spelled around the highest note.
    If False, then chords are spelled around the lowest note. This keyword is
    overridden by any valid clefs present in the music.
* **dummyRestLength** (None) For a given positive integer n, adds n "dummy rests"
    near the beginning of a segment. Designed for test purposes, as the rests
    are used to demonstrate measure division at the end of braille lines.
* **maxLineLength** (40): The maximum amount of braille characters
    that should be present in a line of braille.
* **segmentBreaks** ([]): A list consisting of (measure number, offset start)
    tuples indicating where the music should be broken into segments.
* **showClefSigns** (False): If True, then clef signs are displayed.
    Since braille does not use clefs or staves to represent music, they would
    instead be shown for referential or historical purposes.
* **showFirstMeasureNumber** (True): If True, then a measure number is shown
    following the heading (if applicable) and preceding the music.
* **showHand** (None): If set to "right" or "left", the corresponding
    hand sign is shown before the music. In keyboard music,
    the hand signs are shown automatically.
* **showHeading** (True): If True, then a braille heading is created above
    the initial segment. A heading consists
    of an initial :class:`~music21.key.KeySignature`, :class:`~music21.meter.TimeSignature`,
    :class:`~music21.tempo.TempoText`, and :class:`~music21.tempo.MetronomeMark`,
    or any subset thereof. The heading
    is centered above the music automatically.
* **showLongSlursAndTiesTogether** (False), **showShortSlursAndTiesTogether** (False):
    If False, then the slur on either side of the phrase is reduced by the amount
    that ties are present. If True, then slurs and ties are shown together
    (i.e. the note can have both a slur and a tie).
* **slurLongPhraseWithBrackets** (True): If True, then the slur of a
    long phrase (4+ consecutive notes) is brailled using the bracket slur.
    If False, the double slur is used instead.
* **suppressOctaveMarks** (True): If True, then all octave marks are suppressed.
    Designed for test purposes, as octave marks were not presented in BMTM until Chapter 7.
* **upperFirstInNoteFingering** (True): If True, then whenever
    there is a choice fingering (i.e. 5|4), the upper
    number is transcribed before the lower number. If False, the reverse is the case.
'''
import re
import unittest


from music21 import exceptions21
from music21 import metadata
from music21 import stream

from music21.braille.basic import wordToBraille
from music21.braille.lookup import alphabet
from music21.braille import segment


# -----------------------------------------------------------------------------

def objectToBraille(music21Obj, **keywords):
    '''
    Translates an arbitrary object to braille.

    >>> from music21.braille import translate
    >>> samplePart = converter.parse('tinynotation: 3/4 C4 D16 E F G# r4 e2.')
    >>> #_DOCS_SHOW samplePart.show()


        .. image:: images/objectToBraille.*
            :width: 700


    >>> print(translate.objectToBraille(samplePart))
    ⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠸⠹⠵⠋⠛⠩⠓⠧⠀⠐⠏⠄⠣⠅


    For normal users, you'll just call this, which starts a text editor:


    >>> #_DOCS_SHOW samplePart.show('braille')
    ⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠸⠹⠵⠋⠛⠩⠓⠧⠀⠐⠏⠄⠣⠅


    Other examples:


    >>> sampleNote = note.Note('C3')
    >>> print(translate.objectToBraille(sampleNote))
    ⠸⠹

    >>> sampleDynamic = dynamics.Dynamic('fff')
    >>> print(translate.objectToBraille(sampleDynamic))
    ⠜⠋⠋⠋
    '''
    if isinstance(music21Obj, stream.Stream):
        return streamToBraille(music21Obj, **keywords)
    else:
        music21Measure = stream.Measure()
        music21Measure.append(music21Obj)
        keywords['inPlace'] = True
        return measureToBraille(music21Measure, **keywords)


def streamToBraille(music21Stream, **keywords):
    '''
    Translates a :class:`~music21.stream.Stream` to braille.
    '''
    if isinstance(music21Stream, stream.Part):
        return partToBraille(music21Stream, **keywords)
    elif isinstance(music21Stream, stream.Measure):
        return measureToBraille(music21Stream, **keywords)
    keyboardParts = music21Stream.getElementsByClass(stream.PartStaff)
    if len(keyboardParts) == 2:
        return keyboardPartsToBraille(music21Stream, **keywords)
    elif isinstance(music21Stream, stream.Score):
        return scoreToBraille(music21Stream, **keywords)
    elif isinstance(music21Stream, stream.Opus):
        return opusToBraille(music21Stream, **keywords)
    raise BrailleTranslateException('Stream cannot be translated to Braille.')


def scoreToBraille(music21Score, **keywords):
    '''
    Translates a :class:`~music21.stream.Score` to braille.
    '''
    allBrailleLines = []
    for music21Metadata in music21Score.getElementsByClass(metadata.Metadata):
        allBrailleLines.append(metadataToString(music21Metadata, returnBrailleUnicode=True))
    for p in music21Score.getElementsByClass(stream.Part):
        braillePart = partToBraille(p, **keywords)
        allBrailleLines.append(braillePart)
    return '\n'.join(allBrailleLines)


def metadataToString(music21Metadata, returnBrailleUnicode=False):
    '''
    >>> from music21.braille import translate
    >>> corelli = corpus.parse('monteverdi/madrigal.3.1.rntxt')
    >>> mdObject = corelli.getElementsByClass('Metadata')[0]
    >>> mdObject.__class__
    <class 'music21.metadata.Metadata'>
    >>> print(translate.metadataToString(mdObject))
    Alternative Title: 3.1
    Title: La Giovinetta Pianta

    >>> print(translate.metadataToString(mdObject, returnBrailleUnicode=True))
    ⠠⠁⠇⠞⠑⠗⠝⠁⠞⠊⠧⠑⠀⠠⠞⠊⠞⠇⠑⠒⠀⠼⠉⠲⠁
    ⠠⠞⠊⠞⠇⠑⠒⠀⠠⠇⠁⠀⠠⠛⠊⠕⠧⠊⠝⠑⠞⠞⠁⠀⠠⠏⠊⠁⠝⠞⠁
    '''
    allBrailleLines = []
    for key in music21Metadata._workIds:
        value = music21Metadata._workIds[key]
        if value is not None:
            n = ' '.join(re.findall(r'([A-Z]*[a-z]+)', key))
            outString = f'{n.title()}: {value}'
            if returnBrailleUnicode:
                outTemp = []
                for word in outString.split():
                    outTemp.append(wordToBraille(word))
                outString = alphabet[' '].join(outTemp)
            allBrailleLines.append(outString)
    return '\n'.join(sorted(allBrailleLines))


def opusToBraille(music21Opus, **keywords):
    '''
    Translates an :class:`~music21.stream.Opus` to braille.
    '''
    allBrailleLines = []
    for score in music21Opus.getElementsByClass(stream.Score):
        allBrailleLines.append(scoreToBraille(score, **keywords))
    return '\n\n'.join(allBrailleLines)


def measureToBraille(music21Measure, **keywords):
    '''
    Translates a :class:`~music21.stream.Measure` to braille.

    >>> p = stream.Part()
    >>> p.append(note.Note('C4', type='whole'))
    >>> p.makeMeasures(inPlace=True)
    >>> p.show('t')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.note.Note C>
        {4.0} <music21.bar.Barline type=final>
    >>> print(braille.translate.objectToBraille(p))
    ⠀⠀⠼⠙⠲⠀⠀
    ⠼⠁⠀⠐⠽⠣⠅
    >>> print(braille.translate.measureToBraille(p.measure(1)))
    ⠼⠙⠲⠀⠐⠽⠣⠅

    '''
    (inPlace, unused_debug) = _translateArgs(**keywords)
    if 'showHeading' not in keywords:
        keywords['showHeading'] = False
    if 'showFirstMeasureNumber' not in keywords:
        keywords['showFirstMeasureNumber'] = False
    measureToTranscribe = music21Measure
    if not inPlace:
        measureToTranscribe = music21Measure.makeNotation(cautionaryNotImmediateRepeat=False)
    music21Part = stream.Part()
    music21Part.append(measureToTranscribe)
    keywords['inPlace'] = True
    return partToBraille(music21Part, **keywords)


def partToBraille(music21Part, **keywords):
    '''
    Translates a :class:`~music21.stream.Part` to braille.

    This is one of two (w/ keyboardPartsToBraille) main routines.  Runs segment.findSegments
    and then for each segment runs transcribe on it.
    '''
    (inPlace, debug) = _translateArgs(**keywords)
    partToTranscribe = music21Part
    if not inPlace:
        partToTranscribe = music21Part.makeNotation(cautionaryNotImmediateRepeat=False)
    allSegments = segment.findSegments(partToTranscribe, **keywords)
    allBrailleText = []
    for brailleSegment in allSegments:
        transcription = brailleSegment.transcribe()

        if not debug:
            allBrailleText.append(transcription)
        else:
            allBrailleText.append(str(brailleSegment))

    from music21.braille.basic import beamStatus
    for x in list(beamStatus):  # coerce to list first so that dictionary does not change size
        del beamStatus[x]      # while iterating.

    return '\n'.join([str(bt) for bt in allBrailleText])


def keyboardPartsToBraille(keyboardScore, **keywords):
    '''
    Translates a Score object containing two :class:`~music21.stream.Part` instances to braille,
    an upper part and a lower
    part. Assumes that the two parts are aligned and well constructed. Bar over bar format is used.
    '''
    parts = keyboardScore.getElementsByClass(['Part', 'PartStaff'])
    if len(parts) != 2:
        raise BrailleTranslateException('Can only translate two keyboard parts at a time')
    (inPlace, debug) = _translateArgs(**keywords)
    staffUpper = parts[0]
    staffLower = parts[1]
    upperPartToTranscribe = staffUpper
    if not inPlace:
        upperPartToTranscribe = staffUpper.makeNotation(cautionaryNotImmediateRepeat=False)
    lowerPartToTranscribe = staffLower
    if not inPlace:
        lowerPartToTranscribe = staffLower.makeNotation(cautionaryNotImmediateRepeat=False)
    rhSegments = segment.findSegments(upperPartToTranscribe, setHand='right', **keywords)
    lhSegments = segment.findSegments(lowerPartToTranscribe, setHand='left', **keywords)

    allBrailleText = []
    for (rhSegment, lhSegment) in zip(rhSegments, lhSegments):
        bg = segment.BrailleGrandSegment()
        for rhGroupingKey in rhSegment:
            # print(type(rhSegment), type(rhSegment[rhGroupingKey]))
            # breakpoint()
            bg[rhGroupingKey] = rhSegment[rhGroupingKey]

        for lhGroupingKey in lhSegment:
            bg[lhGroupingKey] = lhSegment[lhGroupingKey]

        bg.transcribe()
        if not debug:
            allBrailleText.append(bg.brailleText)
        else:
            allBrailleText.append(str(bg))

    return '\n'.join([str(bt) for bt in allBrailleText])


def _translateArgs(**keywords):
    '''
    Returns a tuple of inPlace (default False) and debug (default False)
    from a set of keywords:

    >>> braille.translate._translateArgs()
    (False, False)
    >>> braille.translate._translateArgs(debug=True)
    (False, True)
    >>> braille.translate._translateArgs(inPlace=True)
    (True, False)
    >>> braille.translate._translateArgs(inPlace=True, debug=True)
    (True, True)
    '''
    inPlace = keywords.get('inPlace', False)
    debug = keywords.get('debug', False)
    return (inPlace, debug)


_DOC_ORDER = [objectToBraille]

# -----------------------------------------------------------------------------


class BrailleTranslateException(exceptions21.Music21Exception):
    pass


# -----------------------------------------------------------------------------


class Test(unittest.TestCase):

    def x_testTranslateRespectsLineLength(self):
        # does not yet work.
        from music21 import converter
        s = converter.parse('tinyNotation: 2/4 c4 d e f8 g a2 B2 c4. d8 e2')
        x = objectToBraille(s, maxLineLength=10)
        for line in x:
            self.assertLessEqual(len(line), 10)


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)

