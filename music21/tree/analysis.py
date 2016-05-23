# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         tree/analysis.py
# Purpose:      horizontal analysis tools on timespan trees
#
# Authors:      Josiah Wolf Oberholtzer
#
# Copyright:    Copyright © 2013-14 Michael Scott Cuthbert and the music21
#               Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------
'''
Tools for performing voice-leading analysis with trees.
'''
import collections
import unittest
#from music21 import base
#from music21 import common
from music21 import environment
from music21 import exceptions21
#from music21 import key

environLocal = environment.Environment("tree.analysis")


class HorizontalityException(exceptions21.TreeException):
    pass


#------------------------------------------------------------------------------


class Horizontality(collections.Sequence):
    r'''
    A horizontality of consecutive PitchedTimespan objects.
    
    It must be initiated with a list or tuple of Timespan objects.
    '''

    ### CLASS VARIABLES ###

    __slots__ = (
        'timespans',
        )

    ### INITIALIZER ###

    def __init__(self,
        timespans=None,
        ):
        if not isinstance(timespans, collections.Sequence):
            raise HorizontalityException("timespans must be a sequence, not %r" % timespans)
        if len(timespans) == 0:
            raise HorizontalityException(
                "there must be at least one timespan in the timespans list")
        if not all(hasattr(x, 'offset') and hasattr(x, 'endTime') for x in timespans):
            raise HorizontalityException("only Timespan objects can be added to a horizontality")
        self.timespans = tuple(timespans)

    ### SPECIAL METHODS ###

    def __getitem__(self, item):
        return self.timespans[item]

    def __len__(self):
        return len(self.timespans)

    def __repr__(self):
        pitch_strings = []
        for x in self:
            string = '({},)'.format(', '.join(
                y.nameWithOctave for y in x.pitches))
            pitch_strings.append(string)
        return '<{}: {}>'.format(
            type(self).__name__,
            ' '.join(pitch_strings),
            )

    ### PROPERTIES ###

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
        Is true if the Horizontality contains no motion (including enharmonic restatings)
        '''
        pitchSets = set()
        for x in self:
            pitchSets.add(tuple(x.pitches))
        if len(pitchSets) == 1:
            return True
        return False



#------------------------------------------------------------------------------




# class VoiceLeadingQuartet(common.SlottedObjectMixin):
# 
#     ### CLASS VARIABLES ###
# 
#     __slots__ = (
#         '_key_signature',
#         '_voiceOneNoteOne',
#         '_voiceOneNoteTwo',
#         '_voiceTwoNoteOne',
#         '_voiceTwoNoteTwo',
#         )
# 
#     ### INITIALIZER ###
# 
#     def __init__(
#         self,
#         voiceOneNoteOne=None,
#         voiceOneNoteTwo=None,
#         voiceTwoNoteOne=None,
#         voiceTwoNoteTwo=None,
#         key_signature=None,
#         ):
#         base.Music21Object.__init__(self)
#         if key_signature is None:
#             key_signature = key.Key('C')
#         self._key_signature = key.Key(key_signature)
#         self._voiceOneNoteOne = voiceOneNoteOne
#         self._voiceOneNoteTwo = voiceOneNoteTwo
#         self._voiceTwoNoteOne = voiceTwoNoteOne
#         self._voiceTwoNoteTwo = voiceTwoNoteTwo
# 
#     ### PUBLIC METHODS ###
# 
#     def hasAntiParallelMotion(self):
#         pass
# 
#     def hasContraryMotion(self):
#         pass
# 
#     def hasHiddenFifth(self):
#         pass
# 
#     def hasHiddenInterval(self, expr):
#         pass
# 
#     def hasHiddenOctave(self):
#         pass
# 
#     def hasImproperResolution(self):
#         pass
# 
#     def hasInwardContraryMotion(self):
#         pass
# 
#     def hasNoMotion(self):
#         pass
# 
#     def hasObliqueMotion(self):
#         pass
# 
#     def hasOutwardContraryMotion(self):
#         pass
# 
#     def hasParallelFifth(self):
#         pass
# 
#     def hasParallelInterval(self, expr):
#         pass
# 
#     def hasParallelMotion(self):
#         pass
# 
#     def hasParallelOctave(self):
#         pass
# 
#     def hasParallelUnison(self):
#         pass
# 
#     def hasParallelUnisonOrOctave(self):
#         pass
# 
#     def hasSimilarMotion(self):
#         pass
# 
#     ### PUBLIC PROPERTIES ###
# 
#     @property
#     def key_signature(self):
#         return self._key_signature
# 
#     @property
#     def voiceOneNoteOne(self):
#         return self._voiceOneNoteOne
# 
#     @property
#     def voiceOneNoteTwo(self):
#         return self._voiceOneNoteTwo
# 
#     @property
#     def voiceTwoNoteOne(self):
#         return self._voiceTwoNoteOne
# 
#     @property
#     def voiceTwoNoteTwo(self):
#         return self._voiceTwoNoteTwo


#------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass


#------------------------------------------------------------------------------


_DOC_ORDER = ()


#------------------------------------------------------------------------------


if __name__ == "__main__":
    import music21
    music21.mainTest(Test)
