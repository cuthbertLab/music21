# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         expressions.py
# Purpose:      notation mods
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#               Neena Parikh
#
# Copyright:    Copyright © 2009-2012 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
This module provides object representations of expressions, that is
notational symbols such as Fermatas, Mordents, Trills, Turns, etc.
which are stored under a Music21Object's .expressions attribute

It also includes representations of things such as TextExpressions which
are better attached to the Stream itself.

TODO: replace .size with a string representing interval and then
    create interval.Interval objects only when necessary.
'''
import copy
import string
import unittest
from typing import List, Optional

from music21 import base
from music21 import common
from music21 import exceptions21
from music21 import interval
from music21 import spanner
from music21 import style

_MOD = 'expressions'


def realizeOrnaments(srcObject):
    '''
    given a Music21Object with Ornament expressions,
    convert them into a list of objects that represents
    the performed version of the object:


    >>> n1 = note.Note('D5')
    >>> n1.quarterLength = 1
    >>> n1.expressions.append(expressions.WholeStepMordent())
    >>> expList = expressions.realizeOrnaments(n1)
    >>> st1 = stream.Stream()
    >>> st1.append(expList)
    >>> #_DOCS_SHOW st1.show()

    .. image:: images/expressionsMordentRealize.*
         :width: 218

    :type srcObject: base.Music21Object
    '''
    if not hasattr(srcObject, 'expressions'):
        return [srcObject]
    elif not srcObject.expressions:
        return [srcObject]
    else:
        preExpandList = []
        postExpandList = []

        loopBuster = 100
        while loopBuster:
            loopBuster -= 1
            thisExpression = srcObject.expressions[0]
            if hasattr(thisExpression, 'realize'):
                preExpand, newSrcObject, postExpand = thisExpression.realize(srcObject)
                for i in preExpand:
                    preExpandList.append(i)
                for i in postExpand:
                    postExpandList.append(i)
                if newSrcObject is None:
                    # some ornaments eat up the entire source object. Trills for instance
                    break
                newSrcObject.expressions = srcObject.expressions[1:]
                srcObject = newSrcObject
                if not srcObject.expressions:
                    break
            else:  # cannot realize this object
                srcObject.expressions = srcObject.expressions[1:]
                if not srcObject.expressions:
                    break

        retList = []
        for i in preExpandList:
            retList.append(i)
        retList.append(srcObject)
        for i in postExpandList:
            retList.append(i)
        return retList


# ------------------------------------------------------------------------------
class ExpressionException(exceptions21.Music21Exception):
    pass


class Expression(base.Music21Object):
    '''
    This base class is inherited by many diverse expressions.
    '''
    _styleClass = style.TextStyle

    def __init__(self):
        super().__init__()
        self.tieAttach = 'first'  # attach to first note of a tied group.

    def _reprInternal(self) -> str:
        return ''

    @property
    def name(self) -> str:
        '''
        returns the name of the expression, which is generally the
        class name lowercased and spaces where a new capital occurs.

        Subclasses can override this as necessary.

        >>> sc = expressions.Schleifer()
        >>> sc.name
        'schleifer'

        >>> iTurn = expressions.InvertedTurn()
        >>> iTurn.name
        'inverted turn'
        '''
        className = self.__class__.__name__
        return common.camelCaseToHyphen(className, replacement=' ')

# ------------------------------------------------------------------------------


class RehearsalMark(Expression):
    '''
    A rehearsal mark is a type of Expression that designates a rehearsal
    marking, such as A., B., etc.

    Takes two inputs, content ('B', 5, 'III') and an optional numbering system which
    is helpful for getting the next rehearsal mark.

    >>> rm = expressions.RehearsalMark('B')
    >>> rm
    <music21.expressions.RehearsalMark 'B'>

    '''
    classSortOrder = -30
    _styleClass = style.TextStylePlacement

    def __init__(self, content=None, *, numbering=None):
        super().__init__()
        self.content = content
        if numbering not in ('alphabetical', 'roman', 'number', None):
            raise ExpressionException(
                'Numbering must be "alphabetical", "roman", "number", or None')
        self.numbering = numbering
        self.style.alignHorizontal = 'center'
        self.style.alignVertical = 'middle'

    def _reprInternal(self):
        return repr(self.content)

    @staticmethod
    def _getNumberingFromContent(c) -> Optional[str]:
        '''
        if numbering was not set, get it from the content

        >>> ex = expressions.RehearsalMark()
        >>> ex._getNumberingFromContent('C')
        'alphabetical'

        >>> ex._getNumberingFromContent('VII')
        'roman'
        >>> ex._getNumberingFromContent('X')
        'roman'
        >>> ex._getNumberingFromContent('CI')
        'roman'

        >>> ex._getNumberingFromContent('5')
        'number'
        >>> ex._getNumberingFromContent(5)
        'number'

        >>> print(ex._getNumberingFromContent('*'))
        None

        '''
        if c is None:
            return None
        if isinstance(c, int):
            return 'number'
        if not isinstance(c, str):
            return None

        try:
            unused = int(c)
            return 'number'
        except ValueError:
            pass

        try:
            romanValue = common.numberTools.fromRoman(c)
            if len(c) >= 2:
                return 'roman'  # two letters is enough

            if romanValue < 50:
                return 'roman'  # I, X, V
            else:
                return 'alphabetical'  # L, C, D, M

        except ValueError:
            pass

        if c in string.ascii_letters:
            return 'alphabetical'
        else:
            return None

    def nextContent(self):
        '''
        Return the next content based on the numbering

        >>> expressions.RehearsalMark('A').nextContent()
        'B'

        >>> expressions.RehearsalMark('II').nextContent()
        'III'

        >>> expressions.RehearsalMark('IV').nextContent()
        'V'

        >>> expressions.RehearsalMark(7).nextContent()
        8

        >>> expressions.RehearsalMark('Z').nextContent()
        'AA'


        With rehearsal mark 'I' default is to consider it
        as a roman numeral:

        >>> expressions.RehearsalMark('I').nextContent()
        'II'

        Specify `numbering` directly to avoid problems:

        >>> expressions.RehearsalMark('I', numbering='alphabetical').nextContent()
        'J'
        '''
        numbering = self.numbering
        if not numbering:
            numbering = self._getNumberingFromContent(self.content)

        if not numbering:
            if self.content is None:
                return None
            # duplicate current content
            return self.content * 2

        if numbering == 'alphabetical':
            nextContent = chr(ord(self.content[-1]) + 1)
            if nextContent not in string.ascii_letters:
                return 'A' * (len(self.content) + 1)
            else:
                return nextContent
        elif numbering == 'number':
            return int(self.content) + 1
        elif numbering == 'roman':
            return common.toRoman(common.fromRoman(self.content) + 1)

    def nextMark(self):
        '''
        Return the next rehearsal mark.

        >>> rm = expressions.RehearsalMark('C')
        >>> rm.nextMark()
        <music21.expressions.RehearsalMark 'D'>


        >>> rm = expressions.RehearsalMark('IV', numbering='roman')
        >>> nm = rm.nextMark()
        >>> nm.content
        'V'
        >>> nm.numbering
        'roman'
        '''
        return RehearsalMark(self.nextContent(), numbering=self.numbering)

# ------------------------------------------------------------------------------


class TextExpressionException(ExpressionException):
    pass


class TextExpression(Expression):
    '''
    A TextExpression is a word, phrase, or similar
    bit of text that is positioned in a Stream or Measure.
    Conventional expressive indications are text
    like "agitato" or "con fuoco."

    >>> te = expressions.TextExpression('Con fuoco')
    >>> te.content
    'Con fuoco'
    >>> te.style.fontSize = 24.0
    >>> te.style.fontSize
    24
    >>> te.style.fontStyle = 'italic'
    >>> te.style.fontWeight = 'bold'
    >>> te.style.letterSpacing = 0.5
    '''

    # always need to be first, before even clefs
    classSortOrder = -30
    _styleClass = style.TextStyle

    def __init__(self, content=None):
        super().__init__()
        # numerous properties are inherited from TextFormat
        # the text string to be displayed; not that line breaks
        # are given in the xml with this non-printing character: (#)
        if not isinstance(content, str):
            self._content = str(content)
        else:
            self._content = content

        self._enclosure = None

        # this does not do anything if default y is defined
        self.positionPlacement = None

    def _reprInternal(self):
        if len(self._content) >= 13:
            shortContent = self._content[:10] + '...'
            return repr(shortContent)
        elif self._content is not None:
            return repr(self._content)
        else:
            return ''

    def _getContent(self):
        return self._content

    def _setContent(self, value):
        self._content = str(value)

    content = property(_getContent, _setContent,
                       doc='''Get or set the content.

        >>> te = expressions.TextExpression('dolce')
        >>> te.content
        'dolce'
        ''')

    # --------------------------------------------------------------------------
    # text expression in musicxml may be repeat expressions
    # need to see if this is a repeat expression, and if so
    # return the appropriate object

    def getRepeatExpression(self):
        '''
        If this TextExpression can be a RepeatExpression,
        return a new :class:`~music21.repeat.RepeatExpression`.
        object, otherwise, return None.
        '''
        # use objects stored in
        # repeat.repeatExpressionReferences for comparison to stored
        # text; if compatible, create and return object
        from music21 import repeat
        for obj in repeat.repeatExpressionReference:
            if obj.isValidText(self._content):
                re = copy.deepcopy(obj)
                # set the text to whatever is used here
                # create a copy of these text expression and set it
                # this will transfer all positional/formatting settings
                re.setTextExpression(copy.deepcopy(self))
                return re
        # if cannot be expressed as a repeat expression
        return None

    def getTempoText(self):
        # TODO: if this TextExpression, once imported, can be a tempo
        # text object, create and return
        pass


# ------------------------------------------------------------------------------
class Ornament(Expression):

    def __init__(self):
        super().__init__()
        self.connectedToPrevious = True
        # should follow directly on previous; true for most "ornaments".

    def realize(self, srcObj):
        '''
        subclassable method call that takes a sourceObject
        and returns a three-element tuple of a list of notes before the
        "main note" or the result of the expression if it gobbles up the entire note,
        the "main note" itself (or None) to keep processing for ornaments,
        and a list of notes after the "main note"
        '''
        return ([], srcObj, [])

    def fillListOfRealizedNotes(
        self,
        srcObj: 'music21.note.Note',
        fillObjects: List['music21.note.Note'],
        transposeInterval
    ):
        '''
        Used by trills and mordants to fill out their realization
        '''
        firstNote = copy.deepcopy(srcObj)
        # TODO: remove expressions
        # firstNote.expressions = None
        # TODO: clear lyrics.
        firstNote.duration.quarterLength = self.quarterLength
        secondNote = copy.deepcopy(srcObj)
        secondNote.duration.quarterLength = self.quarterLength
        # TODO: remove expressions
        # secondNote.expressions = None
        secondNote.transpose(transposeInterval, inPlace=True)

        fillObjects.append(firstNote)
        fillObjects.append(secondNote)


# ------------------------------------------------------------------------------
class GeneralMordent(Ornament):
    '''Base class for all Mordent types.
    '''

    def __init__(self):
        super().__init__()
        self.direction = ''  # up or down
        self.size = None  # interval.Interval (General, etc.) class
        self.quarterLength = 0.125  # 32nd note default
        self.size = interval.Interval(2)

    def realize(self, srcObj: 'music21.note.Note'):
        '''
        Realize a mordent.

        returns a three-element tuple.
        The first is a list of the two notes that the beginning of the note were converted to.
        The second is the rest of the note
        The third is an empty list (since there are no notes at the end of a mordent)

        >>> n1 = note.Note('C4')
        >>> n1.quarterLength = 0.5
        >>> m1 = expressions.Mordent()
        >>> m1.realize(n1)
        ([<music21.note.Note C>, <music21.note.Note B>], <music21.note.Note C>, [])


        Note: use one of the subclasses, not the GeneralMordent class

        >>> n2 = note.Note('C4')
        >>> n2.quarterLength = 0.125
        >>> m2 = expressions.GeneralMordent()
        >>> m2.realize(n2)
        Traceback (most recent call last):
        music21.expressions.ExpressionException: Cannot realize a mordent if I do not
            know its direction
        '''
        from music21 import key

        if self.direction != 'up' and self.direction != 'down':
            raise ExpressionException('Cannot realize a mordent if I do not know its direction')
        if self.size == '':
            raise ExpressionException('Cannot realize a mordent if there is no size given')
        if srcObj.duration is None or srcObj.duration.quarterLength == 0:
            raise ExpressionException('Cannot steal time from an object with no duration')
        if srcObj.duration.quarterLength < self.quarterLength * 2:
            raise ExpressionException('The note is not long enough to realize a mordent')

        remainderDuration = srcObj.duration.quarterLength - (2 * self.quarterLength)
        if self.direction == 'down':
            transposeInterval = self.size.reverse()
        else:
            transposeInterval = self.size
        mordNotes = []
        self.fillListOfRealizedNotes(srcObj, mordNotes, transposeInterval)

        currentKeySig = srcObj.getContextByClass(key.KeySignature)
        if currentKeySig is None:
            currentKeySig = key.KeySignature(0)

        for n in mordNotes:
            n.pitch.accidental = currentKeySig.accidentalByStep(n.step)
        remainderNote = copy.deepcopy(srcObj)
        remainderNote.duration.quarterLength = remainderDuration
        # TODO clear just mordent here...
        return (mordNotes, remainderNote, [])

# ------------------------------------------------------------------------------


class Mordent(GeneralMordent):
    '''
    A normal Mordent.

    >>> m = expressions.Mordent()
    >>> m.direction
    'down'
    >>> m.size
    <music21.interval.Interval M2>
    '''

    def __init__(self):
        super().__init__()
        self.direction = 'down'  # up or down


class HalfStepMordent(Mordent):
    '''
    A half step normal Mordent.

    >>> m = expressions.HalfStepMordent()
    >>> m.direction
    'down'
    >>> m.size
    <music21.interval.Interval m2>
    '''

    def __init__(self):
        super().__init__()
        self.size = interval.Interval('m2')


class WholeStepMordent(Mordent):
    '''
    A whole step normal Mordent.

    >>> m = expressions.WholeStepMordent()
    >>> m.direction
    'down'
    >>> m.size
    <music21.interval.Interval M2>
    '''

    def __init__(self):
        super().__init__()
        self.size = interval.Interval('M2')


# ------------------------------------------------------------------------------
class InvertedMordent(GeneralMordent):
    '''
    An inverted Mordent.

    >>> m = expressions.InvertedMordent()
    >>> m.direction
    'up'
    >>> m.size
    <music21.interval.Interval M2>
    '''

    def __init__(self):
        super().__init__()
        self.direction = 'up'


class HalfStepInvertedMordent(InvertedMordent):
    '''
    A half-step inverted Mordent.

    >>> m = expressions.HalfStepInvertedMordent()
    >>> m.direction
    'up'
    >>> m.size
    <music21.interval.Interval m2>
    '''

    def __init__(self):
        super().__init__()
        self.size = interval.Interval('m2')


class WholeStepInvertedMordent(InvertedMordent):
    '''
    A whole-step inverted Mordent.

    >>> m = expressions.WholeStepInvertedMordent()
    >>> m.direction
    'up'
    >>> m.size
    <music21.interval.Interval M2>
    '''

    def __init__(self):
        super().__init__()
        self.size = interval.Interval('M2')


# ------------------------------------------------------------------------------
class Trill(Ornament):
    '''A basic trill marker.

    >>> m = expressions.Trill()
    >>> m.placement
    'above'
    >>> m.size
    <music21.interval.Interval M2>
    '''

    def __init__(self):
        super().__init__()
        self.size = interval.Interval('M2')

        self.placement = 'above'
        self.nachschlag = False  # play little notes at the end of the trill?
        self.tieAttach = 'all'
        self.quarterLength = 0.125

    def splitClient(self, noteList):
        '''
        splitClient is called by base.splitAtQuarterLength() to support splitting trills.

        >>> n = note.Note(type='whole')
        >>> n.expressions.append(expressions.Trill())
        >>> st = n.splitAtQuarterLength(3.0)
        >>> n1, n2 = st
        >>> st.spannerList
        [<music21.expressions.TrillExtension <music21.note.Note C><music21.note.Note C>>]
        >>> n1.getSpannerSites()
        [<music21.expressions.TrillExtension <music21.note.Note C><music21.note.Note C>>]
        '''
        returnSpanners = []
        if noteList:
            noteList[0].expressions.append(self)
        if len(noteList) > 1 and not noteList[0].getSpannerSites('TrillExtension'):
            te = TrillExtension(noteList)
            returnSpanners.append(te)

        return returnSpanners

    def realize(self, srcObj: 'music21.note.Note'):
        '''
        realize a trill.

        returns a three-element tuple.
        The first is a list of the notes that the note was converted to.
        The second is None because the trill "eats up" the whole note.
        The third is a list of the notes at the end if nachschlag is True, and empty list if False.


        >>> n1 = note.Note('C4')
        >>> n1.quarterLength = 0.5
        >>> t1 = expressions.Trill()
        >>> t1.realize(n1)
        ([<music21.note.Note C>,
          <music21.note.Note D>,
          <music21.note.Note C>,
          <music21.note.Note D>], None, [])


        >>> n2 = note.Note('D4')
        >>> n2.quarterLength = 0.125
        >>> t2 = expressions.Trill()
        >>> t2.realize(n2)
        Traceback (most recent call last):
        music21.expressions.ExpressionException: The note is not long enough to realize a trill

        :type srcObj: base.Music21Object
        '''
        from music21 import key
        if self.size == '':
            raise ExpressionException('Cannot realize a trill if there is no size given')
        if srcObj.duration is None or srcObj.duration.quarterLength == 0:
            raise ExpressionException('Cannot steal time from an object with no duration')
        if srcObj.duration.quarterLength < 2 * self.quarterLength:
            raise ExpressionException('The note is not long enough to realize a trill')
        if srcObj.duration.quarterLength < 4 * self.quarterLength and self.nachschlag:
            raise ExpressionException('The note is not long enough for a nachschlag')

        transposeInterval = self.size
        transposeIntervalReverse = self.size.reverse()

        if self.nachschlag:
            numberOfTrillNotes = int(srcObj.duration.quarterLength / (self.quarterLength - 2))
        else:
            numberOfTrillNotes = int(srcObj.duration.quarterLength / self.quarterLength)

        trillNotes = []
        for unused_counter in range(int(numberOfTrillNotes / 2)):
            self.fillListOfRealizedNotes(srcObj, trillNotes, transposeInterval)

        currentKeySig = srcObj.getContextByClass(key.KeySignature)
        if currentKeySig is None:
            currentKeySig = key.KeySignature(0)

        for n in trillNotes:
            n.pitch.accidental = currentKeySig.accidentalByStep(n.step)

        if self.nachschlag:
            firstNoteNachschlag = copy.deepcopy(srcObj)
            # TODO: remove expressions
            firstNoteNachschlag.duration.quarterLength = self.quarterLength
            firstNoteNachschlag.pitch.accidental = currentKeySig.accidentalByStep(
                firstNoteNachschlag.step)

            secondNoteNachschlag = copy.deepcopy(srcObj)
            # TODO: remove expressions
            secondNoteNachschlag.duration.quarterLength = self.quarterLength
            secondNoteNachschlag.transpose(transposeIntervalReverse,
                                           inPlace=True)
            secondNoteNachschlag.pitch.accidental = currentKeySig.accidentalByStep(
                secondNoteNachschlag.step)

            nachschlag = [firstNoteNachschlag, secondNoteNachschlag]

            return (trillNotes, None, nachschlag)

        else:
            return (trillNotes, None, [])


class HalfStepTrill(Trill):
    '''A basic trill marker.


    >>> m = expressions.HalfStepTrill()
    >>> m.placement
    'above'
    >>> m.size
    <music21.interval.Interval m2>
    '''

    def __init__(self):
        super().__init__()
        self.size = interval.Interval('m2')


class WholeStepTrill(Trill):
    '''A basic trill marker.


    >>> m = expressions.WholeStepTrill()
    >>> m.placement
    'above'
    >>> m.size
    <music21.interval.Interval M2>
    '''

    def __init__(self):
        super().__init__()
        self.size = interval.Interval('M2')


class Shake(Trill):
    def __init__(self):
        super().__init__()
        self.size = interval.Interval('M2')
        self.quarterLength = 0.25


# ------------------------------------------------------------------------------

# TODO: BaroqueSlide
# this is a slide or culee
class Schleifer(Ornament):
    def __init__(self):
        super().__init__()
        self.size = interval.Interval('M2')
        self.quarterLength = 0.25


# ------------------------------------------------------------------------------
class Turn(Ornament):
    def __init__(self):
        super().__init__()
        self.size = interval.Interval('M2')
        self.placement = 'above'
        self.nachschlag = False  # play little notes at the end of the trill?
        self.tieAttach = 'all'
        self.quarterLength = 0.25

    def realize(self, srcObject: 'music21.note.Note'):
        '''
        realize a turn.

        returns a three-element tuple.
        The first is a list of the four notes that the beginning of the note was converted to.
        The second is a note of duration 0 because the turn "eats up" the whole note.
        The third is a list of the notes at the end if nachschlag is True,
        and empty list if False.

        >>> from  music21 import *
        >>> m1 = stream.Measure()
        >>> m1.append(key.Key('F', 'major'))
        >>> n1 = note.Note('C5')
        >>> m1.append(n1)
        >>> t1 = expressions.Turn()
        >>> t1.realize(n1)
        ([], <music21.note.Note C>, [<music21.note.Note D>,
                                     <music21.note.Note C>,
                                     <music21.note.Note B->,
                                     <music21.note.Note C>])


        >>> m2 = stream.Measure()
        >>> m2.append(key.KeySignature(5))
        >>> n2 = note.Note('B4')
        >>> m2.append(n2)
        >>> t2 = expressions.InvertedTurn()
        >>> t2.realize(n2)
        ([], <music21.note.Note B>, [<music21.note.Note A#>,
                                     <music21.note.Note B>,
                                     <music21.note.Note C#>,
                                     <music21.note.Note B>])



        >>> n2 = note.Note('C4')
        >>> n2.quarterLength = 0.125
        >>> t2 = expressions.Turn()
        >>> t2.realize(n2)
        Traceback (most recent call last):
        music21.expressions.ExpressionException: The note is not long enough to realize a turn
        '''
        from music21 import key

        if self.size is None:
            raise ExpressionException('Cannot realize a turn if there is no size given')
        if srcObject.duration is None or srcObject.duration.quarterLength == 0:
            raise ExpressionException('Cannot steal time from an object with no duration')
        if srcObject.duration.quarterLength < 4 * self.quarterLength:
            raise ExpressionException('The note is not long enough to realize a turn')

        remainderDuration = srcObject.duration.quarterLength - 4 * self.quarterLength
        transposeIntervalUp = self.size
        transposeIntervalDown = self.size.reverse()
        turnNotes = []

        # TODO: if nachschlag...

        firstNote = copy.deepcopy(srcObject)
        # TODO: remove expressions
        firstNote.duration.quarterLength = self.quarterLength
        firstNote.transpose(transposeIntervalUp, inPlace=True)

        secondNote = copy.deepcopy(srcObject)
        # TODO: remove expressions
        secondNote.duration.quarterLength = self.quarterLength

        thirdNote = copy.deepcopy(srcObject)
        # TODO: remove expressions
        thirdNote.duration.quarterLength = self.quarterLength
        thirdNote.transpose(transposeIntervalDown, inPlace=True)

        fourthNote = copy.deepcopy(srcObject)
        # TODO: remove expressions
        fourthNote.duration.quarterLength = self.quarterLength

        turnNotes.append(firstNote)
        turnNotes.append(secondNote)
        turnNotes.append(thirdNote)
        turnNotes.append(fourthNote)

        currentKeySig = srcObject.getContextByClass(key.KeySignature)
        if currentKeySig is None:
            currentKeySig = key.KeySignature(0)

        for n in turnNotes:
            n.pitch.accidental = currentKeySig.accidentalByStep(n.step)

        remainderNote = copy.deepcopy(srcObject)
        remainderNote.duration.quarterLength = remainderDuration

        return ([], remainderNote, turnNotes)


class InvertedTurn(Turn):
    def __init__(self):
        super().__init__()
        self.size = self.size.reverse()


# ------------------------------------------------------------------------------
class GeneralAppoggiatura(Ornament):
    # up or down -- up means the grace note is below and goes up to the actual note
    direction = ''
    size = None  # interval.Interval (General, etc.) class

    def __init__(self):
        super().__init__()
        self.size = interval.Interval(2)

    def realize(self, srcObj):
        '''
        realize an appoggiatura

        returns a three-element tuple.
        The first is the list of notes that the grace note was converted to.
        The second is the rest of the note
        The third is an empty list (since there are no notes at the end of an appoggiatura)

        >>> n1 = note.Note('C4')
        >>> n1.quarterLength = 0.5
        >>> a1 = expressions.Appoggiatura()
        >>> a1.realize(n1)
        ([<music21.note.Note D>], <music21.note.Note C>, [])


        >>> n2 = note.Note('C4')
        >>> n2.quarterLength = 1
        >>> a2 = expressions.HalfStepInvertedAppoggiatura()
        >>> a2.realize(n2)
        ([<music21.note.Note B>], <music21.note.Note C>, [])

        :type srcObj: base.Music21Object
        '''
        from music21 import key
        if self.direction != 'up' and self.direction != 'down':
            raise ExpressionException(
                'Cannot realize an Appoggiatura if I do not know its direction')
        if self.size == '':
            raise ExpressionException(
                'Cannot realize an Appoggiatura if there is no size given')
        if srcObj.duration is None or srcObj.duration.quarterLength == 0:
            raise ExpressionException('Cannot steal time from an object with no duration')

        newDuration = srcObj.duration.quarterLength / 2
        if self.direction == 'down':
            transposeInterval = self.size
        else:
            transposeInterval = self.size.reverse()

        appoggiaturaNote = copy.deepcopy(srcObj)
        appoggiaturaNote.duration.quarterLength = newDuration
        appoggiaturaNote.transpose(transposeInterval, inPlace=True)

        remainderNote = copy.deepcopy(srcObj)
        remainderNote.duration.quarterLength = newDuration

        currentKeySig = srcObj.getContextByClass(key.KeySignature)
        if currentKeySig is None:
            currentKeySig = key.KeySignature(0)

        # TODO clear just mordent here...
        return ([appoggiaturaNote], remainderNote, [])


class Appoggiatura(GeneralAppoggiatura):
    direction = 'down'


class HalfStepAppoggiatura(Appoggiatura):
    def __init__(self):
        super().__init__()
        self.size = interval.Interval('m2')


class WholeStepAppoggiatura(Appoggiatura):
    def __init__(self):
        super().__init__()
        self.size = interval.Interval('M2')


class InvertedAppoggiatura(GeneralAppoggiatura):
    direction = 'up'


class HalfStepInvertedAppoggiatura(InvertedAppoggiatura):
    def __init__(self):
        super().__init__()
        self.size = interval.Interval('m2')


class WholeStepInvertedAppoggiatura(InvertedAppoggiatura):
    def __init__(self):
        super().__init__()
        self.size = interval.Interval('M2')

# ------------------------------------------------------------------------------


class TremoloException(exceptions21.Music21Exception):
    pass


class Tremolo(Ornament):
    '''
    A tremolo ornament represents a single-note tremolo, whether measured or unmeasured.

    >>> n = note.Note(type='quarter')
    >>> t = expressions.Tremolo()
    >>> t.measured = True  # default
    >>> t.numberOfMarks = 3  # default


    >>> t.numberOfMarks = 'Hi'
    Traceback (most recent call last):
    music21.expressions.TremoloException: Number of marks must be a number from 0 to 8

    >>> t.numberOfMarks = -1
    Traceback (most recent call last):
    music21.expressions.TremoloException: Number of marks must be a number from 0 to 8


    TODO: (someday) realize triplet Tremolos, etc. differently from other tremolos.
    TODO: deal with unmeasured tremolos.
    '''

    def __init__(self):
        super().__init__()
        self.measured = True
        self._numberOfMarks = 3

    @property
    def numberOfMarks(self):
        '''
        The number of marks on the note.  Currently completely controls playback.
        '''
        return self._numberOfMarks

    @numberOfMarks.setter
    def numberOfMarks(self, num):
        try:
            num = int(num)
            if num < 0 or num > 8:
                raise ValueError(str(num))
            self._numberOfMarks = num
        except ValueError as ve:
            raise TremoloException(
                'Number of marks must be a number from 0 to 8'
            ) from ve

    def realize(self, srcObj: 'music21.note.Note'):
        '''
        Realize the ornament

        >>> n = note.Note(type='quarter')
        >>> t = expressions.Tremolo()
        >>> t.measured = True  # default
        >>> t.numberOfMarks = 3  # default
        >>> t.realize(n)
        ([<music21.note.Note C>, <music21.note.Note C>, <music21.note.Note C>,
          <music21.note.Note C>, <music21.note.Note C>, <music21.note.Note C>,
          <music21.note.Note C>, <music21.note.Note C>], None, [])
        >>> c2 = t.realize(n)[0]
        >>> [ts.quarterLength for ts in c2]
        [0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125]

        Same thing with Streams:

        >>> n = note.Note(type='quarter')
        >>> t = expressions.Tremolo()
        >>> n.expressions.append(t)
        >>> s = stream.Stream()
        >>> s.append(n)
        >>> s.show('text')
        {0.0} <music21.note.Note C>

        >>> y = stream.makeNotation.realizeOrnaments(s)
        >>> y.show('text')
        {0.0} <music21.note.Note C>
        {0.125} <music21.note.Note C>
        {0.25} <music21.note.Note C>
        {0.375} <music21.note.Note C>
        {0.5} <music21.note.Note C>
        {0.625} <music21.note.Note C>
        {0.75} <music21.note.Note C>
        {0.875} <music21.note.Note C>


        >>> t.numberOfMarks = 1
        >>> y = stream.makeNotation.realizeOrnaments(s)
        >>> y.show('text')
        {0.0} <music21.note.Note C>
        {0.5} <music21.note.Note C>
        '''
        lengthOfEach = 2**(-1 * self.numberOfMarks)
        objsConverted = []
        eRemain = copy.deepcopy(srcObj)
        if self in eRemain.expressions:
            eRemain.expressions.remove(self)
        while eRemain is not None and eRemain.quarterLength > lengthOfEach:
            addNote, eRemain = eRemain.splitAtQuarterLength(lengthOfEach, retainOrigin=False)
            objsConverted.append(addNote)

        if eRemain is not None:
            objsConverted.append(eRemain)

        return (objsConverted, None, [])

# ------------------------------------------------------------------------------

class Fermata(Expression):
    '''
    Fermatas by default get appended to the last
    note if a note is split because of measures.

    To override this (for Fermatas or for any
    expression) set .tieAttach to 'all' or 'first'
    instead of 'last'.


    >>> p1 = stream.Part()
    >>> p1.append(meter.TimeSignature('6/8'))
    >>> n1 = note.Note('D-2')
    >>> n1.quarterLength = 6
    >>> n1.expressions.append(expressions.Fermata())
    >>> p1.append(n1)
    >>> #_DOCS_SHOW p1.show()
    .. image:: images/expressionsFermata.*
         :width: 193
    '''

    def __init__(self):
        super().__init__()
        self.shape = 'normal'  # angled, square.
        # for musicmxml, can be upright or inverted, but Finale's idea of an
        # inverted fermata is backwards.
        self.type = 'inverted'
        self.tieAttach = 'last'


# ------------------------------------------------------------------------------
# spanner expressions

class TrillExtensionException(exceptions21.Music21Exception):
    pass


class TrillExtension(spanner.Spanner):
    '''
    A wavy line trill extension, placed between two notes. N
    ote that some MusicXML readers include a trill symbol with the wavy line.


    >>> s = stream.Stream()
    >>> s.repeatAppend(note.Note(), 8)

    Create TrillExtension between notes 2 and 3

    >>> te = expressions.TrillExtension(s.notes[1], s.notes[2])
    >>> s.append(te)  # spanner can go anywhere in the Stream
    >>> print(te)
    <music21.expressions.TrillExtension <music21.note.Note C><music21.note.Note C>>
    '''
    # musicxml defines a start, stop, and a continue; will try to avoid continue
    # note that this always includes a trill symbol

    def __init__(self, *arguments, **keywords):
        super().__init__(*arguments, **keywords)
        self._placement = None  # can above or below or None, after musicxml

    def _getPlacement(self):
        return self._placement

    def _setPlacement(self, value):
        if value is not None and value.lower() not in ['above', 'below']:
            raise TrillExtensionException('incorrect placement value: %s' % value)
        if value is not None:
            self._placement = value.lower()

    placement = property(_getPlacement, _setPlacement, doc='''
        Get or set the placement as either above, below, or None.

        >>> s = stream.Stream()
        >>> s.repeatAppend(note.Note(), 8)
        >>> te = expressions.TrillExtension(s.notes[1], s.notes[2])
        >>> te.placement = 'above'
        >>> te.placement
        'above'
        ''')


class TremoloSpanner(spanner.Spanner):
    '''
    A tremolo that spans multiple notes

    >>> ts = expressions.TremoloSpanner()
    >>> n1 = note.Note('C')
    >>> n2 = note.Note('D')
    >>> ts.addSpannedElements([n1, n2])
    >>> ts.numberOfMarks = 2
    >>> ts
    <music21.expressions.TremoloSpanner <music21.note.Note C><music21.note.Note D>>

    >>> ts.numberOfMarks = -1
    Traceback (most recent call last):
    music21.expressions.TremoloException: Number of marks must be a number from 0 to 8
    '''
    # musicxml defines a start, stop, and a continue; will try to avoid continue

    def __init__(self, *arguments, **keywords):
        super().__init__(*arguments, **keywords)
        self.placement = None
        self.measured = True
        self._numberOfMarks = 3

    @property
    def numberOfMarks(self):
        '''
        The number of marks on the note.  Will eventually control playback.
        '''
        return self._numberOfMarks

    @numberOfMarks.setter
    def numberOfMarks(self, num):
        try:
            num = int(num)
            if num < 0 or num > 8:
                raise ValueError(str(num))
            self._numberOfMarks = num
        except ValueError as ve:
            raise TremoloException('Number of marks must be a number from 0 to 8') from ve


# ------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def x_testRealize(self):
        from music21 import note
        from music21 import stream
        n1 = note.Note('D4')
        n1.quarterLength = 4
        n1.expressions.append(WholeStepMordent())
        expList = realizeOrnaments(n1)
        st1 = stream.Stream()
        st1.append(expList)
        st1n = st1.notes
        self.assertEqual(st1n[0].name, 'D')
        self.assertEqual(st1n[0].quarterLength, 0.125)
        self.assertEqual(st1n[1].name, 'C')
        self.assertEqual(st1n[1].quarterLength, 0.125)
        self.assertEqual(st1n[2].name, 'D')
        self.assertEqual(st1n[2].quarterLength, 3.75)

    def testGetRepeatExpression(self):
        from music21 import expressions

        te = expressions.TextExpression('lightly')
        # no repeat expression is possible
        self.assertEqual(te.getRepeatExpression(), None)

        te = expressions.TextExpression('d.c.')
        self.assertEqual(str(te.getRepeatExpression()),
                         "<music21.repeat.DaCapo 'd.c.'>")
        re = te.getRepeatExpression()
        self.assertEqual(re.getTextExpression().content, 'd.c.')

        te = expressions.TextExpression('DC al coda')
        self.assertEqual(str(te.getRepeatExpression()),
                         "<music21.repeat.DaCapoAlCoda 'DC al coda'>")
        re = te.getRepeatExpression()
        self.assertEqual(re.getTextExpression().content, 'DC al coda')

        te = expressions.TextExpression('DC al fine')
        self.assertEqual(str(te.getRepeatExpression()),
                         "<music21.repeat.DaCapoAlFine 'DC al fine'>")
        re = te.getRepeatExpression()
        self.assertEqual(re.getTextExpression().content, 'DC al fine')

        te = expressions.TextExpression('ds al coda')
        self.assertEqual(str(te.getRepeatExpression()),
                         "<music21.repeat.DalSegnoAlCoda 'ds al coda'>")
        re = te.getRepeatExpression()
        self.assertEqual(re.getTextExpression().content, 'ds al coda')

        te = expressions.TextExpression('d.s. al fine')
        self.assertEqual(str(te.getRepeatExpression()),
                         "<music21.repeat.DalSegnoAlFine 'd.s. al fine'>")
        re = te.getRepeatExpression()
        self.assertEqual(re.getTextExpression().content, 'd.s. al fine')

    def x_testExpandTurns(self):
        from music21 import note, stream, clef, key, meter
        p1 = stream.Part()
        m1 = stream.Measure()
        m2 = stream.Measure()
        p1.append(clef.TrebleClef())
        p1.append(key.Key('F', 'major'))
        p1.append(meter.TimeSignature('2/4'))
        n1 = note.Note('C5', type='half')
        n1.expressions.append(Turn())
        n2 = note.Note('B4', type='half')
        n2.expressions.append(InvertedTurn())
        m1.append(n1)
        m2.append(key.KeySignature(5))
        m2.append(n2)
        p1.append(m1)
        p1.append(m2)
        # print(realizeOrnaments(n1))
        # print(realizeOrnaments(n2))

    def x_testExpandTrills(self):
        from music21 import note, stream, clef, key, meter
        p1 = stream.Part()
        m1 = stream.Measure()
        p1.append(clef.TrebleClef())
        p1.append(key.Key('D', 'major'))
        p1.append(meter.TimeSignature('2/4'))
        n1 = note.Note('E4', type='eighth')
        n1.expressions.append(Trill())
        m1.append(n1)
        p1.append(m1)
        # print(realizeOrnaments(n1))

    # def testCPEBachRealizeOrnaments(self):
    #     from music21 import corpus
    #     cpe = corpus.parse('cpebach/h186').parts[0].measures(1, 4)
    #     cpe2 = cpe.realizeOrnaments()
    #     cpe2.show()

    def testTrillExtensionA(self):
        '''Test basic wave line creation and output, as well as passing
        objects through make measure calls.
        '''
        from music21 import stream, note, chord, expressions
        from music21.musicxml import m21ToXml
        s = stream.Stream()
        s.repeatAppend(note.Note(), 12)
        n1 = s.notes[0]
        n2 = s.notes[-1]
        sp1 = expressions.TrillExtension(n1, n2)
        s.append(sp1)
        raw = m21ToXml.GeneralObjectExporter().parse(s)
        self.assertEqual(raw.count(b'wavy-line'), 2)

        s = stream.Stream()
        s.repeatAppend(chord.Chord(['c-3', 'g4']), 12)
        n1 = s.notes[0]
        n2 = s.notes[-1]
        sp1 = expressions.TrillExtension(n1, n2)
        s.append(sp1)
        raw = m21ToXml.GeneralObjectExporter().parse(s)
        # s.show()
        self.assertEqual(raw.count(b'wavy-line'), 2)


# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [TextExpression]

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)

