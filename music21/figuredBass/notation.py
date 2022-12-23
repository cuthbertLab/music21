# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         notation.py
# Purpose:      representations of figured bass notation
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    Copyright © 2011 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
from __future__ import annotations

import copy
import re
import unittest

from music21 import exceptions21
from music21 import pitch
from music21 import prebase

shorthandNotation = {(None,): (5, 3),
                     (5,): (5, 3),
                     (6,): (6, 3),
                     (7,): (7, 5, 3),
                     (9,): (9, 7, 5, 3),
                     (11,): (11, 9, 7, 5, 3),
                     (13,): (13, 11, 9, 7, 5, 3),
                     (6, 5): (6, 5, 3),
                     (4, 3): (6, 4, 3),
                     (4, 2): (6, 4, 2),
                     (2,): (6, 4, 2),
                     }


class Notation(prebase.ProtoM21Object):
    '''
    Breaks apart and stores the information in a figured bass notation
    column, which is a string of figures, each associated with a number
    and an optional modifier. The figures are delimited using commas.
    Examples include '7,5,#3', '6,4', and '6,4+,2'.


    Valid modifiers include those accepted by :class:`~music21.pitch.Accidental`,
    such as #, -, and n, as well as those which can correspond to one, such as +,
    /, and b.


    .. note:: If a figure has a modifier but no number, the number is
        assumed to be 3.


    Notation also translates many forms of shorthand notation into longhand. It understands
    all the forms of shorthand notation listed below. This is true even if a number is accompanied
    by a modifier, or if a stand-alone modifier implies a 3.


    * None, '' or '5' -> '5,3'


    * '6' -> '6,3'


    * '7' -> '7,5,3'


    * '6,5' -> '6,5,3'


    * '4,3' -> '6,4,3'


    * '4,2' or '2' -> '6,4,2'


    * '9' -> '9,7,5,3'


    * '11' -> '11,9,7,5,3'


    * '13' -> '13,11,9,7,5,3'


    Figures are saved in order from left to right as found in the notationColumn.

    >>> from music21.figuredBass import notation
    >>> n1 = notation.Notation('4+,2')
    >>> n1
    <music21.figuredBass.notation.Notation 4+,2>

    >>> n1.notationColumn
    '4+,2'
    >>> n1.figureStrings
    ['4+', '2']
    >>> n1.origNumbers
    (4, 2)
    >>> n1.origModStrings
    ('+', None)
    >>> n1.numbers
    (6, 4, 2)
    >>> n1.modifierStrings
    (None, '+', None)
    >>> n1.modifiers
    (<music21.figuredBass.notation.Modifier None None>,
     <music21.figuredBass.notation.Modifier + sharp>,
     <music21.figuredBass.notation.Modifier None None>)
    >>> n1.figures[0]
    <music21.figuredBass.notation.Figure 6 <Modifier None None>>
    >>> n1.figures[1]
    <music21.figuredBass.notation.Figure 4 <Modifier + sharp>>
    >>> n1.figures[2]
    <music21.figuredBass.notation.Figure 2 <Modifier None None>>


    Here, a stand-alone '#' is being passed to Notation.


    >>> n2 = notation.Notation('#')
    >>> n2.numbers
    (5, 3)
    >>> n2.modifiers
    (<music21.figuredBass.notation.Modifier None None>,
     <music21.figuredBass.notation.Modifier # sharp>)
    >>> n2.figures[0]
    <music21.figuredBass.notation.Figure 5 <Modifier None None>>
    >>> n2.figures[1]
    <music21.figuredBass.notation.Figure 3 <Modifier # sharp>>


    Now, a stand-alone b is being passed to Notation as part of a larger notationColumn.


    >>> n3 = notation.Notation('b6,b')
    >>> n3.numbers
    (6, 3)
    >>> n3.modifiers
    (<music21.figuredBass.notation.Modifier b flat>,
     <music21.figuredBass.notation.Modifier b flat>)
    >>> n3.figures[0]
    <music21.figuredBass.notation.Figure 6 <Modifier b flat>>
    >>> n3.figures[1]
    <music21.figuredBass.notation.Figure 3 <Modifier b flat>>
    '''
    _DOC_ORDER = ['notationColumn', 'figureStrings', 'numbers', 'modifiers',
                  'figures', 'origNumbers', 'origModStrings', 'modifierStrings']
    _DOC_ATTR: dict[str, str] = {
        'modifiers': '''
            A list of :class:`~music21.figuredBass.notation.Modifier`
            objects associated with the expanded
            :attr:`~music21.figuredBass.notation.Notation.notationColumn`.
            ''',
        'notationColumn': '''
            A string of figures delimited by commas,
            each associated with a number and an optional modifier.
            ''',
        'modifierStrings': '''
            The modifiers associated with the expanded
            :attr:`~music21.figuredBass.notation.Notation.notationColumn`, as strings.
            ''',
        'figureStrings': '''
            A list of figures derived from the original
            :attr:`~music21.figuredBass.notation.Notation.notationColumn`.
            ''',
        'origNumbers': '''
            The numbers associated with the original
            :attr:`~music21.figuredBass.notation.Notation.notationColumn`.
            ''',
        'numbers': '''
            The numbers associated with the expanded
            :attr:`~music21.figuredBass.notation.Notation.notationColumn`.
            ''',
        'origModStrings': '''
            The modifiers associated with the original
            :attr:`~music21.figuredBass.notation.Notation.notationColumn`, as strings.
            ''',
        'figures': '''
            A list of :class:`~music21.figuredBass.notation.Figure` objects
            associated with figures in the expanded
            :attr:`~music21.figuredBass.notation.Notation.notationColumn`.
            ''',
    }

    def __init__(self, notationColumn=None):
        # Parse notation string
        if notationColumn is None:
            notationColumn = ''
        self.notationColumn = notationColumn
        self.figureStrings = None
        self.origNumbers = None
        self.origModStrings = None
        self.numbers = None
        self.modifierStrings = None
        self._parseNotationColumn()
        self._translateToLonghand()

        # Convert to convenient notation
        self.modifiers = None
        self.figures = None
        self._getModifiers()
        self._getFigures()

    def _reprInternal(self):
        return str(self.notationColumn)

    def _parseNotationColumn(self):
        '''
        Given a notation column below a pitch, defines both self.numbers
        and self.modifierStrings, which provide the intervals above the
        bass and (if necessary) how to modify the corresponding pitches
        accordingly.


        >>> from music21.figuredBass import notation as n
        >>> notation1 = n.Notation('#6,5')  #__init__ method calls _parseNotationColumn()
        >>> notation1.figureStrings
        ['#6', '5']
        >>> notation1.origNumbers
        (6, 5)
        >>> notation1.origModStrings
        ('#', None)
        >>> notation2 = n.Notation('-6,-')
        >>> notation2.figureStrings
        ['-6', '-']
        >>> notation2.origNumbers
        (6, None)
        >>> notation2.origModStrings
        ('-', '-')
        '''
        delimiter = '[,]'
        figures = re.split(delimiter, self.notationColumn)
        patternA1 = '([0-9]*)'
        patternA2 = '([^0-9]*)'
        numbers = []
        modifierStrings = []
        figureStrings = []

        for figure in figures:
            figure = figure.strip()
            figureStrings.append(figure)
            m1 = re.findall(patternA1, figure)
            m2 = re.findall(patternA2, figure)
            for i in range(m1.count('')):
                m1.remove('')
            for i in range(m2.count('')):
                m2.remove('')
            if not (len(m1) <= 1 or len(m2) <= 1):
                raise NotationException('Invalid Notation: ' + figure)

            number = None
            modifierString = None
            if m1:
                number = int(m1[0].strip())
            if m2:
                modifierString = m2[0].strip()

            numbers.append(number)
            modifierStrings.append(modifierString)

        numbers = tuple(numbers)
        modifierStrings = tuple(modifierStrings)

        self.origNumbers = numbers  # Keep original numbers
        self.numbers = numbers  # Will be converted to longhand
        self.origModStrings = modifierStrings  # Keep original modifier strings
        self.modifierStrings = modifierStrings  # Will be converted to longhand
        self.figureStrings = figureStrings

    def _translateToLonghand(self):
        '''
        Provided the numbers and modifierStrings of a parsed notation column,
        translates it to longhand.


        >>> from music21.figuredBass import notation as n
        >>> notation1 = n.Notation('#6,5')  # __init__ method calls _parseNotationColumn()
        >>> str(notation1.origNumbers) + ' -> ' + str(notation1.numbers)
        '(6, 5) -> (6, 5, 3)'
        >>> str(notation1.origModStrings) + ' -> ' + str(notation1.modifierStrings)
        "('#', None) -> ('#', None, None)"
        >>> notation2 = n.Notation('-6,-')
        >>> notation2.numbers
        (6, 3)
        >>> notation2.modifierStrings
        ('-', '-')
        '''
        oldNumbers = self.numbers
        newNumbers = oldNumbers
        oldModifierStrings = self.modifierStrings
        newModifierStrings = oldModifierStrings

        try:
            newNumbers = shorthandNotation[oldNumbers]
            newModifierStrings = []

            oldNumbers = list(oldNumbers)
            temp = []
            for number in oldNumbers:
                if number is None:
                    temp.append(3)
                else:
                    temp.append(number)

            oldNumbers = tuple(temp)

            for number in newNumbers:
                newModifierString = None
                if number in oldNumbers:
                    modifierStringIndex = oldNumbers.index(number)
                    newModifierString = oldModifierStrings[modifierStringIndex]
                newModifierStrings.append(newModifierString)

            newModifierStrings = tuple(newModifierStrings)
        except KeyError:
            newNumbers = list(newNumbers)
            temp = []
            for number in newNumbers:
                if number is None:
                    temp.append(3)
                else:
                    temp.append(number)

            newNumbers = tuple(temp)

        self.numbers = newNumbers
        self.modifierStrings = newModifierStrings

    def _getModifiers(self):
        '''
        Turns the modifier strings into Modifier objects.
        A modifier object keeps track of both the modifier string
        and its corresponding pitch Accidental.


        >>> from music21.figuredBass import notation as n
        >>> notation1 = n.Notation('#4,2+')  #__init__ method calls _getModifiers()
        >>> notation1.modifiers[0]
        <music21.figuredBass.notation.Modifier None None>
        >>> notation1.modifiers[1]
        <music21.figuredBass.notation.Modifier # sharp>
        >>> notation1.modifiers[2]
        <music21.figuredBass.notation.Modifier + sharp>
        '''
        modifiers = []

        for i in range(len(self.numbers)):
            modifierString = self.modifierStrings[i]
            modifier = Modifier(modifierString)
            modifiers.append(modifier)

        self.modifiers = tuple(modifiers)

    def _getFigures(self):
        '''
        Turns the numbers and Modifier objects into Figure objects, each corresponding
        to a number with its Modifier.


        >>> from music21.figuredBass import notation as n
        >>> notation2 = n.Notation('-6,-')  #__init__ method calls _getFigures()
        >>> notation2.figures[0]
        <music21.figuredBass.notation.Figure 6 <Modifier - flat>>
        >>> notation2.figures[1]
        <music21.figuredBass.notation.Figure 3 <Modifier - flat>>
        '''
        figures = []

        for i in range(len(self.numbers)):
            number = self.numbers[i]
            modifierString = self.modifierStrings[i]
            figure = Figure(number, modifierString)
            figures.append(figure)

        self.figures = figures


