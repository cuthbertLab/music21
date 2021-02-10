# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         analysis/elements.py
# Purpose:      Tools for analyzing general elements
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2017 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
import collections

_MOD = 'analysis.elements'

def attributeCount(streamOrStreamIter, attrName='quarterLength') -> collections.Counter:
    '''
    Return a collections.Counter of attribute usage for elements in a stream
    or StreamIterator

    >>> from music21 import corpus
    >>> bach = corpus.parse('bach/bwv324.xml')
    >>> bachIter = bach.parts[0].recurse().getElementsByClass('Note')
    >>> qlCount = analysis.elements.attributeCount(bachIter, 'quarterLength')
    >>> qlCount.most_common(3)
    [(1.0, 12), (2.0, 11), (4.0, 2)]

    Changed in 4.0: Returns a collections.Counter object.
    '''
    post = collections.Counter()
    for e in streamOrStreamIter:
        if hasattr(e, attrName):
            k = getattr(e, attrName)
            post[k] += 1
    return post


if __name__ == '__main__':
    import music21
    music21.mainTest()
