# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         layout.py
# Purpose:      Layout objects 
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010, 2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''
Layout objects provide models of various forms of page or other musical layouts. 
Layout objects may be used like other :class:`~music21.base.Music21Object` and 
placed on a :class:`~music21.stream.Stream`.
'''


# layout objects suggested by musicxml

# Defaults:
# PageLayout
# SystemLayout
# StaffLayout

# may need to have object to convert between size units

import unittest

from music21 import base
from music21 import spanner

#-------------------------------------------------------------------------------
class PageLayout(base.Music21Object):
    '''Parameters for configuring a page's layout.
    
    PageLayout objects may be found on Measure or Part Streams.    

    >>> from music21 import *
    >>> pl = layout.PageLayout(pageNumber = 4, leftMargin=234, rightMargin=124, pageHeight=4000, pageWidth=3000, isNew=True)
    >>> pl.pageNumber
    4
    >>> pl.rightMargin
    124
    >>> pl.leftMargin
    234
    >>> pl.isNew
    True

    This object represents both <print new-page> and <page-layout>
    elements in musicxml

    ## TODO -- make sure that the first pageLayout and systemLayout 
    for each page are working together.

    '''
    def __init__(self, *args, **keywords):
        base.Music21Object.__init__(self)
        
        self.pageNumber = None
        self.leftMargin = None
        self.rightMargin = None
        self.pageHeight = None
        self.pageWidth = None

        # store if this is the start of a new page
        self.isNew = None

        for key in keywords.keys():
            if key.lower() == 'pagenumber':
                self.pageNumber = keywords[key]
            if key.lower() == 'leftmargin':
                self.leftMargin = keywords[key]
            if key.lower() == 'rightmargin':
                self.rightMargin = keywords[key]
            if key.lower() == 'pageheight':
                self.pageHeight = keywords[key]
            if key.lower() == 'pagewidth':
                self.pageWidth = keywords[key]
            if key.lower() == 'isnew':
                self.isNew = keywords[key]

    def __repr__(self):
        return "<music21.layout.PageLayout>"


#-------------------------------------------------------------------------------
class SystemLayout(base.Music21Object):
    '''
    Object that configures or alters a system's layout.

    SystemLayout objects may be found on Measure or 
    Part Streams.    
    
    Importantly, if isNew is True then this object 
    indicates that a new system should start here.
    
    >>> from music21 import *
    >>> sl = layout.SystemLayout(leftMargin=234, rightMargin=124, distance=3, isNew=True)
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
        base.Music21Object.__init__(self)
        
        self.leftMargin = None
        self.rightMargin = None

        # this is probably the distance between adjacent systems
        # musicxml also defines a top-system-distance tag; this may not be
        # necessary to implement, as the top system is defined by context
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

    def __repr__(self):
        return "<music21.layout.SystemLayout>"


#-------------------------------------------------------------------------------
class StaffGroupException(spanner.SpannerException):
    pass


#-------------------------------------------------------------------------------
class StaffGroup(spanner.Spanner):
    '''
    A StaffGroup defines a collection of one or more Parts, 
    specifying that they should be shown together with a bracket, 
    brace, or other symbol, and may have a common name.

    
    >>> from music21 import *
    >>> p1 = stream.Part()
    >>> p2 = stream.Part()
    >>> p1.append(note.WholeNote('C5'))
    >>> p1.append(note.WholeNote('D5'))
    >>> p2.append(note.WholeNote('C3'))
    >>> p2.append(note.WholeNote('D3'))
    >>> p3 = stream.Part()
    >>> p3.append(note.WholeNote('F#4'))
    >>> p3.append(note.WholeNote('G#4'))
    >>> s = stream.Score()
    >>> s.insert(0, p1)
    >>> s.insert(0, p2)
    >>> s.insert(0, p3)
    >>> staffGroup1 = layout.StaffGroup([p1, p2], name='Marimba', abbreviation='Mba.', symbol='brace')
    >>> staffGroup1.barTogether = 'Mensurstrich'
    >>> s.insert(0, staffGroup1)
    >>> staffGroup2 = layout.StaffGroup([p3], name='Xylophone', abbreviation='Xyl.', symbol='bracket')
    >>> s.insert(0, staffGroup2)
    >>> #_DOCS_SHOW s.show()

    .. image:: images/layout_StaffGroup_01.*
        :width: 400


    '''
    def __init__(self, *arguments, **keywords):
        spanner.Spanner.__init__(self, *arguments, **keywords)

        self.name = None # if this group has a name
        self.abbreviation = None 
        self._symbol = None # can be bracket, line, brace
        # determines if barlines are grouped through; this is group barline
        # in musicxml
        self._barTogether = True

        if 'symbol' in keywords.keys():
            self.symbol = keywords['symbol'] # user property
        if 'barTogether' in keywords.keys():
            self.barTogether = keywords['barTogether'] # user property
        if 'name' in keywords.keys():
            self.name = keywords['name'] # user property
        if 'abbreviation' in keywords.keys():
            self.name = keywords['abbreviation'] # user property


    #---------------------------------------------------------------------------
    def _getBarTogether(self):
        return self._barTogether    

    def _setBarTogether(self, value):
        if value is None:
            pass # do nothing for now; could set a default
        elif value in ['yes', True]:
            self._barTogether = True
        elif value in ['no', False]:
            self._barTogether = False
        elif hasattr(value, 'lower') and value.lower() == 'mensurstrich':
            self._barTogether = 'Mensurstrich'
        else:
            raise StaffGroupException('the bar together value %s is not acceptable' % value)

    barTogether = property(_getBarTogether, _setBarTogether, doc = '''
        Get or set the barTogether value, with either Boolean values 
        or yes or no strings.  Or the string 'Mensurstrich' which
        indicates baring between staves but not in staves.

        Currently Mensurstrich i

        >>> from music21 import *
        >>> sg = layout.StaffGroup()
        >>> sg.barTogether = 'yes'
        >>> sg.barTogether
        True
        >>> sg.barTogether = 'Mensurstrich'
        >>> sg.barTogether
        'Mensurstrich'
        ''')

    def _getSymbol(self):
        return self._symbol    

    def _setSymbol(self, value):
        if value is None or str(value).lower() == 'none':
            self._symbol = None
        elif value.lower() in ['brace', 'line', 'bracket']:
            self._symbol = value.lower()
        else:
            raise StaffGroupException('the symbol value %s is not acceptable' % value)
        
    symbol = property(_getSymbol, _setSymbol, doc = '''
        Get or set the symbol value, with either Boolean values or yes or no strings.

        >>> from music21 import *
        >>> sg = layout.StaffGroup()
        >>> sg.symbol = 'Brace'
        >>> sg.symbol
        'brace'
        ''')


#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testBasic(self):
        import music21
        from music21 import stream, note
        from music21.musicxml import m21ToString
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
        unused_raw = m21ToString.fromMusic21Object(s)

    def testGetPageMeasureNumbers(self):
        from music21 import corpus
        c = corpus.parse('luca/gloria').parts[0]
        #c.show('text')
        retStr = ""
        for x in c.flat:
            if 'PageLayout' in x.classes:
                retStr += str(x.pageNumber) + ": " + str(x.measureNumber) + ", "
#        print retStr
        self.assertEqual(retStr, '1: 1, 2: 23, 3: 50, 4: 80, 5: 103, ')

#-------------------------------------------------------------------------------
if __name__ == "__main__":
    import music21
    music21.mainTest(Test)



#------------------------------------------------------------------------------
# eof