class NotationException(exceptions21.Music21Exception):
    pass

# ------------------------------------------------------------------------------


class Figure(prebase.ProtoM21Object):
    '''
    A Figure is created by providing a number and a modifierString. The
    modifierString is turned into a :class:`~music21.figuredBass.notation.Modifier`,
    and a ModifierException is raised if the modifierString is not valid.

    >>> from music21.figuredBass import notation
    >>> f1 = notation.Figure(4, '+')
    >>> f1
    <music21.figuredBass.notation.Figure 4 <Modifier + sharp>>

    >>> f1.number
    4
    >>> f1.modifierString
    '+'
    >>> f1.modifier
    <music21.figuredBass.notation.Modifier + sharp>
    '''
    _DOC_ATTR: dict[str, str] = {
        'number': '''
            A number associated with an expanded
            :attr:`~music21.figuredBass.notation.Notation.notationColumn`.
            ''',
        'modifierString': '''
            A modifier string associated with an
            expanded :attr:`~music21.figuredBass.notation.Notation.notationColumn`.
            ''',
        'modifier': '''
            A :class:`~music21.figuredBass.notation.Modifier`
            associated with an expanded
            :attr:`~music21.figuredBass.notation.Notation.notationColumn`.
            ''',
    }

    def __init__(self, number=1, modifierString=None):
        self.number = number
        self.modifierString = modifierString
        self.modifier = Modifier(modifierString)

    def _reprInternal(self):
        mod = repr(self.modifier).replace('music21.figuredBass.notation.', '')
        return f'{self.number} {mod}'


