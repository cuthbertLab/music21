# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         expressions.py
# Purpose:      Expressions such as Fermatas, etc.
#
# Authors:      Michael Scott Asato Cuthbert
#               Christopher Ariza
#               Neena Parikh
#
# Copyright:    Copyright © 2009-2023 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
This module provides object representations of expressions, that is
notational symbols such as Fermatas, Mordents, Trills, Turns, etc.
which are stored under a Music21Object's .expressions attribute.

A sub-category of Expressions are Ornaments.

Unlike articulations, expressions can be attached to the Stream itself.
For instance, TextExpressions.
'''
from __future__ import annotations

import copy
import string
import typing as t
from fractions import Fraction

from music21 import base
from music21 import common
from music21.common.enums import OrnamentDelay
from music21.common.numberTools import opFrac
from music21.common.types import OffsetQL
from music21 import exceptions21
from music21 import interval
from music21 import key
from music21 import pitch
from music21 import spanner
from music21 import style


if t.TYPE_CHECKING:
    from music21 import note


def isUnison(intv: interval.IntervalBase) -> bool:
    if isinstance(intv, interval.Interval):
        return intv.name == 'P1' and intv.chromatic.semitones == 0
    elif isinstance(intv, interval.DiatonicInterval):
        return intv.name == 'P1'
    elif isinstance(intv, interval.ChromaticInterval):
        return intv.semitones == 0
    return False

def realizeOrnaments(
    srcObj: note.Note | note.Unpitched,
    *,
    keySig: key.KeySignature | None = None
):
    '''
    given a Note or Unpitched with Ornament expressions,
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
    '''
    srcObject: note.Note | note.Unpitched | None = srcObj
    if t.TYPE_CHECKING:
        # it comes in as not None
        assert srcObject is not None

    if not hasattr(srcObject, 'expressions'):
        return [srcObject]
    elif not srcObject.expressions:
        return [srcObject]
    else:
        preExpandList = []
        postExpandList = []

        loopBuster = 100
        while loopBuster:
            if t.TYPE_CHECKING:
                # if it was set to None, we break out of the loop, so we won't get here
                assert srcObject is not None
            loopBuster -= 1
            thisExpression = srcObject.expressions[0]
            if hasattr(thisExpression, 'realize'):
                preExpand, newSrcObject, postExpand = thisExpression.realize(
                    srcObject, keySig=keySig
                )
                for i in preExpand:
                    preExpandList.append(i)
                for i in postExpand:
                    postExpandList.append(i)
                if newSrcObject is None:
                    # some ornaments eat up the entire source object. Trills for instance
                    srcObject = newSrcObject
                    break
                newSrcObject.expressions = srcObject.expressions[1:]
                srcObject = newSrcObject
                if t.TYPE_CHECKING:
                    # if newSrcObject/srcObject were None, we would have broken out of the loop
                    assert srcObject is not None
                if not srcObject.expressions:
                    break
            else:  # cannot realize this object
                srcObject.expressions = srcObject.expressions[1:]
                if not srcObject.expressions:
                    break

        retList = []
        # TODO: use extend...
        for i in preExpandList:
            retList.append(i)
        if srcObject is not None:
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

    def __init__(self, **keywords):
        super().__init__(**keywords)
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

    def __init__(self, content=None, *, numbering=None, **keywords):
        super().__init__(**keywords)
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
    def _getNumberingFromContent(c) -> str | None:
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
class TextExpression(Expression):
    '''
    A TextExpression is a word, phrase, or similar
    bit of text that is positioned in a Stream or Measure.
    Conventional expressive indications are text
    like "agitato" or "con fuoco."

    >>> te = expressions.TextExpression('Con fuoco')
    >>> te.content
    'Con fuoco'

    Most configuration of style is done
    on the `.style` :class:`~music21.style.TextStyle` object
    itself.

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

    _DOC_ATTR: dict[str, str] = {
        'placement': '''
            Staff placement: 'above', 'below', or None.

            A setting of None implies that the placement will be determined
            by notation software and no particular placement is demanded.

            This is not placed in the `.style` property, since for some
            expressions, the placement above or below an object has semantic
            meaning and is not purely presentational.
            ''',
    }

    def __init__(self, content=None, **keywords):
        super().__init__(**keywords)
        # numerous properties are inherited from TextFormat
        # the text string to be displayed; not that line breaks
        # are given in the xml with this non-printing character: (#)
        if not isinstance(content, str):
            self._content = str(content)
        else:
            self._content = content

        # this does not do anything if default y is defined
        self.placement = None

    def _reprInternal(self):
        if len(self._content) >= 13:
            shortContent = self._content[:10] + '...'
            return repr(shortContent)
        elif self._content is not None:
            return repr(self._content)
        else:
            return ''

    @property
    def enclosure(self) -> style.Enclosure | None:
        '''
        Returns or sets the enclosure on the Style object
        stored on .style.

        Exposed directly on the expression for backwards
        compatibility.  Does not create a .style object if
        one does not exist and the value is None.

        >>> te = expressions.TextExpression('Bridge')
        >>> te.enclosure is None
        True
        >>> te.enclosure = style.Enclosure.RECTANGLE
        >>> te.enclosure
        <Enclosure.RECTANGLE>

        Note that this is also set on `.style`.

        >>> te.style.enclosure
        <Enclosure.RECTANGLE>
        '''
        if not self.hasStyleInformation:
            return None
        return self.style.enclosure

    @enclosure.setter
    def enclosure(self, value: style.Enclosure | None):
        if not self.hasStyleInformation and value is None:
            return
        self.style.enclosure = value

    @property
    def content(self):
        '''
        Get or set the content.

        >>> te = expressions.TextExpression('dolce')
        >>> te.content
        'dolce'
        >>> te.content = 'sweeter'
        >>> te
        <music21.expressions.TextExpression 'sweeter'>
        '''
        return self._content

    @content.setter
    def content(self, value):
        self._content = str(value)


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
        # Return None if it cannot be expressed as a repeat expression
        return None

    def getTempoText(self):
        # TODO: if this TextExpression, once imported, can be a tempo
        # text object, create and return
        pass


# ------------------------------------------------------------------------------
class Ornament(Expression):
    '''
    An Ornament is a type of Expression that, when attached to a Note
    (in the future: Notes) can transform into the main note.

    All ornaments have an `.autoScale` boolean which determines
    whether to shrink (not currently to expand) the ornament if the
    note it is attached to is too short to realize.
    '''
    def __init__(self, **keywords) -> None:
        super().__init__(**keywords)
        # should follow directly on previous; true for most "ornaments".
        self.connectedToPrevious = True
        self.autoScale = True
        self._ornamentalPitches: tuple[pitch.Pitch, ...] = ()

    def realize(
        self,
        srcObj: note.Note | note.Unpitched,
        *,
        keySig: key.KeySignature | None = None,
        inPlace: bool = False
    ) -> tuple[list[note.Note | note.Unpitched],
                note.Note | note.Unpitched | None,
                list[note.Note | note.Unpitched]]:
        '''
        subclassable method call that takes a sourceObject and optional keySig
        and returns a three-element tuple of a list of notes before the
        "main note" or the result of the expression if it gobbles up the entire note,
        the "main note" itself (or None) to keep processing for ornaments,
        and a list of notes after the "main note".

        * New in v8: inPlace boolean; note that some ornaments
          might not return a Note in the second position at all (such as trills)
          so inPlace does nothing.
        * Changed in v9: Optional keySig can be passed in (useful in cases where there
          is no keySig in srcObj's context, or where a different keySig is desired).
        '''
        if not inPlace:
            srcObj = copy.deepcopy(srcObj)

        return ([], srcObj, [])

    def fillListOfRealizedNotes(
        self,
        srcObj: note.Note | note.Unpitched,
        fillObjects: list[note.Note | note.Unpitched],
        transposeInterval: interval.IntervalBase,
        *,
        useQL: OffsetQL | None = None
    ) -> None:
        '''
        Used by trills and mordents to fill out their realization.
        '''
        isTransposed: bool = not isUnison(transposeInterval)
        if isTransposed and not hasattr(srcObj, 'transpose'):
            raise TypeError(f'Expected note; got {type(srcObj)}')

        if useQL is None:
            useQL = self.quarterLength

        firstNote = copy.deepcopy(srcObj)
        # TODO: remove expressions
        # firstNote.expressions = None
        # TODO: clear lyrics.
        firstNote.duration.quarterLength = useQL
        secondNote = copy.deepcopy(srcObj)
        secondNote.duration.quarterLength = useQL
        # TODO: remove expressions
        # secondNote.expressions = None
        if isTransposed:
            if t.TYPE_CHECKING:
                assert isinstance(secondNote, note.Note)
            secondNote.transpose(transposeInterval, inPlace=True)

        fillObjects.append(firstNote)
        fillObjects.append(secondNote)

    def resolveOrnamentalPitches(
        self,
        srcObj: note.GeneralNote,
        *,
        keySig: key.KeySignature | None = None
    ):
        '''
        Only implemented in Turn, GeneralMordent, and Trill.
        '''
        return

    @property
    def ornamentalPitches(self) -> tuple[pitch.Pitch, ...]:
        '''
        Only implemented in Turn, GeneralMordent, and Trill.
        '''
        return tuple()

    def updateAccidentalDisplay(
        self,
        *,
        pitchPast: list[pitch.Pitch] | None = None,
        pitchPastMeasure: list[pitch.Pitch] | None = None,
        otherSimultaneousPitches: list[pitch.Pitch] | None = None,
        alteredPitches: list[pitch.Pitch] | None = None,
        cautionaryPitchClass: bool = True,
        cautionaryAll: bool = False,
        overrideStatus: bool = False,
        cautionaryNotImmediateRepeat: bool = True,
    ) -> None:
        '''
        Only implemented in Turn, GeneralMordent, and Trill.
        '''
        return


