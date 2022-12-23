# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         analysis/elements.py
# Purpose:      Tools for analyzing general elements
#
# Authors:      Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2017-22 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
from __future__ import annotations

import collections
import typing as t

def attributeCount(streamOrStreamIter, attrName='quarterLength') -> collections.Counter[t.Any]:
    '''
    Return a collections.Counter of attribute usage for elements in a stream
    or StreamIterator

    >>> bach = corpus.parse('bach/bwv324.xml')
    >>> bachIter = bach.parts[0].recurse().getElementsByClass(note.Note)
    >>> qlCount = analysis.elements.attributeCount(bachIter, 'quarterLength')
    >>> qlCount.most_common(3)
    [(1.0, 12), (2.0, 11), (4.0, 2)]

    * Changed in v4: Returns a collections.Counter object.
    '''
    post: collections.Counter[t.Any] = collections.Counter()
    for e in streamOrStreamIter:
        if hasattr(e, attrName):
            k = getattr(e, attrName)
            post[k] += 1
    return post


if __name__ == '__main__':
    import music21
    music21.mainTest()
