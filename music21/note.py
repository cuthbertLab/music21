# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         note.py
# Purpose:      music21 classes for representing notes
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2006-2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Classes and functions for creating Notes, Rests, and Lyrics.

The :class:`~music21.pitch.Pitch` object is stored within,
and used to configure, :class:`~music21.note.Note` objects.
'''

import copy
import unittest

from music21 import base
from music21 import common
from music21 import duration
from music21 import exceptions21
from music21 import interval
from music21 import editorial
#from music21 import midi as midiModule
from music21 import expressions
from music21 import pitch
from music21 import beam
from music21 import tie
from music21 import volume
from music21.common import SlottedObject


from music21 import environment
_MOD = "note.py"
environLocal = environment.Environment(_MOD)

noteheadTypeNames = [
    'arrow down',
    'arrow up',
    'back slashed',
    'circle dot',
    'circle-x',
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
    're',
    'rectangle',
    'slash',
    'slashed',
    'so',
    'square',
    'ti',
    'triangle',
    'x',
    ]

stemDirectionNames = [
    'double',
    'down',
    'noStem',
    'none',
    'unspecified',
    'up',
    ]


#------------------------------------------------------------------------------


class LyricException(exceptions21.Music21Exception):
    pass


class Lyric(SlottedObject):
    '''
    An object representing a single Lyric as part of a note's .lyrics property.

    The note.lyric property is a simple way of specifying a single lyric, but
    Lyric objects are needed for working with multiple lyrics.

    >>> l = note.Lyric(text="hello")
    >>> l
    <music21.note.Lyric number=1 syllabic=single text="hello">

    Music21 processes leading and following hyphens intelligently...

    >>> l2 = note.Lyric(text='hel-')
    >>> l2
    <music21.note.Lyric number=1 syllabic=begin text="hel">

    ...unless applyRaw is set to True

    >>> l3 = note.Lyric(number=3, text='hel-', applyRaw=True)
    >>> l3
    <music21.note.Lyric number=3 syllabic=single text="hel-">

    Lyrics have four properties: text, number, identifier, syllabic (single,
    begin, middle, end)

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
    '''

    ### CLASS VARIABLES ###

    __slots__ = (
        '_identifier',
        '_number',
        'syllabic',
        'text',
        )

    ### INITIALIZER ###

    def __init__(
        self,
        text=None,
        number=1,
        **kwargs
        ):
        self._identifier = None
        self._number = None

        # these are set by setTextAndSyllabic
        self.text = None
        # given as begin, middle, end, or single
        if 'syllabic' in kwargs:
            self.syllabic = kwargs['syllabic']
        else:
            self.syllabic = None

        if 'applyRaw' in kwargs:
            applyRaw = kwargs['applyRaw']
        else:
            applyRaw = False            
        self.setTextAndSyllabic(text, applyRaw)
        self.number = number

        if 'identifier' in kwargs:
            self.identifier = kwargs['identifier']
        else:
            self.identifier = None

    ### SPECIAL METHODS ###

    def __repr__(self):
        if self._identifier is None:
            if self.text is not None:
                if self.syllabic is not None:
                    return '<music21.note.Lyric number=%d syllabic=%s text="%s">' % (self.number, self.syllabic, self.text)
                else:
                    return '<music21.note.Lyric number=%d text="%s">' % (self.number, self.text)
            else:
                return '<music21.note.Lyric number=%d>' % (self.number)
        else:
            if self.text is not None:
                if self.syllabic is not None:
                    return '<music21.note.Lyric number=%d identifier="%s" syllabic=%s text="%s">' % (self.number, self.identifier, self.syllabic, self.text)
                else:
                    return '<music21.note.Lyric number=%d identifier="%s" text="%s">' % (self.number, self.identifier, self.text)
            else:
                return '<music21.note.Lyric number=%d identifier="%s">' % (self.number, self.identifier)

    ### PRIVATE METHODS ###

    def setTextAndSyllabic(self, rawText, applyRaw=False):
        '''
        Given a setting for rawText and applyRaw,
        sets the syllabic type for a lyric based on the rawText:
        
        >>> l = note.Lyric()
        >>> l.setTextAndSyllabic('hel-')
        >>> l.text
        'hel'
        >>> l.syllabic
        'begin'
        '''
        # do not want to do this unless we are sure this is not a string
        # possible might alter unicode or other string-like representations
        if not common.isStr(rawText):
            rawText = str(rawText)
        else:
            rawText = rawText
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
        else: # assume single
            self.text = rawText
            if self.syllabic is None or self.syllabic is False:
                self.syllabic = 'single'

    ### PUBLIC PROPERTIES ###

    @property
    def identifier(self):
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

        '''
        if self._identifier is None:
            return self._number
        else:
            return self._identifier

    @identifier.setter
    def identifier(self, value):
        self._identifier = value

    @property
    def rawText(self):
        '''
        returns the text of the syllable with '-' etc.
        
        >>> l = note.Lyric("hel-")
        >>> l.text
        'hel'
        >>> l.rawText
        'hel-'
        '''
        if self.syllabic == 'begin':
            return self.text + '-'
        elif self.syllabic == 'middle':
            return '-' + self.text + '-'
        elif self.syllabic == 'end':
            return '-' + self.text
        else:
            return self.text
    @property
    def number(self):
        '''
        This stores the number of the lyric (which determines the order
        lyrics appear in the score if there are multiple lyrics). Unlike
        the musicXML lyric number attribute, this value must always be a
        number; lyric order is always stored in this form. Descriptive
        identifiers like 'part2verse1' which can be found in the musicXML
        lyric number attribute should be stored in self.identifier.

        '''
        return self._number

    @number.setter
    def number(self, value):
        if not common.isNum(value):
            raise LyricException('Number best be number')
        else:
            self._number = value


