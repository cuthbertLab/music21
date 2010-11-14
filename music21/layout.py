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
        234.0
        >>> slAlt.rightMargin
        124.0
        >>> slAlt.distance
        3.0
        >>> slAlt.isNew
        True
        '''
        mxPrint = musicxml.Print()
        if self.isNew:
            mxPrint.set('new-system', 'yes')
        
        mxSystemLayout = musicxml.SystemLayout()
        mxSystemMargins = musicxml.SystemMargins()

        # musicxml requires both left and right defined
        matchLeft = False
        matchRight = False
        if self.leftMargin != None:
            mxSystemMargins.set('leftMargin', self.leftMargin)
            matchLeft = True
        if self.rightMargin != None:
            mxSystemMargins.set('rightMargin', self.rightMargin)
            matchRight = True

        if matchLeft and not matchRight:
            mxSystemMargins.set('rightMargin', 0)
        if matchRight and not matchLeft:
            mxSystemMargins.set('leftMargin', 0)

        # stored on components list
        if matchLeft or matchRight:
            mxSystemLayout.append(mxSystemMargins) 

        if self.distance != None:
            #mxSystemDistance = musicxml.SystemDistance()
            #mxSystemDistance.set('charData', self.distance)
            # only append if defined
            mxSystemLayout.systemDistance = self.distance

        mxPrint.append(mxSystemLayout)

        return mxPrint


    def _setMX(self, mxPrint):
        '''Given an mxPrint object, set object data

        >>> from music21 import musicxml
        >>> mxPrint = musicxml.Print()
        >>> mxPrint.set('new-system', 'yes')
        >>> mxSystemLayout = musicxml.SystemLayout()
        >>> mxSystemLayout.systemDistance = 55
        >>> mxSystemMargins = musicxml.SystemMargins()
        >>> mxSystemMargins.set('leftMargin', 20)
        >>> mxSystemMargins.set('rightMargin', 30.2)
        >>> mxSystemLayout.append(mxSystemMargins) 
        >>> mxPrint.append(mxSystemLayout)

        >>> sl = SystemLayout()
        >>> sl.mx = mxPrint
        >>> sl.isNew
        True
        >>> sl.rightMargin > 30.1 and sl.rightMargin <= 30.2
        True
        >>> sl.leftMargin
        20.0
        >>> sl.distance
        55.0
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
        for x in mxSystemLayout:
            if isinstance(x, musicxml.SystemMargins):
                mxSystemMargins = x

        if mxSystemMargins != None:
            data = mxSystemMargins.get('leftMargin')
            if data != None:
                # may be floating point values
                self.leftMargin = float(data)
            data = mxSystemMargins.get('rightMargin')
            if data != None:
                self.rightMargin = float(data)
        
        if mxSystemLayout != [] and mxSystemLayout.systemDistance != None:
            self.distance = float(mxSystemLayout.systemDistance)

    mx = property(_getMX, _setMX)    







#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testBasic(self):
        import music21
        from music21 import stream, note
        s = stream.Stream()
        
        for i in range(1,11):
            m = stream.Measure()
            m.number = i
            n = note.Note()
            m.append(n)
            s.append(m)
        
        sl = music21.layout.SystemLayout()
        #sl.isNew = True # this should not be on first system
        # as this causes all subsequent margins to be distorted
        sl.leftMargin = 300
        sl.rightMargin = 300
        s.getElementsByClass('Measure')[0].insert(0, sl)
        
        sl = music21.layout.SystemLayout()
        sl.isNew = True
        sl.leftMargin = 200
        sl.rightMargin = 200
        sl.distance = 40
        s.getElementsByClass('Measure')[2].insert(0, sl)
        
        sl = music21.layout.SystemLayout()
        sl.isNew = True
        sl.leftMargin = 220
        s.getElementsByClass('Measure')[4].insert(0, sl)
        
        sl = music21.layout.SystemLayout()
        sl.isNew = True
        sl.leftMargin = 60
        sl.rightMargin = 300
        sl.distance = 200
        s.getElementsByClass('Measure')[6].insert(0, sl)
        
        sl = music21.layout.SystemLayout()
        sl.isNew = True
        sl.leftMargin = 0
        sl.rightMargin = 0
        s.getElementsByClass('Measure')[8].insert(0, sl)

#         systemLayoutList = s.flat.getElementsByClass(music21.layout.SystemLayout)
#         self.assertEqual(len(systemLayoutList), 4)

        #s.show()
    
        mx = s.musicxml


#-------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        a = Test()

        a.testBasic()


#------------------------------------------------------------------------------
# eof

