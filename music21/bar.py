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


# store alternative names for styles
# derived from musicxml    

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
    '''Convert a bar style into a standard form

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
    validRepeats = ['right', 'left', 'both']

    _repeatDots = None
    _style = None
    _pause = None  # can be music21.expressions.Fermata object
    
    def __init__(self, style = None):
        music21.Music21Object.__init__(self)

        # this will raise an exception on error from property
        self.style = style
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
class Repeat(music21.Music21Object):
    '''The Repeat object defines a jump but not a change in barline style.  However
    the Measure object\'s addRepeat both adds a Repeat object and changes the appropriate
    Barline style.'''
    pass




#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
   


if __name__ == '__main__':
    music21.mainTest(Test)
