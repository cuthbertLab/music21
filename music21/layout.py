#-------------------------------------------------------------------------------
# Name:         layout.py
# Purpose:      Layout objects 
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''Layout objects provide models of various forms of page or other musical layouts. Layout objects may be used like other :class:`~music21.base.Music21Object` and placed on a :class:`~music21.stream.Stream`.
'''


# layout objects suggested by musicxml

# Defaults:
# PageLayout
# SystemLayout
# StaffLayout

# may need to have object to convert between size units

import string, copy, math
import unittest, doctest

import music21
from music21 import musicxml


#-------------------------------------------------------------------------------

class SystemLayout(music21.Music21Object):
    '''Parameters for configureing a system's layout.

    SystemLayout objects may be found on Measure or Part Streams.    

    >>> sl = SystemLayout(leftmargin=234, rightmargin=124, distance=3, isNew=True)
    >>> sl.distance
    3
    >>> sl.rightMargin
    124
    >>> sl.leftMargin
    234
    >>> sl.isNew
    True
    '''
    def __init__(self, *args, **keywords):
        music21.Music21Object.__init__(self)
        
        self.leftMargin = None
        self.rightMargin = None

        # this is probably the distance between adjacent systems
        # musicxml also defines a top-system-distance tag; this may not be
        # necessary to implements, as the top system is defined by context
        self.distance = None

        # store if this is the start of a new system
        self.isNew = None

        for key in keywords.keys():
            if key.lower() == 'leftmargin':
                self.leftMargin = keywords[key]
            if key.lower() == 'rightmargin':
                self.rightMargin = keywords[key]
            if key.lower() == 'distance':
                self.distance = keywords[key]
            if key.lower() == 'isnew':
                self.isNew = keywords[key]


    #---------------------------------------------------------------------------
    def _getMX(self):
        '''Return a mxPrint object

        >>> sl = SystemLayout(leftmargin=234, rightmargin=124, distance=3, isNew=True)
        >>> mxPrint = sl.mx
        >>> slAlt = SystemLayout()
        >>> slAlt.mx = mxPrint # transfter
        >>> slAlt.leftMargin
        234
        >>> slAlt.rightMargin
        124
        >>> slAlt.distance
        3
        >>> slAlt.isNew
        True
        '''
        mxPrint = musicxml.Print()
        if self.isNew:
            mxPrint.set('new-system', 'yes')
        
        mxSystemLayout = musicxml.SystemLayout()
        mxSystemMargins = musicxml.SystemMargins()
        if self.leftMargin != None:
            mxSystemMargins.set('leftMargin', self.leftMargin)
        if self.rightMargin != None:
            mxSystemMargins.set('rightMargin', self.rightMargin)

        # stored on components list
        mxSystemLayout.append(mxSystemMargins) 

        if self.distance != None:
            mxSystemDistance = musicxml.SystemDistance()
            mxSystemDistance.set('charData', self.distance)
            # only append if defined
            mxSystemLayout.append(mxSystemDistance)

        mxPrint.append(mxSystemLayout)

        return mxPrint


    def _setMX(self, mxPrint):
        '''Given an mxPrint object, set object data

        >>> from music21 import musicxml
        >>> mxPrint = musicxml.Print()
        >>> mxPrint.set('new-system', 'yes')
        >>> mxSystemLayout = musicxml.SystemLayout()
        >>> mxSystemMargins = musicxml.SystemMargins()
        >>> mxSystemMargins.set('leftMargin', 20)
        >>> mxSystemMargins.set('rightMargin', 30)
        >>> mxSystemDistance = musicxml.SystemDistance()
        >>> mxSystemDistance.set('charData', 55)
        >>> mxSystemLayout.append(mxSystemMargins) 
        >>> mxSystemLayout.append(mxSystemDistance)
        >>> mxPrint.append(mxSystemLayout)

        >>> sl = SystemLayout()
        >>> sl.mx = mxPrint
        >>> sl.isNew
        True
        >>> sl.rightMargin
        30
        >>> sl.leftMargin
        20
        >>> sl.distance
        55
        '''
        data = mxPrint.get('newSystem')
        if data == 'yes': # encoded as yes/no in musicxml
            self.isNew = True
        elif data == 'no':
            self.isNew = False

        #mxSystemLayout = mxPrint.get('systemLayout')
        mxSystemLayout = [] # blank
        for x in mxPrint:
            if isinstance(x, musicxml.SystemLayout):
                mxSystemLayout = x
                break # find first and break

        mxSystemMargins = None
        mxSystemDistance = None
        for x in mxSystemLayout:
            if isinstance(x, musicxml.SystemMargins):
                mxSystemMargins = x
            if isinstance(x, musicxml.SystemDistance):
                mxSystemDistance = x

        if mxSystemMargins != None:
            data = mxSystemMargins.get('leftMargin')
            if data != None:
                self.leftMargin = int(data)
            data = mxSystemMargins.get('rightMargin')
            if data != None:
                self.rightMargin = int(data)

        if mxSystemDistance != None:
            data = mxSystemDistance.get('charData')
            if data != None:
                self.distance = int(data)

    mx = property(_getMX, _setMX)    







#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testPass(self):
        pass



#-------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        a = Test()
        #a.testNoteBeatPropertyCorpus()


