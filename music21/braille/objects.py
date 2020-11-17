# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         object.py
# Purpose:      music21 classes for indicating Braille formatting, etc.
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2016 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
import unittest

from music21.base import Music21Object


class BrailleTranscriptionHelper(Music21Object):
    '''
    represents an object that should not be transcribed into braille
    but can help with transcription.

    >>> bth = braille.objects.BrailleTranscriptionHelper()
    >>> bth
    <music21.braille.objects.BrailleTranscriptionHelper object at 0x10afc1a58>
    '''
    classSortOrder = -100


class BrailleSegmentDivision(BrailleTranscriptionHelper):
    '''
    Represents that a segment must divide at this point.

    >>> bsd = braille.objects.BrailleSegmentDivision()
    >>> bsd
    <music21.braille.objects.BrailleSegmentDivision object at 0x10afc1a58>
    '''


class BrailleOptionalSegmentDivision(BrailleSegmentDivision):
    '''
    Represents that a segment might divide at this point.

    >>> segmentDivision = braille.objects.BrailleOptionalSegmentDivision()
    >>> segmentDivision
    <music21.braille.objects.BrailleOptionalSegmentDivision object at 0x10afc1b38>
    '''


class BrailleOptionalNoteDivision(BrailleTranscriptionHelper):
    '''
    Represents the best place in a measure to divide notes
    if the measure needs to be divided.

    >>> bond = braille.objects.BrailleOptionalNoteDivision()
    >>> bond
    <music21.braille.objects.BrailleOptionalNoteDivision object at 0x10afc19b0>
    '''


class BrailleMusicComma(BrailleTranscriptionHelper):
    pass


class BrailleExplicitNoteLength(BrailleTranscriptionHelper):
    pass


class BrailleExplicitNoteLarger(BrailleExplicitNoteLength):
    pass


class BrailleExplicitNoteSmaller(BrailleExplicitNoteLength):
    pass


class BrailleExplicitNoteExtraSmaller(BrailleExplicitNoteLength):
    pass


# ------------------------------------------------------------------------------
class Test(unittest.TestCase):
    pass


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
