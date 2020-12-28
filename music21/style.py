# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         style.py
# Purpose:      Music21 classes for non-analytic display properties
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2016 Michael Scott Cuthbert and the music21
#               Project
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
The style module represents information about the style of a Note, Accidental,
etc. such that precise positioning information, layout, size, etc. can be specified.
'''
from typing import Optional, Union
import unittest

from music21 import common
from music21 import exceptions21


class TextFormatException(exceptions21.Music21Exception):
    pass


class Style:
    '''
    A style object is a lightweight object that
    keeps track of information about the look of an object.

    >>> st = style.Style()
    >>> st.units
    'tenths'
    >>> st.absoluteX is None
    True

    >>> st.absoluteX = 20.4
    >>> st.absoluteX
    20.4

    '''
    _DOC_ATTR = {
        'hideObjectOnPrint': '''if set to `True` will not print upon output
            (only used in MusicXML output at this point and
            Lilypond for notes, chords, and rests).''',
    }

    def __init__(self):
        self.size = None

        self.relativeX: Optional[Union[float, int]] = None
        self.relativeY: Optional[Union[float, int]] = None
        self.absoluteX: Optional[Union[float, int]] = None

        # managed by property below.
        self._absoluteY: Optional[Union[float, int]] = None

        self._enclosure: Optional[str] = None

        # how should this symbol be represented in the font?
        # SMuFL characters are allowed.
        self.fontRepresentation = None

        self.color: Optional[str] = None

        self.units: str = 'tenths'
        self.hideObjectOnPrint: bool = False

    def _getEnclosure(self):
        return self._enclosure

    def _setEnclosure(self, value):
        if value is None:
            self._enclosure = value
        elif value == 'none':
            self._enclosure = None
        elif value.lower() in ('rectangle', 'square', 'oval', 'circle',
                               'bracket', 'triangle', 'diamond',
                               'pentagon', 'hexagon', 'heptagon', 'octagon',
                               'nonagon', 'decagon'):
            self._enclosure = value.lower()
        else:
            raise TextFormatException(f'Not a supported enclosure: {value}')

    enclosure = property(_getEnclosure,
                         _setEnclosure,
                         doc='''
        Get or set the enclosure.  Valid names are
        rectangle, square, oval, circle, bracket, triangle, diamond,
        pentagon, hexagon, heptagon, octagon,
        nonagon, decagon or None.


        >>> tst = style.TextStyle()
        >>> tst.enclosure = None
        >>> tst.enclosure = 'rectangle'
        >>> tst.enclosure
        'rectangle'

        ''')

    def _getAbsoluteY(self):
        return self._absoluteY

    def _setAbsoluteY(self, value):
        if value is None:
            self._absoluteY = None
        else:
            if value == 'above':
                value = 10
            elif value == 'below':
                value = -70
            try:
                value = common.numToIntOrFloat(value)
            except ValueError as ve:
                raise TextFormatException(
                    f'Not a supported absoluteY position: {value!r}'
                ) from ve
            self._absoluteY = value

    absoluteY = property(_getAbsoluteY,
                         _setAbsoluteY,
                         doc='''
        Get or set the vertical position, where 0
        is the top line of the staff and units
        are in 10ths of a staff space.

        Other legal positions are 'above' and 'below' which
        are synonyms for 10 and -70 respectively (for 5-line
        staves; other staves are not yet implemented)

        >>> te = style.Style()
        >>> te.absoluteY = 10
        >>> te.absoluteY
        10

        >>> te.absoluteY = 'below'
        >>> te.absoluteY
        -70
        ''')


class NoteStyle(Style):
    '''
    A Style object that also includes stem and accidental style information.

    Beam style is stored on the Beams object, as is lyric style
    '''

    def __init__(self):
        super().__init__()
        self.stemStyle = None
        self.accidentalStyle = None
        self.noteSize = None  # can be 'cue'...


class TextStyle(Style):
    '''
    A Style object that also includes text formatting.
    '''

    def __init__(self):
        super().__init__()
        self._fontFamily = None
        self._fontSize = None
        self._fontStyle = None
        self._fontWeight = None
        self._letterSpacing = None

        self.lineHeight = None
        self.textDirection = None
        self.textRotation = None
        self.language = None
        # this might be a complex device -- underline, overline, line-through etc.
        self.textDecoration = None

        self._justify = None
        self._alignHorizontal = None
        self._alignVertical = None

    def _getAlignVertical(self):
        return self._alignVertical

    def _setAlignVertical(self, value):
        if value in (None, 'top', 'middle', 'bottom', 'baseline'):
            self._alignVertical = value
        else:
            raise TextFormatException(f'invalid vertical align: {value}')

    alignVertical = property(_getAlignVertical,
                             _setAlignVertical,
                             doc='''
        Get or set the vertical align. Valid values are top, middle, bottom, baseline
        or None

        >>> te = style.TextStyle()
        >>> te.alignVertical = 'top'
        >>> te.alignVertical
        'top'
        ''')

    def _getAlignHorizontal(self):
        return self._alignHorizontal

    def _setAlignHorizontal(self, value):
        if value in (None, 'left', 'right', 'center'):
            self._alignHorizontal = value
        else:
            raise TextFormatException(f'invalid horizontal align: {value}')

    alignHorizontal = property(_getAlignHorizontal,
                               _setAlignHorizontal,
                               doc='''
        Get or set the horizontal alignment.  Valid values are left, right, center,
        or None


        >>> te = style.TextStyle()
        >>> te.alignHorizontal = 'right'
        >>> te.alignHorizontal
        'right'
        ''')

    def _getJustify(self):
        return self._justify

    def _setJustify(self, value):
        if value is None:
            self._justify = None
        else:
            if value.lower() not in ('left', 'center', 'right', 'full'):
                raise TextFormatException(f'Not a supported justification: {value}')
            self._justify = value.lower()

    justify = property(_getJustify,
                       _setJustify,
                       doc='''
        Get or set the justification.  Valid values are left,
        center, right, full (not supported by MusicXML), and None

        >>> tst = style.TextStyle()
        >>> tst.justify = 'center'
        >>> tst.justify
        'center'
        ''')

    def _getStyle(self):
        return self._fontStyle

    def _setStyle(self, value):
        if value is None:
            self._fontStyle = None
        else:
            if value.lower() not in ('italic', 'normal', 'bold', 'bolditalic'):
                raise TextFormatException(f'Not a supported fontStyle: {value}')
            self._fontStyle = value.lower()

    fontStyle = property(_getStyle,
                         _setStyle,
                         doc='''
        Get or set the style, as normal, italic, bold, and bolditalic.

        >>> tst = style.TextStyle()
        >>> tst.fontStyle = 'bold'
        >>> tst.fontStyle
        'bold'
        ''')

    def _getWeight(self):
        return self._fontWeight

    def _setWeight(self, value):
        if value is None:
            self._fontWeight = None
        else:
            if value.lower() not in ('normal', 'bold'):
                raise TextFormatException(f'Not a supported fontWeight: {value}')
            self._fontWeight = value.lower()

    fontWeight = property(_getWeight,
                          _setWeight,
                          doc='''
        Get or set the weight, as normal, or bold.

        >>> tst = style.TextStyle()
        >>> tst.fontWeight = 'bold'
        >>> tst.fontWeight
        'bold'
        ''')

    def _getSize(self):
        return self._fontSize

    def _setSize(self, value):
        if value is not None:
            try:
                value = common.numToIntOrFloat(value)
            except ValueError:
                pass  # MusicXML font sizes can be CSS strings.
                # raise TextFormatException('Not a supported size: %s' % value)
        self._fontSize = value

    fontSize = property(_getSize,
                        _setSize,
                        doc='''
        Get or set the size.  Best, an int or float, but also a css font size

        >>> tst = style.TextStyle()
        >>> tst.fontSize = 20
        >>> tst.fontSize
        20
        ''')

    def _getLetterSpacing(self):
        return self._letterSpacing

    def _setLetterSpacing(self, value):
        if value != 'normal' and value is not None:
            # convert to number
            try:
                value = float(value)
            except ValueError as ve:
                raise TextFormatException(
                    f'Not a supported letterSpacing: {value!r}'
                ) from ve

        self._letterSpacing = value

    letterSpacing = property(_getLetterSpacing,
                             _setLetterSpacing,
                             doc='''
         Get or set the letter spacing.

        >>> tst = style.TextStyle()
        >>> tst.letterSpacing = 20
        >>> tst.letterSpacing
        20.0
        >>> tst.letterSpacing = 'normal'
        ''')

    @property
    def fontFamily(self):
        '''
        Returns a list of font family names associated with
        the style, or sets the font family name list.

        If a single string is passed then it is converted to
        a list.

        >>> ts = style.TextStyle()
        >>> ff = ts.fontFamily
        >>> ff
        []
        >>> ff.append('Times')
        >>> ts.fontFamily
        ['Times']
        >>> ts.fontFamily.append('Garamond')
        >>> ts.fontFamily
        ['Times', 'Garamond']
        >>> ts.fontFamily = 'Helvetica, sans-serif'
        >>> ts.fontFamily
        ['Helvetica', 'sans-serif']
        '''
        if self._fontFamily is None:
            self._fontFamily = []
        return self._fontFamily

    @fontFamily.setter
    def fontFamily(self, newFamily):
        if common.isIterable(newFamily):
            self._fontFamily = newFamily
        else:
            self._fontFamily = [f.strip() for f in newFamily.split(',')]


class TextStylePlacement(TextStyle):
    '''
    TextStyle plus a placement attribute
    '''

    def __init__(self):
        super().__init__()
        self.placement = None


class BezierStyle(Style):
    '''
    From the MusicXML Definition.
    '''

    def __init__(self):
        super().__init__()

        self.bezierOffset = None
        self.bezierOffset2 = None

        self.bezierX = None
        self.bezierY = None
        self.bezierX2 = None
        self.bezierY2 = None


class LineStyle(Style):
    '''
    from the MusicXML Definition

    Defines lineShape ('straight', 'curved' or None)
    lineType ('solid', 'dashed', 'dotted', 'wavy' or None)
    dashLength (in tenths)
    spaceLength (in tenths)
    '''

    def __init__(self):
        super().__init__()

        self.lineShape = None
        self.lineType = None
        self.dashLength = None
        self.spaceLength = None


class StreamStyle(Style):
    '''
    Includes several elements in the MusicXML <appearance> tag in <defaults>
    along with <music-font> and <word-font>
    '''

    def __init__(self):
        super().__init__()
        self.lineWidths = []  # two-tuples of type, width measured in tenths
        self.noteSizes = []  # two-tuples of type and percentages of the normal size
        self.distances = []  # two-tuples of beam or hyphen and tenths
        self.otherAppearances = []  # two-tuples of type and tenths
        self.musicFont = None  # None or a TextStyle object
        self.wordFont = None  # None or a TextStyle object
        self.lyricFonts = []  # a list of TextStyle objects
        self.lyricLanguages = []  # a list of strings

        self.printPartName = True
        self.printPartAbbreviation = True

        # can be None -- meaning no comment,
        # 'none', 'measure', or 'system'...
        self.measureNumbering = None
        self.measureNumberStyle = None


class BeamStyle(Style):
    '''
    Style for beams
    '''

    def __init__(self):
        super().__init__()
        self.fan = None


class StyleMixin(common.SlottedObjectMixin):
    '''
    Mixin for any class that wants to support style and editorial, since several
    non-music21 objects, such as Lyrics and Accidentals will support Style.

    Not used by Music21Objects because of the added trouble in copying etc. so
    there is code duplication with base.Music21Object
    '''
    _styleClass = Style

    __slots__ = ('_style', '_editorial')

    def __init__(self):
        #  no need to call super().__init__() on SlottedObjectMixin
        self._style = None
        self._editorial = None

    @property
    def hasStyleInformation(self):
        '''
        Returns True if there is a :class:`~music21.style.Style` object
        already associated with this object, False otherwise.

        Calling .style on an object will always create a new
        Style object, so even though a new Style object isn't too expensive
        to create, this property helps to prevent creating new Styles more than
        necessary.

        >>> lObj = note.Lyric('hello')
        >>> lObj.hasStyleInformation
        False
        >>> lObj.style
        <music21.style.TextStylePlacement object at 0x10b0a2080>
        >>> lObj.hasStyleInformation
        True
        '''
        try:
            self._style
        except AttributeError:
            pass

        return not (self._style is None)

    @property
    def style(self):
        '''
        Returns (or Creates and then Returns) the Style object
        associated with this object, or sets a new
        style object.  Different classes might use
        different Style objects because they might have different
        style needs (such as text formatting or bezier positioning)

        Eventually will also query the groups to see if they have
        any styles associated with them.

        >>> acc = pitch.Accidental()
        >>> st = acc.style
        >>> st
        <music21.style.TextStyle object at 0x10ba96208>
        >>> st.absoluteX = 20.0
        >>> st.absoluteX
        20.0
        >>> acc.style = style.TextStyle()
        >>> acc.style.absoluteX is None
        True
        '''
        if self._style is None:
            styleClass = self._styleClass
            self._style = styleClass()
        return self._style

    @style.setter
    def style(self, newStyle):
        self._style = newStyle

    @property
    def hasEditorialInformation(self):
        '''
        Returns True if there is a :class:`~music21.editorial.Editorial` object
        already associated with this object, False otherwise.

        Calling .style on an object will always create a new
        Style object, so even though a new Style object isn't too expensive
        to create, this property helps to prevent creating new Styles more than
        necessary.

        >>> acc = pitch.Accidental('#')
        >>> acc.hasEditorialInformation
        False
        >>> acc.editorial
        <music21.editorial.Editorial {}>
        >>> acc.hasEditorialInformation
        True
        '''
        return not (self._editorial is None)

    @property
    def editorial(self):
        '''
        a :class:`~music21.editorial.Editorial` object that stores editorial information
        (comments, footnotes, harmonic information, ficta).

        Created automatically as needed:

        >>> acc = pitch.Accidental()
        >>> acc.editorial
        <music21.editorial.Editorial {}>
        >>> acc.editorial.ficta = pitch.Accidental('sharp')
        >>> acc.editorial.ficta
        <accidental sharp>
        >>> acc.editorial
        <music21.editorial.Editorial {'ficta': <accidental sharp>}>
        '''
        from music21 import editorial
        if self._editorial is None:
            self._editorial = editorial.Editorial()
        return self._editorial

    @editorial.setter
    def editorial(self, ed):
        self._editorial = ed


class Test(unittest.TestCase):
    pass


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)  # , runTest='')