# ------------------------------------------------------------------------------
specialModifiers = {'+': '#',
                    '/': '-',
                    '\\': '#',
                    'b': '-',
                    'bb': '--',
                    'bbb': '---',
                    'bbbb': '-----',
                    '++': '##',
                    '+++': '###',
                    '++++': '####',
                    }


class Modifier(prebase.ProtoM21Object):
    '''
    Turns a modifierString (a modifier in a
    :attr:`~music21.figuredBass.notation.Notation.notationColumn`)
    to an :class:`~music21.pitch.Accidental`. A ModifierException
    is raised if the modifierString is not valid.


    Accepted inputs are those accepted by Accidental, as well as the following:

    * '+' or '\\' -> '#'

    * 'b' or '/' -> '-'

    >>> from music21.figuredBass import notation
    >>> m1a = notation.Modifier('#')
    >>> m1a
    <music21.figuredBass.notation.Modifier # sharp>
    >>> m1a.modifierString
    '#'
    >>> m1a.accidental
    <music21.pitch.Accidental sharp>

    Providing a + in place of a sharp, we get the same result for the accidental.

    >>> m2a = notation.Modifier('+')
    >>> m2a
    <music21.figuredBass.notation.Modifier + sharp>
    >>> m2a.accidental
    <music21.pitch.Accidental sharp>

    If None or '' is provided for modifierString, then the accidental is None.

    >>> m3a = notation.Modifier(None)
    >>> m3a
    <music21.figuredBass.notation.Modifier None None>
    >>> m3a.accidental is None
    True
    >>> m3b = notation.Modifier('')
    >>> m3b
    <music21.figuredBass.notation.Modifier  None>
    >>> m3b.accidental is None
    True
    '''
    _DOC_ATTR: dict[str, str] = {
        'modifierString': '''
            A modifier string associated with an
            expanded :attr:`~music21.figuredBass.notation.Notation.notationColumn`.
            ''',
        'accidental': '''
            A :class:`~music21.pitch.Accidental` corresponding to
            :attr:`~music21.figuredBass.notation.Modifier.modifierString`.
            ''',
    }

    def __init__(self, modifierString=None):
        self.modifierString = modifierString
        self.accidental = self._toAccidental()

    def _reprInternal(self):
        if self.accidental is not None:
            acc = self.accidental.name
        else:
            acc = None
        return f'{self.modifierString} {acc}'

    def _toAccidental(self):
        '''

        >>> from music21.figuredBass import notation as n
        >>> m1 = n.Modifier('#')
        >>> m2 = n.Modifier('-')
        >>> m3 = n.Modifier('n')
        >>> m4 = n.Modifier('+')  # Raises pitch by semitone
        >>> m5 = n.Modifier('b')  # acceptable for flat since note names not allowed
        >>> m1.accidental
        <music21.pitch.Accidental sharp>
        >>> m2.accidental
        <music21.pitch.Accidental flat>
        >>> m3.accidental
        <music21.pitch.Accidental natural>
        >>> m4.accidental
        <music21.pitch.Accidental sharp>
        >>> m5.accidental
        <music21.pitch.Accidental flat>
        '''
        if not self.modifierString:
            return None

        a = pitch.Accidental()
        try:
            a.set(self.modifierString)
        except pitch.AccidentalException:
            try:
                newModifierString = specialModifiers[self.modifierString]
            except KeyError:
                raise ModifierException(
                    f'Figure modifier unsupported in music21: {self.modifierString}'
                )
            a.set(newModifierString)

        return a

    def modifyPitchName(self, pitchNameToAlter):
        '''
        Given a pitch name, modify its accidental given the Modifier's
        :attr:`~music21.figuredBass.notation.Modifier.accidental`.

        >>> from music21.figuredBass import notation
        >>> m1 = notation.Modifier('#')
        >>> m2 = notation.Modifier('-')
        >>> m3 = notation.Modifier('n')
        >>> m1.modifyPitchName('D')  # Sharp
        'D#'
        >>> m2.modifyPitchName('F')  # Flat
        'F-'
        >>> m3.modifyPitchName('C#')  # Natural
        'C'
        '''
        pitchToAlter = pitch.Pitch(pitchNameToAlter)
        self.modifyPitch(pitchToAlter, inPlace=True)
        return pitchToAlter.name

    def modifyPitch(self, pitchToAlter, *, inPlace=False):
        '''
        Given a :class:`~music21.pitch.Pitch`, modify its :attr:`~music21.pitch.Pitch.accidental`
        given the Modifier's :attr:`~music21.figuredBass.notation.Modifier.accidental`.

        >>> from music21.figuredBass import notation
        >>> m1 = notation.Modifier('#')
        >>> m2 = notation.Modifier('-')
        >>> m3 = notation.Modifier('n')
        >>> p1a = pitch.Pitch('D5')
        >>> m1.modifyPitch(p1a)  # Sharp
        <music21.pitch.Pitch D#5>
        >>> m2.modifyPitch(p1a)  # Flat
        <music21.pitch.Pitch D-5>
        >>> p1b = pitch.Pitch('D#5')
        >>> m3.modifyPitch(p1b)
        <music21.pitch.Pitch D5>

        OMIT_FROM_DOCS
        >>> m4 = notation.Modifier('##')
        >>> m5 = notation.Modifier('--')
        >>> p2 = pitch.Pitch('F5')
        >>> m4.modifyPitch(p2)  # Double Sharp
        <music21.pitch.Pitch F##5>
        >>> m5.modifyPitch(p2)  # Double Flat
        <music21.pitch.Pitch F--5>
        '''
        if not inPlace:
            pitchToAlter = copy.deepcopy(pitchToAlter)
        if self.accidental is None:
            return pitchToAlter
        if self.accidental.alter == 0.0 or pitchToAlter.accidental is None:
            pitchToAlter.accidental = copy.deepcopy(self.accidental)
        else:
            newAccidental = pitch.Accidental()
            newAlter = pitchToAlter.accidental.alter + self.accidental.alter
            try:
                newAccidental.set(newAlter)
                pitchToAlter.accidental = newAccidental
            except pitch.AccidentalException:
                raise ModifierException('Resulting pitch accidental unsupported in music21.')

        if not inPlace:
            return pitchToAlter


class ModifierException(exceptions21.Music21Exception):
    pass

# ------------------------------------------------------------------------------

# Helper Methods


def convertToPitch(pitchString):
    '''
    Converts a pitchString to a :class:`~music21.pitch.Pitch`, only if necessary.

    >>> from music21.figuredBass import notation
    >>> pitchStr = 'C5'
    >>> notation.convertToPitch(pitchStr)
    <music21.pitch.Pitch C5>
    >>> notation.convertToPitch(pitch.Pitch('E4'))  # does nothing
    <music21.pitch.Pitch E4>
    '''
    if isinstance(pitchString, pitch.Pitch):
        return pitchString

    if isinstance(pitchString, str):
        try:
            return pitch.Pitch(pitchString)
        except:
            raise ValueError('Cannot convert string ' + pitchString + ' to a music21 Pitch.')

    raise TypeError('Cannot convert ' + pitchString + ' to a music21 Pitch.')


_DOC_ORDER = [Notation, Figure, Modifier]


class Test(unittest.TestCase):
    pass


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
