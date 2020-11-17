# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         tie.py
# Purpose:      music21 classes for representing ties (visual and conceptual)
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2010, 2012, 2015 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------

'''
The `tie` module contains a single class, `Tie` that represents the visual and
conceptual idea of tied notes.  They can be start or stop ties.
'''

import unittest
from music21 import exceptions21
from music21.common.objects import SlottedObjectMixin
from music21 import prebase

class TieException(exceptions21.Music21Exception):
    pass


# ------------------------------------------------------------------------------
class Tie(prebase.ProtoM21Object, SlottedObjectMixin):
    '''
    Object added to notes that are tied to other notes. The `type` value is one
    of start, stop, or continue.

    >>> note1 = note.Note()
    >>> note1.tie = tie.Tie('start')  # start, stop, or continue
    >>> note1.tie.style = 'normal'  # default; could also be 'dotted' or 'dashed' or 'hidden'
    >>> note1.tie.type
    'start'

    >>> note1.tie
    <music21.tie.Tie start>

    Generally Ties have a placement of None, but if they are defined
    as 'above' or 'below' this will be retained.  (see:
    http://forums.makemusic.com/viewtopic.php?f=12&t=2179&start=0
    for how orientation and placement in musicxml are essentially the same
    content).

    >>> note1.tie.placement is None
    True

    Differences from MusicXML:

    *  notes do not need to know if they are tied from a
       previous note.  i.e., you can tie n1 to n2 just with
       a tie start on n1.  However, if you want proper musicXML output
       you need a tie stop on n2.

    *  one tie with "continue" implies tied from and tied to.

    The tie.style only applies to ties of type 'start' or 'continue' (and then
    only to the next part of the tie).  For instance, if there are two
    tied notes, and the first note has a 'dotted'-start tie, and the
    second note has a 'dashed'-stop tie, the graphical tie itself will be dotted.

    A type of tie that is unknown raises a ValueError:

    >>> tie.Tie('hello')
    Traceback (most recent call last):
    music21.tie.TieException: Type must be one of
    ('start', 'stop', 'continue', 'let-ring', 'continue-let-ring'), not hello

    OMIT_FROM_DOCS
       optional (to know what notes are next:)
          .to = note()   # not implemented yet, b/c of garbage coll.
          .from = note()

    (question: should notes be able to be tied to multiple notes
    for the case where a single note is tied both voices of a
    two-note-head unison?)
    '''
    # CLASS VARIABLES #
    __slots__ = (
        'id',
        'placement',
        'style',
        'type',
    )

    _DOC_ATTR = {
        'type': '''
            The tie type, can be 'start', 'stop', 'continue', 'let-ring', or 'continue-let-ring'.
            ''',
        'style': '''
            The style of the tie.  Currently can be 'normal', 'dotted', 'dashed' or 'hidden'
            ''',
        'placement': '''
            Whether the tie should go up or down. Can be None, meaning
            it is unknown or should be determined from context, or 'above' or 'below.
            ''',
    }

    VALID_TIE_TYPES = ('start', 'stop', 'continue', 'let-ring', 'continue-let-ring')

    # pylint: disable=redefined-builtin
    def __init__(self, type='start'):  # @ReservedAssignment
        # super().__init__()
        if type not in self.VALID_TIE_TYPES:
            raise TieException(
                'Type must be one of {}, not {}'.format(self.VALID_TIE_TYPES, type))
        # naming this 'type' was a mistake, because cannot create a property of this name.

        self.id = id(self)
        self.type = type
        self.style = 'normal'
        self.placement = None  # = unknown, can be 'above' or 'below'

    # SPECIAL METHODS #
    def __eq__(self, other):
        # noinspection PyComparisonWithNone
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

    def _reprInternal(self):
        return self.type


class Test(unittest.TestCase):
    pass


# ------------------------------------------------------------------------------

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)

