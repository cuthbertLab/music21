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
from music21.ext import six

#------------------------------------------------------------------------------


class EditorialException(exceptions21.Music21Exception):
    pass

class CommentException(exceptions21.Music21Exception):
    pass


#------------------------------------------------------------------------------


def getObjectsWithEditorial(
    listToSearch, 
    editorialStringToFind,
    listOfValues=None,
    ):
    '''
    Provided a list of objects (typically note objects) to search through, this
    method returns only those objects that have the editorial attribute defined
    by the editorialStringToFind.  An optional parameter, listOfValues, is a
    list of all the possible values the given object's editorialString can
    have.

    The editorialStringToFind can be any of the pre-defined editorial
    attributes (such as "ficta" or "harmonicIntervals") but it may also be the
    dictionary key of editorial notes stored in the miscellaneous (misc)
    dictionary.  For example, "isPassingTone" or "isNeighborTone"

    >>> n1 = note.Note()
    >>> n1.editorial.misc['isPassingTone'] = True
    >>> n2 = note.Note()
    >>> n2.editorial.comment = 'consider revising'
    >>> s = stream.Stream()
    >>> s.repeatAppend(n1, 5)
    >>> s.repeatAppend(note.Note(), 2)
    >>> s.repeatAppend(n2, 3)
    >>> listofNotes = s.getElementsByClass(note.Note)
    >>> listOfValues = ['consider revising', 'remove']
    >>> listofNotesWithEditorialisPassingTone = editorial.getObjectsWithEditorial(
    ...     listofNotes, "isPassingTone")
    >>> listofNotesWithEditorialComment = editorial.getObjectsWithEditorial(
    ...     listofNotes, "comment", listOfValues)
    >>> print(len(listofNotesWithEditorialisPassingTone))
    5

    >>> print(len(listofNotesWithEditorialComment))
    3
    '''
    listofOBJToReturn = []
    for obj in listToSearch:
        try:
            try:
                editorialContents = getattr(
                    obj.editorial, editorialStringToFind)
            except AttributeError:
                editorialContents = obj.editorial.misc[editorialStringToFind]

            if listOfValues is not None:
                if editorialContents in listOfValues:
                    listofOBJToReturn.append(obj)
            else:
                listofOBJToReturn.append(obj)
        except KeyError:
            pass
    return listofOBJToReturn


class NoteEditorial(SlottedObjectMixin):
    '''
    Editorial comments and special effects that can be applied to notes
    Standard ones are stored as attributes.  Non-standard/one-off effects are
    stored in the dict called "misc":

    >>> a = editorial.NoteEditorial()
    >>> a.color = "blue"  # a standard editorial effect
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
        'color': 'the color of the note (RGP, x11 colors, and extended x11colors are allowed)',
        'comment': 'a reference to a :class:`~music21.editorial.Comment` object',
        'ficta': '''a :class:`~music21.pitch.Accidental` object that specifies musica 
            ficta for the note.  Will only be displayed in LilyPond and then only if 
            there is no Accidental object on the note itself''',
        'hidden': '''boolean value about whether to hide the 
            note or not (only works in lilypond)''',
        'harmonicInterval': '''an :class:`~music21.interval.Interval` object that specifies 
            the harmonic interval between this note and a single other note 
            (useful for storing information post analysis)''',
        'harmonicIntervals': 'a list for when you want to store more than one harmonicInterval',
        'melodicInterval': '''an :class:`~music21.interval.Interval` object that specifies 
            the melodic interval to the next note in this part/voice/stream, etc.''',
        'melodicIntervals': 'a list for storing more than one melodic interval',
        'melodicIntervalsOverRests': 'same thing but a list',
        'misc': 'A dict to hold anything you might like to store.',
        }

    __slots__ = (
        'ficta',
        'color',
        'misc',
        'harmonicInterval',
        'harmonicIntervals',
        'hidden',
        'melodicInterval',
        'melodicIntervals',
        'melodicIntervalsOverRests',
        'comment',
        )

    ### INITIALIZER ###

    def __init__(self):
        # Accidental object -- N.B. for PRINTING only not for determining intervals
        self.ficta = None
        self.color = None
        self.misc = {}
        self.harmonicInterval = None
        self.harmonicIntervals = []
        self.hidden = False
        self.melodicInterval = None
        self.melodicIntervals = []
        self.melodicIntervalsOverRests = []
        self.comment = Comment()

    ### PUBLIC METHODS ###

    def lilyStart(self):
        r'''
        A method that returns a string containing the lilypond output that
        comes before the note.

        >>> n = note.Note()
        >>> n.editorial.lilyStart()
        ''

        >>> n.editorial.ficta = pitch.Accidental("Sharp")
        >>> n.editorial.color = "blue"
        >>> n.editorial.hidden = True
        >>> print(n.editorial.lilyStart())
        \ficta \color "blue" \hideNotes

        '''
        result = ""
        if self.ficta is not None:
            result += self.fictaLilyStart()
        if self.color:
            result += self.colorLilyStart()
        if self.hidden is True:
            result += r"\hideNotes "
        return result

    def fictaLilyStart(self):
        r'''
        Returns \ficta -- called out so it is more easily subclassed
        '''
        return r"\ficta "

    def colorLilyStart(self):
        r'''
        Returns \color "theColorName" -- called out so it is more easily
        subclassed.
        '''
        return r'\color "' + self.color + '" '

    def lilyAttached(self):
        r'''
        Returns any information that should be attached under the note,
        currently just returns self.comment.lily or "".
        '''
        # pylint: disable=undefined-variable
        if self.comment and self.comment.text:
            if six.PY2:
                return unicode(self.comment.lily) # @UndefinedVariable
            else:
                return str(self.comment.lily)
        else:
            return ''

    def lilyEnd(self):
        r'''
        Returns a string of editorial lily instructions to come after the note.
        Currently it is just info to turn off hidding of notes.
        '''
        result = u""
        if self.hidden is True:
            result += u"\\unHideNotes "
        return result


class Comment(SlottedObjectMixin):
    '''
    An object that adds text above or below a note:

    >>> n = note.Note()
    >>> n.editorial.comment.text = "hello"
    >>> n.editorial.comment.position = "above"
    >>> n.editorial.comment.lily
    '^"hello"'

    '''

    ### CLASS VARIABLES ###

    __slots__ = (
        'position',
        'text',
        )

    ### INITIALIZER ###

    def __init__(self):
        self.position = "below"
        self.text = None

    ### PUBLIC PROPERTIES ###

    @property
    def lily(self):
        if self.text is None:
            return ""
        if self.position == 'below':
            return '_"' + self.text + '"'
        elif self.position == 'above':
            return '^"' + self.text + '"'
        else:
            raise CommentException(
                'Cannot deal with position: ' + self.position)


#------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testSlots(self):
        editorial = NoteEditorial()
        assert not hasattr(editorial, '__dict__')
        comment = Comment()
        assert not hasattr(comment, '__dict__')

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
                unused_a = copy.copy(obj)
                unused_b = copy.deepcopy(obj)

    def testBasic(self):
        a = Comment()
        self.assertEqual(a.position, 'below')


#------------------------------------------------------------------------------


_DOC_ORDER = (
    NoteEditorial,
    )

if __name__ == "__main__":
    #import doctest
    #doctest.testmod()
    import music21
    music21.mainTest(Test)
