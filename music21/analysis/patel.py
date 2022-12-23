# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         patel.py
# Purpose:      Tools for testing Aniruddh D. Patel's analysis theories
#
# Authors:      Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2011 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
from __future__ import annotations

import math
import unittest

def nPVI(streamForAnalysis):
    '''
    Algorithm to give the normalized pairwise variability index
    (Low, Grabe, & Nolan, 2000) of the rhythm of a stream.


    Used by Aniruddh D. Patel to argue for national differences between musical
    themes.  First encountered it in a presentation by Patel, Chew, Francois,
    and Child at MIT.


    n.b. -- takes the distance between each element, including clefs, keys, etc.
    use .notesAndRests etc. to filter out elements that are not useful (though this will skip
    zero length objects)

    n.b.  -- duration is used rather than actual distance -- for gapless
    streams (the norm) these two measures will be identical.

    >>> s2 = converter.parse('tinynotation: 4/4 C4 D E F G').flatten().notesAndRests.stream()
    >>> analysis.patel.nPVI(s2)
    0.0

    >>> s3 = converter.parse('tinynotation: 4/4 C4 D8 C4 D8 C4').flatten().notesAndRests.stream()
    >>> analysis.patel.nPVI(s3)
    66.6666...

    >>> s4 = corpus.parse('bwv66.6').parts[0].flatten().notesAndRests.stream()
    >>> analysis.patel.nPVI(s4)
    12.96296...
    '''
    s = streamForAnalysis  # shorter
    totalElements = len(s)
    summation = 0
    prevQL = s[0].quarterLength
    for i in range(1, totalElements):
        thisQL = s[i].quarterLength
        if thisQL > 0 and prevQL > 0:
            summation += abs(thisQL - prevQL) / ((thisQL + prevQL) / 2.0)
        else:
            pass
        prevQL = thisQL

    final = summation * 100 / (totalElements - 1)
    return final

def melodicIntervalVariability(streamForAnalysis, **skipKeywords):
    '''
    Gives the Melodic Interval Variability (MIV) for a Stream,
    as defined by Aniruddh D. Patel in "Music, Language, and the Brain"
    p. 223, as 100 x the coefficient of variation (standard deviation/mean)
    of the interval size (measured in semitones) between consecutive elements.

    The multiplication by 100x exists to put it in the same range as nPVI.

    Keywords are passed on to
    Stream.findConsecutiveNotes() via Stream.melodicIntervals for
    determining how to find consecutive intervals.

    >>> s2 = converter.parse('tinynotation: 4/4 C4 D E F# G#')[note.Note].stream()
    >>> analysis.patel.melodicIntervalVariability(s2)
    0.0
    >>> s3 = converter.parse('tinynotation: 4/4 C4 D E F G C')[note.Note].stream()
    >>> analysis.patel.melodicIntervalVariability(s3)
    85.266688...
    >>> s4 = corpus.parse('bwv66.6').parts[0][note.GeneralNote].stream()
    >>> analysis.patel.melodicIntervalVariability(s4)
    65.287...

    Too short streams raise a ValueError:

    >>> s5 = converter.parse('tinynotation: 4/4 C2 D2')[note.Note].stream()
    >>> analysis.patel.melodicIntervalVariability(s5)
    Traceback (most recent call last):
    ValueError: need at least three notes to have a std-deviation of intervals (and thus a MIV)

    * Changed in v9: ValueError rather than a Music21Exception raised.
    '''
    s = streamForAnalysis  # shorter
    intervalStream = s.melodicIntervals(**skipKeywords)
    totalElements = len(intervalStream)
    if totalElements < 2:  # this is correct.
        raise ValueError('need at least three notes to have '
                             + 'a std-deviation of intervals (and thus a MIV)')
    # summation = 0
    semitoneList = [myInt.chromatic.undirected for myInt in intervalStream]
    mean = 0
    std = 0
    for a in semitoneList:
        mean = mean + a
    mean = mean / totalElements
    for a in semitoneList:
        std = std + (a - mean) ** 2
    std = math.sqrt(std / (totalElements - 1))
    return 100 * (std / mean)


class Test(unittest.TestCase):
    pass


# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [melodicIntervalVariability]

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)

