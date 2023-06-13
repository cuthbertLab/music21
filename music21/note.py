# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         note.py
# Purpose:      music21 classes for representing notes
#
# Authors:      Michael Scott Asato Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2006-2023 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Classes and functions for creating Notes, Rests, and Lyrics.

The :class:`~music21.pitch.Pitch` object is stored within,
and used to configure, :class:`~music21.note.Note` objects.
'''
from __future__ import annotations

import copy
import typing as t
from typing import overload  # PyCharm bug
import unittest

from music21 import base
from music21 import beam
from music21 import common
from music21.duration import Duration
from music21 import environment
from music21 import exceptions21
from music21 import expressions
from music21 import interval
from music21.pitch import Pitch
from music21 import prebase
from music21 import style
from music21 import tie
from music21 import volume

if t.TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from music21.common.types import StepName, OffsetQLIn
    from music21 import articulations
    from music21 import chord
    from music21 import instrument
    from music21 import percussion
    _NotRestType = t.TypeVar('_NotRestType', bound='NotRest')

environLocal = environment.Environment('note')

noteheadTypeNames = (
    'arrow down',
    'arrow up',
    'back slashed',
    'circle dot',
    'circle-x',
    'circled',
    'cluster',
    'cross',
    'diamond',
    'do',
    'fa',
    'inverted triangle',
    'la',
    'left triangle',
    'mi',
    'none',
    'normal',
    'other',
    're',
    'rectangle',
    'slash',
    'slashed',
    'so',
    'square',
    'ti',
    'triangle',
    'x',
)

stemDirectionNames = (
    'double',
    'down',
    'noStem',
    'none',
    'unspecified',
    'up',
)

def __dir__():
    out = [n for n in globals() if not n.startswith('__') and not n.startswith('Test')]
    out.remove('t')

    out.remove('annotations')
    out.remove('unittest')
    out.remove('overload')
    out.remove('environLocal')
    out.remove('copy')
    out.remove('_DOC_ORDER')

    out.remove('Duration')
    out.remove('Pitch')
    out.remove('base')
    out.remove('beam')
    out.remove('common')
    out.remove('environment')
    out.remove('exceptions21')
    out.remove('expressions')
    out.remove('interval')
    out.remove('prebase')
    out.remove('style')
    out.remove('tie')
    out.remove('volume')

    out.remove('SyllabicChoices')
    return out

# -----------------------------------------------------------------------------
class LyricException(exceptions21.Music21Exception):
    pass


class NoteException(exceptions21.Music21Exception):
    pass


class NotRestException(exceptions21.Music21Exception):
    pass


# ------------------------------------------------------------------------------
SyllabicChoices = t.Literal[None, 'begin', 'single', 'end', 'middle', 'composite']

SYLLABIC_CHOICES: list[SyllabicChoices] = [
    None, 'begin', 'single', 'end', 'middle', 'composite',
]


class Lyric(prebase.ProtoM21Object, style.StyleMixin):
    '''
    An object representing a single Lyric as part of a note's .lyrics property.

    The note.lyric property is a simple way of specifying a single lyric, but
    Lyric objects are needed for working with multiple lyrics.

    >>> l = note.Lyric(text='hello')
    >>> l
    <music21.note.Lyric number=1 syllabic=single text='hello'>

    Music21 processes leading and following hyphens intelligently...

    >>> l2 = note.Lyric(text='hel-')
    >>> l2
    <music21.note.Lyric number=1 syllabic=begin text='hel'>

    ...unless applyRaw is set to True

    >>> l3 = note.Lyric(number=3, text='hel-', applyRaw=True)
    >>> l3
    <music21.note.Lyric number=3 syllabic=single text='hel-'>

    Lyrics have four properties: text, number, identifier, syllabic (single,
    begin, middle, end, or (not in musicxml) composite)

    >>> l3.text
    'hel-'

    >>> l3.number
    3

    >>> l3.syllabic
    'single'

    Note musicXML only supports one 'identifier' attribute which is called
    'number' but which can be a number or a descriptive identifier like
    'part2verse1.' To preserve lyric ordering, music21 stores a number and a
    descriptive identifier separately. The descriptive identifier is by default
    the same as the number, but in cases where a string identifier is present,
    it will be different.

    Both music21 and musicxml support multiple `Lyric` objects in the same stanza,
    for instance, if there is an elision on a note then multiple lyrics with
    different syllabics can appear on a single note.  In music21 these are supported
    by setting .components into a list of `Lyric` object.  For instance in
    the madrigal "Il bianco e dolce cigno", the "co" and "e" of "bianco e"
    are elided into a single lyric:

    >>> bianco = note.Lyric()
    >>> co = note.Lyric('co', syllabic='end')
    >>> e = note.Lyric('e', syllabic='single')
    >>> bianco.components = [co, e]
    >>> bianco.isComposite
    True
    >>> bianco.text
    'co e'
    >>> bianco.syllabic
    'composite'
    >>> e.elisionBefore = '_'
    >>> bianco.text
    'co_e'

    >>> [component.syllabic for component in bianco.components]
    ['end', 'single']

    Custom elision elements for composite components will be supported later.

    * New in v6.7: composite components, elisionBefore
    * Changed in v8: lyric text can be an empty string, but not None.
    '''
    _styleClass = style.TextStylePlacement
    # CLASS VARIABLES #

    __slots__ = (
        '_identifier',
        '_number',
        '_syllabic',
        '_text',
        'components',
        'elisionBefore',
    )

    # INITIALIZER #

    def __init__(self,
                 text: str = '',
                 number: int = 1,
                 *,
                 applyRaw: bool = False,
                 syllabic: SyllabicChoices = None,
                 identifier: str | None = None,
                 **keywords):
        super().__init__()
        self._identifier: str | None = None
        self._number: int = 1
        self._text: str = ''
        self._syllabic: SyllabicChoices = None
        self.components: list[Lyric] | None = None
        self.elisionBefore = ' '

        # these are set by setTextAndSyllabic
        if text:
            self.setTextAndSyllabic(text, applyRaw)

        # given as begin, middle, end, or single
        if syllabic is not None:
            self.syllabic = syllabic
        self.number = number

        # type ignore until https://github.com/python/mypy/issues/3004 resolved
        self.identifier = identifier  # type: ignore

    # PRIVATE METHODS #

    def _reprInternal(self):
        out = ''
        if self.number is not None:
            out += f'number={self.number} '
        if self._identifier is not None:
            out += f'identifier={self.identifier!r} '
        if self.syllabic is not None:
            out += f'syllabic={self.syllabic} '
        if self.text:
            out += f'text={self.text!r} '
        return out

    # PUBLIC PROPERTIES #
    @property
    def isComposite(self) -> bool:
        '''
        Returns True if this Lyric has composite elements,
        for instance, is multiple lyrics placed together.
        '''
        return bool(self.components)

    @property
    def text(self) -> str:
        '''
        Gets or sets the text of the lyric.  For composite lyrics, set
        the text of individual components instead of setting the text here.

        >>> l = note.Lyric()
        >>> l.text
        ''
        >>> l.text = 'hi'
        >>> l.text
        'hi'

        Setting the text of a composite lyric wipes out the components:

        >>> bianco = note.Lyric()
        >>> co = note.Lyric('co', syllabic='end')
        >>> e = note.Lyric('e', syllabic='single')
        >>> bianco.components = [co, e]
        >>> bianco.isComposite
        True
        >>> bianco.text
        'co e'
        >>> bianco.text = 'co_e'
        >>> bianco.isComposite
        False
        '''
        if not self.isComposite:
            return self._text
        else:
            if t.TYPE_CHECKING:
                assert isinstance(self.components, Sequence), \
                    'Programming error: isComposite implies that components exists'  # mypy
            text_out = self.components[0].text
            if text_out is None:
                text_out = ''
            for component in self.components[1:]:
                componentText = component.text if component.text is not None else ''
                text_out += component.elisionBefore + componentText
            return text_out

    @text.setter
    def text(self, newText: str):
        if self.isComposite:
            self.components = None
        self._text = newText

    @property
    def syllabic(self) -> SyllabicChoices:
        '''
        Returns or sets the syllabic property of a lyric.

        >>> fragment = note.Lyric('frag', syllabic='begin')
        >>> fragment.syllabic
        'begin'
        >>> fragment.rawText
        'frag-'
        >>> fragment.syllabic = 'end'
        >>> fragment.rawText
        '-frag'

        Illegal values raise a LyricException

        >>> fragment.syllabic = 'slide'
        Traceback (most recent call last):
        music21.note.LyricException: Syllabic value 'slide' is not in
            note.SYLLABIC_CHOICES, namely:
            [None, 'begin', 'single', 'end', 'middle', 'composite']
        '''
        if self.isComposite:
            return 'composite'
        else:
            return self._syllabic


    @syllabic.setter
    def syllabic(self, newSyllabic: SyllabicChoices):
        if newSyllabic not in SYLLABIC_CHOICES:
            raise LyricException(
                f'Syllabic value {newSyllabic!r} is not in '
                + f'note.SYLLABIC_CHOICES, namely: {SYLLABIC_CHOICES}'
            )
        self._syllabic = newSyllabic

    @property
    def identifier(self) -> str | int:
        '''
        By default, this is the same as self.number. However, if there is a
        descriptive identifier like 'part2verse1', it is stored here and
        will be different from self.number. When converting to musicXML,
        this property will be stored in the lyric 'number' attribute which
        can store a number or a descriptive identifier but not both.

        >>> l = note.Lyric()
        >>> l.number = 12
        >>> l.identifier
        12

        >>> l.identifier = 'Rainbow'
        >>> l.identifier
        'Rainbow'

        Default value is the same as default for number, that is, 1:

        >>> note.Lyric().identifier
        1
        '''
        if self._identifier is None:
            return self._number
        else:
            return self._identifier

    @identifier.setter
    def identifier(self, value: str | None):
        self._identifier = value

    @property
    def rawText(self) -> str:
        '''
        returns the text of the syllable with '-' etc.

        >>> l = note.Lyric('hel-')
        >>> l.text
        'hel'
        >>> l.rawText
        'hel-'

        >>> l = note.Lyric('lo', syllabic='end')
        >>> l.rawText
        '-lo'

        >>> l = note.Lyric('-ti-')
        >>> l.rawText
        '-ti-'

        >>> l = note.Lyric('bye')
        >>> l.rawText
        'bye'

        Composite lyrics take their endings from the first and last components:

        >>> composite = note.Lyric()
        >>> co = note.Lyric('co', syllabic='end')
        >>> e = note.Lyric('e', syllabic='single')
        >>> e.elisionBefore = '_'
        >>> composite.components = [co, e]
        >>> composite.rawText
        '-co_e'
        >>> e.syllabic = 'middle'
        >>> composite.rawText
        '-co_e-'
        '''
        text = self.text
        if not self.isComposite:
            syllabic = self.syllabic
            if syllabic == 'begin':
                return text + '-'
            elif syllabic == 'middle':
                return '-' + text + '-'
            elif syllabic == 'end':
                return '-' + text
            else:
                return text
        else:
            if t.TYPE_CHECKING:
                assert isinstance(self.components, Sequence), \
                    'Programming error: isComposite should assert components exists'  # for mypy
            firstSyllabic = self.components[0].syllabic
            lastSyllabic = self.components[-1].syllabic
            if firstSyllabic in ['middle', 'end']:
                text = '-' + text
            if lastSyllabic in ['begin', 'middle']:
                text += '-'
            return text


    @rawText.setter
    def rawText(self, rawTextIn: str):
        self.setTextAndSyllabic(rawTextIn, applyRaw=True)

    @property
    def number(self) -> int:
        '''
        This stores the number of the lyric (which determines the order
        lyrics appear in the score if there are multiple lyrics). Unlike
        the musicXML lyric number attribute, this value must always be a
        number; lyric order is always stored in this form. Descriptive
        identifiers like 'part2verse1' which can be found in the musicXML
        lyric number attribute should be stored in self.identifier.

        Default is 1

        >>> l = note.Lyric('Hi')
        >>> l.number
        1

        >>> l.number = 5
        >>> l.number
        5
        >>> l.number = None
        Traceback (most recent call last):
        music21.note.LyricException: Number best be number
        '''
        return self._number

    @number.setter
    def number(self, value: int) -> None:
        if not common.isInt(value):
            raise LyricException('Number best be number')
        self._number = value

    # PUBLIC METHODS #
    def setTextAndSyllabic(self, rawText: str, applyRaw: bool = False) -> None:
        '''
        Given a setting for rawText and applyRaw,
        sets the syllabic type for a lyric based on the rawText.  Useful for
        parsing raw text from, say, an OMR score.  Or just to quickly set text
        and syllabic.

        >>> l = note.Lyric()
        >>> l.setTextAndSyllabic('hel-')
        >>> l.text
        'hel'
        >>> l.syllabic
        'begin'
        >>> l.setTextAndSyllabic('-lo')
        >>> l.text
        'lo'
        >>> l.syllabic
        'end'
        >>> l.setTextAndSyllabic('the')
        >>> l.text
        'the'
        >>> l.syllabic
        'single'

        If applyRaw is True then this will assume you actually want hyphens
        in the text, and if syllabic is None, sets it to 'single'

        >>> l = note.Lyric()
        >>> l.setTextAndSyllabic('hel-', applyRaw=True)
        >>> l.text
        'hel-'
        >>> l.syllabic
        'single'

        If applyRaw is True, other syllabic settings except None are retained

        >>> l.syllabic = 'begin'
        >>> l.setTextAndSyllabic('-lo', applyRaw=True)
        >>> l.text
        '-lo'
        >>> l.syllabic
        'begin'

        This method wipes out components.
        '''
        # do not want to do this unless we are sure this is not a string
        # possible might alter unicode or other string-like representations
        if not isinstance(rawText, str):
            rawText = str(rawText)

        # check for hyphens
        if applyRaw is False and rawText.startswith('-') and not rawText.endswith('-'):
            self.text = rawText[1:]
            self.syllabic = 'end'
        elif applyRaw is False and not rawText.startswith('-') and rawText.endswith('-'):
            self.text = rawText[:-1]
            self.syllabic = 'begin'
        elif applyRaw is False and rawText.startswith('-') and rawText.endswith('-'):
            self.text = rawText[1:-1]
            self.syllabic = 'middle'
        else:  # assume single
            self.text = rawText
            if self.syllabic is None or not applyRaw:
                self.syllabic = 'single'


# ------------------------------------------------------------------------------


class GeneralNote(base.Music21Object):
    '''
    A GeneralNote object is the base class object
    for the :class:`~music21.note.Note`,
    :class:`~music21.note.Rest`, :class:`~music21.chord.Chord`,
    and related objects.

    Keywords can be passed to
    a GeneralNote which are then passed to the
    underlying :class:`~music21.duration.Duration`.
    These keywords might be listed like
    type='16th', dots=2 etc. to create a
    double-dotted sixteenth note.

    In almost every circumstance, you should
    create note.Note() or note.Rest() or chord.Chord()
    objects directly, and not use this underlying
    structure.

    >>> gn = note.GeneralNote(type='16th', dots=2)
    >>> gn.quarterLength
    0.4375

    **Equality**

    GeneralNote objects are equal if they pass superclass tests (e.g., their durations are equal),
    and they have the same articulation and expression classes (in any order),
    and their ties are equal.
    '''
    isNote = False
    isRest = False
    isChord = False
    _styleClass: type[style.Style] = style.NoteStyle
    equalityAttributes: tuple[str, ...] = ('tie',)

    # define order for presenting names in documentation; use strings
    _DOC_ORDER = ['duration', 'quarterLength']
    # documentation for all attributes (not properties or methods)
    _DOC_ATTR: dict[str, str] = {
        'isChord': 'Boolean read-only value describing if this object is a Chord.',
        'lyrics': 'A list of :class:`~music21.note.Lyric` objects.',
        'expressions': '''a list of expressions (such
            as :class:`~music21.expressions.Fermata`, etc.)
            that are stored on this Note.''',
        'articulations': '''a list of articulations such
            as :class:`~music21.articulations.Staccato`, etc.) that are stored on this Note.'''
    }

    def __init__(self,
                 *,
                 duration: Duration | None = None,
                 lyric: None | str | Lyric = None,
                 **keywords
                 ):
        if duration is None:
            # ensure music21base not automatically create a zero duration before we can.
            if not keywords or ('type' not in keywords and 'quarterLength' not in keywords):
                tempDuration = Duration(1.0)
            else:
                tempDuration = Duration(**keywords)
                if 'quarterLength' in keywords:
                    del keywords['quarterLength']
                if 'type' in keywords:
                    del keywords['type']
                # only apply default if components are empty
                # looking at currentComponents so as not to trigger
                # _updateComponents
                if (tempDuration.quarterLength == 0
                        and not tempDuration.currentComponents()):
                    tempDuration.quarterLength = 1.0
        else:
            tempDuration = duration
        # this sets the stored duration defined in Music21Object
        super().__init__(duration=tempDuration, **keywords)

        self.lyrics: list[Lyric] = []  # a list of lyric objects
        self.expressions: list[expressions.Expression] = []
        self.articulations: list[articulations.Articulation] = []

        if lyric is not None:
            self.addLyric(lyric)

        # note: Chords handle ties differently
        self._tie: tie.Tie | None = None  # store a Tie object

    def __eq__(self, other):
        if not super().__eq__(other):
            return False

        # note: tie is in equalityClasses, so already checked above.

        # Articulations are a list of Articulation objects.
        # Converting them to Set objects produces ordered cols that remove duplicates.
        # However, we must then convert to list to match based on class ==
        # not on class id().
        for search in 'articulations', 'expressions':
            my_art_express_classes = [type(x) for x in getattr(self, search)]
            other_art_express_classes = [type(x) for x in getattr(other, search)]
            if len(my_art_express_classes) != len(other_art_express_classes):
                return False
            if set(my_art_express_classes) != set(other_art_express_classes):
                return False

        return True

    def __hash__(self):
        return super().__hash__()

    # --------------------------------------------------------------------------
    @property
    def tie(self) -> tie.Tie | None:
        '''
        Return and set a :class:`~music21.note.Tie` object, or None.

        >>> n = note.Note()
        >>> n.tie is None
        True
        >>> n.tie = tie.Tie('start')
        '''
        return self._tie

    @tie.setter
    def tie(self, value: tie.Tie | None):
        self._tie = value

    def _getLyric(self) -> str | None:
        if not self.lyrics:
            return None

        allText = [ly.text for ly in self.lyrics]
        return '\n'.join([textStr for textStr in allText if textStr is not None])

    def _setLyric(self, value: str | Lyric | None) -> None:
        self.lyrics = []
        if value is None:
            return

        if isinstance(value, Lyric):
            self.lyrics.append(value)
            return

        if not isinstance(value, str):
            value = str(value)

        values = value.split('\n')
        for i, v in enumerate(values):
            self.lyrics.append(Lyric(v, number=i + 1))

    lyric = property(_getLyric,
                     _setLyric,
                     doc=r'''
        The lyric property can
        be used to get and set a lyric for this
        Note, Chord, or Rest. This is a simplified version of the more general
        :meth:`~music21.note.GeneralNote.addLyric` method.

        >>> a = note.Note('A4')
        >>> a.lyrics
        []
        >>> a.lyric = 'hel-'
        >>> a.lyric
        'hel'
        >>> a.lyrics
        [<music21.note.Lyric number=1 syllabic=begin text='hel'>]

        Eliminate Lyrics by setting a.lyric to None

        >>> a.lyric = None
        >>> a.lyric
        >>> a.lyrics
        []

        Set multiple lyrics with \n separated text:

        >>> a.lyric = '1. Hi\n2. Bye'
        >>> a.lyric
        '1. Hi\n2. Bye'
        >>> a.lyrics
        [<music21.note.Lyric number=1 syllabic=single text='1. Hi'>,
         <music21.note.Lyric number=2 syllabic=single text='2. Bye'>]


        You can also set a lyric with a lyric object directly:

        >>> b = note.Note('B5')
        >>> ly = note.Lyric('bon-')
        >>> b.lyric = ly
        >>> b.lyrics
        [<music21.note.Lyric number=1 syllabic=begin text='bon'>]
        >>> b.lyric
        'bon'

        * Changed in v6.7: added setting to a Lyric object.  Removed undocumented
          setting to False instead of setting to None
        ''')

    def addLyric(self,
                 text,
                 lyricNumber=None,
                 *,
                 applyRaw=False,
                 lyricIdentifier=None) -> None:
        '''
        Adds a lyric, or an additional lyric, to a Note, Chord, or Rest's lyric list.
        If `lyricNumber` is not None, a specific line of lyric text can be set.
        The lyricIdentifier can also be set.

        >>> n1 = note.Note()
        >>> n1.addLyric('hello')
        >>> n1.lyrics[0].text
        'hello'
        >>> n1.lyrics[0].number
        1

        An added option gives the lyric number, not the list position

        >>> n1.addLyric('bye', 3)
        >>> n1.lyrics[1].text
        'bye'
        >>> n1.lyrics[1].number
        3
        >>> for lyr in n1.lyrics:
        ...     print(lyr.text)
        hello
        bye

        Replace an existing lyric by specifying the same number:

        >>> n1.addLyric('ciao', 3)
        >>> n1.lyrics[1].text
        'ciao'
        >>> n1.lyrics[1].number
        3

        Giving a lyric with a hyphen at either end will set whether it
        is part of a multisyllable word:

        >>> n1.addLyric('good-')
        >>> n1.lyrics[2].text
        'good'
        >>> n1.lyrics[2].syllabic
        'begin'

        This feature can be overridden by specifying the keyword only argument "applyRaw=True":

        >>> n1.addLyric('-5', applyRaw=True)
        >>> n1.lyrics[3].text
        '-5'
        >>> n1.lyrics[3].syllabic
        'single'
        '''
        if not isinstance(text, str):
            text = str(text)
        if lyricNumber is None:
            maxLyrics = len(self.lyrics) + 1
            self.lyrics.append(Lyric(text, maxLyrics,
                                     applyRaw=applyRaw, identifier=lyricIdentifier))
        else:
            foundLyric = False
            for thisLyric in self.lyrics:
                if thisLyric.number == lyricNumber:
                    thisLyric.text = text
                    foundLyric = True
                    break
            if foundLyric is False:
                self.lyrics.append(Lyric(text, lyricNumber,
                                         applyRaw=applyRaw, identifier=lyricIdentifier))

    def insertLyric(self, text, index=0, *, applyRaw=False, identifier=None):
        '''
        Inserts a lyric into the Note, Chord, or Rest's lyric list in front of
        the index specified (0 by default), using index + 1 as the inserted lyric's
        line number. shifts line numbers of all following lyrics in list

        >>> n1 = note.Note()
        >>> n1.addLyric('second')
        >>> n1.lyrics
        [<music21.note.Lyric number=1 syllabic=single text='second'>]
        >>> n1.insertLyric('first', 0)
        >>> n1.lyrics
        [<music21.note.Lyric number=1 syllabic=single text='first'>,
         <music21.note.Lyric number=2 syllabic=single text='second'>]

        OMIT_FROM_DOCS

        test inserting in the middle.

        >>> n1.insertLyric('newSecond', 1)
        >>> n1.lyrics
        [<music21.note.Lyric number=1 syllabic=single text='first'>,
         <music21.note.Lyric number=2 syllabic=single text='newSecond'>,
         <music21.note.Lyric number=3 syllabic=single text='second'>]

        Test number as lyric...

        >>> n1.insertLyric(0, 3)
        >>> n1.lyrics
        [<music21.note.Lyric number=1 syllabic=single text='first'>,
         <music21.note.Lyric number=2 syllabic=single text='newSecond'>,
         <music21.note.Lyric number=3 syllabic=single text='second'>,
         <music21.note.Lyric number=4 syllabic=single text='0'>]
        '''
        if not isinstance(text, str):
            text = str(text)
        for lyric in self.lyrics[index:]:
            lyric.number += 1
        self.lyrics.insert(index, Lyric(text, (index + 1),
                                        applyRaw=applyRaw, identifier=identifier))

    # --------------------------------------------------------------------------
    # properties common to Notes, Rests, etc.

    @property
    def fullName(self) -> str:
        return self.classes[0]  # override in subclasses

    @property
    def pitches(self) -> tuple[Pitch, ...]:
        '''
        Returns an empty tuple.  (Useful for iterating over NotRests since they
        include Notes and Chords.)
        '''
        return ()

    @pitches.setter
    def pitches(self, _value: Iterable[Pitch]):
        pass


    # --------------------------------------------------------------------------
    def augmentOrDiminish(self, scalar, *, inPlace=False):
        '''
        Given a scalar greater than zero, return a Note with a scaled Duration.
        If `inPlace` is True, this is done in-place and the method returns None.
        If `inPlace` is False [default], this returns a modified deepcopy.

        * Changed in v5: inPlace is now False.

        >>> n = note.Note('g#')
        >>> n.quarterLength = 3
        >>> n.augmentOrDiminish(2, inPlace=True)
        >>> n.quarterLength
        6.0

        >>> c = chord.Chord(['g#', 'a#', 'd'])
        >>> c.quarterLength = 2
        >>> c.augmentOrDiminish(0.25, inPlace=True)
        >>> c.quarterLength
        0.5

        >>> n = note.Note('g#')
        >>> n.augmentOrDiminish(-1)
        Traceback (most recent call last):
        music21.note.NoteException: scalar must be greater than zero

        >>> n = note.Note()
        >>> n.quarterLength = 3
        >>> n2 = n.augmentOrDiminish(1/3, inPlace=False)
        >>> n2.quarterLength
        1.0
        >>> n.quarterLength
        3.0
        '''
        if not scalar > 0:
            raise NoteException('scalar must be greater than zero')

        if inPlace:
            post = self
        else:  # slight speedup could happen by setting duration to Zero before copying.
            post = copy.deepcopy(self)

        # this is never True.
        post.duration = post.duration.augmentOrDiminish(scalar)

        if not inPlace:
            return post
        else:
            return None

    # --------------------------------------------------------------------------
    def getGrace(self, *, appoggiatura=False, inPlace=False):
        '''
        Return a grace version of this GeneralNote

        >>> n = note.Note('G4', quarterLength=2)
        >>> n.duration.quarterLength
        2.0
        >>> n.duration.isGrace
        False
        >>> n.duration
        <music21.duration.Duration 2.0>
        >>> n.duration.type
        'half'
        >>> n.duration.components
        (DurationTuple(type='half', dots=0, quarterLength=2.0),)

        >>> ng = n.getGrace()
        >>> ng.duration.quarterLength
        0.0
        >>> ng.duration.isGrace
        True
        >>> ng.duration
        <music21.duration.GraceDuration unlinked type:half quarterLength:0.0>
        >>> ng.duration.type
        'half'
        >>> ng.duration.components
        (DurationTuple(type='half', dots=0, quarterLength=0.0),)

        Appoggiaturas are still a work in progress...
        * Changed in v6: corrected spelling of `appoggiatura` keyword.

        >>> ng2 = n.getGrace(appoggiatura=True)
        >>> ng2.duration
        <music21.duration.AppoggiaturaDuration unlinked type:half quarterLength:0.0>
        >>> ng2.duration.slash
        False

        Set inPlace to True to change the duration element on the Note.  This can have
        negative consequences if the Note is in a stream.

        >>> r = note.Rest(quarterLength=0.5)
        >>> r.getGrace(inPlace=True)
        >>> r.duration
        <music21.duration.GraceDuration unlinked type:eighth quarterLength:0.0>
        '''
        if inPlace is False:
            e = copy.deepcopy(self)
        else:
            e = self

        e.duration = e.duration.getGraceDuration(appoggiatura=appoggiatura)

        if inPlace is False:
            return e


# ------------------------------------------------------------------------------
class NotRest(GeneralNote):
    '''
    Parent class for Note-like objects that are not rests; that is to say
    they have a stem, can be tied, and volume is important.
    Basically, that's a :class:`Note` or :class:`~music21.chord.Chord`
    (or their subclasses such as :class:`~music21.harmony.ChordSymbol`), or
    :class:`Unpitched` object.
    '''
    # unspecified means that there may be a stem, but its orientation
    # has not been declared.

    _DOC_ATTR: dict[str, str] = {
        'beams': '''
            A :class:`~music21.beam.Beams` object that contains
            information about the beaming of this note.''',
    }

    # Should volume be here too?  and _chordAttached?
    equalityAttributes: tuple[str, ...] = (
        'notehead', 'noteheadFill', 'noteheadParenthesis', 'beams'
    )

    def __init__(self,
                 beams: beam.Beams | None = None,
                 **keywords):
        super().__init__(**keywords)
        self._notehead: str = 'normal'
        self._noteheadFill: bool | None = None
        self._noteheadParenthesis: bool = False
        self._stemDirection: str = 'unspecified'
        self._volume: volume.Volume | None = None  # created on demand
        if beams is not None:
            self.beams = beams
        else:
            self.beams = beam.Beams()
        self._storedInstrument: instrument.Instrument | None = None
        self._chordAttached: chord.ChordBase | None = None

    # ==============================================================================================
    # Special functions
    # ==============================================================================================

    def _deepcopySubclassable(self: _NotRestType,
                              memo: dict[int, t.Any] | None = None,
                              *,
                              ignoreAttributes: set[str] | None = None) -> _NotRestType:
        new = super()._deepcopySubclassable(memo, ignoreAttributes={'_chordAttached'})
        if t.TYPE_CHECKING:
            new = t.cast(_NotRestType, new)
        # let the chord restore _chordAttached

        # after copying, if a Volume exists, it is linked to the old object
        # look at _volume so as not to create object if not already there
        if self.hasVolumeInformation():
            new.volume.client = new  # update with new instance
        return new

    def __deepcopy__(self, memo=None):
        '''
        As NotRest objects have a Volume, objects, and Volume objects
        store refs to the client object, need to specialize deepcopy handling

        >>> import copy
        >>> n = note.NotRest()
        >>> n.volume = volume.Volume(50)
        >>> m = copy.deepcopy(n)
        >>> m.volume.client is m
        True
        >>> n.volume.client is n
        True
        '''
        # environLocal.printDebug(['calling NotRest.__deepcopy__', self])
        return self._deepcopySubclassable(memo=memo)

    def _getStemDirection(self) -> str:
        return self._stemDirection

    def _setStemDirection(self, direction):
        if direction is None:
            direction = 'unspecified'  # allow setting to None meaning
        elif direction == 'none':
            direction = 'noStem'  # allow setting to none or None
        elif direction not in stemDirectionNames:
            raise NotRestException(f'not a valid stem direction name: {direction}')
        self._stemDirection = direction

    stemDirection = property(_getStemDirection,
                             _setStemDirection,
                             doc='''
        Get or set the stem direction of this NotRest object.
        Valid stem direction names are found in note.stemDirectionNames (see below).

        >>> note.stemDirectionNames
        ('double', 'down', 'noStem', 'none', 'unspecified', 'up')
        >>> n = note.Note()

        By default, a Note's stemDirection is 'unspecified'
        meaning that it is unknown:

        >>> n.stemDirection
        'unspecified'

        >>> n.stemDirection = 'noStem'
        >>> n.stemDirection
        'noStem'

        The alias 'none' (the string) is the same as 'noStem'

        >>> n.stemDirection = 'none'
        >>> n.stemDirection
        'noStem'

        >>> n.stemDirection = 'junk'
        Traceback (most recent call last):
        music21.note.NotRestException: not a valid stem direction name: junk

        Stem direction can be set explicitly to None to remove
        any prior stem information, same as 'unspecified':

        >>> n.stemDirection = None
        >>> n.stemDirection
        'unspecified'
        ''')

    @property
    def notehead(self) -> str:
        '''
        Get or set the notehead type of this NotRest object.
        Valid notehead type names are found in note.noteheadTypeNames (see below):


        >>> note.noteheadTypeNames
        ('arrow down', 'arrow up', 'back slashed', 'circle dot', 'circle-x', 'circled', 'cluster',
         'cross', 'diamond', 'do', 'fa', 'inverted triangle', 'la', 'left triangle',
         'mi', 'none', 'normal', 'other', 're', 'rectangle', 'slash', 'slashed', 'so',
         'square', 'ti', 'triangle', 'x')
        >>> n = note.Note()
        >>> n.notehead = 'diamond'
        >>> n.notehead
        'diamond'

        >>> n.notehead = 'junk'
        Traceback (most recent call last):
        music21.note.NotRestException: not a valid notehead type name: 'junk'
        '''
        return self._notehead

    @notehead.setter
    def notehead(self, value):
        if value in ('none', None, ''):
            value = None  # allow setting to none or None
        elif value not in noteheadTypeNames:
            raise NotRestException(f'not a valid notehead type name: {value!r}')
        self._notehead = value

    @property
    def noteheadFill(self) -> bool | None:
        '''
        Get or set the note head fill status of this NotRest. Valid note head fill values are
        True, False, or None (meaning default).  "yes" and "no" are converted to True
        and False.

        >>> n = note.Note()
        >>> n.noteheadFill = 'no'
        >>> n.noteheadFill
        False
        >>> n.noteheadFill = 'filled'
        >>> n.noteheadFill
        True

        >>> n.noteheadFill = 'jelly'
        Traceback (most recent call last):
        music21.note.NotRestException: not a valid notehead fill value: 'jelly'
        '''
        return self._noteheadFill

    @noteheadFill.setter
    def noteheadFill(self, value: bool | None | str):
        boolValue: bool | None
        if value in ('none', None, 'default'):
            boolValue = None  # allow setting to none or None
        elif value in (True, 'filled', 'yes'):
            boolValue = True
        elif value in (False, 'notfilled', 'no'):
            boolValue = False
        else:
            raise NotRestException(f'not a valid notehead fill value: {value!r}')
        self._noteheadFill = boolValue

    @property
    def noteheadParenthesis(self) -> bool:
        '''
        Get or set the note head parentheses for this Note/Unpitched/Chord object.

        >>> n = note.Note()
        >>> n.noteheadParenthesis
        False
        >>> n.noteheadParenthesis = True
        >>> n.noteheadParenthesis
        True

        'yes' or 1 equate to True; 'no' or 0 to False

        >>> n.noteheadParenthesis = 'no'
        >>> n.noteheadParenthesis
        False

        Anything else raises an exception:

        >>> n.noteheadParenthesis = 'blah'
        Traceback (most recent call last):
        music21.note.NotRestException: notehead parentheses must be True or False, not 'blah'
        '''
        return self._noteheadParenthesis

    @noteheadParenthesis.setter
    def noteheadParenthesis(self, value: bool | str | int):
        boolValue: bool
        if value in (True, 'yes', 1):
            boolValue = True
        elif value in (False, 'no', 0):
            boolValue = False
        else:
            raise NotRestException(f'notehead parentheses must be True or False, not {value!r}')
        self._noteheadParenthesis = boolValue

    # --------------------------------------------------------------------------
    def hasVolumeInformation(self) -> bool:
        '''
        Returns bool whether volume was set -- saving some time for advanced
        users (such as MusicXML exporters) that only want to look at the volume
        if it is already there.

        >>> n = note.Note()
        >>> n.hasVolumeInformation()
        False
        >>> n.volume
         <music21.volume.Volume realized=0.71>
        >>> n.hasVolumeInformation()
        True
        '''
        if self._volume is None:
            return False
        else:
            return True

    def _getVolume(self,
                   forceClient: NotRest | None = None
                   ) -> volume.Volume:
        # DO NOT CHANGE TO @property because of optional attributes
        # lazy volume creation.  property is set below.
        if self._volume is None:
            if forceClient is None:
                # when creating the volume object, set the client as self
                self._volume = volume.Volume(client=self)
            else:
                self._volume = volume.Volume(client=forceClient)

        volume_out = self._volume
        if t.TYPE_CHECKING:
            assert volume_out is not None

        return volume_out

    def _setVolume(self, value: None | volume.Volume | int | float, setClient=True):
        # DO NOT CHANGE TO @property because of optional attributes
        # setClient is only False when Chords are bundling Notes.
        if value is None:
            self._volume = None
        elif isinstance(value, volume.Volume):
            if setClient:
                if value.client is not None:
                    value = copy.deepcopy(value)
                value.client = self  # set to self
            self._volume = value
        elif common.isNum(value) and setClient:
            # if we can define the client, we can set from numbers
            # call local getVolume will set client appropriately
            vol = self._getVolume()
            if value < 1:  # assume a scalar
                vol.velocityScalar = value
            else:  # assume velocity
                vol.velocity = value

        else:
            raise TypeError(f'this must be a Volume object, not {value}')

    @property
    def volume(self) -> volume.Volume:
        '''
        Get and set the :class:`~music21.volume.Volume` object of this object.
        Volume objects are created on demand.

        >>> n1 = note.Note()
        >>> n1.volume.velocity = 120
        >>> n2 = note.Note()
        >>> n2.volume = 80  # can directly set a velocity value
        >>> s = stream.Stream()
        >>> s.append([n1, n2])
        >>> [n.volume.velocity for n in s.notes]
        [120, 80]
        '''
        return self._getVolume()

    @volume.setter
    def volume(self, value: None | volume.Volume | int | float):
        self._setVolume(value)

    def _getStoredInstrument(self):
        return self._storedInstrument

    def _setStoredInstrument(self, newValue):
        if not (hasattr(newValue, 'instrumentId') or newValue is None):
            raise TypeError(f'Expected Instrument; got {type(newValue)}')
        self._storedInstrument = newValue

    storedInstrument = property(_getStoredInstrument,
                                _setStoredInstrument,
                                doc='''
        Get and set the :class:`~music21.instrument.Instrument` that
        should be used to play this note, overriding whatever
        Instrument object may be active in the Stream. (See
        :meth:`getInstrument` for a means of retrieving `storedInstrument`
        if available before falling back to a context search to find
        the active instrument.)
        ''')

    @overload
    def getInstrument(self,
                      *,
                      returnDefault: t.Literal[True] = True
                      ) -> instrument.Instrument:
        from music21 import instrument
        return instrument.Instrument()  # astroid #1015

    @overload
    def getInstrument(self,
                      *,
                      returnDefault: t.Literal[False]
                      ) -> instrument.Instrument | None:
        return None  # astroid #1015

    def getInstrument(self,
                      *,
                      returnDefault: bool = True
                      ) -> instrument.Instrument | None:
        '''
        Retrieves the `.storedInstrument` on this `NotRest` instance, if any.
        If one is not found, executes a context search (without following
        derivations) to find the closest (i.e., active) instrument in the
        stream hierarchy.

        Returns a default instrument if no instrument is found in the context
        and `returnDefault` is True (default).

        >>> n = note.Note()
        >>> m = stream.Measure([n])
        >>> n.getInstrument(returnDefault=False) is None
        True
        >>> dulcimer = instrument.Dulcimer()
        >>> m.insert(0, dulcimer)
        >>> n.getInstrument() is dulcimer
        True

        Overridden `.storedInstrument` is privileged:

        >>> picc = instrument.Piccolo()
        >>> n.storedInstrument = picc
        >>> n.getInstrument() is picc
        True

        Instruments in containing streams ARE found:

        >>> n.storedInstrument = None
        >>> m.remove(dulcimer)
        >>> p = stream.Part([m])
        >>> p.insert(0, dulcimer)
        >>> n.getInstrument() is dulcimer
        True

        But not if the instrument is only found in a derived stream:

        >>> derived = p.stripTies()
        >>> p.remove(dulcimer)
        >>> derived.getInstruments().first()
        <music21.instrument.Dulcimer 'Dulcimer'>
        >>> n.getInstrument(returnDefault=False) is None
        True

        Electing to return a default generic `Instrument`:

        >>> n.getInstrument(returnDefault=True)
        <music21.instrument.Instrument ''>
        '''
        from music21 import instrument
        if self.storedInstrument is not None:
            return self.storedInstrument
        instrument_or_none = self.getContextByClass(
            instrument.Instrument, followDerivation=False)
        if returnDefault and instrument_or_none is None:
            return instrument.Instrument()
        elif instrument_or_none is None:
            return None
        return t.cast(instrument.Instrument, instrument_or_none)


# ------------------------------------------------------------------------------
class Note(NotRest):
    '''
    One of the most important music21 classes, a Note
    stores a single note (that is, not a rest or an unpitched element)
    that can be represented by one or more notational units -- so
    for instance a C quarter-note and a D# eighth-tied-to-32nd are both
    a single Note object.

    A Note knows both its total duration and how to express itself as a set of
    tied notes of different lengths. For instance, a note of 2.5 quarters in
    length could be half tied to eighth or dotted quarter tied to quarter.

    The first argument to the Note is the pitch name (with or without
    octave, see the introduction to :class:`music21.pitch.Pitch`).
    Further arguments can be specified as keywords (such as type, dots, etc.)
    and are passed to the underlying :class:`music21.duration.Duration` element.

    >>> n = note.Note()
    >>> n
    <music21.note.Note C>
    >>> n.pitch
    <music21.pitch.Pitch C4>

    >>> n = note.Note('B-')
    >>> n.name
    'B-'
    >>> n.octave is None
    True
    >>> n.pitch.implicitOctave
    4

    >>> n = note.Note(name='D#')
    >>> n.name
    'D#'
    >>> n = note.Note(nameWithOctave='D#5')
    >>> n.nameWithOctave
    'D#5'

    Other ways of instantiating a Pitch object, such as by MIDI number or pitch class
    are also possible:

    >>> note.Note(64).nameWithOctave
    'E4'

    All keyword args that are valid for Duration or Pitch objects
    are valid (as well as those for superclasses, NotRest, GeneralNote,
    Music21Object):

    >>> n = note.Note(step='C', accidental='sharp', octave=2, id='csharp', type='eighth', dots=2)
    >>> n.nameWithOctave
    'C#2'
    >>> n.duration
    <music21.duration.Duration 0.875>

    **Equality and ordering**

    Two notes are equal if they pass all the equality tests for NotRest and their
    pitches are equal.

    Attributes that might change based on the wider context
    of a note (such as offset) are not compared. This test does not look at lyrics in
    establishing equality.  (It may in the future.)

    >>> note.Note('C4') == note.Note('C4')
    True

    Enharmonics are not equal:

    >>> note.Note('D#4') == note.Note('E-4')
    False

    >>> note.Note('C4', type='half') == note.Note('C4', type='quarter')
    False

    Notes, like pitches, also have an ordering based on their pitches.

    >>> highE = note.Note('E5')
    >>> lowF = note.Note('F2')
    >>> otherHighE = note.Note('E5')

    >>> highE > lowF
    True
    >>> highE < lowF
    False
    >>> highE >= otherHighE
    True
    >>> highE <= otherHighE
    True

    Notice you cannot compare Notes w/ ints or anything that does not a have a
    `.pitch` attribute.

    >>> highE < 50
    Traceback (most recent call last):
    TypeError: '<' not supported between instances of 'Note' and 'int'

    Note also that two objects can be >= and <= without being equal, because
    only pitch-height is being compared in <, <=, >, >= but duration and other
    elements are compared in equality.

    >>> otherHighE.duration.type = 'whole'

    Now otherHighE is != highE

    >>> highE == otherHighE
    False

    But it is both >= and <= it:

    >>> highE >= otherHighE
    True
    >>> highE <= otherHighE
    True

    (The pigeonhole principle police have a bounty out on my head for this.)
    '''
    isNote = True
    equalityAttributes: tuple[str, ...] = ('pitch',)

    # Defines the order of presenting names in the documentation; use strings
    _DOC_ORDER = ['duration', 'quarterLength', 'nameWithOctave']
    # documentation for all attributes (not properties or methods)
    _DOC_ATTR: dict[str, str] = {
        'isNote': 'Boolean read-only value describing if this Note is a Note (True).',
        'isRest': 'Boolean read-only value describing if this Note is a Rest (False).',
        'pitch': '''A :class:`~music21.pitch.Pitch` object containing all the
                information about the note's pitch.  Many `.pitch` properties and
                methods are also made `Note` properties also''',
    }

    # Accepts an argument for pitch
    def __init__(self,
                 pitch: str | int | Pitch | None = None,
                 *,
                 name: str | None = None,
                 nameWithOctave: str | None = None,
                 **keywords):
        super().__init__(**keywords)
        self._chordAttached: chord.Chord | None

        if pitch is not None:
            if isinstance(pitch, Pitch):
                self.pitch = pitch
            else:  # assume first argument is pitch
                self.pitch = Pitch(pitch, **keywords)
        else:  # supply a default pitch
            if nameWithOctave is not None:
                name = nameWithOctave
            elif not name:
                name = 'C4'
            self.pitch = Pitch(name, **keywords)

        # noinspection PyProtectedMember
        self.pitch._client = self

    # --------------------------------------------------------------------------
    # operators, representations, and transformations

    def _reprInternal(self):
        return self.name


    def __lt__(self, other):
        try:
            return self.pitch < other.pitch
        except AttributeError:
            return NotImplemented

    # do not factor out into @total_ordering because of the difference between __eq__ and
    # the equal part of __le__ and __ge__
    def __gt__(self, other):
        try:
            return self.pitch > other.pitch
        except AttributeError:
            return NotImplemented

    def __le__(self, other):
        try:
            return self.pitch <= other.pitch
        except AttributeError:
            return NotImplemented

    def __ge__(self, other):
        try:
            return self.pitch >= other.pitch
        except AttributeError:
            return NotImplemented

    def __deepcopy__(self: Note, memo=None) -> Note:
        '''
        After doing a deepcopy of the pitch, be sure to set the client
        '''
        new = self._deepcopySubclassable(memo)
        # noinspection PyProtectedMember
        new.pitch._client = new  # pylint: disable=no-member
        return new

    # --------------------------------------------------------------------------
    # property access

    def _getName(self) -> str:
        return self.pitch.name

    def _setName(self, value: str):
        self.pitch.name = value

    name = property(_getName,
                    _setName,
                    doc='''
        Return or set the pitch name from the :class:`~music21.pitch.Pitch` object.
        See `Pitch`'s attribute :attr:`~music21.pitch.Pitch.name`.
        ''')

    def _getNameWithOctave(self) -> str:
        return self.pitch.nameWithOctave

    def _setNameWithOctave(self, value: str):
        self.pitch.nameWithOctave = value

    nameWithOctave = property(_getNameWithOctave,
                              _setNameWithOctave,
                              doc='''
        Return or set the pitch name with octave from the :class:`~music21.pitch.Pitch` object.
        See `Pitch`'s attribute :attr:`~music21.pitch.Pitch.nameWithOctave`.
        ''')

    @property
    def step(self) -> StepName:
        '''
        Return or set the pitch step from the :class:`~music21.pitch.Pitch` object.
        See :attr:`~music21.pitch.Pitch.step`.
        '''
        return self.pitch.step

    @step.setter
    def step(self, value: StepName):
        self.pitch.step = value

    def _getOctave(self) -> int | None:
        return self.pitch.octave

    def _setOctave(self, value: int | None):
        self.pitch.octave = value

    octave = property(_getOctave,
                      _setOctave,
                      doc='''
        Return or set the octave value from the :class:`~music21.pitch.Pitch` object.
        See :attr:`~music21.pitch.Pitch.octave`.
        ''')

    @property
    def pitches(self) -> tuple[Pitch, ...]:
        '''
        Return the single :class:`~music21.pitch.Pitch` object in a tuple.
        This property is designed to provide an interface analogous to
        that found on :class:`~music21.chord.Chord` so that `[c.pitches for c in s.notes]`
        provides a consistent interface for all objects.

        >>> n = note.Note('g#')
        >>> n.nameWithOctave
        'G#'
        >>> n.pitches
        (<music21.pitch.Pitch G#>,)

        Since this is a Note, not a chord, from the list or tuple,
        only the first one will be used:

        >>> n.pitches = [pitch.Pitch('c2'), pitch.Pitch('g2')]
        >>> n.nameWithOctave
        'C2'
        >>> n.pitches
        (<music21.pitch.Pitch C2>,)

        The value for setting must be a list or tuple:

        >>> n.pitches = pitch.Pitch('C4')
        Traceback (most recent call last):
        music21.note.NoteException: cannot set pitches with provided object: C4

        For setting a single one, use `n.pitch` instead.

        Don't use strings, or you will get a string back!

        >>> n.pitches = ('C4', 'D4')
        >>> n.pitch
        'C4'
        >>> n.pitch.diatonicNoteNum
        Traceback (most recent call last):
        AttributeError: 'str' object has no attribute 'diatonicNoteNum'
        '''
        return (self.pitch,)

    @pitches.setter
    def pitches(self, value: Sequence[Pitch]):
        if common.isListLike(value) and value:
            self.pitch = value[0]
        else:
            raise NoteException(f'cannot set pitches with provided object: {value}')

    def transpose(self, value, *, inPlace=False):
        '''
        Transpose the Note by the user-provided
        value. If the value is an integer, the transposition is treated in half steps.

        If the value is a string, any Interval string specification can be provided.

        >>> a = note.Note('g4')
        >>> b = a.transpose('m3')
        >>> b
        <music21.note.Note B->
        >>> aInterval = interval.Interval(-6)
        >>> b = a.transpose(aInterval)
        >>> b
        <music21.note.Note C#>

        >>> c = b.transpose(interval.GenericInterval(2))
        >>> c
        <music21.note.Note D#>

        >>> a.transpose(aInterval, inPlace=True)
        >>> a
        <music21.note.Note C#>


        If the transposition value is an integer, take the KeySignature or Key context
        into account...

        >>> s = stream.Stream()
        >>> s.append(key.Key('D'))
        >>> s.append(note.Note('F'))
        >>> s.append(key.Key('b-', 'minor'))
        >>> s.append(note.Note('F'))
        >>> s.show('text')
        {0.0} <music21.key.Key of D major>
        {0.0} <music21.note.Note F>
        {1.0} <music21.key.Key of b- minor>
        {1.0} <music21.note.Note F>
        >>> for n in s.notes:
        ...     n.transpose(1, inPlace=True)
        >>> s.show('text')
        {0.0} <music21.key.Key of D major>
        {0.0} <music21.note.Note F#>
        {1.0} <music21.key.Key of b- minor>
        {1.0} <music21.note.Note G->

        '''
        from music21 import key
        if isinstance(value, interval.IntervalBase):
            intervalObj = value
        else:  # try to process
            intervalObj = interval.Interval(value)

        if not inPlace:
            post = copy.deepcopy(self)
        else:
            post = self

        # use inPlace, b/c if we are inPlace, we operate on self;
        # if we are not inPlace, post is a copy
        post.pitch.transpose(intervalObj, inPlace=True)
        if (post.pitch.accidental is not None
                and isinstance(value, (int, interval.ChromaticInterval))):
            ksContext = self.getContextByClass(key.KeySignature)
            if ksContext is not None:
                for alteredPitch in ksContext.alteredPitches:
                    if (post.pitch.pitchClass == alteredPitch.pitchClass
                            and post.pitch.accidental.alter != alteredPitch.accidental.alter):
                        post.pitch.getEnharmonic(inPlace=True)

        if not inPlace:
            post.derivation.method = 'transpose'
            return post
        else:
            return None

    @property
    def fullName(self) -> str:
        '''
        Return the most complete representation of this Note,
        providing duration and pitch information.


        >>> n = note.Note('A-', quarterLength=1.5)
        >>> n.fullName
        'A-flat Dotted Quarter Note'

        >>> n = note.Note('E~3', quarterLength=2)
        >>> n.fullName
        'E-half-sharp in octave 3 Half Note'

        >>> n = note.Note('D', quarterLength=0.25)
        >>> n.pitch.microtone = 25
        >>> n.fullName
        'D (+25c) 16th Note'
        '''
        msg = []
        msg.append(self.pitch.fullName + ' ')
        msg.append(self.duration.fullName)
        msg.append(' Note')
        return ''.join(msg)

    def pitchChanged(self):
        '''
        Called by the underlying pitch if something changed there.
        '''
        self._cache = {}
        if self._chordAttached is not None:
            self._chordAttached.clearCache()

# ------------------------------------------------------------------------------
# convenience classes


# ------------------------------------------------------------------------------
class Unpitched(NotRest):
    '''
    A General class of unpitched objects which appear at different places
    on the staff.  Examples: percussion notation.

    >>> unp = note.Unpitched()

    Unpitched elements have :attr:`displayStep` and :attr:`displayOctave`,
    which shows where they should be displayed as if the staff were a
    5-line staff in treble clef, but they do not have pitch
    objects:

    >>> unp.displayStep
    'B'
    >>> unp.displayOctave
    4
    >>> unp.displayStep = 'G'
    >>> unp.pitch
    Traceback (most recent call last):
    AttributeError: 'Unpitched' object has no attribute 'pitch'
    '''

    equalityAttributes = ('displayStep', 'displayOctave')

    def __init__(
        self,
        displayName: str | None = None,
        **keywords
    ):
        super().__init__(**keywords)
        self._chordAttached: percussion.PercussionChord | None = None

        self.displayStep: StepName = 'B'
        self.displayOctave: int = 4
        if displayName:
            display_pitch = Pitch(displayName)
            self.displayStep = display_pitch.step
            self.displayOctave = display_pitch.implicitOctave

    def _getStoredInstrument(self):
        return self._storedInstrument

    def _setStoredInstrument(self, newValue):
        self._storedInstrument = newValue

    storedInstrument = property(_getStoredInstrument, _setStoredInstrument)

    def displayPitch(self) -> Pitch:
        '''
        returns a pitch object that is the same as the displayStep and displayOctave.
        it will never have an accidental.

        >>> unp = note.Unpitched()
        >>> unp.displayStep = 'E'
        >>> unp.displayOctave = 4
        >>> unp.displayPitch()
        <music21.pitch.Pitch E4>
        '''
        return Pitch(step=self.displayStep, octave=self.displayOctave)

    @property
    def displayName(self) -> str:
        '''
        Returns the `nameWithOctave` of the :meth:`displayPitch`.

        >>> unp = note.Unpitched('B2')
        >>> unp.displayName
        'B2'
        '''
        display_pitch = self.displayPitch()
        return display_pitch.nameWithOctave


# ------------------------------------------------------------------------------
class Rest(GeneralNote):
    '''
    Rests are represented in music21 as GeneralNote objects that do not have
    a pitch object attached to them.  By default, they have length 1.0 (Quarter Rest)

    Calling :attr:`~music21.stream.Stream.notes` on a Stream does not get rests.
    However, the property :attr:`~music21.stream.Stream.notesAndRests` of Streams
    gets rests as well.

    >>> r = note.Rest()
    >>> r.isRest
    True
    >>> r.isNote
    False
    >>> r.duration.quarterLength = 2.0
    >>> r.duration.type
    'half'

    All Rests have the name property 'rest':

    >>> r.name
    'rest'

    And their .pitches is an empty tuple

    >>> r.pitches
    ()


    All arguments to Duration are valid in constructing:

    >>> r2 = note.Rest(type='whole')
    >>> r2.duration.quarterLength
    4.0

    Or they can just be specified in without a type, and they'll be evaluated automatically

    >>> r3, r4 = note.Rest('half'), note.Rest(2.0)
    >>> r3 == r4
    True
    >>> r3.duration.quarterLength
    2.0

    Two rests are considered equal if their durations are equal.

    >>> r1 = note.Rest('quarter')
    >>> r2 = note.Rest('quarter')
    >>> r1 == r2
    True
    >>> r1 != r2
    False

    >>> r2.duration.quarterLength = 4/3
    >>> r1 == r2
    False

    A rest is never equal to a note.

    >>> r1 == note.Note()
    False
    '''
    isRest = True
    name = 'rest'

    _DOC_ATTR: dict[str, str] = {
        'isNote': 'Boolean read-only value describing if this Rest is a Note (False).',
        'isRest': 'Boolean read-only value describing if this Rest is a Rest (True, obviously).',
        'name': '''returns "rest" always.  It is here so that you can get
               `x.name` on all `.notesAndRests` objects''',
        'stepShift': 'number of lines/spaces to shift the note upwards or downwards for display.',
        'fullMeasure': '''does this rest last a full measure or if it does, should it display
                itself as whole rest (or breve rest) and centered.

                Options are "auto" (default), False, True, and "always"

                "auto" is the default, where if the rest value happens to match the current
                time signature context (and there is no pickup or other padding),
                then display it as a whole rest, centered, etc. otherwise will display normally.

                False means do not display the rest as full measure whole rest,
                no matter what.  This setting is often used by composers in very small time
                signatures such as 1/8, where a whole rest can look incongruous.

                True keeps the set duration, but will always display as a full measure rest
                even if it's not the length of the measure
                (generally a whole note unless the time signature is very long).

                "always" means that on export, the duration will (EVENTUALLY, not yet!)
                update automatically to match the time signature context and always display
                as a whole rest. "always" does not work yet -- functions as True.

                See examples in :meth:`music21.musicxml.m21ToXml.MeasureExporter.restToXml`
                ''',
    }

    def __init__(self,
                 length: str | OffsetQLIn | None = None,
                 *,
                 stepShift: int = 0,
                 fullMeasure: t.Literal[True, False, 'auto', 'always'] = 'auto',
                 **keywords):
        if length is not None:
            if isinstance(length, str) and 'type' not in keywords:
                keywords['type'] = length
            elif 'quarterLength' not in keywords:
                keywords['quarterLength'] = length
        super().__init__(**keywords)
        self.stepShift = stepShift  # display line
        # TODO: fullMeasure=='always' does not work properly
        self.fullMeasure = fullMeasure  # see docs; True, False, 'always',

    def _reprInternal(self):
        duration_name = self.duration.fullName.lower()
        if len(duration_name) < 15:  # dotted quarter = 14
            return duration_name.replace(' ', '-')
        else:
            ql = self.duration.quarterLength
            if ql == int(ql):
                ql = int(ql)
            ql_string = str(ql)
            return f'{ql_string}ql'

    @property
    def fullName(self) -> str:
        '''
        Return the most complete representation of this Rest,
        providing duration information.

        >>> r = note.Rest(quarterLength=1.5)
        >>> r.fullName
        'Dotted Quarter Rest'

        >>> note.Rest(type='whole').fullName
        'Whole Rest'
        '''
        return self.duration.fullName + ' Rest'


# ------------------------------------------------------------------------------
# test methods and classes

class TestExternal(unittest.TestCase):
    '''
    These are tests that open windows and rely on external software
    '''
    show = True

    def testSingle(self):
        '''
        Need to test direct note creation w/o stream
        '''
        from music21 import note
        a = note.Note('D-3')
        a.quarterLength = 2.25
        if self.show:
            a.show()

    def testBasic(self):
        from music21 import note
        from music21 import stream
        a = stream.Stream()

        for pitchName, qLen in [('d-3', 2.5), ('c#6', 3.25), ('a--5', 0.5),
                                ('f', 1.75), ('g3', 1.5), ('d##4', 1.25),
                                ('d-3', 2.5), ('c#6', 3.25), ('a--5', 0.5),
                                ('f#2', 1.75), ('g-3', (4 / 3)), ('d#6', (2 / 3))
                                ]:
            b = note.Note()
            b.quarterLength = qLen
            b.name = pitchName
            b.style.color = '#FF00FF'
            a.append(b)

        if self.show:
            a.show()


# ------------------------------------------------------------------------------
class Test(unittest.TestCase):
    def testCopyAndDeepcopy(self):
        from music21.test.commonTest import testCopyAll
        testCopyAll(self, globals())


# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Note, Rest, Unpitched, NotRest, GeneralNote, Lyric]

if __name__ == '__main__':
    # sys.arg test options will be used in mainTest()
    import music21
    music21.mainTest(Test)
