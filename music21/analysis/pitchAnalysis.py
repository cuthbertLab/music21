# ------------------------------------------------------------------------------
# Name:         analysis/pitchAnalysis.py
# Purpose:      Tools for analyzing pitches
#
# Authors:      Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2017 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
from __future__ import annotations

import collections

def pitchAttributeCount(s, pitchAttr='name'):
    '''
    Return a collections.Counter of pitch class usage (count)
    by selecting an attribute of the Pitch object.

    * Changed in v4: Returns a collections.Counter object.

    >>> bach = corpus.parse('bach/bwv324.xml')
    >>> pcCount = analysis.pitchAnalysis.pitchAttributeCount(bach, 'pitchClass')
    >>> for n in sorted(pcCount):
    ...     print(f'{n:2d}: {pcCount[n]:2d}')
     0:  3
     2: 26
     3:  3
     4: 13
     6: 15
     7: 13
     9: 17
    11: 14


    List in most common order:

    >>> nameCount = analysis.pitchAnalysis.pitchAttributeCount(bach, 'name')
    >>> for n, count in nameCount.most_common(3):
    ...     print(f'{n:>2s}: {nameCount[n]:2d}')
     D: 26
     A: 17
    F#: 15


    >>> nameOctaveCount = analysis.pitchAnalysis.pitchAttributeCount(bach, 'nameWithOctave')
    >>> for n in sorted(nameOctaveCount):
    ...     print(f'{n:>3s}: {nameOctaveCount[n]:2d}')
     A2:  2
     A3:  5
     A4: 10
     B2:  3
     B3:  4
     B4:  7
     C3:  2
     C5:  1
    D#3:  1
    D#4:  2
    ...
    '''
    post = collections.Counter()
    for p in s.pitches:
        k = getattr(p, pitchAttr)
        post[k] += 1
    return post


if __name__ == '__main__':
    import music21
    music21.mainTest()
