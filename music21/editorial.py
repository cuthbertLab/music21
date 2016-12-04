# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         editorial.py
# Purpose:      music21 classes for representing notes
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2008-2015 Michael Scott Cuthbert and the music21
#               Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------
'''
Editorial objects store comments and other meta-data associated with specific
:class:`~music21.note.Note` objects or other music21 objects.
'''
import unittest
from music21 import exceptions21
from music21.common import SlottedObjectMixin

#------------------------------------------------------------------------------


class EditorialException(exceptions21.Music21Exception):
    pass

class CommentException(exceptions21.Music21Exception):
    pass


#------------------------------------------------------------------------------
class NoteEditorial(SlottedObjectMixin):
    '''
    Editorial comments and special effects that can be applied to notes
    Standard ones are stored as attributes.  Non-standard/one-off effects are
    stored in the dict called "misc":

    >>> a = editorial.NoteEditorial()
    >>> a.comment = "blue note"  # a standard editorial 
    >>> a.misc['backgroundHighlight'] = 'yellow'  # non-standard.

    Every GeneralNote object already has a NoteEditorial object attached to it
    at object.editorial.  Normally you will just change that object instead.

    For instance, take the case where a scribe wrote F in the score, knowing
    that a good singer would automatically sing F-sharp instead.  We can store
    the editorial suggestion to sing F-sharp as a "musica ficta" accidental
    object:

    >>> fictaSharp = pitch.Accidental("Sharp")
    >>> n = note.Note("F")
    >>> n.editorial.ficta = fictaSharp
    >>> assert(n.editorial.ficta.alter == 1.0) #_DOCS_HIDE
    >>> #_DOCS_SHOW n.show('lily.png')  # only Lilypond currently supports musica ficta

    .. image:: images/noteEditorialFictaSharp.*
        :width: 103

    '''

    _DOC_ATTR = {
        'ficta': '''a :class:`~music21.pitch.Accidental` object that specifies musica 
            ficta for the note.  Will only be displayed in LilyPond and then only if 
            there is no Accidental object on the note itself''',
        'harmonicInterval': '''an :class:`~music21.interval.Interval` object that specifies 
            the harmonic interval between this note and a single other note 
            (useful for storing information post analysis)''',
        'melodicInterval': '''an :class:`~music21.interval.Interval` object that specifies 
            the melodic interval to the next note in this part/voice/stream, etc.''',
        'misc': 'A dict to hold anything you might like to store.',
        }

    __slots__ = (
        'ficta',
        '_misc',
        'harmonicInterval',
        'melodicInterval',
        )

    ### INITIALIZER ###

    def __init__(self):
        # Accidental object -- N.B. for PRINTING only not for determining intervals
        self.ficta = None
        self._misc = None
        self.harmonicInterval = None
        self.melodicInterval = None

    @property
    def misc(self):
        if self._misc is None:
            self._misc = {}
        return self._misc
    
    @misc.setter
    def misc(self, value):
        self._misc = value

#------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testSlots(self):
        editorial = NoteEditorial()
        assert not hasattr(editorial, '__dict__')

    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
        '''
        import copy
        import sys
        import types
        for part in sys.modules[self.__module__].__dict__:
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            name = getattr(sys.modules[self.__module__], part)
            if callable(name) and not isinstance(name, types.FunctionType):
                try:  # see if obj can be made w/ args
                    obj = name()
                except TypeError:
                    continue
                a = copy.copy(obj)
                b = copy.deepcopy(obj)
                self.assertIsNot(a, None)
                self.assertIsNot(b, None)


#------------------------------------------------------------------------------


_DOC_ORDER = (
    NoteEditorial,
    )

if __name__ == "__main__":
    #import doctest
    #doctest.testmod()
    import music21
    music21.mainTest(Test)