# ------------------------------------------------------------------------------
class GeneralMordent(Ornament):
    '''
    Base class for all Mordent types.
    '''
    _direction: str = ''  # up or down

    def __init__(self, *, accidental: pitch.Accidental | None = None, **keywords):
        super().__init__(**keywords)
        self._accidental: pitch.Accidental | None = accidental
        self.quarterLength = 0.125  # 32nd note default
        self.placement = 'above'

    @property
    def name(self) -> str:
        '''
        returns the name of the Mordent/InvertedMordent, which is generally
        the class name lowercased, with spaces where a new capital occurs. The
        name also will include any accidental, if it exists.

        Subclasses can override this as necessary.

        >>> mordent = expressions.Mordent()
        >>> mordent.name
        'mordent'

        >>> sharp = pitch.Accidental('sharp')
        >>> invertedMordent = expressions.InvertedMordent(accidental=sharp)
        >>> invertedMordent.name
        'inverted mordent (sharp)'

        '''
        theName: str = super().name
        if self.accidental is not None:
            theName += ' (' + self.accidental.name + ')'
        return theName

    @property
    def accidental(self) -> pitch.Accidental | None:
        '''
        This is the GeneralMordent's accidental.
        '''
        return self._accidental

    @accidental.setter
    def accidental(self, newAccidental: pitch.Accidental | None):
        self._accidental = newAccidental

    @property
    def direction(self) -> str:
        '''
        The direction of the mordent's ornamental pitch from the main note.
        Can be 'up' or 'down'.
        '''
        return self._direction

    def getSize(
        self,
        srcObj: note.GeneralNote,
        *,
        keySig: key.KeySignature | None = None,
    ) -> interval.IntervalBase:
        '''
        Returns the size of the mordent's interval, given a source note and
        an optional key signature.  If the key signature is not specified, the
        source note's context is searched for the current key signature, and if
        there is no such key signature, a key signature with no sharps and no flats
        will be used.  Any `accidental` that has been set on the mordent will also
        be taken into account.  If no `accidental` has been set, the appropriate
        accidental from the key signature will be used.

        If keySig is specified, this can be considered to be a theoretical question:
        "If this particular mordent were to be attached to this note, in this key,
        what would the size of the mordent interval be?"
        '''
        if self._direction not in ('up', 'down'):
            raise ExpressionException('Cannot compute mordent size if I do not know its direction')

        if not srcObj.pitches:
            # perfect unison
            return interval.Interval('P1')

        # Use keySig if passed in, else use keySig from context, else no sharps or flats.
        keySig = keySig or srcObj.getContextByClass(key.KeySignature) or key.KeySignature(0)

        srcPitch: pitch.Pitch = srcObj.pitches[-1]

        ornamentalPitch: pitch.Pitch = copy.deepcopy(srcPitch)
        ornamentalPitch.accidental = None
        if ornamentalPitch.octave is None:
            ornamentalPitch.octave = ornamentalPitch.implicitOctave

        if self._direction == 'up':
            ornamentalPitch.transpose(interval.GenericInterval(2), inPlace=True)
        else:
            ornamentalPitch.transpose(interval.GenericInterval(-2), inPlace=True)

        if self.accidental:
            ornamentalPitch.accidental = self.accidental
        else:
            # use whatever accidental the key signature says
            ornamentalPitch.accidental = keySig.accidentalByStep(ornamentalPitch.step)

        return interval.Interval(srcPitch, ornamentalPitch)

    def resolveOrnamentalPitches(
        self,
        srcObj: note.GeneralNote,
        *,
        keySig: key.KeySignature | None = None
    ):
        '''
        Computes and stores the ornamental pitch for a GeneralMordent, given the srcObj
        (can be any kind of ornamented GeneralNote) and an optional keySig.

        If keySig is None, srcNote's context will be searched for a key signature.
        If no key signature is found, a key signature with no sharps and no flats
        will be used.


        A mordent on a G in a key with no sharps or flats (ornamental pitch will be F).

        >>> noSharpsOrFlats = key.KeySignature(sharps=0)
        >>> n1 = note.Note('G4')
        >>> mordent = expressions.Mordent()
        >>> mordent.resolveOrnamentalPitches(n1, keySig=noSharpsOrFlats)
        >>> mordent.ornamentalPitches
        (<music21.pitch.Pitch F4>,)
        >>> mordent.ornamentalPitch
        <music21.pitch.Pitch F4>

        e.g. A mordent on a G in a key with one sharp (ornamental pitch will be F#).

        >>> oneSharp = key.KeySignature(sharps=1)
        >>> mordent.resolveOrnamentalPitches(n1, keySig=oneSharp)
        >>> mordent.ornamentalPitches
        (<music21.pitch.Pitch F#4>,)
        >>> mordent.ornamentalPitch
        <music21.pitch.Pitch F#4>

        e.g. A mordent with a natural, on a G, in a key with one sharp
        (ornamental pitch will be F).

        >>> mordent.accidental = pitch.Accidental('natural')
        >>> mordent.resolveOrnamentalPitches(n1, keySig=oneSharp)
        >>> mordent.ornamentalPitches
        (<music21.pitch.Pitch F4>,)
        >>> mordent.ornamentalPitch
        <music21.pitch.Pitch F4>
        '''
        if not srcObj.pitches:
            # There are no ornamental pitches relative to this srcObj
            return

        srcPitch: pitch.Pitch = srcObj.pitches[-1]
        transposeInterval: interval.IntervalBase = self.getSize(srcObj, keySig=keySig)

        ornamentalPitch: pitch.Pitch = copy.deepcopy(srcPitch)
        if ornamentalPitch.octave is None:
            ornamentalPitch.octave = ornamentalPitch.implicitOctave
        ornamentalPitch.transpose(transposeInterval, inPlace=True)
        # if there are microtones, see if they can be converted to quarter tones.
        if ornamentalPitch.microtone.cents != 0:
            ornamentalPitch.convertMicrotonesToQuarterTones(inPlace=True)

        if self.accidental is not None:
            # Note that we don't need to look at what the accidental actually is,
            # since that has already been incorporated into transposeInterval and the
            # ornamentalPitch via the call to getSize()/srcPitch.transpose().  But if
            # accidental is set at all, we need to copy the displayStatus.
            if ornamentalPitch.accidental is None:
                ornamentalPitch.accidental = pitch.Accidental(0)
            ornamentalPitch.accidental.displayStatus = self.accidental.displayStatus
        self._ornamentalPitches = (ornamentalPitch,)

    @property
    def ornamentalPitch(self) -> pitch.Pitch | None:
        '''
        Returns the mordent's ornamentalPitch.  If resolveOrnamentalPitches
        has not yet been called, None is returned.
        '''
        if self._ornamentalPitches:
            return self._ornamentalPitches[0]
        return None

    @property
    def ornamentalPitches(self) -> tuple[pitch.Pitch, ...]:
        '''
        Returns any ornamental pitch that has been resolved (see
        `resolveOrnamentalPitches`, which must be called first, or an
        empty tuple will be returned).
        '''
        return self._ornamentalPitches

    def updateAccidentalDisplay(
        self,
        *,
        pitchPast: list[pitch.Pitch] | None = None,
        pitchPastMeasure: list[pitch.Pitch] | None = None,
        otherSimultaneousPitches: list[pitch.Pitch] | None = None,
        alteredPitches: list[pitch.Pitch] | None = None,
        cautionaryPitchClass: bool = True,
        cautionaryAll: bool = False,
        overrideStatus: bool = False,
        cautionaryNotImmediateRepeat: bool = True,
    ):
        '''
        Updates accidental display for a GeneralMordent's ornamental pitch.
        Defined exactly like Pitch.updateAccidentalDisplay, with two changes:
        Instead of self being the pitch to update, self is a GeneralMordent whose
        ornamentalPitch is to be updated; and we pay no attention to ties,
        since ornamental notes cannot be tied.
        '''
        p = self.ornamentalPitch
        if p is None:
            return

        if self.accidental is not None and self.accidental.displayStatus is not None:
            # copy accidental visibility from self.accidental
            if p.accidental is None:
                p.accidental = pitch.Accidental(0)
            p.accidental.displayStatus = self.accidental.displayStatus
            return

        p.updateAccidentalDisplay(
            pitchPast=pitchPast,
            pitchPastMeasure=pitchPastMeasure,
            alteredPitches=alteredPitches,
            cautionaryPitchClass=cautionaryPitchClass,
            cautionaryAll=cautionaryAll,
            overrideStatus=overrideStatus,
            cautionaryNotImmediateRepeat=cautionaryNotImmediateRepeat,
            lastNoteWasTied=False)

    def realize(
        self,
        srcObj: note.Note | note.Unpitched,
        *,
        keySig: key.KeySignature | None = None,
        inPlace: bool = False
    ) -> tuple[list[note.Note | note.Unpitched],
                note.Note | note.Unpitched | None,
                list[note.Note | note.Unpitched]]:
        '''
        Realize a mordent.

        returns a three-element tuple.
        The first is a list of the two notes that the beginning of the note were converted to.
        The second is the rest of the note.
        The third is an empty list (since there are no notes at the end of a mordent).

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
        if self._direction not in ('up', 'down'):
            raise ExpressionException('Cannot realize a mordent if I do not know its direction')
        if srcObj.duration.quarterLength == 0:
            raise ExpressionException('Cannot steal time from an object with no duration')

        use_ql = self.quarterLength
        if srcObj.duration.quarterLength <= self.quarterLength * 2:
            if not self.autoScale:
                raise ExpressionException('The note is not long enough to realize a mordent')
            use_ql = srcObj.duration.quarterLength / 4

        currentKeySig: key.KeySignature | None = keySig
        if currentKeySig is None:
            currentKeySig = srcObj.getContextByClass(key.KeySignature)
            if currentKeySig is None:
                currentKeySig = key.KeySignature(0)

        remainderQL = srcObj.duration.quarterLength - (2 * use_ql)
        transposeInterval = self.getSize(srcObj, keySig=currentKeySig)
        mordNotes: list[note.Note | note.Unpitched] = []
        self.fillListOfRealizedNotes(srcObj, mordNotes, transposeInterval, useQL=use_ql)

        isTransposed: bool = not isUnison(transposeInterval)
        if isTransposed:
            # second (middle) note might need an accidental from the keysig (but
            # only if it doesn't already have an accidental, from self.accidental)
            for noteIdx, n in enumerate(mordNotes):
                if t.TYPE_CHECKING:
                    assert isinstance(n, note.Note)
                noteNum: int = noteIdx + 1
                if n.pitch.accidental is None and noteNum == 2:
                    n.pitch.accidental = currentKeySig.accidentalByStep(n.pitch.step)

        inExpressions = -1
        if self in srcObj.expressions:
            inExpressions = srcObj.expressions.index(self)

        remainderNote = copy.deepcopy(srcObj) if not inPlace else srcObj
        remainderNote.duration.quarterLength = remainderQL
        if inExpressions != -1:
            remainderNote.expressions.pop(inExpressions)

        return (mordNotes, remainderNote, [])

# ------------------------------------------------------------------------------


class Mordent(GeneralMordent):
    '''
    A normal Mordent -- goes downwards and has a line through it.

    Note that some computer terminology calls this one an inverted mordent, but this
    is a modern term.  See Apel, *Harvard Dictionary of Music*, "Mordent"::

        A musical ornament consisting of the alternation of the written note
        with the note immediately below it.


    A mordent has the size of a second, of some form, depending on the note
    that will have the mordent, the current key signature in that note's context, as
    well as any accidental on the mordent itself.

    e.g. Mordent without accidentals in default key (no flats or sharps)

    >>> m = expressions.Mordent()
    >>> m.direction
    'down'
    >>> m.getSize(note.Note('C4'))
    <music21.interval.Interval m-2>
    >>> m.getSize(note.Note('B3'))
    <music21.interval.Interval M-2>

    e.g. Mordent with flat, in default key (no flats or sharps)

    >>> mFlat = expressions.Mordent(accidental=pitch.Accidental('flat'))
    >>> mFlat.direction
    'down'
    >>> mFlat.getSize(note.Note('C4'))
    <music21.interval.Interval M-2>
    >>> mFlat.getSize(note.Note('B3'))
    <music21.interval.Interval A-2>

    e.g. Mordent without accidentals, in key with one flat

    >>> oneFlat = key.KeySignature(-1)
    >>> mNotFlat = expressions.Mordent()
    >>> mNotFlat.direction
    'down'
    >>> mNotFlat.getSize(note.Note('C4'), keySig=oneFlat)
    <music21.interval.Interval M-2>
    >>> mNotFlat.getSize(note.Note('B3'), keySig=oneFlat)
    <music21.interval.Interval M-2>

    e.g. Mordent without accidentals, with a key from context with one flat (same results)

    >>> noteC4 = note.Note('C4')
    >>> noteB3 = note.Note('B3')
    >>> measure = stream.Measure([oneFlat, noteC4, noteB3])
    >>> mNotFlatWithKeyFromContext = expressions.Mordent()
    >>> mNotFlatWithKeyFromContext.direction
    'down'
    >>> mNotFlatWithKeyFromContext.getSize(noteC4)
    <music21.interval.Interval M-2>
    >>> mNotFlatWithKeyFromContext.getSize(noteB3)
    <music21.interval.Interval M-2>



    * Changed in v7: Mordent sizes are GenericIntervals -- as was originally
      intended but programmed incorrectly.
    * Changed in v9: Support an accidental on Mordent. This also adds the concept of
      an ornamental pitch that is processed by makeAccidentals.
      The size property has been removed and replaced with `.getSize()` (which requires
      a `srcObj` and optional `keySig` param).  Added optional `keySig` param to
      `.realize()` as well.
    '''
    _direction: str = 'down'  # up or down


class HalfStepMordent(Mordent):
    '''
    A half step normal Mordent.

    >>> m = expressions.HalfStepMordent()
    >>> m.direction
    'down'
    >>> m.getSize(note.Note('C4'))
    <music21.interval.Interval m-2>
    '''
    def __init__(self, **keywords) -> None:
        # no accidental supported here, just "HalfStep"
        if 'accidental' in keywords:
            raise ExpressionException('Cannot initialize HalfStepMordent with accidental')
        super().__init__(**keywords)
        self._minorSecondDown: interval.IntervalBase = interval.Interval('m-2')

    def getSize(
        self,
        srcObj: note.GeneralNote,
        *,
        keySig: key.KeySignature | None = None,
    ) -> interval.IntervalBase:
        return self._minorSecondDown

    @property
    def accidental(self) -> pitch.Accidental | None:
        return None

    @accidental.setter
    def accidental(self, newAccidental: pitch.Accidental | None):
        raise ExpressionException('Cannot set accidental of HalfStepMordent')


class WholeStepMordent(Mordent):
    '''
    A whole step normal Mordent.

    >>> m = expressions.WholeStepMordent()
    >>> m.direction
    'down'
    >>> m.getSize(note.Note('C4'))
    <music21.interval.Interval M-2>
    '''
    def __init__(self, **keywords) -> None:
        # no accidental supported here, just "WholeStep"
        if 'accidental' in keywords:
            raise ExpressionException('Cannot initialize WholeStepMordent with accidental')
        super().__init__(**keywords)
        self._majorSecondDown: interval.IntervalBase = interval.Interval('M-2')

    def getSize(
        self,
        srcObj: note.GeneralNote,
        *,
        keySig: key.KeySignature | None = None,
    ) -> interval.IntervalBase:
        return self._majorSecondDown

    @property
    def accidental(self) -> pitch.Accidental | None:
        return None

    @accidental.setter
    def accidental(self, newAccidental: pitch.Accidental | None):
        raise ExpressionException('Cannot set accidental of WholeStepMordent')


# ------------------------------------------------------------------------------
class InvertedMordent(GeneralMordent):
    '''
    An inverted Mordent -- goes upwards and has no line through it.

    Note that some computer terminology calls this one a (normal) mordent, but this
    is a modern term.    See Apel, *Harvard Dictionary of Music*,
    "Inverted Mordent"::

        An 18th-century ornament involving alternation of the
        written note with the note immediately above it.

    An inverted mordent has the size of a second, of some form, depending on the note
    that will have the mordent, the current key signature in that note's context, as
    well as any accidental on the mordent itself.

    >>> m = expressions.InvertedMordent()
    >>> m.direction
    'up'
    >>> m.getSize(note.Note('C4'))
    <music21.interval.Interval M2>
    >>> m.getSize(note.Note('B3'))
    <music21.interval.Interval m2>

    >>> mSharp = expressions.InvertedMordent(accidental=pitch.Accidental('sharp'))
    >>> mSharp.direction
    'up'
    >>> mSharp.getSize(note.Note('C4'))
    <music21.interval.Interval A2>
    >>> mSharp.getSize(note.Note('B3'))
    <music21.interval.Interval M2>

    * Changed in v7: InvertedMordent sizes are GenericIntervals -- as was originally
      intended but programmed incorrectly.
    * Changed in v9: Support an accidental on InvertedMordent. This also adds the concept of
      an ornamental pitch that is processed by makeAccidentals.
      The size property has been removed and replaced with `.getSize()` (which requires
      a `srcObj` and optional `keySig` param).  Added optional `keySig` param to
      `.realize()` as well.
    '''
    _direction: str = 'up'


class HalfStepInvertedMordent(InvertedMordent):
    '''
    A half-step inverted Mordent.

    >>> m = expressions.HalfStepInvertedMordent()
    >>> m.direction
    'up'
    >>> m.getSize(note.Note('C4'))
    <music21.interval.Interval m2>
    '''
    def __init__(self, **keywords) -> None:
        # no accidental supported here, just "HalfStep"
        if 'accidental' in keywords:
            raise ExpressionException(
                'Cannot initialize HalfStepInvertedMordent with accidental')
        super().__init__(**keywords)
        self._minorSecondUp: interval.IntervalBase = interval.Interval('m2')

    def getSize(
        self,
        srcObj: note.GeneralNote,
        *,
        keySig: key.KeySignature | None = None,
    ) -> interval.IntervalBase:
        return self._minorSecondUp

    @property
    def accidental(self) -> pitch.Accidental | None:
        return None

    @accidental.setter
    def accidental(self, newAccidental: pitch.Accidental | None):
        raise ExpressionException('Cannot set accidental of HalfStepInvertedMordent')


class WholeStepInvertedMordent(InvertedMordent):
    '''
    A whole-step inverted Mordent.

    >>> m = expressions.WholeStepInvertedMordent()
    >>> m.direction
    'up'
    >>> m.getSize(note.Note('C4'))
    <music21.interval.Interval M2>
    '''
    def __init__(self, **keywords) -> None:
        # no accidental supported here, just "WholeStep"
        if 'accidental' in keywords:
            raise ExpressionException(
                'Cannot initialize WholeStepInvertedMordent with accidental')
        super().__init__(**keywords)
        self._majorSecondUp: interval.IntervalBase = interval.Interval('M2')

    def getSize(
        self,
        srcObj: note.GeneralNote,
        *,
        keySig: key.KeySignature | None = None,
    ) -> interval.IntervalBase:
        return self._majorSecondUp

    @property
    def accidental(self) -> pitch.Accidental | None:
        return None

    @accidental.setter
    def accidental(self, newAccidental: pitch.Accidental | None):
        raise ExpressionException('Cannot set accidental of WholeStepInvertedMordent')


# ------------------------------------------------------------------------------
class Trill(Ornament):
    '''
    A basic trill marker without the trill extension

    >>> tr = expressions.Trill()
    >>> tr.placement
    'above'
    >>> tr.getSize(note.Note('C4'))
    <music21.interval.Interval M2>
    >>> tr.getSize(note.Note('B4'))
    <music21.interval.Interval m2>

    Trills have a `.nachschlag` attribute which determines whether there
    should be extra gracenotes at the end of the trill.

    >>> tr.nachschlag
    False
    >>> tr.nachschlag = True

    The Trill also has a "quarterLength" attribute that sets how long
    each trill note should be.  Defaults to 32nd note:

    >>> tr.quarterLength
    0.125
    >>> tr.quarterLength == duration.Duration('32nd').quarterLength
    True

    * Changed in v7: the size should be a generic second.
    * Changed in v9: Support an accidental on trills. This also adds the concept of
      an ornamental pitch that is processed by makeAccidentals.
      The size property has been removed and replaced with `.getSize()` (which requires
      a `srcObj` and optional `keySig` param).  Added optional `keySig` param to
      `.realize()` as well.

    '''
    _direction: str = 'up'

    def __init__(self, *, accidental: pitch.Accidental | None = None, **keywords) -> None:
        super().__init__(**keywords)
        self._accidental: pitch.Accidental | None = accidental
        self.placement = 'above'
        self.nachschlag = False  # play little notes at the end of the trill?
        self.tieAttach = 'all'
        self.quarterLength = 0.125
        self._setAccidentalFromKeySig = True

    @property
    def name(self) -> str:
        '''
        returns the name of the Trill, which is generally the class name
        lowercased, with spaces where a new capital occurs. The name also
        will include the accidental, if it exists.

        Subclasses can override this as necessary.

        >>> trill = expressions.Trill()
        >>> trill.name
        'trill'

        >>> doubleSharpedTrill = expressions.Trill(accidental=pitch.Accidental('double-sharp'))
        >>> doubleSharpedTrill.name
        'trill (double-sharp)'

        '''
        theName: str = super().name
        if self.accidental:
            theName += ' (' + self.accidental.name + ')'
        return theName

    @property
    def direction(self) -> str:
        '''
        The direction of the trill's ornamental pitch from the main note.
        Can be 'up' or 'down'.
        '''
        return self._direction

    @property
    def accidental(self) -> pitch.Accidental | None:
        '''
        This is the Trill's accidental.  Whether or not it is visible is dictated by
        the accidental's displayStatus.
        '''
        return self._accidental

    @accidental.setter
    def accidental(self, newAccidental: pitch.Accidental | None):
        self._accidental = newAccidental

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

    def getSize(
        self,
        srcObj: note.GeneralNote,
        *,
        keySig: key.KeySignature | None = None,
    ) -> interval.IntervalBase:
        '''
        Returns the size of the trill's interval, given a source note and
        an optional key signature.  If the key signature is not specified, the
        source note's context is searched for the current key signature, and if
        there is no such key signature, a key signature with no sharps and no flats
        will be used.  Any `accidental` that has been set on the trill will also
        be taken into account.

        If keySig is specified, this can be considered to be a theoretical question:
        "If this particular trill were to be attached to this note, in this key,
        what would the size of the trill interval be?"
        '''
        if self._direction not in ('up', 'down'):
            raise ExpressionException('Cannot compute trill size if I do not know its direction')

        if not srcObj.pitches:
            # perfect unison (e.g. snare drum "trill")
            return interval.Interval('P1')

        # Use keySig if passed in, else use keySig from context, else no sharps or flats.
        keySig = keySig or srcObj.getContextByClass(key.KeySignature) or key.KeySignature(0)

        srcPitch: pitch.Pitch = srcObj.pitches[-1]

        ornamentalPitch: pitch.Pitch = copy.deepcopy(srcPitch)
        ornamentalPitch.accidental = None
        if ornamentalPitch.octave is None:
            ornamentalPitch.octave = ornamentalPitch.implicitOctave

        if self._direction == 'up':
            ornamentalPitch.transpose(interval.GenericInterval(2), inPlace=True)
        else:
            ornamentalPitch.transpose(interval.GenericInterval(-2), inPlace=True)

        if self.accidental:
            ornamentalPitch.accidental = self.accidental
        else:
            # use whatever accidental the key signature says
            ornamentalPitch.accidental = keySig.accidentalByStep(ornamentalPitch.step)

        return interval.Interval(srcPitch, ornamentalPitch)

    def resolveOrnamentalPitches(
        self,
        srcObj: note.GeneralNote,
        *,
        keySig: key.KeySignature | None = None
    ):
        '''
        Computes and stores the ornamental pitch for a Trill, given the srcObj
        (can be any kind of ornamented GeneralNote) and an optional keySig.

        If keySig is None, srcNote's context will be searched for a key signature.
        If no key signature is found, a key signature with no sharps and no flats
        will be used.

        e.g. A trill on a D in a key with no sharps or flats (ornamental pitch will be E).

        >>> noSharpsOrFlats = key.KeySignature(0)
        >>> n2 = note.Note('D4')
        >>> trill = expressions.Trill()
        >>> trill.resolveOrnamentalPitches(n2, keySig=noSharpsOrFlats)
        >>> trill.ornamentalPitches
        (<music21.pitch.Pitch E4>,)
        >>> trill.ornamentalPitch
        <music21.pitch.Pitch E4>
        '''
        if not srcObj.pitches:
            # There are no ornamental pitches relative to this srcObj
            return

        srcPitch: pitch.Pitch = srcObj.pitches[-1]
        transposeInterval: interval.IntervalBase = self.getSize(srcObj, keySig=keySig)

        ornamentalPitch: pitch.Pitch = copy.deepcopy(srcPitch)
        if ornamentalPitch.octave is None:
            ornamentalPitch.octave = ornamentalPitch.implicitOctave
        ornamentalPitch.transpose(transposeInterval, inPlace=True)
        # if there are microtones, see if they can be converted to quarter tones.
        if ornamentalPitch.microtone.cents != 0:
            ornamentalPitch.convertMicrotonesToQuarterTones(inPlace=True)

        if self.accidental is not None:
            # Note that we don't need to look at what the accidental actually is,
            # since that has already been incorporated into transposeInterval and the
            # ornamentalPitch via the call to getSize()/srcPitch.transpose().  But we
            # do need to copy self.accidental.displayStatus.
            if ornamentalPitch.accidental is None:
                ornamentalPitch.accidental = pitch.Accidental(0)
            ornamentalPitch.accidental.displayStatus = self.accidental.displayStatus
        self._ornamentalPitches = (ornamentalPitch,)

    @property
    def ornamentalPitch(self) -> pitch.Pitch | None:
        '''
        Returns the trill's ornamentalPitch.  If resolveOrnamentalPitches
        has not yet been called, None is returned.
        '''
        if self._ornamentalPitches:
            return self._ornamentalPitches[0]
        return None

    @property
    def ornamentalPitches(self) -> tuple[pitch.Pitch, ...]:
        '''
        Returns any ornamental pitch that has been resolved (see
        `resolveOrnamentalPitches`, which must be called first, or an
        empty tuple will be returned).
        '''
        return self._ornamentalPitches

    def updateAccidentalDisplay(
        self,
        *,
        pitchPast: list[pitch.Pitch] | None = None,
        pitchPastMeasure: list[pitch.Pitch] | None = None,
        otherSimultaneousPitches: list[pitch.Pitch] | None = None,
        alteredPitches: list[pitch.Pitch] | None = None,
        cautionaryPitchClass: bool = True,
        cautionaryAll: bool = False,
        overrideStatus: bool = False,
        cautionaryNotImmediateRepeat: bool = True,
    ):
        '''
        Updates accidental display for a Trill's ornamental pitch.
        Defined exactly like Pitch.updateAccidentalDisplay, with two changes:
        Instead of self being the pitch to update, self is an Trill whose
        ornamentalPitch is to be updated; and we pay no attention to ties,
        since ornamental notes cannot be tied.

        These examples show a Trill whose main note is a G in a key with no sharps or
        flats, so the trill's ornamental pitch is an A. We show various situations
        where the A might or might not end up with a natural accidental.

        If updateAccidentalDisplay is called with cautionaryAll, the A gets a (cautionary)
        natural accidental.

        >>> noSharpsOrFlats = key.KeySignature(0)
        >>> trill1 = expressions.Trill()
        >>> trill1.resolveOrnamentalPitches(note.Note('g4'), keySig=noSharpsOrFlats)
        >>> trill1.ornamentalPitch
        <music21.pitch.Pitch A4>
        >>> trill1.ornamentalPitch.accidental is None
        True
        >>> past = [pitch.Pitch('a#4'), pitch.Pitch('c#4'), pitch.Pitch('c4')]
        >>> trill1.updateAccidentalDisplay(pitchPast=past, cautionaryAll=True)
        >>> trill1.ornamentalPitch.accidental, trill1.ornamentalPitch.accidental.displayStatus
        (<music21.pitch.Accidental natural>, True)

        If updateAccidentalDisplay is called without cautionaryAll, the A gets a natural
        accidental, because a previous A had a sharp accidental.

        >>> trill2 = expressions.Trill()
        >>> trill2.resolveOrnamentalPitches(note.Note('g4'), keySig=noSharpsOrFlats)
        >>> trill2.ornamentalPitch
        <music21.pitch.Pitch A4>
        >>> trill2.ornamentalPitch.accidental is None
        True
        >>> past = [pitch.Pitch('a#4'), pitch.Pitch('c#4'), pitch.Pitch('c4')]
        >>> trill2.updateAccidentalDisplay(pitchPast=past)  # should add a natural
        >>> trill2.ornamentalPitch.accidental, trill2.ornamentalPitch.accidental.displayStatus
        (<music21.pitch.Accidental natural>, True)

        If updateAccidentalDisplay is called with cautionaryPitchClass=False, the A does
        not get a natural accidental because the previous A# was in a different octave.

        >>> trill3 = expressions.Trill()
        >>> trill3.resolveOrnamentalPitches(note.Note('g4'), keySig=noSharpsOrFlats)
        >>> trill3.ornamentalPitch
        <music21.pitch.Pitch A4>
        >>> trill3.ornamentalPitch.accidental is None
        True
        >>> past = [pitch.Pitch('a#3'), pitch.Pitch('c#'), pitch.Pitch('c')]
        >>> trill3.updateAccidentalDisplay(pitchPast=past, cautionaryPitchClass=False)
        >>> trill3.ornamentalPitch.accidental is None
        True

        If we add a natural accidental to the trill (with displayStatus True), and then
        updateAccidentalDisplay is called with cautionaryPitchClass=False, the A gets a
        visible natural accidental because of that added natural accidental.

        >>> trill4 = expressions.Trill()
        >>> natural = pitch.Accidental('natural')
        >>> natural.displayStatus = True
        >>> trill4.accidental = natural
        >>> trill4.resolveOrnamentalPitches(note.Note('g4'), keySig=noSharpsOrFlats)
        >>> trill4.ornamentalPitch
        <music21.pitch.Pitch A4>
        >>> trill4.ornamentalPitch.accidental
        <music21.pitch.Accidental natural>
        >>> trill4.ornamentalPitch.accidental.displayStatus
        True
        >>> past = [pitch.Pitch('a#3'), pitch.Pitch('c#'), pitch.Pitch('c')]
        >>> trill4.updateAccidentalDisplay(pitchPast=past, cautionaryPitchClass=False)
        >>> trill4.ornamentalPitch.accidental
        <music21.pitch.Accidental natural>
        >>> trill4.ornamentalPitch.accidental.displayStatus
        True
        '''
        p = self.ornamentalPitch
        if p is None:
            return

        if self.accidental:
            # copy displayStatus from self.accidental
            if p.accidental is None:
                p.accidental = pitch.Accidental(0)
            p.accidental.displayStatus = self.accidental.displayStatus
            return

        p.updateAccidentalDisplay(
            pitchPast=pitchPast,
            pitchPastMeasure=pitchPastMeasure,
            alteredPitches=alteredPitches,
            cautionaryPitchClass=cautionaryPitchClass,
            cautionaryAll=cautionaryAll,
            overrideStatus=overrideStatus,
            cautionaryNotImmediateRepeat=cautionaryNotImmediateRepeat,
            lastNoteWasTied=False)

    def realize(
        self,
        srcObj: note.Note | note.Unpitched,
        *,
        keySig: key.KeySignature | None = None,
        inPlace: bool = False
    ) -> tuple[list[note.Note | note.Unpitched],
                note.Note | note.Unpitched | None,
                list[note.Note | note.Unpitched]]:
        '''
        realize a trill.

        Returns a three-element tuple:

        * The first is a list of the notes that the note was converted to.
        * The second is None because the trill "eats up" the whole note.
        * The third is a list of the notes at the end if nachschlag is True,
          and empty list if False.

        >>> n1 = note.Note('C4')
        >>> n1.duration.type = 'eighth'
        >>> t1 = expressions.Trill()
        >>> n1.expressions.append(t1)
        >>> realization = t1.realize(n1)
        >>> realization
        ([<music21.note.Note C>,
          <music21.note.Note D>,
          <music21.note.Note C>,
          <music21.note.Note D>], None, [])
        >>> realization[0][0].quarterLength
        0.125
        >>> realization[0][0].pitch.octave
        4

        When inside a stream, the realizations will consult the current key to see
        if it should be a whole-step or half-step trill:

        >>> m = stream.Measure()
        >>> k1 = key.Key('D-')
        >>> m.insert(0, k1)
        >>> m.append(n1)
        >>> t1.realize(n1)
        ([<music21.note.Note C>,
          <music21.note.Note D->,
          <music21.note.Note C>,
          <music21.note.Note D->], None, [])

        Note that if the key contradicts the note of the trill, for instance, here
        having a C-natural rather than a C-sharp, we do not correct the C to C#.

        >>> k2 = key.Key('A')
        >>> m.replace(k1, k2)
        >>> t1.realize(n1)
        ([<music21.note.Note C>,
          <music21.note.Note D>,
          <music21.note.Note C>,
          <music21.note.Note D>], None, [])

        This can lead to certain unusual circumstances such as augmented second trills
        which are technically correct, but probably not what a performer exprects.

        >>> k3 = key.Key('E')
        >>> m.replace(k2, k3)
        >>> t1.realize(n1)
        ([<music21.note.Note C>,
          <music21.note.Note D#>,
          <music21.note.Note C>,
          <music21.note.Note D#>], None, [])


        To avoid this case, create a :class:`~music21.expressions.HalfStepTrill` or
        :class:`~music21.expressions.WholeStepTrill`.

        If there is a nachschlag, it will appear in the third element of the list.

        >>> n1.duration.type = 'quarter'
        >>> m.replace(k3, k1)  # back to D-flat major
        >>> t1.nachschlag = True
        >>> t1.realize(n1)
        ([<music21.note.Note C>,
          <music21.note.Note D->,
          <music21.note.Note C>,
          <music21.note.Note D->,
          <music21.note.Note C>,
          <music21.note.Note D->], None, [<music21.note.Note C>, <music21.note.Note B->])

        Some notes can be too short to realize if autoscale is off.

        >>> n2 = note.Note('D4')
        >>> n2.duration.type = '32nd'
        >>> t2 = expressions.Trill()
        >>> t2.autoScale = False
        >>> t2.realize(n2)
        Traceback (most recent call last):
        music21.expressions.ExpressionException: The note is not long enough to realize a trill

        A quicker trill makes it possible:

        >>> t2.quarterLength = duration.Duration('64th').quarterLength
        >>> t2.realize(n2)
        ([<music21.note.Note D>,
          <music21.note.Note E>], None, [])

        inPlace is not used for Trills.
        '''
        useQL = self.quarterLength
        if srcObj.duration.quarterLength == 0:
            raise ExpressionException('Cannot steal time from an object with no duration')
        if srcObj.duration.quarterLength < 2 * useQL:
            if not self.autoScale:
                raise ExpressionException('The note is not long enough to realize a trill')
            useQL = srcObj.duration.quarterLength / 2
        if srcObj.duration.quarterLength < 4 * self.quarterLength and self.nachschlag:
            if not self.autoScale:
                raise ExpressionException('The note is not long enough for a nachschlag')
            useQL = srcObj.duration.quarterLength / 4

        currentKeySig = keySig
        if currentKeySig is None:
            currentKeySig = srcObj.getContextByClass(key.KeySignature)
            if currentKeySig is None:
                currentKeySig = key.KeySignature(0)

        transposeInterval = self.getSize(srcObj, keySig=currentKeySig)
        transposeIntervalReverse = transposeInterval.reverse()
        isTransposed: bool = not isUnison(transposeInterval)

        numberOfTrillNotes = int(srcObj.duration.quarterLength / useQL)
        if self.nachschlag:
            numberOfTrillNotes -= 2

        trillNotes: list[note.Note | note.Unpitched] = []
        for unused_counter in range(int(numberOfTrillNotes / 2)):
            self.fillListOfRealizedNotes(srcObj, trillNotes, transposeInterval, useQL=useQL)

        if isTransposed:
            setAccidentalFromKeySig = self._setAccidentalFromKeySig
            if setAccidentalFromKeySig:
                for n in trillNotes:
                    if t.TYPE_CHECKING:
                        assert isinstance(n, note.Note)
                        assert isinstance(srcObj, note.Note)
                    if n.pitch.nameWithOctave != srcObj.pitch.nameWithOctave:
                        # do not correct original note, no matter what.
                        if n.pitch.accidental is None:
                            # correct if there isn't already an accidental (from self.accidental)
                            n.pitch.accidental = (
                                currentKeySig.accidentalByStep(n.step)
                            )

        if inPlace and self in srcObj.expressions:
            srcObj.expressions.remove(self)

        if self.nachschlag:
            firstNoteNachschlag = copy.deepcopy(srcObj)
            firstNoteNachschlag.expressions = []
            firstNoteNachschlag.duration.quarterLength = useQL

            secondNoteNachschlag = copy.deepcopy(srcObj)
            secondNoteNachschlag.expressions = []
            secondNoteNachschlag.duration.quarterLength = useQL
            if isTransposed:
                if t.TYPE_CHECKING:
                    assert isinstance(secondNoteNachschlag, note.Note)
                    assert isinstance(firstNoteNachschlag, note.Note)
                secondNoteNachschlag.transpose(transposeIntervalReverse,
                                                inPlace=True)
                if setAccidentalFromKeySig and currentKeySig:
                    firstNoteNachschlag.pitch.accidental = currentKeySig.accidentalByStep(
                        firstNoteNachschlag.step)
                    secondNoteNachschlag.pitch.accidental = currentKeySig.accidentalByStep(
                        secondNoteNachschlag.step)

            nachschlag = [firstNoteNachschlag, secondNoteNachschlag]

            return (trillNotes, None, nachschlag)

        else:
            return (trillNotes, None, [])


class InvertedTrill(Trill):
    _direction: str = 'down'


class HalfStepTrill(Trill):
    '''
    A trill confined to half steps.

    >>> halfTrill = expressions.HalfStepTrill()
    >>> halfTrill.placement
    'above'
    >>> halfTrill.getSize(note.Note('C4'))
    <music21.interval.Interval m2>

    Here the key signature of 2 sharps will not affect the trill:

    >>> n = note.Note('B4', type='eighth')
    >>> m = stream.Measure()
    >>> m.insert(0, key.KeySignature(2))
    >>> m.append(n)
    >>> halfTrill.realize(n)
    ([<music21.note.Note B>,
      <music21.note.Note C>,
      <music21.note.Note B>,
      <music21.note.Note C>], None, [])
    '''
    def __init__(self, **keywords) -> None:
        # no accidental supported here, just "HalfStep"
        if 'accidental' in keywords:
            raise ExpressionException(
                'Cannot initialize HalfStepTrill with accidental')
        super().__init__(**keywords)
        self._minorSecondUp: interval.IntervalBase = interval.Interval('m2')
        self._setAccidentalFromKeySig = False

    def getSize(
        self,
        srcObj: note.GeneralNote,
        *,
        keySig: key.KeySignature | None = None,
    ) -> interval.IntervalBase:
        return self._minorSecondUp

    @property
    def accidental(self) -> pitch.Accidental | None:
        return None

    @accidental.setter
    def accidental(self, newAccidental: pitch.Accidental | None):
        raise ExpressionException('Cannot set accidental of HalfStepTrill')


class WholeStepTrill(Trill):
    '''
    A trill that yields whole steps no matter what.

    >>> wholeTrill = expressions.WholeStepTrill()
    >>> wholeTrill.placement
    'above'
    >>> wholeTrill.getSize(note.Note('C4'))
    <music21.interval.Interval M2>

    Here the key signature of one sharp will not affect the trill:

    >>> n = note.Note('B4', type='eighth')
    >>> m = stream.Measure()
    >>> m.insert(0, key.KeySignature(1))
    >>> m.append(n)
    >>> wholeTrill.realize(n)
    ([<music21.note.Note B>,
      <music21.note.Note C#>,
      <music21.note.Note B>,
      <music21.note.Note C#>], None, [])
    '''
    def __init__(self, **keywords) -> None:
        # no accidental supported here, just "WholeStep"
        if 'accidental' in keywords:
            raise ExpressionException(
                'Cannot initialize WholeStepTrill with accidental')
        super().__init__(**keywords)
        self._majorSecondUp: interval.IntervalBase = interval.Interval('M2')
        self._setAccidentalFromKeySig = False

    def getSize(
        self,
        srcObj: note.GeneralNote,
        *,
        keySig: key.KeySignature | None = None,
    ) -> interval.IntervalBase:
        return self._majorSecondUp

    @property
    def accidental(self) -> pitch.Accidental | None:
        return None

    @accidental.setter
    def accidental(self, newAccidental: pitch.Accidental | None):
        raise ExpressionException('Cannot set accidental of WholeStepTrill')


class Shake(Trill):
    '''
    A slower trill.

    >>> shake = expressions.Shake()
    >>> shake.quarterLength
    0.25
    '''
    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.quarterLength = 0.25


# ------------------------------------------------------------------------------

# TODO: BaroqueSlide

class Schleifer(Ornament):
    '''
    A slide or culee

    * Changed in v7: size is a Generic second.  removed unused nachschlag component.
    '''
    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.size = interval.GenericInterval(2)
        self.quarterLength = 0.25


# ------------------------------------------------------------------------------
class Turn(Ornament):
    '''
    A turn or Gruppetto.

    * Changed in v7: size is a Generic second.  removed unused nachschlag component.
    * Changed in v9: Added support for delayed vs non-delayed Turn.
    * Changed in v9: Support upper and lower accidentals on turns. This also adds
      the concept of ornamental pitches that are processed by makeAccidentals.
      The size property has been removed and replaced with `.getSize()` (which requires
      a `srcObj` and optional `keySig` param, as well as which='upper' or which='lower').
      Added optional `keySig` param to `.realize()` as well.
    '''
    _isInverted: bool = False

    def __init__(
        self,
        *,
        delay: OrnamentDelay | OffsetQL = OrnamentDelay.NO_DELAY,
        upperAccidental: pitch.Accidental | None = None,
        lowerAccidental: pitch.Accidental | None = None,
        **keywords
    ):
        super().__init__(**keywords)
        self._upperAccidental: pitch.Accidental | None = upperAccidental
        self._lowerAccidental: pitch.Accidental | None = lowerAccidental
        self.placement: str = 'above'
        self.tieAttach: str = 'all'
        self.quarterLength: OffsetQL = 0.25
        self._delay: OrnamentDelay | OffsetQL = 0.0
        self.delay = delay  # use property setter

    @property
    def upperAccidental(self) -> pitch.Accidental | None:
        '''
        This is the Turn's upperAccidental. Whether or not it is visible is dictated by
        the upperAccidental's displayStatus.
        '''
        return self._upperAccidental

    @upperAccidental.setter
    def upperAccidental(self, newUpperAccidental: pitch.Accidental | None):
        self._upperAccidental = newUpperAccidental

    @property
    def lowerAccidental(self) -> pitch.Accidental | None:
        '''
        This is the Turn's lowerAccidental. Whether or not it is visible is dictated by
        the upperAccidental's displayStatus.
        '''
        return self._lowerAccidental

    @lowerAccidental.setter
    def lowerAccidental(self, newLowerAccidental: pitch.Accidental | None):
        self._lowerAccidental = newLowerAccidental

    @property
    def delay(self) -> OrnamentDelay | OffsetQL:
        '''
        If delay is NO_DELAY, the turn is not delayed.

        If delay is anything else (an OffsetQL or DEFAULT_DELAY), the turn is delayed.

        Note that if you set delay to OffsetQL(0), and then get the delay, you will
        get NO_DELAY, not 0.
        '''
        return self._delay

    @delay.setter
    def delay(self, newDelay: OrnamentDelay | OffsetQL):
        # we convert to OrnamentDelay if possible now, to simplify life later
        if isinstance(newDelay, (float, Fraction)) and newDelay <= 0:
            newDelay = OrnamentDelay.NO_DELAY
        self._delay = newDelay

    @property
    def isDelayed(self) -> bool:
        '''
        Whether the Turn is delayed (i.e. between a specific note and the following note) or
        not (i.e. exactly on a specific note).
        '''
        return self.delay != OrnamentDelay.NO_DELAY

    @property
    def name(self) -> str:
        '''
        returns the name of the Turn/InvertedTurn, which is generally the class
        name lowercased, with spaces where a new capital occurs, but also with
        a 'delayed' prefix, if the Turn/InvertedTurn is delayed.  If the delay
        is of a specific duration, the prefix will include that duration. The
        name also will include upper and lower accidentals, if they exist.

        Subclasses can override this as necessary.

        >>> nonDelayedTurn = expressions.Turn()
        >>> nonDelayedTurn.name
        'turn'

        >>> from music21.common.enums import OrnamentDelay
        >>> delayedInvertedTurn = expressions.InvertedTurn(
        ...     delay=OrnamentDelay.DEFAULT_DELAY,
        ...     upperAccidental=pitch.Accidental('sharp'),
        ...     lowerAccidental=pitch.Accidental('natural')
        ... )
        >>> delayedInvertedTurn.name
        'delayed inverted turn (upper=sharp, lower=natural)'

        >>> delayedBy1Turn = expressions.Turn(
        ...     delay=1.0, lowerAccidental=pitch.Accidental('double-flat'))
        >>> delayedBy1Turn.name
        'delayed(delayQL=1.0) turn (lower=double-flat)'

        '''
        theName: str = super().name
        if self.delay == OrnamentDelay.DEFAULT_DELAY:
            theName = 'delayed ' + theName
        elif isinstance(self.delay, (float, Fraction)):
            theName = f'delayed(delayQL={self.delay}) ' + theName

        if self.upperAccidental is not None or self.lowerAccidental is not None:
            theName += ' ('
            if self.upperAccidental is not None:
                theName += 'upper=' + self.upperAccidental.name
                if self.lowerAccidental is not None:
                    theName += ', '
            if self.lowerAccidental is not None:
                theName += 'lower=' + self.lowerAccidental.name
            theName += ')'

        return theName

    def getSize(
        self,
        srcObj: note.GeneralNote,
        which: str,
        *,
        keySig: key.KeySignature | None = None,
    ) -> interval.IntervalBase:
        '''
        Returns the size of one of the turn's two intervals (which='upper'
        or which='lower'), given a source note and an optional key signature.
        If the key signature is not specified, the source note's context is
        searched for the current key signature, and if there is no such key
        signature, a key signature with no sharps and no flats will be used.
        Any `upperAccidental` or `lowerAccidental` that has been set on the
        turn will also be taken into account.  If either has not been set,
        the appropriate accidental from the key signature will be used.

        If keySig is specified, this can be considered to be a theoretical
        question: "If this particular turn were to be attached to this note,
        in this key, what would the ('upper' or 'lower') size of the turn
        interval be?"
        '''
        if which not in ('upper', 'lower'):
            raise ExpressionException(
                "Turn.getSize requires 'which' parameter be set to 'upper' or 'lower'")

        if not srcObj.pitches:
            # perfect unison
            return interval.Interval('P1')

        srcPitch: pitch.Pitch = srcObj.pitches[-1]

        # Use keySig if passed in, else use keySig from context, else no sharps or flats.
        keySig = keySig or srcObj.getContextByClass(key.KeySignature) or key.KeySignature(0)

        ornamentalPitch: pitch.Pitch = copy.deepcopy(srcPitch)
        ornamentalPitch.accidental = None
        if ornamentalPitch.octave is None:
            ornamentalPitch.octave = ornamentalPitch.implicitOctave

        accidental: pitch.Accidental | None = None
        if which == 'upper':
            ornamentalPitch.transpose(interval.GenericInterval(2), inPlace=True)
            accidental = self.upperAccidental
        else:
            ornamentalPitch.transpose(interval.GenericInterval(-2), inPlace=True)
            accidental = self.lowerAccidental

        if accidental:
            ornamentalPitch.accidental = accidental
        else:
            # use whatever accidental the key signature says
            ornamentalPitch.accidental = keySig.accidentalByStep(ornamentalPitch.step)

        return interval.Interval(srcPitch, ornamentalPitch)

    def resolveOrnamentalPitches(
        self,
        srcObj: note.GeneralNote,
        *,
        keySig: key.KeySignature | None = None
    ):
        '''
        Computes and stores the ornamental pitches for a Turn, given the srcObj
        (can be any kind of ornamented GeneralNote) and an optional keySig.

        If keySig is None, srcNote's context will be searched for a key signature.
        If no key signature is found, a key signature with no sharps and no flats
        will be used.

        e.g. A turn on a D in a key with two flats (upper ornamental pitch will be E flat,
        lower ornamental pitch will be C).

        >>> twoFlats = key.KeySignature(sharps=-2)
        >>> n1 = note.Note('D4')
        >>> turn = expressions.Turn()
        >>> turn.resolveOrnamentalPitches(n1, keySig=twoFlats)
        >>> turn.ornamentalPitches
        (<music21.pitch.Pitch E-4>, <music21.pitch.Pitch C4>)
        >>> turn.upperOrnamentalPitch
        <music21.pitch.Pitch E-4>
        >>> turn.lowerOrnamentalPitch
        <music21.pitch.Pitch C4>

        e.g. A turn with a sharp over it and a flat under it, on a C, in a key with
        no sharps or flats (upper ornamental pitch will be D#, lower ornamental pitch
        will be B flat).

        >>> noSharpsOrFlats = key.KeySignature(0)
        >>> n2 = note.Note('C4')
        >>> turn = expressions.Turn(
        ...     upperAccidental=pitch.Accidental('sharp'),
        ...     lowerAccidental=pitch.Accidental('flat'))
        >>> turn.resolveOrnamentalPitches(n2, keySig=noSharpsOrFlats)
        >>> turn.ornamentalPitches
        (<music21.pitch.Pitch D#4>, <music21.pitch.Pitch B-3>)
        >>> turn.upperOrnamentalPitch
        <music21.pitch.Pitch D#4>
        >>> turn.lowerOrnamentalPitch
        <music21.pitch.Pitch B-3>
        '''
        if not srcObj.pitches:
            # There are no ornamental pitches relative to this srcObj
            return

        srcPitch: pitch.Pitch = srcObj.pitches[-1]

        transposeIntervalUp: interval.IntervalBase = self.getSize(
            srcObj, 'upper', keySig=keySig)
        transposeIntervalDown: interval.IntervalBase = self.getSize(
            srcObj, 'lower', keySig=keySig)

        upperPitch: pitch.Pitch = copy.deepcopy(srcPitch)
        if upperPitch.octave is None:
            upperPitch.octave = upperPitch.implicitOctave
        upperPitch.transpose(transposeIntervalUp, inPlace=True)
        # if there are microtones, see if they can be converted to quarter tones.
        if upperPitch.microtone.cents != 0:
            upperPitch.convertMicrotonesToQuarterTones(inPlace=True)

        lowerPitch: pitch.Pitch = copy.deepcopy(srcPitch)
        if lowerPitch.octave is None:
            lowerPitch.octave = lowerPitch.implicitOctave
        lowerPitch.transpose(transposeIntervalDown, inPlace=True)
        # if there are microtones, see if they can be converted to quarter tones.
        if lowerPitch.microtone.cents != 0:
            lowerPitch.convertMicrotonesToQuarterTones(inPlace=True)

        # The actual value of upperAccidental (or lowerAccidental) is not
        # relevant here, since it is already incorporated into the upperPitch
        # (or lowerPitch) via getSize()/transpose().  We're just looking for
        # displayStatus.
        if self.upperAccidental is not None:
            if upperPitch.accidental is None:
                upperPitch.accidental = pitch.Accidental(0)
            upperPitch.accidental.displayStatus = self.upperAccidental.displayStatus
        if self.lowerAccidental is not None:
            if lowerPitch.accidental is None:
                lowerPitch.accidental = pitch.Accidental(0)
            lowerPitch.accidental.displayStatus = self.lowerAccidental.displayStatus

        # order matters, see upperOrnamentalPitch and lowerOrnamentalPitch properties below
        self._ornamentalPitches = (upperPitch, lowerPitch)

    @property
    def upperOrnamentalPitch(self) -> pitch.Pitch | None:
        '''
        Returns the turn's upper ornamental pitch.  If resolveOrnamentalPitches
        has not yet been called, None is returned.
        '''
        if len(self._ornamentalPitches) >= 1:
            return self._ornamentalPitches[0]
        return None

    @property
    def lowerOrnamentalPitch(self) -> pitch.Pitch | None:
        '''
        Returns the turn's lower ornamental pitch.  If resolveOrnamentalPitches
        has not yet been called, None is returned.
        '''
        if len(self._ornamentalPitches) >= 2:
            return self._ornamentalPitches[1]
        return None

    @property
    def ornamentalPitches(self) -> tuple[pitch.Pitch, ...]:
        '''
        Returns any ornamental pitches that have been resolved (see
        `resolveOrnamentalPitches`, which must be called first, or an
        empty tuple will be returned).
        '''
        return self._ornamentalPitches

    def updateAccidentalDisplay(
        self,
        *,
        pitchPast: list[pitch.Pitch] | None = None,
        pitchPastMeasure: list[pitch.Pitch] | None = None,
        otherSimultaneousPitches: list[pitch.Pitch] | None = None,
        alteredPitches: list[pitch.Pitch] | None = None,
        cautionaryPitchClass: bool = True,
        cautionaryAll: bool = False,
        overrideStatus: bool = False,
        cautionaryNotImmediateRepeat: bool = True,
    ):
        '''
        Updates accidental display for a Turn's ornamental pitches (upper and lower).
        Defined exactly like Pitch.updateAccidentalDisplay, with two changes:
        Instead of self being the pitch to update, self is a Turn whose
        ornamentalPitches are to be updated; and we pay no attention to ties,
        since ornamental notes cannot be tied.
        '''
        if not self.ornamentalPitches:
            return

        for p, acc in (
            (self.upperOrnamentalPitch, self.upperAccidental),
            (self.lowerOrnamentalPitch, self.lowerAccidental)
        ):
            if p is not None:
                if acc is not None and acc.displayStatus is not None:
                    # force accidental visibility to be whatever acc's visibility is
                    if p.accidental is None:
                        p.accidental = pitch.Accidental(0)
                    p.accidental.displayStatus = acc.displayStatus
                else:
                    p.updateAccidentalDisplay(
                        pitchPast=pitchPast,
                        pitchPastMeasure=pitchPastMeasure,
                        alteredPitches=alteredPitches,
                        cautionaryPitchClass=cautionaryPitchClass,
                        cautionaryAll=cautionaryAll,
                        overrideStatus=overrideStatus,
                        cautionaryNotImmediateRepeat=cautionaryNotImmediateRepeat,
                        lastNoteWasTied=False)

    def realize(
        self,
        srcObj: note.Note | note.Unpitched,
        *,
        keySig: key.KeySignature | None = None,
        inPlace: bool = False
    ) -> tuple[list[note.Note | note.Unpitched],
                note.Note | note.Unpitched | None,
                list[note.Note | note.Unpitched]]:
        # noinspection PyShadowingNames
        '''
        realize a turn.

        returns a three-element tuple.
        The first element is an empty list because there are no notes at the start of a turn.
        The second element is the original note with a duration equal to the delay (but if there
        is no delay, the second element is None, because the turn "eats up" the entire note).
        The third element is a list of the four turn notes, adding up to the duration of the
        original note (less the delay, if there is one).  The four turn notes will either be
        of equal duration, or the fourth note will be longer, to "eat up" the entire note.

        >>> from  music21 import *
        >>> from music21.common.enums import OrnamentDelay
        >>> m1 = stream.Measure()
        >>> m1.append(key.Key('F', 'major'))
        >>> n1 = note.Note('C5')
        >>> m1.append(n1)
        >>> t1 = expressions.Turn()
        >>> t1.realize(n1)
        ([], None, [<music21.note.Note D>,
                    <music21.note.Note C>,
                    <music21.note.Note B->,
                    <music21.note.Note C>])

        >>> m2 = stream.Measure()
        >>> m2.append(key.KeySignature(5))
        >>> n2 = note.Note('B4', type='quarter')
        >>> m2.append(n2)
        >>> t2 = expressions.InvertedTurn(delay=OrnamentDelay.DEFAULT_DELAY)
        >>> n2.expressions.append(t2)
        >>> t2.realize(n2)
        ([], <music21.note.Note B>, [<music21.note.Note A#>,
                                     <music21.note.Note B>,
                                     <music21.note.Note C#>,
                                     <music21.note.Note B>])

        Realizing an expression leaves the original note and expression alone

        >>> n2.duration.type
        'quarter'
        >>> n2.expressions
        [<music21.expressions.InvertedTurn>]

        If `inPlace` is True then the note is affected and the turn is
        removed from `.expressions`:

        >>> n2 = note.Note('C4')
        >>> n2.duration.type = '32nd'
        >>> t2 = expressions.Turn(delay=OrnamentDelay.DEFAULT_DELAY)
        >>> _empty, newOrigNote, turnNotes = t2.realize(n2, inPlace=True)
        >>> for turnNote in turnNotes:
        ...     print(turnNote, turnNote.duration.type)
        <music21.note.Note D> 256th
        <music21.note.Note C> 256th
        <music21.note.Note B> 256th
        <music21.note.Note C> 256th
        >>> n2.duration.type
        '64th'
        >>> n2.expressions
        []
        >>> newOrigNote is n2
        True

        If the four turn notes (self.quarterLength each) don't add up to the original note
        duration, the fourth turn note should be held to the length of any remaining unused
        duration.  Here, for example, we have a dotted eighth note total duration, a delay
        of a 16th note, and a turn note duration of a triplet 32nd note, leaving the fourth
        turn note with a duration of a 16th note.  This sort of turn is seen all over the
        music of Weber.

        >>> from fractions import Fraction
        >>> n3 = note.Note('C4')
        >>> n3.quarterLength = 0.75
        >>> t3 = expressions.Turn(delay=0.25)
        >>> t3.quarterLength = 0.125 * Fraction(2, 3)
        >>> _empty, newOrigNote, turnNotes = t3.realize(n3, inPlace=True)
        >>> print(newOrigNote, newOrigNote.quarterLength)
        <music21.note.Note C> 0.25
        >>> for turnNote in turnNotes:
        ...     print(turnNote, turnNote.quarterLength)
        <music21.note.Note D> 1/12
        <music21.note.Note C> 1/12
        <music21.note.Note B> 1/12
        <music21.note.Note C> 0.25

        If `.autoScale` is off and the note is not long enough to realize 4
        32nd notes, then an exception is raised.

        >>> n2 = note.Note('C4')
        >>> n2.duration.type = '32nd'
        >>> t2 = expressions.Turn()
        >>> t2.autoScale = False
        >>> t2.realize(n2)
        Traceback (most recent call last):
        music21.expressions.ExpressionException: The note is not long enough to realize a turn
        '''
        useQL = self.quarterLength
        if srcObj.duration.quarterLength == 0:
            raise ExpressionException('Cannot steal time from an object with no duration')

        # here we compute transposeIntervals, and invert them if self._isInverted
        currentKeySig = keySig
        if currentKeySig is None:
            currentKeySig = srcObj.getContextByClass(key.KeySignature)
            if currentKeySig is None:
                currentKeySig = key.KeySignature(0)

        remainderDuration: OffsetQL
        if self.delay == OrnamentDelay.NO_DELAY:
            remainderDuration = 0.0
        elif self.delay == OrnamentDelay.DEFAULT_DELAY:
            # half the duration of the srcObj note
            remainderDuration = opFrac(srcObj.duration.quarterLength / 2)
        else:
            theDelay = self.delay
            if t.TYPE_CHECKING:
                assert isinstance(theDelay, (float, Fraction))
            remainderDuration = theDelay

        turnDuration = srcObj.duration.quarterLength - remainderDuration
        fourthNoteQL: OffsetQL | None = None
        if turnDuration < 4 * self.quarterLength:
            if not self.autoScale:
                raise ExpressionException('The note is not long enough to realize a turn')
            useQL = opFrac(turnDuration / 4)
        elif turnDuration > 4 * self.quarterLength:
            # in this case, we keep the first 3 turn notes as self.quarterLength, and
            # extend the 4th turn note to finish up the turnDuration
            useQL = self.quarterLength
            fourthNoteQL = opFrac(turnDuration - (3 * useQL))

        if not self._isInverted:
            firstTransposeInterval = self.getSize(srcObj, 'upper', keySig=currentKeySig)
            secondTransposeInterval = self.getSize(srcObj, 'lower', keySig=currentKeySig)
        else:
            firstTransposeInterval = self.getSize(srcObj, 'lower', keySig=currentKeySig)
            secondTransposeInterval = self.getSize(srcObj, 'upper', keySig=currentKeySig)

        # no need to check both intervals, they will both be perfectUnison, or neither will be.
        isTransposed: bool = not isUnison(firstTransposeInterval)
        turnNotes: list[note.Note | note.Unpitched] = []

        firstNote = copy.deepcopy(srcObj)
        firstNote.expressions = []
        firstNote.duration.quarterLength = useQL
        if isTransposed:
            if t.TYPE_CHECKING:
                assert isinstance(firstNote, note.Note)
            firstNote.transpose(firstTransposeInterval, inPlace=True)

        secondNote = copy.deepcopy(srcObj)
        secondNote.expressions = []
        secondNote.duration.quarterLength = useQL

        thirdNote = copy.deepcopy(srcObj)
        thirdNote.expressions = []
        thirdNote.duration.quarterLength = useQL
        if isTransposed:
            if t.TYPE_CHECKING:
                assert isinstance(thirdNote, note.Note)
            thirdNote.transpose(secondTransposeInterval, inPlace=True)

        fourthNote = copy.deepcopy(srcObj)
        fourthNote.expressions = []
        if fourthNoteQL is None:
            fourthNote.duration.quarterLength = useQL
        else:
            fourthNote.duration.quarterLength = fourthNoteQL

        turnNotes.append(firstNote)
        turnNotes.append(secondNote)
        turnNotes.append(thirdNote)
        turnNotes.append(fourthNote)

        if isTransposed:
            # first note and third note might need an accidental from the keySig (but
            # only if they don't already have an accidental from upper/lowerAccidental)
            for noteIdx, n in enumerate(turnNotes):
                if t.TYPE_CHECKING:
                    assert isinstance(n, note.Note)
                noteNum: int = noteIdx + 1
                if n.pitch.accidental is None and noteNum in (1, 3):
                    n.pitch.accidental = currentKeySig.accidentalByStep(n.pitch.step)

        inExpressions = -1
        if self in srcObj.expressions:
            inExpressions = srcObj.expressions.index(self)

        if remainderDuration == 0:
            return ([], None, turnNotes)

        if not inPlace:
            remainderNote = copy.deepcopy(srcObj)
        else:
            remainderNote = srcObj
        remainderNote.duration.quarterLength = remainderDuration
        if inExpressions != -1:
            remainderNote.expressions.pop(inExpressions)

        return ([], remainderNote, turnNotes)


class InvertedTurn(Turn):
    _isInverted: bool = True


# ------------------------------------------------------------------------------
class GeneralAppoggiatura(Ornament):
    # up or down -- up means the grace note is below and goes up to the actual note
    direction = ''

    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.size = interval.Interval(2)

    def realize(
        self,
        srcObj: note.Note | note.Unpitched,
        *,
        keySig: key.KeySignature | None = None,
        inPlace: bool = False
    ) -> tuple[list[note.Note | note.Unpitched],
                note.Note | note.Unpitched | None,
                list[note.Note | note.Unpitched]]:
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
        '''
        if self.direction not in ('up', 'down'):
            raise ExpressionException(
                'Cannot realize an Appoggiatura if I do not know its direction')
        if self.size == '':
            raise ExpressionException(
                'Cannot realize an Appoggiatura if there is no size given')
        if srcObj.duration.quarterLength == 0:
            raise ExpressionException('Cannot steal time from an object with no duration')

        newDuration = srcObj.duration.quarterLength / 2
        if self.direction == 'down':
            transposeInterval = self.size
        else:
            transposeInterval = self.size.reverse()

        appoggiaturaNote = copy.deepcopy(srcObj)
        appoggiaturaNote.duration.quarterLength = newDuration
        isTransposed: bool = not isUnison(transposeInterval)
        if isTransposed:
            if t.TYPE_CHECKING:
                assert isinstance(appoggiaturaNote, note.Note)
            appoggiaturaNote.transpose(transposeInterval, inPlace=True)

        inExpressions = -1
        if self in srcObj.expressions:
            inExpressions = srcObj.expressions.index(self)

        remainderNote = copy.deepcopy(srcObj) if not inPlace else srcObj
        remainderNote.duration.quarterLength = newDuration
        if inExpressions != -1:
            remainderNote.expressions.pop(inExpressions)

        # currentKeySig = srcObj.getContextByClass(key.KeySignature)
        # if currentKeySig is None:
        #    currentKeySig = key.KeySignature(0)
        return ([appoggiaturaNote], remainderNote, [])


class Appoggiatura(GeneralAppoggiatura):
    direction = 'down'


class HalfStepAppoggiatura(Appoggiatura):
    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.size = interval.Interval('m2')


class WholeStepAppoggiatura(Appoggiatura):
    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.size = interval.Interval('M2')


class InvertedAppoggiatura(GeneralAppoggiatura):
    direction = 'up'


class HalfStepInvertedAppoggiatura(InvertedAppoggiatura):
    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.size = interval.Interval('m2')


class WholeStepInvertedAppoggiatura(InvertedAppoggiatura):
    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.size = interval.Interval('M2')

# ------------------------------------------------------------------------------


class TremoloException(exceptions21.Music21Exception):
    pass


class Tremolo(Ornament):
    '''
    A tremolo ornament represents a single-note tremolo, whether measured or unmeasured.

    >>> n = note.Note(type='quarter')
    >>> trem = expressions.Tremolo()
    >>> trem.measured = True  # default
    >>> trem.numberOfMarks = 3  # default

    >>> trem.numberOfMarks = 'Hi'
    Traceback (most recent call last):
    music21.expressions.TremoloException: Number of marks must be a number from 0 to 8

    >>> trem.numberOfMarks = -1
    Traceback (most recent call last):
    music21.expressions.TremoloException: Number of marks must be a number from 0 to 8

    TODO: (someday) realize triplet Tremolos, etc. differently from other tremolos.
    TODO: deal with unmeasured tremolos.
    '''
    def __init__(self, **keywords):
        super().__init__(**keywords)
        self.measured = True
        self._numberOfMarks = 3

    @property
    def numberOfMarks(self):
        '''
        The number of marks on the note.  Currently, completely controls playback.
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

    def realize(
        self,
        srcObj: note.Note | note.Unpitched,
        *,
        keySig: key.KeySignature | None = None,
        inPlace: bool = False
    ) -> tuple[list[note.Note | note.Unpitched],
                note.Note | note.Unpitched | None,
                list[note.Note | note.Unpitched]]:
        '''
        Realize the ornament

        >>> n = note.Note(type='quarter')
        >>> trem = expressions.Tremolo()
        >>> trem.measured = True  # default
        >>> trem.numberOfMarks = 3  # default
        >>> trem.realize(n)
        ([<music21.note.Note C>, <music21.note.Note C>, <music21.note.Note C>,
          <music21.note.Note C>, <music21.note.Note C>, <music21.note.Note C>,
          <music21.note.Note C>, <music21.note.Note C>], None, [])
        >>> c2 = trem.realize(n)[0]
        >>> [ts.quarterLength for ts in c2]
        [0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125]

        Same thing with Streams:

        >>> n = note.Note(type='quarter')
        >>> trem = expressions.Tremolo()
        >>> n.expressions.append(trem)
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


        >>> trem.numberOfMarks = 1
        >>> y = stream.makeNotation.realizeOrnaments(s)
        >>> y.show('text')
        {0.0} <music21.note.Note C>
        {0.5} <music21.note.Note C>
        '''
        lengthOfEach = 2**(-1 * self.numberOfMarks)
        objsConverted = []
        eRemain = copy.deepcopy(srcObj) if not inPlace else srcObj
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
    def __init__(self, **keywords):
        super().__init__(**keywords)
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
    # musicxml defines a "start", "stop", and a "continue" type;
    # We will try to avoid "continue".
    # N.B. this extension always includes a trill symbol
    def __init__(self, *spannedElements, **keywords):
        super().__init__(*spannedElements, **keywords)

        # from music21 import note
        # self.fillElementTypes = [note.NotRest]

        self._placement = None  # can above or below or None, after musicxml

    def _getPlacement(self):
        return self._placement

    def _setPlacement(self, value):
        if value is not None and value.lower() not in ['above', 'below']:
            raise TrillExtensionException(f'incorrect placement value: {value}')
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

        A setting of None implies that the placement will be determined
        by notation software and no particular placement is demanded.
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
    # musicxml defines a "start", "stop", and a "continue" type.
    # We will try to avoid using the "continue" type.

    def __init__(self, *spannedElements, **keywords):
        super().__init__(*spannedElements, **keywords)

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


class ArpeggioMark(Expression):
    '''
    ArpeggioMark must be applied to a Chord (not to a single Note).

    The parameter arpeggioType can be 'normal' (a squiggly line), 'up' (a squiggly line
    with an up arrow), 'down' (a squiggly line with a down arrow), or 'non-arpeggio' (a
    bracket instead of a squiggly line, used to indicate a non-arpeggiated chord
    intervening in a sequence of arpeggiated ones).

    >>> am = expressions.ArpeggioMark('normal')
    >>> am.type
    'normal'

    >>> am = expressions.ArpeggioMark('down')
    >>> am.type
    'down'
    '''
    def __init__(self, arpeggioType: str | None = None, **keywords):
        super().__init__(**keywords)
        if not arpeggioType:
            arpeggioType = 'normal'
        if arpeggioType not in ('normal', 'up', 'down', 'non-arpeggio'):
            raise ValueError(
                'Arpeggio type must be "normal", "up", "down", or "non-arpeggio", '
                + f'not {arpeggioType!r}.'
            )
        self.type = arpeggioType


class ArpeggioMarkSpanner(spanner.Spanner):
    '''
    ArpeggioMarkSpanner is a multi-staff or multi-voice (i.e. multi-chord) arpeggio.
    The spanner should contain all the simultaneous Chords that are to be
    arpeggiated together.  If there is only one arpeggiated note in a particular staff
    or voice (i.e. the rest are in other staves/voices), then in that case only the
    spanner can contain a Note.  Do not ever put a Note that is within a Chord into a
    spanner; put the Chord in instead.  And do not ever put an ArpeggioMark in a note
    or chord's .expressions.

    The parameter arpeggioType can be 'normal' (a squiggly line), 'up' (a squiggly line
    with an up arrow), 'down' (a squiggly line with a down arrow), or 'non-arpeggio' (a
    bracket instead of a squiggly line, used to indicate a non-arpeggiated multi-chord
    intervening in a sequence of arpeggiated ones).

    >>> ams = expressions.ArpeggioMarkSpanner(arpeggioType='non-arpeggio')
    >>> c1 = chord.Chord('C3 E3 G3')
    >>> c2 = chord.Chord('C4 E4 G4')
    >>> ams.addSpannedElements([c1, c2])
    >>> ams.type
    'non-arpeggio'
    >>> ams
    <music21.expressions.ArpeggioMarkSpanner
     <music21.chord.Chord C3 E3 G3><music21.chord.Chord C4 E4 G4>>
    '''
    def __init__(self,
                 *spannedElements,
                 arpeggioType: str = 'normal',
                 **keywords):
        super().__init__(*spannedElements, **keywords)

        if arpeggioType not in ('normal', 'up', 'down', 'non-arpeggio'):
            raise ValueError(
                'Arpeggio type must be "normal", "up", "down", or "non-arpeggio", '
                + f'not {arpeggioType!r}.'
            )
        self.type = arpeggioType

    def noteExtremes(self) -> tuple[note.Note | None,
                                    note.Note | None]:
        '''
        Return the lowest and highest note spanned by the element,
        extracting them from Chords if need be.

        >>> ch = chord.Chord(['C4', 'E4', 'G4'])
        >>> n = note.Note('C#3')
        >>> nonArp = expressions.ArpeggioMarkSpanner([ch, n])
        >>> nonArp.noteExtremes()
        (<music21.note.Note C#>, <music21.note.Note G>)
        '''
        from music21 import chord
        from music21 import note
        notes = []
        for n_or_ch in self:
            if isinstance(n_or_ch, note.Note):
                notes.append(n_or_ch)
            elif isinstance(n_or_ch, chord.Chord):
                notes.extend(n_or_ch.notes)
        return (min(notes), max(notes))


# ------------------------------------------------------------------------------
# Tests moved to test/test_expressions


# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [TextExpression]

if __name__ == '__main__':
    import music21
    music21.mainTest()

