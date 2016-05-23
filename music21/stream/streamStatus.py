# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         streamStatus.py
# Purpose:      functionality for reporting on the notational status of streams
#
# Authors:      Josiah Wolf Oberholtzer
#
# Copyright:    Copyright © 2013 Michael Scott Cuthbert and the music21
#               Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------

import unittest

from music21 import environment
from music21 import common
from music21.common import SlottedObjectMixin

environLocal = environment.Environment(__file__)


#------------------------------------------------------------------------------


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


    ### CLASS VARIABLES ###

    __slots__ = (
        '_accidentals',
        '_beams',
        '_client',
        '_concertPitch',
        '_dirty',
        '_enharmonics',
        '_measures',
        '_ornaments',
        '_rests',
        '_ties',
        )

    ### INITIALIZER ###

    def __init__(self, client=None):
        self._client = None
        self._accidentals = None
        self._beams = None
        self._concertPitch = None
        self._dirty = None
        self._enharmonics = None
        self._measures = None
        self._ornaments = None
        self._rests = None
        self._ties = None
        self.client = client


    ## SPECIAL METHODS ###
    def __deepcopy__(self, memo=None):
        '''
        Manage deepcopying by creating a new reference to the same object. 
        leaving out the client
        '''
        new = type(self)()
        for x in self.__slots__:
            if x == '_client':
                new._client = None
            else:
                setattr(new, x, getattr(self, x))
            
        return new


    ## unwrap weakref for pickling

    def __getstate__(self):
        self._client = common.unwrapWeakref(self._client)
        return SlottedObjectMixin.__getstate__(self)

    def __setstate__(self, state):
        SlottedObjectMixin.__setstate__(self, state)
        self._client = common.wrapWeakref(self._client)

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
        for n in self.client.recurse(classFilter=('NotRest'), restoreActiveSites=False):
            if n.beams is not None and len(n.beams.beamsList):
                return True
        return False
    
    def haveTupletBracketsBeenMade(self):
        '''
        If any GeneralNote in this Stream is a tuplet, then check to
        see if any of them have a first Tuplet with type besides None
        return True. Otherwise return False if there is a tuplet. Return None if
        no Tuplets.
        
        >>> s = stream.Stream()
        >>> s.streamStatus.haveTupletBracketsBeenMade() is None
        True
        >>> s.append(note.Note())
        >>> s.streamStatus.haveTupletBracketsBeenMade() is None
        True
        >>> n = note.Note(quarterLength=1./3)
        >>> s.append(n)
        >>> s.streamStatus.haveTupletBracketsBeenMade()
        False
        >>> n.duration.tuplets[0].type = 'start'
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

    ### PUBLIC PROPERTIES ###

    @property
    def client(self):
        return common.unwrapWeakref(self._client)
    @client.setter
    def client(self, client):
        # client is the Stream that this status lives on
        self._client = common.wrapWeakref(client)


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
