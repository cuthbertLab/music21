# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         style.py
# Purpose:      Music21 classes for non-analytic display properties
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2016 Michael Scott Cuthbert and the music21
#               Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------
'''
The style module represents information about the style of a Note, Accidental,
etc. such that precise positioning information, layout, size, etc. can be specified.
'''
import unittest

from music21 import common
from music21 import exceptions21

class TextFormatException(exceptions21.Music21Exception):
    pass

class Style(object):
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
    def __init__(self):
        self.size = None

        self.relativeX = None
        self.relativeY = None
        self.absoluteX = None
        
        # managed by property below.
        self._absoluteY = None
                
        self._enclosure = None
        
        # how should this symbol be represented in the font?
        # SMuFL characters are allowed.
        self.fontRepresentation = None
        
        # TODO: migrate from elsewhere
        # self.color = None
        
        self.units = 'tenths'

    def _getEnclosure(self):
        return self._enclosure
    
    def _setEnclosure(self, value):
        if value is None:
            self._enclosure = value
        elif value == 'none':
            self._enclosure = None
        elif value.lower() in ('rectangle', 'square', 'oval', 'circle',
                               'bracket', 'triangle', 'diamond'):
            self._enclosure = value.lower()
        else:
            raise TextFormatException('Not a supported enclosure: %s' % value)
    
    enclosure = property(_getEnclosure, _setEnclosure, 
        doc = '''Get or set the enclosure.  Valid names are
        rectangle, square, oval, circle, bracket, triangle, diamond, or None.

        
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
            except (ValueError):
                raise TextFormatException('Not a supported absoluteY position: %s' % value)
            self._absoluteY = value
    
    absoluteY = property(_getAbsoluteY, _setAbsoluteY, 
        doc = '''
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



class TextStyle(Style):
    '''
    A Style object that also includes text formatting.
    '''
    def __init__(self):
        super(TextStyle, self).__init__()
        self._fontFamily = None
        self._fontSize = None
        self._fontStyle = None
        self._fontWeight = None
        self._letterSpacing = None

        # this might be a complex device -- underline, overline, line-through etc.
        self.textDecoration = None

        self._justify = None
        self._alignHorizontal = 'left'
        self._alignVertical = 'top'

    def _getAlignVertical(self):
        return self._alignVertical
    
    def _setAlignVertical(self, value):
        if value in (None, 'top', 'middle', 'bottom', 'baseline'):
            self._alignVertical = value 
        else:
            raise TextFormatException('invalid vertical align: %s' % value)
    
    alignVertical = property(_getAlignVertical, _setAlignVertical, 
        doc = '''
        Get or set the vertical align. Valid values are top, middle, bottom, and baseline
        
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
            raise TextFormatException('invalid horizontal align: %s' % value)
    
    alignHorizontal = property(_getAlignHorizontal,     
        _setAlignHorizontal, 
        doc = '''
        Get or set the horizontal alignment.  Valid values are left, right, center

        
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
                raise TextFormatException('Not a supported justification: %s' % value)
            self._justify = value.lower()

    justify = property(_getJustify, _setJustify, 
        doc = '''Get or set the justification.  Valid values are left,
        center, right, and full (the last not supported by MusicXML)

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
                raise TextFormatException('Not a supported fontStyle: %s' % value)
            self._fontStyle = value.lower()

    fontStyle = property(_getStyle, _setStyle, 
        doc = '''Get or set the style, as normal, italic, bold, and bolditalic.
        
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
                raise TextFormatException('Not a supported fontWeight: %s' % value)
            self._fontWeight = value.lower()

    fontWeight = property(_getWeight, _setWeight, 
        doc = '''Get or set the weight, as normal, or bold.

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
                pass # MusicXML font sizes can be CSS strings...
                #raise TextFormatException('Not a supported size: %s' % value)
        self._fontSize = value

    fontSize = property(_getSize, _setSize, 
        doc = '''Get or set the size.  Best, an int or float, but also a css font size

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
            except ValueError:
                raise TextFormatException('Not a supported letterSpacing: %s' % value)

        self._letterSpacing = value

    letterSpacing = property(_getLetterSpacing, _setLetterSpacing, 
        doc = '''Get or set the letter spacing.

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
        >>> ts.fontFamily = 'Helvetica'
        >>> ts.fontFamily
        ['Helvetica']
        '''
        if self._fontFamily is None:
            self._fontFamily = []
        return self._fontFamily

    @fontFamily.setter
    def fontFamily(self, newFamily):
        if common.isIterable(newFamily):
            self._fontFamily = newFamily
        else:
            self._fontFamily = [newFamily]
        

class BezierStyle(Style):
    '''
    From the MusicXML Definition.
    '''
    def __init__(self):
        super(BezierStyle, self).__init__()

        self.bezierOffset = None
        self.bezierOffset2 = None

        self.bezierX = None
        self.bezierY = None
        self.bezierX2 = None
        self.bezierY2 = None

class Test(unittest.TestCase):
    pass

if __name__ == "__main__":
    import music21
    music21.mainTest(Test) #, runTest='')

#------------------------------------------------------------------------------
# eof
