# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         bar.py
# Purpose:      music21 classes for representing bars, repeats, and related
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2012, 2020 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Object models of barlines, including repeat barlines.
'''
import unittest
from typing import Optional

from music21 import base
from music21 import exceptions21

from music21 import expressions
from music21 import repeat

from music21 import environment
from music21 import style

_MOD = 'bar'
environLocal = environment.Environment(_MOD)

# ------------------------------------------------------------------------------

class BarException(exceptions21.Music21Exception):
    pass


# store alternative names for types; use this dictionary for translation
# reference
barTypeList = [
    'regular', 'dotted', 'dashed', 'heavy', 'double', 'final',
    'heavy-light', 'heavy-heavy', 'tick', 'short', 'none',
]

# former are MusicXML names we allow
barTypeDict = {
    'light-light': 'double',
    'light-heavy': 'final'
}
reverseBarTypeDict = {
    'double': 'light-light',
    'final': 'light-heavy',
}


def typeToMusicXMLBarStyle(value):
    '''
    Convert a music21 barline name into the musicxml name --
    essentially just changes the names of 'double' and 'final'
    to 'light-light' and 'light-heavy'

    Does not do error checking to make sure it's a valid name,
    since setting the style on a Barline object already does that.

    >>> bar.typeToMusicXMLBarStyle('final')
    'light-heavy'
    >>> bar.typeToMusicXMLBarStyle('regular')
    'regular'
    '''
    if value.lower() in reverseBarTypeDict:
        return reverseBarTypeDict[value.lower()]
    else:
        return value

def standardizeBarType(value):
    '''
    Standardizes bar type names.

    converts all names to lower case, None to 'regular',
    and 'light-light' to 'double' and 'light-heavy' to 'final',
    raises an error for unknown styles.
    '''
    if value is None:
        return 'regular'  # for now, return with string

    value = value.lower()

    if value in barTypeList:
        return value
    elif value in barTypeDict:
        return barTypeDict[value]
    # if not match
    else:
        raise BarException(f'cannot process style: {value}')


# ------------------------------------------------------------------------------
class Barline(base.Music21Object, style.StyleMixin):
    '''A representation of a barline.
    Barlines are conventionally assigned to Measure objects
    using the leftBarline and rightBarline attributes.


    >>> bl = bar.Barline('double')
    >>> bl
    <music21.bar.Barline type=double>

    The type can also just be set via a keyword of "type".  Or if no type is specified,
    a regular barline is returned.  Location can also be explicitly stored, but it's not
    needed except for musicxml translation:

    >>> bl2 = bar.Barline(type='dashed')
    >>> bl2
    <music21.bar.Barline type=dashed>
    >>> bl3 = bar.Barline()
    >>> bl3
    <music21.bar.Barline type=regular>
    >>> bl4 = bar.Barline(type='final', location='right')
    >>> bl4
    <music21.bar.Barline type=final>
    >>> bl4.type
    'final'

    Note that the barline type 'ticked' only is displayed correctly in Finale and Finale Notepad.

    N.B. for backwards compatibility reasons, currently
    Bar objects do not use the style.Style class since
    the phrase "style" was already used.
    '''
    validStyles = list(barTypeDict.keys())

    classSortOrder = -5

    def __init__(self,
                 type=None,  # @ReservedAssignment  # pylint: disable=redefined-builtin
                 location=None):
        super().__init__()

        self._type = None  # same as style...
        # this will raise an exception on error from property
        self.type = type

        # pause can be music21.expressions.Fermata object
        self.pause = None

        # location is primarily stored in the stream as leftBarline or rightBarline
        # but can also be stored here.
        self.location = location  # musicxml values: can be left, right, middle, None

    def _reprInternal(self):
        return f'type={self.type}'


    def _getType(self):
        return self._type

    def _setType(self, value):
        self._type = standardizeBarType(value)

    type = property(_getType, _setType,
        doc='''
        Get and set the Barline type property.

        >>> b = bar.Barline()
        >>> b.type = 'tick'
        >>> b.type
        'tick'

        Synonyms are given for some types, based on
        musicxml styles:

        >>> b.type = 'light-light'
        >>> b.type
        'double'
        ''')

    def musicXMLBarStyle(self):
        '''
        returns the musicxml style for the bar.  most are the same as
        `.type` but "double" and "final" are different.

        >>> b = bar.Barline('tick')
        >>> b.musicXMLBarStyle()
        'tick'

        >>> b.type = 'double'
        >>> b.musicXMLBarStyle()
        'light-light'

        >>> b.type = 'final'
        >>> b.musicXMLBarStyle()
        'light-heavy'

        Changed in v.5.7 -- was a property before.
        '''
        return typeToMusicXMLBarStyle(self.type)






# ------------------------------------------------------------------------------

# note that musicxml permits the barline to have attributes for segno and coda
# <xs:attribute name="segno" type="xs:token"/>
# <xs:attribute name="coda" type="xs:token"/>

# type <ending> in musicxml is used to mark different endings


class Repeat(repeat.RepeatMark, Barline):
    '''
    A Repeat barline.

    The `direction` parameter can be one of `start` or `end`.
    An `end` followed by a `start`
    should be encoded as two `bar.Repeat` signs.


    >>> rep = bar.Repeat(direction='end', times=3)
    >>> rep
    <music21.bar.Repeat direction=end times=3>

    To apply a repeat barline assign it to either the `.leftBarline` or
    `.rightBarline` attribute
    of a measure.

    >>> m = stream.Measure()
    >>> m.leftBarline = bar.Repeat(direction='start')
    >>> m.rightBarline = bar.Repeat(direction='end')
    >>> m.insert(0.0, meter.TimeSignature('4/4'))
    >>> m.repeatAppend(note.Note('D--5'), 4)
    >>> p = stream.Part()
    >>> p.insert(0.0, m)
    >>> p.show('text')
    {0.0} <music21.stream.Measure 0 offset=0.0>
        {0.0} <music21.bar.Repeat direction=start>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.note.Note D-->
        {1.0} <music21.note.Note D-->
        {2.0} <music21.note.Note D-->
        {3.0} <music21.note.Note D-->
        {4.0} <music21.bar.Repeat direction=end>

    The method :meth:`~music21.stream.Part.expandRepeats` on a
    :class:`~music21.stream.Part` object expands the repeats, but
    does not update measure numbers

    >>> q = p.expandRepeats()
    >>> q.show('text')
    {0.0} <music21.stream.Measure 0 offset=0.0>
        {0.0} <music21.bar.Barline type=double>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.note.Note D-->
        {1.0} <music21.note.Note D-->
        {2.0} <music21.note.Note D-->
        {3.0} <music21.note.Note D-->
        {4.0} <music21.bar.Barline type=double>
    {4.0} <music21.stream.Measure 0a offset=4.0>
        {0.0} <music21.bar.Barline type=double>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.note.Note D-->
        {1.0} <music21.note.Note D-->
        {2.0} <music21.note.Note D-->
        {3.0} <music21.note.Note D-->
        {4.0} <music21.bar.Barline type=double>
    '''
    # _repeatDots = None  # not sure what this is for; inherited from old modules
    def __init__(self, direction='start', times=None):
        repeat.RepeatMark.__init__(self)
        if direction == 'start':
            barType = 'heavy-light'
        else:
            barType = 'final'
        Barline.__init__(self, type=barType)

        self._direction: Optional[str] = None  # either start or end
        self._times: Optional[int] = None  # if an end, how many repeats

        # start is forward, end is backward in musicxml
        self.direction = direction  # start, end
        self.times = times

    def _reprInternal(self):
        msg = f'direction={self.direction}'
        if self.times is not None:
            msg += f' times={self.times}'
        return msg


    @property
    def direction(self) -> str:
        '''
        Get or set the direction of this Repeat barline. Can be start or end.

        TODO: show how changing direction changes type.
        '''
        return self._direction

    @direction.setter
    def direction(self, value: str):
        if value.lower() in ('start', 'end'):
            self._direction = value.lower()
            if self._direction == 'end':
                self.type = 'final'
            elif self._direction == 'start':
                self.type = 'heavy-light'
        else:
            raise BarException(f'cannot set repeat direction to: {value}')

    @property
    def times(self) -> Optional[int]:
        '''
        Get or set the times property of this barline. This
        defines how many times the repeat happens. A standard repeat
        repeats 2 times; values equal to or greater than 0 are permitted.
        A repeat of 0 skips the repeated passage.

        >>> lb = bar.Repeat(direction='start')
        >>> rb = bar.Repeat(direction='end')

        Only end expressions can have times:

        >>> lb.times = 3
        Traceback (most recent call last):
        music21.bar.BarException: cannot set repeat times on a start Repeat

        >>> rb.times = 3
        >>> rb.times = -3
        Traceback (most recent call last):
        music21.bar.BarException: cannot set repeat times to a value less than zero: -3
        '''
        return self._times

    @times.setter
    def times(self, value: int):
        if value is None:
            self._times = None
        else:
            try:
                candidate = int(value)
            except ValueError:
                # pylint: disable:raise-missing-from
                raise BarException(
                    f'cannot set repeat times to: {value!r}'
                )

            if candidate < 0:
                raise BarException(
                    f'cannot set repeat times to a value less than zero: {value}'
                )
            if self.direction == 'start':
                raise BarException('cannot set repeat times on a start Repeat')

            self._times = candidate


    def getTextExpression(self, prefix='', postfix='x'):
        '''
        Return a configured :class:`~music21.expressions.TextExpressions`
        object describing the repeat times. Append this to the stream
        for annotation of repeat times.

        >>> rb = bar.Repeat(direction='end')
        >>> rb.times = 3
        >>> rb.getTextExpression()
        <music21.expressions.TextExpression '3x'>

        >>> rb.getTextExpression(prefix='repeat ', postfix=' times')
        <music21.expressions.TextExpression 'repeat 3 t...'>
        '''
        value = f'{prefix}{self._times}{postfix}'
        return expressions.TextExpression(value)


# ------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def testSortOrder(self):
        from music21 import stream, clef, note, metadata
        m = stream.Measure()
        b = Repeat()
        m.leftBarline = b
        c = clef.BassClef()
        m.append(c)
        n = note.Note()
        m.append(n)

        # check sort order
        self.assertEqual(m[0], b)
        self.assertEqual(m[1], c)
        self.assertEqual(m[2], n)

        # if we add metadata, it sorts ahead of bar
        md = metadata.Metadata()
        m.insert(0, md)

        self.assertEqual(m[0], md)
        self.assertEqual(m[1], b)


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)

