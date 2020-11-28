# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         editorial.py
# Purpose:      music21 classes for representing editorial information
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2008-2015 Michael Scott Cuthbert and the music21
#               Project
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
Editorial objects store comments and other metadata associated with specific
:class:`~music21.base.Music21Object` elements such as Notes.

Some of the aspects of :class:`~music21.editorial.Editorial` objects
represent very early (pre-v0.1) versions of music21.  Thus some of the
pre-defined aspects might be removed from documentation in the future.

Access an editorial object by calling `.editorial` on any music21 object:

>>> c = clef.TrebleClef()
>>> ed = c.editorial
>>> ed
<music21.editorial.Editorial {}>

The object is lazily created on first access.
To see if there is any existing editorial information without creating
the object, call `.hasEditorialInformation`

>>> n = note.Note('C#4')
>>> n.hasEditorialInformation
False

>>> n.editorial.unedited = True
>>> n.hasEditorialInformation
True
'''
import unittest
from music21 import exceptions21
from music21 import prebase
from music21 import style

# -----------------------------------------------------------------------------


class EditorialException(exceptions21.Music21Exception):
    pass


class CommentException(exceptions21.Music21Exception):
    pass


# -----------------------------------------------------------------------------
class Editorial(prebase.ProtoM21Object, dict):
    '''
    Editorial comments and special effects that can be applied to music21 objects.

    >>> ed1 = editorial.Editorial()
    >>> ed1.backgroundHighlight = 'yellow'  # non-standard.
    >>> ed1.backgroundHighlight
    'yellow'
    >>> list(ed1.keys())
    ['backgroundHighlight']
    >>> ed1
     <music21.editorial.Editorial {'backgroundHighlight': 'yellow'}>

    Every GeneralNote object already has a NoteEditorial object attached to it
    at object.editorial.  Normally you will just change that object instead.

    For instance, take the case where a scribe wrote F in the score, knowing
    that a good singer would automatically sing F-sharp instead.  We can store
    the editorial suggestion to sing F-sharp as a "musica ficta" accidental
    object:

    >>> fictaSharp = pitch.Accidental('sharp')
    >>> n = note.Note('F')
    >>> n.editorial.ficta = fictaSharp
    >>> assert(n.editorial.ficta.alter == 1.0) #_DOCS_HIDE
    >>> #_DOCS_SHOW n.show('lily.png')  # only Lilypond currently supports musica ficta

    .. image:: images/noteEditorialFictaSharp.*
        :width: 103

    '''
    _DOC_ATTR = {
        'comments': '''
            a list of :class:`~music21.editorial.Comment` objects that represent any comments
            about the object.
            ''',
        'footnotes': '''
            a list of :class:`~music21.editorial.Comment` objects that represent annotations
            for the object.  These have specific meanings in MusicXML.
        ''',
        'ficta': '''a :class:`~music21.pitch.Accidental` object that specifies musica
            ficta for the note.  Will only be displayed in LilyPond and then only if
            there is no Accidental object on the note itself''',
        'harmonicInterval': '''an :class:`~music21.interval.Interval` object that specifies
            the harmonic interval between this object and a single other object, or None
            (useful for storing information post analysis)''',
        'melodicInterval': '''an :class:`~music21.interval.Interval` object that specifies
            the melodic interval to the next object in this Part/Voice/Stream, etc.''',
        'misc': '''
            DEPRECATED! To be removed in v.7.

            A dict to hold anything you might like to store.

            Note that this is deprecated since editorials subclass dict objects, therefore
            they can be used for anything else without needing the "misc" attribute.
            ''',
    }

    predefinedDicts = ('misc',)
    predefinedLists = ('footnotes', 'comments')
    predefinedNones = ('ficta', 'harmonicInterval', 'melodicInterval')

    def _reprInternal(self):
        return dict.__repr__(self)

    # INITIALIZER #
    def __getattr__(self, name):
        if name in self:
            return self[name]
        elif name in self.predefinedDicts:
            self[name] = {}
            return self[name]
        elif name in self.predefinedLists:
            self[name] = []
            return self[name]
        elif name in self.predefinedNones:
            self[name] = None
            return self[name]
        else:
            raise AttributeError('Editorial does not have an attribute %s' % name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError("No such attribute: " + name)


# -----------------------------------------------------------------------------
class Comment(prebase.ProtoM21Object, style.StyleMixin):
    '''
    A comment or footnote or something else attached to a note.

    >>> c = editorial.Comment('presented as C natural in the 1660 print.')
    >>> c.isFootnote = True
    >>> c.levelInformation = 'musicological'

    >>> n = note.Note('C#4')
    >>> n.editorial.footnotes.append(c)
    >>> n.editorial.footnotes[0]
    <music21.editorial.Comment 'presented as C na...'>

    Comments have style information:

    >>> c.style.color = 'red'
    >>> c.style.color
    'red'
    '''
    def __init__(self, text=None):
        super().__init__()
        self.text = text
        self.isFootnote = False
        self.isReference = False
        self.levelInformation = None

    def _reprInternal(self):
        if self.text is None:
            return ''

        if len(self.text) < 20:
            return repr(self.text)
        else:
            return repr(self.text[:17] + '...')

# -----------------------------------------------------------------------------


class Test(unittest.TestCase):

    def testCopyAndDeepcopy(self):
        '''
        Test copying all objects defined in this module
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
            # noinspection PyTypeChecker
            if callable(name) and not isinstance(name, types.FunctionType):
                try:  # see if obj can be made w/ args
                    obj = name()
                except TypeError:
                    continue
                a = copy.copy(obj)
                b = copy.deepcopy(obj)
                self.assertIsNot(a, None)
                self.assertIsNot(b, None)


# -----------------------------------------------------------------------------


_DOC_ORDER = (
    Editorial,
    Comment,
)

if __name__ == '__main__':
    # import doctest
    # doctest.testmod()
    import music21
    music21.mainTest(Test)
