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
import typing as t

from music21 import clef
from music21 import environment
from music21 import key
from music21 import meter
from music21 import stream

if t.TYPE_CHECKING:
    from music21.base import Music21Object

environLocal = environment.Environment('stream.tools')


# ------------------------------------------------------------------------------

def removeDuplicates(thisStream: stream.Stream,
                     classesToRemove: tuple = (meter.TimeSignature, key.KeySignature, clef.Clef),
                     inPlace: bool = True
                     ) -> stream.Stream:
    '''
    The repetition of some classes like notes is common.
    By contrast, the explicit repetition of certain other objects like clefs
    usually indicates an error e.g., resulting from a copy'n'paste.
    This function serves to remove those that are likely in error and make no change.

    Use the `classesToRemove` argument to specify which music21 classes to check and remove.
    The classes currently supported are: time signatures, key signatures, and clefs.
    The `classesToRemove` argument defaults all three.
    Sometimes there are legitimate reasons to duplicate even these classes.
    In that case, override the default by specifying the list of which of the three of classes.
    More classes may be added, but for now they will simply raise a ValueError.

    So let's create an example part with an initial set of
    time signature, key signature, and clef.

    >>> p = stream.Part()
    >>> p.append(meter.TimeSignature('3/4'))  # first TS
    >>> p.append(key.KeySignature(6))  # first KS
    >>> p.append(clef.TrebleClef())  # first Clef

    Then a few notes, followed by a duplicates of the
    key signature, and clef.

    >>> p.append(note.Note('C'))
    >>> p.append(note.Note('C'))
    >>> p.append(note.Note('D'))

    >>> p.append(meter.TimeSignature('3/4'))  # duplicate
    >>> p.append(key.KeySignature(6))  # duplicate
    >>> p.append(clef.TrebleClef())  # duplicate

    Finally, a few more notes, followed by a
    change of time signature, key signature, and clef.

    >>> p.append(note.Note('E'))
    >>> p.append(note.Note('F'))
    >>> p.append(note.Note('G'))

    >>> p.append(meter.TimeSignature('2/4'))
    >>> p.append(key.KeySignature(-5))
    >>> p.append(clef.BassClef())

    >>> p.append(note.Note('A'))
    >>> p.append(note.Note('B'))
    >>> p.append(note.Note('C5'))

    Now we'll make it into a proper part with measures and see
    how it looks in its original, unaltered form:

    >>> p.makeMeasures(inPlace=True)
    >>> p.show('t')
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

    >>> testInPlace = stream.tools.removeDuplicates(p)
    >>> testInPlace.show('t')
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

    As the example shows, this function defaults to working on a stream inPlace.

    >>> testInPlace == p
    True

    To avoid this, set inPlace to False.

    >>> testNotInPlace = stream.tools.removeDuplicates(p, inPlace=False)
    >>> testNotInPlace == p
    False

    This function is primarily designed and intended for use on a stream.Part object.
    If called on a steam.Score, it will simply be applied to each of that score's parts in turn.

    >>> s = stream.Score()
    >>> s.append(p)
    >>> t = stream.tools.removeDuplicates(s, inPlace=False)
    >>> s.parts[0] == testInPlace
    True

    '''

    supportedClasses = (meter.TimeSignature, key.KeySignature, clef.Clef)

    removalDict: dict[stream.Stream, list[Music21Object]] = {}

    if not inPlace:
        thisStream = thisStream.coreCopyAsDerivation('removeDuplicates')

    if isinstance(thisStream, stream.Score):
        if len(thisStream.parts) > 0:
            for p in thisStream.parts:
                removeDuplicates(p, classesToRemove=classesToRemove, inPlace=True)

    for thisClass in classesToRemove:

        if not any(issubclass(thisClass, supportedClass) for supportedClass in supportedClasses):
            raise ValueError(f'Invalid class. Only {supportedClasses} are supported.')

        allStates = thisStream.recurse().getElementsByClass(thisClass)

        if len(allStates) < 2:  # Not used, or doesn't change
            continue

        currentState = allStates[0]  # First to initialize: can't be a duplicate
        for thisState in allStates[1:]:
            if thisState == currentState:
                if thisState.activeSite in removalDict:  # May be several in same (e.g., measure)
                    removalDict[thisState.activeSite].append(thisState)
                else:
                    removalDict[thisState.activeSite] = [thisState]
            else:
                currentState = thisState

    for activeSiteKey, valuesToRemove in removalDict.items():
        activeSiteKey.remove(valuesToRemove, recurse=True)

    return thisStream


# -----------------------------------------------------------------------------

if __name__ == '__main__':
    import music21
    music21.mainTest()