#-------------------------------------------------------------------------------


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
    create note.Note() or note.Rest() or note.Chord()
    objects directly, and not use this underlying
    structure.


    >>> gn = note.GeneralNote(type = '16th', dots = 2)
    >>> gn.quarterLength
    0.4375
    '''
    isChord = False

    # define order to present names in documentation; use strings
    _DOC_ORDER = ['duration', 'quarterLength']
    # documentation for all attributes (not properties or methods)
    _DOC_ATTR = {
    #'expressions': 'a list of :class:`music21.expressions.TextExpression` objects to store note-attached expressions',
    'isChord': 'Boolean read-only value describing if this object is a Chord.',
    'lyrics': 'A list of :class:`~music21.note.Lyric` objects.',
    'tie': 'either None or a :class:`~music21.note.Tie` object.',
    'expressions': 'a list of expressions (such as :class:`~music21.expressions.Fermata`, etc.) that are stored on this Note.',
    'articulations': 'a list of articulations (such as :class:`~music21.articulations.Staccato`, etc.) that are stored on this Note.'
    }
    def __init__(self, *arguments, **keywords):
        if 'duration' not in keywords:
            # music21base does not automatically create a duration.
            if len(keywords) == 0:
                tempDuration = duration.Duration(1.0)
            else:
                tempDuration = duration.Duration(**keywords)
                # only apply default if components are empty
                # looking at currentComponents so as not to trigger
                # _updateComponents
                if (tempDuration.quarterLength == 0 and
                    len(tempDuration.currentComponents()) == 0):
                    tempDuration.quarterLength = 1.0                
        else:
            tempDuration = keywords['duration']
        # this sets the stored duration defined in Music21Object
        base.Music21Object.__init__(self, duration=tempDuration)

        self.lyrics = [] # a list of lyric objects
        self.expressions = []
        self.articulations = []
        self._editorial = None

        if "lyric" in keywords:
            self.addLyric(keywords['lyric'])

        # note: Chords handle ties differently
        self.tie = None # store a Tie object

    #---------------------------------------------------------------------------
    def _getEditorial(self):
        if self._editorial is None:
            self._editorial = editorial.NoteEditorial()
        return self._editorial

    def _setEditorial(self, ed):
        self._editorial = ed

    editorial = property(_getEditorial, _setEditorial, doc = '''
        a :class:`~music21.editorial.NoteEditorial` object that stores editorial information
        (comments, harmonic information, ficta) and certain display information (color, hidden-state).

        Created automatically as needed:

        >>> n = note.Note("C4")
        >>> n.editorial
        <music21.editorial.NoteEditorial object at 0x...>
        >>> n.editorial.ficta = pitch.Accidental('sharp')
        >>> n.editorial.ficta
        <accidental sharp>

        OMIT_FROM_DOCS
        >>> n2 = note.Note("D4")
        >>> n2._editorial is None
        True
        >>> n2.editorial
        <music21.editorial.NoteEditorial object at 0x...>
        >>> n2._editorial is None
        False
        ''')

    #---------------------------------------------------------------------------
    def _getColor(self):
        '''Return the Note color.

        >>> a = note.GeneralNote()
        >>> a.duration.type = 'whole'
        >>> a.color is None
        True
        >>> a.color = '#235409'
        >>> a.color
        '#235409'
        >>> a.editorial.color
        '#235409'


        '''
        #return self.editorial.color
        if self._editorial is not None:
            return self.editorial.color
        else:
            return None

    def _setColor(self, value):
        r'''
        should check data here
        uses this re: #[\dA-F]{6}([\dA-F][\dA-F])?
        No: because Lilypond supports "blue", "red" etc., as does CSS; musicxml also supports alpha
        '''
        self.editorial.color = value

    color = property(_getColor, _setColor)


    def _getLyric(self):
        '''
        returns the first Lyric's text

        TODO: should return a \\n separated string of lyrics.  See text.assembleAllLyrics
        '''
        if len(self.lyrics) > 0:
            return self.lyrics[0].text
        else:
            return None

    def _setLyric(self, value):
        '''
        presently only creates one lyric, and destroys any existing
        lyrics
        '''
        self.lyrics = []
        if value is not None and value is not False:
            self.lyrics.append(Lyric(value))

    lyric = property(_getLyric, _setLyric,
        doc = '''
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
        [<music21.note.Lyric number=1 syllabic=begin text="hel">]

        Eliminate Lyrics by setting a.lyric to None

        >>> a.lyric = None
        >>> a.lyric
        >>> a.lyrics
        []

        TODO: should check data here
        should split \\n separated lyrics into different lyrics

        presently only creates one lyric, and destroys any existing
        lyrics
        ''')

    def addLyric(self, text, lyricNumber = None, applyRaw = False, lyricIdentifier=None):
        '''
        Adds a lyric, or an additional lyric, to a Note, Chord, or Rest's lyric list. 
        If `lyricNumber` is not None, a specific line of lyric text can be set. The lyricIdentifier
        can also be set.

        >>> n1 = note.Note()
        >>> n1.addLyric("hello")
        >>> n1.lyrics[0].text
        'hello'
        >>> n1.lyrics[0].number
        1


        An added option gives the lyric number, not the list position


        >>> n1.addLyric("bye", 3)
        >>> n1.lyrics[1].text
        'bye'
        >>> n1.lyrics[1].number
        3
        >>> for lyr in n1.lyrics: print(lyr.text)
        hello
        bye


        Replace an existing lyric by specifying the same number:


        >>> n1.addLyric("ciao", 3)
        >>> n1.lyrics[1].text
        'ciao'
        >>> n1.lyrics[1].number
        3


        Giving a lyric with a hyphen at either end will set whether it
        is part of a multisyllable word:


        >>> n1.addLyric("good-")
        >>> n1.lyrics[2].text
        'good'
        >>> n1.lyrics[2].syllabic
        'begin'


        This feature can be overridden by specifying "applyRaw = True":


        >>> n1.addLyric("-5", applyRaw = True)
        >>> n1.lyrics[3].text
        '-5'
        >>> n1.lyrics[3].syllabic
        'single'


        '''
        if not common.isStr(text):
            text = str(text)
        if lyricNumber is None:
            maxLyrics = len(self.lyrics) + 1
            self.lyrics.append(Lyric(text, maxLyrics, applyRaw = applyRaw, identifier = lyricIdentifier))
        else:
            foundLyric = False
            for thisLyric in self.lyrics:
                if thisLyric.number == lyricNumber:
                    thisLyric.text = text
                    foundLyric = True
                    break
            if foundLyric is False:
                self.lyrics.append(Lyric(text, lyricNumber, applyRaw = applyRaw, identifier = lyricIdentifier))

    def insertLyric(self, text, index=0, applyRaw=False, identifier=None):
        '''Inserts a lyric into the Note, Chord, or Rest's lyric list in front of
        the index specified (0 by default), using index + 1 as the inserted lyric's
        line number. shifts line numbers of all following lyrics in list


        >>> n1 = note.Note()
        >>> n1.addLyric("second")
        >>> n1.lyrics
        [<music21.note.Lyric number=1 syllabic=single text="second">]
        >>> n1.insertLyric("first", 0)
        >>> n1.lyrics
        [<music21.note.Lyric number=1 syllabic=single text="first">, <music21.note.Lyric number=2 syllabic=single text="second">]

        OMIT_FROM_DOCS
        >>> n1.insertLyric("newSecond", 1)
        >>> n1.lyrics
        [<music21.note.Lyric number=1 syllabic=single text="first">, <music21.note.Lyric number=2 syllabic=single text="newSecond">, <music21.note.Lyric number=3 syllabic=single text="second">]
        '''
        if not common.isStr(text):
            text = str(text)
        for lyric in self.lyrics[index:]:
            lyric.number += 1
        self.lyrics.insert(index, Lyric(text, (index+ 1), applyRaw=applyRaw, identifier=identifier ))

    def hasLyrics(self):
        '''Return True if this object has any lyrics defined
        '''
        if len(self.lyrics) > 0:
            return True
        else:
            return False


    #---------------------------------------------------------------------------
    # properties common to Notes, Rests,

    #---------------------------------------------------------------------------
    def augmentOrDiminish(self, scalar, inPlace=True):
        '''Given a scalar greater than zero, return a Note with a scaled Duration. If `inPlace` is True, this is done in-place and the method returns None. If `inPlace` is False, this returns a modified deep copy.


        >>> n = note.Note('g#')
        >>> n.quarterLength = 3
        >>> n.augmentOrDiminish(2)
        >>> n.quarterLength
        6.0

        >>> c = chord.Chord(['g#','A#','d'])
        >>> n.quarterLength = 2
        >>> n.augmentOrDiminish(.25)
        >>> n.quarterLength
        0.5

        >>> n = note.Note('g#')
        >>> n.augmentOrDiminish(-1)
        Traceback (most recent call last):
        NoteException: scalar must be greater than zero
        '''
        if not scalar > 0:
            raise NoteException('scalar must be greater than zero')

        if inPlace:
            post = self
        else:
            post = copy.deepcopy(self)

        # inPlace always True b/c we have already made a copy if necessary
        post.duration = post.duration.augmentOrDiminish(scalar)

        if not inPlace:
            return post
        else:
            return None

    #---------------------------------------------------------------------------
    def getGrace(self, appogiatura=False, inPlace=False):
        '''Return a grace version of this GeneralNote


        >>> n = note.Note('G4', quarterLength=2)
        >>> n.duration.quarterLength
        2.0
        >>> n.isGrace
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
        >>> ng.isGrace
        True
        >>> ng.duration
        <music21.duration.GraceDuration unlinked type:zero quarterLength:0.0>
        >>> ng.duration.type
        'zero'
        >>> ng.duration.components
        (DurationTuple(type='half', dots=0, quarterLength=0.0),)

        Appogiaturas are still a work in progress...

        >>> ng2 = n.getGrace(appogiatura=True)
        >>> ng2.duration
        <music21.duration.AppogiaturaDuration unlinked type:zero quarterLength:0.0>
        >>> ng2.duration.slash
        False
        
        Set inPlace to True to change the duration element on the Note.  This can have
        negative consequences if the Note is in a stream.
        
        >>> r = note.Rest(quarterLength = .5)
        >>> r.getGrace(inPlace=True)
        >>> r.duration
        <music21.duration.GraceDuration unlinked type:zero quarterLength:0.0>
        '''
        if inPlace is False:
            e = copy.deepcopy(self)
        else:
            e = self
            
        e.duration = e.duration.getGraceDuration(appogiatura=appogiatura)
        
        if inPlace is False:
            return e


#-------------------------------------------------------------------------------
class NotRestException(exceptions21.Music21Exception):
    pass

#-------------------------------------------------------------------------------
class NotRest(GeneralNote):
    '''
    Parent class for Note-like objects that are not rests; that is to say
    they have a stem, can be tied, and volume is important.
    Basically, that's a `Note` or
    `Unpitched` object for now.
    '''

    # unspecified means that there may be a stem, but its orientation
    # has not been declared.
    _DOC_ATTR = {
    'beams': 'A :class:`~music21.beam.Beams` object that contains information about the beaming of this note.',
    }
    def __init__(self, *arguments, **keywords):
        GeneralNote.__init__(self, **keywords)
        self._notehead = 'normal'
        self._noteheadFill = None
        self._noteheadParenthesis = False
        self._stemDirection = 'unspecified'
        self._volume = None # created on demand
        #replace
        self.linkage = 'tie'
        if "beams" in keywords:
            self.beams = keywords["beams"]
        else:
            self.beams = beam.Beams()

    #===============================================================================================
    # Special functions
    #===============================================================================================

    def __deepcopy__(self, memo=None):
        '''
        As NotRest objects have a Volume, objects, and Volume objects
        store weak refs to the to client object, need to specialize deep copy handling
        
        >>> import copy
        >>> n = note.NotRest()
        >>> n.volume = volume.Volume(50)
        >>> m = copy.deepcopy(n)
        >>> m.volume.client is m
        True
        '''
        #environLocal.printDebug(['calling NotRest.__deepcopy__', self])
        new = super(NotRest, self).__deepcopy__(memo=memo)
        # after copying, if a Volume exists, it is linked to the old object
        # look at _volume so as not to create object if not already there
        if self._volume is not None:
            new.volume.client = new # update with new instance
        return new

    def __getstate__(self):
        state = super(NotRest, self).__getstate__()
        if '_volume' in state and state['_volume'] is not None:
            state['_volume'].client = None
        return state
 
    def __setstate__(self, state):
        super(NotRest, self).__setstate__(state)
        if self._volume is not None:
            self._volume.client = self
    ####

    def _getStemDirection(self):
        return self._stemDirection

    def _setStemDirection(self, direction):
        if direction is None:
            direction = None # allow setting to none or None
        elif direction == 'none':
            direction = 'noStem' # allow setting to none or None
        elif direction not in stemDirectionNames:
            raise NotRestException('not a valid stem direction name: %s' % direction)
        self._stemDirection = direction

    stemDirection = property(_getStemDirection, _setStemDirection, doc=
        '''Get or set the stem direction of this NotRest object. Valid stem direction names are found in note.stemDirectionNames (see below).


        >>> note.stemDirectionNames
        ['double', 'down', 'noStem', 'none', 'unspecified', 'up']
        >>> n = note.Note()
        >>> n.stemDirection = 'noStem'
        >>> n.stemDirection
        'noStem'
        >>> n.stemDirection = 'junk'
        Traceback (most recent call last):
        NotRestException: not a valid stem direction name: junk
        ''')


    def _getNotehead(self):
        return self._notehead

    def _setNotehead(self, value):
        if value in ['none', None, '']:
            value = None # allow setting to none or None
        elif value not in noteheadTypeNames:
            raise NotRestException('not a valid notehead type name: %s' % repr(value))
        self._notehead = value

    notehead = property(_getNotehead, _setNotehead, doc=
        '''
        Get or set the notehead type of this NotRest object.
        Valid notehead type names are found in note.noteheadTypeNames (see below):


        >>> note.noteheadTypeNames
        ['arrow down', 'arrow up', 'back slashed', 'circle dot', 'circle-x', 'cluster', 'cross', 'diamond', 'do', 'fa', 'inverted triangle', 'la', 'left triangle', 'mi', 'none', 'normal', 're', 'rectangle', 'slash', 'slashed', 'so', 'square', 'ti', 'triangle', 'x']
        >>> n = note.Note()
        >>> n.notehead = 'diamond'
        >>> n.notehead
        'diamond'

        >>> n.notehead = 'junk'
        Traceback (most recent call last):
        NotRestException: not a valid notehead type name: 'junk'
        ''')


    def _getNoteheadFill(self):
        '''Return the Notehead fill type.  "yes" and "no" are converted to True, False
        '''
        return self._noteheadFill

    def _setNoteheadFill(self, value):
        if value in ('none', None, 'default'):
            value = None # allow setting to none or None
        if value in ('filled', 'yes'):
            value = True
        elif value in ('notfilled', 'no'):
            value = False
        if value not in (True, False, None):
            raise NotRestException('not a valid notehead fill value: %s' % value)
        self._noteheadFill = value

    noteheadFill = property(_getNoteheadFill, _setNoteheadFill, doc='''
        Get or set the note head fill status of this NotRest. Valid note head fill values are 
        True, False, or None (meaning default).

        >>> n = note.Note()
        >>> n.noteheadFill = 'no'
        >>> n.noteheadFill
        False
        >>> n.noteheadFill = 'filled'
        >>> n.noteheadFill
        True

        >>> n.noteheadFill = 'junk'
        Traceback (most recent call last):
        NotRestException: not a valid notehead fill value: junk
        ''')


    def _getNoteheadParenthesis(self):
        return self._noteheadParenthesis

    def _setNoteheadParenthesis(self, value):
        if value in (True, 'yes', 1):
            value = True
        elif value in (False, 'no', 0):
            value = False
        else:
            raise NotRestException('notehead parentheses must be True or False, not %r' % value)       
        self._noteheadParenthesis = value
        

    noteheadParenthesis = property(_getNoteheadParenthesis, _setNoteheadParenthesis, doc='''
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
        NotRestException: notehead parentheses must be True or False, not 'blah'
        ''')

    #---------------------------------------------------------------------------
    def _getVolume(self, forceClient=None):
        # lazy volume creation
        if self._volume is None:
            if forceClient is None:
                # when creating the volume object, set the client as self
                self._volume = volume.Volume(client=self)
            else:
                self._volume = volume.Volume(client=forceClient)
        return self._volume

    def _setVolume(self, value, setClient=True):
        # setParent is only False when Chords bundling Notes
        # test by looking for method
        if hasattr(value, "getDynamicContext"):
            if setClient:
                if value.client is not None:
                    raise NotRestException(
                        'cannot set a volume object that has a defined client: %s' % value.client)
                value.client = self # set to self
            self._volume = value
        elif common.isNum(value) and setClient:
            # if we can define the client, we can set from numbers
            # call local getVolume will set client appropriately
            vol = self._getVolume()
            if value < 1: # assume a scalar
                vol.velocityScalar = value
            else: # assume velocity
                vol.velocity = value

        else:
            raise Exception('this must be a Volume object, not %s' % value)

    volume = property(_getVolume, _setVolume,
        doc = '''
        Get and set the :class:`~music21.volume.Volume` object of this object. 
        Volume objects are created on demand.


        >>> n1 = note.Note()
        >>> n1.volume.velocity = 120
        >>> n2 = note.Note()
        >>> n2.volume = 80 # can directly set a velocity value
        >>> s = stream.Stream()
        >>> s.append([n1, n2])
        >>> [n.volume.velocity for n in s.notes]
        [120, 80]
        ''')




#-------------------------------------------------------------------------------
class NoteException(exceptions21.Music21Exception):
    pass


#-------------------------------------------------------------------------------
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


    Two notes are considered equal if their most important attributes
    (such as pitch, duration,
    articulations, and ornaments) are equal.  Attributes
    that might change based on the wider context
    of a note (such as offset, beams, stem direction)
    are not compared. This test presently does not look at lyrics in
    establishing equality.  It may in the future.


    '''
    isNote = True
    isUnpitched = False
    isRest = False

    # define order to present names in documentation; use strings
    _DOC_ORDER = ['duration', 'quarterLength', 'nameWithOctave', 'pitchClass']
    # documentation for all attributes (not properties or methods)
    _DOC_ATTR = {
    'isNote': 'Boolean read-only value describing if this Note is a Note (True).',
    'isUnpitched': 'Boolean read-only value describing if this Note is Unpitched (False).',
    'isRest': 'Boolean read-only value describing if this Note is a Rest (False).',
    'pitch': 'A :class:`~music21.pitch.Pitch` object containing all the information about the note\'s pitch.  Many `.pitch` properties and methods are also made `Note` properties also',
    }

    # Accepts an argument for pitch
    def __init__(self, *arguments, **keywords):
        NotRest.__init__(self, **keywords)
        if len(arguments) > 0:
            if isinstance(arguments[0], pitch.Pitch):
                self.pitch = arguments[0]
            else: # assume first argument is pitch
                self.pitch = pitch.Pitch(arguments[0], **keywords)
        else: # supply a default pitch
            if 'name' in keywords:
                del keywords['name']
            self.pitch = pitch.Pitch('C4', **keywords)

    #---------------------------------------------------------------------------
    # operators, representations, and transformations

    def __repr__(self):
        return "<music21.note.Note %s>" % self.name


    def __eq__(self, other):
        '''
        Tests Equality. See docs under Note above
        (since __eq__'s docs don't display)

        >>> n1 = note.Note()
        >>> n1.pitch.name = 'G#'
        >>> n2 = note.Note()
        >>> n2.pitch.name = 'A-'
        >>> n3 = note.Note()
        >>> n3.pitch.name = 'G#'
        >>> n1 == n2
        False
        >>> n1 == n3
        True
        >>> n3.duration.quarterLength = 3
        >>> n1 == n3
        False

        '''
        if other == None or not isinstance(other, Note):
            return False
        # checks pitch.octave, pitch.accidental, uses Pitch.__eq__
        if self.pitch != other.pitch:
            return False
        # checks type, dots, tuplets, quarterlength, uses Pitch.__eq__
        if self.duration != other.duration:
            return False
        # articulations are a list of Articulation objects
        # converting to sets produces ordered cols that remove duplicate
        # however, must then convert to list to match based on class ==
        # not on class id()
        if (sorted(list(set([x.classes[0] for x in self.articulations]))) !=
            sorted(list(set([x.classes[0] for x in other.articulations])))):
            return False
        if (sorted(list(set([x.classes[0] for x in self.expressions]))) !=
            sorted(list(set([x.classes[0] for x in other.expressions])))):
            return False

        # Tie objects if present compare only type
        if self.tie != other.tie:
            return False
        return True

    def __ne__(self, other):
        '''Inequality.

        >>> n1 = note.Note()
        >>> n1.pitch.name = 'G#'
        >>> n2 = note.Note()
        >>> n2.pitch.name = 'A-'
        >>> n3 = note.Note()
        >>> n3.pitch.name = 'G#'
        >>> n1 != n2
        True
        >>> n1 != n3
        False
        >>> n3.duration.quarterLength = 3
        >>> n1 != n3
        True
        '''
        return not self.__eq__(other)

    def __lt__(self, other):
        '''
        __lt__, __gt__, __le__, __ge__ all use a pitch comparison

        >>> highE = note.Note("E5")
        >>> lowF = note.Note("F2")
        >>> otherHighE = note.Note("E5")

        >>> highE > lowF
        True
        >>> highE < lowF
        False
        >>> highE >= otherHighE
        True
        >>> highE <= otherHighE
        True
        '''
        return self.pitch < other.pitch

    def __gt__(self, other):
        return self.pitch > other.pitch

    def __le__(self, other):
        return self.pitch <= other.pitch

    def __ge__(self, other):
        return self.pitch >= other.pitch


    #---------------------------------------------------------------------------
    # property access


    def _getName(self):
        return self.pitch.name

    def _setName(self, value):
        self.pitch.name = value

    name = property(_getName, _setName,
        doc = '''Return or set the pitch name from the :class:`~music21.pitch.Pitch` object.
        See `Pitch`'s attribute :attr:`~music21.pitch.Pitch.name`.
        ''')

    def _getNameWithOctave(self):
        return self.pitch.nameWithOctave
    def _setNameWithOctave(self, value):
        self.pitch.nameWithOctave = value

    nameWithOctave = property(_getNameWithOctave, _setNameWithOctave,
        doc = '''
        Return or set the pitch name with octave from the :class:`~music21.pitch.Pitch` object.
        See `Pitch`'s attribute :attr:`~music21.pitch.Pitch.nameWithOctave`.
        ''')


    @common.deprecated("May 2014", "Jan 2016", "use pitch.accidental instead")
    def _getAccidental(self):
        return self.pitch.accidental

    def _setAccidental(self, value):
        '''
        Adds an accidental to the Note, given as an Accidental object.
        Also alters the name of the note


        >>> a = note.Note()
        >>> a.step = "D"
        >>> a.name
        'D'
        >>> b = pitch.Accidental("sharp")
        >>> a.accidental = (b)
        >>> a.name
        'D#'
        '''
        if common.isStr(value):
            accidental = pitch.Accidental(value)
        else:
            accidental = value
        self.pitch.accidental = accidental


    accidental = property(_getAccidental, _setAccidental,
        doc = '''
        Return or set the :class:`~music21.pitch.Accidental` object 
        from the :class:`~music21.pitch.Pitch` object.

        DEPRECATED May 2014: use n.pitch.accidental instead        
        ''')


    def _getStep(self):
        return self.pitch.step

    def _setStep(self, value):
        self.pitch.step = value

    step = property(_getStep, _setStep,
        doc = '''Return or set the pitch step from the :class:`~music21.pitch.Pitch` object. See :attr:`~music21.pitch.Pitch.step`.
        ''')

    @common.deprecated("May 2014", "Jan 2016", "use pitch.frequency instead")
    def _getFrequency(self):
        return self.pitch.frequency

    def _setFrequency(self, value):
        self.pitch.frequency = value

    frequency = property(_getFrequency, _setFrequency,
        doc = '''
        Return or set the frequency from 
        the :class:`~music21.pitch.Pitch` object. 
        
        See :attr:`~music21.pitch.Pitch.frequency`.
        
        DEPRECATED May 2014: use n.pitch.frequency instead
        ''')

    def _getOctave(self):
        return self.pitch.octave

    def _setOctave(self, value):
        self.pitch.octave = value

    octave = property(_getOctave, _setOctave,
        doc = '''Return or set the octave value from the :class:`~music21.pitch.Pitch` object. See :attr:`~music21.pitch.Pitch.octave`.''')

    @common.deprecated("May 2014", "Jan 2016", "use pitch.midi instead")
    def _getMidi(self):
        return self.pitch.midi

    def _setMidi(self, value):
        self.pitch.midi = value

    midi = property(_getMidi, _setMidi,
        doc = '''
        Return or set the numerical MIDI pitch 
        representation from the 
        :class:`~music21.pitch.Pitch` object. 
        
        See :attr:`~music21.pitch.Pitch.midi`.
        
        DEPRECATED May 2014: use n.pitch.midi instead
        ''')

    @common.deprecated("May 2014", "Jan 2016", "use pitch.ps instead")
    def _getPs(self):
        return self.pitch.ps

    def _setPs(self, value):
        self.pitch.ps = value

    ps = property(_getPs, _setPs,
        doc = '''
        Return or set the numerical pitch space 
        representation from the 
        :class:`music21.pitch.Pitch` object. 
        
        See :attr:`music21.pitch.Pitch.ps`.
        
        DEPRECATED May 2014: use n.pitch.ps instead
        ''')

    @common.deprecated("May 2014", "Jan 2016", "use pitch.microtone instead")
    def _getMicrotone(self):
        return self.pitch.microtone

    def _setMicrotone(self, value):
        self.pitch.microtone = value

    microtone = property(_getMicrotone, _setMicrotone,
        doc = '''Return or set the microtone value from the 
        :class:`~music21.pitch.Pitch` object. 
        
        See :attr:`~music21.pitch.Pitch.microtone`.
        
        DEPRECATED May 2014: use n.pitch.microtone instead
        ''')


    @common.deprecated("May 2014", "Jan 2016", "use pitch.pitchClass instead")
    def _getPitchClass(self):
        return self.pitch.pitchClass

    def _setPitchClass(self, value):
        self.pitch.pitchClass = value

    pitchClass = property(_getPitchClass, _setPitchClass,
        doc = '''Return or set the pitch class from the :class:`~music21.pitch.Pitch` object.
        See :attr:`music21.pitch.Pitch.pitchClass`.

        DEPRECATED May 2014: use n.pitch.pitchClass instead
        ''')


    @common.deprecated("May 2014", "Jan 2016", "use pitch.pitchClassString instead")
    def _getPitchClassString(self):
        return self.pitch.pitchClassString

    def _setPitchClassString(self, value):
        self.pitch.pitchClassString = value

    pitchClassString = property(_getPitchClassString, _setPitchClassString,
        doc = '''
        Return or set the pitch class string 
        from the :class:`~music21.pitch.Pitch` 
        object. 
        
        See :attr:`~music21.pitch.Pitch.pitchClassString`.
        
        DEPRECATED May 2014: use n.pitch.pitchClassString instead
        ''')


    # was diatonicNoteNum
    def _getDiatonicNoteNum(self):
        '''
        see Pitch.diatonicNoteNum
        '''
        return self.pitch.diatonicNoteNum

    diatonicNoteNum = property(_getDiatonicNoteNum,
        doc = '''Return the diatonic note number from the :class:`~music21.pitch.Pitch` object. 
        See :attr:`~music21.pitch.Pitch.diatonicNoteNum`.
        
        Probably will be deprecated soon...
        ''')



    def _getPitches(self):
        return [self.pitch]

    def _setPitches(self, value):
        if common.isListLike(value):
            if 'Pitch' in value[0].classes:
                self.pitch = value[0]
            else:
                raise NoteException('must provide a list containing a Pitch, not: %s' % value)
        else:
            raise NoteException('cannot set pitches with provided object: %s' % value)

    pitches = property(_getPitches, _setPitches,
        doc = '''
        Return the :class:`~music21.pitch.Pitch` object in a list.
        This property is designed to provide an interface analogous to
        that found on :class:`~music21.chord.Chord`.

        >>> n = note.Note('g#')
        >>> n.nameWithOctave
        'G#'
        >>> n.pitches
        [<music21.pitch.Pitch G#>]
        >>> n.pitches = [pitch.Pitch('c2'), pitch.Pitch('g2')]
        >>> n.nameWithOctave
        'C2'
        >>> n.pitches
        [<music21.pitch.Pitch C2>]
        ''')


    def transpose(self, value, inPlace=False):
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

        '''
        if hasattr(value, 'classes') and 'IntervalBase' in value.classes:
            intervalObj = value
        else: # try to process
            intervalObj = interval.Interval(value)

        if not inPlace:
            post = copy.deepcopy(self)
        else:
            post = self

        # use inPlace, b/c if we are inPlace, we operate on self;
        # if we are not inPlace, post is a copy
        post.pitch.transpose(intervalObj, inPlace=True)

        if not inPlace:
            return post
        else:
            return None



    def _getFullName(self):
        msg = []
        msg.append('%s ' % self.pitch.fullName)
        msg.append(self.duration.fullName)
        msg.append(' Note')
        return ''.join(msg)

    fullName = property(_getFullName,
        doc = '''
        Return the most complete representation of this Note, providing duration and pitch information.


        >>> n = note.Note('A-', quarterLength=1.5)
        >>> n.fullName
        'A-flat Dotted Quarter Note'

        >>> n = note.Note('E~3', quarterLength=2)
        >>> n.fullName
        'E-half-sharp in octave 3 Half Note'

        >>> n = note.Note('D', quarterLength=.25)
        >>> n.microtone = 25
        >>> n.fullName
        'D (+25c) 16th Note'
        ''')


#-------------------------------------------------------------------------------
# convenience classes


#-------------------------------------------------------------------------------
class Unpitched(NotRest):
    '''
    A General class of unpitched objects which appear at different places
    on the staff.  Examples: percussion notation.

    The `Unpitched` object does not currently do anything and should
    not be used.
    '''
    displayStep = "C"
    displayOctave = 4
    isNote = False
    isUnpitched = True
    isRest = False

    def __init__(self):
        NotRest.__init__(self)
        self._storedInstrument = None

    def _getStoredInstrument(self):
        return self._storedInstrument

    def _setStoredInstrument(self, newValue):
        self._storedInstrument = newValue

    storedInstrument = property(_getStoredInstrument, _setStoredInstrument)

    def displayPitch(self):
        '''
        returns a pitch object that is the same as the displayStep and displayOctave
        '''
        p = pitch.Pitch()
        p.step = self.displayStep
        p.octave = self.displayOctave
        return p



#-------------------------------------------------------------------------------
class Rest(GeneralNote):
    '''
    Rests are represented in music21 as GeneralNote objects that do not have
    a pitch object attached to them.  By default they have length 1.0 (Quarter Rest)

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
    '''
    isNote = False
    isUnpitched = False
    isRest = True
    name = "rest"

    _DOC_ATTR = {
    'isNote': 'Boolean read-only value describing if this Rest is a Note (False).',
    'isUnpitched': 'Boolean read-only value describing if this Rest is Unpitched (False -- only Unpitched objects are True).',
    'isRest': 'Boolean read-only value describing if this Rest is a Rest (True, obviously).',
    'name': 'returns "rest" always.  It is here so that you can get `x.name` on all `.notesAndRests` objects',
    'lineShift': 'number of lines/spaces to shift the note upwards or downwards for display.',
    }

    def __init__(self, *arguments, **keywords):
        GeneralNote.__init__(self, **keywords)
        self.lineShift = 0 # display line

    def __repr__(self):
        return "<music21.note.Rest %s>" % self.name

    def __eq__(self, other):
        '''
        A Music21 rest is equal to another object if that object is also a rest which
        has the same duration.


        >>> r1 = note.Rest()
        >>> r2 = note.Rest()
        >>> r1 == r2
        True
        >>> r2.duration.quarterLength = 4.0/3
        >>> r1 == r2
        False
        >>> r1 == note.Note()
        False
        '''

        return isinstance(other, Rest) and self.duration == other.duration

    def __ne__(self, other):
        '''
        Inequality


        >>> r1 = note.Rest()
        >>> r2 = note.Rest()
        >>> r1 != r2
        False
        >>> r2.duration.quarterLength = 2.0
        >>> r1 != r2
        True
        >>> r1 != note.Note()
        True
        '''

        return not self == other


    def _getFullName(self):
        msg = []
        msg.append(self.duration.fullName)
        msg.append(' Rest')
        return ''.join(msg)

    fullName = property(_getFullName,
        doc = '''Return the most complete representation of this Rest, providing duration information.


        >>> r = note.Rest(quarterLength=1.5)
        >>> r.fullName
        'Dotted Quarter Rest'

        >>> note.Rest(type='whole').fullName
        'Whole Rest'
        ''')


class SpacerRest(Rest):
    '''
    This is exactly the same as a rest, but it is a SpacerRest.
    This object should only be used for making hidden space in a score in lilypond.
    '''
    def __init__(self, *arguments, **keywords):
        Rest.__init__(self, **keywords)

    def __repr__(self):
        return "<music21.note.SpacerRest %s duration=%s>" % (self.name, self.duration.quarterLength)


#-------------------------------------------------------------------------------
# test methods and classes

class TestExternal(unittest.TestCase):
    '''These are tests that open windows and rely on external software
    '''

    def runTest(self):
        pass

    def testSingle(self):
        '''Need to test direct meter creation w/o stream
        '''
        a = Note('d-3')
        a.quarterLength = 2.25
        a.show()

    def testBasic(self):
        from music21 import stream
        a = stream.Stream()

        for pitchName, qLen in [('d-3', 2.5), ('c#6', 3.25), ('a--5', .5),
                           ('f', 1.75), ('g3', 1.5), ('d##4', 1.25),
                           ('d-3', 2.5), ('c#6', 3.25), ('a--5', .5),
                           ('f#2', 1.75), ('g-3', 1.33333), ('d#6', .6666)
                ]:
            b = Note()
            b.quarterLength = qLen
            b.name = pitchName
            b.color = '#FF00FF'
            # print a.musicxml
            a.append(b)

        a.show()



#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
        '''
        import sys, types
        for part in sys.modules[self.__module__].__dict__:
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            name = getattr(sys.modules[self.__module__], part)
            if callable(name) and not isinstance(name, types.FunctionType):
                try: # see if obj can be made w/ args
                    obj = name()
                except TypeError:
                    continue
                a = copy.copy(obj)
                b = copy.deepcopy(obj)
                self.assertNotEqual(id(a), id(b))


    def testComplex(self):
        note1 = Note()
        note1.duration.clear()
        d1 = duration.DurationTuple('whole', 0, 4.0)
        d2 = duration.DurationTuple('quarter', 0, 1.0)
        note1.duration.addDurationTuple(d1)
        note1.duration.addDurationTuple(d2)
        self.assertEqual(note1.duration.quarterLength, 5.0)
        self.assertEqual(note1.duration.componentIndexAtQtrPosition(2), 0)
        self.assertEqual(note1.duration.componentIndexAtQtrPosition(4), 1)
        self.assertEqual(note1.duration.componentIndexAtQtrPosition(4.5), 1)
        note1.duration.sliceComponentAtPosition(1.0)

        matchStr = "c'4~\nc'2.~\nc'4"
        from music21.lily.translate import LilypondConverter
        conv = LilypondConverter()
        conv.appendM21ObjectToContext(note1)
        outStr = str(conv.context).replace(' ', '').strip()
        #print outStr
        self.assertEqual(matchStr, outStr)
        i = 0
        for thisNote in note1.splitAtDurations():
            matchSub = matchStr.split('\n')[i]
            conv = LilypondConverter()
            conv.appendM21ObjectToContext(thisNote)
            outStr = str(conv.context).replace(' ', '').strip()
            self.assertEqual(matchSub, outStr)
            i += 1


    def testNote(self):
    #    note1 = Note("c#1")
    #    assert note1.duration.quarterLength == 4
    #    note1.duration.dots = 1
    #    assert note1.duration.quarterLength == 6
    #    note1.duration.type = "eighth"
    #    assert note1.duration.quarterLength == 0.75
    #    assert note1.octave == 4
    #    assert note1.step == "C"

        note2 = Rest()
        self.assertEqual(note2.isRest, True)
        note3 = Note()
        note3.pitch.name = "B-"
        # not sure how to test not None
        #self.assertFalse (note3.pitch.accidental, None)
        self.assertEqual (note3.pitch.accidental.name, "flat")
        self.assertEqual (note3.pitch.pitchClass, 10)

        a5 = Note()
        a5.name = "A"
        a5.octave = 5
        self.assertAlmostEquals(a5.pitch.frequency, 880.0)
        self.assertEqual(a5.pitch.pitchClass, 9)



    def testCopyNote(self):
        a = Note()
        a.quarterLength = 3.5
        a.name = 'D'
        b = copy.deepcopy(a)
        self.assertEqual(b.name, a.name)


    def testMusicXMLFermata(self):
        from music21 import corpus
        a = corpus.parse('bach/bwv5.7')
        found = []
        for n in a.flat.notesAndRests:
            for obj in n.expressions:
                if isinstance(obj, expressions.Fermata):
                    found.append(obj)
        self.assertEqual(len(found), 6)


    def testNoteBeatProperty(self):
        from music21 import stream, meter

        data = [
    ['3/4', .5, 6, [1.0, 1.5, 2.0, 2.5, 3.0, 3.5],
            [1.0]*6, ],
    ['3/4', .25, 8, [1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75],
            [1.0]*8],
    ['3/2', .5, 8, [1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75],
            [2.0]*8],

    ['6/8', .5, 6, [1.0, 1.3333, 1.66666, 2.0, 2.3333, 2.666666],
            [1.5]*6],
    ['9/8', .5, 6, [1.0, 1.3333, 1.66666, 2.0, 2.3333, 2.666666],
            [1.5]*6],
    ['12/8', .5, 6, [1.0, 1.3333, 1.66666, 2.0, 2.3333, 2.666666],
            [1.5]*6],

    ['6/16', .25, 6, [1.0, 1.3333, 1.66666, 2.0, 2.3333, 2.666666],
            [0.75]*6],

    ['5/4', 1, 5, [1.0, 2.0, 3.0, 4.0, 5.0],
            [1.]*5],

    ['2/8+3/8+2/8', .5, 6, [1.0, 1.5, 2.0, 2.33333, 2.66666, 3.0],
            [1., 1., 1.5, 1.5, 1.5, 1.]],

        ]

        # one measure case
        for tsStr, nQL, nCount, matchBeat, matchBeatDur in data:
            n = Note() # need fully qualified name
            n.quarterLength = nQL
            m = stream.Measure()
            m.timeSignature = meter.TimeSignature(tsStr)
            m.repeatAppend(n, nCount)

            self.assertEqual(len(m), nCount+1)

            # test matching beat proportion value
            post = [m.notesAndRests[i].beat for i in range(nCount)]
            for i in range(len(matchBeat)):
                self.assertAlmostEquals(post[i], matchBeat[i], 4)

            # test getting beat duration
            post = [m.notesAndRests[i].beatDuration.quarterLength for i in range(nCount)]

            for i in range(len(matchBeat)):
                self.assertAlmostEquals(post[i], matchBeatDur[i], 4)

        # two measure case
        for tsStr, nQL, nCount, matchBeat, matchBeatDur in data:
            p = stream.Part()
            n = Note()
            n.quarterLength = nQL

            # m1 has time signature
            m1 = stream.Measure()
            m1.timeSignature = meter.TimeSignature(tsStr)
            p.append(m1)

            # m2 does not have time signature
            m2 = stream.Measure()
            m2.repeatAppend(n, nCount)
            self.assertEqual(len(m2), nCount)
            self.assertEqual(len(m2.notesAndRests), nCount)

            p.append(m2)

            # test matching beat proportion value
            post = [m2.notesAndRests[i].beat for i in range(nCount)]
            for i in range(len(matchBeat)):
                self.assertAlmostEquals(post[i], matchBeat[i], 4)
            # test getting beat duration
            post = [m2.notesAndRests[i].beatDuration.quarterLength for i in range(nCount)]
            for i in range(len(matchBeat)):
                self.assertAlmostEquals(post[i], matchBeatDur[i], 4)



    def testNoteBeatPropertyCorpus(self):
        data = [['bach/bwv255', [4.0, 1.0, 2.0, 2.5, 3.0, 4.0, 4.5, 1.0, 1.5]],
                ['bach/bwv153.9', [1.0, 2.0, 3.0, 1.0, 2.0, 3.0, 1.0, 3.0, 1.0]]
                ]

        for work, match in data:
            from music21 import corpus
            s = corpus.parse(work)
            # always use tenor line
            found = []
            for n in s.parts[2].flat.notesAndRests:
                n.lyric = n.beatStr
                found.append(n.beat)

            for i in range(len(match)):
                self.assertEquals(match[i], found[i])

            #s.show()


    def testNoteEquality(self):
        from music21 import articulations

        n1 = Note('a#')
        n2 = Note('g')
        n3 = Note('a-')
        n4 = Note('a#')

        self.assertEqual(n1==n2, False)
        self.assertEqual(n1==n3, False)
        self.assertEqual(n1==n4, True)

        # test durations with the same pitch
        for x, y, match in [(1, 1, True), (1, .5, False),
                     (1, 2, False), (1, 1.5, False)]:
            n1.quarterLength = x
            n4.quarterLength = y
            self.assertEqual(n1==n4, match) # sub1

        # test durations with different pitch
        for x, y, match in [(1, 1, False), (1, .5, False),
                     (1, 2, False), (1, 1.5, False)]:
            n1.quarterLength = x
            n2.quarterLength = y
            self.assertEqual(n1==n2, match) # sub2

        # same pitches different octaves
        n1.quarterLength = 1.0
        n4.quarterLength = 1.0
        for x, y, match in [(4, 4, True), (3, 4, False), (2, 4, False)]:
            n1.pitch.octave = x
            n4.pitch.octave = y
            self.assertEqual(n1==n4, match) # sub4

        # with and without ties
        n1.pitch.octave = 4
        n4.pitch.octave = 4
        t1 = tie.Tie()
        t2 = tie.Tie()
        for x, y, match in [(t1, None, False), (t1, t2, True)]:
            n1.tie = x
            n4.tie = y
            self.assertEqual(n1==n4, match) # sub4

        # with ties but different pitches
        for n in [n1, n2, n3, n4]:
            n.quarterLength = 1.0
        t1 = tie.Tie()
        t2 = tie.Tie()
        for a, b, match in [(n1, n2, False), (n1, n3, False),
                            (n2, n3, False), (n1, n4, True)]:
            a.tie = t1
            b.tie = t2
            self.assertEqual(a==b, match) # sub5

        # articulation groups
        a1 = [articulations.Accent()]
        a2 = [articulations.Accent(), articulations.StrongAccent()]
        a3 = [articulations.StrongAccent(), articulations.Accent()]
        a4 = [articulations.StrongAccent(), articulations.Accent(),
             articulations.Tenuto()]
        a5 = [articulations.Accent(), articulations.Tenuto(),
             articulations.StrongAccent()]

        for a, b, c, d, match in [(n1, n4, a1, a1, True),
                (n1, n2, a1, a1, False), (n1, n3, a1, a1, False),
                # same pitch different orderings
                (n1, n4, a2, a3, True), (n1, n4, a4, a5, True),
                # different pitch same orderings
               (n1, n2, a2, a3, False), (n1, n3, a4, a5, False),
            ]:
            a.articulations = c
            b.articulations = d
            self.assertEqual(a==b, match) # sub6



    def testMetricalAccent(self):
        from music21 import meter, stream
        data = [
('4/4', 8, .5, [1.0, 0.125, 0.25, 0.125, 0.5, 0.125, 0.25, 0.125]),
('3/4', 6, .5, [1.0, 0.25, 0.5, 0.25, 0.5, 0.25] ),
('6/8', 6, .5, [1.0, 0.25, 0.25, 0.5, 0.25, 0.25]  ),

('12/32', 12, .125, [1.0, 0.125, 0.125, 0.25, 0.125, 0.125, 0.5, 0.125, 0.125, 0.25, 0.125, 0.125]  ),

('5/8', 10, .25, [1.0, 0.25, 0.5, 0.25, 0.5, 0.25, 0.5, 0.25, 0.5, 0.25]  ),

# test notes that do not have defined accents
('4/4', 16, .25, [1.0, 0.0625, 0.125, 0.0625, 0.25, 0.0625, 0.125, 0.0625, 0.5, 0.0625, 0.125, 0.0625, 0.25, 0.0625, 0.125, 0.0625]),

('4/4', 32, .125, [1.0, 0.0625, 0.0625, 0.0625, 0.125, 0.0625, 0.0625, 0.0625, 0.25, 0.0625, 0.0625, 0.0625, 0.125, 0.0625, 0.0625, 0.0625, 0.5, 0.0625, 0.0625, 0.0625, 0.125, 0.0625, 0.0625, 0.0625, 0.25, 0.0625, 0.0625, 0.0625, 0.125, 0.0625, 0.0625, 0.0625]),


                ]

        for tsStr, nCount, dur, match in data:

            m = stream.Measure()
            m.timeSignature = meter.TimeSignature(tsStr)
            n = Note()
            n.quarterLength = dur
            m.repeatAppend(n, nCount)

            self.assertEqual([n.beatStrength for n in m.notesAndRests], match)


    def testTieContinue(self):
        from music21 import stream

        n1 = Note()
        n1.tie = tie.Tie()
        n1.tie.type = 'start'

        n2 = Note()
        n2.tie = tie.Tie()
        n2.tie.type = 'continue'

        n3 = Note()
        n3.tie = tie.Tie()
        n3.tie.type = 'stop'

        s = stream.Stream()
        s.append([n1, n2, n3])

        # need to test that this gets us a continue tie, but hard to test
        # post musicxml processing
        #s.show()

    def testVolumeA(self):
        v1 = volume.Volume()

        n1 = Note()
        n2 = Note()

        n1.volume = v1 # can set as v1 has no client
        self.assertEqual(n1.volume, v1)
        self.assertEqual(n1.volume.client, n1)

        # object is created on demand
        self.assertEqual(n2.volume is not v1, True)
        self.assertEqual(n2.volume is not None, True)


    def testVolumeB(self):
        # manage deepcopying properly
        n1 = Note()

        n1.volume.velocity = 100
        self.assertEqual(n1.volume.velocity, 100)
        self.assertEqual(n1.volume.client, n1)

        n1Copy = copy.deepcopy(n1)
        self.assertEqual(n1Copy.volume.velocity, 100)
        self.assertEqual(n1Copy.volume.client, n1Copy)

#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Note, Rest, SpacerRest, Unpitched, NotRest, GeneralNote, Lyric]

if __name__ == "__main__":
    # sys.arg test options will be used in mainTest()
    import music21
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof





