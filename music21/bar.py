#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         bar.py
# Purpose:      music21 classes for representing bars, repeats, and related
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''Object models of bars and repeats. 
'''

import unittest, doctest

import music21
from music21 import musicxml

from music21 import environment
_MOD = 'bar.py'
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------

class BarException(Exception):
    pass


# store alternative names for styles; use this dictionary for translation
# reference
barStyleDict = {
    'regular': [], 
    'dotted': [], 
    'dashed': [], 
    'heavy': [], 
    'light-light': ['double'],              
    'light-heavy': ['final'], 
    'heavy-light': [], 
    'heavy-heavy': [], 
    'tick': [],
    'short': [], 
    'none': [],
        }


def styleToBarStyle(value):
    '''Convert a bar style into a standard form.

    >>> styleToBarStyle('regular')
    'regular'
    >>> styleToBarStyle('final')
    'light-heavy'

    '''
    if value == None:
        return 'none' # for now, return with string
    if value.lower() in barStyleDict.keys():
        return value.lower()
    for key in barStyleDict.keys():
        for alt in barStyleDict[key]: # look at all aternatives
            if alt.lower() == value.lower():
                return key
    # if not match
    raise BarException('cannot process styel: %s' % value)
 

#-------------------------------------------------------------------------------
class Barline(music21.Music21Object):

    validStyles = barStyleDict.keys()

    _style = None
    _pause = None  # can be music21.expressions.Fermata object
    
    def __init__(self, style = None):
        music21.Music21Object.__init__(self)

        # this will raise an exception on error from property
        self.style = style

        # this parameter does not seem to be needed in this object
        self.location = None # can be left, right, middle, None

    def _getStyle(self):
        return self._style

    def _setStyle(self, value):
        # will raise exception on error
        self._style = styleToBarStyle(value)

    style = property(_getStyle, _setStyle, 
        doc = '''Get and set the Barline style property.

        >>> b = Barline()
        ''')


    def _getMX(self):
        '''
        >>> b = Barline('final')
        >>> mxBarline = b.mx
        >>> mxBarline.get('barStyle')
        'light-heavy'

        '''
        mxBarline = musicxml.Barline()
        mxBarline.set('barStyle', self.style)
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
        'light-light'
        '''
        self.style = mxBarline.get('barStyle')
        location = mxBarline.get('location')
        if location != None:
            self.location = location

    mx = property(_getMX, _setMX)    






#-------------------------------------------------------------------------------
class Repeat(Barline):
    '''A Repeat barline

    '''

    _repeatDots = None # not sure what this is for; inherited from old modles

    def __init__(self, style=None, direction='start'):
        Barline.__init__(self, style=style)

        # must declare a direction
        # start is forward, end is backward in musicxml
        self.direction = direction # start, end, or bidirectional
        self.times = None  # if an end, how many repeats


    def _getMX(self):
        '''
        >>> b = Repeat('light-heavy')
        >>> mxBarline = b.mx
        >>> mxBarline.get('barStyle')
        'light-heavy'
        '''
        mxBarline = musicxml.Barline()
        mxBarline.set('barStyle', self.style)
        if self.location != None:
            mxBarline.set('location', self.location)

        mxRepeat = musicxml.Repeat()
        if self.direction == 'start':
            mxRepeat.set('direction', 'forward')
        elif self.direction == 'end':
            mxRepeat.set('direction', 'backward')
        elif self.direction == 'bidirectional':
            environLocal.printDebug(['skipping bi-directional repeat'])
        else:
            raise BarException('cannot handle direction format:', self.direction)

        if self.times != None:
            mxRepeat.set('times', self.times)

        mxBarline.set('repeatObj', mxRepeat)

        return mxBarline

    def _setMX(self, mxBarline):
        '''Given an mxBarline, fille the necessary parameters

        >>> from music21 import musicxml
        >>> mxRepeat = musicxml.Repeat()
        >>> mxRepeat.set('direction', 'forward')
        >>> mxRepeat.get('times') == None
        True
        >>> mxBarline = musicxml.Barline()
        >>> mxBarline.set('barStyle', 'light-heavy')
        >>> mxBarline.set('repeatObj', mxRepeat)
        >>> b = Repeat()
        >>> b.mx = mxBarline
        >>> b.style
        'light-heavy'
        >>> b.direction
        'start'
        '''
        self.style = mxBarline.get('barStyle')
        location = mxBarline.get('location')
        if location != None:
            self.location = location

        mxRepeat = mxBarline.get('repeatObj')
        if mxRepeat == None:
            raise BarException('attempting to create a Repeat from an MusicXML bar that does not define a repeat')

        mxDirection = mxRepeat.get('direction')

        #environLocal.printDebug(['mxRepeat', mxRepeat, mxRepeat._attr])

        if mxRepeat.get('times') != None:
            # make into a number
            self.times = int(mxRepeat.get('times'))

        if mxDirection.lower() == 'forward':
            self.direction = 'start'
        elif mxDirection.lower() == 'backward':
            self.direction = 'end'
        else:
            raise BarException('cannot handle mx direction format:', mxDirection)


    mx = property(_getMX, _setMX)    






#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
   


if __name__ == '__main__':
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof

