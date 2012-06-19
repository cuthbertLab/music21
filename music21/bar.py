# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         bar.py
# Purpose:      music21 classes for representing bars, repeats, and related
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009-2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''Object models of bars and repeats. 
'''

import unittest, doctest

import music21
from music21 import expressions
from music21 import repeat
from music21 import musicxml
from music21.musicxml import translate as musicxmlTranslate

from music21 import environment
_MOD = 'bar.py'
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------

class BarException(Exception):
    pass


# store alternative names for styles; use this dictionary for translation
# reference
barStyleList = ['regular', 'dotted', 'dashed', 'heavy', 'double', 'final', 
                'heavy-light', 'heavy-heavy', 'tick', 'short', 'none']
barStyleDict = {'light-light': 'double',
                'light-heavy': 'final', }
reverseBarStyleDict = {'double': 'light-light',
                       'final': 'light-heavy', }


def styleToMusicXMLBarStyle(value):
    '''
    Convert a music21 barline name into the musicxml name -- 
    essentially just changes the names of 'double' and 'final'
    to 'light-light' and 'light-heavy'


    Does not do error checking to make sure it's a valid name,
    since setting the style on a Barline object already does that.
    

    >>> styleToMusicXMLBarStyle('final')
    'light-heavy'
    >>> styleToMusicXMLBarStyle('regular')
    'regular'
    '''
    if value.lower() in reverseBarStyleDict:
        return reverseBarStyleDict[value.lower()]
    else:
        return value

def standardizeBarStyle(value):
    '''
    Standardizes bar style names.
    
    converts all names to lower case, None to 'regular',
    and 'light-light' to 'double' and 'light-heavy' to 'final',
    raises an error for unknown styles.
    '''  
    if value is None:
        return 'regular' # for now, return with string

    value = value.lower()
    
    if value in barStyleList:
        return value
    elif value in barStyleDict:
        return barStyleDict[value]
    # if not match
    else:
        raise BarException('cannot process style: %s' % value)
 

#-------------------------------------------------------------------------------
class Barline(music21.Music21Object):
    '''A representation of a barline. 
    Barlines are conventionally assigned to Measure objects 
    using the leftBarline and rightBarline attributes.


    >>> from music21 import *
    >>> bl = bar.Barline('double')
    >>> bl
    <music21.bar.Barline style=double>


    The style can also just be set via a keyword of "style".  Or if no style is specified, 
    a regular barline is returned.  Location can also be explicitly stored, but it's not
    needed except for musicxml translation:


    >>> bl2 = bar.Barline(style='dashed')
    >>> bl2
    <music21.bar.Barline style=dashed>
    >>> bl3 = bar.Barline()
    >>> bl3
    <music21.bar.Barline style=regular>
    >>> bl4 = bar.Barline(style='final', location='right')
    >>> bl4
    <music21.bar.Barline style=final>
    '''
    validStyles = barStyleDict.keys()

    _style = None
    _pause = None  # can be music21.expressions.Fermata object
    
    classSortOrder = -5 

    def __init__(self, style = None, location = None):
        music21.Music21Object.__init__(self)

        # this will raise an exception on error from property
        self.style = style

        # location is primarily stored in the stream as leftBarline or rightBarline
        # but can also be stored here.
        self.location = location # musicxml values: can be left, right, middle, None

    def __repr__(self):
        return "<music21.bar.Barline style=%s>" % (self.style)

    def _getStyle(self):
        return self._style

    def _setStyle(self, value):
        # will raise exception on error
        self._style = standardizeBarStyle(value)

    style = property(_getStyle, _setStyle, 
        doc = '''Get and set the Barline style property.

        >>> b = Barline()
        ''')
    def _musicXMLBarStyle(self):
        return styleToMusicXMLBarStyle(self.style)
    
    musicXMLBarStyle = property(_musicXMLBarStyle)

    def _getMX(self):
        '''
        >>> b = Barline('final')
        >>> mxBarline = b.mx
        >>> mxBarline.get('barStyle')
        'light-heavy'

        '''
        mxBarline = musicxml.Barline()
        mxBarline.set('barStyle', self.musicXMLBarStyle)
        if self.location != None:
            mxBarline.set('location', self.location)
        return mxBarline

    def _setMX(self, mxBarline):
        '''Given an mxBarline, fille the necessary parameters

        >>> from music21 import musicxml
        >>> mxBarline = musicxml.Barline()
        >>> mxBarline.set('barStyle', 'light-light')
        >>> b = Barline()
        >>> b.mx = mxBarline
        >>> b.style
        'double'
        '''
        self.style = mxBarline.get('barStyle')
        location = mxBarline.get('location')
        if location != None:
            self.location = location

    mx = property(_getMX, _setMX)    






#-------------------------------------------------------------------------------

# note that musicxml permits the barline to have attributes for segno and coda
#		<xs:attribute name="segno" type="xs:token"/>
#		<xs:attribute name="coda" type="xs:token"/>

# type <ending> in musicxml is used to mark different endings

class Repeat(repeat.RepeatMark, Barline):
    '''A Repeat barline.

    The `direction` parameter can be one of 'start' or 'end.'

    >>> from music21 import *
    >>> rep = bar.Repeat(direction='end', times=3)
    >>> rep
    <music21.bar.Repeat direction=end times=3>

    To apply a repeat barline assign it to either the `.leftBarline` or `.rightBarline` attribute
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
        {0.0} <music21.bar.Barline style=double>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.note.Note D-->
        {1.0} <music21.note.Note D-->
        {2.0} <music21.note.Note D-->
        {3.0} <music21.note.Note D-->
        {4.0} <music21.bar.Barline style=double>
    {4.0} <music21.stream.Measure 0 offset=4.0>
        {0.0} <music21.bar.Barline style=double>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.note.Note D-->
        {1.0} <music21.note.Note D-->
        {2.0} <music21.note.Note D-->
        {3.0} <music21.note.Note D-->
        {4.0} <music21.bar.Barline style=double>


    '''
    _repeatDots = None # not sure what this is for; inherited from old modles


    def __init__(self, direction='start', times=None):
        if direction == 'start':
            style = 'heavy-light'
        else:
            style = 'light-heavy'
        
        Barline.__init__(self, style=style)

        self._direction = None # either start or end
        self._times = None  # if an end, how many repeats

        # start is forward, end is backward in musicxml
        self._setDirection(direction) # start, end
        self._setTimes(times)

    def __repr__(self):
        if self._times is not None:
            return "<music21.bar.Repeat direction=%s times=%s>" % (self.direction, self.times)
        else:
            return "<music21.bar.Repeat direction=%s>" % (self.direction)

    def _setDirection(self, value):
        if value.lower() in ['start', 'end']:
            self._direction = value.lower()
            if self._direction=='end':
                self.style='light-heavy'
            elif self._direction=='start':
                self.style='heavy-light'
        
        
        else:
            raise BarException('cannot set repeat direction to: %s' % value)

    def _getDirection(self):
        return self._direction

    direction = property(_getDirection, _setDirection, 
        doc = '''Get or set the direction of this Repeat barline. Can be start or end. 
        
        TODO: show how changing direction changes style.
        ''')

    def _setTimes(self, value):
        if value is None:
            self._times = None
        else:
            try:
                candidate = int(value)
            except ValueError:
                raise BarException('cannot set repeat times to: %s' % value)
            if candidate < 0:
                raise BarException('cannot set repeat times to a value less than zero: %s' % value)
            if self._direction == 'start':
                raise BarException('cannot set repeat times on a start Repeat')

            self._times = candidate

    def _getTimes(self):
        return self._times

    times = property(_getTimes, _setTimes, 
        doc = '''Get or set the times property of this barline. This defines how many times the repeat happens. A standard repeat repeats 2 times; values equal to or greater than 0 are permitted. A repeat of 0 skips the repeated passage. 
        
        >>> from music21 import bar
        >>> lb = bar.Repeat(direction='start')
        >>> rb = bar.Repeat(direction='end')
        >>> lb.times = 3
        Traceback (most recent call last):
        BarException: cannot set repeat times on a start Repeat
        >>> rb.times = 3
        >>> rb.times = -3
        Traceback (most recent call last):
        BarException: cannot set repeat times to a value less than zero: -3
        ''')


    def getTextExpression(self, prefix='', postfix='x'):
        '''Return a configured :class:`~music21.expressions.TextExpressions` object describing the repeat times. Append this to the stream for annotation of repeat times. 
        '''
        value = '%s%s%s' % (prefix, self._times, postfix)
        return expressions.TextExpression(value)


    def _getMX(self):
        return musicxmlTranslate.repeatToMx(self)

    def _setMX(self, mxBarline):
        # provide self to configure
        musicxmlTranslate.mxToRepeat(mxBarline, self)

    mx = property(_getMX, _setMX)    






#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
   

    def testSortorder(self):
        from music21 import stream, bar, clef, note, metadata
        m = stream.Measure()
        b = bar.Repeat()
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
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof

