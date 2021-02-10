# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         analysis/pitchAnalysis.py
# Purpose:      Tools for analyzing pitches
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2017 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
import collections

_MOD = 'analysis.pitchAnalysis'

def pitchAttributeCount(s, pitchAttr='name'):
    '''
    Return a collections.Counter of pitch class usage (count)
    by selecting an attribute of the Pitch object.

    Changed in 4.0: Returns a collections.Counter object.

    >>> bach = corpus.parse('bach/bwv324.xml')
    >>> pcCount = analysis.pitchAnalysis.pitchAttributeCount(bach, 'pitchClass')
    >>> for n in sorted(pcCount):
    ...     print("%2d: %2d" % (n, pcCount[n]))
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
    ...     print("%2s: %2d" % (n, nameCount[n]))
     D: 26
     A: 17
    F#: 15


    >>> nameOctaveCount = analysis.pitchAnalysis.pitchAttributeCount(bach, 'nameWithOctave')
    >>> for n in sorted(nameOctaveCount):
    ...     print("%3s: %2d" % (n, nameOctaveCount[n]))
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
