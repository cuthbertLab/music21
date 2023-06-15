# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         streamStatus.py
# Purpose:      Functionality for reporting on the notational status of streams
#
# Authors:      Josiah Wolf Oberholtzer
#
# Copyright:    Copyright © 2013 Michael Scott Asato Cuthbert and the music21
#               Project
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
from __future__ import annotations

import unittest

from music21 import environment
from music21.common.misc import defaultDeepcopy
from music21.common.objects import SlottedObjectMixin

environLocal = environment.Environment(__file__)


# -----------------------------------------------------------------------------


class StreamStatus(SlottedObjectMixin):
    '''
    An object that stores the current notation state for the client stream.

    Separates out tasks such as whether notation has been made, etc.

    >>> s = stream.Stream()
    >>> ss = s.streamStatus
    >>> ss
    <music21.stream.streamStatus.StreamStatus object at 0x...>
    >>> s.streamStatus.client is s
    True

    Copying of StreamStatus and surrounding Streams

    >>> import copy
    >>> ss2 = copy.deepcopy(ss)
    >>> ss2.client is None
    True

    >>> s2 = copy.deepcopy(s)
    >>> s2.streamStatus
    <music21.stream.streamStatus.StreamStatus object at 0x...>
    >>> s2.streamStatus is ss
    False
    >>> s2.streamStatus.client is s2
    True
    '''

    # CLASS VARIABLES #

    __slots__ = (
        '_accidentals',
        '_beams',
        '_concertPitch',
        '_dirty',
        '_enharmonics',
        '_measures',
        '_ornaments',
        '_rests',
        '_ties',
        '_tuplets',
        'client',
    )

    # INITIALIZER #

    def __init__(self, client=None):
        self._accidentals = None
        self._beams = None
        self._concertPitch = None
        self._dirty = None
        self._enharmonics = None
        self._measures = None
        self._ornaments = None
        self._rests = None
        self._ties = None
        self._tuplets = None
        self.client = client

    # SPECIAL METHODS #

    def __deepcopy__(self, memo=None):
        '''
        Manage deepcopying by creating a new reference to the same object.
        leaving out the client
        '''
        return defaultDeepcopy(self, memo, ignoreAttributes={'client'})

    # PUBLIC METHODS #

    def haveAccidentalsBeenMade(self):
        '''
        If Accidentals.displayStatus is None for all contained pitches, it as
        assumed that accidentals have not been set for display and/or
        makeAccidentals has not been run. If any Accidental has displayStatus
        other than None, this method returns True, regardless of if
        makeAccidentals has actually been run.
        '''
        for p in self.client.pitches:
            if p.accidental is not None:
                if p.accidental.displayStatus is not None:
                    return True
        return False

    def haveBeamsBeenMade(self):
        '''
        If any Note in this Stream has .beams defined, it as assumed that Beams
        have not been set and/or makeBeams has not been run. If any Beams
        exist, this method returns True, regardless of if makeBeams has
        actually been run.
        '''
        for n in self.client.recurse(classFilter=('NotRest',), restoreActiveSites=False):
            if n.beams is not None and n.beams.beamsList:
                return True
        return False

    def haveTupletBracketsBeenMade(self):
        '''
        If any GeneralNote in this Stream is a tuplet, then check to
        see if any of them have a first Tuplet with type besides None
        return True. Otherwise, return False if there is a tuplet. Return None if
        no Tuplets.

        >>> s = stream.Stream()
        >>> s.streamStatus.haveTupletBracketsBeenMade() is None
        True
        >>> s.append(note.Note())
        >>> s.streamStatus.haveTupletBracketsBeenMade() is None
        True
        >>> nTuplet = note.Note(quarterLength=1/3)
        >>> s.append(nTuplet)
        >>> s.streamStatus.haveTupletBracketsBeenMade()
        False
        >>> nTuplet.duration.tuplets[0].type = 'start'
        >>> s.streamStatus.haveTupletBracketsBeenMade()
        True

        '''
        foundTuplet = False
        for n in self.client.recurse(classFilter='GeneralNote', restoreActiveSites=False):
            if n.duration.tuplets:
                foundTuplet = True
                if n.duration.tuplets[0].type is not None:
                    return True
        if foundTuplet:
            return False
        else:
            return None

    # PUBLIC PROPERTIES #

    @property
    def accidentals(self):
        if self._accidentals is None:
            self._accidentals = self.haveAccidentalsBeenMade()
        return self._accidentals

    @accidentals.setter
    def accidentals(self, expr):
        if expr is not None:
            self._accidentals = bool(expr)
        else:
            self._accidentals = None

    @property
    def beams(self):
        if self._beams is None:
            self._beams = self.haveBeamsBeenMade()
        return self._beams

    @beams.setter
    def beams(self, expr):
        if expr is not None:
            self._beams = bool(expr)
        else:
            self._beams = None

    @property
    def tuplets(self):
        if self._tuplets is None:
            self._tuplets = self.haveTupletBracketsBeenMade()
            # If there were no tuplet durations,
            # tuplet brackets don't need to be made.
            if self._tuplets is None:
                self._tuplets = True
        return self._tuplets

    @tuplets.setter
    def tuplets(self, expr):
        if expr is not None:
            self._tuplets = bool(expr)
        else:
            self._tuplets = None


# -----------------------------------------------------------------------------


class Test(unittest.TestCase):
    '''
    Note: most Stream tests are found in stream.tests
    '''

    def testHaveBeamsBeenMadeAfterDeepcopy(self):
        import copy
        from music21 import stream
        from music21 import note
        m = stream.Measure()
        c = note.Note('C4', type='quarter')
        m.append(c)
        d1 = note.Note('D4', type='eighth')
        d2 = note.Note('D4', type='eighth')
        m.append([d1, d2])
        e3 = note.Note('E4', type='eighth')
        e4 = note.Note('E4', type='eighth')
        m.append([e3, e4])
        d1.beams.append('start')
        d2.beams.append('stop')
        self.assertTrue(m.streamStatus.haveBeamsBeenMade())
        mm = copy.deepcopy(m)
        self.assertTrue(mm.streamStatus.haveBeamsBeenMade())
        mm.streamStatus.beams = False
        mmm = copy.deepcopy(mm)
        self.assertFalse(mmm.streamStatus.beams)
        # m.show()


# -----------------------------------------------------------------------------


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
