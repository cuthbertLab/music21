# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         streamStatus.py
# Purpose:      functionality for reporting on the notational status of streams
#
# Authors:      Josiah Wolf Oberholtzer
#
# Copyright:    Copyright © 2013 Michael Scott Cuthbert and the music21
#               Project
# License:      LGPL, see license.txt
#------------------------------------------------------------------------------


import unittest

from music21 import environment

environLocal = environment.Environment(__file__)


#------------------------------------------------------------------------------


class StreamStatus(object):

    ### CLASS VARIABLES ###

#    __slots__ = (
#        '_accidentals',
#        '_beams',
#        '_client',
#        '_concertPitch',
#        '_dirty',
#        '_enharmonics',
#        '_measures',
#        '_ornaments',
#        '_rests',
#        '_ties',
#        )

    ### INITIALIZER ###

    def __init__(self, client=None):
        self._accidentals = None
        self._beams = None
        self._client = client
        self._concertPitch = None
        self._dirty = None
        self._enharmonics = None
        self._measures = None
        self._ornaments = None
        self._rests = None
        self._ties = None

    ### SPECIAL METHODS ###

#    def __getstate__(self):
#        state = {}
#        attributes = (
#            '_accidentals',
#            '_beams',
#            '_client',
#            '_concertPitch',
#            '_dirty',
#            '_enharmonics',
#            '_measures',
#            '_ornaments',
#            '_rests',
#            '_ties',
#            )
#        for attribute in attributes:
#            state[attribute] = getattr(self, attribute)
#        return state

    ### PUBLIC METHODS ###

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
        for n in self.client.flat.notes:
            if n.beams is not None and len(n.beams.beamsList):
                return True
        return False

    ### PUBLIC PROPERTIES ###

    @property
    def client(self):
        return self._client

    @apply
    def beams():
        def fget(self):
            if self._beams is None:
                self._beams = self.haveBeamsBeenMade()
            return self._beams

        def fset(self, expr):
            if expr is not None:
                self._beams = bool(expr)
            else:
                self._beams = None

        return property(**locals())


#------------------------------------------------------------------------------


class Test(unittest.TestCase):
    '''
    Note: all Stream tests are found in test/testStream.py
    '''

    def runTest(self):
        pass


#------------------------------------------------------------------------------


if __name__ == "__main__":
    import music21
    music21.mainTest(Test)
