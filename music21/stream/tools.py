# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         stream/tools.py
# Purpose:      Additional tools for working with streams
#
# Authors:      Mark Gotham
#
# Copyright:    Copyright © 2022 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------

from __future__ import annotations

from music21 import clef
from music21 import environment
from music21 import key
from music21 import meter
from music21 import stream

environLocal = environment.Environment('stream.tools')


# ------------------------------------------------------------------------------

def removeDuplicates(thisStream: stream.Stream,
                     classesToRemove: list | None = None,
                     ) -> stream.Stream:
    '''
    The repetition of some classes like notes is common.
    By contrast, the explicit repetition of certain other objects like clefs
    usually indicates an error e.g., resulting from a copy'n'paste.
    This function serves to remove those that are likely in error and make no change.

    Use the `classesToRemove` argument to specify which music21 classes to check and remove.
    The classes currently supported are: time signatures, key signatures, and clefs.
    The `classesToRemove` arument defaults all three.
    Sometimes there are legitimate reasons to duplicate even these classes.
    In that case, override the default by specifying the list of which of the three of classes.
    More classes may be added, but for now they will simply raise a ValueError.

    So let's create an example part with an initial set of
    time signature, key signature, and clef.

    >>> s = stream.Part()
    >>> s.append(meter.TimeSignature('3/4'))  # first TS
    >>> s.append(key.KeySignature(6))  # first KS
    >>> s.append(clef.TrebleClef())  # first Clef

    Then a few notes, followed by a duplicates of the
    key signature, and clef.

    >>> s.append(note.Note('C'))
    >>> s.append(note.Note('C'))
    >>> s.append(note.Note('D'))

    >>> s.append(meter.TimeSignature('3/4'))  # duplicate
    >>> s.append(key.KeySignature(6))  # duplicate
    >>> s.append(clef.TrebleClef())  # duplicate

    Finally, a few more notes, followed by a
    change of time signature, key signature, and clef.

    >>> s.append(note.Note('E'))
    >>> s.append(note.Note('F'))
    >>> s.append(note.Note('G'))

    >>> s.append(meter.TimeSignature('2/4'))
    >>> s.append(key.KeySignature(-5))
    >>> s.append(clef.BassClef())

    >>> s.append(note.Note('A'))
    >>> s.append(note.Note('B'))
    >>> s.append(note.Note('C5'))

    Now we'll make it into a proper part with measures and see
    how it looks in its original, unaltered form:

    >>> s = s.makeMeasures()
    >>> s.show('t')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.key.KeySignature of 6 sharps>
        {0.0} <music21.meter.TimeSignature 3/4>
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note C>
        {2.0} <music21.note.Note D>
    {3.0} <music21.stream.Measure 2 offset=3.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.key.KeySignature of 6 sharps>
        {0.0} <music21.meter.TimeSignature 3/4>
        {0.0} <music21.note.Note E>
        {1.0} <music21.note.Note F>
        {2.0} <music21.note.Note G>
    {6.0} <music21.stream.Measure 3 offset=6.0>
        {0.0} <music21.clef.BassClef>
        {0.0} <music21.key.KeySignature of 5 flats>
        {0.0} <music21.meter.TimeSignature 2/4>
        {0.0} <music21.note.Note A>
        {1.0} <music21.note.Note B>
    {8.0} <music21.stream.Measure 4 offset=8.0>
        {0.0} <music21.note.Note C>
        {1.0} <music21.bar.Barline type=final>

    Calling removeDuplicates should remove the duplicates
    even with those changes now stored within measures,
    not directly on the part.
    Specifically, in our example,
    the duplicates entries are removed from measure 2
    and the actual changes in measure 3 remain.

    >>> s = stream.tools.removeDuplicates(s)
    >>> s.show('t')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.key.KeySignature of 6 sharps>
        {0.0} <music21.meter.TimeSignature 3/4>
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note C>
        {2.0} <music21.note.Note D>
    {3.0} <music21.stream.Measure 2 offset=3.0>
        {0.0} <music21.note.Note E>
        {1.0} <music21.note.Note F>
        {2.0} <music21.note.Note G>
    {6.0} <music21.stream.Measure 3 offset=6.0>
        {0.0} <music21.clef.BassClef>
        {0.0} <music21.key.KeySignature of 5 flats>
        {0.0} <music21.meter.TimeSignature 2/4>
        {0.0} <music21.note.Note A>
        {1.0} <music21.note.Note B>
    {8.0} <music21.stream.Measure 4 offset=8.0>
        {0.0} <music21.note.Note C>
        {1.0} <music21.bar.Barline type=final>

    '''

    supportedClasses = [meter.TimeSignature, key.KeySignature, clef.Clef]
    if classesToRemove is None:
        classesToRemove = supportedClasses

    listOfObjectsToRemove = []

    for thisClass in classesToRemove:

        if not any(issubclass(thisClass, supportedClass) for supportedClass in supportedClasses):
            raise ValueError(f'Invalid class. Only {supportedClasses} are supported.')

        allStates = thisStream.recurse().getElementsByClass(thisClass)

        if len(allStates) < 2:  # Not used, or doesn't change
            continue

        currentState = allStates[0]  # First to initialize: can't be a duplicate
        for thisState in allStates[1:]:
            if thisState == currentState:
                listOfObjectsToRemove.append(thisState)
            else:
                currentState = thisState

    for item in listOfObjectsToRemove:
        m = item.getContextByClass(stream.Measure)
        m.remove(item, recurse=True)

    return thisStream


# -----------------------------------------------------------------------------

if __name__ == '__main__':
    import music21
    music21.mainTest()
