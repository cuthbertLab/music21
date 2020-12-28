# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         tree/analysis.py
# Purpose:      horizontal analysis tools on timespan trees
#
# Authors:      Josiah Wolf Oberholtzer
#
# Copyright:    Copyright © 2013-14 Michael Scott Cuthbert and the music21
#               Project
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
Tools for performing voice-leading analysis with trees.
'''
import collections.abc
import unittest
# from music21 import base
# from music21 import common
from music21 import environment
from music21 import exceptions21
# from music21 import key

environLocal = environment.Environment('tree.analysis')


class HorizontalityException(exceptions21.TreeException):
    pass


# -----------------------------------------------------------------------------


class Horizontality(collections.abc.Sequence):
    r'''
    A horizontality of consecutive PitchedTimespan objects.

    It must be initiated with a list or tuple of Timespan objects.
    '''

    # CLASS VARIABLES #

    __slots__ = (
        'timespans',
    )

    # INITIALIZER #

    def __init__(self, timespans=None):
        if not isinstance(timespans, collections.abc.Sequence):
            raise HorizontalityException(f'timespans must be a sequence, not {timespans!r}')
        if not timespans:
            raise HorizontalityException(
                'there must be at least one timespan in the timespans list')
        if not all(hasattr(x, 'offset') and hasattr(x, 'endTime') for x in timespans):
            raise HorizontalityException('only Timespan objects can be added to a horizontality')
        self.timespans = tuple(timespans)

    # SPECIAL METHODS #

    def __getitem__(self, item):
        return self.timespans[item]

    def __len__(self):
        return len(self.timespans)

    def __repr__(self):
        pitchStrings = []
        for x in self:
            joinedPitches = ', '.join(y.nameWithOctave for y in x.pitches)
            out = f'({joinedPitches},)'
            pitchStrings.append(out)
        pitchStr = ' '.join(pitchStrings)
        return f'<{type(self).__name__}: {pitchStr}>'

    # PROPERTIES #

    @property
    def hasPassingTone(self):
        r'''
        Is true if the Horizontality contains a passing tone; currently defined as three tones in
        one direction.

        (TODO: better check)
        '''
        if len(self) < 3:
            return False
        elif not all(len(x.pitches) for x in self):
            return False
        pitches = (
            self[0].pitches[0],
            self[1].pitches[0],
            self[2].pitches[0],
        )
        if pitches[0] < pitches[1] < pitches[2]:
            return True
        elif pitches[0] > pitches[1] > pitches[2]:
            return True
        return False

    @property
    def hasNeighborTone(self):
        r'''
        Is true if the Horizontality contains a neighbor tone.
        '''
        if len(self) < 3:
            return False
        elif not all(len(x.pitches) for x in self):
            return False

        pitches = (
            self[0].pitches[0],
            self[1].pitches[0],
            self[2].pitches[0],
        )
        if pitches[0] == pitches[2]:
            if abs(pitches[1].ps - pitches[0].ps) < 3:
                return True
        return False

    @property
    def hasNoMotion(self):
        r'''
        Is true if the Horizontality contains no motion (including enharmonic restatements)
        '''
        pitchSets = set()
        for x in self:
            pitchSets.add(tuple(x.pitches))
        if len(pitchSets) == 1:
            return True
        return False


# -----------------------------------------------------------------------------


class Test(unittest.TestCase):
    pass


# -----------------------------------------------------------------------------


_DOC_ORDER = ()


# -----------------------------------------------------------------------------


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
