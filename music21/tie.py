# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         tie.py
# Purpose:      music21 classes for representing ties (visual and conceptual)
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2010, 2012, 2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

'''
The `tie` module contains a single class, `Tie` that represents the visual and
conceptual idea of tied notes.  They can be start or stop ties.
'''

import unittest
from music21 import exceptions21
from music21.common import SlottedObject

class TieException(exceptions21.Music21Exception):
    pass

#-------------------------------------------------------------------------------

class Tie(SlottedObject):
    '''
    Object added to notes that are tied to other notes. The `type` value is one
    of start, stop, or continue.

    >>> note1 = note.Note()
    >>> note1.tie = tie.Tie("start") # start, stop, or continue
    >>> note1.tie.style = "normal" # default; could also be "dotted" or "dashed" or "hidden"
    >>> note1.tie.type
    'start'

    >>> note1.tie
    <music21.tie.Tie start>

    Differences from MusicXML:
       notes do not need to know if they are tied from a
       previous note.  i.e., you can tie n1 to n2 just with
       a tie start on n1.  However, if you want proper musicXML output
       you need a tie stop on n2
       one tie with "continue" implies tied from and tied to

    OMIT_FROM_DOCS
       optional (to know what notes are next:)
          .to = note()   # not implimented yet, b/c of garbage coll.
          .from = note()

    (question: should notes be able to be tied to multiple notes
    for the case where a single note is tied both voices of a
    two-note-head unison?)
    '''

    ### CLASS VARIABLES ###

    __slots__ = (
        'style',
        'type',
        )

    ### INITIALIZER ###

    def __init__(self, type='start'): #@ReservedAssignment
        #music21.Music21Object.__init__(self)
        if type not in ('start', 'stop', 'continue'):
            raise TieException("Type must be one of 'start', 'stop', or 'continue', not %s" % type)
        # naming this "type" was a mistake, because cannot create a property of this name.
        
        
        self.type = type
        self.style = "normal"

    ### SPECIAL METHODS ###

    def __eq__(self, other):
        '''
        Equality. Based entirely on Tie.type.

        >>> t1 = tie.Tie('start')
        >>> t2 = tie.Tie('start')
        >>> t3 = tie.Tie('stop')
        >>> t1 == t2
        True

        >>> t2 == t3, t3 == t1
        (False, False)

        >>> t2 == None
        False
        '''
        if other is None or not isinstance(other, Tie):
            return False
        elif self.type == other.type:
            return True
        return False

    def __ne__(self, other):
        '''
        Tests for object inequality. Needed for pitch comparisons.

        >>> a = tie.Tie('start')
        >>> b = tie.Tie('stop')
        >>> a != b
        True
        '''
        return not self.__eq__(other)

    def __repr__(self):
        return '<music21.tie.Tie %s>' % self.type



class Test(unittest.TestCase):

    def runTest(self):
        pass


#-------------------------------------------------------------------------------

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof

